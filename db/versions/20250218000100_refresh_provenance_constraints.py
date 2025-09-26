"""Refresh provenance dedupe constraints."""
from __future__ import annotations

from alembic import op


# revision identifiers, used by Alembic.
revision = "20250218000100"
down_revision = "20250217000100"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint(
        "uq_provenance_reg_source_checksum",
        "provenance",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_provenance_reg_source_checksum_v2",
        "provenance",
        ["regulation_id", "source_uri", "content_checksum"],
    )
    op.create_index(
        "ix_provenance_regulation_source",
        "provenance",
        ["regulation_id", "source_uri"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_provenance_regulation_source", table_name="provenance")
    op.drop_constraint(
        "uq_provenance_reg_source_checksum_v2",
        "provenance",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_provenance_reg_source_checksum",
        "provenance",
        ["regulation_id", "source_uri", "content_checksum"],
    )
