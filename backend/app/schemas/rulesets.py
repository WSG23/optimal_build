"""Schemas for rule pack management and validation APIs."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class RulePackSchema(BaseModel):
    """Serialized representation of a stored rule pack."""

    id: int
    slug: str
    name: str
    description: str | None = None
    jurisdiction: str
    authority: str | None = None
    version: int
    definition: dict[str, Any]
    metadata: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm_model(cls, obj: Any) -> RulePackSchema:
        """Create a RulePackSchema from an ORM model instance.

        This handles the mapping of metadata_json to metadata field.

        Args:
            obj: The ORM model instance to convert.

        Returns:
            A RulePackSchema instance.
        """
        data: dict[str, Any] = {}
        for name in cls.model_fields:
            if name == "metadata":
                if hasattr(obj, "metadata_json"):
                    value = obj.metadata_json
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


class RulePackSummary(BaseModel):
    """Compact metadata about a rule pack."""

    id: int
    slug: str
    name: str
    jurisdiction: str
    authority: str | None = None
    version: int
    description: str | None = None

    model_config = ConfigDict(from_attributes=True)


class RulesetValidationRequest(BaseModel):
    """Payload received when validating geometry against a rule pack."""

    ruleset_id: int | None = Field(default=None, ge=1)
    ruleset_slug: str | None = Field(default=None, min_length=1)
    ruleset_version: int | None = Field(default=None, ge=1)
    geometry: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _check_identifier(
        cls, values: RulesetValidationRequest
    ) -> RulesetValidationRequest:
        if values.ruleset_id is None and not values.ruleset_slug:
            raise ValueError("Either ruleset_id or ruleset_slug must be provided")
        return values


class ViolationFact(BaseModel):
    """Individual fact captured while evaluating a predicate."""

    field: str
    operator: str
    expected: Any = None
    actual: Any = None
    message: str | None = None


class ViolationDetail(BaseModel):
    """Explainability payload describing a rule violation."""

    entity_id: str
    messages: list[str] = Field(default_factory=list)
    facts: list[ViolationFact] = Field(default_factory=list)
    attributes: dict[str, Any] = Field(default_factory=dict)


class RuleEvaluationResult(BaseModel):
    """Outcome of evaluating a single rule against the geometry."""

    rule_id: str
    title: str | None = None
    target: str | None = None
    citation: dict[str, Any] | None = None
    passed: bool
    checked: int
    violations: list[ViolationDetail] = Field(default_factory=list)


class RulesetEvaluationSummary(BaseModel):
    """Aggregate metrics about a validation run."""

    total_rules: int
    evaluated_rules: int
    violations: int
    checked_entities: int


class RulesetValidationResponse(BaseModel):
    """Response returned by the validation endpoint."""

    ruleset: RulePackSummary
    results: list[RuleEvaluationResult]
    summary: RulesetEvaluationSummary
    citations: list[dict[str, Any]] = Field(default_factory=list)


class RulesetListResponse(BaseModel):
    """Paginated response for the rule pack catalogue."""

    items: list[RulePackSchema]
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
