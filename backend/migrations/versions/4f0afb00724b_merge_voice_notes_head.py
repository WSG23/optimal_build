"""merge_voice_notes_head

Revision ID: 4f0afb00724b
Revises: 20251129_000026, 9e6cabd1ec16
Create Date: 2025-11-29 09:04:54.734599

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4f0afb00724b"
down_revision: Union[str, None] = ("20251129_000026", "9e6cabd1ec16")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
