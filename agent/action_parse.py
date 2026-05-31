"""Parse and validate vision model action JSON."""

from __future__ import annotations

import ast
import json
import re
from typing import Any

from agent.schema import Action, validate_action

_INT_FIELDS = frozenset({"x", "y", "amount", "ms"})

# Regex patterns keyed by action name for salvaging truncated Ollama responses.
_SALVAGE_PATTERNS: dict[str, dict[str, str]] = {
    "click": {
        "x": r'"x"\s*:\s*(\d+)',
        "y": r'"y"\s*:\s*(\d+)',
    },
    "type": {
        "text": r'"text"\s*:\s*"((?:[^"\\]|\\.)*)',
    },
    "press_key": {
        "key": r'"key"\s*:\s*"([^"]+)"',
    },
    "scroll": {
        "direction": r'"direction"\s*:\s*"(\w+)"',
        "amount": r'"amount"\s*:\s*(\d+)',
    },
    "wait": {
        "ms": r'"ms"\s*:\s*(\d+)',
    },
}


def format_history(history: list[Action]) -> str:
    if not history:
        return "(no prior actions)"
    lines: list[str] = []
    for i, item in enumerate(history, start=1):
        dumped = item.model_dump()
        action = dumped.get("action", "?")
        reasoning = str(dumped.get("reasoning", ""))[:200]
        lines.append(f"{i}. {action}: {reasoning}")
    return "\n".join(lines)


def build_user_text(
    user_prompt: str,
    history: list[Action],
    current_url: str,
    *,
    extra_instruction: str | None = None,
) -> str:
    user_text = (
        f"User goal:\n{user_prompt}\n\n"
        f"Current URL:\n{current_url}\n\n"
        f"Prior actions:\n{format_history(history)}\n"
    )
    if extra_instruction:
        user_text += f"\nSystem note:\n{extra_instruction}\n"
    user_text += "\nWhat is the single next action?"
    return user_text


def action_retry_message(raw: str, err: Exception) -> str:
    return (
        "Your previous response was not valid action JSON. "
        f"Error: {err}\n\n"
        f"Invalid response was:\n{raw}\n\n"
        "Reply with exactly one JSON object. Use double-quoted keys and string values only. "
        "Keep reasoning under 80 characters for navigation actions."
    )


def _strip_json_fences(raw: str) -> str:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, count=1)
        text = re.sub(r"\s*```\s*$", "", text, count=1)
    return text.strip()


def _extract_json_object(text: str) -> str:
    """Take the first top-level `{...}` object when the model adds prose around JSON."""
    start = text.find("{")
    if start == -1:
        return text
    depth = 0
    in_string = False
    escape = False
    quote: str | None = None
    for i in range(start, len(text)):
        ch = text[i]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == quote:
                in_string = False
            continue
        if ch in ('"', "'"):
            in_string = True
            quote = ch
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return text[start:]


def _repair_json(text: str) -> str:
    """Fix common LLM JSON mistakes (trailing commas)."""
    return re.sub(r",(\s*[}\]])", r"\1", text)


def _repair_truncated_tail(text: str) -> str:
    """Close JSON cut off before reasoning or closing brace (common Ollama truncation)."""
    t = text.strip()
    if not t.startswith("{") or t.endswith("}"):
        return t
    if '"reasoning"' not in t and "'reasoning'" not in t:
        t = t.rstrip().rstrip(",") + ',"reasoning":""}'
    if not t.endswith("}"):
        t += "}"
    return t


def _salvage_truncated_action(text: str) -> dict[str, Any] | None:
    """Rebuild a valid navigation action dict when the response was cut off mid-JSON."""
    stripped = text.strip()
    if not stripped.startswith("{"):
        return None

    action_m = re.search(r"""['"]action['"]\s*:\s*['"](\w+)['"]""", stripped)
    if not action_m:
        return None

    action = action_m.group(1)
    patterns = _SALVAGE_PATTERNS.get(action)
    if patterns is None:
        return None

    result: dict[str, Any] = {"action": action, "reasoning": ""}
    for field, pattern in patterns.items():
        match = re.search(pattern, stripped)
        if not match:
            return None
        value: Any = int(match.group(1)) if field in _INT_FIELDS else match.group(1)
        result[field] = value
    return result


def _normalize_action_payload(data: object) -> object:
    """Fill fields vision models often omit despite JSON schema (e.g. reasoning)."""
    if not isinstance(data, dict) or "action" not in data:
        return data

    normalized = dict(data)

    # Model sometimes emits click coords as a single [x, y] array under "x".
    x_val = normalized.get("x")
    if isinstance(x_val, (list, tuple)) and len(x_val) >= 2:
        normalized["x"] = x_val[0]
        if "y" not in normalized:
            normalized["y"] = x_val[1]

    # Scroll actions occasionally omit direction.
    if normalized.get("action") == "scroll" and "direction" not in normalized:
        normalized["direction"] = "down"

    if "reasoning" not in normalized:
        normalized["reasoning"] = ""

    return normalized


def _loads_json(raw: str, *, lenient: bool) -> object:
    text = _extract_json_object(_strip_json_fences(raw))
    if not lenient:
        return json.loads(text)

    candidates = [text, _repair_json(text), _repair_truncated_tail(text)]
    last_err: json.JSONDecodeError | None = None
    for candidate in candidates:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError as err:
            last_err = err

    salvaged = _salvage_truncated_action(text)
    if salvaged is not None:
        return salvaged

    try:
        value = ast.literal_eval(text)
    except (SyntaxError, ValueError):
        value = None
    if isinstance(value, dict):
        return value

    assert last_err is not None
    raise last_err


def parse_action(raw: str) -> Action:
    """Strict parse for structured-output providers (e.g. Gemini)."""
    data = _loads_json(raw, lenient=False)
    return validate_action(_normalize_action_payload(data))


def parse_action_lenient(raw: str) -> Action:
    """Lenient parse with repair/salvage for providers that truncate or malform JSON."""
    data = _loads_json(raw, lenient=True)
    return validate_action(_normalize_action_payload(data))
