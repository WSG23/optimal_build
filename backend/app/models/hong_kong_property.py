"""Hong Kong Property model for Property Development Platform."""

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


class HKPropertyZoning(str, Enum):
    """Hong Kong zoning types based on Outline Zoning Plans (OZP).

    Town Planning Board (TPB) zoning categories.
    Reference: https://www.pland.gov.hk/
    """

    # Residential Zones
    RESIDENTIAL_A = "R(A)"  # Residential (Group A) - High density
    RESIDENTIAL_B = "R(B)"  # Residential (Group B) - Medium density
    RESIDENTIAL_C = "R(C)"  # Residential (Group C) - Low density
    RESIDENTIAL_D = "R(D)"  # Residential (Group D) - Very low density
    RESIDENTIAL_E = "R(E)"  # Residential (Group E) - Rural

    # Commercial Zones
    COMMERCIAL = "C"  # Commercial
    COMMERCIAL_RESIDENTIAL = "C/R"  # Commercial/Residential

    # Industrial Zones
    INDUSTRIAL = "I"  # Industrial
    INDUSTRIAL_OFFICE = "I(D)"  # Industrial (Special)

    # Mixed Use
    OTHER_SPECIFIED_USES = "OU"  # Other Specified Uses
    COMPREHENSIVE_DEVELOPMENT_AREA = "CDA"  # Comprehensive Development Area

    # Open Space and Recreation
    OPEN_SPACE = "O"  # Open Space
    RECREATION = "REC"  # Recreation

    # Government/Institution/Community
    GIC = "G/IC"  # Government/Institution/Community

    # Green Belt and Conservation
    GREEN_BELT = "GB"  # Green Belt
    CONSERVATION_AREA = "CA"  # Conservation Area
    COASTAL_PROTECTION_AREA = "CPA"  # Coastal Protection Area

    # Village and Agriculture
    VILLAGE_TYPE_DEVELOPMENT = "V"  # Village Type Development
    AGRICULTURE = "AGR"  # Agriculture

    # Undetermined
    UNDETERMINED = "U"  # Undetermined


class HKPropertyTenure(str, Enum):
    """Hong Kong property tenure types.

    Most land in Hong Kong is leasehold from the government.
    """

    GOVERNMENT_LEASE_999 = "government_lease_999"  # Rare pre-1898 leases
    GOVERNMENT_LEASE_75 = "government_lease_75"  # Renewable 75+75 years
    GOVERNMENT_LEASE_50 = (
        "government_lease_50"  # Post-1997 standard (50 years renewable)
    )
    GOVERNMENT_LEASE_OTHER = "government_lease_other"  # Other lease terms
    INDIGENOUS_VILLAGE = "indigenous_village"  # New Territories small house policy


class HKDevelopmentStatus(str, Enum):
    """Hong Kong property development status."""

    VACANT_LAND = "vacant_land"
    PLANNING_APPLICATION = "planning_application"  # S16 application submitted
    PLANNING_APPROVED = "planning_approved"  # TPB approval obtained
    BUILDING_PLANS_SUBMITTED = "building_plans_submitted"  # BD submission
    BUILDING_PLANS_APPROVED = "building_plans_approved"  # BD approval
    UNDER_CONSTRUCTION = "under_construction"
    OCCUPATION_PERMIT = "occupation_permit"  # OP obtained
    OPERATIONAL = "operational"


class HKAcquisitionStatus(str, Enum):
    """Property acquisition status for feasibility workflow."""

    AVAILABLE = "available"
    UNDER_REVIEW = "under_review"
    ACQUIRED = "acquired"
    REJECTED = "rejected"


class HKFeasibilityStatus(str, Enum):
    """Feasibility analysis status."""

    ANALYZING = "analyzing"
    APPROVED = "approved"
    REJECTED = "rejected"
    ON_HOLD = "on_hold"


class HKComplianceStatus(str, Enum):
    """TPB/Buildings Department compliance check status."""

    PENDING = "pending"
    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"


class HongKongProperty(BaseModel):
    """Hong Kong property with local regulatory compliance.

    Regulatory authorities:
    - TPB (Town Planning Board) - Zoning and planning
    - BD (Buildings Department) - Building regulations
    - Lands Department - Land administration
    - Environmental Protection Department (EPD)
    - Fire Services Department (FSD)
    """

    __tablename__ = "hong_kong_properties"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)

    # Basic Information
    property_name = Column(String(255), nullable=False)
    address = Column(Text, nullable=False)
    address_chinese = Column(Text)  # Chinese address

    # Location data
    latitude = Column(Float)
    longitude = Column(Float)
    location = Column(Geometry("POINT", srid=4326), nullable=True)

    # Hong Kong Administrative Regions
    district = Column(String(100))  # 18 districts (e.g., Central and Western, Wan Chai)
    constituency_area = Column(String(100))  # District Council constituency
    planning_scheme_area = Column(String(100))  # OZP area name
    lot_number = Column(String(100))  # Government lot number (e.g., IL 123, NKIL 456)

    # Property Details
    zoning = Column(
        SQLEnum(HKPropertyZoning, values_callable=lambda x: [e.value for e in x])
    )
    ozp_reference = Column(String(50))  # Outline Zoning Plan reference number
    tenure = Column(
        SQLEnum(HKPropertyTenure, values_callable=lambda x: [e.value for e in x])
    )
    lease_expiry_date = Column(Date)
    lease_remaining_years = Column(Integer)
    government_rent_multiplier = Column(
        DECIMAL(5, 3)
    )  # Annual rent as % of rateable value

    # Land and Building Details
    land_area_sqft = Column(DECIMAL(12, 2))  # Hong Kong uses sqft
    land_area_sqm = Column(DECIMAL(12, 2))  # For calculations
    gross_floor_area_sqft = Column(DECIMAL(12, 2))
    gross_floor_area_sqm = Column(DECIMAL(12, 2))
    saleable_area_sqft = Column(DECIMAL(12, 2))  # Saleable Area per REDA guidelines

    # Development Parameters (OZP/Lease restrictions)
    plot_ratio = Column(DECIMAL(5, 2))  # Maximum plot ratio
    current_plot_ratio = Column(DECIMAL(5, 2))
    site_coverage = Column(DECIMAL(5, 2))  # Maximum site coverage %
    building_height_m = Column(DECIMAL(6, 2))
    max_building_height_m = Column(DECIMAL(6, 2))  # Height restriction
    max_building_height_mpd = Column(
        DECIMAL(6, 2)
    )  # mPD (metres above Principal Datum)
    num_storeys = Column(Integer)
    max_storeys = Column(Integer)

    # Hong Kong Regulatory Compliance
    # Town Planning Board (TPB)
    tpb_approval_status = Column(String(100))
    tpb_application_number = Column(String(50))  # S16 application number
    tpb_approval_date = Column(Date)
    ozp_notes = Column(Text)  # Notes from OZP

    # Buildings Department (BD)
    bd_approval_status = Column(String(100))
    building_plans_number = Column(String(50))
    occupation_permit_number = Column(String(50))
    occupation_permit_date = Column(Date)

    # Lands Department
    lease_modification_required = Column(Boolean, default=False)
    land_premium_estimate = Column(DECIMAL(15, 2))  # Premium for lease modification
    waiver_application = Column(Boolean, default=False)

    # Other Departments
    epd_clearance = Column(Boolean, default=False)  # Environmental Protection
    fsd_clearance = Column(Boolean, default=False)  # Fire Services
    td_clearance = Column(Boolean, default=False)  # Transport Department
    dsd_clearance = Column(Boolean, default=False)  # Drainage Services

    # Conservation and Heritage
    is_graded_building = Column(Boolean, default=False)
    heritage_grade = Column(String(20))  # Grade 1, 2, 3, or Monument
    antiquities_advisory_board = Column(String(100))

    # Environmental Sustainability (BEAM Plus)
    beam_plus_rating = Column(
        String(50)
    )  # Platinum, Gold, Silver, Bronze, Unclassified
    energy_efficiency_rating = Column(String(20))
    mandatory_building_energy_code = Column(Boolean, default=False)

    # Status
    development_status = Column(
        SQLEnum(HKDevelopmentStatus, values_callable=lambda x: [e.value for e in x]),
        default=HKDevelopmentStatus.VACANT_LAND,
    )
    is_government_land = Column(Boolean, default=False)
    is_ura_project = Column(Boolean, default=False)  # Urban Renewal Authority project

    # Acquisition and Feasibility Workflow
    acquisition_status = Column(
        SQLEnum(HKAcquisitionStatus, values_callable=lambda x: [e.value for e in x]),
        default=HKAcquisitionStatus.AVAILABLE,
    )
    feasibility_status = Column(
        SQLEnum(HKFeasibilityStatus, values_callable=lambda x: [e.value for e in x]),
        default=HKFeasibilityStatus.ANALYZING,
    )

    # Financial Tracking
    estimated_acquisition_cost = Column(DECIMAL(15, 2))  # HKD
    actual_acquisition_cost = Column(DECIMAL(15, 2))
    estimated_development_cost = Column(DECIMAL(15, 2))
    land_premium = Column(DECIMAL(15, 2))  # Actual land premium paid
    expected_revenue = Column(DECIMAL(15, 2))

    # Compliance Monitoring
    tpb_compliance_status = Column(
        SQLEnum(HKComplianceStatus, values_callable=lambda x: [e.value for e in x]),
        default=HKComplianceStatus.PENDING,
    )
    bd_compliance_status = Column(
        SQLEnum(HKComplianceStatus, values_callable=lambda x: [e.value for e in x]),
        default=HKComplianceStatus.PENDING,
    )
    compliance_notes = Column(Text)
    compliance_data = Column(JSON)
    compliance_last_checked = Column(DateTime)

    # Space Optimization Metrics
    max_developable_gfa_sqft = Column(DECIMAL(12, 2))
    max_developable_gfa_sqm = Column(DECIMAL(12, 2))
    gfa_utilization_percentage = Column(DECIMAL(5, 2))
    potential_additional_units = Column(Integer)

    # Valuation and Market Data
    market_value_hkd = Column(DECIMAL(15, 2))
    valuation_date = Column(Date)
    psf_value = Column(DECIMAL(10, 2))  # Price per square foot
    rental_yield_percentage = Column(DECIMAL(5, 2))
    rateable_value = Column(DECIMAL(12, 2))  # For government rent calculation

    # Location Amenities
    mtr_station_nearest = Column(String(100))
    mtr_distance_m = Column(DECIMAL(6, 2))
    school_nearest = Column(String(100))
    school_distance_m = Column(DECIMAL(6, 2))

    # Metadata
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)
    data_source = Column(String(100))  # GeoInfo, CSDI, manual entry

    # JSON fields for flexible data
    ozp_requirements = Column(JSON)  # OZP planning requirements
    lease_conditions = Column(JSON)  # Special lease conditions
    nearby_amenities = Column(JSON)
    development_constraints = Column(JSON)

    # Project Linking
    project_id = Column(UUID(), ForeignKey("projects.id"), nullable=True)
    owner_email = Column(String(255))

    # Relationships
    project = relationship("Project", back_populates="hk_properties")

    def __repr__(self) -> str:
        return f"<HongKongProperty {self.property_name} ({self.lot_number})>"


__all__ = [
    "HongKongProperty",
    "HKPropertyZoning",
    "HKPropertyTenure",
    "HKDevelopmentStatus",
    "HKAcquisitionStatus",
    "HKFeasibilityStatus",
    "HKComplianceStatus",
]
