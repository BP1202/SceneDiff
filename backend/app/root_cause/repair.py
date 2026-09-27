"""Repair Recommendation Engine (Sprint 5 - Task 39).

Generates structured repair plans and actionable diagnostic checklists for IBM
Bob's autonomous code repair engine.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.root_cause.candidate import RootCauseCandidate

from app.root_cause.evidence import CorrelatedEvidenceItem, EvidenceCategory
from app.services.secret_shield import mask_string


@dataclass(frozen=True)
class RepairRecommendation:
    """Actionable repair recommendation targeting a file or component."""

    target_file: str | None
    target_function: str | None
    issue_summary: str
    suggested_action: str
    checklist: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize recommendation to dictionary."""
        return {
            "target_file": self.target_file,
            "target_function": self.target_function,
            "issue_summary": mask_string(self.issue_summary),
            "suggested_action": mask_string(self.suggested_action),
            "checklist": [mask_string(c) for c in self.checklist],
        }


def generate_repair_plan(
    primary: RootCauseCandidate,
    evidence_items: list[CorrelatedEvidenceItem],
) -> list[RepairRecommendation]:
    """Generate deterministic repair recommendations for IBM Bob.

    Args:
        primary: Primary suspected root cause candidate.
        evidence_items: Correlated runtime evidence items.

    Returns:
        List of RepairRecommendation items.
    """
    plan: list[RepairRecommendation] = []

    # 1. Primary candidate recommendation
    if "500" in primary.evidence_type or "5XX" in primary.evidence_type:
        plan.append(
            RepairRecommendation(
                target_file=primary.file_path,
                target_function=primary.function_name,
                issue_summary="Server-side HTTP 500 error triggered at runtime.",
                suggested_action=(
                    "Inspect backend route handler and middleware exception boundaries."
                ),
                checklist=[
                    "Check unhandled null/None pointers in request payloads.",
                    "Verify database query error handling and rollback blocks.",
                    "Ensure response serialization matches expected OpenAPI schema.",
                ],
            )
        )
    elif "4XX" in primary.evidence_type or "401" in primary.evidence_type:
        plan.append(
            RepairRecommendation(
                target_file=primary.file_path,
                target_function=primary.function_name,
                issue_summary="Client authentication or authorization failure.",
                suggested_action="Verify session credentials and auth headers.",
                checklist=[
                    "Inspect authorization header propagation in API client.",
                    "Verify JWT / session cookie validation logic.",
                    "Check route permissions and role-based access checks.",
                ],
            )
        )
    elif "EXCEPTION" in primary.evidence_type or "ERROR" in primary.evidence_type:
        plan.append(
            RepairRecommendation(
                target_file=primary.file_path,
                target_function=primary.function_name,
                issue_summary="Uncaught JavaScript exception in browser execution.",
                suggested_action=(
                    "Add optional chaining (?.) and defensive type guards."
                ),
                checklist=[
                    "Guard against undefined or null nested property access.",
                    "Verify asynchronous promise rejection handling.",
                    "Add React Error Boundary or try/catch blocks around rendering.",
                ],
            )
        )
    elif "DOM" in primary.evidence_type or "BUTTON" in primary.evidence_type:
        plan.append(
            RepairRecommendation(
                target_file=primary.file_path,
                target_function=primary.function_name,
                issue_summary="Interactive UI elements unexpectedly missing.",
                suggested_action="Review conditional rendering expressions.",
                checklist=[
                    "Audit boolean flags governing component visibility.",
                    "Verify state initialization before initial render.",
                    "Check CSS display/visibility styles on target selector.",
                ],
            )
        )
    else:
        plan.append(
            RepairRecommendation(
                target_file=primary.file_path,
                target_function=primary.function_name,
                issue_summary=primary.reason,
                suggested_action="Investigate behavioral divergence in Head commit.",
                checklist=[
                    "Review Git diff in Head commit for unintended side effects.",
                    "Verify runtime state transitions across routes.",
                ],
            )
        )

    # 2. Performance or memory leak checklist if present
    has_perf = any(e.category == EvidenceCategory.PERFORMANCE for e in evidence_items)
    if has_perf:
        plan.append(
            RepairRecommendation(
                target_file=None,
                target_function=None,
                issue_summary="Performance regression or memory degradation detected.",
                suggested_action="Optimize render lifecycle and memory usage.",
                checklist=[
                    "Unsubscribe active event listeners and intervals in unmount.",
                    "Memoize expensive calculations and component sub-trees.",
                    "Reduce bundle size or defer non-critical asset loading.",
                ],
            )
        )

    return plan
