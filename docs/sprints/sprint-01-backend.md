# Sprint 01: Backend Foundation

## Overview

Sprint 01 builds the production-grade backend foundation for SceneDiff using FastAPI, Python 3.11+, PostgreSQL 17, and SQLAlchemy 2.0 with asyncpg.

---

## Sprint Tracker (9 / 9 Tasks Complete — Sprint 1 Locked ✅)

| Task | Description | Status |
| --- | --- | --- |
| ✅ Task 01 | Python foundation & virtual environment | Complete |
| ✅ Task 02 | FastAPI project structure & router foundation | Complete |
| ✅ Task 03 | Pydantic Settings configuration engine | Complete |
| ✅ Task 04 | Async SQLAlchemy 2.0 engine & session factory | Complete |
| ✅ Task 05 | Alembic migration foundation & autogenerate | Complete |
| ✅ Task 06 | Database health endpoint (`/api/v1/health`) | Complete |
| ✅ Task 07 | Middleware, logging & exception infrastructure | Complete |
| ✅ Task 08 | Docker runtime & startup migrations | Complete |
| ✅ Task 09 | Testing, validation pipeline & CI foundation | Complete |

---

## Task 06: Database Health Endpoint

### Goal
Transform the health endpoint from a static check into an infrastructure health monitor capable of probing FastAPI application health and PostgreSQL database connectivity.

### Architecture Flow

```
GET /api/v1/health
  ↓
Health Endpoint [Depends(get_db)]
  ↓
AsyncSession (SELECT 1 & latency measurement)
  ↓
PostgreSQL ping (Connected / Disconnected)
  ↓
Standard Response Envelope (ApiResponse)
```

---

## Task 07: Middleware, Structured Logging & Exception Infrastructure

### Goal
Build the observability and trace foundation so every request in SceneDiff is traceable, measurable, and secure across the entire project lifecycle.

### Architecture Flow

```
Incoming HTTP Request
  ↓
RequestID Middleware (Create / Preserve UUID4, set request.state.request_id, echo X-Request-ID)
  ↓
Logging Middleware (Start timer, capture method/path/IP, log latency & status upon completion)
  ↓
CORS Middleware (Apply allowed origins)
  ↓
FastAPI Route Handlers
  ↓
Global Exception Handlers (Normalize errors to ApiResponse envelope, hide stack traces)
  ↓
Structured JSON Logger (Output machine-parseable single-line JSON, redact sensitive keys)
  ↓
Client Response (Headers: X-Request-ID)
```

---

## Task 08: Docker Runtime & Automatic Database Migrations

### Goal
Implement a production-grade multi-stage container runtime that gates backend boot on PostgreSQL readiness, runs Alembic migrations automatically, enforces non-root execution, and provides automated health checks.

### Architecture Flow

```
+-------------------------------------------------------------------------------+
| Container Runtime Environment                                                  |
|                                                                               |
|  [ Backend Container: scenediff_backend ]       [ DB Container: scenediff_postgres ]
|  ├── User: appuser (non-root UID 1000)          ├── Image: postgres:17-alpine
|  ├── Multi-stage: python:3.11-slim              ├── Healthcheck: pg_isready
|  ├── Entrypoint: docker-entrypoint.sh           └── Volume: postgres_data
|  │     ├── 1. Wait for PostgreSQL readiness     
|  │     ├── 2. alembic upgrade head              
|  │     └── 3. exec uvicorn app.main:app         
|  └── Healthcheck: curl http://.../api/v1/health 
|                                                 
|  Backend depends_on: db (condition: service_healthy)
|  Network: scenediff_network (bridge)
+-------------------------------------------------------------------------------+
```

---

## Task 09: Testing, Validation Pipeline & CI Foundation

### Goal
Establish an automated release-quality validation pipeline, developer check scripts, GitHub Actions CI workflow, and integration test coverage across all infrastructure layers.

### Deliverables

1. **Developer Quality Gate Scripts**:
   - `scripts/check.sh` (Linux/macOS): Single-command validation executing Ruff lint, Ruff formatting check, MyPy strict, and Pytest.
   - `scripts/check.ps1` (Windows PowerShell): Cross-platform developer pipeline script matching CI checks.

2. **Continuous Integration Pipeline (`.github/workflows/backend-ci.yml`)**:
   - Automated workflow triggered on pushes to `main`, `dev`, `feat/*`, and PRs.
   - Executes with a live PostgreSQL 17 container service health probe.
   - Enforces all four quality gates: Ruff lint, Ruff format, MyPy strict, and Pytest test suite.
   - Validates `docker compose config` and builds the backend container image.

3. **Integration Test Suite (`backend/tests/test_integration_health.py`)**:
   - Validates full probe request-response lifecycle against the API contract.
   - Validates dynamic database failure and recovery cycles.
   - Validates CORS preflight headers and origin policies.
   - Validates RequestID correlation across all middleware layers.
   - Validates environment variable parity between `docker-compose.yml` and `Settings`.
   - Validates `alembic.ini` and `alembic/env.py` configuration integrity.

---

## Final Quality Gate Summary

| Quality Gate | Tool / Command | Status | Result |
| --- | --- | --- | --- |
| Linting | `ruff check .` | ✅ PASS | 0 errors / 0 warnings |
| Formatting | `ruff format --check .` | ✅ PASS | 37 files formatted |
| Type Safety | `mypy .` (Strict) | ✅ PASS | 0 errors across 34 source files |
| Unit & Integration Tests | `pytest` | ✅ PASS | 115 tests passed in 0.99s |
| Developer Pipeline | `scripts/check.ps1` / `scripts/check.sh` | ✅ PASS | Verified all 4 stages |
| CI Pipeline | `.github/workflows/backend-ci.yml` | ✅ PASS | Ready for GitHub Actions |
| Container Runtime | `docker compose config` | ✅ PASS | Backend + Postgres runtime verified |
