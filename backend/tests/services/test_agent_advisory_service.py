"""Comprehensive tests for the AgentAdvisoryService."""

from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.services.agents.advisory import AgentAdvisoryService, AdvisorySummary


# ============================================================================
# HELPER CLASSES FOR STUBBING
# ============================================================================


class _StubResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value


class _StubSession:
    def __init__(self, property_exists=True):
        self.property_exists = property_exists
        self.added = []
        self.committed = False
        self.refreshed = []

    async def execute(self, stmt):
        return _StubResult(uuid4() if self.property_exists else None)

    def add(self, obj):
        self.added.append(obj)

    async def commit(self):
        self.committed = True

    async def refresh(self, obj):
        obj.created_at = datetime(2025, 1, 1, 12, 0, 0)
        self.refreshed.append(obj)


# ============================================================================
# ADVISORY SUMMARY TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_build_summary_handles_conservation(monkeypatch):
    """Test build_summary includes conservation notes and correct market tier."""
    service = AgentAdvisoryService()
    property_id = uuid4()
    property_record = SimpleNamespace(
        id=property_id,
        property_type="historic_mixed",
        gross_floor_area_sqm=None,
        land_area_sqm=2500,
        plot_ratio=3.2,
        is_conservation=True,
        district="D11",
        units_total=40,
    )

    monkeypatch.setattr(
        service, "_get_property", AsyncMock(return_value=property_record)
    )
    monkeypatch.setattr(
        service,
        "_list_feedback",
        AsyncMock(return_value=[{"id": str(uuid4()), "notes": "Great potential"}]),
    )

    summary = await service.build_summary(property_id=property_id, session=None)
    payload = summary.to_dict()

    assert payload["asset_mix"]["notes"]  # conservation note added
    assert payload["market_positioning"]["market_tier"] == "Core Central Region"
    assert payload["absorption_forecast"]["monthly_velocity_target"] == 4
    assert payload["feedback"][0]["notes"] == "Great potential"


@pytest.mark.asyncio
async def test_build_summary_with_office_property(monkeypatch):
    """Test build_summary generates correct asset mix for office property."""
    service = AgentAdvisoryService()
    property_id = uuid4()
    property_record = SimpleNamespace(
        id=property_id,
        property_type="office",
        gross_floor_area_sqm=10000,
        land_area_sqm=2000,
        plot_ratio=5.0,
        is_conservation=False,
        district="D01",
        units_total=50,
    )

    monkeypatch.setattr(
        service, "_get_property", AsyncMock(return_value=property_record)
    )
    monkeypatch.setattr(service, "_list_feedback", AsyncMock(return_value=[]))

    summary = await service.build_summary(property_id=property_id, session=None)
    payload = summary.to_dict()

    # Verify office-specific asset mix recommendations
    mix_recs = payload["asset_mix"]["mix_recommendations"]
    use_types = [rec["use"] for rec in mix_recs]
    assert "office" in use_types
    assert "flex workspace" in use_types

    # Verify Prime CBD market tier for D01
    assert payload["market_positioning"]["market_tier"] == "Prime CBD"


@pytest.mark.asyncio
async def test_build_summary_with_retail_property(monkeypatch):
    """Test build_summary generates correct asset mix for retail property."""
    service = AgentAdvisoryService()
    property_id = uuid4()
    property_record = SimpleNamespace(
        id=property_id,
        property_type="retail",
        gross_floor_area_sqm=5000,
        land_area_sqm=1000,
        plot_ratio=5.0,
        is_conservation=False,
        district="D06",
        units_total=30,
    )

    monkeypatch.setattr(
        service, "_get_property", AsyncMock(return_value=property_record)
    )
    monkeypatch.setattr(service, "_list_feedback", AsyncMock(return_value=[]))

    summary = await service.build_summary(property_id=property_id, session=None)
    payload = summary.to_dict()

    # Verify retail-specific asset mix
    mix_recs = payload["asset_mix"]["mix_recommendations"]
    use_types = [rec["use"] for rec in mix_recs]
    assert "anchor retail" in use_types
    assert "specialty retail" in use_types


@pytest.mark.asyncio
async def test_build_summary_with_residential_property(monkeypatch):
    """Test build_summary generates correct asset mix for residential property."""
    service = AgentAdvisoryService()
    property_id = uuid4()
    property_record = SimpleNamespace(
        id=property_id,
        property_type="residential",
        gross_floor_area_sqm=8000,
        land_area_sqm=2000,
        plot_ratio=4.0,
        is_conservation=False,
        district="D09",
        units_total=80,
    )

    monkeypatch.setattr(
        service, "_get_property", AsyncMock(return_value=property_record)
    )
    monkeypatch.setattr(service, "_list_feedback", AsyncMock(return_value=[]))

    summary = await service.build_summary(property_id=property_id, session=None)
    payload = summary.to_dict()

    # Verify residential velocity (highest at 8 units/month)
    assert payload["absorption_forecast"]["monthly_velocity_target"] == 8


@pytest.mark.asyncio
async def test_build_summary_with_industrial_property(monkeypatch):
    """Test build_summary generates correct asset mix for industrial property."""
    service = AgentAdvisoryService()
    property_id = uuid4()
    property_record = SimpleNamespace(
        id=property_id,
        property_type="industrial",
        gross_floor_area_sqm=20000,
        land_area_sqm=10000,
        plot_ratio=2.0,
        is_conservation=False,
        district="D20",
        units_total=20,
    )

    monkeypatch.setattr(
        service, "_get_property", AsyncMock(return_value=property_record)
    )
    monkeypatch.setattr(service, "_list_feedback", AsyncMock(return_value=[]))

    summary = await service.build_summary(property_id=property_id, session=None)
    payload = summary.to_dict()

    # Verify industrial-specific asset mix
    mix_recs = payload["asset_mix"]["mix_recommendations"]
    use_types = [rec["use"] for rec in mix_recs]
    assert "production" in use_types
    assert "high-spec logistics" in use_types

    # Verify industrial velocity (lowest at 2 units/month)
    assert payload["absorption_forecast"]["monthly_velocity_target"] == 2


@pytest.mark.asyncio
async def test_build_summary_calculates_gfa_from_land_and_plot_ratio(monkeypatch):
    """Test that GFA is calculated from land area * plot ratio when GFA is missing."""
    service = AgentAdvisoryService()
    property_id = uuid4()
    property_record = SimpleNamespace(
        id=property_id,
        property_type="mixed_use",
        gross_floor_area_sqm=None,  # Not provided
        land_area_sqm=5000,
        plot_ratio=4.0,
        is_conservation=False,
        district="D02",
        units_total=100,
    )

    monkeypatch.setattr(
        service, "_get_property", AsyncMock(return_value=property_record)
    )
    monkeypatch.setattr(service, "_list_feedback", AsyncMock(return_value=[]))

    summary = await service.build_summary(property_id=property_id, session=None)
    payload = summary.to_dict()

    # GFA should be calculated as 5000 * 4.0 = 20000
    assert payload["asset_mix"]["total_programmable_gfa_sqm"] == 20000.0


# ============================================================================
# FEEDBACK TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_record_feedback_persists(monkeypatch):
    """Test record_feedback creates and persists feedback record."""
    service = AgentAdvisoryService()
    session = _StubSession(property_exists=True)
    property_id = uuid4()

    feedback = await service.record_feedback(
        property_id=property_id,
        session=session,
        submitted_by="agent@example.com",
        sentiment="positive",
        notes="Strong investor demand",
        metadata={"channel": "call"},
    )

    assert session.added
    assert session.committed
    assert feedback["sentiment"] == "positive"
    assert "created_at" in feedback


@pytest.mark.asyncio
async def test_record_feedback_raises_when_property_missing():
    """Test record_feedback raises ValueError when property doesn't exist."""
    service = AgentAdvisoryService()
    session = _StubSession(property_exists=False)

    with pytest.raises(ValueError):
        await service.record_feedback(
            property_id=uuid4(),
            session=session,
            submitted_by=None,
            sentiment="neutral",
            notes="No property located",
        )


@pytest.mark.asyncio
async def test_record_feedback_with_channel(monkeypatch):
    """Test record_feedback includes channel in the response."""
    service = AgentAdvisoryService()
    session = _StubSession(property_exists=True)
    property_id = uuid4()

    feedback = await service.record_feedback(
        property_id=property_id,
        session=session,
        submitted_by="agent@example.com",
        sentiment="negative",
        notes="Price concerns",
        channel="email",
        metadata={"source": "client inquiry"},
    )

    assert feedback["sentiment"] == "negative"
    assert feedback["notes"] == "Price concerns"


# ============================================================================
# SALES VELOCITY TESTS
# ============================================================================


class TestBuildSalesVelocity:
    """Tests for the build_sales_velocity method."""

    def test_sales_velocity_default_singapore_jurisdiction(self):
        """Test sales velocity uses Singapore defaults."""
        service = AgentAdvisoryService()
        payload = {"jurisdiction": "SG", "asset_type": "residential"}

        result = service.build_sales_velocity(payload)

        assert result["context"]["jurisdiction"] == "SG"
        assert result["benchmarks"]["velocity_median"] == 24
        assert result["benchmarks"]["median_psf"] == 2050

    def test_sales_velocity_with_sea_jurisdiction(self):
        """Test sales velocity uses SEA defaults."""
        service = AgentAdvisoryService()
        payload = {"jurisdiction": "SEA", "asset_type": "condo"}

        result = service.build_sales_velocity(payload)

        assert result["context"]["jurisdiction"] == "SEA"
        assert result["benchmarks"]["velocity_median"] == 20
        assert result["benchmarks"]["median_psf"] == 780

    def test_sales_velocity_with_hk_jurisdiction(self):
        """Test sales velocity uses Hong Kong defaults."""
        service = AgentAdvisoryService()
        payload = {"jurisdiction": "HK", "asset_type": "residential"}

        result = service.build_sales_velocity(payload)

        assert result["context"]["jurisdiction"] == "HK"
        assert result["benchmarks"]["velocity_median"] == 18
        assert result["benchmarks"]["inventory_months"] == 11.0

    def test_sales_velocity_applies_asset_multiplier_for_office(self):
        """Test that office assets get lower velocity multiplier."""
        service = AgentAdvisoryService()
        payload = {"jurisdiction": "SG", "asset_type": "office"}

        result = service.build_sales_velocity(payload)

        # Office multiplier is 0.75, so velocity = 24 * 0.75 = 18
        assert result["forecast"]["velocity_units_per_month"] == 18.0

    def test_sales_velocity_applies_asset_multiplier_for_industrial(self):
        """Test that industrial assets get lowest velocity multiplier."""
        service = AgentAdvisoryService()
        payload = {"jurisdiction": "SG", "asset_type": "industrial"}

        result = service.build_sales_velocity(payload)

        # Industrial multiplier is 0.65, so velocity = 24 * 0.65 = 15.6
        assert result["forecast"]["velocity_units_per_month"] == 15.6

    def test_sales_velocity_uses_recent_absorption_override(self):
        """Test that recent_absorption overrides calculated velocity."""
        service = AgentAdvisoryService()
        payload = {
            "jurisdiction": "SG",
            "asset_type": "residential",
            "recent_absorption": 30,
        }

        result = service.build_sales_velocity(payload)

        assert result["forecast"]["velocity_units_per_month"] == 30.0
        # Higher confidence when recent_absorption is provided
        assert result["forecast"]["confidence"] >= 0.70

    def test_sales_velocity_uses_camel_case_fields(self):
        """Test that camelCase field names are accepted."""
        service = AgentAdvisoryService()
        payload = {
            "jurisdiction": "SG",
            "assetType": "mixed_use",
            "priceBand": "luxury",
            "unitsPlanned": 100,
            "launchWindow": "Q2 2025",
            "inventoryMonths": 10.0,
        }

        result = service.build_sales_velocity(payload)

        assert result["context"]["asset_type"] == "mixed_use"
        assert result["context"]["price_band"] == "luxury"
        assert result["context"]["units_planned"] == 100
        assert result["context"]["launch_window"] == "Q2 2025"
        assert result["benchmarks"]["inventory_months"] == 10.0

    def test_sales_velocity_includes_oversupply_risk(self):
        """Test that high inventory triggers oversupply risk warning."""
        service = AgentAdvisoryService()
        payload = {
            "jurisdiction": "SG",
            "asset_type": "residential",
            "inventory_months": 50,  # Very high inventory
        }

        result = service.build_sales_velocity(payload)

        risks = [r["label"] for r in result["risks"]]
        assert "Oversupply" in risks

    def test_sales_velocity_includes_price_sensitivity_risk(self):
        """Test that price band triggers price sensitivity warning."""
        service = AgentAdvisoryService()
        payload = {
            "jurisdiction": "SG",
            "asset_type": "residential",
            "price_band": "luxury",
        }

        result = service.build_sales_velocity(payload)

        risks = [r["label"] for r in result["risks"]]
        assert "Price sensitivity" in risks

    def test_sales_velocity_recommends_phased_launch(self):
        """Test that long absorption triggers phased launch recommendation."""
        service = AgentAdvisoryService()
        payload = {
            "jurisdiction": "SG",
            "asset_type": "industrial",  # Low velocity
            "inventory_months": 24,  # High inventory
        }

        result = service.build_sales_velocity(payload)

        assert any("tranches" in rec for rec in result["recommendations"])

    def test_sales_velocity_applies_benchmark_overrides(self):
        """Test that benchmark overrides are applied correctly."""
        service = AgentAdvisoryService()
        payload = {
            "jurisdiction": "SG",
            "asset_type": "residential",
            "benchmarks_override": {
                "velocityPctl25": 10,
                "velocityMedian": 15,
                "velocityPctl75": 20,
                "medianPsf": 1500,
            },
        }

        result = service.build_sales_velocity(payload)

        assert result["benchmarks"]["velocity_p25"] == 10
        assert result["benchmarks"]["velocity_median"] == 15
        assert result["benchmarks"]["velocity_p75"] == 20
        assert result["benchmarks"]["median_psf"] == 1500

    def test_sales_velocity_uses_camel_case_benchmark_overrides(self):
        """Test that camelCase benchmark overrides work."""
        service = AgentAdvisoryService()
        payload = {
            "jurisdiction": "SG",
            "asset_type": "residential",
            "benchmarksOverride": {
                "velocityPctl25": 12,
                "velocityMedian": 18,
            },
        }

        result = service.build_sales_velocity(payload)

        assert result["benchmarks"]["velocity_p25"] == 12
        assert result["benchmarks"]["velocity_median"] == 18

    def test_sales_velocity_unknown_jurisdiction_uses_sg_defaults(self):
        """Test that unknown jurisdiction falls back to SG defaults."""
        service = AgentAdvisoryService()
        payload = {"jurisdiction": "UNKNOWN", "asset_type": "residential"}

        result = service.build_sales_velocity(payload)

        # Should use SG defaults
        assert result["benchmarks"]["velocity_median"] == 24


# ============================================================================
# MARKET TIER TESTS
# ============================================================================


class TestDetermineMarketTier:
    """Tests for market tier determination logic."""

    def test_prime_cbd_for_d01(self):
        """Test D01 returns Prime CBD tier."""
        service = AgentAdvisoryService()
        tier = service._determine_market_tier("D01")
        assert tier == "Prime CBD"

    def test_prime_cbd_for_d02(self):
        """Test D02 returns Prime CBD tier."""
        service = AgentAdvisoryService()
        tier = service._determine_market_tier("D02")
        assert tier == "Prime CBD"

    def test_prime_cbd_for_d06(self):
        """Test D06 returns Prime CBD tier."""
        service = AgentAdvisoryService()
        tier = service._determine_market_tier("D06")
        assert tier == "Prime CBD"

    def test_core_central_for_d09(self):
        """Test D09 returns Core Central Region tier."""
        service = AgentAdvisoryService()
        tier = service._determine_market_tier("D09")
        assert tier == "Core Central Region"

    def test_core_central_for_d10(self):
        """Test D10 returns Core Central Region tier."""
        service = AgentAdvisoryService()
        tier = service._determine_market_tier("D10")
        assert tier == "Core Central Region"

    def test_rest_of_central_for_numbered_district(self):
        """Test numbered district outside prime/core returns Rest of Central Region."""
        service = AgentAdvisoryService()
        tier = service._determine_market_tier("D15")
        assert tier == "Rest of Central Region"

    def test_island_wide_for_non_numbered_district(self):
        """Test non-numbered district returns Singapore Island-wide."""
        service = AgentAdvisoryService()
        tier = service._determine_market_tier("Sentosa")
        assert tier == "Singapore Island-wide"

    def test_core_cbd_for_none_district(self):
        """Test None district defaults to Core CBD."""
        service = AgentAdvisoryService()
        tier = service._determine_market_tier(None)
        assert tier == "Core CBD"


# ============================================================================
# ADVISORY SUMMARY DATACLASS TESTS
# ============================================================================


class TestAdvisorySummary:
    """Tests for the AdvisorySummary dataclass."""

    def test_to_dict_returns_all_fields(self):
        """Test that to_dict returns all expected fields."""
        summary = AdvisorySummary(
            asset_mix={"mix": "data"},
            market_positioning={"positioning": "data"},
            absorption_forecast={"forecast": "data"},
            feedback=[{"id": "1", "notes": "test"}],
        )

        result = summary.to_dict()

        assert "asset_mix" in result
        assert "market_positioning" in result
        assert "absorption_forecast" in result
        assert "feedback" in result
        assert result["asset_mix"] == {"mix": "data"}

    def test_to_dict_is_json_serializable(self):
        """Test that to_dict output is JSON serializable."""
        import json

        summary = AdvisorySummary(
            asset_mix={"total_gfa": 10000},
            market_positioning={"tier": "Prime CBD"},
            absorption_forecast={"months": 12},
            feedback=[],
        )

        result = summary.to_dict()

        # Should not raise
        json_str = json.dumps(result)
        assert json_str is not None
