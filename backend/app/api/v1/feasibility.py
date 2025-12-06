"""Feasibility assessment API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from app.api.deps import require_viewer

from app.schemas.feasibility import (
    FeasibilityAssessmentRequest,
    FeasibilityAssessmentResponse,
    FeasibilityRulesResponse,
    NewFeasibilityProjectInput,
)
from app.schemas.engineering import EngineeringDefaultsResponse
from app.services.feasibility import (
    generate_feasibility_rules,
    run_feasibility_assessment,
    get_engineering_defaults,
)
from app.services.feasibility.normalization import (
    normalise_assessment_payload,
    normalise_project_payload,
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
                normalised = normalise_assessment_payload(data)
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


@router.get("/defaults", response_model=EngineeringDefaultsResponse)
async def get_defaults(
    _: str = Depends(require_viewer),
) -> EngineeringDefaultsResponse:
    """Get global engineering defaults by jurisdiction."""
    return get_engineering_defaults()


@router.post("/rules", response_model=FeasibilityRulesResponse)
async def fetch_feasibility_rules(
    payload: dict[str, Any],
    _: str = Depends(require_viewer),
) -> FeasibilityRulesResponse:
    """Fetch applicable feasibility rules for the project."""
    normalised = normalise_project_payload(payload)
    project = NewFeasibilityProjectInput(**normalised)
    return generate_feasibility_rules(project)


@router.post("/assessment", response_model=FeasibilityAssessmentResponse)
async def submit_assessment(
    payload: dict[str, Any],
    _: str = Depends(require_viewer),
) -> FeasibilityAssessmentResponse:
    """Evaluate the feasibility assessment for the selected rules."""
    # Request model validation happens here via normaliser
    request = FeasibilityAssessmentRequest(**normalise_assessment_payload(payload))
    return run_feasibility_assessment(request)


__all__ = ["router"]
