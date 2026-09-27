"""Pydantic schemas for the health endpoint.

These schemas define the API contract response envelope and health-specific
data payload.  ORM models never appear here.
"""

from typing import Any

from pydantic import BaseModel, Field


class DatabaseHealth(BaseModel):
    """Database connectivity and latency details."""

    status: str
    latency_ms: int | None = None
    engine: str = "postgresql"


class HealthData(BaseModel):
    """Payload returned inside ApiResponse.data for the health endpoint."""

    status: str
    version: str
    database: DatabaseHealth


class ApiResponse(BaseModel):
    """Standard envelope returned by every SceneDiff endpoint.

    Follows the contract defined in api-contract.md:
        success  — whether the request succeeded
        data     — endpoint-specific payload (None on error)
        error    — human-readable error or error object (None on success)
        metadata — request context (request_id, api_version, …)
        request_id — unique request identifier
        timestamp  — ISO 8601 UTC timestamp
    """

    success: bool
    data: Any | None = None
    error: Any | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    request_id: str | None = None
    timestamp: str | None = None
