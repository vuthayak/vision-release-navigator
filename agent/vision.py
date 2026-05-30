"""Vision client factory and public exports."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from agent.gemini_client import GeminiVisionClient
from agent.ollama_client import OllamaConnectionError, OllamaVisionClient, ollama_requires_api_key
from agent.schema import (
    Action,
    ClickAction,
    DoneAction,
    DownloadAsset,
    PressKeyAction,
    ScrollAction,
    SYSTEM_PROMPT,
    TypeAction,
    WaitAction,
)

DEFAULT_OLLAMA_MODEL = "qwen2.5vl:3b"
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
DEFAULT_OLLAMA_HOST = "https://ollama.com"


@runtime_checkable
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
    normalized = provider.strip().lower()
    if normalized == "ollama":
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
    raise ValueError(f"Unknown vision provider: {provider!r} (expected ollama or gemini)")


__all__ = [
    "Action",
    "ClickAction",
    "DEFAULT_GEMINI_MODEL",
    "DEFAULT_OLLAMA_HOST",
    "DEFAULT_OLLAMA_MODEL",
    "DoneAction",
    "DownloadAsset",
    "GeminiVisionClient",
    "OllamaConnectionError",
    "OllamaVisionClient",
    "PressKeyAction",
    "ScrollAction",
    "SYSTEM_PROMPT",
    "TypeAction",
    "VisionClient",
    "WaitAction",
    "create_vision_client",
    "ollama_requires_api_key",
]
