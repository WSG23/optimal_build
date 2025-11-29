"""add_timezone_to_voice_notes_capture_date

Revision ID: f64ee42f9736
Revises: 4f0afb00724b
Create Date: 2025-11-29 09:16:25.692745

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "f64ee42f9736"
down_revision: Union[str, None] = "4f0afb00724b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Alter capture_date column to TIMESTAMP WITH TIME ZONE
    op.execute(
        "ALTER TABLE property_voice_notes "
        "ALTER COLUMN capture_date TYPE TIMESTAMP WITH TIME ZONE "
        "USING capture_date AT TIME ZONE 'UTC'"
    )


def downgrade() -> None:
    # Revert to TIMESTAMP WITHOUT TIME ZONE
    op.execute(
        "ALTER TABLE IF EXISTS property_voice_notes "
        "ALTER COLUMN capture_date TYPE TIMESTAMP WITHOUT TIME ZONE"
    )
