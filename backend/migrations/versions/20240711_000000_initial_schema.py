"""Create the base schema for Optimal Build."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20240711_000000"
down_revision = None
branch_labels = None
depends_on = None


JSONB_TYPE = postgresql.JSONB(astext_type=sa.Text())


def upgrade() -> None:
    """Apply the migration."""

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("baseline_seconds", sa.Float(), nullable=True),
        sa.Column("actual_seconds", sa.Float(), nullable=True),
        sa.Column("context", JSONB_TYPE, nullable=False),
        sa.Column("hash", sa.String(length=64), nullable=False),
        sa.Column("prev_hash", sa.String(length=64), nullable=True),
        sa.Column("signature", sa.String(length=128), nullable=False),
        sa.Column(
            "recorded_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("project_id", "version", name="uq_audit_logs_project_version"),
    )
    op.create_index("ix_audit_logs_project_id", "audit_logs", ["project_id"])
    op.create_index("ix_audit_logs_event_type", "audit_logs", ["event_type"])
    op.create_index("ix_audit_logs_version", "audit_logs", ["version"])
    op.create_index("ix_audit_logs_hash", "audit_logs", ["hash"])
    op.create_index("ix_audit_logs_recorded_at", "audit_logs", ["recorded_at"])
    op.create_index(
        "idx_audit_logs_project_event",
        "audit_logs",
        ["project_id", "event_type"],
    )
    op.create_index(
        "idx_audit_logs_project_version",
        "audit_logs",
        ["project_id", "version"],
    )

    op.create_table(
        "imports",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("project_id", sa.Integer(), nullable=True),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=100), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("storage_path", sa.Text(), nullable=False),
        sa.Column(
            "uploaded_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("layer_metadata", JSONB_TYPE, nullable=True),
        sa.Column("detected_floors", JSONB_TYPE, nullable=True),
        sa.Column("detected_units", JSONB_TYPE, nullable=True),
        sa.Column("vector_storage_path", sa.Text(), nullable=True),
        sa.Column("vector_summary", JSONB_TYPE, nullable=True),
        sa.Column("parse_status", sa.String(length=32), nullable=False),
        sa.Column("parse_requested_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("parse_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("parse_error", sa.Text(), nullable=True),
        sa.Column("parse_result", JSONB_TYPE, nullable=True),
    )
    op.create_index("ix_imports_project_id", "imports", ["project_id"])

    op.create_table(
        "overlay_source_geometries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("source_geometry_key", sa.String(length=100), nullable=False),
        sa.Column("graph", JSONB_TYPE, nullable=False),
        sa.Column("metadata", JSONB_TYPE, nullable=False),
        sa.Column("checksum", sa.String(length=64), nullable=False),
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
            onupdate=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "project_id",
            "source_geometry_key",
            name="uq_overlay_source_key",
        ),
    )
    op.create_index(
        "ix_overlay_source_geometries_project_id",
        "overlay_source_geometries",
        ["project_id"],
    )
    op.create_index(
        "ix_overlay_source_geometries_checksum",
        "overlay_source_geometries",
        ["checksum"],
    )
    op.create_index(
        "ix_overlay_source_geometries_created_at",
        "overlay_source_geometries",
        ["created_at"],
    )

    op.create_table(
        "overlay_suggestions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column(
            "source_geometry_id",
            sa.Integer(),
            sa.ForeignKey("overlay_source_geometries.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("severity", sa.String(length=20), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("engine_version", sa.String(length=50), nullable=True),
        sa.Column("engine_payload", JSONB_TYPE, nullable=False),
        sa.Column("target_ids", JSONB_TYPE, nullable=False),
        sa.Column("props", JSONB_TYPE, nullable=False),
        sa.Column("rule_refs", JSONB_TYPE, nullable=False),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("geometry_checksum", sa.String(length=64), nullable=False),
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
            onupdate=sa.func.now(),
            nullable=False,
        ),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decided_by", sa.String(length=100), nullable=True),
        sa.Column("decision_notes", sa.Text(), nullable=True),
        sa.UniqueConstraint(
            "project_id",
            "source_geometry_id",
            "code",
            name="uq_overlay_suggestion_code",
        ),
    )
    op.create_index("ix_overlay_suggestions_project_id", "overlay_suggestions", ["project_id"])
    op.create_index(
        "ix_overlay_suggestions_source_geometry_id",
        "overlay_suggestions",
        ["source_geometry_id"],
    )
    op.create_index(
        "idx_overlay_suggestions_status",
        "overlay_suggestions",
        ["project_id", "status"],
    )
    op.create_index(
        "ix_overlay_suggestions_status",
        "overlay_suggestions",
        ["status"],
    )
    op.create_index(
        "ix_overlay_suggestions_created_at",
        "overlay_suggestions",
        ["created_at"],
    )

    op.create_table(
        "overlay_decisions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column(
            "source_geometry_id",
            sa.Integer(),
            sa.ForeignKey("overlay_source_geometries.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "suggestion_id",
            sa.Integer(),
            sa.ForeignKey("overlay_suggestions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("decision", sa.String(length=20), nullable=False),
        sa.Column("decided_by", sa.String(length=100), nullable=True),
        sa.Column(
            "decided_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.UniqueConstraint("suggestion_id", name="uq_overlay_decision_suggestion"),
    )
    op.create_index("ix_overlay_decisions_project_id", "overlay_decisions", ["project_id"])
    op.create_index(
        "ix_overlay_decisions_source_geometry_id",
        "overlay_decisions",
        ["source_geometry_id"],
    )
    op.create_index("ix_overlay_decisions_decision", "overlay_decisions", ["decision"])
    op.create_index(
        "idx_overlay_decisions_project",
        "overlay_decisions",
        ["project_id", "decision"],
    )
    op.create_index(
        "ix_overlay_decisions_decided_at",
        "overlay_decisions",
        ["decided_at"],
    )

    op.create_table(
        "overlay_run_locks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column(
            "source_geometry_id",
            sa.Integer(),
            sa.ForeignKey("overlay_source_geometries.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("lock_kind", sa.String(length=50), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column(
            "acquired_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("released_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.UniqueConstraint(
            "project_id",
            "source_geometry_id",
            "lock_kind",
            name="uq_overlay_lock",
        ),
    )
    op.create_index("ix_overlay_run_locks_project_id", "overlay_run_locks", ["project_id"])
    op.create_index(
        "ix_overlay_run_locks_source_geometry_id",
        "overlay_run_locks",
        ["source_geometry_id"],
    )
    op.create_index("ix_overlay_run_locks_is_active", "overlay_run_locks", ["is_active"])
    op.create_index(
        "idx_overlay_locks_active",
        "overlay_run_locks",
        ["project_id", "is_active"],
    )
    op.create_index(
        "ix_overlay_run_locks_acquired_at",
        "overlay_run_locks",
        ["acquired_at"],
    )

    op.create_table(
        "ref_sources",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("jurisdiction", sa.String(length=10), nullable=False),
        sa.Column("authority", sa.String(length=50), nullable=False),
        sa.Column("topic", sa.String(length=50), nullable=False),
        sa.Column("doc_title", sa.Text(), nullable=False),
        sa.Column("landing_url", sa.Text(), nullable=False),
        sa.Column("fetch_kind", sa.String(length=20), nullable=True),
        sa.Column("update_freq_hint", sa.String(length=50), nullable=True),
        sa.Column("selectors", JSONB_TYPE, nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.CheckConstraint(
            "fetch_kind IN ('pdf', 'html', 'sitemap')",
            name="ck_ref_sources_fetch_kind",
        ),
    )
    op.create_index("ix_ref_sources_jurisdiction", "ref_sources", ["jurisdiction"])
    op.create_index("ix_ref_sources_authority", "ref_sources", ["authority"])
    op.create_index("ix_ref_sources_topic", "ref_sources", ["topic"])
    op.create_index("ix_ref_sources_is_active", "ref_sources", ["is_active"])
    op.create_index(
        "idx_ref_sources_jurisdiction_authority",
        "ref_sources",
        ["jurisdiction", "authority"],
    )

    op.create_table(
        "ref_documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "source_id",
            sa.Integer(),
            sa.ForeignKey("ref_sources.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version_label", sa.String(length=100), nullable=True),
        sa.Column(
            "retrieved_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("storage_path", sa.Text(), nullable=False),
        sa.Column("file_hash", sa.String(length=64), nullable=False),
        sa.Column("http_etag", sa.String(length=200), nullable=True),
        sa.Column("http_last_modified", sa.String(length=200), nullable=True),
        sa.Column("suspected_update", sa.Boolean(), nullable=False),
    )
    op.create_index("ix_ref_documents_file_hash", "ref_documents", ["file_hash"])
    op.create_index(
        "ix_ref_documents_suspected_update",
        "ref_documents",
        ["suspected_update"],
    )
    op.create_index("ix_ref_documents_retrieved_at", "ref_documents", ["retrieved_at"])

    op.create_table(
        "ref_clauses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "document_id",
            sa.Integer(),
            sa.ForeignKey("ref_documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("clause_ref", sa.String(length=50), nullable=True),
        sa.Column("section_heading", sa.Text(), nullable=True),
        sa.Column("text_span", sa.Text(), nullable=False),
        sa.Column("page_from", sa.Integer(), nullable=True),
        sa.Column("page_to", sa.Integer(), nullable=True),
        sa.Column("extraction_quality", sa.String(length=20), nullable=True),
    )
    op.create_index("ix_ref_clauses_clause_ref", "ref_clauses", ["clause_ref"])
    op.create_index(
        "idx_ref_clauses_document_clause",
        "ref_clauses",
        ["document_id", "clause_ref"],
    )

    op.create_table(
        "ref_rules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "source_id",
            sa.Integer(),
            sa.ForeignKey("ref_sources.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "document_id",
            sa.Integer(),
            sa.ForeignKey("ref_documents.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("jurisdiction", sa.String(length=10), nullable=False),
        sa.Column("authority", sa.String(length=50), nullable=False),
        sa.Column("topic", sa.String(length=50), nullable=False),
        sa.Column("clause_ref", sa.String(length=50), nullable=True),
        sa.Column("parameter_key", sa.String(length=200), nullable=False),
        sa.Column("operator", sa.String(length=10), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("unit", sa.String(length=20), nullable=True),
        sa.Column("applicability", JSONB_TYPE, nullable=True),
        sa.Column("exceptions", JSONB_TYPE, nullable=True),
        sa.Column("source_provenance", JSONB_TYPE, nullable=True),
        sa.Column("review_status", sa.String(length=20), nullable=False),
        sa.Column("reviewer", sa.String(length=100), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("is_published", sa.Boolean(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "review_status IN ('needs_review', 'approved', 'rejected')",
            name="ck_ref_rules_review_status",
        ),
    )
    op.create_index("ix_ref_rules_jurisdiction", "ref_rules", ["jurisdiction"])
    op.create_index("ix_ref_rules_authority", "ref_rules", ["authority"])
    op.create_index("ix_ref_rules_topic", "ref_rules", ["topic"])
    op.create_index("ix_ref_rules_clause_ref", "ref_rules", ["clause_ref"])
    op.create_index("ix_ref_rules_parameter_key", "ref_rules", ["parameter_key"])
    op.create_index("ix_ref_rules_review_status", "ref_rules", ["review_status"])
    op.create_index("ix_ref_rules_is_published", "ref_rules", ["is_published"])
    op.create_index(
        "idx_ref_rules_jurisdiction_topic",
        "ref_rules",
        ["jurisdiction", "topic"],
    )
    op.create_index(
        "idx_ref_rules_parameter_key",
        "ref_rules",
        ["parameter_key"],
    )
    op.create_index(
        "idx_ref_rules_authority_status",
        "ref_rules",
        ["authority", "review_status"],
    )

    op.create_table(
        "ref_parcels",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("jurisdiction", sa.String(length=10), nullable=False),
        sa.Column("parcel_ref", sa.String(length=100), nullable=True),
        sa.Column("bounds_json", JSONB_TYPE, nullable=True),
        sa.Column("centroid_lat", sa.Numeric(10, 7), nullable=True),
        sa.Column("centroid_lon", sa.Numeric(10, 7), nullable=True),
        sa.Column("area_m2", sa.Numeric(12, 2), nullable=True),
        sa.Column("source", sa.String(length=50), nullable=True),
    )
    op.create_index("ix_ref_parcels_jurisdiction", "ref_parcels", ["jurisdiction"])
    op.create_index("ix_ref_parcels_parcel_ref", "ref_parcels", ["parcel_ref"])
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
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("jurisdiction", sa.String(length=10), nullable=False),
        sa.Column("layer_name", sa.String(length=100), nullable=True),
        sa.Column("zone_code", sa.String(length=20), nullable=True),
        sa.Column("attributes", JSONB_TYPE, nullable=True),
        sa.Column("bounds_json", JSONB_TYPE, nullable=True),
        sa.Column("effective_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expiry_date", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_ref_zoning_layers_jurisdiction", "ref_zoning_layers", ["jurisdiction"])
    op.create_index("ix_ref_zoning_layers_layer_name", "ref_zoning_layers", ["layer_name"])
    op.create_index("ix_ref_zoning_layers_zone_code", "ref_zoning_layers", ["zone_code"])
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
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("address", sa.Text(), nullable=False),
        sa.Column("lat", sa.Numeric(10, 7), nullable=True),
        sa.Column("lon", sa.Numeric(10, 7), nullable=True),
        sa.Column(
            "parcel_id",
            sa.Integer(),
            sa.ForeignKey("ref_parcels.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("confidence_score", sa.Numeric(3, 2), nullable=True),
        sa.Column("cache_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_verified", sa.Boolean(), nullable=False),
    )
    op.create_index(
        "ix_ref_geocode_cache_address",
        "ref_geocode_cache",
        ["address"],
        unique=True,
    )
    op.create_index(
        "idx_geocode_cache_coords",
        "ref_geocode_cache",
        ["lat", "lon"],
    )

    op.create_table(
        "ref_material_standards",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("jurisdiction", sa.String(length=10), nullable=False),
        sa.Column("standard_code", sa.String(length=50), nullable=False),
        sa.Column("material_type", sa.String(length=100), nullable=False),
        sa.Column("standard_body", sa.String(length=100), nullable=False),
        sa.Column("property_key", sa.String(length=200), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("unit", sa.String(length=20), nullable=True),
        sa.Column("context", JSONB_TYPE, nullable=True),
        sa.Column("section", sa.String(length=100), nullable=True),
        sa.Column("applicability", JSONB_TYPE, nullable=True),
        sa.Column("edition", sa.String(length=50), nullable=True),
        sa.Column("effective_date", sa.Date(), nullable=True),
        sa.Column("license_ref", sa.String(length=100), nullable=True),
        sa.Column("provenance", JSONB_TYPE, nullable=True),
        sa.Column("source_document", sa.Text(), nullable=True),
    )
    op.create_index("ix_ref_material_standards_jurisdiction", "ref_material_standards", ["jurisdiction"])
    op.create_index("ix_ref_material_standards_standard_code", "ref_material_standards", ["standard_code"])
    op.create_index("ix_ref_material_standards_material_type", "ref_material_standards", ["material_type"])
    op.create_index("ix_ref_material_standards_standard_body", "ref_material_standards", ["standard_body"])
    op.create_index("ix_ref_material_standards_property_key", "ref_material_standards", ["property_key"])
    op.create_index(
        "idx_material_standards_type_property",
        "ref_material_standards",
        ["material_type", "property_key"],
    )

    op.create_table(
        "ref_products",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("vendor", sa.String(length=100), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("product_code", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("brand", sa.String(length=100), nullable=True),
        sa.Column("model_number", sa.String(length=100), nullable=True),
        sa.Column("sku", sa.String(length=100), nullable=True),
        sa.Column("dimensions", JSONB_TYPE, nullable=True),
        sa.Column("specifications", JSONB_TYPE, nullable=True),
        sa.Column("bim_uri", sa.Text(), nullable=True),
        sa.Column("spec_uri", sa.Text(), nullable=True),
        sa.Column("unit_cost", sa.Numeric(10, 2), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
    )
    op.create_index("ix_ref_products_vendor", "ref_products", ["vendor"])
    op.create_index("ix_ref_products_category", "ref_products", ["category"])
    op.create_index("ix_ref_products_brand", "ref_products", ["brand"])
    op.create_index("ix_ref_products_model_number", "ref_products", ["model_number"])
    op.create_index("ix_ref_products_sku", "ref_products", ["sku"])
    op.create_index("ix_ref_products_is_active", "ref_products", ["is_active"])
    op.create_index(
        "idx_products_vendor_category",
        "ref_products",
        ["vendor", "category"],
    )
    op.create_index(
        "idx_products_category_active",
        "ref_products",
        ["category", "is_active"],
    )

    op.create_table(
        "ref_ergonomics",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("metric_key", sa.String(length=200), nullable=False),
        sa.Column("population", sa.String(length=50), nullable=False),
        sa.Column("percentile", sa.String(length=10), nullable=True),
        sa.Column("value", sa.Numeric(8, 2), nullable=False),
        sa.Column("unit", sa.String(length=20), nullable=False),
        sa.Column("context", JSONB_TYPE, nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("source", sa.String(length=100), nullable=True),
    )
    op.create_index("ix_ref_ergonomics_metric_key", "ref_ergonomics", ["metric_key"])
    op.create_index("ix_ref_ergonomics_population", "ref_ergonomics", ["population"])
    op.create_index(
        "idx_ergonomics_metric_population",
        "ref_ergonomics",
        ["metric_key", "population"],
    )

    op.create_table(
        "ref_cost_indices",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("jurisdiction", sa.String(length=10), nullable=False),
        sa.Column("series_name", sa.String(length=100), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("subcategory", sa.String(length=100), nullable=True),
        sa.Column("period", sa.String(length=20), nullable=False),
        sa.Column("value", sa.Numeric(12, 4), nullable=False),
        sa.Column("unit", sa.String(length=50), nullable=False),
        sa.Column("source", sa.String(length=100), nullable=True),
        sa.Column("provider", sa.String(length=100), nullable=False),
        sa.Column("methodology", sa.Text(), nullable=True),
    )
    op.create_index("ix_ref_cost_indices_jurisdiction", "ref_cost_indices", ["jurisdiction"])
    op.create_index("ix_ref_cost_indices_series_name", "ref_cost_indices", ["series_name"])
    op.create_index("ix_ref_cost_indices_category", "ref_cost_indices", ["category"])
    op.create_index("ix_ref_cost_indices_period", "ref_cost_indices", ["period"])
    op.create_index("ix_ref_cost_indices_provider", "ref_cost_indices", ["provider"])
    op.create_index(
        "idx_cost_indices_series_period",
        "ref_cost_indices",
        ["series_name", "period"],
    )
    op.create_index(
        "idx_cost_indices_jurisdiction_category",
        "ref_cost_indices",
        ["jurisdiction", "category"],
    )

    op.create_table(
        "ref_cost_catalogs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("jurisdiction", sa.String(length=10), nullable=False),
        sa.Column("catalog_name", sa.String(length=100), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=True),
        sa.Column("item_code", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("unit", sa.String(length=20), nullable=True),
        sa.Column("unit_cost", sa.Numeric(12, 2), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("effective_date", sa.Date(), nullable=True),
        sa.Column("item_metadata", JSONB_TYPE, nullable=True),
        sa.Column("source", sa.String(length=100), nullable=True),
    )
    op.create_index("ix_ref_cost_catalogs_jurisdiction", "ref_cost_catalogs", ["jurisdiction"])
    op.create_index("ix_ref_cost_catalogs_catalog_name", "ref_cost_catalogs", ["catalog_name"])
    op.create_index("ix_ref_cost_catalogs_category", "ref_cost_catalogs", ["category"])
    op.create_index("ix_ref_cost_catalogs_item_code", "ref_cost_catalogs", ["item_code"])
    op.create_index(
        "idx_cost_catalogs_name_code",
        "ref_cost_catalogs",
        ["catalog_name", "item_code"],
    )
    op.create_index(
        "idx_cost_catalogs_category",
        "ref_cost_catalogs",
        ["category"],
    )

    op.create_table(
        "ref_ingestion_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("run_key", sa.String(length=100), nullable=False),
        sa.Column("flow_name", sa.String(length=100), nullable=False),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("records_ingested", sa.Integer(), nullable=True),
        sa.Column("suspected_updates", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("metrics", JSONB_TYPE, nullable=True),
        sa.UniqueConstraint("run_key", name="uq_ref_ingestion_runs_run_key"),
    )
    op.create_index("ix_ref_ingestion_runs_run_key", "ref_ingestion_runs", ["run_key"], unique=True)
    op.create_index("ix_ref_ingestion_runs_flow_name", "ref_ingestion_runs", ["flow_name"])
    op.create_index("ix_ref_ingestion_runs_status", "ref_ingestion_runs", ["status"])
    op.create_index(
        "idx_ingestion_runs_flow_status",
        "ref_ingestion_runs",
        ["flow_name", "status"],
    )

    op.create_table(
        "ref_alerts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("alert_type", sa.String(length=50), nullable=False),
        sa.Column("level", sa.String(length=20), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("context", JSONB_TYPE, nullable=True),
        sa.Column(
            "ingestion_run_id",
            sa.Integer(),
            sa.ForeignKey("ref_ingestion_runs.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("acknowledged", sa.Boolean(), nullable=False),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("acknowledged_by", sa.String(length=100), nullable=True),
    )
    op.create_index("ix_ref_alerts_alert_type", "ref_alerts", ["alert_type"])
    op.create_index("ix_ref_alerts_level", "ref_alerts", ["level"])
    op.create_index("ix_ref_alerts_created_at", "ref_alerts", ["created_at"])
    op.create_index("ix_ref_alerts_acknowledged", "ref_alerts", ["acknowledged"])
    op.create_index(
        "idx_alerts_type_level",
        "ref_alerts",
        ["alert_type", "level"],
    )

    op.create_table(
        "rule_packs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slug", sa.String(length=128), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("jurisdiction", sa.String(length=32), nullable=False),
        sa.Column("authority", sa.String(length=128), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("definition", JSONB_TYPE, nullable=False),
        sa.Column("metadata", JSONB_TYPE, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
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
            onupdate=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("slug", "version", name="uq_rule_pack_slug_version"),
    )
    op.create_index("ix_rule_packs_slug", "rule_packs", ["slug"])
    op.create_index("ix_rule_packs_jurisdiction", "rule_packs", ["jurisdiction"])
    op.create_index("ix_rule_packs_is_active", "rule_packs", ["is_active"])
    op.create_index("ix_rule_packs_created_at", "rule_packs", ["created_at"])


def downgrade() -> None:
    """Revert the migration."""

    op.execute("DROP INDEX IF EXISTS ix_rule_packs_created_at")
    op.execute("DROP INDEX IF EXISTS ix_rule_packs_is_active")
    op.execute("DROP INDEX IF EXISTS ix_rule_packs_jurisdiction")
    op.execute("DROP INDEX IF EXISTS ix_rule_packs_slug")
    op.drop_table("rule_packs")

    op.execute("DROP INDEX IF EXISTS idx_alerts_type_level")
    op.execute("DROP INDEX IF EXISTS ix_ref_alerts_acknowledged")
    op.execute("DROP INDEX IF EXISTS ix_ref_alerts_created_at")
    op.execute("DROP INDEX IF EXISTS ix_ref_alerts_level")
    op.execute("DROP INDEX IF EXISTS ix_ref_alerts_alert_type")
    op.drop_table("ref_alerts")

    op.execute("DROP INDEX IF EXISTS idx_ingestion_runs_flow_status")
    op.execute("DROP INDEX IF EXISTS ix_ref_ingestion_runs_status")
    op.execute("DROP INDEX IF EXISTS ix_ref_ingestion_runs_flow_name")
    op.execute("DROP INDEX IF EXISTS ix_ref_ingestion_runs_run_key")
    op.drop_table("ref_ingestion_runs")

    op.execute("DROP INDEX IF EXISTS idx_cost_catalogs_category")
    op.execute("DROP INDEX IF EXISTS idx_cost_catalogs_name_code")
    op.execute("DROP INDEX IF EXISTS ix_ref_cost_catalogs_item_code")
    op.execute("DROP INDEX IF EXISTS ix_ref_cost_catalogs_category")
    op.execute("DROP INDEX IF EXISTS ix_ref_cost_catalogs_catalog_name")
    op.execute("DROP INDEX IF EXISTS ix_ref_cost_catalogs_jurisdiction")
    op.drop_table("ref_cost_catalogs")

    op.execute("DROP INDEX IF EXISTS idx_cost_indices_jurisdiction_category")
    op.execute("DROP INDEX IF EXISTS idx_cost_indices_series_period")
    op.execute("DROP INDEX IF EXISTS ix_ref_cost_indices_provider")
    op.execute("DROP INDEX IF EXISTS ix_ref_cost_indices_period")
    op.execute("DROP INDEX IF EXISTS ix_ref_cost_indices_category")
    op.execute("DROP INDEX IF EXISTS ix_ref_cost_indices_series_name")
    op.execute("DROP INDEX IF EXISTS ix_ref_cost_indices_jurisdiction")
    op.drop_table("ref_cost_indices")

    op.execute("DROP INDEX IF EXISTS idx_ergonomics_metric_population")
    op.execute("DROP INDEX IF EXISTS ix_ref_ergonomics_population")
    op.execute("DROP INDEX IF EXISTS ix_ref_ergonomics_metric_key")
    op.drop_table("ref_ergonomics")

    op.execute("DROP INDEX IF EXISTS idx_products_category_active")
    op.execute("DROP INDEX IF EXISTS idx_products_vendor_category")
    op.execute("DROP INDEX IF EXISTS ix_ref_products_is_active")
    op.execute("DROP INDEX IF EXISTS ix_ref_products_sku")
    op.execute("DROP INDEX IF EXISTS ix_ref_products_model_number")
    op.execute("DROP INDEX IF EXISTS ix_ref_products_brand")
    op.execute("DROP INDEX IF EXISTS ix_ref_products_category")
    op.execute("DROP INDEX IF EXISTS ix_ref_products_vendor")
    op.drop_table("ref_products")

    op.execute("DROP INDEX IF EXISTS idx_material_standards_type_property")
    op.execute("DROP INDEX IF EXISTS ix_ref_material_standards_property_key")
    op.execute("DROP INDEX IF EXISTS ix_ref_material_standards_standard_body")
    op.execute("DROP INDEX IF EXISTS ix_ref_material_standards_material_type")
    op.execute("DROP INDEX IF EXISTS ix_ref_material_standards_standard_code")
    op.execute("DROP INDEX IF EXISTS ix_ref_material_standards_jurisdiction")
    op.drop_table("ref_material_standards")

    op.execute("DROP INDEX IF EXISTS idx_geocode_cache_coords")
    op.execute("DROP INDEX IF EXISTS ix_ref_geocode_cache_address")
    op.drop_table("ref_geocode_cache")

    op.execute("DROP INDEX IF EXISTS idx_ref_zoning_layer_effective")
    op.execute("DROP INDEX IF EXISTS idx_ref_zoning_jurisdiction_zone")
    op.execute("DROP INDEX IF EXISTS ix_ref_zoning_layers_zone_code")
    op.execute("DROP INDEX IF EXISTS ix_ref_zoning_layers_layer_name")
    op.execute("DROP INDEX IF EXISTS ix_ref_zoning_layers_jurisdiction")
    op.drop_table("ref_zoning_layers")

    op.execute("DROP INDEX IF EXISTS idx_ref_parcels_jurisdiction_ref")
    op.execute("DROP INDEX IF EXISTS idx_ref_parcels_centroid")
    op.execute("DROP INDEX IF EXISTS ix_ref_parcels_parcel_ref")
    op.execute("DROP INDEX IF EXISTS ix_ref_parcels_jurisdiction")
    op.drop_table("ref_parcels")

    op.execute("DROP INDEX IF EXISTS idx_ref_rules_authority_status")
    op.execute("DROP INDEX IF EXISTS idx_ref_rules_parameter_key")
    op.execute("DROP INDEX IF EXISTS idx_ref_rules_jurisdiction_topic")
    op.execute("DROP INDEX IF EXISTS ix_ref_rules_is_published")
    op.execute("DROP INDEX IF EXISTS ix_ref_rules_review_status")
    op.execute("DROP INDEX IF EXISTS ix_ref_rules_parameter_key")
    op.execute("DROP INDEX IF EXISTS ix_ref_rules_clause_ref")
    op.execute("DROP INDEX IF EXISTS ix_ref_rules_topic")
    op.execute("DROP INDEX IF EXISTS ix_ref_rules_authority")
    op.execute("DROP INDEX IF EXISTS ix_ref_rules_jurisdiction")
    op.drop_table("ref_rules")

    op.execute("DROP INDEX IF EXISTS idx_ref_clauses_document_clause")
    op.execute("DROP INDEX IF EXISTS ix_ref_clauses_clause_ref")
    op.drop_table("ref_clauses")

    op.execute("DROP INDEX IF EXISTS ix_ref_documents_retrieved_at")
    op.execute("DROP INDEX IF EXISTS ix_ref_documents_suspected_update")
    op.execute("DROP INDEX IF EXISTS ix_ref_documents_file_hash")
    op.drop_table("ref_documents")

    op.execute("DROP INDEX IF EXISTS idx_ref_sources_jurisdiction_authority")
    op.execute("DROP INDEX IF EXISTS ix_ref_sources_is_active")
    op.execute("DROP INDEX IF EXISTS ix_ref_sources_topic")
    op.execute("DROP INDEX IF EXISTS ix_ref_sources_authority")
    op.execute("DROP INDEX IF EXISTS ix_ref_sources_jurisdiction")
    op.drop_table("ref_sources")

    op.execute("DROP INDEX IF EXISTS ix_overlay_run_locks_acquired_at")
    op.execute("DROP INDEX IF EXISTS idx_overlay_locks_active")
    op.execute("DROP INDEX IF EXISTS ix_overlay_run_locks_is_active")
    op.execute("DROP INDEX IF EXISTS ix_overlay_run_locks_source_geometry_id")
    op.execute("DROP INDEX IF EXISTS ix_overlay_run_locks_project_id")
    op.drop_table("overlay_run_locks")

    op.execute("DROP INDEX IF EXISTS ix_overlay_decisions_decided_at")
    op.execute("DROP INDEX IF EXISTS idx_overlay_decisions_project")
    op.execute("DROP INDEX IF EXISTS ix_overlay_decisions_decision")
    op.execute("DROP INDEX IF EXISTS ix_overlay_decisions_source_geometry_id")
    op.execute("DROP INDEX IF EXISTS ix_overlay_decisions_project_id")
    op.drop_table("overlay_decisions")

    op.execute("DROP INDEX IF EXISTS ix_overlay_suggestions_created_at")
    op.execute("DROP INDEX IF EXISTS ix_overlay_suggestions_status")
    op.execute("DROP INDEX IF EXISTS idx_overlay_suggestions_status")
    op.execute("DROP INDEX IF EXISTS ix_overlay_suggestions_source_geometry_id")
    op.execute("DROP INDEX IF EXISTS ix_overlay_suggestions_project_id")
    op.drop_table("overlay_suggestions")

    op.execute("DROP INDEX IF EXISTS ix_overlay_source_geometries_created_at")
    op.execute("DROP INDEX IF EXISTS ix_overlay_source_geometries_checksum")
    op.drop_index(
        "ix_overlay_source_geometries_project_id",
        table_name="overlay_source_geometries",
    )
    op.drop_table("overlay_source_geometries")

    op.execute("DROP INDEX IF EXISTS ix_imports_project_id")
    op.drop_table("imports")

    op.execute("DROP INDEX IF EXISTS idx_audit_logs_project_version")
    op.execute("DROP INDEX IF EXISTS idx_audit_logs_project_event")
    op.execute("DROP INDEX IF EXISTS ix_audit_logs_recorded_at")
    op.execute("DROP INDEX IF EXISTS ix_audit_logs_hash")
    op.execute("DROP INDEX IF EXISTS ix_audit_logs_version")
    op.execute("DROP INDEX IF EXISTS ix_audit_logs_event_type")
    op.execute("DROP INDEX IF EXISTS ix_audit_logs_project_id")
    op.drop_table("audit_logs")
