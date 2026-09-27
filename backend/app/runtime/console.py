"""Task 26 — Console Event Collector.

Captures JavaScript console output and page errors emitted during a
Playwright browser session.

Collected event types
---------------------
- console.log  → level "log"
- console.warn → level "warning"
- console.error → level "error"
- Unhandled page exceptions → level "exception"
- Unhandled promise rejections → level "exception"

Design rules
------------
- Events are collected in insertion order.
- Message text is length-capped at 4 KB to prevent artifact bloat.
- No secret masking here — Secret Shield runs at the normalizer layer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.async_api import ConsoleMessage, Page

logger = logging.getLogger(__name__)

_MAX_MSG_LEN = 4096  # 4 KB per console message


@dataclass(frozen=True)
class ConsoleEvent:
    """A single captured console or page-error event."""

    level: str  # "log" | "warning" | "error" | "exception"
    message: str  # message text, capped at _MAX_MSG_LEN
    source_url: str  # URL of the script that generated the message
    line_number: int  # 0 if unknown


@dataclass
class ConsoleCollector:
    """Stateful collector that attaches to a Playwright page.

    Usage::

        collector = ConsoleCollector()
        collector.attach(page)
        # ... run page interactions ...
        events = collector.events
    """

    _events: list[ConsoleEvent] = field(default_factory=list)

    def attach(self, page: Page) -> None:
        """Register console and error event listeners on *page*.

        Args:
            page: Active Playwright page (before navigation).
        """
        page.on("console", self._on_console)
        page.on("pageerror", self._on_page_error)

    def _on_console(self, msg: ConsoleMessage) -> None:
        level = msg.type  # "log" | "warning" | "error" | "info" | "debug"
        text = msg.text[:_MAX_MSG_LEN]
        location = msg.location
        event = ConsoleEvent(
            level=level,
            message=text,
            source_url=location.get("url", "") if location else "",
            line_number=location.get("lineNumber", 0) if location else 0,
        )
        self._events.append(event)
        if level in ("error", "warning"):
            logger.debug("runtime.console: %s — %s", level, text[:120])

    def _on_page_error(self, exc: Exception) -> None:
        event = ConsoleEvent(
            level="exception",
            message=str(exc)[:_MAX_MSG_LEN],
            source_url="",
            line_number=0,
        )
        self._events.append(event)
        logger.warning("runtime.console: unhandled page exception — %s", str(exc)[:120])

    @property
    def events(self) -> tuple[ConsoleEvent, ...]:
        """Return collected events as an immutable tuple."""
        return tuple(self._events)

    @property
    def error_count(self) -> int:
        return sum(1 for e in self._events if e.level in ("error", "exception"))

    @property
    def warning_count(self) -> int:
        return sum(1 for e in self._events if e.level == "warning")
