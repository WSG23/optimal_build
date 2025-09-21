from __future__ import annotations

import pytest

from app.services.geocode import GeocodeService


@pytest.mark.asyncio
async def test_buildable_endpoints(session, client) -> None:
    geocode_service = GeocodeService(session)
    await geocode_service.seed_cache()

    response = await client.get(
        "/api/v1/screen/buildable",
        params={"address": "1 Marina Boulevard, Singapore"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["parcel_ref"] == "MK21-12345A"
    assert payload["gross_floor_area_m2"] > payload["allowable_coverage_m2"]

    geojson = await client.get(
        "/api/v1/screen/buildable-geojson",
        params={"address": "1 Marina Boulevard, Singapore"},
    )
    assert geojson.status_code == 200
    feature_collection = geojson.json()
    assert feature_collection["type"] == "FeatureCollection"
    assert feature_collection["features"]
