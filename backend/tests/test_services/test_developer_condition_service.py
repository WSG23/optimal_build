"""Integration tests for DeveloperConditionService."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

import pytest

pytest.importorskip("sqlalchemy")

from app.models.developer_checklists import ChecklistPriority, ChecklistStatus
from app.models.developer_condition import DeveloperConditionAssessmentRecord
from app.models.property import Property, PropertyStatus, PropertyType
from app.services.developer_checklist_service import DeveloperChecklistService
from app.services.developer_condition_service import (
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
    _normalise_scenario,
    _score_to_rating,
    _severity_from_priority,
    _slugify_identifier,
    _system_specialist_hint,
    _years_until_lease_expiry,
)
from sqlalchemy.ext.asyncio import AsyncSession

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def _make_property(**overrides) -> Property:
    """Create a minimal Property for testing."""
    defaults = dict(
        name="Test Tower",
        address="1 Example Road",
        property_type=PropertyType.OFFICE,
        status=PropertyStatus.EXISTING,
        year_built=1998,
        floors_above_ground=42,
        building_height_m=210.0,
        location="POINT(0 0)",
        data_source="test",
    )
    defaults.update(overrides)
    return Property(**defaults)


def _make_assessment_record(
    property_id, **overrides
) -> DeveloperConditionAssessmentRecord:
    """Create a minimal DeveloperConditionAssessmentRecord for testing."""
    defaults = dict(
        property_id=property_id,
        scenario="existing_building",
        overall_rating="B",
        overall_score=78,
        risk_level="moderate",
        summary="Test summary",
        scenario_context="Test context",
        systems=[
            {
                "name": "Structural frame & envelope",
                "rating": "B",
                "score": 78,
                "notes": "Test notes",
                "recommended_actions": ["Action 1"],
            }
        ],
        recommended_actions=["Action 1", "Action 2"],
    )
    defaults.update(overrides)
    return DeveloperConditionAssessmentRecord(**defaults)


# ============================================================================
# HELPER FUNCTION UNIT TESTS
# ============================================================================


def test_normalise_scenario_none():
    """Test _normalise_scenario returns None for None input."""
    assert _normalise_scenario(None) is None


def test_normalise_scenario_empty_string():
    """Test _normalise_scenario returns None for empty string."""
    assert _normalise_scenario("") is None
    assert _normalise_scenario("  ") is None


def test_normalise_scenario_all():
    """Test _normalise_scenario returns None for 'all'."""
    assert _normalise_scenario("all") is None
    assert _normalise_scenario("ALL") is None
    assert _normalise_scenario("  All  ") is None


def test_normalise_scenario_valid():
    """Test _normalise_scenario normalizes valid scenario strings."""
    assert _normalise_scenario("Existing_Building") == "existing_building"
    assert _normalise_scenario("MIXED_USE") == "mixed_use"
    assert _normalise_scenario("  raw_land  ") == "raw_land"


def test_score_to_rating():
    """Test _score_to_rating converts scores to letter ratings."""
    assert _score_to_rating(90) == "A"
    assert _score_to_rating(85) == "A"
    assert _score_to_rating(80) == "B"
    assert _score_to_rating(75) == "B"
    assert _score_to_rating(70) == "C"
    assert _score_to_rating(65) == "C"
    assert _score_to_rating(60) == "D"
    assert _score_to_rating(55) == "D"
    assert _score_to_rating(50) == "E"
    assert _score_to_rating(40) == "E"


def test_determine_risk_level():
    """Test _determine_risk_level maps ratings to risk levels."""
    assert _determine_risk_level("A") == "low"
    assert _determine_risk_level("B") == "moderate"
    assert _determine_risk_level("C") == "elevated"
    assert _determine_risk_level("D") == "high"
    assert _determine_risk_level("E") == "critical"
    assert _determine_risk_level("X") == "moderate"  # Unknown defaults to moderate


def test_severity_from_priority():
    """Test _severity_from_priority maps priorities to severity levels."""
    assert _severity_from_priority(ChecklistPriority.CRITICAL) == "critical"
    assert _severity_from_priority(ChecklistPriority.HIGH) == "warning"
    assert _severity_from_priority(ChecklistPriority.MEDIUM) == "info"
    assert _severity_from_priority(ChecklistPriority.LOW) == "info"


def test_format_status_label():
    """Test _format_status_label formats checklist status."""
    assert _format_status_label(ChecklistStatus.PENDING) == "Pending"
    assert _format_status_label(ChecklistStatus.IN_PROGRESS) == "In Progress"
    assert _format_status_label(ChecklistStatus.COMPLETED) == "Completed"
    assert _format_status_label(ChecklistStatus.NOT_APPLICABLE) == "Not Applicable"


def test_format_scenario_label():
    """Test _format_scenario_label formats scenario strings."""
    assert _format_scenario_label("existing_building") == "Existing Building"
    assert (
        _format_scenario_label("mixed_use_redevelopment") == "Mixed Use Redevelopment"
    )
    assert _format_scenario_label("raw_land") == "Raw Land"


def test_slugify_identifier():
    """Test _slugify_identifier creates slugs from text."""
    assert (
        _slugify_identifier("Structural Frame & Envelope")
        == "structural-frame-envelope"
    )
    assert _slugify_identifier("M&E Systems") == "m-e-systems"
    assert _slugify_identifier("  multiple   spaces  ") == "multiple-spaces"
    assert _slugify_identifier("!!!") == "insight"  # Default fallback


def test_system_specialist_hint():
    """Test _system_specialist_hint returns correct specialist type."""
    assert (
        _system_specialist_hint("Structural frame & envelope") == "Structural engineer"
    )
    assert _system_specialist_hint("Mechanical & electrical systems") == "M&E engineer"
    assert (
        _system_specialist_hint("Compliance & envelope maintenance")
        == "Building surveyor"
    )
    assert _system_specialist_hint("Unknown system") is None


def test_calculate_age_score_new_building():
    """Test _calculate_age_score for new buildings."""
    property_record = _make_property(year_built=date.today().year - 5)
    score, band = _calculate_age_score(property_record)
    assert score == 90
    assert band == "new"


def test_calculate_age_score_mid_life():
    """Test _calculate_age_score for mid-life buildings."""
    property_record = _make_property(year_built=date.today().year - 15)
    score, band = _calculate_age_score(property_record)
    assert score == 80
    assert band == "mid_life"


def test_calculate_age_score_ageing():
    """Test _calculate_age_score for ageing buildings."""
    property_record = _make_property(year_built=date.today().year - 30)
    score, band = _calculate_age_score(property_record)
    assert score == 65
    assert band == "ageing"


def test_calculate_age_score_late_life():
    """Test _calculate_age_score for late-life buildings."""
    property_record = _make_property(year_built=date.today().year - 45)
    score, band = _calculate_age_score(property_record)
    assert score == 55
    assert band == "late_life"


def test_calculate_age_score_legacy():
    """Test _calculate_age_score for legacy buildings."""
    property_record = _make_property(year_built=date.today().year - 70)
    score, band = _calculate_age_score(property_record)
    assert score == 45
    assert band == "legacy"


def test_calculate_age_score_no_year_built():
    """Test _calculate_age_score defaults to age 25 (ageing) when year_built is None."""
    property_record = _make_property(year_built=None)
    score, band = _calculate_age_score(property_record)
    assert score == 65  # age=25 falls in ageing band (25-40 years)
    assert band == "ageing"


def test_calculate_structure_score_office():
    """Test _calculate_structure_score for office buildings."""
    property_record = _make_property(
        property_type=PropertyType.OFFICE,
        floors_above_ground=30,
        building_height_m=150.0,
    )
    score = _calculate_structure_score(property_record)
    assert 65 <= score <= 90


def test_calculate_structure_score_mixed_use():
    """Test _calculate_structure_score for mixed-use buildings."""
    property_record = _make_property(
        property_type=PropertyType.MIXED_USE,
        floors_above_ground=20,
        building_height_m=100.0,
    )
    score = _calculate_structure_score(property_record)
    assert 65 <= score <= 90


def test_calculate_structure_score_residential():
    """Test _calculate_structure_score for residential buildings."""
    property_record = _make_property(
        property_type=PropertyType.RESIDENTIAL,
        floors_above_ground=15,
        building_height_m=60.0,
    )
    score = _calculate_structure_score(property_record)
    assert 40 <= score <= 90


def test_calculate_structure_score_tall_building_penalty():
    """Test _calculate_structure_score applies penalty for tall buildings."""
    property_record = _make_property(
        property_type=PropertyType.OFFICE,
        floors_above_ground=60,
        building_height_m=250.0,
    )
    score = _calculate_structure_score(property_record)
    assert score < 75  # Should have penalties applied


def test_calculate_systems_score_new():
    """Test _calculate_systems_score for new buildings."""
    property_record = _make_property(year_built=date.today().year - 5)
    score = _calculate_systems_score(property_record)
    assert score >= 85


def test_calculate_systems_score_ageing():
    """Test _calculate_systems_score for ageing buildings."""
    property_record = _make_property(year_built=date.today().year - 35)
    score = _calculate_systems_score(property_record)
    assert 60 <= score <= 70


def test_calculate_systems_score_occupied_penalty():
    """Test _calculate_systems_score applies penalty for occupied buildings."""
    property_record = _make_property(
        year_built=date.today().year - 15,
        status=PropertyStatus.EXISTING,
    )
    score = _calculate_systems_score(property_record)
    # Should have slight penalty for live load
    assert score >= 45


def test_describe_scenario_context_existing_building():
    """Test _describe_scenario_context for existing_building."""
    property_record = _make_property()
    context = _describe_scenario_context(property_record, "existing_building")
    assert "phased upgrade" in context.lower()


def test_describe_scenario_context_heritage():
    """Test _describe_scenario_context for heritage_property."""
    property_record = _make_property()
    context = _describe_scenario_context(property_record, "heritage_property")
    assert "conservation" in context.lower()


def test_describe_scenario_context_underused():
    """Test _describe_scenario_context for underused_asset."""
    property_record = _make_property()
    context = _describe_scenario_context(property_record, "underused_asset")
    assert "adaptive reuse" in context.lower()


def test_describe_scenario_context_mixed_use():
    """Test _describe_scenario_context for mixed_use_redevelopment."""
    property_record = _make_property()
    context = _describe_scenario_context(property_record, "mixed_use_redevelopment")
    assert "strip-out" in context.lower()


def test_describe_scenario_context_raw_land():
    """Test _describe_scenario_context for raw_land."""
    property_record = _make_property()
    context = _describe_scenario_context(property_record, "raw_land")
    assert "demolition" in context.lower()


def test_describe_scenario_context_unknown():
    """Test _describe_scenario_context for unknown scenario."""
    property_record = _make_property()
    context = _describe_scenario_context(property_record, "unknown_scenario")
    assert context is None


def test_describe_scenario_context_none():
    """Test _describe_scenario_context for None scenario."""
    property_record = _make_property()
    context = _describe_scenario_context(property_record, None)
    assert context is None


def test_build_structure_system():
    """Test _build_structure_system creates proper system."""
    property_record = _make_property(floors_above_ground=45)
    system = _build_structure_system(property_record, 75)
    assert system.name == "Structural frame & envelope"
    assert system.rating == "B"
    assert system.score == 75
    assert len(system.recommended_actions) >= 2
    assert "high-rise" in " ".join(system.recommended_actions).lower()


def test_build_services_system():
    """Test _build_services_system creates proper system."""
    property_record = _make_property(status=PropertyStatus.EXISTING)
    system = _build_services_system(property_record, 78)
    assert system.name == "Mechanical & electrical systems"
    assert system.rating == "B"
    assert system.score == 78
    assert len(system.recommended_actions) >= 2
    assert any("downtime" in action.lower() for action in system.recommended_actions)


def test_build_compliance_system_new():
    """Test _build_compliance_system for new/mid-life buildings."""
    property_record = _make_property()
    system = _build_compliance_system(property_record, "mid_life")
    assert system.name == "Compliance & envelope maintenance"
    assert system.score == 82
    assert system.rating == "B"
    assert "current" in system.notes.lower()


def test_build_compliance_system_legacy():
    """Test _build_compliance_system for legacy buildings."""
    property_record = _make_property()
    system = _build_compliance_system(property_record, "legacy")
    assert system.name == "Compliance & envelope maintenance"
    assert system.score == 68
    assert system.rating == "C"
    assert "legacy" in system.notes.lower()


def test_build_action_plan_basic():
    """Test _build_action_plan creates action list."""
    property_record = _make_property()
    actions = _build_action_plan(property_record, "B", None)
    assert len(actions) >= 3
    assert any("survey" in action.lower() for action in actions)
    assert any("capex" in action.lower() for action in actions)


def test_build_action_plan_high_risk():
    """Test _build_action_plan includes escalation for D/E ratings."""
    property_record = _make_property()
    actions = _build_action_plan(property_record, "E", None)
    assert any("escalate" in action.lower() for action in actions)


def test_build_action_plan_mixed_use_scenario():
    """Test _build_action_plan includes decant for mixed_use_redevelopment."""
    property_record = _make_property()
    actions = _build_action_plan(property_record, "B", "mixed_use_redevelopment")
    assert any("decant" in action.lower() for action in actions)


def test_build_action_plan_mixed_use_type():
    """Test _build_action_plan includes segregation for mixed-use properties."""
    property_record = _make_property(property_type=PropertyType.MIXED_USE)
    actions = _build_action_plan(property_record, "B", None)
    assert any(
        "segregation" in action.lower() or "shared" in action.lower()
        for action in actions
    )


def test_build_summary():
    """Test _build_summary creates summary text."""
    property_record = _make_property(name="Test Tower")
    summary = _build_summary(property_record, "B", "moderate", "Test context")
    assert "Test Tower" in summary
    assert "B" in summary
    assert "moderate" in summary
    assert "Test context" in summary


def test_build_summary_no_context():
    """Test _build_summary without scenario context."""
    property_record = _make_property(name="Test Tower")
    summary = _build_summary(property_record, "C", "elevated", None)
    assert "Test Tower" in summary
    assert "C" in summary
    assert "elevated" in summary


def test_estimate_property_age_with_year():
    """Test _estimate_property_age calculates age correctly."""
    current_year = date.today().year
    property_record = _make_property(year_built=current_year - 20)
    age = _estimate_property_age(property_record)
    assert age == 20


def test_estimate_property_age_none():
    """Test _estimate_property_age returns None when year_built is None."""
    property_record = _make_property(year_built=None)
    age = _estimate_property_age(property_record)
    assert age is None


def test_years_until_lease_expiry_future():
    """Test _years_until_lease_expiry with future expiry."""
    future_date = date.today() + timedelta(days=3650)  # ~10 years
    property_record = _make_property(lease_expiry_date=future_date)
    years = _years_until_lease_expiry(property_record)
    assert 9 <= years <= 10


def test_years_until_lease_expiry_past():
    """Test _years_until_lease_expiry with past expiry."""
    past_date = date.today() - timedelta(days=365)  # 1 year ago
    property_record = _make_property(lease_expiry_date=past_date)
    years = _years_until_lease_expiry(property_record)
    assert years == -1


def test_years_until_lease_expiry_none():
    """Test _years_until_lease_expiry returns None when no expiry date."""
    property_record = _make_property(lease_expiry_date=None)
    years = _years_until_lease_expiry(property_record)
    assert years is None


def test_condition_system_to_dict():
    """Test ConditionSystem.to_dict serializes correctly."""
    system = ConditionSystem(
        name="Test System",
        rating="B",
        score=75,
        notes="Test notes",
        recommended_actions=["Action 1", "Action 2"],
    )
    data = system.to_dict()
    assert data["name"] == "Test System"
    assert data["rating"] == "B"
    assert data["score"] == 75
    assert data["notes"] == "Test notes"
    assert data["recommended_actions"] == ["Action 1", "Action 2"]


def test_condition_system_from_dict():
    """Test ConditionSystem.from_dict deserializes correctly."""
    data = {
        "name": "Test System",
        "rating": "B",
        "score": 75,
        "notes": "Test notes",
        "recommended_actions": ["Action 1", "Action 2"],
    }
    system = ConditionSystem.from_dict(data)
    assert system.name == "Test System"
    assert system.rating == "B"
    assert system.score == 75
    assert system.notes == "Test notes"
    assert system.recommended_actions == ["Action 1", "Action 2"]


def test_condition_system_from_dict_missing_fields():
    """Test ConditionSystem.from_dict handles missing fields."""
    data = {"name": "Test"}
    system = ConditionSystem.from_dict(data)
    assert system.name == "Test"
    assert system.rating == ""
    assert system.score == 0
    assert system.notes == ""
    assert system.recommended_actions == []


def test_condition_system_from_dict_filters_non_strings():
    """Test ConditionSystem.from_dict filters non-string actions."""
    data = {
        "name": "Test",
        "recommended_actions": ["Action 1", 123, "Action 2", None, 45.6],
    }
    system = ConditionSystem.from_dict(data)
    assert system.recommended_actions == ["Action 1", "123", "Action 2", "45.6"]


def test_condition_insight_to_dict():
    """Test ConditionInsight.to_dict serializes correctly."""
    insight = ConditionInsight(
        id="test-1",
        severity="warning",
        title="Test Insight",
        detail="Test detail",
        specialist="Test Specialist",
    )
    data = insight.to_dict()
    assert data["id"] == "test-1"
    assert data["severity"] == "warning"
    assert data["title"] == "Test Insight"
    assert data["detail"] == "Test detail"
    assert data["specialist"] == "Test Specialist"


def test_condition_insight_to_dict_no_specialist():
    """Test ConditionInsight.to_dict with no specialist."""
    insight = ConditionInsight(
        id="test-1",
        severity="info",
        title="Test Insight",
        detail="Test detail",
    )
    data = insight.to_dict()
    assert data["specialist"] is None


# ============================================================================
# SERVICE INTEGRATION TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_generate_assessment_returns_structured_response(
    db_session: AsyncSession,
):
    """Test generate_assessment creates complete assessment for property."""
    property_record = _make_property()
    db_session.add(property_record)
    await db_session.flush()

    assessment = await DeveloperConditionService.generate_assessment(
        session=db_session,
        property_id=property_record.id,
        scenario="existing_building",
    )

    assert assessment.property_id == property_record.id
    assert assessment.scenario == "existing_building"
    assert assessment.overall_rating in {"A", "B", "C", "D", "E"}
    assert assessment.overall_score >= 0
    assert assessment.risk_level in {"low", "moderate", "elevated", "high", "critical"}
    assert len(assessment.systems) >= 3
    assert assessment.recommended_actions
    assert assessment.insights
    assert assessment.summary
    assert assessment.scenario_context is not None


@pytest.mark.asyncio
async def test_generate_assessment_property_not_found(db_session: AsyncSession):
    """Test generate_assessment raises error when property not found."""
    non_existent_id = uuid4()

    with pytest.raises(ValueError, match="Property not found"):
        await DeveloperConditionService.generate_assessment(
            session=db_session,
            property_id=non_existent_id,
        )


@pytest.mark.asyncio
async def test_generate_assessment_no_scenario(db_session: AsyncSession):
    """Test generate_assessment works without scenario."""
    property_record = _make_property()
    db_session.add(property_record)
    await db_session.flush()

    assessment = await DeveloperConditionService.generate_assessment(
        session=db_session,
        property_id=property_record.id,
        scenario=None,
    )

    assert assessment.scenario is None
    assert assessment.scenario_context is None
    assert assessment.overall_rating is not None


@pytest.mark.asyncio
async def test_record_assessment_creates_new_record(db_session: AsyncSession):
    """Test record_assessment creates and persists assessment record."""
    property_id = uuid4()
    systems = [
        ConditionSystem(
            name="Structural frame & envelope",
            rating="B",
            score=78,
            notes="Inspection notes",
            recommended_actions=["Action 1", "Action 2"],
        )
    ]

    assessment = await DeveloperConditionService.record_assessment(
        session=db_session,
        property_id=property_id,
        scenario="existing_building",
        overall_rating="B",
        overall_score=78,
        risk_level="moderate",
        summary="Inspection summary",
        scenario_context="Context note",
        systems=systems,
        recommended_actions=["Action 1", "Action 2"],
    )
    await db_session.commit()

    assert assessment.property_id == property_id
    assert assessment.scenario == "existing_building"
    assert assessment.overall_rating == "B"
    assert assessment.overall_score == 78
    assert assessment.risk_level == "moderate"
    assert assessment.summary == "Inspection summary"
    assert assessment.scenario_context == "Context note"
    assert len(assessment.systems) == 1
    assert assessment.recorded_at is not None


@pytest.mark.asyncio
async def test_record_assessment_with_inspector_and_attachments(
    db_session: AsyncSession,
):
    """Test record_assessment stores inspector name and attachments."""
    property_id = uuid4()
    systems = [
        ConditionSystem(
            name="Test System",
            rating="C",
            score=65,
            notes="Notes",
            recommended_actions=["Action"],
        )
    ]
    attachments = [
        {"label": "Site photo", "url": "https://example.test/photo.jpg"},
        {"label": "Report", "url": "https://example.test/report.pdf"},
    ]
    recorded_at = datetime(2025, 10, 1, 9, 30, tzinfo=timezone.utc)

    assessment = await DeveloperConditionService.record_assessment(
        session=db_session,
        property_id=property_id,
        scenario=None,
        overall_rating="C",
        overall_score=65,
        risk_level="elevated",
        summary="Summary",
        scenario_context=None,
        systems=systems,
        recommended_actions=["Action"],
        inspector_name="Inspector Jane",
        recorded_at=recorded_at,
        attachments=attachments,
    )
    await db_session.commit()

    assert assessment.inspector_name == "Inspector Jane"
    # recorded_at is stored as naive datetime, compare without timezone
    assert assessment.recorded_at.replace(tzinfo=timezone.utc) == recorded_at
    assert len(assessment.attachments) == 2
    assert assessment.attachments[0]["label"] == "Site photo"
    assert assessment.attachments[0]["url"] == "https://example.test/photo.jpg"


@pytest.mark.asyncio
async def test_record_assessment_cleans_attachments(db_session: AsyncSession):
    """Test record_assessment cleans and filters attachments."""
    property_id = uuid4()
    systems = [ConditionSystem("Test", "B", 70, "Notes", [])]
    attachments = [
        {"label": "Valid", "url": "https://example.test/file.pdf"},
        {"label": "", "url": ""},  # Empty - should be filtered
        {"label": "No URL", "url": None},  # No URL but has label - should be kept
        "invalid",  # Not a dict - should be filtered
        {"label": None, "url": None},  # Both empty - should be filtered
    ]

    assessment = await DeveloperConditionService.record_assessment(
        session=db_session,
        property_id=property_id,
        scenario=None,
        overall_rating="B",
        overall_score=70,
        risk_level="moderate",
        summary="Summary",
        scenario_context=None,
        systems=systems,
        recommended_actions=[],
        attachments=attachments,
    )
    await db_session.commit()

    assert len(assessment.attachments) == 2
    assert assessment.attachments[0]["label"] == "Valid"
    assert assessment.attachments[1]["label"] == "No URL"


@pytest.mark.asyncio
async def test_record_assessment_strips_inspector_name(db_session: AsyncSession):
    """Test record_assessment strips whitespace from inspector name."""
    property_id = uuid4()
    systems = [ConditionSystem("Test", "B", 70, "Notes", [])]

    assessment = await DeveloperConditionService.record_assessment(
        session=db_session,
        property_id=property_id,
        scenario=None,
        overall_rating="B",
        overall_score=70,
        risk_level="moderate",
        summary="Summary",
        scenario_context=None,
        systems=systems,
        recommended_actions=[],
        inspector_name="  Inspector Jane  ",
    )
    await db_session.commit()

    assert assessment.inspector_name == "Inspector Jane"


@pytest.mark.asyncio
async def test_get_assessment_history_empty(db_session: AsyncSession):
    """Test get_assessment_history returns empty list when no records."""
    property_id = uuid4()

    history = await DeveloperConditionService.get_assessment_history(
        session=db_session,
        property_id=property_id,
    )

    assert history == []


@pytest.mark.asyncio
async def test_get_assessment_history_ordered_by_date(db_session: AsyncSession):
    """Test get_assessment_history returns records in descending date order."""
    property_id = uuid4()
    property_record = _make_property(id=property_id)
    db_session.add(property_record)
    await db_session.flush()

    # Create records with different dates
    systems = [ConditionSystem("Test", "B", 70, "Notes", [])]
    await DeveloperConditionService.record_assessment(
        session=db_session,
        property_id=property_id,
        scenario=None,
        overall_rating="B",
        overall_score=70,
        risk_level="moderate",
        summary="First",
        scenario_context=None,
        systems=systems,
        recommended_actions=[],
        recorded_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
    )
    await DeveloperConditionService.record_assessment(
        session=db_session,
        property_id=property_id,
        scenario=None,
        overall_rating="C",
        overall_score=65,
        risk_level="elevated",
        summary="Third",
        scenario_context=None,
        systems=systems,
        recommended_actions=[],
        recorded_at=datetime(2025, 3, 1, tzinfo=timezone.utc),
    )
    await DeveloperConditionService.record_assessment(
        session=db_session,
        property_id=property_id,
        scenario=None,
        overall_rating="B",
        overall_score=75,
        risk_level="moderate",
        summary="Second",
        scenario_context=None,
        systems=systems,
        recommended_actions=[],
        recorded_at=datetime(2025, 2, 1, tzinfo=timezone.utc),
    )
    await db_session.commit()

    history = await DeveloperConditionService.get_assessment_history(
        session=db_session,
        property_id=property_id,
    )

    assert len(history) == 3
    assert history[0].summary == "Third"
    assert history[1].summary == "Second"
    assert history[2].summary == "First"


@pytest.mark.asyncio
async def test_get_assessment_history_with_limit(db_session: AsyncSession):
    """Test get_assessment_history respects limit parameter."""
    property_id = uuid4()
    property_record = _make_property(id=property_id)
    db_session.add(property_record)
    await db_session.flush()

    systems = [ConditionSystem("Test", "B", 70, "Notes", [])]
    for i in range(5):
        await DeveloperConditionService.record_assessment(
            session=db_session,
            property_id=property_id,
            scenario=None,
            overall_rating="B",
            overall_score=70,
            risk_level="moderate",
            summary=f"Record {i}",
            scenario_context=None,
            systems=systems,
            recommended_actions=[],
        )
    await db_session.commit()

    history = await DeveloperConditionService.get_assessment_history(
        session=db_session,
        property_id=property_id,
        limit=2,
    )

    assert len(history) == 2


@pytest.mark.asyncio
async def test_get_assessment_history_filters_by_scenario(db_session: AsyncSession):
    """Test get_assessment_history filters by scenario."""
    property_id = uuid4()
    property_record = _make_property(id=property_id)
    db_session.add(property_record)
    await db_session.flush()

    systems = [ConditionSystem("Test", "B", 70, "Notes", [])]
    await DeveloperConditionService.record_assessment(
        session=db_session,
        property_id=property_id,
        scenario="existing_building",
        overall_rating="B",
        overall_score=70,
        risk_level="moderate",
        summary="Existing building",
        scenario_context=None,
        systems=systems,
        recommended_actions=[],
    )
    await DeveloperConditionService.record_assessment(
        session=db_session,
        property_id=property_id,
        scenario="raw_land",
        overall_rating="C",
        overall_score=65,
        risk_level="elevated",
        summary="Raw land",
        scenario_context=None,
        systems=systems,
        recommended_actions=[],
    )
    await DeveloperConditionService.record_assessment(
        session=db_session,
        property_id=property_id,
        scenario=None,
        overall_rating="B",
        overall_score=72,
        risk_level="moderate",
        summary="Generic",
        scenario_context=None,
        systems=systems,
        recommended_actions=[],
    )
    await db_session.commit()

    history = await DeveloperConditionService.get_assessment_history(
        session=db_session,
        property_id=property_id,
        scenario="existing_building",
    )

    # Should include scenario-specific and generic (None scenario) records
    assert len(history) == 2
    summaries = {h.summary for h in history}
    assert "Existing building" in summaries
    assert "Generic" in summaries


@pytest.mark.asyncio
async def test_get_latest_assessments_by_scenario_empty(db_session: AsyncSession):
    """Test get_latest_assessments_by_scenario returns empty for property with no records."""
    property_id = uuid4()

    results = await DeveloperConditionService.get_latest_assessments_by_scenario(
        session=db_session,
        property_id=property_id,
    )

    assert results == []


@pytest.mark.asyncio
async def test_get_latest_assessments_by_scenario_multiple_scenarios(
    db_session: AsyncSession,
):
    """Test get_latest_assessments_by_scenario returns latest for each scenario."""
    property_id = uuid4()
    property_record = _make_property(id=property_id)
    db_session.add(property_record)
    await db_session.flush()

    systems = [ConditionSystem("Test", "B", 70, "Notes", [])]

    # Create multiple records for different scenarios
    await DeveloperConditionService.record_assessment(
        session=db_session,
        property_id=property_id,
        scenario="existing_building",
        overall_rating="B",
        overall_score=70,
        risk_level="moderate",
        summary="Existing old",
        scenario_context=None,
        systems=systems,
        recommended_actions=[],
        recorded_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
    )
    await DeveloperConditionService.record_assessment(
        session=db_session,
        property_id=property_id,
        scenario="existing_building",
        overall_rating="B",
        overall_score=75,
        risk_level="moderate",
        summary="Existing new",
        scenario_context=None,
        systems=systems,
        recommended_actions=[],
        recorded_at=datetime(2025, 2, 1, tzinfo=timezone.utc),
    )
    await DeveloperConditionService.record_assessment(
        session=db_session,
        property_id=property_id,
        scenario="raw_land",
        overall_rating="C",
        overall_score=65,
        risk_level="elevated",
        summary="Raw land",
        scenario_context=None,
        systems=systems,
        recommended_actions=[],
    )
    await DeveloperConditionService.record_assessment(
        session=db_session,
        property_id=property_id,
        scenario=None,
        overall_rating="B",
        overall_score=72,
        risk_level="moderate",
        summary="Generic",
        scenario_context=None,
        systems=systems,
        recommended_actions=[],
    )
    await db_session.commit()

    results = await DeveloperConditionService.get_latest_assessments_by_scenario(
        session=db_session,
        property_id=property_id,
    )

    assert len(results) == 3
    summaries_by_scenario = {r.scenario: r.summary for r in results}
    assert summaries_by_scenario["existing_building"] == "Existing new"  # Latest
    assert summaries_by_scenario["raw_land"] == "Raw land"
    assert summaries_by_scenario[None] == "Generic"


@pytest.mark.asyncio
async def test_generate_assessment_uses_stored_assessment(db_session: AsyncSession):
    """Test generate_assessment returns stored assessment when available."""
    property_id = uuid4()
    property_record = _make_property(id=property_id)
    db_session.add(property_record)
    await db_session.flush()

    systems = [
        ConditionSystem("Custom System", "A", 90, "Custom notes", ["Custom action"])
    ]
    await DeveloperConditionService.record_assessment(
        session=db_session,
        property_id=property_id,
        scenario="existing_building",
        overall_rating="A",
        overall_score=90,
        risk_level="low",
        summary="Custom summary",
        scenario_context="Custom context",
        systems=systems,
        recommended_actions=["Custom action"],
        inspector_name="Inspector John",
    )
    await db_session.commit()

    assessment = await DeveloperConditionService.generate_assessment(
        session=db_session,
        property_id=property_id,
        scenario="existing_building",
    )

    assert assessment.summary == "Custom summary"
    assert assessment.overall_rating == "A"
    assert assessment.inspector_name == "Inspector John"
    assert assessment.scenario_context == "Custom context"


@pytest.mark.asyncio
async def test_generate_assessment_falls_back_to_generic(db_session: AsyncSession):
    """Test generate_assessment falls back to generic (None scenario) assessment."""
    property_id = uuid4()
    property_record = _make_property(id=property_id)
    db_session.add(property_record)
    await db_session.flush()

    systems = [ConditionSystem("Generic System", "B", 75, "Generic notes", [])]
    await DeveloperConditionService.record_assessment(
        session=db_session,
        property_id=property_id,
        scenario=None,
        overall_rating="B",
        overall_score=75,
        risk_level="moderate",
        summary="Generic fallback",
        scenario_context=None,
        systems=systems,
        recommended_actions=[],
    )
    await db_session.commit()

    assessment = await DeveloperConditionService.generate_assessment(
        session=db_session,
        property_id=property_id,
        scenario="raw_land",  # No specific record for this scenario
    )

    assert assessment.summary == "Generic fallback"
    assert assessment.scenario is None  # Falls back to generic (None scenario) record


@pytest.mark.asyncio
async def test_merge_insights_empty_additional(db_session: AsyncSession):
    """Test _merge_insights returns baseline when additional is empty."""
    baseline = [
        ConditionInsight("id1", "info", "Title 1", "Detail 1"),
        ConditionInsight("id2", "warning", "Title 2", "Detail 2"),
    ]

    merged = DeveloperConditionService._merge_insights(baseline, [])

    assert len(merged) == 2
    assert merged[0].id == "id1"
    assert merged[1].id == "id2"


@pytest.mark.asyncio
async def test_merge_insights_adds_new(db_session: AsyncSession):
    """Test _merge_insights adds new insights."""
    baseline = [ConditionInsight("id1", "info", "Title 1", "Detail 1")]
    additional = [ConditionInsight("id2", "warning", "Title 2", "Detail 2")]

    merged = DeveloperConditionService._merge_insights(baseline, additional)

    assert len(merged) == 2
    assert merged[0].id == "id1"
    assert merged[1].id == "id2"


@pytest.mark.asyncio
async def test_merge_insights_replaces_existing(db_session: AsyncSession):
    """Test _merge_insights replaces insights with same id."""
    baseline = [
        ConditionInsight("id1", "info", "Original Title", "Original Detail"),
        ConditionInsight("id2", "warning", "Title 2", "Detail 2"),
    ]
    additional = [
        ConditionInsight("id1", "critical", "Updated Title", "Updated Detail"),
    ]

    merged = DeveloperConditionService._merge_insights(baseline, additional)

    assert len(merged) == 2
    assert merged[0].id == "id1"
    assert merged[0].title == "Updated Title"
    assert merged[0].severity == "critical"
    assert merged[1].id == "id2"


@pytest.mark.asyncio
async def test_record_to_assessment_with_property(db_session: AsyncSession):
    """Test _record_to_assessment includes insights when property provided."""
    property_id = uuid4()
    property_record = _make_property(
        id=property_id,
        year_built=date.today().year - 70,  # Legacy building for insights
    )
    record = _make_assessment_record(property_id)

    assessment = DeveloperConditionService._record_to_assessment(
        record,
        property_record=property_record,
    )

    assert assessment.property_id == property_id
    assert len(assessment.insights) > 0  # Should have age-related insights


@pytest.mark.asyncio
async def test_record_to_assessment_without_property(db_session: AsyncSession):
    """Test _record_to_assessment works without property record."""
    property_id = uuid4()
    record = _make_assessment_record(property_id)

    assessment = DeveloperConditionService._record_to_assessment(
        record,
        property_record=None,
    )

    assert assessment.property_id == property_id
    assert assessment.insights == []


@pytest.mark.asyncio
async def test_record_to_assessment_with_previous(db_session: AsyncSession):
    """Test _record_to_assessment generates comparison insights with previous."""
    property_id = uuid4()
    property_record = _make_property(id=property_id)

    previous_record = _make_assessment_record(property_id, overall_score=80)
    previous = DeveloperConditionService._record_to_assessment(
        previous_record,
        property_record=property_record,
    )

    current_record = _make_assessment_record(property_id, overall_score=70)
    current = DeveloperConditionService._record_to_assessment(
        current_record,
        property_record=property_record,
        previous=previous,
    )

    # Should have a deterioration insight
    assert any(
        "deteriorated" in i.detail.lower() or "dropped" in i.detail.lower()
        for i in current.insights
    )


@pytest.mark.asyncio
async def test_build_specialist_checklist_insights_no_checklist(
    db_session: AsyncSession,
):
    """Test _build_specialist_checklist_insights returns empty when no checklist."""
    property_id = uuid4()

    insights = await DeveloperConditionService._build_specialist_checklist_insights(
        session=db_session,
        property_id=property_id,
        scenario=None,
    )

    assert insights == []


@pytest.mark.asyncio
async def test_build_specialist_checklist_insights_with_professional_items(
    db_session: AsyncSession,
):
    """Test _build_specialist_checklist_insights creates insights from checklist items."""
    # Seed templates first
    await DeveloperChecklistService.ensure_templates_seeded(db_session)

    property_record = _make_property()
    db_session.add(property_record)
    await db_session.flush()

    # Auto-populate checklist
    await DeveloperChecklistService.auto_populate_checklist(
        session=db_session,
        property_id=property_record.id,
        development_scenarios=["existing_building"],
    )

    # Get checklist items and mark one as requiring professional
    checklist_items = await DeveloperChecklistService.get_property_checklist(
        session=db_session,
        property_id=property_record.id,
    )

    # Find an item that requires professional
    professional_item = next(
        (
            item
            for item in checklist_items
            if item.template and item.template.requires_professional
        ),
        None,
    )

    if professional_item:
        professional_item.status = ChecklistStatus.PENDING
        professional_item.notes = "Awaiting structural engineer."
        await db_session.flush()

        insights = await DeveloperConditionService._build_specialist_checklist_insights(
            session=db_session,
            property_id=property_record.id,
            scenario="existing_building",
        )

        assert len(insights) > 0
        assert any(i.specialist is not None for i in insights)


@pytest.mark.asyncio
async def test_build_specialist_checklist_insights_filters_completed(
    db_session: AsyncSession,
):
    """Test _build_specialist_checklist_insights filters out completed items."""
    await DeveloperChecklistService.ensure_templates_seeded(db_session)

    property_record = _make_property()
    db_session.add(property_record)
    await db_session.flush()

    await DeveloperChecklistService.auto_populate_checklist(
        session=db_session,
        property_id=property_record.id,
        development_scenarios=["existing_building"],
    )

    checklist_items = await DeveloperChecklistService.get_property_checklist(
        session=db_session,
        property_id=property_record.id,
    )

    # Mark all items as completed
    for item in checklist_items:
        item.status = ChecklistStatus.COMPLETED
    await db_session.flush()

    insights = await DeveloperConditionService._build_specialist_checklist_insights(
        session=db_session,
        property_id=property_record.id,
        scenario="existing_building",
    )

    # Should not include completed items
    assert insights == []


@pytest.mark.asyncio
async def test_generate_assessment_includes_specialist_insights(
    db_session: AsyncSession,
):
    """Test generate_assessment merges specialist checklist insights."""
    await DeveloperChecklistService.ensure_templates_seeded(db_session)

    property_record = _make_property()
    db_session.add(property_record)
    await db_session.flush()

    await DeveloperChecklistService.auto_populate_checklist(
        session=db_session,
        property_id=property_record.id,
        development_scenarios=["existing_building"],
    )

    checklist_items = await DeveloperChecklistService.get_property_checklist(
        session=db_session,
        property_id=property_record.id,
    )

    # Keep at least one professional item pending
    professional_item = next(
        (
            item
            for item in checklist_items
            if item.template and item.template.requires_professional
        ),
        None,
    )

    if professional_item:
        professional_item.status = ChecklistStatus.PENDING

        # Mark others as completed
        for item in checklist_items:
            if item != professional_item:
                item.status = ChecklistStatus.COMPLETED
        await db_session.flush()

        assessment = await DeveloperConditionService.generate_assessment(
            session=db_session,
            property_id=property_record.id,
            scenario="existing_building",
        )

        # Should have checklist insight
        checklist_insights = [
            i for i in assessment.insights if i.id.startswith("checklist-")
        ]
        assert len(checklist_insights) > 0


@pytest.mark.asyncio
async def test_assessment_with_conservation_property(db_session: AsyncSession):
    """Test assessment generates conservation insight for conservation properties."""
    property_record = _make_property(
        is_conservation=True,
        conservation_status="Grade II Listed",
    )
    db_session.add(property_record)
    await db_session.flush()

    assessment = await DeveloperConditionService.generate_assessment(
        session=db_session,
        property_id=property_record.id,
    )

    # Should have heritage/conservation insight
    assert any(
        "conservation" in i.detail.lower() or "heritage" in i.title.lower()
        for i in assessment.insights
    )


@pytest.mark.asyncio
async def test_assessment_with_short_lease(db_session: AsyncSession):
    """Test assessment generates lease insight for properties with short lease."""
    property_record = _make_property(
        lease_expiry_date=date.today() + timedelta(days=2555),  # ~7 years
    )
    db_session.add(property_record)
    await db_session.flush()

    assessment = await DeveloperConditionService.generate_assessment(
        session=db_session,
        property_id=property_record.id,
    )

    # Should have lease-related critical insight
    lease_insights = [i for i in assessment.insights if "lease" in i.title.lower()]
    assert len(lease_insights) > 0
    assert any(i.severity == "critical" for i in lease_insights)


@pytest.mark.asyncio
async def test_assessment_with_recent_renovation(db_session: AsyncSession):
    """Test assessment generates positive insight for recently renovated properties."""
    property_record = _make_property(
        year_renovated=date.today().year - 2,
    )
    db_session.add(property_record)
    await db_session.flush()

    assessment = await DeveloperConditionService.generate_assessment(
        session=db_session,
        property_id=property_record.id,
    )

    # Should have positive renovation insight
    assert any(
        i.severity == "positive" and "renovation" in i.title.lower()
        for i in assessment.insights
    )


@pytest.mark.asyncio
async def test_assessment_with_poor_system_ratings(db_session: AsyncSession):
    """Test assessment generates system insights for poor ratings."""
    property_record = _make_property(
        year_built=date.today().year - 80,  # Very old building
        floors_above_ground=60,  # Very tall
    )
    db_session.add(property_record)
    await db_session.flush()

    assessment = await DeveloperConditionService.generate_assessment(
        session=db_session,
        property_id=property_record.id,
    )

    # Should have system-related insights
    system_insights = [i for i in assessment.insights if i.id.startswith("system-")]
    assert len(system_insights) > 0


@pytest.mark.asyncio
async def test_get_latest_assessment_scenario_fallback(db_session: AsyncSession):
    """Test _get_latest_assessment falls back to generic (None) scenario."""
    property_id = uuid4()

    # Create only a generic assessment
    generic_record = _make_assessment_record(property_id, scenario=None)
    db_session.add(generic_record)
    await db_session.flush()

    # Request specific scenario
    result = await DeveloperConditionService._get_latest_assessment(
        session=db_session,
        property_id=property_id,
        scenario="raw_land",
    )

    # Should fall back to generic
    assert result is not None
    assert result.scenario is None


@pytest.mark.asyncio
async def test_get_latest_assessment_prefers_scenario_specific(
    db_session: AsyncSession,
):
    """Test _get_latest_assessment prefers scenario-specific over generic."""
    property_id = uuid4()

    # Create both generic and specific
    generic_record = _make_assessment_record(
        property_id,
        scenario=None,
        summary="Generic",
    )
    specific_record = _make_assessment_record(
        property_id,
        scenario="existing_building",
        summary="Specific",
    )
    db_session.add(generic_record)
    db_session.add(specific_record)
    await db_session.flush()

    result = await DeveloperConditionService._get_latest_assessment(
        session=db_session,
        property_id=property_id,
        scenario="existing_building",
    )

    # Should prefer specific
    assert result is not None
    assert result.summary == "Specific"


@pytest.mark.asyncio
async def test_record_assessment_includes_previous_in_result(db_session: AsyncSession):
    """Test record_assessment returns assessment with previous insights."""
    property_id = uuid4()
    property_record = _make_property(id=property_id, year_built=date.today().year - 30)
    db_session.add(property_record)
    await db_session.flush()

    systems = [ConditionSystem("Test", "B", 80, "Notes", [])]

    # Create first assessment
    await DeveloperConditionService.record_assessment(
        session=db_session,
        property_id=property_id,
        scenario="existing_building",
        overall_rating="B",
        overall_score=80,
        risk_level="moderate",
        summary="First",
        scenario_context=None,
        systems=systems,
        recommended_actions=[],
        recorded_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
    )
    await db_session.commit()

    # Create second assessment with lower score
    assessment = await DeveloperConditionService.record_assessment(
        session=db_session,
        property_id=property_id,
        scenario="existing_building",
        overall_rating="C",
        overall_score=68,
        risk_level="elevated",
        summary="Second",
        scenario_context=None,
        systems=systems,
        recommended_actions=[],
        recorded_at=datetime(2025, 2, 1, tzinfo=timezone.utc),
    )
    await db_session.commit()

    # Should include comparison insight
    assert any(
        "deteriorated" in i.detail.lower() or "dropped" in i.detail.lower()
        for i in assessment.insights
    )
