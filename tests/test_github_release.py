"""Tests for GitHub release policy helpers."""

from __future__ import annotations

import pytest

from agent.github_release import (
    claims_no_assets,
    done_rejection_reason,
    history_used_end_key,
    is_release_detail_page,
    is_release_list_page,
    scroll_oscillation_instruction,
)
from agent.schema import DoneAction, DownloadAsset, PressKeyAction, ScrollAction


def _complete_done(**overrides: object) -> DoneAction:
    base = {
        "action": "done",
        "repository": "openclaw/openclaw",
        "latest_release": "v2026.5.30-beta.1",
        "version": "2026.5.30-beta.1",
        "tag": "v2026.5.30-beta.1",
        "author": "user",
        "published_at": "May 30th, 2026",
        "release_notes": "notes",
        "downloads": [DownloadAsset(name="zip", url="https://example.com/a.zip")],
        "reasoning": "ok",
    }
    base.update(overrides)
    return DoneAction(**base)


DETAIL_URL = "https://github.com/openclaw/openclaw/releases/tag/v2026.5.30-beta.1"
LIST_URL = "https://github.com/openclaw/openclaw/releases"


def test_is_release_list_and_detail_page() -> None:
    assert is_release_list_page(LIST_URL)
    assert not is_release_detail_page(LIST_URL)
    assert is_release_detail_page(DETAIL_URL)
    assert not is_release_list_page(DETAIL_URL)


def test_history_used_end_key() -> None:
    assert not history_used_end_key([])
    assert history_used_end_key(
        [PressKeyAction(action="press_key", key="End", reasoning="assets")]
    )
    assert history_used_end_key(
        [PressKeyAction(action="press_key", key="Meta+ArrowDown", reasoning="bottom")]
    )


def test_done_rejection_on_list_page() -> None:
    reason = done_rejection_reason(LIST_URL, [], _complete_done())
    assert reason is not None
    assert "list page" in reason.lower()


def test_done_rejection_detail_without_end_or_downloads() -> None:
    done = _complete_done(downloads=[], reasoning="finished notes")
    reason = done_rejection_reason(DETAIL_URL, [], done)
    assert reason is not None
    assert "end" in reason.lower()


def test_done_accepts_detail_after_end_with_no_assets_reasoning() -> None:
    done = _complete_done(
        downloads=[],
        reasoning="Assets section not visible after pressing End",
    )
    history = [PressKeyAction(action="press_key", key="End", reasoning="jump")]
    assert done_rejection_reason(DETAIL_URL, history, done) is None


def test_done_accepts_detail_with_downloads_without_end() -> None:
    done = _complete_done()
    assert done_rejection_reason(DETAIL_URL, [], done) is None


@pytest.mark.parametrize(
    ("reasoning", "expected"),
    [
        ("confirmed no assets on this release", True),
        ("finished reading release notes", False),
    ],
)
def test_claims_no_assets(reasoning: str, expected: bool) -> None:
    done = _complete_done(downloads=[], reasoning=reasoning)
    assert claims_no_assets(done) is expected


def test_scroll_oscillation_nudge_does_not_say_emit_done_first() -> None:
    history = [
        ScrollAction(action="scroll", direction="down", amount=1, reasoning="a"),
        ScrollAction(action="scroll", direction="up", amount=1, reasoning="b"),
        ScrollAction(action="scroll", direction="down", amount=1, reasoning="c"),
        ScrollAction(action="scroll", direction="up", amount=1, reasoning="d"),
    ]
    msg = scroll_oscillation_instruction(history)
    assert msg is not None
    assert "press end" in msg.lower()
    assert "emit done now" not in msg.lower()
