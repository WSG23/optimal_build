"""Pydantic schemas for Phase 2G Construction Delivery Module."""

from __future__ import annotations
from datetime import date, datetime
from decimal import Decimal
from typing import Any, List
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

from app.models.construction import (
    ContractorType,
    InspectionStatus,
    SeverityLevel,
    DrawdownStatus,
)


class ContractorBase(BaseModel):
    company_name: str
    contractor_type: ContractorType = ContractorType.GENERAL_CONTRACTOR
    contact_person: str | None = None
    email: str | None = None
    phone: str | None = None
    contract_value: Decimal | None = None
    contract_date: date | None = None
    is_active: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class ContractorCreate(ContractorBase):
    project_id: UUID


class ContractorUpdate(BaseModel):
    company_name: str | None = None
    contractor_type: ContractorType | None = None
    contact_person: str | None = None
    email: str | None = None
    phone: str | None = None
    contract_value: Decimal | None = None
    contract_date: date | None = None
    is_active: bool | None = None
    metadata: dict[str, Any] | None = None


class ContractorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    project_id: UUID
    company_name: str
    contractor_type: ContractorType = ContractorType.GENERAL_CONTRACTOR
    contact_person: str | None = None
    email: str | None = None
    phone: str | None = None
    contract_value: Decimal | None = None
    contract_date: date | None = None
    is_active: bool = True
    metadata: dict[str, Any] = Field(
        default_factory=dict, validation_alias="metadata_json"
    )
    created_at: datetime
    updated_at: datetime | None = None


# Inspections
class QualityInspectionBase(BaseModel):
    inspection_date: date
    inspector_name: str
    location: str | None = None
    status: InspectionStatus = InspectionStatus.SCHEDULED
    defects_found: dict[str, Any] = Field(default_factory=dict)
    photos_url: List[str] = Field(default_factory=list)
    notes: str | None = None


class QualityInspectionCreate(QualityInspectionBase):
    project_id: UUID
    development_phase_id: int | None = None


class QualityInspectionUpdate(BaseModel):
    inspection_date: date | None = None
    inspector_name: str | None = None
    location: str | None = None
    status: InspectionStatus | None = None
    defects_found: dict[str, Any] | None = None
    photos_url: List[str] | None = None
    notes: str | None = None


class QualityInspectionResponse(QualityInspectionBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    project_id: UUID
    development_phase_id: int | None = None
    created_at: datetime


# Safety
class SafetyIncidentBase(BaseModel):
    incident_date: datetime
    severity: SeverityLevel
    title: str
    description: str | None = None
    location: str | None = None
    reported_by: str | None = None
    is_resolved: bool = False
    resolution_notes: str | None = None


class SafetyIncidentCreate(SafetyIncidentBase):
    project_id: UUID


class SafetyIncidentUpdate(BaseModel):
    incident_date: datetime | None = None
    severity: SeverityLevel | None = None
    title: str | None = None
    description: str | None = None
    location: str | None = None
    reported_by: str | None = None
    is_resolved: bool | None = None
    resolution_notes: str | None = None


class SafetyIncidentResponse(SafetyIncidentBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    project_id: UUID
    created_at: datetime


# Drawdowns
class DrawdownRequestBase(BaseModel):
    request_name: str
    request_date: date
    amount_requested: Decimal
    amount_approved: Decimal | None = None
    status: DrawdownStatus = DrawdownStatus.DRAFT
    contractor_id: UUID | None = None
    supporting_docs: List[str] = Field(default_factory=list)
    notes: str | None = None


class DrawdownRequestCreate(DrawdownRequestBase):
    project_id: UUID


class DrawdownRequestUpdate(BaseModel):
    request_name: str | None = None
    request_date: date | None = None
    amount_requested: Decimal | None = None
    amount_approved: Decimal | None = None
    status: DrawdownStatus | None = None
    contractor_id: UUID | None = None
    supporting_docs: List[str] | None = None
    notes: str | None = None


class DrawdownRequestResponse(DrawdownRequestBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    project_id: UUID
    created_at: datetime
    updated_at: datetime | None = None
