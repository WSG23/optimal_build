"""merge_hk_jurisdiction_heads

Revision ID: 8706cd5fd7e5
Revises: 1c64fb33855c, 20251118_000025
Create Date: 2025-11-19 19:29:55.509977

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8706cd5fd7e5"
down_revision: Union[str, None] = ("1c64fb33855c", "20251118_000025")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
