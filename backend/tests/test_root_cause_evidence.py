"""Tests for root_cause/evidence.py (Sprint 5 - Task 35)."""

from __future__ import annotations

from app.root_cause.evidence import (
    CorrelatedEvidenceItem,
    EvidenceCategory,
    EvidenceSeverity,
    RouteEvidenceGroup,
)


class TestEvidenceStructures:
    def test_correlated_evidence_item_to_dict(self) -> None:
        item = CorrelatedEvidenceItem(
            category=EvidenceCategory.NETWORK,
            severity=EvidenceSeverity.CRITICAL,
            route="/api/login",
            event_type="STATUS_CODE_5XX_INTRODUCED",
            title="POST /api/login returned HTTP 500",
            description="Fatal server error in head commit.",
            divergence_order=1,
            is_root_cause_candidate=True,
            file_path="backend/auth/routes.py",
            function_name="login_user",
        )
        d = item.to_dict()
        assert d["category"] == "network"
        assert d["severity"] == "CRITICAL"
        assert d["route"] == "/api/login"
        assert d["divergence_order"] == 1
        assert d["is_root_cause_candidate"] is True
        assert d["file_path"] == "backend/auth/routes.py"
        assert d["function_name"] == "login_user"

    def test_secret_in_evidence_is_masked(self) -> None:
        item = CorrelatedEvidenceItem(
            category=EvidenceCategory.CONSOLE,
            severity=EvidenceSeverity.HIGH,
            route="/login",
            event_type="RUNTIME_EXCEPTION",
            title="Bearer secret_token_12345 auth failed",
            description="Token Bearer secret_token_12345 was invalid.",
        )
        d = item.to_dict()
        assert "[REDACTED]" in d["title"]
        assert "[REDACTED]" in d["description"]

    def test_route_evidence_group_properties(self) -> None:
        item1 = CorrelatedEvidenceItem(
            category=EvidenceCategory.DOM,
            severity=EvidenceSeverity.LOW,
            route="/checkout",
            event_type="BUTTON_ADDED",
            title="Button added",
            description="",
        )
        item2 = CorrelatedEvidenceItem(
            category=EvidenceCategory.NETWORK,
            severity=EvidenceSeverity.CRITICAL,
            route="/checkout",
            event_type="NETWORK_REQUEST_FAILED",
            title="Network call failed",
            description="",
        )
        group = RouteEvidenceGroup(route="/checkout", events=[item1, item2])
        assert group.total_events == 2
        assert group.highest_severity == EvidenceSeverity.CRITICAL

        g_dict = group.to_dict()
        assert g_dict["route"] == "/checkout"
        assert g_dict["total_events"] == 2
        assert g_dict["highest_severity"] == "CRITICAL"
        assert len(g_dict["events"]) == 2

    def test_empty_route_group_highest_severity(self) -> None:
        group = RouteEvidenceGroup(route="/empty")
        assert group.total_events == 0
        assert group.highest_severity == EvidenceSeverity.INFO
