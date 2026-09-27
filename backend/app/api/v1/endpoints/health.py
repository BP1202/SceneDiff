"""Health endpoint — /api/v1/health

Responsibilities:
- Verify FastAPI application is running.
- Verify PostgreSQL database is reachable via AsyncSession and SELECT 1.
- Measure database latency in milliseconds.
- Return the standard ApiResponse envelope with HealthData and DatabaseHealth.
- Catch database connection errors without leaking credentials or stack traces.
- Return degraded status and 503 HTTP status code when database connectivity fails.
"""

from datetime import UTC, datetime
import logging
import time
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.health import ApiResponse, DatabaseHealth, HealthData

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])

_VERSION = "0.1.0"


@router.get(
    "/health",
    response_model=ApiResponse,
    summary="Application and infrastructure health check",
    description=(
        "Returns 200 when application and database are healthy. "
        "Returns 503 with degraded status when database connectivity fails."
    ),
)
async def health_check(
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse:
    """Check application and database health status."""
    request_id: str = getattr(request.state, "request_id", "")
    now_iso = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    try:
        start_time = time.perf_counter()
        await db.execute(text("SELECT 1"))
        latency_ms = int(round((time.perf_counter() - start_time) * 1000))

        db_health = DatabaseHealth(
            status="connected",
            latency_ms=latency_ms,
            engine="postgresql",
        )
        health_data = HealthData(
            status="ok",
            version=_VERSION,
            database=db_health,
        )
        return ApiResponse(
            success=True,
            data=health_data,
            error=None,
            metadata={"request_id": request_id, "api_version": "v1"},
            request_id=request_id,
            timestamp=now_iso,
        )
    except Exception as exc:
        # Never leak connection details, hostnames, passwords, or stack traces
        logger.warning(
            "Database health check failed: %s",
            type(exc).__name__,
        )
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

        db_health = DatabaseHealth(
            status="disconnected",
            latency_ms=None,
            engine="postgresql",
        )
        health_data = HealthData(
            status="degraded",
            version=_VERSION,
            database=db_health,
        )
        return ApiResponse(
            success=False,
            data=health_data,
            error={
                "code": "DATABASE_UNAVAILABLE",
                "message": "Database health check failed",
            },
            metadata={"request_id": request_id, "api_version": "v1"},
            request_id=request_id,
            timestamp=now_iso,
        )
