"""Tests for behavior/timeline.py — Runtime Divergence Timeline Engine (Sprint 4)."""

from __future__ import annotations

from app.behavior.severity import BehaviorDivergence, SeverityLevel
from app.behavior.timeline import build_divergence_timeline


class TestTimelineEngine:
    def test_empty_divergences(self) -> None:
        ordered, first = build_divergence_timeline([])
        assert ordered == []
        assert first is None

    def test_first_meaningful_divergence_identified(self) -> None:
        div1 = BehaviorDivergence(
            category="dom",
            severity=SeverityLevel.LOW,
            route="/login",
            event_type="BUTTON_ADDED",
            title="Button added",
            description="",
        )
        div2 = BehaviorDivergence(
            category="network",
            severity=SeverityLevel.CRITICAL,
            route="/login",
            event_type="STATUS_CODE_5XX_INTRODUCED",
            title="POST /login returned 500",
            description="",
        )
        div3 = BehaviorDivergence(
            category="console",
            severity=SeverityLevel.HIGH,
            route="/login",
            event_type="RUNTIME_EXCEPTION",
            title="Uncaught error",
            description="",
        )

        ordered, first = build_divergence_timeline(
            [div1, div2, div3], journey_routes=["/login"]
        )

        assert len(ordered) == 3
        # Network error is causal #1 on /login, so it should be divergence_order 1
        assert ordered[0].event_type == "STATUS_CODE_5XX_INTRODUCED"
        assert ordered[0].divergence_order == 1
        assert ordered[0].is_root_cause_candidate is True

        assert first is not None
        assert first.event_type == "STATUS_CODE_5XX_INTRODUCED"
        assert first.is_root_cause_candidate is True

    def test_journey_order_respected(self) -> None:
        div_dashboard = BehaviorDivergence(
            category="network",
            severity=SeverityLevel.CRITICAL,
            route="/dashboard",
            event_type="NETWORK_REQUEST_FAILED",
            title="Failed on dashboard",
            description="",
        )
        div_login = BehaviorDivergence(
            category="network",
            severity=SeverityLevel.CRITICAL,
            route="/login",
            event_type="NETWORK_REQUEST_FAILED",
            title="Failed on login",
            description="",
        )

        ordered, first = build_divergence_timeline(
            [div_dashboard, div_login],
            journey_routes=["/login", "/dashboard"],
        )

        # /login occurred before /dashboard in journey
        assert ordered[0].route == "/login"
        assert ordered[1].route == "/dashboard"
        assert first.route == "/login"
