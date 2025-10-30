"""Feasibility assessment API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from app.api.deps import require_viewer
from app.schemas.feasibility import (
    FeasibilityAssessmentRequest,
    FeasibilityAssessmentResponse,
    FeasibilityRulesResponse,
    NewFeasibilityProjectInput,
)
from app.services.feasibility import (
    generate_feasibility_rules,
    run_feasibility_assessment,
)

router = APIRouter(prefix="/feasibility", tags=["feasibility"])


def _normalise_project_payload(data: dict[str, Any]) -> dict[str, Any]:
    def _normalise_envelope(payload: dict[str, Any] | None) -> dict[str, Any] | None:
        if not isinstance(payload, dict):
            return None
        envelope_mapping = {
            "siteAreaSqm": "site_area_sqm",
            "allowablePlotRatio": "allowable_plot_ratio",
            "maxBuildableGfaSqm": "max_buildable_gfa_sqm",
            "currentGfaSqm": "current_gfa_sqm",
            "additionalPotentialGfaSqm": "additional_potential_gfa_sqm",
        }
        normalised_envelope = {
            envelope_mapping.get(key, key): value for key, value in payload.items()
        }
        return normalised_envelope

    mapping = {
        "siteAddress": "site_address",
        "siteAreaSqm": "site_area_sqm",
        "landUse": "land_use",
        "targetGrossFloorAreaSqm": "target_gross_floor_area_sqm",
        "buildingHeightMeters": "building_height_meters",
    }
    normalised = {mapping.get(key, key): value for key, value in data.items()}
    if "buildEnvelope" in data:
        normalised["build_envelope"] = _normalise_envelope(data.get("buildEnvelope"))
    elif "build_envelope" in data:
        normalised["build_envelope"] = _normalise_envelope(data.get("build_envelope"))
    return normalised


def _normalise_assessment_payload(data: dict[str, Any]) -> dict[str, Any]:
    normalised = dict(data)
    project_payload = normalised.get("project")
    if isinstance(project_payload, dict):
        normalised["project"] = _normalise_project_payload(project_payload)
    if "selectedRuleIds" in normalised:
        normalised["selected_rule_ids"] = normalised.pop("selectedRuleIds")
    return normalised


@router.post("/rules", response_model=FeasibilityRulesResponse)
async def fetch_rules(
    payload: dict[str, Any],
    _: str = Depends(require_viewer),
) -> FeasibilityRulesResponse:
    """Return the recommended rules for the submitted project."""

    project = NewFeasibilityProjectInput(**_normalise_project_payload(payload))
    return generate_feasibility_rules(project)


@router.post("/assessment", response_model=FeasibilityAssessmentResponse)
async def submit_assessment(
    payload: dict[str, Any],
    _: str = Depends(require_viewer),
) -> FeasibilityAssessmentResponse:
    """Evaluate the feasibility assessment for the selected rules."""

    request = FeasibilityAssessmentRequest(**_normalise_assessment_payload(payload))
    return run_feasibility_assessment(request)


__all__ = ["router"]
