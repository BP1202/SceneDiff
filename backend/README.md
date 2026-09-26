# SceneDiff Backend

FastAPI application for the SceneDiff platform.

---

## Prerequisites

- Python 3.11+
- Docker and Docker Compose

---

## Local Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env             # fill in real values
```

---

## Run Locally

```bash
uvicorn app.main:app --reload --port 8000
```

---

## Lint and Type Check

```bash
ruff check app/ tests/
mypy app/
```

---

## Tests

```bash
pytest tests/
```

---

## Database Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Generate a new migration after adding/changing models
alembic revision --autogenerate -m "describe the change"
```

---

## Docker

```bash
# From the repository root
docker compose up --build
```
