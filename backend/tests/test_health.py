"""Tests for GET /api/v1/health — Database health endpoint (Sprint 1, Task 06)."""

from datetime import datetime
from unittest.mock import AsyncMock

from httpx import AsyncClient
import pytest
from sqlalchemy.exc import OperationalError, SQLAlchemyError


@pytest.mark.asyncio()
async def test_health_returns_200(async_client: AsyncClient) -> None:
    """Health endpoint must return HTTP 200 when database is healthy."""
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200


@pytest.mark.asyncio()
async def test_health_envelope_shape(async_client: AsyncClient) -> None:
    """Response must contain the standard api-contract.md envelope fields."""
    response = await async_client.get("/api/v1/health")
    body = response.json()
    assert body["success"] is True
    assert body["data"]["status"] == "ok"
    assert body["data"]["version"] == "0.1.0"
    assert "request_id" in body["metadata"]
    assert body["error"] is None
    assert "request_id" in body
    assert "timestamp" in body


@pytest.mark.asyncio()
async def test_health_database_connected_payload(async_client: AsyncClient) -> None:
    """Healthy response must include connected database status with latency."""
    response = await async_client.get("/api/v1/health")
    body = response.json()
    db_info = body["data"]["database"]
    assert db_info["status"] == "connected"
    assert db_info["engine"] == "postgresql"
    assert isinstance(db_info["latency_ms"], int)
    assert db_info["latency_ms"] >= 0


@pytest.mark.asyncio()
async def test_health_response_has_request_id_header(async_client: AsyncClient) -> None:
    """Response must contain X-Request-ID header injected by middleware."""
    response = await async_client.get("/api/v1/health")
    assert "x-request-id" in response.headers


@pytest.mark.asyncio()
async def test_health_preserves_client_request_id(async_client: AsyncClient) -> None:
    """If client sends X-Request-ID, the same value must be echoed back."""
    test_id = "test-id-123"
    response = await async_client.get(
        "/api/v1/health", headers={"X-Request-ID": test_id}
    )
    body = response.json()
    assert response.headers["x-request-id"] == test_id
    assert body["request_id"] == test_id
    assert body["metadata"]["request_id"] == test_id


@pytest.mark.asyncio()
async def test_health_degraded_when_database_fails(
    async_client: AsyncClient, mock_db: AsyncMock
) -> None:
    """When DB query fails, endpoint must return 503 degraded without crashing."""
    mock_db.execute.side_effect = OperationalError(
        "connection closed", params=None, orig=Exception("connection closed")
    )

    response = await async_client.get("/api/v1/health")
    assert response.status_code == 503

    body = response.json()
    assert body["success"] is False
    assert body["data"]["status"] == "degraded"
    assert body["data"]["version"] == "0.1.0"

    db_info = body["data"]["database"]
    assert db_info["status"] == "disconnected"
    assert db_info["latency_ms"] is None
    assert db_info["engine"] == "postgresql"

    assert body["error"] == {
        "code": "DATABASE_UNAVAILABLE",
        "message": "Database health check failed",
    }


@pytest.mark.asyncio()
async def test_health_no_credentials_leaked_on_error(
    async_client: AsyncClient, mock_db: AsyncMock
) -> None:
    """Error response must never leak database URLs, passwords, or hosts."""
    sensitive_error = (
        "password authentication failed for user 'scenediff' at host '10.0.0.1:5432'"
    )
    mock_db.execute.side_effect = SQLAlchemyError(sensitive_error)

    response = await async_client.get("/api/v1/health")
    body_text = response.text

    assert "scenediff" not in body_text
    assert "10.0.0.1" not in body_text
    assert "5432" not in body_text
    assert "password" not in body_text
    assert response.json()["error"]["message"] == "Database health check failed"


@pytest.mark.asyncio()
async def test_health_handles_timeout_error(
    async_client: AsyncClient, mock_db: AsyncMock
) -> None:
    """When DB query times out, endpoint must return 503 with degraded status."""
    mock_db.execute.side_effect = TimeoutError("Query timed out")

    response = await async_client.get("/api/v1/health")
    assert response.status_code == 503
    body = response.json()
    assert body["success"] is False
    assert body["data"]["database"]["status"] == "disconnected"


@pytest.mark.asyncio()
async def test_health_preserves_request_id_on_failure(
    async_client: AsyncClient, mock_db: AsyncMock
) -> None:
    """Request ID must be preserved even when database health check fails."""
    mock_db.execute.side_effect = SQLAlchemyError("DB error")
    custom_id = "failed-req-999"

    response = await async_client.get(
        "/api/v1/health", headers={"X-Request-ID": custom_id}
    )
    assert response.status_code == 503
    assert response.headers["x-request-id"] == custom_id
    body = response.json()
    assert body["request_id"] == custom_id
    assert body["metadata"]["request_id"] == custom_id


@pytest.mark.asyncio()
async def test_health_timestamp_is_iso8601(async_client: AsyncClient) -> None:
    """Timestamp in response must be valid ISO 8601 UTC string."""
    response = await async_client.get("/api/v1/health")
    body = response.json()
    assert body["timestamp"].endswith("Z")
    # Must parse without exception
    parsed = datetime.fromisoformat(body["timestamp"].replace("Z", "+00:00"))
    assert parsed.year >= 2024
