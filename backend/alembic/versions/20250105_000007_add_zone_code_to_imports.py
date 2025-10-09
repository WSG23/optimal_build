"""Add zone_code column to imports table.

Revision ID: 20250105_000007
Revises: 20241228_000006
Create Date: 2025-01-05 00:00:07
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20250105_000007"
down_revision = "20241228_000006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "imports", sa.Column("zone_code", sa.String(length=50), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("imports", "zone_code")
