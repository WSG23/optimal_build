"""change_required_role_to_string

Revision ID: 8f91023abcdd
Revises: d9412310ba89
Create Date: 2026-01-09 12:26:59.611248

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8f91023abcdd"
down_revision: Union[str, None] = "d9412310ba89"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Change required_role from UserRole enum to String(50)
    # This avoids enum value case mismatch issues between Python (lowercase) and DB (uppercase)
    op.alter_column(
        "approval_steps",
        "required_role",
        type_=sa.String(50),
        existing_type=sa.Enum(
            "admin",
            "developer",
            "investor",
            "contractor",
            "consultant",
            "regulatory_officer",
            "viewer",
            name="userrole",
            create_type=False,
        ),
        existing_nullable=True,
        postgresql_using="required_role::text",
    )


def downgrade() -> None:
    # Revert back to enum type (note: this may fail if values don't match enum)
    op.alter_column(
        "approval_steps",
        "required_role",
        type_=sa.Enum(
            "admin",
            "developer",
            "investor",
            "contractor",
            "consultant",
            "regulatory_officer",
            "viewer",
            name="userrole",
            create_type=False,
        ),
        existing_type=sa.String(50),
        existing_nullable=True,
        postgresql_using="required_role::userrole",
    )
