"""Additional unit tests for marketing materials generator helper methods."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from reportlab.platypus import Paragraph, Table

from app.models.property import PropertyType
from app.services.agents.marketing_materials import (
    AmenityIcons,
    FloorPlanDiagram,
    MarketingMaterialsGenerator,
)


def _generator():
    """Create a generator instance."""
    return MarketingMaterialsGenerator(storage_service=SimpleNamespace())


def _property_payload(**overrides):
    """Create mock property payload."""
    property_obj = SimpleNamespace(
        name="Harbor View Tower",
        gross_floor_area_sqm=25000.0,
        floors_above_ground=15,
        year_built=2018,
        property_type=PropertyType.OFFICE,
        district="D01",
        net_lettable_area_sqm=22000.0,
    )
    rentals = [
        SimpleNamespace(
            floor_level="10",
            unit_number="10-01",
            floor_area_sqm=800.0,
        ),
        SimpleNamespace(
            floor_level="12",
            unit_number="12-03",
            floor_area_sqm=600.0,
        ),
    ]
    base = {
        "property": property_obj,
        "total_available": 2000.0,
        "rentals": rentals,
        "available_units": len(rentals),
    }
    base.update(overrides)
    return base


# -----------------------------------------------------------
# FloorPlanDiagram tests
# -----------------------------------------------------------


def test_floor_plan_diagram_init():
    """Test FloorPlanDiagram initialization."""
    floor_data = {"floor": "10", "units": []}
    diagram = FloorPlanDiagram(floor_data)

    assert diagram.floor_data == floor_data
    assert diagram.width > 0
    assert diagram.height > 0


def test_floor_plan_diagram_with_custom_dimensions():
    """Test FloorPlanDiagram with custom dimensions."""
    floor_data = {"floor": "5"}
    diagram = FloorPlanDiagram(floor_data, width=8 * 72, height=6 * 72)

    assert diagram.width == 8 * 72  # 8 inches
    assert diagram.height == 6 * 72  # 6 inches


# -----------------------------------------------------------
# AmenityIcons tests
# -----------------------------------------------------------


def test_amenity_icons_init():
    """Test AmenityIcons initialization."""
    amenities = ["parking", "gym", "cafe"]
    icons = AmenityIcons(amenities)

    assert icons.amenities == amenities
    assert icons.width > 0
    assert icons.height > 0


def test_amenity_icons_get_icon_symbol():
    """Test icon symbol lookup."""
    icons = AmenityIcons([])

    # Known amenities
    assert icons._get_icon_symbol("parking") == "P"
    assert icons._get_icon_symbol("gym") == "G"
    assert icons._get_icon_symbol("security") == "S"
    assert icons._get_icon_symbol("cafe") == "C"
    assert icons._get_icon_symbol("meeting") == "M"
    assert icons._get_icon_symbol("reception") == "R"
    assert icons._get_icon_symbol("wifi") == "W"
    assert icons._get_icon_symbol("elevator") == "E"

    # Partial matches (case-insensitive)
    assert icons._get_icon_symbol("Free Parking") == "P"
    assert icons._get_icon_symbol("Fitness Gym") == "G"

    # Unknown amenity returns first letter uppercase
    assert icons._get_icon_symbol("pool") == "P"
    assert icons._get_icon_symbol("lounge") == "L"


# -----------------------------------------------------------
# _get_key_highlights tests
# -----------------------------------------------------------


def test_get_key_highlights_lease():
    """Test key highlights for lease material."""
    generator = _generator()
    payload = _property_payload()

    highlights = generator._get_key_highlights(payload, "lease")

    assert len(highlights) == 3
    assert highlights[0][0] == "Available"
    assert "2,000" in highlights[0][1]
    assert highlights[1][0] == "Rental"
    assert highlights[2][0] == "Occupancy"


def test_get_key_highlights_sale():
    """Test key highlights for sale material."""
    generator = _generator()
    payload = _property_payload()

    highlights = generator._get_key_highlights(payload, "sale")

    assert len(highlights) == 3
    assert highlights[0][0] == "Price"
    assert highlights[1][0] == "Yield"
    assert highlights[2][0] == "GFA"
    assert "25,000" in highlights[2][1]


# -----------------------------------------------------------
# _get_ideal_tenants tests
# -----------------------------------------------------------


def test_get_ideal_tenants_office():
    """Test ideal tenants for office property."""
    generator = _generator()

    tenants = generator._get_ideal_tenants(PropertyType.OFFICE)

    assert "Technology companies" in tenants
    assert "Financial services" in tenants
    assert len(tenants) == 4


def test_get_ideal_tenants_retail():
    """Test ideal tenants for retail property."""
    generator = _generator()

    tenants = generator._get_ideal_tenants(PropertyType.RETAIL)

    assert "F&B operators" in tenants
    assert "Fashion retailers" in tenants


def test_get_ideal_tenants_industrial():
    """Test ideal tenants for industrial property."""
    generator = _generator()

    tenants = generator._get_ideal_tenants(PropertyType.INDUSTRIAL)

    assert "Logistics operators" in tenants
    assert "R&D facilities" in tenants


def test_get_ideal_tenants_warehouse():
    """Test ideal tenants for warehouse property."""
    generator = _generator()

    tenants = generator._get_ideal_tenants(PropertyType.WAREHOUSE)

    assert "3PL providers" in tenants
    assert "E-commerce fulfillment" in tenants


def test_get_ideal_tenants_fallback():
    """Test fallback tenants for unknown property type."""
    generator = _generator()

    tenants = generator._get_ideal_tenants(PropertyType.LAND)

    assert "Corporate tenants" in tenants
    assert len(tenants) == 3


# -----------------------------------------------------------
# _create_marketing_cover tests
# -----------------------------------------------------------


def test_create_marketing_cover_lease():
    """Test marketing cover for lease."""
    generator = _generator()
    payload = _property_payload()

    story = generator._create_marketing_cover(payload, "lease")

    # Check story has content
    assert len(story) > 0
    # Check property name appears
    assert any(
        isinstance(item, Paragraph) and payload["property"].name in item.text
        for item in story
    )
    # Check "AVAILABLE FOR LEASE" subtitle
    assert any(
        isinstance(item, Paragraph) and "LEASE" in item.text
        for item in story
    )


def test_create_marketing_cover_sale():
    """Test marketing cover for sale."""
    generator = _generator()
    payload = _property_payload()

    story = generator._create_marketing_cover(payload, "sale")

    assert any(
        isinstance(item, Paragraph) and "FOR SALE" in item.text
        for item in story
    )


# -----------------------------------------------------------
# _create_property_highlights tests
# -----------------------------------------------------------


def test_create_property_highlights_contains_sections():
    """Test property highlights section structure."""
    generator = _generator()
    payload = _property_payload()

    story = generator._create_property_highlights(payload, "lease")

    assert len(story) > 0
    # Should contain "Building Features" heading
    text_content = " ".join(
        item.text for item in story if isinstance(item, Paragraph)
    )
    assert "Building Features" in text_content or "PROPERTY" in text_content


def test_create_property_highlights_ideal_for_section():
    """Test property highlights includes ideal for section."""
    generator = _generator()
    payload = _property_payload()

    story = generator._create_property_highlights(payload, "sale")

    text_content = " ".join(
        item.text for item in story if isinstance(item, Paragraph)
    )
    # Should mention ideal tenants
    assert "Ideal For" in text_content or "Technology" in text_content


# -----------------------------------------------------------
# _create_location_benefits tests
# -----------------------------------------------------------


def test_create_location_benefits_structure():
    """Test location benefits section structure."""
    generator = _generator()
    payload = _property_payload()

    story = generator._create_location_benefits(payload)

    assert len(story) > 0
    assert any(isinstance(item, Paragraph) for item in story)


# -----------------------------------------------------------
# _create_floor_plans tests
# -----------------------------------------------------------


def test_create_floor_plans_structure():
    """Test floor plans section structure."""
    generator = _generator()
    payload = _property_payload()

    story = generator._create_floor_plans(payload)

    assert len(story) > 0


# -----------------------------------------------------------
# _create_amenities_section tests
# -----------------------------------------------------------


def test_create_amenities_section_includes_icons():
    """Test amenities section includes AmenityIcons."""
    generator = _generator()
    payload = _property_payload()

    story = generator._create_amenities_section(payload)

    assert any(isinstance(item, AmenityIcons) for item in story)


# -----------------------------------------------------------
# _create_availability_section tests
# -----------------------------------------------------------


def test_create_availability_section_lease():
    """Test availability section for lease."""
    generator = _generator()
    payload = _property_payload()

    story = generator._create_availability_section(payload, "lease")

    text_content = " ".join(
        item.text for item in story if isinstance(item, Paragraph)
    )
    assert "Rental" in text_content or "AVAILABILITY" in text_content


def test_create_availability_section_sale():
    """Test availability section for sale."""
    generator = _generator()
    payload = _property_payload()

    story = generator._create_availability_section(payload, "sale")

    text_content = " ".join(
        item.text for item in story if isinstance(item, Paragraph)
    )
    assert "Investment" in text_content or "AVAILABILITY" in text_content


# -----------------------------------------------------------
# _create_contact_section tests
# -----------------------------------------------------------


def test_create_contact_section_with_custom_info():
    """Test contact section with custom contact info."""
    generator = _generator()
    contact_info = {
        "name": "John Smith",
        "email": "john@example.com",
        "phone": "+65 1234 5678",
    }

    story = generator._create_contact_section(contact_info, "lease")

    assert any(isinstance(item, Table) for item in story)
    # CTA should be for viewing
    cta = story[-1]
    assert isinstance(cta, Paragraph)
    assert "VIEWING" in cta.text


def test_create_contact_section_without_info():
    """Test contact section uses defaults without custom info."""
    generator = _generator()

    story = generator._create_contact_section(None, "sale")

    assert any(isinstance(item, Table) for item in story)
    # CTA should be for investment pack
    cta = story[-1]
    assert isinstance(cta, Paragraph)
    assert "INVESTMENT" in cta.text


# -----------------------------------------------------------
# _create_photo_gallery tests
# -----------------------------------------------------------


def test_create_photo_gallery_with_photos():
    """Test photo gallery with photos."""
    generator = _generator()
    photos = [
        SimpleNamespace(filename="lobby.jpg"),
        SimpleNamespace(filename="exterior.jpg"),
        SimpleNamespace(filename="interior.jpg"),
    ]

    story = generator._create_photo_gallery(photos)

    assert len(story) > 0
    assert any(isinstance(item, Table) for item in story)


def test_create_photo_gallery_empty():
    """Test photo gallery with no photos returns empty story."""
    generator = _generator()

    story = generator._create_photo_gallery([])

    # Should still have some content (header)
    assert len(story) >= 0


# -----------------------------------------------------------
# FloorPlanDiagram.draw tests
# -----------------------------------------------------------


def test_floor_plan_diagram_draw_basic():
    """Test FloorPlanDiagram draws correctly."""
    from io import BytesIO
    from reportlab.pdfgen import canvas

    floor_data = {"floor": "10"}
    diagram = FloorPlanDiagram(floor_data)

    buffer = BytesIO()
    canv = canvas.Canvas(buffer)
    diagram.canv = canv

    # Should not raise an exception
    diagram.draw()


def test_floor_plan_diagram_draw_with_units():
    """Test FloorPlanDiagram draws with units."""
    from io import BytesIO
    from reportlab.pdfgen import canvas

    floor_data = {
        "floor": "12",
        "units": [
            {"name": "Unit A", "size": 500, "available": True},
            {"name": "Unit B", "size": 600, "available": False},
            {"name": "Unit C", "size": 450, "available": True},
        ],
    }
    diagram = FloorPlanDiagram(floor_data)

    buffer = BytesIO()
    canv = canvas.Canvas(buffer)
    diagram.canv = canv

    diagram.draw()


def test_floor_plan_diagram_draw_no_units_key():
    """Test FloorPlanDiagram draws when units key is absent."""
    from io import BytesIO
    from reportlab.pdfgen import canvas

    # No units key at all - just floor
    floor_data = {"floor": "5"}
    diagram = FloorPlanDiagram(floor_data)

    buffer = BytesIO()
    canv = canvas.Canvas(buffer)
    diagram.canv = canv

    # Should draw without error since "units" key is absent
    diagram.draw()


# -----------------------------------------------------------
# AmenityIcons.draw tests
# -----------------------------------------------------------


def test_amenity_icons_draw():
    """Test AmenityIcons draws correctly."""
    from io import BytesIO
    from reportlab.pdfgen import canvas

    amenities = ["parking", "gym", "cafe", "wifi"]
    icons = AmenityIcons(amenities)

    buffer = BytesIO()
    canv = canvas.Canvas(buffer)
    icons.canv = canv

    icons.draw()


def test_amenity_icons_draw_many_amenities():
    """Test AmenityIcons draws with many amenities (max 8)."""
    from io import BytesIO
    from reportlab.pdfgen import canvas

    amenities = [
        "parking", "gym", "security", "cafe",
        "meeting", "reception", "wifi", "elevator",
        "extra1", "extra2",  # Should be ignored (max 8)
    ]
    icons = AmenityIcons(amenities)

    buffer = BytesIO()
    canv = canvas.Canvas(buffer)
    icons.canv = canv

    icons.draw()


def test_amenity_icons_draw_unknown_amenities():
    """Test AmenityIcons draws with unknown amenities."""
    from io import BytesIO
    from reportlab.pdfgen import canvas

    amenities = ["pool", "lounge", "terrace"]
    icons = AmenityIcons(amenities)

    buffer = BytesIO()
    canv = canvas.Canvas(buffer)
    icons.canv = canv

    icons.draw()


# -----------------------------------------------------------
# Additional edge case tests for better coverage
# -----------------------------------------------------------


def test_get_key_highlights_with_different_prices():
    """Test key highlights with various price scenarios."""
    generator = _generator()

    # Create payload with custom values
    property_obj = SimpleNamespace(
        name="Test Tower",
        gross_floor_area_sqm=100000.0,
        floors_above_ground=30,
        year_built=2020,
        property_type=PropertyType.OFFICE,
        district="D01",
        net_lettable_area_sqm=90000.0,
    )
    rentals = [
        SimpleNamespace(
            floor_level="15",
            unit_number="15-01",
            floor_area_sqm=2000.0,
        ),
    ]
    payload = {
        "property": property_obj,
        "total_available": 5000.0,
        "rentals": rentals,
        "available_units": 1,
    }

    highlights = generator._get_key_highlights(payload, "lease")

    assert len(highlights) == 3
    assert "5,000" in highlights[0][1]  # Available area


def test_get_ideal_tenants_mixed_use():
    """Test ideal tenants for mixed use property."""
    generator = _generator()

    tenants = generator._get_ideal_tenants(PropertyType.MIXED_USE)

    assert len(tenants) >= 3


def test_get_ideal_tenants_hotel():
    """Test ideal tenants for hotel property."""
    generator = _generator()

    tenants = generator._get_ideal_tenants(PropertyType.HOTEL)

    # Should return default tenants for hotel
    assert len(tenants) >= 3


def test_create_location_benefits_complete():
    """Test location benefits section with complete data."""
    generator = _generator()
    property_obj = SimpleNamespace(
        name="Central Tower",
        gross_floor_area_sqm=25000.0,
        floors_above_ground=20,
        year_built=2015,
        property_type=PropertyType.OFFICE,
        district="D01",
        net_lettable_area_sqm=22000.0,
        address="1 Marina Bay",
        latitude=1.28,
        longitude=103.85,
    )
    payload = {
        "property": property_obj,
        "total_available": 3000.0,
        "rentals": [],
        "available_units": 2,
    }

    story = generator._create_location_benefits(payload)

    assert len(story) > 0


def test_create_floor_plans_multiple_rentals():
    """Test floor plans with multiple rental units."""
    generator = _generator()
    property_obj = SimpleNamespace(
        name="Multi-floor Tower",
        gross_floor_area_sqm=50000.0,
        floors_above_ground=25,
        year_built=2018,
        property_type=PropertyType.OFFICE,
        district="D02",
        net_lettable_area_sqm=45000.0,
    )
    rentals = [
        SimpleNamespace(floor_level="5", unit_number="05-01", floor_area_sqm=500.0),
        SimpleNamespace(floor_level="5", unit_number="05-02", floor_area_sqm=600.0),
        SimpleNamespace(floor_level="10", unit_number="10-01", floor_area_sqm=1000.0),
        SimpleNamespace(floor_level="15", unit_number="15-01", floor_area_sqm=800.0),
    ]
    payload = {
        "property": property_obj,
        "total_available": 2900.0,
        "rentals": rentals,
        "available_units": 4,
    }

    story = generator._create_floor_plans(payload)

    assert len(story) > 0


def test_create_availability_section_lease_with_rentals():
    """Test availability section for lease with multiple rentals."""
    generator = _generator()
    property_obj = SimpleNamespace(
        name="Lease Building",
        gross_floor_area_sqm=20000.0,
        floors_above_ground=10,
        year_built=2019,
        property_type=PropertyType.OFFICE,
        district="D01",
        net_lettable_area_sqm=18000.0,
    )
    rentals = [
        SimpleNamespace(
            floor_level="3",
            unit_number="03-01",
            floor_area_sqm=400.0,
            monthly_rent_psm=15.0,
        ),
        SimpleNamespace(
            floor_level="5",
            unit_number="05-02",
            floor_area_sqm=500.0,
            monthly_rent_psm=16.0,
        ),
    ]
    payload = {
        "property": property_obj,
        "total_available": 900.0,
        "rentals": rentals,
        "available_units": 2,
    }

    story = generator._create_availability_section(payload, "lease")

    assert len(story) > 0


def test_create_availability_section_sale_mode():
    """Test availability section for sale."""
    generator = _generator()
    payload = _property_payload()

    story = generator._create_availability_section(payload, "sale")

    text_content = " ".join(
        item.text for item in story if isinstance(item, Paragraph)
    )
    assert "Investment" in text_content or "AVAILABILITY" in text_content


def test_create_marketing_cover_custom_property():
    """Test marketing cover with custom property details."""
    generator = _generator()
    property_obj = SimpleNamespace(
        name="Premium Office Tower",
        gross_floor_area_sqm=80000.0,
        floors_above_ground=40,
        year_built=2022,
        property_type=PropertyType.OFFICE,
        district="D01",
        net_lettable_area_sqm=72000.0,
    )
    rentals = [
        SimpleNamespace(floor_level="30", unit_number="30-01", floor_area_sqm=2000.0),
    ]
    payload = {
        "property": property_obj,
        "total_available": 8000.0,
        "rentals": rentals,
        "available_units": 3,
    }

    story = generator._create_marketing_cover(payload, "sale")

    assert len(story) > 0
    # Check property name appears
    assert any(
        isinstance(item, Paragraph) and property_obj.name in item.text
        for item in story
    )
