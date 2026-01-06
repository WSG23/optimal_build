"""Tests for normalize service.

Tests focus on NormalizedRule, RuleTemplate, and RuleNormalizer classes.
"""

from __future__ import annotations

import re



class TestNormalizedRule:
    """Test NormalizedRule dataclass."""

    def test_as_dict_basic(self):
        """Test as_dict returns expected structure."""
        from app.services.normalize import NormalizedRule

        rule = NormalizedRule(
            parameter_key="zoning.max_far",
            operator="<=",
            value=2.5,
            unit="ratio",
            context={"zone": "R1"},
            hints=["Max FAR is 2.5"],
        )

        result = rule.as_dict()

        assert result["parameter_key"] == "zoning.max_far"
        assert result["operator"] == "<="
        assert result["value"] == 2.5
        assert result["unit"] == "ratio"
        assert result["context"] == {"zone": "R1"}
        assert result["hints"] == ["Max FAR is 2.5"]

    def test_as_dict_without_unit(self):
        """Test as_dict excludes unit when None."""
        from app.services.normalize import NormalizedRule

        rule = NormalizedRule(
            parameter_key="test.key",
            operator="=",
            value=100,
            unit=None,
        )

        result = rule.as_dict()

        assert "unit" not in result

    def test_as_dict_with_empty_context(self):
        """Test as_dict with empty context and hints."""
        from app.services.normalize import NormalizedRule

        rule = NormalizedRule(
            parameter_key="test.key",
            operator=">=",
            value=5,
        )

        result = rule.as_dict()

        assert result["context"] == {}
        assert result["hints"] == []


class TestRuleTemplate:
    """Test RuleTemplate class."""

    def test_build_rule_basic(self):
        """Test build_rule creates NormalizedRule from match."""
        from app.services.normalize import RuleTemplate

        pattern = re.compile(r"max\s+(\d+)")

        def transform(match: re.Match[str]) -> int:
            return int(match.group(1))

        template = RuleTemplate(
            parameter_key="test.max",
            operator="<=",
            unit="units",
            pattern=pattern,
            value_transform=transform,
        )

        match = pattern.search("max 100")
        assert match is not None

        rule = template.build_rule(match)

        assert rule.parameter_key == "test.max"
        assert rule.operator == "<="
        assert rule.value == 100
        assert rule.unit == "units"

    def test_build_rule_with_hint_template(self):
        """Test build_rule applies hint template."""
        from app.services.normalize import RuleTemplate

        pattern = re.compile(r"height\s+(\d+)\s*m")

        def transform(match: re.Match[str]) -> int:
            return int(match.group(1))

        template = RuleTemplate(
            parameter_key="zoning.max_height",
            operator="<=",
            unit="m",
            pattern=pattern,
            value_transform=transform,
            hint_template="Maximum height is {value} meters.",
        )

        match = pattern.search("height 45 m")
        assert match is not None

        rule = template.build_rule(match)

        assert len(rule.hints) == 1
        assert rule.hints[0] == "Maximum height is 45 meters."

    def test_build_rule_with_context(self):
        """Test build_rule passes context to rule."""
        from app.services.normalize import RuleTemplate

        pattern = re.compile(r"(\d+)")

        template = RuleTemplate(
            parameter_key="test.value",
            operator="=",
            unit=None,
            pattern=pattern,
            value_transform=lambda m: int(m.group(1)),
        )

        match = pattern.search("value 42")
        assert match is not None

        context = {"source": "document.pdf", "page": 5}
        rule = template.build_rule(match, context=context)

        assert rule.context == context


class TestRuleNormalizer:
    """Test RuleNormalizer class."""

    def test_normalizer_has_default_templates(self):
        """Test RuleNormalizer registers default templates."""
        from app.services.normalize import RuleNormalizer

        normalizer = RuleNormalizer()

        # Should have some templates registered
        assert len(normalizer._templates) > 0

    def test_normalize_parking_rule(self):
        """Test normalizer extracts parking rule."""
        from app.services.normalize import RuleNormalizer

        normalizer = RuleNormalizer()

        text = "Provide 1.5 car spaces per dwelling unit."
        rules = normalizer.normalize(text)

        assert len(rules) >= 1
        parking_rule = next(
            (r for r in rules if r.parameter_key == "parking.min_car_spaces_per_unit"),
            None,
        )
        assert parking_rule is not None
        assert parking_rule.value == 1.5
        assert parking_rule.operator == ">="

    def test_normalize_far_rule(self):
        """Test normalizer extracts FAR/plot ratio rule."""
        from app.services.normalize import RuleNormalizer

        normalizer = RuleNormalizer()

        text = "Maximum gross plot ratio 2.8"
        rules = normalizer.normalize(text)

        assert len(rules) >= 1
        far_rule = next((r for r in rules if r.parameter_key == "zoning.max_far"), None)
        assert far_rule is not None
        assert far_rule.value == 2.8
        assert far_rule.operator == "<="

    def test_normalize_height_rule(self):
        """Test normalizer extracts building height rule."""
        from app.services.normalize import RuleNormalizer

        normalizer = RuleNormalizer()

        text = "Maximum building height 45 metres"
        rules = normalizer.normalize(text)

        height_rule = next(
            (r for r in rules if r.parameter_key == "zoning.max_building_height_m"),
            None,
        )
        assert height_rule is not None
        assert height_rule.value == 45.0
        assert height_rule.unit == "m"

    def test_normalize_ramp_slope_rule(self):
        """Test normalizer extracts ramp slope rule."""
        from app.services.normalize import RuleNormalizer

        normalizer = RuleNormalizer()

        text = "Maximum ramp slope 1:12"
        rules = normalizer.normalize(text)

        slope_rule = next(
            (
                r
                for r in rules
                if r.parameter_key == "accessibility.ramp.max_slope_ratio"
            ),
            None,
        )
        assert slope_rule is not None
        assert abs(slope_rule.value - 1 / 12) < 0.0001
        assert slope_rule.operator == "<="

    def test_normalize_site_coverage_percent(self):
        """Test normalizer extracts site coverage percentage."""
        from app.services.normalize import RuleNormalizer

        normalizer = RuleNormalizer()

        text = "Maximum site coverage 60%"
        rules = normalizer.normalize(text)

        coverage_rule = next(
            (r for r in rules if r.parameter_key == "zoning.site_coverage.max_percent"),
            None,
        )
        assert coverage_rule is not None
        assert coverage_rule.value == 60.0

    def test_normalize_site_coverage_decimal(self):
        """Test normalizer converts decimal site coverage to percent."""
        from app.services.normalize import RuleNormalizer

        normalizer = RuleNormalizer()

        text = "Site coverage limited to 0.45"
        rules = normalizer.normalize(text)

        coverage_rule = next(
            (r for r in rules if r.parameter_key == "zoning.site_coverage.max_percent"),
            None,
        )
        assert coverage_rule is not None
        assert coverage_rule.value == 45.0  # Converted from 0.45

    def test_normalize_front_setback(self):
        """Test normalizer extracts front setback rule."""
        from app.services.normalize import RuleNormalizer

        normalizer = RuleNormalizer()

        text = "Minimum front setback 7.5 metres"
        rules = normalizer.normalize(text)

        setback_rule = next(
            (r for r in rules if r.parameter_key == "zoning.setback.front_min_m"),
            None,
        )
        assert setback_rule is not None
        assert setback_rule.value == 7.5
        assert setback_rule.operator == ">="

    def test_normalize_with_context(self):
        """Test normalizer passes context to extracted rules."""
        from app.services.normalize import RuleNormalizer

        normalizer = RuleNormalizer()

        context = {"zone": "B2", "source": "MP2019"}
        text = "Maximum plot ratio 3.5"
        rules = normalizer.normalize(text, context=context)

        assert len(rules) >= 1
        assert rules[0].context == context

    def test_normalize_multiple_rules(self):
        """Test normalizer extracts multiple rules from text."""
        from app.services.normalize import RuleNormalizer

        normalizer = RuleNormalizer()

        text = """
        Maximum gross plot ratio 2.5.
        Maximum building height 36 metres.
        Minimum front setback 6m.
        """
        rules = normalizer.normalize(text)

        # Should extract at least 3 rules
        assert len(rules) >= 3

    def test_normalize_no_matches(self):
        """Test normalizer returns empty list when no matches."""
        from app.services.normalize import RuleNormalizer

        normalizer = RuleNormalizer()

        text = "This text has no zoning rules."
        rules = normalizer.normalize(text)

        assert rules == []

    def test_register_template(self):
        """Test register_template adds custom template."""
        from app.services.normalize import RuleNormalizer, RuleTemplate

        normalizer = RuleNormalizer()
        initial_count = len(normalizer._templates)

        custom_pattern = re.compile(r"custom_value:\s*(\d+)")
        custom_template = RuleTemplate(
            parameter_key="custom.value",
            operator="=",
            unit=None,
            pattern=custom_pattern,
            value_transform=lambda m: int(m.group(1)),
        )

        normalizer.register_template(custom_template)

        assert len(normalizer._templates) == initial_count + 1

        # Verify new template works
        text = "custom_value: 42"
        rules = normalizer.normalize(text)
        custom_rule = next(
            (r for r in rules if r.parameter_key == "custom.value"), None
        )
        assert custom_rule is not None
        assert custom_rule.value == 42


class TestApplyOverlays:
    """Test RuleNormalizer.apply_overlays static method."""

    def test_apply_overlays_to_empty_attributes(self):
        """Test apply_overlays adds overlays to empty attributes."""
        from app.services.normalize import RuleNormalizer

        attributes: dict = {}
        overlays = ["heritage", "conservation"]

        result = RuleNormalizer.apply_overlays(attributes, overlays)

        assert result["overlays"] == ["heritage", "conservation"]

    def test_apply_overlays_merges_existing(self):
        """Test apply_overlays merges with existing overlays."""
        from app.services.normalize import RuleNormalizer

        attributes = {"overlays": ["flood_zone"]}
        overlays = ["heritage", "conservation"]

        result = RuleNormalizer.apply_overlays(attributes, overlays)

        assert "flood_zone" in result["overlays"]
        assert "heritage" in result["overlays"]
        assert "conservation" in result["overlays"]

    def test_apply_overlays_deduplicates(self):
        """Test apply_overlays removes duplicates."""
        from app.services.normalize import RuleNormalizer

        attributes = {"overlays": ["heritage", "flood_zone"]}
        overlays = ["heritage", "conservation", "heritage"]

        result = RuleNormalizer.apply_overlays(attributes, overlays)

        # Count occurrences of heritage
        heritage_count = result["overlays"].count("heritage")
        assert heritage_count == 1

    def test_apply_overlays_filters_empty_strings(self):
        """Test apply_overlays filters out empty overlay strings."""
        from app.services.normalize import RuleNormalizer

        attributes: dict = {}
        overlays = ["heritage", "", "conservation", ""]

        result = RuleNormalizer.apply_overlays(attributes, overlays)

        assert "" not in result["overlays"]
        assert result["overlays"] == ["heritage", "conservation"]

    def test_apply_overlays_handles_non_list_existing(self):
        """Test apply_overlays handles non-list existing overlays."""
        from app.services.normalize import RuleNormalizer

        attributes = {"overlays": "not_a_list"}
        overlays = ["heritage"]

        result = RuleNormalizer.apply_overlays(attributes, overlays)

        assert result["overlays"] == ["heritage"]
