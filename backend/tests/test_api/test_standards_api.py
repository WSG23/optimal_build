from __future__ import annotations

import pytest

from app.models.rkp import RefMaterialStandard
from app.utils import metrics as prometheus_metrics


@pytest.fixture(autouse=True)
def reset_metrics():
    prometheus_metrics.reset_metrics()
    yield
    prometheus_metrics.reset_metrics()


@pytest.fixture
async def standards_seed(session):
    first = RefMaterialStandard(
        jurisdiction="SG",
        standard_code="SS EN 206",
        material_type="concrete",
        standard_body="BCA",
        property_key="compressive_strength_mpa",
        value="40",
        section="4.2",
    )
    second = RefMaterialStandard(
        jurisdiction="SG",
        standard_code="SS EN 1993",
        material_type="steel",
        standard_body="BCA",
        property_key="yield_strength_mpa",
        value="275",
        section="5.1",
    )
    session.add_all([first, second])
    await session.commit()
    return {"first": first, "second": second}


@pytest.mark.asyncio
async def test_list_standards_returns_records(client, standards_seed):
    response = await client.get("/api/v1/standards")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 2
    assert {record["standard_code"] for record in payload} == {
        "SS EN 206",
        "SS EN 1993",
    }


@pytest.mark.asyncio
async def test_list_standards_filters_by_property_key(client, standards_seed):
    response = await client.get(
        "/api/v1/standards",
        params={"property_key": "compressive_strength_mpa"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["value"] == "40"

    counter_value = prometheus_metrics.counter_value(
        prometheus_metrics.REQUEST_COUNTER, {"endpoint": "standards_lookup"}
    )
    assert counter_value >= 1
