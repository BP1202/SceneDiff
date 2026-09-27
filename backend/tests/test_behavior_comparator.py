"""Tests for behavior/comparator.py — Behavior Comparator Orchestrator (Sprint 4)."""

from __future__ import annotations

from app.behavior.comparator import compare_runtime_artifacts
from app.behavior.severity import ComparisonVerdict, SeverityLevel


def _sample_artifacts() -> tuple[dict, dict]:
    base = {
        "commit_ref": "1111111",
        "base_url": "http://localhost:3000",
        "routes_visited": ["/login", "/dashboard"],
        "dom_snapshots": [
            {
                "route": "/login",
                "button_count": 2,
                "form_count": 1,
                "element_count": 25,
                "title": "Login",
            },
            {
                "route": "/dashboard",
                "button_count": 5,
                "form_count": 0,
                "element_count": 80,
                "title": "Dashboard",
            },
        ],
        "network_events": [
            {
                "method": "POST",
                "url": "http://localhost:3000/api/auth",
                "status_code": 200,
                "latency_ms": 100,
            },
            {
                "method": "GET",
                "url": "http://localhost:3000/api/user",
                "status_code": 200,
                "latency_ms": 50,
            },
        ],
        "console_events": [],
        "storage_snapshots": [
            {
                "route": "/dashboard",
                "local_storage_keys": ["token"],
                "session_storage_keys": [],
                "cookie_names": ["session"],
            },
        ],
        "performance_metrics": [
            {"route": "/login", "load_event_ms": 500.0, "lcp_ms": 400.0},
            {"route": "/dashboard", "load_event_ms": 700.0, "lcp_ms": 600.0},
        ],
    }

    # Head introduces: 500 on /api/auth, console exception, submit button removed
    head = {
        "commit_ref": "2222222",
        "base_url": "http://localhost:3000",
        "routes_visited": ["/login", "/dashboard"],
        "dom_snapshots": [
            {
                "route": "/login",
                "button_count": 1,
                "form_count": 1,
                "element_count": 23,
                "title": "Login",
            },
            {
                "route": "/dashboard",
                "button_count": 5,
                "form_count": 0,
                "element_count": 80,
                "title": "Dashboard",
            },
        ],
        "network_events": [
            {
                "method": "POST",
                "url": "http://localhost:3000/api/auth",
                "status_code": 500,
                "latency_ms": 110,
            },
            {
                "method": "GET",
                "url": "http://localhost:3000/api/user",
                "status_code": 200,
                "latency_ms": 55,
            },
        ],
        "console_events": [
            {
                "level": "exception",
                "message": (
                    "Uncaught TypeError: Cannot read property 'token' of undefined"
                ),
                "source_url": "auth.js",
                "line_number": 42,
            },
        ],
        "storage_snapshots": [
            {
                "route": "/dashboard",
                "local_storage_keys": [],
                "session_storage_keys": [],
                "cookie_names": ["session"],
            },
        ],
        "performance_metrics": [
            {"route": "/login", "load_event_ms": 520.0, "lcp_ms": 410.0},
            {"route": "/dashboard", "load_event_ms": 710.0, "lcp_ms": 605.0},
        ],
    }
    return base, head


class TestComparatorEngine:
    def test_compare_runtime_artifacts_regression(self) -> None:
        base, head = _sample_artifacts()
        report = compare_runtime_artifacts(base, head, repository_name="SceneDiff")

        assert report.repository_name == "SceneDiff"
        assert report.base_commit == "1111111"
        assert report.head_commit == "2222222"
        assert report.verdict == ComparisonVerdict.REGRESSION
        assert report.highest_severity == SeverityLevel.CRITICAL

        assert report.summary.total_divergences > 0
        assert report.summary.critical_count >= 1  # 500 status code + exception
        assert report.summary.high_count >= 1  # button removed + token removed
        assert report.first_meaningful_divergence is not None
        assert report.first_meaningful_divergence.severity == SeverityLevel.CRITICAL

    def test_clean_artifacts_produce_clean_verdict(self) -> None:
        base, _ = _sample_artifacts()
        # Head identical to Base
        report = compare_runtime_artifacts(base, base, repository_name="SceneDiff")

        assert report.verdict == ComparisonVerdict.CLEAN
        assert report.highest_severity == SeverityLevel.INFO
        assert report.summary.total_divergences == 0
        assert report.first_meaningful_divergence is None

    def test_to_dict_serializable(self) -> None:
        import json

        base, head = _sample_artifacts()
        report = compare_runtime_artifacts(base, head)
        data = report.to_dict()

        serialized = json.dumps(data)
        assert "SceneDiff" in serialized
        assert "REGRESSION" in serialized
