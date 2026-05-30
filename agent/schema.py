"""Action schema, system prompt, and JSON parsing shared by vision providers."""

from __future__ import annotations

import ast
import json
import re
from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel, Field, TypeAdapter, ValidationError

SYSTEM_PROMPT = """\
You are a vision-driven browser automation agent. Each turn you receive a screenshot \
of the current browser viewport and must output exactly ONE next action as JSON.

Coordinate convention:
- x and y for clicks are integers from 0 to 1000 (normalized viewport space).
- (0, 0) is the top-left corner; (1000, 1000) is the bottom-right.
- (500, 500) is the center of the viewport.

Available actions (discriminated by the "action" field):
- click: click at (x, y)
- type: type text into the currently focused element
- press_key: press a keyboard key (e.g. Enter, Tab, Escape)
- scroll: scroll up or down by amount (1-10)
- wait: pause for ms milliseconds (0-10000)
- done: task complete — include repository, latest_release, version, tag, author

Task contract:
- Fulfill the user's natural-language goal starting from the given URL.
- For GitHub release tasks, navigate to the repository and open the releases area \
(click a visible "Releases" link or label in the sidebar or page header).
- Do NOT emit "done" until you have read all five fields from a **stable** release \
entry under the Releases section.

Important constraints:
- You only see pixels. Do NOT reference CSS selectors, XPath, DOM ids, or HTML structure.
- Output exactly one action per turn.
- Every JSON object MUST include a non-empty "reasoning" string (one or two sentences).
- Example click: {"action":"click","x":500,"y":120,"reasoning":"Open the Releases link."}

GitHub heuristics (visual, not selectors):
- The search bar is near the top of github.com.
- Locate a visible **"Releases"** heading or sidebar label (often with a count, e.g. \
"Releases 126"). Release entries live in the panel **below or beside** that label.
- Do NOT assume the first entry under Releases is the latest — it may be a pre-release \
or draft listed above the stable release.
- Skip entries showing a **"Pre-release"** badge or tags containing -next, -rc, -alpha, \
or -beta. Prefer the entry labeled **"Latest"** or the newest stable-looking semver.
- If the visible region only shows pre-releases, scroll down within the release list \
and rescan before emitting "done".
- Field mapping from the chosen **stable** entry only:
  - repository: owner/repo from page context
  - latest_release: the release **title** (not the tag)
  - version: semver number without a leading "v"
  - tag: full tag exactly as shown
  - author: username on that release card
- Navigation: use vision to reach the repo and open the releases area; do not rely on \
typing URLs.
"""


class ClickAction(BaseModel):
    action: Literal["click"]
    x: int = Field(ge=0, le=1000)
    y: int = Field(ge=0, le=1000)
    reasoning: str


class TypeAction(BaseModel):
    action: Literal["type"]
    text: str
    reasoning: str


class PressKeyAction(BaseModel):
    action: Literal["press_key"]
    key: str
    reasoning: str


class ScrollAction(BaseModel):
    action: Literal["scroll"]
    direction: Literal["up", "down"]
    amount: int = Field(ge=1, le=10)
    reasoning: str


class WaitAction(BaseModel):
    action: Literal["wait"]
    ms: int = Field(ge=0, le=10000)
    reasoning: str


class DoneAction(BaseModel):
    action: Literal["done"]
    repository: str
    latest_release: str
    version: str
    tag: str
    author: str
    reasoning: str


Action = Annotated[
    Union[ClickAction, TypeAction, PressKeyAction, ScrollAction, WaitAction, DoneAction],
    Field(discriminator="action"),
]

_ACTION_ADAPTER: TypeAdapter[Action] = TypeAdapter(Action)
ACTION_JSON_SCHEMA = _ACTION_ADAPTER.json_schema()


def format_history(history: list[Action]) -> str:
    if not history:
        return "(no prior actions)"
    lines: list[str] = []
    for i, item in enumerate(history, start=1):
        dumped = item.model_dump() if isinstance(item, BaseModel) else dict(item)
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


def _loads_action_json(raw: str) -> Any:
    text = _extract_json_object(_strip_json_fences(raw))
    candidates = [text, _repair_json(text)]
    last_err: json.JSONDecodeError | None = None
    for candidate in candidates:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError as err:
            last_err = err
    try:
        value = ast.literal_eval(text)
    except (SyntaxError, ValueError):
        value = None
    if isinstance(value, dict):
        return value
    assert last_err is not None
    raise last_err


def _normalize_action_payload(data: Any) -> Any:
    """Fill fields vision models often omit despite JSON schema (e.g. reasoning)."""
    if not isinstance(data, dict) or "action" not in data:
        return data
    if "reasoning" not in data:
        data = {**data, "reasoning": ""}
    return data


def parse_action(raw: str) -> Action:
    data = _loads_action_json(raw)
    return _ACTION_ADAPTER.validate_python(_normalize_action_payload(data))


def action_retry_message(raw: str, err: Exception) -> str:
    return (
        "Your previous response was not valid action JSON. "
        f"Error: {err}\n\n"
        f"Invalid response was:\n{raw}\n\n"
        "Reply with exactly one JSON object. Use double-quoted keys and string values only."
    )
