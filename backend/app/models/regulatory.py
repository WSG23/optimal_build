from __future__ import annotations

import enum
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.projects import Project


class AgencyCode(str, enum.Enum):
    URA = "URA"
    BCA = "BCA"
    SCDF = "SCDF"
    NEA = "NEA"
    LTA = "LTA"
    NPARKS = "NPARKS"
    PUB = "PUB"
    SLA = "SLA"


class SubmissionType(str, enum.Enum):
    DC = "DC"  # Development Control (URA)
    BP = "BP"  # Building Plan (BCA)
    TOP = "TOP"  # Temporary Occupation Permit
    CSC = "CSC"  # Certificate of Statutory Completion
    WAIVER = "Waiver"
    CONSULTATION = "Consultation"


class SubmissionStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    RFI = "rfi"  # Request for Information / Amendment


class RegulatoryAgency(Base):
    __tablename__ = "regulatory_agencies"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    code: Mapped[AgencyCode] = mapped_column(
        Enum(AgencyCode), unique=True, nullable=False
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
        Enum(SubmissionType), nullable=False
    )
    submission_no: Mapped[Optional[str]] = mapped_column(
        String, nullable=True
    )  # External Reference No
    status: Mapped[SubmissionStatus] = mapped_column(
        Enum(SubmissionStatus), default=SubmissionStatus.DRAFT, nullable=False
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

    def __repr__(self) -> str:
        return f"<AuthoritySubmission {self.submission_no} - {self.status}>"
