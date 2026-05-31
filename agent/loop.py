"""Agent orchestration loop."""

from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

from agent.browser import Browser
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

HISTORY_LIMIT = 6
NO_PROGRESS_STREAK = 3


class AgentLoopError(Exception):
    """Raised when the agent cannot complete the task."""


def _screenshot_hash(png: bytes) -> str:
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

        png = browser.screenshot()
        url = browser.current_url()
        shot_hash = _screenshot_hash(png)

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

        if stale_streak >= NO_PROGRESS_STREAK:
            extra_instruction = _no_progress_instruction(NO_PROGRESS_STREAK)
        else:
            extra_instruction = None

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
            if action.is_incomplete_extraction():
                raise AgentLoopError(
                    "Model returned done with incomplete extraction "
                    "(blank v1/v2 fields or empty downloads without no-assets reasoning)"
                )
            return action

        _apply_action(browser, action)

        history.append(action)
        if len(history) > HISTORY_LIMIT:
            history = history[-HISTORY_LIMIT:]

    raise AgentLoopError(f"Max steps ({max_steps}) reached without done action")
