"""Unit tests for finance real-estate metric helpers."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.services.finance import re_metrics


def test_calculate_noi_includes_other_income_and_vacancy_loss() -> None:
    noi = re_metrics.calculate_noi(
        gross_rental_income=100_000,
        other_income=5_000,
        vacancy_rate=Decimal("0.05"),
        operating_expenses=20_000,
    )
    # 100k + 5k = 105k total potential, 5% vacancy -> 5,250, NOI = 105k - 5,250 - 20k
    assert noi == Decimal("79750.00")


@pytest.mark.parametrize(
    "noi, property_value, expected",
    [
        (80_000, 1_000_000, Decimal("0.0800")),
        (0, 1_000_000, Decimal("0.0000")),
    ],
)
def test_calculate_cap_rate_rounds_to_four_decimals(
    noi, property_value, expected
) -> None:
    result = re_metrics.calculate_cap_rate(noi, property_value)
    assert result == expected


def test_calculate_cap_rate_returns_none_when_value_zero() -> None:
    assert re_metrics.calculate_cap_rate(100_000, 0) is None


def test_cash_on_cash_return_handles_zero_investment() -> None:
    assert re_metrics.calculate_cash_on_cash_return(10_000, 0) is None

    result = re_metrics.calculate_cash_on_cash_return(75_500, 300_000)
    assert result == Decimal("0.2517")


def test_gross_rent_multiplier_rounds_to_two_decimals() -> None:
    grm = re_metrics.calculate_gross_rent_multiplier(1_200_000, 180_000)
    assert grm == Decimal("6.67")


def test_debt_metrics_return_none_when_denominator_zero() -> None:
    assert re_metrics.calculate_debt_yield(120_000, 0) is None
    assert re_metrics.calculate_loan_to_value(720_000, 0) is None
    assert re_metrics.calculate_property_value_from_noi(120_000, 0) is None


def test_vacancy_loss_and_operating_expense_ratio() -> None:
    loss = re_metrics.calculate_vacancy_loss(200_000, Decimal("0.045"))
    assert loss == Decimal("9000.00")

    assert (
        re_metrics.calculate_operating_expense_ratio(60_000, 0) is None
    ), "Zero income should return None"

    oer = re_metrics.calculate_operating_expense_ratio(60_000, 180_500)
    assert oer == Decimal("0.3324")


def test_rental_yield_gross_and_net() -> None:
    gross = re_metrics.calculate_rental_yield(180_000, 1_200_000)
    assert gross == Decimal("0.1500")

    net = re_metrics.calculate_rental_yield(
        180_000,
        1_200_000,
        gross=False,
        operating_expenses=60_000,
    )
    assert net == Decimal("0.1000")


def test_calculate_comprehensive_metrics_populates_all_fields() -> None:
    metrics = re_metrics.calculate_comprehensive_metrics(
        property_value=1_200_000,
        gross_rental_income=180_000,
        operating_expenses=60_000,
        loan_amount=720_000,
        annual_debt_service=45_000,
        initial_cash_investment=300_000,
        vacancy_rate=Decimal("0.05"),
        other_income=10_000,
    )

    assert metrics.noi == Decimal("120500.00")
    assert metrics.cap_rate == Decimal("0.1004")
    assert metrics.debt_yield == Decimal("0.1674")
    assert metrics.ltv_ratio == Decimal("0.6000")
    assert metrics.cash_on_cash_return == Decimal("0.2517")
    assert metrics.dscr == Decimal("2.6778")
    assert metrics.gross_rent_multiplier == Decimal("6.67")
    assert metrics.rental_yield == Decimal("0.1000")
    assert metrics.operating_expense_ratio == Decimal("0.3324")


def test_value_property_multiple_approaches_averages_present_methods() -> None:
    valuation = re_metrics.value_property_multiple_approaches(
        noi=120_000,
        market_cap_rate=Decimal("0.06"),
        comparable_psf=1_000,
        property_size_sqf=1_500,
        replacement_cost_psf=800,
        land_value=300_000,
        depreciation_factor=Decimal("0.85"),
    )

    assert valuation.income_approach_value == Decimal("2000000.00")
    assert valuation.comparable_sales_value == Decimal("1500000.00")
    assert valuation.replacement_cost_value == Decimal("1320000.00")
    assert valuation.recommended_value == Decimal("1606666.67")
    assert valuation.currency == "SGD"
