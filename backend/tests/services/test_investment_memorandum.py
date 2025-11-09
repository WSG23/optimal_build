from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace

from reportlab.platypus import Paragraph

from app.models.property import PropertyType
from app.services.agents.investment_memorandum import InvestmentMemorandumGenerator


def _property_data():
    property_obj = SimpleNamespace(
        name="Harbor View",
        property_type=PropertyType.OFFICE,
        gross_floor_area_sqm=30000.0,
        floors_above_ground=20,
        year_built=2012,
        district="D02",
        net_lettable_area_sqm=25000.0,
        gross_floor_area=30000.0,
    )
    rentals = [
        SimpleNamespace(is_active=True, floor_area_sqm=8000.0),
        SimpleNamespace(is_active=True, floor_area_sqm=12000.0),
    ]
    return {
        "property": property_obj,
        "vacancy_rate": 0.1,
        "rentals": rentals,
    }


def _financial_data():
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
    return {
        "metrics": metrics,
        "annual_rental_income": 8_000_000.0,
        "operating_expenses": 3_000_000.0,
        "estimated_value": Decimal("150000000"),
    }


def _generator():
    return InvestmentMemorandumGenerator(storage_service=SimpleNamespace())


def test_memorandum_sections_cover_major_blocks():
    generator = _generator()
    property_payload = _property_data()
    financial_payload = _financial_data()

    sections = [
        generator._create_investment_highlights(property_payload, financial_payload),
        generator._create_financial_analysis(financial_payload),
        generator._create_investment_returns(financial_payload, target_return=11.0),
        generator._create_risk_analysis(property_payload, {}),
        generator._create_exit_strategies(property_payload, financial_payload),
        generator._create_transaction_structure(property_payload),
        generator._create_appendices(),
    ]

    for story in sections:
        assert story
        assert any(isinstance(item, Paragraph) for item in story)


def test_calculate_vacancy_rate_uses_lettable_area():
    generator = _generator()
    property_payload = _property_data()
    rentals = property_payload["rentals"]
    rate = generator._calculate_vacancy_rate(rentals, property_payload["property"])
    assert 0 < rate < 1
