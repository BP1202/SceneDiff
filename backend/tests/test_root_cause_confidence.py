"""Tests for root_cause/confidence.py (Sprint 5 - Task 38)."""

from __future__ import annotations

from app.root_cause.candidate import RootCauseCandidate
from app.root_cause.confidence import ConfidenceBand, calculate_confidence
from app.root_cause.evidence import (
    CorrelatedEvidenceItem,
    EvidenceCategory,
    EvidenceSeverity,
)


class TestConfidenceScoringEngine:
    def test_clean_baseline_has_very_high_confidence(self) -> None:
        cand = RootCauseCandidate(
            reason="Clean",
            evidence_type="NONE",
            severity="INFO",
            score=10.0,
        )
        score = calculate_confidence([], cand)
        assert score.score == 100
        assert score.band == ConfidenceBand.VERY_HIGH

    def test_strong_evidence_yields_very_high_confidence(self) -> None:
        ev1 = CorrelatedEvidenceItem(
            category=EvidenceCategory.NETWORK,
            severity=EvidenceSeverity.CRITICAL,
            route="/api/login",
            event_type="STATUS_CODE_5XX_INTRODUCED",
            title="HTTP 500",
            description="",
            divergence_order=1,
            is_root_cause_candidate=True,
        )
        ev2 = CorrelatedEvidenceItem(
            category=EvidenceCategory.CONSOLE,
            severity=EvidenceSeverity.HIGH,
            route="/login",
            event_type="RUNTIME_EXCEPTION",
            title="Uncaught TypeError",
            description="",
            divergence_order=2,
        )
        ev3 = CorrelatedEvidenceItem(
            category=EvidenceCategory.DOM,
            severity=EvidenceSeverity.HIGH,
            route="/login",
            event_type="BUTTON_REMOVED",
            title="Login button missing",
            description="",
            divergence_order=3,
        )

        cand = RootCauseCandidate(
            reason="Server 500",
            evidence_type="STATUS_CODE_5XX_INTRODUCED",
            severity="CRITICAL",
            score=95.0,
            file_path="src/login.py",
            function_name="handle_login",
        )

        score = calculate_confidence([ev1, ev2, ev3], cand)
        # 35 (crit) + 25 (order 1) + 20 (3 cats) + 20 (file & func) = 100
        assert score.score == 100
        assert score.band == ConfidenceBand.VERY_HIGH
        assert score.severity_points == 35
        assert score.timeline_points == 25
        assert score.evidence_points == 20
        assert score.git_points == 20

    def test_single_low_evidence_yields_lower_band(self) -> None:
        ev = CorrelatedEvidenceItem(
            category=EvidenceCategory.DOM,
            severity=EvidenceSeverity.LOW,
            route="/about",
            event_type="BUTTON_ADDED",
            title="Button added",
            description="",
            divergence_order=5,
        )
        cand = RootCauseCandidate(
            reason="Cosmetic button",
            evidence_type="BUTTON_ADDED",
            severity="LOW",
            score=30.0,
        )
        score = calculate_confidence([ev], cand)
        # 5 (low) + 5 (no root flag) + 10 (1 cat) + 6 (no file) = 26
        assert score.score < 60
        assert score.band == ConfidenceBand.LOW
