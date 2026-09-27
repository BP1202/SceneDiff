"""Repair Report Builder & PR Summary Generator (Sprint 6 - Task 53).

Assembles repair plans, patches, validation results, risk scores, and rollback
strategies into canonical reports (JSON, Markdown, and GitHub PR summaries).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any
import uuid

if TYPE_CHECKING:
    from app.repair.patch_generator import GeneratedPatch
    from app.repair.planner import RepairPlan
    from app.repair.risk import RiskAssessmentResult
    from app.repair.rollback import RollbackPlan
    from app.repair.validator import ValidationResult

from app.services.secret_shield import mask_string


@dataclass(frozen=True)
class RepairReportData:
    """Canonical aggregated repair report."""

    report_id: uuid.UUID
    root_cause_id: uuid.UUID
    comparison_id: uuid.UUID
    repository_name: str
    summary: str
    plan: RepairPlan
    patch: GeneratedPatch
    validation: ValidationResult
    risk: RiskAssessmentResult
    rollback: RollbackPlan
    raw_git_patch: str

    def to_dict(self) -> dict[str, Any]:
        """Convert report to JSON-serializable dictionary."""
        return {
            "report_id": str(self.report_id),
            "root_cause_id": str(self.root_cause_id),
            "comparison_id": str(self.comparison_id),
            "repository_name": self.repository_name,
            "summary": mask_string(self.summary),
            "plan": self.plan.to_dict(),
            "patch": self.patch.to_dict(),
            "validation": self.validation.to_dict(),
            "risk": self.risk.to_dict(),
            "rollback": self.rollback.to_dict(),
            "repair_confidence": self.risk.repair_confidence,
            "raw_git_patch": self.raw_git_patch,
        }

    def generate_markdown(self) -> str:
        """Generate comprehensive technical Markdown report for IBM Bob."""
        actions_md = "\n".join(
            f"{a.step}. **{a.description}** — {a.rationale}" for a in self.plan.actions
        )

        reasons_md = "\n".join(f"- {r}" for r in self.risk.reasons)

        rollback_cmds_md = "\n".join(f"$ {cmd}" for cmd in self.rollback.commands)

        validation_notes_md = "\n".join(
            f"- [x] {note}" for note in self.validation.notes
        )
        if self.validation.errors:
            validation_notes_md += "\n" + "\n".join(
                f"- [ ] ERROR: {err}" for err in self.validation.errors
            )

        score_str = f"{self.risk.score}/100"
        conf_str = f"{self.risk.repair_confidence}%"

        md = f"""# IBM Bob Autonomous Repair Report

**Repository:** `{self.repository_name}`
**Report ID:** `{self.report_id}`
**Target File:** `{self.patch.target_file}`
**Risk Level:** `{self.risk.level.value}` (Score: {score_str})
**Repair Confidence:** `{conf_str}`

---

## 1. Executive Summary
{mask_string(self.summary)}

## 2. Repair Plan
{actions_md}

## 3. Unified Git Diff
```diff
{self.patch.diff_content.strip()}
```

## 4. Multi-Layer Validation
- **Syntax Valid:** `{self.validation.syntax_valid}`
- **Python AST Valid:** `{self.validation.ast_valid}`
- **Secret Shield Status:** `{self.validation.secret_scan}`
- **Scope Valid:** `{self.validation.scope_valid}`

{validation_notes_md}

## 5. Risk Assessment
{reasons_md}

## 6. Rollback & Recovery Strategy
**Strategy:** {self.rollback.strategy}

```bash
{rollback_cmds_md}
```
"""
        return md

    def generate_pr_summary(self) -> str:
        """Generate concise, production-ready GitHub PR summary (Improvement 3)."""
        actions_list = "\n".join(f"- {a.description}" for a in self.plan.actions)
        reasons_list = "\n".join(f"- {r}" for r in self.risk.reasons)
        score_str = f"{self.risk.score}/100"
        conf_str = f"{self.risk.repair_confidence}%"
        is_secret_pass = self.validation.secret_scan == "passed"  # noqa: S105
        secret_summary = "Passed (Zero secrets)" if is_secret_pass else "Failed"
        ast_summary = "Passed" if self.validation.ast_valid else "Failed"
        syntax_summary = "Passed" if self.validation.syntax_valid else "Failed"
        scope_summary = (
            "Passed (Culprit file only)" if self.validation.scope_valid else "Failed"
        )

        pr_md = f"""## IBM Bob Repair Summary

### Root Cause
{mask_string(self.summary)}

### Proposed Fix
{actions_list}

### Risk Assessment
**Risk Level:** **{self.risk.level.value}** ({score_str})
**Repair Confidence:** **{conf_str}**
{reasons_list}

### Validation
- **Python AST:** {ast_summary}
- **Secret Shield:** {secret_summary}
- **Unified Diff Syntax:** {syntax_summary}
- **Scope Confinement:** {scope_summary}

### Rollback Strategy
```bash
git apply -R repair.patch
git revert --no-edit HEAD
```
"""
        return pr_md


class RepairReportBuilder:
    """Assembles all diagnostic & repair artifacts into canonical report."""

    @classmethod
    def build(
        cls,
        report_id: uuid.UUID,
        root_cause_id: uuid.UUID,
        comparison_id: uuid.UUID,
        repository_name: str,
        summary: str,
        plan: RepairPlan,
        patch: GeneratedPatch,
        validation: ValidationResult,
        risk: RiskAssessmentResult,
        rollback: RollbackPlan,
        raw_git_patch: str,
    ) -> RepairReportData:
        """Construct a validated RepairReportData instance."""
        return RepairReportData(
            report_id=report_id,
            root_cause_id=root_cause_id,
            comparison_id=comparison_id,
            repository_name=repository_name,
            summary=summary,
            plan=plan,
            patch=patch,
            validation=validation,
            risk=risk,
            rollback=rollback,
            raw_git_patch=raw_git_patch,
        )
