"""Schemas for rule pack management and validation APIs."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, model_validator


class RulePackSchema(BaseModel):
    """Serialized representation of a stored rule pack."""

    id: int
    slug: str
    name: str
    description: Optional[str] = None
    jurisdiction: str
    authority: Optional[str] = None
    version: int
    definition: Dict[str, Any]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic configuration."""

        from_attributes = True

    @classmethod
    def model_validate(
        cls,
        obj: Any,
        *,
        from_attributes: bool = False,
    ) -> "RulePackSchema":
        if from_attributes and not isinstance(obj, dict):
            data: Dict[str, Any] = {}
            for name in cls.model_fields:
                if name == "metadata":
                    if hasattr(obj, "metadata_json"):
                        value = getattr(obj, "metadata_json")
                    else:
                        value = getattr(obj, "metadata", {})
                    if isinstance(value, dict):
                        data[name] = dict(value)
                    else:
                        data[name] = {}
                    continue
                if hasattr(obj, name):
                    data[name] = getattr(obj, name)
            return cls(**data)
        return super().model_validate(obj, from_attributes=from_attributes)


class RulePackSummary(BaseModel):
    """Compact metadata about a rule pack."""

    id: int
    slug: str
    name: str
    jurisdiction: str
    authority: Optional[str] = None
    version: int
    description: Optional[str] = None

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class RulesetValidationRequest(BaseModel):
    """Payload received when validating geometry against a rule pack."""

    ruleset_id: Optional[int] = Field(default=None, ge=1)
    ruleset_slug: Optional[str] = Field(default=None, min_length=1)
    ruleset_version: Optional[int] = Field(default=None, ge=1)
    geometry: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _check_identifier(cls, values: "RulesetValidationRequest") -> "RulesetValidationRequest":
        if values.ruleset_id is None and not values.ruleset_slug:
            raise ValueError("Either ruleset_id or ruleset_slug must be provided")
        return values


class ViolationFact(BaseModel):
    """Individual fact captured while evaluating a predicate."""

    field: str
    operator: str
    expected: Any = None
    actual: Any = None
    message: Optional[str] = None


class ViolationDetail(BaseModel):
    """Explainability payload describing a rule violation."""

    entity_id: str
    messages: List[str] = Field(default_factory=list)
    facts: List[ViolationFact] = Field(default_factory=list)
    attributes: Dict[str, Any] = Field(default_factory=dict)


class RuleEvaluationResult(BaseModel):
    """Outcome of evaluating a single rule against the geometry."""

    rule_id: str
    title: Optional[str] = None
    target: Optional[str] = None
    citation: Optional[Dict[str, Any]] = None
    passed: bool
    checked: int
    violations: List[ViolationDetail] = Field(default_factory=list)


class RulesetEvaluationSummary(BaseModel):
    """Aggregate metrics about a validation run."""

    total_rules: int
    evaluated_rules: int
    violations: int
    checked_entities: int


class RulesetValidationResponse(BaseModel):
    """Response returned by the validation endpoint."""

    ruleset: RulePackSummary
    results: List[RuleEvaluationResult]
    summary: RulesetEvaluationSummary
    citations: List[Dict[str, Any]] = Field(default_factory=list)


class RulesetListResponse(BaseModel):
    """Paginated response for the rule pack catalogue."""

    items: List[RulePackSchema]
    count: int


__all__ = [
    "RulePackSchema",
    "RulePackSummary",
    "RulesetEvaluationSummary",
    "RulesetListResponse",
    "RulesetValidationRequest",
    "RulesetValidationResponse",
    "RuleEvaluationResult",
    "ViolationDetail",
    "ViolationFact",
]
