"""Pydantic schemas for finance feasibility endpoints."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class CostIndexSnapshot(BaseModel):
    """Snapshot of a cost index reading used for escalation."""

    period: str
    value: Decimal
    unit: str
    source: str | None = None
    provider: str | None = None
    methodology: str | None = None


class CostIndexProvenance(BaseModel):
    """Details describing how a cost index adjustment was derived."""

    series_name: str
    jurisdiction: str
    provider: str | None = None
    base_period: str
    latest_period: str | None = None
    scalar: Decimal | None = None
    base_index: CostIndexSnapshot | None = None
    latest_index: CostIndexSnapshot | None = None


class CostEscalationInput(BaseModel):
    """Inputs required to escalate a base amount using cost indices."""

    amount: Decimal = Field(..., ge=Decimal("0"))
    base_period: str = Field(..., min_length=1)
    series_name: str = Field(..., min_length=1)
    jurisdiction: str = Field(default="SG", min_length=1)
    provider: str | None = None


class CashflowInputs(BaseModel):
    """Cash flow series used for NPV and IRR calculations."""

    discount_rate: Decimal
    cash_flows: list[Decimal]

    @field_validator("cash_flows")
    @classmethod
    def _ensure_cashflows_present(cls, value: list[Decimal]) -> list[Decimal]:
        if not value:
            raise ValueError("cash_flows must contain at least one value")
        return value


class DscrInputs(BaseModel):
    """Net operating income and debt service schedules for DSCR calculations."""

    net_operating_incomes: list[Decimal]
    debt_services: list[Decimal]
    period_labels: list[str] | None = None

    @model_validator(mode="after")
    def _validate_lengths(cls, instance: DscrInputs) -> DscrInputs:
        """Ensure DSCR timelines share a consistent length."""

        incomes_len = len(instance.net_operating_incomes)
        if len(instance.debt_services) != incomes_len:
            raise ValueError(
                "net_operating_incomes and debt_services must be the same length"
            )
        if (
            instance.period_labels is not None
            and len(instance.period_labels) != incomes_len
        ):
            raise ValueError(
                "period_labels must be the same length as net_operating_incomes"
            )
        return instance


class FinanceScenarioInput(BaseModel):
    """Scenario level configuration submitted by the frontend."""

    name: str
    description: str | None = None
    currency: str = Field(default="SGD", min_length=1)
    is_primary: bool = False
    cost_escalation: CostEscalationInput
    cash_flow: CashflowInputs
    dscr: DscrInputs | None = None


class FinanceFeasibilityRequest(BaseModel):
    """Payload accepted by the finance feasibility endpoint."""

    project_id: int
    project_name: str | None = None
    fin_project_id: int | None = None
    scenario: FinanceScenarioInput


class DscrEntrySchema(BaseModel):
    """Serialised DSCR timeline entry."""

    period: str
    noi: Decimal
    debt_service: Decimal
    dscr: str | None = None
    currency: str


class FinanceResultSchema(BaseModel):
    """Persisted finance result returned to callers."""

    name: str
    value: Decimal | None = None
    unit: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class FinanceFeasibilityResponse(BaseModel):
    """Response payload returned by the finance feasibility endpoint."""

    scenario_id: int
    project_id: int
    fin_project_id: int
    scenario_name: str
    currency: str
    escalated_cost: Decimal
    cost_index: CostIndexProvenance
    results: list[FinanceResultSchema]
    dscr_timeline: list[DscrEntrySchema] = Field(default_factory=list)


__all__ = [
    "CashflowInputs",
    "CostEscalationInput",
    "CostIndexProvenance",
    "CostIndexSnapshot",
    "DscrEntrySchema",
    "DscrInputs",
    "FinanceFeasibilityRequest",
    "FinanceFeasibilityResponse",
    "FinanceResultSchema",
    "FinanceScenarioInput",
]
