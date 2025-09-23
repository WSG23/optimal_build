"""Pydantic schemas for entitlement management."""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class EntitlementStatus(str, Enum):
    """Workflow statuses shared across entitlement artefacts."""

    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    ON_HOLD = "on_hold"
    ARCHIVED = "archived"


class EntitlementStudyType(str, Enum):
    """Types of studies captured for entitlement submissions."""

    TRAFFIC = "traffic"
    ENVIRONMENTAL = "environmental"
    INFRASTRUCTURE = "infrastructure"
    HERITAGE = "heritage"
    OTHER = "other"


class StakeholderKind(str, Enum):
    """Stakeholder groupings used for engagement tracking."""

    AGENCY = "agency"
    COMMUNITY = "community"
    POLITICAL = "political"
    UTILITY = "utility"
    CONSULTANT = "consultant"
    OTHER = "other"


class LegalInstrumentType(str, Enum):
    """Categories of legal instruments captured in entitlement workflows."""

    AGREEMENT = "agreement"
    COVENANT = "covenant"
    ORDINANCE = "ordinance"
    POLICY = "policy"
    LICENSE = "license"
    OTHER = "other"


class ProvenanceStamp(BaseModel):
    """Standard provenance metadata returned by listing endpoints."""

    generated_at: datetime


class EntAuthority(BaseModel):
    """Authority metadata returned by exports and seed summaries."""

    id: int
    code: str
    name: str
    jurisdiction: str
    contact_email: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class EntApprovalType(BaseModel):
    """Approval type summary."""

    id: int
    authority_id: int
    code: str
    name: str
    description: Optional[str] = None
    default_lead_time_days: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class RoadmapItemBase(BaseModel):
    """Shared roadmap item fields."""

    approval_type_id: int
    status: EntitlementStatus = EntitlementStatus.PLANNED
    sequence: Optional[int] = None
    target_submission_date: Optional[date] = None
    actual_submission_date: Optional[date] = None
    decision_date: Optional[date] = None
    notes: Optional[str] = None
    attachments: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("attachments", mode="before")
    @classmethod
    def _normalise_attachments(cls, value: object) -> List[Dict[str, Any]]:
        if value in (None, ""):
            return []
        if isinstance(value, list):
            return [dict(item) if isinstance(item, dict) else {"value": item} for item in value]
        if isinstance(value, dict):
            return [dict(value)]
        return []

    @field_validator("metadata", mode="before")
    @classmethod
    def _normalise_metadata(cls, value: object) -> Dict[str, Any]:
        if isinstance(value, dict):
            return dict(value)
        return {}


class RoadmapItemCreate(RoadmapItemBase):
    """Payload for creating a roadmap item."""

    pass


class RoadmapItemUpdate(BaseModel):
    """Mutable roadmap fields."""

    approval_type_id: Optional[int] = None
    status: Optional[EntitlementStatus] = None
    sequence: Optional[int] = None
    target_submission_date: Optional[date] = None
    actual_submission_date: Optional[date] = None
    decision_date: Optional[date] = None
    notes: Optional[str] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None


class RoadmapItem(RoadmapItemBase):
    """Roadmap response model."""

    id: int
    project_id: int
    approval_type: Optional[EntApprovalType] = None
    sequence: int
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class RoadmapCollection(BaseModel):
    """Paginated roadmap response."""

    items: List[RoadmapItem]
    total: int
    provenance: ProvenanceStamp


class StudyBase(BaseModel):
    """Shared study fields."""

    name: str
    study_type: EntitlementStudyType
    status: EntitlementStatus
    consultant: Optional[str] = None
    submission_date: Optional[date] = None
    approval_date: Optional[date] = None
    report_uri: Optional[str] = None
    findings: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("findings", "metadata", mode="before")
    @classmethod
    def _ensure_dict(cls, value: object) -> Dict[str, Any]:
        if isinstance(value, dict):
            return dict(value)
        return {}


class StudyCreate(StudyBase):
    """Payload for creating a study."""

    pass


class StudyUpdate(BaseModel):
    """Mutable study fields."""

    name: Optional[str] = None
    study_type: Optional[EntitlementStudyType] = None
    status: Optional[EntitlementStatus] = None
    consultant: Optional[str] = None
    submission_date: Optional[date] = None
    approval_date: Optional[date] = None
    report_uri: Optional[str] = None
    findings: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class Study(StudyBase):
    """Study response model."""

    id: int
    project_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class StudyCollection(BaseModel):
    """Paginated study list."""

    items: List[Study]
    total: int
    provenance: ProvenanceStamp


class StakeholderBase(BaseModel):
    """Shared stakeholder engagement fields."""

    stakeholder_name: str
    stakeholder_type: StakeholderKind
    status: EntitlementStatus
    contact_email: Optional[str] = None
    meeting_date: Optional[date] = None
    summary: Optional[str] = None
    next_steps: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("next_steps", mode="before")
    @classmethod
    def _ensure_list(cls, value: object) -> List[str]:
        if value in (None, ""):
            return []
        if isinstance(value, list):
            return [str(item) for item in value]
        return [str(value)]

    @field_validator("metadata", mode="before")
    @classmethod
    def _ensure_metadata(cls, value: object) -> Dict[str, Any]:
        if isinstance(value, dict):
            return dict(value)
        return {}


class StakeholderCreate(StakeholderBase):
    """Payload for creating a stakeholder engagement."""

    pass


class StakeholderUpdate(BaseModel):
    """Mutable stakeholder fields."""

    stakeholder_name: Optional[str] = None
    stakeholder_type: Optional[StakeholderKind] = None
    status: Optional[EntitlementStatus] = None
    contact_email: Optional[str] = None
    meeting_date: Optional[date] = None
    summary: Optional[str] = None
    next_steps: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class Stakeholder(StakeholderBase):
    """Stakeholder response."""

    id: int
    project_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class StakeholderCollection(BaseModel):
    """Paginated stakeholder list."""

    items: List[Stakeholder]
    total: int
    provenance: ProvenanceStamp


class LegalInstrumentBase(BaseModel):
    """Shared legal instrument fields."""

    title: str
    instrument_type: LegalInstrumentType
    status: EntitlementStatus
    reference_code: Optional[str] = None
    effective_date: Optional[date] = None
    expiry_date: Optional[date] = None
    storage_uri: Optional[str] = None
    attachments: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("attachments", mode="before")
    @classmethod
    def _ensure_attachment_list(cls, value: object) -> List[Dict[str, Any]]:
        if value in (None, ""):
            return []
        if isinstance(value, list):
            return [dict(item) if isinstance(item, dict) else {"value": item} for item in value]
        if isinstance(value, dict):
            return [dict(value)]
        return []

    @field_validator("metadata", mode="before")
    @classmethod
    def _ensure_metadata_dict(cls, value: object) -> Dict[str, Any]:
        if isinstance(value, dict):
            return dict(value)
        return {}


class LegalInstrumentCreate(LegalInstrumentBase):
    """Payload for creating a legal instrument."""

    pass


class LegalInstrumentUpdate(BaseModel):
    """Mutable legal instrument fields."""

    title: Optional[str] = None
    instrument_type: Optional[LegalInstrumentType] = None
    status: Optional[EntitlementStatus] = None
    reference_code: Optional[str] = None
    effective_date: Optional[date] = None
    expiry_date: Optional[date] = None
    storage_uri: Optional[str] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None


class LegalInstrument(LegalInstrumentBase):
    """Legal instrument response."""

    id: int
    project_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class LegalInstrumentCollection(BaseModel):
    """Paginated legal instrument list."""

    items: List[LegalInstrument]
    total: int
    provenance: ProvenanceStamp


class EntitlementExportFormat(str, Enum):
    """Supported entitlement export formats."""

    CSV = "csv"
    HTML = "html"
    PDF = "pdf"


__all__ = [
    "EntApprovalType",
    "EntAuthority",
    "EntitlementExportFormat",
    "EntitlementStatus",
    "EntitlementStudyType",
    "LegalInstrument",
    "LegalInstrumentBase",
    "LegalInstrumentCreate",
    "LegalInstrumentType",
    "LegalInstrumentUpdate",
    "LegalInstrumentCollection",
    "ProvenanceStamp",
    "RoadmapCollection",
    "RoadmapItem",
    "RoadmapItemBase",
    "RoadmapItemCreate",
    "RoadmapItemUpdate",
    "Stakeholder",
    "StakeholderBase",
    "StakeholderCollection",
    "StakeholderCreate",
    "StakeholderKind",
    "StakeholderUpdate",
    "Study",
    "StudyBase",
    "StudyCollection",
    "StudyCreate",
    "StudyUpdate",
]
