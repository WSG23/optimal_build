"""Pydantic models for feasibility rule and assessment APIs."""

from __future__ import annotations

from typing import Literal

from app.schemas.finance import AssetFinancialSummarySchema
from pydantic import BaseModel, Field

FeasibilityRuleSeverity = Literal["critical", "important", "informational"]
FeasibilityRuleStatus = Literal["pass", "fail", "warning"]


class BuildEnvelopeSnapshot(BaseModel):
    """Optional snapshot of zoning envelope inputs."""

    site_area_sqm: float | None = Field(default=None, gt=0)
    allowable_plot_ratio: float | None = Field(default=None, gt=0)
    max_buildable_gfa_sqm: float | None = Field(default=None, gt=0)
    current_gfa_sqm: float | None = Field(default=None, ge=0)
    additional_potential_gfa_sqm: float | None = Field(default=None)


class NewFeasibilityProjectInput(BaseModel):
    """Input details describing the project under assessment."""

    name: str = Field(..., min_length=1)
    site_address: str = Field(..., min_length=1)
    site_area_sqm: float = Field(..., gt=0)
    land_use: str = Field(..., min_length=1)
    target_gross_floor_area_sqm: float | None = Field(None, gt=0)
    building_height_meters: float | None = Field(None, gt=0)
    build_envelope: BuildEnvelopeSnapshot | None = None


class FeasibilityRule(BaseModel):
    """Rule definition returned to the frontend wizard."""

    id: str
    title: str
    description: str
    authority: str
    topic: str
    parameter_key: str
    operator: str
    value: str
    unit: str | None = None
    severity: FeasibilityRuleSeverity
    default_selected: bool = False


class FeasibilityRulesSummary(BaseModel):
    """Summary describing how the recommended rules were chosen."""

    compliance_focus: str
    notes: str | None = None


class FeasibilityRulesResponse(BaseModel):
    """Response payload for the feasibility rules endpoint."""

    project_id: str
    rules: list[FeasibilityRule]
    recommended_rule_ids: list[str]
    summary: FeasibilityRulesSummary


class FeasibilityAssessmentRequest(BaseModel):
    """Request payload for evaluating the selected rules."""

    project: NewFeasibilityProjectInput
    selected_rule_ids: list[str]


class RuleAssessmentResult(FeasibilityRule):
    """Assessment outcome for a rule."""

    status: FeasibilityRuleStatus
    actual_value: str | None = None
    notes: str | None = None


class BuildableAreaSummary(BaseModel):
    """High-level metrics produced by the feasibility engine."""

    max_permissible_gfa_sqm: int
    estimated_achievable_gfa_sqm: int
    estimated_unit_count: int
    site_coverage_percent: float
    remarks: str | None = None


class AssetOptimizationRecommendation(BaseModel):
    """Asset-specific optimisation recommendation surfaced to clients."""

    asset_type: str
    allocation_pct: float
    allocated_gfa_sqm: int | None = None
    nia_efficiency: float | None = None
    target_floor_height_m: float | None = None
    parking_ratio_per_1000sqm: float | None = None
    rent_psm_month: float | None = None
    stabilised_vacancy_pct: float | None = None
    opex_pct_of_rent: float | None = None
    estimated_revenue_sgd: float | None = None
    estimated_capex_sgd: float | None = None
    fitout_cost_psm: float | None = None
    absorption_months: int | None = None
    risk_level: str | None = None
    heritage_premium_pct: float | None = None
    notes: list[str] = Field(default_factory=list)


class FeasibilityAssessmentResponse(BaseModel):
    """Response payload produced after evaluating the project."""

    project_id: str
    summary: BuildableAreaSummary
    rules: list[RuleAssessmentResult]
    recommendations: list[str]
    asset_optimizations: list[AssetOptimizationRecommendation]
    asset_mix_summary: AssetFinancialSummarySchema | None = None


__all__ = [
    "BuildEnvelopeSnapshot",
    "BuildableAreaSummary",
    "FeasibilityAssessmentRequest",
    "FeasibilityAssessmentResponse",
    "FeasibilityRule",
    "FeasibilityRuleSeverity",
    "FeasibilityRuleStatus",
    "FeasibilityRulesResponse",
    "FeasibilityRulesSummary",
    "AssetOptimizationRecommendation",
    "AssetFinancialSummarySchema",
    "NewFeasibilityProjectInput",
    "RuleAssessmentResult",
]
