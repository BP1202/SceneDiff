"""Root Cause Candidate Generator (Sprint 5 - Task 37).

Analyzes the causal dependency graph and runtime evidence to identify primary
and secondary root cause candidates for IBM Bob's repair engine.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.root_cause.graph import CausalGraph

from app.root_cause.evidence import CorrelatedEvidenceItem, EvidenceSeverity
from app.services.secret_shield import mask_string


@dataclass(frozen=True)
class RootCauseCandidate:
    """Suspected root cause candidate pinpointed to file, function, and trigger."""

    reason: str
    evidence_type: str
    severity: str
    score: float
    file_path: str | None = None
    function_name: str | None = None
    route: str = "global"

    def to_dict(self) -> dict[str, Any]:
        """Serialize candidate into clean dictionary."""
        return {
            "reason": mask_string(self.reason),
            "evidence_type": self.evidence_type,
            "severity": self.severity,
            "score": round(self.score, 2),
            "file_path": self.file_path,
            "function_name": self.function_name,
            "route": mask_string(self.route),
        }


def generate_root_cause_candidates(
    graph: CausalGraph,
    evidence_items: list[CorrelatedEvidenceItem],
    changed_functions: list[dict[str, str]] | None = None,
) -> tuple[RootCauseCandidate, list[RootCauseCandidate]]:
    """Generate primary and secondary root cause candidates.

    Args:
        graph: Causal dependency graph.
        evidence_items: Ordered list of correlated evidence items.
        changed_functions: Optional list of changed functions from Git diff.

    Returns:
        tuple (primary_candidate, secondary_candidates)
    """
    if not evidence_items:
        default_candidate = RootCauseCandidate(
            reason="No behavioral regressions detected between commits.",
            evidence_type="NONE",
            severity=EvidenceSeverity.INFO.value,
            score=10.0,
        )
        return default_candidate, []

    # Priority 1: Flagged root cause from timeline or root node of causal graph
    root_nodes = graph.root_nodes
    root_evidence = (
        root_nodes[0].evidence
        if root_nodes
        else next(
            (e for e in evidence_items if e.is_root_cause_candidate),
            evidence_items[0],
        )
    )

    # Correlate with changed functions if available
    matched_func = None
    matched_file = root_evidence.file_path
    if changed_functions:
        for fn in changed_functions:
            fn_file = fn.get("file", "")
            fn_name = fn.get("function", "")
            if matched_file and fn_file and fn_file in matched_file:
                matched_func = fn_name
                matched_file = fn_file
                break
            if not matched_file and fn_file:
                matched_file = fn_file
                matched_func = fn_name
                break

    primary = RootCauseCandidate(
        reason=f"Earliest divergence triggered by {root_evidence.title}: "
        f"{root_evidence.description}",
        evidence_type=root_evidence.event_type,
        severity=root_evidence.severity.value,
        score=95.0 if root_evidence.severity == EvidenceSeverity.CRITICAL else 80.0,
        file_path=matched_file,
        function_name=matched_func,
        route=root_evidence.route,
    )

    # Build secondary candidates from other significant divergences
    secondaries: list[RootCauseCandidate] = []
    for item in evidence_items:
        is_distinct = (
            item.event_type != root_evidence.event_type
            or item.route != root_evidence.route
        )
        is_significant = item.severity in (
            EvidenceSeverity.CRITICAL,
            EvidenceSeverity.HIGH,
            EvidenceSeverity.MEDIUM,
        )
        if is_distinct and is_significant:
            secondaries.append(
                RootCauseCandidate(
                    reason=f"Contributing divergence on {item.route}: {item.title}",
                    evidence_type=item.event_type,
                    severity=item.severity.value,
                    score=70.0 if item.severity == EvidenceSeverity.HIGH else 50.0,
                    file_path=item.file_path,
                    function_name=item.function_name,
                    route=item.route,
                )
            )

    return primary, secondaries
