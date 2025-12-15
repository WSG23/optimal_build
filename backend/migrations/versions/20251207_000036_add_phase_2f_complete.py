"""Add Phase 2F complete tables and enum updates

Revision ID: 20251207_000036
Revises: 20251207_000035
Create Date: 2025-12-07 08:00:00.000000

This migration adds:
- STB and JTC to agency codes
- Asset type enum for compliance paths
- asset_compliance_paths table
- change_of_use_applications table
- heritage_submissions table
- New submission types (CHANGE_OF_USE, HERITAGE_APPROVAL, INDUSTRIAL_PERMIT)
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20251207_000036"
down_revision = "20251207_000035"
branch_labels = None
depends_on = None


def upgrade():
    # Add new agency codes (STB, JTC) to the enum
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'STB' AND enumtypid = 'agencycode'::regtype) THEN
                ALTER TYPE agencycode ADD VALUE 'STB';
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'JTC' AND enumtypid = 'agencycode'::regtype) THEN
                ALTER TYPE agencycode ADD VALUE 'JTC';
            END IF;
        EXCEPTION
            WHEN undefined_object THEN NULL;
        END$$;
        """
    )

    # Add new submission types
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'CHANGE_OF_USE' AND enumtypid = 'submissiontype'::regtype) THEN
                ALTER TYPE submissiontype ADD VALUE 'CHANGE_OF_USE';
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'HERITAGE_APPROVAL' AND enumtypid = 'submissiontype'::regtype) THEN
                ALTER TYPE submissiontype ADD VALUE 'HERITAGE_APPROVAL';
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'INDUSTRIAL_PERMIT' AND enumtypid = 'submissiontype'::regtype) THEN
                ALTER TYPE submissiontype ADD VALUE 'INDUSTRIAL_PERMIT';
            END IF;
        EXCEPTION
            WHEN undefined_object THEN NULL;
        END$$;
        """
    )

    # Create asset type enum
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'assettype') THEN
                CREATE TYPE assettype AS ENUM (
                    'office', 'retail', 'residential', 'industrial',
                    'heritage', 'mixed_use', 'hospitality'
                );
            END IF;
        END$$;
        """
    )

    # Create asset_compliance_paths table
    op.create_table(
        "asset_compliance_paths",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("asset_type", sa.String(), nullable=False),
        sa.Column("agency_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("submission_type", sa.String(), nullable=False),
        sa.Column("sequence_order", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_mandatory", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("typical_duration_days", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["agency_id"],
            ["regulatory_agencies.id"],
        ),
    )
    op.create_index(
        "ix_asset_compliance_paths_asset_type",
        "asset_compliance_paths",
        ["asset_type"],
        unique=False,
    )
    op.create_index(
        "ix_asset_compliance_paths_agency_id",
        "asset_compliance_paths",
        ["agency_id"],
        unique=False,
    )

    # Create change_of_use_applications table
    op.create_table(
        "change_of_use_applications",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("current_use", sa.String(), nullable=False),
        sa.Column("proposed_use", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="draft"),
        sa.Column("justification", sa.Text(), nullable=True),
        sa.Column("ura_reference", sa.String(), nullable=True),
        sa.Column(
            "requires_dc_amendment",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
        sa.Column(
            "requires_planning_permission",
            sa.Boolean(),
            nullable=False,
            server_default="true",
        ),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
        ),
    )
    op.create_index(
        "ix_change_of_use_applications_project_id",
        "change_of_use_applications",
        ["project_id"],
        unique=False,
    )

    # Create heritage_submissions table
    op.create_table(
        "heritage_submissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("conservation_status", sa.String(), nullable=False),
        sa.Column("stb_reference", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="draft"),
        sa.Column("original_construction_year", sa.Integer(), nullable=True),
        sa.Column("heritage_elements", sa.Text(), nullable=True),
        sa.Column("proposed_interventions", sa.Text(), nullable=True),
        sa.Column(
            "conservation_plan_attached",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
        ),
    )
    op.create_index(
        "ix_heritage_submissions_project_id",
        "heritage_submissions",
        ["project_id"],
        unique=False,
    )


def downgrade():
    # Drop tables using IF EXISTS guards (required by audit-migrations)
    op.execute('DROP INDEX IF EXISTS "ix_heritage_submissions_project_id"')
    op.execute("DROP TABLE IF EXISTS heritage_submissions")

    op.execute('DROP INDEX IF EXISTS "ix_change_of_use_applications_project_id"')
    op.execute("DROP TABLE IF EXISTS change_of_use_applications")

    op.execute('DROP INDEX IF EXISTS "ix_asset_compliance_paths_agency_id"')
    op.execute('DROP INDEX IF EXISTS "ix_asset_compliance_paths_asset_type"')
    op.execute("DROP TABLE IF EXISTS asset_compliance_paths")

    # Note: Cannot remove values from PostgreSQL ENUMs without recreating them
    # The new enum values (STB, JTC, etc.) will remain in the database
    op.execute("DROP TYPE IF EXISTS assettype")
