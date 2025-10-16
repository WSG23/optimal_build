"""Add metric_overrides to imports.

Revision ID: 20250105_000008
Revises: 20250105_000007
Create Date: 2025-01-05 00:15:00
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = "20250105_000008"
down_revision = "20250105_000007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("imports", sa.Column("metric_overrides", sa.JSON(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    column_names = {column["name"] for column in inspector.get_columns("imports")}
    if "metric_overrides" in column_names:
        with op.batch_alter_table("imports") as batch_op:
            batch_op.drop_column("metric_overrides")
