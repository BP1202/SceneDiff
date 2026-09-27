"""Tests for global exception handlers and normalized error envelopes."""

from datetime import datetime

from fastapi import APIRouter
from httpx import AsyncClient
from pydantic import BaseModel
import pytest

from app.core.exceptions import SceneDiffError
from app.main import app

# Add a test-only router to trigger various exception types
_error_router = APIRouter(prefix="/api/v1/test-errors", tags=["test"])


class SamplePayload(BaseModel):
    name: str
    count: int


@_error_router.post("/validate")
async def _validate_payload(payload: SamplePayload) -> dict[str, str]:
    return {"message": f"Hello {payload.name}"}


@_error_router.get("/domain-error")
async def _raise_domain_error() -> None:
    raise SceneDiffError(
        message="Invalid behavior diff target.",
        code="INVALID_TARGET",
        status_code=400,
    )


@_error_router.get("/unhandled-error")
async def _raise_unhandled_error() -> None:
    raise RuntimeError("Internal crash with secret_key=abcdef123456")


app.include_router(_error_router)


@pytest.mark.asyncio()
async def test_404_not_found_returns_normalized_envelope(
    async_client: AsyncClient,
) -> None:
    """Non-existent endpoints must return 404 in standard ApiResponse envelope."""
    response = await async_client.get("/api/v1/missing-route")
    assert response.status_code == 404
    assert "x-request-id" in response.headers

    body = response.json()
    assert body["success"] is False
    assert body["data"] is None
    assert body["error"]["code"] == "NOT_FOUND"
    assert "Not Found" in body["error"]["message"]
    assert "request_id" in body["metadata"]
    assert body["request_id"] == response.headers["x-request-id"]
    assert "timestamp" in body


@pytest.mark.asyncio()
async def test_validation_error_returns_422_envelope(
    async_client: AsyncClient,
) -> None:
    """Invalid request payload must return 422 with VALIDATION_ERROR code."""
    response = await async_client.post(
        "/api/v1/test-errors/validate",
        json={"name": "test", "count": "not-a-number"},
    )
    assert response.status_code == 422
    assert "x-request-id" in response.headers

    body = response.json()
    assert body["success"] is False
    assert body["data"] is None
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert "Validation failed" in body["error"]["message"]
    assert body["request_id"] == response.headers["x-request-id"]


@pytest.mark.asyncio()
async def test_custom_scenediff_error_returns_envelope(
    async_client: AsyncClient,
) -> None:
    """SceneDiffError must return custom status code, code, and message."""
    response = await async_client.get("/api/v1/test-errors/domain-error")
    assert response.status_code == 400
    assert "x-request-id" in response.headers

    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "INVALID_TARGET"
    assert body["error"]["message"] == "Invalid behavior diff target."
    assert body["request_id"] == response.headers["x-request-id"]


@pytest.mark.asyncio()
async def test_unhandled_exception_returns_500_without_leaks() -> None:
    """Unhandled exceptions must return 500 without leaking stack traces or secrets."""
    from httpx import ASGITransport

    async with AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://test",
    ) as client:
        response = await client.get("/api/v1/test-errors/unhandled-error")
        assert response.status_code == 500
        assert "x-request-id" in response.headers

        body = response.json()
        assert body["success"] is False
        assert body["data"] is None
        assert body["error"]["code"] == "INTERNAL_SERVER_ERROR"
        assert body["error"]["message"] == "An unexpected server error occurred."
        assert body["request_id"] == response.headers["x-request-id"]

        # Security: Secrets or tracebacks must never appear in response body
        assert "secret_key" not in response.text
        assert "abcdef123456" not in response.text
        assert "Traceback" not in response.text


@pytest.mark.asyncio()
async def test_error_response_timestamp_format(
    async_client: AsyncClient,
) -> None:
    """Timestamps in error responses must be ISO 8601 UTC strings."""
    response = await async_client.get("/api/v1/test-errors/domain-error")
    body = response.json()
    assert body["timestamp"].endswith("Z")
    parsed = datetime.fromisoformat(body["timestamp"].replace("Z", "+00:00"))
    assert parsed.year >= 2024


@pytest.mark.asyncio()
async def test_http_exception_403_forbidden(
    async_client: AsyncClient,
) -> None:
    """Explicit Starlette/FastAPI HTTPException must format with HTTPStatus name."""
    from fastapi import HTTPException

    @_error_router.get("/forbidden")
    async def _raise_forbidden() -> None:
        raise HTTPException(status_code=403, detail="Access denied by policy.")

    response = await async_client.get("/api/v1/test-errors/forbidden")
    assert response.status_code == 403
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "FORBIDDEN"
    assert body["error"]["message"] == "Access denied by policy."
