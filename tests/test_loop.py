"""Tests for agent loop pure helpers."""

from __future__ import annotations

from agent.loop import NO_PROGRESS_STREAK, _no_progress_instruction, _screenshot_hash


def test_screenshot_hash_is_stable() -> None:
    png = b"\x89PNG\r\n\x1a\nfake"
    assert _screenshot_hash(png) == _screenshot_hash(png)
    assert _screenshot_hash(png) != _screenshot_hash(png + b"x")


def test_no_progress_instruction_mentions_streak() -> None:
    text = _no_progress_instruction(NO_PROGRESS_STREAK)
    assert str(NO_PROGRESS_STREAK) in text
    assert "scroll" in text.lower()
