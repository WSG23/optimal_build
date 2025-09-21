"""Tests for the rule normalisation helpers."""

from pytest import approx

from app.services.normalize import RuleNormalizer


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
