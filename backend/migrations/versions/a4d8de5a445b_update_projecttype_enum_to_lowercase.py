"""update_projecttype_enum_to_lowercase

Revision ID: a4d8de5a445b
Revises: 20251111_000024
Create Date: 2025-11-13 12:53:43.027483

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a4d8de5a445b"
down_revision: Union[str, None] = "20251111_000024"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Update projecttype enum values from uppercase to lowercase to match Python enum."""
    # Mapping of old (uppercase) to new (lowercase) values
    enum_mappings = {
        "NEW_DEVELOPMENT": "new_development",
        "REDEVELOPMENT": "redevelopment",
        "ADDITION_ALTERATION": "addition_alteration",
        "CONSERVATION": "conservation",
        "CHANGE_OF_USE": "change_of_use",
        "SUBDIVISION": "subdivision",
        "EN_BLOC": "en_bloc",
        "DEMOLITION": "demolition",
    }

    # Step 1: Add new lowercase enum values
    for new_value in enum_mappings.values():
        op.execute(f"ALTER TYPE projecttype ADD VALUE IF NOT EXISTS '{new_value}'")

    # Step 2: Update existing data to use lowercase values
    for old_value, new_value in enum_mappings.items():
        op.execute(
            f"UPDATE projects SET project_type = '{new_value}' "
            f"WHERE project_type = '{old_value}'"
        )

    # Note: Cannot remove old enum values in PostgreSQL without recreating the type
    # This is safe because we're adding new values and migrating data


def downgrade() -> None:
    """Revert projecttype enum values back to uppercase."""
    # Mapping of new (lowercase) to old (uppercase) values
    enum_mappings = {
        "new_development": "NEW_DEVELOPMENT",
        "redevelopment": "REDEVELOPMENT",
        "addition_alteration": "ADDITION_ALTERATION",
        "conservation": "CONSERVATION",
        "change_of_use": "CHANGE_OF_USE",
        "subdivision": "SUBDIVISION",
        "en_bloc": "EN_BLOC",
        "demolition": "DEMOLITION",
    }

    # Update existing data back to uppercase values
    for new_value, old_value in enum_mappings.items():
        op.execute(
            f"UPDATE projects SET project_type = '{old_value}' "
            f"WHERE project_type = '{new_value}'"
        )
