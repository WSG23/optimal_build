"""Toronto Property model for Property Development Platform."""

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

    # GeoAlchemy2 stub when PostGIS not available (test environments)
    class Geometry(UserDefinedType):  # type: ignore[misc]  # SQLAlchemy UserDefinedType pattern
        """Minimal stub emulating geoalchemy2.Geometry for test environments."""

        def __init__(self, *args: object, **kwargs: object) -> None:
            self.args = args
            self.kwargs = kwargs

        def get_col_spec(self, **_: object) -> str:  # pragma: no cover - simple stub
            return "GEOMETRY"


from backend._compat.datetime import utcnow

from app.models.base import UUID, BaseModel


class TorontoZoning(str, Enum):
    """Toronto zoning classifications based on City of Toronto Zoning By-law 569-2013.

    Reference: https://www.toronto.ca/city-government/planning-development/zoning-by-law-preliminary-zoning-reviews/
    """

    # Residential Zones
    RD = "RD"  # Residential Detached
    RS = "RS"  # Residential Semi-Detached
    RT = "RT"  # Residential Townhouse
    RM = "RM"  # Residential Multiple Dwelling
    RA = "RA"  # Residential Apartment
    RAC = "RAC"  # Residential Apartment Commercial

    # Commercial Zones
    CR = "CR"  # Commercial Residential
    CL = "CL"  # Commercial Local
    CG = "CG"  # Commercial General

    # Employment Zones
    E = "E"  # Employment Industrial
    EL = "EL"  # Employment Light Industrial
    EO = "EO"  # Employment Office
    EH = "EH"  # Employment Heavy Industrial

    # Institutional Zones
    INST = "I"  # Institutional General (I)
    IS = "IS"  # Institutional School

    # Open Space Zones
    OS = "O"  # Open Space (O)
    ON = "ON"  # Open Space Natural
    OR = "OR"  # Open Space Recreation

    # Utility and Transportation
    UT = "UT"  # Utility and Transportation


class TorontoPropertyTenure(str, Enum):
    """Property tenure types in Toronto/Ontario."""

    FREEHOLD = "freehold"  # Fee simple
    LEASEHOLD = "leasehold"  # Ground lease
    CONDOMINIUM = "condominium"  # Condo under Condominium Act
    LIFE_LEASE = "life_lease"  # Life lease housing
    COOPERATIVE = "cooperative"  # Co-op housing


class TorontoDevelopmentStatus(str, Enum):
    """Toronto property development status."""

    VACANT_LAND = "vacant_land"
    PRE_APPLICATION = "pre_application"  # Pre-application consultation
    SITE_PLAN_SUBMITTED = "site_plan_submitted"  # Site Plan Application
    SITE_PLAN_APPROVED = "site_plan_approved"
    ZONING_AMENDMENT = "zoning_amendment"  # ZBA in process
    OFFICIAL_PLAN_AMENDMENT = "official_plan_amendment"  # OPA in process
    BUILDING_PERMIT_SUBMITTED = "building_permit_submitted"
    BUILDING_PERMIT_APPROVED = "building_permit_approved"
    UNDER_CONSTRUCTION = "under_construction"
    OCCUPANCY_PERMIT = "occupancy_permit"  # Occupancy permit issued
    OPERATIONAL = "operational"


class TorontoAcquisitionStatus(str, Enum):
    """Property acquisition status for feasibility workflow."""

    AVAILABLE = "available"
    UNDER_REVIEW = "under_review"
    ACQUIRED = "acquired"
    REJECTED = "rejected"


class TorontoFeasibilityStatus(str, Enum):
    """Feasibility analysis status."""

    ANALYZING = "analyzing"
    APPROVED = "approved"
    REJECTED = "rejected"
    ON_HOLD = "on_hold"


class TorontoComplianceStatus(str, Enum):
    """City of Toronto compliance check status."""

    PENDING = "pending"
    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"


class TorontoProperty(BaseModel):
    """Toronto property with local regulatory compliance.

    Regulatory framework:
    - Planning Act (Ontario)
    - City of Toronto Official Plan
    - Zoning By-law 569-2013
    - Ontario Building Code (OBC)

    Regulatory authorities:
    - City of Toronto Planning
    - Toronto Building (building permits)
    - Ontario Land Tribunal (OLT) - appeals
    """

    __tablename__ = "toronto_properties"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)

    # Basic Information
    property_name = Column(String(255), nullable=False)
    address = Column(Text, nullable=False)

    # Location data
    latitude = Column(Float)
    longitude = Column(Float)
    location = Column(Geometry("POINT", srid=4326), nullable=True)

    # Toronto Administrative
    ward = Column(String(50))  # City Ward (1-25)
    ward_name = Column(String(100))
    neighbourhood = Column(String(100))  # Official neighbourhood name
    community_council = Column(String(100))  # Community Council area
    assessment_roll_number = Column(String(25))  # MPAC roll number

    # Property Details
    zoning = Column(
        SQLEnum(TorontoZoning, values_callable=lambda x: [e.value for e in x])
    )
    zoning_exception = Column(String(100))  # Exception number if applicable
    official_plan_designation = Column(String(100))  # OP land use designation
    secondary_plan = Column(String(100))  # Secondary plan area if applicable
    tenure = Column(
        SQLEnum(TorontoPropertyTenure, values_callable=lambda x: [e.value for e in x])
    )

    # Land and Building Details (Canada uses sqm and sqft)
    lot_area_sqm = Column(DECIMAL(12, 2))
    lot_area_sqft = Column(DECIMAL(12, 2))
    gross_floor_area_sqm = Column(DECIMAL(12, 2))
    gross_floor_area_sqft = Column(DECIMAL(12, 2))
    net_leasable_area_sqm = Column(DECIMAL(12, 2))

    # Development Parameters (Zoning By-law 569-2013)
    floor_space_index = Column(DECIMAL(5, 2))  # FSI (equivalent to FAR)
    max_fsi = Column(DECIMAL(5, 2))  # Maximum FSI allowed
    lot_coverage_percent = Column(DECIMAL(5, 2))
    max_lot_coverage_percent = Column(DECIMAL(5, 2))
    building_height_m = Column(DECIMAL(6, 2))
    max_building_height_m = Column(DECIMAL(6, 2))
    num_storeys = Column(Integer)
    max_storeys = Column(Integer)
    setback_front_m = Column(DECIMAL(5, 2))
    setback_side_m = Column(DECIMAL(5, 2))
    setback_rear_m = Column(DECIMAL(5, 2))
    angular_plane = Column(DECIMAL(5, 2))  # Angular plane from property line

    # Inclusionary Zoning (IZ)
    iz_area = Column(Boolean, default=False)  # In Inclusionary Zoning area
    iz_affordable_units_required = Column(Integer)  # Required affordable units
    iz_affordable_percentage = Column(DECIMAL(5, 2))  # Required % affordable

    # Section 37 / Community Benefits (legacy before Bill 23)
    section_37_agreement = Column(Boolean, default=False)
    community_benefits_charge = Column(DECIMAL(12, 2))  # CBC under Bill 23

    # City of Toronto Planning Applications
    site_plan_number = Column(String(50))
    site_plan_status = Column(String(50))
    site_plan_decision_date = Column(Date)
    zba_number = Column(String(50))  # Zoning By-law Amendment number
    zba_status = Column(String(50))
    opa_number = Column(String(50))  # Official Plan Amendment number
    opa_status = Column(String(50))
    minor_variance_number = Column(String(50))  # Committee of Adjustment
    minor_variance_status = Column(String(50))

    # Building Permit (Toronto Building)
    building_permit_number = Column(String(50))
    building_permit_status = Column(String(50))
    building_permit_issue_date = Column(Date)
    occupancy_permit_date = Column(Date)

    # Heritage
    is_heritage_designated = Column(Boolean, default=False)
    heritage_designation_type = Column(String(50))  # Part IV, Part V (HCD)
    heritage_easement = Column(Boolean, default=False)

    # Environmental
    environmental_assessment_required = Column(Boolean, default=False)
    phase_1_esa_complete = Column(Boolean, default=False)  # Phase 1 ESA
    phase_2_esa_complete = Column(Boolean, default=False)  # Phase 2 ESA
    record_of_site_condition = Column(String(50))  # RSC number

    # Sustainability (Toronto Green Standard)
    tgs_tier = Column(String(10))  # Tier 1 (mandatory), Tier 2, 3, 4
    tgs_points = Column(Integer)
    near_zero_emissions = Column(Boolean, default=False)  # NZE building
    leed_certification = Column(String(50))

    # Status
    development_status = Column(
        SQLEnum(
            TorontoDevelopmentStatus, values_callable=lambda x: [e.value for e in x]
        ),
        default=TorontoDevelopmentStatus.VACANT_LAND,
    )
    is_city_owned = Column(Boolean, default=False)
    is_ravine_protected = Column(Boolean, default=False)

    # Acquisition and Feasibility Workflow
    acquisition_status = Column(
        SQLEnum(
            TorontoAcquisitionStatus, values_callable=lambda x: [e.value for e in x]
        ),
        default=TorontoAcquisitionStatus.AVAILABLE,
    )
    feasibility_status = Column(
        SQLEnum(
            TorontoFeasibilityStatus, values_callable=lambda x: [e.value for e in x]
        ),
        default=TorontoFeasibilityStatus.ANALYZING,
    )

    # Financial Tracking (CAD)
    estimated_acquisition_cost = Column(DECIMAL(15, 2))
    actual_acquisition_cost = Column(DECIMAL(15, 2))
    estimated_development_cost = Column(DECIMAL(15, 2))
    development_charges = Column(DECIMAL(12, 2))  # City DCs
    parkland_dedication = Column(DECIMAL(12, 2))  # Parkland or cash-in-lieu
    expected_revenue = Column(DECIMAL(15, 2))

    # Compliance Monitoring
    zoning_compliance_status = Column(
        SQLEnum(
            TorontoComplianceStatus, values_callable=lambda x: [e.value for e in x]
        ),
        default=TorontoComplianceStatus.PENDING,
    )
    building_code_compliance_status = Column(
        SQLEnum(
            TorontoComplianceStatus, values_callable=lambda x: [e.value for e in x]
        ),
        default=TorontoComplianceStatus.PENDING,
    )
    compliance_notes = Column(Text)
    compliance_data = Column(JSON)
    compliance_last_checked = Column(DateTime)

    # Space Optimization Metrics
    max_developable_gfa_sqm = Column(DECIMAL(12, 2))
    max_developable_gfa_sqft = Column(DECIMAL(12, 2))
    gfa_utilization_percentage = Column(DECIMAL(5, 2))
    potential_additional_units = Column(Integer)

    # Valuation and Market Data
    current_value_assessment = Column(DECIMAL(15, 2))  # MPAC CVA
    land_value_cad = Column(DECIMAL(15, 2))
    improvement_value_cad = Column(DECIMAL(15, 2))
    valuation_date = Column(Date)
    property_tax_annual = Column(DECIMAL(10, 2))
    psf_value = Column(DECIMAL(10, 2))  # Price per square foot
    rental_yield_percentage = Column(DECIMAL(5, 2))

    # Metadata
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)
    data_source = Column(String(100))  # City Open Data, MPAC, manual entry

    # JSON fields for flexible data
    zoning_provisions = Column(JSON)  # Applicable zoning provisions
    op_policies = Column(JSON)  # Official Plan policies
    nearby_amenities = Column(JSON)
    development_constraints = Column(JSON)

    # Project Linking
    project_id = Column(UUID(), ForeignKey("projects.id"), nullable=True)
    owner_email = Column(String(255))

    # Relationships
    project = relationship("Project", back_populates="toronto_properties")

    def __repr__(self) -> str:
        return f"<TorontoProperty {self.property_name} ({self.assessment_roll_number})>"


__all__ = [
    "TorontoProperty",
    "TorontoZoning",
    "TorontoPropertyTenure",
    "TorontoDevelopmentStatus",
    "TorontoAcquisitionStatus",
    "TorontoFeasibilityStatus",
    "TorontoComplianceStatus",
]
