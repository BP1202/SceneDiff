"""Repair Planning Engine (Sprint 6 - Task 47).

Converts Sprint 5 root cause reports into structured, actionable repair plans
for IBM Bob's autonomous repair engine. Deterministic and safe by default.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.services.secret_shield import mask_string


@dataclass(frozen=True)
class RepairAction:
    """An individual atomic repair step."""

    step: int
    description: str
    rationale: str
    is_automated: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert repair action to masked dictionary."""
        return {
            "step": self.step,
            "description": mask_string(self.description),
            "rationale": mask_string(self.rationale),
            "is_automated": self.is_automated,
        }


@dataclass(frozen=True)
class RepairPlan:
    """Structured repair plan synthesized from root cause analysis."""

    summary: str
    target_file: str
    target_function: str | None
    actions: list[RepairAction] = field(default_factory=list)
    prerequisites: list[str] = field(default_factory=list)
    validation_checklist: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize plan to dictionary."""
        return {
            "summary": mask_string(self.summary),
            "target_file": self.target_file,
            "target_function": self.target_function,
            "actions": [a.to_dict() for a in self.actions],
            "prerequisites": [mask_string(p) for p in self.prerequisites],
            "validation_checklist": [mask_string(v) for v in self.validation_checklist],
            "metadata": self.metadata,
        }


class RepairPlanner:
    """Deterministic planning engine for synthesizing repair steps."""

    @classmethod
    def plan(cls, report_data: dict[str, Any] | object) -> RepairPlan:
        """Create a structured repair plan from a root cause report.

        Args:
            report_data: Dictionary or model representing RootCauseReport.

        Returns:
            RepairPlan with ordered repair actions.
        """
        if isinstance(report_data, dict):
            primary = report_data.get("primary_candidate", {}) or {}
            summary = str(report_data.get("summary", ""))
            raw_repair_plan = report_data.get("repair_plan", []) or []
        else:
            primary = getattr(report_data, "primary_candidate", {}) or {}
            summary = str(getattr(report_data, "summary", ""))
            raw_repair_plan = getattr(report_data, "repair_plan", []) or []

        # Resolve target file and function
        target_file = (
            primary.get("file_path")
            or primary.get("file")
            or (raw_repair_plan[0].get("target_file") if raw_repair_plan else None)
            or "src/main.py"
        )
        target_function = (
            primary.get("function_name")
            or primary.get("function")
            or (raw_repair_plan[0].get("target_function") if raw_repair_plan else None)
        )

        reason = str(primary.get("reason", summary)).lower()
        evidence_type = str(primary.get("evidence_type", "")).lower()

        actions: list[RepairAction] = []
        prerequisites: list[str] = [
            f"Verify working tree is clean before modifying {target_file}",
            "Capture baseline unit test status",
        ]
        checklist: list[str] = [
            f"Validate syntax of {target_file}",
            "Verify Secret Shield scan passes on modified lines",
            "Run unit and regression test suite",
        ]

        # Deterministic strategy formulation based on root cause diagnostics
        fn_name = target_function or "function"
        if "null" in reason or "none" in reason or "nullpointer" in reason:
            actions = [
                RepairAction(
                    step=1,
                    description=f"Inspect {fn_name} input and return contracts",
                    rationale="Identify where None/null can propagate unexpectedly.",
                ),
                RepairAction(
                    step=2,
                    description="Add explicit null guard / boundary check",
                    rationale="Prevent unhandled None return from cascading to caller.",
                ),
                RepairAction(
                    step=3,
                    description="Raise explicit domain exception or provide default",
                    rationale="Ensure caller receives error or safe fallback.",
                ),
                RepairAction(
                    step=4,
                    description="Update caller validation and error handling contracts",
                    rationale="Preserve interface compatibility across boundaries.",
                ),
            ]
            plan_summary = f"Fix {target_function or target_file} null handling"

        elif (
            "500" in evidence_type or "server_error" in reason or "exception" in reason
        ):
            actions = [
                RepairAction(
                    step=1,
                    description=f"Add targeted exception handler in {fn_name}",
                    rationale="Catch unhandled runtime errors at the source.",
                ),
                RepairAction(
                    step=2,
                    description="Map fault to structured domain error response",
                    rationale="Prevent raw 500 status from exposing internals.",
                ),
                RepairAction(
                    step=3,
                    description="Ensure debug context is logged safely without secrets",
                    rationale="Preserve diagnostic observability for IBM Bob.",
                ),
            ]
            plan_summary = (
                f"Remediate 500 server error in {target_function or target_file}"
            )

        elif "404" in evidence_type or "route" in reason or "not found" in reason:
            actions = [
                RepairAction(
                    step=1,
                    description=f"Verify route handler in {target_file}",
                    rationale="Ensure route path and methods match expectations.",
                ),
                RepairAction(
                    step=2,
                    description="Add missing endpoint or update routing configuration",
                    rationale="Restore accessible API surface.",
                ),
            ]
            plan_summary = f"Restore route availability in {target_file}"

        elif "storage" in evidence_type or "token" in reason or "state" in reason:
            actions = [
                RepairAction(
                    step=1,
                    description=f"Verify state persistence key in {target_file}",
                    rationale="Prevent key collision or missing session values.",
                ),
                RepairAction(
                    step=2,
                    description="Sanitize state operations with default fallbacks",
                    rationale="Prevent undefined state crashes during navigation.",
                ),
            ]
            plan_summary = f"Fix state synchronization in {target_file}"

        else:
            # Fallback deterministic plan
            actions = [
                RepairAction(
                    step=1,
                    description=f"Inspect {fn_name} in {target_file}",
                    rationale="Locate root cause divergence identified in Sprint 5.",
                ),
                RepairAction(
                    step=2,
                    description="Apply defensive boundary guard and validation logic",
                    rationale="Ensure safe handling of unexpected inputs.",
                ),
                RepairAction(
                    step=3,
                    description="Add regression test covering root cause reproduction",
                    rationale="Prevent future regressions.",
                ),
            ]
            plan_summary = f"Repair logic in {target_file}"

        return RepairPlan(
            summary=plan_summary,
            target_file=target_file,
            target_function=target_function,
            actions=actions,
            prerequisites=prerequisites,
            validation_checklist=checklist,
            metadata={"source": "deterministic_planner", "rules_version": "1.0.0"},
        )
