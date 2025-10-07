"""Entitlements domain models."""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Optional

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy import (
    Enum as SAEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import BaseModel, MetadataProxy
from app.models.types import FlexibleJSONB

JSONType = FlexibleJSONB


class EntApprovalCategory(str, Enum):
    """Categories describing the type of approval required."""

    PLANNING = "planning"
    BUILDING = "building"
    ENVIRONMENTAL = "environmental"
    TRANSPORT = "transport"
    UTILITIES = "utilities"


class EntRoadmapStatus(str, Enum):
    """Lifecycle statuses for roadmap items."""

    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    BLOCKED = "blocked"
    COMPLETE = "complete"


class EntStudyType(str, Enum):
    """Types of technical studies tracked in the entitlement process."""

    TRAFFIC = "traffic"
    ENVIRONMENTAL = "environmental"
    HERITAGE = "heritage"
    UTILITIES = "utilities"
    COMMUNITY = "community"


class EntStudyStatus(str, Enum):
    """Lifecycle statuses for entitlement studies."""

    DRAFT = "draft"
    SCOPE_DEFINED = "scope_defined"
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class EntEngagementType(str, Enum):
    """Stakeholder engagement categories."""

    AGENCY = "agency"
    COMMUNITY = "community"
    POLITICAL = "political"
    PRIVATE_PARTNER = "private_partner"
    REGULATOR = "regulator"


class EntEngagementStatus(str, Enum):
    """Lifecycle statuses for stakeholder engagements."""

    PLANNED = "planned"
    ACTIVE = "active"
    COMPLETED = "completed"
    BLOCKED = "blocked"


class EntLegalInstrumentType(str, Enum):
    """Categories of legal instruments tracked for entitlement delivery."""

    AGREEMENT = "agreement"
    LICENCE = "licence"
    MEMORANDUM = "memorandum"
    WAIVER = "waiver"
    VARIATION = "variation"


class EntLegalInstrumentStatus(str, Enum):
    """Lifecycle statuses for legal instruments."""

    DRAFT = "draft"
    IN_REVIEW = "in_review"
    EXECUTED = "executed"
    EXPIRED = "expired"


class EntAuthority(BaseModel):
    """Regulatory authorities participating in the entitlement process."""

    __tablename__ = "ent_authorities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    jurisdiction: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    slug: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    website: Mapped[Optional[str]] = mapped_column(String(255))
    contact_email: Mapped[Optional[str]] = mapped_column(String(120))
    metadata_json: Mapped[dict] = mapped_column(
        "metadata", JSONType, default=dict, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    approval_types: Mapped[list[EntApprovalType]] = relationship(
        back_populates="authority", cascade="all, delete-orphan"
    )
    metadata = MetadataProxy()

    __table_args__ = (Index("ix_ent_authority_slug", "slug"),)


class EntApprovalType(BaseModel):
    """Specific approvals issued by an authority."""

    __tablename__ = "ent_approval_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    authority_id: Mapped[int] = mapped_column(
        ForeignKey("ent_authorities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(60), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    category: Mapped[EntApprovalCategory] = mapped_column(
        SAEnum(EntApprovalCategory, name="ent_approval_category"), nullable=False
    )
    description: Mapped[Optional[str]] = mapped_column(Text)
    requirements: Mapped[dict] = mapped_column(JSONType, default=dict, nullable=False)
    processing_time_days: Mapped[Optional[int]] = mapped_column(Integer)
    is_mandatory: Mapped[bool] = mapped_column(default=True, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(
        "metadata", JSONType, default=dict, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    authority: Mapped[EntAuthority] = relationship(back_populates="approval_types")
    roadmap_items: Mapped[list[EntRoadmapItem]] = relationship(
        back_populates="approval_type"
    )
    metadata = MetadataProxy()

    __table_args__ = (
        Index("uq_ent_approval_type_code", "authority_id", "code", unique=True),
    )


class EntRoadmapItem(BaseModel):
    """Sequenced roadmap item for a project entitlement."""

    __tablename__ = "ent_roadmap_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    approval_type_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("ent_approval_types.id", ondelete="SET NULL"), index=True
    )
    sequence_order: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[EntRoadmapStatus] = mapped_column(
        SAEnum(EntRoadmapStatus, name="ent_roadmap_status"), nullable=False
    )
    status_changed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    target_submission_date: Mapped[Optional[date]] = mapped_column(Date)
    target_decision_date: Mapped[Optional[date]] = mapped_column(Date)
    actual_submission_date: Mapped[Optional[date]] = mapped_column(Date)
    actual_decision_date: Mapped[Optional[date]] = mapped_column(Date)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column(
        "metadata", JSONType, default=dict, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    approval_type: Mapped[Optional[EntApprovalType]] = relationship(
        back_populates="roadmap_items"
    )
    metadata = MetadataProxy()

    __table_args__ = (
        Index(
            "idx_ent_roadmap_project_sequence",
            "project_id",
            "sequence_order",
            unique=True,
        ),
        CheckConstraint(
            "sequence_order >= 1", name="chk_ent_roadmap_sequence_positive"
        ),
    )


class EntStudy(BaseModel):
    """Technical study required for entitlement approvals."""

    __tablename__ = "ent_studies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    study_type: Mapped[EntStudyType] = mapped_column(
        SAEnum(EntStudyType, name="ent_study_type"), nullable=False
    )
    status: Mapped[EntStudyStatus] = mapped_column(
        SAEnum(EntStudyStatus, name="ent_study_status"), nullable=False
    )
    summary: Mapped[Optional[str]] = mapped_column(Text)
    consultant: Mapped[Optional[str]] = mapped_column(String(120))
    due_date: Mapped[Optional[date]] = mapped_column(Date)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    attachments: Mapped[list] = mapped_column(JSONType, default=list, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(
        "metadata", JSONType, default=dict, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    metadata = MetadataProxy()


class EntEngagement(BaseModel):
    """Stakeholder engagement records tied to a project."""

    __tablename__ = "ent_engagements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    organisation: Mapped[Optional[str]] = mapped_column(String(150))
    engagement_type: Mapped[EntEngagementType] = mapped_column(
        SAEnum(EntEngagementType, name="ent_engagement_type"), nullable=False
    )
    status: Mapped[EntEngagementStatus] = mapped_column(
        SAEnum(EntEngagementStatus, name="ent_engagement_status"), nullable=False
    )
    contact_email: Mapped[Optional[str]] = mapped_column(String(120))
    contact_phone: Mapped[Optional[str]] = mapped_column(String(40))
    meetings: Mapped[list] = mapped_column(JSONType, default=list, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column(
        "metadata", JSONType, default=dict, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    metadata = MetadataProxy()


class EntLegalInstrument(BaseModel):
    """Legal instruments formalising entitlement decisions."""

    __tablename__ = "ent_legal_instruments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    instrument_type: Mapped[EntLegalInstrumentType] = mapped_column(
        SAEnum(EntLegalInstrumentType, name="ent_legal_instrument_type"), nullable=False
    )
    status: Mapped[EntLegalInstrumentStatus] = mapped_column(
        SAEnum(EntLegalInstrumentStatus, name="ent_legal_instrument_status"),
        nullable=False,
    )
    reference_code: Mapped[Optional[str]] = mapped_column(String(80))
    effective_date: Mapped[Optional[date]] = mapped_column(Date)
    expiry_date: Mapped[Optional[date]] = mapped_column(Date)
    attachments: Mapped[list] = mapped_column(JSONType, default=list, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(
        "metadata", JSONType, default=dict, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    metadata = MetadataProxy()


__all__ = [
    "EntApprovalCategory",
    "EntRoadmapStatus",
    "EntStudyType",
    "EntStudyStatus",
    "EntEngagementType",
    "EntEngagementStatus",
    "EntLegalInstrumentType",
    "EntLegalInstrumentStatus",
    "EntAuthority",
    "EntApprovalType",
    "EntRoadmapItem",
    "EntStudy",
    "EntEngagement",
    "EntLegalInstrument",
]
