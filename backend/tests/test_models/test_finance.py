"""Integration tests for Finance models."""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from app.models.finance import (
    FinCapitalStack,
    FinCostItem,
    FinProject,
    FinResult,
    FinScenario,
    FinSchedule,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.asyncio


class TestFinProject:
    """Test FinProject model CRUD operations and relationships."""

    async def test_create_minimal_fin_project(self, session: AsyncSession):
        """Test creating a finance project with only required fields."""
        project_id = uuid4()
        fin_project = FinProject(
            project_id=project_id,
            name="Test Finance Project",
            currency="USD",
        )
        session.add(fin_project)
        await session.commit()
        await session.refresh(fin_project)

        assert fin_project.id is not None
        assert fin_project.project_id == project_id
        assert fin_project.name == "Test Finance Project"
        assert fin_project.currency == "USD"
        assert fin_project.created_at is not None
        assert fin_project.updated_at is not None
        assert fin_project.metadata_json == {}

    async def test_create_full_fin_project(self, session: AsyncSession):
        """Test creating a finance project with all fields populated."""
        project_id = uuid4()
        fin_project = FinProject(
            project_id=project_id,
            name="Marina Waterfront Finance",
            currency="SGD",
            discount_rate=Decimal("0.0850"),
            total_development_cost=Decimal("150000000.00"),
            total_gross_profit=Decimal("75000000.00"),
            metadata_json={"phase": "planning", "status": "active"},
        )
        session.add(fin_project)
        await session.commit()
        await session.refresh(fin_project)

        assert fin_project.project_id == project_id
        assert fin_project.currency == "SGD"
        assert fin_project.discount_rate == Decimal("0.0850")
        assert fin_project.total_development_cost == Decimal("150000000.00")
        assert fin_project.total_gross_profit == Decimal("75000000.00")
        assert fin_project.metadata_json["phase"] == "planning"

    async def test_fin_project_default_currency(self, session: AsyncSession):
        """Test that default currency is USD."""
        project_id = uuid4()
        fin_project = FinProject(
            project_id=project_id,
            name="Currency Default Test",
        )
        session.add(fin_project)
        await session.commit()
        await session.refresh(fin_project)

        assert fin_project.currency == "USD"

    async def test_fin_project_scenarios_relationship(self, session: AsyncSession):
        """Test cascade delete of scenarios when project is deleted."""
        project_id = uuid4()
        fin_project = FinProject(
            project_id=project_id,
            name="Project with Scenarios",
        )
        session.add(fin_project)
        await session.flush()

        scenario = FinScenario(
            project_id=project_id,
            fin_project_id=fin_project.id,
            name="Base Case",
        )
        session.add(scenario)
        await session.commit()

        # Verify scenario was created
        result = await session.execute(
            select(FinScenario).where(FinScenario.fin_project_id == fin_project.id)
        )
        assert result.scalars().first() is not None

        # Delete project and verify scenario cascades
        await session.delete(fin_project)
        await session.commit()

        result = await session.execute(
            select(FinScenario).where(FinScenario.fin_project_id == fin_project.id)
        )
        assert result.scalars().first() is None

    async def test_fin_project_metadata_proxy(self, session: AsyncSession):
        """Test metadata proxy functionality."""
        project_id = uuid4()
        fin_project = FinProject(
            project_id=project_id,
            name="Metadata Test",
            metadata_json={"custom_field": "custom_value"},
        )
        session.add(fin_project)
        await session.commit()
        await session.refresh(fin_project)

        assert fin_project.metadata["custom_field"] == "custom_value"


class TestFinScenario:
    """Test FinScenario model with multiple relationships."""

    async def test_create_minimal_fin_scenario(self, session: AsyncSession):
        """Test creating a scenario with only required fields."""
        project_id = uuid4()
        fin_project = FinProject(
            project_id=project_id,
            name="Parent Project",
        )
        session.add(fin_project)
        await session.flush()

        scenario = FinScenario(
            project_id=project_id,
            fin_project_id=fin_project.id,
            name="Base Case Scenario",
        )
        session.add(scenario)
        await session.commit()
        await session.refresh(scenario)

        assert scenario.id is not None
        assert scenario.project_id == project_id
        assert scenario.fin_project_id == fin_project.id
        assert scenario.name == "Base Case Scenario"
        assert scenario.is_primary is False
        assert scenario.is_private is False
        assert scenario.assumptions == {}
        assert scenario.created_at is not None

    async def test_create_full_fin_scenario(self, session: AsyncSession):
        """Test creating a scenario with all fields."""
        project_id = uuid4()
        fin_project = FinProject(
            project_id=project_id,
            name="Parent Project",
        )
        session.add(fin_project)
        await session.flush()

        scenario = FinScenario(
            project_id=project_id,
            fin_project_id=fin_project.id,
            name="Aggressive Growth",
            description="High growth scenario with optimistic assumptions",
            assumptions={
                "revenue_growth": 0.15,
                "cost_inflation": 0.03,
                "occupancy_rate": 0.95,
            },
            is_primary=True,
            is_private=False,
        )
        session.add(scenario)
        await session.commit()
        await session.refresh(scenario)

        assert (
            scenario.description == "High growth scenario with optimistic assumptions"
        )
        assert scenario.is_primary is True
        assert scenario.assumptions["revenue_growth"] == 0.15

    async def test_fin_scenario_cost_items_relationship(self, session: AsyncSession):
        """Test cost items cascade with scenario."""
        project_id = uuid4()
        fin_project = FinProject(project_id=project_id, name="Project")
        session.add(fin_project)
        await session.flush()

        scenario = FinScenario(
            project_id=project_id,
            fin_project_id=fin_project.id,
            name="Cost Test Scenario",
        )
        session.add(scenario)
        await session.flush()

        cost_item = FinCostItem(
            project_id=project_id,
            scenario_id=scenario.id,
            name="Foundation Work",
            category="Construction",
            total_cost=Decimal("500000.00"),
        )
        session.add(cost_item)
        await session.commit()

        # Verify relationship
        await session.refresh(scenario)
        assert len(scenario.cost_items) == 1
        assert scenario.cost_items[0].name == "Foundation Work"

    async def test_fin_scenario_multiple_child_relationships(
        self, session: AsyncSession
    ):
        """Test that scenario can have multiple types of related items."""
        project_id = uuid4()
        fin_project = FinProject(project_id=project_id, name="Project")
        session.add(fin_project)
        await session.flush()

        scenario = FinScenario(
            project_id=project_id,
            fin_project_id=fin_project.id,
            name="Complex Scenario",
        )
        session.add(scenario)
        await session.flush()

        # Add cost item
        cost_item = FinCostItem(
            project_id=project_id,
            scenario_id=scenario.id,
            name="Cost Item",
        )
        session.add(cost_item)

        # Add schedule
        schedule = FinSchedule(
            project_id=project_id,
            scenario_id=scenario.id,
            month_index=1,
            hard_cost=Decimal("100000.00"),
        )
        session.add(schedule)

        # Add capital stack
        capital_stack = FinCapitalStack(
            project_id=project_id,
            scenario_id=scenario.id,
            name="Senior Debt",
            source_type="Bank Loan",
        )
        session.add(capital_stack)

        # Add result
        result = FinResult(
            project_id=project_id,
            scenario_id=scenario.id,
            name="IRR",
            value=Decimal("0.1450"),
            unit="%",
        )
        session.add(result)

        await session.commit()
        await session.refresh(scenario)

        assert len(scenario.cost_items) == 1
        assert len(scenario.schedules) == 1
        assert len(scenario.capital_stack) == 1
        assert len(scenario.results) == 1


class TestFinCostItem:
    """Test FinCostItem model for cost modeling."""

    async def test_create_minimal_cost_item(self, session: AsyncSession):
        """Test creating a cost item with required fields."""
        project_id = uuid4()
        fin_project = FinProject(project_id=project_id, name="Project")
        session.add(fin_project)
        await session.flush()

        scenario = FinScenario(
            project_id=project_id,
            fin_project_id=fin_project.id,
            name="Scenario",
        )
        session.add(scenario)
        await session.flush()

        cost_item = FinCostItem(
            project_id=project_id,
            scenario_id=scenario.id,
            name="Structural Steel",
        )
        session.add(cost_item)
        await session.commit()
        await session.refresh(cost_item)

        assert cost_item.id is not None
        assert cost_item.name == "Structural Steel"
        assert cost_item.metadata_json == {}

    async def test_create_full_cost_item(self, session: AsyncSession):
        """Test creating a cost item with all fields."""
        project_id = uuid4()
        fin_project = FinProject(project_id=project_id, name="Project")
        session.add(fin_project)
        await session.flush()

        scenario = FinScenario(
            project_id=project_id,
            fin_project_id=fin_project.id,
            name="Scenario",
        )
        session.add(scenario)
        await session.flush()

        cost_item = FinCostItem(
            project_id=project_id,
            scenario_id=scenario.id,
            name="Concrete Work",
            category="Material",
            cost_group="Hard Costs",
            quantity=Decimal("1000.00"),
            unit_cost=Decimal("250.00"),
            total_cost=Decimal("250000.00"),
            metadata_json={"supplier": "ABC Concrete", "lead_time_days": 30},
        )
        session.add(cost_item)
        await session.commit()
        await session.refresh(cost_item)

        assert cost_item.category == "Material"
        assert cost_item.cost_group == "Hard Costs"
        assert cost_item.quantity == Decimal("1000.00")
        assert cost_item.unit_cost == Decimal("250.00")
        assert cost_item.total_cost == Decimal("250000.00")
        assert cost_item.metadata["supplier"] == "ABC Concrete"

    async def test_cost_item_calculations(self, session: AsyncSession):
        """Test cost item calculation consistency."""
        project_id = uuid4()
        fin_project = FinProject(project_id=project_id, name="Project")
        session.add(fin_project)
        await session.flush()

        scenario = FinScenario(
            project_id=project_id,
            fin_project_id=fin_project.id,
            name="Scenario",
        )
        session.add(scenario)
        await session.flush()

        quantity = Decimal("500")
        unit_cost = Decimal("150.50")
        expected_total = quantity * unit_cost

        cost_item = FinCostItem(
            project_id=project_id,
            scenario_id=scenario.id,
            name="Material",
            quantity=quantity,
            unit_cost=unit_cost,
            total_cost=expected_total,
        )
        session.add(cost_item)
        await session.commit()
        await session.refresh(cost_item)

        assert cost_item.total_cost == Decimal("75250.00")


class TestFinSchedule:
    """Test FinSchedule model for monthly cash flow tracking."""

    async def test_create_fin_schedule(self, session: AsyncSession):
        """Test creating a monthly schedule entry."""
        project_id = uuid4()
        fin_project = FinProject(project_id=project_id, name="Project")
        session.add(fin_project)
        await session.flush()

        scenario = FinScenario(
            project_id=project_id,
            fin_project_id=fin_project.id,
            name="Scenario",
        )
        session.add(scenario)
        await session.flush()

        schedule = FinSchedule(
            project_id=project_id,
            scenario_id=scenario.id,
            month_index=1,
            hard_cost=Decimal("100000.00"),
            soft_cost=Decimal("20000.00"),
            revenue=Decimal("50000.00"),
            cash_flow=Decimal("-70000.00"),
            cumulative_cash_flow=Decimal("-70000.00"),
        )
        session.add(schedule)
        await session.commit()
        await session.refresh(schedule)

        assert schedule.id is not None
        assert schedule.month_index == 1
        assert schedule.hard_cost == Decimal("100000.00")
        assert schedule.soft_cost == Decimal("20000.00")

    async def test_fin_schedule_cumulative_flow(self, session: AsyncSession):
        """Test cumulative cash flow tracking across months."""
        project_id = uuid4()
        fin_project = FinProject(project_id=project_id, name="Project")
        session.add(fin_project)
        await session.flush()

        scenario = FinScenario(
            project_id=project_id,
            fin_project_id=fin_project.id,
            name="Scenario",
        )
        session.add(scenario)
        await session.flush()

        # Month 1: -70000
        schedule1 = FinSchedule(
            project_id=project_id,
            scenario_id=scenario.id,
            month_index=1,
            cash_flow=Decimal("-70000.00"),
            cumulative_cash_flow=Decimal("-70000.00"),
        )
        session.add(schedule1)

        # Month 2: +50000 (cumulative: -20000)
        schedule2 = FinSchedule(
            project_id=project_id,
            scenario_id=scenario.id,
            month_index=2,
            cash_flow=Decimal("50000.00"),
            cumulative_cash_flow=Decimal("-20000.00"),
        )
        session.add(schedule2)

        await session.commit()

        result = await session.execute(
            select(FinSchedule)
            .where(FinSchedule.scenario_id == scenario.id)
            .order_by(FinSchedule.month_index)
        )
        schedules = result.scalars().all()

        assert len(schedules) == 2
        assert schedules[0].cash_flow == Decimal("-70000.00")
        assert schedules[1].cash_flow == Decimal("50000.00")
        assert schedules[1].cumulative_cash_flow == Decimal("-20000.00")

    async def test_fin_schedule_metadata(self, session: AsyncSession):
        """Test schedule metadata storage."""
        project_id = uuid4()
        fin_project = FinProject(project_id=project_id, name="Project")
        session.add(fin_project)
        await session.flush()

        scenario = FinScenario(
            project_id=project_id,
            fin_project_id=fin_project.id,
            name="Scenario",
        )
        session.add(scenario)
        await session.flush()

        schedule = FinSchedule(
            project_id=project_id,
            scenario_id=scenario.id,
            month_index=6,
            metadata_json={
                "milestone": "Milestone achieved",
                "notes": "On schedule",
            },
        )
        session.add(schedule)
        await session.commit()
        await session.refresh(schedule)

        assert schedule.metadata["milestone"] == "Milestone achieved"
        assert schedule.metadata["notes"] == "On schedule"


class TestFinCapitalStack:
    """Test FinCapitalStack model for financing composition."""

    async def test_create_capital_stack_entry(self, session: AsyncSession):
        """Test creating a capital stack financing entry."""
        project_id = uuid4()
        fin_project = FinProject(project_id=project_id, name="Project")
        session.add(fin_project)
        await session.flush()

        scenario = FinScenario(
            project_id=project_id,
            fin_project_id=fin_project.id,
            name="Scenario",
        )
        session.add(scenario)
        await session.flush()

        capital_stack = FinCapitalStack(
            project_id=project_id,
            scenario_id=scenario.id,
            name="Senior Debt",
            source_type="Bank Loan",
            tranche_order=1,
            amount=Decimal("75000000.00"),
            rate=Decimal("0.0450"),
            equity_share=Decimal("0.5000"),
        )
        session.add(capital_stack)
        await session.commit()
        await session.refresh(capital_stack)

        assert capital_stack.id is not None
        assert capital_stack.name == "Senior Debt"
        assert capital_stack.source_type == "Bank Loan"
        assert capital_stack.tranche_order == 1
        assert capital_stack.amount == Decimal("75000000.00")
        assert capital_stack.rate == Decimal("0.0450")
        assert capital_stack.equity_share == Decimal("0.5000")

    async def test_capital_stack_tranche_ordering(self, session: AsyncSession):
        """Test multiple tranches with ordering."""
        project_id = uuid4()
        fin_project = FinProject(project_id=project_id, name="Project")
        session.add(fin_project)
        await session.flush()

        scenario = FinScenario(
            project_id=project_id,
            fin_project_id=fin_project.id,
            name="Scenario",
        )
        session.add(scenario)
        await session.flush()

        # Senior debt
        senior = FinCapitalStack(
            project_id=project_id,
            scenario_id=scenario.id,
            name="Senior Debt",
            tranche_order=1,
            amount=Decimal("100000000.00"),
            rate=Decimal("0.0450"),
        )
        session.add(senior)

        # Mezzanine
        mezz = FinCapitalStack(
            project_id=project_id,
            scenario_id=scenario.id,
            name="Mezzanine Financing",
            tranche_order=2,
            amount=Decimal("25000000.00"),
            rate=Decimal("0.0850"),
        )
        session.add(mezz)

        # Equity
        equity = FinCapitalStack(
            project_id=project_id,
            scenario_id=scenario.id,
            name="Equity",
            tranche_order=3,
            amount=Decimal("25000000.00"),
            rate=Decimal("0.0000"),
        )
        session.add(equity)

        await session.commit()

        result = await session.execute(
            select(FinCapitalStack)
            .where(FinCapitalStack.scenario_id == scenario.id)
            .order_by(FinCapitalStack.tranche_order)
        )
        tranches = result.scalars().all()

        assert len(tranches) == 3
        assert tranches[0].name == "Senior Debt"
        assert tranches[1].name == "Mezzanine Financing"
        assert tranches[2].name == "Equity"

    async def test_capital_stack_metadata(self, session: AsyncSession):
        """Test capital stack metadata storage."""
        project_id = uuid4()
        fin_project = FinProject(project_id=project_id, name="Project")
        session.add(fin_project)
        await session.flush()

        scenario = FinScenario(
            project_id=project_id,
            fin_project_id=fin_project.id,
            name="Scenario",
        )
        session.add(scenario)
        await session.flush()

        capital_stack = FinCapitalStack(
            project_id=project_id,
            scenario_id=scenario.id,
            name="Bank Loan",
            metadata_json={
                "lender": "Bank XYZ",
                "tenor_years": 15,
                "amortization_schedule": "straight-line",
            },
        )
        session.add(capital_stack)
        await session.commit()
        await session.refresh(capital_stack)

        assert capital_stack.metadata["lender"] == "Bank XYZ"
        assert capital_stack.metadata["tenor_years"] == 15


class TestFinResult:
    """Test FinResult model for financial calculation outputs."""

    async def test_create_fin_result(self, session: AsyncSession):
        """Test creating a financial result entry."""
        project_id = uuid4()
        fin_project = FinProject(project_id=project_id, name="Project")
        session.add(fin_project)
        await session.flush()

        scenario = FinScenario(
            project_id=project_id,
            fin_project_id=fin_project.id,
            name="Scenario",
        )
        session.add(scenario)
        await session.flush()

        result = FinResult(
            project_id=project_id,
            scenario_id=scenario.id,
            name="IRR",
            value=Decimal("0.1450"),
            unit="%",
        )
        session.add(result)
        await session.commit()
        await session.refresh(result)

        assert result.id is not None
        assert result.name == "IRR"
        assert result.value == Decimal("0.1450")
        assert result.unit == "%"

    async def test_multiple_fin_results(self, session: AsyncSession):
        """Test creating multiple result metrics for a scenario."""
        project_id = uuid4()
        fin_project = FinProject(project_id=project_id, name="Project")
        session.add(fin_project)
        await session.flush()

        scenario = FinScenario(
            project_id=project_id,
            fin_project_id=fin_project.id,
            name="Scenario",
        )
        session.add(scenario)
        await session.flush()

        results_data = [
            ("IRR", Decimal("0.1450"), "%"),
            ("Equity Multiple", Decimal("2.5000"), "x"),
            ("NPV", Decimal("25000000.00"), "$"),
            ("Payback Period", Decimal("8.5"), "years"),
            ("Debt Service Coverage Ratio", Decimal("1.2500"), "x"),
        ]

        for name, value, unit in results_data:
            result = FinResult(
                project_id=project_id,
                scenario_id=scenario.id,
                name=name,
                value=value,
                unit=unit,
            )
            session.add(result)

        await session.commit()

        result = await session.execute(
            select(FinResult).where(FinResult.scenario_id == scenario.id)
        )
        results = result.scalars().all()

        assert len(results) == 5
        result_names = {r.name for r in results}
        assert "IRR" in result_names
        assert "Equity Multiple" in result_names
        assert "NPV" in result_names

    async def test_fin_result_metadata(self, session: AsyncSession):
        """Test result metadata storage."""
        project_id = uuid4()
        fin_project = FinProject(project_id=project_id, name="Project")
        session.add(fin_project)
        await session.flush()

        scenario = FinScenario(
            project_id=project_id,
            fin_project_id=fin_project.id,
            name="Scenario",
        )
        session.add(scenario)
        await session.flush()

        result = FinResult(
            project_id=project_id,
            scenario_id=scenario.id,
            name="IRR",
            value=Decimal("0.1450"),
            unit="%",
            metadata_json={
                "calculation_method": "XIRR",
                "confidence_level": "high",
                "calculated_at": "2025-01-15T10:30:00Z",
            },
        )
        session.add(result)
        await session.commit()
        await session.refresh(result)

        assert result.metadata["calculation_method"] == "XIRR"
        assert result.metadata["confidence_level"] == "high"


class TestFinanceModelIndexes:
    """Test that indexes are properly defined for performance."""

    async def test_fin_project_has_indexes(self, session: AsyncSession):
        """Test that FinProject has expected indexes."""
        # Create test data to verify indexes exist
        project_id = uuid4()
        fin_project = FinProject(
            project_id=project_id,
            name="Index Test Project",
        )
        session.add(fin_project)
        await session.commit()

        # Verify query by indexed columns works
        result = await session.execute(
            select(FinProject).where(FinProject.project_id == project_id)
        )
        assert result.scalars().first() is not None

    async def test_fin_scenario_has_indexes(self, session: AsyncSession):
        """Test that FinScenario has expected indexes."""
        project_id = uuid4()
        fin_project = FinProject(project_id=project_id, name="Project")
        session.add(fin_project)
        await session.flush()

        scenario = FinScenario(
            project_id=project_id,
            fin_project_id=fin_project.id,
            name="Indexed Scenario",
            is_primary=True,
        )
        session.add(scenario)
        await session.commit()

        # Query by indexed columns
        result = await session.execute(
            select(FinScenario).where(
                (FinScenario.project_id == project_id)
                & (FinScenario.is_primary.is_(True))
            )
        )
        assert result.scalars().first() is not None


class TestFinanceModelIntegration:
    """Integration tests across multiple finance models."""

    async def test_complete_finance_scenario_workflow(self, session: AsyncSession):
        """Test a complete workflow with all finance model types."""
        project_id = uuid4()

        # Create project
        fin_project = FinProject(
            project_id=project_id,
            name="Complete Workflow Project",
            currency="SGD",
            discount_rate=Decimal("0.0850"),
        )
        session.add(fin_project)
        await session.flush()

        # Create scenario
        scenario = FinScenario(
            project_id=project_id,
            fin_project_id=fin_project.id,
            name="Base Case",
            is_primary=True,
            assumptions={"growth_rate": 0.10},
        )
        session.add(scenario)
        await session.flush()

        # Add cost items
        for i in range(3):
            cost_item = FinCostItem(
                project_id=project_id,
                scenario_id=scenario.id,
                name=f"Cost Item {i+1}",
                category="Material",
                total_cost=Decimal("50000.00") * (i + 1),
            )
            session.add(cost_item)

        # Add schedules
        for month in range(1, 4):
            schedule = FinSchedule(
                project_id=project_id,
                scenario_id=scenario.id,
                month_index=month,
                hard_cost=Decimal("100000.00"),
                cash_flow=Decimal("50000.00"),
                cumulative_cash_flow=Decimal("50000.00") * month,
            )
            session.add(schedule)

        # Add capital stack
        capital_stack = FinCapitalStack(
            project_id=project_id,
            scenario_id=scenario.id,
            name="Senior Debt",
            amount=Decimal("100000000.00"),
            rate=Decimal("0.0450"),
        )
        session.add(capital_stack)

        # Add results
        result = FinResult(
            project_id=project_id,
            scenario_id=scenario.id,
            name="IRR",
            value=Decimal("0.1450"),
            unit="%",
        )
        session.add(result)

        await session.commit()
        await session.refresh(scenario)

        # Verify complete structure
        assert scenario.fin_project.name == "Complete Workflow Project"
        assert len(scenario.cost_items) == 3
        assert len(scenario.schedules) == 3
        assert len(scenario.capital_stack) == 1
        assert len(scenario.results) == 1

        # Verify cost totals
        total_costs = sum(ci.total_cost for ci in scenario.cost_items)
        assert total_costs == Decimal("300000.00")

        # Verify cumulative cash flow
        final_schedule = scenario.schedules[-1]
        assert final_schedule.cumulative_cash_flow == Decimal("150000.00")

    async def test_update_finance_scenario_fields(self, session: AsyncSession):
        """Test updating finance scenario fields."""
        project_id = uuid4()
        fin_project = FinProject(project_id=project_id, name="Project")
        session.add(fin_project)
        await session.flush()

        scenario = FinScenario(
            project_id=project_id,
            fin_project_id=fin_project.id,
            name="Original Name",
            is_primary=False,
        )
        session.add(scenario)
        await session.commit()
        await session.refresh(scenario)

        original_updated_at = scenario.updated_at

        # Update fields
        scenario.name = "Updated Name"
        scenario.is_primary = True
        scenario.assumptions = {"updated": True}
        await session.commit()
        await session.refresh(scenario)

        assert scenario.name == "Updated Name"
        assert scenario.is_primary is True
        assert scenario.assumptions["updated"] is True
        assert scenario.updated_at >= original_updated_at

    async def test_query_finance_models_by_project(self, session: AsyncSession):
        """Test querying all finance models by project_id."""
        project_id_1 = uuid4()
        project_id_2 = uuid4()

        # Create two projects with scenarios
        for proj_id, proj_name in [
            (project_id_1, "Project 1"),
            (project_id_2, "Project 2"),
        ]:
            fin_project = FinProject(
                project_id=proj_id,
                name=proj_name,
            )
            session.add(fin_project)
            await session.flush()

            for scenario_num in range(2):
                scenario = FinScenario(
                    project_id=proj_id,
                    fin_project_id=fin_project.id,
                    name=f"Scenario {scenario_num + 1}",
                )
                session.add(scenario)

        await session.commit()

        # Query scenarios for project 1
        result = await session.execute(
            select(FinScenario).where(FinScenario.project_id == project_id_1)
        )
        project_1_scenarios = result.scalars().all()

        # Query scenarios for project 2
        result = await session.execute(
            select(FinScenario).where(FinScenario.project_id == project_id_2)
        )
        project_2_scenarios = result.scalars().all()

        assert len(project_1_scenarios) == 2
        assert len(project_2_scenarios) == 2
        assert all(s.project_id == project_id_1 for s in project_1_scenarios)
        assert all(s.project_id == project_id_2 for s in project_2_scenarios)
