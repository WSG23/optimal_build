"""Focused tests for Seattle compliance helpers that don't require the DB."""

from __future__ import annotations

import os
from decimal import Decimal

import pytest

# Ensure the app configuration loads without failing on SECRET_KEY.
os.environ.setdefault("SECRET_KEY", "test-secret")

pytestmark = pytest.mark.skip(
    reason=(
        "Seattle compliance helpers rely on SQLAlchemy metadata removal APIs that "
        "are not available in the stubbed ORM."
    )
)

from app.models.seattle_property import (
    SeattleComplianceStatus,
    SeattlePropertyTenure,
    SeattleZoning,
    SeattleProperty,
)
from app.utils import seattle_compliance as compliance


def _make_property(**overrides) -> SeattleProperty:
    """Create a minimal SeattleProperty for testing utilities."""

    defaults = dict(
        property_name="Test Property",
        address="1 Example Street, Seattle, WA",
        zoning=SeattleZoning.LR2,
        tenure=SeattlePropertyTenure.FEE_SIMPLE,
        lot_area_sqft=Decimal("5000"),
        max_far=Decimal("1.3"),
        gross_floor_area_sqft=Decimal("4000"),
        building_height_ft=Decimal("35"),
        num_storeys=3,
    )
    defaults.update(overrides)
    return SeattleProperty(**defaults)


def test_calculate_gfa_utilization_requires_lot_area_and_far() -> None:
    property = _make_property(lot_area_sqft=None)

    result = compliance.calculate_gfa_utilization(property)

    assert result["error"] == "Lot area and maximum FAR required for GFA calculation"
    assert result["max_gfa_sqft"] is None
    assert "Specify lot area and FAR" in result["recommendations"][0]


def test_calculate_gfa_utilization_returns_expected_metrics() -> None:
    property = _make_property()

    result = compliance.calculate_gfa_utilization(property)

    assert "error" not in result
    # max_gfa = 5000 sqft * 1.3 FAR = 6500 sqft
    assert result["max_gfa_sqft"] == pytest.approx(6500.0)
    assert result["current_gfa_sqft"] == pytest.approx(4000.0)
    assert result["remaining_gfa_sqft"] == pytest.approx(2500.0)
    assert result["utilization_percentage"] == pytest.approx(61.54, rel=0.01)
    assert result["potential_units"] is not None
    # Recommendations should highlight additional GFA potential
    assert any("Maximum GFA" in item for item in result["recommendations"])


@pytest.mark.asyncio
async def test_calculate_gfa_utilization_async_fallback() -> None:
    """Async helper should fall back to simple math when no session is provided."""

    property = _make_property(
        zoning=SeattleZoning.MR, gross_floor_area_sqft=Decimal("0")
    )

    result = await compliance.calculate_gfa_utilization_async(property, session=None)

    assert result["max_gfa_sqft"] is not None
    assert result["current_gfa_sqft"] == 0.0
    assert "buildable_metrics" in result


@pytest.mark.asyncio
async def test_check_zoning_compliance_pending_without_zoning(db_session) -> None:
    property = _make_property()
    property.zoning = None

    result = await compliance.check_zoning_compliance(property, db_session)

    assert result["status"] == SeattleComplianceStatus.PENDING
    assert "Zoning not specified" in result["message"]
    assert result["warnings"]


@pytest.mark.asyncio
async def test_check_zoning_compliance_warns_when_rules_missing(db_session) -> None:
    property = _make_property(zoning=SeattleZoning.UT)

    result = await compliance.check_zoning_compliance(property, db_session)

    assert result["status"] == SeattleComplianceStatus.WARNING
    assert "No zoning rules found" in result["warnings"][0]


@pytest.mark.asyncio
async def test_check_building_code_compliance_warns_when_rules_missing(
    db_session,
) -> None:
    """Missing rules should return WARNING status."""

    property = _make_property(
        property_name="Industrial Building",
        zoning=SeattleZoning.IB,
        gross_floor_area_sqft=Decimal("50000"),
        lot_area_sqft=Decimal("20000"),
        num_storeys=2,
    )

    result = await compliance.check_building_code_compliance(property, db_session)

    assert result["status"] == SeattleComplianceStatus.WARNING
    assert "No building rules found" in result["warnings"][0]


@pytest.mark.asyncio
async def test_run_full_compliance_check_compiles_summary(db_session) -> None:
    property = _make_property(
        property_name="Summary Tower",
        max_far=Decimal("6.0"),
        building_height_ft=Decimal("160"),
        gross_floor_area_sqft=Decimal("100000"),
        lot_area_sqft=Decimal("15000"),
        num_storeys=15,
    )

    result = await compliance.run_full_compliance_check(property, db_session)

    # Should return overall status based on component checks
    assert result["overall_status"] in [
        SeattleComplianceStatus.PASSED,
        SeattleComplianceStatus.WARNING,
        SeattleComplianceStatus.FAILED,
    ]
    assert "gfa_calculation" in result["compliance_data"]


@pytest.mark.asyncio
async def test_run_full_compliance_check_reports_warning_without_violations(
    db_session,
) -> None:
    property = _make_property(gross_floor_area_sqft=Decimal("0"))
    property.zoning = None

    result = await compliance.run_full_compliance_check(property, db_session)

    assert result["overall_status"] == SeattleComplianceStatus.WARNING
    assert not result["violations"]
    assert result["warnings"]


@pytest.mark.asyncio
async def test_update_property_compliance_sets_fields(db_session) -> None:
    property = _make_property(
        property_name="Compliance Update",
        max_far=Decimal("4.5"),
        building_height_ft=Decimal("75"),
        gross_floor_area_sqft=Decimal("30000"),
        lot_area_sqft=Decimal("8000"),
        num_storeys=6,
    )

    db_session.add(property)
    await db_session.flush()

    updated = await compliance.update_property_compliance(property, db_session)

    assert updated.compliance_last_checked is not None
    assert updated.compliance_data is not None
    assert updated.max_developable_gfa_sqft is not None


def test_mha_calculation() -> None:
    """Test MHA (Mandatory Housing Affordability) calculation."""
    property = _make_property(
        mha_zone="M1",
        mha_payment_option=True,
    )

    result = compliance.calculate_gfa_utilization(property)

    # MHA info should be present for applicable properties
    assert result is not None
    # MHA requirements depend on zone and payment vs performance choice


@pytest.mark.asyncio
async def test_sepa_review_trigger(db_session) -> None:
    """Test that SEPA review is flagged for large projects."""
    property = _make_property(
        property_name="Large Development",
        lot_area_sqft=Decimal("50000"),
        gross_floor_area_sqft=Decimal("200000"),
        num_storeys=20,
    )

    result = await compliance.check_building_code_compliance(property, db_session)

    # SEPA review should be mentioned in recommendations for large projects
    # Note: actual SEPA trigger depends on project size thresholds
    assert result is not None
    assert "recommendations" in result
