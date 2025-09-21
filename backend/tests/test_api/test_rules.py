"""Offline-friendly tests for rule serialization and buildable screening."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import pytest

from app.services.buildable_screening import (
    compose_buildable_response,
    zone_code_from_geometry,
    zone_code_from_parcel,
)
from app.services.normalize import RuleNormalizer
from app.services.rules_logic import apply_review_action, serialise_rule


@dataclass
class DummyLayer:
    zone_code: str
    attributes: Dict[str, Any] | None = None


@dataclass
class DummyParcel:
    bounds_json: Dict[str, Any] | None = None


@dataclass
class DummyRule:
    id: int
    parameter_key: str
    operator: str
    value: str
    unit: Optional[str]
    jurisdiction: str
    authority: str
    topic: str
    applicability: Dict[str, Any] | None = None
    notes: Optional[str] = None
    review_status: str = "needs_review"
    is_published: bool = False
    reviewer: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    published_at: Optional[datetime] = None


@pytest.fixture
def normalizer() -> RuleNormalizer:
    return RuleNormalizer()


def test_serialise_rule_includes_overlays_and_hints(normalizer: RuleNormalizer) -> None:
    rule = DummyRule(
        id=1,
        parameter_key="parking.min_car_spaces_per_unit",
        operator=">=",
        value="1.5",
        unit="spaces_per_unit",
        jurisdiction="SG",
        authority="URA",
        topic="zoning",
        applicability={"zone_code": "R2"},
        notes="Provide 1.5 parking spaces per unit and ensure maximum ramp slope is 1:12.",
    )
    layer = DummyLayer(
        zone_code="R2",
        attributes={
            "overlays": ["heritage"],
            "advisory_hints": ["Heritage impact assessment required."],
        },
    )

    payload = serialise_rule(rule, normalizer, {"R2": [layer]})

    assert payload["overlays"] == ["heritage"]
    assert "Heritage impact assessment required." in payload["advisory_hints"]
    assert any("parking" in hint.lower() for hint in payload["advisory_hints"])
    assert any("slope" in hint.lower() for hint in payload["advisory_hints"])


def test_buildable_screening_supports_address_and_geojson() -> None:
    parcel = DummyParcel(bounds_json={"zone_code": "R2"})
    geometry = {"type": "Feature", "properties": {"zone_code": "R2"}}
    layers: List[DummyLayer] = [
        DummyLayer(
            zone_code="R2",
            attributes={
                "overlays": ["heritage"],
                "advisory_hints": ["Heritage impact assessment required."],
            },
        )
    ]

    zone_from_parcel = zone_code_from_parcel(parcel)
    assert zone_from_parcel == "R2"

    address_summary = compose_buildable_response(
        address="123 Example Ave",
        geometry=None,
        zone_code=zone_from_parcel,
        layers=layers,
    )
    assert address_summary["input_kind"] == "address"
    assert address_summary["zone_code"] == "R2"
    assert "heritage" in address_summary["overlays"]

    zone_from_geometry = zone_code_from_geometry(geometry)
    assert zone_from_geometry == "R2"

    geometry_summary = compose_buildable_response(
        address=None,
        geometry=geometry,
        zone_code=zone_from_geometry,
        layers=layers,
    )
    assert geometry_summary["input_kind"] == "geometry"
    assert geometry_summary["zone_code"] == "R2"
    assert geometry_summary["advisory_hints"] == address_summary["advisory_hints"]


def test_apply_review_action_publish_updates_rule(normalizer: RuleNormalizer) -> None:
    rule = DummyRule(
        id=7,
        parameter_key="parking.min_car_spaces_per_unit",
        operator=">=",
        value="1.5",
        unit="spaces_per_unit",
        jurisdiction="SG",
        authority="URA",
        topic="zoning",
        applicability={"zone_code": "R2"},
    )

    now = datetime(2024, 1, 1, tzinfo=timezone.utc)
    apply_review_action(
        rule,
        "publish",
        reviewer="Casey",
        notes="Ready",
        timestamp=now,
    )

    assert rule.is_published is True
    assert rule.review_status == "approved"
    assert rule.reviewer == "Casey"
    assert rule.notes == "Ready"
    assert rule.published_at == now
    assert rule.reviewed_at == now

    payload = serialise_rule(rule, normalizer, {"R2": []})
    assert payload["is_published"] is True
    assert payload["review_status"] == "approved"
