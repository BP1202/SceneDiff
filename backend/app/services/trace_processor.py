"""Trace Processor — background pipeline for diff analysis.

Pipeline stages:
    1. Mark session COLLECTING
    2. Parse the unified diff into structured hunks
    3. Generate behavior hashes for each changed function
    4. Store trace events (metadata sanitized by Secret Shield)
    5. Mark session COMPLETED
    On any error: mark session FAILED and log structured details.

This module coordinates services; it contains no direct DB SQL.

Public API
----------
process_trace(db, session_id, unified_diff)  — run full pipeline
"""

import logging
from typing import Any
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.trace_session import TraceStatus
from app.services.behavior_hash import generate_behavior_hash
from app.services.diff_parser import ParsedDiff, parse_diff
from app.services.trace_storage import (
    delete_failed_session,
    list_events,
    store_event,
    update_status,
)

logger = logging.getLogger(__name__)

# Event type constants — used when inserting TraceEvent rows.
EVENT_FUNCTION_ADDED = "FUNCTION_ADDED"
EVENT_FUNCTION_REMOVED = "FUNCTION_REMOVED"
EVENT_FUNCTION_MODIFIED = "FUNCTION_MODIFIED"
EVENT_FILE_CHANGED = "FILE_CHANGED"


# ---------------------------------------------------------------------------
# Pipeline entry point
# ---------------------------------------------------------------------------


async def process_trace(
    db: AsyncSession,
    session_id: uuid.UUID,
    unified_diff: str,
) -> None:
    """Run the full diff-to-events pipeline for a trace session.

    This is designed to be called from a background task, worker, or
    integration test.  All errors are caught, the session is marked FAILED,
    and structured logs are emitted.  The caller is responsible for
    scheduling this coroutine.

    Args:
        db:           Active async database session (must be open for
                      the duration of the pipeline).
        session_id:   UUID of the existing PENDING trace session.
        unified_diff: Raw ``git diff`` or ``git show`` output.
    """
    logger.info("trace_processor.start session_id=%s", session_id)

    try:
        await update_status(db, session_id, TraceStatus.COLLECTING)
        parsed_files = _parse_stage(unified_diff)

        await update_status(db, session_id, TraceStatus.PROCESSING)
        await _store_events_stage(db, session_id, parsed_files)

        await update_status(db, session_id, TraceStatus.COMPLETED)
        logger.info("trace_processor.completed session_id=%s", session_id)

    except Exception as exc:  # noqa: BLE001
        logger.error(
            "trace_processor.failed session_id=%s error_type=%s",
            session_id,
            type(exc).__name__,
        )
        # Best-effort status update — ignore secondary failures.
        try:
            await update_status(db, session_id, TraceStatus.FAILED)
        except Exception:  # noqa: BLE001
            logger.error(
                "trace_processor.status_update_failed session_id=%s",
                session_id,
            )
        raise


# ---------------------------------------------------------------------------
# Stage helpers (pure / async)
# ---------------------------------------------------------------------------


def _parse_stage(unified_diff: str) -> list[ParsedDiff]:
    """Parse unified diff into a list of ParsedDiff objects.

    Args:
        unified_diff: Raw unified diff text.

    Returns:
        List of ParsedDiff (one per changed file).
    """
    parsed = parse_diff(unified_diff)
    logger.info(
        "trace_processor.parsed file_count=%d",
        len(parsed),
    )
    return parsed


async def _store_events_stage(
    db: AsyncSession,
    session_id: uuid.UUID,
    parsed_files: list[ParsedDiff],
) -> None:
    """Generate behavior hashes and store events for all parsed files.

    Emits one FILE_CHANGED event per file plus individual events for
    each added, removed, and modified function.

    Args:
        db:           Active async database session.
        session_id:   UUID of the parent trace session.
        parsed_files: Output from _parse_stage.
    """
    for parsed in parsed_files:
        # Always emit one file-level event.
        file_meta: dict[str, Any] = {
            "language": parsed.language.value,
            "hunk_count": len(parsed.hunks),
            "added_functions": list(parsed.added_functions),
            "removed_functions": list(parsed.removed_functions),
            "modified_functions": list(parsed.modified_functions),
        }
        file_hash = generate_behavior_hash(parsed.file_path, "", _diff_text(parsed))
        await store_event(
            db,
            trace_session_id=session_id,
            event_type=EVENT_FILE_CHANGED,
            file_path=parsed.file_path,
            behavior_hash=file_hash,
            metadata=file_meta,
        )

        # Per-function events for added functions.
        for fn_name in parsed.added_functions:
            fn_hash = generate_behavior_hash(
                parsed.file_path, fn_name, _diff_text(parsed)
            )
            await store_event(
                db,
                trace_session_id=session_id,
                event_type=EVENT_FUNCTION_ADDED,
                file_path=parsed.file_path,
                function_name=fn_name,
                line_number=parsed.line_numbers[0] if parsed.line_numbers else None,
                behavior_hash=fn_hash,
                metadata={"language": parsed.language.value},
            )

        # Per-function events for removed functions.
        for fn_name in parsed.removed_functions:
            fn_hash = generate_behavior_hash(
                parsed.file_path, fn_name, _diff_text(parsed)
            )
            await store_event(
                db,
                trace_session_id=session_id,
                event_type=EVENT_FUNCTION_REMOVED,
                file_path=parsed.file_path,
                function_name=fn_name,
                line_number=parsed.line_numbers[0] if parsed.line_numbers else None,
                behavior_hash=fn_hash,
                metadata={"language": parsed.language.value},
            )

        # Per-function events for modified functions.
        for fn_name in parsed.modified_functions:
            fn_hash = generate_behavior_hash(
                parsed.file_path, fn_name, _diff_text(parsed)
            )
            await store_event(
                db,
                trace_session_id=session_id,
                event_type=EVENT_FUNCTION_MODIFIED,
                file_path=parsed.file_path,
                function_name=fn_name,
                line_number=parsed.line_numbers[0] if parsed.line_numbers else None,
                behavior_hash=fn_hash,
                metadata={"language": parsed.language.value},
            )

    logger.info(
        "trace_processor.events_stored session_id=%s file_count=%d",
        session_id,
        len(parsed_files),
    )


def _diff_text(parsed: ParsedDiff) -> str:
    """Build a compact diff text from all hunks in a ParsedDiff.

    Used as input to the behavior hash engine.

    Args:
        parsed: A single file's ParsedDiff.

    Returns:
        Concatenated added and removed lines from all hunks.
    """
    parts: list[str] = []
    for hunk in parsed.hunks:
        parts.extend(f"+{line}" for line in hunk.added_lines)
        parts.extend(f"-{line}" for line in hunk.removed_lines)
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Cleanup helper (used by failed session cleanup routes / tasks)
# ---------------------------------------------------------------------------


async def cleanup_failed_session(
    db: AsyncSession,
    session_id: uuid.UUID,
) -> bool:
    """Remove a FAILED trace session from the database.

    Delegates to trace_storage.delete_failed_session which enforces the
    FAILED-status precondition.

    Args:
        db:         Active async database session.
        session_id: UUID of the failed session to remove.

    Returns:
        True if deleted, False if not found or status mismatch.
    """
    return await delete_failed_session(db, session_id)


async def get_session_events(
    db: AsyncSession,
    session_id: uuid.UUID,
) -> list[Any]:
    """Convenience wrapper to fetch all events for a session.

    Args:
        db:         Active async database session.
        session_id: UUID of the trace session.

    Returns:
        List of TraceEvent instances.
    """
    return await list_events(db, session_id)
