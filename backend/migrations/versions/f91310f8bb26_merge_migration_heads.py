"""merge_migration_heads

Revision ID: f91310f8bb26
Revises: 0d44ff5c0126, 20251028_000020
Create Date: 2025-10-31 08:25:48.623518

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f91310f8bb26"
down_revision: Union[str, None] = ("0d44ff5c0126", "20251028_000020")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
