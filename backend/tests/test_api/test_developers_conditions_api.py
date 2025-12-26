"""Comprehensive tests for developers_conditions API.

Tests cover:
- ConditionSystemResponse model
- ConditionInsightResponse model
- ConditionAssessmentResponse model
- ConditionSystemRequest model
- ConditionAssessmentUpsertRequest model
- ScenarioComparisonEntryResponse model
- ConditionReportResponse model
- Helper functions
"""

from __future__ import annotations

from typing import List

import pytest

from app.api.v1.developers_conditions import (
    ConditionSystemResponse,
    ConditionInsightResponse,
    ConditionAssessmentResponse,
    ConditionSystemRequest,
    ConditionAssessmentUpsertRequest,
    ScenarioComparisonEntryResponse,
    ConditionReportResponse,
)
from app.api.v1.developers_checklists import ChecklistProgressResponse

# Mark all tests in this module as not requiring database
pytestmark = pytest.mark.no_db


class TestConditionSystemResponse:
    """Tests for ConditionSystemResponse model."""

    def test_required_fields(self) -> None:
        """Test required fields."""
        response = ConditionSystemResponse(
            name="Structural",
            rating="good",
            score=85,
            notes="No significant issues observed",
            recommended_actions=["Regular maintenance"],
        )
        assert response.name == "Structural"
        assert response.rating == "good"
        assert response.score == 85

    def test_multiple_actions(self) -> None:
        """Test multiple recommended actions."""
        response = ConditionSystemResponse(
            name="Electrical",
            rating="fair",
            score=65,
            notes="Some wiring needs updating",
            recommended_actions=[
                "Replace outdated wiring",
                "Add additional circuits",
                "Install surge protection",
            ],
        )
        assert len(response.recommended_actions) == 3


class TestConditionInsightResponse:
    """Tests for ConditionInsightResponse model."""

    def test_required_fields(self) -> None:
        """Test required fields."""
        response = ConditionInsightResponse(
            id="insight-1",
            severity="warning",
            title="Roof Maintenance Required",
            detail="Roof tiles showing wear after 15 years",
        )
        assert response.id == "insight-1"
        assert response.severity == "warning"

    def test_with_specialist(self) -> None:
        """Test with specialist recommendation."""
        response = ConditionInsightResponse(
            id="insight-2",
            severity="critical",
            title="Foundation Settlement",
            detail="Evidence of differential settlement",
            specialist="structural_engineer",
        )
        assert response.specialist == "structural_engineer"


class TestConditionAssessmentResponse:
    """Tests for ConditionAssessmentResponse model."""

    def test_required_fields(self) -> None:
        """Test required fields."""
        system = ConditionSystemResponse(
            name="Structural",
            rating="good",
            score=85,
            notes="Sound structure",
            recommended_actions=[],
        )
        response = ConditionAssessmentResponse(
            property_id="prop-123",
            overall_score=85,
            overall_rating="good",
            risk_level="low",
            summary="Property in good overall condition",
            systems=[system],
            recommended_actions=["Regular maintenance"],
        )
        assert response.property_id == "prop-123"
        assert response.overall_score == 85

    def test_with_scenario(self) -> None:
        """Test with scenario context."""
        response = ConditionAssessmentResponse(
            property_id="prop-456",
            scenario="heritage_property",
            overall_score=70,
            overall_rating="fair",
            risk_level="medium",
            summary="Heritage building requires specialist assessment",
            scenario_context="Heritage preservation requirements apply",
            systems=[],
            recommended_actions=["Heritage impact assessment"],
            insights=[
                ConditionInsightResponse(
                    id="insight-1",
                    severity="warning",
                    title="Heritage Constraints",
                    detail="Limited modification options",
                )
            ],
        )
        assert response.scenario == "heritage_property"
        assert len(response.insights) == 1

    def test_with_inspector(self) -> None:
        """Test with inspector information."""
        response = ConditionAssessmentResponse(
            property_id="prop-789",
            overall_score=90,
            overall_rating="excellent",
            risk_level="low",
            summary="Well-maintained property",
            systems=[],
            recommended_actions=[],
            recorded_at="2024-01-15T10:30:00Z",
            inspectorName="John Smith",
            recordedBy="user-123",
        )
        assert response.inspector_name == "John Smith"
        assert response.recorded_by == "user-123"


class TestConditionSystemRequest:
    """Tests for ConditionSystemRequest model."""

    def test_required_fields(self) -> None:
        """Test required fields."""
        request = ConditionSystemRequest(
            name="HVAC",
            rating="fair",
            score=60,
            notes="System nearing end of life",
        )
        assert request.name == "HVAC"
        assert request.score == 60

    def test_with_actions(self) -> None:
        """Test with recommended actions."""
        request = ConditionSystemRequest(
            name="Plumbing",
            rating="poor",
            score=40,
            notes="Multiple leaks detected",
            recommendedActions=["Replace main pipes", "Install backflow prevention"],
        )
        assert len(request.recommended_actions) == 2


class TestConditionAssessmentUpsertRequest:
    """Tests for ConditionAssessmentUpsertRequest model."""

    def test_required_fields(self) -> None:
        """Test required fields."""
        system = ConditionSystemRequest(
            name="Structural",
            rating="good",
            score=80,
            notes="Minor cracks observed",
        )
        request = ConditionAssessmentUpsertRequest(
            overallRating="good",
            overallScore=80,
            riskLevel="low",
            summary="Property in good condition",
            systems=[system],
        )
        assert request.overall_rating == "good"
        assert request.overall_score == 80

    def test_with_optional_fields(self) -> None:
        """Test with optional fields."""
        request = ConditionAssessmentUpsertRequest(
            scenario="existing_building",
            overallRating="fair",
            overallScore=65,
            riskLevel="medium",
            summary="Requires attention in some areas",
            scenarioContext="Refurbishment potential",
            systems=[],
            recommendedActions=["Commission full survey"],
            inspectorName="Jane Doe",
            recordedAt="2024-02-01T14:00:00Z",
            attachments=[{"type": "photo", "url": "https://example.com/photo1.jpg"}],
        )
        assert request.scenario == "existing_building"
        assert request.inspector_name == "Jane Doe"
        assert len(request.attachments) == 1


class TestScenarioComparisonEntryResponse:
    """Tests for ScenarioComparisonEntryResponse model."""

    def test_basic_entry(self) -> None:
        """Test basic entry."""
        entry = ScenarioComparisonEntryResponse(
            scenario="new_development",
            label="New Development",
            source="heuristic",
        )
        assert entry.scenario == "new_development"
        assert entry.source == "heuristic"

    def test_full_entry(self) -> None:
        """Test full entry with all fields."""
        insight = ConditionInsightResponse(
            id="insight-1",
            severity="warning",
            title="Soil Assessment Needed",
            detail="Unknown soil conditions",
        )
        entry = ScenarioComparisonEntryResponse(
            scenario="heritage_property",
            label="Heritage Property",
            recordedAt="2024-01-20T09:00:00Z",
            overallScore=75,
            overallRating="fair",
            riskLevel="medium",
            checklistCompleted=15,
            checklistTotal=25,
            checklistPercent=60,
            primaryInsight=insight,
            insightCount=3,
            recommendedAction="Commission heritage survey",
            inspectorName="Heritage Specialist",
            source="manual",
        )
        assert entry.overall_score == 75
        assert entry.checklist_percent == 60
        assert entry.primary_insight is not None


class TestConditionReportResponse:
    """Tests for ConditionReportResponse model."""

    def test_minimal_report(self) -> None:
        """Test minimal report."""
        report = ConditionReportResponse(
            propertyId="prop-123",
            generatedAt="2024-02-15T10:00:00Z",
            scenarioAssessments=[],
            history=[],
        )
        assert report.property_id == "prop-123"
        assert report.scenario_assessments == []

    def test_full_report(self) -> None:
        """Test full report with all data."""
        system = ConditionSystemResponse(
            name="Structural",
            rating="good",
            score=85,
            notes="Sound structure",
            recommended_actions=[],
        )
        assessment = ConditionAssessmentResponse(
            property_id="prop-456",
            scenario="new_development",
            overall_score=85,
            overall_rating="good",
            risk_level="low",
            summary="Good condition",
            systems=[system],
            recommended_actions=[],
        )
        checklist = ChecklistProgressResponse(
            total=20,
            completed=15,
            inProgress=3,
            pending=2,
            notApplicable=0,
            completionPercentage=75,
        )
        comparison = ScenarioComparisonEntryResponse(
            scenario="new_development",
            label="New Development",
            source="manual",
            overallScore=85,
        )
        report = ConditionReportResponse(
            propertyId="prop-456",
            propertyName="123 Main Street",
            address="123 Main Street, Singapore 123456",
            generatedAt="2024-02-15T10:00:00Z",
            scenarioAssessments=[assessment],
            history=[assessment],
            checklistSummary=checklist,
            scenarioComparison=[comparison],
        )
        assert report.property_name == "123 Main Street"
        assert len(report.scenario_assessments) == 1
        assert report.checklist_summary is not None


class TestConditionAssessmentScenarios:
    """Tests for condition assessment use case scenarios."""

    def test_new_development_assessment(self) -> None:
        """Test new development assessment."""
        systems: List[ConditionSystemResponse] = [
            ConditionSystemResponse(
                name="Site",
                rating="good",
                score=90,
                notes="Clear site with good access",
                recommended_actions=[],
            ),
            ConditionSystemResponse(
                name="Soil",
                rating="unknown",
                score=50,
                notes="Soil survey recommended",
                recommended_actions=["Commission geotechnical survey"],
            ),
        ]
        assessment = ConditionAssessmentResponse(
            property_id="new-dev-1",
            scenario="new_development",
            overall_score=70,
            overall_rating="fair",
            risk_level="medium",
            summary="Site suitable for development pending soil survey",
            scenario_context="Greenfield development opportunity",
            systems=systems,
            recommended_actions=["Complete soil survey", "Confirm utility connections"],
        )
        assert assessment.scenario == "new_development"
        assert len(assessment.systems) == 2

    def test_heritage_property_assessment(self) -> None:
        """Test heritage property assessment."""
        insights: List[ConditionInsightResponse] = [
            ConditionInsightResponse(
                id="heritage-1",
                severity="warning",
                title="Listed Building Constraints",
                detail="Grade II listing restricts external modifications",
                specialist="heritage_consultant",
            ),
            ConditionInsightResponse(
                id="heritage-2",
                severity="info",
                title="Conservation Area",
                detail="Property in designated conservation area",
            ),
        ]
        assessment = ConditionAssessmentResponse(
            property_id="heritage-1",
            scenario="heritage_property",
            overall_score=65,
            overall_rating="fair",
            risk_level="medium",
            summary="Heritage building with renovation potential",
            scenario_context="Listed building requiring specialist approach",
            systems=[],
            recommended_actions=["Commission heritage impact assessment"],
            insights=insights,
        )
        assert len(assessment.insights) == 2
        assert assessment.insights[0].specialist == "heritage_consultant"

    def test_existing_building_assessment(self) -> None:
        """Test existing building assessment with inspection data."""
        systems: List[ConditionSystemResponse] = [
            ConditionSystemResponse(
                name="Structure",
                rating="good",
                score=80,
                notes="Reinforced concrete frame in good condition",
                recommended_actions=[],
            ),
            ConditionSystemResponse(
                name="Facade",
                rating="fair",
                score=65,
                notes="Some weathering and minor repairs needed",
                recommended_actions=["Facade cleaning", "Repoint brickwork"],
            ),
            ConditionSystemResponse(
                name="Services",
                rating="poor",
                score=45,
                notes="Dated M&E systems require upgrade",
                recommended_actions=["Replace HVAC", "Upgrade electrical"],
            ),
        ]
        assessment = ConditionAssessmentResponse(
            property_id="existing-1",
            scenario="existing_building",
            overall_score=63,
            overall_rating="fair",
            risk_level="medium",
            summary="Building suitable for refurbishment",
            systems=systems,
            recommended_actions=["Full building survey", "M&E assessment"],
            recorded_at="2024-02-10T09:30:00Z",
            inspectorName="Building Surveyor Ltd",
        )
        assert assessment.overall_score == 63
        assert len(assessment.systems) == 3

    def test_scenario_comparison(self) -> None:
        """Test comparing multiple scenarios."""
        scenarios = ["new_development", "heritage_property", "existing_building"]
        comparisons: List[ScenarioComparisonEntryResponse] = []

        for i, scenario in enumerate(scenarios):
            comparisons.append(
                ScenarioComparisonEntryResponse(
                    scenario=scenario,
                    label=scenario.replace("_", " ").title(),
                    overallScore=70 + i * 5,
                    riskLevel=["medium", "high", "low"][i],
                    source="heuristic",
                )
            )

        assert len(comparisons) == 3
        assert comparisons[0].overall_score == 70
        assert comparisons[2].overall_score == 80
