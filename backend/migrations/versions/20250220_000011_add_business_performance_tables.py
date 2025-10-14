"""Add agent business performance tables for deal pipeline foundation."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20250220_000011"
down_revision = "20250220_000010"
branch_labels = None
depends_on = None


DEAL_ASSET_TYPE_ENUM = sa.Enum(
    "office",
    "retail",
    "industrial",
    "residential",
    "mixed_use",
    "hotel",
    "warehouse",
    "land",
    "special_purpose",
    "portfolio",
    name="deal_asset_type",
    create_type=False,
)

DEAL_TYPE_ENUM = sa.Enum(
    "buy_side",
    "sell_side",
    "lease",
    "management",
    "capital_raise",
    "other",
    name="deal_type",
    create_type=False,
)

PIPELINE_STAGE_ENUM = sa.Enum(
    "lead_captured",
    "qualification",
    "needs_analysis",
    "proposal",
    "negotiation",
    "agreement",
    "due_diligence",
    "awaiting_closure",
    "closed_won",
    "closed_lost",
    name="pipeline_stage",
    create_type=False,
)

DEAL_STATUS_ENUM = sa.Enum(
    "open",
    "closed_won",
    "closed_lost",
    "cancelled",
    name="deal_status",
    create_type=False,
)

DEAL_CONTACT_TYPE_ENUM = sa.Enum(
    "principal",
    "co_broke",
    "legal",
    "finance",
    "other",
    name="deal_contact_type",
    create_type=False,
)

DEAL_DOCUMENT_TYPE_ENUM = sa.Enum(
    "loi",
    "valuation",
    "agreement",
    "financials",
    "other",
    name="deal_document_type",
    create_type=False,
)


def upgrade() -> None:
    DEAL_ASSET_TYPE_ENUM.create(op.get_bind(), checkfirst=True)
    DEAL_TYPE_ENUM.create(op.get_bind(), checkfirst=True)
    PIPELINE_STAGE_ENUM.create(op.get_bind(), checkfirst=True)
    DEAL_STATUS_ENUM.create(op.get_bind(), checkfirst=True)
    DEAL_CONTACT_TYPE_ENUM.create(op.get_bind(), checkfirst=True)
    DEAL_DOCUMENT_TYPE_ENUM.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "agent_deals",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "agent_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "property_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("properties.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("asset_type", DEAL_ASSET_TYPE_ENUM, nullable=False),
        sa.Column("deal_type", DEAL_TYPE_ENUM, nullable=False),
        sa.Column(
            "pipeline_stage",
            PIPELINE_STAGE_ENUM,
            nullable=False,
            server_default="lead_captured",
        ),
        sa.Column(
            "status",
            DEAL_STATUS_ENUM,
            nullable=False,
            server_default="open",
        ),
        sa.Column("lead_source", sa.String(length=120), nullable=True),
        sa.Column("estimated_value_amount", sa.Numeric(16, 2), nullable=True),
        sa.Column(
            "estimated_value_currency",
            sa.String(length=3),
            nullable=False,
            server_default="SGD",
        ),
        sa.Column("expected_close_date", sa.Date(), nullable=True),
        sa.Column("actual_close_date", sa.Date(), nullable=True),
        sa.Column("confidence", sa.Numeric(5, 4), nullable=True),
        sa.Column(
            "metadata",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
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
        "ix_agent_deals_agent_stage",
        "agent_deals",
        ["agent_id", "pipeline_stage"],
    )
    op.create_index(
        "ix_agent_deals_status_created",
        "agent_deals",
        ["status", "created_at"],
    )
    op.create_index(
        "ix_agent_deals_project_id",
        "agent_deals",
        ["project_id"],
    )
    op.create_index(
        "ix_agent_deals_property_id",
        "agent_deals",
        ["property_id"],
    )

    op.create_table(
        "agent_deal_stage_events",
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
        sa.Column("from_stage", PIPELINE_STAGE_ENUM, nullable=True),
        sa.Column("to_stage", PIPELINE_STAGE_ENUM, nullable=False),
        sa.Column(
            "changed_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("note", sa.Text(), nullable=True),
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
    )
    op.create_index(
        "ix_agent_deal_stage_events_deal_id",
        "agent_deal_stage_events",
        ["deal_id"],
    )
    op.create_index(
        "ix_agent_deal_stage_events_stage_time",
        "agent_deal_stage_events",
        ["to_stage", "recorded_at"],
    )
    op.create_index(
        "ix_agent_deal_stage_events_changed_by",
        "agent_deal_stage_events",
        ["changed_by"],
    )

    op.create_table(
        "agent_deal_contacts",
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
        sa.Column("contact_type", DEAL_CONTACT_TYPE_ENUM, nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("company", sa.String(length=200), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "metadata",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
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
        "ix_agent_deal_contacts_deal_id",
        "agent_deal_contacts",
        ["deal_id"],
    )
    op.create_index(
        "ix_agent_deal_contacts_type",
        "agent_deal_contacts",
        ["contact_type"],
    )

    op.create_table(
        "agent_deal_documents",
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
        sa.Column("document_type", DEAL_DOCUMENT_TYPE_ENUM, nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("uri", sa.String(length=500), nullable=False),
        sa.Column("mime_type", sa.String(length=120), nullable=True),
        sa.Column(
            "uploaded_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "uploaded_at",
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
        sa.UniqueConstraint(
            "deal_id",
            "title",
            name="uq_agent_deal_document_title",
        ),
    )
    op.create_index(
        "ix_agent_deal_documents_deal_id",
        "agent_deal_documents",
        ["deal_id"],
    )
    op.create_index(
        "ix_agent_deal_documents_type",
        "agent_deal_documents",
        ["document_type"],
    )
    op.create_index(
        "ix_agent_deal_documents_uploaded_by",
        "agent_deal_documents",
        ["uploaded_by"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_agent_deal_documents_uploaded_by",
        table_name="agent_deal_documents",
        if_exists=True,
    )
    op.drop_index(
        "ix_agent_deal_documents_type",
        table_name="agent_deal_documents",
        if_exists=True,
    )
    op.drop_index(
        "ix_agent_deal_documents_deal_id",
        table_name="agent_deal_documents",
        if_exists=True,
    )
    op.drop_table("agent_deal_documents", if_exists=True)

    op.drop_index(
        "ix_agent_deal_contacts_type",
        table_name="agent_deal_contacts",
        if_exists=True,
    )
    op.drop_index(
        "ix_agent_deal_contacts_deal_id",
        table_name="agent_deal_contacts",
        if_exists=True,
    )
    op.drop_table("agent_deal_contacts", if_exists=True)

    op.drop_index(
        "ix_agent_deal_stage_events_changed_by",
        table_name="agent_deal_stage_events",
        if_exists=True,
    )
    op.drop_index(
        "ix_agent_deal_stage_events_stage_time",
        table_name="agent_deal_stage_events",
        if_exists=True,
    )
    op.drop_index(
        "ix_agent_deal_stage_events_deal_id",
        table_name="agent_deal_stage_events",
        if_exists=True,
    )
    op.drop_table("agent_deal_stage_events", if_exists=True)

    op.drop_index(
        "ix_agent_deals_property_id",
        table_name="agent_deals",
        if_exists=True,
    )
    op.drop_index(
        "ix_agent_deals_project_id",
        table_name="agent_deals",
        if_exists=True,
    )
    op.drop_index(
        "ix_agent_deals_status_created",
        table_name="agent_deals",
        if_exists=True,
    )
    op.drop_index(
        "ix_agent_deals_agent_stage",
        table_name="agent_deals",
        if_exists=True,
    )
    op.drop_table("agent_deals", if_exists=True)

    DEAL_DOCUMENT_TYPE_ENUM.drop(op.get_bind(), checkfirst=True)
    DEAL_CONTACT_TYPE_ENUM.drop(op.get_bind(), checkfirst=True)
    DEAL_STATUS_ENUM.drop(op.get_bind(), checkfirst=True)
    PIPELINE_STAGE_ENUM.drop(op.get_bind(), checkfirst=True)
    DEAL_TYPE_ENUM.drop(op.get_bind(), checkfirst=True)
    DEAL_ASSET_TYPE_ENUM.drop(op.get_bind(), checkfirst=True)
