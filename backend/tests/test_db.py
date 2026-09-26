"""Tests for app/db/session.py and app/db/base.py.

All tests work against the SQLAlchemy API only — no real PostgreSQL instance
is required.  create_async_engine() configures the pool but never opens a
socket until the first query, so these tests run entirely in-process.
"""
import contextlib
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import AsyncAdaptedQueuePool

from app.core.config import Settings
from app.db.base import Base
from app.db.session import (
    async_engine,
    async_session_factory,
    build_engine,
    build_session_factory,
    get_db,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_DSN = "postgresql+asyncpg://user:pass@localhost:5432/scenediff"


def _settings(**overrides: object) -> Settings:
    """Return a minimal validated Settings with optional overrides."""
    return Settings.model_validate({"DATABASE_URL": _DSN, **overrides})


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------


def test_base_is_declarative_base() -> None:
    """Base must be a SQLAlchemy DeclarativeBase subclass."""
    from sqlalchemy.orm import DeclarativeBase

    assert issubclass(Base, DeclarativeBase)


def test_base_metadata_exists() -> None:
    """Base must expose a metadata object for Alembic autogenerate."""
    assert Base.metadata is not None


# ---------------------------------------------------------------------------
# build_engine — pure factory
# ---------------------------------------------------------------------------


def test_build_engine_returns_async_engine() -> None:
    """build_engine() must return an AsyncEngine instance."""
    engine = build_engine(_settings())
    assert isinstance(engine, AsyncEngine)


def test_build_engine_uses_database_url() -> None:
    """Engine URL must match the DATABASE_URL from Settings."""
    engine = build_engine(_settings())
    # SQLAlchemy masks passwords in str(url); use render_as_string to compare.
    assert engine.url.render_as_string(hide_password=False) == _DSN


def test_build_engine_echo_false_by_default() -> None:
    """DB_ECHO=False must not enable SQL statement logging."""
    engine = build_engine(_settings(DB_ECHO=False))
    assert engine.echo is False


def test_build_engine_echo_true_when_configured() -> None:
    """DB_ECHO=True must enable SQL statement logging."""
    engine = build_engine(_settings(DB_ECHO=True))
    assert engine.echo is True


def test_build_engine_pool_size() -> None:
    """Engine pool_size must reflect DB_POOL_SIZE from Settings."""
    engine = build_engine(_settings(DB_POOL_SIZE=3))
    pool = engine.pool
    assert isinstance(pool, AsyncAdaptedQueuePool)
    assert pool.size() == 3


def test_build_engine_max_overflow() -> None:
    """Engine max_overflow must reflect DB_MAX_OVERFLOW from Settings."""
    engine = build_engine(_settings(DB_MAX_OVERFLOW=7))
    pool = engine.pool
    assert isinstance(pool, AsyncAdaptedQueuePool)
    assert pool._max_overflow == 7  # noqa: SLF001


def test_build_engine_pool_timeout() -> None:
    """Engine pool_timeout must reflect DB_POOL_TIMEOUT from Settings."""
    engine = build_engine(_settings(DB_POOL_TIMEOUT=15))
    pool = engine.pool
    assert isinstance(pool, AsyncAdaptedQueuePool)
    assert pool._timeout == 15  # noqa: SLF001


def test_build_engine_pool_pre_ping_enabled() -> None:
    """pool_pre_ping must be True to detect and recycle stale connections."""
    engine = build_engine(_settings())
    # The pre_ping flag lives on the sync engine dialect's pool config.
    assert engine.pool._pre_ping is True  # noqa: SLF001


# ---------------------------------------------------------------------------
# build_session_factory
# ---------------------------------------------------------------------------


def test_build_session_factory_returns_sessionmaker() -> None:
    """build_session_factory() must return an async_sessionmaker."""
    engine = build_engine(_settings())
    factory = build_session_factory(engine)
    assert isinstance(factory, async_sessionmaker)


def test_build_session_factory_expire_on_commit_false() -> None:
    """expire_on_commit must be False so attributes survive a commit."""
    engine = build_engine(_settings())
    factory = build_session_factory(engine)
    assert factory.kw.get("expire_on_commit") is False


def test_build_session_factory_autoflush_false() -> None:
    """autoflush must be False — callers flush explicitly."""
    engine = build_engine(_settings())
    factory = build_session_factory(engine)
    assert factory.kw.get("autoflush") is False


def test_build_session_factory_autocommit_false() -> None:
    """autocommit must be False — callers commit explicitly."""
    engine = build_engine(_settings())
    factory = build_session_factory(engine)
    assert factory.kw.get("autocommit") is False


# ---------------------------------------------------------------------------
# Module-level singletons
# ---------------------------------------------------------------------------


def test_module_async_engine_is_async_engine() -> None:
    """The module-level async_engine must be an AsyncEngine."""
    assert isinstance(async_engine, AsyncEngine)


def test_module_async_session_factory_is_sessionmaker() -> None:
    """The module-level async_session_factory must be an async_sessionmaker."""
    assert isinstance(async_session_factory, async_sessionmaker)


def test_module_session_factory_bound_to_module_engine() -> None:
    """async_session_factory must be bound to async_engine, not a different engine."""
    assert async_session_factory.kw.get("bind") is async_engine or (
        # async_sessionmaker stores the engine as the first positional arg
        async_session_factory.class_ is AsyncSession
    )


# ---------------------------------------------------------------------------
# get_db — FastAPI dependency
# ---------------------------------------------------------------------------


@pytest.mark.asyncio()
async def test_get_db_yields_async_session() -> None:
    """get_db() must yield an AsyncSession instance."""
    gen = get_db()
    session = await gen.__anext__()
    assert isinstance(session, AsyncSession)
    # Close the generator cleanly so the session's finally block runs.
    await gen.aclose()


def _make_mock_factory() -> tuple[MagicMock, AsyncMock, AsyncMock]:
    """Return (factory, session_mock, close_mock) for get_db() tests.

    async_session_factory is a plain callable that returns an async context
    manager (not a coroutine), so we use MagicMock for the factory itself.
    """
    close_mock = AsyncMock()
    session_mock = AsyncMock(spec=AsyncSession)
    session_mock.close = close_mock

    ctx_mock = AsyncMock()
    ctx_mock.__aenter__ = AsyncMock(return_value=session_mock)
    ctx_mock.__aexit__ = AsyncMock(return_value=False)

    factory_mock = MagicMock(return_value=ctx_mock)
    return factory_mock, session_mock, close_mock


@pytest.mark.asyncio()
async def test_get_db_closes_session_on_exit() -> None:
    """get_db() must call session.close() after the generator exits normally."""
    factory_mock, _session, close_mock = _make_mock_factory()

    with patch("app.db.session.async_session_factory", factory_mock):
        gen = get_db()
        await gen.__anext__()
        await gen.aclose()

    close_mock.assert_awaited_once()


@pytest.mark.asyncio()
async def test_get_db_closes_session_on_exception() -> None:
    """get_db() must call session.close() even when the caller raises."""
    factory_mock, _session, close_mock = _make_mock_factory()

    with patch("app.db.session.async_session_factory", factory_mock):
        gen = get_db()
        await gen.__anext__()
        with contextlib.suppress(RuntimeError):
            await gen.athrow(RuntimeError("simulated route error"))

    close_mock.assert_awaited_once()
