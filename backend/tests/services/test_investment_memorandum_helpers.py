"""Additional unit tests for investment memorandum generator helper methods."""

from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace

import pytest
from reportlab.platypus import Paragraph, Table

from app.models.property import PropertyType
from app.services.agents.investment_memorandum import (
    InvestmentHighlight,
    InvestmentMemorandumGenerator,
)


def _generator():
    """Create a generator instance."""
    return InvestmentMemorandumGenerator(storage_service=SimpleNamespace())


def _property_data(**overrides):
    """Create mock property payload."""
    property_obj = SimpleNamespace(
        name="Harbor View Tower",
        property_type=PropertyType.OFFICE,
        gross_floor_area_sqm=30000.0,
        floors_above_ground=20,
        year_built=2012,
        district="D02",
        net_lettable_area_sqm=25000.0,
        gross_floor_area=30000.0,
        land_area_sqm=5000.0,  # Required by _create_property_overview
        building_height_m=80.0,  # Required by _create_property_overview
    )
    rentals = [
        SimpleNamespace(is_active=True, floor_area_sqm=8000.0),
        SimpleNamespace(is_active=True, floor_area_sqm=12000.0),
    ]
    base = {
        "property": property_obj,
        "vacancy_rate": 0.1,
        "rentals": rentals,
    }
    base.update(overrides)
    return base


def _financial_data(**overrides):
    """Create mock financial data."""
    metrics = SimpleNamespace(
        noi=Decimal("6000000"),
        cap_rate=Decimal("0.045"),
        dscr=1.8,
        ltv=0.55,
        debt_yield=0.09,
        equity_multiple=1.7,
        irr=0.12,
        operating_expense_ratio=0.35,
        break_even_occupancy=0.65,
        net_rent_per_sqm=120.0,
    )
    base = {
        "metrics": metrics,
        "annual_rental_income": 8_000_000.0,
        "operating_expenses": 3_000_000.0,
        "estimated_value": Decimal("150000000"),
    }
    base.update(overrides)
    return base


# -----------------------------------------------------------
# InvestmentHighlight tests
# -----------------------------------------------------------


def test_investment_highlight_init():
    """Test InvestmentHighlight initialization."""
    highlights = [
        {"label": "Cap Rate", "value": "4.5%"},
        {"label": "NOI", "value": "$6M"},
    ]
    flowable = InvestmentHighlight(highlights)

    assert len(flowable.highlights) == 2
    assert flowable.width > 0


def test_investment_highlight_custom_width():
    """Test InvestmentHighlight with custom width."""
    highlights = [{"label": "Test", "value": "Value"}]
    flowable = InvestmentHighlight(highlights, width=8 * 72)

    assert flowable.width == 8 * 72


# -----------------------------------------------------------
# _calculate_vacancy_rate tests
# -----------------------------------------------------------


def test_calculate_vacancy_rate_with_rentals():
    """Test vacancy rate calculation with active rentals."""
    generator = _generator()
    property_obj = SimpleNamespace(net_lettable_area_sqm=25000.0)
    rentals = [
        SimpleNamespace(is_active=True, floor_area_sqm=10000.0),
        SimpleNamespace(is_active=True, floor_area_sqm=10000.0),
    ]

    rate = generator._calculate_vacancy_rate(rentals, property_obj)

    # 20000 / 25000 = 0.8 occupied, 0.2 vacant
    assert rate == pytest.approx(0.2)


def test_calculate_vacancy_rate_fully_occupied():
    """Test vacancy rate with full occupancy."""
    generator = _generator()
    property_obj = SimpleNamespace(net_lettable_area_sqm=25000.0)
    rentals = [
        SimpleNamespace(is_active=True, floor_area_sqm=25000.0),
    ]

    rate = generator._calculate_vacancy_rate(rentals, property_obj)

    assert rate == pytest.approx(0.0)


def test_calculate_vacancy_rate_fully_vacant():
    """Test vacancy rate with no active rentals."""
    generator = _generator()
    property_obj = SimpleNamespace(net_lettable_area_sqm=25000.0)
    rentals = []

    rate = generator._calculate_vacancy_rate(rentals, property_obj)

    assert rate == pytest.approx(1.0)


def test_calculate_vacancy_rate_no_nla():
    """Test vacancy rate with no net lettable area returns default."""
    generator = _generator()
    property_obj = SimpleNamespace(net_lettable_area_sqm=None)
    rentals = [SimpleNamespace(is_active=True, floor_area_sqm=10000.0)]

    rate = generator._calculate_vacancy_rate(rentals, property_obj)

    assert rate == 0.05  # Default 5%


def test_calculate_vacancy_rate_zero_nla():
    """Test vacancy rate with zero net lettable area returns default."""
    generator = _generator()
    property_obj = SimpleNamespace(net_lettable_area_sqm=0)
    rentals = []

    rate = generator._calculate_vacancy_rate(rentals, property_obj)

    assert rate == 0.05  # Default 5%


def test_calculate_vacancy_rate_excludes_inactive_rentals():
    """Test vacancy rate excludes inactive rentals."""
    generator = _generator()
    property_obj = SimpleNamespace(net_lettable_area_sqm=25000.0)
    rentals = [
        SimpleNamespace(is_active=True, floor_area_sqm=10000.0),
        SimpleNamespace(is_active=False, floor_area_sqm=10000.0),  # Inactive
    ]

    rate = generator._calculate_vacancy_rate(rentals, property_obj)

    # Only 10000 / 25000 = 0.4 occupied, 0.6 vacant
    assert rate == pytest.approx(0.6)


def test_calculate_vacancy_rate_handles_none_floor_area():
    """Test vacancy rate handles rentals with no floor area."""
    generator = _generator()
    property_obj = SimpleNamespace(net_lettable_area_sqm=25000.0)
    rentals = [
        SimpleNamespace(is_active=True, floor_area_sqm=10000.0),
        SimpleNamespace(is_active=True, floor_area_sqm=None),  # No area
    ]

    rate = generator._calculate_vacancy_rate(rentals, property_obj)

    # Only 10000 / 25000 = 0.4 occupied, 0.6 vacant
    assert rate == pytest.approx(0.6)


# -----------------------------------------------------------
# _create_table_of_contents tests
# -----------------------------------------------------------


def test_create_table_of_contents():
    """Test table of contents structure."""
    generator = _generator()

    story = generator._create_table_of_contents()

    assert len(story) > 0
    text_content = " ".join(
        item.text for item in story if isinstance(item, Paragraph)
    )
    assert "Executive Summary" in text_content or "TABLE OF CONTENTS" in text_content


# -----------------------------------------------------------
# _create_investment_highlights tests
# -----------------------------------------------------------


def test_create_investment_highlights_structure():
    """Test investment highlights section structure."""
    generator = _generator()
    property_payload = _property_data()
    financial_payload = _financial_data()

    story = generator._create_investment_highlights(property_payload, financial_payload)

    assert len(story) > 0
    # Should contain highlight visual
    assert any(isinstance(item, InvestmentHighlight) for item in story)


def test_create_investment_highlights_contains_value_points():
    """Test investment highlights contains value creation points."""
    generator = _generator()
    property_payload = _property_data()
    financial_payload = _financial_data()

    story = generator._create_investment_highlights(property_payload, financial_payload)

    text_content = " ".join(
        item.text for item in story if isinstance(item, Paragraph)
    )
    # Should mention value creation
    assert "Value" in text_content or "Invest" in text_content


# -----------------------------------------------------------
# _create_financial_analysis tests
# -----------------------------------------------------------


def test_create_financial_analysis_structure():
    """Test financial analysis section structure."""
    generator = _generator()
    financial_payload = _financial_data()

    story = generator._create_financial_analysis(financial_payload)

    assert len(story) > 0
    # Should have tables for financial data
    assert any(isinstance(item, Table) for item in story)


def test_create_financial_analysis_shows_metrics():
    """Test financial analysis shows key metrics."""
    generator = _generator()
    financial_payload = _financial_data()

    story = generator._create_financial_analysis(financial_payload)

    text_content = " ".join(
        item.text for item in story if isinstance(item, Paragraph)
    )
    # Should show financial content
    assert any(
        term in text_content
        for term in ["NOI", "Cap Rate", "Income", "FINANCIAL", "Analysis"]
    )


# -----------------------------------------------------------
# _create_investment_returns tests
# -----------------------------------------------------------


def test_create_investment_returns_structure():
    """Test investment returns section structure."""
    generator = _generator()
    financial_payload = _financial_data()

    story = generator._create_investment_returns(financial_payload, target_return=12.0)

    assert len(story) > 0


def test_create_investment_returns_with_different_targets():
    """Test investment returns with different target returns."""
    generator = _generator()
    financial_payload = _financial_data()

    story_conservative = generator._create_investment_returns(
        financial_payload, target_return=8.0
    )
    story_aggressive = generator._create_investment_returns(
        financial_payload, target_return=15.0
    )

    # Both should produce content
    assert len(story_conservative) > 0
    assert len(story_aggressive) > 0


# -----------------------------------------------------------
# _create_risk_analysis tests
# -----------------------------------------------------------


def test_create_risk_analysis_structure():
    """Test risk analysis section structure."""
    generator = _generator()
    property_payload = _property_data()
    market_data = {"vacancy_trend": "stable"}

    story = generator._create_risk_analysis(property_payload, market_data)

    assert len(story) > 0
    text_content = " ".join(
        item.text for item in story if isinstance(item, Paragraph)
    )
    assert "Risk" in text_content or "RISK" in text_content


def test_create_risk_analysis_with_empty_market_data():
    """Test risk analysis with empty market data."""
    generator = _generator()
    property_payload = _property_data()

    story = generator._create_risk_analysis(property_payload, {})

    # Should still produce content
    assert len(story) > 0


# -----------------------------------------------------------
# _create_exit_strategies tests
# -----------------------------------------------------------


def test_create_exit_strategies_structure():
    """Test exit strategies section structure."""
    generator = _generator()
    property_payload = _property_data()
    financial_payload = _financial_data()

    story = generator._create_exit_strategies(property_payload, financial_payload)

    assert len(story) > 0
    text_content = " ".join(
        item.text for item in story if isinstance(item, Paragraph)
    )
    assert "Exit" in text_content or "EXIT" in text_content


# -----------------------------------------------------------
# _create_transaction_structure tests
# -----------------------------------------------------------


def test_create_transaction_structure_content():
    """Test transaction structure section."""
    generator = _generator()
    property_payload = _property_data()

    story = generator._create_transaction_structure(property_payload)

    assert len(story) > 0


# -----------------------------------------------------------
# _create_appendices tests
# -----------------------------------------------------------


def test_create_appendices_structure():
    """Test appendices section structure."""
    generator = _generator()

    story = generator._create_appendices()

    assert len(story) > 0
    # Appendices contains important notice and contact information
    text_content = " ".join(
        item.text for item in story if isinstance(item, Paragraph)
    )
    assert "IMPORTANT NOTICE" in text_content or "Contact" in text_content


# -----------------------------------------------------------
# _create_executive_summary tests
# -----------------------------------------------------------


def test_create_executive_summary_contains_opportunity():
    """Test executive summary contains opportunity section."""
    generator = _generator()
    property_payload = _property_data()
    financial_payload = _financial_data()

    story = generator._create_executive_summary(
        property_payload, financial_payload, {}
    )

    assert len(story) > 0
    text_content = " ".join(
        item.text for item in story if isinstance(item, Paragraph)
    )
    assert "Opportunity" in text_content or "investment" in text_content.lower()


def test_create_executive_summary_shows_property_name():
    """Test executive summary shows property name."""
    generator = _generator()
    property_payload = _property_data()
    financial_payload = _financial_data()

    story = generator._create_executive_summary(
        property_payload, financial_payload, {}
    )

    text_content = " ".join(
        item.text for item in story if isinstance(item, Paragraph)
    )
    assert property_payload["property"].name in text_content


# -----------------------------------------------------------
# _create_property_overview tests
# -----------------------------------------------------------


def test_create_property_overview_structure():
    """Test property overview section structure."""
    generator = _generator()
    # Add all required properties
    property_obj = SimpleNamespace(
        name="Test Building",
        property_type=PropertyType.OFFICE,
        gross_floor_area_sqm=30000.0,
        floors_above_ground=20,
        year_built=2012,
        district="D02",
        net_lettable_area_sqm=25000.0,
        land_area_sqm=5000.0,
        building_height_m=80.0,
        address="123 Main Street",
        latitude=1.3,
        longitude=103.8,
        units_total=150,  # Required for parking spaces
        year_renovated=2020,  # Required for last renovation
    )
    property_payload = {
        "property": property_obj,
        "vacancy_rate": 0.1,
        "rentals": [],
    }

    story = generator._create_property_overview(property_payload)

    assert len(story) > 0


# -----------------------------------------------------------
# _create_location_analysis tests
# -----------------------------------------------------------


def test_create_location_analysis_structure():
    """Test location analysis section structure."""
    generator = _generator()
    property_obj = SimpleNamespace(
        name="Test Building",
        property_type=PropertyType.OFFICE,
        gross_floor_area_sqm=30000.0,
        floors_above_ground=20,
        year_built=2012,
        district="D02",
        net_lettable_area_sqm=25000.0,
        land_area_sqm=5000.0,
        building_height_m=80.0,
        address="123 Main Street",
        latitude=1.3,
        longitude=103.8,
        units_total=150,
        year_renovated=2020,
    )
    property_payload = {
        "property": property_obj,
        "vacancy_rate": 0.1,
        "rentals": [],
    }
    # current_cycle needs to be an object with specific attributes
    market_data = {
        "current_cycle": SimpleNamespace(
            cycle_phase="expansion",
            price_momentum=0.05,
            rental_momentum=0.03,
            cycle_outlook="favorable growth conditions",
        ),
        "comparables": [],  # Also required
    }

    story = generator._create_location_analysis(property_payload, market_data)

    assert len(story) > 0
    text_content = " ".join(
        item.text for item in story if isinstance(item, Paragraph)
    )
    assert "Location" in text_content or "LOCATION" in text_content


# -----------------------------------------------------------
# _create_investment_cover tests
# -----------------------------------------------------------


def test_create_investment_cover():
    """Test investment cover page creation."""
    from app.services.agents.pdf_generator import CoverPage

    generator = _generator()
    property_payload = _property_data()
    financial_payload = _financial_data()

    cover = generator._create_investment_cover(property_payload, financial_payload)

    assert isinstance(cover, CoverPage)


# -----------------------------------------------------------
# InvestmentHighlight.draw tests
# -----------------------------------------------------------


def test_investment_highlight_draw():
    """Test InvestmentHighlight draws correctly."""
    from io import BytesIO
    from reportlab.pdfgen import canvas

    highlights = [
        {"label": "Cap Rate", "value": "4.5%"},
        {"label": "NOI", "value": "$6M"},
        {"label": "IRR", "value": "12%"},
    ]
    flowable = InvestmentHighlight(highlights)

    # Create a mock canvas to test drawing
    buffer = BytesIO()
    canv = canvas.Canvas(buffer)
    flowable.canv = canv

    # Should not raise an exception
    flowable.draw()


def test_investment_highlight_draw_single_highlight():
    """Test InvestmentHighlight draws with single highlight."""
    from io import BytesIO
    from reportlab.pdfgen import canvas

    highlights = [{"label": "Yield", "value": "5.2%"}]
    flowable = InvestmentHighlight(highlights)

    buffer = BytesIO()
    canv = canvas.Canvas(buffer)
    flowable.canv = canv

    flowable.draw()


# -----------------------------------------------------------
# Location analysis with comparables tests
# -----------------------------------------------------------


def test_create_location_analysis_with_comparables():
    """Test location analysis section with comparable transactions."""
    from datetime import date

    generator = _generator()
    property_obj = SimpleNamespace(
        name="Test Building",
        property_type=PropertyType.OFFICE,
        gross_floor_area_sqm=30000.0,
        floors_above_ground=20,
        year_built=2012,
        district="D02",
        net_lettable_area_sqm=25000.0,
        land_area_sqm=5000.0,
        building_height_m=80.0,
        address="123 Main Street",
        latitude=1.3,
        longitude=103.8,
        units_total=150,
        year_renovated=2020,
    )
    property_payload = {
        "property": property_obj,
        "vacancy_rate": 0.1,
        "rentals": [],
    }

    # Create comparables with required attributes
    comp1 = SimpleNamespace(
        transaction_date=date(2024, 6, 15),
        property=SimpleNamespace(property_type=PropertyType.OFFICE),
        psf_price=3200.0,
        floor_area_sqm=5000.0,
    )
    comp2 = SimpleNamespace(
        transaction_date=date(2024, 3, 10),
        property=SimpleNamespace(property_type=PropertyType.OFFICE),
        psf_price=3100.0,
        floor_area_sqm=4500.0,
    )

    market_data = {
        "current_cycle": SimpleNamespace(
            cycle_phase="expansion",
            price_momentum=0.05,
            rental_momentum=0.03,
            cycle_outlook="favorable growth conditions",
        ),
        "comparables": [comp1, comp2],
    }

    story = generator._create_location_analysis(property_payload, market_data)

    assert len(story) > 0
    # Should contain table with comparables
    assert any(isinstance(item, Table) for item in story)


def test_create_location_analysis_no_cycle():
    """Test location analysis when current_cycle is None."""
    generator = _generator()
    property_obj = SimpleNamespace(
        name="Test Building",
        property_type=PropertyType.OFFICE,
        gross_floor_area_sqm=30000.0,
        floors_above_ground=20,
        year_built=2012,
        district="D02",
        net_lettable_area_sqm=25000.0,
        land_area_sqm=5000.0,
        building_height_m=80.0,
        address="123 Main Street",
        latitude=1.3,
        longitude=103.8,
        units_total=150,
        year_renovated=2020,
    )
    property_payload = {
        "property": property_obj,
        "vacancy_rate": 0.1,
        "rentals": [],
    }

    market_data = {
        "current_cycle": None,
        "comparables": [],
    }

    story = generator._create_location_analysis(property_payload, market_data)

    # Should still produce content even without cycle data
    assert len(story) > 0


# -----------------------------------------------------------
# Additional helper method tests
# -----------------------------------------------------------


def test_create_financial_analysis_with_different_values():
    """Test financial analysis with various metric values."""
    generator = _generator()
    metrics = SimpleNamespace(
        noi=Decimal("10000000"),
        cap_rate=Decimal("0.05"),
        dscr=2.0,
        ltv=0.6,
        debt_yield=0.10,
        equity_multiple=2.0,
        irr=0.15,
        operating_expense_ratio=0.28,
        break_even_occupancy=0.55,
        net_rent_per_sqm=150.0,
    )
    financial_payload = {
        "metrics": metrics,
        "annual_rental_income": 15_000_000.0,
        "operating_expenses": 4_200_000.0,
        "estimated_value": Decimal("200000000"),
    }

    story = generator._create_financial_analysis(financial_payload)

    assert len(story) > 0
    assert any(isinstance(item, Table) for item in story)


def test_create_investment_returns_various_targets():
    """Test investment returns with various target values."""
    generator = _generator()
    financial_payload = _financial_data()

    # Very low target
    story_low = generator._create_investment_returns(financial_payload, target_return=5.0)
    assert len(story_low) > 0

    # High target
    story_high = generator._create_investment_returns(financial_payload, target_return=20.0)
    assert len(story_high) > 0

    # No target (None)
    story_none = generator._create_investment_returns(financial_payload, target_return=None)
    assert len(story_none) > 0


def test_create_risk_analysis_various_conditions():
    """Test risk analysis with various market conditions."""
    generator = _generator()
    property_payload = _property_data()

    # Market with high vacancy
    market_data = {"vacancy_trend": "increasing", "supply_pipeline": "high"}
    story = generator._create_risk_analysis(property_payload, market_data)
    assert len(story) > 0


def test_create_exit_strategies_office():
    """Test exit strategies for office property."""
    generator = _generator()
    property_payload = _property_data()
    financial_payload = _financial_data()

    story = generator._create_exit_strategies(property_payload, financial_payload)

    assert len(story) > 0
    text_content = " ".join(
        item.text for item in story if isinstance(item, Paragraph)
    )
    assert "Exit" in text_content or "EXIT" in text_content


def test_create_transaction_structure_various_properties():
    """Test transaction structure for various property types."""
    generator = _generator()

    # Test with retail property
    property_obj = SimpleNamespace(
        name="Retail Mall",
        property_type=PropertyType.RETAIL,
        gross_floor_area_sqm=50000.0,
        floors_above_ground=5,
        year_built=2010,
        district="D09",
        net_lettable_area_sqm=45000.0,
        gross_floor_area=50000.0,
        land_area_sqm=10000.0,
        building_height_m=25.0,
    )
    property_payload = {
        "property": property_obj,
        "vacancy_rate": 0.05,
        "rentals": [],
    }

    story = generator._create_transaction_structure(property_payload)

    assert len(story) > 0
