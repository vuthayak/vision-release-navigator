"""Tests for create_vision_client factory and credential validation."""

from __future__ import annotations

import pytest

from agent.gemini_client import GeminiVisionClient
from agent.ollama_client import OllamaVisionClient
from agent.vision import create_vision_client


def test_create_vision_client_ollama_local() -> None:
    client = create_vision_client("ollama", ollama_host="http://localhost:11434")
    assert isinstance(client, OllamaVisionClient)


def test_create_vision_client_ollama_cloud_requires_key() -> None:
    with pytest.raises(ValueError, match="OLLAMA_API_KEY is required"):
        create_vision_client("ollama", ollama_host="https://ollama.com")


def test_create_vision_client_ollama_cloud_with_key() -> None:
    client = create_vision_client(
        "ollama",
        ollama_host="https://ollama.com",
        ollama_api_key="test-key",
    )
    assert isinstance(client, OllamaVisionClient)


def test_create_vision_client_gemini_requires_key() -> None:
    with pytest.raises(ValueError, match="GOOGLE_API_KEY is required"):
        create_vision_client("gemini", api_key=None)


def test_create_vision_client_gemini_with_key() -> None:
    client = create_vision_client("gemini", api_key="test-key")
    assert isinstance(client, GeminiVisionClient)


def test_create_vision_client_unknown_provider() -> None:
    with pytest.raises(ValueError, match="Unknown vision provider"):
        create_vision_client("openai")
