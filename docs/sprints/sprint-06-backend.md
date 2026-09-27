# Sprint 6 — IBM Bob AI Repair Engine (Backend)

**Status:** ✅ Complete  
**Depends on:** Sprint 5 (AI Root Cause Engine) ✅  
**Branch:** `feat/repair-engine`  
**Test Suite:** 502 Passing Tests (88 Sprint 6 Tests)  

> **Mission:** Transform SceneDiff from diagnosing regressions to autonomously formulating and validating safe code fixes. Convert Sprint 5 root cause reports into Git-compatible patches (`.patch`), explain why the fix works, compute operational risk tiers (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`), evaluate independent repair confidence, synthesize deterministic rollback procedures, and assemble artifacts ready for GitHub Pull Requests.

---

## 1. Architecture

```
Sprint 5 Root Cause Report (Culprit file, function, evidence chain, checklist)
                                   │
                                   ▼
                       [Repair Planning Engine]
           (Synthesize root cause into structured repair actions)
                                   │
                                   ▼
                      [Code Context Retriever]
         (Extract target file source, function body, and diff context)
                                   │
                                   ▼
                       [Patch Generator Engine]
          (Produces unified Git diff patch using provider interface)
                                   │
                                   ▼
                         [Patch Validator]
          (Syntax validation, hunk structure checks, Secret Shield)
                                   │
                                   ▼
                      [Risk Assessment Engine]
           (LOW / MEDIUM / HIGH / CRITICAL based on sensitivity & lines)
                                   │
                                   ▼
                     [Rollback Recommendation Engine]
            (Generates safe git revert instructions & backout risks)
                                   │
                                   ▼
                   [Repair Report & Exporter Engine]
            (Outputs unified .patch, JSON metadata, and Markdown)
                                   │
                                   ▼
               [Database Persistence & REST API Endpoints]
        (POST /api/v1/repairs, GET by ID, /patch, /report, and list)
```

---

## 2. Folder Structure

```
backend/app/
├── repair/
│   ├── __init__.py           # Public exports
│   ├── planner.py            # Repair Planning Engine (Task 47)
│   ├── context.py            # Code Context Retriever (Task 48)
│   ├── patch_generator.py    # Patch Generator Engine (Task 49)
│   ├── validator.py          # Patch Validator & Safety Scope (Task 50)
│   ├── risk.py               # Risk Assessment & Repair Confidence (Task 51)
│   ├── rollback.py           # Rollback Generator Engine (Task 52)
│   ├── exporter.py           # Patch Exporter (.patch, JSON, MD) (Task 54)
│   └── report.py             # Repair Report Builder & PR Summary (Task 53)
│
├── models/
│   ├── repair_report.py      # SQLAlchemy RepairReport model (Task 55)
│   ├── repair_patch.py       # SQLAlchemy RepairPatch model (Task 55)
│   └── __init__.py           # Re-exports
│
├── schemas/
│   └── repairs.py            # Pydantic schemas (Task 57)
│
├── services/
│   └── repair_service.py     # Orchestration service (Task 57)
│
└── api/v1/endpoints/
    └── repairs.py            # REST API endpoints (Task 57)

backend/alembic/versions/
└── 20260927_0004_sprint6_repair_engine.py # Migration 0004 (Task 56)

backend/tests/
├── test_repair_planner.py     # 10 tests
├── test_repair_context.py     # 8 tests
├── test_patch_generator.py    # 9 tests
├── test_patch_validator.py    # 14 tests
├── test_repair_risk.py        # 10 tests
├── test_repair_rollback.py    # 7 tests
├── test_repair_exporter.py    # 5 tests
├── test_repair_service.py     # 7 tests
├── test_repairs_api.py        # 11 tests
└── test_alembic_sprint6.py    # 7 tests
```

---

## 3. Three Production Improvements

### Improvement 1 — Patch Safety Rules (`validate_patch_scope()`)
- **No `.env` file modifications:** Blocks any edit to `.env*` files to guarantee zero environment secret exposure.
- **No unprompted dependency edits:** Rejects changes to `requirements.txt`, `pyproject.toml`, or `package.json` unless the root cause explicitly identifies a dependency divergence.
- **No migrations inside patches:** Blocks any schema generation inside automated patches.
- **Strict culprit file confinement:** Ensures patches touch only files identified by Sprint 5.
- **Extension whitelisting:** Rejects binary or executable file formats.

### Improvement 2 — Independent Repair Confidence
Separates root cause diagnostic confidence from repair confidence. A root cause may be 95% certain while the proposed repair strategy may require human verification. Repair confidence starts from the diagnostic confidence and factors in:
- Multi-layer validation (+5)
- Python AST syntax parse verification (+5)
- Code churn precision (bonus for <=15 lines changed)
- Risk level temperance (-5 for HIGH, -25 for CRITICAL)

### Improvement 3 — PR Summary Generator
Generates clean, GitHub-ready Markdown for developer PRs with:
- Root Cause
- Proposed Fix
- Risk Assessment
- Multi-layer Validation status (AST, Secret Shield, diff syntax)
- Rollback commands (`git apply -R`, `git revert`)

---

## 4. REST API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/repairs` | Trigger AI repair planning and patch synthesis |
| `GET` | `/api/v1/repairs/{id}` | High-level status, risk tier, and repair confidence |
| `GET` | `/api/v1/repairs/{id}/report` | Full technical report (JSON, Markdown, PR summary) |
| `GET` | `/api/v1/repairs/{id}/patch` | Download raw `.patch` or view structured JSON |
| `GET` | `/api/v1/repairs` | Paginated previous repair analyses |

---

## 5. Security & Verification Matrix

- **Zero Secret Persistence:** Secret Shield scans all generated patch hunks and metadata before database insertion.
- **Read-Only Context:** Code Context Retriever blocks directory traversal (`../`) and enforces base directory constraints.
- **Non-Destructive Repairs:** Patches are generated and exported as unified diffs; never applied directly to working trees.
- **Database Safety:** Complete foreign key cascade deletes and PostgreSQL JSONB persistence.

---

## 6. Verification & Quality Gates

```
ruff check .           -> All checks passed (0 errors)
ruff format --check .  -> 152 files already formatted
mypy app               -> Success: no issues found in 84 source files
pytest                 -> 502 passed in 4.17s
alembic history        -> <base> -> 0001 -> 0002 -> 0003 -> 0004 (head)
docker compose config  -> Valid
```
