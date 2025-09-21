"""Utilities for normalising free-form rule text into structured parameters."""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any, Callable, Dict, Iterable, List, Optional, Pattern


@dataclass
class NormalizedRule:
    """Structured representation of a rule extracted from a clause."""

    parameter_key: str
    operator: str
    value: Any
    unit: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    hints: List[str] = field(default_factory=list)

    def as_dict(self) -> Dict[str, Any]:
        """Return a serialisable representation suitable for persistence."""

        payload: Dict[str, Any] = {
            "parameter_key": self.parameter_key,
            "operator": self.operator,
            "value": self.value,
            "context": self.context,
            "hints": self.hints,
        }
        if self.unit:
            payload["unit"] = self.unit
        return payload


@dataclass
class RuleTemplate:
    """Template describing how to extract a structured rule from text."""

    parameter_key: str
    operator: str
    unit: Optional[str]
    pattern: Pattern[str]
    value_transform: Callable[[re.Match[str]], Any]
    hint_template: Optional[str] = None

    def build_rule(
        self, match: re.Match[str], *, context: Optional[Dict[str, Any]] = None
    ) -> NormalizedRule:
        """Create a :class:`NormalizedRule` instance from a regex match."""

        value = self.value_transform(match)
        hints: List[str] = []
        if self.hint_template:
            hints.append(self.hint_template.format(value=value))
        return NormalizedRule(
            parameter_key=self.parameter_key,
            operator=self.operator,
            value=value,
            unit=self.unit,
            context=context or {},
            hints=hints,
        )


class RuleNormalizer:
    """Normalise rule text using a library of templates."""

    def __init__(self) -> None:
        self._templates: List[RuleTemplate] = []
        self._register_default_templates()

    def register_template(self, template: RuleTemplate) -> None:
        """Register a template used for normalisation."""

        self._templates.append(template)

    def normalize(
        self, text: str, *, context: Optional[Dict[str, Any]] = None
    ) -> List[NormalizedRule]:
        """Extract structured rules from the provided text."""

        matches: List[NormalizedRule] = []
        for template in self._templates:
            for match in template.pattern.finditer(text):
                matches.append(template.build_rule(match, context=context))
        return matches

    @staticmethod
    def apply_overlays(
        attributes: Dict[str, Any], overlays: Iterable[str]
    ) -> Dict[str, Any]:
        """Persist overlays within a zoning layer attribute payload."""

        unique_overlays = list(dict.fromkeys(o for o in overlays if o))
        existing = attributes.get("overlays", [])
        if isinstance(existing, list):
            merged = list(dict.fromkeys([*existing, *unique_overlays]))
        else:
            merged = unique_overlays
        attributes["overlays"] = merged
        return attributes

    def _register_default_templates(self) -> None:
        """Seed the normaliser with the default template library."""

        # Parking minimum car spaces per unit
        parking_pattern = re.compile(
            r"(?P<value>\d+(?:\.\d+)?)\s*(?:car|parking)\s+spaces?\s+per\s+(?:dwelling|unit)",
            re.IGNORECASE,
        )

        def parking_transform(match: re.Match[str]) -> float:
            return float(match.group("value"))

        self.register_template(
            RuleTemplate(
                parameter_key="parking.min_car_spaces_per_unit",
                operator=">=",
                unit="spaces_per_unit",
                pattern=parking_pattern,
                value_transform=parking_transform,
                hint_template="Provide at least {value} parking spaces per dwelling unit.",
            )
        )

        # Accessibility ramp maximum slope ratio
        slope_pattern = re.compile(
            r"(?:maximum\s+ramp\s+slope|max(?:imum)?\s+slope)\D*(?P<num>\d+)\s*:?\s*(?P<den>\d+(?:\.\d+)?)",
            re.IGNORECASE,
        )

        def slope_transform(match: re.Match[str]) -> float:
            numerator = float(match.group("num"))
            denominator = float(match.group("den"))
            if denominator == 0:
                return 0.0
            return round(numerator / denominator, 6)

        self.register_template(
            RuleTemplate(
                parameter_key="accessibility.ramp.max_slope_ratio",
                operator="<=",
                unit="ratio",
                pattern=slope_pattern,
                value_transform=slope_transform,
                hint_template="Maximum ramp slope of {value} (rise/run).",
            )
        )


__all__ = [
    "NormalizedRule",
    "RuleTemplate",
    "RuleNormalizer",
]
