"""Link GPS-captured properties to projects.

Revision ID: 20251230_000039
Revises: 20251208_000038
Create Date: 2025-12-30
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20251230_000039"
down_revision = "20251208_000038"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "properties",
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "properties",
        sa.Column("owner_email", sa.String(length=255), nullable=True),
    )
    op.create_index(
        "ix_properties_project_id",
        "properties",
        ["project_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_properties_project_id_projects",
        "properties",
        "projects",
        ["project_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_properties_project_id_projects",
        "properties",
        type_="foreignkey",
    )
    op.drop_index("ix_properties_project_id", table_name="properties")
    op.drop_column("properties", "owner_email")
    op.drop_column("properties", "project_id")
