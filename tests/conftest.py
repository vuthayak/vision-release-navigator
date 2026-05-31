"""Shared test fixtures and import stubs."""

from __future__ import annotations

import sys
from types import ModuleType
from unittest.mock import MagicMock


def _install_ollama_stub() -> None:
    if "ollama" in sys.modules:
        return
    ollama = ModuleType("ollama")
    ollama.Client = MagicMock()
    ollama.ResponseError = type("ResponseError", (Exception,), {})
    sys.modules["ollama"] = ollama


def _install_google_genai_stub() -> None:
    if "google.genai" in sys.modules:
        return

    genai = ModuleType("genai")
    genai.Client = MagicMock()
    genai_errors = ModuleType("errors")
    genai_errors.ClientError = type(
        "ClientError",
        (Exception,),
        {"code": 400},
    )
    types_mod = ModuleType("types")
    types_mod.Content = MagicMock()
    types_mod.Part = MagicMock()
    types_mod.Part.from_bytes = MagicMock()
    types_mod.Part.from_text = MagicMock()
    types_mod.GenerateContentConfig = MagicMock()
    types_mod.GenerateContentResponse = MagicMock()

    google = sys.modules.get("google")
    if google is None:
        google = ModuleType("google")
        sys.modules["google"] = google
    google.genai = genai
    genai.errors = genai_errors
    genai.types = types_mod
    sys.modules["google.genai"] = genai
    sys.modules["google.genai.errors"] = genai_errors
    sys.modules["google.genai.types"] = types_mod


_install_ollama_stub()
_install_google_genai_stub()
