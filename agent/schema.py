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

# Substrings that indicate the model confirmed no Assets section on the release page.
_NO_ASSETS_REASONING_MARKERS = (
    "no assets",
    "without assets",
    "assets absent",
    "no asset section",
    "no downloads",
    "no asset",
    "assets empty",
    "assets none",
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
        """True when the model emitted done before filling required release fields."""
        if not all(getattr(self, field).strip() for field in REQUIRED_STRING_FIELDS):
            return True
        if not self.downloads and not self._claims_no_assets():
            return True
        return False

    def _claims_no_assets(self) -> bool:
        """Empty downloads are OK only when reasoning clearly states no Assets section."""
        reasoning = self.reasoning.lower()
        if any(marker in reasoning for marker in _NO_ASSETS_REASONING_MARKERS):
            return True
        if "assets" in reasoning and any(
            word in reasoning for word in ("absent", "empty", "none", "missing")
        ):
            return True
        return False


Action = Annotated[
    Union[ClickAction, TypeAction, PressKeyAction, ScrollAction, WaitAction, DoneAction],
    Field(discriminator="action"),
]

_ACTION_ADAPTER: TypeAdapter[Action] = TypeAdapter(Action)
ACTION_JSON_SCHEMA = _ACTION_ADAPTER.json_schema()


def validate_action(data: object) -> Action:
    return _ACTION_ADAPTER.validate_python(data)
