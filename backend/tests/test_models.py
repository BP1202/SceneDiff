"""Tests for TraceSession and TraceEvent ORM models."""

import uuid

from app.models.trace_event import TraceEvent
from app.models.trace_session import TraceSession, TraceStatus


class TestTraceStatus:
    """Tests for the TraceStatus enum."""

    def test_all_statuses_present(self) -> None:
        statuses = {s.value for s in TraceStatus}
        expected = {"PENDING", "COLLECTING", "PROCESSING", "COMPLETED", "FAILED"}
        assert statuses == expected

    def test_status_is_string_enum(self) -> None:
        assert isinstance(TraceStatus.PENDING, str)
        assert TraceStatus.PENDING == "PENDING"


class TestTraceSessionModel:
    """Tests for TraceSession ORM model instantiation."""

    def test_can_create_instance(self) -> None:
        session = TraceSession(
            id=uuid.uuid4(),
            repository_name="owner/repo",
            base_commit="abc1234",
            head_commit="def5678",
            branch="main",
            status=TraceStatus.PENDING,
        )
        assert session.repository_name == "owner/repo"
        assert session.status == TraceStatus.PENDING

    def test_tablename_is_trace_sessions(self) -> None:
        assert TraceSession.__tablename__ == "trace_sessions"

    def test_has_events_relationship(self) -> None:
        assert hasattr(TraceSession, "events")

    def test_uuid_id_column(self) -> None:
        session = TraceSession(
            id=uuid.uuid4(),
            repository_name="r",
            base_commit="a" * 7,
            head_commit="b" * 7,
            branch="feat",
            status=TraceStatus.PENDING,
        )
        assert isinstance(session.id, uuid.UUID)


class TestTraceEventModel:
    """Tests for TraceEvent ORM model instantiation."""

    def test_can_create_instance(self) -> None:
        session_id = uuid.uuid4()
        event = TraceEvent(
            id=uuid.uuid4(),
            trace_session_id=session_id,
            event_type="FUNCTION_MODIFIED",
            file_path="app/main.py",
        )
        assert event.event_type == "FUNCTION_MODIFIED"
        assert event.file_path == "app/main.py"
        assert event.trace_session_id == session_id

    def test_tablename_is_trace_events(self) -> None:
        assert TraceEvent.__tablename__ == "trace_events"

    def test_has_trace_session_relationship(self) -> None:
        assert hasattr(TraceEvent, "trace_session")

    def test_optional_fields_default_to_none(self) -> None:
        event = TraceEvent(
            id=uuid.uuid4(),
            trace_session_id=uuid.uuid4(),
            event_type="FILE_CHANGED",
            file_path="src/app.py",
        )
        assert event.function_name is None
        assert event.line_number is None
        assert event.behavior_hash is None
        assert event.metadata_ is None
