"""Tests for parse_action_with_retry and decide_with_retry."""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from agent.errors import VisionParseError
from agent.schema import ClickAction
from agent.vision_parse import decide_with_retry, parse_action_with_retry


def test_parse_action_with_retry_succeeds_on_first_try() -> None:
    raw = '{"action":"click","x":100,"y":200,"reasoning":"ok"}'
    action = parse_action_with_retry(
        raw,
        provider="test",
        retry_fn=lambda _: pytest.fail("retry should not run"),
        make_error=lambda err: VisionParseError(str(err)),
    )
    assert isinstance(action, ClickAction)
    assert action.x == 100


def test_parse_action_with_retry_retries_then_succeeds() -> None:
    attempts: list[str] = []

    def retry_fn(_: str) -> str:
        attempts.append("retry")
        return '{"action":"click","x":50,"y":75,"reasoning":"fixed"}'

    action = parse_action_with_retry(
        "not json",
        provider="test",
        retry_fn=retry_fn,
        make_error=lambda err: VisionParseError(str(err)),
    )
    assert attempts == ["retry"]
    assert action.x == 50


def test_parse_action_with_retry_raises_parse_error_after_retry() -> None:
    with pytest.raises(VisionParseError, match="invalid action JSON after retry"):
        parse_action_with_retry(
            "still bad",
            provider="test",
            retry_fn=lambda _: "also bad",
            make_error=lambda err: VisionParseError(
                f"invalid action JSON after retry. Last error: {err}"
            ),
        )


def test_parse_action_with_retry_wraps_validation_error() -> None:
    with pytest.raises(VisionParseError):
        parse_action_with_retry(
            '{"action":"click","x":-1,"y":0,"reasoning":""}',
            provider="test",
            retry_fn=lambda _: '{"action":"click","x":-1,"y":0,"reasoning":""}',
            make_error=lambda err: VisionParseError(str(err)),
        )


def test_decide_with_retry_calls_initial_and_retry() -> None:
    calls: list[str] = []

    def call_initial() -> tuple[str, dict]:
        calls.append("initial")
        return "bad", {"total_duration": 1_000_000}

    def call_retry(_: str, __: str) -> tuple[str, dict]:
        calls.append("retry")
        return '{"action":"click","x":10,"y":20,"reasoning":"ok"}', {"total_duration": 2_000_000}

    action = decide_with_retry(
        provider="test",
        call_initial=call_initial,
        call_retry=call_retry,
        log_debug=lambda _: None,
        parse_fn=lambda raw: ClickAction(**json.loads(raw)),
        debug=True,
        make_error=lambda err: VisionParseError(str(err)),
    )
    assert calls == ["initial", "retry"]
    assert action.x == 10
