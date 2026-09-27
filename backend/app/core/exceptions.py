"""Global exception handling and normalized error responses.

Ensures every error returned by SceneDiff adheres to the standard
ApiResponse envelope defined in api-contract.md:
    success  — False
    data     — None
    error    — dict with code, message
    metadata — request_id, api_version
    request_id — correlation ID
    timestamp  — ISO 8601 UTC

No internal stack traces, database credentials, or hostnames are ever exposed.
"""

from datetime import UTC, datetime
from http import HTTPStatus
import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)

REQUEST_ID_HEADER = "X-Request-ID"


class SceneDiffError(Exception):
    """Base application exception for SceneDiff domain errors."""

    def __init__(
        self,
        message: str = "An application error occurred.",
        code: str = "SCENEDIFF_ERROR",
        status_code: int = 500,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code


def _build_error_response(
    status_code: int,
    code: str,
    message: str,
    request: Request,
) -> JSONResponse:
    """Construct a standardized error JSONResponse adhering to api-contract.md."""
    request_id: str = getattr(request.state, "request_id", "") or request.headers.get(
        REQUEST_ID_HEADER, ""
    )
    timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    payload: dict[str, Any] = {
        "success": False,
        "data": None,
        "error": {
            "code": code,
            "message": message,
        },
        "metadata": {
            "request_id": request_id,
            "api_version": "v1",
        },
        "request_id": request_id,
        "timestamp": timestamp,
    }

    headers: dict[str, str] = {}
    if request_id:
        headers[REQUEST_ID_HEADER] = request_id

    return JSONResponse(status_code=status_code, content=payload, headers=headers)


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Handle standard HTTP exceptions with normalized error schema."""
    try:
        status_name = HTTPStatus(exc.status_code).name
    except ValueError:
        status_name = "HTTP_ERROR"

    message = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    return _build_error_response(
        status_code=exc.status_code,
        code=status_name,
        message=message,
        request=request,
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle 422 request validation errors without leaking sensitive payloads."""
    errors = exc.errors()
    # Summarize validation errors cleanly
    if errors:
        first_err = errors[0]
        loc = " -> ".join(str(item) for item in first_err.get("loc", []))
        msg = first_err.get("msg", "Invalid value")
        message = f"Validation failed at '{loc}': {msg}" if loc else msg
    else:
        message = "Validation error in request."

    return _build_error_response(
        status_code=422,
        code="VALIDATION_ERROR",
        message=message,
        request=request,
    )


async def scenediff_error_handler(
    request: Request, exc: SceneDiffError
) -> JSONResponse:
    """Handle custom SceneDiff domain exceptions."""
    return _build_error_response(
        status_code=exc.status_code,
        code=exc.code,
        message=exc.message,
        request=request,
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle uncaught 500 exceptions, logging securely without leaking traces."""
    request_id: str = getattr(request.state, "request_id", "")
    logger.error(
        "Unhandled exception in request [%s]: %s",
        request_id,
        type(exc).__name__,
    )

    return _build_error_response(
        status_code=500,
        code="INTERNAL_SERVER_ERROR",
        message="An unexpected server error occurred.",
        request=request,
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all global exception handlers on the application instance."""
    app.add_exception_handler(
        StarletteHTTPException,
        http_exception_handler,  # type: ignore[arg-type]
    )
    app.add_exception_handler(
        RequestValidationError,
        validation_exception_handler,  # type: ignore[arg-type]
    )
    app.add_exception_handler(
        SceneDiffError,
        scenediff_error_handler,  # type: ignore[arg-type]
    )
    app.add_exception_handler(Exception, unhandled_exception_handler)
