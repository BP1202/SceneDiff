"""Tests for runtime/console.py — Console Event Collector (Task 26)."""

from __future__ import annotations

from unittest.mock import MagicMock

from app.runtime.console import ConsoleCollector


def _make_console_msg(type_: str, text: str, url: str = "", line: int = 0) -> MagicMock:
    msg = MagicMock()
    msg.type = type_
    msg.text = text
    msg.location = {"url": url, "lineNumber": line}
    return msg


class TestConsoleCollector:
    def test_initial_events_empty(self) -> None:
        c = ConsoleCollector()
        assert c.events == ()

    def test_attach_registers_listeners(self) -> None:
        c = ConsoleCollector()
        page = MagicMock()
        c.attach(page)
        assert page.on.call_count == 2

    def test_on_console_captures_log(self) -> None:
        c = ConsoleCollector()
        msg = _make_console_msg("log", "Hello log", url="app.js", line=10)
        c._on_console(msg)
        assert len(c.events) == 1
        assert c.events[0].level == "log"
        assert c.events[0].message == "Hello log"

    def test_on_console_captures_error(self) -> None:
        c = ConsoleCollector()
        msg = _make_console_msg("error", "Uncaught TypeError", url="app.js", line=42)
        c._on_console(msg)
        assert c.events[0].level == "error"
        assert c.events[0].source_url == "app.js"
        assert c.events[0].line_number == 42

    def test_on_page_error_captured(self) -> None:
        c = ConsoleCollector()
        c._on_page_error(RuntimeError("Unhandled rejection"))
        assert len(c.events) == 1
        assert c.events[0].level == "exception"
        assert "Unhandled rejection" in c.events[0].message

    def test_error_count(self) -> None:
        c = ConsoleCollector()
        c._on_console(_make_console_msg("error", "err1"))
        c._on_console(_make_console_msg("log", "info"))
        c._on_page_error(RuntimeError("crash"))
        assert c.error_count == 2

    def test_warning_count(self) -> None:
        c = ConsoleCollector()
        c._on_console(_make_console_msg("warning", "warn1"))
        c._on_console(_make_console_msg("warning", "warn2"))
        c._on_console(_make_console_msg("log", "info"))
        assert c.warning_count == 2

    def test_events_returns_immutable_tuple(self) -> None:
        c = ConsoleCollector()
        events = c.events
        assert isinstance(events, tuple)

    def test_message_length_capped(self) -> None:
        c = ConsoleCollector()
        long_msg = "x" * 10_000
        msg = _make_console_msg("log", long_msg)
        c._on_console(msg)
        assert len(c.events[0].message) == 4096

    def test_multiple_events_ordered(self) -> None:
        c = ConsoleCollector()
        c._on_console(_make_console_msg("log", "first"))
        c._on_console(_make_console_msg("error", "second"))
        assert c.events[0].message == "first"
        assert c.events[1].message == "second"
