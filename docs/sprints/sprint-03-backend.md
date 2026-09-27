# Sprint 3 — Runtime Trace Collector & Playwright Engine

**Status:** 🔲 Planned  
**Depends on:** Sprint 2 (Behavior Trace Engine) ✅  
**Branch:** `feat/sprint-3-runtime-trace-collector`

> **Mission:** Execute two versions of an application (Base Commit vs Head Commit), collect runtime evidence from both executions, normalize it into trace artifacts, and feed it into the Sprint 2 Behavior Engine.

---

## Why This Sprint Is the Demo Sprint

After Sprint 3, SceneDiff can show judges:

1. User selects Base Commit and Head Commit
2. SceneDiff launches two isolated Chromium browsers automatically
3. Same user journey executes in both versions
4. DOM, network, console, storage, screenshots, and performance traces are collected
5. Runtime artifacts flow into Sprint 2's Behavior Hash + Secret Shield pipeline

**Code changed → runtime behavior changed.** This is SceneDiff's core value proposition, made visible.

---

## Architecture

```
POST /api/v1/runtime/collect
        │
        ▼
  Playwright Runtime Collector
        │
        ├── DOM Snapshot Collector
        ├── Console Event Collector
        ├── Network Request Collector
        ├── Storage Collector (Cookie / LocalStorage / SessionStorage)
        ├── Screenshot Collector
        └── Performance Metrics Collector
        │
        ▼
  Runtime Trace Normalizer
  (deterministic JSON artifact)
        │
        ▼
  Sprint 2 Behavior Engine
  (Secret Shield → Behavior Hash → Trace Storage)
```

Each collector has one responsibility. Normalizer unifies all outputs.

---

## Folder Structure

```
backend/app/runtime/
├── __init__.py
├── browser.py          # Playwright launcher + context manager
├── collector.py        # Orchestration pipeline
├── dom.py              # DOM snapshot collection
├── console.py          # Console event capture
├── network.py          # Network request/response capture
├── storage.py          # Cookie / LocalStorage / SessionStorage
├── screenshots.py      # Visual artifact collection
├── performance.py      # Core Web Vitals + timing metrics
├── normalizer.py       # Unified artifact format
└── artifacts.py        # Artifact storage + retrieval

backend/app/api/v1/endpoints/
└── runtime.py          # Sprint 3 API endpoints

backend/tests/
├── test_runtime_browser.py
├── test_runtime_dom.py
├── test_runtime_console.py
├── test_runtime_network.py
├── test_runtime_storage.py
├── test_runtime_normalizer.py
└── test_runtime_api.py
```

---

## Task Breakdown

### Task 23 — Playwright Collector Foundation

Install and configure Playwright as the runtime execution engine.

**Browser Configuration:**

| Setting     | Value    |
|-------------|----------|
| Browser     | Chromium |
| Mode        | Headless |
| Viewport    | 1280×720 |
| Tracing     | Enabled  |
| Downloads   | Disabled |
| Permissions | Minimal  |

**Deliverables:**
- `browser.py` — Playwright Chromium launcher, context manager, safe shutdown
- `pyproject.toml` update — add `playwright>=1.44.0` to dependencies
- `playwright install chromium` in CI pipeline

---

### Task 24 — Browser Session Manager

Manage isolated browser contexts for Base Commit and Head Commit.

- No cookie sharing between sessions
- No cache reuse between sessions
- Separate storage per context
- Clean teardown after execution
- **Security benefit:** prevents runtime contamination between commits

---

### Task 25 — DOM Snapshot Collector (`dom.py`)

Capture DOM state throughout user flows.

**Captured artifacts:**

| Artifact        | Purpose               |
|-----------------|-----------------------|
| HTML Snapshot   | Full DOM tree         |
| Element Tree    | Structure comparison  |
| Attributes      | class, id, aria, etc. |
| Text Content    | UI content changes    |
| Visibility State| Hidden vs visible     |

**Example artifact:**
```json
{
  "type": "dom_snapshot",
  "route": "/dashboard",
  "elements": 248,
  "buttons": 14,
  "forms": 2,
  "hidden_elements": 8
}
```

> DOM comparison, not screenshot comparison. Deterministic and diff-friendly.

---

### Task 26 — Console Event Collector (`console.py`)

Capture JavaScript runtime behavior.

| Event                | Captured |
|----------------------|----------|
| `console.log`        | ✅        |
| `console.warn`       | ✅        |
| `console.error`      | ✅        |
| Unhandled Exceptions | ✅        |
| Promise Rejections   | ✅        |

**Example:**
```json
{
  "event_type": "console_error",
  "message": "Cannot read property 'user' of undefined",
  "source": "dashboard.js",
  "line": 82
}
```

---

### Task 27 — Network Request Collector (`network.py`)

Capture all HTTP traffic during execution.

| Field       | Description               |
|-------------|---------------------------|
| Method      | GET / POST / PUT / DELETE |
| URL         | Normalized endpoint       |
| Status Code | 200 / 404 / 500           |
| Latency     | Milliseconds              |
| Headers     | Sanitized by Secret Shield |

**Security rule:** Secret Shield sanitizes Authorization, Cookies, API Keys, and Tokens before persistence.

---

### Task 28 — Storage Collector (`storage.py`)

Observe browser storage changes.

| Collector      | Purpose                         |
|----------------|---------------------------------|
| LocalStorage   | App state                       |
| SessionStorage | Temporary runtime state         |
| Cookies        | Authentication/session changes  |

**Example:**
```json
{
  "local_storage": { "theme": "dark", "language": "en" },
  "cookies": { "session": "[REDACTED]" }
}
```

---

### Task 29 — Screenshot Collector (`screenshots.py`)

Collect visual evidence (not used for comparison logic — DOM traces are used for comparison).

| Type               | Purpose                 |
|--------------------|-------------------------|
| Full Page          | Entire UI evidence      |
| Viewport           | Current visible screen  |
| Element Screenshot | Specific component      |

**Storage layout:**
```
runtime_artifacts/
  screenshots/
    base/
    head/
```

---

### Task 30 — Performance Metrics Collector (`performance.py`)

Measure runtime performance differences between commits.

| Metric                   | Example |
|--------------------------|---------|
| Page Load Time           | 1.2s    |
| First Contentful Paint   | 620ms   |
| Largest Contentful Paint | 1.5s    |
| DOM Ready                | 340ms   |
| JS Execution Time        | 190ms   |

```json
{
  "performance": {
    "load_time_ms": 1180,
    "dom_ready_ms": 341,
    "lcp_ms": 1422
  }
}
```

---

### Task 31 — Runtime Trace Normalizer (`normalizer.py`)

Normalize all collector outputs into a single deterministic artifact format.

**Unified artifact:**
```json
{
  "trace_id": "uuid",
  "commit": "9bc47de",
  "route": "/dashboard",
  "events": [],
  "network": [],
  "console": [],
  "dom": {},
  "storage": {},
  "performance": {},
  "screenshots": []
}
```

Behavior Engine consumes one format regardless of which collector produced the data.

---

### Task 32 — Runtime Execution Pipeline (`collector.py`)

Full pipeline:

```
Checkout Base Commit
        ↓
Start Application
        ↓
Run Playwright Flow (user journey)
        ↓
Collect Runtime Artifacts
        ↓
Checkout Head Commit
        ↓
Repeat Collection
        ↓
Normalize Both Traces
        ↓
Send to Behavior Engine
```

**Example user journey:**
```
Open Login Page → Login → Dashboard → Profile → Logout
```

---

### Task 33 — Runtime Collector API (`runtime.py`)

| Endpoint                           | Method | Purpose                      |
|------------------------------------|--------|------------------------------|
| `/api/v1/runtime/collect`          | POST   | Start Playwright collection  |
| `/api/v1/runtime/{id}`             | GET    | Collection status            |
| `/api/v1/runtime/{id}/artifacts`   | GET    | Normalized artifacts         |

**Status response:**
```json
{
  "status": "COLLECTING",
  "progress": 68,
  "current_step": "network_collection"
}
```

---

### Task 34 — Tests, Validation & Documentation

**Test coverage:**

| Module             | Tests                       |
|--------------------|-----------------------------|
| Browser Manager    | Launch / Close / Cleanup    |
| DOM Collector      | Snapshot integrity          |
| Console Collector  | Error capture               |
| Network Collector  | Request interception        |
| Storage Collector  | Cookie masking              |
| Normalizer         | Deterministic JSON output   |
| Runtime API        | Integration tests           |

**Validation gates:**
```
ruff check .
ruff format --check .
mypy app/
pytest -v
playwright install chromium
docker compose up
```

---

## Security Rules (Sprint 3)

| Data Type          | Rule                                  |
|--------------------|---------------------------------------|
| Network Headers    | Secret Shield before persistence      |
| Cookie Values      | Always `[REDACTED]` in artifacts      |
| localStorage       | Secret Shield scan before write       |
| Console Messages   | Secret pattern detection              |
| Screenshots        | No PII extraction — visual only       |

All runtime artifacts pass through Secret Shield before entering the Behavior Engine.

---

## Deliverables Summary

| Module                      | Deliverable                                    |
|-----------------------------|------------------------------------------------|
| Task 23 — Playwright Setup  | Browser launcher, context manager, CI install  |
| Task 24 — Session Manager   | Isolated base/head browser contexts            |
| Task 25 — DOM Collector     | Snapshot + element tree artifacts              |
| Task 26 — Console Collector | Error, warn, log capture                       |
| Task 27 — Network Collector | Request/response + latency (sanitized)         |
| Task 28 — Storage Collector | LocalStorage, SessionStorage, Cookie capture   |
| Task 29 — Screenshot        | Visual evidence artifacts                      |
| Task 30 — Performance       | Core Web Vitals + timing                       |
| Task 31 — Normalizer        | Unified deterministic JSON artifact format     |
| Task 32 — Pipeline          | Full base→head execution orchestration         |
| Task 33 — API               | 3 new runtime endpoints                        |
| Task 34 — Tests + Docs      | Full test suite + sprint documentation         |

---

*Sprint 3 is the demo sprint. After this, SceneDiff shows runtime behavior changing between commits — visually, deterministically, and securely.*
