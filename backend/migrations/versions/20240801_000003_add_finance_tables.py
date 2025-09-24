"""Create finance modelling tables."""

from __future__ import annotations

from alembic import op
from sqlalchemy.dialects import postgresql

import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20240801_000003"
down_revision = "20240626_000002"
branch_labels = None
depends_on = None


JSONB_TYPE = postgresql.JSONB(astext_type=sa.Text())


def upgrade() -> None:
    """Apply the migration."""
    # Ensure a minimal 'projects' table exists so our FKs don't fail in fresh dev DBs.
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'projects'
            ) THEN
                CREATE TABLE projects (
                    id SERIAL PRIMARY KEY
                );
            END IF;
        END$$;
        """
    )

    # fin_projects
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
        sa.Column(
            "metadata", JSONB_TYPE, nullable=False, server_default=sa.text("'{}'")
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
    op.create_index("ix_fin_projects_project_id", "fin_projects", ["project_id"])
    op.create_index("ix_fin_projects_created_at", "fin_projects", ["created_at"])
    op.create_index(
        "idx_fin_projects_project_name",
        "fin_projects",
        ["project_id", "name"],
    )

    # fin_scenarios
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
    op.create_index(
        "ix_fin_scenarios_fin_project_id", "fin_scenarios", ["fin_project_id"]
    )
    op.create_index("ix_fin_scenarios_is_primary", "fin_scenarios", ["is_primary"])


def downgrade() -> None:
    # Drop in reverse order of dependencies
    op.execute("DROP INDEX IF EXISTS ix_fin_scenarios_is_primary")
    op.execute("DROP INDEX IF EXISTS ix_fin_scenarios_fin_project_id")
    op.execute("DROP INDEX IF EXISTS ix_fin_scenarios_project_id")
    op.execute("DROP TABLE IF EXISTS fin_scenarios CASCADE")

    op.execute("DROP INDEX IF EXISTS idx_fin_projects_project_name")
    op.execute("DROP INDEX IF EXISTS ix_fin_projects_created_at")
    op.execute("DROP INDEX IF EXISTS ix_fin_projects_project_id")
    op.execute("DROP TABLE IF EXISTS fin_projects CASCADE")
