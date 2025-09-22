"""Tests for the rule normalisation helpers."""

from pytest import approx

import pytest

pytest.importorskip("sqlalchemy")

from app.services.normalize import NormalizedRule, RuleNormalizer


def test_rule_normalizer_extracts_parking_and_slope() -> None:
    normalizer = RuleNormalizer()
    text = (
        "Residential towers shall provide 1.5 parking spaces per unit and the "
        "maximum ramp slope is 1:12 for accessibility compliance."
    )
    matches = normalizer.normalize(text)
    assert any(
        match.parameter_key == "parking.min_car_spaces_per_unit" and match.value == 1.5
        for match in matches
    )
    assert any(
        match.parameter_key == "accessibility.ramp.max_slope_ratio"
        and match.value == approx(1 / 12, rel=1e-3)
        for match in matches
    )


def test_apply_overlays_merges_unique_values() -> None:
    attributes = {"overlays": ["heritage", "coastal"]}
    normalizer = RuleNormalizer()
    updated = normalizer.apply_overlays(attributes, ["coastal", "noise"])
    assert updated["overlays"] == ["heritage", "coastal", "noise"]


def test_rule_normalizer_extracts_sg_zoning_metrics() -> None:
    normalizer = RuleNormalizer()
    text = (
        "The URA Master Plan specifies a maximum gross plot ratio of 3.5. "
        "Building height shall not exceed 120 metres within the precinct. "
        "Site coverage must not exceed 0.65 for new developments. "
        "A minimum front setback of 7.5m is required along arterial roads."
    )
    matches = normalizer.normalize(text)

    def _find(parameter_key: str) -> NormalizedRule:
        for match in matches:
            if match.parameter_key == parameter_key:
                return match
        raise AssertionError(f"Expected rule for {parameter_key!r} not found")

    far_rule = _find("zoning.max_far")
    assert far_rule.value == approx(3.5)
    assert far_rule.unit == "ratio"
    assert any("plot ratio" in hint.lower() for hint in far_rule.hints)

    height_rule = _find("zoning.max_building_height_m")
    assert height_rule.value == approx(120)
    assert height_rule.unit == "m"
    assert any("height" in hint.lower() for hint in height_rule.hints)

    site_coverage_rule = _find("zoning.site_coverage.max_percent")
    assert site_coverage_rule.value == approx(65.0)
    assert site_coverage_rule.unit == "percent"
    assert any("site coverage" in hint.lower() for hint in site_coverage_rule.hints)

    setback_rule = _find("zoning.setback.front_min_m")
    assert setback_rule.value == approx(7.5)
    assert setback_rule.unit == "m"
    assert any("setback" in hint.lower() for hint in setback_rule.hints)
