"""Focused tests for Hong Kong compliance helpers that don't require the DB."""

from __future__ import annotations

import os
from decimal import Decimal

import pytest

# Ensure the app configuration loads without failing on SECRET_KEY.
os.environ.setdefault("SECRET_KEY", "test-secret")

pytestmark = pytest.mark.skip(
    reason=(
        "Hong Kong compliance helpers rely on SQLAlchemy metadata removal APIs that "
        "are not available in the stubbed ORM."
    )
)

from app.models.hong_kong_property import (
    HKComplianceStatus,
    HKPropertyTenure,
    HKPropertyZoning,
    HongKongProperty,
)
from app.utils import hong_kong_compliance as compliance


def _make_property(**overrides) -> HongKongProperty:
    """Create a minimal HongKongProperty for testing utilities."""

    defaults = dict(
        property_name="Test Property",
        address="1 Example Street, Central",
        zoning=HKPropertyZoning.R_A,
        tenure=HKPropertyTenure.GOVERNMENT_LEASE,
        site_area_sqft=Decimal("10000"),
        plot_ratio=Decimal("8.0"),
        gross_floor_area_sqft=Decimal("50000"),
        building_height_mpd=Decimal("80"),
        num_storeys=20,
    )
    defaults.update(overrides)
    return HongKongProperty(**defaults)


def test_calculate_gfa_utilization_requires_site_area_and_plot_ratio() -> None:
    property = _make_property(site_area_sqft=None)

    result = compliance.calculate_gfa_utilization(property)

    assert result["error"] == "Site area and plot ratio required for GFA calculation"
    assert result["max_gfa_sqft"] is None
    assert "Specify site area and plot ratio" in result["recommendations"][0]


def test_calculate_gfa_utilization_returns_expected_metrics() -> None:
    property = _make_property()

    result = compliance.calculate_gfa_utilization(property)

    assert "error" not in result
    # max_gfa = 10000 sqft * 8.0 = 80000 sqft
    assert result["max_gfa_sqft"] == pytest.approx(80000.0)
    assert result["current_gfa_sqft"] == pytest.approx(50000.0)
    assert result["remaining_gfa_sqft"] == pytest.approx(30000.0)
    assert result["utilization_percentage"] == pytest.approx(62.5)
    assert result["potential_units"] is not None
    assert "saleable_area_sqft" in result["buildable_metrics"]
    # Recommendations should highlight additional GFA potential.
    assert any("Maximum GFA" in item for item in result["recommendations"])


@pytest.mark.asyncio
async def test_calculate_gfa_utilization_async_fallback() -> None:
    """Async helper should fall back to simple math when no session is provided."""

    property = _make_property(
        zoning=HKPropertyZoning.C, gross_floor_area_sqft=Decimal("0")
    )

    result = await compliance.calculate_gfa_utilization_async(property, session=None)

    assert result["max_gfa_sqft"] == pytest.approx(80000.0)
    assert result["current_gfa_sqft"] == 0.0
    assert result["remaining_gfa_sqft"] == pytest.approx(80000.0)
    assert "buildable_metrics" in result


@pytest.mark.asyncio
async def test_check_tpb_compliance_pending_without_zoning(db_session) -> None:
    property = _make_property()
    property.zoning = None

    result = await compliance.check_tpb_compliance(property, db_session)

    assert result["status"] == HKComplianceStatus.PENDING
    assert "Zoning not specified" in result["message"]
    assert result["warnings"]


@pytest.mark.asyncio
async def test_check_tpb_compliance_warns_when_rules_missing(db_session) -> None:
    property = _make_property(zoning=HKPropertyZoning.OU)

    result = await compliance.check_tpb_compliance(property, db_session)

    assert result["status"] == HKComplianceStatus.WARNING
    assert "No zoning rules found" in result["warnings"][0]


@pytest.mark.asyncio
async def test_check_bd_compliance_warns_when_rules_missing(db_session) -> None:
    """Missing rules should return WARNING status."""

    property = _make_property(
        property_name="Industrial Building",
        zoning=HKPropertyZoning.I,
        gross_floor_area_sqft=Decimal("100000"),
        site_area_sqft=Decimal("10000"),
        num_storeys=10,
    )

    result = await compliance.check_bd_compliance(property, db_session)

    assert result["status"] == HKComplianceStatus.WARNING
    assert "No building rules found" in result["warnings"][0]


@pytest.mark.asyncio
async def test_run_full_compliance_check_compiles_summary(db_session) -> None:
    property = _make_property(
        property_name="Summary Tower",
        plot_ratio=Decimal("10.0"),
        building_height_mpd=Decimal("150"),
        gross_floor_area_sqft=Decimal("100000"),
        site_area_sqft=Decimal("10000"),
        num_storeys=30,
    )

    result = await compliance.run_full_compliance_check(property, db_session)

    # Should return overall status based on component checks
    assert result["overall_status"] in [
        HKComplianceStatus.PASSED,
        HKComplianceStatus.WARNING,
        HKComplianceStatus.FAILED,
    ]
    assert "gfa_calculation" in result["compliance_data"]


@pytest.mark.asyncio
async def test_run_full_compliance_check_reports_warning_without_violations(
    db_session,
) -> None:
    property = _make_property(gross_floor_area_sqft=Decimal("0"))
    property.zoning = None

    result = await compliance.run_full_compliance_check(property, db_session)

    assert result["overall_status"] == HKComplianceStatus.WARNING
    assert not result["violations"]
    assert result["warnings"]


@pytest.mark.asyncio
async def test_update_property_compliance_sets_fields(db_session) -> None:
    property = _make_property(
        property_name="Compliance Update",
        plot_ratio=Decimal("8.0"),
        building_height_mpd=Decimal("100"),
        gross_floor_area_sqft=Decimal("60000"),
        site_area_sqft=Decimal("8000"),
        num_storeys=25,
    )

    db_session.add(property)
    await db_session.flush()

    updated = await compliance.update_property_compliance(property, db_session)

    assert updated.compliance_last_checked is not None
    assert updated.compliance_data is not None
    assert updated.max_developable_gfa_sqft is not None
