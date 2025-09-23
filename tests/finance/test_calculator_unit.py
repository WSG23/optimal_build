"""Unit tests for deterministic finance calculator helpers."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.services.finance import calculator


def test_npv_handles_negative_cashflow_months() -> None:
    """NPV should discount positive and negative periods consistently."""

    rate = Decimal("0.05")
    cash_flows = [
        Decimal("-1000"),
        Decimal("-200"),
        Decimal("500"),
        Decimal("700"),
    ]
    expected = sum(
        cash / (Decimal("1") + rate) ** period for period, cash in enumerate(cash_flows)
    )

    result = calculator.npv(rate, cash_flows)

    assert result == expected
    assert result.quantize(Decimal("0.01")) == Decimal("-132.28")


def test_irr_matches_expected_value_for_mixed_cashflows() -> None:
    """IRR should converge on the correct root when cash flows change sign."""

    cash_flows = [
        Decimal("-1200"),
        Decimal("400"),
        Decimal("600"),
        Decimal("700"),
    ]

    result = calculator.irr(cash_flows)

    assert result.quantize(Decimal("0.0001")) == Decimal("0.1781")


def test_irr_rejects_zero_equity_sequences() -> None:
    """IRR should raise when the sequence never changes sign (zero equity)."""

    cash_flows = [Decimal("0"), Decimal("500"), Decimal("600")]

    with pytest.raises(ValueError):
        calculator.irr(cash_flows)


def test_dscr_timeline_handles_zero_debt_and_negative_income() -> None:
    """DSCR timeline should report infinity, -infinity and null ratios as appropriate."""

    incomes = [Decimal("500.00"), Decimal("-200.00"), Decimal("0")]
    debts = [Decimal("250.00"), Decimal("0"), Decimal("0")]
    labels = ["M0", "M1", "M2"]

    timeline = calculator.dscr_timeline(
        incomes,
        debts,
        period_labels=labels,
        currency="USD",
    )

    assert [entry.period for entry in timeline] == labels
    assert timeline[0].dscr == Decimal("2.0000")
    assert timeline[1].dscr == Decimal("-Infinity")
    assert timeline[2].dscr is None
    assert all(entry.currency == "USD" for entry in timeline)


def test_dscr_timeline_quantizes_inputs_and_ratios() -> None:
    """DSCR entries should be rounded to cents for cash values and 4dp for ratios."""

    incomes = [Decimal("1234.567"), Decimal("890.123")]
    debts = [Decimal("1000.001"), Decimal("456.789")]

    timeline = calculator.dscr_timeline(incomes, debts, period_labels=[1, 2])

    first, second = timeline
    assert first.noi == Decimal("1234.57")
    assert first.debt_service == Decimal("1000.00")
    assert first.dscr == Decimal("1.2346")
    assert second.noi == Decimal("890.12")
    assert second.debt_service == Decimal("456.79")
    assert second.dscr == Decimal("1.9487")
