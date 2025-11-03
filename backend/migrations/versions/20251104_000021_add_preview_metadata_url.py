"""add_preview_metadata_url

Revision ID: 20251104_000021
Revises: ff3f1bcb3551
Create Date: 2025-11-04 18:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20251104_000021"
down_revision: Union[str, None] = "ff3f1bcb3551"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "preview_jobs",
        sa.Column("metadata_url", sa.String(length=500), nullable=True),
    )


def downgrade() -> None:
    from sqlalchemy import inspect

    bind = op.get_bind()
    inspector = inspect(bind)
    column_names = {column["name"] for column in inspector.get_columns("preview_jobs")}
    if "metadata_url" in column_names:
        with op.batch_alter_table("preview_jobs") as batch_op:
            batch_op.drop_column("metadata_url")
