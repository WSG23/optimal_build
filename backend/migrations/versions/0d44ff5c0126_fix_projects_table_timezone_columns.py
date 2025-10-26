"""fix projects table timezone columns

Revision ID: 0d44ff5c0126
Revises: 20251026_000019
Create Date: 2025-10-26 12:57:39.493514

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0d44ff5c0126"
down_revision: Union[str, None] = "20251026_000019"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Convert created_at and updated_at to TIMESTAMP WITH TIME ZONE."""
    # ALTER COLUMN to add timezone information
    op.execute(
        "ALTER TABLE projects ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE USING created_at AT TIME ZONE 'UTC'"
    )
    op.execute(
        "ALTER TABLE projects ALTER COLUMN updated_at TYPE TIMESTAMP WITH TIME ZONE USING updated_at AT TIME ZONE 'UTC'"
    )


def downgrade() -> None:
    """Convert created_at and updated_at back to TIMESTAMP WITHOUT TIME ZONE."""
    op.execute(
        "ALTER TABLE projects ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE"
    )
    op.execute(
        "ALTER TABLE projects ALTER COLUMN updated_at TYPE TIMESTAMP WITHOUT TIME ZONE"
    )
