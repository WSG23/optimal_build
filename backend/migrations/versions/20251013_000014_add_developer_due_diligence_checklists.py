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


def upgrade() -> None:
    """Create due diligence checklist tables."""
    # Create ENUMs using raw SQL to avoid SQLAlchemy auto-creation issues with asyncpg
    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'checklist_category') THEN
                    CREATE TYPE checklist_category AS ENUM (
                        'title_verification',
                        'zoning_compliance',
                        'environmental_assessment',
                        'structural_survey',
                        'heritage_constraints',
                        'utility_capacity',
                        'access_rights'
                    );
                END IF;
            END $$;
            """
        )
    )
    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'checklist_status') THEN
                    CREATE TYPE checklist_status AS ENUM (
                        'pending',
                        'in_progress',
                        'completed',
                        'not_applicable'
                    );
                END IF;
            END $$;
            """
        )
    )
    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'checklist_priority') THEN
                    CREATE TYPE checklist_priority AS ENUM (
                        'critical',
                        'high',
                        'medium',
                        'low'
                    );
                END IF;
            END $$;
            """
        )
    )

    # Checklist Templates table using raw SQL
    op.execute(
        sa.text(
            """
            CREATE TABLE developer_checklist_templates (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                development_scenario VARCHAR(50) NOT NULL,
                category checklist_category NOT NULL,
                item_title VARCHAR(255) NOT NULL,
                item_description TEXT,
                priority checklist_priority NOT NULL,
                typical_duration_days INTEGER,
                requires_professional BOOLEAN NOT NULL DEFAULT false,
                professional_type VARCHAR(100),
                display_order INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
            )
            """
        )
    )

    # Create indexes for templates
    op.execute(
        sa.text(
            "CREATE INDEX ix_developer_checklist_templates_scenario_category ON developer_checklist_templates (development_scenario, category)"
        )
    )

    # Property Checklists table using raw SQL
    op.execute(
        sa.text(
            """
            CREATE TABLE developer_property_checklists (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                property_id UUID NOT NULL,
                template_id UUID REFERENCES developer_checklist_templates(id) ON DELETE SET NULL,
                development_scenario VARCHAR(50) NOT NULL,
                category checklist_category NOT NULL,
                item_title VARCHAR(255) NOT NULL,
                item_description TEXT,
                priority checklist_priority NOT NULL,
                status checklist_status NOT NULL DEFAULT 'pending',
                assigned_to UUID REFERENCES users(id) ON DELETE SET NULL,
                due_date DATE,
                completed_date DATE,
                completed_by UUID REFERENCES users(id) ON DELETE SET NULL,
                notes TEXT,
                metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
            )
            """
        )
    )

    # Create indexes for property checklists
    op.execute(
        sa.text(
            "CREATE INDEX ix_developer_property_checklists_property ON developer_property_checklists (property_id)"
        )
    )
    op.execute(
        sa.text(
            "CREATE INDEX ix_developer_property_checklists_status ON developer_property_checklists (status)"
        )
    )
    op.execute(
        sa.text(
            "CREATE INDEX ix_developer_property_checklists_property_scenario ON developer_property_checklists (property_id, development_scenario)"
        )
    )


def downgrade() -> None:
    """Drop due diligence checklist tables."""
    op.execute(sa.text("DROP TABLE IF EXISTS developer_property_checklists CASCADE"))
    op.execute(sa.text("DROP TABLE IF EXISTS developer_checklist_templates CASCADE"))
    op.execute(sa.text("DROP TYPE IF EXISTS checklist_priority CASCADE"))
    op.execute(sa.text("DROP TYPE IF EXISTS checklist_status CASCADE"))
    op.execute(sa.text("DROP TYPE IF EXISTS checklist_category CASCADE"))
