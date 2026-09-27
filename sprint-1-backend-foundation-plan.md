# Sprint 1 — Backend Foundation Plan

## Overview

Stand up the complete backend foundation inside `backend/` only. The goal is a
running FastAPI application inside Docker that connects to PostgreSQL via
SQLAlchemy async, exposes a `/health` endpoint, has structured logging and
request-ID middleware, and is ready for feature development in Sprint 2.

**Scope:** `backend/` directory only.  
**Excluded:** frontend, packages, scripts, docs (except `docs/sprints/sprint-01-backend.md`).  
**Governing documents:** `AGENTS.md`, `RULES.md`, `SECURITY.md`, `.bob/context/architecture.md`,
`.bob/context/api-contract.md`, `.bob/context/coding-standards.md`.

---

## Sub-Task 1 — Python Project Setup

**Status:** [ ] pending

### Intent
Establish the Python project metadata and dependency manifest so every other
sub-task has a reproducible environment to build against.

### Expected Outcomes
- `backend/pyproject.toml` declares project name, Python ≥ 3.11 requirement,
  and all direct runtime dependencies.
- `backend/requirements.txt` (or `requirements-dev.txt`) covers dev/test extras.
- No code is importable yet — this task is purely configuration.

### Todo List
- [ ] Create `backend/pyproject.toml` using the standard `[project]` table.
- [ ] Pin runtime dependencies: `fastapi`, `uvicorn[standard]`, `sqlalchemy[asyncio]`,
      `asyncpg`, `alembic`, `pydantic`, `pydantic-settings`, `python-dotenv`.
- [ ] Add dev dependencies: `pytest`, `pytest-asyncio`, `httpx`, `ruff`, `mypy`.
- [ ] Add `[tool.ruff]` and `[tool.mypy]` configuration sections aligned with
      `coding-standards.md` (Python 3.11+, strict types).
- [ ] Create `backend/.python-version` pinning `3.11`.

### Relevant Context
- `coding-standards.md` — Python 3.11+, type hints everywhere.
- `RULES.md` — Done Checklist requires lint and type checks to pass.

---

## Sub-Task 2 — FastAPI Application Structure

**Status:** [ ] pending

### Intent
Lay out the FastAPI application directory tree that matches the ownership rules
in `architecture.md`: routes own validation/serialisation only, services
coordinate workflows, models never leave API responses.

### Expected Outcomes
- `backend/app/` package exists with `__init__.py`.
- `backend/app/main.py` creates the `FastAPI` application instance, registers
  routers, and attaches middleware.
- `backend/app/api/v1/` package exists with `router.py` that aggregates v1
  route modules.
- `backend/app/core/` package exists for config and logging utilities.
- `backend/app/models/` package exists (empty, ready for Sprint 2 models).
- `backend/app/schemas/` package exists (empty, ready for Sprint 2 schemas).
- `backend/app/services/` package exists (empty, ready for Sprint 2 services).

### Todo List
- [ ] Create directory tree:
  ```
  backend/
    app/
      __init__.py
      main.py
      api/
        __init__.py
        v1/
          __init__.py
          router.py
          endpoints/
            __init__.py
            health.py
      core/
        __init__.py
        config.py
        logging.py
      db/
        __init__.py
        session.py
        base.py
      models/
        __init__.py
      schemas/
        __init__.py
      services/
        __init__.py
  ```
- [ ] `app/main.py` — instantiate `FastAPI(title="SceneDiff", version="0.1.0")`,
      include `api_router` from `app/api/v1/router.py`.
- [ ] `app/api/v1/router.py` — create an `APIRouter(prefix="/api/v1")` and
      include the health sub-router.
- [ ] All `__init__.py` files are empty or export the package-level symbol.

### Relevant Context
- `architecture.md` — Ownership rules: routes never contain business logic.
- `api-contract.md` — All routes live under `/api/v1`.

---

## Sub-Task 3 — Configuration and Settings

**Status:** [ ] pending

### Intent
Centralise all environment-driven configuration in one `Settings` class using
`pydantic-settings`, so every module reads from a single source of truth and
secrets are never hard-coded.

### Expected Outcomes
- `backend/app/core/config.py` contains a `Settings` class that reads from
  environment variables.
- `backend/.env.example` documents required variables without real values.
- No secret values are committed anywhere (enforces `SECURITY.md`).

### Todo List
- [ ] Create `app/core/config.py` with a `pydantic-settings` `Settings` class.
- [ ] Include fields: `APP_ENV`, `DATABASE_URL` (async DSN format),
      `LOG_LEVEL`, `ALLOWED_ORIGINS`.
- [ ] `DATABASE_URL` must default to `None` and raise a validation error if
      unset — never fall back to a hard-coded string.
- [ ] Export a module-level `settings = Settings()` singleton.
- [ ] Create `backend/.env.example`:
      ```
      APP_ENV=development
      DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/scenediff
      LOG_LEVEL=INFO
      ALLOWED_ORIGINS=http://localhost:3000
      ```
- [ ] Add `.env` to `.gitignore` (already present at root; verify `backend/.env`
      is also covered).

### Relevant Context
- `SECURITY.md` — Never upload `.env`. Never log credentials.
- `coding-standards.md` — Typed Python.

---

## Sub-Task 4 — SQLAlchemy Async Database Setup

**Status:** [ ] pending

### Intent
Configure the async SQLAlchemy engine and session factory so all database
interaction in future sprints is non-blocking. Establish `Base` for declarative
model inheritance.

### Expected Outcomes
- `backend/app/db/session.py` exports `async_engine` and `async_session_factory`.
- `backend/app/db/base.py` exports `Base` (declarative base).
- A FastAPI dependency `get_db` yields an `AsyncSession` and closes it reliably.
- No direct engine creation outside `db/session.py`.

### Todo List
- [ ] `app/db/session.py` — create `async_engine` via
      `create_async_engine(settings.DATABASE_URL, echo=settings.APP_ENV == "development")`.
- [ ] Create `async_session_factory = async_sessionmaker(async_engine, expire_on_commit=False)`.
- [ ] Define `async def get_db()` as a FastAPI dependency that yields
      `AsyncSession` within a try/finally.
- [ ] `app/db/base.py` — define `Base = declarative_base()`.
- [ ] Import guard: `app/db/__init__.py` exports only `Base`, `get_db`.

### Relevant Context
- `coding-standards.md` — Async services where appropriate.
- `architecture.md` — Database layer stores sanitised results only.

---

## Sub-Task 5 — Alembic Migration Setup

**Status:** [ ] pending

### Intent
Bootstrap Alembic inside `backend/` configured for async migrations so schema
changes are version-controlled from day one.

### Expected Outcomes
- `backend/alembic.ini` points to the migrations directory.
- `backend/alembic/env.py` uses the async engine and imports `Base.metadata`
  for autogenerate support.
- `backend/alembic/versions/` is empty but tracked.
- Running `alembic upgrade head` inside the container succeeds (no tables to
  create yet beyond what `Base.metadata` contains).

### Todo List
- [ ] Run `alembic init alembic` inside `backend/` (or create files manually).
- [ ] Edit `alembic.ini` to set `script_location = alembic` and remove the
      hard-coded `sqlalchemy.url` (URL comes from `settings`).
- [ ] Edit `alembic/env.py` to:
  - Import `settings` from `app.core.config`.
  - Import `Base` from `app.db.base`.
  - Set `config.set_main_option("sqlalchemy.url", str(settings.DATABASE_URL))`.
  - Use `run_async_migrations` pattern for async engine support.
- [ ] Create `backend/alembic/versions/.gitkeep`.
- [ ] Document migration command in `backend/README.md`.

### Relevant Context
- `RULES.md` — Done Checklist requires Docker to start; migrations must run
  cleanly inside Docker.

---

## Sub-Task 6 — Health Endpoint

**Status:** [ ] pending

### Intent
Implement the `/api/v1/health` endpoint that confirms the application is alive
and the database is reachable, following the standard response envelope from
`api-contract.md`.

### Expected Outcomes
- `GET /api/v1/health` returns `200 OK` with the standard envelope when healthy.
- If the database is unreachable the endpoint returns `503` (not `500`), with
  `success: false` and a safe error message.
- ORM models are not returned in the response (uses a schema).

### Todo List
- [ ] Create `app/schemas/health.py` with `HealthResponse(BaseModel)` containing
      `success: bool`, `data: dict`, `error: str | None`, `metadata: dict`.
- [ ] Create `app/api/v1/endpoints/health.py` with router and `GET /health` handler.
- [ ] Handler performs a lightweight DB ping (`SELECT 1`) using `get_db` dependency.
- [ ] On success: `data = {"status": "ok", "version": "0.1.0"}`.
- [ ] On DB failure: catch exception, return `503` with `success: false`.
- [ ] Register health router in `app/api/v1/router.py`.

### Relevant Context
- `api-contract.md` — Response envelope: `success`, `data`, `error`, `metadata`.
- `architecture.md` — Routes own validation/serialisation only.

---

## Sub-Task 7 — Middleware and Structured Logging

**Status:** [ ] pending

### Intent
Add request-ID injection and structured JSON logging so every request is
traceable through logs without exposing secrets.

### Expected Outcomes
- Every request receives a `X-Request-ID` header (generated if absent).
- All log lines are JSON with fields: `level`, `timestamp`, `request_id`,
  `message`.
- No `Authorization` headers, cookies, or bearer tokens appear in logs
  (enforces `SECURITY.md`).
- CORS middleware is configured from `settings.ALLOWED_ORIGINS`.

### Todo List
- [ ] Create `app/core/logging.py` — configure `logging` with a JSON formatter.
      Use stdlib `logging`; no third-party logging framework required.
- [ ] Create `app/middleware/` package with `request_id.py`:
      - Starlette `BaseHTTPMiddleware` subclass.
      - Generate `uuid4` request ID if `X-Request-ID` header is absent.
      - Attach to `request.state.request_id`.
      - Append `X-Request-ID` to response headers.
- [ ] Register `RequestIDMiddleware` in `app/main.py`.
- [ ] Add `CORSMiddleware` in `app/main.py` using `settings.ALLOWED_ORIGINS`.
- [ ] Never log: `Authorization`, `Cookie`, `Set-Cookie` headers.
- [ ] Unit test: request without `X-Request-ID` → response contains one.

### Relevant Context
- `SECURITY.md` — Never log Authorization headers, never store cookies.
- `AGENTS.md` — Security by default.

---

## Sub-Task 8 — Dockerfile and Docker Compose Completion

**Status:** [ ] pending

### Intent
Build a production-ready `Dockerfile` for the backend and complete the
`docker-compose.yml` skeleton so `docker compose up` starts a working stack.

### Expected Outcomes
- `backend/Dockerfile` builds successfully.
- `docker compose up` starts `scenediff_backend` and `scenediff_postgres`.
- Backend container waits for Postgres to be ready before accepting traffic.
- `GET http://localhost:8000/api/v1/health` returns `200` from the host.
- No secrets in the `Dockerfile`; all config via environment variables.

### Todo List
- [ ] Create `backend/Dockerfile`:
      - Base image: `python:3.11-slim`.
      - `WORKDIR /app`.
      - Copy and install `pyproject.toml` / dependencies first (layer cache).
      - Copy application source.
      - `CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]`.
- [ ] Complete root `docker-compose.yml`:
      - `backend` service: `build: ./backend`, port `8000:8000`, `env_file: ./backend/.env`,
        `depends_on: db`, network `scenediff_network`.
      - `db` service: image `postgres:16-alpine`, `POSTGRES_*` env vars,
        volume `postgres_data:/var/lib/postgresql/data`, network `scenediff_network`.
      - Health-check on `db` using `pg_isready`.
- [ ] Create `backend/.env` (gitignored) for local development.
- [ ] Add Alembic migration step to container startup or document the
      `docker compose exec backend alembic upgrade head` command.

### Relevant Context
- `RULES.md` — Docker must start cleanly.
- `SECURITY.md` — Local secrets (POSTGRES_USER, POSTGRES_PASSWORD) are
  `LOCAL_ONLY` and must never be committed.
- `docker-compose.yml` — Service stubs already exist; complete them, do not replace.

---

## Sub-Task 9 — Unit and Integration Tests

**Status:** [ ] pending

### Intent
Provide the minimum test suite required by `AGENTS.md` (unit + integration)
covering the health endpoint and middleware, using `pytest-asyncio` and
`httpx.AsyncClient`.

### Expected Outcomes
- `backend/tests/` directory with `conftest.py`, `test_health.py`,
  `test_middleware.py`.
- All tests pass with `pytest backend/tests/`.
- Tests do not connect to a real database (mock or override `get_db`).

### Todo List
- [ ] Create `backend/tests/__init__.py`.
- [ ] Create `backend/tests/conftest.py`:
      - Override `get_db` with an in-memory mock that returns a passing ping.
      - Provide `async_client` fixture using `httpx.AsyncClient` + `ASGITransport`.
- [ ] Create `backend/tests/test_health.py`:
      - Test: healthy DB → `200`, `success: true`.
      - Test: unhealthy DB → `503`, `success: false`.
- [ ] Create `backend/tests/test_middleware.py`:
      - Test: request without `X-Request-ID` → response header present.
      - Test: request with `X-Request-ID` → same value echoed in response.
- [ ] All tests must pass before the sub-task is marked done.

### Relevant Context
- `AGENTS.md` — Every feature must include unit tests and integration tests.
- `RULES.md` — Tests pass is a Done Checklist requirement.

---

## Validation Checklist (Full Sprint)

These checks must all pass before Sprint 1 is considered complete:

- [ ] `ruff check backend/` — zero errors.
- [ ] `mypy backend/app` — zero errors.
- [ ] `pytest backend/tests/` — all tests pass.
- [ ] `docker compose up --build` — both containers start without errors.
- [ ] `curl http://localhost:8000/api/v1/health` — returns `200`.
- [ ] `docker compose exec backend alembic upgrade head` — succeeds.
- [ ] No secrets committed to git (`git log --all` clean).
- [ ] `docs/sprints/sprint-01-backend.md` updated with sprint summary.
