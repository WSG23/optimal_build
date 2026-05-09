from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.models.rkp import RefBuildingFootprint, RefParcel, RefZoningLayer


@pytest.mark.asyncio
async def test_capture_data_readiness_endpoint_reports_loaded_sg_sources(
    app_client: AsyncClient,
    async_session_factory,
) -> None:
    async with async_session_factory() as session:
        session.add_all(
            [
                RefZoningLayer(
                    jurisdiction="SG",
                    layer_name="ura_master_plan_2019_land_use",
                    zone_code="SG:commercial",
                    attributes={"LU_DESC": "Commercial", "GPR": "6.3"},
                ),
                RefParcel(
                    jurisdiction="SG",
                    parcel_ref="SG:LOT:MK01-12345",
                    bounds_json={"type": "Polygon", "coordinates": []},
                    area_m2=4321.0,
                    source="sla_data_gov",
                ),
                RefBuildingFootprint(
                    jurisdiction="SG",
                    layer_name="ura_master_plan_2019_building",
                    footprint_ref="SG:BUILDING:1",
                    bounds_json={"type": "Polygon", "coordinates": []},
                    area_m2=500.0,
                    source="ura_data_gov",
                ),
            ]
        )
        await session.commit()

    response = await app_client.get("/api/v1/data-readiness/capture?jurisdiction=sg")

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["jurisdiction"] == "SG"
    assert payload["status"] == "ready"
    assert payload["capturePlanningGfaReady"] is True
    assert payload["currentGfaSourceReady"] is False
    assert payload["counts"]["zoningLayers"] == 1
    assert payload["counts"]["zoningPlotRatioLayers"] == 1
    assert payload["counts"]["parcels"] == 1
    assert payload["counts"]["buildingFootprints"] == 1
    assert payload["nextActions"] == []
