# Phase 02 — Playwright browser wrapper

## Goal

Build `agent/browser.py` — the only file allowed to import Playwright. Its public surface deliberately excludes anything that resembles a CSS/XPath selector, enforcing the "no hardcoded selectors" rule at the architectural level.

## Status

- **State**: Done
- **Started**: 2026-05-28
- **Completed**: 2026-05-30

## Deliverables

A `Browser` class exposing:

- `start(headless: bool = False, viewport: tuple[int,int] = (1280, 800)) -> None`
- `goto(url: str) -> None`
- `screenshot() -> bytes` — current viewport only, PNG.
- `click(norm_x: int, norm_y: int) -> None` — coordinates in 0–1000 normalized space.
- `type_text(text: str) -> None` — types into currently focused element via `page.keyboard.type`.
- `press_key(key: str) -> None` — `Enter`, `Tab`, `Escape`, etc.
- `scroll(direction: Literal["up","down"], amount: int) -> None` — uses `page.mouse.wheel`.
- `wait(ms: int) -> None`.
- `current_url() -> str`.
- `viewport() -> tuple[int,int]`.
- `close() -> None`.

## Tasks

- [x] Create `agent/browser.py`.
- [x] Implement coordinate de-normalization helper:
  ```python
  def _denorm(self, nx: int, ny: int) -> tuple[int, int]:
      w, h = self._viewport
      return round(nx / 1000 * w), round(ny / 1000 * h)
  ```
- [x] After every action that can navigate (`click`, `press_key("Enter")`, `goto`), call `self._page.wait_for_load_state("networkidle", timeout=8000)` inside `try/except PlaywrightTimeoutError: pass`.
- [x] Use the sync Playwright API (`sync_playwright`) — simpler than async for a single-page CLI tool.
- [x] Accept `user_agent` override (default: a realistic desktop UA string) to avoid bot-detection edge cases.
- [x] Add a tiny `__main__` block that opens github.com, takes a screenshot to `screenshots/_browser_smoke.png`, prints viewport size, and closes — for manual sanity-check.

## Acceptance criteria

- `python -m agent.browser` opens a Chromium window, navigates to https://github.com, saves a PNG screenshot, prints `1280 800`, and exits 0.
- `rg "querySelector|locator\(|xpath|css=" agent/browser.py` returns no matches.
- Public methods accept only primitive types (no `Page`, no `ElementHandle` leak through).

## Dependencies

- Phase 01 (scaffold) must be done.

## Risks

- Playwright's `mouse.click` ignores element-level event handlers in some SPAs. Fallback: `page.mouse.move(x, y); page.mouse.down(); page.mouse.up()`.
- Some GitHub interactions trigger client-side route changes without firing `networkidle`. The `wait_for_load_state` swallow-on-timeout pattern handles this gracefully.
- High-DPI displays can shift coordinates. Force `device_scale_factor=1` when creating the context.

## Notes

- Keep this file ruthlessly small. Anything that smells like "find the search box" belongs in the vision layer, not here.
- Resist the temptation to add `find_element_by_text` helpers — they'd reintroduce the very selector coupling we're avoiding.
