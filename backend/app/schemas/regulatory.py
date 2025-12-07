from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel
from app.models.regulatory import AgencyCode, SubmissionType, SubmissionStatus


class RegulatoryAgencyBase(BaseModel):
    code: AgencyCode
    name: str
    description: Optional[str] = None
    api_endpoint: Optional[str] = None


class RegulatoryAgencyRead(RegulatoryAgencyBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SubmissionBase(BaseModel):
    title: str
    description: Optional[str] = None
    submission_type: SubmissionType
    agency_id: UUID


class SubmissionCreate(SubmissionBase):
    pass


class SubmissionUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[SubmissionStatus] = None


class SubmissionRead(SubmissionBase):
    id: UUID
    project_id: UUID
    submission_no: Optional[str] = None
    status: SubmissionStatus
    submitted_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    agency: Optional[RegulatoryAgencyRead] = None

    class Config:
        from_attributes = True


class SubmissionStatusCheck(BaseModel):
    submission_no: str
    status: str
    last_updated: datetime
    agency_remarks: Optional[str]
