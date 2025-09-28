"""Add checksum-based dedupe constraint for provenance."""

from __future__ import annotations

import hashlib

from alembic import op

import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20250217000100"
down_revision = "20250216000000"
branch_labels = None
depends_on = None


def _compute_checksum(raw_content: str) -> str:
    return hashlib.sha256(raw_content.encode("utf-8")).hexdigest()


def upgrade() -> None:
    op.add_column(
        "provenance",
        sa.Column("content_checksum", sa.String(length=64), nullable=True),
    )

    bind = op.get_bind()
    metadata = sa.MetaData()
    provenance = sa.Table("provenance", metadata, autoload_with=bind)

    rows = bind.execute(sa.select(provenance.c.id, provenance.c.raw_content)).fetchall()
    for row in rows:
        checksum = _compute_checksum(row.raw_content)
        bind.execute(
            provenance.update()
            .where(provenance.c.id == row.id)
            .values(content_checksum=checksum)
        )

    op.alter_column(
        "provenance",
        "content_checksum",
        existing_type=sa.String(length=64),
        nullable=False,
    )
    op.create_unique_constraint(
        "uq_provenance_reg_source_checksum",
        "provenance",
        ["regulation_id", "source_uri", "content_checksum"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_provenance_reg_source_checksum", "provenance", type_="unique"
    )
    op.drop_column("provenance", "content_checksum")
