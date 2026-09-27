"""Tests for runtime/performance.py — Performance Metrics Collector (Task 30)."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from unittest.mock import AsyncMock

import pytest

from app.runtime.performance import capture_performance


def _make_page(
    timing: dict[str, float] | None = None,
    fcp: float = 240.5,
    lcp: float = 520.1,
    heap_mb: float = 18.4,
) -> AsyncMock:
    page = AsyncMock()
    nav_timing = (
        timing
        if timing is not None
        else {
            "dns": 12.3,
            "tcp": 25.1,
            "ttfb": 85.0,
            "dom_interactive": 210.0,
            "dom_content_loaded": 320.0,
            "load": 550.0,
        }
    )
    # evaluate is called in order: timing dict, fcp float, lcp float, heap float
    page.evaluate = AsyncMock(side_effect=[nav_timing, fcp, lcp, heap_mb])
    return page


class TestCapturePerformance:
    @pytest.mark.asyncio()
    async def test_capture_performance_metrics(self) -> None:
        page = _make_page()
        metrics = await capture_performance(page, "/dashboard")

        assert metrics.route == "/dashboard"
        assert metrics.dns_ms == 12.3
        assert metrics.tcp_connect_ms == 25.1
        assert metrics.ttfb_ms == 85.0
        assert metrics.dom_interactive_ms == 210.0
        assert metrics.dom_content_loaded_ms == 320.0
        assert metrics.load_event_ms == 550.0
        assert metrics.fcp_ms == 240.5
        assert metrics.lcp_ms == 520.1
        assert metrics.js_heap_used_mb == 18.4

    @pytest.mark.asyncio()
    async def test_fallback_when_metrics_unavailable(self) -> None:
        page = _make_page(timing={}, fcp=-1.0, lcp=-1.0, heap_mb=-1.0)
        metrics = await capture_performance(page, "/")

        assert metrics.dns_ms == 0.0
        assert metrics.fcp_ms == -1.0
        assert metrics.lcp_ms == -1.0
        assert metrics.js_heap_used_mb == -1.0

    @pytest.mark.asyncio()
    async def test_performance_metrics_is_frozen(self) -> None:
        page = _make_page()
        metrics = await capture_performance(page, "/")
        with pytest.raises(FrozenInstanceError):
            metrics.route = "mutated"  # type: ignore[misc]
