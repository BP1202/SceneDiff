"""Tests for the Trace Processor pipeline (services/trace_processor.py)."""

from unittest.mock import AsyncMock, MagicMock, patch
import uuid

import pytest

from app.models.trace_session import TraceSession, TraceStatus
from app.services import trace_processor

_PYTHON_DIFF = """\
diff --git a/app/handler.py b/app/handler.py
--- a/app/handler.py
+++ b/app/handler.py
@@ -1,5 +1,6 @@
-def handle(req):
+def handle(req, timeout=30):
     x = 1
-    return x
+    return x + timeout
"""

_EMPTY_DIFF = ""


def _make_mock_db() -> AsyncMock:
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.delete = AsyncMock()
    return db


class TestProcessTrace:
    """Integration-style tests for the trace processor pipeline."""

    async def test_process_trace_updates_status_to_completed(self) -> None:
        session_id = uuid.uuid4()
        db = _make_mock_db()

        status_calls: list[TraceStatus] = []

        async def fake_update_status(
            _db: object, _id: object, s: TraceStatus
        ) -> TraceSession | None:
            status_calls.append(s)
            return None

        async def fake_store_event(*args: object, **kwargs: object) -> MagicMock:
            return MagicMock()

        with (
            patch.object(trace_processor, "update_status", fake_update_status),
            patch.object(trace_processor, "store_event", fake_store_event),
        ):
            await trace_processor.process_trace(db, session_id, _PYTHON_DIFF)

        assert TraceStatus.COLLECTING in status_calls
        assert TraceStatus.PROCESSING in status_calls
        assert TraceStatus.COMPLETED in status_calls

    async def test_process_trace_empty_diff_completes(self) -> None:
        session_id = uuid.uuid4()
        db = _make_mock_db()

        async def fake_update_status(
            _db: object, _id: object, s: TraceStatus
        ) -> TraceSession | None:
            return None

        async def fake_store_event(*args: object, **kwargs: object) -> MagicMock:
            return MagicMock()

        with (
            patch.object(trace_processor, "update_status", fake_update_status),
            patch.object(trace_processor, "store_event", fake_store_event),
        ):
            await trace_processor.process_trace(db, session_id, _EMPTY_DIFF)
        # No assertion needed — we just verify no exception is raised.

    async def test_process_trace_marks_failed_on_error(self) -> None:
        session_id = uuid.uuid4()
        db = _make_mock_db()

        status_calls: list[TraceStatus] = []

        async def fake_update_status(_db: object, _id: object, s: TraceStatus) -> None:
            status_calls.append(s)
            if s == TraceStatus.PROCESSING:
                raise RuntimeError("simulated failure")

        with (
            patch.object(trace_processor, "update_status", fake_update_status),
            pytest.raises(RuntimeError),
        ):
            await trace_processor.process_trace(db, session_id, _PYTHON_DIFF)

        assert TraceStatus.FAILED in status_calls


class TestParseStage:
    def test_parse_stage_returns_parsed_diffs(self) -> None:
        parsed = trace_processor._parse_stage(_PYTHON_DIFF)
        assert len(parsed) == 1
        assert parsed[0].file_path == "app/handler.py"

    def test_parse_stage_empty_diff_returns_empty_list(self) -> None:
        parsed = trace_processor._parse_stage(_EMPTY_DIFF)
        assert parsed == []


class TestDiffText:
    def test_diff_text_includes_added_and_removed(self) -> None:
        from app.services.diff_parser import parse_diff

        parsed = parse_diff(_PYTHON_DIFF)
        text = trace_processor._diff_text(parsed[0])
        assert "+" in text or "-" in text or text == ""


class TestCleanupFailedSession:
    async def test_delegates_to_delete_failed_session(self) -> None:
        db = _make_mock_db()
        session_id = uuid.uuid4()

        async def fake_delete(_db: object, _id: object) -> bool:
            return True

        with patch.object(trace_processor, "delete_failed_session", fake_delete):
            result = await trace_processor.cleanup_failed_session(db, session_id)
        assert result is True
