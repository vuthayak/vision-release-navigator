"""Ollama vision backend (local or Ollama Cloud)."""

from __future__ import annotations

import base64
import sys

from ollama import Client, ResponseError

from agent.action_parse import build_user_text, parse_action_lenient
from agent.defaults import DEFAULT_OLLAMA_HOST, DEFAULT_OLLAMA_MODEL
from agent.errors import VisionClientError, VisionParseError
from agent.prompts import SYSTEM_PROMPT
from agent.schema import ACTION_JSON_SCHEMA, Action
from agent.vision_parse import decide_with_retry


OLLAMA_CHAT_OPTIONS = {"temperature": 0, "num_predict": 1024}  # num_predict caps JSON length.


class OllamaConnectionError(VisionClientError):
    """Raised when Ollama is unreachable or the model is missing."""


def ollama_requires_api_key(host: str) -> bool:
    normalized = host.strip().lower().rstrip("/")
    return normalized == "https://ollama.com" or normalized.endswith(".ollama.com")


class OllamaVisionClient:
    def __init__(
        self,
        model: str = DEFAULT_OLLAMA_MODEL,
        host: str = DEFAULT_OLLAMA_HOST,
        api_key: str | None = None,
    ) -> None:
        self._model = model
        self._host = host
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else None
        self._client = Client(host=host, headers=headers)

    def _chat(self, messages: list[dict], *, on_retry: bool = False) -> tuple[str, dict]:
        try:
            response = self._client.chat(
                model=self._model,
                messages=messages,
                format=ACTION_JSON_SCHEMA,  # Structured output hint; Ollama still malforms sometimes.
                options=OLLAMA_CHAT_OPTIONS,
            )
        except (ResponseError, ConnectionError, OSError) as exc:
            if on_retry:
                raise OllamaConnectionError(
                    f"Ollama request failed on retry ({exc})."
                ) from exc
            hint = (
                "Check OLLAMA_API_KEY and model name at https://ollama.com/library"
                if ollama_requires_api_key(self._host)
                else f"Ensure Ollama is running locally: ollama pull {self._model}"
            )
            raise OllamaConnectionError(
                f"Ollama request failed ({exc}). {hint}"
            ) from exc
        return response.message.content or "", response

    def _log_debug(self, response: dict) -> None:
        duration_ms = (response.get("total_duration") or 0) // 1_000_000
        target = "cloud" if ollama_requires_api_key(self._host) else "local"
        print(
            f"[vision:ollama:{target}] host={self._host} model={self._model} "
            f"duration_ms={duration_ms}",
            file=sys.stderr,
        )

    def decide_next_action(
        self,
        screenshot_png: bytes,
        user_prompt: str,
        history: list[Action],
        current_url: str,
        *,
        extra_instruction: str | None = None,
        debug: bool = False,
    ) -> Action:
        user_text = build_user_text(
            user_prompt, history, current_url, extra_instruction=extra_instruction
        )
        image_b64 = base64.b64encode(screenshot_png).decode("ascii")

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": user_text,
                "images": [image_b64],
            },
        ]

        def call_initial() -> tuple[str, dict]:
            return self._chat(messages)

        def call_retry(original_raw: str, retry_text: str) -> tuple[str, dict]:
            retry_messages = [
                *messages,
                {"role": "assistant", "content": original_raw},
                {"role": "user", "content": retry_text},
            ]
            return self._chat(retry_messages, on_retry=True)

        return decide_with_retry(
            provider="ollama",
            call_initial=call_initial,
            call_retry=call_retry,
            log_debug=self._log_debug,
            parse_fn=parse_action_lenient,  # Ollama needs repair/salvage path.
            debug=debug,
            make_error=lambda err: VisionParseError(
                "Ollama returned invalid action JSON after retry. "
                f"Last error: {err}"
            ),
        )
