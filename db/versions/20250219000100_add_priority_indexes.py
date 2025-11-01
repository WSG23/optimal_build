"""Add high-priority composite indexes for Phase 2D audit."""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "20250219000100"
down_revision = "20250218000100"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "idx_property_planning_area",
        "properties",
        ["planning_area"],
        unique=False,
    )

    op.create_index(
        "ix_preview_jobs_property_status",
        "preview_jobs",
        ["property_id", "status"],
        unique=False,
    )
    op.create_index(
        "ix_preview_jobs_status_requested",
        "preview_jobs",
        ["status", "requested_at"],
        unique=False,
    )

    op.create_index(
        "ix_agent_deals_agent_status",
        "agent_deals",
        ["agent_id", "status"],
        unique=False,
    )
    op.create_index(
        "ix_agent_deals_agent_stage",
        "agent_deals",
        ["agent_id", "pipeline_stage"],
        unique=False,
    )
    op.create_index(
        "ix_agent_deals_project_status",
        "agent_deals",
        ["project_id", "status"],
        unique=False,
    )

    op.create_index(
        "idx_ent_roadmap_project_status",
        "ent_roadmap_items",
        ["project_id", "status"],
        unique=False,
    )
    op.create_index(
        "idx_ent_engagements_project_status",
        "ent_engagements",
        ["project_id", "status"],
        unique=False,
    )
    op.create_index(
        "idx_ent_legal_instruments_project_status",
        "ent_legal_instruments",
        ["project_id", "status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "idx_ent_legal_instruments_project_status",
        table_name="ent_legal_instruments",
    )
    op.drop_index("idx_ent_engagements_project_status", table_name="ent_engagements")
    op.drop_index("idx_ent_roadmap_project_status", table_name="ent_roadmap_items")

    op.drop_index("ix_agent_deals_project_status", table_name="agent_deals")
    op.drop_index("ix_agent_deals_agent_stage", table_name="agent_deals")
    op.drop_index("ix_agent_deals_agent_status", table_name="agent_deals")

    op.drop_index("ix_preview_jobs_status_requested", table_name="preview_jobs")
    op.drop_index("ix_preview_jobs_property_status", table_name="preview_jobs")

    op.drop_index("idx_property_planning_area", table_name="properties")
