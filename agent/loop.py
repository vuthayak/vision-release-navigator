"""Agent orchestration loop."""

from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

from agent.browser import Browser
from agent.vision import Action, DoneAction, VisionClient

HISTORY_LIMIT = 6
NO_PROGRESS_STREAK = 3


class AgentLoopError(Exception):
    """Raised when the agent cannot complete the task."""


def _screenshot_hash(png: bytes) -> str:
    return hashlib.sha256(png).hexdigest()


def _is_blank_done(action: DoneAction) -> bool:
    v1_fields = (
        action.repository,
        action.latest_release,
        action.version,
        action.tag,
        action.author,
    )
    if not any(f.strip() for f in v1_fields):
        return True
    if not action.published_at.strip():
        return True
    if not action.release_notes.strip():
        return True
    return False


def run_agent_loop(
    browser: Browser,
    vision: VisionClient,
    user_prompt: str,
    max_steps: int = 30,
    time_budget_s: float = 180.0,
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
            extra_instruction = (
                "The page has not changed for the last 3 actions. "
                "Try scrolling, clicking a different control, or reconsider your approach."
            )
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
            print(f"[step {step:02d}] {action.action}: {action.reasoning[:120]}", file=sys.stderr)
            debug_dir.mkdir(parents=True, exist_ok=True)
            stem = f"step_{step:02d}"
            (debug_dir / f"{stem}.png").write_bytes(png)
            payload = action.model_dump()
            (debug_dir / f"{stem}.json").write_text(
                json.dumps(payload, indent=2), encoding="utf-8"
            )

        if action.action == "done":
            if _is_blank_done(action):
                raise AgentLoopError(
                    "Model returned done with incomplete extraction (blank v1 or v2 fields)"
                )
            return action

        if action.action == "click":
            browser.click(action.x, action.y)
        elif action.action == "type":
            browser.type_text(action.text)
        elif action.action == "press_key":
            browser.press_key(action.key)
        elif action.action == "scroll":
            browser.scroll(action.direction, action.amount)
        elif action.action == "wait":
            browser.wait(action.ms)

        history.append(action)
        if len(history) > HISTORY_LIMIT:
            history = history[-HISTORY_LIMIT:]

    raise AgentLoopError(f"Max steps ({max_steps}) reached without done action")
