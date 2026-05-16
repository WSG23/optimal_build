"""alter deal_outcomes.recorded_by to nullable with SET NULL

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-04-17 09:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Make recorded_by nullable so users can be deleted without losing audit records
    op.alter_column(
        "deal_outcomes",
        "recorded_by",
        existing_type=sa.CHAR(36),
        nullable=True,
    )

    # Drop the existing CASCADE FK and replace with SET NULL
    op.execute(
        "ALTER TABLE IF EXISTS deal_outcomes "
        "DROP CONSTRAINT IF EXISTS fk_deal_outcomes_recorded_by"
    )
    op.create_foreign_key(
        "fk_deal_outcomes_recorded_by",
        "deal_outcomes",
        "users",
        ["recorded_by"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE IF EXISTS deal_outcomes "
        "DROP CONSTRAINT IF EXISTS fk_deal_outcomes_recorded_by"
    )
    op.create_foreign_key(
        "fk_deal_outcomes_recorded_by",
        "deal_outcomes",
        "users",
        ["recorded_by"],
        ["id"],
        ondelete="CASCADE",
    )
    op.alter_column(
        "deal_outcomes",
        "recorded_by",
        existing_type=sa.CHAR(36),
        nullable=False,
    )
