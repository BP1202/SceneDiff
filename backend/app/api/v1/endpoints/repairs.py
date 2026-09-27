"""AI Repair Engine API endpoints (Sprint 6 - Task 57).

POST /api/v1/repairs              — generate AI repair plan & Git patch
GET  /api/v1/repairs/{id}         — retrieve repair summary
GET  /api/v1/repairs/{id}/report  — retrieve full diagnostic & PR report
GET  /api/v1/repairs/{id}/patch   — retrieve/download unified Git patch
GET  /api/v1/repairs              — list previous repair reports

Delegates business logic to app.services.repair_service.
"""

from datetime import UTC, datetime
import logging
from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.repairs import (
    CreateRepairRequest,
    RepairPatchResponse,
    RepairReportDetailResponse,
    RepairReportSummaryResponse,
)
from app.schemas.traces import ApiResponse, PaginatedMeta
from app.services import repair_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["repairs"])


def _now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _request_id(request: Request) -> str:
    return str(getattr(request.state, "request_id", ""))


# ---------------------------------------------------------------------------
# POST /api/v1/repairs
# ---------------------------------------------------------------------------


@router.post(
    "/repairs",
    response_model=ApiResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate AI repair plan and Git patch",
    description=(
        "Converts a completed Sprint 5 RootCauseReport into a validated Git patch, "
        "calculates operational risk, repair confidence, and backout instructions."
    ),
)
async def create_repair(
    request: Request,
    body: CreateRepairRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse:
    """Trigger autonomous repair planning and patch synthesis."""
    req_id = _request_id(request)

    try:
        report_record = await repair_service.create_repair_report(
            db,
            root_cause_id=body.root_cause_id,
            provider_name=body.provider,
            override_target_file=body.override_target_file,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return ApiResponse(
        success=True,
        data=RepairReportDetailResponse.model_validate(report_record).model_dump(
            mode="json"
        ),
        metadata={
            "request_id": req_id,
            "timestamp": _now_iso(),
        },
    )


# ---------------------------------------------------------------------------
# GET /api/v1/repairs/{id}
# ---------------------------------------------------------------------------


@router.get(
    "/repairs/{repair_id}",
    response_model=ApiResponse,
    summary="Get repair report summary",
    description="Returns high-level status, risk tier, and repair confidence.",
)
async def get_repair(
    repair_id: uuid.UUID,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse:
    """Retrieve repair report summary by ID."""
    req_id = _request_id(request)

    report = await repair_service.get_repair_report_by_id(db, repair_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repair report {repair_id} not found",
        )

    return ApiResponse(
        success=True,
        data=RepairReportSummaryResponse.model_validate(report).model_dump(mode="json"),
        metadata={
            "request_id": req_id,
            "timestamp": _now_iso(),
        },
    )


# ---------------------------------------------------------------------------
# GET /api/v1/repairs/{id}/report
# ---------------------------------------------------------------------------


@router.get(
    "/repairs/{repair_id}/report",
    response_model=ApiResponse,
    summary="Get full repair report and PR summary",
    description="Returns full repair details, Markdown report, and GitHub PR summary.",
)
async def get_repair_report(
    repair_id: uuid.UUID,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse:
    """Retrieve full repair diagnostics for IBM Bob and developers."""
    req_id = _request_id(request)

    report = await repair_service.get_repair_report_by_id(db, repair_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repair report {repair_id} not found",
        )

    return ApiResponse(
        success=True,
        data=RepairReportDetailResponse.model_validate(report).model_dump(mode="json"),
        metadata={
            "request_id": req_id,
            "timestamp": _now_iso(),
        },
    )


# ---------------------------------------------------------------------------
# GET /api/v1/repairs/{id}/patch
# ---------------------------------------------------------------------------


@router.get(
    "/repairs/{repair_id}/patch",
    response_model=None,
    summary="Download or view unified Git patch",
    description=(
        "Returns the unified diff patch as raw text/download or structured JSON."
    ),
)
async def get_repair_patch(
    repair_id: uuid.UUID,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    format: str = Query("json", description="Output format: 'json' or 'raw'"),
) -> Response | ApiResponse:
    """Retrieve unified Git patch for a repair report."""
    req_id = _request_id(request)

    report = await repair_service.get_repair_report_by_id(db, repair_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repair report {repair_id} not found",
        )

    patch = report.patches[0] if report.patches else None
    if not patch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No patch associated with repair report {repair_id}",
        )

    # If raw format requested, stream plain text diff file download
    if format.lower() == "raw":
        disposition = f'attachment; filename="repair_{repair_id}.patch"'
        return PlainTextResponse(
            content=patch.diff_content,
            media_type="text/x-diff",
            headers={"Content-Disposition": disposition},
        )

    patch_data = RepairPatchResponse(
        report_id=report.id,
        target_file=patch.target_file,
        lines_added=patch.lines_added,
        lines_removed=patch.lines_removed,
        is_validated=patch.is_validated,
        risk_level=patch.risk_level.value,
        raw_git_patch=patch.diff_content,
    )

    return ApiResponse(
        success=True,
        data=patch_data.model_dump(mode="json"),
        metadata={
            "request_id": req_id,
            "timestamp": _now_iso(),
        },
    )


# ---------------------------------------------------------------------------
# GET /api/v1/repairs
# ---------------------------------------------------------------------------


@router.get(
    "/repairs",
    response_model=ApiResponse,
    summary="List previous repair reports",
    description="Returns paginated list of repair analyses.",
)
async def list_repairs(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    repository_name: str | None = Query(None, description="Filter by repository"),
    risk_level: str | None = Query(None, description="Filter by risk level"),
) -> ApiResponse:
    """Retrieve paginated repair reports."""
    req_id = _request_id(request)

    records, total = await repair_service.list_repair_reports(
        db,
        page=page,
        page_size=page_size,
        repository_name=repository_name,
        risk_level=risk_level,
    )

    items = [
        RepairReportSummaryResponse.model_validate(r).model_dump(mode="json")
        for r in records
    ]

    offset = (page - 1) * page_size
    meta = PaginatedMeta(
        total=total,
        limit=page_size,
        offset=offset,
    )

    return ApiResponse(
        success=True,
        data=items,
        metadata={
            "request_id": req_id,
            "timestamp": _now_iso(),
            "pagination": meta.model_dump(),
        },
    )
