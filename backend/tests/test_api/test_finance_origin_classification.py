from __future__ import annotations

from app.api.v1.finance_feasibility import _finance_scenario_origin
from app.schemas.finance import (
    CashflowInputs,
    CostEscalationInput,
    FinanceFeasibilityRequest,
    FinanceScenarioInput,
)


def _build_request(description: str | None) -> FinanceFeasibilityRequest:
    return FinanceFeasibilityRequest(
        project_id="project-123",
        scenario=FinanceScenarioInput(
            name="Origin Test Scenario",
            description=description,
            currency="SGD",
            cost_escalation=CostEscalationInput(
                amount="1000000",
                base_period="2024-Q1",
                series_name="construction_all_in",
                jurisdiction="SG",
            ),
            cash_flow=CashflowInputs(
                discount_rate="0.08",
                cash_flows=["-1000000", "1250000"],
            ),
        ),
    )


def test_finance_origin_classifies_workbook_context() -> None:
    payload = _build_request("[Workbook import context] Imported from lender model")

    assert _finance_scenario_origin(payload) == "workbook"


def test_finance_origin_classifies_quick_screen_context() -> None:
    payload = _build_request("[Quick screen context] Generated from deal calculator")

    assert _finance_scenario_origin(payload) == "quick_screen"


def test_finance_origin_defaults_to_manual() -> None:
    payload = _build_request("Manual scenario build")

    assert _finance_scenario_origin(payload) == "manual"
