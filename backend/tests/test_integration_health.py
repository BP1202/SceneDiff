"""Integration tests for health probes, database recovery, and environment parity."""

from configparser import ConfigParser
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock

from httpx import AsyncClient
import pytest
from sqlalchemy.exc import OperationalError
import yaml  # type: ignore[import-untyped]

from app.core.config import Settings


def _get_project_root() -> Path:
    """Return repository root path."""
    return Path(__file__).resolve().parent.parent.parent


@pytest.mark.asyncio()
async def test_integration_health_probe_full_flow(
    async_client: AsyncClient,
) -> None:
    """Test full health check request-response flow against API contract."""
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    assert "x-request-id" in response.headers

    body = response.json()
    assert body["success"] is True
    assert body["data"]["status"] == "ok"
    assert body["data"]["version"] == "0.1.0"
    assert body["data"]["database"]["status"] == "connected"
    assert body["data"]["database"]["engine"] == "postgresql"
    assert isinstance(body["data"]["database"]["latency_ms"], int)
    assert body["error"] is None
    assert body["request_id"] == response.headers["x-request-id"]
    assert "timestamp" in body


@pytest.mark.asyncio()
async def test_integration_database_recovery_cycle(
    async_client: AsyncClient,
    mock_db: AsyncMock,
) -> None:
    """Verify endpoint transitions to degraded on failure and recovers when healthy."""
    # 1. Simulate database failure
    mock_db.execute.side_effect = OperationalError(
        "DB connection dropped", None, Exception("dropped")
    )
    fail_response = await async_client.get("/api/v1/health")
    assert fail_response.status_code == 503
    fail_body = fail_response.json()
    assert fail_body["success"] is False
    assert fail_body["data"]["status"] == "degraded"
    assert fail_body["data"]["database"]["status"] == "disconnected"
    assert fail_body["error"]["code"] == "DATABASE_UNAVAILABLE"

    # 2. Simulate database recovery
    mock_db.execute.side_effect = None
    recover_response = await async_client.get("/api/v1/health")
    assert recover_response.status_code == 200
    recover_body = recover_response.json()
    assert recover_body["success"] is True
    assert recover_body["data"]["status"] == "ok"
    assert recover_body["data"]["database"]["status"] == "connected"
    assert recover_body["error"] is None


@pytest.mark.asyncio()
async def test_integration_cors_preflight_headers(
    async_client: AsyncClient,
) -> None:
    """Verify CORS preflight OPTIONS request returns allowed origins."""
    headers = {
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "X-Request-ID",
    }
    response = await async_client.options("/api/v1/health", headers=headers)
    assert response.status_code == 200
    assert (
        response.headers.get("access-control-allow-origin") == "http://localhost:3000"
    )


@pytest.mark.asyncio()
async def test_integration_request_correlation_across_middleware_chain(
    async_client: AsyncClient,
) -> None:
    """Verify client-supplied request correlation ID is echoed across all layers."""
    trace_id = "trace-correlation-id-998877"
    response = await async_client.get(
        "/api/v1/health", headers={"X-Request-ID": trace_id}
    )
    assert response.headers["x-request-id"] == trace_id

    body = response.json()
    assert body["request_id"] == trace_id
    assert body["metadata"]["request_id"] == trace_id


def test_integration_docker_compose_environment_parity() -> None:
    """Validate that environment variables in docker-compose.yml exist in Settings."""
    compose_path = _get_project_root() / "docker-compose.yml"
    data: dict[str, Any] = yaml.safe_load(compose_path.read_text(encoding="utf-8"))
    compose_env = data["services"]["backend"]["environment"]

    settings_fields = set(Settings.model_fields.keys())

    # Check each variable declared in docker-compose.yml
    for env_var in compose_env:
        var_name = env_var.split("=")[0].strip()
        assert var_name in settings_fields, (
            f"Variable {var_name} from compose not found in Settings"
        )


def test_integration_alembic_configuration_integrity() -> None:
    """Validate alembic.ini points to the correct script location."""
    ini_path = _get_project_root() / "backend" / "alembic.ini"
    assert ini_path.exists(), "alembic.ini must exist"

    config = ConfigParser()
    config.read(ini_path)
    assert config.has_section("alembic")
    script_loc = config.get("alembic", "script_location")
    assert script_loc == "alembic"

    env_py = _get_project_root() / "backend" / "alembic" / "env.py"
    assert env_py.exists(), "alembic/env.py must exist"
