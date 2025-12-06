"""Project model for Singapore Property Development Platform."""

import uuid
from enum import Enum

from backend._compat.datetime import utcnow

from app.models.base import UUID, BaseModel
from sqlalchemy import (
    DECIMAL,
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship


class ProjectType(str, Enum):
    """Types of development projects."""

    NEW_DEVELOPMENT = "new_development"
    REDEVELOPMENT = "redevelopment"
    ADDITION_ALTERATION = "addition_alteration"
    CONSERVATION = "conservation"
    CHANGE_OF_USE = "change_of_use"
    SUBDIVISION = "subdivision"
    EN_BLOC = "en_bloc"
    DEMOLITION = "demolition"


class ProjectPhase(str, Enum):
    """Project development phases."""

    CONCEPT = "concept"
    FEASIBILITY = "feasibility"
    DESIGN = "design"
    APPROVAL = "approval"
    TENDER = "tender"
    CONSTRUCTION = "construction"
    TESTING_COMMISSIONING = "testing_commissioning"
    HANDOVER = "handover"
    OPERATION = "operation"


class ApprovalStatus(str, Enum):
    """Regulatory approval status."""

    NOT_SUBMITTED = "not_submitted"
    PENDING = "pending"
    APPROVED = "approved"
    APPROVED_WITH_CONDITIONS = "approved_with_conditions"
    REJECTED = "rejected"
    RESUBMISSION_REQUIRED = "resubmission_required"
    EXPIRED = "expired"


class Project(BaseModel):
    """Development project for Singapore properties."""

    __tablename__ = "projects"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)

    # Basic Information
    project_name = Column(String(255), nullable=False)
    project_code = Column(String(100), unique=True, nullable=False)
    description = Column(Text)

    # Foreign Keys
    # NOTE: Removed property_id - properties now link TO projects (one-to-many)
    # One project can have multiple properties (multiple street addresses)
    owner_id = Column(
        UUID(), ForeignKey("users.id"), nullable=True
    )  # Made optional for MVP
    owner_email = Column(String(255))  # Simple email-based ownership for MVP

    # Project Classification
    project_type = Column(
        SQLEnum(ProjectType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    current_phase = Column(
        SQLEnum(ProjectPhase, values_callable=lambda x: [e.value for e in x]),
        default=ProjectPhase.CONCEPT,
        nullable=False,
    )

    # Timeline
    start_date = Column(Date)
    target_completion_date = Column(Date)
    actual_completion_date = Column(Date)

    # Singapore Regulatory Submissions
    # URA (Urban Redevelopment Authority)
    ura_submission_number = Column(String(100))
    ura_approval_status = Column(
        SQLEnum(ApprovalStatus, values_callable=lambda x: [e.value for e in x]),
        default=ApprovalStatus.NOT_SUBMITTED,
    )
    ura_submission_date = Column(Date)
    ura_approval_date = Column(Date)
    ura_conditions = Column(JSON)  # Conditions of approval

    # BCA (Building and Construction Authority)
    bca_submission_number = Column(String(100))
    bca_approval_status = Column(
        SQLEnum(ApprovalStatus, values_callable=lambda x: [e.value for e in x]),
        default=ApprovalStatus.NOT_SUBMITTED,
    )
    bca_submission_date = Column(Date)
    bca_approval_date = Column(Date)
    bca_bc1_number = Column(String(100))  # Building Control number
    bca_permit_number = Column(String(100))
    structural_pe_number = Column(String(100))  # Professional Engineer registration

    # SCDF (Singapore Civil Defence Force)
    scdf_approval_status = Column(
        SQLEnum(ApprovalStatus, values_callable=lambda x: [e.value for e in x]),
        default=ApprovalStatus.NOT_SUBMITTED,
    )
    scdf_submission_date = Column(Date)
    scdf_approval_date = Column(Date)
    fire_safety_certificate = Column(String(100))

    # Other Agencies
    nea_approval = Column(Boolean, default=False)  # National Environment Agency
    pub_approval = Column(Boolean, default=False)  # Public Utilities Board
    lta_approval = Column(Boolean, default=False)  # Land Transport Authority
    nparks_approval = Column(Boolean, default=False)  # National Parks Board

    # Development Parameters
    proposed_gfa_sqm = Column(DECIMAL(10, 2))  # Gross Floor Area
    proposed_units = Column(Integer)
    proposed_height_m = Column(DECIMAL(6, 2))
    proposed_storeys = Column(Integer)
    proposed_plot_ratio = Column(DECIMAL(5, 2))

    # Financial
    estimated_cost_sgd = Column(DECIMAL(15, 2))
    actual_cost_sgd = Column(DECIMAL(15, 2))
    development_charge_sgd = Column(DECIMAL(12, 2))
    construction_cost_psf = Column(DECIMAL(10, 2))

    # Construction Details
    main_contractor = Column(String(255))
    architect_firm = Column(String(255))
    c_and_s_engineer = Column(String(255))  # Civil & Structural Engineer
    mep_engineer = Column(String(255))  # Mechanical, Electrical, Plumbing
    qs_consultant = Column(String(255))  # Quantity Surveyor

    # Compliance and Quality
    buildability_score = Column(DECIMAL(5, 2))  # BCA Buildability Score
    constructability_score = Column(DECIMAL(5, 2))  # BCA Constructability Score
    quality_mark_score = Column(DECIMAL(5, 2))  # CONQUAS score
    green_mark_target = Column(String(50))

    # Progress Tracking
    completion_percentage = Column(DECIMAL(5, 2), default=0)
    milestones_data = Column(JSON)  # List of project milestones
    risks_identified = Column(JSON)  # Risk register
    issues_log = Column(JSON)  # Current issues

    # Documents and Submissions
    documents = Column(JSON)  # Links to document storage
    submission_history = Column(JSON)  # History of all regulatory submissions

    # Status
    is_active = Column(Boolean, default=True)
    is_completed = Column(Boolean, default=False)
    has_top = Column(Boolean, default=False)  # Temporary Occupation Permit
    has_csc = Column(Boolean, default=False)  # Certificate of Statutory Completion

    # Key Dates (Singapore specific)
    land_tender_date = Column(Date)
    award_date = Column(Date)
    groundbreaking_date = Column(Date)
    topping_out_date = Column(Date)
    top_date = Column(Date)  # Temporary Occupation Permit date
    csc_date = Column(Date)  # Certificate of Statutory Completion date

    # Metadata
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )
    created_by = Column(String(100))

    # Relationships
    properties = relationship(
        "SingaporeProperty", back_populates="project"
    )  # One project can have multiple properties (Singapore)
    hk_properties = relationship(
        "HongKongProperty", back_populates="project"
    )  # One project can have multiple properties (Hong Kong)
    nz_properties = relationship(
        "NewZealandProperty", back_populates="project"
    )  # One project can have multiple properties (New Zealand)
    seattle_properties = relationship(
        "SeattleProperty", back_populates="project"
    )  # One project can have multiple properties (Seattle)
    toronto_properties = relationship(
        "TorontoProperty", back_populates="project"
    )  # One project can have multiple properties (Toronto)
    owner = relationship("User", back_populates="projects")
    ai_sessions = relationship("AIAgentSession", back_populates="project")
    # Phase 2D: Multi-phase development management
    development_phases = relationship(
        "DevelopmentPhase", back_populates="project", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Project {self.project_name} ({self.project_code})>"
