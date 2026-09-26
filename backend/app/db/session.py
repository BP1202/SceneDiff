"""Async SQLAlchemy engine and session factory.

Public API
----------
async_engine          — AsyncEngine configured from Settings
async_session_factory — async_sessionmaker[AsyncSession] bound to the engine
get_db()              — FastAPI dependency that yields a managed AsyncSession

Design notes
------------
- build_engine() is a pure factory: given a Settings object it returns a
  configured AsyncEngine.  It is importable and testable without side effects.
- The module-level async_engine and async_session_factory are built once from
  get_settings() at import time.  Because conftest.py sets DATABASE_URL before
  any app module is collected, this is safe for the test suite.
- create_async_engine() configures the connection pool but does NOT open any
  real connections until the first query is executed.  Importing this module
  in tests does not require a running PostgreSQL server.
"""
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import Settings, get_settings


def build_engine(settings: Settings) -> AsyncEngine:
    """Return a configured AsyncEngine for the given Settings.

    Pure factory — no module-level state is accessed or modified.
    Suitable for direct use in tests.

    Args:
        settings: A fully validated Settings instance.

    Returns:
        AsyncEngine ready for use with async_sessionmaker.
    """
    # DATABASE_URL is guaranteed non-None by Settings._validate_required_fields.
    assert settings.DATABASE_URL is not None  # noqa: S101

    return create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DB_ECHO,
        # pool_pre_ping issues a lightweight "SELECT 1" before each checkout,
        # ensuring stale connections are recycled rather than surfaced as errors.
        pool_pre_ping=True,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_timeout=settings.DB_POOL_TIMEOUT,
    )


def build_session_factory(
    engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    """Return an async_sessionmaker bound to the given engine.

    Args:
        engine: An AsyncEngine returned by build_engine().

    Returns:
        async_sessionmaker[AsyncSession] with expire_on_commit=False so that
        ORM attributes remain accessible after a commit without re-querying.
    """
    return async_sessionmaker(
        engine,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )


# ---------------------------------------------------------------------------
# Module-level singletons — built once from the application settings.
# Tests that need different pool settings should call build_engine() directly.
# ---------------------------------------------------------------------------
async_engine: AsyncEngine = build_engine(get_settings())
async_session_factory: async_sessionmaker[AsyncSession] = build_session_factory(
    async_engine
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — yield a managed AsyncSession.

    Opens a session from the factory, yields it to the route handler, then
    closes it in the finally block regardless of whether an exception occurred.
    Callers are responsible for committing or rolling back within their scope.

    Yields:
        AsyncSession: A live database session.
    """
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
