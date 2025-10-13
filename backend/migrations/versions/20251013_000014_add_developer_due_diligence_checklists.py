"""Add developer due diligence checklist tables.

Revision ID: 20251013_000014
Revises: 20250220_000013
Create Date: 2025-10-13

"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20251013_000014"
down_revision = "20250220_000013"
branch_labels = None
depends_on = None


CHECKLIST_CATEGORY_ENUM = sa.Enum(
    "title_verification",
    "zoning_compliance",
    "environmental_assessment",
    "structural_survey",
    "heritage_constraints",
    "utility_capacity",
    "access_rights",
    name="checklist_category",
    create_type=False,
)

CHECKLIST_STATUS_ENUM = sa.Enum(
    "pending",
    "in_progress",
    "completed",
    "not_applicable",
    name="checklist_status",
    create_type=False,
)

CHECKLIST_PRIORITY_ENUM = sa.Enum(
    "critical",
    "high",
    "medium",
    "low",
    name="checklist_priority",
    create_type=False,
)


def upgrade() -> None:
    """Create due diligence checklist tables."""
    # Create ENUMs
    CHECKLIST_CATEGORY_ENUM.create(op.get_bind(), checkfirst=True)
    CHECKLIST_STATUS_ENUM.create(op.get_bind(), checkfirst=True)
    CHECKLIST_PRIORITY_ENUM.create(op.get_bind(), checkfirst=True)

    # Checklist Templates table
    # Stores predefined checklist items for each development scenario
    op.create_table(
        "developer_checklist_templates",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "development_scenario",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column("category", CHECKLIST_CATEGORY_ENUM, nullable=False),
        sa.Column("item_title", sa.String(length=255), nullable=False),
        sa.Column("item_description", sa.Text(), nullable=True),
        sa.Column("priority", CHECKLIST_PRIORITY_ENUM, nullable=False),
        sa.Column("typical_duration_days", sa.Integer, nullable=True),
        sa.Column("requires_professional", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("professional_type", sa.String(length=100), nullable=True),
        sa.Column("display_order", sa.Integer, nullable=False, server_default="0"),
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

    # Create indexes for templates
    op.create_index(
        "ix_developer_checklist_templates_scenario_category",
        "developer_checklist_templates",
        ["development_scenario", "category"],
    )

    # Property Checklists table
    # Stores checklist items for specific properties
    op.create_table(
        "developer_property_checklists",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column(
            "property_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "template_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("developer_checklist_templates.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "development_scenario",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column("category", CHECKLIST_CATEGORY_ENUM, nullable=False),
        sa.Column("item_title", sa.String(length=255), nullable=False),
        sa.Column("item_description", sa.Text(), nullable=True),
        sa.Column("priority", CHECKLIST_PRIORITY_ENUM, nullable=False),
        sa.Column("status", CHECKLIST_STATUS_ENUM, nullable=False, server_default="pending"),
        sa.Column(
            "assigned_to",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("completed_date", sa.Date(), nullable=True),
        sa.Column(
            "completed_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
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

    # Create indexes for property checklists
    op.create_index(
        "ix_developer_property_checklists_property",
        "developer_property_checklists",
        ["property_id"],
    )
    op.create_index(
        "ix_developer_property_checklists_status",
        "developer_property_checklists",
        ["status"],
    )
    op.create_index(
        "ix_developer_property_checklists_property_scenario",
        "developer_property_checklists",
        ["property_id", "development_scenario"],
    )


def downgrade() -> None:
    """Drop due diligence checklist tables."""
    # Drop indexes
    op.drop_index(
        "ix_developer_property_checklists_property_scenario",
        table_name="developer_property_checklists",
        if_exists=True,
    )
    op.drop_index(
        "ix_developer_property_checklists_status",
        table_name="developer_property_checklists",
        if_exists=True,
    )
    op.drop_index(
        "ix_developer_property_checklists_property",
        table_name="developer_property_checklists",
        if_exists=True,
    )

    op.drop_index(
        "ix_developer_checklist_templates_scenario_category",
        table_name="developer_checklist_templates",
        if_exists=True,
    )

    # Drop tables
    op.drop_table("developer_property_checklists", if_exists=True)
    op.drop_table("developer_checklist_templates", if_exists=True)

    # Drop ENUMs
    CHECKLIST_PRIORITY_ENUM.drop(op.get_bind(), checkfirst=True)
    CHECKLIST_STATUS_ENUM.drop(op.get_bind(), checkfirst=True)
    CHECKLIST_CATEGORY_ENUM.drop(op.get_bind(), checkfirst=True)
