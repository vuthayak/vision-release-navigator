"""Tests for agent loop pure helpers."""

from __future__ import annotations

from agent.github_release import (
    build_extra_instruction,
    is_release_list_page,
    scroll_budget_instruction,
    scroll_oscillation_instruction,
)
from agent.loop import NO_PROGRESS_STREAK, _no_progress_instruction, _screenshot_hash
from agent.schema import ScrollAction


def test_screenshot_hash_is_stable() -> None:
    png = b"\x89PNG\r\n\x1a\nfake"
    assert _screenshot_hash(png) == _screenshot_hash(png)
    assert _screenshot_hash(png) != _screenshot_hash(png + b"x")


def test_no_progress_instruction_mentions_streak() -> None:
    text = _no_progress_instruction(NO_PROGRESS_STREAK)
    assert str(NO_PROGRESS_STREAK) in text
    assert "scroll" in text.lower()


def test_scroll_oscillation_instruction_detects_ping_pong() -> None:
    history = [
        ScrollAction(action="scroll", direction="down", amount=1, reasoning="a"),
        ScrollAction(action="scroll", direction="up", amount=1, reasoning="b"),
        ScrollAction(action="scroll", direction="down", amount=1, reasoning="c"),
        ScrollAction(action="scroll", direction="up", amount=1, reasoning="d"),
    ]
    msg = scroll_oscillation_instruction(history)
    assert msg is not None
    assert "alternating scroll" in msg.lower() or "scroll up and down" in msg.lower()


def test_scroll_budget_instruction_after_many_scrolls() -> None:
    history = [
        ScrollAction(action="scroll", direction="down", amount=1, reasoning=str(i))
        for i in range(5)
    ]
    assert scroll_budget_instruction(history) is not None


def test_build_extra_instruction_prefers_oscillation_over_stale() -> None:
    history = [
        ScrollAction(action="scroll", direction="down", amount=1, reasoning="a"),
        ScrollAction(action="scroll", direction="up", amount=1, reasoning="b"),
        ScrollAction(action="scroll", direction="down", amount=1, reasoning="c"),
        ScrollAction(action="scroll", direction="up", amount=1, reasoning="d"),
    ]
    msg = build_extra_instruction(
        history,
        stale_streak=NO_PROGRESS_STREAK,
        no_progress_streak=NO_PROGRESS_STREAK,
        no_progress_message=_no_progress_instruction(NO_PROGRESS_STREAK),
    )
    assert msg is not None
    assert "scroll" in msg.lower()


def test_is_release_list_page() -> None:
    assert is_release_list_page("https://github.com/openclaw/openclaw/releases")
    assert not is_release_list_page(
        "https://github.com/openclaw/openclaw/releases/tag/v2026.5.30-beta.1"
    )
