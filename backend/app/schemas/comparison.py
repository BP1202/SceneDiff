"""Pydantic schemas for behavior comparison endpoints (Sprint 4).

Defines the API contract for comparing two runtime traces and retrieving
the Behavior Diff Report for IBM Bob.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
import uuid

from pydantic import BaseModel, Field, field_validator

_MIN_SHA = 7
_MAX_SHA = 40
_REPO_RE = r"^[A-Za-z0-9_.\-]+(\/[A-Za-z0-9_.\-]+)?$"


class CompareRequest(BaseModel):
    """Request payload to initiate a behavior comparison."""

    repository_name: str = Field(
        default="SceneDiff",
        min_length=1,
        max_length=255,
        pattern=_REPO_RE,
        description="Repository identifier.",
    )
    base_commit: str = Field(
        ...,
        min_length=_MIN_SHA,
        max_length=_MAX_SHA,
        description="Base (before) commit SHA.",
    )
    head_commit: str = Field(
        ...,
        min_length=_MIN_SHA,
        max_length=_MAX_SHA,
        description="Head (after) commit SHA.",
    )
    base_artifact: dict[str, Any] = Field(
        default_factory=dict,
        description="Base runtime trace artifact dict.",
    )
    head_artifact: dict[str, Any] = Field(
        default_factory=dict,
        description="Head runtime trace artifact dict.",
    )

    @field_validator("base_commit", "head_commit")
    @classmethod
    def _validate_sha(cls, v: str) -> str:
        if not all(c in "0123456789abcdefABCDEF" for c in v):
            msg = "Commit SHA must be hexadecimal."
            raise ValueError(msg)
        return v.lower()


class ComparisonSummarySchema(BaseModel):
    """Numerical summary of differences across categories."""

    total_divergences: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    info_count: int = 0
    dom_count: int = 0
    network_count: int = 0
    console_count: int = 0
    storage_count: int = 0
    performance_count: int = 0


class ComparisonEventSchema(BaseModel):
    """Schema for a single behavior divergence item."""

    category: str
    severity: str
    route: str
    event_type: str
    title: str
    description: str
    divergence_order: int
    is_root_cause_candidate: bool = False
    base_value: dict[str, Any] | None = None
    head_value: dict[str, Any] | None = None
    evidence: dict[str, Any] | None = None


class ComparisonEventRecordResponse(BaseModel):
    """Schema for a persisted comparison event record from DB."""

    id: uuid.UUID
    comparison_id: uuid.UUID
    category: str
    severity: str
    route: str
    event_type: str
    title: str
    description: str
    divergence_order: int
    base_value: dict[str, Any] | None = None
    head_value: dict[str, Any] | None = None
    evidence: dict[str, Any] | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ComparisonRecordResponse(BaseModel):
    """Schema for a persisted BehaviorComparison record from DB."""

    id: uuid.UUID
    repository_name: str
    base_commit: str
    head_commit: str
    status: str
    verdict: str
    highest_severity: str
    total_divergences: int
    summary: dict[str, Any] | None = None
    first_divergence: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BehaviorDiffReportSchema(BaseModel):
    """The canonical Behavior Diff Report schema consumed by IBM Bob."""

    repository_name: str
    base_commit: str
    head_commit: str
    verdict: str
    highest_severity: str
    summary: ComparisonSummarySchema
    first_meaningful_divergence: ComparisonEventSchema | None = None
    divergence_timeline: list[ComparisonEventSchema] = Field(default_factory=list)
