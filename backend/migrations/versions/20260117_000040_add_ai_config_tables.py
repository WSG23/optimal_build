"""add ai_config tables

Revision ID: 20260117_000040
Revises: 8f91023abcdd
Create Date: 2026-01-17

Stores configurable AI parameters previously hardcoded in service modules.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260117_000040"
down_revision = "8f91023abcdd"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create ai_configs table
    op.create_table(
        "ai_configs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("config_key", sa.String(200), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("config_value", postgresql.JSON(), nullable=False),
        sa.Column("value_type", sa.String(50), nullable=False, server_default="object"),
        sa.Column("validation_schema", postgresql.JSON(), nullable=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("version", sa.String(20), nullable=False, server_default="1.0.0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
    )

    # Create indexes for ai_configs
    op.create_index("ix_ai_configs_category", "ai_configs", ["category"])
    op.create_index("ix_ai_configs_organization_id", "ai_configs", ["organization_id"])

    # Create unique constraint
    op.create_unique_constraint(
        "uq_ai_config_category_key_org",
        "ai_configs",
        ["category", "config_key", "organization_id"],
    )

    # Create foreign keys for ai_configs
    op.create_foreign_key(
        "fk_ai_configs_organization_id",
        "ai_configs",
        "teams",
        ["organization_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_ai_configs_created_by",
        "ai_configs",
        "users",
        ["created_by"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_ai_configs_updated_by",
        "ai_configs",
        "users",
        ["updated_by"],
        ["id"],
        ondelete="SET NULL",
    )

    # Create ai_config_audits table
    op.create_table(
        "ai_config_audits",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("config_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("previous_value", postgresql.JSON(), nullable=True),
        sa.Column("new_value", postgresql.JSON(), nullable=True),
        sa.Column("change_reason", sa.Text(), nullable=True),
        sa.Column("changed_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "changed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    # Create indexes for ai_config_audits
    op.create_index("ix_ai_config_audits_config_id", "ai_config_audits", ["config_id"])
    op.create_index("ix_ai_config_audits_changed_at", "ai_config_audits", ["changed_at"])

    # Create foreign keys for ai_config_audits
    op.create_foreign_key(
        "fk_ai_config_audits_config_id",
        "ai_config_audits",
        "ai_configs",
        ["config_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_ai_config_audits_changed_by",
        "ai_config_audits",
        "users",
        ["changed_by"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    # Drop ai_config_audits table
    op.drop_constraint(
        "fk_ai_config_audits_changed_by", "ai_config_audits", type_="foreignkey"
    )
    op.drop_constraint(
        "fk_ai_config_audits_config_id", "ai_config_audits", type_="foreignkey"
    )
    op.drop_index("ix_ai_config_audits_changed_at", "ai_config_audits")
    op.drop_index("ix_ai_config_audits_config_id", "ai_config_audits")
    op.drop_table("ai_config_audits")

    # Drop ai_configs table
    op.drop_constraint("fk_ai_configs_updated_by", "ai_configs", type_="foreignkey")
    op.drop_constraint("fk_ai_configs_created_by", "ai_configs", type_="foreignkey")
    op.drop_constraint(
        "fk_ai_configs_organization_id", "ai_configs", type_="foreignkey"
    )
    op.drop_constraint("uq_ai_config_category_key_org", "ai_configs", type_="unique")
    op.drop_index("ix_ai_configs_organization_id", "ai_configs")
    op.drop_index("ix_ai_configs_category", "ai_configs")
    op.drop_table("ai_configs")
