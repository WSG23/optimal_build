"""Pydantic schemas for entitlement tracking."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

from app.models.entitlements import (
    EntApprovalCategory,
    EntEngagementStatus,
    EntEngagementType,
    EntLegalInstrumentStatus,
    EntLegalInstrumentType,
    EntRoadmapStatus,
    EntStudyStatus,
    EntStudyType,
)


class EntAuthorityBase(BaseModel):
    """Shared attributes for authority payloads."""

    jurisdiction: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    slug: str = Field(..., min_length=1)
    website: Optional[str] = None
    contact_email: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EntAuthorityCreate(EntAuthorityBase):
    """Attributes required to create an authority."""

    pass


class EntAuthorityUpdate(BaseModel):
    """Attributes accepted when updating an authority."""

    jurisdiction: Optional[str] = Field(default=None, min_length=1)
    name: Optional[str] = Field(default=None, min_length=1)
    slug: Optional[str] = Field(default=None, min_length=1)
    website: Optional[str] = None
    contact_email: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class EntAuthoritySchema(EntAuthorityBase):
    """Authority record returned via API."""

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EntApprovalTypeBase(BaseModel):
    """Shared attributes for approval types."""

    authority_id: int
    code: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    category: EntApprovalCategory
    description: Optional[str] = None
    requirements: Dict[str, Any] = Field(default_factory=dict)
    processing_time_days: Optional[int] = None
    is_mandatory: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EntApprovalTypeCreate(EntApprovalTypeBase):
    """Payload accepted when creating an approval type."""

    pass


class EntApprovalTypeUpdate(BaseModel):
    """Partial update payload for approval types."""

    code: Optional[str] = Field(default=None, min_length=1)
    name: Optional[str] = Field(default=None, min_length=1)
    category: Optional[EntApprovalCategory] = None
    description: Optional[str] = None
    requirements: Optional[Dict[str, Any]] = None
    processing_time_days: Optional[int] = None
    is_mandatory: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class EntApprovalTypeSchema(EntApprovalTypeBase):
    """Approval type record returned to clients."""

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EntRoadmapItemBase(BaseModel):
    """Shared attributes for roadmap items."""

    project_id: int
    approval_type_id: Optional[int] = None
    sequence_order: Optional[int] = Field(default=None, ge=1)
    status: EntRoadmapStatus = EntRoadmapStatus.PLANNED
    status_changed_at: Optional[datetime] = None
    target_submission_date: Optional[date] = None
    target_decision_date: Optional[date] = None
    actual_submission_date: Optional[date] = None
    actual_decision_date: Optional[date] = None
    notes: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EntRoadmapItemCreate(EntRoadmapItemBase):
    """Payload for creating roadmap items."""

    pass


class EntRoadmapItemUpdate(BaseModel):
    """Partial update payload for roadmap items."""

    approval_type_id: Optional[int] = None
    sequence_order: Optional[int] = Field(default=None, ge=1)
    status: Optional[EntRoadmapStatus] = None
    target_submission_date: Optional[date] = None
    target_decision_date: Optional[date] = None
    actual_submission_date: Optional[date] = None
    actual_decision_date: Optional[date] = None
    notes: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class EntRoadmapItemSchema(EntRoadmapItemBase):
    """Roadmap item returned to API callers."""

    id: int
    sequence_order: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EntStudyBase(BaseModel):
    """Shared attributes for entitlement studies."""

    project_id: int
    name: str = Field(..., min_length=1)
    study_type: EntStudyType
    status: EntStudyStatus = EntStudyStatus.DRAFT
    summary: Optional[str] = None
    consultant: Optional[str] = None
    due_date: Optional[date] = None
    completed_at: Optional[datetime] = None
    attachments: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EntStudyCreate(EntStudyBase):
    """Payload for creating studies."""

    pass


class EntStudyUpdate(BaseModel):
    """Partial update payload for studies."""

    name: Optional[str] = Field(default=None, min_length=1)
    study_type: Optional[EntStudyType] = None
    status: Optional[EntStudyStatus] = None
    summary: Optional[str] = None
    consultant: Optional[str] = None
    due_date: Optional[date] = None
    completed_at: Optional[datetime] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None


class EntStudySchema(EntStudyBase):
    """Study record returned from the API."""

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EntEngagementBase(BaseModel):
    """Shared fields for stakeholder engagements."""

    project_id: int
    name: str = Field(..., min_length=1)
    organisation: Optional[str] = None
    engagement_type: EntEngagementType
    status: EntEngagementStatus = EntEngagementStatus.PLANNED
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    meetings: List[Dict[str, Any]] = Field(default_factory=list)
    notes: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EntEngagementCreate(EntEngagementBase):
    """Payload for creating engagements."""

    pass


class EntEngagementUpdate(BaseModel):
    """Partial update payload for engagements."""

    name: Optional[str] = Field(default=None, min_length=1)
    organisation: Optional[str] = None
    engagement_type: Optional[EntEngagementType] = None
    status: Optional[EntEngagementStatus] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    meetings: Optional[List[Dict[str, Any]]] = None
    notes: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class EntEngagementSchema(EntEngagementBase):
    """Engagement record returned from the API."""

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EntLegalInstrumentBase(BaseModel):
    """Shared fields for legal instruments."""

    project_id: int
    name: str = Field(..., min_length=1)
    instrument_type: EntLegalInstrumentType
    status: EntLegalInstrumentStatus = EntLegalInstrumentStatus.DRAFT
    reference_code: Optional[str] = None
    effective_date: Optional[date] = None
    expiry_date: Optional[date] = None
    attachments: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EntLegalInstrumentCreate(EntLegalInstrumentBase):
    """Payload for creating legal instruments."""

    pass


class EntLegalInstrumentUpdate(BaseModel):
    """Partial update payload for legal instruments."""

    name: Optional[str] = Field(default=None, min_length=1)
    instrument_type: Optional[EntLegalInstrumentType] = None
    status: Optional[EntLegalInstrumentStatus] = None
    reference_code: Optional[str] = None
    effective_date: Optional[date] = None
    expiry_date: Optional[date] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None


class EntLegalInstrumentSchema(EntLegalInstrumentBase):
    """Legal instrument returned via API."""

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


SchemaType = TypeVar("SchemaType", bound=BaseModel)


class PaginatedCollection(BaseModel, Generic[SchemaType]):
    """Generic collection payload for list endpoints."""

    items: List[SchemaType]
    total: int
    limit: int
    offset: int


class EntRoadmapCollection(PaginatedCollection[EntRoadmapItemSchema]):
    """Paginated roadmap response."""


class EntStudyCollection(PaginatedCollection[EntStudySchema]):
    """Paginated study response."""


class EntEngagementCollection(PaginatedCollection[EntEngagementSchema]):
    """Paginated engagement response."""


class EntLegalInstrumentCollection(
    PaginatedCollection[EntLegalInstrumentSchema]
):
    """Paginated legal instrument response."""


__all__ = [
    "EntAuthorityCreate",
    "EntAuthoritySchema",
    "EntAuthorityUpdate",
    "EntApprovalTypeCreate",
    "EntApprovalTypeSchema",
    "EntApprovalTypeUpdate",
    "EntRoadmapItemCreate",
    "EntRoadmapItemSchema",
    "EntRoadmapItemUpdate",
    "EntStudyCreate",
    "EntStudySchema",
    "EntStudyUpdate",
    "EntEngagementCreate",
    "EntEngagementSchema",
    "EntEngagementUpdate",
    "EntLegalInstrumentCreate",
    "EntLegalInstrumentSchema",
    "EntLegalInstrumentUpdate",
    "PaginatedCollection",
    "EntRoadmapCollection",
    "EntStudyCollection",
    "EntEngagementCollection",
    "EntLegalInstrumentCollection",
    "EntRoadmapStatus",
    "EntStudyStatus",
    "EntStudyType",
    "EntApprovalCategory",
    "EntEngagementStatus",
    "EntEngagementType",
    "EntLegalInstrumentStatus",
    "EntLegalInstrumentType",
]

