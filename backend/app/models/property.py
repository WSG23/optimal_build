"""Property and building data models for Commercial Property Advisors agent."""

from enum import Enum

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.types import Enum as SQLEnum
from sqlalchemy.types import Numeric as SQLDecimal

try:
    from geoalchemy2 import Geometry
except ModuleNotFoundError:  # pragma: no cover - optional dependency fallback
    from sqlalchemy.types import UserDefinedType

    class Geometry(UserDefinedType):  # type: ignore[misc]
        """Minimal stub emulating geoalchemy2.Geometry when unavailable."""

        def __init__(self, *args: object, **kwargs: object) -> None:
            self.args = args
            self.kwargs = kwargs

        def get_col_spec(self, **_: object) -> str:
            return "GEOMETRY"


from backend._compat.datetime import utcnow

from app.models.base import UUID, BaseModel


class PropertyType(str, Enum):
    """Types of commercial properties."""

    OFFICE = "office"
    RETAIL = "retail"
    INDUSTRIAL = "industrial"
    RESIDENTIAL = "residential"
    MIXED_USE = "mixed_use"
    HOTEL = "hotel"
    WAREHOUSE = "warehouse"
    LAND = "land"
    SPECIAL_PURPOSE = "special_purpose"


class PropertyStatus(str, Enum):
    """Property development status."""

    EXISTING = "existing"
    PLANNED = "planned"
    APPROVED = "approved"
    UNDER_CONSTRUCTION = "under_construction"
    COMPLETED = "completed"
    DEMOLISHED = "demolished"


class TenureType(str, Enum):
    """Property tenure types."""

    FREEHOLD = "freehold"
    LEASEHOLD_99 = "leasehold_99"
    LEASEHOLD_999 = "leasehold_999"
    LEASEHOLD_60 = "leasehold_60"
    LEASEHOLD_30 = "leasehold_30"
    LEASEHOLD_OTHER = "leasehold_other"


def _enum_values(enum_cls: type[Enum]) -> list[str]:
    return [member.value for member in enum_cls]


class Property(BaseModel):
    """Core property entity for market intelligence."""

    __tablename__ = "properties"

    id = Column(UUID(), primary_key=True, server_default=text("gen_random_uuid()"))

    # Basic Information
    name = Column(String(255), nullable=False)
    address = Column(String(500), nullable=False)
    postal_code = Column(String(20))
    property_type = Column(
        SQLEnum(
            PropertyType,
            name="property_type",
            values_callable=_enum_values,
        ),
        nullable=False,
        index=True,
    )
    status = Column(
        SQLEnum(
            PropertyStatus,
            name="property_status",
            values_callable=_enum_values,
        ),
        default=PropertyStatus.EXISTING,
    )

    # Location
    location = Column(Geometry("POINT", srid=4326), nullable=False)
    district = Column(String(50))
    subzone = Column(String(100))
    planning_area = Column(String(100))

    # Physical Attributes
    land_area_sqm = Column(SQLDecimal(10, 2))
    gross_floor_area_sqm = Column(SQLDecimal(12, 2))
    net_lettable_area_sqm = Column(SQLDecimal(12, 2))
    building_height_m = Column(SQLDecimal(6, 2))
    floors_above_ground = Column(Integer)
    floors_below_ground = Column(Integer)
    units_total = Column(Integer)

    # Development Information
    year_built = Column(Integer)
    year_renovated = Column(Integer)
    developer = Column(String(255))
    architect = Column(String(255))

    # Legal/Regulatory
    tenure_type = Column(
        SQLEnum(
            TenureType,
            name="tenure_type",
            values_callable=_enum_values,
        )
    )
    lease_start_date = Column(Date)
    lease_expiry_date = Column(Date)
    zoning_code = Column(String(50))
    plot_ratio = Column(SQLDecimal(4, 2))

    # Heritage/Conservation
    is_conservation = Column(Boolean, default=False)
    conservation_status = Column(String(100))
    heritage_constraints = Column(JSON)

    # Additional Metadata
    ura_property_id = Column(String(50), unique=True)
    data_source = Column(String(50))
    external_references = Column(JSON)  # Links to other databases

    # Relationships
    transactions = relationship("MarketTransaction", back_populates="property")
    rental_listings = relationship("RentalListing", back_populates="property")
    development_analyses = relationship(
        "DevelopmentAnalysis", back_populates="property"
    )
    photos = relationship("PropertyPhoto", back_populates="property")

    # Indexes
    __table_args__ = (
        Index("idx_property_location", "location"),
        Index("idx_property_type_status", "property_type", "status"),
        Index("idx_property_district", "district"),
    )


class MarketTransaction(BaseModel):
    """Historical property transaction records."""

    __tablename__ = "market_transactions"

    id = Column(UUID(), primary_key=True, server_default=text("gen_random_uuid()"))

    # Property Reference
    property_id = Column(UUID(), ForeignKey("properties.id"), nullable=False)
    property = relationship("Property", back_populates="transactions")

    # Transaction Details
    transaction_date = Column(Date, nullable=False, index=True)
    transaction_type = Column(String(50))  # sale, new_sale, resale, sub_sale

    # Financial
    sale_price = Column(SQLDecimal(15, 2), nullable=False)
    psf_price = Column(SQLDecimal(10, 2))
    psm_price = Column(SQLDecimal(10, 2))

    # Parties
    buyer_type = Column(String(50))  # individual, company, REIT, foreign
    seller_type = Column(String(50))
    buyer_profile = Column(JSON)  # Additional buyer details

    # Unit Details (for strata properties)
    unit_number = Column(String(20))
    floor_area_sqm = Column(SQLDecimal(10, 2))
    floor_level = Column(Integer)

    # Market Conditions
    market_segment = Column(String(50))
    financing_type = Column(String(50))

    # Data Quality
    data_source = Column(String(50), nullable=False)
    confidence_score = Column(SQLDecimal(3, 2))  # 0-1 confidence in data accuracy

    __table_args__ = (
        Index("idx_transaction_date", "transaction_date"),
        Index("idx_transaction_property_date", "property_id", "transaction_date"),
    )


class RentalListing(BaseModel):
    """Current and historical rental listings."""

    __tablename__ = "rental_listings"

    id = Column(UUID(), primary_key=True, server_default=text("gen_random_uuid()"))

    # Property Reference
    property_id = Column(UUID(), ForeignKey("properties.id"), nullable=False)
    property = relationship("Property", back_populates="rental_listings")

    # Listing Details
    listing_date = Column(Date, nullable=False)
    listing_type = Column(String(50))  # whole_building, floor, unit
    is_active = Column(Boolean, default=True)

    # Space Details
    floor_area_sqm = Column(SQLDecimal(10, 2), nullable=False)
    floor_level = Column(String(50))  # Can be range like "10-15"
    unit_number = Column(String(50))

    # Rental Terms
    asking_rent_monthly = Column(SQLDecimal(10, 2))
    asking_psf_monthly = Column(SQLDecimal(8, 2))
    achieved_rent_monthly = Column(SQLDecimal(10, 2))  # When leased
    achieved_psf_monthly = Column(SQLDecimal(8, 2))

    # Lease Details
    lease_commencement_date = Column(Date)
    lease_term_months = Column(Integer)
    tenant_name = Column(String(255))
    tenant_trade = Column(String(100))

    # Availability
    available_date = Column(Date)
    days_on_market = Column(Integer)

    # Data Source
    listing_source = Column(String(50))
    agent_company = Column(String(255))

    __table_args__ = (
        Index("idx_rental_active", "is_active"),
        Index("idx_rental_property_active", "property_id", "is_active"),
    )


class DevelopmentPipeline(BaseModel):
    """Upcoming property development projects."""

    __tablename__ = "development_pipeline"

    id = Column(UUID(), primary_key=True, server_default=text("gen_random_uuid()"))

    # Project Information
    project_name = Column(String(255), nullable=False)
    developer = Column(String(255))
    project_type = Column(SQLEnum(PropertyType), nullable=False)

    # Location
    location = Column(Geometry("POINT", srid=4326), nullable=False)
    address = Column(String(500))
    district = Column(String(50))

    # Development Details
    total_gfa_sqm = Column(SQLDecimal(12, 2))
    total_units = Column(Integer)
    building_count = Column(Integer, default=1)

    # Timeline
    announcement_date = Column(Date)
    approval_date = Column(Date)
    construction_start = Column(Date)
    expected_completion = Column(Date)
    expected_launch = Column(Date)

    # Status
    development_status = Column(SQLEnum(PropertyStatus), nullable=False)
    completion_percentage = Column(SQLDecimal(5, 2))

    # Market Impact
    estimated_supply_impact = Column(JSON)  # Structured data on market impact
    competing_projects = Column(JSON)  # List of competing project IDs

    # Sales/Leasing Progress
    units_launched = Column(Integer, default=0)
    units_sold = Column(Integer, default=0)
    average_psf_transacted = Column(SQLDecimal(10, 2))

    # Data Source
    data_source = Column(String(50))
    last_updated = Column(DateTime, default=utcnow)

    __table_args__ = (
        Index("idx_pipeline_status", "development_status"),
        Index("idx_pipeline_completion", "expected_completion"),
        Index("idx_pipeline_location", "location"),
    )


class PropertyPhoto(BaseModel):
    """Site photos and documentation."""

    __tablename__ = "property_photos"

    id = Column(UUID(), primary_key=True, server_default=text("gen_random_uuid()"))

    # Property Reference
    property_id = Column(UUID(), ForeignKey("properties.id"), nullable=False)
    property = relationship("Property", back_populates="photos")

    # Photo Details
    storage_key = Column(String(500), nullable=False)  # S3/MinIO key
    filename = Column(String(255))
    mime_type = Column(String(50))
    file_size_bytes = Column(Integer)

    # Metadata
    capture_date = Column(DateTime)
    capture_location = Column(Geometry("POINT", srid=4326))
    photographer = Column(String(255))

    # AI Tags
    auto_tags = Column(JSON)  # AI-generated tags
    manual_tags = Column(JSON)  # User-added tags
    site_conditions = Column(JSON)  # Detected conditions

    # EXIF Data
    exif_data = Column(JSON)
    camera_model = Column(String(100))

    # Usage Rights
    copyright_owner = Column(String(255))
    usage_rights = Column(String(100))

    __table_args__ = (
        Index("idx_photo_property", "property_id"),
        Index("idx_photo_capture_date", "capture_date"),
    )


class DevelopmentAnalysis(BaseModel):
    """Development potential analysis results."""

    __tablename__ = "development_analyses"

    id = Column(UUID(), primary_key=True, server_default=text("gen_random_uuid()"))

    # Property Reference
    property_id = Column(UUID(), ForeignKey("properties.id"), nullable=False)
    property = relationship("Property", back_populates="development_analyses")

    # Analysis Type
    analysis_type = Column(
        String(50), nullable=False
    )  # raw_land, existing_building, historical
    analysis_date = Column(DateTime, default=utcnow)

    # Development Potential
    gfa_potential_sqm = Column(SQLDecimal(12, 2))
    optimal_use_mix = Column(JSON)  # {office: 60%, retail: 40%}

    # Market Indicators (No developer financials)
    market_value_estimate = Column(SQLDecimal(15, 2))  # Current market value
    projected_cap_rate = Column(SQLDecimal(5, 2))  # Market cap rate only

    # Constraints
    site_constraints = Column(JSON)
    regulatory_constraints = Column(JSON)
    heritage_constraints = Column(JSON)

    # Opportunities
    development_opportunities = Column(JSON)
    value_add_potential = Column(JSON)

    # Scenarios
    development_scenarios = Column(JSON)  # Multiple scenario comparisons
    recommended_scenario = Column(String(50))

    # Analysis Parameters
    assumptions = Column(JSON)
    methodology = Column(String(100))
    confidence_level = Column(SQLDecimal(3, 2))  # 0-1

    __table_args__ = (
        Index("idx_analysis_property_date", "property_id", "analysis_date"),
        Index("idx_analysis_type", "analysis_type"),
    )
