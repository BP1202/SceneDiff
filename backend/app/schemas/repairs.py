"""Pydantic schemas for AI Repair Engine API (Sprint 6 - Task 57).

Defines request and response contracts for IBM Bob 2.0 autonomous repair endpoints.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
import uuid

from pydantic import BaseModel, ConfigDict, Field


class CreateRepairRequest(BaseModel):
    """Payload to trigger AI repair planning and patch generation."""

    root_cause_id: uuid.UUID = Field(
        ...,
        description="UUID of completed RootCauseReport record from Sprint 5.",
    )
    provider: str = Field(
        default="TemplatePatchProvider",
        description="Patch provider ('TemplatePatchProvider', 'MockPatchProvider').",
    )
    override_target_file: str | None = Field(
        default=None,
        description="Optional override for target file path to repair.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "root_cause_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "provider": "TemplatePatchProvider",
            }
        }
    )


class RepairPatchSchema(BaseModel):
    """Schema for a persisted Git unified patch."""

    id: uuid.UUID
    report_id: uuid.UUID
    target_file: str
    diff_content: str
    lines_added: int
    lines_removed: int
    is_validated: bool
    risk_level: str
    validation_notes: list[Any] = Field(default_factory=list)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RepairReportSummaryResponse(BaseModel):
    """High-level summary of an AI repair analysis."""

    id: uuid.UUID
    root_cause_id: uuid.UUID
    comparison_id: uuid.UUID
    repository_name: str
    status: str
    summary: str
    risk_level: str
    risk_score: int
    repair_confidence: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RepairReportDetailResponse(BaseModel):
    """Complete diagnostic and repair report for IBM Bob and frontend."""

    id: uuid.UUID
    root_cause_id: uuid.UUID
    comparison_id: uuid.UUID
    repository_name: str
    status: str
    summary: str
    risk_level: str
    risk_score: int
    repair_confidence: int
    plan: dict[str, Any] = Field(default_factory=dict)
    rollback_plan: dict[str, Any] = Field(default_factory=dict)
    markdown_report: str
    pr_summary: str
    patches: list[RepairPatchSchema] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RepairPatchResponse(BaseModel):
    """Unified patch metadata and download details."""

    report_id: uuid.UUID
    target_file: str
    lines_added: int
    lines_removed: int
    is_validated: bool
    risk_level: str
    raw_git_patch: str
