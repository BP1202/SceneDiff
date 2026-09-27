"""Tests for runtime/browser.py — Playwright launcher (Tasks 23, 24).

All tests mock Playwright so no Chromium binary is needed during testing.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.runtime.browser import isolated_context, launch_browser, new_page


class TestLaunchBrowser:
    @pytest.mark.asyncio()
    async def test_launch_and_close_lifecycle(self) -> None:
        mock_browser = AsyncMock()
        mock_pw = MagicMock()
        mock_pw.chromium.launch = AsyncMock(return_value=mock_browser)

        @asynccontextmanager
        async def _mock_playwright():
            yield mock_pw

        with patch("playwright.async_api.async_playwright", side_effect=_mock_playwright):
            async with launch_browser() as browser:
                assert browser is mock_browser
                mock_pw.chromium.launch.assert_awaited_once_with(
                    headless=True,
                    args=[
                        "--no-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-gpu",
                        "--disable-extensions",
                    ],
                )

        mock_browser.close.assert_awaited_once()

    @pytest.mark.asyncio()
    async def test_browser_closes_on_exception(self) -> None:
        mock_browser = AsyncMock()
        mock_pw = MagicMock()
        mock_pw.chromium.launch = AsyncMock(return_value=mock_browser)

        @asynccontextmanager
        async def _mock_playwright():
            yield mock_pw

        with (
            patch("playwright.async_api.async_playwright", side_effect=_mock_playwright),
            pytest.raises(RuntimeError, match="test error"),
        ):
            async with launch_browser():
                raise RuntimeError("test error")

        mock_browser.close.assert_awaited_once()


class TestIsolatedContext:
    @pytest.mark.asyncio()
    async def test_isolated_context_parameters(self) -> None:
        mock_context = AsyncMock()
        mock_context.set_default_timeout = MagicMock()
        mock_context.set_default_navigation_timeout = MagicMock()
        mock_browser = MagicMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)

        async with isolated_context(mock_browser, "a1b2c3d") as ctx:
            assert ctx is mock_context
            mock_browser.new_context.assert_awaited_once_with(
                viewport={"width": 1280, "height": 720},
                accept_downloads=False,
                ignore_https_errors=False,
                java_script_enabled=True,
                permissions=[],
            )
            mock_context.set_default_timeout.assert_called_once_with(30_000)
            mock_context.set_default_navigation_timeout.assert_called_once_with(30_000)

        mock_context.close.assert_awaited_once()

    @pytest.mark.asyncio()
    async def test_isolated_context_closes_on_error(self) -> None:
        mock_context = AsyncMock()
        mock_context.set_default_timeout = MagicMock()
        mock_context.set_default_navigation_timeout = MagicMock()
        mock_browser = MagicMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)

        with pytest.raises(ValueError, match="context fail"):
            async with isolated_context(mock_browser, "a1b2c3d"):
                raise ValueError("context fail")

        mock_context.close.assert_awaited_once()


class TestNewPage:
    @pytest.mark.asyncio()
    async def test_new_page_lifecycle(self) -> None:
        mock_page = AsyncMock()
        mock_context = MagicMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)

        async with new_page(mock_context) as page:
            assert page is mock_page
            mock_context.new_page.assert_awaited_once()

        mock_page.close.assert_awaited_once()

    @pytest.mark.asyncio()
    async def test_new_page_closes_on_error(self) -> None:
        mock_page = AsyncMock()
        mock_context = MagicMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)

        with pytest.raises(RuntimeError, match="page crash"):
            async with new_page(mock_context):
                raise RuntimeError("page crash")

        mock_page.close.assert_awaited_once()
