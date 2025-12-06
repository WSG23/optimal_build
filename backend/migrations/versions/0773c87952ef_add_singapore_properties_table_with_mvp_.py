"""Add singapore_properties table with MVP workflow fields

Revision ID: 0773c87952ef
Revises: 20241228_000006
Create Date: 2025-09-30 21:51:34.296834

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "0773c87952ef"
down_revision: Union[str, None] = "20241228_000006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create singapore_properties table with MVP workflow fields."""

    # Create enum types using raw SQL with IF NOT EXISTS checks
    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'propertyzoning') THEN
                    CREATE TYPE propertyzoning AS ENUM (
                        'residential', 'commercial', 'industrial', 'mixed_use',
                        'business_park', 'civic_institutional', 'educational',
                        'healthcare', 'transport', 'open_space', 'special_use'
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
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'propertytenure') THEN
                    CREATE TYPE propertytenure AS ENUM (
                        'freehold', '999_year_leasehold', '99_year_leasehold',
                        '60_year_leasehold', '30_year_leasehold'
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
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'developmentstatus') THEN
                    CREATE TYPE developmentstatus AS ENUM (
                        'vacant_land', 'planning', 'approved', 'under_construction',
                        'top_obtained', 'csc_obtained', 'operational'
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
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'acquisitionstatus') THEN
                    CREATE TYPE acquisitionstatus AS ENUM (
                        'available', 'under_review', 'acquired', 'rejected'
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
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'feasibilitystatus') THEN
                    CREATE TYPE feasibilitystatus AS ENUM (
                        'analyzing', 'approved', 'rejected', 'on_hold'
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
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'compliancestatus') THEN
                    CREATE TYPE compliancestatus AS ENUM (
                        'pending', 'passed', 'warning', 'failed'
                    );
                END IF;
            END $$;
            """
        )
    )

    # Create singapore_properties table using raw SQL
    op.execute(
        sa.text(
            """
            CREATE TABLE singapore_properties (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                -- Basic Information
                property_name VARCHAR(255) NOT NULL,
                address TEXT NOT NULL,
                postal_code VARCHAR(6),
                -- Location data
                latitude DOUBLE PRECISION,
                longitude DOUBLE PRECISION,
                location GEOMETRY(POINT, 4326),
                -- Singapore Planning Region
                planning_region VARCHAR(100),
                planning_area VARCHAR(100),
                subzone VARCHAR(100),
                -- Property Details
                zoning propertyzoning,
                tenure propertytenure,
                lease_start_date DATE,
                lease_remaining_years INTEGER,
                -- Land and Building Details
                land_area_sqm NUMERIC(10, 2),
                gross_floor_area_sqm NUMERIC(10, 2),
                gross_plot_ratio NUMERIC(5, 2),
                current_plot_ratio NUMERIC(5, 2),
                -- Development Parameters
                building_height_m NUMERIC(6, 2),
                max_building_height_m NUMERIC(6, 2),
                num_storeys INTEGER,
                max_storeys INTEGER,
                -- Singapore Regulatory Compliance
                ura_approval_status VARCHAR(100),
                ura_approval_date DATE,
                bca_approval_status VARCHAR(100),
                bca_submission_number VARCHAR(100),
                scdf_approval_status VARCHAR(100),
                nea_clearance BOOLEAN DEFAULT false,
                pub_clearance BOOLEAN DEFAULT false,
                lta_clearance BOOLEAN DEFAULT false,
                -- Development Charges and Fees
                development_charge NUMERIC(12, 2),
                differential_premium NUMERIC(12, 2),
                temporary_occupation_fee NUMERIC(10, 2),
                property_tax_annual NUMERIC(10, 2),
                -- Conservation and Heritage
                is_conserved BOOLEAN DEFAULT false,
                conservation_status VARCHAR(100),
                heritage_status VARCHAR(100),
                -- Environmental Sustainability
                green_mark_rating VARCHAR(50),
                energy_efficiency_index NUMERIC(6, 2),
                water_efficiency_rating VARCHAR(20),
                -- Status
                development_status developmentstatus DEFAULT 'vacant_land',
                is_government_land BOOLEAN DEFAULT false,
                is_en_bloc_potential BOOLEAN DEFAULT false,
                -- MVP: Acquisition and Feasibility Workflow
                acquisition_status acquisitionstatus DEFAULT 'available',
                feasibility_status feasibilitystatus DEFAULT 'analyzing',
                -- MVP: Financial Tracking
                estimated_acquisition_cost NUMERIC(15, 2),
                actual_acquisition_cost NUMERIC(15, 2),
                estimated_development_cost NUMERIC(15, 2),
                expected_revenue NUMERIC(15, 2),
                -- MVP: Compliance Monitoring
                bca_compliance_status compliancestatus DEFAULT 'pending',
                ura_compliance_status compliancestatus DEFAULT 'pending',
                compliance_notes TEXT,
                compliance_data JSONB,
                compliance_last_checked TIMESTAMP,
                -- MVP: Space Optimization Metrics
                max_developable_gfa_sqm NUMERIC(12, 2),
                gfa_utilization_percentage NUMERIC(5, 2),
                potential_additional_units INTEGER,
                -- Valuation and Market Data
                market_value_sgd NUMERIC(15, 2),
                valuation_date DATE,
                psf_value NUMERIC(10, 2),
                rental_yield_percentage NUMERIC(5, 2),
                -- Additional Singapore-specific data
                mrt_station_nearest VARCHAR(100),
                mrt_distance_km NUMERIC(5, 2),
                school_nearest VARCHAR(100),
                school_distance_km NUMERIC(5, 2),
                -- Metadata
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                data_source VARCHAR(100),
                -- JSON fields for flexible data
                ura_guidelines JSONB,
                nearby_amenities JSONB,
                development_constraints JSONB,
                -- MVP: Project Linking
                project_id UUID REFERENCES projects(id),
                owner_email VARCHAR(255)
            )
            """
        )
    )

    # Create indexes for frequently queried fields
    op.execute(
        sa.text(
            "CREATE INDEX ix_singapore_properties_owner_email ON singapore_properties (owner_email)"
        )
    )
    op.execute(
        sa.text(
            "CREATE INDEX ix_singapore_properties_project_id ON singapore_properties (project_id)"
        )
    )
    op.execute(
        sa.text(
            "CREATE INDEX ix_singapore_properties_postal_code ON singapore_properties (postal_code)"
        )
    )
    op.execute(
        sa.text(
            "CREATE INDEX ix_singapore_properties_acquisition_status ON singapore_properties (acquisition_status)"
        )
    )
    # Create spatial index for location
    op.execute(
        sa.text(
            "CREATE INDEX ix_singapore_properties_location ON singapore_properties USING gist (location)"
        )
    )


def downgrade() -> None:
    """Drop singapore_properties table."""
    op.execute(sa.text("DROP TABLE IF EXISTS singapore_properties CASCADE"))

    # Drop enum types
    op.execute(sa.text("DROP TYPE IF EXISTS compliancestatus CASCADE"))
    op.execute(sa.text("DROP TYPE IF EXISTS feasibilitystatus CASCADE"))
    op.execute(sa.text("DROP TYPE IF EXISTS acquisitionstatus CASCADE"))
    op.execute(sa.text("DROP TYPE IF EXISTS developmentstatus CASCADE"))
    op.execute(sa.text("DROP TYPE IF EXISTS propertytenure CASCADE"))
    op.execute(sa.text("DROP TYPE IF EXISTS propertyzoning CASCADE"))
