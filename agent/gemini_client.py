"""Gemini vision backend."""

from __future__ import annotations

import sys

from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from agent.action_parse import build_user_text, parse_action
from agent.defaults import DEFAULT_GEMINI_MODEL
from agent.errors import VisionClientError, VisionParseError
from agent.prompts import SYSTEM_PROMPT
from agent.schema import ACTION_JSON_SCHEMA, Action
from agent.vision_parse import decide_with_retry


class GeminiVisionError(VisionClientError):
    """Raised when Gemini API requests fail."""


class GeminiVisionClient:
    def __init__(self, api_key: str, model: str = DEFAULT_GEMINI_MODEL) -> None:
        self._client = genai.Client(api_key=api_key)
        self._model = model

    def _generate_content(self, contents: list[types.Content]) -> types.GenerateContentResponse:
        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_json_schema=ACTION_JSON_SCHEMA,  # Enforced structured output from Gemini.
            temperature=0,
        )
        try:
            return self._client.models.generate_content(
                model=self._model,
                contents=contents,
                config=config,
            )
        except genai_errors.ClientError as exc:
            if exc.code == 400 and "API key not valid" in str(exc):
                raise GeminiVisionError(
                    "Gemini rejected GOOGLE_API_KEY (invalid or revoked). "
                    "Create a new key at https://aistudio.google.com/apikey and update .env:\n"
                    "  GOOGLE_API_KEY=your_key_with_no_quotes_or_spaces"
                ) from exc
            raise GeminiVisionError(f"Gemini API error: {exc}") from exc

    def _log_debug(self, response: types.GenerateContentResponse) -> None:
        if not response.usage_metadata:
            return
        meta = response.usage_metadata
        print(
            f"[vision:gemini] tokens prompt={meta.prompt_token_count} "
            f"candidates={meta.candidates_token_count}",
            file=sys.stderr,
        )

    def _user_contents(
        self,
        screenshot_png: bytes,
        user_text: str,
    ) -> list[types.Content]:
        return [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_bytes(data=screenshot_png, mime_type="image/png"),
                    types.Part.from_text(text=user_text),
                ],
            )
        ]

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
        contents = self._user_contents(screenshot_png, user_text)

        def call_initial() -> tuple[str, types.GenerateContentResponse]:
            response = self._generate_content(contents)
            return response.text or "", response

        def call_retry(
            original_raw: str, retry_text: str
        ) -> tuple[str, types.GenerateContentResponse]:
            # Multi-turn: replay the bad response, then send the correction prompt.
            retry_contents = [
                *contents,
                types.Content(role="model", parts=[types.Part.from_text(text=original_raw)]),
                types.Content(role="user", parts=[types.Part.from_text(text=retry_text)]),
            ]
            retry_response = self._generate_content(retry_contents)
            return retry_response.text or "", retry_response

        return decide_with_retry(
            provider="gemini",
            call_initial=call_initial,
            call_retry=call_retry,
            log_debug=self._log_debug,
            parse_fn=parse_action,  # Gemini JSON is reliable enough for strict parse.
            debug=debug,
            make_error=lambda err: VisionParseError(
                "Gemini returned invalid action JSON after retry. "
                f"Last error: {err}"
            ),
        )
