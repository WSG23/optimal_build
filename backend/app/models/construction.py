"""Construction delivery models for Phase 2G.

Phase 2G: Construction & Project Delivery
- Contractor coordination
- Quality control & Safety monitoring
- Construction financing (Drawdowns)
"""

from __future__ import annotations

import uuid as uuid_module
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from app.models.base import UUID, BaseModel
from app.models.types import FlexibleJSONB
from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

JSONType = FlexibleJSONB


class ContractorType(str, Enum):
    """Types of contractors."""

    GENERAL_CONTRACTOR = "general_contractor"
    SUB_CONTRACTOR = "sub_contractor"
    SPECIALIST = "specialist"
    CONSULTANT = "consultant"
    SUPPLIER = "supplier"


class InspectionStatus(str, Enum):
    """Status of quality inspection."""

    SCHEDULED = "scheduled"
    PASSED = "passed"
    FAILED = "failed"
    PASSED_WITH_CONDITIONS = "passed_with_conditions"
    RECTIFICATION_REQUIRED = "rectification_required"


class SeverityLevel(str, Enum):
    """Severity of safety incident."""

    NEAR_MISS = "near_miss"
    MINOR = "minor"
    MODERATE = "moderate"
    SEVERE = "severe"
    FATAL = "fatal"


class DrawdownStatus(str, Enum):
    """Status of finance drawdown request."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    VERIFIED_QS = "verified_qs"
    APPROVED_ARCHITECT = "approved_architect"
    APPROVED_LENDER = "approved_lender"
    PAID = "paid"
    REJECTED = "rejected"


class Contractor(BaseModel):
    """Contractor or vendor involved in the project."""

    __tablename__ = "contractors"

    id: Mapped[UUID] = mapped_column(
        UUID(), primary_key=True, default=uuid_module.uuid4
    )
    project_id: Mapped[UUID] = mapped_column(
        UUID(),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    company_name: Mapped[str] = mapped_column(String(200), nullable=False)
    contractor_type: Mapped[ContractorType] = mapped_column(
        SQLEnum(ContractorType, values_callable=lambda x: [e.value for e in x]),
        default=ContractorType.GENERAL_CONTRACTOR,
        nullable=False,
    )
    contact_person: Mapped[Optional[str]] = mapped_column(String(100))
    email: Mapped[Optional[str]] = mapped_column(String(200))  # Should check format
    phone: Mapped[Optional[str]] = mapped_column(String(50))

    contract_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(16, 2))
    contract_date: Mapped[Optional[date]] = mapped_column(Date)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    metadata_json: Mapped[dict] = mapped_column(
        "metadata", JSONType, default=dict, nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    project = relationship("Project", backref="contractors")


class QualityInspection(BaseModel):
    """Quality control inspection record."""

    __tablename__ = "quality_inspections"

    id: Mapped[UUID] = mapped_column(
        UUID(), primary_key=True, default=uuid_module.uuid4
    )
    project_id: Mapped[UUID] = mapped_column(
        UUID(),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Link to generic development phase if applicable
    development_phase_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("development_phases.id", ondelete="SET NULL"), nullable=True
    )

    inspection_date: Mapped[date] = mapped_column(Date, nullable=False)
    inspector_name: Mapped[str] = mapped_column(String(100), nullable=False)
    location: Mapped[str] = mapped_column(String(200))  # E.g. "Level 1 Slab"

    status: Mapped[InspectionStatus] = mapped_column(
        SQLEnum(InspectionStatus, values_callable=lambda x: [e.value for e in x]),
        default=InspectionStatus.SCHEDULED,
        nullable=False,
    )

    defects_found: Mapped[dict] = mapped_column(JSONType, default=dict)  # List of items
    photos_url: Mapped[Optional[list[str]]] = mapped_column(JSONType, default=list)

    notes: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    development_phase = relationship("DevelopmentPhase")


class SafetyIncident(BaseModel):
    """Safety incident or observation log."""

    __tablename__ = "safety_incidents"

    id: Mapped[UUID] = mapped_column(
        UUID(), primary_key=True, default=uuid_module.uuid4
    )
    project_id: Mapped[UUID] = mapped_column(
        UUID(),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    incident_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    severity: Mapped[SeverityLevel] = mapped_column(
        SQLEnum(SeverityLevel, values_callable=lambda x: [e.value for e in x]),
        default=SeverityLevel.MINOR,
        nullable=False,
    )

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    location: Mapped[Optional[str]] = mapped_column(String(200))

    reported_by: Mapped[Optional[str]] = mapped_column(String(100))
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class DrawdownRequest(BaseModel):
    """Construction finance drawdown request."""

    __tablename__ = "drawdown_requests"

    id: Mapped[UUID] = mapped_column(
        UUID(), primary_key=True, default=uuid_module.uuid4
    )
    project_id: Mapped[UUID] = mapped_column(
        UUID(),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    request_name: Mapped[str] = mapped_column(
        String(200), nullable=False
    )  # e.g. "Drawdown #3 - Foundation"
    request_date: Mapped[date] = mapped_column(Date, nullable=False)

    amount_requested: Mapped[Decimal] = mapped_column(Numeric(16, 2), nullable=False)
    amount_approved: Mapped[Optional[Decimal]] = mapped_column(Numeric(16, 2))

    status: Mapped[DrawdownStatus] = mapped_column(
        SQLEnum(DrawdownStatus, values_callable=lambda x: [e.value for e in x]),
        default=DrawdownStatus.DRAFT,
        nullable=False,
    )

    contractor_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(), ForeignKey("contractors.id", ondelete="SET NULL"), nullable=True
    )

    supporting_docs: Mapped[list[str]] = mapped_column(JSONType, default=list)

    notes: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    contractor = relationship("Contractor")
