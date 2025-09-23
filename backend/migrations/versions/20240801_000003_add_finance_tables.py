"""Create finance modelling tables."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20240801_000003"
down_revision = "20240626_000002"
branch_labels = None
depends_on = None


JSONB_TYPE = postgresql.JSONB(astext_type=sa.Text())


def upgrade() -> None:
    """Apply the migration."""

    op.create_table(
        "fin_projects",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "project_id",
            sa.Integer(),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column(
            "currency",
            sa.String(length=3),
            nullable=False,
            server_default=sa.text("'USD'"),
        ),
        sa.Column("discount_rate", sa.Numeric(5, 4), nullable=True),
        sa.Column("total_development_cost", sa.Numeric(16, 2), nullable=True),
        sa.Column("total_gross_profit", sa.Numeric(16, 2), nullable=True),
        sa.Column("metadata", JSONB_TYPE, nullable=False, server_default=sa.text("'{}'")),
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
    op.create_index("ix_fin_projects_project_id", "fin_projects", ["project_id"])
    op.create_index("ix_fin_projects_created_at", "fin_projects", ["created_at"])
    op.create_index(
        "idx_fin_projects_project_name",
        "fin_projects",
        ["project_id", "name"],
    )

    op.create_table(
        "fin_scenarios",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "project_id",
            sa.Integer(),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "fin_project_id",
            sa.Integer(),
            sa.ForeignKey("fin_projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "assumptions", JSONB_TYPE, nullable=False, server_default=sa.text("'{}'")
        ),
        sa.Column(
            "is_primary",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
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
    op.create_index("ix_fin_scenarios_project_id", "fin_scenarios", ["project_id"])
    op.create_index("ix_fin_scenarios_fin_project_id", "fin_scenarios", ["fin_project_id"])
    op.create_index("ix_fin_scenarios_is_primary", "fin_scenarios", ["is_primary"])
    op.create_index("ix_fin_scenarios_created_at", "fin_scenarios", ["created_at"])
    op.create_index(
        "idx_fin_scenarios_project_name",
        "fin_scenarios",
        ["project_id", "name"],
    )

    op.create_table(
        "fin_cost_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "project_id",
            sa.Integer(),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "scenario_id",
            sa.Integer(),
            sa.ForeignKey("fin_scenarios.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=True),
        sa.Column("cost_group", sa.String(length=50), nullable=True),
        sa.Column("quantity", sa.Numeric(14, 2), nullable=True),
        sa.Column("unit_cost", sa.Numeric(14, 2), nullable=True),
        sa.Column("total_cost", sa.Numeric(16, 2), nullable=True),
        sa.Column("metadata", JSONB_TYPE, nullable=False, server_default=sa.text("'{}'")),
    )
    op.create_index("ix_fin_cost_items_project_id", "fin_cost_items", ["project_id"])
    op.create_index("ix_fin_cost_items_scenario_id", "fin_cost_items", ["scenario_id"])
    op.create_index(
        "idx_fin_cost_items_project_name",
        "fin_cost_items",
        ["project_id", "name"],
    )

    op.create_table(
        "fin_schedules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "project_id",
            sa.Integer(),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "scenario_id",
            sa.Integer(),
            sa.ForeignKey("fin_scenarios.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("month_index", sa.Integer(), nullable=False),
        sa.Column("hard_cost", sa.Numeric(16, 2), nullable=True),
        sa.Column("soft_cost", sa.Numeric(16, 2), nullable=True),
        sa.Column("revenue", sa.Numeric(16, 2), nullable=True),
        sa.Column("cash_flow", sa.Numeric(16, 2), nullable=True),
        sa.Column("cumulative_cash_flow", sa.Numeric(16, 2), nullable=True),
        sa.Column("metadata", JSONB_TYPE, nullable=False, server_default=sa.text("'{}'")),
    )
    op.create_index("ix_fin_schedules_project_id", "fin_schedules", ["project_id"])
    op.create_index("ix_fin_schedules_scenario_id", "fin_schedules", ["scenario_id"])
    op.create_index(
        "idx_fin_schedules_project_month",
        "fin_schedules",
        ["project_id", "month_index"],
    )

    op.create_table(
        "fin_capital_stacks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "project_id",
            sa.Integer(),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "scenario_id",
            sa.Integer(),
            sa.ForeignKey("fin_scenarios.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("source_type", sa.String(length=50), nullable=True),
        sa.Column("tranche_order", sa.Integer(), nullable=True),
        sa.Column("amount", sa.Numeric(16, 2), nullable=True),
        sa.Column("rate", sa.Numeric(8, 4), nullable=True),
        sa.Column("equity_share", sa.Numeric(6, 4), nullable=True),
        sa.Column("metadata", JSONB_TYPE, nullable=False, server_default=sa.text("'{}'")),
    )
    op.create_index(
        "ix_fin_capital_stacks_project_id",
        "fin_capital_stacks",
        ["project_id"],
    )
    op.create_index(
        "ix_fin_capital_stacks_scenario_id",
        "fin_capital_stacks",
        ["scenario_id"],
    )
    op.create_index(
        "idx_fin_capital_stacks_project_name",
        "fin_capital_stacks",
        ["project_id", "name"],
    )

    op.create_table(
        "fin_results",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "project_id",
            sa.Integer(),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "scenario_id",
            sa.Integer(),
            sa.ForeignKey("fin_scenarios.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("value", sa.Numeric(16, 4), nullable=True),
        sa.Column("unit", sa.String(length=20), nullable=True),
        sa.Column("metadata", JSONB_TYPE, nullable=False, server_default=sa.text("'{}'")),
    )
    op.create_index("ix_fin_results_project_id", "fin_results", ["project_id"])
    op.create_index("ix_fin_results_scenario_id", "fin_results", ["scenario_id"])
    op.create_index(
        "idx_fin_results_project_name",
        "fin_results",
        ["project_id", "name"],
    )


def downgrade() -> None:
    """Revert the migration."""

    op.drop_index("idx_fin_results_project_name", table_name="fin_results")
    op.drop_index("ix_fin_results_scenario_id", table_name="fin_results")
    op.drop_index("ix_fin_results_project_id", table_name="fin_results")
    op.drop_table("fin_results")

    op.drop_index("idx_fin_capital_stacks_project_name", table_name="fin_capital_stacks")
    op.drop_index("ix_fin_capital_stacks_scenario_id", table_name="fin_capital_stacks")
    op.drop_index("ix_fin_capital_stacks_project_id", table_name="fin_capital_stacks")
    op.drop_table("fin_capital_stacks")

    op.drop_index("idx_fin_schedules_project_month", table_name="fin_schedules")
    op.drop_index("ix_fin_schedules_scenario_id", table_name="fin_schedules")
    op.drop_index("ix_fin_schedules_project_id", table_name="fin_schedules")
    op.drop_table("fin_schedules")

    op.drop_index("idx_fin_cost_items_project_name", table_name="fin_cost_items")
    op.drop_index("ix_fin_cost_items_scenario_id", table_name="fin_cost_items")
    op.drop_index("ix_fin_cost_items_project_id", table_name="fin_cost_items")
    op.drop_table("fin_cost_items")

    op.drop_index("idx_fin_scenarios_project_name", table_name="fin_scenarios")
    op.drop_index("ix_fin_scenarios_created_at", table_name="fin_scenarios")
    op.drop_index("ix_fin_scenarios_is_primary", table_name="fin_scenarios")
    op.drop_index("ix_fin_scenarios_fin_project_id", table_name="fin_scenarios")
    op.drop_index("ix_fin_scenarios_project_id", table_name="fin_scenarios")
    op.drop_table("fin_scenarios")

    op.drop_index("idx_fin_projects_project_name", table_name="fin_projects")
    op.drop_index("ix_fin_projects_created_at", table_name="fin_projects")
    op.drop_index("ix_fin_projects_project_id", table_name="fin_projects")
    op.drop_table("fin_projects")
