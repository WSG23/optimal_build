"""New Zealand Property model for Property Development Platform."""

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


class NZPropertyZoning(str, Enum):
    """New Zealand zoning types based on Auckland Unitary Plan and District Plans.

    Reference: https://www.aucklandcouncil.govt.nz/plans-projects-policies-reports-bylaws/our-plans-strategies/unitary-plan/
    """

    # Residential Zones
    RESIDENTIAL_LARGE_LOT = "residential_large_lot"
    RESIDENTIAL_SINGLE_HOUSE = "residential_single_house"
    RESIDENTIAL_MIXED_HOUSING_SUBURBAN = "residential_mixed_housing_suburban"
    RESIDENTIAL_MIXED_HOUSING_URBAN = "residential_mixed_housing_urban"
    RESIDENTIAL_TERRACE_HOUSING_APARTMENT = "residential_terrace_housing_apartment"

    # Business Zones
    BUSINESS_NEIGHBOURHOOD_CENTRE = "business_neighbourhood_centre"
    BUSINESS_LOCAL_CENTRE = "business_local_centre"
    BUSINESS_TOWN_CENTRE = "business_town_centre"
    BUSINESS_METROPOLITAN_CENTRE = "business_metropolitan_centre"
    BUSINESS_CITY_CENTRE = "business_city_centre"
    BUSINESS_MIXED_USE = "business_mixed_use"
    BUSINESS_LIGHT_INDUSTRY = "business_light_industry"
    BUSINESS_HEAVY_INDUSTRY = "business_heavy_industry"

    # Open Space and Recreation
    OPEN_SPACE_CONSERVATION = "open_space_conservation"
    OPEN_SPACE_INFORMAL_RECREATION = "open_space_informal_recreation"
    OPEN_SPACE_SPORT_ACTIVE_RECREATION = "open_space_sport_active_recreation"
    OPEN_SPACE_COMMUNITY = "open_space_community"

    # Rural Zones
    RURAL_PRODUCTION = "rural_production"
    RURAL_MIXED_RURAL = "rural_mixed_rural"
    RURAL_RURAL_COASTAL = "rural_rural_coastal"
    RURAL_COUNTRYSIDE_LIVING = "rural_countryside_living"

    # Special Purpose
    SPECIAL_PURPOSE_MAORI = "special_purpose_maori"
    SPECIAL_PURPOSE_SCHOOL = "special_purpose_school"
    SPECIAL_PURPOSE_HEALTHCARE = "special_purpose_healthcare"
    SPECIAL_PURPOSE_AIRPORT = "special_purpose_airport"

    # Future Urban
    FUTURE_URBAN = "future_urban"


class NZPropertyTenure(str, Enum):
    """New Zealand property tenure types."""

    FREEHOLD = "freehold"  # Fee simple (most common)
    LEASEHOLD = "leasehold"  # Ground lease
    CROSS_LEASE = "cross_lease"  # Shared ownership of land
    UNIT_TITLE = "unit_title"  # Apartments/units under Unit Titles Act
    MAORI_LAND = "maori_land"  # Te Ture Whenua Maori Act land


class NZDevelopmentStatus(str, Enum):
    """New Zealand property development status."""

    VACANT_LAND = "vacant_land"
    RESOURCE_CONSENT_APPLIED = "resource_consent_applied"
    RESOURCE_CONSENT_APPROVED = "resource_consent_approved"
    BUILDING_CONSENT_APPLIED = "building_consent_applied"
    BUILDING_CONSENT_APPROVED = "building_consent_approved"
    UNDER_CONSTRUCTION = "under_construction"
    CODE_COMPLIANCE_APPLIED = "code_compliance_applied"
    CODE_COMPLIANCE_ISSUED = "code_compliance_issued"
    OPERATIONAL = "operational"


class NZAcquisitionStatus(str, Enum):
    """Property acquisition status for feasibility workflow."""

    AVAILABLE = "available"
    UNDER_REVIEW = "under_review"
    ACQUIRED = "acquired"
    REJECTED = "rejected"


class NZFeasibilityStatus(str, Enum):
    """Feasibility analysis status."""

    ANALYZING = "analyzing"
    APPROVED = "approved"
    REJECTED = "rejected"
    ON_HOLD = "on_hold"


class NZComplianceStatus(str, Enum):
    """Resource/Building consent compliance check status."""

    PENDING = "pending"
    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"


class NewZealandProperty(BaseModel):
    """New Zealand property with local regulatory compliance.

    Regulatory framework:
    - Resource Management Act 1991 (RMA) - Planning and environment
    - Building Act 2004 - Building regulations
    - Local Government Act 2002 - Council powers
    - Unit Titles Act 2010 - Strata/unit titles

    Regulatory authorities:
    - Auckland Council / District Councils - Resource consents
    - Building Consent Authority (BCA) - Building consents
    - MBIE (Ministry of Business, Innovation and Employment) - National building code
    """

    __tablename__ = "new_zealand_properties"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)

    # Basic Information
    property_name = Column(String(255), nullable=False)
    address = Column(Text, nullable=False)

    # Location data
    latitude = Column(Float)
    longitude = Column(Float)
    location = Column(Geometry("POINT", srid=4326), nullable=True)

    # New Zealand Administrative Regions
    region = Column(String(100))  # e.g., Auckland, Wellington, Canterbury
    territorial_authority = Column(
        String(100)
    )  # e.g., Auckland Council, Wellington City
    suburb = Column(String(100))
    legal_description = Column(Text)  # CT/Lot/DP reference
    valuation_reference = Column(String(50))  # Council valuation number

    # Property Details
    zoning = Column(
        SQLEnum(NZPropertyZoning, values_callable=lambda x: [e.value for e in x])
    )
    district_plan_reference = Column(String(100))  # District Plan zone reference
    tenure = Column(
        SQLEnum(NZPropertyTenure, values_callable=lambda x: [e.value for e in x])
    )
    certificate_of_title = Column(String(50))  # CT reference

    # Land and Building Details (NZ uses sqm)
    land_area_sqm = Column(DECIMAL(12, 2))
    gross_floor_area_sqm = Column(DECIMAL(12, 2))
    net_floor_area_sqm = Column(DECIMAL(12, 2))

    # Development Parameters (Auckland Unitary Plan / District Plan)
    height_in_relation_to_boundary = Column(DECIMAL(5, 2))  # HIRB angle
    maximum_building_height_m = Column(DECIMAL(6, 2))
    building_height_m = Column(DECIMAL(6, 2))
    site_coverage_percent = Column(DECIMAL(5, 2))
    max_site_coverage_percent = Column(DECIMAL(5, 2))
    building_coverage_sqm = Column(DECIMAL(10, 2))
    impervious_surface_percent = Column(DECIMAL(5, 2))
    max_impervious_surface_percent = Column(DECIMAL(5, 2))
    num_storeys = Column(Integer)
    max_storeys = Column(Integer)
    setback_front_m = Column(DECIMAL(5, 2))
    setback_side_m = Column(DECIMAL(5, 2))
    setback_rear_m = Column(DECIMAL(5, 2))

    # Minimum lot size and density
    minimum_lot_size_sqm = Column(DECIMAL(10, 2))
    density_dwellings_per_ha = Column(DECIMAL(6, 2))

    # Resource Consent (RMA)
    resource_consent_required = Column(Boolean, default=False)
    resource_consent_type = Column(
        String(50)
    )  # Permitted, Controlled, Restricted Discretionary, etc.
    resource_consent_number = Column(String(50))
    resource_consent_status = Column(String(50))
    resource_consent_date = Column(Date)
    resource_consent_conditions = Column(JSON)
    notification_required = Column(Boolean, default=False)  # Public notification
    affected_party_approval = Column(Boolean, default=False)

    # Building Consent (Building Act)
    building_consent_number = Column(String(50))
    building_consent_status = Column(String(50))
    building_consent_date = Column(Date)
    bca_name = Column(String(100))  # Building Consent Authority name
    code_compliance_certificate = Column(String(50))  # CCC number
    ccc_issue_date = Column(Date)

    # Environmental and Heritage
    is_heritage_listed = Column(Boolean, default=False)
    heritage_category = Column(String(50))  # Category A, B
    heritage_new_zealand_list = Column(String(100))
    significant_ecological_area = Column(Boolean, default=False)
    outstanding_natural_feature = Column(Boolean, default=False)
    coastal_hazard_zone = Column(Boolean, default=False)
    flood_hazard_zone = Column(Boolean, default=False)

    # Infrastructure
    has_reticulated_water = Column(Boolean, default=True)
    has_reticulated_wastewater = Column(Boolean, default=True)
    has_stormwater_connection = Column(Boolean, default=True)
    infrastructure_growth_charge = Column(DECIMAL(12, 2))  # Development contributions

    # Sustainability (Homestar / Green Star NZ)
    homestar_rating = Column(String(20))  # 6-10 stars
    green_star_rating = Column(String(20))  # 1-6 stars
    nabersnz_rating = Column(String(20))  # NABERSNZ energy rating

    # Status
    development_status = Column(
        SQLEnum(NZDevelopmentStatus, values_callable=lambda x: [e.value for e in x]),
        default=NZDevelopmentStatus.VACANT_LAND,
    )
    is_crown_land = Column(Boolean, default=False)
    is_maori_land = Column(Boolean, default=False)

    # Acquisition and Feasibility Workflow
    acquisition_status = Column(
        SQLEnum(NZAcquisitionStatus, values_callable=lambda x: [e.value for e in x]),
        default=NZAcquisitionStatus.AVAILABLE,
    )
    feasibility_status = Column(
        SQLEnum(NZFeasibilityStatus, values_callable=lambda x: [e.value for e in x]),
        default=NZFeasibilityStatus.ANALYZING,
    )

    # Financial Tracking (NZD)
    estimated_acquisition_cost = Column(DECIMAL(15, 2))
    actual_acquisition_cost = Column(DECIMAL(15, 2))
    estimated_development_cost = Column(DECIMAL(15, 2))
    development_contributions = Column(DECIMAL(12, 2))  # Council development levies
    expected_revenue = Column(DECIMAL(15, 2))

    # Compliance Monitoring
    resource_consent_compliance_status = Column(
        SQLEnum(NZComplianceStatus, values_callable=lambda x: [e.value for e in x]),
        default=NZComplianceStatus.PENDING,
    )
    building_consent_compliance_status = Column(
        SQLEnum(NZComplianceStatus, values_callable=lambda x: [e.value for e in x]),
        default=NZComplianceStatus.PENDING,
    )
    compliance_notes = Column(Text)
    compliance_data = Column(JSON)
    compliance_last_checked = Column(DateTime)

    # Space Optimization Metrics
    max_developable_gfa_sqm = Column(DECIMAL(12, 2))
    gfa_utilization_percentage = Column(DECIMAL(5, 2))
    potential_additional_units = Column(Integer)

    # Valuation and Market Data
    capital_value_nzd = Column(DECIMAL(15, 2))  # CV from council
    land_value_nzd = Column(DECIMAL(15, 2))  # LV from council
    improvement_value_nzd = Column(DECIMAL(15, 2))  # IV from council
    valuation_date = Column(Date)
    rates_annual_nzd = Column(DECIMAL(10, 2))  # Council rates
    rental_yield_percentage = Column(DECIMAL(5, 2))

    # Metadata
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)
    data_source = Column(String(100))  # LINZ, Council, manual entry

    # JSON fields for flexible data
    district_plan_provisions = Column(JSON)  # Applicable plan provisions
    overlays = Column(JSON)  # Special overlays (viewshaft, volcanic, etc.)
    nearby_amenities = Column(JSON)
    development_constraints = Column(JSON)

    # Project Linking
    project_id = Column(UUID(), ForeignKey("projects.id"), nullable=True)
    owner_email = Column(String(255))

    # Relationships
    project = relationship("Project", back_populates="nz_properties")

    def __repr__(self) -> str:
        return f"<NewZealandProperty {self.property_name} ({self.legal_description})>"


__all__ = [
    "NewZealandProperty",
    "NZPropertyZoning",
    "NZPropertyTenure",
    "NZDevelopmentStatus",
    "NZAcquisitionStatus",
    "NZFeasibilityStatus",
    "NZComplianceStatus",
]
