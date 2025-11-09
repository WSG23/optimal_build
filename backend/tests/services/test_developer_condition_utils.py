from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

from app.models.developer_checklists import ChecklistPriority, ChecklistStatus
from app.models.property import PropertyStatus, PropertyType
from app.services.developer_condition_service import (
    ConditionAssessment,
    ConditionInsight,
    ConditionSystem,
    DeveloperConditionService,
    _build_action_plan,
    _build_compliance_system,
    _build_services_system,
    _build_structure_system,
    _build_summary,
    _calculate_age_score,
    _calculate_structure_score,
    _calculate_systems_score,
    _describe_scenario_context,
    _determine_risk_level,
    _estimate_property_age,
    _format_scenario_label,
    _format_status_label,
    _generate_condition_insights,
    _normalise_scenario,
    _score_to_rating,
    _severity_from_priority,
    _slugify_identifier,
    _system_specialist_hint,
    _years_until_lease_expiry,
)


def _make_property(**overrides):
    base = dict(
        property_type=PropertyType.OFFICE,
        floors_above_ground=42,
        building_height_m=Decimal("220"),
        status=PropertyStatus.EXISTING,
        year_built=1980,
        year_renovated=2018,
        lease_expiry_date=date.today() + timedelta(days=10 * 365),
        is_conservation=False,
        conservation_status="",
        name="Harbour Tower",
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def test_calculate_age_and_system_scores():
    property_record = _make_property(year_built=date.today().year - 5)
    score, band = _calculate_age_score(property_record)
    assert score == 90 and band == "new"

    property_record.year_built = date.today().year - 35
    score, band = _calculate_age_score(property_record)
    assert score == 65 and band == "ageing"

    structure = _calculate_structure_score(property_record)
    assert structure < 70  # tall office penalty applied

    systems = _calculate_systems_score(property_record)
    assert systems < 78  # status adjustment applied


def test_score_to_rating_and_risk_mapping():
    assert _score_to_rating(92) == "A"
    assert _score_to_rating(77) == "B"
    assert _score_to_rating(66) == "C"
    assert _score_to_rating(58) == "D"
    assert _score_to_rating(30) == "E"

    assert _determine_risk_level("A") == "low"
    assert _determine_risk_level("E") == "critical"
    assert _determine_risk_level("unknown") == "moderate"


def test_describe_scenario_context():
    property_record = _make_property()
    assert (
        _describe_scenario_context(property_record, "heritage_property")
        == "Coordinate with conservation guidelines before intrusive works."
    )
    assert _describe_scenario_context(property_record, "unknown") is None


def test_build_system_helpers_inject_actions():
    property_record = _make_property()
    structure_system = _build_structure_system(property_record, 60)
    assert any(
        "lateral load" in action for action in structure_system.recommended_actions
    )

    services_system = _build_services_system(property_record, 72)
    assert any("downtime" in action for action in services_system.recommended_actions)

    compliance_new = _build_compliance_system(property_record, "new")
    compliance_old = _build_compliance_system(property_record, "legacy")
    assert compliance_new.rating == "B"
    assert compliance_old.rating == "C"


def test_action_plan_and_specialist_hints():
    property_record = _make_property(property_type=PropertyType.MIXED_USE)
    actions = _build_action_plan(
        property_record, overall_rating="E", scenario="mixed_use_redevelopment"
    )
    assert actions[0].startswith("Escalate risk")
    assert any("decant" in action for action in actions)
    assert any("mixed-use compliance" in action.lower() for action in actions)

    assert _system_specialist_hint("Structural frame") == "Structural engineer"
    assert _system_specialist_hint("Mechanical & electrical systems") == "M&E engineer"
    assert (
        _system_specialist_hint("Compliance & envelope maintenance")
        == "Building surveyor"
    )
    assert _system_specialist_hint("Landscape") is None


def test_property_age_and_lease_helpers():
    property_record = _make_property(year_built=1990)
    assert _estimate_property_age(property_record) >= 30

    property_record.lease_expiry_date = date.today() + timedelta(days=6 * 365)
    assert _years_until_lease_expiry(property_record) <= 6


def test_slugify_identifier_cleans_names():
    assert (
        _slugify_identifier("Mechanical & Electrical Systems!")
        == "mechanical-electrical-systems"
    )


def test_generate_condition_insights_covers_multiple_sources():
    property_record = _make_property(
        year_built=1950,
        year_renovated=2022,
        lease_expiry_date=date.today() + timedelta(days=5 * 365),
        is_conservation=True,
        conservation_status="National monument status",
    )

    systems = [
        ConditionSystem(
            name="Structural frame",
            rating="E",
            score=45,
            notes="Significant deflection observed.",
            recommended_actions=["Commission structural survey"],
        ),
        ConditionSystem(
            name="Mechanical systems",
            rating="C",
            score=65,
            notes="",
            recommended_actions=[],
        ),
    ]

    assessment = ConditionAssessment(
        property_id=uuid4(),
        scenario=None,
        overall_score=50,
        overall_rating="D",
        risk_level="high",
        summary="",
        scenario_context=None,
        systems=systems,
        recommended_actions=[],
    )
    assessment.recorded_at = datetime.now()
    previous = ConditionAssessment(
        property_id=assessment.property_id,
        scenario=None,
        overall_score=70,
        overall_rating="B",
        risk_level="moderate",
        summary="",
        scenario_context=None,
        systems=systems,
        recommended_actions=[],
    )
    previous.recorded_at = datetime.now() - timedelta(days=120)

    insights = _generate_condition_insights(
        property_record, assessment, previous=previous
    )

    ids = {insight.id for insight in insights}
    assert "age-critical" in ids
    assert "recent-renovation" in ids
    assert "lease-watch" in ids or "lease-critical" in ids
    assert "heritage-controls" in ids
    assert "overall-rating" in ids
    assert "system-structural-frame" in ids
    assert "score-decline" in ids


def test_merge_insights_replaces_duplicates():
    base = [
        ConditionInsight(id="one", severity="info", title="One", detail=""),
        ConditionInsight(id="two", severity="warning", title="Two", detail=""),
    ]
    additional = [
        ConditionInsight(id="two", severity="critical", title="Updated Two", detail=""),
        ConditionInsight(id="three", severity="info", title="Three", detail=""),
    ]
    merged = DeveloperConditionService._merge_insights(base, additional)
    ids = [insight.id for insight in merged]
    assert ids == ["one", "two", "three"]
    assert merged[1].severity == "critical"


def test_summary_and_format_helpers():
    property_record = _make_property()
    summary = _build_summary(
        property_record,
        overall_rating="C",
        risk_level="elevated",
        scenario_context="Focus on phased works.",
    )
    assert "Harbour Tower" in summary
    assert summary.endswith("Focus on phased works.")

    assert _severity_from_priority(ChecklistPriority.CRITICAL) == "critical"
    assert _severity_from_priority(ChecklistPriority.MEDIUM) == "info"

    assert _format_status_label(ChecklistStatus.IN_PROGRESS) == "In Progress"
    assert (
        _format_scenario_label("mixed_use_redevelopment") == "Mixed Use Redevelopment"
    )

    assert _normalise_scenario(None) is None
    assert _normalise_scenario(" All ") is None
    assert _normalise_scenario(" Feasibility ") == "feasibility"
