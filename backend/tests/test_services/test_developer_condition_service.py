"""Tests for DeveloperConditionService."""

from __future__ import annotations

from uuid import uuid4

import pytest
from app.models.property import Property, PropertyStatus, PropertyType
from app.services.developer_condition_service import DeveloperConditionService


class _FakeSession:
    def __init__(self, property_record: Property):
        self._property = property_record

    async def get(self, model, identifier):  # pragma: no cover - simple stub
        if model is Property and identifier == self._property.id:
            return self._property
        return None


def _build_property() -> Property:
    return Property(
        id=uuid4(),
        name="Test Tower",
        property_type=PropertyType.OFFICE,
        status=PropertyStatus.EXISTING,
        year_built=1998,
        floors_above_ground=42,
        building_height_m=210,
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
