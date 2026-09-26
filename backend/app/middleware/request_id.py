"""Request-ID middleware.

Injects a unique X-Request-ID into every request/response cycle.
If the client already provides the header its value is preserved.
"""

from collections.abc import Callable
from typing import Any
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

REQUEST_ID_HEADER = "X-Request-ID"


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach a request ID to every request and echo it in the response."""

    async def dispatch(
        self, request: Request, call_next: Callable[..., Any]
    ) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())
        request.state.request_id = request_id
        response: Response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request_id
        return response
