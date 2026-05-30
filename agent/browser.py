"""Playwright browser wrapper — no CSS/XPath selectors."""

from __future__ import annotations

import time
from typing import Literal

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)


class Browser:
    def __init__(self, user_agent: str = DEFAULT_USER_AGENT) -> None:
        self._user_agent = user_agent
        self._playwright = None
        self._browser = None
        self._page = None
        self._viewport: tuple[int, int] = (1280, 800)

    def _denorm(self, nx: int, ny: int) -> tuple[int, int]:
        w, h = self._viewport
        return round(nx / 1000 * w), round(ny / 1000 * h)

    def _wait_network_idle(self) -> None:
        if self._page is None:
            return
        try:
            self._page.wait_for_load_state("networkidle", timeout=8000)
        except PlaywrightTimeoutError:
            pass

    def start(self, headless: bool = False, viewport: tuple[int, int] = (1280, 800)) -> None:
        self._viewport = viewport
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=headless)
        context = self._browser.new_context(
            viewport={"width": viewport[0], "height": viewport[1]},
            user_agent=self._user_agent,
            device_scale_factor=1,
        )
        self._page = context.new_page()

    def goto(self, url: str) -> None:
        assert self._page is not None
        self._page.goto(url, wait_until="domcontentloaded")
        self._wait_network_idle()

    def screenshot(self) -> bytes:
        assert self._page is not None
        return self._page.screenshot(type="png")

    def click(self, norm_x: int, norm_y: int) -> None:
        assert self._page is not None
        x, y = self._denorm(norm_x, norm_y)
        self._page.mouse.click(x, y)
        self._wait_network_idle()

    def type_text(self, text: str) -> None:
        assert self._page is not None
        self._page.keyboard.type(text)

    def press_key(self, key: str) -> None:
        assert self._page is not None
        self._page.keyboard.press(key)
        if key.lower() in ("enter", "return"):
            self._wait_network_idle()

    def scroll(self, direction: Literal["up", "down"], amount: int) -> None:
        assert self._page is not None
        delta = amount * 120
        if direction == "up":
            delta = -delta
        self._page.mouse.wheel(0, delta)

    def wait(self, ms: int) -> None:
        time.sleep(ms / 1000.0)

    def current_url(self) -> str:
        assert self._page is not None
        return self._page.url

    def viewport(self) -> tuple[int, int]:
        return self._viewport

    def close(self) -> None:
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
    browser = Browser()
    browser.start(headless=True)
    try:
        browser.goto("https://github.com")
        path = out / "_browser_smoke.png"
        path.write_bytes(browser.screenshot())
        w, h = browser.viewport()
        print(f"{w} {h}")
        print(f"screenshot: {path}")
    finally:
        browser.close()
