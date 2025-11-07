from __future__ import annotations

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.api.v1 import singapore_property_api as sg_api
from app.models.singapore_property import (
    AcquisitionStatus,
    ComplianceStatus,
    FeasibilityStatus,
    PropertyTenure,
    PropertyZoning,
)
from app.main import app


class _Token(SimpleNamespace):
    pass


class _QueryStub:
    def __init__(self, records):
        self._records = records
        self._offset = 0
        self._limit = len(records)

    def filter(self, *args, **kwargs):
        return self

    def offset(self, value):
        self._offset = value
        return self

    def limit(self, value):
        self._limit = value
        return self

    def all(self):
        end = self._offset + self._limit
        return self._records[self._offset : end]

    def first(self):
        items = self.all()
        return items[0] if items else None


class _DBStub:
    def __init__(self, records: list | None = None):
        self.records = records or []
        self.added: list = []
        self.commits = 0

    def query(self, model):
        return _QueryStub(self.records)

    def add(self, obj):
        self.added.append(obj)
        self.records.append(obj)

    def commit(self):
        self.commits += 1

    def refresh(self, obj):
        return obj

    def close(self):
        return None


def _make_property(**overrides):
    base = dict(
        id=uuid4(),
        property_name="Existing Tower",
        address="1 Example Lane",
        postal_code="123456",
        zoning=PropertyZoning.RESIDENTIAL,
        tenure=PropertyTenure.FREEHOLD,
        land_area_sqm=Decimal("1200"),
        gross_plot_ratio=Decimal("3.0"),
        gross_floor_area_sqm=Decimal("2500"),
        building_height_m=Decimal("45"),
        num_storeys=12,
        acquisition_status=AcquisitionStatus.AVAILABLE,
        feasibility_status=FeasibilityStatus.ANALYZING,
        estimated_acquisition_cost=Decimal("10000000"),
        estimated_development_cost=Decimal("5000000"),
        expected_revenue=Decimal("20000000"),
        actual_acquisition_cost=None,
        owner_email="owner@example.com",
        development_status=None,
        ura_compliance_status=None,
        bca_compliance_status=None,
        compliance_notes=None,
        compliance_last_checked=None,
        max_developable_gfa_sqm=None,
        gfa_utilization_percentage=None,
        potential_additional_units=None,
        project_id=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    base.update(overrides)
    return SimpleNamespace(**base)


@pytest.fixture(autouse=True)
def override_singapore_deps(monkeypatch):
    async def _get_user():
        return _Token(user_id="user-123", email="owner@example.com")

    app.dependency_overrides[sg_api.get_current_user] = _get_user
    yield
    app.dependency_overrides.pop(sg_api.get_current_user, None)


def _property_create_payload() -> sg_api.PropertyCreate:
    return sg_api.PropertyCreate(
        property_name="New Tower",
        address="123 Demo Street",
        postal_code="123456",
        zoning=PropertyZoning.RESIDENTIAL,
        tenure=PropertyTenure.FREEHOLD,
        land_area_sqm=Decimal("1500"),
        gross_plot_ratio=Decimal("2.8"),
        gross_floor_area_sqm=Decimal("2000"),
        building_height_m=Decimal("30"),
        num_storeys=8,
        estimated_acquisition_cost=Decimal("10000000"),
        estimated_development_cost=Decimal("5000000"),
        expected_revenue=Decimal("20000000"),
    )


def test_create_and_list_properties(monkeypatch):
    db = _DBStub()

    def _mark_compliant(prop):
        prop.zoning = PropertyZoning.RESIDENTIAL
        prop.tenure = PropertyTenure.FREEHOLD
        prop.acquisition_status = AcquisitionStatus.AVAILABLE
        prop.feasibility_status = FeasibilityStatus.ANALYZING
        prop.ura_compliance_status = ComplianceStatus.PASSED
        prop.created_at = datetime.now(timezone.utc)
        prop.updated_at = datetime.now(timezone.utc)

    monkeypatch.setattr(sg_api, "update_property_compliance_sync", _mark_compliant)

    payload = _property_create_payload()
    created = sg_api.create_property(payload, _Token(email="owner@example.com"), db)
    assert db.added
    assert created.owner_email == "owner@example.com"

    listed = sg_api.list_properties(db=db)
    assert len(listed) == 1
    assert listed[0].property_name == "New Tower"


def test_update_and_get_property(monkeypatch):
    prop = _make_property()
    db = _DBStub([prop])
    monkeypatch.setattr(
        sg_api,
        "update_property_compliance_sync",
        lambda prop: setattr(
            prop, "compliance_last_checked", datetime.now(timezone.utc)
        ),
    )

    updated = sg_api.update_property(
        str(prop.id),
        sg_api.PropertyUpdate(property_name="Renamed Tower"),
        _Token(email="owner@example.com"),
        db,
    )
    assert updated.property_name == "Renamed Tower"

    fetched = sg_api.get_property(str(prop.id), _Token(email="owner@example.com"), db)
    assert fetched.property_name == "Renamed Tower"


def test_check_property_compliance_and_gfa(monkeypatch):
    prop = _make_property()
    db = _DBStub([prop])
    compliance_result = {
        "overall_status": SimpleNamespace(value="passed"),
        "bca_status": SimpleNamespace(value="passed"),
        "ura_status": SimpleNamespace(value="passed"),
        "violations": [],
        "warnings": ["none"],
        "recommendations": ["keep going"],
        "compliance_data": {"notes": "ok"},
    }
    monkeypatch.setattr(
        sg_api,
        "run_full_compliance_check_sync",
        lambda property_obj: compliance_result,
    )
    response = sg_api.check_property_compliance(
        str(prop.id), _Token(email="owner@example.com"), db
    )
    assert response.overall_status == "passed"

    monkeypatch.setattr(
        sg_api,
        "calculate_gfa_utilization",
        lambda property_obj: {"gfa_utilization_pct": 75.0},
    )
    gfa_payload = sg_api.calculate_property_gfa(
        str(prop.id), _Token(email="owner@example.com"), db
    )
    assert gfa_payload["gfa_utilization_pct"] == 75.0


@pytest.mark.asyncio
async def test_calculate_buildable_metrics_fallback(monkeypatch):
    class DummySession:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr("app.core.database.AsyncSessionLocal", lambda: DummySession())

    async def _boom(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr("app.services.buildable.calculate_buildable", _boom)

    payload = {"land_area_sqm": 1200, "zoning": "residential", "jurisdiction": "SG"}
    result = await sg_api.calculate_buildable_metrics(payload)
    assert result["fallback_used"] is True
    assert result["plot_ratio"] == 2.8
