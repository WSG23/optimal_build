from __future__ import annotations

from uuid import uuid4

import pytest
from backend._compat.datetime import utcnow

import pytest_asyncio
from app.api.v1 import compliance as compliance_api
from app.main import app
from app.models.singapore_property import (
    ComplianceStatus,
    PropertyTenure,
    PropertyZoning,
    SingaporeProperty,
)
from app.services import compliance as compliance_service
from httpx import AsyncClient


async def _create_property(async_session_factory, **overrides):
    """Helper to seed a SingaporeProperty record for tests."""

    async with async_session_factory() as session:
        property_id = overrides.get("id", uuid4())
        record = SingaporeProperty(
            id=property_id,
            property_name=overrides.get("property_name", "Test Residences"),
            address=overrides.get("address", "123 Test Street"),
            zoning=overrides.get("zoning", PropertyZoning.RESIDENTIAL),
            tenure=overrides.get("tenure", PropertyTenure.FREEHOLD),
        )
        session.add(record)
        await session.commit()
        return property_id


@pytest_asyncio.fixture
async def compliance_client(async_session_factory):
    compliance_api._service_factory.cache_clear()
    service = compliance_service.ComplianceService(async_session_factory)
    app.dependency_overrides[compliance_api.get_compliance_service] = lambda: service
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client
    app.dependency_overrides.pop(compliance_api.get_compliance_service, None)


@pytest.mark.asyncio
async def test_check_property_compliance_returns_response(
    compliance_client, async_session_factory, monkeypatch
):
    # Arrange: seed property and stub compliance update
    property_id = await _create_property(async_session_factory)

    async def fake_update(record, session):
        record.bca_compliance_status = ComplianceStatus.PASSED.value
        record.ura_compliance_status = ComplianceStatus.WARNING.value
        record.compliance_notes = "Checks completed"
        record.compliance_data = {"gfa_calculation": {}}
        record.compliance_last_checked = utcnow()
        return record

    monkeypatch.setattr(
        compliance_service, "update_property_compliance", fake_update, raising=True
    )

    # Act
    response = await compliance_client.post(
        "/api/v1/compliance/check",
        json={"property_id": str(property_id)},
    )

    # Assert
    assert response.status_code == 200
    payload = response.json()
    assert payload["property_id"] == str(property_id)
    assert payload["metadata"]["jurisdiction"] == "SG"
    assert payload["compliance"]["bca_status"] == "passed"
    assert payload["compliance"]["ura_status"] == "warning"
    assert payload["compliance"]["notes"] == "Checks completed"


@pytest.mark.asyncio
async def test_check_property_compliance_missing_returns_404(
    compliance_client, async_session_factory, monkeypatch
):
    response = await compliance_client.post(
        "/api/v1/compliance/check",
        json={"property_id": str(uuid4())},
    )

    assert response.status_code == 404
    assert "Property" in response.json()["detail"]
