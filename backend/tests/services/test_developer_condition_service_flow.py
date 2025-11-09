from __future__ import annotations

from datetime import date, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

import app.services.developer_condition_service as dev_condition_module
from app.models.developer_condition import DeveloperConditionAssessmentRecord
from app.models.property import PropertyStatus, PropertyType
from app.services.developer_condition_service import (
    ConditionAssessment,
    ConditionInsight,
    ConditionSystem,
    DeveloperConditionService,
)


class DummyScalars:
    def __init__(self, rows):
        self._rows = list(rows)

    def all(self):
        return list(self._rows)

    def first(self):
        return self._rows[0] if self._rows else None

    def unique(self):
        return self

    def __iter__(self):
        return iter(self._rows)


class DummyResult:
    def __init__(self, rows):
        self._rows = list(rows)

    def scalars(self):
        return DummyScalars(self._rows)

    def scalar_one_or_none(self):
        return self._rows[0] if self._rows else None

    def __iter__(self):
        return iter(self._rows)


class StubSession:
    def __init__(self, *, property_record, execute_results=None):
        self.property_record = property_record
        self.execute_results = list(execute_results or [])
        self.added_objects = []
        self.refreshed = []

    async def get(self, model, pk):
        return self.property_record

    def add(self, obj):
        self.added_objects.append(obj)

    async def flush(self):
        pass

    async def refresh(self, obj):
        self.refreshed.append(obj)
        if getattr(obj, "recorded_at", None) is None:
            obj.recorded_at = datetime.utcnow()

    async def execute(self, stmt):
        if self.execute_results:
            return self.execute_results.pop(0)
        return DummyResult([])


def make_property(**overrides):
    defaults = dict(
        name="Harbour Tower",
        year_built=date.today().year - 15,
        floors_above_ground=20,
        building_height_m=150,
        property_type=PropertyType.OFFICE,
        status=PropertyStatus.EXISTING,
        year_renovated=date.today().year - 3,
        is_conservation=False,
        conservation_status="",
        lease_expiry_date=date.today() + timedelta(days=12 * 365),
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def make_record(**overrides):
    record = DeveloperConditionAssessmentRecord(
        property_id=overrides.get("property_id", uuid4()),
        scenario=overrides.get("scenario"),
        overall_rating=overrides.get("overall_rating", "B"),
        overall_score=overrides.get("overall_score", 75),
        risk_level=overrides.get("risk_level", "moderate"),
        summary=overrides.get("summary", "Summary text"),
        scenario_context=overrides.get("scenario_context"),
        systems=overrides.get("systems", []),
        recommended_actions=overrides.get("recommended_actions", []),
        inspector_name=overrides.get("inspector_name"),
        recorded_by=overrides.get("recorded_by"),
        attachments=overrides.get("attachments", []),
    )
    if "recorded_at" in overrides:
        record.recorded_at = overrides["recorded_at"]
    return record


@pytest.mark.asyncio
async def test_generate_assessment_heuristic_path(monkeypatch):
    property_id = uuid4()
    property_record = make_property()
    session = StubSession(property_record=property_record)

    baseline_insight = ConditionInsight(
        id="baseline",
        severity="info",
        title="Baseline Insight",
        detail="Details",
    )
    specialist_insight = ConditionInsight(
        id="specialist",
        severity="warning",
        title="Specialist Insight",
        detail="Specialist detail",
    )

    monkeypatch.setattr(
        DeveloperConditionService,
        "_get_latest_assessment",
        AsyncMock(return_value=None),
    )
    monkeypatch.setattr(
        dev_condition_module,
        "_generate_condition_insights",
        lambda *args, **kwargs: [baseline_insight],
    )
    monkeypatch.setattr(
        DeveloperConditionService,
        "_build_specialist_checklist_insights",
        AsyncMock(return_value=[specialist_insight]),
    )

    assessment = await DeveloperConditionService.generate_assessment(
        session=session,
        property_id=property_id,
        scenario="mixed_use_redevelopment",
    )

    assert isinstance(assessment, ConditionAssessment)
    assert assessment.property_id == property_id
    assert assessment.scenario == "mixed_use_redevelopment"
    assert assessment.overall_rating == "B"
    assert assessment.overall_score == 77
    assert assessment.risk_level == "moderate"
    assert assessment.scenario_context is not None
    assert assessment.systems[0].name == "Structural frame & envelope"
    assert "Commission intrusive condition survey" in assessment.recommended_actions[0]
    insight_ids = {insight.id for insight in assessment.insights}
    assert {"baseline", "specialist"} <= insight_ids


@pytest.mark.asyncio
async def test_record_assessment_cleans_attachments(monkeypatch):
    property_id = uuid4()
    property_record = make_property()
    session = StubSession(property_record=property_record)
    systems = [
        ConditionSystem(
            name="Structure",
            rating="B",
            score=75,
            notes="Structural notes",
            recommended_actions=["Inspect beams"],
        )
    ]

    monkeypatch.setattr(
        DeveloperConditionService,
        "_get_latest_assessment",
        AsyncMock(return_value=None),
    )
    monkeypatch.setattr(
        dev_condition_module,
        "_generate_condition_insights",
        lambda *args, **kwargs: [],
    )

    assessment = await DeveloperConditionService.record_assessment(
        session=session,
        property_id=property_id,
        scenario=" ALL ",
        overall_rating="C",
        overall_score=68,
        risk_level="elevated",
        summary="Summary text",
        scenario_context=None,
        systems=systems,
        recommended_actions=["Follow-up"],
        inspector_name=" Inspector ",
        recorded_at=datetime(2025, 1, 1),
        attachments=[
            {"label": " Floorplan ", "url": " http://example.com/plan.pdf "},
            {"label": " ", "url": " "},
        ],
    )

    assert isinstance(assessment, ConditionAssessment)
    assert assessment.scenario is None
    assert assessment.overall_rating == "C"
    assert assessment.attachments == [
        {"label": "Floorplan", "url": "http://example.com/plan.pdf"}
    ]
    assert session.added_objects
    stored_record = session.added_objects[0]
    assert stored_record.scenario is None


@pytest.mark.asyncio
async def test_get_assessment_history_orders_records(monkeypatch):
    property_id = uuid4()
    property_record = make_property()
    older = make_record(
        property_id=property_id,
        overall_score=70,
        overall_rating="B",
        risk_level="moderate",
        summary="Older summary",
        recorded_at=datetime(2025, 1, 1, 12, 0, 0),
    )
    newer = make_record(
        property_id=property_id,
        overall_score=80,
        overall_rating="A",
        risk_level="low",
        summary="Newer summary",
        recorded_at=datetime(2025, 2, 1, 12, 0, 0),
    )
    session = StubSession(
        property_record=property_record,
        execute_results=[DummyResult([newer, older])],
    )
    monkeypatch.setattr(
        dev_condition_module,
        "_generate_condition_insights",
        lambda *args, **kwargs: [],
    )

    history = await DeveloperConditionService.get_assessment_history(
        session=session,
        property_id=property_id,
        scenario=None,
    )
    assert len(history) == 2
    assert history[0].summary == "Newer summary"
    assert history[1].summary == "Older summary"
