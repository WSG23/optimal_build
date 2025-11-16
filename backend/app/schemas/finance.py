"""Pydantic schemas for finance feasibility endpoints."""

from __future__ import annotations

from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Any
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
    field_validator,
    model_validator,
)

FINANCE_FEASIBILITY_REQUEST_EXAMPLE = {
    "project_id": 0,
    "project_name": "string",
    "fin_project_id": 0,
    "scenario": {
        "name": "string",
        "description": "string",
        "currency": "SGD",
        "is_primary": False,
        "cost_escalation": {
            "amount": "0",
            "base_period": "string",
            "jurisdiction": "SG",
            "provider": "string",
            "series_name": "string",
        },
        "cash_flow": {
            "discount_rate": "0",
            "cash_flows": ["0"],
        },
        "dscr": {
            "net_operating_incomes": ["0"],
            "debt_services": ["0"],
            "period_labels": ["string"],
        },
        "capital_stack": [],
        "drawdown_schedule": [],
    },
}


FINANCE_FEASIBILITY_RESPONSE_EXAMPLE = {
    "project_id": 0,
    "fin_project_id": 0,
    "scenario_id": 0,
    "scenario_name": "string",
    "currency": "string",
    "escalated_cost": "0",
    "cost_index": {
        "series_name": "string",
        "jurisdiction": "string",
        "provider": "string",
        "base_period": "string",
        "latest_period": "string",
        "scalar": "0",
        "base_index": {
            "period": "string",
            "value": "0",
            "unit": "string",
            "source": "string",
            "provider": "string",
            "methodology": "string",
        },
        "latest_index": {
            "period": "string",
            "value": "0",
            "unit": "string",
            "source": "string",
            "provider": "string",
            "methodology": "string",
        },
    },
    "results": [
        {
            "name": None,
            "value": None,
            "unit": None,
            "metadata": {},
        }
    ],
    "dscr_timeline": [],
    "capital_stack": {
        "currency": "string",
        "total": "0",
        "equity_total": "0",
        "debt_total": "0",
        "other_total": "0",
        "slices": [],
    },
    "drawdown_schedule": {
        "currency": "string",
        "entries": [],
        "total_equity": "0",
        "total_debt": "0",
        "peak_debt_balance": "0",
        "final_debt_balance": "0",
    },
}


def _format_rate(value: Decimal | None, *, places: int = 4) -> str | None:
    if value is None:
        return None
    quantized = value.quantize(
        Decimal(f"0.{'0' * (places - 1)}1"), rounding=ROUND_HALF_UP
    )
    return f"{quantized:.{places}f}"


def _format_percentage(value: Decimal | None, *, places: int = 2) -> str | None:
    if value is None:
        return None
    quantized = value.quantize(
        Decimal(f"0.{'0' * (places - 1)}1"), rounding=ROUND_HALF_UP
    )
    return f"{quantized:.{places}f}"


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


class CapitalStackSliceInput(BaseModel):
    """Capital stack tranche supplied by the caller."""

    name: str
    source_type: str = Field(..., min_length=1)
    amount: Decimal = Field(..., ge=Decimal("0"))
    rate: Decimal | None = None
    tranche_order: int | None = Field(default=None, ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DrawdownPeriodInput(BaseModel):
    """Single period drawdown inputs for financing schedules."""

    period: str
    equity_draw: Decimal = Decimal("0")
    debt_draw: Decimal = Decimal("0")


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


class FinanceAssetMixInput(BaseModel):
    """Asset mix entry used to drive asset-level finance modelling."""

    asset_type: str
    allocation_pct: Decimal | None = None
    nia_sqm: Decimal | None = None
    rent_psm_month: Decimal | None = None
    stabilised_vacancy_pct: Decimal | None = None
    opex_pct_of_rent: Decimal | None = None
    estimated_revenue_sgd: Decimal | None = None
    estimated_capex_sgd: Decimal | None = None
    absorption_months: Decimal | None = None
    risk_level: str | None = None
    heritage_premium_pct: Decimal | None = None
    notes: list[str] = Field(default_factory=list)


class ConstructionLoanFacilityInput(BaseModel):
    """Facility configuration for construction loan modelling."""

    name: str
    amount: Decimal = Field(..., ge=Decimal("0"))
    interest_rate: Decimal | None = None
    periods_per_year: int | None = Field(default=None, ge=1)
    capitalise_interest: bool | None = None
    upfront_fee_pct: Decimal | None = Field(default=None, ge=Decimal("0"))
    exit_fee_pct: Decimal | None = Field(default=None, ge=Decimal("0"))
    reserve_months: int | None = Field(default=None, ge=0)
    amortisation_months: int | None = Field(default=None, ge=0)

    @field_serializer("interest_rate", when_used="json")
    def _serialise_interest_rate(self, value: Decimal | None) -> str | None:
        return _format_rate(value)

    @field_serializer("upfront_fee_pct", "exit_fee_pct", when_used="json")
    def _serialise_percentages(self, value: Decimal | None, info: Any) -> str | None:
        return _format_percentage(value)


class ConstructionLoanInput(BaseModel):
    """Base construction loan configuration submitted by the frontend."""

    interest_rate: Decimal | None = None
    periods_per_year: int | None = Field(default=None, ge=1)
    capitalise_interest: bool = True
    facilities: list[ConstructionLoanFacilityInput] | None = None

    @field_serializer("interest_rate", when_used="json")
    def _serialise_interest_rate(self, value: Decimal | None) -> str | None:
        return _format_rate(value)


class SensitivityBandInput(BaseModel):
    """Input describing a single sensitivity parameter."""

    parameter: str
    low: Decimal | None = None
    base: Decimal | None = None
    high: Decimal | None = None
    notes: list[str] = Field(default_factory=list)


class FinanceScenarioInput(BaseModel):
    """Scenario level configuration submitted by the frontend."""

    name: str
    description: str | None = None
    currency: str = Field(default="SGD", min_length=1)
    is_primary: bool = False
    cost_escalation: CostEscalationInput
    cash_flow: CashflowInputs
    dscr: DscrInputs | None = None
    capital_stack: list[CapitalStackSliceInput] | None = None
    drawdown_schedule: list[DrawdownPeriodInput] | None = None
    asset_mix: list[FinanceAssetMixInput] | None = None
    construction_loan: ConstructionLoanInput | None = None
    sensitivity_bands: list[SensitivityBandInput] | None = None


class FinanceFeasibilityRequest(BaseModel):
    """Payload accepted by the finance feasibility endpoint."""

    model_config = ConfigDict(
        json_schema_extra={"example": FINANCE_FEASIBILITY_REQUEST_EXAMPLE}
    )

    project_id: str | int | UUID
    project_name: str | None = None
    fin_project_id: int | None = None
    scenario: FinanceScenarioInput

    @field_validator("project_id", mode="before")
    @classmethod
    def _coerce_project_id(cls, value: Any) -> str | int | UUID:
        """Accept UUID-compatible values supplied by clients."""

        if value is None:
            raise ValueError("project_id is required")
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                raise ValueError("project_id cannot be blank")
            return stripped
        return value


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


class CapitalStackSliceSchema(BaseModel):
    """Serialised representation of a capital stack component."""

    name: str
    source_type: str
    category: str
    amount: Decimal
    share: Decimal
    rate: Decimal | None = None
    tranche_order: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CapitalStackSummarySchema(BaseModel):
    """Aggregated capital stack summary returned by the API."""

    currency: str
    total: Decimal
    equity_total: Decimal
    debt_total: Decimal
    other_total: Decimal
    equity_ratio: Decimal | None = None
    debt_ratio: Decimal | None = None
    other_ratio: Decimal | None = None
    loan_to_cost: Decimal | None = None
    weighted_average_debt_rate: Decimal | None = None
    slices: list[CapitalStackSliceSchema] = Field(default_factory=list)


class FinancingDrawdownEntrySchema(BaseModel):
    """Serialised drawdown schedule entry."""

    period: str
    equity_draw: Decimal
    debt_draw: Decimal
    total_draw: Decimal
    cumulative_equity: Decimal
    cumulative_debt: Decimal
    outstanding_debt: Decimal


class FinancingDrawdownScheduleSchema(BaseModel):
    """Full drawdown schedule summary returned by the API."""

    currency: str
    entries: list[FinancingDrawdownEntrySchema] = Field(default_factory=list)
    total_equity: Decimal
    total_debt: Decimal
    peak_debt_balance: Decimal
    final_debt_balance: Decimal


class AssetFinancialSummarySchema(BaseModel):
    """Aggregated financial summary derived from asset optimisation."""

    project_name: str | None = None
    total_annual_revenue_sgd: Decimal | None = None
    total_annual_noi_sgd: Decimal | None = None
    total_capex_sgd: Decimal | None = None
    total_nia_sqm: Decimal | None = None
    dominant_risk_profile: str | None = None
    blended_yield_pct: Decimal | None = None
    # Legacy fields retained for compatibility with earlier API responses.
    total_estimated_revenue_sgd: Decimal | None = None
    total_estimated_capex_sgd: Decimal | None = None
    notes: list[str] = Field(default_factory=list)


class FinanceAssetBreakdownSchema(BaseModel):
    """Individual asset breakdown for Phase 2C asset-specific modelling."""

    asset_type: str
    allocation_pct: str | None = None
    nia_sqm: str | None = None
    rent_psm_month: str | None = None
    gross_rent_annual_sgd: str | None = None
    annual_revenue_sgd: str | None = None
    vacancy_loss_sgd: str | None = None
    effective_gross_income_sgd: str | None = None
    operating_expenses_sgd: str | None = None
    annual_opex_sgd: str | None = None
    noi_annual_sgd: str | None = None
    annual_noi_sgd: str | None = None
    estimated_capex_sgd: str | None = None
    capex_sgd: str | None = None
    payback_years: str | None = None
    absorption_months: str | None = None
    stabilised_yield_pct: str | None = None
    risk_level: str | None = None
    risk_priority: int | None = None
    heritage_premium_pct: str | None = None
    notes: list[str] = Field(default_factory=list)


class ConstructionLoanFacilitySchema(BaseModel):
    """Facility-level construction loan metadata returned by the API."""

    name: str
    amount: Decimal | None = None
    interest_rate: Decimal | None = None
    periods_per_year: int | None = None
    capitalised: bool = True
    total_interest: Decimal | None = None
    upfront_fee: Decimal | None = None
    exit_fee: Decimal | None = None
    reserve_months: int | None = None
    amortisation_months: int | None = None


class ConstructionLoanInterestEntrySchema(BaseModel):
    """Per-period construction loan interest accrual."""

    period: str
    opening_balance: Decimal
    closing_balance: Decimal
    average_balance: Decimal
    interest_accrued: Decimal


class ConstructionLoanInterestSchema(BaseModel):
    """Construction loan interest summary for Phase 2C."""

    currency: str
    interest_rate: Decimal | None = None
    periods_per_year: int | None = None
    capitalised: bool = True
    total_interest: Decimal | None = None
    upfront_fee_total: Decimal | None = None
    exit_fee_total: Decimal | None = None
    facilities: list[ConstructionLoanFacilitySchema] = Field(default_factory=list)
    entries: list[ConstructionLoanInterestEntrySchema] = Field(default_factory=list)


class FinanceSensitivityOutcomeSchema(BaseModel):
    """Result row emitted for each sensitivity permutation."""

    parameter: str
    scenario: str
    delta_label: str | None = None
    npv: Decimal | None = None
    irr: Decimal | None = None
    escalated_cost: Decimal | None = None
    total_interest: Decimal | None = None
    notes: list[str] = Field(default_factory=list)


class FinanceJobStatusSchema(BaseModel):
    """Status row describing queued sensitivity jobs."""

    scenario_id: int
    task_id: str | None = None
    status: str
    backend: str | None = None
    queued_at: datetime | None = None


class FinanceFeasibilityResponse(BaseModel):
    """Response payload returned by the finance feasibility endpoint."""

    model_config = ConfigDict(
        json_schema_extra={"example": FINANCE_FEASIBILITY_RESPONSE_EXAMPLE},
        from_attributes=True,
    )

    scenario_id: int
    project_id: str
    fin_project_id: int
    scenario_name: str
    currency: str
    escalated_cost: Decimal
    cost_index: CostIndexProvenance
    results: list[FinanceResultSchema]
    dscr_timeline: list[DscrEntrySchema] = Field(default_factory=list)
    capital_stack: CapitalStackSummarySchema | None = None
    drawdown_schedule: FinancingDrawdownScheduleSchema | None = None
    asset_mix_summary: AssetFinancialSummarySchema | None = None
    asset_breakdowns: list[FinanceAssetBreakdownSchema] = Field(default_factory=list)
    construction_loan_interest: ConstructionLoanInterestSchema | None = None
    construction_loan: ConstructionLoanInput | None = None
    sensitivity_results: list[FinanceSensitivityOutcomeSchema] = Field(
        default_factory=list
    )
    sensitivity_jobs: list[FinanceJobStatusSchema] = Field(default_factory=list)
    sensitivity_bands: list[SensitivityBandInput] = Field(default_factory=list)
    is_primary: bool = False
    is_private: bool = False
    updated_at: datetime | None = None


__all__ = [
    "FINANCE_FEASIBILITY_REQUEST_EXAMPLE",
    "FINANCE_FEASIBILITY_RESPONSE_EXAMPLE",
    "AssetFinancialSummarySchema",
    "CapitalStackSliceInput",
    "CapitalStackSliceSchema",
    "CapitalStackSummarySchema",
    "CashflowInputs",
    "ConstructionLoanFacilityInput",
    "ConstructionLoanInput",
    "ConstructionLoanFacilitySchema",
    "ConstructionLoanInterestEntrySchema",
    "ConstructionLoanInterestSchema",
    "CostEscalationInput",
    "CostIndexProvenance",
    "CostIndexSnapshot",
    "DrawdownPeriodInput",
    "DscrEntrySchema",
    "DscrInputs",
    "FinanceAssetBreakdownSchema",
    "FinanceAssetMixInput",
    "FinanceFeasibilityRequest",
    "FinanceFeasibilityResponse",
    "FinanceResultSchema",
    "FinanceSensitivityOutcomeSchema",
    "FinanceJobStatusSchema",
    "FinanceScenarioInput",
    "SensitivityBandInput",
    "FinancingDrawdownEntrySchema",
    "FinancingDrawdownScheduleSchema",
]
