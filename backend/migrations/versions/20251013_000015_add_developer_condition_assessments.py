"""Add developer condition assessment tables.

Revision ID: 20251013_000015
Revises: 20251013_000014
Create Date: 2025-10-13

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20251013_000015"
down_revision = "20251013_000014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "developer_condition_assessments",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "property_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("scenario", sa.String(length=50), nullable=True),
        sa.Column("overall_rating", sa.String(length=10), nullable=False),
        sa.Column("overall_score", sa.Integer(), nullable=False),
        sa.Column("risk_level", sa.String(length=20), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("scenario_context", sa.Text(), nullable=True),
        sa.Column(
            "systems",
            sa.JSON().with_variant(postgresql.JSONB(), "postgresql"),
            nullable=False,
            server_default=sa.text("'[]'"),
        ),
        sa.Column(
            "recommended_actions",
            sa.JSON().with_variant(postgresql.JSONB(), "postgresql"),
            nullable=False,
            server_default=sa.text("'[]'"),
        ),
        sa.Column("recorded_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "recorded_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
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
        ),
        sa.ForeignKeyConstraint(
            ["recorded_by"],
            ["users.id"],
            ondelete="SET NULL",
        ),
    )

    op.create_index(
        "ix_developer_condition_assessments_property",
        "developer_condition_assessments",
        ["property_id"],
    )
    op.create_index(
        "ix_developer_condition_assessments_scenario",
        "developer_condition_assessments",
        ["scenario"],
    )
    op.create_index(
        "ix_developer_condition_assessments_recorded_at",
        "developer_condition_assessments",
        ["recorded_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_developer_condition_assessments_recorded_at",
        table_name="developer_condition_assessments",
    )
    op.drop_index(
        "ix_developer_condition_assessments_scenario",
        table_name="developer_condition_assessments",
    )
    op.drop_index(
        "ix_developer_condition_assessments_property",
        table_name="developer_condition_assessments",
    )
    op.drop_table("developer_condition_assessments")
