"""Sprint 2 -- trace_sessions and trace_events tables.

Revision ID: 0001
Revises: (initial — first migration)
Create Date: 2026-09-27 00:00:00.000000 UTC

Creates
-------
ENUM    tracestatus          (PENDING, COLLECTING, PROCESSING, COMPLETED, FAILED)
TABLE   trace_sessions       UUID PK | repository_name | base_commit | head_commit
                             | branch | status | created_at | updated_at
TABLE   trace_events         UUID PK | trace_session_id FK | event_type | file_path
                             | function_name | line_number | behavior_hash
                             | metadata JSONB | created_at

Indexes
-------
ix_trace_sessions_repository_name
ix_trace_sessions_status
ix_trace_sessions_created_at
ix_trace_events_trace_session_id
ix_trace_events_event_type
ix_trace_events_behavior_hash
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# ---------------------------------------------------------------------------
# Revision identifiers — used by Alembic to chain migrations.
# ---------------------------------------------------------------------------
revision: str = "0001"
down_revision: str | None = None
branch_labels: str | None = None
depends_on: str | None = None


# ---------------------------------------------------------------------------
# upgrade — forward migration
# ---------------------------------------------------------------------------


def upgrade() -> None:
    """Create Sprint 2 schema: trace_sessions and trace_events."""

    # ----------------------------------------------------------------
    # Create the ENUM type first; using checkfirst=True so the
    # migration is idempotent if the type already exists.
    # ----------------------------------------------------------------
    tracestatus_enum = postgresql.ENUM(
        "PENDING",
        "COLLECTING",
        "PROCESSING",
        "COMPLETED",
        "FAILED",
        name="tracestatus",
    )
    tracestatus_enum.create(op.get_bind(), checkfirst=True)

    # ----------------------------------------------------------------
    # TABLE: trace_sessions
    # ----------------------------------------------------------------
    op.create_table(
        "trace_sessions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "repository_name",
            sa.String(255),
            nullable=False,
        ),
        sa.Column(
            "base_commit",
            sa.String(40),
            nullable=False,
        ),
        sa.Column(
            "head_commit",
            sa.String(40),
            nullable=False,
        ),
        sa.Column(
            "branch",
            sa.String(255),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "PENDING",
                "COLLECTING",
                "PROCESSING",
                "COMPLETED",
                "FAILED",
                name="tracestatus",
                create_type=False,  # already created above
            ),
            nullable=False,
            server_default="PENDING",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    op.create_index(
        "ix_trace_sessions_repository_name",
        "trace_sessions",
        ["repository_name"],
    )
    op.create_index(
        "ix_trace_sessions_status",
        "trace_sessions",
        ["status"],
    )
    op.create_index(
        "ix_trace_sessions_created_at",
        "trace_sessions",
        ["created_at"],
    )

    # ----------------------------------------------------------------
    # TABLE: trace_events
    # metadata is stored as JSONB — Secret Shield sanitizes before insert.
    # ----------------------------------------------------------------
    op.create_table(
        "trace_events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "trace_session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("trace_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "event_type",
            sa.String(100),
            nullable=False,
        ),
        sa.Column(
            "file_path",
            sa.String(1024),
            nullable=False,
        ),
        sa.Column(
            "function_name",
            sa.String(255),
            nullable=True,
        ),
        sa.Column(
            "line_number",
            sa.Integer,
            nullable=True,
        ),
        sa.Column(
            "behavior_hash",
            sa.String(64),
            nullable=True,
        ),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    op.create_index(
        "ix_trace_events_trace_session_id",
        "trace_events",
        ["trace_session_id"],
    )
    op.create_index(
        "ix_trace_events_event_type",
        "trace_events",
        ["event_type"],
    )
    op.create_index(
        "ix_trace_events_behavior_hash",
        "trace_events",
        ["behavior_hash"],
    )


# ---------------------------------------------------------------------------
# downgrade — reverse migration (reverse dependency order)
# ---------------------------------------------------------------------------


def downgrade() -> None:
    """Drop Sprint 2 schema in reverse dependency order."""

    # Drop trace_events first (child table — has FK to trace_sessions).
    op.drop_index("ix_trace_events_behavior_hash", table_name="trace_events")
    op.drop_index("ix_trace_events_event_type", table_name="trace_events")
    op.drop_index("ix_trace_events_trace_session_id", table_name="trace_events")
    op.drop_table("trace_events")

    # Drop trace_sessions (parent table).
    op.drop_index("ix_trace_sessions_created_at", table_name="trace_sessions")
    op.drop_index("ix_trace_sessions_status", table_name="trace_sessions")
    op.drop_index("ix_trace_sessions_repository_name", table_name="trace_sessions")
    op.drop_table("trace_sessions")

    # Drop the ENUM type last — PostgreSQL requires all columns using it gone first.
    sa.Enum(name="tracestatus").drop(op.get_bind(), checkfirst=True)
