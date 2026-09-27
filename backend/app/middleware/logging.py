"""Access and performance logging middleware.

Captures request timing, correlation IDs, and HTTP metadata for every
request without logging sensitive payloads, headers, or query parameters.
"""

from collections.abc import Callable
import logging
import time
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("scenediff.access")


class LoggingMiddleware(BaseHTTPMiddleware):
    """Log HTTP request lifecycle details with timing and correlation IDs."""

    async def dispatch(
        self, request: Request, call_next: Callable[..., Any]
    ) -> Response:
        start_time = time.perf_counter()

        state_id = getattr(request.state, "request_id", "")
        request_id: str = state_id or request.headers.get("X-Request-ID", "")
        client_ip = request.client.host if request.client else "unknown"
        method = request.method
        path = request.url.path

        try:
            response: Response = await call_next(request)
            latency_ms = int(round((time.perf_counter() - start_time) * 1000))

            logger.info(
                "HTTP request completed",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "path": path,
                    "status_code": response.status_code,
                    "latency_ms": latency_ms,
                    "client_ip": client_ip,
                },
            )
            return response
        except Exception:
            latency_ms = int(round((time.perf_counter() - start_time) * 1000))
            logger.error(
                "HTTP request failed",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "path": path,
                    "status_code": 500,
                    "latency_ms": latency_ms,
                    "client_ip": client_ip,
                },
            )
            raise
