"""Root Cause Report Generator (Sprint 5 - Task 40).

Orchestrates the entire Sprint 5 root cause analysis pipeline into a canonical
RootCauseAnalysisReport consumed by IBM Bob 2.0.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any
import uuid

if TYPE_CHECKING:
    from app.root_cause.evidence import (
        CorrelatedEvidenceItem,
        RouteEvidenceGroup,
    )

from app.root_cause.candidate import (
    RootCauseCandidate,
    generate_root_cause_candidates,
)
from app.root_cause.confidence import (
    ConfidenceScore,
    calculate_confidence,
)
from app.root_cause.correlator import correlate_evidence
from app.root_cause.explainer import (
    build_bob_prompt,
    generate_structured_explanation,
)
from app.root_cause.graph import CausalGraph, build_causal_graph
from app.root_cause.repair import (
    RepairRecommendation,
    generate_repair_plan,
)
from app.services.secret_shield import mask_string


@dataclass
class RootCauseAnalysisReport:
    """Canonical AI root cause report for IBM Bob 2.0."""

    analysis_id: uuid.UUID
    comparison_id: uuid.UUID
    repository_name: str
    base_commit: str
    head_commit: str
    summary: str
    primary_candidate: RootCauseCandidate
    secondary_candidates: list[RootCauseCandidate]
    confidence: ConfidenceScore
    repair_plan: list[RepairRecommendation]
    causal_graph: CausalGraph
    evidence_items: list[CorrelatedEvidenceItem]
    route_groups: list[RouteEvidenceGroup]
    bob_prompt: str
    explanation: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize complete root cause analysis report."""
        return {
            "analysis_id": str(self.analysis_id),
            "comparison_id": str(self.comparison_id),
            "repository_name": mask_string(self.repository_name),
            "base_commit": self.base_commit,
            "head_commit": self.head_commit,
            "summary": mask_string(self.summary),
            "primary_candidate": self.primary_candidate.to_dict(),
            "secondary_candidates": [c.to_dict() for c in self.secondary_candidates],
            "confidence": self.confidence.to_dict(),
            "repair_plan": [r.to_dict() for r in self.repair_plan],
            "causal_graph": self.causal_graph.to_dict(),
            "evidence_count": len(self.evidence_items),
            "evidence_items": [e.to_dict() for e in self.evidence_items],
            "route_groups": [g.to_dict() for g in self.route_groups],
            "bob_prompt": self.bob_prompt,
            "explanation": self.explanation,
        }


def generate_root_cause_report(
    comparison_id: uuid.UUID,
    repository_name: str,
    base_commit: str,
    head_commit: str,
    divergences: list[dict[str, Any]],
    git_diff_files: list[str] | None = None,
    changed_functions: list[dict[str, str]] | None = None,
) -> RootCauseAnalysisReport:
    """Execute complete Sprint 5 root cause analysis workflow.

    Args:
        comparison_id: UUID of behavior comparison.
        repository_name: Name of git repository.
        base_commit: Base git commit SHA.
        head_commit: Head git commit SHA.
        divergences: Serialized BehaviorDivergence list from Sprint 4.
        git_diff_files: Optional modified files from Git diff.
        changed_functions: Optional modified function signatures.

    Returns:
        Canonical RootCauseAnalysisReport.
    """
    analysis_id = uuid.uuid4()

    # 1. Correlate evidence
    items, route_groups = correlate_evidence(
        divergences=divergences,
        git_diff_files=git_diff_files,
    )

    # 2. Build causal dependency graph
    graph = build_causal_graph(items)

    # 3. Generate primary and secondary candidates
    primary, secondaries = generate_root_cause_candidates(
        graph=graph,
        evidence_items=items,
        changed_functions=changed_functions,
    )

    # 4. Compute deterministic confidence
    confidence = calculate_confidence(items, primary)

    # 5. Formulate actionable repair recommendations
    repair_plan = generate_repair_plan(primary, items)

    # 6. Build prompt and explanation
    bob_prompt = build_bob_prompt(
        repository_name=repository_name,
        base_commit=base_commit,
        head_commit=head_commit,
        primary_candidate=primary,
        confidence=confidence,
        evidence_items=items,
        repair_plan=repair_plan,
    )

    explanation = generate_structured_explanation(
        repository_name=repository_name,
        base_commit=base_commit,
        head_commit=head_commit,
        primary_candidate=primary,
        confidence=confidence,
        evidence_items=items,
    )

    summary = explanation.get("summary", primary.reason)

    return RootCauseAnalysisReport(
        analysis_id=analysis_id,
        comparison_id=comparison_id,
        repository_name=repository_name,
        base_commit=base_commit,
        head_commit=head_commit,
        summary=summary,
        primary_candidate=primary,
        secondary_candidates=secondaries,
        confidence=confidence,
        repair_plan=repair_plan,
        causal_graph=graph,
        evidence_items=items,
        route_groups=route_groups,
        bob_prompt=bob_prompt,
        explanation=explanation,
    )
