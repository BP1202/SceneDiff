"""Smoke test — verifies the FastAPI app instantiates and responds."""

from httpx import AsyncClient
import pytest


@pytest.mark.asyncio()
async def test_app_instantiates(async_client: AsyncClient) -> None:
    """The application must be importable and return a valid response object."""
    # Hitting a non-existent route returns 404 (not a 500 crash).
    response = await async_client.get("/api/v1/nonexistent")
    assert response.status_code == 404
