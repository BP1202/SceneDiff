# Sprint 4 — Behavior Comparator & Regression Intelligence

**Status:** ✅ Complete  
**Depends on:** Sprint 2 (Behavior Trace Engine) ✅, Sprint 3 (Runtime Trace Collector) ✅  
**Branch:** `feat/behavior-comparator-engine`

> **Mission:** Compare two normalized runtime trace artifacts (Base Commit vs Head Commit), classify regressions with a deterministic severity engine, pinpoint the first meaningful runtime divergence, and generate the canonical Behavior Diff Report for IBM Bob's repair engine.

---

## Architecture

```
Base Runtime Artifact (Sprint 3)       Head Runtime Artifact (Sprint 3)
           │                                      │
           └──────────────────┬───────────────────┘
                              ▼
                  Behavior Comparator Engine
                              │
     ┌────────────────────────┼────────────────────────┐
     ▼                        ▼                        ▼
DOM Diff Engine      Network Diff Engine      Console Diff Engine
(buttons/forms/DOM)    (5xx/4xx/latency)      (exceptions/errors)
     │                        │                        │
     ▼                        ▼                        ▼
Storage Diff Engine  Performance Diff Engine  Secret Shield
(localStorage/keys)  (load/LCP/FCP/memory)    (sanitization)
     │                        │                        │
     └────────────────────────┼────────────────────────┘
                              ▼
                   Severity & Verdict Engine
                   (CRITICAL / HIGH / MEDIUM / LOW / INFO)
                              │
                              ▼
                  Divergence Timeline Engine
                  (Identifies First Meaningful Divergence)
                              │
                              ▼
                   Behavior Diff Report
                   (Consumed by IBM Bob & Persisted to DB)
```

---

## Folder Structure

```
backend/app/behavior/
├── __init__.py
├── comparator.py         # Main orchestrator & report generator
├── dom_diff.py           # Structural DOM snapshot comparison
├── network_diff.py       # HTTP status, latency, and endpoint diff
├── console_diff.py       # JavaScript console errors & exceptions diff
├── storage_diff.py       # LocalStorage, SessionStorage & Cookie diff
├── performance_diff.py   # Page load, FCP, LCP, memory regressions
├── severity.py           # Deterministic severity classification & verdict
└── timeline.py           # Ordered causal timeline & root-cause identification

backend/app/models/
└── behavior_comparison.py # BehaviorComparison & ComparisonEvent ORM models

backend/app/schemas/
└── comparison.py         # Request, response & Behavior Diff Report schemas

backend/app/services/
└── comparison_service.py # Async DB persistence and comparison coordinator

backend/app/api/v1/endpoints/
└── comparisons.py        # REST endpoints: POST /comparisons, GET /report, etc.

backend/alembic/versions/
└── 20260927_0002_sprint4_behavior_comparisons.py # Migration 0002

backend/tests/
├── test_behavior_severity.py
├── test_behavior_dom_diff.py
├── test_behavior_network_diff.py
├── test_behavior_console_diff.py
├── test_behavior_storage_diff.py
├── test_behavior_performance_diff.py
├── test_behavior_timeline.py
├── test_behavior_comparator.py
├── test_comparison_service.py
├── test_comparisons_api.py
└── test_alembic_sprint4.py
```

---

## Comparator Rules

1. **Normalized artifacts only:** Always compare structured JSON evidence, never screenshot pixels.
2. **Structural DOM diff:** Detects button removal, form disappearance, input removals, element count loss (>50%).
3. **Network diff:** Detects HTTP 5xx, 4xx, network failures, latency spikes (>50% & >250ms), missing endpoints.
4. **Console diff:** Detects unhandled exceptions, error spikes, and console warnings.
5. **Storage diff:** Detects auth token and key changes while preserving Secret Shield redactions (`[REDACTED]`).
6. **Performance diff:** Detects regressions in Page Load (>25% & >200ms), LCP (>500ms), FCP (>300ms), and JS heap memory growth.
7. **Severity classification:**
   - **CRITICAL:** HTTP 500 introduced, route completely missing, all forms removed, fatal network drop.
   - **HIGH:** Button removed, form removed, new runtime exception, HTTP 404 introduced, auth token removed.
   - **MEDIUM:** Latency regression, page load regression, LCP/FCP regression, console warnings, cookie removed.
   - **LOW:** Button/form added, title changed, non-auth key added.
   - **INFO:** New route visited, clean additions.

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/comparisons` | Run behavior comparison and persist report |
| `GET` | `/api/v1/comparisons/{id}` | Retrieve comparison metadata and summary |
| `GET` | `/api/v1/comparisons/{id}/report` | Retrieve canonical Behavior Diff Report for IBM Bob |
| `GET` | `/api/v1/comparisons/{id}/events` | Retrieve ordered divergence timeline events (filterable) |
