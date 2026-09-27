"""Task 28 — Storage Collector (LocalStorage / SessionStorage / Cookies).

Captures browser storage state at a given point in the user journey.

Security rules
--------------
- Cookie VALUES are always redacted (name preserved for structure comparison).
- localStorage / sessionStorage values are scanned by Secret Shield before
  inclusion in the artifact.
- No raw credentials ever leave this module unmasked.
"""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import TYPE_CHECKING

from app.services.secret_shield import mask_string

if TYPE_CHECKING:
    from playwright.async_api import BrowserContext, Page

logger = logging.getLogger(__name__)

_REDACTED = "[REDACTED]"


@dataclass(frozen=True)
class CookieRecord:
    """A single browser cookie (value always redacted)."""

    name: str
    domain: str
    path: str
    http_only: bool
    secure: bool
    same_site: str
    # value intentionally omitted — always [REDACTED]
    value: str = _REDACTED


@dataclass(frozen=True)
class StorageSnapshot:
    """Browser storage state at one point in the session."""

    route: str
    local_storage: dict[str, str]  # values Secret-Shield-masked
    session_storage: dict[str, str]  # values Secret-Shield-masked
    cookies: tuple[CookieRecord, ...]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def capture_storage_snapshot(
    page: Page,
    context: BrowserContext,
    route: str,
) -> StorageSnapshot:
    """Capture storage state for the current page.

    Args:
        page:    Active Playwright page.
        context: Active Playwright browser context (for cookie access).
        route:   Human-readable label for this checkpoint.

    Returns:
        Immutable ``StorageSnapshot`` with all sensitive values masked.
    """
    # localStorage
    raw_local: dict[str, str] = await page.evaluate(
        """
        () => {
            const result = {};
            for (let i = 0; i < localStorage.length; i++) {
                const key = localStorage.key(i);
                if (key !== null) result[key] = localStorage.getItem(key) || '';
            }
            return result;
        }
        """
    )
    safe_local = {k: mask_string(v) for k, v in raw_local.items()}

    # sessionStorage
    raw_session: dict[str, str] = await page.evaluate(
        """
        () => {
            const result = {};
            for (let i = 0; i < sessionStorage.length; i++) {
                const key = sessionStorage.key(i);
                if (key !== null) result[key] = sessionStorage.getItem(key) || '';
            }
            return result;
        }
        """
    )
    safe_session = {k: mask_string(v) for k, v in raw_session.items()}

    # Cookies — name/domain/path/flags only, value always redacted
    raw_cookies = await context.cookies()
    cookie_records = tuple(
        CookieRecord(
            name=c.get("name", ""),
            domain=c.get("domain", ""),
            path=c.get("path", "/"),
            http_only=bool(c.get("httpOnly", False)),
            secure=bool(c.get("secure", False)),
            same_site=str(c.get("sameSite", "None")),
        )
        for c in raw_cookies
    )

    snapshot = StorageSnapshot(
        route=route,
        local_storage=safe_local,
        session_storage=safe_session,
        cookies=cookie_records,
    )

    logger.info(
        "runtime.storage: captured route=%s local=%d session=%d cookies=%d",
        route,
        len(safe_local),
        len(safe_session),
        len(cookie_records),
    )
    return snapshot
