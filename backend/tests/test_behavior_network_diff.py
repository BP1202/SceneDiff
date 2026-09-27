"""Tests for behavior/network_diff.py — Network Diff Engine (Sprint 4)."""

from __future__ import annotations

from app.behavior.network_diff import compare_network_events
from app.behavior.severity import SeverityLevel


class TestNetworkDiff:
    def test_status_code_500_triggers_critical(self) -> None:
        base = [
            {
                "method": "POST",
                "url": "http://app/api/login",
                "status_code": 200,
                "latency_ms": 100,
            }
        ]
        head = [
            {
                "method": "POST",
                "url": "http://app/api/login",
                "status_code": 500,
                "latency_ms": 120,
            }
        ]

        diffs = compare_network_events(base, head)
        err = [d for d in diffs if d.event_type == "STATUS_CODE_5XX_INTRODUCED"]
        assert len(err) == 1
        assert err[0].severity == SeverityLevel.CRITICAL
        assert "HTTP 500" in err[0].title

    def test_status_code_404_triggers_high(self) -> None:
        base = [
            {
                "method": "GET",
                "url": "http://app/api/data",
                "status_code": 200,
                "latency_ms": 50,
            }
        ]
        head = [
            {
                "method": "GET",
                "url": "http://app/api/data",
                "status_code": 404,
                "latency_ms": 60,
            }
        ]

        diffs = compare_network_events(base, head)
        err = [d for d in diffs if d.event_type == "STATUS_CODE_4XX_INTRODUCED"]
        assert len(err) == 1
        assert err[0].severity == SeverityLevel.HIGH

    def test_hard_network_failure_triggers_critical(self) -> None:
        base = [
            {
                "method": "GET",
                "url": "http://app/api/ping",
                "status_code": 200,
                "failed": False,
            }
        ]
        head = [
            {
                "method": "GET",
                "url": "http://app/api/ping",
                "status_code": 0,
                "failed": True,
            }
        ]

        diffs = compare_network_events(base, head)
        err = [d for d in diffs if d.event_type == "NETWORK_REQUEST_FAILED"]
        assert len(err) == 1
        assert err[0].severity == SeverityLevel.CRITICAL

    def test_latency_regression_triggers_medium(self) -> None:
        base = [
            {
                "method": "GET",
                "url": "http://app/api/search",
                "status_code": 200,
                "latency_ms": 100,
            }
        ]
        head = [
            {
                "method": "GET",
                "url": "http://app/api/search",
                "status_code": 200,
                "latency_ms": 450,
            }
        ]

        diffs = compare_network_events(base, head)
        lat = [d for d in diffs if d.event_type == "LATENCY_REGRESSION"]
        assert len(lat) == 1
        assert lat[0].severity == SeverityLevel.MEDIUM

    def test_endpoint_missing_triggers_high(self) -> None:
        base = [{"method": "GET", "url": "http://app/api/auth/me", "status_code": 200}]
        head = []

        diffs = compare_network_events(base, head)
        missing = [d for d in diffs if d.event_type == "ENDPOINT_CALL_MISSING"]
        assert len(missing) == 1
        assert missing[0].severity == SeverityLevel.HIGH

    def test_url_with_secret_is_masked(self) -> None:
        base = []
        head = [
            {
                "method": "GET",
                "url": "http://app/api?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.abc.def",
                "status_code": 500,
            }
        ]

        diffs = compare_network_events(base, head)
        assert len(diffs) == 1
        assert "[REDACTED]" in diffs[0].evidence["url"]
