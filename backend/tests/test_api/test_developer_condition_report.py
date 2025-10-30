from __future__ import annotations

from datetime import datetime, timedelta
from uuid import UUID, uuid4

import pytest

pytest.importorskip("sqlalchemy")

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.property import Property, PropertyStatus, PropertyType
from app.services.developer_checklist_service import DeveloperChecklistService
from app.services.developer_condition_service import (
    ConditionAssessment,
    ConditionSystem,
    DeveloperConditionService,
)
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_condition_report_json(
    app_client: AsyncClient,
    async_session_factory: async_sessionmaker[AsyncSession],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    property_id = await _seed_property(async_session_factory)
    _stub_services(monkeypatch, property_id)

    resp = await app_client.get(
        f"/api/v1/developers/properties/{property_id}/condition-assessment/report"
    )

    assert resp.status_code == 200, resp.text
    payload = resp.json()

    assert payload["propertyId"] == str(property_id)
    assert payload["propertyName"] == "Developer Demo Tower"
    assert payload["checklistSummary"]["total"] == 2
    assert payload["checklistSummary"]["completed"] == 1
    assert payload["checklistSummary"]["pending"] == 1
    assert len(payload["scenarioAssessments"]) == 1
    assert payload["scenarioAssessments"][0]["scenario"] == "raw_land"
    assert len(payload["history"]) == 2


@pytest.mark.asyncio
async def test_condition_report_pdf(
    app_client: AsyncClient,
    async_session_factory: async_sessionmaker[AsyncSession],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    property_id = await _seed_property(async_session_factory)
    _stub_services(monkeypatch, property_id)

    resp = await app_client.get(
        f"/api/v1/developers/properties/{property_id}/condition-assessment/report?format=pdf"
    )

    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"] == "application/pdf"
    assert resp.content.startswith(b"%PDF")


async def _seed_property(
    async_session_factory: async_sessionmaker[AsyncSession],
) -> UUID:
    property_id = uuid4()
    async with async_session_factory() as session:
        await session.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS properties (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    address TEXT,
                    postal_code TEXT,
                    property_type TEXT,
                    status TEXT,
                    location TEXT,
                    district TEXT,
                    subzone TEXT,
                    planning_area TEXT,
                    land_area_sqm REAL,
                    gross_floor_area_sqm REAL,
                    net_lettable_area_sqm REAL,
                    building_height_m REAL,
                    floors_above_ground INTEGER,
                    floors_below_ground INTEGER,
                    units_total INTEGER,
                    year_built INTEGER,
                    year_renovated INTEGER,
                    developer TEXT,
                    architect TEXT,
                    tenure_type TEXT,
                    lease_start_date TEXT,
                    lease_expiry_date TEXT,
                    zoning_code TEXT,
                    plot_ratio REAL,
                    is_conservation INTEGER,
                conservation_status TEXT,
                heritage_constraints TEXT,
                    ura_property_id TEXT,
                external_references TEXT,
                    data_source TEXT
                )
                """
            )
        )
        session.add(
            Property(
                id=property_id,
                name="Developer Demo Tower",
                address="1 Developer Crescent",
                property_type=PropertyType.OFFICE,
                status=PropertyStatus.EXISTING,
                location="POINT(103.85 1.30)",
                data_source="test-suite",
            )
        )
        await session.commit()
    return property_id


def _stub_services(monkeypatch: pytest.MonkeyPatch, property_id: UUID) -> None:
    summary = {
        "property_id": str(property_id),
        "total": 2,
        "completed": 1,
        "in_progress": 0,
        "pending": 1,
        "not_applicable": 0,
        "completion_percentage": 50,
        "by_category_status": {
            "title_verification": {
                "total": 1,
                "completed": 1,
                "in_progress": 0,
                "pending": 0,
                "not_applicable": 0,
            },
            "environmental_assessment": {
                "total": 1,
                "completed": 0,
                "in_progress": 0,
                "pending": 1,
                "not_applicable": 0,
            },
        },
    }

    systems = [
        ConditionSystem(
            name="Structural frame & envelope",
            rating="B",
            score=75,
            notes="Undeveloped — structural plan not yet required.",
            recommended_actions=["Commission geotechnical survey"],
        )
    ]

    current = ConditionAssessment(
        property_id=property_id,
        scenario="raw_land",
        overall_score=78,
        overall_rating="B",
        risk_level="moderate",
        summary="Raw land inspection notes",
        scenario_context="Suitable for phased development.",
        systems=systems,
        recommended_actions=["Complete soil investigation before schematic design"],
        recorded_at=datetime.utcnow(),
    )

    fallback = ConditionAssessment(
        property_id=property_id,
        scenario=None,
        overall_score=70,
        overall_rating="C",
        risk_level="moderate",
        summary="General fallback assessment",
        scenario_context=None,
        systems=systems,
        recommended_actions=["Coordinate with MEP consultant"],
        recorded_at=(datetime.utcnow() - timedelta(days=14)),
    )

    async def _checklist_summary(*_args, **_kwargs):
        return summary

    monkeypatch.setattr(
        DeveloperChecklistService,
        "get_checklist_summary",
        _checklist_summary,
    )

    async def _latest_assessments(*_args, **_kwargs):
        return [current]

    async def _assessment_history(*_args, **_kwargs):
        return [current, fallback]

    monkeypatch.setattr(
        DeveloperConditionService,
        "get_latest_assessments_by_scenario",
        _latest_assessments,
    )
    monkeypatch.setattr(
        DeveloperConditionService,
        "get_assessment_history",
        _assessment_history,
    )
