"""Async SQLAlchemy engine and session factory.

Exports:
    async_engine          — shared engine instance
    async_session_factory — sessionmaker bound to the engine
    get_db                — FastAPI dependency that yields an AsyncSession
"""
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings

_settings = get_settings()

# DATABASE_URL is guaranteed non-None by the Settings model validator.
assert _settings.DATABASE_URL is not None  # noqa: S101

async_engine = create_async_engine(
    _settings.DATABASE_URL,
    echo=_settings.DB_ECHO,
    pool_pre_ping=True,
    pool_size=_settings.DB_POOL_SIZE,
    max_overflow=_settings.DB_MAX_OVERFLOW,
    pool_timeout=_settings.DB_POOL_TIMEOUT,
)

async_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    async_engine,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an AsyncSession; always close on exit."""
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
