"""Behavior Event API endpoints.

GET /api/v1/traces/{id}/events — list events for a session (paginated, filtered)

Route handlers contain validation and serialization only.
All business logic lives in services/trace_storage.py.
"""

from datetime import UTC, datetime
import logging
from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.traces import (
    ApiResponse,
    PaginatedMeta,
    TraceEventResponse,
)
from app.services import trace_storage

logger = logging.getLogger(__name__)

router = APIRouter(tags=["events"])

_MAX_LIMIT = 200


def _now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _request_id(request: Request) -> str:
    return str(getattr(request.state, "request_id", ""))


# ---------------------------------------------------------------------------
# GET /api/v1/traces/{trace_id}/events
# ---------------------------------------------------------------------------


@router.get(
    "/traces/{trace_id}/events",
    response_model=ApiResponse,
    status_code=status.HTTP_200_OK,
    summary="List behavior events for a trace session",
    description=(
        "Returns a paginated list of behavior events captured during "
        "the given trace session. Supports filtering by event_type and file_path."
    ),
)
async def list_trace_events(
    trace_id: uuid.UUID,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    event_type: Annotated[
        str | None,
        Query(description="Filter events by type string (e.g. FUNCTION_MODIFIED)."),
    ] = None,
    file_path: Annotated[
        str | None,
        Query(description="Filter events by exact file path."),
    ] = None,
    limit: Annotated[
        int,
        Query(ge=1, le=_MAX_LIMIT, description="Maximum results per page."),
    ] = 50,
    offset: Annotated[
        int,
        Query(ge=0, description="Number of results to skip."),
    ] = 0,
) -> ApiResponse:
    """List behavior events for a specific trace session."""
    request_id = _request_id(request)

    # Verify the parent session exists before fetching events.
    session = await trace_storage.get_session(db, trace_id)
    if session is None:
        raise HTTPException(
            status_code=404,
            detail=f"Trace session {trace_id} not found.",
        )

    events = await trace_storage.list_events(
        db,
        trace_session_id=trace_id,
        event_type=event_type,
        file_path=file_path,
        limit=limit,
        offset=offset,
    )

    data = [
        TraceEventResponse.model_validate(e).model_dump(mode="json") for e in events
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
            "trace_session_id": str(trace_id),
        },
        request_id=request_id,
        timestamp=_now_iso(),
    )
