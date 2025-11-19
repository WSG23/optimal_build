"""drop_unused_propertytype_enum

Revision ID: 9e6cabd1ec16
Revises: 8706cd5fd7e5
Create Date: 2025-11-19 19:57:11.192882

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9e6cabd1ec16"
down_revision: Union[str, None] = "8706cd5fd7e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the unused 'propertytype' ENUM type (no underscore)
    # All tables use 'property_type' (with underscore) instead
    # This fixes SQLAlchemy type mismatch errors during inserts
    op.execute("DROP TYPE IF EXISTS propertytype CASCADE")


def downgrade() -> None:
    # Recreate the propertytype enum if needed (matches property_type values)
    op.execute(
        """
        CREATE TYPE propertytype AS ENUM (
            'office', 'retail', 'industrial', 'residential',
            'mixed_use', 'hotel', 'warehouse', 'land', 'special_purpose'
        )
    """
    )
