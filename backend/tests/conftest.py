"""Pytest fixtures shared across all test modules.

DATABASE_URL is set via os.environ before any app module is imported so that
pydantic-settings can resolve the required field without a real database.
"""

from collections.abc import AsyncGenerator, Generator
import os
from unittest.mock import AsyncMock, MagicMock

# Must be set before app modules are imported — pydantic-settings reads env at
# class definition time when Settings() is instantiated at module level.
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://test:test@localhost:5432/test",
)

from httpx import ASGITransport, AsyncClient  # noqa: E402
import pytest  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def mock_db() -> Generator[AsyncMock, None, None]:
    """Provide a mock AsyncSession for get_db dependency in all API tests."""
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.execute = AsyncMock(return_value=MagicMock())

    async def _override_get_db() -> AsyncGenerator[AsyncMock, None]:
        yield mock_session

    app.dependency_overrides[get_db] = _override_get_db
    yield mock_session
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture()
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Return an HTTPX async client bound to the FastAPI ASGI app."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
