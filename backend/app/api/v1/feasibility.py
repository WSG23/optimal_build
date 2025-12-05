"""Feasibility assessment API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from app.api.deps import require_viewer
from app.schemas.feasibility import (
    FeasibilityAssessmentRequest,
    FeasibilityAssessmentResponse,
)
from app.services.feasibility import (
    run_feasibility_assessment,
    _normalise_assessment_payload,
)

router = APIRouter(prefix="/feasibility", tags=["Feasibility"])


@router.websocket("/ws")
async def ws_feasibility(websocket: WebSocket):
    """
    Real-time feasibility assessment via WebSockets.
    Accepts JSON payload matching FeasibilityAssessmentRequest.
    Returns JSON payload matching FeasibilityAssessmentResponse.
    """
    await websocket.accept()
    try:
        while True:
            # Receive payload
            data = await websocket.receive_json()

            try:
                # Normalise and validate
                # Note: reusing internal helpers from service layer for consistency
                # In a larger refactor, these should be exposed properly
                normalised = _normalise_assessment_payload(data)
                request = FeasibilityAssessmentRequest(**normalised)

                # Run assessment (synchronous logic, but fast enough for MVP)
                # For very heavy blocking logic, allow wrapping in run_in_executor
                response = run_feasibility_assessment(request)

                # Send back response
                await websocket.send_json(response.dict())

            except ValidationError as e:
                await websocket.send_json(
                    {"error": "Validation Error", "details": e.errors()}
                )
            except Exception as e:
                await websocket.send_json(
                    {"error": "Processing Error", "details": str(e)}
                )

    except WebSocketDisconnect:
        pass  # Normal disconnect


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


@router.post("/assessment", response_model=FeasibilityAssessmentResponse)
async def submit_assessment(
    payload: dict[str, Any],
    _: str = Depends(require_viewer),
) -> FeasibilityAssessmentResponse:
    """Evaluate the feasibility assessment for the selected rules."""

    request = FeasibilityAssessmentRequest(**_normalise_assessment_payload(payload))
    return run_feasibility_assessment(request)


__all__ = ["router"]
