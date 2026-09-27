"""Behavior Comparison API endpoints (Sprint 4).

POST /api/v1/comparisons               — execute & persist behavior comparison
GET  /api/v1/comparisons/{id}          — retrieve comparison status & summary
GET  /api/v1/comparisons/{id}/report   — retrieve full Behavior Diff Report for IBM Bob
GET  /api/v1/comparisons/{id}/events   — retrieve timeline events with filtering

Route handlers validate requests and serialize responses.
Business logic is delegated to app.services.comparison_service.
"""

from datetime import UTC, datetime
import logging
from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.comparison import (
    BehaviorDiffReportSchema,
    CompareRequest,
    ComparisonEventRecordResponse,
    ComparisonEventSchema,
    ComparisonRecordResponse,
    ComparisonSummarySchema,
)
from app.schemas.traces import ApiResponse
from app.services import comparison_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["comparisons"])


def _now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _request_id(request: Request) -> str:
    return str(getattr(request.state, "request_id", ""))


# ---------------------------------------------------------------------------
# POST /api/v1/comparisons
# ---------------------------------------------------------------------------


@router.post(
    "/comparisons",
    response_model=ApiResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Run behavior comparison",
    description=(
        "Compares Base and Head runtime traces, classifies regression severity, "
        "identifies the first meaningful divergence, and persists the record."
    ),
)
async def create_comparison(
    request: Request,
    body: CompareRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse:
    """Run behavior comparison between two runtime trace artifacts."""
    req_id = _request_id(request)

    comparison, report = await comparison_service.create_comparison(
        db,
        repository_name=body.repository_name,
        base_commit=body.base_commit,
        head_commit=body.head_commit,
        base_artifact=body.base_artifact,
        head_artifact=body.head_artifact,
    )

    data = ComparisonRecordResponse.model_validate(comparison).model_dump(mode="json")
    return ApiResponse(
        success=True,
        data=data,
        error=None,
        metadata={
            "request_id": req_id,
            "api_version": "v1",
            "verdict": comparison.verdict,
            "total_divergences": comparison.total_divergences,
        },
        request_id=req_id,
        timestamp=_now_iso(),
    )


# ---------------------------------------------------------------------------
# GET /api/v1/comparisons/{comparison_id}
# ---------------------------------------------------------------------------


@router.get(
    "/comparisons/{comparison_id}",
    response_model=ApiResponse,
    summary="Get comparison by ID",
    description="Retrieve the status, summary, and verdict of a behavior comparison.",
)
async def get_comparison(
    comparison_id: uuid.UUID,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse:
    """Retrieve comparison status and metadata."""
    req_id = _request_id(request)

    comparison = await comparison_service.get_comparison_by_id(db, comparison_id)
    if comparison is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Behavior comparison {comparison_id} not found.",
        )

    data = ComparisonRecordResponse.model_validate(comparison).model_dump(mode="json")
    return ApiResponse(
        success=True,
        data=data,
        error=None,
        metadata={
            "request_id": req_id,
            "api_version": "v1",
        },
        request_id=req_id,
        timestamp=_now_iso(),
    )


# ---------------------------------------------------------------------------
# GET /api/v1/comparisons/{comparison_id}/report
# ---------------------------------------------------------------------------


@router.get(
    "/comparisons/{comparison_id}/report",
    response_model=ApiResponse,
    summary="Get Behavior Diff Report for IBM Bob",
    description=(
        "Returns the full canonical Behavior Diff Report "
        "including first divergence and timeline."
    ),
)
async def get_comparison_report(
    comparison_id: uuid.UUID,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse:
    """Retrieve full Behavior Diff Report consumed by IBM Bob."""
    req_id = _request_id(request)

    comparison = await comparison_service.get_comparison_by_id(db, comparison_id)
    if comparison is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Behavior comparison {comparison_id} not found.",
        )

    events = await comparison_service.get_comparison_events(db, comparison_id)

    # Reconstruct report structure
    summary_data = comparison.summary or {}
    timeline = [
        ComparisonEventSchema(
            category=ev.category,
            severity=ev.severity,
            route=ev.route,
            event_type=ev.event_type,
            title=ev.title,
            description=ev.description,
            divergence_order=ev.divergence_order,
            is_root_cause_candidate=(
                comparison.first_divergence is not None
                and comparison.first_divergence.get("divergence_order")
                == ev.divergence_order
            ),
            base_value=ev.base_value,
            head_value=ev.head_value,
            evidence=ev.evidence,
        )
        for ev in events
    ]

    first_div = (
        ComparisonEventSchema(**comparison.first_divergence)
        if comparison.first_divergence
        else None
    )

    report_schema = BehaviorDiffReportSchema(
        repository_name=comparison.repository_name,
        base_commit=comparison.base_commit,
        head_commit=comparison.head_commit,
        verdict=comparison.verdict,
        highest_severity=comparison.highest_severity,
        summary=ComparisonSummarySchema(**summary_data),
        first_meaningful_divergence=first_div,
        divergence_timeline=timeline,
    )

    return ApiResponse(
        success=True,
        data=report_schema.model_dump(mode="json"),
        error=None,
        metadata={
            "request_id": req_id,
            "api_version": "v1",
        },
        request_id=req_id,
        timestamp=_now_iso(),
    )


# ---------------------------------------------------------------------------
# GET /api/v1/comparisons/{comparison_id}/events
# ---------------------------------------------------------------------------


@router.get(
    "/comparisons/{comparison_id}/events",
    response_model=ApiResponse,
    summary="Get comparison events timeline",
    description=(
        "Returns ordered comparison events with optional category or severity filters."
    ),
)
async def get_comparison_events(
    comparison_id: uuid.UUID,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    category: Annotated[
        str | None,
        Query(
            description=(
                "Filter by category (dom, network, console, storage, performance)."
            )
        ),
    ] = None,
    severity: Annotated[
        str | None,
        Query(description="Filter by severity (CRITICAL, HIGH, MEDIUM, LOW, INFO)."),
    ] = None,
) -> ApiResponse:
    """Retrieve ordered divergence events for a comparison."""
    req_id = _request_id(request)

    comparison = await comparison_service.get_comparison_by_id(db, comparison_id)
    if comparison is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Behavior comparison {comparison_id} not found.",
        )

    events = await comparison_service.get_comparison_events(
        db,
        comparison_id=comparison_id,
        category=category,
        severity=severity,
    )

    data = [
        ComparisonEventRecordResponse.model_validate(ev).model_dump(mode="json")
        for ev in events
    ]

    return ApiResponse(
        success=True,
        data=data,
        error=None,
        metadata={
            "request_id": req_id,
            "api_version": "v1",
            "total_events": len(data),
        },
        request_id=req_id,
        timestamp=_now_iso(),
    )
