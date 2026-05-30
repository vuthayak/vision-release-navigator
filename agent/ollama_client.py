"""Ollama vision backend (local or Ollama Cloud)."""

from __future__ import annotations

import base64
import json
import sys

from ollama import Client, ResponseError
from pydantic import ValidationError

from agent.schema import (
    ACTION_JSON_SCHEMA,
    SYSTEM_PROMPT,
    Action,
    action_retry_message,
    build_user_text,
    parse_action,
)


class OllamaConnectionError(Exception):
    """Raised when Ollama is unreachable or the model is missing."""


def ollama_requires_api_key(host: str) -> bool:
    normalized = host.strip().lower().rstrip("/")
    return normalized == "https://ollama.com" or normalized.endswith(".ollama.com")


class OllamaVisionClient:
    def __init__(
        self,
        model: str = "qwen2.5vl:3b",
        host: str = "https://ollama.com",
        api_key: str | None = None,
    ) -> None:
        self._model = model
        self._host = host
        headers: dict[str, str] | None = None
        if api_key:
            headers = {"Authorization": f"Bearer {api_key}"}
        elif ollama_requires_api_key(host):
            raise OllamaConnectionError(
                "OLLAMA_API_KEY is required for Ollama Cloud. "
                "Create a key at https://ollama.com/settings/keys"
            )
        self._client = Client(host=host, headers=headers)

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

        try:
            response = self._client.chat(
                model=self._model,
                messages=messages,
                format=ACTION_JSON_SCHEMA,
                options={"temperature": 0},
            )
        except (ResponseError, ConnectionError, OSError) as exc:
            hint = (
                "Check OLLAMA_API_KEY and model name at https://ollama.com/library"
                if ollama_requires_api_key(self._host)
                else f"Ensure Ollama is running locally: ollama pull {self._model}"
            )
            raise OllamaConnectionError(
                f"Ollama request failed ({exc}). {hint}"
            ) from exc

        if debug:
            duration_ms = response.get("total_duration", 0) // 1_000_000
            target = "cloud" if ollama_requires_api_key(self._host) else "local"
            print(
                f"[vision:ollama:{target}] host={self._host} model={self._model} "
                f"duration_ms={duration_ms}",
                file=sys.stderr,
            )

        raw = response.message.content or ""
        try:
            return parse_action(raw)
        except (json.JSONDecodeError, ValidationError) as first_err:
            retry_text = action_retry_message(raw, first_err)
            retry_messages = [
                *messages,
                {"role": "assistant", "content": raw},
                {"role": "user", "content": retry_text},
            ]
            try:
                retry_response = self._client.chat(
                    model=self._model,
                    messages=retry_messages,
                    format=ACTION_JSON_SCHEMA,
                    options={"temperature": 0},
                )
            except (ResponseError, ConnectionError, OSError) as exc:
                raise OllamaConnectionError(
                    f"Ollama request failed on retry ({exc})."
                ) from exc
            try:
                return parse_action(retry_response.message.content or "")
            except (json.JSONDecodeError, ValidationError) as retry_err:
                raise OllamaConnectionError(
                    "Ollama returned invalid action JSON after retry. "
                    f"Last error: {retry_err}"
                ) from retry_err
