"""Tests for normalized-to-pixel coordinate conversion."""

from __future__ import annotations

import sys
from types import ModuleType
from unittest.mock import MagicMock


def _install_playwright_stub() -> None:
    if "playwright.sync_api" in sys.modules:
        return
    sync_api = ModuleType("playwright.sync_api")
    sync_api.BrowserContext = MagicMock()
    sync_api.Page = MagicMock()
    sync_api.TimeoutError = type("TimeoutError", (Exception,), {})
    sync_api.sync_playwright = MagicMock()
    playwright = ModuleType("playwright")
    playwright.sync_api = sync_api
    sys.modules["playwright"] = playwright
    sys.modules["playwright.sync_api"] = sync_api


_install_playwright_stub()

from agent.browser import Browser  # noqa: E402


def test_denorm_center_of_default_viewport() -> None:
    browser = Browser(viewport=(1280, 800))
    assert browser._denorm(500, 500) == (640, 400)


def test_denorm_clamps_to_viewport_minus_one() -> None:
    browser = Browser(viewport=(1280, 800))
    assert browser._denorm(1000, 1000) == (1279, 799)


def test_press_key_back_uses_page_history() -> None:
    browser = Browser(viewport=(1280, 800))
    page = MagicMock()
    browser._page = page

    browser.press_key("Back")

    page.go_back.assert_called_once_with(wait_until="domcontentloaded")
    page.keyboard.press.assert_not_called()


def test_press_key_end_scrolls_to_bottom() -> None:
    browser = Browser(viewport=(1280, 800))
    page = MagicMock()
    browser._page = page

    browser.press_key("End")

    page.evaluate.assert_called_once_with(
        "window.scrollTo(0, document.body.scrollHeight)"
    )
    page.keyboard.press.assert_not_called()
