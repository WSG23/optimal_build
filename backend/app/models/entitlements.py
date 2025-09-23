"""Entitlements domain models."""

from __future__ import annotations

from datetime import date, datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    Date,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel
from .types import FlexibleJSONB


def _utcnow() -> datetime:
    """Return the current UTC time."""

    return datetime.now(timezone.utc)


class EntitlementStatus(str, Enum):
    """Overall progression state for entitlement artefacts."""

    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    ON_HOLD = "on_hold"
    ARCHIVED = "archived"


class EntitlementStudyType(str, Enum):
    """Categories of consultant or authority studies."""

    TRAFFIC = "traffic"
    ENVIRONMENTAL = "environmental"
    INFRASTRUCTURE = "infrastructure"
    HERITAGE = "heritage"
    OTHER = "other"


class StakeholderKind(str, Enum):
    """Stakeholder groupings for engagement tracking."""

    AGENCY = "agency"
    COMMUNITY = "community"
    POLITICAL = "political"
    UTILITY = "utility"
    CONSULTANT = "consultant"
    OTHER = "other"


class LegalInstrumentType(str, Enum):
    """Legal instrument categories tracked for entitlements."""

    AGREEMENT = "agreement"
    COVENANT = "covenant"
    ORDINANCE = "ordinance"
    POLICY = "policy"
    LICENSE = "license"
    OTHER = "other"


ENTITLEMENT_STATUS_ENUM = SAEnum(EntitlementStatus, name="entitlement_status")
ENTITLEMENT_STUDY_ENUM = SAEnum(EntitlementStudyType, name="entitlement_study_type")
ENTITLEMENT_STAKEHOLDER_ENUM = SAEnum(
    StakeholderKind, name="entitlement_stakeholder_kind"
)
ENTITLEMENT_LEGAL_TYPE_ENUM = SAEnum(
    LegalInstrumentType, name="entitlement_legal_instrument_type"
)


class TimestampMixin:
    """Common provenance timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )


class EntAuthority(TimestampMixin, BaseModel):
    """Permitting or reviewing authority."""

    __tablename__ = "ent_authorities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    jurisdiction: Mapped[str] = mapped_column(String(50), nullable=False, default="SG")
    contact_email: Mapped[Optional[str]] = mapped_column(String(200))
    metadata: Mapped[Dict[str, Any]] = mapped_column(FlexibleJSONB, default=dict)

    approval_types: Mapped[List["EntApprovalType"]] = relationship(
        back_populates="authority", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_ent_authorities_jurisdiction", "jurisdiction"),
    )


class EntApprovalType(TimestampMixin, BaseModel):
    """Approval types issued by an authority."""

    __tablename__ = "ent_approval_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    authority_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("ent_authorities.id", ondelete="CASCADE"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    default_lead_time_days: Mapped[Optional[int]] = mapped_column(Integer)
    metadata: Mapped[Dict[str, Any]] = mapped_column(FlexibleJSONB, default=dict)

    authority: Mapped[EntAuthority] = relationship(back_populates="approval_types")

    __table_args__ = (
        UniqueConstraint("authority_id", "code", name="uq_ent_approval_code"),
        Index("ix_ent_approval_types_authority", "authority_id"),
    )


class EntRoadmapItem(TimestampMixin, BaseModel):
    """Sequenced entitlement roadmap milestone."""

    __tablename__ = "ent_roadmap_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(Integer, nullable=False)
    approval_type_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("ent_approval_types.id", ondelete="RESTRICT"), nullable=False
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[EntitlementStatus] = mapped_column(
        ENTITLEMENT_STATUS_ENUM, nullable=False, default=EntitlementStatus.PLANNED
    )
    target_submission_date: Mapped[Optional[date]] = mapped_column(Date)
    actual_submission_date: Mapped[Optional[date]] = mapped_column(Date)
    decision_date: Mapped[Optional[date]] = mapped_column(Date)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    attachments: Mapped[List[Dict[str, Any]]] = mapped_column(FlexibleJSONB, default=list)
    metadata: Mapped[Dict[str, Any]] = mapped_column(FlexibleJSONB, default=dict)

    approval_type: Mapped[EntApprovalType] = relationship()

    __table_args__ = (
        UniqueConstraint("project_id", "sequence", name="uq_ent_roadmap_sequence"),
        Index("ix_ent_roadmap_project", "project_id"),
        Index("ix_ent_roadmap_status", "status"),
    )


class EntStudy(TimestampMixin, BaseModel):
    """Studies supporting entitlement applications."""

    __tablename__ = "ent_studies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    study_type: Mapped[EntitlementStudyType] = mapped_column(
        ENTITLEMENT_STUDY_ENUM, nullable=False
    )
    status: Mapped[EntitlementStatus] = mapped_column(ENTITLEMENT_STATUS_ENUM, nullable=False)
    consultant: Mapped[Optional[str]] = mapped_column(String(200))
    submission_date: Mapped[Optional[date]] = mapped_column(Date)
    approval_date: Mapped[Optional[date]] = mapped_column(Date)
    report_uri: Mapped[Optional[str]] = mapped_column(String(500))
    findings: Mapped[Dict[str, Any]] = mapped_column(FlexibleJSONB, default=dict)
    metadata: Mapped[Dict[str, Any]] = mapped_column(FlexibleJSONB, default=dict)

    __table_args__ = (
        Index("ix_ent_studies_project", "project_id"),
        Index("ix_ent_studies_status", "status"),
        Index("ix_ent_studies_type", "study_type"),
    )


class EntEngagement(TimestampMixin, BaseModel):
    """Stakeholder engagement records."""

    __tablename__ = "ent_engagements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(Integer, nullable=False)
    stakeholder_name: Mapped[str] = mapped_column(String(200), nullable=False)
    stakeholder_type: Mapped[StakeholderKind] = mapped_column(
        ENTITLEMENT_STAKEHOLDER_ENUM, nullable=False
    )
    status: Mapped[EntitlementStatus] = mapped_column(ENTITLEMENT_STATUS_ENUM, nullable=False)
    contact_email: Mapped[Optional[str]] = mapped_column(String(200))
    meeting_date: Mapped[Optional[date]] = mapped_column(Date)
    summary: Mapped[Optional[str]] = mapped_column(Text)
    next_steps: Mapped[List[str]] = mapped_column(FlexibleJSONB, default=list)
    metadata: Mapped[Dict[str, Any]] = mapped_column(FlexibleJSONB, default=dict)

    __table_args__ = (
        Index("ix_ent_engagements_project", "project_id"),
        Index("ix_ent_engagements_status", "status"),
    )


class EntLegalInstrument(TimestampMixin, BaseModel):
    """Legal agreements associated with entitlement approvals."""

    __tablename__ = "ent_legal_instruments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    instrument_type: Mapped[LegalInstrumentType] = mapped_column(
        ENTITLEMENT_LEGAL_TYPE_ENUM, nullable=False
    )
    status: Mapped[EntitlementStatus] = mapped_column(ENTITLEMENT_STATUS_ENUM, nullable=False)
    reference_code: Mapped[Optional[str]] = mapped_column(String(100))
    effective_date: Mapped[Optional[date]] = mapped_column(Date)
    expiry_date: Mapped[Optional[date]] = mapped_column(Date)
    storage_uri: Mapped[Optional[str]] = mapped_column(String(500))
    attachments: Mapped[List[Dict[str, Any]]] = mapped_column(FlexibleJSONB, default=list)
    metadata: Mapped[Dict[str, Any]] = mapped_column(FlexibleJSONB, default=dict)

    __table_args__ = (
        Index("ix_ent_legal_project", "project_id"),
        Index("ix_ent_legal_status", "status"),
    )


__all__ = [
    "EntAuthority",
    "EntApprovalType",
    "EntRoadmapItem",
    "EntStudy",
    "EntEngagement",
    "EntLegalInstrument",
    "EntitlementStatus",
    "EntitlementStudyType",
    "StakeholderKind",
    "LegalInstrumentType",
]
