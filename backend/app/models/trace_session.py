"""ORM model for trace_sessions table.

A TraceSession represents a single diff analysis run between two commits.
It tracks the lifecycle of the entire trace collection and processing pipeline.
"""

from __future__ import annotations

from datetime import datetime
import enum
from typing import TYPE_CHECKING
import uuid

from sqlalchemy import DateTime, Enum, Index, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.trace_event import TraceEvent


class TraceStatus(enum.StrEnum):
    """Lifecycle states for a trace session."""

    PENDING = "PENDING"
    COLLECTING = "COLLECTING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class TraceSession(Base):
    """Persisted record of a single trace collection run.

    Stores commit coordinates and tracks pipeline status.
    Never stores secrets, tokens, or sensitive environment values.
    """

    __tablename__ = "trace_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    repository_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    base_commit: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )
    head_commit: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )
    branch: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    status: Mapped[TraceStatus] = mapped_column(
        Enum(TraceStatus, name="tracestatus"),
        nullable=False,
        default=TraceStatus.PENDING,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationship populated by TraceEvent.trace_session FK
    events: Mapped[list[TraceEvent]] = relationship(
        "TraceEvent",
        back_populates="trace_session",
        cascade="all, delete-orphan",
        lazy="select",
    )

    __table_args__ = (
        Index("ix_trace_sessions_repository_name", "repository_name"),
        Index("ix_trace_sessions_status", "status"),
        Index("ix_trace_sessions_created_at", "created_at"),
    )
