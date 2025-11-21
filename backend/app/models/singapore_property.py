"""Singapore Property model for Property Development Platform."""

import uuid
from enum import Enum

from sqlalchemy import (
    DECIMAL,
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    Enum as SQLEnum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

try:
    from geoalchemy2 import Geometry
except ModuleNotFoundError:  # pragma: no cover - optional dependency fallback
    from sqlalchemy.types import UserDefinedType

    class Geometry(UserDefinedType):  # type: ignore[misc]
        """Minimal stub emulating geoalchemy2.Geometry for test environments."""

        def __init__(self, *args: object, **kwargs: object) -> None:
            self.args = args
            self.kwargs = kwargs

        def get_col_spec(self, **_: object) -> str:  # pragma: no cover - simple stub
            return "GEOMETRY"


from backend._compat.datetime import utcnow

from app.models.base import UUID, BaseModel
from app.models.compliance import ComplianceStatus


class PropertyZoning(str, Enum):
    """Singapore zoning types based on URA Master Plan."""

    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    INDUSTRIAL = "industrial"
    MIXED_USE = "mixed_use"
    BUSINESS_PARK = "business_park"
    CIVIC_INSTITUTIONAL = "civic_institutional"
    EDUCATIONAL = "educational"
    HEALTHCARE = "healthcare"
    TRANSPORT = "transport"
    OPEN_SPACE = "open_space"
    SPECIAL_USE = "special_use"


class PropertyTenure(str, Enum):
    """Singapore property tenure types."""

    FREEHOLD = "freehold"
    LEASEHOLD_999 = "999_year_leasehold"
    LEASEHOLD_99 = "99_year_leasehold"
    LEASEHOLD_60 = "60_year_leasehold"
    LEASEHOLD_30 = "30_year_leasehold"


class DevelopmentStatus(str, Enum):
    """Property development status."""

    VACANT_LAND = "vacant_land"
    PLANNING = "planning"
    APPROVED = "approved"
    UNDER_CONSTRUCTION = "under_construction"
    TOP_OBTAINED = "top_obtained"  # Temporary Occupation Permit
    CSC_OBTAINED = "csc_obtained"  # Certificate of Statutory Completion
    OPERATIONAL = "operational"


class AcquisitionStatus(str, Enum):
    """Property acquisition status for feasibility workflow."""

    AVAILABLE = "available"  # Property identified, not yet analyzed
    UNDER_REVIEW = "under_review"  # Feasibility analysis in progress
    ACQUIRED = "acquired"  # Property purchased, linked to project
    REJECTED = "rejected"  # Analysis complete, not suitable


class FeasibilityStatus(str, Enum):
    """Feasibility analysis status."""

    ANALYZING = "analyzing"  # Initial analysis phase
    APPROVED = "approved"  # Feasibility approved, ready for acquisition
    REJECTED = "rejected"  # Not feasible for development
    ON_HOLD = "on_hold"  # Analysis paused/waiting


class SingaporeProperty(BaseModel):
    """Singapore property with local regulatory compliance."""

    __tablename__ = "singapore_properties"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)

    # Basic Information
    property_name = Column(String(255), nullable=False)
    address = Column(Text, nullable=False)
    postal_code = Column(String(6))  # Singapore postal codes are 6 digits

    # Location data (optional for SQLite compatibility)
    latitude = Column(Float)
    longitude = Column(Float)
    location = Column(
        Geometry("POINT", srid=4326), nullable=True
    )  # PostGIS geometry (optional)

    # Singapore Planning Region and Subzone (based on URA)
    planning_region = Column(String(100))  # e.g., Central Region, East Region
    planning_area = Column(String(100))  # e.g., Marina South, Tampines
    subzone = Column(String(100))  # e.g., Raffles Place, CBD

    # Property Details
    zoning = Column(
        SQLEnum(PropertyZoning, values_callable=lambda x: [e.value for e in x])
    )
    tenure = Column(
        SQLEnum(PropertyTenure, values_callable=lambda x: [e.value for e in x])
    )
    lease_start_date = Column(Date)  # For leasehold properties
    lease_remaining_years = Column(Integer)  # Calculated field

    # Land and Building Details
    land_area_sqm = Column(DECIMAL(10, 2))
    gross_floor_area_sqm = Column(DECIMAL(10, 2))
    gross_plot_ratio = Column(DECIMAL(5, 2))  # GPR limit
    current_plot_ratio = Column(DECIMAL(5, 2))  # Current usage

    # Site Context (jurisdiction-specific, may not be used in all jurisdictions)
    street_width_m = Column(
        DECIMAL(6, 2)
    )  # Width of adjacent street (used for envelope calculations in some jurisdictions like NYC)

    # Development Parameters (URA/BCA requirements)
    building_height_m = Column(DECIMAL(6, 2))
    max_building_height_m = Column(DECIMAL(6, 2))  # Based on technical height controls
    num_storeys = Column(Integer)
    max_storeys = Column(Integer)  # Based on zoning

    # Singapore Regulatory Compliance
    ura_approval_status = Column(String(100))
    ura_approval_date = Column(Date)
    bca_approval_status = Column(String(100))
    bca_submission_number = Column(String(100))
    scdf_approval_status = Column(String(100))
    nea_clearance = Column(Boolean, default=False)  # National Environment Agency
    pub_clearance = Column(Boolean, default=False)  # Public Utilities Board
    lta_clearance = Column(Boolean, default=False)  # Land Transport Authority

    # Development Charges and Fees (Singapore specific)
    development_charge = Column(DECIMAL(12, 2))  # SDG
    differential_premium = Column(DECIMAL(12, 2))  # For change of use
    temporary_occupation_fee = Column(DECIMAL(10, 2))
    property_tax_annual = Column(DECIMAL(10, 2))

    # Conservation and Heritage (for historical buildings)
    is_conserved = Column(Boolean, default=False)
    conservation_status = Column(String(100))  # URA conservation programme
    heritage_status = Column(String(100))  # National Heritage Board status

    # Environmental Sustainability (BCA Green Mark)
    green_mark_rating = Column(String(50))  # Platinum, GoldPLUS, Gold, Certified
    energy_efficiency_index = Column(DECIMAL(6, 2))
    water_efficiency_rating = Column(String(20))

    # Status
    development_status = Column(
        SQLEnum(DevelopmentStatus, values_callable=lambda x: [e.value for e in x]),
        default=DevelopmentStatus.VACANT_LAND,
    )
    is_government_land = Column(Boolean, default=False)
    is_en_bloc_potential = Column(Boolean, default=False)  # Collective sale potential

    # MVP: Acquisition and Feasibility Workflow
    acquisition_status = Column(
        SQLEnum(AcquisitionStatus, values_callable=lambda x: [e.value for e in x]),
        default=AcquisitionStatus.AVAILABLE,
    )
    feasibility_status = Column(
        SQLEnum(FeasibilityStatus, values_callable=lambda x: [e.value for e in x]),
        default=FeasibilityStatus.ANALYZING,
    )

    # MVP: Financial Tracking (Space Optimization Focus)
    estimated_acquisition_cost = Column(DECIMAL(15, 2))  # Estimate during feasibility
    actual_acquisition_cost = Column(DECIMAL(15, 2))  # Actual after acquired
    estimated_development_cost = Column(DECIMAL(15, 2))  # Rough development estimate
    expected_revenue = Column(DECIMAL(15, 2))  # Projected sale/rental value

    # MVP: Compliance Monitoring (Always Informational)
    bca_compliance_status = Column(
        SQLEnum(ComplianceStatus, values_callable=lambda x: [e.value for e in x]),
        default=ComplianceStatus.PENDING,
    )
    ura_compliance_status = Column(
        SQLEnum(ComplianceStatus, values_callable=lambda x: [e.value for e in x]),
        default=ComplianceStatus.PENDING,
    )
    compliance_notes = Column(Text)  # Summary of violations/warnings
    compliance_data = Column(JSON)  # Detailed compliance check results
    compliance_last_checked = Column(DateTime)  # When compliance was last verified

    # MVP: Space Optimization Metrics
    max_developable_gfa_sqm = Column(DECIMAL(12, 2))  # Based on plot ratio
    gfa_utilization_percentage = Column(DECIMAL(5, 2))  # Current vs max GFA
    potential_additional_units = Column(Integer)  # Space optimization potential

    # Valuation and Market Data
    market_value_sgd = Column(DECIMAL(15, 2))
    valuation_date = Column(Date)
    psf_value = Column(DECIMAL(10, 2))  # Price per square foot
    rental_yield_percentage = Column(DECIMAL(5, 2))

    # Additional Singapore-specific data
    mrt_station_nearest = Column(String(100))
    mrt_distance_km = Column(DECIMAL(5, 2))
    school_nearest = Column(String(100))
    school_distance_km = Column(DECIMAL(5, 2))

    # Metadata
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)
    data_source = Column(String(100))  # URA, OneMap, manual entry

    # JSON fields for flexible data
    ura_guidelines = Column(JSON)  # Specific URA guidelines for the plot
    nearby_amenities = Column(JSON)  # List of nearby facilities
    development_constraints = Column(JSON)  # Height restrictions, setbacks, etc.

    # MVP: Project Linking
    project_id = Column(
        UUID(), ForeignKey("projects.id"), nullable=True
    )  # Link to project after acquisition
    owner_email = Column(String(255))  # Track who owns/analyzes this property

    # Relationships
    project = relationship(
        "Project", back_populates="properties"
    )  # One property can link to one project
    # ai_sessions = relationship("AIAgentSession", back_populates="property")  # Disabled - table not created yet

    def __repr__(self) -> str:
        return f"<SingaporeProperty {self.property_name} ({self.postal_code})>"
