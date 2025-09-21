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

    op.add_column("ref_rules", sa.Column("review_notes", sa.Text(), nullable=True))


def downgrade() -> None:
    """Revert the migration."""

    op.drop_column("ref_rules", "review_notes")
