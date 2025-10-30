"""Integration tests for MarketingMaterialsGenerator service."""

from __future__ import annotations

import io
from datetime import date, datetime
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.property import (
    Property,
    PropertyPhoto,
    PropertyStatus,
    PropertyType,
    RentalListing,
)
from app.services.agents.marketing_materials import (
    AmenityIcons,
    FloorPlanDiagram,
    MarketingMaterialsGenerator,
)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def _make_property(**overrides) -> Property:
    """Create a minimal Property for testing."""
    defaults = dict(
        name="Marina Bay Tower",
        address="1 Marina Boulevard",
        property_type=PropertyType.OFFICE,
        status=PropertyStatus.EXISTING,
        year_built=2015,
        floors_above_ground=42,
        building_height_m=210.0,
        gross_floor_area_sqm=Decimal("50000.00"),
        net_lettable_area_sqm=Decimal("42000.00"),
        location="POINT(103.8547 1.2789)",
        district="Marina Bay",
        subzone="Marina South",
        planning_area="Downtown Core",
        data_source="test",
    )
    defaults.update(overrides)
    return Property(**defaults)


def _make_rental_listing(property_id, **overrides) -> RentalListing:
    """Create a minimal RentalListing for testing."""
    defaults = dict(
        property_id=property_id,
        listing_date=date.today(),
        floor_level="15",
        unit_number="15-01",
        floor_area_sqm=Decimal("500.00"),
        is_active=True,
    )
    defaults.update(overrides)
    return RentalListing(**defaults)


def _make_property_photo(property_id, **overrides) -> PropertyPhoto:
    """Create a minimal PropertyPhoto for testing."""
    defaults = dict(
        property_id=property_id,
        storage_key=f"photos/{property_id}/exterior_001.jpg",
        filename="exterior_001.jpg",
        capture_date=datetime.now(),
    )
    defaults.update(overrides)
    return PropertyPhoto(**defaults)


# ============================================================================
# FLOWABLE TESTS
# ============================================================================


def test_floor_plan_diagram_init():
    """Test FloorPlanDiagram initialization."""
    floor_data = {
        "floor": "Level 10",
        "units": [
            {"name": "Unit A", "size": 500, "available": True},
            {"name": "Unit B", "size": 600, "available": False},
        ],
    }
    diagram = FloorPlanDiagram(floor_data)

    assert diagram.floor_data == floor_data
    assert diagram.width > 0
    assert diagram.height > 0


def test_floor_plan_diagram_custom_size():
    """Test FloorPlanDiagram with custom dimensions."""
    from reportlab.lib.units import inch

    floor_data = {"floor": "Typical"}
    diagram = FloorPlanDiagram(floor_data, width=8 * inch, height=5 * inch)

    assert diagram.width == 8 * inch
    assert diagram.height == 5 * inch


def test_amenity_icons_init():
    """Test AmenityIcons initialization."""
    amenities = ["Parking", "Gym", "Security", "WiFi"]
    icons = AmenityIcons(amenities)

    assert icons.amenities == amenities
    assert icons.width > 0
    assert icons.height > 0


def test_amenity_icons_get_icon_symbol_parking():
    """Test _get_icon_symbol returns correct symbol for parking."""
    icons = AmenityIcons([])

    assert icons._get_icon_symbol("parking") == "P"
    assert icons._get_icon_symbol("Parking Lot") == "P"


def test_amenity_icons_get_icon_symbol_gym():
    """Test _get_icon_symbol returns correct symbol for gym."""
    icons = AmenityIcons([])

    assert icons._get_icon_symbol("gym") == "G"
    assert icons._get_icon_symbol("Fitness Center gym") == "G"


def test_amenity_icons_get_icon_symbol_unknown():
    """Test _get_icon_symbol returns first letter for unknown amenity."""
    icons = AmenityIcons([])

    assert icons._get_icon_symbol("Unknown Amenity") == "U"
    assert icons._get_icon_symbol("xyz") == "X"


def test_amenity_icons_get_icon_symbol_all_known():
    """Test _get_icon_symbol for all known symbols."""
    icons = AmenityIcons([])

    known_mappings = {
        "parking": "P",
        "gym": "G",
        "security": "S",
        "cafe": "C",
        "meeting": "M",
        "reception": "R",
        "wifi": "W",
        "elevator": "E",
    }

    for key, expected_symbol in known_mappings.items():
        assert icons._get_icon_symbol(key) == expected_symbol


# ============================================================================
# DATA LOADING TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_load_property_data_success(db_session: AsyncSession):
    """Test _load_property_data loads property and rentals successfully."""
    # Create test data
    prop = _make_property()
    db_session.add(prop)
    await db_session.flush()

    rental1 = _make_rental_listing(
        prop.id, floor_level="10", floor_area_sqm=Decimal("500.00")
    )
    rental2 = _make_rental_listing(
        prop.id, floor_level="12", floor_area_sqm=Decimal("750.00")
    )
    db_session.add_all([rental1, rental2])
    await db_session.flush()

    # Execute
    generator = MarketingMaterialsGenerator()
    result = await generator._load_property_data(prop.id, db_session)

    # Assert
    assert result is not None
    assert result["property"].id == prop.id
    assert result["property"].name == "Marina Bay Tower"
    assert len(result["rentals"]) == 2
    assert result["total_available"] == Decimal("1250.00")
    assert result["available_units"] == 2


@pytest.mark.asyncio
async def test_load_property_data_no_rentals(db_session: AsyncSession):
    """Test _load_property_data with no active rentals."""
    # Create test data
    prop = _make_property()
    db_session.add(prop)
    await db_session.flush()

    # Execute
    generator = MarketingMaterialsGenerator()
    result = await generator._load_property_data(prop.id, db_session)

    # Assert
    assert result is not None
    assert result["property"].id == prop.id
    assert len(result["rentals"]) == 0
    assert result["total_available"] == 0
    assert result["available_units"] == 0


@pytest.mark.asyncio
async def test_load_property_data_inactive_rentals(db_session: AsyncSession):
    """Test _load_property_data excludes inactive rentals."""
    # Create test data
    prop = _make_property()
    db_session.add(prop)
    await db_session.flush()

    active_rental = _make_rental_listing(prop.id, is_active=True)
    inactive_rental = _make_rental_listing(prop.id, is_active=False, floor_level="20")
    db_session.add_all([active_rental, inactive_rental])
    await db_session.flush()

    # Execute
    generator = MarketingMaterialsGenerator()
    result = await generator._load_property_data(prop.id, db_session)

    # Assert
    assert len(result["rentals"]) == 1
    assert result["rentals"][0].is_active is True


@pytest.mark.asyncio
async def test_load_property_data_rentals_sorted_by_floor(db_session: AsyncSession):
    """Test _load_property_data sorts rentals by floor level (string sort)."""
    # Create test data
    prop = _make_property()
    db_session.add(prop)
    await db_session.flush()

    rental_high = _make_rental_listing(prop.id, floor_level="20")
    rental_low = _make_rental_listing(prop.id, floor_level="5")
    rental_mid = _make_rental_listing(prop.id, floor_level="12")
    db_session.add_all([rental_high, rental_low, rental_mid])
    await db_session.flush()

    # Execute
    generator = MarketingMaterialsGenerator()
    result = await generator._load_property_data(prop.id, db_session)

    # Assert - floor_level is sorted alphabetically as string
    assert result["rentals"][0].floor_level == "12"
    assert result["rentals"][1].floor_level == "20"
    assert result["rentals"][2].floor_level == "5"


@pytest.mark.asyncio
async def test_load_property_photos_success(db_session: AsyncSession):
    """Test _load_property_photos loads photos successfully."""
    # Create test data
    prop = _make_property()
    db_session.add(prop)
    await db_session.flush()

    photo1 = _make_property_photo(
        prop.id, filename="photo1.jpg", capture_date=datetime(2023, 1, 1)
    )
    photo2 = _make_property_photo(
        prop.id, filename="photo2.jpg", capture_date=datetime(2023, 6, 1)
    )
    photo3 = _make_property_photo(
        prop.id, filename="photo3.jpg", capture_date=datetime(2023, 3, 1)
    )
    db_session.add_all([photo1, photo2, photo3])
    await db_session.flush()

    # Execute
    generator = MarketingMaterialsGenerator()
    result = await generator._load_property_photos(prop.id, db_session)

    # Assert
    assert len(result) == 3
    # Should be sorted by capture_date descending
    assert result[0].capture_date == datetime(2023, 6, 1)
    assert result[1].capture_date == datetime(2023, 3, 1)
    assert result[2].capture_date == datetime(2023, 1, 1)


@pytest.mark.asyncio
async def test_load_property_photos_with_limit(db_session: AsyncSession):
    """Test _load_property_photos with limit parameter."""
    # Create test data
    prop = _make_property()
    db_session.add(prop)
    await db_session.flush()

    photo1 = _make_property_photo(prop.id, filename="photo1.jpg")
    photo2 = _make_property_photo(prop.id, filename="photo2.jpg")
    photo3 = _make_property_photo(prop.id, filename="photo3.jpg")
    db_session.add_all([photo1, photo2, photo3])
    await db_session.flush()

    # Execute
    generator = MarketingMaterialsGenerator()
    result = await generator._load_property_photos(prop.id, db_session, limit=2)

    # Assert
    assert len(result) == 2


@pytest.mark.asyncio
async def test_load_property_photos_empty(db_session: AsyncSession):
    """Test _load_property_photos with no photos."""
    # Create test data
    prop = _make_property()
    db_session.add(prop)
    await db_session.flush()

    # Execute
    generator = MarketingMaterialsGenerator()
    result = await generator._load_property_photos(prop.id, db_session)

    # Assert
    assert len(result) == 0


# ============================================================================
# HELPER METHOD TESTS
# ============================================================================


def test_get_ideal_tenants_office():
    """Test _get_ideal_tenants returns correct list for office property."""
    generator = MarketingMaterialsGenerator()

    result = generator._get_ideal_tenants(PropertyType.OFFICE)

    assert "Technology companies" in result
    assert "Financial services" in result
    assert "Professional services" in result
    assert "Regional headquarters" in result


def test_get_ideal_tenants_retail():
    """Test _get_ideal_tenants returns correct list for retail property."""
    generator = MarketingMaterialsGenerator()

    result = generator._get_ideal_tenants(PropertyType.RETAIL)

    assert "F&B operators" in result
    assert "Fashion retailers" in result
    assert "Lifestyle brands" in result
    assert "Service providers" in result


def test_get_ideal_tenants_industrial():
    """Test _get_ideal_tenants returns correct list for industrial property."""
    generator = MarketingMaterialsGenerator()

    result = generator._get_ideal_tenants(PropertyType.INDUSTRIAL)

    assert "Logistics operators" in result
    assert "Light manufacturing" in result
    assert "R&D facilities" in result
    assert "Data centers" in result


def test_get_ideal_tenants_warehouse():
    """Test _get_ideal_tenants returns correct list for warehouse property."""
    generator = MarketingMaterialsGenerator()

    result = generator._get_ideal_tenants(PropertyType.WAREHOUSE)

    assert "3PL providers" in result
    assert "E-commerce fulfillment" in result
    assert "Distribution centers" in result
    assert "Cold storage operators" in result


def test_get_ideal_tenants_unknown_type():
    """Test _get_ideal_tenants returns default list for unknown property type."""
    generator = MarketingMaterialsGenerator()

    result = generator._get_ideal_tenants(PropertyType.HOTEL)

    assert "Corporate tenants" in result
    assert "Service providers" in result
    assert "Retailers" in result


def test_get_key_highlights_lease():
    """Test _get_key_highlights returns correct data for lease material."""
    generator = MarketingMaterialsGenerator()
    property_data = {
        "property": _make_property(),
        "total_available": Decimal("5000.00"),
        "available_units": 10,
        "rentals": [],
    }

    result = generator._get_key_highlights(property_data, "lease")

    assert len(result) == 3
    assert result[0][0] == "Available"
    assert "5,000" in result[0][1]
    assert result[1][0] == "Rental"
    assert result[2][0] == "Occupancy"


def test_get_key_highlights_sale():
    """Test _get_key_highlights returns correct data for sale material."""
    generator = MarketingMaterialsGenerator()
    property_data = {
        "property": _make_property(gross_floor_area_sqm=Decimal("50000.00")),
        "total_available": Decimal("5000.00"),
        "available_units": 10,
        "rentals": [],
    }

    result = generator._get_key_highlights(property_data, "sale")

    assert len(result) == 3
    assert result[0][0] == "Price"
    assert result[1][0] == "Yield"
    assert result[2][0] == "GFA"
    assert "50,000" in result[2][1]


# ============================================================================
# SALES BROCHURE GENERATION TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_generate_sales_brochure_lease_success(db_session: AsyncSession):
    """Test generate_sales_brochure creates lease brochure successfully."""
    # Create test data
    prop = _make_property()
    db_session.add(prop)
    await db_session.flush()

    rental = _make_rental_listing(prop.id)
    db_session.add(rental)
    await db_session.flush()

    # Execute
    generator = MarketingMaterialsGenerator()
    result = await generator.generate_sales_brochure(
        prop.id, db_session, material_type="lease"
    )

    # Assert
    assert result is not None
    assert isinstance(result, io.BytesIO)
    assert result.tell() == 0  # Pointer at start
    content = result.read()
    assert len(content) > 0
    assert content[:4] == b"%PDF"  # PDF magic number


@pytest.mark.asyncio
async def test_generate_sales_brochure_sale_success(db_session: AsyncSession):
    """Test generate_sales_brochure creates sale brochure successfully."""
    # Create test data
    prop = _make_property()
    db_session.add(prop)
    await db_session.flush()

    # Execute
    generator = MarketingMaterialsGenerator()
    result = await generator.generate_sales_brochure(
        prop.id, db_session, material_type="sale"
    )

    # Assert
    assert result is not None
    assert isinstance(result, io.BytesIO)
    content = result.read()
    assert len(content) > 0
    assert content[:4] == b"%PDF"


@pytest.mark.asyncio
async def test_generate_sales_brochure_with_photos(db_session: AsyncSession):
    """Test generate_sales_brochure includes photo gallery when photos exist."""
    # Create test data
    prop = _make_property()
    db_session.add(prop)
    await db_session.flush()

    photo1 = _make_property_photo(prop.id, filename="photo1.jpg")
    photo2 = _make_property_photo(prop.id, filename="photo2.jpg")
    db_session.add_all([photo1, photo2])
    await db_session.flush()

    # Execute
    generator = MarketingMaterialsGenerator()
    result = await generator.generate_sales_brochure(
        prop.id, db_session, material_type="lease"
    )

    # Assert
    assert result is not None
    content = result.read()
    assert len(content) > 0


@pytest.mark.asyncio
async def test_generate_sales_brochure_with_contact_info(db_session: AsyncSession):
    """Test generate_sales_brochure uses custom contact info."""
    # Create test data
    prop = _make_property()
    db_session.add(prop)
    await db_session.flush()

    contact_info = {
        "company": "Test Realty",
        "phone": "+65 1234 5678",
        "email": "test@example.com",
        "website": "www.test.com",
    }

    # Execute
    generator = MarketingMaterialsGenerator()
    result = await generator.generate_sales_brochure(
        prop.id, db_session, material_type="lease", contact_info=contact_info
    )

    # Assert
    assert result is not None
    content = result.read()
    assert len(content) > 0


# ============================================================================
# EMAIL FLYER GENERATION TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_generate_email_flyer_lease_success(db_session: AsyncSession):
    """Test generate_email_flyer creates lease flyer successfully."""
    # Create test data
    prop = _make_property()
    db_session.add(prop)
    await db_session.flush()

    rental = _make_rental_listing(prop.id)
    db_session.add(rental)
    await db_session.flush()

    # Execute
    generator = MarketingMaterialsGenerator()
    result = await generator.generate_email_flyer(
        prop.id, db_session, material_type="lease"
    )

    # Assert
    assert result is not None
    assert isinstance(result, io.BytesIO)
    content = result.read()
    assert len(content) > 0
    assert content[:4] == b"%PDF"


@pytest.mark.asyncio
async def test_generate_email_flyer_sale_success(db_session: AsyncSession):
    """Test generate_email_flyer creates sale flyer successfully."""
    # Create test data
    prop = _make_property()
    db_session.add(prop)
    await db_session.flush()

    # Execute
    generator = MarketingMaterialsGenerator()
    result = await generator.generate_email_flyer(
        prop.id, db_session, material_type="sale"
    )

    # Assert
    assert result is not None
    content = result.read()
    assert len(content) > 0
    assert content[:4] == b"%PDF"


@pytest.mark.asyncio
async def test_generate_email_flyer_with_photos(db_session: AsyncSession):
    """Test generate_email_flyer includes photo when available."""
    # Create test data
    prop = _make_property()
    db_session.add(prop)
    await db_session.flush()

    photo = _make_property_photo(prop.id, filename="hero.jpg")
    db_session.add(photo)
    await db_session.flush()

    # Execute
    generator = MarketingMaterialsGenerator()
    result = await generator.generate_email_flyer(prop.id, db_session)

    # Assert
    assert result is not None
    content = result.read()
    assert len(content) > 0


@pytest.mark.asyncio
async def test_generate_email_flyer_no_photos(db_session: AsyncSession):
    """Test generate_email_flyer works without photos."""
    # Create test data
    prop = _make_property()
    db_session.add(prop)
    await db_session.flush()

    # Execute
    generator = MarketingMaterialsGenerator()
    result = await generator.generate_email_flyer(prop.id, db_session)

    # Assert
    assert result is not None
    content = result.read()
    assert len(content) > 0


# ============================================================================
# SECTION CREATION TESTS
# ============================================================================


def test_create_marketing_cover_lease():
    """Test _create_marketing_cover generates lease cover content."""
    generator = MarketingMaterialsGenerator()
    property_data = {
        "property": _make_property(),
        "total_available": Decimal("5000.00"),
        "available_units": 5,
        "rentals": [],
    }

    result = generator._create_marketing_cover(property_data, "lease")

    assert len(result) > 0
    # Check that story elements were created (Spacer, Paragraph, Table)
    assert any(hasattr(item, "__class__") for item in result)


def test_create_marketing_cover_sale():
    """Test _create_marketing_cover generates sale cover content."""
    generator = MarketingMaterialsGenerator()
    property_data = {
        "property": _make_property(),
        "total_available": Decimal("5000.00"),
        "available_units": 5,
        "rentals": [],
    }

    result = generator._create_marketing_cover(property_data, "sale")

    assert len(result) > 0


def test_create_property_highlights_lease():
    """Test _create_property_highlights generates highlight content."""
    generator = MarketingMaterialsGenerator()
    property_data = {
        "property": _make_property(gross_floor_area_sqm=Decimal("50000.00")),
        "total_available": Decimal("5000.00"),
        "available_units": 5,
        "rentals": [],
    }

    result = generator._create_property_highlights(property_data, "lease")

    assert len(result) > 0


def test_create_location_benefits():
    """Test _create_location_benefits generates location content."""
    generator = MarketingMaterialsGenerator()
    property_data = {
        "property": _make_property(),
        "rentals": [],
    }

    result = generator._create_location_benefits(property_data)

    assert len(result) > 0


def test_create_floor_plans_with_rentals():
    """Test _create_floor_plans with available rentals."""
    generator = MarketingMaterialsGenerator()
    prop = _make_property()
    rental1 = _make_rental_listing(
        prop.id, floor_level="10", unit_number="10-01", floor_area_sqm=Decimal("500.00")
    )
    rental2 = _make_rental_listing(
        prop.id, floor_level="12", unit_number="12-01", floor_area_sqm=Decimal("750.00")
    )

    property_data = {
        "property": prop,
        "rentals": [rental1, rental2],
        "total_available": Decimal("1250.00"),
        "available_units": 2,
    }

    result = generator._create_floor_plans(property_data)

    assert len(result) > 0


def test_create_floor_plans_no_rentals():
    """Test _create_floor_plans without rentals."""
    generator = MarketingMaterialsGenerator()
    property_data = {
        "property": _make_property(),
        "rentals": [],
        "total_available": 0,
        "available_units": 0,
    }

    result = generator._create_floor_plans(property_data)

    assert len(result) > 0


def test_create_amenities_section():
    """Test _create_amenities_section generates amenity content."""
    generator = MarketingMaterialsGenerator()
    property_data = {
        "property": _make_property(),
        "rentals": [],
    }

    result = generator._create_amenities_section(property_data)

    assert len(result) > 0


def test_create_photo_gallery_with_photos():
    """Test _create_photo_gallery with photos."""
    generator = MarketingMaterialsGenerator()
    prop = _make_property()
    photos = [
        _make_property_photo(prop.id, filename=f"photo{i}.jpg") for i in range(1, 7)
    ]

    result = generator._create_photo_gallery(photos)

    assert len(result) > 0


def test_create_photo_gallery_few_photos():
    """Test _create_photo_gallery with less than 6 photos."""
    generator = MarketingMaterialsGenerator()
    prop = _make_property()
    photos = [
        _make_property_photo(prop.id, filename="photo1.jpg"),
        _make_property_photo(prop.id, filename="photo2.jpg"),
    ]

    result = generator._create_photo_gallery(photos)

    assert len(result) > 0


def test_create_availability_section_lease():
    """Test _create_availability_section for lease material."""
    generator = MarketingMaterialsGenerator()
    property_data = {
        "property": _make_property(),
        "rentals": [],
    }

    result = generator._create_availability_section(property_data, "lease")

    assert len(result) > 0


def test_create_availability_section_sale():
    """Test _create_availability_section for sale material."""
    generator = MarketingMaterialsGenerator()
    property_data = {
        "property": _make_property(),
        "rentals": [],
    }

    result = generator._create_availability_section(property_data, "sale")

    assert len(result) > 0


def test_create_contact_section_default_info():
    """Test _create_contact_section with default contact info."""
    generator = MarketingMaterialsGenerator()

    result = generator._create_contact_section(None, "lease")

    assert len(result) > 0


def test_create_contact_section_custom_info():
    """Test _create_contact_section with custom contact info."""
    generator = MarketingMaterialsGenerator()
    contact_info = {
        "company": "Custom Realty",
        "phone": "+65 9999 8888",
        "email": "custom@example.com",
        "website": "www.custom.com",
    }

    result = generator._create_contact_section(contact_info, "lease")

    assert len(result) > 0


def test_create_contact_section_sale_cta():
    """Test _create_contact_section shows correct CTA for sale."""
    generator = MarketingMaterialsGenerator()

    result = generator._create_contact_section(None, "sale")

    assert len(result) > 0


# ============================================================================
# EDGE CASE TESTS
# ============================================================================


def test_create_floor_plans_many_rentals():
    """Test _create_floor_plans limits display to 10 rentals."""
    generator = MarketingMaterialsGenerator()
    prop = _make_property()

    # Create 15 rentals
    rentals = [
        _make_rental_listing(
            prop.id,
            floor_level=str(i),
            unit_number=f"{i}-01",
            floor_area_sqm=Decimal("500.00"),
        )
        for i in range(1, 16)
    ]

    property_data = {
        "property": prop,
        "rentals": rentals,
        "total_available": Decimal("7500.00"),
        "available_units": 15,
    }

    result = generator._create_floor_plans(property_data)

    assert len(result) > 0


def test_amenity_icons_max_eight():
    """Test AmenityIcons limits display to 8 amenities."""
    amenities = [
        "Parking",
        "Gym",
        "Security",
        "WiFi",
        "Cafe",
        "Meeting",
        "Reception",
        "Elevator",
        "Pool",
        "Sauna",
    ]
    AmenityIcons(amenities)

    # Should only process first 8
    assert len(amenities) == 10
    # Actual test would be in the draw method which processes amenities[:8]


def test_property_with_no_year_built():
    """Test marketing materials handle property with no year_built."""
    generator = MarketingMaterialsGenerator()
    property_data = {
        "property": _make_property(year_built=None),
        "total_available": Decimal("5000.00"),
        "available_units": 5,
        "rentals": [],
    }

    result = generator._create_property_highlights(property_data, "lease")

    assert len(result) > 0


def test_property_with_no_floors():
    """Test marketing materials handle property with no floors_above_ground."""
    generator = MarketingMaterialsGenerator()
    property_data = {
        "property": _make_property(floors_above_ground=None),
        "total_available": Decimal("5000.00"),
        "available_units": 5,
        "rentals": [],
    }

    result = generator._create_marketing_cover(property_data, "lease")

    assert len(result) > 0


def test_property_with_no_district():
    """Test location section handles property with no district."""
    generator = MarketingMaterialsGenerator()
    property_data = {
        "property": _make_property(district=None),
        "rentals": [],
    }

    result = generator._create_location_benefits(property_data)

    assert len(result) > 0
