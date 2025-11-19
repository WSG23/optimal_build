"""Add jurisdiction_code column to properties."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20251118_000025"
down_revision = "20251111_000024"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "properties",
        sa.Column(
            "jurisdiction_code",
            sa.String(length=10),
            nullable=False,
            server_default="SG",
        ),
    )
    op.create_index(
        "ix_properties_jurisdiction_code",
        "properties",
        ["jurisdiction_code"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_properties_jurisdiction_code", table_name="properties")
    op.drop_column("properties", "jurisdiction_code")
