"""Tests for Trace Storage Service (services/trace_storage.py).

All database interactions are mocked — no live PostgreSQL required.
"""

from unittest.mock import AsyncMock, MagicMock
import uuid

from app.models.trace_event import TraceEvent
from app.models.trace_session import TraceSession, TraceStatus
from app.services import trace_storage


def _make_session(**kwargs: object) -> TraceSession:
    """Build a TraceSession with sensible defaults for testing."""
    return TraceSession(
        id=kwargs.get("id", uuid.uuid4()),
        repository_name=kwargs.get("repository_name", "owner/repo"),
        base_commit=kwargs.get("base_commit", "abc1234"),
        head_commit=kwargs.get("head_commit", "def5678"),
        branch=kwargs.get("branch", "main"),
        status=kwargs.get("status", TraceStatus.PENDING),
    )


def _make_mock_db() -> AsyncMock:
    """Return a minimal AsyncSession mock."""
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.delete = AsyncMock()
    return db


class TestCreateTraceSession:
    async def test_returns_trace_session(self) -> None:
        db = _make_mock_db()

        async def refresh_side_effect(obj: object) -> None:
            pass

        db.refresh.side_effect = refresh_side_effect

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=result_mock)

        session = await trace_storage.create_trace_session(
            db, "owner/repo", "abc1234", "def5678", "main"
        )
        assert isinstance(session, TraceSession)
        db.add.assert_called_once()
        db.commit.assert_called_once()

    async def test_status_defaults_to_pending(self) -> None:
        db = _make_mock_db()

        async def refresh_side_effect(obj: object) -> None:
            pass

        db.refresh.side_effect = refresh_side_effect
        session = await trace_storage.create_trace_session(
            db, "owner/repo", "abc1234", "def5678", "main"
        )
        assert session.status == TraceStatus.PENDING


class TestGetSession:
    async def test_returns_none_when_not_found(self) -> None:
        db = _make_mock_db()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=result_mock)

        result = await trace_storage.get_session(db, uuid.uuid4())
        assert result is None

    async def test_returns_session_when_found(self) -> None:
        db = _make_mock_db()
        expected = _make_session()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = expected
        db.execute = AsyncMock(return_value=result_mock)

        result = await trace_storage.get_session(db, expected.id)
        assert result is expected


class TestUpdateStatus:
    async def test_returns_none_when_session_not_found(self) -> None:
        db = _make_mock_db()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=result_mock)

        result = await trace_storage.update_status(db, uuid.uuid4(), TraceStatus.FAILED)
        assert result is None

    async def test_updates_status_field(self) -> None:
        db = _make_mock_db()
        session = _make_session(status=TraceStatus.PENDING)

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = session
        db.execute = AsyncMock(return_value=result_mock)

        async def refresh_side_effect(obj: object) -> None:
            pass

        db.refresh.side_effect = refresh_side_effect

        result = await trace_storage.update_status(
            db, session.id, TraceStatus.COMPLETED
        )
        assert result is not None
        assert result.status == TraceStatus.COMPLETED
        db.commit.assert_called_once()


class TestDeleteFailedSession:
    async def test_returns_false_when_not_found(self) -> None:
        db = _make_mock_db()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=result_mock)

        result = await trace_storage.delete_failed_session(db, uuid.uuid4())
        assert result is False

    async def test_returns_false_when_not_failed_status(self) -> None:
        db = _make_mock_db()
        session = _make_session(status=TraceStatus.COMPLETED)
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = session
        db.execute = AsyncMock(return_value=result_mock)

        result = await trace_storage.delete_failed_session(db, session.id)
        assert result is False

    async def test_returns_true_and_deletes_failed_session(self) -> None:
        db = _make_mock_db()
        session = _make_session(status=TraceStatus.FAILED)
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = session
        db.execute = AsyncMock(return_value=result_mock)

        result = await trace_storage.delete_failed_session(db, session.id)
        assert result is True
        db.delete.assert_called_once_with(session)
        db.commit.assert_called_once()


class TestStoreEvent:
    async def test_stores_event_with_sanitized_metadata(self) -> None:
        db = _make_mock_db()

        async def refresh_side_effect(obj: object) -> None:
            pass

        db.refresh.side_effect = refresh_side_effect

        session_id = uuid.uuid4()
        event = await trace_storage.store_event(
            db,
            trace_session_id=session_id,
            event_type="FUNCTION_MODIFIED",
            file_path="app/main.py",
            function_name="handle",
            metadata={"lang": "python", "api_key": "AKIAIOSFODNN7EXAMPLE"},
        )
        assert isinstance(event, TraceEvent)
        # Secret was masked before storage
        assert event.metadata_ is not None
        assert "AKIAIOSFODNN7EXAMPLE" not in str(event.metadata_)

    async def test_stores_event_without_metadata(self) -> None:
        db = _make_mock_db()

        async def refresh_side_effect(obj: object) -> None:
            pass

        db.refresh.side_effect = refresh_side_effect
        event = await trace_storage.store_event(
            db,
            trace_session_id=uuid.uuid4(),
            event_type="FILE_CHANGED",
            file_path="src/util.ts",
        )
        assert event.metadata_ is None


class TestListSessions:
    async def test_returns_list(self) -> None:
        db = _make_mock_db()
        scalars_mock = MagicMock()
        scalars_mock.all.return_value = [_make_session(), _make_session()]
        result_mock = MagicMock()
        result_mock.scalars.return_value = scalars_mock
        db.execute = AsyncMock(return_value=result_mock)

        results = await trace_storage.list_sessions(db)
        assert len(results) == 2

    async def test_returns_empty_list_when_no_sessions(self) -> None:
        db = _make_mock_db()
        scalars_mock = MagicMock()
        scalars_mock.all.return_value = []
        result_mock = MagicMock()
        result_mock.scalars.return_value = scalars_mock
        db.execute = AsyncMock(return_value=result_mock)

        results = await trace_storage.list_sessions(db)
        assert results == []


class TestListEvents:
    async def test_returns_list_of_events(self) -> None:
        db = _make_mock_db()
        event = TraceEvent(
            id=uuid.uuid4(),
            trace_session_id=uuid.uuid4(),
            event_type="FILE_CHANGED",
            file_path="app/main.py",
        )
        scalars_mock = MagicMock()
        scalars_mock.all.return_value = [event]
        result_mock = MagicMock()
        result_mock.scalars.return_value = scalars_mock
        db.execute = AsyncMock(return_value=result_mock)

        results = await trace_storage.list_events(db, uuid.uuid4())
        assert len(results) == 1
        assert results[0].event_type == "FILE_CHANGED"
