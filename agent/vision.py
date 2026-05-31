"""Vision client factory and protocol."""

from __future__ import annotations

from typing import Protocol

from agent.defaults import DEFAULT_GEMINI_MODEL, DEFAULT_OLLAMA_HOST, DEFAULT_OLLAMA_MODEL
from agent.errors import VisionClientError
from agent.gemini_client import GeminiVisionClient
from agent.ollama_client import OllamaVisionClient, ollama_requires_api_key
from agent.schema import Action


class VisionClient(Protocol):
    def decide_next_action(
        self,
        screenshot_png: bytes,
        user_prompt: str,
        history: list[Action],
        current_url: str,
        *,
        extra_instruction: str | None = None,
        debug: bool = False,
    ) -> Action: ...


def create_vision_client(
    provider: str,
    *,
    model: str | None = None,
    api_key: str | None = None,
    ollama_host: str = DEFAULT_OLLAMA_HOST,
    ollama_api_key: str | None = None,
) -> VisionClient:
    """Return the vision backend matching CLI --provider (ollama or gemini)."""
    normalized = provider.strip().lower()
    if normalized == "ollama":
        if ollama_requires_api_key(ollama_host) and not ollama_api_key:
            raise ValueError(
                "OLLAMA_API_KEY is required for Ollama Cloud. "
                "Create a key at https://ollama.com/settings/keys"
            )
        return OllamaVisionClient(
            model=model or DEFAULT_OLLAMA_MODEL,
            host=ollama_host,
            api_key=ollama_api_key,
        )
    if normalized == "gemini":
        if not api_key:
            raise ValueError("GOOGLE_API_KEY is required for provider gemini")
        return GeminiVisionClient(
            api_key=api_key,
            model=model or DEFAULT_GEMINI_MODEL,
        )
    raise ValueError(
        f"Unknown vision provider: {normalized!r} (expected ollama or gemini)"
    )


__all__ = ["VisionClient", "VisionClientError", "create_vision_client"]
