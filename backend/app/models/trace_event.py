"""ORM model for trace_events table.

A TraceEvent represents a single captured behavior event (e.g. a function
change, a line modification) within a parent TraceSession.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any
import uuid

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.trace_session import TraceSession


class TraceEvent(Base):
    """Single behavior observation captured during trace processing.

    Metadata is stored sanitized — Secret Shield runs before insert.
    """

    __tablename__ = "trace_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    trace_session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trace_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    file_path: Mapped[str] = mapped_column(
        String(1024),
        nullable=False,
    )
    function_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    line_number: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    behavior_hash: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        index=True,
    )
    # Sanitized by Secret Shield before storage — never contains raw secrets.
    metadata_: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata",
        JSONB,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    trace_session: Mapped[TraceSession] = relationship(
        "TraceSession",
        back_populates="events",
    )

    __table_args__ = (
        Index("ix_trace_events_trace_session_id", "trace_session_id"),
        Index("ix_trace_events_event_type", "event_type"),
        Index("ix_trace_events_behavior_hash", "behavior_hash"),
    )
