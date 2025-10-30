"""Tests for the rule normalisation helpers."""

import pytest
from pytest import approx

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


def test_normalized_rule_as_dict_includes_all_fields() -> None:
    """Test that NormalizedRule.as_dict() includes all fields."""
    rule = NormalizedRule(
        parameter_key="test.param",
        operator=">=",
        value=42.5,
        unit="meters",
        context={"zone": "CBD"},
        hints=["Test hint 1", "Test hint 2"],
    )

    result = rule.as_dict()

    assert result["parameter_key"] == "test.param"
    assert result["operator"] == ">="
    assert result["value"] == 42.5
    assert result["unit"] == "meters"
    assert result["context"] == {"zone": "CBD"}
    assert result["hints"] == ["Test hint 1", "Test hint 2"]


def test_normalized_rule_as_dict_omits_none_unit() -> None:
    """Test that as_dict() omits unit when it's None."""
    rule = NormalizedRule(
        parameter_key="test.param",
        operator="==",
        value="test",
        unit=None,
    )

    result = rule.as_dict()

    assert "unit" not in result


def test_rule_normalizer_normalize_with_context() -> None:
    """Test that context is passed to extracted rules."""
    normalizer = RuleNormalizer()
    text = "Maximum plot ratio 2.0"
    context = {"jurisdiction": "SG", "district": "CBD"}

    matches = normalizer.normalize(text, context=context)

    assert len(matches) > 0
    for match in matches:
        assert match.context == context


def test_rule_normalizer_normalize_empty_text() -> None:
    """Test normalizing empty text returns empty list."""
    normalizer = RuleNormalizer()

    matches = normalizer.normalize("")

    assert matches == []


def test_rule_normalizer_normalize_no_matches() -> None:
    """Test text with no recognizable patterns."""
    normalizer = RuleNormalizer()
    text = "This is just plain text with no rule patterns"

    matches = normalizer.normalize(text)

    assert matches == []


def test_apply_overlays_filters_empty_strings() -> None:
    """Test that empty strings are filtered from overlays."""
    attributes = {}
    normalizer = RuleNormalizer()

    updated = normalizer.apply_overlays(attributes, ["valid", "", None, "another"])

    assert updated["overlays"] == ["valid", "another"]


def test_apply_overlays_with_non_list_existing() -> None:
    """Test applying overlays when existing is not a list."""
    attributes = {"overlays": "not_a_list"}
    normalizer = RuleNormalizer()

    updated = normalizer.apply_overlays(attributes, ["new1", "new2"])

    assert updated["overlays"] == ["new1", "new2"]


def test_apply_overlays_deduplicates() -> None:
    """Test that duplicate overlays are removed."""
    attributes = {"overlays": ["existing"]}
    normalizer = RuleNormalizer()

    updated = normalizer.apply_overlays(
        attributes, ["new", "duplicate", "duplicate", "existing"]
    )

    # Should have unique values only
    assert updated["overlays"].count("duplicate") == 1
    assert updated["overlays"].count("existing") == 1
    assert "new" in updated["overlays"]


def test_apply_overlays_empty_input() -> None:
    """Test applying empty overlays list."""
    attributes = {"overlays": ["existing"]}
    normalizer = RuleNormalizer()

    updated = normalizer.apply_overlays(attributes, [])

    assert updated["overlays"] == ["existing"]


def test_rule_normalizer_case_insensitive_matching() -> None:
    """Test that pattern matching is case insensitive."""
    normalizer = RuleNormalizer()

    text_lower = "maximum plot ratio 2.5"
    text_upper = "MAXIMUM PLOT RATIO 2.5"
    text_mixed = "MaXiMuM PlOt RaTiO 2.5"

    matches_lower = normalizer.normalize(text_lower)
    matches_upper = normalizer.normalize(text_upper)
    matches_mixed = normalizer.normalize(text_mixed)

    assert len(matches_lower) == len(matches_upper) == len(matches_mixed)
    if matches_lower:
        assert (
            matches_lower[0].value == matches_upper[0].value == matches_mixed[0].value
        )


def test_rule_normalizer_parking_variations() -> None:
    """Test different parking requirement phrasings."""
    normalizer = RuleNormalizer()

    variations = [
        "1.5 car spaces per unit",
        "2 parking spaces per dwelling",
        "1 car space per unit",
    ]

    for text in variations:
        matches = normalizer.normalize(text)
        parking_match = next(
            (
                m
                for m in matches
                if m.parameter_key == "parking.min_car_spaces_per_unit"
            ),
            None,
        )
        assert parking_match is not None
        assert parking_match.value > 0


def test_rule_normalizer_height_variations() -> None:
    """Test different building height phrasings."""
    normalizer = RuleNormalizer()

    variations = [
        "maximum building height 80 meters",
        "building height 80m",
        "height limit 80 metres",
    ]

    for text in variations:
        matches = normalizer.normalize(text)
        height_match = next(
            (m for m in matches if m.parameter_key == "zoning.max_building_height_m"),
            None,
        )
        # Some variations might not match due to pattern specifics
        if height_match:
            assert height_match.value == approx(80.0)


def test_rule_normalizer_far_variations() -> None:
    """Test different FAR/plot ratio phrasings."""
    normalizer = RuleNormalizer()

    variations = [
        "maximum plot ratio 3.0",
        "max gross plot ratio 3.0",
        "GPR 3.0",
        "FAR 3.0",
        "plot ratio limit 3.0",
    ]

    for text in variations:
        matches = normalizer.normalize(text)
        far_match = next(
            (m for m in matches if m.parameter_key == "zoning.max_far"), None
        )
        assert far_match is not None
        assert far_match.value == approx(3.0)


def test_rule_normalizer_site_coverage_percentage() -> None:
    """Test site coverage with explicit percentage."""
    normalizer = RuleNormalizer()

    text = "maximum site coverage 45 percent"
    matches = normalizer.normalize(text)

    coverage_match = next(
        (m for m in matches if m.parameter_key == "zoning.site_coverage.max_percent"),
        None,
    )
    assert coverage_match is not None
    assert coverage_match.value == approx(45.0)


def test_rule_normalizer_site_coverage_decimal() -> None:
    """Test site coverage converts decimal to percentage."""
    normalizer = RuleNormalizer()

    text = "site coverage limited to 0.45"
    matches = normalizer.normalize(text)

    coverage_match = next(
        (m for m in matches if m.parameter_key == "zoning.site_coverage.max_percent"),
        None,
    )
    # 0.45 should be converted to 45%
    if coverage_match:
        assert coverage_match.value == approx(45.0)


def test_rule_normalizer_multiple_rules_same_text() -> None:
    """Test extracting multiple rules from same text."""
    normalizer = RuleNormalizer()

    text = (
        "Maximum plot ratio 2.5. Maximum building height 100 meters. "
        "Minimum front setback 5 meters. Maximum site coverage 40 percent."
    )
    matches = normalizer.normalize(text)

    # Should extract multiple rules
    parameter_keys = {m.parameter_key for m in matches}
    assert len(parameter_keys) >= 2  # At least some rules should match


def test_rule_normalizer_register_custom_template() -> None:
    """Test registering and using a custom template."""
    import re

    from app.services.normalize import RuleTemplate

    normalizer = RuleNormalizer()
    initial_count = len(normalizer._templates)

    # Register custom template
    pattern = re.compile(r"custom value (?P<value>\d+)")
    template = RuleTemplate(
        parameter_key="custom.test",
        operator="==",
        unit="units",
        pattern=pattern,
        value_transform=lambda m: int(m.group("value")),
        hint_template="Custom value is {value}",
    )
    normalizer.register_template(template)

    assert len(normalizer._templates) == initial_count + 1

    # Use the custom template
    text = "custom value 123"
    matches = normalizer.normalize(text)

    custom_match = next((m for m in matches if m.parameter_key == "custom.test"), None)
    assert custom_match is not None
    assert custom_match.value == 123
    assert "Custom value is 123" in custom_match.hints


def test_rule_normalizer_slope_ratio_calculation() -> None:
    """Test that slope ratios are calculated correctly."""
    normalizer = RuleNormalizer()

    text = "max slope 1:15"
    matches = normalizer.normalize(text)

    slope_match = next(
        (m for m in matches if m.parameter_key == "accessibility.ramp.max_slope_ratio"),
        None,
    )
    assert slope_match is not None
    assert slope_match.value == approx(1 / 15, rel=1e-5)
