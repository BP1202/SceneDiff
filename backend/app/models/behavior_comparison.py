"""ORM models for behavior_comparisons and comparison_events tables.

A BehaviorComparison represents the diff analysis between two runtime traces
(Base commit vs Head commit). It aggregates divergence events and records
the overall regression verdict and the first meaningful divergence for IBM Bob.
"""

from __future__ import annotations

from datetime import datetime
import enum
from typing import Any
import uuid

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ComparisonStatus(enum.StrEnum):
    """Lifecycle states for a behavior comparison run."""

    PENDING = "PENDING"
    COMPARING = "COMPARING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ComparisonVerdict(enum.StrEnum):
    """High-level behavior regression verdict."""

    CLEAN = "CLEAN"
    WARNING = "WARNING"
    REGRESSION = "REGRESSION"


class SeverityLevel(enum.StrEnum):
    """Deterministic severity ranking."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class BehaviorComparison(Base):
    """Persisted record of a behavior comparison between two commit executions."""

    __tablename__ = "behavior_comparisons"

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
    status: Mapped[ComparisonStatus] = mapped_column(
        Enum(ComparisonStatus, name="comparisonstatus"),
        nullable=False,
        default=ComparisonStatus.PENDING,
        index=True,
    )
    verdict: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=ComparisonVerdict.CLEAN.value,
        index=True,
    )
    highest_severity: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=SeverityLevel.INFO.value,
        index=True,
    )
    total_divergences: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    # Aggregated category and severity counts
    summary: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    # Details of the first runtime divergence found in the timeline
    first_divergence: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
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

    events: Mapped[list[ComparisonEvent]] = relationship(
        "ComparisonEvent",
        back_populates="comparison",
        cascade="all, delete-orphan",
        lazy="select",
        order_by="ComparisonEvent.divergence_order",
    )

    __table_args__ = (
        Index("ix_behavior_comparisons_repository_name", "repository_name"),
        Index("ix_behavior_comparisons_status", "status"),
        Index("ix_behavior_comparisons_verdict", "verdict"),
        Index("ix_behavior_comparisons_created_at", "created_at"),
    )


class ComparisonEvent(Base):
    """A single detected divergence between Base and Head runtime evidence."""

    __tablename__ = "comparison_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    comparison_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("behavior_comparisons.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )  # "dom" | "network" | "console" | "storage" | "performance"
    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )  # "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "INFO"
    route: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        String(1024),
        nullable=False,
    )
    divergence_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        index=True,
    )
    base_value: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    head_value: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    evidence: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    comparison: Mapped[BehaviorComparison] = relationship(
        "BehaviorComparison",
        back_populates="events",
    )

    __table_args__ = (
        Index("ix_comparison_events_comparison_id", "comparison_id"),
        Index("ix_comparison_events_category", "category"),
        Index("ix_comparison_events_severity", "severity"),
        Index("ix_comparison_events_order", "divergence_order"),
    )
