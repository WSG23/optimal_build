"""Pydantic schemas for entitlement tracking."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Generic, TypeVar

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
from pydantic import BaseModel, ConfigDict, Field


class EntAuthorityBase(BaseModel):
    """Shared attributes for authority payloads."""

    jurisdiction: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    slug: str = Field(..., min_length=1)
    website: str | None = None
    contact_email: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class EntAuthorityCreate(EntAuthorityBase):
    """Attributes required to create an authority."""

    pass


class EntAuthorityUpdate(BaseModel):
    """Attributes accepted when updating an authority."""

    jurisdiction: str | None = Field(default=None, min_length=1)
    name: str | None = Field(default=None, min_length=1)
    slug: str | None = Field(default=None, min_length=1)
    website: str | None = None
    contact_email: str | None = None
    metadata: dict[str, Any] | None = None


class EntAuthoritySchema(EntAuthorityBase):
    """Authority record returned via API."""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EntApprovalTypeBase(BaseModel):
    """Shared attributes for approval types."""

    authority_id: int
    code: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    category: EntApprovalCategory
    description: str | None = None
    requirements: dict[str, Any] = Field(default_factory=dict)
    processing_time_days: int | None = None
    is_mandatory: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class EntApprovalTypeCreate(EntApprovalTypeBase):
    """Payload accepted when creating an approval type."""

    pass


class EntApprovalTypeUpdate(BaseModel):
    """Partial update payload for approval types."""

    code: str | None = Field(default=None, min_length=1)
    name: str | None = Field(default=None, min_length=1)
    category: EntApprovalCategory | None = None
    description: str | None = None
    requirements: dict[str, Any] | None = None
    processing_time_days: int | None = None
    is_mandatory: bool | None = None
    metadata: dict[str, Any] | None = None


class EntApprovalTypeSchema(EntApprovalTypeBase):
    """Approval type record returned to clients."""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EntRoadmapItemBase(BaseModel):
    """Shared attributes for roadmap items."""

    project_id: int
    approval_type_id: int | None = None
    sequence_order: int | None = Field(default=None, ge=1)
    status: EntRoadmapStatus = EntRoadmapStatus.PLANNED
    status_changed_at: datetime | None = None
    target_submission_date: date | None = None
    target_decision_date: date | None = None
    actual_submission_date: date | None = None
    actual_decision_date: date | None = None
    notes: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class EntRoadmapItemCreate(EntRoadmapItemBase):
    """Payload for creating roadmap items."""

    pass


class EntRoadmapItemUpdate(BaseModel):
    """Partial update payload for roadmap items."""

    approval_type_id: int | None = None
    sequence_order: int | None = Field(default=None, ge=1)
    status: EntRoadmapStatus | None = None
    target_submission_date: date | None = None
    target_decision_date: date | None = None
    actual_submission_date: date | None = None
    actual_decision_date: date | None = None
    notes: str | None = None
    metadata: dict[str, Any] | None = None


class EntRoadmapItemSchema(EntRoadmapItemBase):
    """Roadmap item returned to API callers."""

    id: int
    sequence_order: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EntStudyBase(BaseModel):
    """Shared attributes for entitlement studies."""

    project_id: int
    name: str = Field(..., min_length=1)
    study_type: EntStudyType
    status: EntStudyStatus = EntStudyStatus.DRAFT
    summary: str | None = None
    consultant: str | None = None
    due_date: date | None = None
    completed_at: datetime | None = None
    attachments: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EntStudyCreate(EntStudyBase):
    """Payload for creating studies."""

    pass


class EntStudyUpdate(BaseModel):
    """Partial update payload for studies."""

    name: str | None = Field(default=None, min_length=1)
    study_type: EntStudyType | None = None
    status: EntStudyStatus | None = None
    summary: str | None = None
    consultant: str | None = None
    due_date: date | None = None
    completed_at: datetime | None = None
    attachments: list[dict[str, Any]] | None = None
    metadata: dict[str, Any] | None = None


class EntStudySchema(EntStudyBase):
    """Study record returned from the API."""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EntEngagementBase(BaseModel):
    """Shared fields for stakeholder engagements."""

    project_id: int
    name: str = Field(..., min_length=1)
    organisation: str | None = None
    engagement_type: EntEngagementType
    status: EntEngagementStatus = EntEngagementStatus.PLANNED
    contact_email: str | None = None
    contact_phone: str | None = None
    meetings: list[dict[str, Any]] = Field(default_factory=list)
    notes: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class EntEngagementCreate(EntEngagementBase):
    """Payload for creating engagements."""

    pass


class EntEngagementUpdate(BaseModel):
    """Partial update payload for engagements."""

    name: str | None = Field(default=None, min_length=1)
    organisation: str | None = None
    engagement_type: EntEngagementType | None = None
    status: EntEngagementStatus | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    meetings: list[dict[str, Any]] | None = None
    notes: str | None = None
    metadata: dict[str, Any] | None = None


class EntEngagementSchema(EntEngagementBase):
    """Engagement record returned from the API."""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EntLegalInstrumentBase(BaseModel):
    """Shared fields for legal instruments."""

    project_id: int
    name: str = Field(..., min_length=1)
    instrument_type: EntLegalInstrumentType
    status: EntLegalInstrumentStatus = EntLegalInstrumentStatus.DRAFT
    reference_code: str | None = None
    effective_date: date | None = None
    expiry_date: date | None = None
    attachments: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EntLegalInstrumentCreate(EntLegalInstrumentBase):
    """Payload for creating legal instruments."""

    pass


class EntLegalInstrumentUpdate(BaseModel):
    """Partial update payload for legal instruments."""

    name: str | None = Field(default=None, min_length=1)
    instrument_type: EntLegalInstrumentType | None = None
    status: EntLegalInstrumentStatus | None = None
    reference_code: str | None = None
    effective_date: date | None = None
    expiry_date: date | None = None
    attachments: list[dict[str, Any]] | None = None
    metadata: dict[str, Any] | None = None


class EntLegalInstrumentSchema(EntLegalInstrumentBase):
    """Legal instrument returned via API."""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


SchemaType = TypeVar("SchemaType", bound=BaseModel)


class PaginatedCollection(BaseModel, Generic[SchemaType]):
    """Generic collection payload for list endpoints."""

    items: list[SchemaType]
    total: int
    limit: int
    offset: int


class EntRoadmapCollection(PaginatedCollection[EntRoadmapItemSchema]):
    """Paginated roadmap response."""


class EntStudyCollection(PaginatedCollection[EntStudySchema]):
    """Paginated study response."""


class EntEngagementCollection(PaginatedCollection[EntEngagementSchema]):
    """Paginated engagement response."""


class EntLegalInstrumentCollection(PaginatedCollection[EntLegalInstrumentSchema]):
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
