"""Alembic migration environment for SceneDiff.

Async migration pattern — uses the AsyncEngine from app.db.session so that
the same connection pool configuration applies to both the application and
migrations.

Key behaviours
--------------
- DATABASE_URL is sourced from pydantic Settings; never hard-coded.
- Base.metadata is imported so that autogenerate can diff ORM models against
  the live schema.
- Both online (run_async_migrations) and offline (run_migrations_offline)
  modes are supported.
- All model modules that define ORM classes must be imported below the
  "Import ORM models" marker so that autogenerate can discover their tables.
"""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

# ---------------------------------------------------------------------------
# Alembic Config object — gives access to alembic.ini values.
# ---------------------------------------------------------------------------
config = context.config

# Bind Python's stdlib logging to the INI file configuration.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ---------------------------------------------------------------------------
# Import ORM models for autogenerate support.
# Add new model modules here as they are created in Sprint 2+.
# ---------------------------------------------------------------------------
from app.db.base import Base  # noqa: E402  (must come after Alembic imports)
from app.models.trace_event import TraceEvent  # noqa: E402, F401

# Sprint 2 models — import so autogenerate picks up the tables.
from app.models.trace_session import TraceSession  # noqa: E402, F401

target_metadata = Base.metadata

# ---------------------------------------------------------------------------
# Read DATABASE_URL from pydantic Settings.
# Deferred to _get_database_url() so that env.py can be imported by tests
# without DATABASE_URL being set in the environment.  The URL is only
# resolved when a migration command actually executes.
# ---------------------------------------------------------------------------
from app.core.config import get_settings  # noqa: E402


def _get_database_url() -> str:
    """Return the validated DATABASE_URL from pydantic Settings.

    Raises:
        AssertionError: if DATABASE_URL is not set (should never happen in
            a properly configured environment).
    """
    settings = get_settings()
    assert settings.DATABASE_URL is not None, (  # noqa: S101
        "DATABASE_URL must be set before running Alembic migrations."
    )
    return settings.DATABASE_URL


# ---------------------------------------------------------------------------
# Offline migrations — emit SQL to stdout without a live DB connection.
# Useful for generating SQL scripts for DBA review.
# ---------------------------------------------------------------------------
def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    Configures the context with a URL (not a live connection), so that
    migrations emit SQL rather than executing against a database.
    """
    context.configure(
        url=_get_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------------------------
# Online migrations — execute against a live database connection.
# ---------------------------------------------------------------------------
def do_run_migrations(connection: Connection) -> None:
    """Run migrations synchronously within an existing connection."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create an async engine and drive migrations inside a sync wrapper.

    AsyncEngine does not support the synchronous connection protocol that
    Alembic's MigrationContext expects.  run_sync() bridges the gap by
    running do_run_migrations() inside a sync connection context.
    """
    connectable = create_async_engine(
        _get_database_url(),
        poolclass=pool.NullPool,  # NullPool: no pooling during migrations
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Entry point for online mode — drives the async event loop."""
    asyncio.run(run_async_migrations())


# ---------------------------------------------------------------------------
# Entry point — Alembic calls this module at migration time.
# ---------------------------------------------------------------------------
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
