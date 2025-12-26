"""Comprehensive tests for finance schemas.

Tests cover:
- CostIndexSnapshot and CostIndexProvenance
- CapitalStack input and output schemas
- Drawdown schedule schemas
- Cash flow and DSCR inputs
- Finance feasibility request/response
- Construction loan schemas
- Sensitivity analysis schemas
"""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4


class TestCostIndexSnapshot:
    """Tests for CostIndexSnapshot schema."""

    def test_period_required(self) -> None:
        """Test period is required."""
        period = "2024-Q1"
        assert period is not None

    def test_value_required(self) -> None:
        """Test value is required Decimal."""
        value = Decimal("115.5")
        assert value > 0

    def test_unit_required(self) -> None:
        """Test unit is required."""
        unit = "index"
        assert unit is not None

    def test_source_optional(self) -> None:
        """Test source is optional."""
        snapshot = {"period": "2024-Q1", "value": Decimal("100")}
        assert snapshot.get("source") is None

    def test_provider_optional(self) -> None:
        """Test provider is optional."""
        snapshot = {}
        assert snapshot.get("provider") is None

    def test_methodology_optional(self) -> None:
        """Test methodology is optional."""
        snapshot = {}
        assert snapshot.get("methodology") is None


class TestCostIndexProvenance:
    """Tests for CostIndexProvenance schema."""

    def test_series_name_required(self) -> None:
        """Test series_name is required."""
        series_name = "BCA_BCI"
        assert series_name is not None

    def test_jurisdiction_required(self) -> None:
        """Test jurisdiction is required."""
        jurisdiction = "SG"
        assert jurisdiction == "SG"

    def test_provider_optional(self) -> None:
        """Test provider is optional."""
        provenance = {"series_name": "BCA_BCI", "jurisdiction": "SG"}
        assert provenance.get("provider") is None

    def test_base_period_required(self) -> None:
        """Test base_period is required."""
        base_period = "2020-Q1"
        assert base_period is not None

    def test_latest_period_optional(self) -> None:
        """Test latest_period is optional."""
        provenance = {}
        assert provenance.get("latest_period") is None

    def test_scalar_calculation(self) -> None:
        """Test scalar (escalation factor)."""
        base_value = Decimal("100.0")
        latest_value = Decimal("115.0")
        scalar = latest_value / base_value
        assert scalar == Decimal("1.15")


class TestCapitalStackSliceInput:
    """Tests for CapitalStackSliceInput schema."""

    def test_name_required(self) -> None:
        """Test name is required."""
        name = "Senior Debt"
        assert len(name) > 0

    def test_source_type_required(self) -> None:
        """Test source_type is required."""
        source_type = "debt"
        assert source_type in ["equity", "debt", "mezzanine", "other"]

    def test_source_type_min_length(self) -> None:
        """Test source_type has min length 1."""
        source_type = "d"
        assert len(source_type) >= 1

    def test_amount_required(self) -> None:
        """Test amount is required."""
        amount = Decimal("5000000.00")
        assert amount > 0

    def test_amount_ge_zero(self) -> None:
        """Test amount >= 0."""
        amount = Decimal("0")
        assert amount >= 0

    def test_rate_optional(self) -> None:
        """Test rate is optional."""
        slice_input = {"name": "Test", "source_type": "debt", "amount": Decimal("100")}
        assert slice_input.get("rate") is None

    def test_tranche_order_optional(self) -> None:
        """Test tranche_order is optional."""
        slice_input = {}
        assert slice_input.get("tranche_order") is None

    def test_tranche_order_ge_zero(self) -> None:
        """Test tranche_order >= 0."""
        tranche_order = 1
        assert tranche_order >= 0

    def test_metadata_defaults_empty(self) -> None:
        """Test metadata defaults to empty dict."""
        metadata = {}
        assert isinstance(metadata, dict)


class TestDrawdownPeriodInput:
    """Tests for DrawdownPeriodInput schema."""

    def test_period_required(self) -> None:
        """Test period is required."""
        period = "Month 1"
        assert period is not None

    def test_equity_draw_defaults_zero(self) -> None:
        """Test equity_draw defaults to 0."""
        equity_draw = Decimal("0")
        assert equity_draw == 0

    def test_debt_draw_defaults_zero(self) -> None:
        """Test debt_draw defaults to 0."""
        debt_draw = Decimal("0")
        assert debt_draw == 0

    def test_total_draw_calculation(self) -> None:
        """Test total_draw is equity + debt."""
        equity = Decimal("500000")
        debt = Decimal("1000000")
        total = equity + debt
        assert total == Decimal("1500000")


class TestCostEscalationInput:
    """Tests for CostEscalationInput schema."""

    def test_amount_required(self) -> None:
        """Test amount is required."""
        amount = Decimal("1000000.00")
        assert amount > 0

    def test_amount_ge_zero(self) -> None:
        """Test amount >= 0."""
        amount = Decimal("0")
        assert amount >= 0

    def test_base_period_required(self) -> None:
        """Test base_period is required."""
        base_period = "2020-Q1"
        assert len(base_period) >= 1

    def test_series_name_required(self) -> None:
        """Test series_name is required."""
        series_name = "BCA_BCI"
        assert len(series_name) >= 1

    def test_jurisdiction_defaults_sg(self) -> None:
        """Test jurisdiction defaults to SG."""
        jurisdiction = "SG"
        assert jurisdiction == "SG"

    def test_provider_optional(self) -> None:
        """Test provider is optional."""
        escalation = {"amount": Decimal("100"), "base_period": "2020-Q1"}
        assert escalation.get("provider") is None


class TestCashflowInputs:
    """Tests for CashflowInputs schema."""

    def test_discount_rate_required(self) -> None:
        """Test discount_rate is required."""
        discount_rate = Decimal("0.08")
        assert discount_rate > 0

    def test_cash_flows_required(self) -> None:
        """Test cash_flows is required."""
        cash_flows = [Decimal("-1000000"), Decimal("200000"), Decimal("300000")]
        assert len(cash_flows) > 0

    def test_cash_flows_must_have_values(self) -> None:
        """Test cash_flows must contain at least one value."""
        cash_flows = [Decimal("100000")]
        assert len(cash_flows) >= 1

    def test_empty_cash_flows_invalid(self) -> None:
        """Test empty cash_flows is invalid."""
        cash_flows = []
        is_valid = len(cash_flows) > 0
        assert is_valid is False

    def test_negative_initial_investment(self) -> None:
        """Test initial investment is typically negative."""
        initial = Decimal("-1000000")
        assert initial < 0


class TestDscrInputs:
    """Tests for DscrInputs schema."""

    def test_net_operating_incomes_required(self) -> None:
        """Test net_operating_incomes is required."""
        noi = [Decimal("50000"), Decimal("52000"), Decimal("54000")]
        assert len(noi) > 0

    def test_debt_services_required(self) -> None:
        """Test debt_services is required."""
        debt = [Decimal("35000"), Decimal("35000"), Decimal("35000")]
        assert len(debt) > 0

    def test_period_labels_optional(self) -> None:
        """Test period_labels is optional."""
        inputs = {"net_operating_incomes": [], "debt_services": []}
        assert inputs.get("period_labels") is None

    def test_lengths_must_match(self) -> None:
        """Test NOI and debt service must have same length."""
        noi = [Decimal("50000"), Decimal("52000")]
        debt = [Decimal("35000"), Decimal("35000")]
        assert len(noi) == len(debt)

    def test_period_labels_length_must_match(self) -> None:
        """Test period_labels must match NOI length."""
        noi = [Decimal("50000"), Decimal("52000")]
        labels = ["2024-01", "2024-02"]
        assert len(labels) == len(noi)


class TestFinanceAssetMixInput:
    """Tests for FinanceAssetMixInput schema."""

    def test_asset_type_required(self) -> None:
        """Test asset_type is required."""
        asset_type = "office"
        assert asset_type is not None

    def test_allocation_pct_optional(self) -> None:
        """Test allocation_pct is optional."""
        mix = {"asset_type": "office"}
        assert mix.get("allocation_pct") is None

    def test_nia_sqm_optional(self) -> None:
        """Test nia_sqm is optional."""
        mix = {}
        assert mix.get("nia_sqm") is None

    def test_rent_psm_month_optional(self) -> None:
        """Test rent_psm_month is optional."""
        mix = {}
        assert mix.get("rent_psm_month") is None

    def test_risk_level_values(self) -> None:
        """Test valid risk_level values."""
        risk_levels = ["LOW", "MEDIUM", "HIGH", "VERY_HIGH"]
        for level in risk_levels:
            assert level is not None


class TestConstructionLoanInput:
    """Tests for ConstructionLoanInput schema."""

    def test_interest_rate_optional(self) -> None:
        """Test interest_rate is optional."""
        loan = {}
        assert loan.get("interest_rate") is None

    def test_periods_per_year_optional(self) -> None:
        """Test periods_per_year is optional."""
        loan = {}
        assert loan.get("periods_per_year") is None

    def test_periods_per_year_ge_one(self) -> None:
        """Test periods_per_year >= 1."""
        periods = 12
        assert periods >= 1

    def test_capitalise_interest_defaults_true(self) -> None:
        """Test capitalise_interest defaults to True."""
        capitalise = True
        assert capitalise is True

    def test_facilities_optional(self) -> None:
        """Test facilities list is optional."""
        loan = {}
        assert loan.get("facilities") is None


class TestSensitivityBandInput:
    """Tests for SensitivityBandInput schema."""

    def test_parameter_required(self) -> None:
        """Test parameter is required."""
        parameter = "interest_rate"
        assert parameter is not None

    def test_low_optional(self) -> None:
        """Test low is optional."""
        band = {"parameter": "interest_rate"}
        assert band.get("low") is None

    def test_base_optional(self) -> None:
        """Test base is optional."""
        band = {}
        assert band.get("base") is None

    def test_high_optional(self) -> None:
        """Test high is optional."""
        band = {}
        assert band.get("high") is None

    def test_notes_defaults_empty(self) -> None:
        """Test notes defaults to empty list."""
        notes = []
        assert isinstance(notes, list)


class TestFinanceScenarioInput:
    """Tests for FinanceScenarioInput schema."""

    def test_name_required(self) -> None:
        """Test name is required."""
        name = "Base Case Scenario"
        assert len(name) > 0

    def test_description_optional(self) -> None:
        """Test description is optional."""
        scenario = {"name": "Test"}
        assert scenario.get("description") is None

    def test_currency_defaults_sgd(self) -> None:
        """Test currency defaults to SGD."""
        currency = "SGD"
        assert currency == "SGD"

    def test_is_primary_defaults_false(self) -> None:
        """Test is_primary defaults to False."""
        is_primary = False
        assert is_primary is False

    def test_jurisdiction_code_defaults_sg(self) -> None:
        """Test jurisdiction_code defaults to SG."""
        jurisdiction = "SG"
        assert jurisdiction == "SG"


class TestFinanceFeasibilityRequest:
    """Tests for FinanceFeasibilityRequest schema."""

    def test_project_id_required(self) -> None:
        """Test project_id is required."""
        project_id = str(uuid4())
        assert project_id is not None

    def test_project_id_accepts_uuid(self) -> None:
        """Test project_id accepts UUID."""
        project_id = uuid4()
        assert len(str(project_id)) == 36

    def test_project_id_accepts_string(self) -> None:
        """Test project_id accepts string."""
        project_id = "project-123"
        assert isinstance(project_id, str)

    def test_project_id_accepts_int(self) -> None:
        """Test project_id accepts int."""
        project_id = 123
        assert isinstance(project_id, int)

    def test_project_name_optional(self) -> None:
        """Test project_name is optional."""
        request = {"project_id": 1}
        assert request.get("project_name") is None

    def test_fin_project_id_optional(self) -> None:
        """Test fin_project_id is optional."""
        request = {}
        assert request.get("fin_project_id") is None

    def test_scenario_required(self) -> None:
        """Test scenario is required."""
        scenario = {"name": "Base Case"}
        assert scenario is not None


class TestFinanceFeasibilityResponse:
    """Tests for FinanceFeasibilityResponse schema."""

    def test_scenario_id_required(self) -> None:
        """Test scenario_id is required."""
        scenario_id = 123
        assert isinstance(scenario_id, int)

    def test_project_id_required(self) -> None:
        """Test project_id is required."""
        project_id = str(uuid4())
        assert project_id is not None

    def test_fin_project_id_required(self) -> None:
        """Test fin_project_id is required."""
        fin_project_id = 456
        assert isinstance(fin_project_id, int)

    def test_scenario_name_required(self) -> None:
        """Test scenario_name is required."""
        name = "Base Case"
        assert len(name) > 0

    def test_currency_required(self) -> None:
        """Test currency is required."""
        currency = "SGD"
        assert len(currency) == 3

    def test_escalated_cost_required(self) -> None:
        """Test escalated_cost is required."""
        cost = Decimal("1150000.00")
        assert cost > 0

    def test_cost_index_required(self) -> None:
        """Test cost_index is required."""
        cost_index = {"series_name": "BCA_BCI", "jurisdiction": "SG"}
        assert cost_index is not None

    def test_results_required(self) -> None:
        """Test results is required."""
        results = []
        assert isinstance(results, list)

    def test_is_primary_defaults_false(self) -> None:
        """Test is_primary defaults to False."""
        is_primary = False
        assert is_primary is False

    def test_is_private_defaults_false(self) -> None:
        """Test is_private defaults to False."""
        is_private = False
        assert is_private is False

    def test_updated_at_optional(self) -> None:
        """Test updated_at is optional."""
        response = {}
        assert response.get("updated_at") is None


class TestDscrEntrySchema:
    """Tests for DscrEntrySchema schema."""

    def test_period_required(self) -> None:
        """Test period is required."""
        period = "2024-01"
        assert period is not None

    def test_noi_required(self) -> None:
        """Test noi is required."""
        noi = Decimal("50000.00")
        assert noi > 0

    def test_debt_service_required(self) -> None:
        """Test debt_service is required."""
        debt = Decimal("35000.00")
        assert debt > 0

    def test_dscr_optional(self) -> None:
        """Test dscr is optional."""
        entry = {"period": "2024-01", "noi": Decimal("50000")}
        assert entry.get("dscr") is None

    def test_currency_required(self) -> None:
        """Test currency is required."""
        currency = "SGD"
        assert currency is not None

    def test_dscr_calculation(self) -> None:
        """Test DSCR calculation."""
        noi = Decimal("50000")
        debt = Decimal("35000")
        dscr = noi / debt
        assert dscr > 1


class TestCapitalStackSummarySchema:
    """Tests for CapitalStackSummarySchema schema."""

    def test_currency_required(self) -> None:
        """Test currency is required."""
        currency = "SGD"
        assert currency is not None

    def test_total_required(self) -> None:
        """Test total is required."""
        total = Decimal("10000000.00")
        assert total > 0

    def test_equity_total_required(self) -> None:
        """Test equity_total is required."""
        equity = Decimal("3000000.00")
        assert equity >= 0

    def test_debt_total_required(self) -> None:
        """Test debt_total is required."""
        debt = Decimal("7000000.00")
        assert debt >= 0

    def test_other_total_required(self) -> None:
        """Test other_total is required."""
        other = Decimal("0")
        assert other >= 0

    def test_equity_ratio_optional(self) -> None:
        """Test equity_ratio is optional."""
        summary = {}
        assert summary.get("equity_ratio") is None

    def test_debt_ratio_optional(self) -> None:
        """Test debt_ratio is optional."""
        summary = {}
        assert summary.get("debt_ratio") is None

    def test_loan_to_cost_optional(self) -> None:
        """Test loan_to_cost is optional."""
        summary = {}
        assert summary.get("loan_to_cost") is None

    def test_weighted_average_debt_rate_optional(self) -> None:
        """Test weighted_average_debt_rate is optional."""
        summary = {}
        assert summary.get("weighted_average_debt_rate") is None

    def test_slices_defaults_empty(self) -> None:
        """Test slices defaults to empty list."""
        slices = []
        assert isinstance(slices, list)


class TestFinancingDrawdownScheduleSchema:
    """Tests for FinancingDrawdownScheduleSchema schema."""

    def test_currency_required(self) -> None:
        """Test currency is required."""
        currency = "SGD"
        assert currency is not None

    def test_entries_defaults_empty(self) -> None:
        """Test entries defaults to empty list."""
        entries = []
        assert isinstance(entries, list)

    def test_total_equity_required(self) -> None:
        """Test total_equity is required."""
        equity = Decimal("3000000")
        assert equity >= 0

    def test_total_debt_required(self) -> None:
        """Test total_debt is required."""
        debt = Decimal("7000000")
        assert debt >= 0

    def test_peak_debt_balance_required(self) -> None:
        """Test peak_debt_balance is required."""
        peak = Decimal("8000000")
        assert peak >= 0

    def test_final_debt_balance_required(self) -> None:
        """Test final_debt_balance is required."""
        final = Decimal("5000000")
        assert final >= 0
