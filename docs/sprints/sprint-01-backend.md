# Sprint 01: Backend Foundation

## Overview

Sprint 01 builds the production-grade backend foundation for SceneDiff using FastAPI, Python 3.11+, PostgreSQL 17, and SQLAlchemy 2.0 with asyncpg.

---

## Sprint Tracker

| Task | Description | Status |
| --- | --- | --- |
| ✅ Task 01 | Python foundation & virtual environment | Complete |
| ✅ Task 02 | FastAPI project structure & router foundation | Complete |
| ✅ Task 03 | Pydantic Settings configuration engine | Complete |
| ✅ Task 04 | Async SQLAlchemy 2.0 engine & session factory | Complete |
| ✅ Task 05 | Alembic migration foundation & autogenerate | Complete |
| ✅ Task 06 | Database health endpoint (`/api/v1/health`) | Complete |
| ✅ Task 07 | Middleware, logging & exception infrastructure | Complete |
| ✅ Task 08 | Docker & startup migrations | Complete |
| ⬜ Task 09 | Integration tests | Pending |

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

### Key Artifacts

1. **`backend/Dockerfile`**:
   - Multi-stage build (`builder` -> `runner`) based on `python:3.11-slim`.
   - Security: Runs as unprivileged `appuser` (UID/GID 1000).
   - Minimal attack surface with build dependencies pruned from the final image.

2. **`backend/docker-entrypoint.sh`**:
   - `set -euo pipefail` strict error handling.
   - Dialect-agnostic asyncpg database ping (`SELECT 1`) with timeout and retries.
   - Automatic migration runner: executes `alembic upgrade head` before process start.
   - Direct `exec "$@"` process handover ensuring PID 1 signal forwarding for graceful shutdown.

3. **`backend/.dockerignore`**:
   - Excludes `.venv`, caches (`.pytest_cache`, `.ruff_cache`, `.mypy_cache`), test suites, and git metadata from the build context.

4. **`docker-compose.yml`**:
   - Declares `db` (`postgres:17-alpine`) with persistent volume and `pg_isready` healthcheck.
   - Declares `backend` with `depends_on: db: { condition: service_healthy }` to eliminate cold-start race conditions.
   - Defines bridge network `scenediff_network` and volume `postgres_data`.

5. **`backend/tests/test_docker_runtime.py`**:
   - Automated tests validating Dockerfile directives, non-root user declaration, entrypoint script logic, `.dockerignore` patterns, and compose topology.

---

## Validation Status

- `ruff check .` — Passed (0 warnings)
- `ruff format --check .` — Passed (36 files formatted)
- `mypy .` — Passed (Strict mode, 0 errors in 33 files)
- `pytest` — 109 passed in 0.82s
