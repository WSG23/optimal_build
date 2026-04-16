"""Pydantic schemas for deal outcome endpoints."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.deal_outcome import ApprovalOutcome, DealOutcome, OutcomeResolution
from app.schemas._typing import validate_model


class DealOutcomeCreate(BaseModel):
    """Payload for recording a deal outcome."""

    resolution: OutcomeResolution
    resolution_note: str | None = None
    scenario_id: int | None = None

    # Financials — all optional, partial capture encouraged
    actual_purchase_price: Decimal | None = None
    actual_price_currency: str = Field(default="SGD", min_length=3, max_length=3)
    actual_gfa_approved_sqm: Decimal | None = None
    actual_construction_cost: Decimal | None = None
    actual_noi: Decimal | None = None
    actual_yield_pct: Decimal | None = Field(
        default=None, ge=Decimal("0"), le=Decimal("100")
    )

    # Timeline
    actual_completion_date: date | None = None
    approval_submitted_date: date | None = None
    approval_decided_date: date | None = None

    # Authority
    approval_authority: str | None = Field(default=None, max_length=100)
    approval_outcome: ApprovalOutcome | None = None
    approval_conditions: str | None = None
    gfa_amendment_sqm: Decimal | None = None

    # Denormalised context
    jurisdiction_code: str | None = Field(default=None, max_length=10)
    asset_type: str | None = Field(default=None, max_length=40)
    metadata: dict[str, Any] | None = None


class DealOutcomeUpdate(BaseModel):
    """All fields optional — users fill in as data arrives."""

    resolution: OutcomeResolution | None = None
    resolution_note: str | None = None
    scenario_id: int | None = None

    actual_purchase_price: Decimal | None = None
    actual_price_currency: str | None = Field(default=None, min_length=3, max_length=3)
    actual_gfa_approved_sqm: Decimal | None = None
    actual_construction_cost: Decimal | None = None
    actual_noi: Decimal | None = None
    actual_yield_pct: Decimal | None = Field(
        default=None, ge=Decimal("0"), le=Decimal("100")
    )

    actual_completion_date: date | None = None
    approval_submitted_date: date | None = None
    approval_decided_date: date | None = None

    approval_authority: str | None = Field(default=None, max_length=100)
    approval_outcome: ApprovalOutcome | None = None
    approval_conditions: str | None = None
    gfa_amendment_sqm: Decimal | None = None

    jurisdiction_code: str | None = Field(default=None, max_length=10)
    asset_type: str | None = Field(default=None, max_length=40)
    metadata: dict[str, Any] | None = None


class DealOutcomeResponse(BaseModel):
    """Serialised deal outcome returned from the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    deal_id: UUID
    scenario_id: int | None = None
    recorded_by: UUID
    resolution: str
    resolution_note: str | None = None

    actual_purchase_price: Decimal | None = None
    actual_price_currency: str
    actual_gfa_approved_sqm: Decimal | None = None
    actual_construction_cost: Decimal | None = None
    actual_noi: Decimal | None = None
    actual_yield_pct: Decimal | None = None

    actual_completion_date: date | None = None
    approval_submitted_date: date | None = None
    approval_decided_date: date | None = None

    approval_authority: str | None = None
    approval_outcome: str | None = None
    approval_conditions: str | None = None
    gfa_amendment_sqm: Decimal | None = None

    jurisdiction_code: str | None = None
    asset_type: str | None = None
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    # Computed — returned by API when scenario is linked
    projected_vs_actual: dict[str, Any] | None = None

    @classmethod
    def from_orm_outcome(
        cls,
        outcome: DealOutcome,
        *,
        projected_vs_actual: dict[str, Any] | None = None,
    ) -> Self:
        metadata_value = getattr(outcome, "metadata", None)
        if not isinstance(metadata_value, dict):
            metadata_value = getattr(outcome, "metadata_json", {}) or {}
        payload = getattr(outcome, "__dict__", {}).copy()
        payload.pop("_sa_instance_state", None)
        payload["metadata"] = metadata_value
        payload["projected_vs_actual"] = projected_vs_actual
        return validate_model(cls, payload)


class DealOutcomeBenchmarkQuery(BaseModel):
    """Query parameters for benchmark aggregation."""

    jurisdiction_code: str | None = None
    asset_type: str | None = None
    resolution: OutcomeResolution | None = None
    date_from: date | None = None
    date_to: date | None = None


class DealOutcomeBenchmarkResponse(BaseModel):
    """Aggregated benchmark statistics across deal outcomes."""

    sample_size: int
    median_yield_pct: Decimal | None = None
    median_price_psm: Decimal | None = None
    median_approval_days: int | None = None
    median_gfa_amendment_pct: Decimal | None = None
    resolution_distribution: dict[str, int] = Field(default_factory=dict)


__all__ = [
    "DealOutcomeBenchmarkQuery",
    "DealOutcomeBenchmarkResponse",
    "DealOutcomeCreate",
    "DealOutcomeResponse",
    "DealOutcomeUpdate",
]
