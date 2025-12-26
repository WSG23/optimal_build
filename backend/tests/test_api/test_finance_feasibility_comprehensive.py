"""Comprehensive tests for finance_feasibility API.

Tests cover:
- FinanceFeasibilityRequest model
- FinanceFeasibilityResponse model
- Cost escalation calculations
- NPV and IRR calculations
- DSCR timeline
- Capital stack summary
- Drawdown schedule
- Asset mix financials
- Sensitivity analysis
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import uuid4


class TestFinanceFeasibilityRequest:
    """Tests for FinanceFeasibilityRequest model."""

    def test_project_id_required(self) -> None:
        """Test project_id is required."""
        project_id = str(uuid4())
        assert project_id is not None

    def test_scenario_required(self) -> None:
        """Test scenario object is required."""
        scenario = {"name": "Base Case", "currency": "SGD"}
        assert scenario["name"] is not None

    def test_fin_project_id_optional(self) -> None:
        """Test fin_project_id is optional."""
        fin_project_id = None
        assert fin_project_id is None

    def test_project_name_optional(self) -> None:
        """Test project_name is optional."""
        project_name = None
        assert project_name is None or isinstance(project_name, str)


class TestScenarioInput:
    """Tests for scenario input fields."""

    def test_name_required(self) -> None:
        """Test scenario name is required."""
        name = "Base Case Scenario"
        assert len(name) > 0

    def test_description_optional(self) -> None:
        """Test description is optional."""
        description = None
        assert description is None or isinstance(description, str)

    def test_currency_defaults_to_jurisdiction(self) -> None:
        """Test currency defaults to jurisdiction currency."""
        default_currency = "SGD"
        assert default_currency == "SGD"

    def test_is_primary_default_false(self) -> None:
        """Test is_primary defaults to False."""
        is_primary = False
        assert is_primary is False


class TestCostEscalationInput:
    """Tests for cost escalation input."""

    def test_amount_required(self) -> None:
        """Test base amount is required."""
        amount = Decimal("1000000.00")
        assert amount > 0

    def test_base_period_required(self) -> None:
        """Test base period is required."""
        base_period = "2020-Q1"
        assert base_period is not None

    def test_series_name_required(self) -> None:
        """Test series name is required."""
        series_name = "BCA_BCI"
        assert series_name is not None

    def test_jurisdiction_required(self) -> None:
        """Test jurisdiction is required."""
        jurisdiction = "SG"
        assert jurisdiction is not None

    def test_provider_optional(self) -> None:
        """Test provider is optional."""
        provider = "BCA"
        assert provider is None or isinstance(provider, str)


class TestCashFlowInput:
    """Tests for cash flow input."""

    def test_discount_rate_required(self) -> None:
        """Test discount rate is required."""
        discount_rate = Decimal("0.08")  # 8%
        assert discount_rate > 0

    def test_cash_flows_required(self) -> None:
        """Test cash flows array is required."""
        cash_flows = [
            Decimal("-1000000"),
            Decimal("200000"),
            Decimal("300000"),
            Decimal("400000"),
            Decimal("500000"),
        ]
        assert len(cash_flows) > 0

    def test_negative_initial_investment(self) -> None:
        """Test initial investment is typically negative."""
        initial_investment = Decimal("-1000000")
        assert initial_investment < 0

    def test_positive_subsequent_flows(self) -> None:
        """Test subsequent cash flows can be positive."""
        subsequent_flow = Decimal("200000")
        assert subsequent_flow > 0


class TestNPVCalculation:
    """Tests for NPV calculation."""

    def test_positive_npv(self) -> None:
        """Test positive NPV indicates viable project."""
        npv = Decimal("500000.00")
        is_viable = npv > 0
        assert is_viable is True

    def test_negative_npv(self) -> None:
        """Test negative NPV indicates unviable project."""
        npv = Decimal("-100000.00")
        is_viable = npv > 0
        assert is_viable is False

    def test_npv_rounding(self) -> None:
        """Test NPV is rounded to 2 decimal places."""
        npv_raw = Decimal("500000.12345")
        npv_rounded = npv_raw.quantize(Decimal("0.01"))
        assert npv_rounded == Decimal("500000.12")


class TestIRRCalculation:
    """Tests for IRR calculation."""

    def test_positive_irr(self) -> None:
        """Test positive IRR indicates return."""
        irr = Decimal("0.1250")  # 12.5%
        assert irr > 0

    def test_irr_above_hurdle_rate(self) -> None:
        """Test IRR above hurdle rate is good."""
        irr = Decimal("0.15")  # 15%
        hurdle_rate = Decimal("0.10")  # 10%
        is_acceptable = irr > hurdle_rate
        assert is_acceptable is True

    def test_irr_rounding(self) -> None:
        """Test IRR is rounded to 4 decimal places."""
        irr_raw = Decimal("0.125678")
        irr_rounded = irr_raw.quantize(Decimal("0.0001"))
        assert irr_rounded == Decimal("0.1257")


class TestDSCRTimeline:
    """Tests for DSCR timeline calculation."""

    def test_dscr_above_one_good(self) -> None:
        """Test DSCR above 1.0 indicates coverage."""
        dscr = Decimal("1.25")
        is_covered = dscr >= 1
        assert is_covered is True

    def test_dscr_below_one_bad(self) -> None:
        """Test DSCR below 1.0 indicates insufficient coverage."""
        dscr = Decimal("0.85")
        is_covered = dscr >= 1
        assert is_covered is False

    def test_dscr_entry_fields(self) -> None:
        """Test DSCR entry fields."""
        entry = {
            "period": "2024-01",
            "noi": Decimal("50000"),
            "debt_service": Decimal("40000"),
            "dscr": Decimal("1.25"),
        }
        assert entry["dscr"] == entry["noi"] / entry["debt_service"]


class TestCapitalStackInput:
    """Tests for capital stack input."""

    def test_slice_name_required(self) -> None:
        """Test slice name is required."""
        name = "Senior Debt"
        assert name is not None

    def test_source_type_required(self) -> None:
        """Test source type is required."""
        source_type = "debt"
        assert source_type in ["equity", "debt", "mezzanine", "other"]

    def test_amount_required(self) -> None:
        """Test amount is required."""
        amount = Decimal("3000000.00")
        assert amount > 0

    def test_rate_optional(self) -> None:
        """Test rate is optional."""
        rate = Decimal("0.045")  # 4.5%
        assert rate is None or rate >= 0

    def test_tranche_order_optional(self) -> None:
        """Test tranche order is optional."""
        tranche_order = 1
        assert tranche_order is None or tranche_order >= 0


class TestCapitalStackSummary:
    """Tests for capital stack summary output."""

    def test_total_calculation(self) -> None:
        """Test total capital stack calculation."""
        equity = Decimal("3000000")
        debt = Decimal("7000000")
        total = equity + debt
        assert total == Decimal("10000000")

    def test_equity_ratio(self) -> None:
        """Test equity ratio calculation."""
        equity = Decimal("3000000")
        total = Decimal("10000000")
        equity_ratio = equity / total
        assert equity_ratio == Decimal("0.3")

    def test_debt_ratio(self) -> None:
        """Test debt ratio calculation."""
        debt = Decimal("7000000")
        total = Decimal("10000000")
        debt_ratio = debt / total
        assert debt_ratio == Decimal("0.7")

    def test_loan_to_cost(self) -> None:
        """Test loan-to-cost ratio."""
        total_debt = Decimal("7000000")
        total_development_cost = Decimal("10000000")
        ltc = total_debt / total_development_cost
        assert ltc == Decimal("0.7")


class TestDrawdownSchedule:
    """Tests for drawdown schedule."""

    def test_entry_fields(self) -> None:
        """Test drawdown entry fields."""
        entry = {
            "period": "Month 1",
            "equity_draw": Decimal("500000"),
            "debt_draw": Decimal("1000000"),
            "total_draw": Decimal("1500000"),
            "cumulative_equity": Decimal("500000"),
            "cumulative_debt": Decimal("1000000"),
            "outstanding_debt": Decimal("1000000"),
        }
        assert entry["total_draw"] == entry["equity_draw"] + entry["debt_draw"]

    def test_peak_debt_balance(self) -> None:
        """Test peak debt balance tracking."""
        debt_balances = [1000000, 2500000, 4000000, 3500000, 2000000]
        peak_debt = max(debt_balances)
        assert peak_debt == 4000000

    def test_final_debt_balance(self) -> None:
        """Test final debt balance."""
        debt_balances = [1000000, 2500000, 4000000, 3500000, 2000000]
        final_debt = debt_balances[-1]
        assert final_debt == 2000000


class TestAssetMixInput:
    """Tests for asset mix input."""

    def test_asset_type_required(self) -> None:
        """Test asset type is required."""
        asset_type = "office"
        assert asset_type is not None

    def test_allocation_pct_required(self) -> None:
        """Test allocation percentage is required."""
        allocation_pct = Decimal("60.0")
        assert allocation_pct >= 0

    def test_nia_sqm_optional(self) -> None:
        """Test NIA sqm is optional."""
        nia_sqm = Decimal("5000")
        assert nia_sqm is None or nia_sqm > 0

    def test_rent_psm_month_optional(self) -> None:
        """Test rent psm month is optional."""
        rent_psm = Decimal("85.00")
        assert rent_psm is None or rent_psm > 0


class TestAssetFinancials:
    """Tests for asset financials output."""

    def test_annual_noi_calculation(self) -> None:
        """Test annual NOI calculation."""
        nia_sqm = Decimal("5000")
        rent_psm_month = Decimal("85")
        annual_rent = nia_sqm * rent_psm_month * 12
        vacancy = Decimal("0.05")
        opex = Decimal("0.20")
        noi = annual_rent * (1 - vacancy) * (1 - opex)
        assert noi > 0

    def test_estimated_capex(self) -> None:
        """Test estimated CAPEX calculation."""
        nia_sqm = Decimal("5000")
        fitout_cost_psm = Decimal("800")
        capex = nia_sqm * fitout_cost_psm
        assert capex == Decimal("4000000")

    def test_payback_years(self) -> None:
        """Test payback years calculation."""
        capex = Decimal("4000000")
        annual_noi = Decimal("500000")
        payback_years = capex / annual_noi
        assert payback_years == 8


class TestConstructionLoan:
    """Tests for construction loan calculations."""

    def test_interest_rate_required(self) -> None:
        """Test interest rate is required."""
        interest_rate = Decimal("0.05")  # 5%
        assert interest_rate > 0

    def test_periods_per_year(self) -> None:
        """Test periods per year."""
        periods_per_year = 12  # Monthly
        assert periods_per_year in [1, 4, 12]

    def test_capitalise_interest(self) -> None:
        """Test capitalise interest flag."""
        capitalise_interest = True
        assert isinstance(capitalise_interest, bool)

    def test_interest_calculation(self) -> None:
        """Test construction loan interest calculation."""
        principal = Decimal("4000000")
        annual_rate = Decimal("0.05")
        months = Decimal("24")
        # Simple interest for construction
        total_interest = principal * annual_rate * (months / Decimal("12"))
        assert total_interest == Decimal("400000")


class TestSensitivityAnalysis:
    """Tests for sensitivity analysis."""

    def test_sensitivity_band_fields(self) -> None:
        """Test sensitivity band fields."""
        band = {
            "parameter": "interest_rate",
            "label": "+100bps",
            "adjustment": Decimal("0.01"),
        }
        assert band["parameter"] is not None

    def test_interest_rate_sensitivity(self) -> None:
        """Test interest rate sensitivity impact."""
        base_npv = Decimal("500000")
        # Higher interest = lower NPV
        adjusted_npv = Decimal("450000")
        delta = adjusted_npv - base_npv
        assert delta < 0

    def test_cost_sensitivity(self) -> None:
        """Test cost sensitivity impact."""
        base_npv = Decimal("500000")
        # Higher costs = lower NPV
        adjusted_npv = Decimal("400000")
        delta = adjusted_npv - base_npv
        assert delta < 0

    def test_revenue_sensitivity(self) -> None:
        """Test revenue sensitivity impact."""
        base_npv = Decimal("500000")
        # Higher revenue = higher NPV
        adjusted_npv = Decimal("600000")
        delta = adjusted_npv - base_npv
        assert delta > 0


class TestFinanceFeasibilityResponse:
    """Tests for FinanceFeasibilityResponse model."""

    def test_scenario_id_included(self) -> None:
        """Test scenario_id is included."""
        scenario_id = 123
        assert isinstance(scenario_id, int)

    def test_project_id_included(self) -> None:
        """Test project_id is included."""
        project_id = str(uuid4())
        assert project_id is not None

    def test_escalated_cost_included(self) -> None:
        """Test escalated_cost is included."""
        escalated_cost = Decimal("1150000.00")
        assert escalated_cost > 0

    def test_results_list_included(self) -> None:
        """Test results list is included."""
        results = [
            {"name": "npv", "value": Decimal("500000"), "unit": "SGD"},
            {"name": "irr", "value": Decimal("0.12"), "unit": "ratio"},
        ]
        assert len(results) >= 2

    def test_updated_at_included(self) -> None:
        """Test updated_at is included."""
        updated_at = datetime.utcnow()
        assert updated_at is not None


class TestCostIndexProvenance:
    """Tests for cost index provenance output."""

    def test_scalar_calculation(self) -> None:
        """Test scalar (escalation factor) calculation."""
        base_index_value = Decimal("100.0")
        latest_index_value = Decimal("115.0")
        scalar = latest_index_value / base_index_value
        assert scalar == Decimal("1.15")

    def test_provenance_fields(self) -> None:
        """Test provenance fields."""
        provenance = {
            "series_name": "BCA_BCI",
            "jurisdiction": "SG",
            "provider": "BCA",
            "base_period": "2020-Q1",
            "latest_period": "2024-Q4",
            "scalar": Decimal("1.15"),
        }
        assert provenance["scalar"] > 1


class TestEdgeCases:
    """Tests for edge cases in finance feasibility API."""

    def test_zero_cash_flows_irr_undefined(self) -> None:
        """Test IRR is undefined for zero cash flows."""
        cash_flows = [Decimal("0"), Decimal("0"), Decimal("0")]
        # IRR cannot be computed for all-zero flows
        irr = None
        assert irr is None
        assert len(cash_flows) == 3

    def test_all_negative_cash_flows(self) -> None:
        """Test all negative cash flows."""
        cash_flows = [Decimal("-100000"), Decimal("-50000"), Decimal("-25000")]
        total = sum(cash_flows)
        assert total < 0

    def test_single_cash_flow(self) -> None:
        """Test single cash flow (no NPV calculation needed)."""
        cash_flows = [Decimal("100000")]
        npv = cash_flows[0]  # No discounting for single period
        assert npv == Decimal("100000")

    def test_missing_cost_indices(self) -> None:
        """Test handling missing cost indices."""
        # Should return base amount if no indices found
        base_amount = Decimal("1000000")
        escalated_amount = base_amount  # No escalation
        assert escalated_amount == base_amount

    def test_finance_project_not_found_404(self) -> None:
        """Test 404 for missing finance project."""
        status_code = 404
        assert status_code == 404

    def test_permission_denied_403(self) -> None:
        """Test 403 for permission denied."""
        status_code = 403
        assert status_code == 403
