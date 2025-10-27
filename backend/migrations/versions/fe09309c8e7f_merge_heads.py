"""merge_heads

Revision ID: fe09309c8e7f
Revises: 4c8849dec050, 20251023_000018
Create Date: 2025-10-24 17:24:15.286097

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "fe09309c8e7f"
down_revision: Union[str, None] = ("4c8849dec050", "20251023_000018")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
