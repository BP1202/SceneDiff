"""API tests for /api/v1/traces endpoints.

Uses HTTPX AsyncClient with a mocked database session.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
import uuid

from httpx import AsyncClient

from app.models.trace_session import TraceSession, TraceStatus


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _make_session(**kwargs: object) -> TraceSession:
    now = _utcnow()
    return TraceSession(
        id=kwargs.get("id", uuid.uuid4()),
        repository_name=str(kwargs.get("repository_name", "owner/repo")),
        base_commit=str(kwargs.get("base_commit", "abc1234")),
        head_commit=str(kwargs.get("head_commit", "def5678")),
        branch=str(kwargs.get("branch", "main")),
        status=kwargs.get("status", TraceStatus.PENDING),
        created_at=kwargs.get("created_at", now),
        updated_at=kwargs.get("updated_at", now),
    )


# ---------------------------------------------------------------------------
# POST /api/v1/traces
# ---------------------------------------------------------------------------


class TestCreateTrace:
    async def test_create_trace_returns_201(
        self,
        async_client: AsyncClient,
        mock_db: AsyncMock,
    ) -> None:
        session = _make_session()

        async def fake_create(*args: object, **kwargs: object) -> TraceSession:
            return session

        with patch(
            "app.services.trace_storage.create_trace_session",
            side_effect=fake_create,
        ):
            response = await async_client.post(
                "/api/v1/traces",
                json={
                    "repository_name": "owner/repo",
                    "base_commit": "abc1234",
                    "head_commit": "def5678",
                    "branch": "main",
                },
            )

        assert response.status_code == 201
        body = response.json()
        assert body["success"] is True
        assert body["data"]["repository_name"] == "owner/repo"

    async def test_create_trace_invalid_sha_returns_422(
        self,
        async_client: AsyncClient,
    ) -> None:
        response = await async_client.post(
            "/api/v1/traces",
            json={
                "repository_name": "owner/repo",
                "base_commit": "ZZZZZZ!",  # non-hex
                "head_commit": "def5678",
                "branch": "main",
            },
        )
        assert response.status_code == 422

    async def test_create_trace_missing_field_returns_422(
        self,
        async_client: AsyncClient,
    ) -> None:
        response = await async_client.post(
            "/api/v1/traces",
            json={"repository_name": "owner/repo"},
        )
        assert response.status_code == 422

    async def test_create_trace_short_sha_returns_422(
        self,
        async_client: AsyncClient,
    ) -> None:
        response = await async_client.post(
            "/api/v1/traces",
            json={
                "repository_name": "owner/repo",
                "base_commit": "abc",  # too short (< 7 chars)
                "head_commit": "def5678",
                "branch": "main",
            },
        )
        assert response.status_code == 422

    async def test_create_trace_invalid_repo_format_returns_422(
        self,
        async_client: AsyncClient,
    ) -> None:
        response = await async_client.post(
            "/api/v1/traces",
            json={
                "repository_name": "owner/repo/extra/segment",
                "base_commit": "abc1234",
                "head_commit": "def5678",
                "branch": "main",
            },
        )
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/v1/traces
# ---------------------------------------------------------------------------


class TestListTraces:
    async def test_list_traces_returns_200(
        self,
        async_client: AsyncClient,
        mock_db: AsyncMock,
    ) -> None:
        scalars_mock = MagicMock()
        scalars_mock.all.return_value = []
        result_mock = MagicMock()
        result_mock.scalars.return_value = scalars_mock
        mock_db.execute = AsyncMock(return_value=result_mock)

        response = await async_client.get("/api/v1/traces")
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert isinstance(body["data"], list)

    async def test_list_traces_pagination_metadata(
        self,
        async_client: AsyncClient,
        mock_db: AsyncMock,
    ) -> None:
        scalars_mock = MagicMock()
        scalars_mock.all.return_value = []
        result_mock = MagicMock()
        result_mock.scalars.return_value = scalars_mock
        mock_db.execute = AsyncMock(return_value=result_mock)

        response = await async_client.get("/api/v1/traces?limit=10&offset=0")
        body = response.json()
        assert "pagination" in body["metadata"]
        assert body["metadata"]["pagination"]["limit"] == 10
        assert body["metadata"]["pagination"]["offset"] == 0

    async def test_list_traces_invalid_limit_returns_422(
        self,
        async_client: AsyncClient,
    ) -> None:
        response = await async_client.get("/api/v1/traces?limit=0")
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/v1/traces/{trace_id}
# ---------------------------------------------------------------------------


class TestGetTrace:
    async def test_get_existing_trace_returns_200(
        self,
        async_client: AsyncClient,
        mock_db: AsyncMock,
    ) -> None:
        session = _make_session()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = session
        mock_db.execute = AsyncMock(return_value=result_mock)

        response = await async_client.get(f"/api/v1/traces/{session.id}")
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["id"] == str(session.id)

    async def test_get_nonexistent_trace_returns_404(
        self,
        async_client: AsyncClient,
        mock_db: AsyncMock,
    ) -> None:
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=result_mock)

        response = await async_client.get(f"/api/v1/traces/{uuid.uuid4()}")
        assert response.status_code == 404

    async def test_get_trace_invalid_uuid_returns_422(
        self,
        async_client: AsyncClient,
    ) -> None:
        response = await async_client.get("/api/v1/traces/not-a-uuid")
        assert response.status_code == 422
