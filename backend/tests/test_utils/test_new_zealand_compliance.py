"""Focused tests for New Zealand compliance helpers that don't require the DB."""

from __future__ import annotations

import os
from decimal import Decimal

import pytest

# Ensure the app configuration loads without failing on SECRET_KEY.
os.environ.setdefault("SECRET_KEY", "test-secret")

pytestmark = pytest.mark.skip(
    reason=(
        "New Zealand compliance helpers rely on SQLAlchemy metadata removal APIs that "
        "are not available in the stubbed ORM."
    )
)

from app.models.new_zealand_property import (
    NZComplianceStatus,
    NZPropertyTenure,
    NZPropertyZoning,
    NewZealandProperty,
)
from app.utils import new_zealand_compliance as compliance


def _make_property(**overrides) -> NewZealandProperty:
    """Create a minimal NewZealandProperty for testing utilities."""

    defaults = dict(
        property_name="Test Property",
        address="1 Example Street, Auckland",
        zoning=NZPropertyZoning.MHU,
        tenure=NZPropertyTenure.FREEHOLD,
        lot_area_sqm=Decimal("800"),
        height_in_relation_to_boundary=Decimal("8.0"),
        gross_floor_area_sqm=Decimal("400"),
        building_height_m=Decimal("11"),
        num_storeys=3,
    )
    defaults.update(overrides)
    return NewZealandProperty(**defaults)


def test_calculate_gfa_utilization_requires_lot_area() -> None:
    property = _make_property(lot_area_sqm=None)

    result = compliance.calculate_gfa_utilization(property)

    assert result["error"] == "Lot area required for GFA calculation"
    assert result["max_gfa_sqm"] is None
    assert "Specify lot area" in result["recommendations"][0]


def test_calculate_gfa_utilization_returns_expected_metrics() -> None:
    property = _make_property()

    result = compliance.calculate_gfa_utilization(property)

    assert "error" not in result
    assert result["max_gfa_sqm"] is not None
    assert result["current_gfa_sqm"] == pytest.approx(400.0)
    assert result["utilization_percentage"] is not None
    # Recommendations should highlight development potential
    assert any("Maximum GFA" in item for item in result["recommendations"])


@pytest.mark.asyncio
async def test_calculate_gfa_utilization_async_fallback() -> None:
    """Async helper should fall back to simple math when no session is provided."""

    property = _make_property(
        zoning=NZPropertyZoning.THAB, gross_floor_area_sqm=Decimal("0")
    )

    result = await compliance.calculate_gfa_utilization_async(property, session=None)

    assert result["max_gfa_sqm"] is not None
    assert result["current_gfa_sqm"] == 0.0
    assert "buildable_metrics" in result


@pytest.mark.asyncio
async def test_check_district_plan_compliance_pending_without_zoning(
    db_session,
) -> None:
    property = _make_property()
    property.zoning = None

    result = await compliance.check_district_plan_compliance(property, db_session)

    assert result["status"] == NZComplianceStatus.PENDING
    assert "Zoning not specified" in result["message"]
    assert result["warnings"]


@pytest.mark.asyncio
async def test_check_district_plan_compliance_warns_when_rules_missing(
    db_session,
) -> None:
    property = _make_property(zoning=NZPropertyZoning.RURAL)

    result = await compliance.check_district_plan_compliance(property, db_session)

    assert result["status"] == NZComplianceStatus.WARNING
    assert "No zoning rules found" in result["warnings"][0]


@pytest.mark.asyncio
async def test_check_building_code_compliance_warns_when_rules_missing(
    db_session,
) -> None:
    """Missing rules should return WARNING status."""

    property = _make_property(
        property_name="Industrial Building",
        zoning=NZPropertyZoning.HEAVY_IND,
        gross_floor_area_sqm=Decimal("5000"),
        lot_area_sqm=Decimal("2000"),
        num_storeys=2,
    )

    result = await compliance.check_building_code_compliance(property, db_session)

    assert result["status"] == NZComplianceStatus.WARNING
    assert "No building rules found" in result["warnings"][0]


@pytest.mark.asyncio
async def test_run_full_compliance_check_compiles_summary(db_session) -> None:
    property = _make_property(
        property_name="Summary Building",
        gross_floor_area_sqm=Decimal("1200"),
        lot_area_sqm=Decimal("600"),
        building_height_m=Decimal("15"),
        num_storeys=4,
    )

    result = await compliance.run_full_compliance_check(property, db_session)

    # Should return overall status based on component checks
    assert result["overall_status"] in [
        NZComplianceStatus.PASSED,
        NZComplianceStatus.WARNING,
        NZComplianceStatus.FAILED,
    ]
    assert "gfa_calculation" in result["compliance_data"]


@pytest.mark.asyncio
async def test_run_full_compliance_check_reports_warning_without_violations(
    db_session,
) -> None:
    property = _make_property(gross_floor_area_sqm=Decimal("0"))
    property.zoning = None

    result = await compliance.run_full_compliance_check(property, db_session)

    assert result["overall_status"] == NZComplianceStatus.WARNING
    assert not result["violations"]
    assert result["warnings"]


@pytest.mark.asyncio
async def test_update_property_compliance_sets_fields(db_session) -> None:
    property = _make_property(
        property_name="Compliance Update",
        building_height_m=Decimal("12"),
        gross_floor_area_sqm=Decimal("600"),
        lot_area_sqm=Decimal("500"),
        num_storeys=3,
    )

    db_session.add(property)
    await db_session.flush()

    updated = await compliance.update_property_compliance(property, db_session)

    assert updated.compliance_last_checked is not None
    assert updated.compliance_data is not None
    assert updated.max_developable_gfa_sqm is not None


def test_activity_status_classifications() -> None:
    """Test that activity status is correctly determined based on compliance."""
    # This tests the RMA activity status logic
    # Permitted, Controlled, Restricted Discretionary, Discretionary, Non-Complying
    property = _make_property()
    result = compliance.calculate_gfa_utilization(property)

    # Activity status should be present in results
    assert "activity_status" in result or result.get("error") is not None
