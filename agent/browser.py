"""Playwright browser wrapper — no CSS/XPath selectors."""

from __future__ import annotations

import time
from types import TracebackType
from typing import Literal

from playwright.sync_api import BrowserContext, Page, TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)
WHEEL_DELTA_PX = 120
_NAVIGATION_KEYS = frozenset({"enter", "return"})
_NETWORK_IDLE_TIMEOUT_MS = 8000


class Browser:
    def __init__(
        self,
        user_agent: str = DEFAULT_USER_AGENT,
        *,
        headless: bool = False,
        viewport: tuple[int, int] = (1280, 800),
    ) -> None:
        self._user_agent = user_agent
        self._headless = headless
        self._viewport = viewport
        self._playwright = None
        self._browser = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None

    def __enter__(self) -> Browser:
        self.start(headless=self._headless, viewport=self._viewport)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.close()

    def _require_page(self) -> Page:
        if self._page is None:
            raise RuntimeError(
                "Browser session not active; use 'with Browser(...) as browser:' or call start()"
            )
        return self._page

    def _denorm(self, nx: int, ny: int) -> tuple[int, int]:
        w, h = self._viewport
        return min(round(nx / 1000 * w), w - 1), min(round(ny / 1000 * h), h - 1)

    def _wait_network_idle(self) -> None:
        page = self._require_page()
        try:
            page.wait_for_load_state("networkidle", timeout=_NETWORK_IDLE_TIMEOUT_MS)
        except PlaywrightTimeoutError:
            pass

    def _after_action(self, *, wait_for_navigation: bool) -> None:
        if wait_for_navigation:
            self._wait_network_idle()

    def start(self, headless: bool = False, viewport: tuple[int, int] = (1280, 800)) -> None:
        if self._playwright is not None:
            raise RuntimeError("Browser session already active")
        self._headless = headless
        self._viewport = viewport
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=headless)
        self._context = self._browser.new_context(
            viewport={"width": viewport[0], "height": viewport[1]},
            user_agent=self._user_agent,
            device_scale_factor=1,
        )
        self._page = self._context.new_page()

    def goto(self, url: str) -> None:
        page = self._require_page()
        page.goto(url, wait_until="domcontentloaded")
        self._after_action(wait_for_navigation=True)

    def screenshot(self) -> bytes:
        return self._require_page().screenshot(type="png")

    def click(self, norm_x: int, norm_y: int) -> None:
        page = self._require_page()
        x, y = self._denorm(norm_x, norm_y)
        page.mouse.click(x, y)
        self._after_action(wait_for_navigation=True)

    def type_text(self, text: str) -> None:
        self._require_page().keyboard.type(text)

    def press_key(self, key: str) -> None:
        self._require_page().keyboard.press(key)
        self._after_action(wait_for_navigation=key.lower() in _NAVIGATION_KEYS)

    def scroll(self, direction: Literal["up", "down"], amount: int) -> None:
        page = self._require_page()
        delta = amount * WHEEL_DELTA_PX
        if direction == "up":
            delta = -delta
        page.mouse.wheel(0, delta)

    def wait(self, ms: int) -> None:
        time.sleep(ms / 1000.0)

    def current_url(self) -> str:
        return self._require_page().url

    def viewport(self) -> tuple[int, int]:
        return self._viewport

    def close(self) -> None:
        if self._context is not None:
            self._context.close()
            self._context = None
        if self._browser is not None:
            self._browser.close()
            self._browser = None
        if self._playwright is not None:
            self._playwright.stop()
            self._playwright = None
        self._page = None


if __name__ == "__main__":
    from pathlib import Path

    out = Path("screenshots")
    out.mkdir(parents=True, exist_ok=True)
    with Browser(headless=True) as browser:
        browser.goto("https://github.com")
        path = out / "_browser_smoke.png"
        path.write_bytes(browser.screenshot())
        w, h = browser.viewport()
        print(f"{w} {h}")
        print(f"screenshot: {path}")
