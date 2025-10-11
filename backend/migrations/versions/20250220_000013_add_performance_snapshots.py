"""Add agent performance snapshot and benchmark tables."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20250220_000013"
down_revision = "20250220_000012_add_commission_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agent_performance_snapshots",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "agent_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("as_of_date", sa.Date(), nullable=False),
        sa.Column("deals_open", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "deals_closed_won", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column(
            "deals_closed_lost", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("gross_pipeline_value", sa.Numeric(18, 2), nullable=True),
        sa.Column("weighted_pipeline_value", sa.Numeric(18, 2), nullable=True),
        sa.Column("confirmed_commission_amount", sa.Numeric(18, 2), nullable=True),
        sa.Column("disputed_commission_amount", sa.Numeric(18, 2), nullable=True),
        sa.Column("avg_cycle_days", sa.Numeric(10, 2), nullable=True),
        sa.Column("conversion_rate", sa.Numeric(6, 4), nullable=True),
        sa.Column(
            "roi_metrics",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "snapshot_context",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "agent_id",
            "as_of_date",
            name="uq_agent_snapshot_agent_date",
        ),
    )
    op.create_index(
        "ix_agent_performance_snapshots_agent_date",
        "agent_performance_snapshots",
        ["agent_id", "as_of_date"],
    )

    op.create_table(
        "performance_benchmarks",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column("metric_key", sa.String(length=100), nullable=False),
        sa.Column("asset_type", sa.String(length=50), nullable=True),
        sa.Column("deal_type", sa.String(length=50), nullable=True),
        sa.Column("cohort", sa.String(length=50), nullable=False),
        sa.Column("value_numeric", sa.Numeric(18, 4), nullable=True),
        sa.Column("value_text", sa.String(length=255), nullable=True),
        sa.Column("source", sa.String(length=255), nullable=True),
        sa.Column("effective_date", sa.Date(), nullable=True),
        sa.Column(
            "metadata",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_performance_benchmarks_metric_asset_deal",
        "performance_benchmarks",
        ["metric_key", "asset_type", "deal_type", "cohort"],
    )
    op.create_index(
        "ix_performance_benchmarks_effective_date",
        "performance_benchmarks",
        ["effective_date"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_performance_benchmarks_effective_date",
        table_name="performance_benchmarks",
        if_exists=True,
    )
    op.drop_index(
        "ix_performance_benchmarks_metric_asset_deal",
        table_name="performance_benchmarks",
        if_exists=True,
    )
    op.drop_table("performance_benchmarks", if_exists=True)

    op.drop_index(
        "ix_agent_performance_snapshots_agent_date",
        table_name="agent_performance_snapshots",
        if_exists=True,
    )
    op.drop_table("agent_performance_snapshots", if_exists=True)
