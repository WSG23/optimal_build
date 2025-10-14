"""Developer property condition assessment heuristics."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.property import Property, PropertyType


@dataclass(slots=True)
class ConditionSystem:
    """Represents the condition of a building subsystem."""

    name: str
    rating: str
    score: int
    notes: str
    recommended_actions: List[str]


@dataclass(slots=True)
class ConditionAssessment:
    """Aggregated condition assessment for a property."""

    property_id: UUID
    overall_score: int
    overall_rating: str
    risk_level: str
    summary: str
    scenario_context: Optional[str]
    systems: List[ConditionSystem]
    recommended_actions: List[str]


class DeveloperConditionService:
    """Provide developer-friendly property condition assessments."""

    @staticmethod
    async def generate_assessment(
        session: AsyncSession,
        property_id: UUID,
        scenario: Optional[str] = None,
    ) -> ConditionAssessment:
        """Generate a heuristic condition assessment for a property."""

        property_record = await session.get(Property, property_id)
        if property_record is None:
            raise ValueError("Property not found")

        age_score, age_band = _calculate_age_score(property_record)
        structure_score = _calculate_structure_score(property_record)
        systems_score = _calculate_systems_score(property_record)

        overall_score = round((age_score + structure_score + systems_score) / 3)
        overall_rating = _score_to_rating(overall_score)
        risk_level = _determine_risk_level(overall_rating)

        scenario_context = (
            _describe_scenario_context(property_record, scenario) if scenario else None
        )

        systems = [
            _build_structure_system(property_record, structure_score),
            _build_services_system(property_record, systems_score),
            _build_compliance_system(property_record, age_band),
        ]
        recommended_actions = _build_action_plan(
            property_record, overall_rating, scenario
        )

        summary = _build_summary(
            property_record, overall_rating, risk_level, scenario_context
        )

        return ConditionAssessment(
            property_id=property_id,
            overall_score=overall_score,
            overall_rating=overall_rating,
            risk_level=risk_level,
            summary=summary,
            scenario_context=scenario_context,
            systems=systems,
            recommended_actions=recommended_actions,
        )


def _calculate_age_score(property_record: Property) -> tuple[int, str]:
    """Score the building age and return score plus age band label."""
    current_year = date.today().year
    if property_record.year_built:
        age = max(current_year - int(property_record.year_built), 0)
    else:
        age = 25  # assume mid-life when unknown

    if age < 10:
        return 90, "new"
    if age < 25:
        return 80, "mid_life"
    if age < 40:
        return 65, "ageing"
    if age < 60:
        return 55, "late_life"
    return 45, "legacy"


def _calculate_structure_score(property_record: Property) -> int:
    """Approximate structural condition using property type + storeys."""
    floors = property_record.floors_above_ground or 0
    if property_record.property_type == PropertyType.OFFICE:
        baseline = 75
    elif property_record.property_type == PropertyType.MIXED_USE:
        baseline = 70
    else:
        baseline = 65

    if floors > 35:
        baseline -= 5
    if floors > 50:
        baseline -= 8

    if property_record.building_height_m and property_record.building_height_m > 200:
        baseline -= 5

    return max(40, min(90, baseline))


def _calculate_systems_score(property_record: Property) -> int:
    """Estimate M&E systems condition based on building age/usage."""
    _, age_band = _calculate_age_score(property_record)
    score_map = {
        "new": 88,
        "mid_life": 78,
        "ageing": 68,
        "late_life": 58,
        "legacy": 50,
    }
    score = score_map.get(age_band, 70)

    if property_record.status and property_record.status.name.lower() in {
        "existing",
        "occupied",
    }:
        score -= 2  # assume live load adds wear

    return max(45, score)


def _score_to_rating(score: int) -> str:
    """Convert numeric score into developer-friendly rating band."""
    if score >= 85:
        return "A"
    if score >= 75:
        return "B"
    if score >= 65:
        return "C"
    if score >= 55:
        return "D"
    return "E"


def _determine_risk_level(rating: str) -> str:
    """Translate rating into a simple risk label."""
    mapping = {
        "A": "low",
        "B": "moderate",
        "C": "elevated",
        "D": "high",
        "E": "critical",
    }
    return mapping.get(rating, "moderate")


def _describe_scenario_context(
    property_record: Property, scenario: Optional[str]
) -> Optional[str]:
    """Provide contextual messaging for the selected development scenario."""
    if not scenario:
        return None

    scenario = scenario.lower()
    if scenario == "existing_building":
        return "Focus on phased upgrade works while maintaining operations."
    if scenario == "heritage_property":
        return "Coordinate with conservation guidelines before intrusive works."
    if scenario == "underused_asset":
        return "Prioritise adaptive reuse strategies aligned with target tenants."
    if scenario == "mixed_use_redevelopment":
        return "Plan for full strip-out and structural strengthening for vertical expansion."
    if scenario == "raw_land":
        return "Existing condition insights inform demolition budgeting and site formation."
    return None


def _build_structure_system(
    property_record: Property, structure_score: int
) -> ConditionSystem:
    """Construct structural system assessment details."""
    rating = _score_to_rating(structure_score)
    notes = (
        "Reinforced concrete core with steel framing. Routine deflection monitoring "
        "recommended for spans exceeding 15m."
    )
    actions = [
        "Commission detailed structural survey and material testing",
        "Validate live load allowances against proposed programme",
    ]
    if property_record.floors_above_ground and property_record.floors_above_ground > 40:
        actions.append("Review lateral load resistance for high-rise retrofit")

    return ConditionSystem(
        name="Structural frame & envelope",
        rating=rating,
        score=structure_score,
        notes=notes,
        recommended_actions=actions,
    )


def _build_services_system(
    property_record: Property, systems_score: int
) -> ConditionSystem:
    """Construct M&E system assessment details."""
    rating = _score_to_rating(systems_score)
    actions = [
        "Undertake full M&E condition appraisal (HVAC, electrical, fire safety)",
        "Plan progressive replacement of aging chillers and switchgear",
    ]
    if property_record.status and property_record.status.name.lower() == "existing":
        actions.append("Coordinate upgrades with operations to minimise downtime")

    notes = (
        "Core plant sized for original specification. Efficiency upgrades required to "
        "meet current BCA Green Mark and tenant expectations."
    )
    return ConditionSystem(
        name="Mechanical & electrical systems",
        rating=rating,
        score=systems_score,
        notes=notes,
        recommended_actions=actions,
    )


def _build_compliance_system(
    property_record: Property, age_band: str
) -> ConditionSystem:
    """Construct regulatory/compliance view."""
    if age_band in {"new", "mid_life"}:
        score = 82
        rating = "B"
        notes = "Fire safety upgrades largely current; confirm latest SCDF submissions."
    else:
        score = 68
        rating = "C"
        notes = (
            "Legacy code compliance. Accessibility, façade inspections, and fire "
            "certifications require refresh."
        )

    return ConditionSystem(
        name="Compliance & envelope maintenance",
        rating=rating,
        score=score,
        notes=notes,
        recommended_actions=[
            "Update façade inspection records and sealant testing",
            "Refresh fire certification and evacuation strategy",
            "Verify accessibility provisions vs. 2024 BCA requirements",
        ],
    )


def _build_action_plan(
    property_record: Property, overall_rating: str, scenario: Optional[str]
) -> List[str]:
    """Provide a concise action plan list."""
    actions = [
        "Commission intrusive condition survey (structural + M&E)",
        "Develop capex phasing aligned with development programme",
        "Engage cost consultant for remediation budget with risk allowance",
    ]
    if overall_rating in {"D", "E"}:
        actions.insert(0, "Escalate risk to investment committee for budget approval")
    if scenario == "mixed_use_redevelopment":
        actions.append("Coordinate decant strategy and safe demolition methodology")
    if property_record.property_type == PropertyType.MIXED_USE:
        actions.append("Assess shared services segregation for mixed-use compliance")
    return actions


def _build_summary(
    property_record: Property,
    overall_rating: str,
    risk_level: str,
    scenario_context: Optional[str],
) -> str:
    """Compose a short summary string for the frontend."""
    property_name = property_record.name or "The property"
    summary = (
        f"{property_name} scores a {overall_rating} condition rating with {risk_level} "
        "delivery risk. Focus remediation on structural integrity, ageing M&E plant, "
        "and compliance uplift."
    )
    if scenario_context:
        summary = f"{summary} {scenario_context}"
    return summary


__all__ = [
    "ConditionAssessment",
    "ConditionSystem",
    "DeveloperConditionService",
]
