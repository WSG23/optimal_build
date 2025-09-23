"""Pydantic schemas for finance feasibility endpoints."""

from __future__ import annotations

from decimal import Decimal
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class CostIndexSnapshot(BaseModel):
    """Snapshot of a cost index reading used for escalation."""

    period: str
    value: Decimal
    unit: str
    source: Optional[str] = None
    provider: Optional[str] = None
    methodology: Optional[str] = None


class CostIndexProvenance(BaseModel):
    """Details describing how a cost index adjustment was derived."""

    series_name: str
    jurisdiction: str
    provider: Optional[str] = None
    base_period: str
    latest_period: Optional[str] = None
    scalar: Optional[Decimal] = None
    base_index: Optional[CostIndexSnapshot] = None
    latest_index: Optional[CostIndexSnapshot] = None


class CostEscalationInput(BaseModel):
    """Inputs required to escalate a base amount using cost indices."""

    amount: Decimal = Field(..., ge=Decimal("0"))
    base_period: str = Field(..., min_length=1)
    series_name: str = Field(..., min_length=1)
    jurisdiction: str = Field(default="SG", min_length=1)
    provider: Optional[str] = None


class CashflowInputs(BaseModel):
    """Cash flow series used for NPV and IRR calculations."""

    discount_rate: Decimal
    cash_flows: List[Decimal]

    @field_validator("cash_flows")
    @classmethod
    def _ensure_cashflows_present(cls, value: List[Decimal]) -> List[Decimal]:
        if not value:
            raise ValueError("cash_flows must contain at least one value")
        return value


class DscrInputs(BaseModel):
    """Net operating income and debt service schedules for DSCR calculations."""

    net_operating_incomes: List[Decimal]
    debt_services: List[Decimal]
    period_labels: Optional[List[str]] = None

    @model_validator(mode="after")
    def _validate_lengths(self) -> "DscrInputs":
        incomes_len = len(self.net_operating_incomes)
        if len(self.debt_services) != incomes_len:
            raise ValueError("net_operating_incomes and debt_services must be the same length")
        if self.period_labels is not None and len(self.period_labels) != incomes_len:
            raise ValueError("period_labels must be the same length as net_operating_incomes")
        return self


class FinanceScenarioInput(BaseModel):
    """Scenario level configuration submitted by the frontend."""

    name: str
    description: Optional[str] = None
    currency: str = Field(default="SGD", min_length=1)
    is_primary: bool = False
    cost_escalation: CostEscalationInput
    cash_flow: CashflowInputs
    dscr: Optional[DscrInputs] = None


class FinanceFeasibilityRequest(BaseModel):
    """Payload accepted by the finance feasibility endpoint."""

    project_id: int
    project_name: Optional[str] = None
    fin_project_id: Optional[int] = None
    scenario: FinanceScenarioInput


class DscrEntrySchema(BaseModel):
    """Serialised DSCR timeline entry."""

    period: str
    noi: Decimal
    debt_service: Decimal
    dscr: Optional[str] = None
    currency: str


class FinanceResultSchema(BaseModel):
    """Persisted finance result returned to callers."""

    name: str
    value: Optional[Decimal] = None
    unit: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class FinanceFeasibilityResponse(BaseModel):
    """Response payload returned by the finance feasibility endpoint."""

    scenario_id: int
    project_id: int
    fin_project_id: int
    scenario_name: str
    currency: str
    escalated_cost: Decimal
    cost_index: CostIndexProvenance
    results: List[FinanceResultSchema]
    dscr_timeline: List[DscrEntrySchema] = Field(default_factory=list)


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

