"""Add Commercial Property Agent tables

Revision ID: 000006
Revises: 000005
Create Date: 2024-12-28

"""

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geography
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "20241228_000006"
down_revision = "20240919_000005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create Commercial Property Agent tables."""

    # Properties table (ENUM types will be created automatically by SQLAlchemy)
    op.create_table(
        "properties",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("address", sa.String(500), nullable=False),
        sa.Column("postal_code", sa.String(20), nullable=True),
        sa.Column(
            "property_type",
            sa.Enum(
                "office",
                "retail",
                "industrial",
                "residential",
                "mixed_use",
                "hotel",
                "warehouse",
                "land",
                "special_purpose",
                name="property_type",
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "existing",
                "planned",
                "approved",
                "under_construction",
                "completed",
                "demolished",
                name="property_status",
            ),
            server_default="existing",
            nullable=True,
        ),
        sa.Column(
            "location", Geography(geometry_type="POINT", srid=4326), nullable=False
        ),
        sa.Column("district", sa.String(50), nullable=True),
        sa.Column("subzone", sa.String(100), nullable=True),
        sa.Column("planning_area", sa.String(100), nullable=True),
        sa.Column("land_area_sqm", sa.DECIMAL(10, 2), nullable=True),
        sa.Column("gross_floor_area_sqm", sa.DECIMAL(12, 2), nullable=True),
        sa.Column("net_lettable_area_sqm", sa.DECIMAL(12, 2), nullable=True),
        sa.Column("building_height_m", sa.DECIMAL(6, 2), nullable=True),
        sa.Column("floors_above_ground", sa.Integer(), nullable=True),
        sa.Column("floors_below_ground", sa.Integer(), nullable=True),
        sa.Column("units_total", sa.Integer(), nullable=True),
        sa.Column("year_built", sa.Integer(), nullable=True),
        sa.Column("year_renovated", sa.Integer(), nullable=True),
        sa.Column("developer", sa.String(255), nullable=True),
        sa.Column("architect", sa.String(255), nullable=True),
        sa.Column(
            "tenure_type",
            sa.Enum(
                "freehold",
                "leasehold_99",
                "leasehold_999",
                "leasehold_60",
                "leasehold_30",
                "leasehold_other",
                name="tenure_type",
            ),
            nullable=True,
        ),
        sa.Column("lease_start_date", sa.Date(), nullable=True),
        sa.Column("lease_expiry_date", sa.Date(), nullable=True),
        sa.Column("zoning_code", sa.String(50), nullable=True),
        sa.Column("plot_ratio", sa.DECIMAL(4, 2), nullable=True),
        sa.Column(
            "is_conservation", sa.Boolean(), server_default="false", nullable=True
        ),
        sa.Column("conservation_status", sa.String(100), nullable=True),
        sa.Column("heritage_constraints", sa.JSON(), nullable=True),
        sa.Column("ura_property_id", sa.String(50), nullable=True),
        sa.Column("data_source", sa.String(50), nullable=True),
        sa.Column("external_references", sa.JSON(), nullable=True),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ura_property_id"),
    )
    op.create_index(
        "idx_property_location", "properties", ["location"], postgresql_using="gist"
    )
    op.create_index(
        "idx_property_type_status", "properties", ["property_type", "status"]
    )
    op.create_index("idx_property_district", "properties", ["district"])

    # Market Transactions table
    op.create_table(
        "market_transactions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("property_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("transaction_date", sa.Date(), nullable=False),
        sa.Column("transaction_type", sa.String(50), nullable=True),
        sa.Column("sale_price", sa.DECIMAL(15, 2), nullable=False),
        sa.Column("psf_price", sa.DECIMAL(10, 2), nullable=True),
        sa.Column("psm_price", sa.DECIMAL(10, 2), nullable=True),
        sa.Column("buyer_type", sa.String(50), nullable=True),
        sa.Column("seller_type", sa.String(50), nullable=True),
        sa.Column("buyer_profile", sa.JSON(), nullable=True),
        sa.Column("unit_number", sa.String(20), nullable=True),
        sa.Column("floor_area_sqm", sa.DECIMAL(10, 2), nullable=True),
        sa.Column("floor_level", sa.Integer(), nullable=True),
        sa.Column("market_segment", sa.String(50), nullable=True),
        sa.Column("financing_type", sa.String(50), nullable=True),
        sa.Column("data_source", sa.String(50), nullable=False),
        sa.Column("confidence_score", sa.DECIMAL(3, 2), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["property_id"],
            ["properties.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_transaction_date", "market_transactions", ["transaction_date"])
    op.create_index(
        "idx_transaction_property_date",
        "market_transactions",
        ["property_id", "transaction_date"],
    )

    # Rental Listings table
    op.create_table(
        "rental_listings",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("property_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("listing_date", sa.Date(), nullable=False),
        sa.Column("listing_type", sa.String(50), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=True),
        sa.Column("floor_area_sqm", sa.DECIMAL(10, 2), nullable=False),
        sa.Column("floor_level", sa.String(50), nullable=True),
        sa.Column("unit_number", sa.String(50), nullable=True),
        sa.Column("asking_rent_monthly", sa.DECIMAL(10, 2), nullable=True),
        sa.Column("asking_psf_monthly", sa.DECIMAL(8, 2), nullable=True),
        sa.Column("achieved_rent_monthly", sa.DECIMAL(10, 2), nullable=True),
        sa.Column("achieved_psf_monthly", sa.DECIMAL(8, 2), nullable=True),
        sa.Column("lease_commencement_date", sa.Date(), nullable=True),
        sa.Column("lease_term_months", sa.Integer(), nullable=True),
        sa.Column("tenant_name", sa.String(255), nullable=True),
        sa.Column("tenant_trade", sa.String(100), nullable=True),
        sa.Column("available_date", sa.Date(), nullable=True),
        sa.Column("days_on_market", sa.Integer(), nullable=True),
        sa.Column("listing_source", sa.String(50), nullable=True),
        sa.Column("agent_company", sa.String(255), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["property_id"],
            ["properties.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_rental_active", "rental_listings", ["is_active"])
    op.create_index(
        "idx_rental_property_active", "rental_listings", ["property_id", "is_active"]
    )

    # Development Pipeline table
    op.create_table(
        "development_pipeline",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("project_name", sa.String(255), nullable=False),
        sa.Column("developer", sa.String(255), nullable=True),
        sa.Column(
            "project_type",
            sa.Enum(
                "office",
                "retail",
                "industrial",
                "residential",
                "mixed_use",
                "hotel",
                "warehouse",
                "land",
                "special_purpose",
                name="property_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "location", Geography(geometry_type="POINT", srid=4326), nullable=False
        ),
        sa.Column("address", sa.String(500), nullable=True),
        sa.Column("district", sa.String(50), nullable=True),
        sa.Column("total_gfa_sqm", sa.DECIMAL(12, 2), nullable=True),
        sa.Column("total_units", sa.Integer(), nullable=True),
        sa.Column("building_count", sa.Integer(), server_default="1", nullable=True),
        sa.Column("announcement_date", sa.Date(), nullable=True),
        sa.Column("approval_date", sa.Date(), nullable=True),
        sa.Column("construction_start", sa.Date(), nullable=True),
        sa.Column("expected_completion", sa.Date(), nullable=True),
        sa.Column("expected_launch", sa.Date(), nullable=True),
        sa.Column(
            "development_status",
            sa.Enum(
                "existing",
                "planned",
                "approved",
                "under_construction",
                "completed",
                "demolished",
                name="property_status",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("completion_percentage", sa.DECIMAL(5, 2), nullable=True),
        sa.Column("estimated_supply_impact", sa.JSON(), nullable=True),
        sa.Column("competing_projects", sa.JSON(), nullable=True),
        sa.Column("units_launched", sa.Integer(), server_default="0", nullable=True),
        sa.Column("units_sold", sa.Integer(), server_default="0", nullable=True),
        sa.Column("average_psf_transacted", sa.DECIMAL(10, 2), nullable=True),
        sa.Column("data_source", sa.String(50), nullable=True),
        sa.Column(
            "last_updated",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
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
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_pipeline_status", "development_pipeline", ["development_status"]
    )
    op.create_index(
        "idx_pipeline_completion", "development_pipeline", ["expected_completion"]
    )
    op.create_index(
        "idx_pipeline_location",
        "development_pipeline",
        ["location"],
        postgresql_using="gist",
    )

    # Property Photos table
    op.create_table(
        "property_photos",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("property_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("storage_key", sa.String(500), nullable=False),
        sa.Column("filename", sa.String(255), nullable=True),
        sa.Column("mime_type", sa.String(50), nullable=True),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
        sa.Column("capture_date", sa.DateTime(), nullable=True),
        sa.Column(
            "capture_location",
            Geography(geometry_type="POINT", srid=4326),
            nullable=True,
        ),
        sa.Column("photographer", sa.String(255), nullable=True),
        sa.Column("auto_tags", sa.JSON(), nullable=True),
        sa.Column("manual_tags", sa.JSON(), nullable=True),
        sa.Column("site_conditions", sa.JSON(), nullable=True),
        sa.Column("exif_data", sa.JSON(), nullable=True),
        sa.Column("camera_model", sa.String(100), nullable=True),
        sa.Column("copyright_owner", sa.String(255), nullable=True),
        sa.Column("usage_rights", sa.String(100), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["property_id"],
            ["properties.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_photo_property", "property_photos", ["property_id"])
    op.create_index("idx_photo_capture_date", "property_photos", ["capture_date"])

    # Development Analyses table
    op.create_table(
        "development_analyses",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("property_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("analysis_type", sa.String(50), nullable=False),
        sa.Column(
            "analysis_date",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.Column("gfa_potential_sqm", sa.DECIMAL(12, 2), nullable=True),
        sa.Column("optimal_use_mix", sa.JSON(), nullable=True),
        sa.Column("market_value_estimate", sa.DECIMAL(15, 2), nullable=True),
        sa.Column("projected_cap_rate", sa.DECIMAL(5, 2), nullable=True),
        sa.Column("site_constraints", sa.JSON(), nullable=True),
        sa.Column("regulatory_constraints", sa.JSON(), nullable=True),
        sa.Column("heritage_constraints", sa.JSON(), nullable=True),
        sa.Column("development_opportunities", sa.JSON(), nullable=True),
        sa.Column("value_add_potential", sa.JSON(), nullable=True),
        sa.Column("development_scenarios", sa.JSON(), nullable=True),
        sa.Column("recommended_scenario", sa.String(50), nullable=True),
        sa.Column("assumptions", sa.JSON(), nullable=True),
        sa.Column("methodology", sa.String(100), nullable=True),
        sa.Column("confidence_level", sa.DECIMAL(3, 2), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["property_id"],
            ["properties.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_analysis_property_date",
        "development_analyses",
        ["property_id", "analysis_date"],
    )
    op.create_index("idx_analysis_type", "development_analyses", ["analysis_type"])

    # Market Intelligence tables

    # Yield Benchmarks table
    op.create_table(
        "yield_benchmarks",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("benchmark_date", sa.Date(), nullable=False),
        sa.Column("period_type", sa.String(20), nullable=True),
        sa.Column("country", sa.String(50), server_default="Singapore", nullable=True),
        sa.Column("district", sa.String(100), nullable=True),
        sa.Column("subzone", sa.String(100), nullable=True),
        sa.Column("location_tier", sa.String(20), nullable=True),
        sa.Column(
            "property_type",
            sa.Enum(
                "office",
                "retail",
                "industrial",
                "residential",
                "mixed_use",
                "hotel",
                "warehouse",
                "land",
                "special_purpose",
                name="property_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("property_grade", sa.String(20), nullable=True),
        sa.Column("cap_rate_mean", sa.DECIMAL(5, 3), nullable=True),
        sa.Column("cap_rate_median", sa.DECIMAL(5, 3), nullable=True),
        sa.Column("cap_rate_p25", sa.DECIMAL(5, 3), nullable=True),
        sa.Column("cap_rate_p75", sa.DECIMAL(5, 3), nullable=True),
        sa.Column("cap_rate_min", sa.DECIMAL(5, 3), nullable=True),
        sa.Column("cap_rate_max", sa.DECIMAL(5, 3), nullable=True),
        sa.Column("rental_yield_mean", sa.DECIMAL(5, 3), nullable=True),
        sa.Column("rental_yield_median", sa.DECIMAL(5, 3), nullable=True),
        sa.Column("rental_yield_p25", sa.DECIMAL(5, 3), nullable=True),
        sa.Column("rental_yield_p75", sa.DECIMAL(5, 3), nullable=True),
        sa.Column("rental_psf_mean", sa.DECIMAL(8, 2), nullable=True),
        sa.Column("rental_psf_median", sa.DECIMAL(8, 2), nullable=True),
        sa.Column("rental_psf_p25", sa.DECIMAL(8, 2), nullable=True),
        sa.Column("rental_psf_p75", sa.DECIMAL(8, 2), nullable=True),
        sa.Column("occupancy_rate_mean", sa.DECIMAL(5, 2), nullable=True),
        sa.Column("vacancy_rate_mean", sa.DECIMAL(5, 2), nullable=True),
        sa.Column("sale_psf_mean", sa.DECIMAL(10, 2), nullable=True),
        sa.Column("sale_psf_median", sa.DECIMAL(10, 2), nullable=True),
        sa.Column("sale_psf_p25", sa.DECIMAL(10, 2), nullable=True),
        sa.Column("sale_psf_p75", sa.DECIMAL(10, 2), nullable=True),
        sa.Column("transaction_count", sa.Integer(), nullable=True),
        sa.Column("total_transaction_value", sa.DECIMAL(15, 2), nullable=True),
        sa.Column("sample_size", sa.Integer(), nullable=True),
        sa.Column("data_quality_score", sa.DECIMAL(3, 2), nullable=True),
        sa.Column("data_sources", sa.JSON(), nullable=True),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "benchmark_date",
            "property_type",
            "district",
            name="uq_benchmark_date_type_location",
        ),
    )
    op.create_index("idx_benchmark_date", "yield_benchmarks", ["benchmark_date"])
    op.create_index(
        "idx_benchmark_location", "yield_benchmarks", ["district", "subzone"]
    )

    # Absorption Tracking table
    op.create_table(
        "absorption_tracking",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("project_name", sa.String(255), nullable=True),
        sa.Column("tracking_date", sa.Date(), nullable=False),
        sa.Column("district", sa.String(100), nullable=True),
        sa.Column(
            "property_type",
            sa.Enum(
                "office",
                "retail",
                "industrial",
                "residential",
                "mixed_use",
                "hotel",
                "warehouse",
                "land",
                "special_purpose",
                name="property_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("total_units", sa.Integer(), nullable=True),
        sa.Column("units_launched", sa.Integer(), nullable=True),
        sa.Column("units_sold_cumulative", sa.Integer(), nullable=True),
        sa.Column("units_sold_period", sa.Integer(), nullable=True),
        sa.Column("sales_absorption_rate", sa.DECIMAL(5, 2), nullable=True),
        sa.Column("months_since_launch", sa.Integer(), nullable=True),
        sa.Column("avg_units_per_month", sa.DECIMAL(8, 2), nullable=True),
        sa.Column("projected_sellout_months", sa.Integer(), nullable=True),
        sa.Column("launch_price_psf", sa.DECIMAL(10, 2), nullable=True),
        sa.Column("current_price_psf", sa.DECIMAL(10, 2), nullable=True),
        sa.Column("price_change_percentage", sa.DECIMAL(5, 2), nullable=True),
        sa.Column("total_nla_sqm", sa.DECIMAL(10, 2), nullable=True),
        sa.Column("nla_leased_cumulative", sa.DECIMAL(10, 2), nullable=True),
        sa.Column("nla_leased_period", sa.DECIMAL(10, 2), nullable=True),
        sa.Column("leasing_absorption_rate", sa.DECIMAL(5, 2), nullable=True),
        sa.Column("competing_supply_units", sa.Integer(), nullable=True),
        sa.Column("competing_projects_count", sa.Integer(), nullable=True),
        sa.Column("market_absorption_rate", sa.DECIMAL(5, 2), nullable=True),
        sa.Column("relative_performance", sa.DECIMAL(5, 2), nullable=True),
        sa.Column("avg_days_to_sale", sa.Integer(), nullable=True),
        sa.Column("avg_days_to_lease", sa.Integer(), nullable=True),
        sa.Column("velocity_trend", sa.String(20), nullable=True),
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
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_absorption_project_date",
        "absorption_tracking",
        ["project_id", "tracking_date"],
    )
    op.create_index(
        "idx_absorption_type_date",
        "absorption_tracking",
        ["property_type", "tracking_date"],
    )

    # Market Cycles table
    op.create_table(
        "market_cycles",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("cycle_date", sa.Date(), nullable=False),
        sa.Column(
            "property_type",
            sa.Enum(
                "office",
                "retail",
                "industrial",
                "residential",
                "mixed_use",
                "hotel",
                "warehouse",
                "land",
                "special_purpose",
                name="property_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("market_segment", sa.String(50), nullable=True),
        sa.Column("cycle_phase", sa.String(50), nullable=True),
        sa.Column("phase_duration_months", sa.Integer(), nullable=True),
        sa.Column("phase_strength", sa.DECIMAL(3, 2), nullable=True),
        sa.Column("price_momentum", sa.DECIMAL(5, 2), nullable=True),
        sa.Column("rental_momentum", sa.DECIMAL(5, 2), nullable=True),
        sa.Column("transaction_volume_change", sa.DECIMAL(5, 2), nullable=True),
        sa.Column("new_supply_sqm", sa.DECIMAL(12, 2), nullable=True),
        sa.Column("net_absorption_sqm", sa.DECIMAL(12, 2), nullable=True),
        sa.Column("supply_demand_ratio", sa.DECIMAL(5, 2), nullable=True),
        sa.Column("pipeline_supply_12m", sa.DECIMAL(12, 2), nullable=True),
        sa.Column("expected_demand_12m", sa.DECIMAL(12, 2), nullable=True),
        sa.Column("cycle_outlook", sa.String(20), nullable=True),
        sa.Column("model_confidence", sa.DECIMAL(3, 2), nullable=True),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "cycle_date",
            "property_type",
            "market_segment",
            name="uq_cycle_date_type_segment",
        ),
    )
    op.create_index("idx_cycle_date", "market_cycles", ["cycle_date"])

    # Market Indices table
    op.create_table(
        "market_indices",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("index_date", sa.Date(), nullable=False),
        sa.Column("index_name", sa.String(100), nullable=False),
        sa.Column(
            "property_type",
            sa.Enum(
                "office",
                "retail",
                "industrial",
                "residential",
                "mixed_use",
                "hotel",
                "warehouse",
                "land",
                "special_purpose",
                name="property_type",
                create_type=False,
            ),
            nullable=True,
        ),
        sa.Column("index_value", sa.DECIMAL(10, 2), nullable=False),
        sa.Column("base_value", sa.DECIMAL(10, 2), server_default="100", nullable=True),
        sa.Column("mom_change", sa.DECIMAL(5, 2), nullable=True),
        sa.Column("qoq_change", sa.DECIMAL(5, 2), nullable=True),
        sa.Column("yoy_change", sa.DECIMAL(5, 2), nullable=True),
        sa.Column("component_values", sa.JSON(), nullable=True),
        sa.Column("data_source", sa.String(50), nullable=True),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("index_date", "index_name", name="uq_index_date_name"),
    )
    op.create_index("idx_index_date", "market_indices", ["index_date"])
    op.create_index("idx_index_name", "market_indices", ["index_name"])

    # Competitive Sets table
    op.create_table(
        "competitive_sets",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("set_name", sa.String(255), nullable=False),
        sa.Column("primary_property_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "property_type",
            sa.Enum(
                "office",
                "retail",
                "industrial",
                "residential",
                "mixed_use",
                "hotel",
                "warehouse",
                "land",
                "special_purpose",
                name="property_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "location_bounds",
            Geography(geometry_type="POLYGON", srid=4326),
            nullable=True,
        ),
        sa.Column("radius_km", sa.DECIMAL(5, 2), nullable=True),
        sa.Column("min_gfa_sqm", sa.DECIMAL(10, 2), nullable=True),
        sa.Column("max_gfa_sqm", sa.DECIMAL(10, 2), nullable=True),
        sa.Column("property_grades", sa.JSON(), nullable=True),
        sa.Column("age_range_years", sa.JSON(), nullable=True),
        sa.Column("competitor_property_ids", sa.JSON(), nullable=True),
        sa.Column("avg_rental_psf", sa.DECIMAL(8, 2), nullable=True),
        sa.Column("avg_occupancy_rate", sa.DECIMAL(5, 2), nullable=True),
        sa.Column("avg_cap_rate", sa.DECIMAL(5, 3), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=True),
        sa.Column("last_refreshed", sa.DateTime(), nullable=True),
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
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_compset_primary", "competitive_sets", ["primary_property_id"])
    op.create_index("idx_compset_active", "competitive_sets", ["is_active"])

    # Market Alerts table
    op.create_table(
        "market_alerts",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("alert_type", sa.String(50), nullable=False),
        sa.Column(
            "property_type",
            sa.Enum(
                "office",
                "retail",
                "industrial",
                "residential",
                "mixed_use",
                "hotel",
                "warehouse",
                "land",
                "special_purpose",
                name="property_type",
                create_type=False,
            ),
            nullable=True,
        ),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("metric_name", sa.String(100), nullable=True),
        sa.Column("threshold_value", sa.DECIMAL(10, 2), nullable=True),
        sa.Column("threshold_direction", sa.String(20), nullable=True),
        sa.Column("triggered_at", sa.DateTime(), nullable=True),
        sa.Column("triggered_value", sa.DECIMAL(10, 2), nullable=True),
        sa.Column("alert_message", sa.String(1000), nullable=True),
        sa.Column("severity", sa.String(20), nullable=True),
        sa.Column("market_context", sa.JSON(), nullable=True),
        sa.Column("affected_properties", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=True),
        sa.Column("acknowledged_at", sa.DateTime(), nullable=True),
        sa.Column("acknowledged_by", postgresql.UUID(as_uuid=True), nullable=True),
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
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_alert_active", "market_alerts", ["is_active"])
    op.create_index("idx_alert_triggered", "market_alerts", ["triggered_at"])


def downgrade() -> None:
    """Drop Commercial Property Agent tables."""

    # Drop tables in reverse order to handle foreign key constraints
    op.drop_table("market_alerts")
    op.drop_table("competitive_sets")
    op.drop_table("market_indices")
    op.drop_table("market_cycles")
    op.drop_table("absorption_tracking")
    op.drop_table("yield_benchmarks")
    op.drop_table("development_analyses")
    op.drop_table("property_photos")
    op.drop_table("development_pipeline")
    op.drop_table("rental_listings")
    op.drop_table("market_transactions")
    op.drop_table("properties")

    # Drop ENUM types
    op.execute("DROP TYPE IF EXISTS tenure_type")
    op.execute("DROP TYPE IF EXISTS property_status")
    op.execute("DROP TYPE IF EXISTS property_type")
