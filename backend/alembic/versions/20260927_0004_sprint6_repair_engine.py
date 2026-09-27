"""Sprint 6 -- repair_reports and repair_patches tables.

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-27 16:30:00.000000 UTC

Creates
-------
ENUM    repairstatus       (PENDING, GENERATING, COMPLETED, FAILED)
ENUM    risk_level         (LOW, MEDIUM, HIGH, CRITICAL)
TABLE   repair_reports     UUID PK | root_cause_id FK | comparison_id FK
                           | repository_name | status | summary | risk_level
                           | risk_score | repair_confidence | plan JSONB
                           | rollback_plan JSONB | markdown_report TEXT
                           | pr_summary TEXT | created_at | updated_at
TABLE   repair_patches     UUID PK | report_id FK | target_file | diff_content
                           | lines_added | lines_removed | is_validated
                           | risk_level | validation_notes JSONB | created_at

Indexes
-------
ix_repair_reports_root_cause_id
ix_repair_reports_comparison_id
ix_repair_reports_repository_name
ix_repair_reports_status
ix_repair_reports_risk_level
ix_repair_reports_created_at
ix_repair_patches_report_id
ix_repair_patches_risk_level
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# ---------------------------------------------------------------------------
# Revision identifiers
# ---------------------------------------------------------------------------
revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | None = None
depends_on: str | None = None


# ---------------------------------------------------------------------------
# upgrade
# ---------------------------------------------------------------------------


def upgrade() -> None:
    """Create Sprint 6 schema: repair_reports and repair_patches."""
    repairstatus_enum = postgresql.ENUM(
        "PENDING",
        "GENERATING",
        "COMPLETED",
        "FAILED",
        name="repairstatus",
    )
    repairstatus_enum.create(op.get_bind(), checkfirst=True)

    risk_level_enum = postgresql.ENUM(
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL",
        name="risk_level",
    )
    risk_level_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "repair_reports",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "root_cause_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("root_cause_reports.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "comparison_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("behavior_comparisons.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("repository_name", sa.String(255), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(
                "PENDING",
                "GENERATING",
                "COMPLETED",
                "FAILED",
                name="repairstatus",
                create_type=False,
            ),
            nullable=False,
            server_default="COMPLETED",
        ),
        sa.Column("summary", sa.String(), nullable=False),
        sa.Column(
            "risk_level",
            postgresql.ENUM(
                "LOW",
                "MEDIUM",
                "HIGH",
                "CRITICAL",
                name="risk_level",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("risk_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "repair_confidence",
            sa.Integer(),
            nullable=False,
            server_default="80",
        ),
        sa.Column(
            "plan",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "rollback_plan",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "markdown_report",
            sa.Text(),
            nullable=False,
            server_default="",
        ),
        sa.Column(
            "pr_summary",
            sa.Text(),
            nullable=False,
            server_default="",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_index(
        "ix_repair_reports_root_cause_id",
        "repair_reports",
        ["root_cause_id"],
    )
    op.create_index(
        "ix_repair_reports_comparison_id",
        "repair_reports",
        ["comparison_id"],
    )
    op.create_index(
        "ix_repair_reports_repository_name",
        "repair_reports",
        ["repository_name"],
    )
    op.create_index(
        "ix_repair_reports_status",
        "repair_reports",
        ["status"],
    )
    op.create_index(
        "ix_repair_reports_risk_level",
        "repair_reports",
        ["risk_level"],
    )
    op.create_index(
        "ix_repair_reports_created_at",
        "repair_reports",
        ["created_at"],
    )

    op.create_table(
        "repair_patches",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "report_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("repair_reports.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("target_file", sa.String(500), nullable=False),
        sa.Column("diff_content", sa.Text(), nullable=False),
        sa.Column("lines_added", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("lines_removed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_validated", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "risk_level",
            postgresql.ENUM(
                "LOW",
                "MEDIUM",
                "HIGH",
                "CRITICAL",
                name="risk_level",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "validation_notes",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_index(
        "ix_repair_patches_report_id",
        "repair_patches",
        ["report_id"],
    )
    op.create_index(
        "ix_repair_patches_risk_level",
        "repair_patches",
        ["risk_level"],
    )


# ---------------------------------------------------------------------------
# downgrade
# ---------------------------------------------------------------------------


def downgrade() -> None:
    """Drop Sprint 6 tables and enums in reverse creation order."""
    op.drop_index("ix_repair_patches_risk_level", table_name="repair_patches")
    op.drop_index("ix_repair_patches_report_id", table_name="repair_patches")
    op.drop_table("repair_patches")

    op.drop_index("ix_repair_reports_created_at", table_name="repair_reports")
    op.drop_index("ix_repair_reports_risk_level", table_name="repair_reports")
    op.drop_index("ix_repair_reports_status", table_name="repair_reports")
    op.drop_index("ix_repair_reports_repository_name", table_name="repair_reports")
    op.drop_index("ix_repair_reports_comparison_id", table_name="repair_reports")
    op.drop_index("ix_repair_reports_root_cause_id", table_name="repair_reports")
    op.drop_table("repair_reports")

    op.execute("DROP TYPE IF EXISTS risk_level CASCADE")
    op.execute("DROP TYPE IF EXISTS repairstatus CASCADE")
