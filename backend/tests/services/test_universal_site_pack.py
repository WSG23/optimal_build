from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace

from reportlab.platypus import Paragraph

from app.models.property import PropertyType, TenureType
from app.services.agents.universal_site_pack import UniversalSitePackGenerator


def _property_payload():
    property_obj = SimpleNamespace(
        name="Aurora Tower",
        address="1 Example Way",
        land_area_sqm=2000.0,
        gross_floor_area_sqm=1500.0,
        property_type=PropertyType.OFFICE,
        plot_ratio=4.2,
        building_height_m=120,
        year_built=2005,
        tenure_type=TenureType.FREEHOLD,
        district="D01",
        planning_area="Downtown",
        zoning_code="Commercial",
        is_conservation=True,
    )
    analysis = SimpleNamespace(
        gfa_potential_sqm=25000.0,
        optimal_use_mix={"office": 60, "retail": 25},
        market_value_estimate=150_000_000,
        projected_cap_rate=4.5,
        site_constraints=None,
    )
    return {
        "property": property_obj,
        "analyses": [analysis],
        "latest_analysis": analysis,
    }


def _market_payload():
    transaction = SimpleNamespace(
        transaction_date=datetime(2024, 1, 15),
        sale_price=50_000_000,
        psf_price=3200,
        floor_area_sqm=1500.0,
    )
    benchmark = SimpleNamespace(
        cap_rate_min=0.038,
        cap_rate_max=0.043,
        cap_rate_median=0.041,
    )
    return {"transactions": [transaction], "benchmarks": [benchmark]}


def _generator():
    return UniversalSitePackGenerator(storage_service=SimpleNamespace())


def test_create_sections_produce_flowables():
    generator = _generator()
    property_data = _property_payload()
    market_data = _market_payload()

    sections = [
        generator._create_executive_summary(property_data, market_data),
        generator._create_site_analysis(property_data),
        generator._create_zoning_section(property_data),
        generator._create_market_analysis(market_data),
        generator._create_development_scenarios(property_data),
        generator._create_financial_analysis(property_data),
        generator._create_risk_assessment(property_data),
        generator._create_implementation_timeline(property_data),
        generator._create_appendix_disclaimers(),
    ]

    for story in sections:
        assert story, "section should include flowables"
        assert any(isinstance(item, Paragraph) for item in story)


def test_format_use_mix_handles_missing_and_values():
    generator = _generator()
    assert generator._format_use_mix(None) == "To be determined"
    assert generator._format_use_mix({}) == "To be determined"
    formatted = generator._format_use_mix({"office": 60, "retail": 0, "hotel": 15})
    assert "office: 60" in formatted
    assert "hotel: 15" in formatted
