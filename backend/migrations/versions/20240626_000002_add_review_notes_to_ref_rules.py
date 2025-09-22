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

    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table("ref_rules"):
        columns = {col["name"] for col in inspector.get_columns("ref_rules")}
        if "review_notes" not in columns:
            op.add_column("ref_rules", sa.Column("review_notes", sa.Text(), nullable=True))


def downgrade() -> None:
    """Revert the migration."""

    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table("ref_rules"):
        columns = {col["name"] for col in inspector.get_columns("ref_rules")}
        if "review_notes" in columns:
            op.drop_column("ref_rules", "review_notes")
