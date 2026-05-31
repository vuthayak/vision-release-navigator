"""Tests for DoneAction extraction completeness checks."""

from __future__ import annotations

import pytest

from agent.schema import DoneAction, DownloadAsset


def _complete_done(**overrides: object) -> DoneAction:
    base = {
        "action": "done",
        "repository": "facebook/react",
        "latest_release": "19.2.6",
        "version": "19.2.6",
        "tag": "v19.2.6",
        "author": "react-bot",
        "published_at": "Jan 1, 2026",
        "release_notes": "Bug fixes",
        "downloads": [DownloadAsset(name="Source", url="https://example.com/src.zip")],
        "reasoning": "extracted stable release",
    }
    base.update(overrides)
    return DoneAction(**base)


@pytest.mark.parametrize(
    ("done", "expected_incomplete"),
    [
        (_complete_done(), False),
        (_complete_done(repository=""), True),
        (_complete_done(latest_release=""), True),
        (_complete_done(version=""), True),
        (_complete_done(tag=""), True),
        (_complete_done(author=""), True),
        (_complete_done(published_at=""), True),
        (_complete_done(release_notes=""), True),
        (
            _complete_done(
                downloads=[],
                reasoning="confirmed no assets on this release",
            ),
            False,
        ),
        (
            _complete_done(
                downloads=[],
                reasoning="assets section is empty",
            ),
            False,
        ),
        (
            _complete_done(downloads=[], reasoning="finished reading release notes"),
            True,
        ),
    ],
)
def test_is_incomplete_extraction(done: DoneAction, expected_incomplete: bool) -> None:
    assert done.is_incomplete_extraction() is expected_incomplete


def test_partial_v1_fields_rejected() -> None:
    """any()-style bug would accept one filled v1 field; all() requires every field."""
    done = DoneAction(
        action="done",
        repository="facebook/react",
        latest_release="",
        version="",
        tag="",
        author="",
        published_at="Jan 1, 2026",
        release_notes="notes",
        downloads=[DownloadAsset(name="Source", url="https://example.com/src.zip")],
        reasoning="partial",
    )
    assert done.is_incomplete_extraction() is True
