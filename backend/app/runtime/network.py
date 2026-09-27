"""Task 27 — Network Request Collector.

Intercepts all HTTP requests and responses during a Playwright session and
records structured, Secret-Shield-safe network events.

Collected fields
----------------
- method        : HTTP verb
- url           : Full URL (query params preserved, fragment stripped)
- status_code   : Response status (-1 if request failed/aborted)
- latency_ms    : Round-trip time in milliseconds
- request_headers: Sanitized (Authorization, Cookie, Set-Cookie → [REDACTED])
- response_size : Content-Length bytes (-1 if unknown)
- resource_type : "document" | "xhr" | "fetch" | "script" | etc.
- failed        : True if request was aborted or failed

Security rules
--------------
- Sensitive request headers are masked at collection time.
- Response bodies are NEVER stored.
- Secret Shield is also applied in the normalizer for defense-in-depth.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import logging
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.async_api import Page, Request, Response

logger = logging.getLogger(__name__)

# Headers that must always be redacted before storage
_SENSITIVE_HEADERS = frozenset(
    {
        "authorization",
        "cookie",
        "set-cookie",
        "x-api-key",
        "x-auth-token",
        "proxy-authorization",
    }
)

_REDACTED = "[REDACTED]"


@dataclass(frozen=True)
class NetworkEvent:
    """A single captured request/response pair."""

    method: str
    url: str
    status_code: int  # -1 if failed/aborted
    latency_ms: float
    request_headers: dict[str, str]  # sanitized
    response_size: int  # -1 if unknown
    resource_type: str
    failed: bool


@dataclass
class NetworkCollector:
    """Stateful collector that intercepts network events on a Playwright page.

    Usage::

        collector = NetworkCollector()
        collector.attach(page)
        # ... navigate / interact ...
        events = collector.events
    """

    _events: list[NetworkEvent] = field(default_factory=list)
    _pending: dict[str, float] = field(default_factory=dict)  # url → start_time

    def attach(self, page: Page) -> None:
        """Register request/response/fail listeners on *page*.

        Args:
            page: Active Playwright page.
        """
        page.on("request", self._on_request)
        page.on("response", self._on_response)
        page.on("requestfailed", self._on_request_failed)

    def _on_request(self, request: Request) -> None:
        self._pending[request.url] = time.monotonic()

    def _on_response(self, response: Response) -> None:
        start = self._pending.pop(response.request.url, time.monotonic())
        latency = (time.monotonic() - start) * 1000  # ms

        raw_headers = dict(response.request.headers)
        safe_headers = _sanitize_headers(raw_headers)

        size = -1
        try:
            cl = response.headers.get("content-length", "")
            size = int(cl) if cl.isdigit() else -1
        except (ValueError, AttributeError):
            pass

        event = NetworkEvent(
            method=response.request.method,
            url=_strip_fragment(response.url),
            status_code=response.status,
            latency_ms=round(latency, 2),
            request_headers=safe_headers,
            response_size=size,
            resource_type=response.request.resource_type,
            failed=False,
        )
        self._events.append(event)

        if response.status >= 400:
            logger.debug(
                "runtime.network: %s %s → %d",
                response.request.method,
                response.url[:80],
                response.status,
            )

    def _on_request_failed(self, request: Request) -> None:
        start = self._pending.pop(request.url, time.monotonic())
        latency = (time.monotonic() - start) * 1000

        event = NetworkEvent(
            method=request.method,
            url=_strip_fragment(request.url),
            status_code=-1,
            latency_ms=round(latency, 2),
            request_headers=_sanitize_headers(dict(request.headers)),
            response_size=-1,
            resource_type=request.resource_type,
            failed=True,
        )
        self._events.append(event)
        logger.debug("runtime.network: request failed url=%s", request.url[:80])

    @property
    def events(self) -> tuple[NetworkEvent, ...]:
        """Return collected events as an immutable tuple."""
        return tuple(self._events)

    @property
    def failed_count(self) -> int:
        return sum(1 for e in self._events if e.failed)

    @property
    def error_count(self) -> int:
        return sum(1 for e in self._events if e.status_code >= 400 and not e.failed)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sanitize_headers(headers: dict[str, str]) -> dict[str, str]:
    """Replace sensitive header values with [REDACTED].

    Args:
        headers: Raw request headers dict.

    Returns:
        New dict with sensitive values masked.
    """
    return {
        k: (_REDACTED if k.lower() in _SENSITIVE_HEADERS else v)
        for k, v in headers.items()
    }


def _strip_fragment(url: str) -> str:
    """Remove URL fragment (#...) which is not sent to the server."""
    return url.split("#", 1)[0]
