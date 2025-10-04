"""Add singapore_properties table with MVP workflow fields

Revision ID: 0773c87952ef
Revises: 20241228_000006
Create Date: 2025-09-30 21:51:34.296834

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from geoalchemy2 import Geometry


# revision identifiers, used by Alembic.
revision: str = "0773c87952ef"
down_revision: Union[str, None] = "20241228_000006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create singapore_properties table with MVP workflow fields."""

    # Create singapore_properties table (enums will be created automatically by SQLAlchemy)
    op.create_table(
        "singapore_properties",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        # Basic Information
        sa.Column("property_name", sa.String(255), nullable=False),
        sa.Column("address", sa.Text(), nullable=False),
        sa.Column("postal_code", sa.String(6), nullable=True),
        # Location data
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("location", Geometry("POINT", srid=4326), nullable=True),
        # Singapore Planning Region
        sa.Column("planning_region", sa.String(100), nullable=True),
        sa.Column("planning_area", sa.String(100), nullable=True),
        sa.Column("subzone", sa.String(100), nullable=True),
        # Property Details
        sa.Column(
            "zoning",
            sa.Enum(
                "residential",
                "commercial",
                "industrial",
                "mixed_use",
                "business_park",
                "civic_institutional",
                "educational",
                "healthcare",
                "transport",
                "open_space",
                "special_use",
                name="propertyzoning",
            ),
            nullable=True,
        ),
        sa.Column(
            "tenure",
            sa.Enum(
                "freehold",
                "999_year_leasehold",
                "99_year_leasehold",
                "60_year_leasehold",
                "30_year_leasehold",
                name="propertytenure",
            ),
            nullable=True,
        ),
        sa.Column("lease_start_date", sa.Date(), nullable=True),
        sa.Column("lease_remaining_years", sa.Integer(), nullable=True),
        # Land and Building Details
        sa.Column("land_area_sqm", sa.DECIMAL(10, 2), nullable=True),
        sa.Column("gross_floor_area_sqm", sa.DECIMAL(10, 2), nullable=True),
        sa.Column("gross_plot_ratio", sa.DECIMAL(5, 2), nullable=True),
        sa.Column("current_plot_ratio", sa.DECIMAL(5, 2), nullable=True),
        # Development Parameters
        sa.Column("building_height_m", sa.DECIMAL(6, 2), nullable=True),
        sa.Column("max_building_height_m", sa.DECIMAL(6, 2), nullable=True),
        sa.Column("num_storeys", sa.Integer(), nullable=True),
        sa.Column("max_storeys", sa.Integer(), nullable=True),
        # Singapore Regulatory Compliance
        sa.Column("ura_approval_status", sa.String(100), nullable=True),
        sa.Column("ura_approval_date", sa.Date(), nullable=True),
        sa.Column("bca_approval_status", sa.String(100), nullable=True),
        sa.Column("bca_submission_number", sa.String(100), nullable=True),
        sa.Column("scdf_approval_status", sa.String(100), nullable=True),
        sa.Column("nea_clearance", sa.Boolean(), default=False, nullable=True),
        sa.Column("pub_clearance", sa.Boolean(), default=False, nullable=True),
        sa.Column("lta_clearance", sa.Boolean(), default=False, nullable=True),
        # Development Charges and Fees
        sa.Column("development_charge", sa.DECIMAL(12, 2), nullable=True),
        sa.Column("differential_premium", sa.DECIMAL(12, 2), nullable=True),
        sa.Column("temporary_occupation_fee", sa.DECIMAL(10, 2), nullable=True),
        sa.Column("property_tax_annual", sa.DECIMAL(10, 2), nullable=True),
        # Conservation and Heritage
        sa.Column("is_conserved", sa.Boolean(), default=False, nullable=True),
        sa.Column("conservation_status", sa.String(100), nullable=True),
        sa.Column("heritage_status", sa.String(100), nullable=True),
        # Environmental Sustainability
        sa.Column("green_mark_rating", sa.String(50), nullable=True),
        sa.Column("energy_efficiency_index", sa.DECIMAL(6, 2), nullable=True),
        sa.Column("water_efficiency_rating", sa.String(20), nullable=True),
        # Status
        sa.Column(
            "development_status",
            sa.Enum(
                "vacant_land",
                "planning",
                "approved",
                "under_construction",
                "top_obtained",
                "csc_obtained",
                "operational",
                name="developmentstatus",
            ),
            server_default="vacant_land",
            nullable=True,
        ),
        sa.Column("is_government_land", sa.Boolean(), default=False, nullable=True),
        sa.Column("is_en_bloc_potential", sa.Boolean(), default=False, nullable=True),
        # MVP: Acquisition and Feasibility Workflow
        sa.Column(
            "acquisition_status",
            sa.Enum(
                "available",
                "under_review",
                "acquired",
                "rejected",
                name="acquisitionstatus",
            ),
            server_default="available",
            nullable=True,
        ),
        sa.Column(
            "feasibility_status",
            sa.Enum(
                "analyzing", "approved", "rejected", "on_hold", name="feasibilitystatus"
            ),
            server_default="analyzing",
            nullable=True,
        ),
        # MVP: Financial Tracking
        sa.Column("estimated_acquisition_cost", sa.DECIMAL(15, 2), nullable=True),
        sa.Column("actual_acquisition_cost", sa.DECIMAL(15, 2), nullable=True),
        sa.Column("estimated_development_cost", sa.DECIMAL(15, 2), nullable=True),
        sa.Column("expected_revenue", sa.DECIMAL(15, 2), nullable=True),
        # MVP: Compliance Monitoring
        sa.Column(
            "bca_compliance_status",
            sa.Enum("pending", "passed", "warning", "failed", name="compliancestatus"),
            server_default="pending",
            nullable=True,
        ),
        sa.Column(
            "ura_compliance_status",
            sa.Enum("pending", "passed", "warning", "failed", name="compliancestatus"),
            server_default="pending",
            nullable=True,
        ),
        sa.Column("compliance_notes", sa.Text(), nullable=True),
        sa.Column(
            "compliance_data", postgresql.JSON(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("compliance_last_checked", sa.DateTime(), nullable=True),
        # MVP: Space Optimization Metrics
        sa.Column("max_developable_gfa_sqm", sa.DECIMAL(12, 2), nullable=True),
        sa.Column("gfa_utilization_percentage", sa.DECIMAL(5, 2), nullable=True),
        sa.Column("potential_additional_units", sa.Integer(), nullable=True),
        # Valuation and Market Data
        sa.Column("market_value_sgd", sa.DECIMAL(15, 2), nullable=True),
        sa.Column("valuation_date", sa.Date(), nullable=True),
        sa.Column("psf_value", sa.DECIMAL(10, 2), nullable=True),
        sa.Column("rental_yield_percentage", sa.DECIMAL(5, 2), nullable=True),
        # Additional Singapore-specific data
        sa.Column("mrt_station_nearest", sa.String(100), nullable=True),
        sa.Column("mrt_distance_km", sa.DECIMAL(5, 2), nullable=True),
        sa.Column("school_nearest", sa.String(100), nullable=True),
        sa.Column("school_distance_km", sa.DECIMAL(5, 2), nullable=True),
        # Metadata
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("data_source", sa.String(100), nullable=True),
        # JSON fields for flexible data
        sa.Column(
            "ura_guidelines", postgresql.JSON(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "nearby_amenities", postgresql.JSON(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "development_constraints",
            postgresql.JSON(astext_type=sa.Text()),
            nullable=True,
        ),
        # MVP: Project Linking
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("owner_email", sa.String(255), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
        ),
    )

    # Create indexes for frequently queried fields
    op.create_index(
        "ix_singapore_properties_owner_email", "singapore_properties", ["owner_email"]
    )
    op.create_index(
        "ix_singapore_properties_project_id", "singapore_properties", ["project_id"]
    )
    op.create_index(
        "ix_singapore_properties_postal_code", "singapore_properties", ["postal_code"]
    )
    op.create_index(
        "ix_singapore_properties_acquisition_status",
        "singapore_properties",
        ["acquisition_status"],
    )


def downgrade() -> None:
    """Drop singapore_properties table."""
    op.drop_index("ix_singapore_properties_acquisition_status", "singapore_properties")
    op.drop_index("ix_singapore_properties_postal_code", "singapore_properties")
    op.drop_index("ix_singapore_properties_project_id", "singapore_properties")
    op.drop_index("ix_singapore_properties_owner_email", "singapore_properties")
    op.drop_table("singapore_properties")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS compliancestatus")
    op.execute("DROP TYPE IF EXISTS feasibilitystatus")
    op.execute("DROP TYPE IF EXISTS acquisitionstatus")
    op.execute("DROP TYPE IF EXISTS developmentstatus")
    op.execute("DROP TYPE IF EXISTS propertytenure")
    op.execute("DROP TYPE IF EXISTS propertyzoning")
