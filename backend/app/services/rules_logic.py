"""Pure utility functions for transforming rule data."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable, Mapping, Protocol, Sequence

from app.services.normalize import NormalizedRule, RuleNormalizer


class RuleLike(Protocol):
    """Protocol describing the attributes required from a rule instance."""

    id: int
    parameter_key: str
    operator: str
    value: Any
    unit: str | None
    jurisdiction: str | None
    authority: str | None
    topic: str | None
    review_status: str | None
    is_published: bool
    applicability: Any
    notes: str | None


class ReviewableRule(RuleLike, Protocol):
    """Protocol describing the mutable fields updated during review."""

    reviewer: str | None
    reviewed_at: datetime | None
    published_at: datetime | None
    notes: str | None


class ZoningLayerLike(Protocol):
    """Protocol describing the shape of zoning layer records."""

    zone_code: str
    attributes: Mapping[str, Any] | None


def _ensure_mapping(value: Any) -> Mapping[str, Any] | None:
    if isinstance(value, Mapping):
        return value
    return None


def _unique(items: Iterable[Any]) -> list[str]:
    seen: dict[str, None] = {}
    for item in items:
        if item is None:
            continue
        text = str(item)
        if text and text not in seen:
            seen[text] = None
    return list(seen.keys())


def get_rule_zone_code(rule: RuleLike) -> str | None:
    """Return the first zone code declared in the rule applicability."""

    applicability = _ensure_mapping(rule.applicability) or {}
    zone = applicability.get("zone_code") or applicability.get("zone")
    if isinstance(zone, Sequence) and not isinstance(zone, (str, bytes, bytearray)):
        for candidate in zone:
            if candidate:
                return str(candidate)
        return None
    if zone:
        return str(zone)
    return None


def collect_layer_metadata(layers: Iterable[ZoningLayerLike]) -> tuple[list[str], list[str]]:
    """Aggregate overlays and advisory hints from a set of zoning layers."""

    overlays: list[str] = []
    hints: list[str] = []
    for layer in layers:
        attributes = _ensure_mapping(layer.attributes) or {}
        raw_overlays = attributes.get("overlays")
        if isinstance(raw_overlays, Sequence) and not isinstance(raw_overlays, (str, bytes, bytearray)):
            overlays.extend(str(value) for value in raw_overlays if value)
        raw_hints = attributes.get("advisory_hints")
        if isinstance(raw_hints, Sequence) and not isinstance(raw_hints, (str, bytes, bytearray)):
            hints.extend(str(value) for value in raw_hints if value)
    return _unique(overlays), _unique(hints)


def serialise_rule(
    rule: RuleLike,
    normalizer: RuleNormalizer,
    zoning_lookup: Mapping[str, Sequence[ZoningLayerLike]],
) -> dict[str, Any]:
    """Build the API payload for a rule using normalised text and zoning data."""

    zone_code = get_rule_zone_code(rule)
    overlays: list[str] = []
    hints: list[str] = []
    if zone_code and zone_code in zoning_lookup:
        overlays, hints = collect_layer_metadata(zoning_lookup[zone_code])

    normalized: list[NormalizedRule] = []
    if rule.notes:
        normalized = normalizer.normalize(rule.notes, context={"rule_id": rule.id})
    if not normalized:
        fragment = f"{rule.parameter_key} {rule.operator} {rule.value}"
        normalized = normalizer.normalize(fragment, context={"rule_id": rule.id})

    hints.extend(hint for match in normalized for hint in match.hints)
    overlays = _unique(overlays)
    hints = _unique(hints)

    return {
        "id": rule.id,
        "parameter_key": rule.parameter_key,
        "operator": rule.operator,
        "value": rule.value,
        "unit": rule.unit,
        "jurisdiction": rule.jurisdiction,
        "authority": rule.authority,
        "topic": rule.topic,
        "review_status": rule.review_status,
        "is_published": rule.is_published,
        "overlays": overlays,
        "advisory_hints": hints,
        "normalized": [match.as_dict() for match in normalized],
    }


def apply_review_action(
    rule: ReviewableRule,
    action: str,
    *,
    reviewer: str | None = None,
    notes: str | None = None,
    timestamp: datetime | None = None,
) -> None:
    """Mutate the rule according to the requested review action."""

    current_time = timestamp or datetime.now(timezone.utc)
    action_key = action.lower()
    if action_key == "approve":
        rule.review_status = "approved"
        rule.reviewed_at = current_time
    elif action_key == "reject":
        rule.review_status = "rejected"
        rule.reviewed_at = current_time
    elif action_key == "publish":
        rule.is_published = True
        rule.published_at = current_time
        rule.review_status = "approved"
        rule.reviewed_at = current_time
    else:  # pragma: no cover - guarded by pydantic schema in production
        raise ValueError(f"Unsupported review action: {action}")

    if reviewer is not None:
        rule.reviewer = reviewer
    if notes is not None:
        rule.notes = notes


__all__ = [
    "RuleLike",
    "ReviewableRule",
    "ZoningLayerLike",
    "apply_review_action",
    "collect_layer_metadata",
    "get_rule_zone_code",
    "serialise_rule",
]
