"""Add metric_overrides to imports.

Revision ID: 20250105_000008
Revises: 20250105_000007
Create Date: 2025-01-05 00:15:00
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20250105_000008"
down_revision = "20250105_000007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("imports", sa.Column("metric_overrides", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("imports", "metric_overrides")
