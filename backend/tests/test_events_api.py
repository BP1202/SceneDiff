"""API tests for /api/v1/traces/{id}/events endpoints."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
import uuid

from httpx import AsyncClient

from app.models.trace_event import TraceEvent
from app.models.trace_session import TraceSession, TraceStatus


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _make_session(**kwargs: object) -> TraceSession:
    now = _utcnow()
    return TraceSession(
        id=kwargs.get("id", uuid.uuid4()),
        repository_name="owner/repo",
        base_commit="abc1234",
        head_commit="def5678",
        branch="main",
        status=TraceStatus.COMPLETED,
        created_at=now,
        updated_at=now,
    )


def _make_event(session_id: uuid.UUID, **kwargs: object) -> TraceEvent:
    return TraceEvent(
        id=kwargs.get("id", uuid.uuid4()),
        trace_session_id=session_id,
        event_type=str(kwargs.get("event_type", "FILE_CHANGED")),
        file_path=str(kwargs.get("file_path", "app/main.py")),
        function_name=None,
        line_number=None,
        behavior_hash=None,
        metadata_=None,
        created_at=_utcnow(),
    )


class TestListTraceEvents:
    async def test_returns_200_with_events(
        self,
        async_client: AsyncClient,
        mock_db: AsyncMock,
    ) -> None:
        session = _make_session()

        # First call: get_session; second call: list_events
        session_result = MagicMock()
        session_result.scalar_one_or_none.return_value = session

        event = _make_event(session.id)
        events_result = MagicMock()
        events_scalars = MagicMock()
        events_scalars.all.return_value = [event]
        events_result.scalars.return_value = events_scalars

        mock_db.execute = AsyncMock(side_effect=[session_result, events_result])

        response = await async_client.get(f"/api/v1/traces/{session.id}/events")
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert isinstance(body["data"], list)
        assert len(body["data"]) == 1

    async def test_returns_404_for_missing_session(
        self,
        async_client: AsyncClient,
        mock_db: AsyncMock,
    ) -> None:
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=result_mock)

        response = await async_client.get(f"/api/v1/traces/{uuid.uuid4()}/events")
        assert response.status_code == 404

    async def test_pagination_metadata_present(
        self,
        async_client: AsyncClient,
        mock_db: AsyncMock,
    ) -> None:
        session = _make_session()
        session_result = MagicMock()
        session_result.scalar_one_or_none.return_value = session

        events_scalars = MagicMock()
        events_scalars.all.return_value = []
        events_result = MagicMock()
        events_result.scalars.return_value = events_scalars

        mock_db.execute = AsyncMock(side_effect=[session_result, events_result])

        response = await async_client.get(
            f"/api/v1/traces/{session.id}/events?limit=25&offset=0"
        )
        body = response.json()
        assert "pagination" in body["metadata"]
        assert body["metadata"]["pagination"]["limit"] == 25

    async def test_filter_by_event_type(
        self,
        async_client: AsyncClient,
        mock_db: AsyncMock,
    ) -> None:
        session = _make_session()
        session_result = MagicMock()
        session_result.scalar_one_or_none.return_value = session

        event = _make_event(session.id, event_type="FUNCTION_MODIFIED")
        events_scalars = MagicMock()
        events_scalars.all.return_value = [event]
        events_result = MagicMock()
        events_result.scalars.return_value = events_scalars

        mock_db.execute = AsyncMock(side_effect=[session_result, events_result])

        response = await async_client.get(
            f"/api/v1/traces/{session.id}/events?event_type=FUNCTION_MODIFIED"
        )
        assert response.status_code == 200

    async def test_invalid_limit_returns_422(
        self,
        async_client: AsyncClient,
    ) -> None:
        response = await async_client.get(
            f"/api/v1/traces/{uuid.uuid4()}/events?limit=0"
        )
        assert response.status_code == 422

    async def test_trace_session_id_in_metadata(
        self,
        async_client: AsyncClient,
        mock_db: AsyncMock,
    ) -> None:
        session = _make_session()
        session_result = MagicMock()
        session_result.scalar_one_or_none.return_value = session

        events_scalars = MagicMock()
        events_scalars.all.return_value = []
        events_result = MagicMock()
        events_result.scalars.return_value = events_scalars

        mock_db.execute = AsyncMock(side_effect=[session_result, events_result])

        response = await async_client.get(f"/api/v1/traces/{session.id}/events")
        body = response.json()
        assert body["metadata"]["trace_session_id"] == str(session.id)
