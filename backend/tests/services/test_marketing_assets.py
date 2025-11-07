from __future__ import annotations

from types import SimpleNamespace

from app.services.agents.investment_memorandum import (
    InvestmentMemorandumGenerator,
)
from app.services.agents.marketing_materials import AmenityIcons


def test_investment_memorandum_calculates_vacancy_rate():
    generator = InvestmentMemorandumGenerator()
    property_obj = SimpleNamespace(net_lettable_area_sqm=2000)
    rental_active = SimpleNamespace(is_active=True, floor_area_sqm=1200)
    rental_inactive = SimpleNamespace(is_active=False, floor_area_sqm=500)

    vacancy = generator._calculate_vacancy_rate(
        [rental_active, rental_inactive], property_obj
    )

    assert vacancy == 0.4  # 1 - (1200/2000)


def test_investment_memorandum_defaults_vacancy_without_area():
    generator = InvestmentMemorandumGenerator()
    property_obj = SimpleNamespace(net_lettable_area_sqm=None)
    vacancy = generator._calculate_vacancy_rate([], property_obj)
    assert vacancy == 0.05


def test_marketing_materials_icon_symbol_mapping():
    icons = AmenityIcons([])
    assert icons._get_icon_symbol("Secure Parking Bays") == "P"
    assert icons._get_icon_symbol("Rooftop wifi lounge") == "W"
    assert icons._get_icon_symbol("Gymnasium") == "G"
    # Fallback to first letter when unknown
    assert icons._get_icon_symbol("Library") == "L"
