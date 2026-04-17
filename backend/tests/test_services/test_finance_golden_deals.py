"""Golden-reference finance validation pack for Singapore-style deal modelling."""

from __future__ import annotations

from decimal import Decimal

from app.api.v1.finance_export import (
    build_construction_interest_schedule,
    evaluate_sensitivity_bands,
)
from app.api.v1.finance_feasibility import _build_finance_analytics_summary
from app.schemas.finance import DscrEntrySchema, SensitivityBandInput
from app.services.finance import calculator


def test_golden_deal_cash_flow_dscr_and_analytics() -> None:
    cash_flows = [
        Decimal("-1250000"),
        Decimal("350000"),
        Decimal("420000"),
        Decimal("580000"),
        Decimal("610000"),
    ]
    discount_rate = Decimal("0.09")
    dscr_entries = calculator.dscr_timeline(
        [Decimal("540000"), Decimal("575000"), Decimal("620000")],
        [Decimal("420000"), Decimal("460000"), Decimal("500000")],
        period_labels=["Y1", "Y2", "Y3"],
        currency="SGD",
    )
    drawdown = calculator.drawdown_schedule(
        [
            {
                "period": "Q1",
                "equity_draw": Decimal("200000"),
                "debt_draw": Decimal("0"),
            },
            {
                "period": "Q2",
                "equity_draw": Decimal("150000"),
                "debt_draw": Decimal("350000"),
            },
            {
                "period": "Q3",
                "equity_draw": Decimal("0"),
                "debt_draw": Decimal("250000"),
            },
            {
                "period": "Q4",
                "equity_draw": Decimal("0"),
                "debt_draw": Decimal("-100000"),
            },
        ],
        currency="SGD",
    )

    npv_value = calculator.npv(discount_rate, cash_flows)
    irr_value = calculator.irr(cash_flows)
    analytics = _build_finance_analytics_summary(
        cash_flows,
        [
            DscrEntrySchema(
                period=entry.period,
                noi=str(entry.noi),
                debt_service=str(entry.debt_service),
                dscr=str(entry.dscr) if entry.dscr is not None else None,
                currency=entry.currency,
            )
            for entry in dscr_entries
        ],
        drawdown,
    )

    assert npv_value.quantize(Decimal("0.01")) == Decimal("304612.31")
    assert irr_value.quantize(Decimal("0.0001")) == Decimal("0.1859")
    assert [entry.dscr for entry in dscr_entries] == [
        Decimal("1.2857"),
        Decimal("1.2500"),
        Decimal("1.2400"),
    ]
    assert analytics is not None
    assert analytics["moic"] == "1.568"
    assert analytics["equity_multiple"] == "1.568"
    assert analytics["drawdown_summary"]["peak_debt_balance"] == "600000.00"
    buckets = {
        item["key"]: item["count"] for item in analytics["dscr_heatmap"]["buckets"]
    }
    assert buckets == {
        "lt_1": 0,
        "range_1_125": 1,
        "range_125_150": 2,
        "gte_150": 0,
    }


def test_golden_deal_construction_interest_schedule() -> None:
    drawdown = calculator.drawdown_schedule(
        [
            {
                "period": "Q1",
                "equity_draw": Decimal("200000"),
                "debt_draw": Decimal("0"),
            },
            {
                "period": "Q2",
                "equity_draw": Decimal("150000"),
                "debt_draw": Decimal("350000"),
            },
            {
                "period": "Q3",
                "equity_draw": Decimal("0"),
                "debt_draw": Decimal("250000"),
            },
            {
                "period": "Q4",
                "equity_draw": Decimal("0"),
                "debt_draw": Decimal("-100000"),
            },
        ],
        currency="SGD",
    )

    schedule, _ = build_construction_interest_schedule(
        drawdown,
        currency="SGD",
        base_interest_rate=Decimal("0.0525"),
        base_periods_per_year=4,
        capitalise_interest=True,
        facilities=[
            {
                "name": "Senior Loan",
                "amount": Decimal("500000"),
                "interest_rate": Decimal("0.045"),
                "periods_per_year": 4,
                "capitalise_interest": True,
                "upfront_fee_pct": Decimal("1.25"),
            },
            {
                "name": "Mezz Loan",
                "amount": Decimal("200000"),
                "interest_rate": Decimal("0.085"),
                "periods_per_year": 4,
                "capitalise_interest": False,
                "exit_fee_pct": Decimal("1.00"),
            },
        ],
    )

    assert schedule.total_interest == Decimal("39500.00")
    assert schedule.upfront_fee_total == Decimal("6250.00")
    assert schedule.exit_fee_total == Decimal("2000.00")
    assert [entry.interest_accrued for entry in schedule.entries] == [
        Decimal("0"),
        Decimal("2296.88"),
        Decimal("6234.38"),
        Decimal("7218.75"),
    ]
    facility_totals = {
        facility.name: facility.total_interest for facility in schedule.facilities
    }
    assert facility_totals == {
        "Senior Loan": Decimal("22500.00"),
        "Mezz Loan": Decimal("17000.00"),
    }


def test_golden_deal_sensitivity_pack() -> None:
    results, metadata = evaluate_sensitivity_bands(
        [
            SensitivityBandInput(
                parameter="Rent",
                low=Decimal("-7.5"),
                base=Decimal("0"),
                high=Decimal("5.0"),
                notes=["Revenue led"],
            ),
            SensitivityBandInput(
                parameter="Interest Rate (delta %)",
                low=Decimal("1.25"),
                base=Decimal("0"),
                high=Decimal("-0.5"),
            ),
        ],
        base_npv=Decimal("233059.40"),
        base_irr=Decimal("0.1812"),
        escalated_cost=Decimal("1250000.00"),
        base_interest_total=Decimal("39500.00"),
        currency="SGD",
    )

    assert len(results) == 6
    assert len(metadata) == 6
    rent_low = next(
        result
        for result in results
        if result.parameter == "Rent" and result.scenario == "Low"
    )
    assert rent_low.npv == Decimal("215579.95")
    assert rent_low.irr == Decimal("0.1737")
    assert rent_low.escalated_cost == Decimal("1203125.00")
    assert rent_low.total_interest == Decimal("38018.75")
    assert rent_low.notes[-1] == "Low case applies -7.5% adjustment to Rent"

    rate_high = next(
        result
        for result in results
        if result.parameter == "Interest Rate (delta %)" and result.scenario == "High"
    )
    assert rate_high.delta_label == "-0.50%"
    assert rate_high.npv == Decimal("231894.10")
    assert rate_high.irr == Decimal("0.1807")
    assert rate_high.escalated_cost == Decimal("1246875.00")
    assert rate_high.total_interest == Decimal("39401.25")
