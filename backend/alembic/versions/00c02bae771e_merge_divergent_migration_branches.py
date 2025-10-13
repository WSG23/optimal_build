"""Merge divergent migration branches

Revision ID: 00c02bae771e
Revises: 0773c87952ef, 20250105_000008
Create Date: 2025-10-12 21:24:48.745895

"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "00c02bae771e"
down_revision: Union[str, None] = ("0773c87952ef", "20250105_000008")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
