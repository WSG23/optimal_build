"""merge ref_building_footprints + deal_outcomes_recorded_by

Revision ID: 069afe97c108
Revises: 20260507_000041, b2c3d4e5f6a7
Create Date: 2026-05-17 21:59:50.813671

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "069afe97c108"
down_revision: Union[str, None] = ("20260507_000041", "b2c3d4e5f6a7")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
