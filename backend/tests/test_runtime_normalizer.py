"""Tests for runtime/normalizer.py — Runtime Trace Normalizer (Task 31)."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from app.runtime.console import ConsoleEvent
from app.runtime.dom import DomSnapshot
from app.runtime.network import NetworkEvent
from app.runtime.normalizer import RuntimeTraceArtifact, normalize
from app.runtime.performance import PerformanceMetrics
from app.runtime.screenshots import ScreenshotArtifact
from app.runtime.storage import StorageSnapshot


def _make_dom(route: str = "/") -> DomSnapshot:
    return DomSnapshot(
        route=route,
        title="Test",
        element_count=50,
        button_count=2,
        form_count=1,
        input_count=2,
        link_count=5,
        image_count=1,
        hidden_element_count=3,
        text_sample="hello",
        html_snapshot="<html/>",
    )


def _make_console(level: str = "log", msg: str = "info") -> ConsoleEvent:
    return ConsoleEvent(level=level, message=msg, source_url="", line_number=0)


def _make_network(failed: bool = False, status: int = 200) -> NetworkEvent:
    return NetworkEvent(
        method="GET",
        url="http://app/api",
        status_code=status,
        latency_ms=10.0,
        request_headers={},
        response_size=512,
        resource_type="fetch",
        failed=failed,
    )


def _make_storage(route: str = "/") -> StorageSnapshot:
    return StorageSnapshot(
        route=route,
        local_storage={},
        session_storage={},
        cookies=(),
    )


def _make_perf(route: str = "/") -> PerformanceMetrics:
    return PerformanceMetrics(
        route=route,
        dns_ms=1.0,
        tcp_connect_ms=2.0,
        ttfb_ms=50.0,
        dom_interactive_ms=300.0,
        dom_content_loaded_ms=400.0,
        load_event_ms=600.0,
        fcp_ms=350.0,
        lcp_ms=500.0,
        js_heap_used_mb=12.0,
    )


def _make_screenshot(route: str = "/") -> ScreenshotArtifact:
    return ScreenshotArtifact(
        route=route,
        screenshot_type="full_page",
        format="png",
        width=1280,
        height=720,
        data_base64="abc123",
        truncated=False,
    )


class TestNormalize:
    def test_returns_runtime_trace_artifact(self) -> None:
        result = normalize(
            commit_ref="abc1234",
            base_url="http://localhost",
            dom_snapshots=[_make_dom()],
            console_events=[],
            network_events=[],
            storage_snapshots=[_make_storage()],
            screenshots=[],
            performance_metrics=[_make_perf()],
        )
        assert isinstance(result, RuntimeTraceArtifact)

    def test_commit_ref_set(self) -> None:
        result = normalize(
            commit_ref="deadbeef",
            base_url="http://app",
            dom_snapshots=[],
            console_events=[],
            network_events=[],
            storage_snapshots=[],
            screenshots=[],
            performance_metrics=[],
        )
        assert result.commit_ref == "deadbeef"

    def test_base_url_set(self) -> None:
        result = normalize(
            commit_ref="abc",
            base_url="http://myapp:3000",
            dom_snapshots=[],
            console_events=[],
            network_events=[],
            storage_snapshots=[],
            screenshots=[],
            performance_metrics=[],
        )
        assert result.base_url == "http://myapp:3000"

    def test_total_console_errors_counted(self) -> None:
        result = normalize(
            commit_ref="abc",
            base_url="http://app",
            dom_snapshots=[],
            console_events=[
                _make_console("error", "err1"),
                _make_console("log", "info"),
                _make_console("exception", "crash"),
            ],
            network_events=[],
            storage_snapshots=[],
            screenshots=[],
            performance_metrics=[],
        )
        assert result.total_console_errors == 2

    def test_total_network_failures_counted(self) -> None:
        result = normalize(
            commit_ref="abc",
            base_url="http://app",
            dom_snapshots=[],
            console_events=[],
            network_events=[
                _make_network(failed=True),
                _make_network(failed=False),
                _make_network(failed=True),
            ],
            storage_snapshots=[],
            screenshots=[],
            performance_metrics=[],
        )
        assert result.total_network_failures == 2

    def test_routes_deduplicated(self) -> None:
        result = normalize(
            commit_ref="abc",
            base_url="http://app",
            dom_snapshots=[_make_dom("/"), _make_dom("/"), _make_dom("/about")],
            console_events=[],
            network_events=[],
            storage_snapshots=[],
            screenshots=[],
            performance_metrics=[],
        )
        assert result.total_routes == 2
        assert "/" in result.routes_visited
        assert "/about" in result.routes_visited

    def test_console_secrets_masked_in_normalizer(self) -> None:
        """Normalizer applies Secret Shield to console messages (defense-in-depth)."""
        jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyIjoiYWRtaW4ifQ.SIG"
        result = normalize(
            commit_ref="abc",
            base_url="http://app",
            dom_snapshots=[],
            console_events=[_make_console("log", f"token={jwt}")],
            network_events=[],
            storage_snapshots=[],
            screenshots=[],
            performance_metrics=[],
        )
        assert "[REDACTED]" in result.console_events[0].message

    def test_artifact_is_frozen(self) -> None:
        result = normalize(
            commit_ref="abc",
            base_url="http://app",
            dom_snapshots=[],
            console_events=[],
            network_events=[],
            storage_snapshots=[],
            screenshots=[],
            performance_metrics=[],
        )
        with pytest.raises(FrozenInstanceError):
            result.commit_ref = "mutated"  # type: ignore[misc]

    def test_to_dict_is_serializable(self) -> None:
        import json

        result = normalize(
            commit_ref="abc123",
            base_url="http://localhost",
            dom_snapshots=[_make_dom("/")],
            console_events=[_make_console()],
            network_events=[_make_network()],
            storage_snapshots=[_make_storage()],
            screenshots=[],
            performance_metrics=[_make_perf()],
        )
        d = result.to_dict()
        # Must be JSON-serializable
        serialized = json.dumps(d)
        assert "abc123" in serialized

    def test_to_dict_excludes_html_snapshot(self) -> None:
        result = normalize(
            commit_ref="abc",
            base_url="http://app",
            dom_snapshots=[_make_dom("/")],
            console_events=[],
            network_events=[],
            storage_snapshots=[],
            screenshots=[],
            performance_metrics=[],
        )
        d = result.to_dict()
        for snap in d["dom_snapshots"]:
            assert "html_snapshot" not in snap

    def test_to_dict_contains_expected_keys(self) -> None:
        result = normalize(
            commit_ref="abc",
            base_url="http://app",
            dom_snapshots=[],
            console_events=[],
            network_events=[],
            storage_snapshots=[],
            screenshots=[],
            performance_metrics=[],
        )
        d = result.to_dict()
        assert "commit_ref" in d
        assert "base_url" in d
        assert "routes_visited" in d
        assert "dom_snapshots" in d
        assert "console_events" in d
        assert "network_events" in d
        assert "storage_snapshots" in d
        assert "performance_metrics" in d
