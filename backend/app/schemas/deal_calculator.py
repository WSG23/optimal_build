"""Schemas for the standalone developer deal calculator."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel

from app.schemas.buildable import RuleCorpusStatus
from app.schemas.external_sources import ExternalSourceMetadata
from app.schemas.feasibility import (
    AssetOptimizationRecommendation,
    BuildEnvelopeSnapshot,
    BuildableAreaSummary,
    RuleAssessmentResult,
)
from app.schemas.finance import AssetFinancialSummarySchema, FinanceAssetBreakdownSchema


class DealCalculatorCoordinates(BaseModel):
    """Coordinates returned when an address is geocoded."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    latitude: float
    longitude: float


class DealCalculatorFinancingAssumptions(BaseModel):
    """Quick financing assumptions used for top-of-funnel modelling."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    equity_pct: float = Field(default=40.0, ge=0, le=100)
    debt_pct: float = Field(default=60.0, ge=0, le=100)
    annual_interest_rate_pct: float = Field(default=4.8, ge=0, le=100)
    discount_rate_pct: float = Field(default=8.0, ge=0, le=100)
    exit_cap_rate_pct: float = Field(default=4.0, gt=0, le=100)
    sale_cost_pct: float = Field(default=2.0, ge=0, le=100)
    hold_years: int = Field(default=3, ge=1, le=10)


class DealCalculatorRequest(BaseModel):
    """Request for the standalone deal calculator."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    project_name: str | None = Field(default="Quick Screen", min_length=1)
    address: str | None = Field(default=None, min_length=3)
    land_use: str | None = Field(default=None, min_length=1)
    zone_code: str | None = Field(default=None, min_length=1)
    site_area_sqm: float | None = Field(default=None, gt=0)
    allowable_plot_ratio: float | None = Field(default=None, gt=0)
    current_gfa_sqm: float | None = Field(default=None, ge=0)
    target_gross_floor_area_sqm: float | None = Field(default=None, gt=0)
    building_height_meters: float | None = Field(default=None, gt=0)
    existing_use: str | None = Field(default=None, min_length=1)
    financing: DealCalculatorFinancingAssumptions = Field(default_factory=DealCalculatorFinancingAssumptions)

    @model_validator(mode="after")
    def _ensure_address_or_manual_inputs(self) -> "DealCalculatorRequest":
        if self.address:
            return self
        if self.site_area_sqm is None and self.zone_code is None and self.land_use is None:
            raise ValueError(
                "Provide an address or manual site assumptions (siteAreaSqm, zoneCode, or landUse)."
            )
        return self


class DealCalculatorSiteSummary(BaseModel):
    """Resolved site identity for the screen."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    input_mode: Literal["address", "manual"]
    formatted_address: str
    coordinates: DealCalculatorCoordinates | None = None
    jurisdiction_code: str = "SG"
    land_use: str
    existing_use: str | None = None
    zone_code: str | None = None
    zone_description: str | None = None
    geocoding_source: ExternalSourceMetadata | None = None
    amenities_source: ExternalSourceMetadata | None = None
    ura_source: ExternalSourceMetadata | None = None


class DealCalculatorFinanceSummary(BaseModel):
    """One-screen finance output for the top-of-funnel model."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    total_capex_sgd: Decimal | None = None
    total_annual_revenue_sgd: Decimal | None = None
    total_annual_noi_sgd: Decimal | None = None
    blended_yield_pct: Decimal | None = None
    equity_required_sgd: Decimal | None = None
    debt_amount_sgd: Decimal | None = None
    annual_debt_service_sgd: Decimal | None = None
    cap_rate_pct: Decimal | None = None
    dscr: Decimal | None = None
    npv_sgd: Decimal | None = None
    irr: Decimal | None = None
    moic: Decimal | None = None
    estimated_exit_value_sgd: Decimal | None = None
    notes: list[str] = Field(default_factory=list)


class DealCalculatorResponse(BaseModel):
    """Response returned by the standalone deal calculator."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    generated_at: datetime
    site: DealCalculatorSiteSummary
    build_envelope: BuildEnvelopeSnapshot
    rule_corpus_status: RuleCorpusStatus | None = None
    recommended_rule_ids: list[str] = Field(default_factory=list)
    feasibility_summary: BuildableAreaSummary
    feasibility_rules: list[RuleAssessmentResult] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    asset_optimizations: list[AssetOptimizationRecommendation] = Field(
        default_factory=list
    )
    asset_mix_summary: AssetFinancialSummarySchema | None = None
    asset_breakdowns: list[FinanceAssetBreakdownSchema] = Field(default_factory=list)
    finance_summary: DealCalculatorFinanceSummary

