"""Task 25 — DOM Snapshot Collector.

Captures the DOM state of a page at a given moment: element counts,
structure summary, text content samples, visibility states, and the full
HTML snapshot.

Design rules
------------
- No AI inference — only deterministic DOM traversal via Playwright.
- Returns immutable dataclasses, never raw Playwright handles.
- Large HTML is trimmed to _MAX_HTML_BYTES to prevent oversized artifacts.
"""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.async_api import Page

logger = logging.getLogger(__name__)

_MAX_HTML_BYTES = 512_000  # 512 KB cap on raw HTML


@dataclass(frozen=True)
class DomSnapshot:
    """Immutable DOM snapshot artifact for one page route."""

    route: str
    title: str
    element_count: int
    button_count: int
    form_count: int
    input_count: int
    link_count: int
    image_count: int
    hidden_element_count: int
    text_sample: str  # first 2 KB of body text
    html_snapshot: str  # full HTML, capped at _MAX_HTML_BYTES


@dataclass(frozen=True)
class DomCollectorResult:
    """Collection result for one commit / route pair."""

    commit_ref: str
    snapshots: tuple[DomSnapshot, ...]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def capture_dom_snapshot(page: Page, route: str) -> DomSnapshot:
    """Capture a DOM snapshot of the current page state.

    Args:
        page:  Active Playwright page (already navigated).
        route: Human-readable route label (e.g. "/dashboard").

    Returns:
        Immutable ``DomSnapshot`` describing the current DOM.
    """
    title = await page.title()

    # Aggregate counts via JS evaluation (single round-trip each)
    element_count: int = await page.evaluate("document.querySelectorAll('*').length")
    button_count: int = await page.evaluate(
        "document.querySelectorAll('button, [role=button]').length"
    )
    form_count: int = await page.evaluate("document.querySelectorAll('form').length")
    input_count: int = await page.evaluate(
        "document.querySelectorAll('input, textarea, select').length"
    )
    link_count: int = await page.evaluate("document.querySelectorAll('a[href]').length")
    image_count: int = await page.evaluate("document.querySelectorAll('img').length")
    hidden_count: int = await page.evaluate(
        """
        Array.from(document.querySelectorAll('*')).filter(el => {
            const s = window.getComputedStyle(el);
            return s.display === 'none' || s.visibility === 'hidden';
        }).length
        """
    )

    # Extract a small text sample from body
    body_text: str = await page.evaluate(
        "document.body ? document.body.innerText.slice(0, 2048) : ''"
    )

    # Full HTML snapshot — cap at _MAX_HTML_BYTES
    raw_html: str = await page.content()
    if len(raw_html.encode()) > _MAX_HTML_BYTES:
        raw_html = raw_html.encode()[:_MAX_HTML_BYTES].decode(errors="replace")
        logger.debug(
            "runtime.dom: HTML truncated to %d bytes for route=%s",
            _MAX_HTML_BYTES,
            route,
        )

    snapshot = DomSnapshot(
        route=route,
        title=title,
        element_count=element_count,
        button_count=button_count,
        form_count=form_count,
        input_count=input_count,
        link_count=link_count,
        image_count=image_count,
        hidden_element_count=hidden_count,
        text_sample=body_text,
        html_snapshot=raw_html,
    )
    logger.info(
        "runtime.dom: snapshot captured route=%s elements=%d",
        route,
        element_count,
    )
    return snapshot
