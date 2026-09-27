"""Repair Service (Sprint 6 - Task 57).

Orchestrates autonomous repair workflow:
1. Loads Sprint 5 RootCauseReport.
2. Synthesizes structured repair plan via RepairPlanner.
3. Retrieves target code context via CodeContextRetriever.
4. Generates Git unified diff via PatchProvider.
5. Multi-layer validation via PatchValidator.
6. Assesses operational risk & repair confidence via RiskAssessmentEngine.
7. Formulates safe rollback instructions via RollbackGenerator.
8. Persists RepairReport and RepairPatch entities to PostgreSQL.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any
import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

from app.models.repair_patch import RepairPatch
from app.models.repair_report import RepairReport, RepairStatus
from app.models.root_cause_report import RootCauseReport
from app.repair.context import CodeContextRetriever
from app.repair.exporter import PatchExporter
from app.repair.patch_generator import (
    MockPatchProvider,
    OllamaPatchProvider,
    PatchProvider,
    TemplatePatchProvider,
)
from app.repair.planner import RepairPlan, RepairPlanner
from app.repair.report import RepairReportBuilder
from app.repair.risk import RiskAssessmentEngine
from app.repair.rollback import RollbackGenerator
from app.repair.validator import PatchValidator

logger = logging.getLogger(__name__)


def _resolve_provider(name: str) -> PatchProvider:
    """Resolve PatchProvider by registry name."""
    clean = name.strip()
    if clean == "MockPatchProvider":
        return MockPatchProvider()
    if clean == "OllamaPatchProvider":
        return OllamaPatchProvider()
    return TemplatePatchProvider()


async def create_repair_report(
    db: AsyncSession,
    root_cause_id: uuid.UUID,
    provider_name: str = "TemplatePatchProvider",
    override_target_file: str | None = None,
    virtual_files: dict[str, str] | None = None,
) -> RepairReport:
    """Execute end-to-end repair analysis and persist report + patch.

    Args:
        db: Active async database session.
        root_cause_id: UUID of completed RootCauseReport.
        provider_name: Provider strategy identifier.
        override_target_file: Optional path override for culprit file.
        virtual_files: Optional mock file mapping for testing without disk IO.

    Returns:
        Persisted RepairReport record.

    Raises:
        ValueError: If root cause report is not found.
    """
    logger.info("Starting repair generation for root_cause_id=%s", root_cause_id)

    # 1. Fetch RootCauseReport
    stmt = select(RootCauseReport).where(RootCauseReport.id == root_cause_id)
    result = await db.execute(stmt)
    rc_report = result.scalar_one_or_none()

    if not rc_report:
        raise ValueError(f"RootCauseReport {root_cause_id} not found")

    # 2. Plan repair
    initial_plan = RepairPlanner.plan(rc_report)
    target_file = override_target_file or initial_plan.target_file

    if override_target_file and override_target_file != initial_plan.target_file:
        plan = RepairPlan(
            summary=initial_plan.summary,
            target_file=target_file,
            target_function=initial_plan.target_function,
            actions=initial_plan.actions,
            prerequisites=initial_plan.prerequisites,
            validation_checklist=initial_plan.validation_checklist,
            metadata=initial_plan.metadata,
        )
    else:
        plan = initial_plan

    # 3. Retrieve code context
    retriever = CodeContextRetriever(virtual_files=virtual_files)
    context = retriever.retrieve(
        file_path=plan.target_file,
        function_name=plan.target_function,
    )

    # 4. Generate patch
    provider = _resolve_provider(provider_name)
    patch = provider.generate(plan, context)

    # 5. Validate patch
    validation = PatchValidator.validate(
        target_file=patch.target_file,
        diff_content=patch.diff_content,
        allowed_files=[plan.target_file],
        root_cause_reason=rc_report.summary,
    )

    # 6. Assess risk and repair confidence
    risk = RiskAssessmentEngine.assess(
        patch=patch,
        validation=validation,
        root_cause_confidence=rc_report.confidence_score,
    )

    # 7. Generate rollback instructions
    rollback = RollbackGenerator.generate(
        target_file=patch.target_file,
        head_commit=rc_report.head_commit,
    )

    # 8. Export git patch with RFC headers
    raw_git_patch = PatchExporter.export_git_patch(
        patch=patch,
        summary=plan.summary,
    )

    # 9. Build canonical report data and markdown
    report_id = uuid.uuid4()
    report_data = RepairReportBuilder.build(
        report_id=report_id,
        root_cause_id=root_cause_id,
        comparison_id=rc_report.comparison_id,
        repository_name=rc_report.repository_name,
        summary=plan.summary,
        plan=plan,
        patch=patch,
        validation=validation,
        risk=risk,
        rollback=rollback,
        raw_git_patch=raw_git_patch,
    )

    # 10. Persist models to database
    report_record = RepairReport(
        id=report_id,
        root_cause_id=root_cause_id,
        comparison_id=rc_report.comparison_id,
        repository_name=rc_report.repository_name,
        status=RepairStatus.COMPLETED,
        summary=plan.summary,
        risk_level=risk.level,
        risk_score=risk.score,
        repair_confidence=risk.repair_confidence,
        plan=plan.to_dict(),
        rollback_plan=rollback.to_dict(),
        markdown_report=report_data.generate_markdown(),
        pr_summary=report_data.generate_pr_summary(),
    )

    validation_notes: list[dict[str, Any]] = [
        {"type": "note", "message": n} for n in validation.notes
    ] + [{"type": "error", "message": e} for e in validation.errors]

    patch_record = RepairPatch(
        id=uuid.uuid4(),
        report_id=report_id,
        target_file=patch.target_file,
        diff_content=patch.diff_content,
        lines_added=patch.lines_added,
        lines_removed=patch.lines_removed,
        is_validated=validation.is_valid,
        risk_level=risk.level,
        validation_notes=validation_notes,
    )

    report_record.patches = [patch_record]

    db.add(report_record)
    await db.commit()
    await db.refresh(report_record)

    logger.info(
        "Successfully created RepairReport %s (risk=%s, confidence=%d%%)",
        report_record.id,
        report_record.risk_level.value,
        report_record.repair_confidence,
    )
    return report_record


async def get_repair_report_by_id(
    db: AsyncSession,
    report_id: uuid.UUID,
) -> RepairReport | None:
    """Retrieve repair report with related patches loaded."""
    stmt = (
        select(RepairReport)
        .where(RepairReport.id == report_id)
        .options(selectinload(RepairReport.patches))
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def list_repair_reports(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    repository_name: str | None = None,
    risk_level: str | None = None,
) -> tuple[list[RepairReport], int]:
    """Retrieve paginated repair reports."""
    stmt = select(RepairReport).order_by(RepairReport.created_at.desc())
    count_stmt = select(func.count(RepairReport.id))

    if repository_name:
        stmt = stmt.where(RepairReport.repository_name == repository_name)
        count_stmt = count_stmt.where(RepairReport.repository_name == repository_name)

    if risk_level:
        stmt = stmt.where(RepairReport.risk_level == risk_level)
        count_stmt = count_stmt.where(RepairReport.risk_level == risk_level)

    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()

    offset = (max(1, page) - 1) * page_size
    stmt = (
        stmt.offset(offset).limit(page_size).options(selectinload(RepairReport.patches))
    )

    records_result = await db.execute(stmt)
    records = list(records_result.scalars().all())

    return records, total
