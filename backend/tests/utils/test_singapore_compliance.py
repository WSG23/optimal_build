from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.models.singapore_property import (
    PropertyTenure,
    PropertyZoning,
    SingaporeProperty,
)
from app.utils import singapore_compliance


class _DummyResult:
    def __init__(self, rows):
        self._rows = list(rows)

    def scalars(self):
        return self

    def all(self):
        return list(self._rows)


class _DummySession:
    def __init__(self, responses):
        self._responses = [list(batch) for batch in responses]

    async def execute(self, _):
        if self._responses:
            return _DummyResult(self._responses.pop(0))
        return _DummyResult([])


def _make_property(**overrides) -> SingaporeProperty:
    base = dict(
        id=uuid4(),
        property_name="Test Tower",
        address="1 Example Street",
        zoning=PropertyZoning.RESIDENTIAL,
        tenure=PropertyTenure.FREEHOLD,
        land_area_sqm=Decimal("1000"),
        gross_plot_ratio=Decimal("2.5"),
        gross_floor_area_sqm=Decimal("1800"),
        num_storeys=12,
        building_height_m=Decimal("45"),
        postal_code=None,
        latitude=None,
        longitude=None,
        location=None,
        planning_region=None,
        planning_area=None,
        subzone=None,
        lease_start_date=None,
        lease_remaining_years=None,
        land_area=None,
        gross_floor_area=None,
        gross_plot_ratio_limit=None,
        current_plot_ratio=None,
        street_width_m=None,
        max_building_height_m=None,
        max_storeys=None,
        ura_approval_status=None,
        ura_approval_date=None,
        bca_approval_status=None,
        bca_submission_number=None,
        scdf_approval_status=None,
        nea_clearance=False,
        pub_clearance=False,
        lta_clearance=False,
        development_charge=None,
        differential_premium=None,
        temporary_occupation_fee=None,
        property_tax_annual=None,
        is_conserved=False,
        conservation_status=None,
        heritage_status=None,
        green_mark_rating=None,
        energy_efficiency_index=None,
        water_efficiency_rating=None,
        development_status=None,
        is_government_land=False,
        is_en_bloc_potential=False,
        acquisition_status=None,
        feasibility_status=None,
        ura_compliance_status=None,
        bca_compliance_status=None,
        compliance_notes=None,
        compliance_data=None,
        compliance_last_checked=None,
        max_developable_gfa_sqm=None,
        gfa_utilization_percentage=None,
        potential_additional_units=None,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def _make_rule(**overrides):
    defaults = dict(
        jurisdiction="SG",
        authority="URA",
        topic="zoning",
        parameter_key="zoning.max_far",
        operator="<=",
        value="3.5",
        unit="",
        applicability={"zone_code": "SG:residential"},
        review_status="approved",
        is_published=True,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


@pytest.mark.asyncio
async def test_check_ura_compliance_requires_zoning():
    property_record = _make_property(zoning=None)
    session = _DummySession([])

    result = await singapore_compliance.check_ura_compliance(property_record, session)

    assert result["status"].value == "pending"
    assert "zoning" in result["warnings"][0].lower()


@pytest.mark.asyncio
async def test_check_ura_compliance_detects_plot_ratio_and_height():
    property_record = _make_property(
        gross_plot_ratio=Decimal("4.2"),
        building_height_m=Decimal("70"),
        gross_floor_area_sqm=Decimal("3000"),
        land_area_sqm=Decimal("1000"),
    )
    rules = [
        _make_rule(value="3.0"),
        _make_rule(
            parameter_key="zoning.max_building_height_m",
            value="55",
        ),
    ]
    session = _DummySession([rules])

    result = await singapore_compliance.check_ura_compliance(property_record, session)

    assert result["status"].value == "failed"
    assert len(result["violations"]) >= 2
    assert "plot ratio" in result["violations"][0].lower()


@pytest.mark.asyncio
async def test_check_ura_compliance_warns_when_rules_missing():
    property_record = _make_property()
    session = _DummySession([[]])

    result = await singapore_compliance.check_ura_compliance(property_record, session)

    assert result["status"].value == "warning"
    assert "no zoning rules" in result["warnings"][0].lower()


@pytest.mark.asyncio
async def test_check_bca_compliance_detects_site_coverage_violation():
    property_record = _make_property(
        gross_floor_area_sqm=Decimal("9000"),
        num_storeys=2,
    )
    rules = [
        _make_rule(
            authority="BCA",
            topic="building",
            parameter_key="zoning.site_coverage.max_percent",
            value="40%",
        )
    ]
    session = _DummySession([rules])

    result = await singapore_compliance.check_bca_compliance(property_record, session)

    assert result["status"].value == "failed"
    assert "site coverage" in result["violations"][0].lower()
    assert result["recommendations"]


@pytest.mark.asyncio
async def test_check_bca_compliance_handles_missing_zoning():
    property_record = _make_property(zoning=None)
    session = _DummySession([])

    result = await singapore_compliance.check_bca_compliance(property_record, session)

    assert result["status"].value == "warning"
    assert "zoning" in result["warnings"][0].lower()


@pytest.mark.asyncio
async def test_calculate_gfa_utilization_async_fallback():
    property_record = _make_property(
        gross_plot_ratio=Decimal("3.0"),
        gross_floor_area_sqm=Decimal("1000"),
        num_storeys=10,
    )

    result = await singapore_compliance.calculate_gfa_utilization_async(property_record)

    assert result["max_gfa_sqm"] > result["current_gfa_sqm"]
    assert "recommendations" in result and result["recommendations"]
    assert result["potential_units"] is not None


@pytest.mark.asyncio
async def test_calculate_gfa_utilization_async_requires_inputs():
    property_record = _make_property(land_area_sqm=None)

    result = await singapore_compliance.calculate_gfa_utilization_async(property_record)

    assert result["error"]


@pytest.mark.asyncio
async def test_run_full_compliance_check_aggregates_results():
    property_record = _make_property()
    ura_rules = [
        _make_rule(value="3.5"),
        _make_rule(
            parameter_key="zoning.max_building_height_m",
            value="60",
        ),
    ]
    bca_rules = [
        _make_rule(
            authority="BCA",
            topic="building",
            parameter_key="zoning.site_coverage.max_percent",
            value="70%",
        )
    ]
    session = _DummySession([ura_rules, bca_rules])

    result = await singapore_compliance.run_full_compliance_check(
        property_record, session
    )

    assert result["overall_status"].value == "passed"
    assert not result["violations"]
    assert result["compliance_data"]["ura_check"]["status"].value == "passed"
    assert result["recommendations"]


@pytest.mark.asyncio
async def test_update_property_compliance_sets_fields():
    property_record = _make_property()
    session = _DummySession(
        [
            [
                _make_rule(value="3.5"),
                _make_rule(
                    parameter_key="zoning.max_building_height_m",
                    value="60",
                ),
            ],
            [
                _make_rule(
                    authority="BCA",
                    topic="building",
                    parameter_key="zoning.site_coverage.max_percent",
                    value="80%",
                )
            ],
        ]
    )

    updated = await singapore_compliance.update_property_compliance(
        property_record, session
    )

    assert updated.bca_compliance_status == "passed"
    assert updated.ura_compliance_status == "passed"
    assert updated.compliance_data["gfa_calculation"]["max_gfa_sqm"] > 0
    assert updated.max_developable_gfa_sqm is not None
    assert updated.compliance_last_checked is not None


def test_run_full_compliance_check_sync(monkeypatch):
    property_record = _make_property()
    ura_rules = [
        _make_rule(value="3.5"),
        _make_rule(
            parameter_key="zoning.max_building_height_m",
            value="60",
        ),
    ]
    bca_rules = [
        _make_rule(
            authority="BCA",
            topic="building",
            parameter_key="zoning.site_coverage.max_percent",
            value="80%",
        )
    ]

    async def _stub(callback):
        session = _DummySession([ura_rules, bca_rules])
        return await callback(session)

    monkeypatch.setattr(
        singapore_compliance,
        "_run_with_temporary_async_session",
        _stub,
    )

    result = singapore_compliance.run_full_compliance_check_sync(property_record)

    assert result["overall_status"].value == "passed"


def test_update_property_compliance_sync(monkeypatch):
    property_record = _make_property()
    session_batches = [
        [
            _make_rule(value="3.5"),
            _make_rule(parameter_key="zoning.max_building_height_m", value="60"),
        ],
        [
            _make_rule(
                authority="BCA",
                topic="building",
                parameter_key="zoning.site_coverage.max_percent",
                value="80%",
            )
        ],
    ]

    async def _stub(callback):
        session = _DummySession(session_batches)
        return await callback(session)

    monkeypatch.setattr(
        singapore_compliance,
        "_run_with_temporary_async_session",
        _stub,
    )

    result = singapore_compliance.update_property_compliance_sync(property_record)

    assert result.bca_compliance_status == "passed"
    assert result.ura_compliance_status == "passed"
