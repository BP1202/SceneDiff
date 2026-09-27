"""Task 33 — Runtime Collector REST API.

Endpoints
---------
POST /api/v1/runtime/collect
    Start a new Playwright collection session. Returns a session ID.
    The actual collection runs asynchronously via a background task.

GET /api/v1/runtime/{session_id}
    Poll the status and progress of a collection session.

GET /api/v1/runtime/{session_id}/artifacts
    Return the normalized runtime trace artifacts once complete.

Design rules
------------
- No business logic in routes — all logic in collector.py / storage.
- Collection runs as a FastAPI BackgroundTask (non-blocking).
- Session state is held in a module-level dict for Sprint 3 scope.
  (Sprint 4 will move this to the database.)
- Request body never logged.
"""

from __future__ import annotations

import logging
from typing import Any
import uuid

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field, field_validator

from app.runtime.collector import CollectionResult, JourneyStep, run_collection

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/runtime", tags=["runtime"])


# ---------------------------------------------------------------------------
# In-memory session store (Sprint 3 scope — replaced by DB in Sprint 4)
# ---------------------------------------------------------------------------

_SESSION_STATUS: dict[str, str] = {}  # id → status
_SESSION_PROGRESS: dict[str, int] = {}  # id → 0-100
_SESSION_STAGE: dict[str, str] = {}  # id → current_step
_SESSION_RESULT: dict[str, dict[str, Any]] = {}  # id → artifact dict
_SESSION_ERROR: dict[str, str] = {}  # id → error message

_STATUS_PENDING = "PENDING"
_STATUS_COLLECTING = "COLLECTING"
_STATUS_COMPLETED = "COMPLETED"
_STATUS_FAILED = "FAILED"


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------


class JourneyStepRequest(BaseModel):
    """One step in the scripted user journey."""

    url: str = Field(..., description="Absolute URL to navigate to.")
    label: str = Field(..., min_length=1, max_length=128, description="Route label.")
    wait_for_selector: str | None = Field(
        None, description="Optional CSS selector to wait for."
    )


class CollectRequest(BaseModel):
    """Request body for POST /runtime/collect."""

    base_commit: str = Field(
        ...,
        min_length=7,
        max_length=40,
        pattern=r"^[0-9a-f]{7,40}$",
        description="Base commit SHA (7-40 hex chars).",
    )
    head_commit: str = Field(
        ...,
        min_length=7,
        max_length=40,
        pattern=r"^[0-9a-f]{7,40}$",
        description="Head commit SHA (7-40 hex chars).",
    )
    base_url: str = Field(
        ...,
        description="Application root URL (e.g. http://localhost:3000).",
    )
    journey: list[JourneyStepRequest] = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Ordered list of journey steps (1-20).",
    )
    capture_screenshots: bool = Field(
        True,
        description="Whether to capture screenshots at each step.",
    )

    @field_validator("journey")
    @classmethod
    def journey_urls_must_be_http(
        cls, steps: list[JourneyStepRequest]
    ) -> list[JourneyStepRequest]:
        for step in steps:
            if not (step.url.startswith("http://") or step.url.startswith("https://")):
                raise ValueError(f"Journey step URL must be http/https: {step.url!r}")
        return steps


class CollectResponse(BaseModel):
    """Response for POST /runtime/collect."""

    session_id: str
    status: str
    message: str


class StatusResponse(BaseModel):
    """Response for GET /runtime/{session_id}."""

    session_id: str
    status: str
    progress: int
    current_step: str


class ArtifactsResponse(BaseModel):
    """Response for GET /runtime/{session_id}/artifacts."""

    session_id: str
    status: str
    base_commit: str
    head_commit: str
    artifact: dict[str, Any]


# ---------------------------------------------------------------------------
# Background task
# ---------------------------------------------------------------------------


async def _run_collection_task(
    session_id: str,
    request: CollectRequest,
) -> None:
    """Background task: run the collection pipeline and update session state."""
    try:
        _SESSION_STATUS[session_id] = _STATUS_COLLECTING
        _SESSION_PROGRESS[session_id] = 10
        _SESSION_STAGE[session_id] = "browser_launch"

        journey = [
            JourneyStep(
                url=step.url,
                label=step.label,
                wait_for_selector=step.wait_for_selector,
            )
            for step in request.journey
        ]

        _SESSION_PROGRESS[session_id] = 30
        _SESSION_STAGE[session_id] = "base_commit_collection"

        result: CollectionResult = await run_collection(
            base_commit=request.base_commit,
            head_commit=request.head_commit,
            base_url=request.base_url,
            journey=journey,
            capture_screenshots=request.capture_screenshots,
        )

        _SESSION_PROGRESS[session_id] = 90
        _SESSION_STAGE[session_id] = "normalizing"

        _SESSION_RESULT[session_id] = {
            "base_commit": result.base_commit,
            "head_commit": result.head_commit,
            "base": result.base.to_dict(),
            "head": result.head.to_dict(),
        }

        _SESSION_STATUS[session_id] = _STATUS_COMPLETED
        _SESSION_PROGRESS[session_id] = 100
        _SESSION_STAGE[session_id] = "completed"

        logger.info("runtime.api: collection complete session=%s", session_id)

    except Exception as exc:
        _SESSION_STATUS[session_id] = _STATUS_FAILED
        _SESSION_PROGRESS[session_id] = 0
        _SESSION_STAGE[session_id] = "failed"
        _SESSION_ERROR[session_id] = str(exc)
        logger.error(
            "runtime.api: collection failed session=%s error=%s",
            session_id,
            str(exc)[:200],
        )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/collect",
    response_model=CollectResponse,
    status_code=202,
    summary="Start runtime collection",
    description=(
        "Launch a Playwright browser session to collect runtime traces "
        "for base_commit and head_commit. Returns a session ID for polling."
    ),
)
async def start_collection(
    request: CollectRequest,
    background_tasks: BackgroundTasks,
) -> CollectResponse:
    """POST /api/v1/runtime/collect — start a new collection session."""
    session_id = str(uuid.uuid4())

    _SESSION_STATUS[session_id] = _STATUS_PENDING
    _SESSION_PROGRESS[session_id] = 0
    _SESSION_STAGE[session_id] = "queued"

    background_tasks.add_task(_run_collection_task, session_id, request)

    logger.info(
        "runtime.api: collection queued session=%s base=%s head=%s",
        session_id,
        request.base_commit,
        request.head_commit,
    )

    return CollectResponse(
        session_id=session_id,
        status=_STATUS_PENDING,
        message="Collection session queued. Poll /runtime/{session_id} for status.",
    )


@router.get(
    "/{session_id}",
    response_model=StatusResponse,
    summary="Get collection status",
    description="Poll the status and progress of a runtime collection session.",
)
async def get_collection_status(session_id: str) -> StatusResponse:
    """GET /api/v1/runtime/{session_id} — poll status."""
    if session_id not in _SESSION_STATUS:
        raise HTTPException(status_code=404, detail="Collection session not found.")

    return StatusResponse(
        session_id=session_id,
        status=_SESSION_STATUS[session_id],
        progress=_SESSION_PROGRESS.get(session_id, 0),
        current_step=_SESSION_STAGE.get(session_id, "unknown"),
    )


@router.get(
    "/{session_id}/artifacts",
    response_model=ArtifactsResponse,
    summary="Get collection artifacts",
    description=(
        "Return the normalized runtime trace artifact once the collection "
        "session is COMPLETED."
    ),
)
async def get_artifacts(session_id: str) -> ArtifactsResponse:
    """GET /api/v1/runtime/{session_id}/artifacts — retrieve artifacts."""
    if session_id not in _SESSION_STATUS:
        raise HTTPException(status_code=404, detail="Collection session not found.")

    status = _SESSION_STATUS[session_id]
    if status != _STATUS_COMPLETED:
        raise HTTPException(
            status_code=409,
            detail=f"Collection session is not COMPLETED (current: {status}).",
        )

    result = _SESSION_RESULT[session_id]
    return ArtifactsResponse(
        session_id=session_id,
        status=status,
        base_commit=result["base_commit"],
        head_commit=result["head_commit"],
        artifact=result,
    )
