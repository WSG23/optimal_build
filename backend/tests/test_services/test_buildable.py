"""Tests for buildable capacity calculations."""

from __future__ import annotations

import pytest
from app.models.rkp import RefRule
from app.schemas.buildable import BuildableDefaults
from app.services.buildable import ResolvedZone, calculate_buildable

pytest.importorskip("sqlalchemy")
pytest.importorskip("pytest_asyncio")


class _LayerStub:
    """Lightweight stand-in for a zoning layer."""

    def __init__(self, attributes: dict[str, float]) -> None:
        self.attributes = attributes
        self.layer_name = "TestLayer"
        self.jurisdiction = "SG"


@pytest.mark.asyncio
async def test_calculate_buildable_honours_overrides(async_session_factory) -> None:
    defaults = BuildableDefaults(
        plot_ratio=2.5,
        site_area_m2=900.0,
        site_coverage=0.25,
        floor_height_m=4.0,
        efficiency_factor=0.8,
    )
    resolved = ResolvedZone(
        zone_code=None,
        parcel=None,
        zone_layers=[_LayerStub({"height_m": 30.0})],
        input_kind="geometry",
    )

    async with async_session_factory() as session:
        baseline = await calculate_buildable(session, resolved, defaults)
        assert baseline.metrics.floors_max == 7
        assert baseline.metrics.nsa_est_m2 == 1800

        overrides = await calculate_buildable(
            session,
            resolved,
            defaults,
            typ_floor_to_floor_m=5.0,
            efficiency_ratio=0.65,
        )
        assert overrides.metrics.floors_max == 6
        assert overrides.metrics.nsa_est_m2 == 1463


@pytest.mark.asyncio
async def test_calculate_buildable_applies_rule_overrides(session) -> None:
    defaults = BuildableDefaults(
        plot_ratio=2.0,
        site_area_m2=800.0,
        site_coverage=0.3,
        floor_height_m=3.5,
        efficiency_factor=0.7,
    )
    resolved = ResolvedZone(
        zone_code="R-OVR",
        parcel=None,
        zone_layers=[
            _LayerStub(
                {
                    "plot_ratio": 1.8,
                    "site_coverage_percent": 40,
                    "height_m": 12.0,
                    "floors_max": 4,
                }
            )
        ],
        input_kind="geometry",
    )

    approved_rule_defaults = {
        "jurisdiction": "SG",
        "authority": "URA",
        "topic": "zoning",
        "applicability": {"zone_code": "R-OVR"},
        "review_status": "approved",
        "is_published": True,
    }

    approved_rules = [
        RefRule(
            parameter_key="zoning.max_far",
            operator="<=",
            value="4.2",
            **approved_rule_defaults,
        ),
        RefRule(
            parameter_key="zoning.site_coverage.max_percent",
            operator="<=",
            value="65%",
            unit="percent",
            **approved_rule_defaults,
        ),
        RefRule(
            parameter_key="zoning.max_building_height_m",
            operator="<=",
            value="24",
            unit="m",
            **approved_rule_defaults,
        ),
        RefRule(
            parameter_key="zoning.max_building_height_m",
            operator="<=",
            value="8",
            unit="storeys",
            **approved_rule_defaults,
        ),
        RefRule(
            parameter_key="zoning.setback.front_min_m",
            operator=">=",
            value="7.5",
            unit="m",
            **approved_rule_defaults,
        ),
    ]

    session.add_all(approved_rules)
    await session.flush()

    calculation = await calculate_buildable(session, resolved, defaults)

    metrics = calculation.metrics
    assert metrics.gfa_cap_m2 == 3360
    assert metrics.footprint_m2 == 520
    assert metrics.floors_max == 6
    assert metrics.nsa_est_m2 == 2352
    assert len(calculation.rules) == len(approved_rules)


@pytest.mark.asyncio
async def test_calculate_buildable_ignores_unapproved_rules(session) -> None:
    defaults = BuildableDefaults(
        plot_ratio=2.2,
        site_area_m2=1000.0,
        site_coverage=0.4,
        floor_height_m=3.0,
        efficiency_factor=0.75,
    )
    resolved = ResolvedZone(
        zone_code="R-NOAPP",
        parcel=None,
        zone_layers=[
            _LayerStub(
                {
                    "plot_ratio": 1.8,
                    "site_coverage_percent": 55,
                    "height_m": 12.0,
                    "floors_max": 6,
                }
            )
        ],
        input_kind="geometry",
    )

    approved_rule = RefRule(
        jurisdiction="SG",
        authority="URA",
        topic="zoning",
        parameter_key="zoning.setback.front_min_m",
        operator=">=",
        value="7.5",
        unit="m",
        applicability={"zone_code": "R-NOAPP"},
        review_status="approved",
        is_published=True,
    )
    pending_rule = RefRule(
        jurisdiction="SG",
        authority="URA",
        topic="zoning",
        parameter_key="zoning.max_far",
        operator="<=",
        value="4.5",
        applicability={"zone_code": "R-NOAPP"},
        review_status="needs_review",
        is_published=True,
    )

    session.add_all([approved_rule, pending_rule])
    await session.flush()

    calculation = await calculate_buildable(session, resolved, defaults)

    metrics = calculation.metrics
    assert metrics.gfa_cap_m2 == 1800
    assert metrics.footprint_m2 == 550
    assert metrics.floors_max == 4
    assert metrics.nsa_est_m2 == 1350
    assert len(calculation.rules) == 1
    rule = calculation.rules[0]
    assert rule.id == approved_rule.id
    assert rule.parameter_key == approved_rule.parameter_key


@pytest.mark.asyncio
async def test_calculate_buildable_ignores_unpublished_rules(session) -> None:
    defaults = BuildableDefaults(
        plot_ratio=2.2,
        site_area_m2=1000.0,
        site_coverage=0.4,
        floor_height_m=3.0,
        efficiency_factor=0.75,
    )
    resolved = ResolvedZone(
        zone_code="R-NOPUB",
        parcel=None,
        zone_layers=[
            _LayerStub(
                {
                    "plot_ratio": 1.8,
                    "site_coverage_percent": 55,
                    "height_m": 12.0,
                    "floors_max": 6,
                }
            )
        ],
        input_kind="geometry",
    )

    unpublished_rule = RefRule(
        jurisdiction="SG",
        authority="URA",
        topic="zoning",
        parameter_key="zoning.max_far",
        operator="<=",
        value="4.5",
        applicability={"zone_code": "R-NOPUB"},
        review_status="approved",
        is_published=False,
    )

    session.add(unpublished_rule)
    await session.flush()

    calculation = await calculate_buildable(session, resolved, defaults)

    metrics = calculation.metrics
    assert metrics.gfa_cap_m2 == 1800
    assert metrics.footprint_m2 == 550
    assert metrics.floors_max == 4
    assert metrics.nsa_est_m2 == 1350
    assert not calculation.rules


@pytest.mark.asyncio
async def test_calculate_buildable_without_rule_overrides(
    async_session_factory,
) -> None:
    defaults = BuildableDefaults(
        plot_ratio=3.0,
        site_area_m2=750.0,
        site_coverage=0.5,
        floor_height_m=3.2,
        efficiency_factor=0.65,
    )
    resolved = ResolvedZone(
        zone_code="R-EMPTY",
        parcel=None,
        zone_layers=[_LayerStub({})],
        input_kind="geometry",
    )

    async with async_session_factory() as session:
        calculation = await calculate_buildable(session, resolved, defaults)

    metrics = calculation.metrics
    assert metrics.gfa_cap_m2 == 2250
    assert metrics.footprint_m2 == 375
    assert metrics.floors_max == 6
    assert metrics.nsa_est_m2 == 1463
    assert not calculation.rules
