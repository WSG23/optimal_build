"""Tests for the compliance API router."""

from __future__ import annotations

import importlib
import importlib.util
import sys
import uuid
from datetime import datetime
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("pydantic")
pytest.importorskip("sqlalchemy")

from app.schemas.compliance import ComplianceCheckResponse
from app.schemas.property import PropertyComplianceSummary

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient


class _StubService:
    def __init__(
        self, response: ComplianceCheckResponse | None = None, *, raises: bool = False
    ) -> None:
        self._response = response
        self._raises = raises

    async def run_for_property(self, property_id):
        if self._raises:
            raise ValueError("not found")

        class _Result:
            def __init__(self, payload: ComplianceCheckResponse) -> None:
                self.response = payload

        assert self._response is not None
        return _Result(self._response)


def _load_router(monkeypatch):
    project_root = Path(__file__).resolve().parents[1]
    module_path = project_root / "backend" / "app" / "api" / "v1" / "compliance.py"

    monkeypatch.setattr(
        "sqlalchemy.ext.asyncio.create_async_engine", lambda *_, **__: object()
    )

    class _SessionFactory:
        async def __aenter__(self):
            raise RuntimeError("session usage not expected in tests")

        async def __aexit__(self, exc_type, exc, tb):
            return False

    class _AsyncSessionMakerStub:
        def __getitem__(self, _item):
            return self

        def __call__(self, *_, **__):
            return _SessionFactory()

    monkeypatch.setattr(
        "sqlalchemy.ext.asyncio.async_sessionmaker", _AsyncSessionMakerStub()
    )
    app_base = importlib.import_module("app.models.base")
    app_property = importlib.import_module("app.models.property")
    monkeypatch.setitem(sys.modules, "backend.app.models.base", app_base)
    monkeypatch.setitem(sys.modules, "backend.app.models.property", app_property)

    module_name = "unit_tests.compliance_router"
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, module_name, module)
    spec.loader.exec_module(module)
    return module


@pytest.mark.asyncio
async def test_compliance_check_success(monkeypatch) -> None:
    compliance_router = _load_router(monkeypatch)

    app = FastAPI()
    app.include_router(compliance_router.router)
    paths = {route.path for route in app.router.routes}
    assert "/compliance/check" in paths

    response_payload = ComplianceCheckResponse(
        property_id=uuid.uuid4(),
        compliance=PropertyComplianceSummary(
            bca_status="passed",
            ura_status="passed",
            notes="All good",
            last_checked=datetime(2024, 4, 1),
            data={"sample": True},
        ),
        updated_at=datetime(2024, 4, 1, 12, 0),
    )
    app.dependency_overrides[
        compliance_router.get_compliance_service
    ] = lambda: _StubService(response_payload)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        response = await client.post(
            "/compliance/check",
            json={"property_id": str(response_payload.property_id)},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["property_id"] == str(response_payload.property_id)
    assert payload["compliance"]["bca_status"] == "passed"
    assert payload["updated_at"] == "2024-04-01T12:00:00"


@pytest.mark.asyncio
async def test_compliance_check_not_found(monkeypatch) -> None:
    compliance_router = _load_router(monkeypatch)

    app = FastAPI()
    app.include_router(compliance_router.router)
    paths = {route.path for route in app.router.routes}
    assert "/compliance/check" in paths
    app.dependency_overrides[
        compliance_router.get_compliance_service
    ] = lambda: _StubService(raises=True)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        response = await client.post(
            "/compliance/check",
            json={"property_id": str(uuid.uuid4())},
        )

    assert response.status_code == 404
    assert response.json()["detail"] == "not found"
