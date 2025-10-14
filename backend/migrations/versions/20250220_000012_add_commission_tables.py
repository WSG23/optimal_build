"""Add commission ledger tables for agent performance."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20250220_000012"
down_revision = "20250220_000011"
branch_labels = None
depends_on = None


COMMISSION_TYPE_ENUM = sa.Enum(
    "introducer",
    "exclusive",
    "co_broke",
    "referral",
    "bonus",
    name="commission_type",
    create_type=False,
)

COMMISSION_STATUS_ENUM = sa.Enum(
    "pending",
    "confirmed",
    "invoiced",
    "paid",
    "disputed",
    "written_off",
    name="commission_status",
    create_type=False,
)

COMMISSION_ADJUSTMENT_TYPE_ENUM = sa.Enum(
    "clawback",
    "bonus",
    "correction",
    name="commission_adjustment_type",
    create_type=False,
)


def upgrade() -> None:
    COMMISSION_TYPE_ENUM.create(op.get_bind(), checkfirst=True)
    COMMISSION_STATUS_ENUM.create(op.get_bind(), checkfirst=True)
    COMMISSION_ADJUSTMENT_TYPE_ENUM.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "agent_commission_records",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "deal_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("agent_deals.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "agent_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("commission_type", COMMISSION_TYPE_ENUM, nullable=False),
        sa.Column(
            "status",
            COMMISSION_STATUS_ENUM,
            nullable=False,
            server_default="pending",
        ),
        sa.Column("basis_amount", sa.Numeric(16, 2), nullable=True),
        sa.Column(
            "basis_currency",
            sa.String(length=3),
            nullable=False,
            server_default="SGD",
        ),
        sa.Column("commission_rate", sa.Numeric(5, 4), nullable=True),
        sa.Column("commission_amount", sa.Numeric(16, 2), nullable=True),
        sa.Column("introduced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("invoiced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("disputed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "metadata",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "audit_log_id",
            sa.Integer,
            sa.ForeignKey("audit_logs.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "deal_id",
            "agent_id",
            "commission_type",
            name="uq_agent_commission_unique_type",
        ),
    )
    op.create_index(
        "ix_agent_commission_records_deal_status",
        "agent_commission_records",
        ["deal_id", "status"],
    )
    op.create_index(
        "ix_agent_commission_records_agent_status",
        "agent_commission_records",
        ["agent_id", "status"],
    )

    op.create_table(
        "agent_commission_adjustments",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "commission_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("agent_commission_records.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "adjustment_type",
            COMMISSION_ADJUSTMENT_TYPE_ENUM,
            nullable=False,
        ),
        sa.Column("amount", sa.Numeric(16, 2), nullable=True),
        sa.Column(
            "currency",
            sa.String(length=3),
            nullable=False,
            server_default="SGD",
        ),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column(
            "recorded_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "recorded_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "metadata",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "audit_log_id",
            sa.Integer,
            sa.ForeignKey("audit_logs.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_agent_commission_adjustments_type",
        "agent_commission_adjustments",
        ["adjustment_type"],
    )
    op.create_index(
        "ix_agent_commission_adjustments_recorded_at",
        "agent_commission_adjustments",
        ["recorded_at"],
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if "agent_commission_adjustments" in inspector.get_table_names():
        op.drop_index(
            "ix_agent_commission_adjustments_recorded_at",
            table_name="agent_commission_adjustments",
            if_exists=True,
        )
        op.drop_index(
            "ix_agent_commission_adjustments_type",
            table_name="agent_commission_adjustments",
            if_exists=True,
        )
        op.drop_table("agent_commission_adjustments", if_exists=True)

    if "agent_commission_records" in inspector.get_table_names():
        op.drop_index(
            "ix_agent_commission_records_agent_status",
            table_name="agent_commission_records",
            if_exists=True,
        )
        op.drop_index(
            "ix_agent_commission_records_deal_status",
            table_name="agent_commission_records",
            if_exists=True,
        )
        op.drop_table("agent_commission_records", if_exists=True)

    COMMISSION_ADJUSTMENT_TYPE_ENUM.drop(op.get_bind(), checkfirst=True)
    COMMISSION_STATUS_ENUM.drop(op.get_bind(), checkfirst=True)
    COMMISSION_TYPE_ENUM.drop(op.get_bind(), checkfirst=True)
