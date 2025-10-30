"""Add privacy flag to finance scenarios."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20251023_000018"
down_revision = "20251022_000017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "fin_scenarios",
        sa.Column(
            "is_private",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.create_index(
        "ix_fin_scenarios_is_private",
        "fin_scenarios",
        ["is_private"],
    )
    op.alter_column(
        "fin_scenarios",
        "is_private",
        server_default=None,
    )


def downgrade() -> None:
    with op.batch_alter_table("fin_scenarios", schema=None) as batch_op:
        batch_op.drop_index("ix_fin_scenarios_is_private")
        batch_op.drop_column("is_private")
