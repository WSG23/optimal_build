"""Add fin_asset_breakdowns table for per-asset finance metrics."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20251111_000024"
down_revision = "20251104_000023"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "fin_asset_breakdowns",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "scenario_id",
            sa.Integer(),
            sa.ForeignKey("fin_scenarios.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("asset_type", sa.String(length=80), nullable=False),
        sa.Column("allocation_pct", sa.Numeric(10, 4), nullable=True),
        sa.Column("nia_sqm", sa.Numeric(16, 2), nullable=True),
        sa.Column("rent_psm_month", sa.Numeric(16, 2), nullable=True),
        sa.Column("annual_noi_sgd", sa.Numeric(18, 2), nullable=True),
        sa.Column("annual_revenue_sgd", sa.Numeric(18, 2), nullable=True),
        sa.Column("estimated_capex_sgd", sa.Numeric(18, 2), nullable=True),
        sa.Column("payback_years", sa.Numeric(12, 4), nullable=True),
        sa.Column("absorption_months", sa.Numeric(12, 4), nullable=True),
        sa.Column("stabilised_yield_pct", sa.Numeric(12, 6), nullable=True),
        sa.Column("risk_level", sa.String(length=40), nullable=True),
        sa.Column("risk_priority", sa.Integer(), nullable=True),
        sa.Column(
            "notes",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.create_index(
        "ix_fin_asset_breakdowns_project",
        "fin_asset_breakdowns",
        ["project_id"],
    )
    op.create_index(
        "ix_fin_asset_breakdowns_scenario",
        "fin_asset_breakdowns",
        ["scenario_id"],
    )
    op.create_index(
        "ix_fin_asset_breakdowns_asset_type",
        "fin_asset_breakdowns",
        ["asset_type"],
    )
    op.alter_column(
        "fin_asset_breakdowns",
        "notes",
        server_default=None,
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_fin_asset_breakdowns_asset_type")
    op.execute("DROP INDEX IF EXISTS ix_fin_asset_breakdowns_scenario")
    op.execute("DROP INDEX IF EXISTS ix_fin_asset_breakdowns_project")
    op.execute("DROP TABLE IF EXISTS fin_asset_breakdowns CASCADE")
