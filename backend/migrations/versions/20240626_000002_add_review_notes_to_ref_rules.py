"""Add review notes column to ref_rules."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20240626_000002"
down_revision = "20240115_000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply the migration."""

    op.execute("""
ALTER TABLE ref_rules
ADD COLUMN IF NOT EXISTS review_notes TEXT
""")


def downgrade() -> None:
    """Revert the migration."""

    op.execute("""
ALTER TABLE ref_rules
DROP COLUMN IF EXISTS review_notes
""")
