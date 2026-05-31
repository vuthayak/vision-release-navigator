# Phase 04 — Agent loop

## Goal

Glue `Browser` and `VisionClient` together in `agent/loop.py`. This is the heart of the tool: screenshot → decide → act → repeat → return the `done` payload.

## Status

- **State**: Done
- **Started**: 2026-05-28
- **Completed**: 2026-05-30

## Deliverables

- `agent/loop.py` exposing:
  ```python
  def run_agent_loop(
      browser: Browser,
      vision: VisionClient,
      user_prompt: str,
      max_steps: int = 25,
      time_budget_s: float = 420.0,
      debug_dir: Path | None = None,
      debug_vision: bool = False,
  ) -> DoneAction: ...
  ```
- `AgentLoopError` for max steps, time budget, and blank `done`.

## Tasks

- [x] Implement the loop body:
  1. `png = browser.screenshot()`
  2. `action = vision.decide_next_action(png, user_prompt, history, browser.current_url())`
  3. dispatch on `action.action`:
     - `click` → `browser.click(x, y)`
     - `type` → `browser.type_text(text)`
     - `press_key` → `browser.press_key(key)`
     - `scroll` → `browser.scroll(direction, amount)`
     - `wait` → `browser.wait(ms)`
     - `done` → return it.
  4. append to history (trim to last N=6).
  5. enforce step + time caps.
- [x] When `debug_dir` is set, write `step_NN.png` and `step_NN.json` (raw `action.model_dump()`) every iteration.
- [x] Add a no-progress heuristic: if URL **and** screenshot hash haven't changed for 3 consecutive steps **and** the action isn't `wait`, inject a synthetic note into the next prompt: "The page hasn't changed for the last 3 actions; try scrolling or reconsidering."
- [x] Detect `done` payloads where all five fields are blank → treat as model give-up, raise a clear error.

## Acceptance criteria

- With a stubbed `VisionClient` that returns a hand-rolled action sequence ending in `done`, the loop returns the `DoneAction` and writes the expected debug artifacts.
- The loop never imports `playwright` or the vision SDK directly (only via the two wrappers).
- Hitting `max_steps` raises a descriptive exception (not a silent return).

## Dependencies

- Phase 02 (`Browser`).
- Phase 03 (`VisionClient`).

## Risks

- **Infinite click loops** on a misidentified button. Mitigated by the step cap, time budget, and no-progress heuristic.
- **Screenshot hashing** for the no-progress check is a heuristic — perceptual hash (`imagehash.phash`) would be more robust but adds a dependency. Start with `hashlib.sha256(png).hexdigest()` and revisit if false negatives are common.
- **Long pages**: the model only sees the viewport. The system prompt instructs it to scroll; if it still misses things, future iteration can stitch multi-section screenshots.

## Notes

- Keep this file thin (~120 lines). Anything domain-specific (e.g. "if URL contains /releases…") goes in the system prompt, not here. The loop should remain reusable for non-GitHub tasks.
- The "no-progress" nudge is the one bit of explicit task knowledge the loop holds, and it's generic across sites.
