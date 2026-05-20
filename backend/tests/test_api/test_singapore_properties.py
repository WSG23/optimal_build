"""Tests for Singapore Property API endpoints."""

from __future__ import annotations

import importlib
from types import SimpleNamespace
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select

from app.core.jwt_auth import TokenData, get_current_user
from app.main import app
from app.models.analytics_capture import EntityLifecycleEvent, StatusTransition
from app.models.singapore_property import SingaporeProperty

if TYPE_CHECKING:
    from httpx import AsyncClient


def _setattr_app_aliases(monkeypatch: pytest.MonkeyPatch, path: str, value) -> None:
    """Patch both app.* and backend.app.* import aliases used by full-suite order."""

    monkeypatch.setattr(path, value, raising=False)
    if path.startswith("app."):
        backend_path = f"backend.{path}"
        module_name, attr_name = backend_path.rsplit(".", 1)
        try:
            module = importlib.import_module(module_name)
        except ModuleNotFoundError:
            pass
        else:
            monkeypatch.setattr(module, attr_name, value, raising=False)
    if "singapore_properties." in path:
        attr_name = path.rsplit(".", 1)[-1]
        for route in app.router.routes:
            endpoint = getattr(route, "endpoint", None)
            endpoint_globals = getattr(endpoint, "__globals__", None)
            if (
                endpoint_globals is not None
                and endpoint_globals.get("__name__", "").endswith(
                    "singapore_properties"
                )
                and attr_name in endpoint_globals
            ):
                monkeypatch.setitem(endpoint_globals, attr_name, value)


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

    _setattr_app_aliases(
        monkeypatch, "app.services.buildable.calculate_buildable", _boom
    )

    payload = {"land_area_sqm": 1200, "zoning": "residential", "jurisdiction": "SG"}
    response = await client.post(
        "/api/v1/singapore-property/calculate/buildable",
        json=payload,
    )
    assert response.status_code == 200
    result = response.json()
    assert result["fallback_used"] is True
    assert result["plot_ratio"] == 2.8
    assert result["rule_corpus_status"]["coverage_state"] == "mock"
    assert result["rule_corpus_status"]["counts"]["approved"] == 0


@pytest.mark.asyncio
async def test_general_compliance_endpoint(client: "AsyncClient", monkeypatch):
    """Test compliance check endpoint."""
    ura_result = {
        "status": SimpleNamespace(value="warning"),
        "violations": ["setback"],
        "warnings": [],
        "rules_applied": {},
        "rule_evidence": [
            {
                "rule_id": 1,
                "review_status": "approved",
                "source_id": 10,
                "document_id": 20,
            }
        ],
        "rule_corpus_status": {
            "coverage_state": "partial",
            "confidence": "medium",
            "counts": {"approved": 1, "needs_review": 1},
        },
    }
    bca_result = {
        "status": SimpleNamespace(value="passed"),
        "violations": [],
        "warnings": ["height"],
        "requirements_applied": {},
        "recommendations": ["add sprinklers"],
        "rule_evidence": [],
        "rule_corpus_status": {
            "coverage_state": "approved",
            "confidence": "high",
            "counts": {"approved": 2, "needs_review": 0},
        },
    }

    async def _ura(*_, **__):
        return ura_result

    async def _bca(*_, **__):
        return bca_result

    _setattr_app_aliases(
        monkeypatch, "app.utils.singapore_compliance.check_ura_compliance", _ura
    )
    _setattr_app_aliases(
        monkeypatch, "app.utils.singapore_compliance.check_bca_compliance", _bca
    )

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
    assert result["ura_check"]["rule_evidence"][0]["rule_id"] == 1
    assert result["ura_check"]["rule_corpus_status"]["coverage_state"] == "partial"
    assert result["bca_check"]["rule_corpus_status"]["confidence"] == "high"


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

    _setattr_app_aliases(
        monkeypatch,
        "app.utils.singapore_compliance.update_property_compliance",
        _noop_compliance,
    )
    _setattr_app_aliases(
        monkeypatch,
        "app.api.v1.singapore_properties.update_property_compliance",
        _noop_compliance,
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

    _setattr_app_aliases(
        monkeypatch,
        "app.utils.singapore_compliance.update_property_compliance",
        _noop_compliance,
    )
    _setattr_app_aliases(
        monkeypatch,
        "app.api.v1.singapore_properties.update_property_compliance",
        _noop_compliance,
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

    _setattr_app_aliases(
        monkeypatch,
        "app.utils.singapore_compliance.update_property_compliance",
        _noop_compliance,
    )
    _setattr_app_aliases(
        monkeypatch,
        "app.api.v1.singapore_properties.update_property_compliance",
        _noop_compliance,
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
    client: "AsyncClient",
    async_session_factory,
    property_create_payload: dict,
    monkeypatch,
):
    """Test deleting a property via API."""

    async def _noop_compliance(*args, **kwargs):
        pass

    _setattr_app_aliases(
        monkeypatch,
        "app.utils.singapore_compliance.update_property_compliance",
        _noop_compliance,
    )
    _setattr_app_aliases(
        monkeypatch,
        "app.api.v1.singapore_properties.update_property_compliance",
        _noop_compliance,
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

    async with async_session_factory() as session:
        property_row = await session.get(SingaporeProperty, UUID(property_id))
        lifecycle = (
            (
                await session.execute(
                    select(EntityLifecycleEvent).where(
                        EntityLifecycleEvent.entity_type == "singapore_property",
                        EntityLifecycleEvent.entity_id == property_id,
                        EntityLifecycleEvent.action == "delete",
                    )
                )
            )
            .scalars()
            .first()
        )
        transition = (
            (
                await session.execute(
                    select(StatusTransition).where(
                        StatusTransition.entity_type == "singapore_property",
                        StatusTransition.entity_id == property_id,
                        StatusTransition.status_field == "deleted_at",
                    )
                )
            )
            .scalars()
            .first()
        )

    assert property_row is not None
    assert property_row.deleted_at is not None
    assert lifecycle is not None
    assert transition is not None


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
    _setattr_app_aliases(
        monkeypatch,
        "app.utils.singapore_compliance.run_full_compliance_check",
        _mock_compliance,
    )
    _setattr_app_aliases(
        monkeypatch,
        "app.utils.singapore_compliance.update_property_compliance",
        lambda *args, **kwargs: None,  # sync noop for the monkeypatch
    )
    # Also patch the import location used by the API module
    _setattr_app_aliases(
        monkeypatch,
        "app.api.v1.singapore_properties.update_property_compliance",
        _mock_compliance,
    )
    _setattr_app_aliases(
        monkeypatch,
        "app.api.v1.singapore_properties.run_full_compliance_check",
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

    _setattr_app_aliases(
        monkeypatch,
        "app.utils.singapore_compliance.update_property_compliance",
        _noop_compliance,
    )
    _setattr_app_aliases(
        monkeypatch,
        "app.api.v1.singapore_properties.update_property_compliance",
        _noop_compliance,
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
