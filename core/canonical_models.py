"""Canonical data models for jurisdictions and regulations."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel, Field
from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class RegstackBase(DeclarativeBase):
    """Declarative base that shares naming conventions across the schema."""

    metadata = MetaData()
    __abstract__ = True


class JurisdictionORM(RegstackBase):
    """SQLAlchemy model for jurisdictions."""

    __tablename__ = "jurisdictions"

    code: Mapped[str] = mapped_column(String(length=50), primary_key=True)
    name: Mapped[str] = mapped_column(String(length=255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )

    regulations: Mapped[list[RegulationORM]] = relationship(
        back_populates="jurisdiction", cascade="all, delete-orphan"
    )


class RegulationORM(RegstackBase):
    """SQLAlchemy model representing a canonical regulation."""

    __tablename__ = "regulations"
    __table_args__ = (
        UniqueConstraint("jurisdiction_code", "external_id", name="uq_reg_external"),
        Index("ix_regulations_global_tags", "global_tags", postgresql_using="gin"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    jurisdiction_code: Mapped[str] = mapped_column(
        ForeignKey("jurisdictions.code", ondelete="CASCADE"), nullable=False
    )
    external_id: Mapped[str] = mapped_column(String(length=255), nullable=False)
    title: Mapped[str] = mapped_column(String(length=500), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    issued_on: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    effective_on: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    version: Mapped[Optional[str]] = mapped_column(String(length=50))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict)
    global_tags: Mapped[list[str]] = mapped_column(JSON, default=list)

    jurisdiction: Mapped[JurisdictionORM] = relationship(back_populates="regulations")
    mappings: Mapped[list[RegMappingORM]] = relationship(
        back_populates="regulation", cascade="all, delete-orphan"
    )
    provenance_entries: Mapped[list[ProvenanceORM]] = relationship(
        back_populates="regulation", cascade="all, delete-orphan"
    )


class RegMappingORM(RegstackBase):
    """SQLAlchemy model describing mapping relationships for a regulation."""

    __tablename__ = "reg_mappings"
    __table_args__ = (
        Index("ix_reg_mappings_payload", "payload", postgresql_using="gin"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    regulation_id: Mapped[int] = mapped_column(
        ForeignKey("regulations.id", ondelete="CASCADE"), nullable=False
    )
    mapping_type: Mapped[str] = mapped_column(String(length=100), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    regulation: Mapped[RegulationORM] = relationship(back_populates="mappings")


class ProvenanceORM(RegstackBase):
    """SQLAlchemy model capturing ingestion provenance."""

    __tablename__ = "provenance"
    __table_args__ = (
        UniqueConstraint(
            "regulation_id",
            "source_uri",
            "content_checksum",
            name="uq_provenance_reg_source_checksum_v2",
        ),
        Index(
            "ix_provenance_regulation_source",
            "regulation_id",
            "source_uri",
        ),
        Index("ix_provenance_source", "source_uri"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    regulation_id: Mapped[int] = mapped_column(
        ForeignKey("regulations.id", ondelete="CASCADE"), nullable=False
    )
    source_uri: Mapped[str] = mapped_column(String(length=1024), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    fetch_parameters: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    raw_content: Mapped[str] = mapped_column(Text, nullable=False)
    content_checksum: Mapped[str] = mapped_column(String(length=64), nullable=False)

    regulation: Mapped[RegulationORM] = relationship(
        back_populates="provenance_entries"
    )


class CanonicalJurisdiction(BaseModel):
    """Pydantic model for jurisdiction metadata."""

    code: str
    name: str


class CanonicalReg(BaseModel):
    """Jurisdiction-agnostic representation of a regulation."""

    jurisdiction_code: str
    external_id: str
    title: str
    text: str
    issued_on: date | None = None
    effective_on: date | None = None
    version: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    global_tags: list[str] = Field(default_factory=list)

    model_config = {"extra": "ignore"}


class CanonicalMapping(BaseModel):
    """Mapping metadata for a regulation."""

    regulation_external_id: str
    mapping_type: str
    payload: dict[str, Any]


class ProvenanceRecord(BaseModel):
    """Provenance metadata for a regulation ingestion."""

    regulation_external_id: str
    source_uri: str
    fetched_at: datetime
    fetch_parameters: dict[str, Any] = Field(default_factory=dict)
    raw_content: str
