"""Tests for root_cause/candidate.py (Sprint 5 - Task 37)."""

from __future__ import annotations

from app.root_cause.candidate import generate_root_cause_candidates
from app.root_cause.evidence import (
    CorrelatedEvidenceItem,
    EvidenceCategory,
    EvidenceSeverity,
)
from app.root_cause.graph import build_causal_graph


class TestRootCauseCandidateGenerator:
    def test_empty_evidence_produces_clean_candidate(self) -> None:
        graph = build_causal_graph([])
        primary, secondaries = generate_root_cause_candidates(graph, [])
        assert primary.severity == "INFO"
        assert "No behavioral regressions" in primary.reason
        assert secondaries == []

    def test_primary_candidate_extracted_from_root_node(self) -> None:
        ev1 = CorrelatedEvidenceItem(
            category=EvidenceCategory.NETWORK,
            severity=EvidenceSeverity.CRITICAL,
            route="/api/auth",
            event_type="STATUS_CODE_5XX_INTRODUCED",
            title="HTTP 500 on /api/auth",
            description="Internal server error",
            divergence_order=1,
            is_root_cause_candidate=True,
            file_path="src/api/auth.ts",
        )
        ev2 = CorrelatedEvidenceItem(
            category=EvidenceCategory.DOM,
            severity=EvidenceSeverity.HIGH,
            route="/login",
            event_type="BUTTON_REMOVED",
            title="Button removed",
            description="",
            divergence_order=2,
        )

        graph = build_causal_graph([ev1, ev2])
        primary, secondaries = generate_root_cause_candidates(
            graph,
            [ev1, ev2],
            changed_functions=[{"file": "src/api/auth.ts", "function": "login"}],
        )

        assert primary.evidence_type == "STATUS_CODE_5XX_INTRODUCED"
        assert primary.file_path == "src/api/auth.ts"
        assert primary.function_name == "login"
        assert primary.severity == "CRITICAL"
        assert len(secondaries) == 1
        assert secondaries[0].evidence_type == "BUTTON_REMOVED"
