"""Tests for PostGIS helper functions."""

from __future__ import annotations

import asyncio

import pytest
from sqlalchemy import literal_column

from app.models.rkp import RefParcel, RefZoningLayer
from app.services import postgis


@pytest.mark.asyncio
async def test_parcel_area_uses_geometry_when_available(monkeypatch) -> None:
    parcel = RefParcel(id=1, area_m2=250.0)

    class StubSession:
        async def scalar(self, stmt):  # noqa: D401 - single-purpose stub
            return 512.5

    monkeypatch.setattr(postgis.RefParcel, "geometry", object())

    result = await postgis.parcel_area(StubSession(), parcel)
    assert result == pytest.approx(512.5)


@pytest.mark.asyncio
async def test_parcel_area_falls_back_without_geometry(monkeypatch) -> None:
    parcel = RefParcel(id=None, area_m2=175.0)
    monkeypatch.setattr(postgis.RefParcel, "geometry", None)

    result = await postgis.parcel_area(None, parcel)
    assert result == pytest.approx(175.0)


@pytest.mark.asyncio
async def test_parcel_area_handles_scalar_exception(monkeypatch) -> None:
    parcel = RefParcel(id=5, area_m2=90.0)

    class StubSession:
        async def scalar(self, stmt):
            raise RuntimeError("missing function")

    monkeypatch.setattr(postgis.RefParcel, "geometry", object())

    result = await postgis.parcel_area(StubSession(), parcel)
    assert result == pytest.approx(90.0)


class _FakeScalarResult:
    def __init__(self, values):
        self._values = values

    def all(self):
        return list(self._values)


class _FakeExecuteResult:
    def __init__(self, rows=None, values=None):
        self._rows = rows
        self._values = values

    def all(self):
        return self._rows

    def scalars(self):
        return _FakeScalarResult(self._values)


@pytest.mark.asyncio
async def test_load_layers_for_zone_with_geometry(monkeypatch) -> None:
    layer1 = RefZoningLayer(id=1, zone_code="SG:residential")
    layer2 = RefZoningLayer(id=2, zone_code="SG:residential")

    class StubSession:
        async def execute(self, stmt):
            return _FakeExecuteResult(rows=[(layer1, "geom1"), (layer2, "geom2")])

    monkeypatch.setattr(postgis.RefZoningLayer, "geometry", literal_column("geom"))

    rows = await postgis.load_layers_for_zone(StubSession(), "SG:residential")
    assert rows == [layer1, layer2]


@pytest.mark.asyncio
async def test_load_layers_for_zone_without_geometry(monkeypatch) -> None:
    layer = RefZoningLayer(id=3, zone_code="SG:commercial")

    class StubSession:
        async def execute(self, stmt):
            return _FakeExecuteResult(values=[layer])

    monkeypatch.setattr(postgis.RefZoningLayer, "geometry", None)

    rows = await postgis.load_layers_for_zone(StubSession(), "SG:commercial")
    assert rows == [layer]


@pytest.mark.asyncio
async def test_load_layers_for_zone_fallback_on_execute_error(monkeypatch) -> None:
    layer = RefZoningLayer(id=4, zone_code="SG:industrial")

    class StubSession:
        def __init__(self) -> None:
            self._attempts = 0

        async def execute(self, stmt):
            self._attempts += 1
            if self._attempts == 1:
                raise RuntimeError("geometry column missing")
            return _FakeExecuteResult(values=[layer])

    monkeypatch.setattr(postgis.RefZoningLayer, "geometry", literal_column("geom"))

    rows = await postgis.load_layers_for_zone(StubSession(), "SG:industrial")
    assert rows == [layer]


def test_postgis_service_facade(monkeypatch):
    calls = {}

    async def fake_parcel(session, parcel):
        calls["parcel"] = parcel
        return 10

    async def fake_load(session, zone_code):
        calls["zone"] = zone_code
        return [zone_code]

    monkeypatch.setattr(postgis, "parcel_area", fake_parcel)
    monkeypatch.setattr(postgis, "load_layers_for_zone", fake_load)

    service = postgis.PostGISService(session="dummy")
    assert asyncio.run(service.parcel_area(parcel="parcel")) == 10
    assert asyncio.run(service.load_layers_for_zone("SG:zone")) == ["SG:zone"]
    assert calls == {"parcel": "parcel", "zone": "SG:zone"}
