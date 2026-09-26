"""Tests for GET /api/v1/health."""
from httpx import AsyncClient
import pytest


@pytest.mark.asyncio()
async def test_health_returns_200(async_client: AsyncClient) -> None:
    """Health endpoint must return HTTP 200."""
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


@pytest.mark.asyncio()
async def test_health_response_has_request_id_header(async_client: AsyncClient) -> None:
    """Response must contain X-Request-ID header injected by middleware."""
    response = await async_client.get("/api/v1/health")
    assert "x-request-id" in response.headers


@pytest.mark.asyncio()
async def test_health_preserves_client_request_id(async_client: AsyncClient) -> None:
    """If client sends X-Request-ID, the same value must be echoed back."""
    response = await async_client.get(
        "/api/v1/health", headers={"X-Request-ID": "test-id-123"}
    )
    assert response.headers["x-request-id"] == "test-id-123"
