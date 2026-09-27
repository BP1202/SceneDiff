"""Confidence Scoring Engine (Sprint 5 - Task 38).

Calculates deterministic confidence scores (0-100) based on severity weights,
timeline causality, multi-collector convergence, and Git correlation.
"""

from __future__ import annotations

from dataclasses import dataclass
import enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.root_cause.candidate import RootCauseCandidate

from app.root_cause.evidence import CorrelatedEvidenceItem, EvidenceSeverity


class ConfidenceBand(enum.StrEnum):
    """Deterministic confidence rating bands."""

    VERY_HIGH = "VERY_HIGH"  # 90-100
    HIGH = "HIGH"  # 75-89
    MEDIUM = "MEDIUM"  # 60-74
    LOW = "LOW"  # Below 60


@dataclass(frozen=True)
class ConfidenceScore:
    """Detailed breakdown of deterministic confidence computation."""

    score: int
    band: ConfidenceBand
    severity_points: int
    timeline_points: int
    evidence_points: int
    git_points: int
    rationale: str

    def to_dict(self) -> dict[str, int | str]:
        """Serialize score breakdown."""
        return {
            "score": self.score,
            "band": self.band.value,
            "severity_points": self.severity_points,
            "timeline_points": self.timeline_points,
            "evidence_points": self.evidence_points,
            "git_points": self.git_points,
            "rationale": self.rationale,
        }


def calculate_confidence(
    evidence_items: list[CorrelatedEvidenceItem],
    primary_candidate: RootCauseCandidate,
) -> ConfidenceScore:
    """Calculate deterministic confidence score for root cause analysis.

    Formula:
        Confidence = SeverityWeight + TimelineWeight + EvidenceWeight + GitWeight
        Capped between 0 and 100.
    """
    if not evidence_items:
        return ConfidenceScore(
            score=100,
            band=ConfidenceBand.VERY_HIGH,
            severity_points=0,
            timeline_points=0,
            evidence_points=0,
            git_points=0,
            rationale="No behavioral regressions detected; baseline is stable.",
        )

    # 1. Severity points (max 35)
    severities = {e.severity for e in evidence_items}
    if EvidenceSeverity.CRITICAL in severities:
        sev_pts = 35
    elif EvidenceSeverity.HIGH in severities:
        sev_pts = 25
    elif EvidenceSeverity.MEDIUM in severities:
        sev_pts = 15
    else:
        sev_pts = 5

    # 2. Timeline points (max 25)
    root_items = [e for e in evidence_items if e.is_root_cause_candidate]
    if root_items and root_items[0].divergence_order == 1:
        time_pts = 25
    elif root_items and root_items[0].divergence_order <= 3:
        time_pts = 18
    elif root_items:
        time_pts = 10
    else:
        time_pts = 5

    # 3. Evidence convergence points (max 20)
    categories = {e.category for e in evidence_items}
    if len(categories) >= 3:
        ev_pts = 20
    elif len(categories) == 2:
        ev_pts = 15
    else:
        ev_pts = 10

    # 4. Git correlation points (max 20)
    if primary_candidate.file_path and primary_candidate.function_name:
        git_pts = 20
    elif primary_candidate.file_path:
        git_pts = 14
    else:
        git_pts = 6

    total = min(100, max(0, sev_pts + time_pts + ev_pts + git_pts))

    if total >= 90:
        band = ConfidenceBand.VERY_HIGH
    elif total >= 75:
        band = ConfidenceBand.HIGH
    elif total >= 60:
        band = ConfidenceBand.MEDIUM
    else:
        band = ConfidenceBand.LOW

    rationale = (
        f"Confidence {total}/100 ({band.value}) based on severity={sev_pts}pts, "
        f"timeline={time_pts}pts, convergence={ev_pts}pts, "
        f"git_match={git_pts}pts."
    )

    return ConfidenceScore(
        score=total,
        band=band,
        severity_points=sev_pts,
        timeline_points=time_pts,
        evidence_points=ev_pts,
        git_points=git_pts,
        rationale=rationale,
    )
