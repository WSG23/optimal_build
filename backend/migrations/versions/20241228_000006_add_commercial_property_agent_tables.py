"""Add Commercial Property Agent tables

Revision ID: 000006
Revises: 000005
Create Date: 2024-12-28

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "20241228_000006"
down_revision = "20240919_000005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create Commercial Property Agent tables."""

    # Create ENUM types using raw SQL to avoid SQLAlchemy auto-creation issues
    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'property_type') THEN
                    CREATE TYPE property_type AS ENUM (
                        'office', 'retail', 'industrial', 'residential', 'mixed_use',
                        'hotel', 'warehouse', 'land', 'special_purpose'
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
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'property_status') THEN
                    CREATE TYPE property_status AS ENUM (
                        'existing', 'planned', 'approved', 'under_construction', 'completed', 'demolished'
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
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tenure_type') THEN
                    CREATE TYPE tenure_type AS ENUM (
                        'freehold', 'leasehold_99', 'leasehold_999', 'leasehold_60', 'leasehold_30', 'leasehold_other'
                    );
                END IF;
            END $$;
            """
        )
    )

    # Properties table
    op.execute(
        sa.text(
            """
            CREATE TABLE properties (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(255) NOT NULL,
                address VARCHAR(500) NOT NULL,
                postal_code VARCHAR(20),
                property_type property_type NOT NULL,
                status property_status DEFAULT 'existing',
                location GEOGRAPHY(POINT, 4326) NOT NULL,
                district VARCHAR(50),
                subzone VARCHAR(100),
                planning_area VARCHAR(100),
                land_area_sqm DECIMAL(10, 2),
                gross_floor_area_sqm DECIMAL(12, 2),
                net_lettable_area_sqm DECIMAL(12, 2),
                building_height_m DECIMAL(6, 2),
                floors_above_ground INTEGER,
                floors_below_ground INTEGER,
                units_total INTEGER,
                year_built INTEGER,
                year_renovated INTEGER,
                developer VARCHAR(255),
                architect VARCHAR(255),
                tenure_type tenure_type,
                lease_start_date DATE,
                lease_expiry_date DATE,
                zoning_code VARCHAR(50),
                plot_ratio DECIMAL(4, 2),
                is_conservation BOOLEAN DEFAULT false,
                conservation_status VARCHAR(100),
                heritage_constraints JSONB,
                ura_property_id VARCHAR(50) UNIQUE,
                data_source VARCHAR(50),
                external_references JSONB,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    )
    op.execute(
        sa.text(
            "CREATE INDEX idx_property_location ON properties USING gist (location)"
        )
    )
    op.execute(
        sa.text(
            "CREATE INDEX idx_property_type_status ON properties (property_type, status)"
        )
    )
    op.execute(sa.text("CREATE INDEX idx_property_district ON properties (district)"))

    # Market Transactions table
    op.execute(
        sa.text(
            """
            CREATE TABLE market_transactions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                property_id UUID NOT NULL REFERENCES properties(id),
                transaction_date DATE NOT NULL,
                transaction_type VARCHAR(50),
                sale_price DECIMAL(15, 2) NOT NULL,
                psf_price DECIMAL(10, 2),
                psm_price DECIMAL(10, 2),
                buyer_type VARCHAR(50),
                seller_type VARCHAR(50),
                buyer_profile JSONB,
                unit_number VARCHAR(20),
                floor_area_sqm DECIMAL(10, 2),
                floor_level INTEGER,
                market_segment VARCHAR(50),
                financing_type VARCHAR(50),
                data_source VARCHAR(50) NOT NULL,
                confidence_score DECIMAL(3, 2),
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    )
    op.execute(
        sa.text(
            "CREATE INDEX idx_transaction_date ON market_transactions (transaction_date)"
        )
    )
    op.execute(
        sa.text(
            "CREATE INDEX idx_transaction_property_date ON market_transactions (property_id, transaction_date)"
        )
    )

    # Rental Listings table
    op.execute(
        sa.text(
            """
            CREATE TABLE rental_listings (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                property_id UUID NOT NULL REFERENCES properties(id),
                listing_date DATE NOT NULL,
                listing_type VARCHAR(50),
                is_active BOOLEAN DEFAULT true,
                floor_area_sqm DECIMAL(10, 2) NOT NULL,
                floor_level VARCHAR(50),
                unit_number VARCHAR(50),
                asking_rent_monthly DECIMAL(10, 2),
                asking_psf_monthly DECIMAL(8, 2),
                achieved_rent_monthly DECIMAL(10, 2),
                achieved_psf_monthly DECIMAL(8, 2),
                lease_commencement_date DATE,
                lease_term_months INTEGER,
                tenant_name VARCHAR(255),
                tenant_trade VARCHAR(100),
                available_date DATE,
                days_on_market INTEGER,
                listing_source VARCHAR(50),
                agent_company VARCHAR(255),
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    )
    op.execute(sa.text("CREATE INDEX idx_rental_active ON rental_listings (is_active)"))
    op.execute(
        sa.text(
            "CREATE INDEX idx_rental_property_active ON rental_listings (property_id, is_active)"
        )
    )

    # Development Pipeline table
    op.execute(
        sa.text(
            """
            CREATE TABLE development_pipeline (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                project_name VARCHAR(255) NOT NULL,
                developer VARCHAR(255),
                project_type property_type NOT NULL,
                location GEOGRAPHY(POINT, 4326) NOT NULL,
                address VARCHAR(500),
                district VARCHAR(50),
                total_gfa_sqm DECIMAL(12, 2),
                total_units INTEGER,
                building_count INTEGER DEFAULT 1,
                announcement_date DATE,
                approval_date DATE,
                construction_start DATE,
                expected_completion DATE,
                expected_launch DATE,
                development_status property_status NOT NULL,
                completion_percentage DECIMAL(5, 2),
                estimated_supply_impact JSONB,
                competing_projects JSONB,
                units_launched INTEGER DEFAULT 0,
                units_sold INTEGER DEFAULT 0,
                average_psf_transacted DECIMAL(10, 2),
                data_source VARCHAR(50),
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    )
    op.execute(
        sa.text(
            "CREATE INDEX idx_pipeline_status ON development_pipeline (development_status)"
        )
    )
    op.execute(
        sa.text(
            "CREATE INDEX idx_pipeline_completion ON development_pipeline (expected_completion)"
        )
    )
    op.execute(
        sa.text(
            "CREATE INDEX idx_pipeline_location ON development_pipeline USING gist (location)"
        )
    )

    # Property Photos table
    op.execute(
        sa.text(
            """
            CREATE TABLE property_photos (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                property_id UUID NOT NULL REFERENCES properties(id),
                storage_key VARCHAR(500) NOT NULL,
                filename VARCHAR(255),
                mime_type VARCHAR(50),
                file_size_bytes INTEGER,
                capture_date TIMESTAMP,
                capture_location GEOGRAPHY(POINT, 4326),
                photographer VARCHAR(255),
                auto_tags JSONB,
                manual_tags JSONB,
                site_conditions JSONB,
                exif_data JSONB,
                camera_model VARCHAR(100),
                copyright_owner VARCHAR(255),
                usage_rights VARCHAR(100),
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    )
    op.execute(
        sa.text("CREATE INDEX idx_photo_property ON property_photos (property_id)")
    )
    op.execute(
        sa.text("CREATE INDEX idx_photo_capture_date ON property_photos (capture_date)")
    )

    # Development Analyses table
    op.execute(
        sa.text(
            """
            CREATE TABLE development_analyses (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                property_id UUID NOT NULL REFERENCES properties(id),
                analysis_type VARCHAR(50) NOT NULL,
                analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                gfa_potential_sqm DECIMAL(12, 2),
                optimal_use_mix JSONB,
                market_value_estimate DECIMAL(15, 2),
                projected_cap_rate DECIMAL(5, 2),
                site_constraints JSONB,
                regulatory_constraints JSONB,
                heritage_constraints JSONB,
                development_opportunities JSONB,
                value_add_potential JSONB,
                development_scenarios JSONB,
                recommended_scenario VARCHAR(50),
                assumptions JSONB,
                methodology VARCHAR(100),
                confidence_level DECIMAL(3, 2),
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    )
    op.execute(
        sa.text(
            "CREATE INDEX idx_analysis_property_date ON development_analyses (property_id, analysis_date)"
        )
    )
    op.execute(
        sa.text(
            "CREATE INDEX idx_analysis_type ON development_analyses (analysis_type)"
        )
    )

    # Yield Benchmarks table
    op.execute(
        sa.text(
            """
            CREATE TABLE yield_benchmarks (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                benchmark_date DATE NOT NULL,
                period_type VARCHAR(20),
                country VARCHAR(50) DEFAULT 'Singapore',
                district VARCHAR(100),
                subzone VARCHAR(100),
                location_tier VARCHAR(20),
                property_type property_type NOT NULL,
                property_grade VARCHAR(20),
                cap_rate_mean DECIMAL(5, 3),
                cap_rate_median DECIMAL(5, 3),
                cap_rate_p25 DECIMAL(5, 3),
                cap_rate_p75 DECIMAL(5, 3),
                cap_rate_min DECIMAL(5, 3),
                cap_rate_max DECIMAL(5, 3),
                rental_yield_mean DECIMAL(5, 3),
                rental_yield_median DECIMAL(5, 3),
                rental_yield_p25 DECIMAL(5, 3),
                rental_yield_p75 DECIMAL(5, 3),
                rental_psf_mean DECIMAL(8, 2),
                rental_psf_median DECIMAL(8, 2),
                rental_psf_p25 DECIMAL(8, 2),
                rental_psf_p75 DECIMAL(8, 2),
                occupancy_rate_mean DECIMAL(5, 2),
                vacancy_rate_mean DECIMAL(5, 2),
                sale_psf_mean DECIMAL(10, 2),
                sale_psf_median DECIMAL(10, 2),
                sale_psf_p25 DECIMAL(10, 2),
                sale_psf_p75 DECIMAL(10, 2),
                transaction_count INTEGER,
                total_transaction_value DECIMAL(15, 2),
                sample_size INTEGER,
                data_quality_score DECIMAL(3, 2),
                data_sources JSONB,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT uq_benchmark_date_type_location UNIQUE (benchmark_date, property_type, district)
            )
            """
        )
    )
    op.execute(
        sa.text("CREATE INDEX idx_benchmark_date ON yield_benchmarks (benchmark_date)")
    )
    op.execute(
        sa.text(
            "CREATE INDEX idx_benchmark_location ON yield_benchmarks (district, subzone)"
        )
    )

    # Absorption Tracking table
    op.execute(
        sa.text(
            """
            CREATE TABLE absorption_tracking (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                project_id UUID,
                project_name VARCHAR(255),
                tracking_date DATE NOT NULL,
                district VARCHAR(100),
                property_type property_type NOT NULL,
                total_units INTEGER,
                units_launched INTEGER,
                units_sold_cumulative INTEGER,
                units_sold_period INTEGER,
                sales_absorption_rate DECIMAL(5, 2),
                months_since_launch INTEGER,
                avg_units_per_month DECIMAL(8, 2),
                projected_sellout_months INTEGER,
                launch_price_psf DECIMAL(10, 2),
                current_price_psf DECIMAL(10, 2),
                price_change_percentage DECIMAL(5, 2),
                total_nla_sqm DECIMAL(10, 2),
                nla_leased_cumulative DECIMAL(10, 2),
                nla_leased_period DECIMAL(10, 2),
                leasing_absorption_rate DECIMAL(5, 2),
                competing_supply_units INTEGER,
                competing_projects_count INTEGER,
                market_absorption_rate DECIMAL(5, 2),
                relative_performance DECIMAL(5, 2),
                avg_days_to_sale INTEGER,
                avg_days_to_lease INTEGER,
                velocity_trend VARCHAR(20),
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    )
    op.execute(
        sa.text(
            "CREATE INDEX idx_absorption_project_date ON absorption_tracking (project_id, tracking_date)"
        )
    )
    op.execute(
        sa.text(
            "CREATE INDEX idx_absorption_type_date ON absorption_tracking (property_type, tracking_date)"
        )
    )

    # Market Cycles table
    op.execute(
        sa.text(
            """
            CREATE TABLE market_cycles (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                cycle_date DATE NOT NULL,
                property_type property_type NOT NULL,
                market_segment VARCHAR(50),
                cycle_phase VARCHAR(50),
                phase_duration_months INTEGER,
                phase_strength DECIMAL(3, 2),
                price_momentum DECIMAL(5, 2),
                rental_momentum DECIMAL(5, 2),
                transaction_volume_change DECIMAL(5, 2),
                new_supply_sqm DECIMAL(12, 2),
                net_absorption_sqm DECIMAL(12, 2),
                supply_demand_ratio DECIMAL(5, 2),
                pipeline_supply_12m DECIMAL(12, 2),
                expected_demand_12m DECIMAL(12, 2),
                cycle_outlook VARCHAR(20),
                model_confidence DECIMAL(3, 2),
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT uq_cycle_date_type_segment UNIQUE (cycle_date, property_type, market_segment)
            )
            """
        )
    )
    op.execute(sa.text("CREATE INDEX idx_cycle_date ON market_cycles (cycle_date)"))

    # Market Indices table
    op.execute(
        sa.text(
            """
            CREATE TABLE market_indices (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                index_date DATE NOT NULL,
                index_name VARCHAR(100) NOT NULL,
                property_type property_type,
                index_value DECIMAL(10, 2) NOT NULL,
                base_value DECIMAL(10, 2) DEFAULT 100,
                mom_change DECIMAL(5, 2),
                qoq_change DECIMAL(5, 2),
                yoy_change DECIMAL(5, 2),
                component_values JSONB,
                data_source VARCHAR(50),
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT uq_index_date_name UNIQUE (index_date, index_name)
            )
            """
        )
    )
    op.execute(sa.text("CREATE INDEX idx_index_date ON market_indices (index_date)"))
    op.execute(sa.text("CREATE INDEX idx_index_name ON market_indices (index_name)"))

    # Competitive Sets table
    op.execute(
        sa.text(
            """
            CREATE TABLE competitive_sets (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                set_name VARCHAR(255) NOT NULL,
                primary_property_id UUID,
                property_type property_type NOT NULL,
                location_bounds GEOGRAPHY(POLYGON, 4326),
                radius_km DECIMAL(5, 2),
                min_gfa_sqm DECIMAL(10, 2),
                max_gfa_sqm DECIMAL(10, 2),
                property_grades JSONB,
                age_range_years JSONB,
                competitor_property_ids JSONB,
                avg_rental_psf DECIMAL(8, 2),
                avg_occupancy_rate DECIMAL(5, 2),
                avg_cap_rate DECIMAL(5, 3),
                is_active BOOLEAN DEFAULT true,
                last_refreshed TIMESTAMP,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    )
    op.execute(
        sa.text(
            "CREATE INDEX idx_compset_primary ON competitive_sets (primary_property_id)"
        )
    )
    op.execute(
        sa.text("CREATE INDEX idx_compset_active ON competitive_sets (is_active)")
    )

    # Market Alerts table
    op.execute(
        sa.text(
            """
            CREATE TABLE market_alerts (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                alert_type VARCHAR(50) NOT NULL,
                property_type property_type,
                location VARCHAR(255),
                metric_name VARCHAR(100),
                threshold_value DECIMAL(10, 2),
                threshold_direction VARCHAR(20),
                triggered_at TIMESTAMP,
                triggered_value DECIMAL(10, 2),
                alert_message VARCHAR(1000),
                severity VARCHAR(20),
                market_context JSONB,
                affected_properties JSONB,
                is_active BOOLEAN DEFAULT true,
                acknowledged_at TIMESTAMP,
                acknowledged_by UUID,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    )
    op.execute(sa.text("CREATE INDEX idx_alert_active ON market_alerts (is_active)"))
    op.execute(
        sa.text("CREATE INDEX idx_alert_triggered ON market_alerts (triggered_at)")
    )


def downgrade() -> None:
    """Drop Commercial Property Agent tables."""

    # Drop tables in reverse order to handle foreign key constraints
    op.execute(sa.text("DROP TABLE IF EXISTS market_alerts CASCADE"))
    op.execute(sa.text("DROP TABLE IF EXISTS competitive_sets CASCADE"))
    op.execute(sa.text("DROP TABLE IF EXISTS market_indices CASCADE"))
    op.execute(sa.text("DROP TABLE IF EXISTS market_cycles CASCADE"))
    op.execute(sa.text("DROP TABLE IF EXISTS absorption_tracking CASCADE"))
    op.execute(sa.text("DROP TABLE IF EXISTS yield_benchmarks CASCADE"))
    op.execute(sa.text("DROP TABLE IF EXISTS development_analyses CASCADE"))
    op.execute(sa.text("DROP TABLE IF EXISTS property_photos CASCADE"))
    op.execute(sa.text("DROP TABLE IF EXISTS development_pipeline CASCADE"))
    op.execute(sa.text("DROP TABLE IF EXISTS rental_listings CASCADE"))
    op.execute(sa.text("DROP TABLE IF EXISTS market_transactions CASCADE"))
    op.execute(sa.text("DROP TABLE IF EXISTS properties CASCADE"))

    # Drop ENUM types
    op.execute(sa.text("DROP TYPE IF EXISTS tenure_type CASCADE"))
    op.execute(sa.text("DROP TYPE IF EXISTS property_status CASCADE"))
    op.execute(sa.text("DROP TYPE IF EXISTS property_type CASCADE"))
