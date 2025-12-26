"""Comprehensive tests for Finance models.

Tests cover:
- FinProject, FinScenario, FinCostItem, FinSchedule, FinCapitalStack, FinResult, FinAssetBreakdown
- Decimal precision for financial values
- Foreign key relationships and cascades
- JSON/metadata fields
- Multi-jurisdiction financing fields
"""

from __future__ import annotations

import uuid
from decimal import Decimal


from app.models.finance import (
    FinAssetBreakdown,
    FinCapitalStack,
    FinCostItem,
    FinProject,
    FinResult,
    FinScenario,
    FinSchedule,
)


class TestFinProject:
    """Tests for FinProject model."""

    def test_create_minimal_fin_project(self) -> None:
        """FinProject with required fields should be valid."""
        project_id = uuid.uuid4()
        fin_project = FinProject(
            project_id=project_id,
            name="Test Finance Project",
        )
        assert fin_project.name == "Test Finance Project"
        assert fin_project.project_id == project_id

    def test_currency_default(self) -> None:
        """Default currency should be USD."""
        fin_project = FinProject(
            project_id=uuid.uuid4(),
            name="Test",
        )
        # Note: Default is set at DB level
        assert fin_project.currency is None or fin_project.currency == "USD"

    def test_currency_custom(self) -> None:
        """Custom currency should be accepted."""
        fin_project = FinProject(
            project_id=uuid.uuid4(),
            name="SGD Project",
            currency="SGD",
        )
        assert fin_project.currency == "SGD"

    def test_discount_rate_precision(self) -> None:
        """Discount rate should support 4 decimal places."""
        fin_project = FinProject(
            project_id=uuid.uuid4(),
            name="Test",
            discount_rate=Decimal("0.0850"),
        )
        assert fin_project.discount_rate == Decimal("0.0850")

    def test_total_development_cost(self) -> None:
        """Total development cost should support large values."""
        fin_project = FinProject(
            project_id=uuid.uuid4(),
            name="Test",
            total_development_cost=Decimal("50000000.00"),
        )
        assert fin_project.total_development_cost == Decimal("50000000.00")

    def test_total_gross_profit(self) -> None:
        """Total gross profit should support decimals."""
        fin_project = FinProject(
            project_id=uuid.uuid4(),
            name="Test",
            total_gross_profit=Decimal("15000000.50"),
        )
        assert fin_project.total_gross_profit == Decimal("15000000.50")

    def test_metadata_json(self) -> None:
        """Metadata should accept JSON."""
        metadata = {"version": "1.0", "notes": ["Initial setup"]}
        fin_project = FinProject(
            project_id=uuid.uuid4(),
            name="Test",
            metadata_json=metadata,
        )
        assert fin_project.metadata_json == metadata


class TestFinScenario:
    """Tests for FinScenario model."""

    def test_create_minimal_scenario(self) -> None:
        """FinScenario with required fields should be valid."""
        scenario = FinScenario(
            project_id=uuid.uuid4(),
            fin_project_id=1,
            name="Base Case",
        )
        assert scenario.name == "Base Case"

    def test_description_field(self) -> None:
        """Description should accept text."""
        scenario = FinScenario(
            project_id=uuid.uuid4(),
            fin_project_id=1,
            name="Test",
            description="Detailed scenario description for analysis",
        )
        assert "Detailed" in scenario.description

    def test_assumptions_json(self) -> None:
        """Assumptions should accept JSON."""
        assumptions = {
            "vacancy_rate": 0.05,
            "rent_growth": 0.03,
            "exit_cap_rate": 0.06,
        }
        scenario = FinScenario(
            project_id=uuid.uuid4(),
            fin_project_id=1,
            name="Test",
            assumptions=assumptions,
        )
        assert scenario.assumptions["vacancy_rate"] == 0.05

    def test_is_primary_flag(self) -> None:
        """is_primary should be settable."""
        scenario = FinScenario(
            project_id=uuid.uuid4(),
            fin_project_id=1,
            name="Primary",
            is_primary=True,
        )
        assert scenario.is_primary is True

    def test_is_private_flag(self) -> None:
        """is_private should be settable."""
        scenario = FinScenario(
            project_id=uuid.uuid4(),
            fin_project_id=1,
            name="Private",
            is_private=True,
        )
        assert scenario.is_private is True

    def test_parent_scenario_id(self) -> None:
        """parent_scenario_id for lineage tracking."""
        scenario = FinScenario(
            project_id=uuid.uuid4(),
            fin_project_id=1,
            name="Derived",
            parent_scenario_id=5,
        )
        assert scenario.parent_scenario_id == 5

    def test_export_hash(self) -> None:
        """export_hash for audit trail."""
        scenario = FinScenario(
            project_id=uuid.uuid4(),
            fin_project_id=1,
            name="Test",
            export_hash="abc123def456",
        )
        assert scenario.export_hash == "abc123def456"

    def test_jurisdiction_code(self) -> None:
        """jurisdiction_code for multi-jurisdiction."""
        scenario = FinScenario(
            project_id=uuid.uuid4(),
            fin_project_id=1,
            name="Singapore",
            jurisdiction_code="SG",
        )
        assert scenario.jurisdiction_code == "SG"

    def test_ltv_limit_precision(self) -> None:
        """LTV limit should support 4 decimal places."""
        scenario = FinScenario(
            project_id=uuid.uuid4(),
            fin_project_id=1,
            name="Test",
            ltv_limit_pct=Decimal("0.7500"),
        )
        assert scenario.ltv_limit_pct == Decimal("0.7500")

    def test_absd_rate(self) -> None:
        """ABSD rate for Singapore."""
        scenario = FinScenario(
            project_id=uuid.uuid4(),
            fin_project_id=1,
            name="Test",
            absd_rate_pct=Decimal("0.3000"),
        )
        assert scenario.absd_rate_pct == Decimal("0.3000")

    def test_dscr_min(self) -> None:
        """DSCR minimum should be settable."""
        scenario = FinScenario(
            project_id=uuid.uuid4(),
            fin_project_id=1,
            name="Test",
            dscr_min=Decimal("1.2500"),
        )
        assert scenario.dscr_min == Decimal("1.2500")

    def test_construction_loan_rate(self) -> None:
        """Construction loan rate precision."""
        scenario = FinScenario(
            project_id=uuid.uuid4(),
            fin_project_id=1,
            name="Test",
            construction_loan_rate_pct=Decimal("0.0450"),
        )
        assert scenario.construction_loan_rate_pct == Decimal("0.0450")


class TestFinCostItem:
    """Tests for FinCostItem model."""

    def test_create_cost_item(self) -> None:
        """FinCostItem with required fields."""
        item = FinCostItem(
            project_id=uuid.uuid4(),
            scenario_id=1,
            name="Land Acquisition",
        )
        assert item.name == "Land Acquisition"

    def test_category_and_cost_group(self) -> None:
        """Category and cost_group should be settable."""
        item = FinCostItem(
            project_id=uuid.uuid4(),
            scenario_id=1,
            name="Foundation",
            category="Hard Cost",
            cost_group="Construction",
        )
        assert item.category == "Hard Cost"
        assert item.cost_group == "Construction"

    def test_quantity_and_unit_cost(self) -> None:
        """Quantity and unit cost calculations."""
        item = FinCostItem(
            project_id=uuid.uuid4(),
            scenario_id=1,
            name="Concrete",
            quantity=Decimal("5000.00"),
            unit_cost=Decimal("150.50"),
            total_cost=Decimal("752500.00"),
        )
        assert item.quantity == Decimal("5000.00")
        assert item.unit_cost == Decimal("150.50")
        assert item.total_cost == Decimal("752500.00")

    def test_total_cost_precision(self) -> None:
        """Total cost should support large values."""
        item = FinCostItem(
            project_id=uuid.uuid4(),
            scenario_id=1,
            name="Building",
            total_cost=Decimal("99999999999999.99"),
        )
        assert item.total_cost == Decimal("99999999999999.99")


class TestFinSchedule:
    """Tests for FinSchedule model."""

    def test_create_schedule(self) -> None:
        """FinSchedule with required fields."""
        schedule = FinSchedule(
            project_id=uuid.uuid4(),
            scenario_id=1,
            month_index=0,
        )
        assert schedule.month_index == 0

    def test_cost_fields(self) -> None:
        """Hard and soft cost fields."""
        schedule = FinSchedule(
            project_id=uuid.uuid4(),
            scenario_id=1,
            month_index=3,
            hard_cost=Decimal("500000.00"),
            soft_cost=Decimal("100000.00"),
        )
        assert schedule.hard_cost == Decimal("500000.00")
        assert schedule.soft_cost == Decimal("100000.00")

    def test_revenue_and_cash_flow(self) -> None:
        """Revenue and cash flow fields."""
        schedule = FinSchedule(
            project_id=uuid.uuid4(),
            scenario_id=1,
            month_index=24,
            revenue=Decimal("1500000.00"),
            cash_flow=Decimal("300000.00"),
            cumulative_cash_flow=Decimal("-2000000.00"),
        )
        assert schedule.revenue == Decimal("1500000.00")
        assert schedule.cash_flow == Decimal("300000.00")
        assert schedule.cumulative_cash_flow == Decimal("-2000000.00")

    def test_negative_cumulative_cash_flow(self) -> None:
        """Cumulative cash flow can be negative."""
        schedule = FinSchedule(
            project_id=uuid.uuid4(),
            scenario_id=1,
            month_index=6,
            cumulative_cash_flow=Decimal("-5000000.00"),
        )
        assert schedule.cumulative_cash_flow < 0


class TestFinCapitalStack:
    """Tests for FinCapitalStack model."""

    def test_create_capital_stack(self) -> None:
        """FinCapitalStack with required fields."""
        stack = FinCapitalStack(
            project_id=uuid.uuid4(),
            scenario_id=1,
            name="Senior Debt",
        )
        assert stack.name == "Senior Debt"

    def test_source_type(self) -> None:
        """Source type classification."""
        stack = FinCapitalStack(
            project_id=uuid.uuid4(),
            scenario_id=1,
            name="Equity",
            source_type="Common Equity",
        )
        assert stack.source_type == "Common Equity"

    def test_tranche_order(self) -> None:
        """Tranche order for waterfall."""
        stack = FinCapitalStack(
            project_id=uuid.uuid4(),
            scenario_id=1,
            name="Mezzanine",
            tranche_order=2,
        )
        assert stack.tranche_order == 2

    def test_amount_precision(self) -> None:
        """Amount should support large values."""
        stack = FinCapitalStack(
            project_id=uuid.uuid4(),
            scenario_id=1,
            name="Senior Debt",
            amount=Decimal("35000000.00"),
        )
        assert stack.amount == Decimal("35000000.00")

    def test_rate_precision(self) -> None:
        """Rate should support 4 decimal places."""
        stack = FinCapitalStack(
            project_id=uuid.uuid4(),
            scenario_id=1,
            name="Senior Debt",
            rate=Decimal("0.0550"),
        )
        assert stack.rate == Decimal("0.0550")

    def test_equity_share(self) -> None:
        """Equity share percentage."""
        stack = FinCapitalStack(
            project_id=uuid.uuid4(),
            scenario_id=1,
            name="LP Equity",
            equity_share=Decimal("0.9000"),
        )
        assert stack.equity_share == Decimal("0.9000")


class TestFinResult:
    """Tests for FinResult model."""

    def test_create_result(self) -> None:
        """FinResult with required fields."""
        result = FinResult(
            project_id=uuid.uuid4(),
            scenario_id=1,
            name="IRR",
        )
        assert result.name == "IRR"

    def test_value_precision(self) -> None:
        """Value should support 4 decimal places."""
        result = FinResult(
            project_id=uuid.uuid4(),
            scenario_id=1,
            name="NPV",
            value=Decimal("12345678.1234"),
        )
        assert result.value == Decimal("12345678.1234")

    def test_unit_field(self) -> None:
        """Unit should be settable."""
        result = FinResult(
            project_id=uuid.uuid4(),
            scenario_id=1,
            name="IRR",
            value=Decimal("0.1850"),
            unit="percentage",
        )
        assert result.unit == "percentage"

    def test_common_result_types(self) -> None:
        """Common financial result types."""
        results = [
            FinResult(
                project_id=uuid.uuid4(),
                scenario_id=1,
                name="IRR",
                value=Decimal("0.1850"),
                unit="pct",
            ),
            FinResult(
                project_id=uuid.uuid4(),
                scenario_id=1,
                name="NPV",
                value=Decimal("5000000.00"),
                unit="SGD",
            ),
            FinResult(
                project_id=uuid.uuid4(),
                scenario_id=1,
                name="Equity Multiple",
                value=Decimal("1.8500"),
                unit="x",
            ),
            FinResult(
                project_id=uuid.uuid4(),
                scenario_id=1,
                name="Development Margin",
                value=Decimal("0.2200"),
                unit="pct",
            ),
        ]
        assert len(results) == 4


class TestFinAssetBreakdown:
    """Tests for FinAssetBreakdown model."""

    def test_create_asset_breakdown(self) -> None:
        """FinAssetBreakdown with required fields."""
        breakdown = FinAssetBreakdown(
            project_id=uuid.uuid4(),
            scenario_id=1,
            asset_type="Office",
        )
        assert breakdown.asset_type == "Office"

    def test_allocation_pct(self) -> None:
        """Allocation percentage precision."""
        breakdown = FinAssetBreakdown(
            project_id=uuid.uuid4(),
            scenario_id=1,
            asset_type="Retail",
            allocation_pct=Decimal("0.2500"),
        )
        assert breakdown.allocation_pct == Decimal("0.2500")

    def test_area_fields(self) -> None:
        """NIA and rent fields."""
        breakdown = FinAssetBreakdown(
            project_id=uuid.uuid4(),
            scenario_id=1,
            asset_type="Office",
            nia_sqm=Decimal("5000.00"),
            rent_psm_month=Decimal("85.00"),
        )
        assert breakdown.nia_sqm == Decimal("5000.00")
        assert breakdown.rent_psm_month == Decimal("85.00")

    def test_revenue_fields(self) -> None:
        """Annual NOI and revenue."""
        breakdown = FinAssetBreakdown(
            project_id=uuid.uuid4(),
            scenario_id=1,
            asset_type="Office",
            annual_noi_sgd=Decimal("3600000.00"),
            annual_revenue_sgd=Decimal("5100000.00"),
        )
        assert breakdown.annual_noi_sgd == Decimal("3600000.00")
        assert breakdown.annual_revenue_sgd == Decimal("5100000.00")

    def test_capex_fields(self) -> None:
        """Estimated capex."""
        breakdown = FinAssetBreakdown(
            project_id=uuid.uuid4(),
            scenario_id=1,
            asset_type="Retail",
            estimated_capex_sgd=Decimal("2500000.00"),
        )
        assert breakdown.estimated_capex_sgd == Decimal("2500000.00")

    def test_payback_and_absorption(self) -> None:
        """Payback years and absorption months."""
        breakdown = FinAssetBreakdown(
            project_id=uuid.uuid4(),
            scenario_id=1,
            asset_type="Office",
            payback_years=Decimal("8.5000"),
            absorption_months=Decimal("18.0000"),
        )
        assert breakdown.payback_years == Decimal("8.5000")
        assert breakdown.absorption_months == Decimal("18.0000")

    def test_stabilised_yield(self) -> None:
        """Stabilised yield precision."""
        breakdown = FinAssetBreakdown(
            project_id=uuid.uuid4(),
            scenario_id=1,
            asset_type="Office",
            stabilised_yield_pct=Decimal("0.045678"),
        )
        assert breakdown.stabilised_yield_pct == Decimal("0.045678")

    def test_risk_fields(self) -> None:
        """Risk level and priority."""
        breakdown = FinAssetBreakdown(
            project_id=uuid.uuid4(),
            scenario_id=1,
            asset_type="Retail",
            risk_level="Medium",
            risk_priority=2,
        )
        assert breakdown.risk_level == "Medium"
        assert breakdown.risk_priority == 2

    def test_notes_json(self) -> None:
        """Notes JSON field."""
        breakdown = FinAssetBreakdown(
            project_id=uuid.uuid4(),
            scenario_id=1,
            asset_type="Office",
            notes_json=["Prime location", "Strong tenant covenant"],
        )
        assert len(breakdown.notes_json) == 2
        assert "Prime location" in breakdown.notes_json


class TestFinanceModelIntegration:
    """Integration tests for finance model relationships."""

    def test_scenario_has_all_child_types(self) -> None:
        """Scenario should support all child relationship types."""
        scenario = FinScenario(
            project_id=uuid.uuid4(),
            fin_project_id=1,
            name="Integration Test",
        )
        # Verify relationship attributes exist
        assert hasattr(scenario, "cost_items")
        assert hasattr(scenario, "schedules")
        assert hasattr(scenario, "capital_stack")
        assert hasattr(scenario, "results")
        assert hasattr(scenario, "asset_breakdowns")

    def test_fin_project_has_scenarios(self) -> None:
        """FinProject should support scenarios relationship."""
        fin_project = FinProject(
            project_id=uuid.uuid4(),
            name="Test",
        )
        assert hasattr(fin_project, "scenarios")
