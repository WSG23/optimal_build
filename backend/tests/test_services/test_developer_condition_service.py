"""Tests for DeveloperConditionService."""

from __future__ import annotations

from uuid import uuid4

import pytest

from app.models.property import Property, PropertyStatus, PropertyType
from app.services.developer_condition_service import (
    ConditionSystem,
    DeveloperConditionService,
)


class _FakeSession:
    def __init__(self, property_record: Property):
        self._property = property_record
        self.add = lambda *_: None
        self.commit = lambda *_: None
        self.flush = lambda *_: None
        self.refresh = lambda *_: None
        self.scalar = lambda *_: None

    async def get(self, model, identifier):  # pragma: no cover - simple stub
        if model is Property and identifier == self._property.id:
            return self._property
        return None

    async def execute(self, *_args, **_kwargs):  # pragma: no cover - simple stub
        class _Result:
            def scalars(self):
                return self

            def first(self):
                return None

        return _Result()


def _build_property() -> Property:
    return Property(
        id=uuid4(),
        name="Test Tower",
        address="1 Example Road",
        property_type=PropertyType.OFFICE,
        status=PropertyStatus.EXISTING,
        year_built=1998,
        floors_above_ground=42,
        building_height_m=210,
        location="POINT(0 0)",
        data_source="test",
    )


@pytest.mark.asyncio
async def test_generate_assessment_returns_structured_response():
    property_record = _build_property()
    dummy_session = _FakeSession(property_record)

    assessment = await DeveloperConditionService.generate_assessment(
        session=dummy_session,  # type: ignore[arg-type]
        property_id=property_record.id,
        scenario="existing_building",
    )

    assert assessment.property_id == property_record.id
    assert assessment.overall_rating in {"A", "B", "C", "D", "E"}
    assert assessment.risk_level in {"low", "moderate", "elevated", "high", "critical"}
    assert len(assessment.systems) >= 3
    structure_system = assessment.systems[0]
    assert structure_system.recommended_actions
    assert assessment.recommended_actions
    assert assessment.insights


@pytest.mark.asyncio
async def test_record_assessment_persists_and_overrides(async_session_factory):
    async with async_session_factory() as session:
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

        stored = await DeveloperConditionService.record_assessment(
            session=session,
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
        await session.commit()

        assert stored.summary == "Inspection summary"
        assert stored.scenario == "existing_building"
        assert stored.recorded_at is not None

        # create general record to serve as fallback for other scenarios
        await DeveloperConditionService.record_assessment(
            session=session,
            property_id=property_id,
            scenario=None,
            overall_rating="C",
            overall_score=72,
            risk_level="moderate",
            summary="Generic inspection",
            scenario_context="Applies to all scenarios",
            systems=systems,
            recommended_actions=["Generic action"],
        )
        await session.commit()

        assessment = await DeveloperConditionService.generate_assessment(
            session=session,
            property_id=property_id,
            scenario="existing_building",
        )
        assert assessment.summary == "Inspection summary"
        assert assessment.recorded_at is not None
        assert isinstance(assessment.insights, list)

        fallback = await DeveloperConditionService.generate_assessment(
            session=session,
            property_id=property_id,
            scenario="raw_land",
        )
        assert fallback.summary == "Generic inspection"
        assert isinstance(fallback.insights, list)

        history = await DeveloperConditionService.get_assessment_history(
            session=session,
            property_id=property_id,
            scenario="existing_building",
            limit=5,
        )
        assert len(history) == 2
        assert history[0].summary == "Inspection summary"
        assert history[1].summary == "Generic inspection"

        full_history = await DeveloperConditionService.get_assessment_history(
            session=session,
            property_id=property_id,
            scenario=None,
        )
        assert len(full_history) == 2

        # Ensure we can retrieve the latest assessment per scenario
        scenario_latest = (
            await DeveloperConditionService.get_latest_assessments_by_scenario(
                session=session,
                property_id=property_id,
            )
        )
        summary_by_scenario = {item.scenario: item.summary for item in scenario_latest}
        # Latest entry for existing_building should be the manual override
        assert summary_by_scenario["existing_building"] == "Inspection summary"
        # Global fallback assessment is also included (scenario None)
        assert summary_by_scenario[None] == "Generic inspection"
