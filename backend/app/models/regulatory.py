from __future__ import annotations

import enum
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.projects import Project


class AgencyCode(str, enum.Enum):
    """Singapore regulatory agencies."""

    URA = "URA"  # Urban Redevelopment Authority
    BCA = "BCA"  # Building and Construction Authority
    SCDF = "SCDF"  # Singapore Civil Defence Force
    NEA = "NEA"  # National Environment Agency
    LTA = "LTA"  # Land Transport Authority
    NPARKS = "NPARKS"  # National Parks Board
    PUB = "PUB"  # Public Utilities Board
    SLA = "SLA"  # Singapore Land Authority
    STB = "STB"  # Singapore Tourism Board (Heritage)
    JTC = "JTC"  # JTC Corporation (Industrial)


class AssetType(str, enum.Enum):
    """Property asset types with different regulatory paths."""

    OFFICE = "office"
    RETAIL = "retail"
    RESIDENTIAL = "residential"
    INDUSTRIAL = "industrial"
    HERITAGE = "heritage"
    MIXED_USE = "mixed_use"
    HOSPITALITY = "hospitality"


class SubmissionType(str, enum.Enum):
    """Types of regulatory submissions."""

    DC = "DC"  # Development Control (URA)
    BP = "BP"  # Building Plan (BCA)
    TOP = "TOP"  # Temporary Occupation Permit
    CSC = "CSC"  # Certificate of Statutory Completion
    WAIVER = "WAIVER"  # Uppercase to match PostgreSQL enum
    CONSULTATION = "CONSULTATION"  # Uppercase to match PostgreSQL enum
    CHANGE_OF_USE = "CHANGE_OF_USE"  # Change of use application
    HERITAGE_APPROVAL = "HERITAGE_APPROVAL"  # STB heritage conservation
    INDUSTRIAL_PERMIT = "INDUSTRIAL_PERMIT"  # JTC industrial development


class SubmissionStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    RFI = "RFI"  # Request for Information / Amendment


class RegulatoryAgency(Base):
    __tablename__ = "regulatory_agencies"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    # Use String instead of Enum to match VARCHAR column in database
    code: Mapped[str] = mapped_column(
        String,
        unique=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    api_endpoint: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    submissions: Mapped[List["AuthoritySubmission"]] = relationship(
        "AuthoritySubmission", back_populates="agency"
    )

    def __repr__(self) -> str:
        return f"<RegulatoryAgency {self.code} - {self.name}>"


class AuthoritySubmission(Base):
    __tablename__ = "authority_submissions"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )

    project_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False
    )
    agency_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("regulatory_agencies.id"), nullable=False
    )

    submission_type: Mapped[SubmissionType] = mapped_column(
        Enum(SubmissionType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    submission_no: Mapped[Optional[str]] = mapped_column(
        String, nullable=True
    )  # External Reference No
    status: Mapped[SubmissionStatus] = mapped_column(
        Enum(SubmissionStatus, values_callable=lambda x: [e.value for e in x]),
        default=SubmissionStatus.DRAFT,
        nullable=False,
    )

    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    submitted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    project: Mapped["Project"] = relationship("Project", backref="submissions")
    agency: Mapped["RegulatoryAgency"] = relationship(
        "RegulatoryAgency", back_populates="submissions"
    )
    documents: Mapped[List["SubmissionDocument"]] = relationship(
        "SubmissionDocument", back_populates="submission", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<AuthoritySubmission {self.submission_no} - {self.status}>"


class SubmissionDocument(Base):
    __tablename__ = "submission_documents"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    submission_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("authority_submissions.id"), nullable=False
    )

    document_type: Mapped[str] = mapped_column(String, nullable=False)
    file_name: Mapped[str] = mapped_column(String, nullable=False)
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1)

    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    uploaded_by_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    submission: Mapped["AuthoritySubmission"] = relationship(
        "AuthoritySubmission", back_populates="documents"
    )

    def __repr__(self) -> str:
        return f"<SubmissionDocument {self.file_name} (v{self.version})>"


class RegulatoryRequirement(Base):
    __tablename__ = "regulatory_requirements"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    agency_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("regulatory_agencies.id"), nullable=False
    )
    category: Mapped[str] = mapped_column(String, nullable=False)

    code_reference: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<RegulatoryRequirement {self.code_reference}>"


class AssetCompliancePath(Base):
    """Asset-specific compliance paths for different property types."""

    __tablename__ = "asset_compliance_paths"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    # Use String instead of Enum to match VARCHAR column in database
    asset_type: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )
    agency_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("regulatory_agencies.id"), nullable=False
    )
    # Use String instead of Enum to match VARCHAR column in database
    submission_type: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )
    sequence_order: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    typical_duration_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        return f"<AssetCompliancePath {self.asset_type} -> {self.submission_type}>"


class ChangeOfUseApplication(Base):
    """Change of use navigation for adaptive reuse projects."""

    __tablename__ = "change_of_use_applications"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    project_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False
    )
    current_use: Mapped[AssetType] = mapped_column(
        Enum(AssetType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    proposed_use: Mapped[AssetType] = mapped_column(
        Enum(AssetType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    status: Mapped[SubmissionStatus] = mapped_column(
        Enum(SubmissionStatus, values_callable=lambda x: [e.value for e in x]),
        default=SubmissionStatus.DRAFT,
        nullable=False,
    )
    justification: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ura_reference: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    requires_dc_amendment: Mapped[bool] = mapped_column(Boolean, default=False)
    requires_planning_permission: Mapped[bool] = mapped_column(Boolean, default=True)

    submitted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    project: Mapped["Project"] = relationship(
        "Project", backref="change_of_use_applications"
    )

    def __repr__(self) -> str:
        return f"<ChangeOfUseApplication {self.current_use} -> {self.proposed_use}>"


class HeritageSubmission(Base):
    """Heritage authority management for STB coordination."""

    __tablename__ = "heritage_submissions"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    project_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False
    )
    conservation_status: Mapped[str] = mapped_column(
        String, nullable=False
    )  # e.g., "National Monument", "Conservation Area"
    stb_reference: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    status: Mapped[SubmissionStatus] = mapped_column(
        Enum(SubmissionStatus, values_callable=lambda x: [e.value for e in x]),
        default=SubmissionStatus.DRAFT,
        nullable=False,
    )

    # Heritage-specific fields
    original_construction_year: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    heritage_elements: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # JSON list of protected elements
    proposed_interventions: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # Description of proposed changes
    conservation_plan_attached: Mapped[bool] = mapped_column(Boolean, default=False)

    submitted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    project: Mapped["Project"] = relationship("Project", backref="heritage_submissions")

    def __repr__(self) -> str:
        return f"<HeritageSubmission {self.stb_reference} - {self.status}>"
