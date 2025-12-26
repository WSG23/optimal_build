"""Add missing columns to fin_scenarios table.

Revision ID: 20251207_000037
Revises: 20251207_000036
Create Date: 2025-12-07
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "20251207_000037"
down_revision = "20251207_000036"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add lineage & audit columns
    op.add_column(
        "fin_scenarios",
        sa.Column("parent_scenario_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "fin_scenarios",
        sa.Column("export_hash", sa.String(64), nullable=True),
    )

    # Add multi-jurisdiction financing columns
    op.add_column(
        "fin_scenarios",
        sa.Column("jurisdiction_code", sa.String(10), nullable=True),
    )
    op.add_column(
        "fin_scenarios",
        sa.Column("ltv_limit_pct", sa.Numeric(6, 4), nullable=True),
    )
    op.add_column(
        "fin_scenarios",
        sa.Column("absd_rate_pct", sa.Numeric(6, 4), nullable=True),
    )
    op.add_column(
        "fin_scenarios",
        sa.Column("dscr_min", sa.Numeric(6, 4), nullable=True),
    )
    op.add_column(
        "fin_scenarios",
        sa.Column("construction_loan_rate_pct", sa.Numeric(6, 4), nullable=True),
    )

    # Add foreign key constraint for self-referential relationship
    op.create_foreign_key(
        "fk_fin_scenarios_parent_scenario_id",
        "fin_scenarios",
        "fin_scenarios",
        ["parent_scenario_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Add index on parent_scenario_id for lineage queries
    op.create_index(
        "ix_fin_scenarios_parent_scenario_id",
        "fin_scenarios",
        ["parent_scenario_id"],
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if "fin_scenarios" in inspector.get_table_names():
        op.execute('DROP INDEX IF EXISTS "ix_fin_scenarios_parent_scenario_id"')

        fk_names = {fk["name"] for fk in inspector.get_foreign_keys("fin_scenarios")}
        if "fk_fin_scenarios_parent_scenario_id" in fk_names:
            op.execute(
                "ALTER TABLE fin_scenarios "
                "DROP CONSTRAINT IF EXISTS fk_fin_scenarios_parent_scenario_id"
            )

        existing_columns = {
            col["name"] for col in inspector.get_columns("fin_scenarios")
        }
        drop_columns = [
            "construction_loan_rate_pct",
            "dscr_min",
            "absd_rate_pct",
            "ltv_limit_pct",
            "jurisdiction_code",
            "export_hash",
            "parent_scenario_id",
        ]
        if any(col in existing_columns for col in drop_columns):
            with op.batch_alter_table("fin_scenarios") as batch_op:
                for column in drop_columns:
                    if column in existing_columns:
                        batch_op.drop_column(column)
