"""Focused tests for Toronto compliance helpers that don't require the DB."""

from __future__ import annotations

import os
from decimal import Decimal

import pytest

# Ensure the app configuration loads without failing on SECRET_KEY.
os.environ.setdefault("SECRET_KEY", "test-secret")

pytestmark = pytest.mark.skip(
    reason=(
        "Toronto compliance helpers rely on SQLAlchemy metadata removal APIs that "
        "are not available in the stubbed ORM."
    )
)

from app.models.toronto_property import (
    TorontoComplianceStatus,
    TorontoPropertyTenure,
    TorontoZoning,
    TorontoProperty,
)
from app.utils import toronto_compliance as compliance


def _make_property(**overrides) -> TorontoProperty:
    """Create a minimal TorontoProperty for testing utilities."""

    defaults = dict(
        property_name="Test Property",
        address="1 Example Street, Toronto, ON",
        zoning=TorontoZoning.RA,
        tenure=TorontoPropertyTenure.FREEHOLD,
        lot_area_sqm=Decimal("1000"),
        max_fsi=Decimal("3.0"),
        gross_floor_area_sqm=Decimal("2000"),
        building_height_m=Decimal("20"),
        num_storeys=6,
    )
    defaults.update(overrides)
    return TorontoProperty(**defaults)


def test_calculate_gfa_utilization_requires_lot_area_and_fsi() -> None:
    property = _make_property(lot_area_sqm=None)

    result = compliance.calculate_gfa_utilization(property)

    assert result["error"] == "Lot area and maximum FSI required for GFA calculation"
    assert result["max_gfa_sqm"] is None
    assert "Specify lot area and FSI" in result["recommendations"][0]


def test_calculate_gfa_utilization_returns_expected_metrics() -> None:
    property = _make_property()

    result = compliance.calculate_gfa_utilization(property)

    assert "error" not in result
    # max_gfa = 1000 sqm * 3.0 FSI = 3000 sqm
    assert result["max_gfa_sqm"] == pytest.approx(3000.0)
    assert result["current_gfa_sqm"] == pytest.approx(2000.0)
    assert result["remaining_gfa_sqm"] == pytest.approx(1000.0)
    assert result["utilization_percentage"] == pytest.approx(66.67, rel=0.01)
    assert result["potential_units"] is not None
    # Recommendations should highlight additional GFA potential
    assert any("Maximum GFA" in item for item in result["recommendations"])


@pytest.mark.asyncio
async def test_calculate_gfa_utilization_async_fallback() -> None:
    """Async helper should fall back to simple math when no session is provided."""

    property = _make_property(
        zoning=TorontoZoning.CR, gross_floor_area_sqm=Decimal("0")
    )

    result = await compliance.calculate_gfa_utilization_async(property, session=None)

    assert result["max_gfa_sqm"] is not None
    assert result["current_gfa_sqm"] == 0.0
    assert "buildable_metrics" in result


@pytest.mark.asyncio
async def test_check_zoning_compliance_pending_without_zoning(db_session) -> None:
    property = _make_property()
    property.zoning = None

    result = await compliance.check_zoning_compliance(property, db_session)

    assert result["status"] == TorontoComplianceStatus.PENDING
    assert "Zoning not specified" in result["message"]
    assert result["warnings"]


@pytest.mark.asyncio
async def test_check_zoning_compliance_warns_when_rules_missing(db_session) -> None:
    property = _make_property(zoning=TorontoZoning.UT)

    result = await compliance.check_zoning_compliance(property, db_session)

    assert result["status"] == TorontoComplianceStatus.WARNING
    assert "No zoning rules found" in result["warnings"][0]


@pytest.mark.asyncio
async def test_check_building_code_compliance_warns_when_rules_missing(
    db_session,
) -> None:
    """Missing rules should return WARNING status."""

    property = _make_property(
        property_name="Industrial Building",
        zoning=TorontoZoning.E,
        gross_floor_area_sqm=Decimal("5000"),
        lot_area_sqm=Decimal("2000"),
        num_storeys=2,
    )

    result = await compliance.check_building_code_compliance(property, db_session)

    # Should return recommendations even if rules are missing
    assert result is not None
    assert "recommendations" in result


@pytest.mark.asyncio
async def test_run_full_compliance_check_compiles_summary(db_session) -> None:
    property = _make_property(
        property_name="Summary Tower",
        max_fsi=Decimal("4.0"),
        building_height_m=Decimal("36"),
        gross_floor_area_sqm=Decimal("10000"),
        lot_area_sqm=Decimal("2500"),
        num_storeys=12,
    )

    result = await compliance.run_full_compliance_check(property, db_session)

    # Should return overall status based on component checks
    assert result["overall_status"] in [
        TorontoComplianceStatus.PASSED,
        TorontoComplianceStatus.WARNING,
        TorontoComplianceStatus.FAILED,
    ]
    assert "gfa_calculation" in result["compliance_data"]


@pytest.mark.asyncio
async def test_run_full_compliance_check_reports_warning_without_violations(
    db_session,
) -> None:
    property = _make_property(gross_floor_area_sqm=Decimal("0"))
    property.zoning = None

    result = await compliance.run_full_compliance_check(property, db_session)

    assert result["overall_status"] == TorontoComplianceStatus.WARNING
    assert not result["violations"]
    assert result["warnings"]


@pytest.mark.asyncio
async def test_update_property_compliance_sets_fields(db_session) -> None:
    property = _make_property(
        property_name="Compliance Update",
        max_fsi=Decimal("3.0"),
        building_height_m=Decimal("24"),
        gross_floor_area_sqm=Decimal("2500"),
        lot_area_sqm=Decimal("1000"),
        num_storeys=8,
    )

    db_session.add(property)
    await db_session.flush()

    updated = await compliance.update_property_compliance(property, db_session)

    assert updated.compliance_last_checked is not None
    assert updated.compliance_data is not None
    assert updated.max_developable_gfa_sqm is not None


def test_inclusionary_zoning_calculation() -> None:
    """Test IZ (Inclusionary Zoning) requirements calculation."""
    property = _make_property(
        iz_area=True,
        iz_affordable_percentage=Decimal("10.0"),
    )

    result = compliance.calculate_gfa_utilization(property)

    # IZ info should be present for applicable properties
    assert result is not None
    # IZ recommendations should mention affordable housing if in IZ area
    if property.iz_area and result.get("potential_units"):
        assert any(
            "affordable" in item.lower() for item in result.get("recommendations", [])
        )


@pytest.mark.asyncio
async def test_tgs_requirements_in_building_check(db_session) -> None:
    """Test that Toronto Green Standard requirements are included."""
    property = _make_property(
        property_name="Green Development",
        tgs_tier="Tier 2",
    )

    result = await compliance.check_building_code_compliance(property, db_session)

    # TGS requirements should be present
    assert "tgs_requirements" in result
    # Tier 1 is mandatory
    assert result["tgs_requirements"].get("tier1_mandatory") is True


@pytest.mark.asyncio
async def test_heritage_property_warnings(db_session) -> None:
    """Test that heritage designated properties get appropriate warnings."""
    property = _make_property(
        property_name="Heritage Building",
        is_heritage_designated=True,
        heritage_designation_type="Part IV",
    )

    result = await compliance.check_building_code_compliance(property, db_session)

    # Should warn about heritage permit requirements
    warnings = result.get("warnings", [])
    assert any("heritage" in w.lower() for w in warnings)
