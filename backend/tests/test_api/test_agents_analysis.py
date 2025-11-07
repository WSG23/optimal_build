from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.api.v1 import agents as agents_api
from app.main import app


class _StubSession:
    def __init__(self, property_obj):
        self._property = property_obj

    async def execute(self, stmt):
        return SimpleNamespace(scalar_one_or_none=lambda: self._property)


class _StubScanner:
    def __init__(self, *args, **kwargs):
        pass

    async def analyze_property(self, **kwargs):
        return {"analysis": "ok"}


def _override_session(property_obj):
    async def _get_session():
        yield _StubSession(property_obj)

    return _get_session


@pytest.mark.asyncio
async def test_analyze_development_potential_success(client, monkeypatch):
    property_id = uuid4()
    property_obj = SimpleNamespace(id=property_id)

    app.dependency_overrides[agents_api.get_session] = _override_session(property_obj)
    monkeypatch.setattr(agents_api, "BuildableService", lambda db: SimpleNamespace())
    monkeypatch.setattr(agents_api, "DevelopmentPotentialScanner", _StubScanner)

    try:
        response = await client.post(
            f"/api/v1/agents/commercial-property/properties/{property_id}/analyze",
            json={
                "property_id": str(property_id),
                "analysis_type": "raw_land",
                "save_results": False,
            },
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["property_id"] == str(property_id)
        assert payload["results"] == {"analysis": "ok"}
    finally:
        app.dependency_overrides.pop(agents_api.get_session, None)


@pytest.mark.asyncio
async def test_analyze_development_potential_property_not_found(client, monkeypatch):
    property_id = uuid4()

    app.dependency_overrides[agents_api.get_session] = _override_session(None)
    monkeypatch.setattr(agents_api, "BuildableService", lambda db: SimpleNamespace())
    monkeypatch.setattr(agents_api, "DevelopmentPotentialScanner", _StubScanner)

    try:
        response = await client.post(
            f"/api/v1/agents/commercial-property/properties/{property_id}/analyze",
            json={
                "property_id": str(property_id),
                "analysis_type": "raw_land",
            },
        )
        assert response.status_code == 404
    finally:
        app.dependency_overrides.pop(agents_api.get_session, None)
