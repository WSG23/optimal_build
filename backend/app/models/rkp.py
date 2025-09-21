"""Reference Knowledge Platform (RKP) models."""

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    CheckConstraint,
    Numeric,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from geoalchemy2 import Geometry

from app.models.base import BaseModel


class RefSource(BaseModel):
    """Reference source model."""

    __tablename__ = "ref_sources"

    id = Column(Integer, primary_key=True, index=True)
    jurisdiction = Column(String(10), nullable=False, index=True)
    authority = Column(String(50), nullable=False, index=True)
    topic = Column(String(50), nullable=False, index=True)
    doc_title = Column(Text, nullable=False)
    landing_url = Column(Text, nullable=False)
    fetch_kind = Column(
        String(20),
        CheckConstraint("fetch_kind IN ('pdf', 'html', 'sitemap')"),
        default="pdf",
    )
    update_freq_hint = Column(String(50))
    selectors = Column(JSONB)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    documents = relationship("RefDocument", back_populates="source", cascade="all, delete-orphan")
    rules = relationship("RefRule", back_populates="source")


class RefDocument(BaseModel):
    """Reference document model."""

    __tablename__ = "ref_documents"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("ref_sources.id", ondelete="CASCADE"), nullable=False)
    version_label = Column(String(100))
    retrieved_at = Column(DateTime(timezone=True), server_default=func.now())
    storage_path = Column(Text, nullable=False)
    file_hash = Column(String(64), nullable=False)
    http_etag = Column(String(200))
    http_last_modified = Column(String(200))
    suspected_update = Column(Boolean, default=False)

    # Relationships
    source = relationship("RefSource", back_populates="documents")
    clauses = relationship("RefClause", back_populates="document", cascade="all, delete-orphan")
    rules = relationship("RefRule", back_populates="document")


class RefClause(BaseModel):
    """Reference clause model."""

    __tablename__ = "ref_clauses"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("ref_documents.id", ondelete="CASCADE"), nullable=False)
    clause_ref = Column(String(50), index=True)
    section_heading = Column(Text)
    text_span = Column(Text, nullable=False)
    page_from = Column(Integer)
    page_to = Column(Integer)
    extraction_quality = Column(String(20))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    document = relationship("RefDocument", back_populates="clauses")


class RefRule(BaseModel):
    """Reference rule model."""

    __tablename__ = "ref_rules"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("ref_sources.id", ondelete="SET NULL"))
    document_id = Column(Integer, ForeignKey("ref_documents.id", ondelete="SET NULL"))
    jurisdiction = Column(String(10), nullable=False, index=True)
    authority = Column(String(50), nullable=False, index=True)
    topic = Column(String(50), nullable=False, index=True)
    clause_ref = Column(String(50), index=True)
    parameter_key = Column(String(200), nullable=False, index=True)
    operator = Column(String(10), nullable=False)
    value = Column(Text, nullable=False)
    unit = Column(String(20))
    applicability = Column(JSONB)
    exceptions = Column(JSONB)
    source_provenance = Column(JSONB)
    review_status = Column(
        String(20),
        CheckConstraint("review_status IN ('needs_review', 'approved', 'rejected')"),
        default="needs_review",
        index=True,
    )
    reviewer = Column(String(100))
    reviewed_at = Column(DateTime(timezone=True))
    notes = Column(Text)

    # Relationships
    source = relationship("RefSource", back_populates="rules")
    document = relationship("RefDocument", back_populates="rules")


class RefParcel(BaseModel):
    """Reference parcel model for GIS data."""

    __tablename__ = "ref_parcels"

    id = Column(Integer, primary_key=True, index=True)
    jurisdiction = Column(String(10), nullable=False, index=True, default="SG")
    parcel_ref = Column(String(100), index=True)  # lot id if available
    geom = Column(Geometry("POLYGON", srid=4326))  # WGS84 coordinate system
    area_m2 = Column(Numeric(12, 2))
    source = Column(String(50))  # 'upload', 'onemap', 'ura'
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class RefZoningLayer(BaseModel):
    """Reference zoning layer model."""

    __tablename__ = "ref_zoning_layers"

    id = Column(Integer, primary_key=True, index=True)
    jurisdiction = Column(String(10), nullable=False, index=True, default="SG")
    layer_name = Column(String(100), index=True)  # 'MasterPlan2019'
    zone_code = Column(String(20), index=True)  # 'R2', 'C1', 'B1'
    attributes = Column(JSONB)  # {"far":3.5,"height_m":36,"overlay":["coastal"]}
    geom = Column(Geometry("MULTIPOLYGON", srid=4326))


class RefGeocodeCache(BaseModel):
    """Geocoding cache for address lookups."""

    __tablename__ = "ref_geocode_cache"

    id = Column(Integer, primary_key=True, index=True)
    address = Column(Text, unique=True, nullable=False, index=True)
    lat = Column(Numeric(10, 7))
    lon = Column(Numeric(10, 7))
    parcel_id = Column(Integer, ForeignKey("ref_parcels.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    parcel = relationship("RefParcel")


class RefMaterialStandard(BaseModel):
    """Material standards reference."""

    __tablename__ = "ref_material_standards"

    id = Column(Integer, primary_key=True, index=True)
    jurisdiction = Column(String(10), nullable=False, index=True, default="SG")
    standard_code = Column(String(50), nullable=False, index=True)
    material_type = Column(String(100), nullable=False, index=True)
    property_key = Column(String(200), nullable=False, index=True)
    value = Column(Text, nullable=False)
    unit = Column(String(20))
    context = Column(JSONB)  # application context
    source_document = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class RefProduct(BaseModel):
    """Product catalog reference."""

    __tablename__ = "ref_products"

    id = Column(Integer, primary_key=True, index=True)
    vendor = Column(String(100), nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)
    product_code = Column(String(100), nullable=False)
    name = Column(String(200), nullable=False)
    dimensions = Column(JSONB)  # {"width_mm": 600, "depth_mm": 400, "height_mm": 850}
    specifications = Column(JSONB)
    unit_cost = Column(Numeric(10, 2))
    currency = Column(String(3), default="SGD")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class RefErgonomics(BaseModel):
    """Human factors and ergonomics reference."""

    __tablename__ = "ref_ergonomics"

    id = Column(Integer, primary_key=True, index=True)
    metric_key = Column(String(200), nullable=False, index=True)
    population = Column(String(50), nullable=False, index=True)  # 'adult', 'elderly', 'wheelchair'
    percentile = Column(String(10))  # '5th', '50th', '95th'
    value = Column(Numeric(8, 2), nullable=False)
    unit = Column(String(20), nullable=False)
    context = Column(JSONB)
    source = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class RefCostIndex(BaseModel):
    """Cost benchmark indices."""

    __tablename__ = "ref_cost_indices"

    id = Column(Integer, primary_key=True, index=True)
    jurisdiction = Column(String(10), nullable=False, index=True, default="SG")
    series_name = Column(String(100), nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)
    subcategory = Column(String(100))
    period = Column(String(20), nullable=False, index=True)  # '2024-Q1'
    value = Column(Numeric(12, 2), nullable=False)
    unit = Column(String(50), nullable=False)
    source = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
