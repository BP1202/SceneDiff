"""Tests for RequestID middleware — UUID generation, propagation, and preservation."""

import uuid

from httpx import AsyncClient
import pytest


@pytest.mark.asyncio()
async def test_request_id_generated_when_missing(
    async_client: AsyncClient,
) -> None:
    """When client omits X-Request-ID, middleware must generate a valid UUID4."""
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    assert "x-request-id" in response.headers

    req_id = response.headers["x-request-id"]
    parsed_uuid = uuid.UUID(req_id)
    assert parsed_uuid.version == 4


@pytest.mark.asyncio()
async def test_request_id_preserved_when_provided(async_client: AsyncClient) -> None:
    """When client supplies X-Request-ID, the identical value must be preserved."""
    custom_id = "trace-client-abc-12345"
    response = await async_client.get(
        "/api/v1/health", headers={"X-Request-ID": custom_id}
    )
    assert response.headers["x-request-id"] == custom_id
    body = response.json()
    assert body["request_id"] == custom_id
    assert body["metadata"]["request_id"] == custom_id


@pytest.mark.asyncio()
async def test_unique_request_id_per_request(async_client: AsyncClient) -> None:
    """Two independent requests must receive distinct request IDs."""
    r1 = await async_client.get("/api/v1/health")
    r2 = await async_client.get("/api/v1/health")

    id1 = r1.headers["x-request-id"]
    id2 = r2.headers["x-request-id"]
    assert id1 != id2


@pytest.mark.asyncio()
async def test_request_id_present_on_not_found(async_client: AsyncClient) -> None:
    """404 responses must still contain an X-Request-ID header and envelope ID."""
    response = await async_client.get("/api/v1/nonexistent-route")
    assert response.status_code == 404
    assert "x-request-id" in response.headers
    body = response.json()
    assert body["request_id"] == response.headers["x-request-id"]
    assert body["metadata"]["request_id"] == response.headers["x-request-id"]


@pytest.mark.asyncio()
async def test_request_id_in_health_response_envelope(
    async_client: AsyncClient,
) -> None:
    """Request ID in the JSON body must match the HTTP response header."""
    response = await async_client.get("/api/v1/health")
    body = response.json()
    header_id = response.headers["x-request-id"]
    assert body["request_id"] == header_id
    assert body["metadata"]["request_id"] == header_id


@pytest.mark.asyncio()
async def test_request_id_preserved_on_validation_error(
    async_client: AsyncClient,
) -> None:
    """X-Request-ID must be preserved when a 422 validation failure occurs."""
    custom_id = "val-fail-req-456"
    response = await async_client.post(
        "/api/v1/test-errors/validate",
        headers={"X-Request-ID": custom_id},
        json={"bad_key": "bad_value"},
    )
    assert response.status_code == 422
    assert response.headers["x-request-id"] == custom_id
    body = response.json()
    assert body["request_id"] == custom_id
    assert body["metadata"]["request_id"] == custom_id
