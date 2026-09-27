"""Trace Collection API endpoints.

POST /api/v1/traces       — create a new trace session
GET  /api/v1/traces       — list sessions (paginated, filtered)
GET  /api/v1/traces/{id}  — retrieve a single session

Route handlers contain validation and serialization only.
All business logic lives in services/trace_storage.py.
"""

from datetime import UTC, datetime
import logging
from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.trace_session import TraceStatus
from app.schemas.traces import (
    ApiResponse,
    PaginatedMeta,
    TraceSessionCreate,
    TraceSessionResponse,
)
from app.services import trace_storage

logger = logging.getLogger(__name__)

router = APIRouter(tags=["traces"])

_MAX_LIMIT = 100


def _now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _request_id(request: Request) -> str:
    return str(getattr(request.state, "request_id", ""))


# ---------------------------------------------------------------------------
# POST /api/v1/traces
# ---------------------------------------------------------------------------


@router.post(
    "/traces",
    response_model=ApiResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new trace session",
    description=(
        "Registers a new diff analysis session between two commits. "
        "Returns the session ID and initial PENDING status."
    ),
)
async def create_trace(
    request: Request,
    body: TraceSessionCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse:
    """Create a trace session from two commit SHAs."""
    request_id = _request_id(request)

    session = await trace_storage.create_trace_session(
        db,
        repository_name=body.repository_name,
        base_commit=body.base_commit,
        head_commit=body.head_commit,
        branch=body.branch,
    )

    data = TraceSessionResponse.model_validate(session)
    return ApiResponse(
        success=True,
        data=data.model_dump(mode="json"),
        error=None,
        metadata={
            "request_id": request_id,
            "api_version": "v1",
        },
        request_id=request_id,
        timestamp=_now_iso(),
    )


# ---------------------------------------------------------------------------
# GET /api/v1/traces
# ---------------------------------------------------------------------------


@router.get(
    "/traces",
    response_model=ApiResponse,
    summary="List trace sessions",
    description="Returns a paginated list of trace sessions with optional filters.",
)
async def list_traces(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    status_filter: Annotated[
        TraceStatus | None,
        Query(alias="status", description="Filter by session status."),
    ] = None,
    repository_name: Annotated[
        str | None,
        Query(description="Filter by repository name."),
    ] = None,
    limit: Annotated[
        int,
        Query(ge=1, le=_MAX_LIMIT, description="Maximum results per page."),
    ] = 20,
    offset: Annotated[
        int,
        Query(ge=0, description="Number of results to skip."),
    ] = 0,
) -> ApiResponse:
    """List trace sessions with optional status/repository filters."""
    request_id = _request_id(request)

    sessions = await trace_storage.list_sessions(
        db,
        status=status_filter,
        repository_name=repository_name,
        limit=limit,
        offset=offset,
    )

    data = [
        TraceSessionResponse.model_validate(s).model_dump(mode="json") for s in sessions
    ]
    return ApiResponse(
        success=True,
        data=data,
        error=None,
        metadata={
            "request_id": request_id,
            "api_version": "v1",
            "pagination": PaginatedMeta(
                total=len(data),
                limit=limit,
                offset=offset,
            ).model_dump(),
        },
        request_id=request_id,
        timestamp=_now_iso(),
    )


# ---------------------------------------------------------------------------
# GET /api/v1/traces/{trace_id}
# ---------------------------------------------------------------------------


@router.get(
    "/traces/{trace_id}",
    response_model=ApiResponse,
    summary="Get a trace session by ID",
    description="Returns the full trace session record for the given UUID.",
)
async def get_trace(
    trace_id: uuid.UUID,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse:
    """Fetch a single trace session by UUID."""
    request_id = _request_id(request)

    session = await trace_storage.get_session(db, trace_id)
    if session is None:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=404,
            detail=f"Trace session {trace_id} not found.",
        )

    data = TraceSessionResponse.model_validate(session)
    return ApiResponse(
        success=True,
        data=data.model_dump(mode="json"),
        error=None,
        metadata={
            "request_id": request_id,
            "api_version": "v1",
        },
        request_id=request_id,
        timestamp=_now_iso(),
    )
