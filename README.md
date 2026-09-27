# SceneDiff — IBM Bob 2.0 AI Debugging & Repair Workspace

> **Turn Git code changes into behavior changes.**  
> SceneDiff captures live runtime evidence, finds the first meaningful divergence, and lets IBM Bob propose & validate repairs — all in one workspace.

[![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61dafb?logo=react)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-6.0-3178c6?logo=typescript)](https://typescriptlang.org)
[![Vite](https://img.shields.io/badge/Vite-6.4-646cff?logo=vite)](https://vite.dev)
[![Playwright](https://img.shields.io/badge/Playwright-1.48-2ead33?logo=playwright)](https://playwright.dev)

---

## What is SceneDiff?

SceneDiff is an AI-powered developer workflow platform built for **IBM Bob 2.0**.

Given two Git commits (a base and a head), SceneDiff:

1. **Collects** live browser traces for both commits using Playwright
2. **Compares** DOM, network, console, storage, and performance — finding the *first meaningful runtime divergence*
3. **Synthesizes** a root cause report with 94%+ confidence scoring
4. **Proposes** a safe, tested Git patch via IBM Bob's AI Repair Engine
5. **Validates** the repair with Pre-Flight checks and a rollback plan
6. **Exports** the evidence as a GitHub PR, `.patch` file, or JSON audit bundle

Instead of saying *"this file changed"*, SceneDiff says:

> *"After commit B, the Login button disappeared, one API started returning 500, console threw a TypeError, page load increased by 620 ms, and LocalStorage gained a new auth token."*

---

## Architecture

```
Frontend (React + TypeScript)
       │
       ▼
REST API  (FastAPI / Python 3.12)
       │
       ▼
Behavior Engine  ←── IBM Bob AI Repair Engine
       │
       ▼
Secret Shield  (masks API keys, tokens, JWTs before storage)
       │
       ▼
Trace Store  ──► PostgreSQL (SQLAlchemy async + Alembic)
```

| Layer | Technology |
|---|---|
| Frontend | React 19, TypeScript 6, Vite 6, Zustand, TanStack Query |
| Backend | FastAPI 0.115, Python 3.12, SQLAlchemy async, Alembic |
| Trace Engine | Playwright 1.48, asyncpg |
| AI Repair | IBM Watsonx / OpenAI-compatible LLM adapter |
| Secret Shield | Regex + entropy analysis — 100+ secret patterns |
| Database | PostgreSQL 16 |
| Testing | Vitest (frontend), Pytest (backend), 379+ passing tests |

---

## Project Structure

```
SceneDiff/
├── backend/                   # FastAPI application
│   ├── app/
│   │   ├── api/               # REST routers (v1)
│   │   ├── behavior/          # Comparison engine modules
│   │   │   ├── comparators/   # DOM, network, console, storage, perf
│   │   │   ├── severity.py    # CRITICAL → INFO classification
│   │   │   └── timeline.py    # Causal timeline builder
│   │   ├── core/              # Config, logging, exceptions
│   │   ├── db/                # SQLAlchemy engine & session
│   │   ├── middleware/        # CORS, logging, request ID
│   │   ├── models/            # SQLAlchemy ORM models
│   │   ├── repair/            # IBM Bob AI Repair Engine
│   │   ├── root_cause/        # Root cause analysis engine
│   │   ├── runtime/           # Playwright trace collector
│   │   ├── schemas/           # Pydantic request/response schemas
│   │   └── main.py            # FastAPI app factory
│   ├── alembic/               # Database migrations (0001–0004)
│   ├── tests/                 # Pytest test suite (379+ tests)
│   ├── .env.example           # Environment variable template
│   └── pyproject.toml         # Python dependencies + tooling
│
├── frontend/                  # React + TypeScript workspace
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/            # Button, Badge, Card, Modal, Tabs …
│   │   │   └── layouts/       # Sidebar, TopNavbar, WorkspaceShell …
│   │   ├── features/
│   │   │   ├── dashboard/     # DashboardOverview
│   │   │   ├── runtime/       # RuntimeCollector
│   │   │   ├── comparison/    # BehaviorTimeline, DOMDiffViewer,
│   │   │   │                  # NetworkInspector, ConsoleStorageViewer,
│   │   │   │                  # PerformanceDashboard
│   │   │   ├── rootcause/     # RootCauseExplorer, EvidenceGraph
│   │   │   ├── repair/        # RepairStudio
│   │   │   └── reports/       # ExportCenter
│   │   ├── store/             # Zustand stores (6 domain stores)
│   │   ├── services/          # Type-safe API client layer
│   │   ├── theme/             # Design tokens, globals.css
│   │   ├── types/             # Shared TypeScript types
│   │   └── App.tsx            # Root router & view switcher
│   ├── vite.config.ts         # Vite 6 + Vitest + API proxy
│   └── package.json
│
├── docs/                      # Architecture docs, demo assets
├── .bob/                      # IBM Bob prompts & sprint templates
├── .github/                   # CI workflows, issue templates
└── README.md                  # This file
```

---

## Prerequisites

| Tool | Minimum Version |
|---|---|
| Node.js | 20+ |
| Python | 3.12+ |
| PostgreSQL | 15+ |
| Git | 2.40+ |

---

## Quick Start — Full Stack

### 1. Clone the repository

```bash
git clone https://github.com/BP1202/SceneDiff.git
cd SceneDiff
```

### 2. Set up the backend

```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Activate (macOS / Linux)
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Copy environment config
cp .env.example .env
# Edit .env and set DATABASE_URL to your PostgreSQL instance
```

### 3. Configure the database

Edit `backend/.env`:

```env
DATABASE_URL=postgresql+asyncpg://scenediff:scenediff@localhost:5432/scenediff
APP_ENV=development
DOCS_ENABLED=true
SECRET_SHIELD_ENABLED=true
```

Create the PostgreSQL database:

```sql
CREATE DATABASE scenediff;
CREATE USER scenediff WITH PASSWORD 'scenediff';
GRANT ALL PRIVILEGES ON DATABASE scenediff TO scenediff;
```

Run Alembic migrations:

```bash
cd backend
alembic upgrade head
```

### 4. Start the backend API server

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

API is now live at:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Health:** http://localhost:8000/api/v1/health

### 5. Set up the frontend

```bash
cd frontend
npm install
```

### 6. Start the frontend dev server

```bash
cd frontend
npm run dev
```

Frontend is live at: **http://localhost:5173/**

> The Vite dev server automatically proxies all `/api/*` requests to `http://localhost:8000` — no CORS configuration needed.

---

## Running Tests

### Backend (Pytest)

```bash
cd backend
pytest                        # run all tests
pytest -v                     # verbose
pytest --cov=app              # with coverage
pytest -k "test_behavior"     # run specific module
```

### Frontend (Vitest)

```bash
cd frontend
npm test                      # run once
npm run test -- --watch       # watch mode
npm run typecheck             # TypeScript type check
```

---

## Production Build

```bash
cd frontend
npm run build    # outputs to frontend/dist/
```

The production bundle is ~362 KB JS (104 KB gzip).

---

## Key Features

### 🎯 Behavior Comparison Engine
Compares two runtime traces across 5 dimensions:
- **DOM Diff** — structural element changes, attribute mutations
- **Network Inspector** — status codes, response times, payload changes
- **Console & Storage** — error logs, LocalStorage / SessionStorage divergence
- **Performance Vitals** — TTFB, LCP, FCP, TTI with statistical significance
- **Divergence Timeline** — ordered by severity (CRITICAL → INFO)

### 🛡️ Secret Shield
Automatic secret detection and masking before any trace is persisted:
- API keys, OAuth tokens, JWTs, AWS/Azure/GCP/IBM cloud credentials
- SSH keys, cookies, session tokens, GitHub PATs
- 100+ regex patterns + entropy-based detection

### 🤖 IBM Bob AI Repair Engine
- Reads root cause report → generates a targeted Git patch
- Risk scoring (0–100) with CRITICAL / HIGH / MEDIUM / LOW classification
- 4-step repair plan with Pre-Flight validation
- Auto-generated rollback plan
- GitHub PR draft export

### 📊 Root Cause Analysis
- Causal timeline with first-divergence detection
- Confidence scoring (0–100%)
- File + function-level culprit identification
- Interactive evidence graph

---

## Environment Variables Reference

| Variable | Default | Description |
|---|---|---|
| `APP_ENV` | `development` | `development` / `staging` / `production` |
| `LOG_LEVEL` | `INFO` | Stdlib log level |
| `DATABASE_URL` | — | PostgreSQL async DSN (required) |
| `ALLOWED_ORIGINS` | `http://localhost:5173` | Comma-separated CORS origins |
| `DOCS_ENABLED` | `true` | Expose `/docs` and `/redoc` |
| `SECRET_SHIELD_ENABLED` | `true` | Enable secret masking |
| `SECRET_SHIELD_BLOCK_ON_DETECT` | `true` | Reject trace if secret found |
| `DB_POOL_SIZE` | `5` | SQLAlchemy connection pool size |

---

## Sprint Roadmap

| Sprint | Deliverable | Status |
|---|---|---|
| Sprint 0 | Repository scaffold, CI, Bob setup | ✅ Complete |
| Sprint 1 | Backend foundation (FastAPI, DB, Secret Shield, Playwright) | ✅ Complete |
| Sprint 2 | Behavior comparators (DOM, Network, Console, Storage) | ✅ Complete |
| Sprint 3 | Runtime Trace Collector & Playwright Engine | ✅ Complete |
| Sprint 4 | Behavior Comparison Engine + Severity Engine | ✅ Complete |
| Sprint 5 | Root Cause Analysis Engine (causal timeline, confidence) | ✅ Complete |
| Sprint 6 | IBM Bob AI Repair Engine (patch gen, risk, rollback) | ✅ Complete |
| Sprint 7 | Frontend AI Workspace (React + TypeScript dashboard) | ✅ Complete |
| Sprint 8 | Deployment, demo assets, IBM submission | 🔄 In Progress |

---

## API Endpoints

### Health
```
GET /api/v1/health
```

### Runtime Traces
```
POST /api/v1/runtime/execute          # run Playwright trace for a commit
GET  /api/v1/runtime/sessions         # list trace sessions
GET  /api/v1/runtime/sessions/{id}    # get session details
```

### Behavior Comparison
```
POST /api/v1/comparisons              # compare two trace sessions
GET  /api/v1/comparisons/{id}         # get comparison result
GET  /api/v1/comparisons/{id}/report  # get comparison report
GET  /api/v1/comparisons/{id}/events  # get comparison events
```

### Root Cause Analysis
```
POST /api/v1/root-cause               # analyze comparison → root cause
GET  /api/v1/root-cause/{id}          # get root cause report
```

### AI Repair Engine
```
POST /api/v1/repairs                  # generate repair for root cause
GET  /api/v1/repairs/{id}             # get repair proposal
POST /api/v1/repairs/{id}/validate    # run Pre-Flight validation
GET  /api/v1/repairs/{id}/patch       # download .patch file
```

---

## Security

- Secrets are **never stored** in the database — masked before persistence
- CORS is restricted to explicit allowed origins
- No authentication tokens in logs or traces
- All Alembic migrations are version-controlled and reversible

---

## Contributing

Follow the branch workflow:

```
main ← dev ← feat/* ← PR ← dev ← main
```

Never commit directly to `main` or `dev`.

Every feature must include: unit tests · integration tests · regression tests.

---

## License

MIT — © 2026 SceneDiff / IBM Bob 2.0 Hackathon Project