"""Initial schema for Regstack."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20250216000000"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "jurisdictions",
        sa.Column("code", sa.String(length=50), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "regulations",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("jurisdiction_code", sa.String(length=50), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("issued_on", sa.Date(), nullable=True),
        sa.Column("effective_on", sa.Date(), nullable=True),
        sa.Column("version", sa.String(length=50), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("global_tags", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(
            ["jurisdiction_code"], ["jurisdictions.code"], ondelete="CASCADE"
        ),
        sa.UniqueConstraint("jurisdiction_code", "external_id", name="uq_reg_external"),
    )

    op.create_table(
        "reg_mappings",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("regulation_id", sa.Integer, nullable=False),
        sa.Column("mapping_type", sa.String(length=100), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(
            ["regulation_id"], ["regulations.id"], ondelete="CASCADE"
        ),
    )

    op.create_table(
        "provenance",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("regulation_id", sa.Integer, nullable=False),
        sa.Column("source_uri", sa.String(length=1024), nullable=False),
        sa.Column(
            "fetched_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("fetch_parameters", sa.JSON(), nullable=False),
        sa.Column("raw_content", sa.Text, nullable=False),
        sa.ForeignKeyConstraint(
            ["regulation_id"], ["regulations.id"], ondelete="CASCADE"
        ),
    )

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.create_index(
            "ix_regulations_global_tags",
            "regulations",
            [sa.text("global_tags")],
            postgresql_using="gin",
        )
        op.create_index(
            "ix_reg_mappings_payload",
            "reg_mappings",
            [sa.text("payload")],
            postgresql_using="gin",
        )
    else:
        op.create_index("ix_regulations_global_tags", "regulations", ["global_tags"])
        op.create_index("ix_reg_mappings_payload", "reg_mappings", ["payload"])

    op.create_index("ix_provenance_source", "provenance", ["source_uri"])


def downgrade() -> None:
    op.drop_index("ix_provenance_source", table_name="provenance")
    op.drop_table("provenance")
    op.drop_index("ix_reg_mappings_payload", table_name="reg_mappings")
    op.drop_table("reg_mappings")
    op.drop_index("ix_regulations_global_tags", table_name="regulations")
    op.drop_table("regulations")
    op.drop_table("jurisdictions")
