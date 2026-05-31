"""GitHub release extraction policy — URL checks, done validation, loop nudges, prompt fragments."""

from __future__ import annotations

from agent.schema import Action, DoneAction, PressKeyAction, ScrollAction

# Empty downloads[] is accepted after End only when reasoning clearly states no Assets.
NO_ASSETS_REASONING_MARKERS = (
    "no assets",
    "without assets",
    "assets absent",
    "no asset section",
    "no downloads",
    "no asset",
    "assets empty",
    "assets none",
    "assets not visible",
    "assets section not visible",
    "not visible after scrolling",
    "could not find assets",
    "unable to find assets",
)

_END_KEY_ALIASES = frozenset({"end", "meta+arrowdown"})

# Loop nudges (also referenced by prompt fragments below).
NUDGE_SCROLL_OSCILLATION = (
    "You are alternating scroll up and down without progress. Stop scrolling. "
    "Press End once to jump to Assets at the page bottom. "
    "Then emit done with partial release_notes from the top of the page and downloads from Assets."
)

NUDGE_SCROLL_BUDGET = (
    "You have scrolled many times in this release view. Use press_key End once to "
    "jump to Assets at the page bottom, then emit done with partial release_notes "
    "from the top of the page."
)

PROMPT_RELEASE_DETAIL_WORKFLOW = """\
Release detail workflow (use this order):
1. Land on `/releases/tag/...` detail — read **header** fields (title, tag, author, date) \
and transcribe **visible** release_notes from the top (one screen is enough).
2. **Do not** incrementally scroll through long changelogs — partial notes from step 1 are \
the intended release_notes value.
3. **press_key End** once to jump to the **bottom** of this release page (like Cmd+Down on \
Mac). GitHub puts **Assets** at the footer; this is safe because the page is isolated to \
one release.
4. Read the **Assets** section and populate downloads[] before emitting done.
5. **Never** press End on the releases **list** page — only on release **detail** pages.
"""

PROMPT_LONG_CHANGELOG_RULE = """\
Long changelog rule (e.g. openclaw/openclaw):
- Capture header + partial notes from the **initial** detail view, then **End** for Assets — \
do not scroll step-by-step through hundreds of bullets.
- If you already scrolled into the mid-changelog by mistake, **do not** scroll up/down \
repeatedly — press **End** once to reach Assets, then emit done with partial notes from \
memory of the top of the page.
- **Never alternate scroll-up and scroll-down** hunting for Assets.
"""

PROMPT_STOP_CONDITION = """\
Stop condition:
- Emit done only after **press_key End** on the release detail page (or Assets were visible \
without End) and downloads[] is filled from Assets **or** tag-based archive URLs.
- release_notes may be **partial** (top-of-page transcript). repository, latest_release, \
version, tag, author, published_at must be populated.
"""


def is_release_list_page(url: str) -> bool:
    """True on /releases index, not on /releases/tag/... detail."""
    lower = url.lower()
    return "/releases" in lower and "/releases/tag/" not in lower


def is_release_detail_page(url: str) -> bool:
    """True on a single-release detail page (/releases/tag/...)."""
    return "/releases/tag/" in url.lower()


def history_used_end_key(history: list[Action]) -> bool:
    """True if the agent already pressed End (jump to Assets) this run."""
    for action in history:
        if isinstance(action, PressKeyAction):
            normalized = action.key.strip().lower().replace(" ", "")
            if normalized in _END_KEY_ALIASES:
                return True
    return False


def claims_no_assets(done: DoneAction) -> bool:
    """True when reasoning clearly states the release has no Assets section."""
    reasoning = done.reasoning.lower()
    if any(marker in reasoning for marker in NO_ASSETS_REASONING_MARKERS):
        return True
    if "assets" in reasoning and any(
        word in reasoning for word in ("absent", "empty", "none", "missing")
    ):
        return True
    return False


def has_blank_required_fields(done: DoneAction) -> bool:
    """True when any required string field on done is empty."""
    from agent.schema import REQUIRED_STRING_FIELDS

    return not all(getattr(done, field).strip() for field in REQUIRED_STRING_FIELDS)


def done_rejection_reason(url: str, history: list[Action], done: DoneAction) -> str | None:
    """Human-readable reason to reject done, or None if the action is acceptable."""
    if is_release_list_page(url):
        return (
            "Model returned done from the releases list page. "
            "Click the topmost release on the list to open its detail page first."
        )
    if has_blank_required_fields(done):
        return (
            "Model returned done with incomplete extraction "
            "(blank required release fields)"
        )
    if done.downloads:
        return None
    if is_release_detail_page(url) and not history_used_end_key(history):
        return (
            "Model returned done on release detail without pressing End to reach Assets. "
            "Use press_key End once, read the Assets section, then emit done."
        )
    if not claims_no_assets(done):
        return (
            "Model returned done with empty downloads. "
            "Populate downloads[] from Assets, or state clearly in reasoning that no Assets "
            "section exists."
        )
    return None


def scroll_oscillation_instruction(history: list[Action]) -> str | None:
    """Detect up/down scroll ping-pong on long changelogs."""
    directions = [a.direction for a in history if isinstance(a, ScrollAction)]
    if len(directions) < 4:
        return None
    recent = directions[-4:]
    if recent[0] == recent[2] and recent[1] == recent[3] and recent[0] != recent[1]:
        return NUDGE_SCROLL_OSCILLATION
    return None


def scroll_budget_instruction(history: list[Action]) -> str | None:
    """Nudge End after many scrolls in the release detail view."""
    scroll_count = sum(1 for a in history if isinstance(a, ScrollAction))
    if scroll_count < 5:
        return None
    return NUDGE_SCROLL_BUDGET


def build_extra_instruction(
    history: list[Action],
    stale_streak: int,
    *,
    no_progress_streak: int,
    no_progress_message: str,
) -> str | None:
    """Compose optional system notes for the vision model this turn."""
    parts: list[str] = []
    if msg := scroll_oscillation_instruction(history):
        parts.append(msg)
    elif msg := scroll_budget_instruction(history):
        parts.append(msg)
    elif stale_streak >= no_progress_streak:
        parts.append(no_progress_message)
    return "\n\n".join(parts) if parts else None
