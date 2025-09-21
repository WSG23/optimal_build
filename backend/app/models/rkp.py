"""Reference Knowledge Platform (RKP) models."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import BaseModel
from app.models.types import FlexibleJSONB


JSONType = FlexibleJSONB


class RefSource(BaseModel):
    """Reference source model for document tracking."""

    __tablename__ = "ref_sources"

    id = Column(Integer, primary_key=True, index=True)
    jurisdiction = Column(String(10), nullable=False, index=True)  # 'SG'
    authority = Column(String(50), nullable=False, index=True)  # 'SCDF', 'PUB', 'URA', 'BCA'
    topic = Column(String(50), nullable=False, index=True)  # 'fire', 'plumbing', 'zoning'
    doc_title = Column(Text, nullable=False)
    landing_url = Column(Text, nullable=False)
    fetch_kind = Column(
        String(20),
        CheckConstraint("fetch_kind IN ('pdf', 'html', 'sitemap')"),
        default="pdf",
    )
    update_freq_hint = Column(String(50))  # 'annual', 'quarterly'
    selectors = Column(JSONType)  # CSS selectors for HTML parsing
    is_active = Column(Boolean, default=True, index=True)

    # Relationships
    documents = relationship("RefDocument", back_populates="source", cascade="all, delete-orphan")
    rules = relationship("RefRule", back_populates="source")

    __table_args__ = (
        Index("idx_ref_sources_jurisdiction_authority", "jurisdiction", "authority"),
    )


class RefDocument(BaseModel):
    """Reference document model for version tracking."""

    __tablename__ = "ref_documents"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("ref_sources.id", ondelete="CASCADE"), nullable=False)
    version_label = Column(String(100))  # '2024-v1', 'Amendment-3'
    retrieved_at = Column(DateTime(timezone=True), server_default=func.now())
    storage_path = Column(Text, nullable=False)  # S3 path or local path
    file_hash = Column(String(64), nullable=False, index=True)  # SHA-256 hash
    http_etag = Column(String(200))
    http_last_modified = Column(String(200))
    suspected_update = Column(Boolean, default=False, index=True)

    # Relationships
    source = relationship("RefSource", back_populates="documents")
    clauses = relationship("RefClause", back_populates="document", cascade="all, delete-orphan")
    rules = relationship("RefRule", back_populates="document")


class RefClause(BaseModel):
    """Reference clause model for extracted text segments."""

    __tablename__ = "ref_clauses"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("ref_documents.id", ondelete="CASCADE"), nullable=False)
    clause_ref = Column(String(50), index=True)  # '4.2.1', 'Section A.3'
    section_heading = Column(Text)
    text_span = Column(Text, nullable=False)
    page_from = Column(Integer)
    page_to = Column(Integer)
    extraction_quality = Column(String(20))  # 'high', 'medium', 'low'

    # Relationships
    document = relationship("RefDocument", back_populates="clauses")

    __table_args__ = (
        Index("idx_ref_clauses_document_clause", "document_id", "clause_ref"),
    )


class RefRule(BaseModel):
    """Reference rule model - the core building code rules."""

    __tablename__ = "ref_rules"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("ref_sources.id", ondelete="SET NULL"))
    document_id = Column(Integer, ForeignKey("ref_documents.id", ondelete="SET NULL"))

    # Core rule identification
    jurisdiction = Column(String(10), nullable=False, index=True)  # 'SG'
    authority = Column(String(50), nullable=False, index=True)  # 'SCDF', 'PUB', 'URA', 'BCA'
    topic = Column(String(50), nullable=False, index=True)  # 'fire', 'plumbing', 'zoning'
    clause_ref = Column(String(50), index=True)  # '4.2.1'

    # Rule specification
    parameter_key = Column(String(200), nullable=False, index=True)  # 'egress.corridor.min_width_mm'
    operator = Column(String(10), nullable=False)  # '>=', '<=', '='
    value = Column(Text, nullable=False)  # '1200'
    unit = Column(String(20))  # 'mm', 'm', '%'

    # Context and applicability
    applicability = Column(JSONType)  # {"occupancy": ["residential"], "height": "any"}
    exceptions = Column(JSONType)  # ["except for existing buildings"]
    source_provenance = Column(JSONType)  # {"document_id": 123, "pages": [37]}

    # Review workflow
    review_status = Column(
        String(20),
        CheckConstraint("review_status IN ('needs_review', 'approved', 'rejected')"),
        default="needs_review",
        index=True,
    )
    reviewer = Column(String(100))
    reviewed_at = Column(DateTime(timezone=True))
    notes = Column(Text)
    is_published = Column(Boolean, default=False, index=True)
    published_at = Column(DateTime(timezone=True))

    # Relationships
    source = relationship("RefSource", back_populates="rules")
    document = relationship("RefDocument", back_populates="rules")

    __table_args__ = (
        Index("idx_ref_rules_jurisdiction_topic", "jurisdiction", "topic"),
        Index("idx_ref_rules_parameter_key", "parameter_key"),
        Index("idx_ref_rules_authority_status", "authority", "review_status"),
    )


class RefParcel(BaseModel):
    """Reference parcel model for land boundaries (simplified without PostGIS for now)."""

    __tablename__ = "ref_parcels"

    id = Column(Integer, primary_key=True, index=True)
    jurisdiction = Column(String(10), nullable=False, index=True, default="SG")
    parcel_ref = Column(String(100), index=True)  # URA lot number

    # Simplified geometry as JSON for now (will upgrade to PostGIS later)
    bounds_json = Column(JSONType)  # {"type": "Polygon", "coordinates": [...]}  
    centroid_lat = Column(Numeric(10, 7))
    centroid_lon = Column(Numeric(10, 7))
    area_m2 = Column(Numeric(12, 2))

    source = Column(String(50))  # 'upload', 'onemap', 'ura'

    __table_args__ = (
        Index("idx_ref_parcels_centroid", "centroid_lat", "centroid_lon"),
        Index("idx_ref_parcels_jurisdiction_ref", "jurisdiction", "parcel_ref"),
    )


class RefZoningLayer(BaseModel):
    """Reference zoning layer model for URA Master Plan data."""

    __tablename__ = "ref_zoning_layers"

    id = Column(Integer, primary_key=True, index=True)
    jurisdiction = Column(String(10), nullable=False, index=True, default="SG")
    layer_name = Column(String(100), index=True)  # 'MasterPlan2019'
    zone_code = Column(String(20), index=True)  # 'R2', 'C1', 'B1'

    # Zoning attributes
    attributes = Column(JSONType)  # {"far": 3.5, "height_m": 36, "overlays": ["coastal"]}

    # Simplified geometry as JSON for now
    bounds_json = Column(JSONType)  # GeoJSON MultiPolygon

    effective_date = Column(DateTime(timezone=True))
    expiry_date = Column(DateTime(timezone=True))

    __table_args__ = (
        Index("idx_ref_zoning_jurisdiction_zone", "jurisdiction", "zone_code"),
        Index("idx_ref_zoning_layer_effective", "layer_name", "effective_date"),
    )


class RefGeocodeCache(BaseModel):
    """Geocoding cache for address lookups."""

    __tablename__ = "ref_geocode_cache"

    id = Column(Integer, primary_key=True, index=True)
    address = Column(Text, unique=True, nullable=False, index=True)
    lat = Column(Numeric(10, 7))
    lon = Column(Numeric(10, 7))
    parcel_id = Column(Integer, ForeignKey("ref_parcels.id"), nullable=True)
    confidence_score = Column(Numeric(3, 2))  # 0.0 to 1.0

    # Cache management
    cache_expires_at = Column(DateTime(timezone=True))
    is_verified = Column(Boolean, default=False)

    # Relationships
    parcel = relationship("RefParcel")

    __table_args__ = (
        Index("idx_geocode_cache_coords", "lat", "lon"),
    )


# Phase 2 Models (Standards, Catalog, Ergonomics, Costs)


class RefMaterialStandard(BaseModel):
    """Material standards reference for Phase 2."""

    __tablename__ = "ref_material_standards"

    id = Column(Integer, primary_key=True, index=True)
    jurisdiction = Column(String(10), nullable=False, index=True, default="SG")
    standard_code = Column(String(50), nullable=False, index=True)  # 'SS EN 206'
    material_type = Column(String(100), nullable=False, index=True)  # 'concrete', 'steel'
    standard_body = Column(String(100), nullable=False, index=True)
    property_key = Column(String(200), nullable=False, index=True)  # 'compressive_strength_mpa'
    value = Column(Text, nullable=False)
    unit = Column(String(20))
    context = Column(JSONType)
    section = Column(String(100))
    applicability = Column(JSONType)
    edition = Column(String(50))
    effective_date = Column(Date)
    license_ref = Column(String(100))
    provenance = Column(JSONType)
    source_document = Column(Text)

    __table_args__ = (
        Index("idx_material_standards_type_property", "material_type", "property_key"),
    )


class RefProduct(BaseModel):
    """Product catalog reference for Phase 2."""

    __tablename__ = "ref_products"

    id = Column(Integer, primary_key=True, index=True)
    vendor = Column(String(100), nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)  # 'toilet', 'basin', 'door'
    product_code = Column(String(100), nullable=False)
    name = Column(String(200), nullable=False)
    brand = Column(String(100), index=True)
    model_number = Column(String(100), index=True)
    sku = Column(String(100), index=True)

    # Product specifications
    dimensions = Column(JSONType)  # {"width_mm": 600, "depth_mm": 400, "height_mm": 850}
    specifications = Column(JSONType)  # {"material": "ceramic", "flush_volume_l": 4.8}
    bim_uri = Column(Text)
    spec_uri = Column(Text)
    unit_cost = Column(Numeric(10, 2))
    currency = Column(String(3), default="SGD")

    is_active = Column(Boolean, default=True, index=True)

    __table_args__ = (
        Index("idx_products_vendor_category", "vendor", "category"),
        Index("idx_products_category_active", "category", "is_active"),
    )


class RefErgonomics(BaseModel):
    """Human factors and ergonomics reference for Phase 2."""

    __tablename__ = "ref_ergonomics"

    id = Column(Integer, primary_key=True, index=True)
    metric_key = Column(String(200), nullable=False, index=True)  # 'wheelchair.turning_radius_mm'
    population = Column(String(50), nullable=False, index=True)  # 'adult', 'elderly', 'wheelchair'
    percentile = Column(String(10))  # '5th', '50th', '95th'
    value = Column(Numeric(8, 2), nullable=False)
    unit = Column(String(20), nullable=False)
    context = Column(JSONType)  # {"space_type": "bathroom", "condition": "seated"}
    notes = Column(Text)
    source = Column(String(100))

    __table_args__ = (
        Index("idx_ergonomics_metric_population", "metric_key", "population"),
    )


class RefCostIndex(BaseModel):
    """Cost benchmark indices for Phase 2."""

    __tablename__ = "ref_cost_indices"

    id = Column(Integer, primary_key=True, index=True)
    jurisdiction = Column(String(10), nullable=False, index=True, default="SG")
    series_name = Column(String(100), nullable=False, index=True)  # 'concrete', 'steel', 'labor'
    category = Column(String(50), nullable=False, index=True)  # 'material', 'labor', 'equipment'
    subcategory = Column(String(100))  # 'ready_mix', 'skilled'
    period = Column(String(20), nullable=False, index=True)  # '2024-Q1'
    value = Column(Numeric(12, 4), nullable=False)
    unit = Column(String(50), nullable=False)  # 'SGD/m3', 'SGD/hour'
    source = Column(String(100))
    provider = Column(String(100), nullable=False, index=True, default="internal")
    methodology = Column(Text)

    __table_args__ = (
        Index("idx_cost_indices_series_period", "series_name", "period"),
        Index("idx_cost_indices_jurisdiction_category", "jurisdiction", "category"),
    )


class RefCostCatalog(BaseModel):
    """Detailed cost catalog references."""

    __tablename__ = "ref_cost_catalogs"

    id = Column(Integer, primary_key=True, index=True)
    jurisdiction = Column(String(10), nullable=False, index=True, default="SG")
    catalog_name = Column(String(100), nullable=False, index=True)
    category = Column(String(50), index=True)
    item_code = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    unit = Column(String(20))
    unit_cost = Column(Numeric(12, 2))
    currency = Column(String(3), default="SGD")
    effective_date = Column(Date)
    item_metadata = Column(JSONType)
    source = Column(String(100))

    __table_args__ = (
        Index("idx_cost_catalogs_name_code", "catalog_name", "item_code"),
        Index("idx_cost_catalogs_category", "category"),
    )


class RefIngestionRun(BaseModel):
    """Prefect ingestion run metadata."""

    __tablename__ = "ref_ingestion_runs"

    id = Column(Integer, primary_key=True, index=True)
    run_key = Column(String(100), nullable=False, unique=True, index=True)
    flow_name = Column(String(100), nullable=False, index=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    finished_at = Column(DateTime(timezone=True))
    status = Column(String(20), nullable=False, index=True, default="running")
    records_ingested = Column(Integer, default=0)
    suspected_updates = Column(Integer, default=0)
    notes = Column(Text)
    metrics = Column(JSONType)

    alerts = relationship("RefAlert", back_populates="ingestion_run", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_ingestion_runs_flow_status", "flow_name", "status"),
    )


class RefAlert(BaseModel):
    """Alert records for ingestion anomalies."""

    __tablename__ = "ref_alerts"

    id = Column(Integer, primary_key=True, index=True)
    alert_type = Column(String(50), nullable=False, index=True)
    level = Column(String(20), nullable=False, index=True, default="info")
    message = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    context = Column(JSONType)
    ingestion_run_id = Column(Integer, ForeignKey("ref_ingestion_runs.id", ondelete="SET NULL"))
    acknowledged = Column(Boolean, default=False, index=True)
    acknowledged_at = Column(DateTime(timezone=True))
    acknowledged_by = Column(String(100))

    ingestion_run = relationship("RefIngestionRun", back_populates="alerts")

    __table_args__ = (
        Index("idx_alerts_type_level", "alert_type", "level"),
    )
