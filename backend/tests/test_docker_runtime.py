"""Tests for Docker runtime configuration, Dockerfile, entrypoint, and compose file."""

from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]


def _get_project_root() -> Path:
    """Return repository root path."""
    return Path(__file__).resolve().parent.parent.parent


def test_dockerfile_exists_and_uses_non_root() -> None:
    """Dockerfile must use multi-stage builds and a non-root appuser."""
    dockerfile_path = _get_project_root() / "backend" / "Dockerfile"
    assert dockerfile_path.exists(), "backend/Dockerfile must exist"

    content = dockerfile_path.read_text(encoding="utf-8")
    assert "FROM python:3.11-slim AS builder" in content
    assert "FROM python:3.11-slim AS runner" in content
    assert "USER appuser" in content
    assert 'ENTRYPOINT ["./docker-entrypoint.sh"]' in content
    assert "EXPOSE 8000" in content


def test_docker_entrypoint_script() -> None:
    """Entrypoint script must wait for DB, run alembic migrations, and exec CMD."""
    entrypoint_path = _get_project_root() / "backend" / "docker-entrypoint.sh"
    assert entrypoint_path.exists(), "backend/docker-entrypoint.sh must exist"

    content = entrypoint_path.read_text(encoding="utf-8")
    assert "set -euo pipefail" in content
    assert "alembic upgrade head" in content
    assert 'exec "$@"' in content
    assert "check_db" in content or "SELECT 1" in content


def test_dockerignore_configuration() -> None:
    """.dockerignore must exclude virtual environments, caches, and tests."""
    dockerignore_path = _get_project_root() / "backend" / ".dockerignore"
    assert dockerignore_path.exists(), "backend/.dockerignore must exist"

    content = dockerignore_path.read_text(encoding="utf-8")
    assert ".venv/" in content
    assert "__pycache__/" in content
    assert ".pytest_cache/" in content
    assert ".git/" in content


def test_docker_compose_valid_structure() -> None:
    """docker-compose.yml must define backend, db, volumes, and networks."""
    compose_path = _get_project_root() / "docker-compose.yml"
    assert compose_path.exists(), "docker-compose.yml must exist"

    data: dict[str, Any] = yaml.safe_load(compose_path.read_text(encoding="utf-8"))
    assert "services" in data
    assert "db" in data["services"]
    assert "backend" in data["services"]
    assert "networks" in data
    assert "volumes" in data
    assert "postgres_data" in data["volumes"]
    assert "scenediff_network" in data["networks"]


def test_docker_compose_database_healthcheck() -> None:
    """Database service must define a pg_isready healthcheck."""
    compose_path = _get_project_root() / "docker-compose.yml"
    data: dict[str, Any] = yaml.safe_load(compose_path.read_text(encoding="utf-8"))
    db = data["services"]["db"]

    assert "healthcheck" in db
    test_cmd = db["healthcheck"]["test"]
    assert any("pg_isready" in str(arg) for arg in test_cmd)
    assert db["image"] == "postgres:17-alpine"
    assert "postgres_data:/var/lib/postgresql/data" in db["volumes"]


def test_docker_compose_backend_readiness_gate() -> None:
    """Backend service must wait for healthy database before starting."""
    compose_path = _get_project_root() / "docker-compose.yml"
    data: dict[str, Any] = yaml.safe_load(compose_path.read_text(encoding="utf-8"))
    backend = data["services"]["backend"]

    assert "depends_on" in backend
    assert "db" in backend["depends_on"]
    assert backend["depends_on"]["db"]["condition"] == "service_healthy"

    assert "healthcheck" in backend
    assert any("/api/v1/health" in str(arg) for arg in backend["healthcheck"]["test"])
    assert "8000:8000" in backend["ports"]
