"""Tests for the standards API."""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("pydantic")
pytest.importorskip("sqlalchemy")

from app.models.rkp import RefMaterialStandard
from app.utils import metrics


@pytest.mark.asyncio
async def test_standards_lookup(app_client, session):
    """The standards lookup endpoint returns matching results."""

    record = RefMaterialStandard(
        standard_code="SS EN 206",
        material_type="concrete",
        standard_body="BCA",
        property_key="compressive_strength_mpa",
        value="30",
        unit="MPa",
        section="4.2",
    )
    session.add(record)
    await session.commit()

    response = await app_client.get(
        "/api/v1/standards", params={"standard_code": "SS EN 206"}
    )
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["standard_body"] == "BCA"
    assert payload[0]["section"] == "4.2"

    count = metrics.counter_value(
        metrics.REQUEST_COUNTER, {"endpoint": "standards_lookup"}
    )
    assert count == 1.0
