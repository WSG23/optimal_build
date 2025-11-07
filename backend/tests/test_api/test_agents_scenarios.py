from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest
from unittest.mock import AsyncMock

from app.api.v1 import agents as agents_api
from app.main import app


class _StubSession:
    def __init__(self, property_obj):
        self._property = property_obj

    async def execute(self, stmt):
        return SimpleNamespace(scalar_one_or_none=lambda: self._property)


class _StubBuilder:
    def __init__(self, *_args, **_kwargs):
        pass

    async def generate_massing_scenarios(
        self, property_data, scenario_types, session, zoning_info
    ):
        return [
            SimpleNamespace(
                to_dict=lambda: {
                    "scenario": scenario_types[0] if scenario_types else "new_build",
                    "notes": ["Generated"],
                }
            )
        ]


@pytest.mark.asyncio
async def test_generate_3d_scenarios_success(client, monkeypatch):
    property_id = uuid4()
    property_obj = SimpleNamespace(id=property_id, address="1 Test Way")

    async def override_get_session():
        yield _StubSession(property_obj)

    app.dependency_overrides[agents_api.get_session] = override_get_session
    monkeypatch.setattr(agents_api, "Quick3DScenarioBuilder", _StubBuilder)
    monkeypatch.setattr(agents_api, "PostGISService", lambda db: SimpleNamespace())
    monkeypatch.setattr(
        agents_api.ura_service,
        "get_zoning_info",
        AsyncMock(return_value={"zone": "C1"}),
    )

    try:
        response = await client.post(
            f"/api/v1/agents/commercial-property/properties/{property_id}/scenarios/3d",
            json={
                "property_id": str(property_id),
                "scenario_types": ["new_build"],
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert body[0]["scenario"] == "new_build"
    finally:
        app.dependency_overrides.pop(agents_api.get_session, None)


@pytest.mark.asyncio
async def test_generate_3d_scenarios_returns_503_when_unavailable(client, monkeypatch):
    monkeypatch.setattr(agents_api, "Quick3DScenarioBuilder", None)

    response = await client.post(
        f"/api/v1/agents/commercial-property/properties/{uuid4()}/scenarios/3d",
        json={
            "property_id": str(uuid4()),
            "scenario_types": ["new_build"],
        },
    )

    assert response.status_code == 503
    assert "unavailable" in response.json()["detail"].lower()
