"""Task 30 — Performance Metrics Collector.

Reads browser performance timing data (Navigation Timing API + Web Vitals
approximations) from the current page.

Metrics collected
-----------------
- DNS lookup time
- TCP connect time
- TTFB (Time to First Byte)
- DOM interactive time
- DOM content loaded time
- Load event time (page load)
- First Contentful Paint (FCP) via PerformanceObserver/entry
- Largest Contentful Paint (LCP) — approximated from paint entries
- JS heap used (MB)

All times are in milliseconds relative to navigation start.
"""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.async_api import Page

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PerformanceMetrics:
    """Captured performance metrics for one page load."""

    route: str
    dns_ms: float
    tcp_connect_ms: float
    ttfb_ms: float
    dom_interactive_ms: float
    dom_content_loaded_ms: float
    load_event_ms: float
    fcp_ms: float  # First Contentful Paint (-1 if unavailable)
    lcp_ms: float  # Largest Contentful Paint approx (-1 if unavailable)
    js_heap_used_mb: float


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def capture_performance(page: Page, route: str) -> PerformanceMetrics:
    """Collect performance timing metrics from the current page.

    Reads window.performance.timing (Navigation Timing Level 1) and
    PerformancePaintTiming entries for FCP.

    Args:
        page:  Active Playwright page (fully loaded).
        route: Human-readable route label.

    Returns:
        Immutable ``PerformanceMetrics`` instance.
    """
    timing: dict[str, float] = await page.evaluate(
        """
        () => {
            const t = performance.timing;
            const nav_start = t.navigationStart;
            return {
                dns:    t.domainLookupEnd   - t.domainLookupStart,
                tcp:    t.connectEnd        - t.connectStart,
                ttfb:   t.responseStart     - t.requestStart,
                dom_interactive: t.domInteractive - nav_start,
                dom_content_loaded: t.domContentLoadedEventEnd - nav_start,
                load:   t.loadEventEnd      - nav_start,
            };
        }
        """
    )

    # FCP from paint entries
    fcp_ms: float = await page.evaluate(
        """
        () => {
            const entries = performance.getEntriesByType('paint');
            const fcp = entries.find(e => e.name === 'first-contentful-paint');
            return fcp ? fcp.startTime : -1;
        }
        """
    )

    # LCP — approximation from largest-contentful-paint entry type
    lcp_ms: float = await page.evaluate(
        """
        () => {
            try {
                const entries =
                    performance.getEntriesByType('largest-contentful-paint');
                if (entries.length > 0) return entries[entries.length - 1].startTime;
            } catch (e) {}
            return -1;
        }
        """
    )

    # JS heap (Chrome-only, graceful fallback)
    heap_mb: float = await page.evaluate(
        """
        () => {
            if (performance.memory) {
                return performance.memory.usedJSHeapSize / (1024 * 1024);
            }
            return -1;
        }
        """
    )

    metrics = PerformanceMetrics(
        route=route,
        dns_ms=round(timing.get("dns", 0.0), 2),
        tcp_connect_ms=round(timing.get("tcp", 0.0), 2),
        ttfb_ms=round(timing.get("ttfb", 0.0), 2),
        dom_interactive_ms=round(timing.get("dom_interactive", 0.0), 2),
        dom_content_loaded_ms=round(timing.get("dom_content_loaded", 0.0), 2),
        load_event_ms=round(timing.get("load", 0.0), 2),
        fcp_ms=round(fcp_ms, 2),
        lcp_ms=round(lcp_ms, 2),
        js_heap_used_mb=round(heap_mb, 2),
    )

    logger.info(
        "runtime.performance: route=%s load=%.0f ms fcp=%.0f ms",
        route,
        metrics.load_event_ms,
        metrics.fcp_ms,
    )
    return metrics
