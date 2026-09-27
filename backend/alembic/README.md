# SceneDiff — Alembic Migrations

This directory contains database schema migrations for SceneDiff, managed by
[Alembic](https://alembic.sqlalchemy.org/).

---

## Prerequisites

- PostgreSQL running and reachable at the DSN in `backend/.env`
- `DATABASE_URL` set to a `postgresql+asyncpg://` DSN

---

## Common Commands

Run all commands from the `backend/` directory.

### Apply all pending migrations

```bash
alembic upgrade head
```

### Roll back the most recent migration

```bash
alembic downgrade -1
```

### Roll back to a specific revision

```bash
alembic downgrade <revision_id>
```

### Show current revision

```bash
alembic current
```

### Show migration history

```bash
alembic history --verbose
```

### Generate a new migration (after adding/changing ORM models)

```bash
alembic revision --autogenerate -m "describe the change"
```

Review the generated file in `alembic/versions/` before applying it.

---

## Async Driver Note

SceneDiff uses `asyncpg` as the PostgreSQL driver.  Alembic `env.py` creates
a dedicated `NullPool` engine for migrations so that the async event loop is
not shared with the application pool.

---

## Naming Convention

Migration files follow the pattern:

```
YYYYMMDD_<revision_id>_<slug>.py
```

Example: `20240101_a1b2c3d4e5f6_create_sessions_table.py`

---

## Security

- `DATABASE_URL` is read from pydantic `Settings` at runtime.
- No credentials are stored in `alembic.ini` or committed to git.
- Never run migrations with a production DSN on a developer machine.
