"""Normalization logic for feasibility payloads."""

from __future__ import annotations

from typing import Any

from app.schemas.feasibility import (
    FeasibilityAssessmentRequest,
    NewFeasibilityProjectInput,
)


def normalise_project_payload(data: dict[str, Any]) -> dict[str, Any]:
    """
    Normalise project payload using Pydantic models.
    Validates input types and keys, enforcing constraints.
    """
    model = NewFeasibilityProjectInput.model_validate(data)
    return model.model_dump()


def normalise_assessment_payload(data: dict[str, Any]) -> dict[str, Any]:
    """
    Normalise assessment payload using Pydantic models.
    Validates the entire structure including nested project and rule IDs.
    """
    model = FeasibilityAssessmentRequest.model_validate(data)
    return model.model_dump()
