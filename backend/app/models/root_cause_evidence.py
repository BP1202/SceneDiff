"""ORM model for root_cause_evidence table (Sprint 5 - Task 41).

Stores individual correlated evidence items linked to a root cause analysis.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any
import uuid

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.root_cause_report import RootCauseReport


class RootCauseEvidence(Base):
    """Individual correlated evidence event supporting an AI root cause diagnosis."""

    __tablename__ = "root_cause_evidence"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("root_cause_reports.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )
    route: Mapped[str] = mapped_column(String(255), nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    function_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    divergence_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    is_root_cause_candidate: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    evidence_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        nullable=False,
    )

    report: Mapped[RootCauseReport] = relationship(
        "RootCauseReport",
        back_populates="evidence_records",
    )

    __table_args__ = (
        Index("ix_root_cause_evidence_order", "report_id", "divergence_order"),
    )
