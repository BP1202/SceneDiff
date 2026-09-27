# Sprint 02 — Behavior Trace Engine (Backend)

**Status:** ✅ Complete  
**Branch:** `feat/sprint-2-behavior-trace-engine`  
**Validation:** `ruff` ✅ · `mypy` ✅ · `pytest 220/220` ✅ · `alembic history` ✅

---

## 1. Mission

Sprint 2 delivers SceneDiff's core capability: converting Git commits into
structured, secure behavior traces that can be compared, stored, and exposed
to IBM Bob for AI-assisted debugging.

---

## 2. Architecture

```
POST /api/v1/traces
        │
        ▼
  TraceSessionCreate (Pydantic validation)
        │
        ▼
  trace_storage.create_trace_session()   ─── TraceSession (PENDING) → DB
        │
        ▼
  [Background] trace_processor.process_trace(session_id, unified_diff)
        │
        ├── 1. update_status(COLLECTING)
        ├── 2. diff_parser.parse_diff()        ─── ParsedDiff[]
        ├── 3. update_status(PROCESSING)
        ├── 4. behavior_hash.generate_behavior_hash()
        ├── 5. secret_shield.mask_metadata()   ─── sanitize before write
        ├── 6. trace_storage.store_event()     ─── TraceEvent[] → DB
        └── 7. update_status(COMPLETED)
                    │ on error
                    └── update_status(FAILED) + structured log
```

---

## 3. Database Schema

### Table: `trace_sessions`

| Column            | Type                  | Constraints                   |
|-------------------|-----------------------|-------------------------------|
| `id`              | `UUID` PK             | not null, default uuid4       |
| `repository_name` | `VARCHAR(255)`        | not null, indexed             |
| `base_commit`     | `VARCHAR(40)`         | not null                      |
| `head_commit`     | `VARCHAR(40)`         | not null                      |
| `branch`          | `VARCHAR(255)`        | not null                      |
| `status`          | `ENUM tracestatus`    | not null, indexed, default PENDING |
| `created_at`      | `TIMESTAMPTZ`         | not null, server default now(), indexed |
| `updated_at`      | `TIMESTAMPTZ`         | not null, server default now() |

**ENUM `tracestatus`:** `PENDING` · `COLLECTING` · `PROCESSING` · `COMPLETED` · `FAILED`

**Indexes:**
- `ix_trace_sessions_repository_name`
- `ix_trace_sessions_status`
- `ix_trace_sessions_created_at`

### Table: `trace_events`

| Column              | Type           | Constraints                        |
|---------------------|----------------|------------------------------------|
| `id`                | `UUID` PK      | not null, default uuid4            |
| `trace_session_id`  | `UUID` FK      | → `trace_sessions.id` ON DELETE CASCADE, indexed |
| `event_type`        | `VARCHAR(100)` | not null, indexed                  |
| `file_path`         | `VARCHAR(1024)`| not null                           |
| `function_name`     | `VARCHAR(255)` | nullable                           |
| `line_number`       | `INTEGER`      | nullable                           |
| `behavior_hash`     | `VARCHAR(64)`  | nullable, indexed                  |
| `metadata`          | `JSONB`        | nullable — sanitized by Secret Shield |
| `created_at`        | `TIMESTAMPTZ`  | not null, server default now()     |

**Indexes:**
- `ix_trace_events_trace_session_id`
- `ix_trace_events_event_type`
- `ix_trace_events_behavior_hash`

---

## 4. API Contracts

All endpoints return the standard `ApiResponse` envelope:

```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "metadata": { "request_id": "...", "api_version": "v1" },
  "request_id": "...",
  "timestamp": "2026-09-27T00:00:00Z"
}
```

### POST `/api/v1/traces`

Create a new trace session.

**Request body:**
```json
{
  "repository_name": "owner/repo",
  "base_commit": "abc1234",
  "head_commit": "def5678",
  "branch": "main"
}
```

**Validation rules:**
- `repository_name`: pattern `^[A-Za-z0-9_.\-]+(\/[A-Za-z0-9_.\-]+)?$`, max 255 chars
- `base_commit` / `head_commit`: 7–40 hexadecimal characters
- `branch`: pattern `^[A-Za-z0-9/_.\\-]+$`, max 255 chars

**Response (201):**
```json
{
  "success": true,
  "data": {
    "id": "<uuid>",
    "repository_name": "owner/repo",
    "base_commit": "abc1234",
    "head_commit": "def5678",
    "branch": "main",
    "status": "PENDING",
    "created_at": "...",
    "updated_at": "..."
  }
}
```

---

### GET `/api/v1/traces`

List trace sessions with pagination and optional filters.

**Query params:**
| Param             | Type     | Description                         |
|-------------------|----------|-------------------------------------|
| `status`          | string   | Filter by TraceStatus value         |
| `repository_name` | string   | Filter by exact repository name     |
| `limit`           | int 1–100| Max results per page (default 20)   |
| `offset`          | int ≥ 0  | Results to skip (default 0)         |

**Pagination metadata** in `ApiResponse.metadata.pagination`:
```json
{ "total": 5, "limit": 20, "offset": 0 }
```

---

### GET `/api/v1/traces/{id}`

Retrieve a single trace session by UUID.

- **200** — session found
- **404** — session not found
- **422** — invalid UUID format

---

### GET `/api/v1/traces/{id}/events`

List behavior events for a session.

**Query params:**
| Param        | Type       | Description                                |
|--------------|------------|--------------------------------------------|
| `event_type` | string     | Filter by event type (e.g. FUNCTION_MODIFIED) |
| `file_path`  | string     | Filter by exact file path                  |
| `limit`      | int 1–200  | Max results (default 50)                   |
| `offset`     | int ≥ 0    | Skip (default 0)                           |

- **200** — events list (may be empty)
- **404** — parent session not found

---

## 5. Service Layer

### `services/trace_storage.py`

Pure async database operations — no business logic in routes.

| Function                | Description                                        |
|-------------------------|----------------------------------------------------|
| `create_trace_session()` | Insert a new PENDING TraceSession                 |
| `get_session()`          | Fetch one session by UUID                         |
| `update_status()`        | Change session status + updated_at                |
| `list_sessions()`        | Paginated query with optional status/repo filters |
| `delete_failed_session()`| Hard-delete only if status == FAILED             |
| `store_event()`          | Insert TraceEvent after Secret Shield sanitizes metadata |
| `list_events()`          | Paginated event query with optional filters       |

### `services/behavior_hash.py`

Generates deterministic SHA-256 behavior hashes.

- **Inputs:** `file_path`, `function_name`, `diff_snippet`
- **Normalization:** strips comments (`#`, `//`), collapses whitespace
- **Stable ordering:** components sorted before hashing — argument order doesn't matter
- **Output:** 64-character lowercase hex digest

### `services/diff_parser.py`

Pure Python parser for Git unified diff output. No subprocess.

- **Supported languages:** Python (`.py`), TypeScript (`.ts`, `.tsx`), JavaScript (`.js`, `.jsx`, `.mjs`, `.cjs`)
- **Output:** `list[ParsedDiff]` — one per changed file
- **Extracts:** added/removed/modified functions, line numbers, raw change hunks

### `services/secret_shield.py`

Pre-storage sanitization of metadata. Regex-only, deterministic.

**Detectors (9 patterns):**

| Category       | Pattern                                         |
|----------------|-------------------------------------------------|
| JWT            | `eyJ…` three-part base64url                    |
| AWS_ACCESS_KEY | `AKIA…` 20-char key IDs                        |
| AWS_SECRET_KEY | 40-char alphanumeric+/+ sequences               |
| GITHUB_TOKEN   | `ghp_`, `gho_`, `ghs_`, `ghr_`, `github_pat_` |
| BEARER_TOKEN   | `Bearer <token>`                                |
| OAUTH_TOKEN    | `access_token=`, `refresh_token=`               |
| API_KEY        | `api_key=`, `x-api-key:`                        |
| PASSWORD       | `password=…`                                    |
| COOKIE         | `Cookie:` / `Set-Cookie:` headers               |
| SSH_PRIVATE_KEY| PEM `-----BEGIN PRIVATE KEY-----` blocks         |

All matched values replaced with `[REDACTED]`. Input never mutated.

### `services/trace_processor.py`

Background pipeline coordinator.

**Pipeline:**
1. `COLLECTING` — parse unified diff → `list[ParsedDiff]`
2. `PROCESSING` — for each file: generate behavior hash, store FILE_CHANGED + function-level events
3. `COMPLETED` — mark session done

**Event types emitted:**
- `FILE_CHANGED` — one per changed file
- `FUNCTION_ADDED` — one per added function
- `FUNCTION_REMOVED` — one per removed function
- `FUNCTION_MODIFIED` — one per function present in both added and removed sets

**Error handling:** any exception → `FAILED` status + structured log. `cleanup_failed_session()` provides hard-delete.

---

## 6. Alembic Migration

**File:** `alembic/versions/20260927_0001_sprint2_trace_sessions_and_events.py`  
**Revision:** `0001`  
**Chain:** `<base>` → `0001 (head)`

```
alembic upgrade head    # applies Sprint 2 schema
alembic downgrade base  # drops all Sprint 2 tables + ENUM type
alembic upgrade head    # re-applies cleanly
```

The migration:
- Creates `tracestatus` ENUM with `checkfirst=True` (idempotent)
- Creates `trace_sessions` with indexes
- Creates `trace_events` with CASCADE FK and indexes
- Drops in reverse order on downgrade

---

## 7. Security Notes

| Control                          | Implementation                                |
|----------------------------------|-----------------------------------------------|
| Secret masking before persistence| `secret_shield.mask_metadata()` in `store_event()` |
| No raw secrets in logs           | Logger never logs request body or metadata values |
| No secrets in ORM models         | `metadata_` column comment explicitly states sanitization |
| Validation before persistence    | Pydantic field validators reject malformed SHAs, repos, branches |
| Cascade delete on session delete | `trace_events.trace_session_id` FK with `ON DELETE CASCADE` |
| FAILED-only delete guard         | `delete_failed_session()` enforces status check |

---

## 8. Validation Summary

| Gate                  | Result         |
|-----------------------|----------------|
| `ruff check .`        | ✅ All checks passed |
| `ruff format --check .` | ✅ 56 files formatted |
| `mypy app/`           | ✅ No issues in 32 files |
| `pytest -q`           | ✅ 220/220 passed |
| `alembic history`     | ✅ `<base> -> 0001 (head)` |

**Test coverage areas:**
- Models (TraceSession, TraceEvent, TraceStatus)
- Trace Storage CRUD (create, get, update_status, list, delete_failed)
- Traces API (POST, GET list, GET by ID — 201/200/404/422 responses)
- Events API (GET with filters — 200/404)
- Behavior Hash Engine (determinism, whitespace insensitivity, comment stripping)
- Diff Parser (Python/TypeScript/JS function extraction, hunk parsing)
- Secret Shield (9 pattern categories, nested dict/list masking, input immutability)
- Trace Processor (pipeline status transitions, FAILED handling, empty diff)
- Alembic (migration file structure, upgrade/downgrade functions, Sprint 2 tables)

---

## 9. Files Changed

### New files (Sprint 2)

| Path | Description |
|------|-------------|
| `app/models/trace_session.py` | TraceSession ORM + TraceStatus enum |
| `app/models/trace_event.py` | TraceEvent ORM |
| `app/schemas/traces.py` | Pydantic schemas: TraceSessionCreate, TraceSessionResponse, TraceEventResponse, ApiResponse, PaginatedMeta |
| `app/services/trace_storage.py` | Async DB operations service |
| `app/services/behavior_hash.py` | Deterministic SHA-256 hash engine |
| `app/services/diff_parser.py` | Git unified diff parser (no subprocess) |
| `app/services/secret_shield.py` | Pre-storage secret masking utility |
| `app/services/trace_processor.py` | Background pipeline coordinator |
| `app/api/v1/endpoints/traces.py` | POST/GET traces endpoints |
| `app/api/v1/endpoints/events.py` | GET events endpoint |
| `alembic/versions/20260927_0001_sprint2_trace_sessions_and_events.py` | Database migration |
| `tests/test_models.py` | Model unit tests |
| `tests/test_trace_storage.py` | Storage service tests |
| `tests/test_traces_api.py` | Traces API tests |
| `tests/test_events_api.py` | Events API tests |
| `tests/test_behavior_hash.py` | Behavior hash tests |
| `tests/test_diff_parser.py` | Diff parser tests |
| `tests/test_secret_shield.py` | Secret Shield tests |
| `tests/test_trace_processor.py` | Processor pipeline tests |

### Modified files (Sprint 1 compatibility)

| Path | Change |
|------|--------|
| `pyproject.toml` | Added `TC003` to ruff ignore (SQLAlchemy ORM runtime requirement) |
| `tests/test_alembic.py` | Updated Sprint 1 empty-versions assertion → Sprint 2 migration structure assertion |

---

*Sprint 2 complete. All validation gates pass. Sprint 1 infrastructure preserved.*
