"""Create reference ingestion and rule tables."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

from app.models.types import geometry_type, jsonb_type

# revision identifiers, used by Alembic.
revision = "20240222_create_reference_tables"
down_revision = None
branch_labels = None
depends_on = None

JSONType = jsonb_type()
ParcelGeometry = geometry_type("MULTIPOLYGON")
ZoningGeometry = geometry_type("MULTIPOLYGON")
PointGeometry = geometry_type("POINT")


def timestamp_columns() -> list[sa.Column]:
    """Return the standard timestamp columns for BaseModel."""

    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            server_onupdate=sa.func.now(),
            nullable=False,
        ),
    ]


def upgrade() -> None:
    op.create_table(
        "ref_sources",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("jurisdiction", sa.String(length=10), nullable=False),
        sa.Column("authority", sa.String(length=50), nullable=False),
        sa.Column("topic", sa.String(length=50), nullable=False),
        sa.Column("doc_title", sa.Text, nullable=False),
        sa.Column("landing_url", sa.Text, nullable=False),
        sa.Column(
            "fetch_kind",
            sa.String(length=20),
            sa.CheckConstraint("fetch_kind IN ('pdf', 'html', 'sitemap')"),
            server_default="pdf",
        ),
        sa.Column("update_freq_hint", sa.String(length=50)),
        sa.Column("selectors", JSONType),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true"), nullable=False),
        *timestamp_columns(),
    )
    op.create_index(
        "idx_ref_sources_jurisdiction_authority",
        "ref_sources",
        ["jurisdiction", "authority"],
    )

    op.create_table(
        "ref_documents",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("source_id", sa.Integer, sa.ForeignKey("ref_sources.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version_label", sa.String(length=100)),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("storage_path", sa.Text, nullable=False),
        sa.Column("file_hash", sa.String(length=64), nullable=False),
        sa.Column("http_etag", sa.String(length=200)),
        sa.Column("http_last_modified", sa.String(length=200)),
        sa.Column("suspected_update", sa.Boolean, server_default=sa.text("false"), nullable=False),
        *timestamp_columns(),
    )
    op.create_index("ix_ref_documents_file_hash", "ref_documents", ["file_hash"], unique=False)

    op.create_table(
        "ref_clauses",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "document_id",
            sa.Integer,
            sa.ForeignKey("ref_documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("clause_ref", sa.String(length=50)),
        sa.Column("section_heading", sa.Text),
        sa.Column("text_span", sa.Text, nullable=False),
        sa.Column("page_from", sa.Integer),
        sa.Column("page_to", sa.Integer),
        sa.Column("extraction_quality", sa.String(length=20)),
        *timestamp_columns(),
    )
    op.create_index(
        "idx_ref_clauses_document_clause",
        "ref_clauses",
        ["document_id", "clause_ref"],
    )

    op.create_table(
        "ref_rules",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("source_id", sa.Integer, sa.ForeignKey("ref_sources.id", ondelete="SET NULL")),
        sa.Column("document_id", sa.Integer, sa.ForeignKey("ref_documents.id", ondelete="SET NULL")),
        sa.Column("jurisdiction", sa.String(length=10), nullable=False),
        sa.Column("authority", sa.String(length=50), nullable=False),
        sa.Column("topic", sa.String(length=50), nullable=False),
        sa.Column("clause_ref", sa.String(length=50)),
        sa.Column("parameter_key", sa.String(length=200), nullable=False),
        sa.Column("operator", sa.String(length=10), nullable=False),
        sa.Column("value", sa.Text, nullable=False),
        sa.Column("unit", sa.String(length=20)),
        sa.Column("applicability", JSONType),
        sa.Column("exceptions", JSONType),
        sa.Column("source_provenance", JSONType),
        sa.Column(
            "review_status",
            sa.String(length=20),
            sa.CheckConstraint("review_status IN ('needs_review', 'approved', 'rejected')"),
            server_default="needs_review",
            nullable=False,
        ),
        sa.Column("reviewer", sa.String(length=100)),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.Column("notes", sa.Text),
        *timestamp_columns(),
    )
    op.create_index(
        "idx_ref_rules_jurisdiction_topic",
        "ref_rules",
        ["jurisdiction", "topic"],
    )
    op.create_index("idx_ref_rules_parameter_key", "ref_rules", ["parameter_key"])
    op.create_index(
        "idx_ref_rules_authority_status",
        "ref_rules",
        ["authority", "review_status"],
    )

    op.create_table(
        "ref_ingestion_runs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("source_id", sa.Integer, sa.ForeignKey("ref_sources.id", ondelete="SET NULL")),
        sa.Column("document_id", sa.Integer, sa.ForeignKey("ref_documents.id", ondelete="SET NULL")),
        sa.Column("run_key", sa.String(length=100), nullable=False, unique=True),
        sa.Column(
            "status",
            sa.String(length=20),
            sa.CheckConstraint("status IN ('pending', 'running', 'succeeded', 'failed')"),
            server_default="pending",
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("metrics", JSONType),
        sa.Column("error_message", sa.Text),
        sa.Column("storage_artifact", JSONType),
        sa.Column("provenance", JSONType),
        *timestamp_columns(),
    )
    op.create_index(
        "idx_ref_ingestion_runs_run_key",
        "ref_ingestion_runs",
        ["run_key"],
    )

    op.create_table(
        "ref_alerts",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("source_id", sa.Integer, sa.ForeignKey("ref_sources.id", ondelete="SET NULL")),
        sa.Column("rule_id", sa.Integer, sa.ForeignKey("ref_rules.id", ondelete="SET NULL")),
        sa.Column(
            "ingestion_run_id",
            sa.Integer,
            sa.ForeignKey("ref_ingestion_runs.id", ondelete="SET NULL"),
        ),
        sa.Column("alert_type", sa.String(length=50), nullable=False),
        sa.Column(
            "severity",
            sa.String(length=20),
            sa.CheckConstraint("severity IN ('info', 'warning', 'critical')"),
            server_default="info",
            nullable=False,
        ),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("context", JSONType),
        sa.Column("triggered_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.Column("resolution_notes", sa.Text),
        *timestamp_columns(),
    )
    op.create_index(
        "idx_ref_alerts_type_severity",
        "ref_alerts",
        ["alert_type", "severity"],
    )

    op.create_table(
        "ref_parcels",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("jurisdiction", sa.String(length=10), nullable=False, server_default="SG"),
        sa.Column("parcel_ref", sa.String(length=100)),
        sa.Column("geometry", ParcelGeometry),
        sa.Column("bounds_json", JSONType),
        sa.Column("centroid_lat", sa.Numeric(10, 7)),
        sa.Column("centroid_lon", sa.Numeric(10, 7)),
        sa.Column("area_m2", sa.Numeric(12, 2)),
        sa.Column("source", sa.String(length=50)),
        *timestamp_columns(),
    )
    op.create_index(
        "idx_ref_parcels_centroid",
        "ref_parcels",
        ["centroid_lat", "centroid_lon"],
    )
    op.create_index(
        "idx_ref_parcels_jurisdiction_ref",
        "ref_parcels",
        ["jurisdiction", "parcel_ref"],
    )

    op.create_table(
        "ref_zoning_layers",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("jurisdiction", sa.String(length=10), nullable=False, server_default="SG"),
        sa.Column("layer_name", sa.String(length=100)),
        sa.Column("zone_code", sa.String(length=20)),
        sa.Column("attributes", JSONType),
        sa.Column("geometry", ZoningGeometry),
        sa.Column("bounds_json", JSONType),
        sa.Column("effective_date", sa.DateTime(timezone=True)),
        sa.Column("expiry_date", sa.DateTime(timezone=True)),
        *timestamp_columns(),
    )
    op.create_index(
        "idx_ref_zoning_jurisdiction_zone",
        "ref_zoning_layers",
        ["jurisdiction", "zone_code"],
    )
    op.create_index(
        "idx_ref_zoning_layer_effective",
        "ref_zoning_layers",
        ["layer_name", "effective_date"],
    )

    op.create_table(
        "ref_geocode_cache",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("address", sa.Text, nullable=False, unique=True),
        sa.Column("lat", sa.Numeric(10, 7)),
        sa.Column("lon", sa.Numeric(10, 7)),
        sa.Column("point_geom", PointGeometry),
        sa.Column("parcel_id", sa.Integer, sa.ForeignKey("ref_parcels.id")),
        sa.Column("confidence_score", sa.Numeric(3, 2)),
        sa.Column("cache_expires_at", sa.DateTime(timezone=True)),
        sa.Column("is_verified", sa.Boolean, server_default=sa.text("false"), nullable=False),
        *timestamp_columns(),
    )
    op.create_index("idx_geocode_cache_coords", "ref_geocode_cache", ["lat", "lon"])


def downgrade() -> None:
    op.drop_index("idx_geocode_cache_coords", table_name="ref_geocode_cache")
    op.drop_table("ref_geocode_cache")

    op.drop_index("idx_ref_zoning_layer_effective", table_name="ref_zoning_layers")
    op.drop_index("idx_ref_zoning_jurisdiction_zone", table_name="ref_zoning_layers")
    op.drop_table("ref_zoning_layers")

    op.drop_index("idx_ref_parcels_jurisdiction_ref", table_name="ref_parcels")
    op.drop_index("idx_ref_parcels_centroid", table_name="ref_parcels")
    op.drop_table("ref_parcels")

    op.drop_index("idx_ref_alerts_type_severity", table_name="ref_alerts")
    op.drop_table("ref_alerts")

    op.drop_index("idx_ref_ingestion_runs_run_key", table_name="ref_ingestion_runs")
    op.drop_table("ref_ingestion_runs")

    op.drop_index("idx_ref_rules_authority_status", table_name="ref_rules")
    op.drop_index("idx_ref_rules_parameter_key", table_name="ref_rules")
    op.drop_index("idx_ref_rules_jurisdiction_topic", table_name="ref_rules")
    op.drop_table("ref_rules")

    op.drop_index("idx_ref_clauses_document_clause", table_name="ref_clauses")
    op.drop_table("ref_clauses")

    op.drop_index("ix_ref_documents_file_hash", table_name="ref_documents")
    op.drop_table("ref_documents")

    op.drop_index("idx_ref_sources_jurisdiction_authority", table_name="ref_sources")
    op.drop_table("ref_sources")
