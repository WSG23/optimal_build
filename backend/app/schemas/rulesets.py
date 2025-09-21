"""Lightweight schema representations for rule sets."""

from __future__ import annotations

from dataclasses import MISSING, dataclass, field, fields
from datetime import datetime
from typing import Any, Dict, List, Mapping, Optional, Type, TypeVar, get_args, get_origin, get_type_hints

T = TypeVar("T", bound="SerializableModel")


class SerializableModel:
    """Minimal dataclass-like model with ``model_validate`` helpers."""

    @classmethod
    def model_validate(cls: Type[T], data: Any, from_attributes: bool = False) -> T:
        """Create an instance from a mapping or attribute-bearing object."""

        if isinstance(data, cls):
            return data

        type_hints = get_type_hints(cls)
        if from_attributes and not isinstance(data, Mapping):
            source: Dict[str, Any] = {
                field_def.name: getattr(data, field_def.name, MISSING)
                for field_def in fields(cls)
            }
        elif isinstance(data, Mapping):
            source = dict(data)
        else:
            source = {}

        values: Dict[str, Any] = {}
        for field_def in fields(cls):
            raw = source.get(field_def.name, MISSING)
            if raw is MISSING:
                if field_def.default is not MISSING:
                    raw = field_def.default
                elif getattr(field_def, "default_factory", MISSING) is not MISSING:
                    raw = field_def.default_factory()  # type: ignore[call-arg]
                else:
                    raw = None
            annotation = type_hints.get(field_def.name, field_def.type)
            values[field_def.name] = cls._coerce_value(raw, annotation)
        return cls(**values)  # type: ignore[arg-type]

    @staticmethod
    def _coerce_value(value: Any, annotation: Any) -> Any:
        origin = get_origin(annotation)
        if origin in (list, List):
            args = get_args(annotation) or (Any,)
            inner = args[0]
            items = value or []
            return [SerializableModel._coerce_value(item, inner) for item in items]
        if origin in (dict, Dict):
            return dict(value) if value is not None else {}
        try:
            if isinstance(annotation, type) and issubclass(annotation, SerializableModel):
                return annotation.model_validate(value, from_attributes=not isinstance(value, Mapping))
        except TypeError:
            pass
        return value

    def model_dump(self, mode: str = "json") -> Dict[str, Any]:
        """Return a serialisable mapping of the model's fields."""

        payload: Dict[str, Any] = {}
        for field_def in fields(self):
            value = getattr(self, field_def.name)
            payload[field_def.name] = self._dump_value(value, mode)
        return payload

    @staticmethod
    def _dump_value(value: Any, mode: str) -> Any:
        if isinstance(value, SerializableModel):
            return value.model_dump(mode=mode)
        if isinstance(value, list):
            return [SerializableModel._dump_value(item, mode) for item in value]
        if isinstance(value, dict):
            return {key: SerializableModel._dump_value(val, mode) for key, val in value.items()}
        return value


@dataclass
class RuleCitation(SerializableModel):
    """Citation information for a rule."""

    text: str
    source: Optional[str] = None
    clause: Optional[str] = None
    url: Optional[str] = None


@dataclass
class RuleDefinition(SerializableModel):
    """Rule definition stored within a rule pack."""

    id: str
    title: Optional[str] = None
    description: Optional[str] = None
    applies_to: Optional[List[str]] = None
    predicate: Dict[str, Any] = field(default_factory=dict)
    citations: List[RuleCitation] = field(default_factory=list)


@dataclass
class RulePackResponse(SerializableModel):
    """Representation of a persisted rule pack."""

    id: int
    key: str
    jurisdiction: str
    authority: str
    topic: str
    version: str
    revision: int
    title: Optional[str] = None
    description: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    rules: List[RuleDefinition] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class RulePackListResponse(SerializableModel):
    """Payload returned by ``GET /rulesets``."""

    items: List[RulePackResponse]
    count: int


@dataclass
class PredicateTrace(SerializableModel):
    """Explainability trace for predicate evaluation."""

    type: str
    result: bool
    details: Dict[str, Any] = field(default_factory=dict)
    children: List["PredicateTrace"] = field(default_factory=list)


@dataclass
class GeometryEvaluationResult(SerializableModel):
    """Evaluation outcome for an individual geometry."""

    geometry_id: str
    passed: bool
    trace: PredicateTrace


@dataclass
class RuleValidationResult(SerializableModel):
    """Validation outcome for a rule."""

    rule_id: str
    title: Optional[str] = None
    description: Optional[str] = None
    passed: bool = False
    citations: List[RuleCitation] = field(default_factory=list)
    offending_geometry_ids: List[str] = field(default_factory=list)
    evaluations: List[GeometryEvaluationResult] = field(default_factory=list)


@dataclass
class RulesetValidationRequest(SerializableModel):
    """Request payload for ``POST /rulesets/validate``."""

    ruleset_id: int
    geometries: Dict[str, Dict[str, Any]]


@dataclass
class RulesetValidationResponse(SerializableModel):
    """Response payload from ``POST /rulesets/validate``."""

    ruleset: RulePackResponse
    valid: bool
    results: List[RuleValidationResult] = field(default_factory=list)


__all__ = [
    "RuleCitation",
    "RuleDefinition",
    "RulePackResponse",
    "RulePackListResponse",
    "PredicateTrace",
    "GeometryEvaluationResult",
    "RuleValidationResult",
    "RulesetValidationRequest",
    "RulesetValidationResponse",
]
