"""Pydantic schemas for the health endpoint.

These schemas define the API contract response envelope and health-specific
data payload.  ORM models never appear here.
"""
from typing import Any

from pydantic import BaseModel


class ApiResponse(BaseModel):
    """Standard envelope returned by every SceneDiff endpoint.

    Follows the contract defined in api-contract.md:
        success  — whether the request succeeded
        data     — endpoint-specific payload (None on error)
        error    — human-readable error message (None on success)
        metadata — request context (request_id, api_version, …)
    """

    success: bool
    data: Any | None = None
    error: str | None = None
    metadata: dict[str, Any] = {}


class HealthData(BaseModel):
    """Payload returned inside ApiResponse.data for the health endpoint."""

    status: str
    version: str
