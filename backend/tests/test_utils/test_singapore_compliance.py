"""Focused tests for Singapore compliance helpers that don't require the DB."""

from __future__ import annotations

import os
from decimal import Decimal

import pytest

# Ensure the app configuration loads without failing on SECRET_KEY.
os.environ.setdefault("SECRET_KEY", "test-secret")

pytestmark = pytest.mark.skip(
    reason=(
        "Singapore compliance helpers rely on SQLAlchemy metadata removal APIs that "
        "are not available in the stubbed ORM."
    )
)

from app.models.singapore_property import (
    ComplianceStatus,
    PropertyZoning,
    SingaporeProperty,
)
from app.utils import singapore_compliance as compliance


def _make_property(**overrides) -> SingaporeProperty:
    """Create a minimal SingaporeProperty for testing utilities."""

    defaults = dict(
        property_name="Test Property",
        address="1 Example Street",
        zoning=PropertyZoning.RESIDENTIAL,
        land_area_sqm=Decimal("1000"),
        gross_plot_ratio=Decimal("2.5"),
        gross_floor_area_sqm=Decimal("1200"),
        num_storeys=12,
    )
    defaults.update(overrides)
    return SingaporeProperty(**defaults)


def test_calculate_gfa_utilization_requires_land_area_and_plot_ratio() -> None:
    property = _make_property(land_area_sqm=None)

    result = compliance.calculate_gfa_utilization(property)

    assert result["error"] == "Land area and plot ratio required for GFA calculation"
    assert result["max_gfa_sqm"] is None
    assert "Specify land area and plot ratio" in result["recommendations"][0]


def test_calculate_gfa_utilization_returns_expected_metrics() -> None:
    property = _make_property()

    result = compliance.calculate_gfa_utilization(property)

    assert "error" not in result
    assert result["max_gfa_sqm"] == pytest.approx(2500.0)
    assert result["current_gfa_sqm"] == pytest.approx(1200.0)
    assert result["remaining_gfa_sqm"] == pytest.approx(1300.0)
    assert result["utilization_percentage"] == pytest.approx(48.0)
    assert result["potential_units"] == 18
    metrics = result["buildable_metrics"]
    assert metrics["nsa_estimate_sqm"] == int(2500 * 0.82)
    assert metrics["efficiency_ratio"] == pytest.approx(0.82)
    # Recommendations should highlight additional GFA potential.
    assert any("You can build up to" in item for item in result["recommendations"])


@pytest.mark.asyncio
async def test_calculate_gfa_utilization_async_fallback() -> None:
    """Async helper should fall back to simple math when no session is provided."""

    property = _make_property(
        zoning=PropertyZoning.MIXED_USE, gross_floor_area_sqm=Decimal("0")
    )

    result = await compliance.calculate_gfa_utilization_async(property, session=None)

    assert result["max_gfa_sqm"] == pytest.approx(2500.0)
    assert result["current_gfa_sqm"] == 0.0
    assert result["remaining_gfa_sqm"] == pytest.approx(2500.0)
    assert result["potential_units"] == int(2500 / 70)
    assert "buildable_metrics" in result
    assert result["buildable_metrics"]["floors_max"] == property.num_storeys


@pytest.mark.asyncio
async def test_calculate_gfa_utilization_async_handles_non_residential() -> None:
    """Non-residential zoning should not produce a potential unit estimate."""

    property = _make_property(
        zoning=PropertyZoning.COMMERCIAL,
        gross_floor_area_sqm=Decimal("2000"),
    )

    result = await compliance.calculate_gfa_utilization_async(property, session=None)

    assert result["potential_units"] is None
    assert any("Current utilization" in item for item in result["recommendations"])


@pytest.mark.asyncio
async def test_check_ura_compliance_detects_height_and_far_violations(
    db_session, singapore_rules
) -> None:
    """URA compliance should flag violations when property exceeds limits."""

    property = _make_property(
        property_name="Violation Tower",
        gross_plot_ratio=Decimal("3.2"),
        building_height_m=Decimal("40"),
        gross_floor_area_sqm=Decimal("3000"),
        land_area_sqm=Decimal("800"),
    )

    result = await compliance.check_ura_compliance(property, db_session)

    assert result["status"] == ComplianceStatus.FAILED
    assert any("Plot ratio" in message for message in result["violations"])
    assert any("Building height" in message for message in result["violations"])


@pytest.mark.asyncio
async def test_check_ura_compliance_pending_without_zoning(db_session) -> None:
    property = _make_property()
    property.zoning = None

    result = await compliance.check_ura_compliance(property, db_session)

    assert result["status"] == ComplianceStatus.PENDING
    assert "Zoning not specified" in result["message"]
    assert result["warnings"]


@pytest.mark.asyncio
async def test_check_ura_compliance_warns_when_rules_missing(db_session) -> None:
    property = _make_property(zoning=PropertyZoning.BUSINESS_PARK)

    result = await compliance.check_ura_compliance(property, db_session)

    assert result["status"] == ComplianceStatus.WARNING
    assert "No zoning rules found" in result["warnings"][0]


@pytest.mark.asyncio
async def test_check_bca_compliance_detects_site_coverage_violation(
    db_session, singapore_rules
) -> None:
    """BCA compliance should fail when site coverage exceeds the limit."""

    property = _make_property(
        property_name="Coverage Plaza",
        gross_floor_area_sqm=Decimal("10000"),
        land_area_sqm=Decimal("1000"),
        num_storeys=2,
    )

    result = await compliance.check_bca_compliance(property, db_session)

    assert result["status"] == ComplianceStatus.FAILED
    assert any("Site coverage" in message for message in result["violations"])
    assert "BCA Green Mark" in result["recommendations"][0]


@pytest.mark.asyncio
async def test_check_bca_compliance_warns_when_rules_missing(db_session) -> None:
    """Missing rules should return WARNING status."""

    property = _make_property(
        property_name="Industrial Shed",
        zoning=PropertyZoning.BUSINESS_PARK,
        gross_floor_area_sqm=Decimal("1000"),
        land_area_sqm=Decimal("1000"),
        num_storeys=1,
    )

    result = await compliance.check_bca_compliance(property, db_session)

    assert result["status"] == ComplianceStatus.WARNING
    assert "No building rules found" in result["warnings"][0]


@pytest.mark.asyncio
async def test_run_full_compliance_check_compiles_summary(
    db_session, singapore_rules
) -> None:
    property = _make_property(
        property_name="Summary Tower",
        gross_plot_ratio=Decimal("3.0"),
        building_height_m=Decimal("50"),
        gross_floor_area_sqm=Decimal("9000"),
        land_area_sqm=Decimal("1000"),
        num_storeys=3,
    )

    result = await compliance.run_full_compliance_check(property, db_session)

    assert result["overall_status"] == ComplianceStatus.FAILED
    assert result["bca_status"] == ComplianceStatus.FAILED
    assert result["ura_status"] == ComplianceStatus.FAILED
    assert result["violations"]
    assert "gfa_calculation" in result["compliance_data"]


@pytest.mark.asyncio
async def test_run_full_compliance_check_reports_warning_without_violations(
    db_session,
) -> None:
    property = _make_property(gross_floor_area_sqm=Decimal("0"))
    property.zoning = None

    result = await compliance.run_full_compliance_check(property, db_session)

    assert result["overall_status"] == ComplianceStatus.WARNING
    assert not result["violations"]
    assert result["warnings"]
    assert "Warning:" in (result["compliance_notes"] or "")


@pytest.mark.asyncio
async def test_update_property_compliance_sets_fields(
    db_session, singapore_rules
) -> None:
    property = _make_property(
        property_name="Compliance Update",
        gross_plot_ratio=Decimal("3.0"),
        building_height_m=Decimal("50"),
        gross_floor_area_sqm=Decimal("5000"),
        land_area_sqm=Decimal("800"),
        num_storeys=2,
    )

    db_session.add(property)
    await db_session.flush()

    updated = await compliance.update_property_compliance(property, db_session)

    assert updated.bca_compliance_status == ComplianceStatus.FAILED.value
    assert updated.ura_compliance_status == ComplianceStatus.FAILED.value
    assert updated.compliance_last_checked is not None
    assert updated.compliance_data is not None
    assert updated.max_developable_gfa_sqm is not None


@pytest.mark.asyncio
async def test_update_property_compliance_skips_gfa_metrics_without_inputs(
    db_session, singapore_rules
) -> None:
    property = _make_property(land_area_sqm=None)
    property.gross_floor_area_sqm = Decimal("0")

    db_session.add(property)
    await db_session.flush()

    updated = await compliance.update_property_compliance(property, db_session)

    assert updated.max_developable_gfa_sqm is None
    assert updated.gfa_utilization_percentage is None


@pytest.mark.asyncio
async def test_calculate_gfa_utilization_async_with_session(
    monkeypatch, db_session
) -> None:
    class _StubMetrics:
        def __init__(self) -> None:
            self.gfa_cap_m2 = 1500.0
            self.nsa_est_m2 = 1100
            self.floors_max = 5
            self.footprint_m2 = 300.0

    class _StubResult:
        metrics = _StubMetrics()

    async def fake_calculate_buildable(*args, **kwargs):
        return _StubResult()

    monkeypatch.setattr(
        "app.services.buildable.calculate_buildable",
        fake_calculate_buildable,
    )

    property = _make_property(
        land_area_sqm=Decimal("800"),
        gross_plot_ratio=Decimal("2.5"),
        gross_floor_area_sqm=Decimal("500"),
        num_storeys=5,
    )

    result = await compliance.calculate_gfa_utilization_async(
        property, session=db_session
    )

    assert result["buildable_metrics"]["nsa_estimate_sqm"] == 1100
    assert result["buildable_metrics"]["floors_max"] == 5


def test_run_full_compliance_check_sync_uses_wrapper(monkeypatch):
    property = _make_property()

    async def fake_run(property: SingaporeProperty, session: str) -> dict[str, str]:
        return {"overall_status": "ok", "session": session}

    async def fake_wrapper(callback):
        return await callback("session-token")

    monkeypatch.setattr(
        compliance,
        "run_full_compliance_check",
        fake_run,
    )
    monkeypatch.setattr(
        compliance,
        "_run_with_temporary_async_session",
        fake_wrapper,
    )

    result = compliance.run_full_compliance_check_sync(property)
    assert result == {"overall_status": "ok", "session": "session-token"}


def test_update_property_compliance_sync_uses_wrapper(monkeypatch):
    property = _make_property()

    async def fake_update(
        property: SingaporeProperty, session: str
    ) -> SingaporeProperty:
        property.compliance_notes = session
        return property

    async def fake_wrapper(callback):
        return await callback("wrapper-session")

    monkeypatch.setattr(compliance, "update_property_compliance", fake_update)
    monkeypatch.setattr(
        compliance,
        "_run_with_temporary_async_session",
        fake_wrapper,
    )

    updated = compliance.update_property_compliance_sync(property)
    assert updated.compliance_notes == "wrapper-session"
