"""Add inspector metadata to developer condition assessments.

Revision ID: 20251020_000016
Revises: 20251013_000015
Create Date: 2025-10-20

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20251020_000016"
down_revision = "20251013_000015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("developer_condition_assessments") as batch_op:
        batch_op.add_column(
            sa.Column("inspector_name", sa.String(length=120), nullable=True)
        )
        batch_op.add_column(
            sa.Column(
                "attachments",
                sa.JSON().with_variant(postgresql.JSONB(), "postgresql"),
                nullable=False,
                server_default=sa.text("'[]'"),
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("developer_condition_assessments") as batch_op:
        batch_op.drop_column("attachments")
        batch_op.drop_column("inspector_name")
