"""Development phase models for multi-phase project management.

Phase 2D: Multi-Phase Development Management
- Complex phasing strategy tools
- Renovation sequencing for occupied buildings
- Heritage integration planning
- Mixed-use orchestration
"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import TYPE_CHECKING, List

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, relationship

from app.models.base import BaseModel as Base, UUID

if TYPE_CHECKING:
    from app.models.project import Project


class PhaseType(str, Enum):
    """Types of development phases."""

    DEMOLITION = "demolition"
    SITE_PREPARATION = "site_preparation"
    FOUNDATION = "foundation"
    STRUCTURE = "structure"
    ENVELOPE = "envelope"
    MEP_ROUGH_IN = "mep_rough_in"
    INTERIOR_FIT_OUT = "interior_fit_out"
    FACADE = "facade"
    LANDSCAPING = "landscaping"
    COMMISSIONING = "commissioning"
    HANDOVER = "handover"
    # Heritage-specific phases
    HERITAGE_ASSESSMENT = "heritage_assessment"
    HERITAGE_RESTORATION = "heritage_restoration"
    HERITAGE_INTEGRATION = "heritage_integration"
    # Renovation-specific phases
    TENANT_RELOCATION = "tenant_relocation"
    SOFT_STRIP = "soft_strip"
    REFURBISHMENT = "refurbishment"
    TENANT_FIT_OUT = "tenant_fit_out"
    # Mixed-use coordination phases
    RETAIL_PODIUM = "retail_podium"
    OFFICE_FLOORS = "office_floors"
    RESIDENTIAL_TOWER = "residential_tower"
    AMENITY_LEVEL = "amenity_level"


class PhaseStatus(str, Enum):
    """Status of a development phase."""

    NOT_STARTED = "not_started"
    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"
    DELAYED = "delayed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class DependencyType(str, Enum):
    """Types of phase dependencies."""

    FINISH_TO_START = "FS"  # Predecessor must finish before successor starts
    START_TO_START = "SS"  # Predecessor must start before successor starts
    FINISH_TO_FINISH = "FF"  # Predecessor must finish before successor finishes
    START_TO_FINISH = "SF"  # Predecessor must start before successor finishes


class MilestoneType(str, Enum):
    """Types of project milestones."""

    AUTHORITY_APPROVAL = "authority_approval"
    PLANNING_APPROVAL = "planning_approval"
    BUILDING_PERMIT = "building_permit"
    HERITAGE_CLEARANCE = "heritage_clearance"
    STRUCTURAL_COMPLETION = "structural_completion"
    FACADE_COMPLETION = "facade_completion"
    TOP_OUT = "top_out"
    PRACTICAL_COMPLETION = "practical_completion"
    FINAL_COMPLETION = "final_completion"
    TENANT_HANDOVER = "tenant_handover"
    CERTIFICATE_OF_OCCUPANCY = "certificate_of_occupancy"
    DEFECTS_LIABILITY_END = "defects_liability_end"


class HeritageClassification(str, Enum):
    """Heritage building classifications."""

    NONE = "none"
    LOCALLY_LISTED = "locally_listed"
    NATIONALLY_LISTED = "nationally_listed"
    CONSERVATION_AREA = "conservation_area"
    WORLD_HERITAGE = "world_heritage"
    FACADE_ONLY = "facade_only"
    INTERIOR_PROTECTED = "interior_protected"


class OccupancyStatus(str, Enum):
    """Building occupancy status during renovation."""

    VACANT = "vacant"
    PARTIALLY_OCCUPIED = "partially_occupied"
    FULLY_OCCUPIED = "fully_occupied"
    DECANTING_IN_PROGRESS = "decanting_in_progress"
    TEMPORARY_RELOCATION = "temporary_relocation"


class DevelopmentPhase(Base):
    """A phase within a multi-phase development project."""

    __tablename__ = "development_phases"
    __table_args__ = (
        UniqueConstraint("project_id", "phase_code", name="uq_project_phase_code"),
    )

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(
        UUID(),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Phase identification
    phase_code = Column(String(50), nullable=False)  # e.g., "P1", "P2A", "HERITAGE-1"
    phase_name = Column(String(200), nullable=False)
    phase_type = Column(
        SQLEnum(PhaseType, values_callable=lambda x: [e.value for e in x]),
        default=PhaseType.STRUCTURE,
        nullable=False,
    )
    description = Column(Text)

    # Status and progress
    status = Column(
        SQLEnum(PhaseStatus, values_callable=lambda x: [e.value for e in x]),
        default=PhaseStatus.NOT_STARTED,
        nullable=False,
    )
    completion_percentage = Column(Numeric(5, 2), default=0)

    # Scheduling
    planned_start_date = Column(Date)
    planned_end_date = Column(Date)
    actual_start_date = Column(Date)
    actual_end_date = Column(Date)
    duration_days = Column(Integer)  # Planned duration in calendar days
    work_days = Column(Integer)  # Planned working days (excl. weekends/holidays)

    # Float and critical path
    total_float_days = Column(Integer, default=0)  # Schedule float
    is_critical_path = Column(Boolean, default=False)

    # Heritage-specific fields
    heritage_classification = Column(
        SQLEnum(HeritageClassification, values_callable=lambda x: [e.value for e in x]),
        default=HeritageClassification.NONE,
    )
    heritage_constraints = Column(JSON)  # List of heritage constraints
    heritage_approval_required = Column(Boolean, default=False)
    heritage_approval_date = Column(Date)
    heritage_conditions = Column(Text)  # Special conditions from heritage authority

    # Renovation/occupancy-specific fields
    occupancy_status = Column(
        SQLEnum(OccupancyStatus, values_callable=lambda x: [e.value for e in x]),
        default=OccupancyStatus.VACANT,
    )
    affected_tenants_count = Column(Integer, default=0)
    tenant_coordination_notes = Column(Text)
    working_hours_restriction = Column(String(100))  # e.g., "08:00-18:00 weekdays only"
    noise_restrictions = Column(JSON)  # Time/zone restrictions for noisy work

    # Cost tracking
    estimated_cost = Column(Numeric(18, 2))
    actual_cost = Column(Numeric(18, 2))
    cost_variance_pct = Column(Numeric(8, 4))

    # Resources
    contractor_name = Column(String(200))
    responsible_party = Column(String(200))

    # Metadata
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project: Mapped["Project"] = relationship(
        "Project", back_populates="development_phases"
    )
    dependencies: Mapped[List["PhaseDependency"]] = relationship(
        "PhaseDependency",
        foreign_keys="PhaseDependency.successor_phase_id",
        back_populates="successor_phase",
        cascade="all, delete-orphan",
    )
    milestones: Mapped[List["PhaseMilestone"]] = relationship(
        "PhaseMilestone",
        back_populates="phase",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<DevelopmentPhase {self.phase_code}: {self.phase_name}>"

    @property
    def is_delayed(self) -> bool:
        """Check if phase is behind schedule."""
        if self.status == PhaseStatus.COMPLETED:
            return False
        if not self.planned_end_date:
            return False
        return date.today() > self.planned_end_date

    @property
    def days_delayed(self) -> int:
        """Calculate days behind schedule."""
        if not self.is_delayed:
            return 0
        if not self.planned_end_date:
            return 0
        return (date.today() - self.planned_end_date).days


class PhaseDependency(Base):
    """Dependency relationship between development phases."""

    __tablename__ = "phase_dependencies"
    __table_args__ = (
        UniqueConstraint(
            "predecessor_phase_id", "successor_phase_id", name="uq_phase_dependency"
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    predecessor_phase_id = Column(
        Integer,
        ForeignKey("development_phases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    successor_phase_id = Column(
        Integer,
        ForeignKey("development_phases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    dependency_type = Column(
        SQLEnum(DependencyType, values_callable=lambda x: [e.value for e in x]),
        default=DependencyType.FINISH_TO_START,
        nullable=False,
    )
    lag_days = Column(Integer, default=0)  # Days of lag (+) or lead (-)

    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    predecessor_phase: Mapped["DevelopmentPhase"] = relationship(
        "DevelopmentPhase",
        foreign_keys=[predecessor_phase_id],
    )
    successor_phase: Mapped["DevelopmentPhase"] = relationship(
        "DevelopmentPhase",
        foreign_keys=[successor_phase_id],
        back_populates="dependencies",
    )

    def __repr__(self) -> str:
        dep_type = self.dependency_type.value if self.dependency_type else "FS"
        return f"<PhaseDependency {self.predecessor_phase_id} -> {self.successor_phase_id} ({dep_type})>"


class PhaseMilestone(Base):
    """Milestone within a development phase."""

    __tablename__ = "phase_milestones"

    id = Column(Integer, primary_key=True, index=True)
    phase_id = Column(
        Integer,
        ForeignKey("development_phases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    milestone_name = Column(String(200), nullable=False)
    milestone_type = Column(
        SQLEnum(MilestoneType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    description = Column(Text)

    # Dates
    planned_date = Column(Date, nullable=False)
    actual_date = Column(Date)
    is_achieved = Column(Boolean, default=False)

    # Authority/approval tracking
    requires_approval = Column(Boolean, default=False)
    approval_authority = Column(String(200))  # e.g., "URA", "BCA", "Heritage Board"
    approval_reference = Column(String(100))  # Reference number
    approval_status = Column(String(50))  # e.g., "pending", "approved", "conditional"
    approval_conditions = Column(Text)

    # Notifications
    notify_before_days = Column(Integer, default=14)  # Days before to send reminder
    notification_sent = Column(Boolean, default=False)

    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    phase: Mapped["DevelopmentPhase"] = relationship(
        "DevelopmentPhase", back_populates="milestones"
    )

    def __repr__(self) -> str:
        return f"<PhaseMilestone {self.milestone_name} ({self.milestone_type.value})>"

    @property
    def is_overdue(self) -> bool:
        """Check if milestone is overdue."""
        if self.is_achieved:
            return False
        return date.today() > self.planned_date

    @property
    def days_until_due(self) -> int:
        """Days until milestone is due (negative if overdue)."""
        return (self.planned_date - date.today()).days


class TenantRelocation(Base):
    """Tenant relocation tracking for occupied building renovations."""

    __tablename__ = "tenant_relocations"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(
        UUID(),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    phase_id = Column(
        Integer, ForeignKey("development_phases.id", ondelete="SET NULL"), index=True
    )

    # Tenant information
    tenant_name = Column(String(200), nullable=False)
    current_unit = Column(String(100))  # Current unit/floor
    leased_area_sqm = Column(Numeric(12, 2))
    lease_expiry_date = Column(Date)

    # Relocation details
    relocation_required = Column(Boolean, default=True)
    temporary_location = Column(String(200))  # Where tenant moves during works
    relocation_start_date = Column(Date)
    relocation_end_date = Column(Date)
    return_unit = Column(String(100))  # Unit tenant returns to

    # Financial
    relocation_allowance = Column(Numeric(12, 2))
    rent_abatement_months = Column(Integer, default=0)
    fit_out_contribution = Column(Numeric(12, 2))

    # Status tracking
    status = Column(
        String(50), default="planned"
    )  # planned, notified, relocated, returned
    notification_date = Column(Date)
    agreement_signed = Column(Boolean, default=False)
    agreement_date = Column(Date)

    # Communication
    contact_name = Column(String(200))
    contact_email = Column(String(200))
    contact_phone = Column(String(50))
    notes = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<TenantRelocation {self.tenant_name} ({self.status})>"


# Register relationships with Project model
# This will be done in projects.py to avoid circular imports
