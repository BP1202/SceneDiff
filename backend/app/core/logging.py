"""Structured JSON logging configuration.

Configures the stdlib logging module with a JSON formatter so every log
line is machine-parseable.  No third-party logging framework required.
"""

from datetime import UTC, datetime
import json
import logging
from typing import Any

SENSITIVE_KEYS = {
    "authorization",
    "password",
    "token",
    "secret",
    "api_key",
    "apikey",
    "access_token",
    "cookie",
}


def sanitize_value(val: object) -> object:
    """Sanitize potentially sensitive fields."""
    if isinstance(val, dict):
        return {
            k: ("[REDACTED]" if k.lower() in SENSITIVE_KEYS else sanitize_value(v))
            for k, v in val.items()
        }
    if isinstance(val, list):
        return [sanitize_value(item) for item in val]
    return val


class JsonFormatter(logging.Formatter):
    """Emit log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.fromtimestamp(record.created, tz=UTC).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )

        payload: dict[str, Any] = {
            "timestamp": timestamp,
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Include structured attributes if attached via extra
        for attr in (
            "request_id",
            "method",
            "path",
            "status_code",
            "latency_ms",
            "client_ip",
        ):
            val = getattr(record, attr, None)
            if val is not None:
                payload[attr] = val

        # Handle any custom extra attributes while sanitizing secrets
        standard_attrs = {
            "args",
            "msg",
            "pathname",
            "filename",
            "module",
            "exc_info",
            "exc_text",
            "stack_info",
            "lineno",
            "funcName",
            "created",
            "msecs",
            "relativeCreated",
            "thread",
            "threadName",
            "processName",
            "process",
            "levelname",
            "levelno",
            "name",
        }
        for k, v in record.__dict__.items():
            if k not in payload and not k.startswith("_") and k not in standard_attrs:
                if k.lower() in SENSITIVE_KEYS:
                    payload[k] = "[REDACTED]"
                else:
                    payload[k] = sanitize_value(v)

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload)


# Backwards compatibility alias
_JsonFormatter = JsonFormatter


def configure_logging(level: str = "INFO") -> None:
    """Apply JSON formatter to the root handler.

    Call once at application startup.
    """
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
