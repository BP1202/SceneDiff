"""Health endpoint — /api/v1/health

Responsibilities:
- Report application liveness.
- Return the standard ApiResponse envelope.
- No business logic; no direct database access.
"""
from fastapi import APIRouter, Request

from app.schemas.health import ApiResponse, HealthData

router = APIRouter(tags=["health"])

_VERSION = "0.1.0"


@router.get(
    "/health",
    response_model=ApiResponse,
    summary="Application health check",
    description=(
        "Returns 200 when the application is running. "
        "Database connectivity is verified in a dedicated readiness check."
    ),
)
async def health_check(request: Request) -> ApiResponse:
    """Return application liveness status."""
    request_id: str = getattr(request.state, "request_id", "")
    return ApiResponse(
        success=True,
        data=HealthData(status="ok", version=_VERSION),
        metadata={"request_id": request_id, "api_version": "v1"},
    )
