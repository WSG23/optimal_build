"""Add Phase 2G construction tables.

Revision ID: 20251207_000038
Revises: 20251207_000037
Create Date: 2025-12-07 17:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers
revision = "20251207_000038"
down_revision = "20251207_000037"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create ENUM types
    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE contractor_type AS ENUM (
                'general_contractor',
                'sub_contractor',
                'specialist',
                'consultant',
                'supplier'
            );
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
        """
    )
    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE inspection_status_enum AS ENUM (
                'scheduled',
                'passed',
                'failed',
                'passed_with_conditions',
                'rectification_required'
            );
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
        """
    )
    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE severity_level_enum AS ENUM (
                'near_miss',
                'minor',
                'moderate',
                'severe',
                'fatal'
            );
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
        """
    )
    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE drawdown_status_enum AS ENUM (
                'draft',
                'submitted',
                'verified_qs',
                'approved_architect',
                'approved_lender',
                'paid',
                'rejected'
            );
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
        """
    )

    # 1. Contractors Table
    op.create_table(
        "contractors",
        sa.Column("id", UUID(), primary_key=True),
        sa.Column(
            "project_id",
            UUID(),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("company_name", sa.String(200), nullable=False),
        # Use simple string for Enum column to avoid Alembic issues, or use explicit ENUM
        sa.Column(
            "contractor_type",
            sa.Enum(
                "general_contractor",
                "sub_contractor",
                "specialist",
                "consultant",
                "supplier",
                name="contractor_type",
            ),
            nullable=False,
            server_default="general_contractor",
        ),
        sa.Column("contact_person", sa.String(100), nullable=True),
        sa.Column("email", sa.String(200), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("contract_value", sa.Numeric(16, 2), nullable=True),
        sa.Column("contract_date", sa.Date(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("metadata", JSONB(), server_default="{}", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
    )
    op.create_index("ix_contractors_project_id", "contractors", ["project_id"])

    # 2. Quality Inspections Table
    op.create_table(
        "quality_inspections",
        sa.Column("id", UUID(), primary_key=True),
        sa.Column(
            "project_id",
            UUID(),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "development_phase_id",
            sa.Integer(),
            sa.ForeignKey("development_phases.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("inspection_date", sa.Date(), nullable=False),
        sa.Column("inspector_name", sa.String(100), nullable=False),
        sa.Column("location", sa.String(200), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "scheduled",
                "passed",
                "failed",
                "passed_with_conditions",
                "rectification_required",
                name="inspection_status_enum",
            ),
            nullable=False,
            server_default="scheduled",
        ),
        sa.Column("defects_found", JSONB(), server_default="{}", nullable=True),
        sa.Column("photos_url", JSONB(), server_default="[]", nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_quality_inspections_project_id", "quality_inspections", ["project_id"]
    )

    # 3. Safety Incidents Table
    op.create_table(
        "safety_incidents",
        sa.Column("id", UUID(), primary_key=True),
        sa.Column(
            "project_id",
            UUID(),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("incident_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "severity",
            sa.Enum(
                "near_miss",
                "minor",
                "moderate",
                "severe",
                "fatal",
                name="severity_level_enum",
            ),
            nullable=False,
            server_default="minor",
        ),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("location", sa.String(200), nullable=True),
        sa.Column("reported_by", sa.String(100), nullable=True),
        sa.Column("is_resolved", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_safety_incidents_project_id", "safety_incidents", ["project_id"]
    )

    # 4. Drawdown Requests Table
    op.create_table(
        "drawdown_requests",
        sa.Column("id", UUID(), primary_key=True),
        sa.Column(
            "project_id",
            UUID(),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("request_name", sa.String(200), nullable=False),
        sa.Column("request_date", sa.Date(), nullable=False),
        sa.Column("amount_requested", sa.Numeric(16, 2), nullable=False),
        sa.Column("amount_approved", sa.Numeric(16, 2), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "draft",
                "submitted",
                "verified_qs",
                "approved_architect",
                "approved_lender",
                "paid",
                "rejected",
                name="drawdown_status_enum",
            ),
            nullable=False,
            server_default="draft",
        ),
        sa.Column(
            "contractor_id",
            UUID(),
            sa.ForeignKey("contractors.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("supporting_docs", JSONB(), server_default="[]", nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_drawdown_requests_project_id", "drawdown_requests", ["project_id"]
    )


def downgrade() -> None:
    # Drop tables
    op.drop_table("drawdown_requests")
    op.drop_table("safety_incidents")
    op.drop_table("quality_inspections")
    op.drop_table("contractors")

    # Drop Enums
    op.execute("DROP TYPE IF EXISTS drawdown_status_enum")
    op.execute("DROP TYPE IF EXISTS severity_level_enum")
    op.execute("DROP TYPE IF EXISTS inspection_status_enum")
    op.execute("DROP TYPE IF EXISTS contractor_type")
