"""Pydantic models for feasibility rule and assessment APIs."""

from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

FeasibilityRuleSeverity = Literal["critical", "important", "informational"]
FeasibilityRuleStatus = Literal["pass", "fail", "warning"]


class NewFeasibilityProjectInput(BaseModel):
    """Input details describing the project under assessment."""

    name: str = Field(..., min_length=1)
    site_address: str = Field(..., min_length=1)
    site_area_sqm: float = Field(..., gt=0)
    land_use: str = Field(..., min_length=1)
    target_gross_floor_area_sqm: Optional[float] = Field(None, gt=0)
    building_height_meters: Optional[float] = Field(None, gt=0)


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
    unit: Optional[str] = None
    severity: FeasibilityRuleSeverity
    default_selected: bool = False


class FeasibilityRulesSummary(BaseModel):
    """Summary describing how the recommended rules were chosen."""

    compliance_focus: str
    notes: Optional[str] = None


class FeasibilityRulesResponse(BaseModel):
    """Response payload for the feasibility rules endpoint."""

    project_id: str
    rules: List[FeasibilityRule]
    recommended_rule_ids: List[str]
    summary: FeasibilityRulesSummary


class FeasibilityAssessmentRequest(BaseModel):
    """Request payload for evaluating the selected rules."""

    project: NewFeasibilityProjectInput
    selected_rule_ids: List[str]


class RuleAssessmentResult(FeasibilityRule):
    """Assessment outcome for a rule."""

    status: FeasibilityRuleStatus
    actual_value: Optional[str] = None
    notes: Optional[str] = None


class BuildableAreaSummary(BaseModel):
    """High-level metrics produced by the feasibility engine."""

    max_permissible_gfa_sqm: int
    estimated_achievable_gfa_sqm: int
    estimated_unit_count: int
    site_coverage_percent: float
    remarks: Optional[str] = None


class FeasibilityAssessmentResponse(BaseModel):
    """Response payload produced after evaluating the project."""

    project_id: str
    summary: BuildableAreaSummary
    rules: List[RuleAssessmentResult]
    recommendations: List[str]


__all__ = [
    "BuildableAreaSummary",
    "FeasibilityAssessmentRequest",
    "FeasibilityAssessmentResponse",
    "FeasibilityRule",
    "FeasibilityRuleSeverity",
    "FeasibilityRuleStatus",
    "FeasibilityRulesResponse",
    "FeasibilityRulesSummary",
    "NewFeasibilityProjectInput",
    "RuleAssessmentResult",
]
