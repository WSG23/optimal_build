"""add_last_active_at_to_team_members

Revision ID: 788e8741fa70
Revises: 20251230_000039
Create Date: 2026-01-07 18:47:51.814527

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "788e8741fa70"
down_revision: Union[str, None] = "20251230_000039"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "team_members",
        sa.Column("last_active_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("team_members", "last_active_at")
