"""Pydantic action models and JSON schema for vision providers."""

from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field, TypeAdapter

REQUIRED_STRING_FIELDS = (
    "repository",
    "latest_release",
    "version",
    "tag",
    "author",
    "published_at",
    "release_notes",
)

class DownloadAsset(BaseModel):
    name: str
    url: str


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
    published_at: str
    release_notes: str
    downloads: list[DownloadAsset] = Field(default_factory=list)
    reasoning: str

    def is_incomplete_extraction(self) -> bool:
        """True when required string fields are blank (downloads checked in github_release)."""
        return not all(
            getattr(self, field).strip() for field in REQUIRED_STRING_FIELDS
        )


Action = Annotated[
    Union[ClickAction, TypeAction, PressKeyAction, ScrollAction, WaitAction, DoneAction],
    Field(discriminator="action"),  # Pydantic picks the model from the "action" string.
]

_ACTION_ADAPTER: TypeAdapter[Action] = TypeAdapter(Action)
ACTION_JSON_SCHEMA = _ACTION_ADAPTER.json_schema()  # Passed to Ollama format= and Gemini schema.


def validate_action(data: object) -> Action:
    return _ACTION_ADAPTER.validate_python(data)
