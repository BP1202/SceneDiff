"""Sprint 5 -- root_cause_reports and root_cause_evidence tables.

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-27 15:00:00.000000 UTC

Creates
-------
ENUM    analysisstatus     (PENDING, ANALYZING, COMPLETED, FAILED)
ENUM    confidence_level   (VERY_HIGH, HIGH, MEDIUM, LOW)
TABLE   root_cause_reports UUID PK | comparison_id FK | repository_name
                           | base_commit | head_commit | status | summary
                           | confidence_score | confidence_band
                           | primary_candidate JSONB | secondary_candidates JSONB
                           | repair_plan JSONB | explanation JSONB
                           | bob_prompt TEXT | created_at | updated_at
TABLE   root_cause_evidence UUID PK | report_id FK | category | severity
                            | route | event_type | title | description
                            | file_path | function_name | divergence_order
                            | is_root_cause_candidate | evidence_metadata JSONB
                            | created_at

Indexes
-------
ix_root_cause_reports_comparison_id
ix_root_cause_reports_repository_name
ix_root_cause_reports_status
ix_root_cause_reports_created_at
ix_root_cause_evidence_report_id
ix_root_cause_evidence_category
ix_root_cause_evidence_severity
ix_root_cause_evidence_order
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# ---------------------------------------------------------------------------
# Revision identifiers
# ---------------------------------------------------------------------------
revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | None = None
depends_on: str | None = None


# ---------------------------------------------------------------------------
# upgrade
# ---------------------------------------------------------------------------


def upgrade() -> None:
    """Create Sprint 5 schema: root_cause_reports and root_cause_evidence."""
    analysisstatus_enum = postgresql.ENUM(
        "PENDING",
        "ANALYZING",
        "COMPLETED",
        "FAILED",
        name="analysisstatus",
    )
    analysisstatus_enum.create(op.get_bind(), checkfirst=True)

    confidence_level_enum = postgresql.ENUM(
        "VERY_HIGH",
        "HIGH",
        "MEDIUM",
        "LOW",
        name="confidence_level",
    )
    confidence_level_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "root_cause_reports",
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
        sa.Column("repository_name", sa.String(255), nullable=False),
        sa.Column("base_commit", sa.String(64), nullable=False),
        sa.Column("head_commit", sa.String(64), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(
                "PENDING",
                "ANALYZING",
                "COMPLETED",
                "FAILED",
                name="analysisstatus",
                create_type=False,
            ),
            nullable=False,
            server_default="COMPLETED",
        ),
        sa.Column("summary", sa.String(), nullable=False),
        sa.Column("confidence_score", sa.Integer(), nullable=False),
        sa.Column(
            "confidence_band",
            postgresql.ENUM(
                "VERY_HIGH",
                "HIGH",
                "MEDIUM",
                "LOW",
                name="confidence_level",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "primary_candidate",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "secondary_candidates",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "repair_plan",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "explanation",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "bob_prompt",
            sa.String(),
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
        "ix_root_cause_reports_comparison_id",
        "root_cause_reports",
        ["comparison_id"],
    )
    op.create_index(
        "ix_root_cause_reports_repository_name",
        "root_cause_reports",
        ["repository_name"],
    )
    op.create_index(
        "ix_root_cause_reports_status",
        "root_cause_reports",
        ["status"],
    )
    op.create_index(
        "ix_root_cause_reports_created_at",
        "root_cause_reports",
        ["created_at"],
    )

    op.create_table(
        "root_cause_evidence",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "report_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("root_cause_reports.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("route", sa.String(255), nullable=False),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("file_path", sa.String(500), nullable=True),
        sa.Column("function_name", sa.String(255), nullable=True),
        sa.Column(
            "divergence_order",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "is_root_cause_candidate",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "evidence_metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_index(
        "ix_root_cause_evidence_report_id",
        "root_cause_evidence",
        ["report_id"],
    )
    op.create_index(
        "ix_root_cause_evidence_category",
        "root_cause_evidence",
        ["category"],
    )
    op.create_index(
        "ix_root_cause_evidence_severity",
        "root_cause_evidence",
        ["severity"],
    )
    op.create_index(
        "ix_root_cause_evidence_order",
        "root_cause_evidence",
        ["report_id", "divergence_order"],
    )


# ---------------------------------------------------------------------------
# downgrade
# ---------------------------------------------------------------------------


def downgrade() -> None:
    """Drop Sprint 5 schema: root_cause_evidence and root_cause_reports."""
    op.drop_index(
        "ix_root_cause_evidence_order",
        table_name="root_cause_evidence",
    )
    op.drop_index(
        "ix_root_cause_evidence_severity",
        table_name="root_cause_evidence",
    )
    op.drop_index(
        "ix_root_cause_evidence_category",
        table_name="root_cause_evidence",
    )
    op.drop_index(
        "ix_root_cause_evidence_report_id",
        table_name="root_cause_evidence",
    )
    op.drop_table("root_cause_evidence")

    op.drop_index(
        "ix_root_cause_reports_created_at",
        table_name="root_cause_reports",
    )
    op.drop_index(
        "ix_root_cause_reports_status",
        table_name="root_cause_reports",
    )
    op.drop_index(
        "ix_root_cause_reports_repository_name",
        table_name="root_cause_reports",
    )
    op.drop_index(
        "ix_root_cause_reports_comparison_id",
        table_name="root_cause_reports",
    )
    op.drop_table("root_cause_reports")

    confidence_level_enum = postgresql.ENUM(
        "VERY_HIGH",
        "HIGH",
        "MEDIUM",
        "LOW",
        name="confidence_level",
    )
    confidence_level_enum.drop(op.get_bind(), checkfirst=True)

    analysisstatus_enum = postgresql.ENUM(
        "PENDING",
        "ANALYZING",
        "COMPLETED",
        "FAILED",
        name="analysisstatus",
    )
    analysisstatus_enum.drop(op.get_bind(), checkfirst=True)
