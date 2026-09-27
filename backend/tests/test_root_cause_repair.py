"""Tests for root_cause/repair.py (Sprint 5 - Task 39)."""

from __future__ import annotations

from app.root_cause.candidate import RootCauseCandidate
from app.root_cause.evidence import (
    CorrelatedEvidenceItem,
    EvidenceCategory,
    EvidenceSeverity,
)
from app.root_cause.repair import generate_repair_plan


class TestRepairRecommendationEngine:
    def test_repair_plan_for_500_error(self) -> None:
        cand = RootCauseCandidate(
            reason="HTTP 500 error",
            evidence_type="STATUS_CODE_5XX_INTRODUCED",
            severity="CRITICAL",
            score=90.0,
            file_path="src/api.py",
            function_name="post_order",
        )
        plan = generate_repair_plan(cand, [])
        assert len(plan) >= 1
        assert plan[0].target_file == "src/api.py"
        assert plan[0].target_function == "post_order"
        assert "HTTP 500" in plan[0].issue_summary
        assert len(plan[0].checklist) >= 2

    def test_repair_plan_for_console_exception(self) -> None:
        cand = RootCauseCandidate(
            reason="Uncaught error",
            evidence_type="RUNTIME_EXCEPTION",
            severity="HIGH",
            score=80.0,
            file_path="src/App.tsx",
        )
        plan = generate_repair_plan(cand, [])
        assert len(plan) >= 1
        assert "JavaScript" in plan[0].issue_summary
        assert any("undefined" in c for c in plan[0].checklist)

    def test_repair_plan_includes_performance_when_present(self) -> None:
        cand = RootCauseCandidate(
            reason="Button missing",
            evidence_type="BUTTON_REMOVED",
            severity="HIGH",
            score=80.0,
        )
        perf_ev = CorrelatedEvidenceItem(
            category=EvidenceCategory.PERFORMANCE,
            severity=EvidenceSeverity.MEDIUM,
            route="/home",
            event_type="PAGE_LOAD_REGRESSION",
            title="Page load regression",
            description="",
        )
        plan = generate_repair_plan(cand, [perf_ev])
        assert len(plan) == 2
        assert any("Performance" in p.issue_summary for p in plan)
