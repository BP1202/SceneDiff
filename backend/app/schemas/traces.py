"""Pydantic schemas for trace_sessions and trace_events endpoints.

These schemas define the API contract for Sprint 2 trace endpoints.
ORM models never appear here — only typed Pydantic models.

Schema groups:
    TraceSessionCreate     — POST /api/v1/traces request body
    TraceSessionResponse   — trace session payload inside ApiResponse.data
    TraceEventResponse     — single trace event payload
    PaginatedMeta          — pagination metadata for list endpoints
"""

from datetime import datetime
from typing import Any
import uuid

from pydantic import BaseModel, Field, field_validator

from app.models.trace_session import TraceStatus

# ---------------------------------------------------------------------------
# Shared response envelope (reused from health.py pattern)
# ---------------------------------------------------------------------------


class ApiResponse(BaseModel):
    """Standard envelope returned by every SceneDiff endpoint."""

    success: bool
    data: Any | None = None
    error: Any | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    request_id: str | None = None
    timestamp: str | None = None


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------


class PaginatedMeta(BaseModel):
    """Pagination context embedded in ApiResponse.metadata."""

    total: int
    limit: int
    offset: int


# ---------------------------------------------------------------------------
# Trace Session schemas
# ---------------------------------------------------------------------------

# Commit SHA: 7-40 hex characters (short or full SHA)
_MIN_SHA = 7
_MAX_SHA = 40
# Repository format: owner/name or plain name
_REPO_RE = r"^[A-Za-z0-9_.\-]+(\/[A-Za-z0-9_.\-]+)?$"
# Branch: letters, digits, /, -, _, .  — no spaces or special chars
_BRANCH_RE = r"^[A-Za-z0-9/_.\-]+$"


class TraceSessionCreate(BaseModel):
    """Validated input for creating a new trace session."""

    repository_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        pattern=_REPO_RE,
        description="Repository identifier, e.g. 'owner/repo' or 'repo-name'.",
    )
    base_commit: str = Field(
        ...,
        min_length=_MIN_SHA,
        max_length=_MAX_SHA,
        description="Git SHA of the base (before) commit.",
    )
    head_commit: str = Field(
        ...,
        min_length=_MIN_SHA,
        max_length=_MAX_SHA,
        description="Git SHA of the head (after) commit.",
    )
    branch: str = Field(
        ...,
        min_length=1,
        max_length=255,
        pattern=_BRANCH_RE,
        description="Branch name for the head commit.",
    )

    @field_validator("base_commit", "head_commit")
    @classmethod
    def _validate_sha(cls, v: str) -> str:
        """Reject non-hexadecimal commit SHAs."""
        if not all(c in "0123456789abcdefABCDEF" for c in v):
            msg = "Commit SHA must be a hexadecimal string."
            raise ValueError(msg)
        return v.lower()


class TraceSessionResponse(BaseModel):
    """Serialized trace session for API responses."""

    id: uuid.UUID
    repository_name: str
    base_commit: str
    head_commit: str
    branch: str
    status: TraceStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Trace Event schemas
# ---------------------------------------------------------------------------


class TraceEventResponse(BaseModel):
    """Serialized trace event for API responses."""

    id: uuid.UUID
    trace_session_id: uuid.UUID
    event_type: str
    file_path: str
    function_name: str | None
    line_number: int | None
    behavior_hash: str | None
    metadata: dict[str, Any] | None = Field(None, alias="metadata_")
    created_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}
