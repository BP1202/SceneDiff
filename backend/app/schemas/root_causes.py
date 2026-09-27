"""Pydantic schemas for AI Root Cause Analysis API (Sprint 5 - Task 43).

Defines request and response data contracts for IBM Bob 2.0 root cause endpoints.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
import uuid

from pydantic import BaseModel, ConfigDict, Field


class AnalyzeRequest(BaseModel):
    """Payload to trigger AI root cause analysis on a behavior comparison."""

    comparison_id: uuid.UUID = Field(
        ...,
        description="UUID of completed BehaviorComparison record.",
    )
    git_diff_files: list[str] | None = Field(
        default=None,
        description="Optional list of modified file paths from git diff.",
    )
    changed_functions: list[dict[str, str]] | None = Field(
        default=None,
        description="Optional list of changed functions.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "comparison_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "git_diff_files": ["src/pages/Login.tsx", "backend/auth/routes.py"],
                "changed_functions": [
                    {"file": "backend/auth/routes.py", "function": "login_handler"}
                ],
            }
        }
    )


class RootCauseCandidateSchema(BaseModel):
    """Pydantic schema for a suspected root cause candidate."""

    reason: str
    evidence_type: str
    severity: str
    score: float
    file_path: str | None = None
    function_name: str | None = None
    route: str = "global"


class ConfidenceScoreSchema(BaseModel):
    """Pydantic schema for confidence score breakdown."""

    score: int
    band: str
    severity_points: int
    timeline_points: int
    evidence_points: int
    git_points: int
    rationale: str


class RepairRecommendationSchema(BaseModel):
    """Pydantic schema for an actionable repair suggestion."""

    target_file: str | None = None
    target_function: str | None = None
    issue_summary: str
    suggested_action: str
    checklist: list[str] = Field(default_factory=list)


class RootCauseEvidenceItemSchema(BaseModel):
    """Pydantic schema for an individual persisted evidence record."""

    id: uuid.UUID
    report_id: uuid.UUID
    category: str
    severity: str
    route: str
    event_type: str
    title: str
    description: str
    file_path: str | None = None
    function_name: str | None = None
    divergence_order: int
    is_root_cause_candidate: bool
    evidence_metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RootCauseReportResponse(BaseModel):
    """Pydantic schema for the persisted root cause report."""

    id: uuid.UUID
    comparison_id: uuid.UUID
    repository_name: str
    base_commit: str
    head_commit: str
    status: str
    summary: str
    confidence_score: int
    confidence_band: str
    primary_candidate: dict[str, Any]
    secondary_candidates: list[dict[str, Any]] = Field(default_factory=list)
    repair_plan: list[dict[str, Any]] = Field(default_factory=list)
    explanation: dict[str, Any] = Field(default_factory=dict)
    bob_prompt: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
