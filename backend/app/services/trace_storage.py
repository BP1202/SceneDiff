"""Trace Storage Service.

Coordinates all database operations for trace sessions and events.
Business logic lives here, not in routes.

Public API
----------
create_trace_session()   — insert a new TraceSession row
update_status()          — change session status
store_event()            — insert a sanitized TraceEvent row
list_events()            — paginated query of events for a session
get_session()            — fetch one session by ID
list_sessions()          — paginated query with optional filters
delete_failed_session()  — hard-delete a FAILED session

All functions are async and accept an AsyncSession dependency.
"""

from datetime import UTC, datetime
import logging
from typing import Any
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.trace_event import TraceEvent
from app.models.trace_session import TraceSession, TraceStatus
from app.services.secret_shield import mask_metadata

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Session operations
# ---------------------------------------------------------------------------


async def create_trace_session(
    db: AsyncSession,
    repository_name: str,
    base_commit: str,
    head_commit: str,
    branch: str,
) -> TraceSession:
    """Persist a new TraceSession with PENDING status.

    Args:
        db:               Active async database session.
        repository_name:  Repository identifier (e.g. "org/repo").
        base_commit:      Full or short SHA of the base commit.
        head_commit:      Full or short SHA of the head commit.
        branch:           Branch name for the head commit.

    Returns:
        Persisted TraceSession instance with id and created_at populated.
    """
    session = TraceSession(
        id=uuid.uuid4(),
        repository_name=repository_name,
        base_commit=base_commit,
        head_commit=head_commit,
        branch=branch,
        status=TraceStatus.PENDING,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    logger.info(
        "trace_session.created session_id=%s repository=%s",
        session.id,
        repository_name,
    )
    return session


async def get_session(
    db: AsyncSession,
    session_id: uuid.UUID,
) -> TraceSession | None:
    """Fetch a single TraceSession by primary key.

    Args:
        db:         Active async database session.
        session_id: UUID primary key of the trace session.

    Returns:
        TraceSession if found, None otherwise.
    """
    result = await db.execute(select(TraceSession).where(TraceSession.id == session_id))
    return result.scalar_one_or_none()


async def update_status(
    db: AsyncSession,
    session_id: uuid.UUID,
    status: TraceStatus,
) -> TraceSession | None:
    """Update the status field of a TraceSession.

    Args:
        db:         Active async database session.
        session_id: UUID of the session to update.
        status:     New TraceStatus value.

    Returns:
        Updated TraceSession, or None if not found.
    """
    session = await get_session(db, session_id)
    if session is None:
        logger.warning(
            "trace_session.update_status.not_found session_id=%s", session_id
        )
        return None

    session.status = status
    session.updated_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(session)
    logger.info(
        "trace_session.status_updated session_id=%s status=%s",
        session_id,
        status.value,
    )
    return session


async def list_sessions(
    db: AsyncSession,
    *,
    status: TraceStatus | None = None,
    repository_name: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[TraceSession]:
    """Return a paginated list of trace sessions.

    Args:
        db:               Active async database session.
        status:           Optional filter by TraceStatus.
        repository_name:  Optional filter by repository name.
        limit:            Maximum number of rows to return (default 20).
        offset:           Number of rows to skip for pagination (default 0).

    Returns:
        List of TraceSession instances (may be empty).
    """
    query = select(TraceSession).order_by(TraceSession.created_at.desc())

    if status is not None:
        query = query.where(TraceSession.status == status)
    if repository_name is not None:
        query = query.where(TraceSession.repository_name == repository_name)

    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    return list(result.scalars().all())


async def delete_failed_session(
    db: AsyncSession,
    session_id: uuid.UUID,
) -> bool:
    """Hard-delete a FAILED trace session and its cascaded events.

    Only sessions with FAILED status may be deleted this way to prevent
    accidental data loss for in-progress or completed sessions.

    Args:
        db:         Active async database session.
        session_id: UUID of the failed session.

    Returns:
        True if the session was found and deleted, False if not found or
        the session was not in FAILED status.
    """
    session = await get_session(db, session_id)
    if session is None:
        return False
    if session.status != TraceStatus.FAILED:
        logger.warning(
            "trace_session.delete_refused session_id=%s status=%s",
            session_id,
            session.status.value,
        )
        return False

    await db.delete(session)
    await db.commit()
    logger.info("trace_session.deleted session_id=%s", session_id)
    return True


# ---------------------------------------------------------------------------
# Event operations
# ---------------------------------------------------------------------------


async def store_event(
    db: AsyncSession,
    trace_session_id: uuid.UUID,
    event_type: str,
    file_path: str,
    *,
    function_name: str | None = None,
    line_number: int | None = None,
    behavior_hash: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> TraceEvent:
    """Persist a single TraceEvent after sanitizing its metadata.

    Secret Shield runs before the row is written — raw secrets are never
    stored in the database.

    Args:
        db:                Active async database session.
        trace_session_id:  FK reference to the parent TraceSession.
        event_type:        Category string (e.g. "FUNCTION_MODIFIED").
        file_path:         Repository-relative path of the changed file.
        function_name:     Optional name of the changed function.
        line_number:       Optional line number within the file.
        behavior_hash:     Pre-computed SHA-256 behavior hash (optional).
        metadata:          Arbitrary key-value metadata; will be sanitized.

    Returns:
        Persisted TraceEvent instance.
    """
    safe_metadata = mask_metadata(metadata) if metadata is not None else None

    event = TraceEvent(
        id=uuid.uuid4(),
        trace_session_id=trace_session_id,
        event_type=event_type,
        file_path=file_path,
        function_name=function_name,
        line_number=line_number,
        behavior_hash=behavior_hash,
        metadata_=safe_metadata,
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event


async def list_events(
    db: AsyncSession,
    trace_session_id: uuid.UUID,
    *,
    event_type: str | None = None,
    file_path: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[TraceEvent]:
    """Return a paginated list of events for a trace session.

    Args:
        db:                Active async database session.
        trace_session_id:  Filter to events belonging to this session.
        event_type:        Optional filter by event type string.
        file_path:         Optional filter by file path (exact match).
        limit:             Maximum rows (default 50).
        offset:            Rows to skip (default 0).

    Returns:
        List of TraceEvent instances.
    """
    query = (
        select(TraceEvent)
        .where(TraceEvent.trace_session_id == trace_session_id)
        .order_by(TraceEvent.created_at.asc())
    )

    if event_type is not None:
        query = query.where(TraceEvent.event_type == event_type)
    if file_path is not None:
        query = query.where(TraceEvent.file_path == file_path)

    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    return list(result.scalars().all())
