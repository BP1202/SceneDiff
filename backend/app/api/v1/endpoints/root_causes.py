"""Root Cause Analysis API endpoints (Sprint 5 - Task 43).

POST /api/v1/root-causes              — run AI root cause analysis
GET  /api/v1/root-causes/{id}         — retrieve analysis summary
GET  /api/v1/root-causes/{id}/report  — retrieve full report for IBM Bob
GET  /api/v1/root-causes/{id}/evidence— retrieve ordered evidence chain
GET  /api/v1/root-causes              — list analysis reports

Route handlers validate requests and serialize responses.
Business logic is delegated to app.services.root_cause_service.
"""

from datetime import UTC, datetime
import logging
from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.root_causes import (
    AnalyzeRequest,
    RootCauseEvidenceItemSchema,
    RootCauseReportResponse,
)
from app.schemas.traces import ApiResponse, PaginatedMeta
from app.services import root_cause_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["root-causes"])


def _now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _request_id(request: Request) -> str:
    return str(getattr(request.state, "request_id", ""))


# ---------------------------------------------------------------------------
# POST /api/v1/root-causes
# ---------------------------------------------------------------------------


@router.post(
    "/root-causes",
    response_model=ApiResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Run AI root cause analysis",
    description=(
        "Executes causal reasoning, generates root cause candidates, computes "
        "deterministic confidence, and stores the diagnosis for IBM Bob."
    ),
)
async def create_root_cause_analysis(
    request: Request,
    body: AnalyzeRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse:
    """Execute AI root cause analysis for a completed behavior comparison."""
    req_id = _request_id(request)

    try:
        report_record = await root_cause_service.create_root_cause_analysis(
            db,
            comparison_id=body.comparison_id,
            git_diff_files=body.git_diff_files,
            changed_functions=body.changed_functions,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return ApiResponse(
        success=True,
        data=RootCauseReportResponse.model_validate(report_record).model_dump(
            mode="json"
        ),
        metadata={
            "request_id": req_id,
            "timestamp": _now_iso(),
        },
    )


# ---------------------------------------------------------------------------
# GET /api/v1/root-causes/{id}
# ---------------------------------------------------------------------------


@router.get(
    "/root-causes/{analysis_id}",
    response_model=ApiResponse,
    summary="Get root cause analysis summary",
    description="Returns high-level summary, confidence score, and primary suspect.",
)
async def get_root_cause_analysis(
    analysis_id: uuid.UUID,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse:
    """Retrieve an AI root cause report by ID."""
    req_id = _request_id(request)

    report = await root_cause_service.get_root_cause_report_by_id(
        db,
        analysis_id,
    )
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Root cause report {analysis_id} not found.",
        )

    return ApiResponse(
        success=True,
        data=RootCauseReportResponse.model_validate(report).model_dump(mode="json"),
        metadata={
            "request_id": req_id,
            "timestamp": _now_iso(),
        },
    )


# ---------------------------------------------------------------------------
# GET /api/v1/root-causes/{id}/report
# ---------------------------------------------------------------------------


@router.get(
    "/root-causes/{analysis_id}/report",
    response_model=ApiResponse,
    summary="Get full IBM Bob diagnostic report",
    description="Returns complete report with prompt, explanation, and repair plan.",
)
async def get_root_cause_report(
    analysis_id: uuid.UUID,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse:
    """Retrieve complete AI diagnostic report for IBM Bob."""
    req_id = _request_id(request)

    report = await root_cause_service.get_root_cause_report_by_id(
        db,
        analysis_id,
    )
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Root cause report {analysis_id} not found.",
        )

    report_data = {
        "analysis_id": str(report.id),
        "comparison_id": str(report.comparison_id),
        "repository_name": report.repository_name,
        "base_commit": report.base_commit,
        "head_commit": report.head_commit,
        "summary": report.summary,
        "confidence_score": report.confidence_score,
        "confidence_band": report.confidence_band.value,
        "primary_candidate": report.primary_candidate,
        "secondary_candidates": report.secondary_candidates,
        "repair_plan": report.repair_plan,
        "explanation": report.explanation,
        "bob_prompt": report.bob_prompt,
    }

    return ApiResponse(
        success=True,
        data=report_data,
        metadata={
            "request_id": req_id,
            "timestamp": _now_iso(),
        },
    )


# ---------------------------------------------------------------------------
# GET /api/v1/root-causes/{id}/evidence
# ---------------------------------------------------------------------------


@router.get(
    "/root-causes/{analysis_id}/evidence",
    response_model=ApiResponse,
    summary="Get root cause evidence chain",
    description="Returns ordered correlated evidence items supporting the diagnosis.",
)
async def get_root_cause_evidence(
    analysis_id: uuid.UUID,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    category: Annotated[
        str | None,
        Query(
            description=(
                "Filter by category (network, console, dom, storage, performance)."
            )
        ),
    ] = None,
    severity: Annotated[
        str | None,
        Query(description="Filter by severity (CRITICAL, HIGH, MEDIUM, LOW, INFO)."),
    ] = None,
) -> ApiResponse:
    """Retrieve ordered evidence records for a root cause report."""
    req_id = _request_id(request)

    report = await root_cause_service.get_root_cause_report_by_id(
        db,
        analysis_id,
    )
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Root cause report {analysis_id} not found.",
        )

    evidence_records = await root_cause_service.get_root_cause_evidence(
        db,
        report_id=analysis_id,
        category=category,
        severity=severity,
    )

    data = [
        RootCauseEvidenceItemSchema.model_validate(ev).model_dump(mode="json")
        for ev in evidence_records
    ]

    return ApiResponse(
        success=True,
        data=data,
        metadata={
            "request_id": req_id,
            "timestamp": _now_iso(),
            "total_items": len(data),
        },
    )


# ---------------------------------------------------------------------------
# GET /api/v1/root-causes
# ---------------------------------------------------------------------------


@router.get(
    "/root-causes",
    response_model=ApiResponse,
    summary="List root cause analyses",
    description="Returns paginated list of previous root cause analyses.",
)
async def list_root_causes(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ApiResponse:
    """Retrieve paginated list of root cause analysis reports."""
    req_id = _request_id(request)

    reports, total = await root_cause_service.list_root_cause_reports(
        db,
        limit=limit,
        offset=offset,
    )

    data = [
        RootCauseReportResponse.model_validate(r).model_dump(mode="json")
        for r in reports
    ]

    return ApiResponse(
        success=True,
        data=data,
        metadata={
            "request_id": req_id,
            "timestamp": _now_iso(),
            "pagination": PaginatedMeta(
                total=total,
                limit=limit,
                offset=offset,
            ).model_dump(),
        },
    )
