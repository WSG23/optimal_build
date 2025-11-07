from __future__ import annotations

from types import SimpleNamespace

from reportlab.platypus import Paragraph, Table

from app.models.property import PropertyType
from app.services.agents.marketing_materials import (
    AmenityIcons,
    MarketingMaterialsGenerator,
)


def _property_payload():
    property_obj = SimpleNamespace(
        name="Civic Square",
        gross_floor_area_sqm=25000.0,
        floors_above_ground=15,
        year_built=2018,
        property_type=PropertyType.OFFICE,
        district="D01",
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
    return {
        "property": property_obj,
        "total_available": 2000.0,
        "rentals": rentals,
        "available_units": len(rentals),
    }


def _generator():
    return MarketingMaterialsGenerator(storage_service=SimpleNamespace())


def test_property_and_location_sections_return_content():
    generator = _generator()
    payload = _property_payload()

    property_section = generator._create_property_highlights(payload, "lease")
    location_section = generator._create_location_benefits(payload)
    floor_section = generator._create_floor_plans(payload)

    assert any(isinstance(item, Paragraph) for item in property_section)
    assert any(isinstance(item, Paragraph) for item in location_section)
    assert any(isinstance(item, Paragraph) for item in floor_section)


def test_contact_section_uses_defaults_and_cta():
    generator = _generator()
    story = generator._create_contact_section(contact_info=None, material_type="sale")

    # Contact table should be present as a Table
    assert any(isinstance(item, Table) for item in story)
    cta_paragraph = story[-1]
    assert isinstance(cta_paragraph, Paragraph)
    assert "REQUEST INVESTMENT PACK" in cta_paragraph.text


def test_highlights_and_tenants_helpers():
    generator = _generator()
    payload = _property_payload()
    highlights = generator._get_key_highlights(payload, "sale")
    assert highlights[0][0] == "Price"

    tenants = generator._get_ideal_tenants(PropertyType.OFFICE)
    assert "Technology companies" in tenants


def test_marketing_cover_and_amenities_sections():
    generator = _generator()
    payload = _property_payload()

    cover = generator._create_marketing_cover(payload, "sale")
    assert any(
        isinstance(item, Paragraph) and payload["property"].name in item.text
        for item in cover
    )

    amenities_story = generator._create_amenities_section(payload)
    assert any(isinstance(item, AmenityIcons) for item in amenities_story)


def test_availability_section_handles_lease_and_sale_branches():
    generator = _generator()
    payload = _property_payload()

    lease_story = generator._create_availability_section(payload, material_type="lease")
    assert any(
        isinstance(item, Paragraph) and "Rental Rates" in item.text
        for item in lease_story
    )

    sale_story = generator._create_availability_section(payload, material_type="sale")
    assert any(
        isinstance(item, Paragraph) and "Investment Summary" in item.text
        for item in sale_story
    )


def test_photo_gallery_renders_placeholders():
    generator = _generator()
    photos = [
        SimpleNamespace(filename="Lobby.jpg"),
        SimpleNamespace(filename="Atrium.jpg"),
        SimpleNamespace(filename="SkyGarden.jpg"),
    ]
    gallery = generator._create_photo_gallery(photos)
    assert any(isinstance(item, Table) for item in gallery)
