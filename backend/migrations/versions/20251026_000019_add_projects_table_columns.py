"""Add full schema columns to projects table.

Revision ID: 20251026_000019
Revises: fe09309c8e7f
Create Date: 2025-10-26

The projects table was initially created as a stub with only an id column
in 20240801_000003_add_finance_tables.py. This migration adds all the
remaining columns from the Project model to match the full schema.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20251026_000019"
down_revision = "fe09309c8e7f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add full schema columns to projects table."""

    # Create ENUM types needed for projects table
    # Note: Using native PostgreSQL ENUMs (not sa.Enum with create_type=False)
    # to avoid the ENUM autocreation bug documented in CODING_RULES.md
    # IMPORTANT: ENUM values must match Python model enum values (uppercase)
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'projecttype') THEN
                CREATE TYPE projecttype AS ENUM (
                    'NEW_DEVELOPMENT',
                    'REDEVELOPMENT',
                    'ADDITION_ALTERATION',
                    'CONSERVATION',
                    'CHANGE_OF_USE',
                    'SUBDIVISION',
                    'EN_BLOC',
                    'DEMOLITION'
                );
            END IF;
        END$$;
        """
    )

    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'projectphase') THEN
                CREATE TYPE projectphase AS ENUM (
                    'CONCEPT',
                    'FEASIBILITY',
                    'DESIGN',
                    'APPROVAL',
                    'TENDER',
                    'CONSTRUCTION',
                    'TESTING_COMMISSIONING',
                    'HANDOVER',
                    'OPERATION'
                );
            END IF;
        END$$;
        """
    )

    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'approvalstatus') THEN
                CREATE TYPE approvalstatus AS ENUM (
                    'NOT_SUBMITTED',
                    'PENDING',
                    'APPROVED',
                    'APPROVED_WITH_CONDITIONS',
                    'REJECTED',
                    'RESUBMISSION_REQUIRED',
                    'EXPIRED'
                );
            END IF;
        END$$;
        """
    )

    # Basic Information
    op.add_column(
        "projects",
        sa.Column(
            "project_name",
            sa.String(255),
            nullable=False,
            server_default="Untitled Project",
        ),
    )
    op.add_column(
        "projects",
        sa.Column(
            "project_code", sa.String(100), nullable=False, server_default="PROJ-000"
        ),
    )
    op.add_column("projects", sa.Column("description", sa.Text(), nullable=True))

    # Foreign Keys
    op.add_column(
        "projects", sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.add_column("projects", sa.Column("owner_email", sa.String(255), nullable=True))

    # Project Classification
    op.add_column(
        "projects",
        sa.Column(
            "project_type",
            sa.String(50),
            nullable=False,
            server_default="NEW_DEVELOPMENT",
        ),
    )
    op.add_column(
        "projects",
        sa.Column(
            "current_phase", sa.String(50), nullable=False, server_default="CONCEPT"
        ),
    )

    # Timeline
    op.add_column("projects", sa.Column("start_date", sa.Date(), nullable=True))
    op.add_column(
        "projects", sa.Column("target_completion_date", sa.Date(), nullable=True)
    )
    op.add_column(
        "projects", sa.Column("actual_completion_date", sa.Date(), nullable=True)
    )

    # Singapore Regulatory Submissions - URA
    op.add_column(
        "projects", sa.Column("ura_submission_number", sa.String(100), nullable=True)
    )
    op.add_column(
        "projects",
        sa.Column(
            "ura_approval_status",
            sa.String(50),
            nullable=True,
            server_default="NOT_SUBMITTED",
        ),
    )
    op.add_column(
        "projects", sa.Column("ura_submission_date", sa.Date(), nullable=True)
    )
    op.add_column("projects", sa.Column("ura_approval_date", sa.Date(), nullable=True))
    op.add_column(
        "projects",
        sa.Column(
            "ura_conditions", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
    )

    # Singapore Regulatory Submissions - BCA
    op.add_column(
        "projects", sa.Column("bca_submission_number", sa.String(100), nullable=True)
    )
    op.add_column(
        "projects",
        sa.Column(
            "bca_approval_status",
            sa.String(50),
            nullable=True,
            server_default="NOT_SUBMITTED",
        ),
    )
    op.add_column(
        "projects", sa.Column("bca_submission_date", sa.Date(), nullable=True)
    )
    op.add_column("projects", sa.Column("bca_approval_date", sa.Date(), nullable=True))
    op.add_column(
        "projects", sa.Column("bca_bc1_number", sa.String(100), nullable=True)
    )
    op.add_column(
        "projects", sa.Column("bca_permit_number", sa.String(100), nullable=True)
    )
    op.add_column(
        "projects", sa.Column("structural_pe_number", sa.String(100), nullable=True)
    )

    # Singapore Regulatory Submissions - SCDF
    op.add_column(
        "projects",
        sa.Column(
            "scdf_approval_status",
            sa.String(50),
            nullable=True,
            server_default="NOT_SUBMITTED",
        ),
    )
    op.add_column(
        "projects", sa.Column("scdf_submission_date", sa.Date(), nullable=True)
    )
    op.add_column("projects", sa.Column("scdf_approval_date", sa.Date(), nullable=True))
    op.add_column(
        "projects", sa.Column("fire_safety_certificate", sa.String(100), nullable=True)
    )

    # Other Agencies
    op.add_column(
        "projects",
        sa.Column("nea_approval", sa.Boolean(), nullable=True, server_default="false"),
    )
    op.add_column(
        "projects",
        sa.Column("pub_approval", sa.Boolean(), nullable=True, server_default="false"),
    )
    op.add_column(
        "projects",
        sa.Column("lta_approval", sa.Boolean(), nullable=True, server_default="false"),
    )
    op.add_column(
        "projects",
        sa.Column(
            "nparks_approval", sa.Boolean(), nullable=True, server_default="false"
        ),
    )

    # Development Parameters
    op.add_column(
        "projects", sa.Column("proposed_gfa_sqm", sa.DECIMAL(10, 2), nullable=True)
    )
    op.add_column("projects", sa.Column("proposed_units", sa.Integer(), nullable=True))
    op.add_column(
        "projects", sa.Column("proposed_height_m", sa.DECIMAL(6, 2), nullable=True)
    )
    op.add_column(
        "projects", sa.Column("proposed_storeys", sa.Integer(), nullable=True)
    )
    op.add_column(
        "projects", sa.Column("proposed_plot_ratio", sa.DECIMAL(5, 2), nullable=True)
    )

    # Financial
    op.add_column(
        "projects", sa.Column("estimated_cost_sgd", sa.DECIMAL(15, 2), nullable=True)
    )
    op.add_column(
        "projects", sa.Column("actual_cost_sgd", sa.DECIMAL(15, 2), nullable=True)
    )
    op.add_column(
        "projects",
        sa.Column("development_charge_sgd", sa.DECIMAL(12, 2), nullable=True),
    )
    op.add_column(
        "projects", sa.Column("construction_cost_psf", sa.DECIMAL(10, 2), nullable=True)
    )

    # Construction Details
    op.add_column(
        "projects", sa.Column("main_contractor", sa.String(255), nullable=True)
    )
    op.add_column(
        "projects", sa.Column("architect_firm", sa.String(255), nullable=True)
    )
    op.add_column(
        "projects", sa.Column("c_and_s_engineer", sa.String(255), nullable=True)
    )
    op.add_column("projects", sa.Column("mep_engineer", sa.String(255), nullable=True))
    op.add_column("projects", sa.Column("qs_consultant", sa.String(255), nullable=True))

    # Compliance and Quality
    op.add_column(
        "projects", sa.Column("buildability_score", sa.DECIMAL(5, 2), nullable=True)
    )
    op.add_column(
        "projects", sa.Column("constructability_score", sa.DECIMAL(5, 2), nullable=True)
    )
    op.add_column(
        "projects", sa.Column("quality_mark_score", sa.DECIMAL(5, 2), nullable=True)
    )
    op.add_column(
        "projects", sa.Column("green_mark_target", sa.String(50), nullable=True)
    )

    # Progress Tracking
    op.add_column(
        "projects",
        sa.Column(
            "completion_percentage", sa.DECIMAL(5, 2), nullable=True, server_default="0"
        ),
    )
    op.add_column(
        "projects",
        sa.Column(
            "milestones_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
    )
    op.add_column(
        "projects",
        sa.Column(
            "risks_identified", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
    )
    op.add_column(
        "projects",
        sa.Column("issues_log", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )

    # Documents and Submissions
    op.add_column(
        "projects",
        sa.Column("documents", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "projects",
        sa.Column(
            "submission_history", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
    )

    # Status
    op.add_column(
        "projects",
        sa.Column("is_active", sa.Boolean(), nullable=True, server_default="true"),
    )
    op.add_column(
        "projects",
        sa.Column("is_completed", sa.Boolean(), nullable=True, server_default="false"),
    )
    op.add_column(
        "projects",
        sa.Column("has_top", sa.Boolean(), nullable=True, server_default="false"),
    )
    op.add_column(
        "projects",
        sa.Column("has_csc", sa.Boolean(), nullable=True, server_default="false"),
    )

    # Key Dates (Singapore specific)
    op.add_column("projects", sa.Column("land_tender_date", sa.Date(), nullable=True))
    op.add_column("projects", sa.Column("award_date", sa.Date(), nullable=True))
    op.add_column(
        "projects", sa.Column("groundbreaking_date", sa.Date(), nullable=True)
    )
    op.add_column("projects", sa.Column("topping_out_date", sa.Date(), nullable=True))
    op.add_column("projects", sa.Column("top_date", sa.Date(), nullable=True))
    op.add_column("projects", sa.Column("csc_date", sa.Date(), nullable=True))

    # Metadata
    op.add_column(
        "projects",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.add_column(
        "projects",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.add_column("projects", sa.Column("created_by", sa.String(100), nullable=True))

    # Add constraints after columns are created
    # Remove server_default after initial migration to match model definition
    op.alter_column("projects", "project_name", server_default=None)
    op.alter_column("projects", "project_code", server_default=None)
    op.alter_column("projects", "project_type", server_default=None)
    op.alter_column("projects", "current_phase", server_default=None)

    # Create unique constraint on project_code
    op.create_unique_constraint(
        "uq_projects_project_code", "projects", ["project_code"]
    )

    # Create indexes for common queries
    op.create_index("ix_projects_project_name", "projects", ["project_name"])
    op.create_index("ix_projects_project_code", "projects", ["project_code"])
    op.create_index("ix_projects_owner_email", "projects", ["owner_email"])
    op.create_index("ix_projects_project_type", "projects", ["project_type"])
    op.create_index("ix_projects_current_phase", "projects", ["current_phase"])
    op.create_index("ix_projects_is_active", "projects", ["is_active"])
    op.create_index("ix_projects_created_at", "projects", ["created_at"])

    # TODO: Add FK to users table when users table is created
    # op.create_foreign_key("fk_projects_owner_id", "projects", "users", ["owner_id"], ["id"])


def downgrade() -> None:
    """Downgrade not supported for this migration due to complexity."""
    pass
