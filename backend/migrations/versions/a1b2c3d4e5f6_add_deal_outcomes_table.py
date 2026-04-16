"""add deal_outcomes table

Revision ID: a1b2c3d4e5f6
Revises: ff3f1bcb3551
Create Date: 2026-04-16 10:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "ff3f1bcb3551"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "deal_outcomes",
        sa.Column("id", sa.CHAR(36), primary_key=True),
        sa.Column("deal_id", sa.CHAR(36), nullable=False),
        sa.Column("scenario_id", sa.Integer(), nullable=True),
        sa.Column("recorded_by", sa.CHAR(36), nullable=False),
        # Resolution
        sa.Column("resolution", sa.String(40), nullable=False),
        sa.Column("resolution_note", sa.Text(), nullable=True),
        # Actual financials
        sa.Column("actual_purchase_price", sa.Numeric(18, 2), nullable=True),
        sa.Column(
            "actual_price_currency",
            sa.String(3),
            nullable=False,
            server_default="SGD",
        ),
        sa.Column("actual_gfa_approved_sqm", sa.Numeric(12, 2), nullable=True),
        sa.Column("actual_construction_cost", sa.Numeric(18, 2), nullable=True),
        sa.Column("actual_noi", sa.Numeric(18, 2), nullable=True),
        sa.Column("actual_yield_pct", sa.Numeric(6, 3), nullable=True),
        # Timeline
        sa.Column("actual_completion_date", sa.Date(), nullable=True),
        sa.Column("approval_submitted_date", sa.Date(), nullable=True),
        sa.Column("approval_decided_date", sa.Date(), nullable=True),
        # Authority / approval
        sa.Column("approval_authority", sa.String(100), nullable=True),
        sa.Column("approval_outcome", sa.String(40), nullable=True),
        sa.Column("approval_conditions", sa.Text(), nullable=True),
        sa.Column("gfa_amendment_sqm", sa.Numeric(12, 2), nullable=True),
        # Denormalised for benchmarks
        sa.Column("jurisdiction_code", sa.String(10), nullable=True),
        sa.Column("asset_type", sa.String(40), nullable=True),
        # Metadata
        sa.Column(
            "metadata",
            sa.JSON().with_variant(sa.dialects.postgresql.JSONB(), "postgresql"),
            nullable=False,
            server_default="{}",
        ),
        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # Foreign keys
    op.create_foreign_key(
        "fk_deal_outcomes_deal_id",
        "deal_outcomes",
        "agent_deals",
        ["deal_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_deal_outcomes_scenario_id",
        "deal_outcomes",
        "fin_scenarios",
        ["scenario_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_deal_outcomes_recorded_by",
        "deal_outcomes",
        "users",
        ["recorded_by"],
        ["id"],
        ondelete="CASCADE",
    )

    # Indexes (all FKs indexed per Rule 9)
    op.create_index(
        "ix_deal_outcomes_deal_id", "deal_outcomes", ["deal_id"], unique=True
    )
    op.create_index("ix_deal_outcomes_scenario_id", "deal_outcomes", ["scenario_id"])
    op.create_index("ix_deal_outcomes_recorded_by", "deal_outcomes", ["recorded_by"])
    op.create_index("ix_deal_outcomes_resolution", "deal_outcomes", ["resolution"])
    op.create_index(
        "ix_deal_outcomes_jurisdiction_asset",
        "deal_outcomes",
        ["jurisdiction_code", "asset_type"],
    )
    op.create_index("ix_deal_outcomes_created_at", "deal_outcomes", ["created_at"])


def downgrade() -> None:
    # Drop indexes (guarded with IF EXISTS via raw SQL)
    op.execute("DROP INDEX IF EXISTS ix_deal_outcomes_created_at")
    op.execute("DROP INDEX IF EXISTS ix_deal_outcomes_jurisdiction_asset")
    op.execute("DROP INDEX IF EXISTS ix_deal_outcomes_resolution")
    op.execute("DROP INDEX IF EXISTS ix_deal_outcomes_recorded_by")
    op.execute("DROP INDEX IF EXISTS ix_deal_outcomes_scenario_id")
    op.execute("DROP INDEX IF EXISTS ix_deal_outcomes_deal_id")

    # Drop foreign key constraints (guarded with IF EXISTS via raw SQL)
    op.execute(
        "ALTER TABLE IF EXISTS deal_outcomes "
        "DROP CONSTRAINT IF EXISTS fk_deal_outcomes_recorded_by"
    )
    op.execute(
        "ALTER TABLE IF EXISTS deal_outcomes "
        "DROP CONSTRAINT IF EXISTS fk_deal_outcomes_scenario_id"
    )
    op.execute(
        "ALTER TABLE IF EXISTS deal_outcomes "
        "DROP CONSTRAINT IF EXISTS fk_deal_outcomes_deal_id"
    )

    # Drop table (guarded with IF EXISTS via raw SQL)
    op.execute("DROP TABLE IF EXISTS deal_outcomes CASCADE")
