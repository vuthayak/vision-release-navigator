"""Agent orchestration loop."""

from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

from agent.browser import Browser
from agent.github_release import build_extra_instruction, done_rejection_reason
from agent.schema import (
    Action,
    ClickAction,
    DoneAction,
    PressKeyAction,
    ScrollAction,
    TypeAction,
    WaitAction,
)
from agent.vision import VisionClient

HISTORY_LIMIT = 6  # Keep recent turns in the prompt without blowing context size.
NO_PROGRESS_STREAK = 3  # Nudge the model after this many identical screenshot+URL pairs.


class AgentLoopError(Exception):
    """Raised when the agent cannot complete the task."""


def _screenshot_hash(png: bytes) -> str:
    # Cheap change detector — same hash + URL means the last action had no visible effect.
    return hashlib.sha256(png).hexdigest()


def _no_progress_instruction(streak: int) -> str:
    return (
        f"The page has not changed for the last {streak} actions. "
        "Try scrolling, clicking a different control, or reconsider your approach."
    )


def _write_debug_artifacts(
    debug_dir: Path, step: int, png: bytes, action: Action
) -> None:
    print(
        f"[step {step:02d}] {action.action}: {action.reasoning[:120]}",
        file=sys.stderr,
    )
    debug_dir.mkdir(parents=True, exist_ok=True)
    stem = f"step_{step:02d}"
    (debug_dir / f"{stem}.png").write_bytes(png)
    (debug_dir / f"{stem}.json").write_text(
        json.dumps(action.model_dump(), indent=2),
        encoding="utf-8",
    )


def _apply_action(browser: Browser, action: Action) -> None:
    # Pattern-match dispatches to browser primitives; DoneAction is handled before this runs.
    match action:
        case ClickAction():
            browser.click(action.x, action.y)
        case TypeAction():
            browser.type_text(action.text)
        case PressKeyAction():
            browser.press_key(action.key)
        case ScrollAction():
            browser.scroll(action.direction, action.amount)
        case WaitAction():
            browser.wait(action.ms)
        case DoneAction():
            raise AgentLoopError("internal error: done action reached dispatch")
        case _:
            raise AgentLoopError(f"Unknown action type: {type(action).__name__}")


def run_agent_loop(
    browser: Browser,
    vision: VisionClient,
    user_prompt: str,
    max_steps: int = 30,
    time_budget_s: float = 420.0,
    debug_dir: Path | None = None,
    debug_vision: bool = False,
) -> DoneAction:
    history: list[Action] = []
    start = time.monotonic()
    last_url: str | None = None
    last_hash: str | None = None
    stale_streak = 0
    extra_instruction: str | None = None

    for step in range(1, max_steps + 1):
        if time.monotonic() - start > time_budget_s:
            raise AgentLoopError(
                f"Time budget exceeded ({time_budget_s:.0f}s) after {step - 1} steps"
            )

        # 1. Observe current page state.
        png = browser.screenshot()
        url = browser.current_url()
        shot_hash = _screenshot_hash(png)

        # 2. Detect stale loops (same pixels after a non-wait action).
        if (
            last_url == url
            and last_hash == shot_hash
            and history
            and history[-1].action != "wait"
        ):
            stale_streak += 1
        else:
            stale_streak = 0

        last_url = url
        last_hash = shot_hash

        extra_instruction = build_extra_instruction(
            history,
            stale_streak,
            no_progress_streak=NO_PROGRESS_STREAK,
            no_progress_message=_no_progress_instruction(NO_PROGRESS_STREAK),
        )

        # 3. Ask the vision model for the next action.
        action = vision.decide_next_action(
            png,
            user_prompt,
            history,
            url,
            extra_instruction=extra_instruction,
            debug=debug_vision,
        )

        if debug_dir:
            _write_debug_artifacts(debug_dir, step, png, action)

        if isinstance(action, DoneAction):
            if reason := done_rejection_reason(url, history, action):
                raise AgentLoopError(reason)
            return action

        # 4. Execute navigation action and record it for the next turn.
        _apply_action(browser, action)

        history.append(action)
        if len(history) > HISTORY_LIMIT:
            history = history[-HISTORY_LIMIT:]

    raise AgentLoopError(f"Max steps ({max_steps}) reached without done action")
