"""Tests for root_cause/explainer.py and report.py (Sprint 5 - Task 40)."""

from __future__ import annotations

import uuid

from app.root_cause.candidate import RootCauseCandidate
from app.root_cause.confidence import ConfidenceBand, ConfidenceScore
from app.root_cause.evidence import (
    CorrelatedEvidenceItem,
    EvidenceCategory,
    EvidenceSeverity,
)
from app.root_cause.explainer import (
    build_bob_prompt,
    generate_structured_explanation,
)
from app.root_cause.repair import RepairRecommendation
from app.root_cause.report import generate_root_cause_report


class TestExplainerAndReportEngine:
    def test_build_bob_prompt_contains_key_sections(self) -> None:
        cand = RootCauseCandidate(
            reason="Auth failure",
            evidence_type="HTTP_500",
            severity="CRITICAL",
            score=95.0,
            file_path="src/auth.ts",
        )
        conf = ConfidenceScore(
            score=90,
            band=ConfidenceBand.VERY_HIGH,
            severity_points=35,
            timeline_points=25,
            evidence_points=15,
            git_points=15,
            rationale="",
        )
        ev = CorrelatedEvidenceItem(
            category=EvidenceCategory.NETWORK,
            severity=EvidenceSeverity.CRITICAL,
            route="/login",
            event_type="HTTP_500",
            title="500 on login",
            description="",
        )
        repair = RepairRecommendation(
            target_file="src/auth.ts",
            target_function="login",
            issue_summary="500 error",
            suggested_action="Fix auth handling",
        )

        prompt = build_bob_prompt(
            repository_name="SceneDiff",
            base_commit="abc1234",
            head_commit="def5678",
            primary_candidate=cand,
            confidence=conf,
            evidence_items=[ev],
            repair_plan=[repair],
        )

        assert "# SceneDiff Root Cause Analysis Prompt" in prompt
        assert "Repository:\n- SceneDiff" in prompt
        assert "Base Commit:\n- abc1234" in prompt
        assert "Head Commit:\n- def5678" in prompt
        assert "Fix auth handling" in prompt
        assert "evidence only" in prompt

    def test_structured_explanation_has_zero_hallucination_flag(self) -> None:
        cand = RootCauseCandidate(
            reason="Token failure",
            evidence_type="STATUS_CODE_5XX_INTRODUCED",
            severity="CRITICAL",
            score=90.0,
        )
        conf = ConfidenceScore(
            score=85,
            band=ConfidenceBand.HIGH,
            severity_points=25,
            timeline_points=25,
            evidence_points=15,
            git_points=20,
            rationale="",
        )
        exp = generate_structured_explanation(
            repository_name="SceneDiff",
            base_commit="abc1234",
            head_commit="def5678",
            primary_candidate=cand,
            confidence=conf,
            evidence_items=[],
        )
        assert exp["zero_hallucination_verified"] is True
        assert exp["confidence_score"] == 85
        assert "SceneDiff" in exp["summary"]

    def test_generate_root_cause_report_orchestration(self) -> None:
        comp_id = uuid.uuid4()
        divergences = [
            {
                "category": "network",
                "severity": "CRITICAL",
                "route": "/api/orders",
                "event_type": "STATUS_CODE_5XX_INTRODUCED",
                "title": "POST /api/orders returned 500",
                "description": "Server failure",
                "divergence_order": 1,
                "is_root_cause_candidate": True,
            },
            {
                "category": "dom",
                "severity": "HIGH",
                "route": "/checkout",
                "event_type": "BUTTON_REMOVED",
                "title": "Pay button disappeared",
                "description": "Button absent",
                "divergence_order": 2,
                "is_root_cause_candidate": False,
            },
        ]

        report = generate_root_cause_report(
            comparison_id=comp_id,
            repository_name="SceneDiff",
            base_commit="1111111",
            head_commit="2222222",
            divergences=divergences,
            git_diff_files=["src/routes/orders.py"],
        )

        assert report.comparison_id == comp_id
        assert report.repository_name == "SceneDiff"
        assert report.primary_candidate.evidence_type == "STATUS_CODE_5XX_INTRODUCED"
        assert report.confidence.score >= 75
        assert len(report.repair_plan) >= 1
        assert len(report.evidence_items) == 2

        d = report.to_dict()
        assert d["analysis_id"] == str(report.analysis_id)
        assert d["comparison_id"] == str(comp_id)
        assert d["confidence"]["score"] == report.confidence.score
        assert len(d["evidence_items"]) == 2
