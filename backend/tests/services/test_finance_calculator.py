"""Expanded coverage for finance calculator helpers."""

from __future__ import annotations

import os
from dataclasses import dataclass
from decimal import Decimal

import pytest

from app.services.finance import calculator as calc

# Ensure configuration loads
os.environ.setdefault("SECRET_KEY", "test-secret")


def _to_decimal(value: Decimal | float | str) -> Decimal:
    return Decimal(str(value))


def test_capital_stack_summary_balances_shares_and_ratios() -> None:
    """Shares should sum to 1.0000 and ratios/loan-to-cost derived correctly."""

    slices = [
        {"name": "Equity", "source_type": "sponsor_equity", "amount": "600"},
        {
            "name": "Senior Loan",
            "source_type": "bank_debt",
            "amount": "350",
            "rate": "0.045",
        },
        {
            "name": "Mezzanine",
            "source_type": "mezz",
            "amount": "50",
            "rate": "0.10",
        },
    ]

    summary = calc.capital_stack_summary(
        slices, currency="USD", total_development_cost="1200"
    )

    assert summary.total == _to_decimal("1000.00")
    assert summary.currency == "USD"
    assert sum(component.share for component in summary.slices) == _to_decimal("1.0000")

    assert summary.equity_total == _to_decimal("600.00")
    assert summary.debt_total == _to_decimal("400.00")
    assert summary.other_total == _to_decimal("0.00")

    assert summary.equity_ratio == _to_decimal("0.6000")
    assert summary.debt_ratio == _to_decimal("0.4000")
    assert summary.other_ratio == _to_decimal("0.0000")
    # Debt + mezzanine (other) against development cost 1200.
    assert summary.loan_to_cost == _to_decimal("0.3333")
    # Weighted debt rate uses only debt category.
    # Weighted average uses both debt tranches (350 @ 4.5%, 50 @ 10%).
    assert summary.weighted_average_debt_rate == _to_decimal("0.0519")


def test_capital_stack_summary_validates_mapping_entries() -> None:
    with pytest.raises(TypeError):
        calc.capital_stack_summary([{"name": "ok"}, "not-a-mapping"])  # type: ignore[list-item]


def test_drawdown_schedule_accumulates_balances() -> None:
    schedule = calc.drawdown_schedule(
        [
            {"period": "M1", "equity_draw": 100, "debt_draw": 0},
            {"period": "M2", "equity_draw": 50, "debt_draw": 200},
            {"period": "M3", "equity_draw": 0, "debt_draw": 150},
        ]
    )

    assert schedule.total_equity == _to_decimal("150.00")
    assert schedule.total_debt == _to_decimal("350.00")
    assert schedule.peak_debt_balance == _to_decimal("350.00")
    assert schedule.final_debt_balance == _to_decimal("350.00")
    assert [entry.period for entry in schedule.entries] == ["M1", "M2", "M3"]
    assert schedule.entries[-1].outstanding_debt == _to_decimal("350.00")


@dataclass
class _CostIndex:
    series_name: str
    jurisdiction: str
    provider: str
    period: str
    value: Decimal
    id: int = 0


def test_escalate_amount_uses_latest_index_values() -> None:
    indices = [
        _CostIndex(
            series_name="construction",
            jurisdiction="SG",
            provider="internal",
            period="2023-Q4",
            value=_to_decimal("100"),
            id=1,
        ),
        _CostIndex(
            series_name="construction",
            jurisdiction="SG",
            provider="internal",
            period="2024-Q1",
            value=_to_decimal("110"),
            id=2,
        ),
        _CostIndex(  # different provider – should be ignored
            series_name="construction",
            jurisdiction="SG",
            provider="external",
            period="2024-Q2",
            value=_to_decimal("200"),
            id=3,
        ),
    ]

    result = calc.escalate_amount(
        100,
        base_period="2023-Q4",
        indices=indices,
        series_name="construction",
        jurisdiction="SG",
        provider="internal",
    )

    # 100 * (110 / 100) -> 110.00
    assert result == _to_decimal("110.00")


def test_escalate_amount_handles_missing_base_or_zero_index() -> None:
    indices = [
        _CostIndex(
            series_name="construction",
            jurisdiction="SG",
            provider="internal",
            period="2024-Q1",
            value=_to_decimal("0"),
            id=1,
        ),
        _CostIndex(
            series_name="construction",
            jurisdiction="SG",
            provider="internal",
            period="2024-Q2",
            value=_to_decimal("120"),
            id=2,
        ),
    ]

    # Zero base value should fall back to the original amount.
    result_zero = calc.escalate_amount(
        80,
        base_period="2024-Q1",
        indices=indices,
        series_name="construction",
        jurisdiction="SG",
        provider="internal",
    )
    assert result_zero == _to_decimal("80.00")

    # Missing base period should also return the original amount.
    result_missing = calc.escalate_amount(
        90,
        base_period="2023-Q4",
        indices=indices,
        series_name="construction",
        jurisdiction="SG",
        provider="internal",
    )
    assert result_missing == _to_decimal("90.00")


def test_price_sensitivity_grid_quantises_revenue() -> None:
    grid = calc.price_sensitivity_grid(
        base_price=100,
        base_volume=10,
        price_deltas=[0, 0.1],
        volume_deltas=[0, -0.1],
    )

    assert grid.currency == "SGD"
    assert grid.prices == (Decimal("100.00"), Decimal("110.00"))
    assert grid.grid[0][0] == Decimal("1000.00")
    assert grid.grid[0][1] == Decimal("900.00")


def test_dscr_timeline_handles_zero_debt() -> None:
    timeline = calc.dscr_timeline(
        net_operating_incomes=[1000, -500, 0],
        debt_services=[0, 0, 200],
        period_labels=["Y1", "Y2", "Y3"],
    )

    assert timeline[0].dscr == Decimal("Infinity")
    assert timeline[1].dscr == Decimal("-Infinity")
    assert timeline[2].dscr == Decimal("-0.0000")


def test_dscr_timeline_raises_on_length_mismatch() -> None:
    with pytest.raises(ValueError):
        calc.dscr_timeline([1000, 1100], [900])


def test_irr_requires_sign_change() -> None:
    with pytest.raises(ValueError):
        calc.irr([100, 50, 25])


# -----------------------------------------------------------
# Additional IRR tests
# -----------------------------------------------------------


def test_irr_with_valid_cashflows() -> None:
    """Test IRR calculation with valid cash flows."""
    # Typical investment: -100 initial, then returns
    cashflows = [-1000, 300, 400, 500, 200]
    result = calc.irr(cashflows)
    assert result is not None
    assert isinstance(result, Decimal)


def test_irr_with_negative_only_cashflows() -> None:
    """Test IRR with all negative cashflows raises."""
    with pytest.raises(ValueError):
        calc.irr([-100, -50, -25])


# -----------------------------------------------------------
# NPV tests
# -----------------------------------------------------------


def test_npv_basic_calculation() -> None:
    """Test basic NPV calculation."""
    cashflows = [-1000, 300, 400, 500, 200]
    discount_rate = Decimal("0.10")

    result = calc.npv(discount_rate, cashflows)

    assert isinstance(result, Decimal)
    # NPV should be positive if returns exceed initial investment at this rate


def test_npv_with_zero_discount_rate() -> None:
    """Test NPV with zero discount rate equals sum of cashflows."""
    cashflows = [-1000, 300, 400, 500, 200]
    result = calc.npv(Decimal("0"), cashflows)

    expected = sum(Decimal(str(cf)) for cf in cashflows)
    assert result == expected


def test_npv_empty_cashflows() -> None:
    """Test NPV with empty cashflows returns zero."""
    result = calc.npv(Decimal("0.10"), [])
    assert result == Decimal("0")
