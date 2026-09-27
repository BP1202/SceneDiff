"""Async Comparison Service (Sprint 4).

Coordinates runtime artifact comparisons, computes verdicts and timelines,
and persists behavior comparisons and events to PostgreSQL.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any
import uuid

from sqlalchemy import select

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

from app.behavior.comparator import (
    BehaviorDiffReport,
    compare_runtime_artifacts,
)
from app.models.behavior_comparison import (
    BehaviorComparison,
    ComparisonEvent,
    ComparisonStatus,
)

logger = logging.getLogger(__name__)


async def create_comparison(
    db: AsyncSession,
    repository_name: str,
    base_commit: str,
    head_commit: str,
    base_artifact: dict[str, Any],
    head_artifact: dict[str, Any],
) -> tuple[BehaviorComparison, BehaviorDiffReport]:
    """Execute behavior comparison and persist results to the database.

    Args:
        db: Active async database session.
        repository_name: Repository name.
        base_commit: Base commit SHA.
        head_commit: Head commit SHA.
        base_artifact: Normalized Base runtime trace dict.
        head_artifact: Normalized Head runtime trace dict.

    Returns:
        tuple (BehaviorComparison ORM instance, BehaviorDiffReport domain report).
    """
    # 1. Run in-memory comparison
    report = compare_runtime_artifacts(
        base_artifact=base_artifact,
        head_artifact=head_artifact,
        repository_name=repository_name,
    )

    first_div_dict = (
        report.first_meaningful_divergence.to_dict()
        if report.first_meaningful_divergence
        else None
    )

    # 2. Create parent record
    comparison = BehaviorComparison(
        repository_name=repository_name,
        base_commit=base_commit,
        head_commit=head_commit,
        status=ComparisonStatus.COMPLETED,
        verdict=report.verdict.value,
        highest_severity=report.highest_severity.value,
        total_divergences=report.summary.total_divergences,
        summary=report.summary.to_dict(),
        first_divergence=first_div_dict,
    )
    db.add(comparison)
    await db.flush()  # Populates comparison.id

    # 3. Create child event records
    for div in report.divergence_timeline:
        event = ComparisonEvent(
            comparison_id=comparison.id,
            category=div.category,
            severity=div.severity.value,
            route=div.route,
            event_type=div.event_type,
            title=div.title,
            description=div.description,
            divergence_order=div.divergence_order,
            base_value=div.base_value,
            head_value=div.head_value,
            evidence=div.evidence,
        )
        db.add(event)

    await db.commit()
    await db.refresh(comparison)

    logger.info(
        "comparison_service: comparison persisted id=%s verdict=%s divergences=%d",
        comparison.id,
        comparison.verdict,
        comparison.total_divergences,
    )
    return comparison, report


async def get_comparison_by_id(
    db: AsyncSession,
    comparison_id: uuid.UUID,
) -> BehaviorComparison | None:
    """Fetch a single comparison record by primary key."""
    result = await db.execute(
        select(BehaviorComparison).where(BehaviorComparison.id == comparison_id)
    )
    return result.scalar_one_or_none()


async def get_comparison_events(
    db: AsyncSession,
    comparison_id: uuid.UUID,
    category: str | None = None,
    severity: str | None = None,
) -> list[ComparisonEvent]:
    """Fetch all comparison events for a comparison, ordered by divergence_order."""
    query = (
        select(ComparisonEvent)
        .where(ComparisonEvent.comparison_id == comparison_id)
        .order_by(ComparisonEvent.divergence_order)
    )
    if category:
        query = query.where(ComparisonEvent.category == category.lower())
    if severity:
        query = query.where(ComparisonEvent.severity == severity.upper())

    result = await db.execute(query)
    return list(result.scalars().all())
