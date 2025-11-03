"""add requires_professional to developer property checklists

Revision ID: 20251104_000023
Revises: 20251104_000022
Create Date: 2025-11-04 12:30:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20251104_000023"
down_revision: Union[str, None] = "20251104_000022"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "developer_property_checklists",
        sa.Column(
            "requires_professional",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "developer_property_checklists",
        sa.Column("professional_type", sa.String(length=100), nullable=True),
    )
    op.execute(
        """
        UPDATE developer_property_checklists
        SET requires_professional = COALESCE((metadata ->> 'requires_professional')::boolean, false),
            professional_type = COALESCE(metadata ->> 'professional_type', professional_type)
        """
    )
    op.alter_column(
        "developer_property_checklists",
        "requires_professional",
        server_default=None,
    )


def downgrade() -> None:
    with op.batch_alter_table("developer_property_checklists") as batch_op:
        try:
            batch_op.drop_column("professional_type")
        except Exception:
            pass
        try:
            batch_op.drop_column("requires_professional")
        except Exception:
            pass
