"""Tests for behavior/performance_diff.py — Performance Diff Engine (Sprint 4)."""

from __future__ import annotations

from app.behavior.performance_diff import compare_performance_metrics
from app.behavior.severity import SeverityLevel


class TestPerformanceDiff:
    def test_page_load_regression_triggers_medium(self) -> None:
        base = [
            {
                "route": "/home",
                "load_event_ms": 1000.0,
                "fcp_ms": 300.0,
                "lcp_ms": 600.0,
                "js_heap_used_mb": 15.0,
            }
        ]
        head = [
            {
                "route": "/home",
                "load_event_ms": 1400.0,
                "fcp_ms": 300.0,
                "lcp_ms": 600.0,
                "js_heap_used_mb": 15.0,
            }
        ]

        diffs = compare_performance_metrics(base, head)
        load_diffs = [d for d in diffs if d.event_type == "PAGE_LOAD_REGRESSION"]
        assert len(load_diffs) == 1
        assert load_diffs[0].severity == SeverityLevel.MEDIUM
        assert "increased by 40%" in load_diffs[0].title

    def test_severe_page_load_regression_triggers_high(self) -> None:
        base = [{"route": "/home", "load_event_ms": 800.0}]
        head = [{"route": "/home", "load_event_ms": 2200.0}]

        diffs = compare_performance_metrics(base, head)
        load_diffs = [d for d in diffs if d.event_type == "PAGE_LOAD_REGRESSION"]
        assert len(load_diffs) == 1
        assert load_diffs[0].severity == SeverityLevel.HIGH

    def test_lcp_regression_triggers_medium(self) -> None:
        base = [{"route": "/catalog", "load_event_ms": 1000.0, "lcp_ms": 800.0}]
        head = [{"route": "/catalog", "load_event_ms": 1000.0, "lcp_ms": 1500.0}]

        diffs = compare_performance_metrics(base, head)
        lcp_diffs = [d for d in diffs if d.event_type == "LCP_REGRESSION"]
        assert len(lcp_diffs) == 1
        assert lcp_diffs[0].severity == SeverityLevel.MEDIUM

    def test_memory_leak_warning_triggers_medium(self) -> None:
        base = [
            {"route": "/dashboard", "load_event_ms": 500.0, "js_heap_used_mb": 20.0}
        ]
        head = [
            {"route": "/dashboard", "load_event_ms": 500.0, "js_heap_used_mb": 60.0}
        ]

        diffs = compare_performance_metrics(base, head)
        mem_diffs = [d for d in diffs if d.event_type == "MEMORY_LEAK_WARNING"]
        assert len(mem_diffs) == 1
        assert mem_diffs[0].severity == SeverityLevel.MEDIUM
