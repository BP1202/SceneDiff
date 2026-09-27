"""Task 23 / 24 — Playwright browser launcher and isolated session manager.

Responsibilities
----------------
- Launch a headless Chromium browser via Playwright.
- Create per-commit isolated browser contexts (no shared cookies/cache).
- Provide async context managers for safe teardown.
- Enforce minimal permissions and controlled viewport.

Security rules
--------------
- Each context is fully isolated: separate storage, cookies, cache.
- Downloads are disabled to prevent accidental file writes.
- Geolocation, notifications, camera, microphone — all denied.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.async_api import Browser, BrowserContext, Page, ViewportSize

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Browser configuration constants
# ---------------------------------------------------------------------------

_VIEWPORT: ViewportSize = {"width": 1280, "height": 720}
_TIMEOUT_MS = 30_000  # 30 s default navigation timeout

_DENIED_PERMISSIONS: list[str] = [
    "geolocation",
    "notifications",
    "camera",
    "microphone",
    "clipboard-read",
    "clipboard-write",
]


# ---------------------------------------------------------------------------
# Task 23 — Playwright launcher
# ---------------------------------------------------------------------------


@asynccontextmanager
async def launch_browser() -> AsyncGenerator[Browser, None]:
    """Async context manager that launches and tears down a Chromium browser.

    Usage::

        async with launch_browser() as browser:
            ...

    Yields:
        Playwright ``Browser`` instance (Chromium, headless).
    """
    from playwright.async_api import async_playwright

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-extensions",
            ],
        )
        logger.info("runtime.browser: Chromium launched")
        try:
            yield browser
        finally:
            await browser.close()
            logger.info("runtime.browser: Chromium closed")


# ---------------------------------------------------------------------------
# Task 24 — Isolated browser session manager
# ---------------------------------------------------------------------------


@asynccontextmanager
async def isolated_context(
    browser: Browser,
    commit_ref: str,
) -> AsyncGenerator[BrowserContext, None]:
    """Create a fully isolated browser context for a single commit.

    Each call returns a context with its own cookies, localStorage,
    sessionStorage, and cache.  No state leaks between base and head runs.

    Args:
        browser:    Active Playwright browser instance.
        commit_ref: Short commit SHA used for logging (e.g. "a3d9d7f").

    Yields:
        Playwright ``BrowserContext`` instance.
    """
    context = await browser.new_context(
        viewport=_VIEWPORT,
        accept_downloads=False,
        ignore_https_errors=False,
        java_script_enabled=True,
        permissions=[],  # deny all
    )
    context.set_default_timeout(_TIMEOUT_MS)
    context.set_default_navigation_timeout(_TIMEOUT_MS)

    logger.info("runtime.browser: isolated context created commit=%s", commit_ref)
    try:
        yield context
    finally:
        await context.close()
        logger.info("runtime.browser: context closed commit=%s", commit_ref)


@asynccontextmanager
async def new_page(context: BrowserContext) -> AsyncGenerator[Page, None]:
    """Open a new page inside a context and close it on exit.

    Args:
        context: Active Playwright browser context.

    Yields:
        Playwright ``Page`` instance.
    """
    page = await context.new_page()
    try:
        yield page
    finally:
        await page.close()
