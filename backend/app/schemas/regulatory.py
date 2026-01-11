from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.regulatory import AssetType, SubmissionType


class SubmissionDocumentBase(BaseModel):
    document_type: str
    file_name: str
    file_path: str


class SubmissionDocumentCreate(SubmissionDocumentBase):
    pass


class SubmissionDocumentRead(SubmissionDocumentBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    submission_id: UUID
    version: int
    uploaded_at: datetime
    uploaded_by_id: Optional[UUID] = None


class AuthoritySubmissionBase(BaseModel):
    submission_type: str


class AuthoritySubmissionCreate(AuthoritySubmissionBase):
    project_id: str  # Accepts UUID string or integer string
    agency: str  # Agency code (URA, BCA, etc.)


class AuthoritySubmissionRead(AuthoritySubmissionBase):
    """Response schema for authority submission - uses UUIDs matching model."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    agency_id: UUID  # Return the agency_id, not the lazy-loaded relationship
    status: str
    title: str
    description: Optional[str] = None
    submission_no: Optional[str] = None  # External reference number
    submitted_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    # Note: documents are omitted to avoid lazy loading - fetch separately if needed


class AuthoritySubmissionUpdate(BaseModel):
    status: Optional[str] = None
    agency_remarks: Optional[str] = None
    reference_number: Optional[str] = None


# Aliases used by the service layer
class SubmissionCreate(BaseModel):
    """Schema for creating a new regulatory submission."""

    title: str
    submission_type: SubmissionType
    agency_id: UUID
    description: Optional[str] = None


class SubmissionUpdate(BaseModel):
    """Schema for updating a regulatory submission."""

    title: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None
    agency_remarks: Optional[str] = None


# Asset Compliance Path schemas
class AssetCompliancePathBase(BaseModel):
    """Base schema for asset compliance paths."""

    asset_type: AssetType
    submission_type: SubmissionType
    sequence_order: int = 1
    is_mandatory: bool = True
    description: Optional[str] = None
    typical_duration_days: Optional[int] = None


class AssetCompliancePathCreate(AssetCompliancePathBase):
    """Schema for creating an asset compliance path."""

    agency_id: UUID


class AssetCompliancePathRead(AssetCompliancePathBase):
    """Schema for reading an asset compliance path."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    agency_id: UUID
    created_at: datetime


# Change of Use schemas
class ChangeOfUseBase(BaseModel):
    """Base schema for change of use applications."""

    current_use: AssetType
    proposed_use: AssetType
    justification: Optional[str] = None


class ChangeOfUseCreate(ChangeOfUseBase):
    """Schema for creating a change of use application."""

    project_id: str  # Accepts UUID string or integer string


class ChangeOfUseRead(ChangeOfUseBase):
    """Schema for reading a change of use application."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    status: str
    ura_reference: Optional[str] = None
    requires_dc_amendment: bool
    requires_planning_permission: bool
    submitted_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class ChangeOfUseUpdate(BaseModel):
    """Schema for updating a change of use application."""

    status: Optional[str] = None
    justification: Optional[str] = None
    ura_reference: Optional[str] = None
    requires_dc_amendment: Optional[bool] = None


# Heritage Submission schemas
class HeritageSubmissionBase(BaseModel):
    """Base schema for heritage submissions."""

    conservation_status: str
    original_construction_year: Optional[int] = None
    heritage_elements: Optional[str] = None
    proposed_interventions: Optional[str] = None


class HeritageSubmissionCreate(HeritageSubmissionBase):
    """Schema for creating a heritage submission."""

    project_id: str  # Accepts UUID string or integer string


class HeritageSubmissionRead(HeritageSubmissionBase):
    """Schema for reading a heritage submission."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    stb_reference: Optional[str] = None
    status: str
    conservation_plan_attached: bool
    submitted_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class HeritageSubmissionUpdate(BaseModel):
    """Schema for updating a heritage submission."""

    status: Optional[str] = None
    stb_reference: Optional[str] = None
    heritage_elements: Optional[str] = None
    proposed_interventions: Optional[str] = None
    conservation_plan_attached: Optional[bool] = None
