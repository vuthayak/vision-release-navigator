"""Gemini vision backend."""

from __future__ import annotations

import json
import sys

from google import genai
from google.genai import types
from pydantic import ValidationError

from agent.schema import (
    ACTION_JSON_SCHEMA,
    SYSTEM_PROMPT,
    Action,
    build_user_text,
    action_retry_message,
    parse_action,
)


class GeminiVisionClient:
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash") -> None:
        self._client = genai.Client(api_key=api_key)
        self._model = model

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

        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_bytes(data=screenshot_png, mime_type="image/png"),
                    types.Part.from_text(text=user_text),
                ],
            )
        ]

        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_json_schema=ACTION_JSON_SCHEMA,
        )

        response = self._client.models.generate_content(
            model=self._model,
            contents=contents,
            config=config,
        )

        if debug and response.usage_metadata:
            meta = response.usage_metadata
            print(
                f"[vision:gemini] tokens prompt={meta.prompt_token_count} "
                f"candidates={meta.candidates_token_count}",
                file=sys.stderr,
            )

        raw = response.text or ""
        try:
            return parse_action(raw)
        except (json.JSONDecodeError, ValidationError) as first_err:
            retry_text = action_retry_message(raw, first_err)
            retry_contents = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_bytes(data=screenshot_png, mime_type="image/png"),
                        types.Part.from_text(text=user_text),
                        types.Part.from_text(text=retry_text),
                    ],
                )
            ]
            retry_response = self._client.models.generate_content(
                model=self._model,
                contents=retry_contents,
                config=config,
            )
            return parse_action(retry_response.text or "")
