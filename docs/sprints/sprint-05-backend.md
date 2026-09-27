# Sprint 5 — AI Root Cause Engine (IBM Bob Intelligence Layer)

**Status:** ✅ Complete  
**Depends on:** Sprint 2 (Behavior Trace Engine) ✅, Sprint 3 (Runtime Trace Collector) ✅, Sprint 4 (Behavior Comparator) ✅  
**Branch:** `feat/root-cause-analysis-engine`

> **Mission:** Transform SceneDiff from an observability collector into an AI-powered debugging platform. Given two commits, automatically correlate Git diffs with runtime behavioral regressions, construct a causal dependency graph, pinpoint primary and secondary root cause candidates, compute deterministic confidence scores, and formulate actionable repair plans for IBM Bob 2.0.

---

## Architecture

```
Sprint 4 Behavior Diff Report + Git Diff Evidence + Runtime Trace Timeline
                               │
                               ▼
                   Evidence Correlation Engine
           (Group by route, sort by causality & timestamp)
                               │
                               ▼
                     Causal Graph Builder
      (Network 100 → Console 90 → DOM 70 → Storage 60 → Perf 50)
                               │
                               ▼
                Root Cause Candidate Generator
     (Correlate with Git diff changed functions & route failures)
                               │
                               ▼
                   Confidence Scoring Engine
   (Formula: Severity + Timeline + Evidence Count + Git Hash Match)
                               │
                               ▼
                 Repair Recommendation Engine
          (Actionable inspection targets & suggestions)
                               │
                               ▼
               LLM Explanation & Report Generator
   (Deterministic structured Markdown & JSON evidence report for Bob)
                               │
                               ▼
           Database Persistence & REST API Endpoints
        (POST /api/v1/root-causes, GET by ID, report, evidence)
```

---

## Folder Structure

```
backend/app/
├── root_cause/
│   ├── __init__.py           # Public exports
│   ├── evidence.py           # CorrelatedEvidenceItem & RouteEvidenceGroup
│   ├── graph.py              # Directed CausalGraph & edge builder
│   ├── correlator.py         # Evidence correlation & route grouping
│   ├── candidate.py          # RootCauseCandidate generator (primary & secondary)
│   ├── confidence.py         # Deterministic confidence scoring (0-100)
│   ├── repair.py             # Repair recommendation engine (IBM Bob copilot)
│   ├── explainer.py          # LLM prompt builder & structured explanation
│   └── report.py             # Canonical RootCauseAnalysisReport orchestrator
│
├── services/
│   └── root_cause_service.py # Database persistence & async retrieval
│
├── models/
│   ├── root_cause_report.py   # SQLAlchemy model for root_cause_reports
│   └── root_cause_evidence.py # SQLAlchemy model for root_cause_evidence
│
├── schemas/
│   └── root_causes.py         # Pydantic schemas (AnalyzeRequest, responses)
│
└── api/v1/endpoints/
    └── root_causes.py         # REST API (/api/v1/root-causes)
```

---

## Tasks & Deliverables

| Task | Module | Main Deliverable |
|---|---|---|
| **Task 35** | `root_cause/evidence.py`, `correlator.py` | Evidence correlation and route grouping. |
| **Task 36** | `root_cause/graph.py` | Causal dependency graph with weighted hierarchy. |
| **Task 37** | `root_cause/candidate.py` | Primary and secondary root cause candidate extraction. |
| **Task 38** | `root_cause/confidence.py` | Deterministic 0–100 scoring and band classification. |
| **Task 39** | `root_cause/repair.py` | Diagnostic checklists and actionable repair suggestions. |
| **Task 40** | `root_cause/explainer.py`, `report.py` | Zero-hallucination prompt generator and full report. |
| **Task 41** | `models/root_cause_*.py` | SQLAlchemy ORM models with cascade foreign keys. |
| **Task 42** | `alembic/versions/0003` | Schema migration for reports and evidence tables. |
| **Task 43** | `api/v1/endpoints/root_causes.py` | REST API endpoints for analysis, reports, and evidence. |
| **Task 44** | `tests/test_root_cause_*.py` | Comprehensive test suite for all AI reasoning modules. |
| **Task 45** | `scripts/check.ps1` | Ruff, MyPy, Pytest, Alembic, Docker verification. |
| **Task 46** | `docs/sprints/sprint-05-backend.md` | Complete architectural documentation. |

---

## API Contract

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/root-causes` | Run AI root cause analysis from comparison ID |
| `GET` | `/api/v1/root-causes/{id}` | Summary, primary candidate, and confidence |
| `GET` | `/api/v1/root-causes/{id}/report` | Full canonical diagnosis report for IBM Bob |
| `GET` | `/api/v1/root-causes/{id}/evidence` | Filterable ordered evidence chain |
| `GET` | `/api/v1/root-causes` | Paginated list of previous root cause analyses |

---

## Security & Privacy Rules

- **Zero Secret Exposure**: All strings undergo Secret Shield masking (`[REDACTED]`).
- **No Hallucination**: AI explanations are generated strictly from structured runtime and Git evidence.
- **Pluggable LLM Layer**: Prompts are deterministic, enabling plug-and-play integration with IBM Granite, Watsonx, or local Ollama.
