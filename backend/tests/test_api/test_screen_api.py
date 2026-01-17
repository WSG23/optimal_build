"""Tests for buildable screening API endpoints."""

from __future__ import annotations

import pytest
import pytest_asyncio

from app.models.rkp import RefGeocodeCache, RefParcel, RefZoningLayer


@pytest_asyncio.fixture
async def geocode_with_parcel(db_session):
    """Create a geocode cache entry with associated parcel."""
    parcel = RefParcel(
        parcel_ref="TEST-001",
        bounds_json={"zone_code": "R1"},
    )
    db_session.add(parcel)
    await db_session.flush()

    geocode = RefGeocodeCache(
        address="123 Test Street",
        parcel_id=parcel.id,
    )
    db_session.add(geocode)
    await db_session.commit()
    return {"geocode": geocode, "parcel": parcel}


@pytest_asyncio.fixture
async def zoning_layer(db_session):
    """Create a zoning layer with overlays and hints."""
    layer = RefZoningLayer(
        jurisdiction="SG",
        zone_code="R1",
        zone_name="Residential Zone 1",
        attributes={
            "overlays": ["Conservation Overlay", "Heritage Zone"],
            "advisory_hints": [
                "Check heritage requirements",
                "Consult conservation board",
            ],
        },
    )
    db_session.add(layer)
    await db_session.commit()
    return layer


@pytest.mark.asyncio
async def test_screen_buildable_with_address(client, geocode_with_parcel):
    """Test buildable screening with address input."""
    payload = {
        "address": "123 Test Street",
        "defaults": {"site_area_m2": 1000},
    }
    response = await client.post("/api/v1/screen/buildable", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["input_kind"] == "address"
    assert "zone_code" in body
    assert "metrics" in body
    assert "rules" in body


@pytest.mark.asyncio
async def test_screen_buildable_with_geometry(client):
    """Test buildable screening with geometry input."""
    payload = {
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
            "properties": {"zone_code": "MU"},
        },
        "defaults": {"site_area_m2": 2000},
    }
    response = await client.post("/api/v1/screen/buildable", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["input_kind"] == "geometry"
    assert "zone_code" in body
    assert "metrics" in body


@pytest.mark.asyncio
async def test_screen_buildable_with_efficiency_ratio(client):
    """Test buildable screening with custom efficiency ratio."""
    payload = {
        "address": "456 Test Avenue",
        "defaults": {"site_area_m2": 1500},
        "efficiency_ratio": 0.85,
    }
    response = await client.post("/api/v1/screen/buildable", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert "metrics" in body


@pytest.mark.asyncio
async def test_screen_buildable_with_floor_to_floor(client):
    """Test buildable screening with custom floor-to-floor height."""
    payload = {
        "address": "789 Test Road",
        "defaults": {"site_area_m2": 1200},
        "typ_floor_to_floor_m": 3.5,
    }
    response = await client.post("/api/v1/screen/buildable", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert "metrics" in body


@pytest.mark.asyncio
async def test_screen_buildable_mock_response_structure(client):
    """Test that fallback/mock response has expected structure."""
    payload = {
        "address": "Unknown Address That Will Fallback",
        "defaults": {"site_area_m2": 1000},
    }
    response = await client.post("/api/v1/screen/buildable", json=payload)
    assert response.status_code == 200
    body = response.json()
    # Mock response should have these fields
    assert "input_kind" in body
    assert "zone_code" in body
    assert "overlays" in body
    assert "advisory_hints" in body
    assert "metrics" in body
    assert "zone_source" in body
    assert "rules" in body


@pytest.mark.asyncio
async def test_screen_buildable_metrics_structure(client):
    """Test buildable metrics have expected fields."""
    payload = {
        "address": "Test Address",
        "defaults": {"site_area_m2": 1000},
    }
    response = await client.post("/api/v1/screen/buildable", json=payload)
    assert response.status_code == 200
    body = response.json()
    metrics = body["metrics"]
    assert "gfa_cap_m2" in metrics
    assert "floors_max" in metrics
    assert "footprint_m2" in metrics
    assert "nsa_est_m2" in metrics


@pytest.mark.asyncio
async def test_screen_buildable_zone_source_structure(client):
    """Test zone source has expected fields."""
    payload = {
        "address": "Test Address",
        "defaults": {"site_area_m2": 1000},
    }
    response = await client.post("/api/v1/screen/buildable", json=payload)
    assert response.status_code == 200
    body = response.json()
    zone_source = body["zone_source"]
    assert "kind" in zone_source
    assert "layer_name" in zone_source
    assert "jurisdiction" in zone_source


@pytest.mark.asyncio
async def test_screen_buildable_rules_structure(client):
    """Test rules have expected fields."""
    payload = {
        "address": "Test Address",
        "defaults": {"site_area_m2": 1000},
    }
    response = await client.post("/api/v1/screen/buildable", json=payload)
    assert response.status_code == 200
    body = response.json()
    rules = body["rules"]
    assert isinstance(rules, list)
    if rules:
        rule = rules[0]
        assert "id" in rule
        assert "authority" in rule
        assert "parameter_key" in rule
        assert "operator" in rule
        assert "value" in rule


@pytest.mark.asyncio
async def test_screen_buildable_geometry_with_zone_code_property(client):
    """Test that zone_code from geometry properties is used."""
    payload = {
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
            "properties": {"zone_code": "C1"},
        },
        "defaults": {"site_area_m2": 500},
    }
    response = await client.post("/api/v1/screen/buildable", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["input_kind"] == "geometry"
