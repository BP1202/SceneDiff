"""Tests for behavior/console_diff.py — Console Log Diff Engine (Sprint 4)."""

from __future__ import annotations

from app.behavior.console_diff import compare_console_events
from app.behavior.severity import SeverityLevel


class TestConsoleDiff:
    def test_new_runtime_exception_triggers_critical(self) -> None:
        base = []
        head = [
            {
                "level": "exception",
                "message": "Uncaught TypeError: Cannot read property 'id'",
                "source_url": "app.js",
                "line_number": 42,
            }
        ]

        diffs = compare_console_events(base, head)
        exc = [d for d in diffs if d.event_type == "RUNTIME_EXCEPTION"]
        assert len(exc) == 1
        assert exc[0].severity == SeverityLevel.CRITICAL

    def test_new_console_error_triggers_high(self) -> None:
        base = []
        head = [
            {
                "level": "error",
                "message": "Failed to load resource",
                "source_url": "bundle.js",
                "line_number": 10,
            }
        ]

        diffs = compare_console_events(base, head)
        err = [d for d in diffs if d.event_type == "NEW_CONSOLE_ERROR"]
        assert len(err) == 1
        assert err[0].severity == SeverityLevel.HIGH

    def test_new_console_warning_triggers_medium(self) -> None:
        base = []
        head = [
            {
                "level": "warning",
                "message": "Deprecated API call",
                "source_url": "main.js",
                "line_number": 88,
            }
        ]

        diffs = compare_console_events(base, head)
        warn = [d for d in diffs if d.event_type == "NEW_CONSOLE_WARNING"]
        assert len(warn) == 1
        assert warn[0].severity == SeverityLevel.MEDIUM

    def test_existing_error_does_not_duplicate(self) -> None:
        base = [{"level": "error", "message": "Known backend error"}]
        head = [{"level": "error", "message": "Known backend error"}]

        diffs = compare_console_events(base, head)
        new_errors = [d for d in diffs if d.event_type == "NEW_CONSOLE_ERROR"]
        assert len(new_errors) == 0

    def test_secret_in_message_is_masked(self) -> None:
        base = []
        head = [
            {
                "level": "error",
                "message": "Auth failed for Bearer secret_mock_token_12345",
            }
        ]

        diffs = compare_console_events(base, head)
        err_diffs = [d for d in diffs if d.event_type == "NEW_CONSOLE_ERROR"]
        assert len(err_diffs) == 1
        assert (
            "[REDACTED]" in err_diffs[0].title
            or "[REDACTED]" in err_diffs[0].description
        )
