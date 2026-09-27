"""Tests for structured JSON logging and LoggingMiddleware."""

import json
import logging

from httpx import AsyncClient
import pytest

from app.core.logging import JsonFormatter, sanitize_value


def test_json_formatter_emits_valid_json() -> None:
    """JsonFormatter must output a valid, parseable single-line JSON string."""
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="test message",
        args=(),
        exc_info=None,
    )
    output = formatter.format(record)
    parsed = json.loads(output)
    assert parsed["level"] == "INFO"
    assert parsed["message"] == "test message"
    assert parsed["logger"] == "test_logger"
    assert "timestamp" in parsed


def test_json_formatter_structured_extras() -> None:
    """Extra attributes (request_id, latency_ms, etc.) must be serialized."""
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="scenediff.access",
        level=logging.INFO,
        pathname="access.py",
        lineno=20,
        msg="HTTP request completed",
        args=(),
        exc_info=None,
    )
    record.request_id = "req-1234"
    record.method = "GET"
    record.path = "/api/v1/health"
    record.status_code = 200
    record.latency_ms = 5
    record.client_ip = "127.0.0.1"

    output = formatter.format(record)
    parsed = json.loads(output)
    assert parsed["request_id"] == "req-1234"
    assert parsed["method"] == "GET"
    assert parsed["path"] == "/api/v1/health"
    assert parsed["status_code"] == 200
    assert parsed["latency_ms"] == 5
    assert parsed["client_ip"] == "127.0.0.1"


def test_sanitize_value_redacts_sensitive_keys() -> None:
    """Sensitive keys (password, token, etc.) must be replaced with [REDACTED]."""
    data = {
        "username": "developer",
        "password": "supersecretpassword",
        "api_key": "sk-1234567890",
        "nested": {
            "token": "bearer-token-val",
            "safe_key": "safe_val",
        },
    }
    sanitized = sanitize_value(data)
    assert isinstance(sanitized, dict)
    assert sanitized["username"] == "developer"
    assert sanitized["password"] == "[REDACTED]"
    assert sanitized["api_key"] == "[REDACTED]"
    nested = sanitized["nested"]
    assert isinstance(nested, dict)
    assert nested["token"] == "[REDACTED]"
    assert nested["safe_key"] == "safe_val"


def test_json_formatter_redacts_custom_extras() -> None:
    """Custom fields on log record with sensitive names must be redacted."""
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="credentials event",
        args=(),
        exc_info=None,
    )
    record.password = "mypassword"
    record.api_key = "apikey123"

    output = formatter.format(record)
    parsed = json.loads(output)
    assert parsed["password"] == "[REDACTED]"
    assert parsed["api_key"] == "[REDACTED]"


@pytest.mark.asyncio()
async def test_logging_middleware_logs_request(
    async_client: AsyncClient, caplog: pytest.LogCaptureFixture
) -> None:
    """Every request must produce an access log from scenediff.access."""
    with caplog.at_level(logging.INFO, logger="scenediff.access"):
        response = await async_client.get("/api/v1/health")
        assert response.status_code == 200

    access_records = [r for r in caplog.records if r.name == "scenediff.access"]
    assert len(access_records) >= 1
    rec = access_records[-1]
    assert "method" in rec.__dict__
    assert rec.__dict__["method"] == "GET"
    assert rec.__dict__["path"] == "/api/v1/health"
    assert rec.__dict__["status_code"] == 200
    assert "latency_ms" in rec.__dict__
    assert rec.__dict__["latency_ms"] >= 0


@pytest.mark.asyncio()
async def test_logging_middleware_unknown_client_ip(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """When request is processed, client_ip is recorded."""
    from httpx import ASGITransport

    from app.main import app

    with caplog.at_level(logging.INFO, logger="scenediff.access"):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get("/api/v1/health")
            assert response.status_code == 200

    access_records = [r for r in caplog.records if r.name == "scenediff.access"]
    assert len(access_records) >= 1
    assert access_records[-1].__dict__.get("client_ip") in (
        "unknown",
        "127.0.0.1",
        "",
    )
