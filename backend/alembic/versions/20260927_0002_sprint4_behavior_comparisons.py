"""Sprint 4 -- behavior_comparisons and comparison_events tables.

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-27 12:00:00.000000 UTC

Creates
-------
ENUM    comparisonstatus     (PENDING, COMPARING, COMPLETED, FAILED)
TABLE   behavior_comparisons UUID PK | repository_name | base_commit | head_commit
                             | status | verdict | highest_severity | total_divergences
                             | summary JSONB | first_divergence JSONB
                             | created_at | updated_at
TABLE   comparison_events    UUID PK | comparison_id FK | category | severity
                             | route | event_type | title | description
                             | divergence_order | base_value JSONB
                             | head_value JSONB | evidence JSONB | created_at

Indexes
-------
ix_behavior_comparisons_repository_name
ix_behavior_comparisons_status
ix_behavior_comparisons_verdict
ix_behavior_comparisons_created_at
ix_comparison_events_comparison_id
ix_comparison_events_category
ix_comparison_events_severity
ix_comparison_events_order
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# ---------------------------------------------------------------------------
# Revision identifiers — used by Alembic to chain migrations.
# ---------------------------------------------------------------------------
revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | None = None
depends_on: str | None = None


# ---------------------------------------------------------------------------
# upgrade — forward migration
# ---------------------------------------------------------------------------


def upgrade() -> None:
    """Create Sprint 4 schema: behavior_comparisons and comparison_events."""
    comparisonstatus_enum = postgresql.ENUM(
        "PENDING",
        "COMPARING",
        "COMPLETED",
        "FAILED",
        name="comparisonstatus",
    )
    comparisonstatus_enum.create(op.get_bind(), checkfirst=True)

    # ----------------------------------------------------------------
    # TABLE: behavior_comparisons
    # ----------------------------------------------------------------
    op.create_table(
        "behavior_comparisons",
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
            "status",
            sa.Enum(
                "PENDING",
                "COMPARING",
                "COMPLETED",
                "FAILED",
                name="comparisonstatus",
                create_type=False,
            ),
            nullable=False,
            server_default="PENDING",
        ),
        sa.Column(
            "verdict",
            sa.String(32),
            nullable=False,
            server_default="CLEAN",
        ),
        sa.Column(
            "highest_severity",
            sa.String(32),
            nullable=False,
            server_default="INFO",
        ),
        sa.Column(
            "total_divergences",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "summary",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "first_divergence",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
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
        "ix_behavior_comparisons_repository_name",
        "behavior_comparisons",
        ["repository_name"],
    )
    op.create_index(
        "ix_behavior_comparisons_status",
        "behavior_comparisons",
        ["status"],
    )
    op.create_index(
        "ix_behavior_comparisons_verdict",
        "behavior_comparisons",
        ["verdict"],
    )
    op.create_index(
        "ix_behavior_comparisons_created_at",
        "behavior_comparisons",
        ["created_at"],
    )

    # ----------------------------------------------------------------
    # TABLE: comparison_events
    # ----------------------------------------------------------------
    op.create_table(
        "comparison_events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "comparison_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("behavior_comparisons.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "category",
            sa.String(50),
            nullable=False,
        ),
        sa.Column(
            "severity",
            sa.String(20),
            nullable=False,
        ),
        sa.Column(
            "route",
            sa.String(255),
            nullable=False,
        ),
        sa.Column(
            "event_type",
            sa.String(100),
            nullable=False,
        ),
        sa.Column(
            "title",
            sa.String(255),
            nullable=False,
        ),
        sa.Column(
            "description",
            sa.String(1024),
            nullable=False,
        ),
        sa.Column(
            "divergence_order",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "base_value",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "head_value",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "evidence",
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
        "ix_comparison_events_comparison_id",
        "comparison_events",
        ["comparison_id"],
    )
    op.create_index(
        "ix_comparison_events_category",
        "comparison_events",
        ["category"],
    )
    op.create_index(
        "ix_comparison_events_severity",
        "comparison_events",
        ["severity"],
    )
    op.create_index(
        "ix_comparison_events_order",
        "comparison_events",
        ["divergence_order"],
    )


# ---------------------------------------------------------------------------
# downgrade — reverse migration
# ---------------------------------------------------------------------------


def downgrade() -> None:
    """Drop comparison_events, behavior_comparisons, and comparisonstatus enum."""
    op.drop_index("ix_comparison_events_order", table_name="comparison_events")
    op.drop_index("ix_comparison_events_severity", table_name="comparison_events")
    op.drop_index("ix_comparison_events_category", table_name="comparison_events")
    op.drop_index("ix_comparison_events_comparison_id", table_name="comparison_events")
    op.drop_table("comparison_events")

    op.drop_index(
        "ix_behavior_comparisons_created_at", table_name="behavior_comparisons"
    )
    op.drop_index("ix_behavior_comparisons_verdict", table_name="behavior_comparisons")
    op.drop_index("ix_behavior_comparisons_status", table_name="behavior_comparisons")
    op.drop_index(
        "ix_behavior_comparisons_repository_name", table_name="behavior_comparisons"
    )
    op.drop_table("behavior_comparisons")

    comparisonstatus_enum = postgresql.ENUM(
        "PENDING",
        "COMPARING",
        "COMPLETED",
        "FAILED",
        name="comparisonstatus",
    )
    comparisonstatus_enum.drop(op.get_bind(), checkfirst=True)
