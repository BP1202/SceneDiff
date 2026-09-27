"""Root Cause Analysis Service (Sprint 5 - Task 43).

Coordinates AI root cause reasoning workflows, correlates runtime comparison
events with Git modifications, and persists reports and evidence to PostgreSQL.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any
import uuid

from sqlalchemy import func, select

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

from app.models.behavior_comparison import BehaviorComparison, ComparisonEvent
from app.models.root_cause_evidence import RootCauseEvidence
from app.models.root_cause_report import (
    AnalysisStatus,
    ConfidenceLevel,
    RootCauseReport,
)
from app.root_cause.report import generate_root_cause_report

logger = logging.getLogger(__name__)


async def create_root_cause_analysis(
    db: AsyncSession,
    comparison_id: uuid.UUID,
    git_diff_files: list[str] | None = None,
    changed_functions: list[dict[str, str]] | None = None,
) -> RootCauseReport:
    """Execute AI root cause analysis for a completed behavior comparison."""
    # 1. Fetch comparison record
    stmt = select(BehaviorComparison).where(BehaviorComparison.id == comparison_id)
    result = await db.execute(stmt)
    comparison = result.scalar_one_or_none()
    if comparison is None:
        raise ValueError(f"BehaviorComparison {comparison_id} not found.")

    # 2. Fetch associated comparison events
    ev_stmt = (
        select(ComparisonEvent)
        .where(ComparisonEvent.comparison_id == comparison_id)
        .order_by(ComparisonEvent.divergence_order.asc())
    )
    ev_result = await db.execute(ev_stmt)
    db_events = list(ev_result.scalars().all())

    # 3. Format divergences for root cause engine
    divergences: list[dict[str, Any]] = [
        {
            "category": ev.category,
            "severity": ev.severity,
            "route": ev.route,
            "event_type": ev.event_type,
            "title": ev.title,
            "description": ev.description,
            "divergence_order": ev.divergence_order,
            "is_root_cause_candidate": (ev.divergence_order == 1),
            "evidence": ev.evidence,
        }
        for ev in db_events
    ]

    # 4. Generate AI analysis report
    report = generate_root_cause_report(
        comparison_id=comparison_id,
        repository_name=comparison.repository_name,
        base_commit=comparison.base_commit,
        head_commit=comparison.head_commit,
        divergences=divergences,
        git_diff_files=git_diff_files,
        changed_functions=changed_functions,
    )

    # 5. Persist RootCauseReport
    conf_band = ConfidenceLevel(report.confidence.band.value)
    report_record = RootCauseReport(
        id=report.analysis_id,
        comparison_id=comparison_id,
        repository_name=report.repository_name,
        base_commit=report.base_commit,
        head_commit=report.head_commit,
        status=AnalysisStatus.COMPLETED,
        summary=report.summary,
        confidence_score=report.confidence.score,
        confidence_band=conf_band,
        primary_candidate=report.primary_candidate.to_dict(),
        secondary_candidates=[c.to_dict() for c in report.secondary_candidates],
        repair_plan=[r.to_dict() for r in report.repair_plan],
        explanation=report.explanation,
        bob_prompt=report.bob_prompt,
    )
    db.add(report_record)

    # 6. Persist individual evidence records
    for item in report.evidence_items:
        ev_record = RootCauseEvidence(
            id=uuid.uuid4(),
            report_id=report.analysis_id,
            category=item.category.value,
            severity=item.severity.value,
            route=item.route,
            event_type=item.event_type,
            title=item.title,
            description=item.description,
            file_path=item.file_path,
            function_name=item.function_name,
            divergence_order=item.divergence_order,
            is_root_cause_candidate=item.is_root_cause_candidate,
            evidence_metadata=item.evidence_metadata,
        )
        db.add(ev_record)

    await db.commit()
    await db.refresh(report_record)

    logger.info(
        "root_cause_service: analysis created id=%s comparison_id=%s confidence=%d",
        report_record.id,
        comparison_id,
        report_record.confidence_score,
    )
    return report_record


async def get_root_cause_report_by_id(
    db: AsyncSession,
    report_id: uuid.UUID,
) -> RootCauseReport | None:
    """Retrieve an AI root cause report by ID."""
    stmt = select(RootCauseReport).where(RootCauseReport.id == report_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_root_cause_report_by_comparison_id(
    db: AsyncSession,
    comparison_id: uuid.UUID,
) -> RootCauseReport | None:
    """Retrieve latest AI root cause report for a comparison ID."""
    stmt = (
        select(RootCauseReport)
        .where(RootCauseReport.comparison_id == comparison_id)
        .order_by(RootCauseReport.created_at.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().first()


async def get_root_cause_evidence(
    db: AsyncSession,
    report_id: uuid.UUID,
    category: str | None = None,
    severity: str | None = None,
) -> list[RootCauseEvidence]:
    """Retrieve ordered evidence records for a root cause report."""
    stmt = select(RootCauseEvidence).where(RootCauseEvidence.report_id == report_id)
    if category:
        stmt = stmt.where(RootCauseEvidence.category == category.lower())
    if severity:
        stmt = stmt.where(RootCauseEvidence.severity == severity.upper())

    stmt = stmt.order_by(RootCauseEvidence.divergence_order.asc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def list_root_cause_reports(
    db: AsyncSession,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[RootCauseReport], int]:
    """Retrieve paginated list of root cause reports and total count."""
    count_stmt = select(func.count(RootCauseReport.id))
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = (
        select(RootCauseReport)
        .order_by(RootCauseReport.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(stmt)
    reports = list(result.scalars().all())
    return reports, total
