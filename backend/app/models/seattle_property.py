"""Seattle/King County Property model for Property Development Platform."""

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


class SeattleZoning(str, Enum):
    """Seattle zoning classifications based on Seattle Municipal Code Title 23.

    Reference: https://www.seattle.gov/sdci/codes/codes-we-enforce-(a-z)/zoning-code
    """

    # Single Family Residential
    SF_5000 = "SF 5000"  # Single Family 5,000 sq ft minimum lot
    SF_7200 = "SF 7200"  # Single Family 7,200 sq ft minimum lot
    SF_9600 = "SF 9600"  # Single Family 9,600 sq ft minimum lot

    # Residential Small Lot
    RSL = "RSL"  # Residential Small Lot

    # Lowrise Multifamily
    LR1 = "LR1"  # Lowrise 1
    LR2 = "LR2"  # Lowrise 2
    LR3 = "LR3"  # Lowrise 3

    # Midrise Multifamily
    MR = "MR"  # Midrise
    MR_RC = "MR-RC"  # Midrise Residential-Commercial

    # Highrise Multifamily
    HR = "HR"  # Highrise

    # Neighborhood Commercial
    NC1 = "NC1"  # Neighborhood Commercial 1
    NC2 = "NC2"  # Neighborhood Commercial 2
    NC3 = "NC3"  # Neighborhood Commercial 3

    # Commercial
    C1 = "C1"  # Commercial 1
    C2 = "C2"  # Commercial 2

    # Seattle Mixed
    SM = "SM"  # Seattle Mixed
    SM_SLU = "SM-SLU"  # Seattle Mixed - South Lake Union
    SM_D = "SM-D"  # Seattle Mixed - Downtown

    # Downtown
    DOC1 = "DOC1"  # Downtown Office Core 1
    DOC2 = "DOC2"  # Downtown Office Core 2
    DMC = "DMC"  # Downtown Mixed Commercial
    DMR = "DMR"  # Downtown Mixed Residential
    DRC = "DRC"  # Downtown Retail Core
    DH1 = "DH1"  # Downtown Harborfront 1
    DH2 = "DH2"  # Downtown Harborfront 2
    PSM = "PSM"  # Pike/Pine Conservation Overlay

    # Industrial
    IG1 = "IG1"  # Industrial General 1
    IG2 = "IG2"  # Industrial General 2
    IB = "IB"  # Industrial Buffer
    IC = "IC"  # Industrial Commercial


class SeattlePropertyTenure(str, Enum):
    """Property tenure types in Seattle/Washington State."""

    FEE_SIMPLE = "fee_simple"  # Full ownership
    LEASEHOLD = "leasehold"  # Ground lease
    CONDOMINIUM = "condominium"  # Condo ownership
    TOWNHOUSE = "townhouse"  # Townhouse ownership
    COOPERATIVE = "cooperative"  # Co-op


class SeattleDevelopmentStatus(str, Enum):
    """Seattle property development status."""

    VACANT_LAND = "vacant_land"
    PRE_APPLICATION = "pre_application"  # Pre-application conference
    DESIGN_REVIEW = "design_review"  # Design review process
    MUP_SUBMITTED = "mup_submitted"  # Master Use Permit submitted
    MUP_APPROVED = "mup_approved"  # MUP approved
    BUILDING_PERMIT_SUBMITTED = "building_permit_submitted"
    BUILDING_PERMIT_APPROVED = "building_permit_approved"
    UNDER_CONSTRUCTION = "under_construction"
    CERTIFICATE_OF_OCCUPANCY = "certificate_of_occupancy"  # C of O issued
    OPERATIONAL = "operational"


class SeattleAcquisitionStatus(str, Enum):
    """Property acquisition status for feasibility workflow."""

    AVAILABLE = "available"
    UNDER_REVIEW = "under_review"
    ACQUIRED = "acquired"
    REJECTED = "rejected"


class SeattleFeasibilityStatus(str, Enum):
    """Feasibility analysis status."""

    ANALYZING = "analyzing"
    APPROVED = "approved"
    REJECTED = "rejected"
    ON_HOLD = "on_hold"


class SeattleComplianceStatus(str, Enum):
    """SDCI compliance check status."""

    PENDING = "pending"
    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"


class SeattleProperty(BaseModel):
    """Seattle/King County property with local regulatory compliance.

    Regulatory framework:
    - Seattle Municipal Code (SMC) Title 23 - Land Use Code
    - Washington State Building Code (WSBC)
    - King County Code

    Regulatory authorities:
    - Seattle Department of Construction and Inspections (SDCI)
    - King County Department of Local Services
    - Washington State Department of Labor & Industries (L&I)
    """

    __tablename__ = "seattle_properties"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)

    # Basic Information
    property_name = Column(String(255), nullable=False)
    address = Column(Text, nullable=False)

    # Location data
    latitude = Column(Float)
    longitude = Column(Float)
    location = Column(Geometry("POINT", srid=4326), nullable=True)

    # Seattle/King County Administrative
    neighborhood = Column(String(100))  # e.g., Capitol Hill, Ballard, South Lake Union
    urban_village = Column(String(100))  # Urban village designation
    council_district = Column(Integer)  # City Council district (1-7)
    king_county_parcel = Column(String(20))  # King County parcel number

    # Property Details
    zoning = Column(
        SQLEnum(SeattleZoning, values_callable=lambda x: [e.value for e in x])
    )
    overlay_district = Column(
        String(100)
    )  # Special overlay (e.g., Pike/Pine, historic)
    tenure = Column(
        SQLEnum(SeattlePropertyTenure, values_callable=lambda x: [e.value for e in x])
    )

    # Land and Building Details (US uses sqft)
    lot_area_sqft = Column(DECIMAL(12, 2))
    lot_area_sqm = Column(DECIMAL(12, 2))  # For calculations
    gross_floor_area_sqft = Column(DECIMAL(12, 2))
    gross_floor_area_sqm = Column(DECIMAL(12, 2))
    net_rentable_area_sqft = Column(DECIMAL(12, 2))

    # Development Parameters (Seattle Land Use Code)
    floor_area_ratio = Column(DECIMAL(5, 2))  # FAR
    max_far = Column(DECIMAL(5, 2))  # Maximum FAR allowed
    lot_coverage_percent = Column(DECIMAL(5, 2))
    max_lot_coverage_percent = Column(DECIMAL(5, 2))
    building_height_ft = Column(DECIMAL(6, 2))
    max_building_height_ft = Column(DECIMAL(6, 2))
    num_storeys = Column(Integer)
    max_storeys = Column(Integer)
    setback_front_ft = Column(DECIMAL(5, 2))
    setback_side_ft = Column(DECIMAL(5, 2))
    setback_rear_ft = Column(DECIMAL(5, 2))

    # Seattle Incentive Zoning
    mha_zone = Column(String(20))  # Mandatory Housing Affordability zone (M, M1, M2)
    mha_payment_option = Column(Boolean, default=False)  # Payment in lieu of units
    mha_performance_option = Column(Boolean, default=False)  # On-site affordable units
    incentive_zoning_bonus = Column(DECIMAL(5, 2))  # Additional FAR from incentives

    # SDCI Permits and Approvals
    mup_number = Column(String(50))  # Master Use Permit number
    mup_status = Column(String(50))
    mup_issue_date = Column(Date)
    building_permit_number = Column(String(50))
    building_permit_status = Column(String(50))
    building_permit_issue_date = Column(Date)
    certificate_of_occupancy_date = Column(Date)

    # Design Review
    design_review_required = Column(Boolean, default=False)
    design_review_type = Column(String(50))  # Administrative, Full, Streamlined
    design_review_decision = Column(String(100))
    design_review_conditions = Column(JSON)

    # Environmental
    sepa_required = Column(Boolean, default=False)  # State Environmental Policy Act
    sepa_determination = Column(String(50))  # DNS, MDNS, DS, EIS
    critical_area = Column(Boolean, default=False)  # Steep slope, wetland, etc.
    shoreline_zone = Column(Boolean, default=False)

    # Historic Preservation
    is_landmark = Column(Boolean, default=False)
    landmark_designation = Column(String(100))
    historic_district = Column(String(100))

    # Sustainability (Seattle Energy Code / LEED)
    seattle_energy_code_compliance = Column(Boolean, default=False)
    leed_certification = Column(String(50))  # Certified, Silver, Gold, Platinum
    living_building_challenge = Column(Boolean, default=False)
    built_green_rating = Column(String(20))

    # Status
    development_status = Column(
        SQLEnum(
            SeattleDevelopmentStatus, values_callable=lambda x: [e.value for e in x]
        ),
        default=SeattleDevelopmentStatus.VACANT_LAND,
    )
    is_city_owned = Column(Boolean, default=False)
    is_opportunity_zone = Column(Boolean, default=False)

    # Acquisition and Feasibility Workflow
    acquisition_status = Column(
        SQLEnum(
            SeattleAcquisitionStatus, values_callable=lambda x: [e.value for e in x]
        ),
        default=SeattleAcquisitionStatus.AVAILABLE,
    )
    feasibility_status = Column(
        SQLEnum(
            SeattleFeasibilityStatus, values_callable=lambda x: [e.value for e in x]
        ),
        default=SeattleFeasibilityStatus.ANALYZING,
    )

    # Financial Tracking (USD)
    estimated_acquisition_cost = Column(DECIMAL(15, 2))
    actual_acquisition_cost = Column(DECIMAL(15, 2))
    estimated_development_cost = Column(DECIMAL(15, 2))
    impact_fees = Column(DECIMAL(12, 2))  # SDCI impact fees
    mha_payment_amount = Column(DECIMAL(12, 2))  # MHA payment if applicable
    expected_revenue = Column(DECIMAL(15, 2))

    # Compliance Monitoring
    zoning_compliance_status = Column(
        SQLEnum(
            SeattleComplianceStatus, values_callable=lambda x: [e.value for e in x]
        ),
        default=SeattleComplianceStatus.PENDING,
    )
    building_code_compliance_status = Column(
        SQLEnum(
            SeattleComplianceStatus, values_callable=lambda x: [e.value for e in x]
        ),
        default=SeattleComplianceStatus.PENDING,
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
    assessed_value_usd = Column(DECIMAL(15, 2))  # King County assessment
    land_value_usd = Column(DECIMAL(15, 2))
    improvement_value_usd = Column(DECIMAL(15, 2))
    valuation_date = Column(Date)
    property_tax_annual = Column(DECIMAL(10, 2))
    psf_value = Column(DECIMAL(10, 2))  # Price per square foot
    rental_yield_percentage = Column(DECIMAL(5, 2))

    # Metadata
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)
    data_source = Column(String(100))  # King County Assessor, SDCI, manual entry

    # JSON fields for flexible data
    smc_provisions = Column(JSON)  # Applicable SMC provisions
    overlays = Column(JSON)  # Special overlay requirements
    nearby_amenities = Column(JSON)
    development_constraints = Column(JSON)

    # Project Linking
    project_id = Column(UUID(), ForeignKey("projects.id"), nullable=True)
    owner_email = Column(String(255))

    # Relationships
    project = relationship("Project", back_populates="seattle_properties")

    def __repr__(self) -> str:
        return f"<SeattleProperty {self.property_name} ({self.king_county_parcel})>"


__all__ = [
    "SeattleProperty",
    "SeattleZoning",
    "SeattlePropertyTenure",
    "SeattleDevelopmentStatus",
    "SeattleAcquisitionStatus",
    "SeattleFeasibilityStatus",
    "SeattleComplianceStatus",
]
