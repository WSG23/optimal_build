"""Tests for Singapore Property API endpoints."""

from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING
from uuid import uuid4

import pytest

from app.core.jwt_auth import TokenData, get_current_user
from app.main import app

if TYPE_CHECKING:
    from httpx import AsyncClient


def _mock_token_data() -> TokenData:
    """Return a mock TokenData for testing."""
    return TokenData(
        email="test@example.com",
        username="testuser",
        user_id="test-user-123",
    )


@pytest.fixture(autouse=True)
def override_auth():
    """Override authentication for all tests in this module."""
    app.dependency_overrides[get_current_user] = _mock_token_data
    yield
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def property_create_payload() -> dict:
    """Valid property creation payload."""
    return {
        "property_name": "New Tower",
        "address": "123 Demo Street",
        "postal_code": "123456",
        "zoning": "residential",
        "tenure": "freehold",
        "land_area_sqm": "1500",
        "gross_plot_ratio": "2.8",
        "gross_floor_area_sqm": "2000",
        "building_height_m": "30",
        "num_storeys": 8,
        "estimated_acquisition_cost": "10000000",
        "estimated_development_cost": "5000000",
        "expected_revenue": "20000000",
    }


@pytest.mark.asyncio
async def test_calculate_buildable_metrics_fallback(client: "AsyncClient", monkeypatch):
    """Test buildable metrics endpoint falls back when service errors."""

    async def _boom(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr("app.services.buildable.calculate_buildable", _boom)

    payload = {"land_area_sqm": 1200, "zoning": "residential", "jurisdiction": "SG"}
    response = await client.post(
        "/api/v1/singapore-property/calculate/buildable",
        json=payload,
    )
    assert response.status_code == 200
    result = response.json()
    assert result["fallback_used"] is True
    assert result["plot_ratio"] == 2.8


@pytest.mark.asyncio
async def test_general_compliance_endpoint(client: "AsyncClient", monkeypatch):
    """Test compliance check endpoint."""
    ura_result = {
        "status": SimpleNamespace(value="warning"),
        "violations": ["setback"],
        "warnings": [],
        "rules_applied": {},
    }
    bca_result = {
        "status": SimpleNamespace(value="passed"),
        "violations": [],
        "warnings": ["height"],
        "requirements_applied": {},
        "recommendations": ["add sprinklers"],
    }

    async def _ura(*_, **__):
        return ura_result

    async def _bca(*_, **__):
        return bca_result

    monkeypatch.setattr("app.utils.singapore_compliance.check_ura_compliance", _ura)
    monkeypatch.setattr("app.utils.singapore_compliance.check_bca_compliance", _bca)

    request = {
        "land_area_sqm": 1500,
        "zoning": "residential",
        "proposed_gfa_sqm": 3200,
        "proposed_height_m": 45,
        "proposed_storeys": 12,
    }
    response = await client.post(
        "/api/v1/singapore-property/check-compliance",
        json=request,
    )
    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "FAILED"
    assert "setback" in result["violations"]


@pytest.mark.asyncio
async def test_list_properties_endpoint(client: "AsyncClient"):
    """Test listing properties returns empty list when none exist."""
    response = await client.get("/api/v1/singapore-property/list")
    assert response.status_code == 200
    result = response.json()
    assert isinstance(result, list)


@pytest.mark.asyncio
async def test_create_property_endpoint(
    client: "AsyncClient", property_create_payload: dict, monkeypatch
):
    """Test creating a property via API."""

    async def _noop_compliance(*args, **kwargs):
        pass

    monkeypatch.setattr(
        "app.utils.singapore_compliance.update_property_compliance", _noop_compliance
    )

    response = await client.post(
        "/api/v1/singapore-property/create",
        json=property_create_payload,
    )
    assert response.status_code == 200
    result = response.json()
    assert result["property_name"] == "New Tower"
    assert result["address"] == "123 Demo Street"
    assert "id" in result


@pytest.mark.asyncio
async def test_create_and_get_property(
    client: "AsyncClient", property_create_payload: dict, monkeypatch
):
    """Test creating then fetching a property."""

    async def _noop_compliance(*args, **kwargs):
        pass

    monkeypatch.setattr(
        "app.utils.singapore_compliance.update_property_compliance", _noop_compliance
    )

    # Create property
    create_response = await client.post(
        "/api/v1/singapore-property/create",
        json=property_create_payload,
    )
    assert create_response.status_code == 200
    created = create_response.json()
    property_id = created["id"]

    # Get property
    get_response = await client.get(f"/api/v1/singapore-property/{property_id}")
    assert get_response.status_code == 200
    fetched = get_response.json()
    assert fetched["id"] == property_id
    assert fetched["property_name"] == "New Tower"


@pytest.mark.asyncio
async def test_update_property_endpoint(
    client: "AsyncClient", property_create_payload: dict, monkeypatch
):
    """Test updating a property via API."""

    async def _noop_compliance(*args, **kwargs):
        pass

    monkeypatch.setattr(
        "app.utils.singapore_compliance.update_property_compliance", _noop_compliance
    )

    # Create property first
    create_response = await client.post(
        "/api/v1/singapore-property/create",
        json=property_create_payload,
    )
    assert create_response.status_code == 200
    created = create_response.json()
    property_id = created["id"]

    # Update property
    update_response = await client.put(
        f"/api/v1/singapore-property/{property_id}",
        json={"property_name": "Renamed Tower"},
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["property_name"] == "Renamed Tower"


@pytest.mark.asyncio
async def test_delete_property_endpoint(
    client: "AsyncClient", property_create_payload: dict, monkeypatch
):
    """Test deleting a property via API."""

    async def _noop_compliance(*args, **kwargs):
        pass

    monkeypatch.setattr(
        "app.utils.singapore_compliance.update_property_compliance", _noop_compliance
    )

    # Create property first
    create_response = await client.post(
        "/api/v1/singapore-property/create",
        json=property_create_payload,
    )
    assert create_response.status_code == 200
    created = create_response.json()
    property_id = created["id"]

    # Delete property
    delete_response = await client.delete(f"/api/v1/singapore-property/{property_id}")
    assert delete_response.status_code == 200
    result = delete_response.json()
    assert result["property_id"] == property_id
    assert result["message"] == "Property deleted successfully"

    # Verify property is gone
    get_response = await client.get(f"/api/v1/singapore-property/{property_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_get_property_not_found(client: "AsyncClient"):
    """Test getting a non-existent property returns 404."""
    fake_id = str(uuid4())
    response = await client.get(f"/api/v1/singapore-property/{fake_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_property_invalid_id(client: "AsyncClient"):
    """Test getting property with invalid UUID returns 400."""
    response = await client.get("/api/v1/singapore-property/not-a-uuid")
    assert response.status_code == 400
    assert "Invalid property ID" in response.json()["detail"]


@pytest.mark.asyncio
async def test_check_property_compliance_endpoint(
    client: "AsyncClient", property_create_payload: dict, monkeypatch
):
    """Test compliance check for a specific property."""
    compliance_result = {
        "overall_status": SimpleNamespace(value="passed"),
        "bca_status": SimpleNamespace(value="passed"),
        "ura_status": SimpleNamespace(value="passed"),
        "violations": [],
        "warnings": [],
        "recommendations": ["consider solar panels"],
        "compliance_data": {"notes": "ok"},
        "compliance_notes": "All checks passed",
    }

    async def _mock_compliance(*args, **kwargs):
        return compliance_result

    # Mock both update_property_compliance and run_full_compliance_check
    monkeypatch.setattr(
        "app.utils.singapore_compliance.run_full_compliance_check", _mock_compliance
    )
    monkeypatch.setattr(
        "app.utils.singapore_compliance.update_property_compliance",
        lambda *args, **kwargs: None,  # sync noop for the monkeypatch
    )
    # Also patch the import location used by the API module
    monkeypatch.setattr(
        "app.api.v1.singapore_property_api.update_property_compliance",
        _mock_compliance,
    )
    monkeypatch.setattr(
        "app.api.v1.singapore_property_api.run_full_compliance_check",
        _mock_compliance,
    )

    # Create property first
    create_response = await client.post(
        "/api/v1/singapore-property/create",
        json=property_create_payload,
    )
    assert create_response.status_code == 200
    property_id = create_response.json()["id"]

    # Check compliance
    response = await client.post(
        f"/api/v1/singapore-property/{property_id}/check-compliance"
    )
    assert response.status_code == 200
    result = response.json()
    assert result["overall_status"] == "passed"


@pytest.mark.asyncio
async def test_calculate_gfa_utilization_endpoint(
    client: "AsyncClient", property_create_payload: dict, monkeypatch
):
    """Test GFA utilization calculation endpoint."""

    async def _noop_compliance(*args, **kwargs):
        pass

    monkeypatch.setattr(
        "app.utils.singapore_compliance.update_property_compliance", _noop_compliance
    )

    # Create property first
    create_response = await client.post(
        "/api/v1/singapore-property/create",
        json=property_create_payload,
    )
    assert create_response.status_code == 200
    property_id = create_response.json()["id"]

    # Calculate GFA
    response = await client.get(
        f"/api/v1/singapore-property/calculate/gfa-utilization/{property_id}"
    )
    assert response.status_code == 200
    result = response.json()
    assert "property_id" in result
    assert result["property_id"] == property_id
