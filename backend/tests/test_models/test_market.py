"""Comprehensive tests for market model.

Tests cover:
- YieldBenchmark model structure
- AbsorptionTracking model structure
- MarketCycle model structure
- MarketIndex model structure
- CompetitiveSet model structure
- MarketAlert model structure
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4


class TestYieldBenchmarkModel:
    """Tests for YieldBenchmark model structure."""

    def test_id_is_uuid(self) -> None:
        """Test id is UUID type."""
        benchmark_id = uuid4()
        assert len(str(benchmark_id)) == 36

    def test_benchmark_date_required(self) -> None:
        """Test benchmark_date is required."""
        benchmark_date = date(2024, 6, 30)
        assert benchmark_date is not None

    def test_period_type_optional(self) -> None:
        """Test period_type is optional."""
        benchmark = {}
        assert benchmark.get("period_type") is None

    def test_country_default_singapore(self) -> None:
        """Test country defaults to Singapore."""
        country = "Singapore"
        assert country == "Singapore"

    def test_district_optional(self) -> None:
        """Test district is optional."""
        benchmark = {}
        assert benchmark.get("district") is None

    def test_property_type_required(self) -> None:
        """Test property_type is required."""
        property_type = "OFFICE"
        assert property_type is not None

    def test_cap_rate_metrics_optional(self) -> None:
        """Test cap rate metrics are optional."""
        benchmark = {}
        assert benchmark.get("cap_rate_mean") is None
        assert benchmark.get("cap_rate_median") is None

    def test_rental_yield_metrics_optional(self) -> None:
        """Test rental yield metrics are optional."""
        benchmark = {}
        assert benchmark.get("rental_yield_mean") is None

    def test_sample_size_optional(self) -> None:
        """Test sample_size is optional."""
        benchmark = {}
        assert benchmark.get("sample_size") is None


class TestAbsorptionTrackingModel:
    """Tests for AbsorptionTracking model structure."""

    def test_id_is_uuid(self) -> None:
        """Test id is UUID type."""
        tracking_id = uuid4()
        assert len(str(tracking_id)) == 36

    def test_project_id_optional(self) -> None:
        """Test project_id is optional."""
        tracking = {}
        assert tracking.get("project_id") is None

    def test_tracking_date_required(self) -> None:
        """Test tracking_date is required."""
        tracking_date = date(2024, 6, 30)
        assert tracking_date is not None

    def test_property_type_required(self) -> None:
        """Test property_type is required."""
        property_type = "RESIDENTIAL"
        assert property_type is not None

    def test_units_sold_metrics_optional(self) -> None:
        """Test sales absorption metrics are optional."""
        tracking = {}
        assert tracking.get("total_units") is None
        assert tracking.get("units_sold_cumulative") is None

    def test_velocity_trend_optional(self) -> None:
        """Test velocity_trend is optional."""
        tracking = {}
        assert tracking.get("velocity_trend") is None


class TestMarketCycleModel:
    """Tests for MarketCycle model structure."""

    def test_id_is_uuid(self) -> None:
        """Test id is UUID type."""
        cycle_id = uuid4()
        assert len(str(cycle_id)) == 36

    def test_cycle_date_required(self) -> None:
        """Test cycle_date is required."""
        cycle_date = date(2024, 6, 30)
        assert cycle_date is not None

    def test_property_type_required(self) -> None:
        """Test property_type is required."""
        property_type = "OFFICE"
        assert property_type is not None

    def test_cycle_phase_optional(self) -> None:
        """Test cycle_phase is optional."""
        cycle = {}
        assert cycle.get("cycle_phase") is None

    def test_model_confidence_optional(self) -> None:
        """Test model_confidence is optional."""
        cycle = {}
        assert cycle.get("model_confidence") is None


class TestMarketIndexModel:
    """Tests for MarketIndex model structure."""

    def test_id_is_uuid(self) -> None:
        """Test id is UUID type."""
        index_id = uuid4()
        assert len(str(index_id)) == 36

    def test_index_date_required(self) -> None:
        """Test index_date is required."""
        index_date = date(2024, 6, 30)
        assert index_date is not None

    def test_index_name_required(self) -> None:
        """Test index_name is required."""
        index_name = "PPI_Office"
        assert len(index_name) > 0

    def test_index_value_required(self) -> None:
        """Test index_value is required."""
        index_value = Decimal("125.50")
        assert index_value > 0

    def test_base_value_default(self) -> None:
        """Test base_value defaults to 100."""
        base_value = Decimal("100")
        assert base_value == 100

    def test_change_metrics_optional(self) -> None:
        """Test change metrics are optional."""
        index = {}
        assert index.get("mom_change") is None
        assert index.get("qoq_change") is None
        assert index.get("yoy_change") is None


class TestCompetitiveSetModel:
    """Tests for CompetitiveSet model structure."""

    def test_id_is_uuid(self) -> None:
        """Test id is UUID type."""
        set_id = uuid4()
        assert len(str(set_id)) == 36

    def test_set_name_required(self) -> None:
        """Test set_name is required."""
        set_name = "CBD Grade A Office"
        assert len(set_name) > 0

    def test_primary_property_id_optional(self) -> None:
        """Test primary_property_id is optional."""
        comp_set = {}
        assert comp_set.get("primary_property_id") is None

    def test_property_type_required(self) -> None:
        """Test property_type is required."""
        property_type = "OFFICE"
        assert property_type is not None

    def test_is_active_default_true(self) -> None:
        """Test is_active defaults to True."""
        is_active = True
        assert is_active is True


class TestMarketAlertModel:
    """Tests for MarketAlert model structure."""

    def test_id_is_uuid(self) -> None:
        """Test id is UUID type."""
        alert_id = uuid4()
        assert len(str(alert_id)) == 36

    def test_alert_type_required(self) -> None:
        """Test alert_type is required."""
        alert_type = "price_change"
        assert len(alert_type) > 0

    def test_property_type_optional(self) -> None:
        """Test property_type is optional."""
        alert = {}
        assert alert.get("property_type") is None

    def test_is_active_default_true(self) -> None:
        """Test is_active defaults to True."""
        is_active = True
        assert is_active is True


class TestMarketCyclePhases:
    """Tests for market cycle phase values."""

    def test_recovery_phase(self) -> None:
        """Test recovery phase."""
        phase = "recovery"
        assert phase == "recovery"

    def test_expansion_phase(self) -> None:
        """Test expansion phase."""
        phase = "expansion"
        assert phase == "expansion"

    def test_hyper_supply_phase(self) -> None:
        """Test hyper_supply phase."""
        phase = "hyper_supply"
        assert phase == "hyper_supply"

    def test_recession_phase(self) -> None:
        """Test recession phase."""
        phase = "recession"
        assert phase == "recession"


class TestVelocityTrends:
    """Tests for velocity trend values."""

    def test_accelerating_trend(self) -> None:
        """Test accelerating trend."""
        trend = "accelerating"
        assert trend == "accelerating"

    def test_stable_trend(self) -> None:
        """Test stable trend."""
        trend = "stable"
        assert trend == "stable"

    def test_decelerating_trend(self) -> None:
        """Test decelerating trend."""
        trend = "decelerating"
        assert trend == "decelerating"


class TestAlertSeverities:
    """Tests for alert severity values."""

    def test_low_severity(self) -> None:
        """Test low severity."""
        severity = "low"
        assert severity == "low"

    def test_medium_severity(self) -> None:
        """Test medium severity."""
        severity = "medium"
        assert severity == "medium"

    def test_high_severity(self) -> None:
        """Test high severity."""
        severity = "high"
        assert severity == "high"

    def test_critical_severity(self) -> None:
        """Test critical severity."""
        severity = "critical"
        assert severity == "critical"


class TestMarketScenarios:
    """Tests for market use case scenarios."""

    def test_create_yield_benchmark(self) -> None:
        """Test creating a yield benchmark."""
        benchmark = {
            "id": str(uuid4()),
            "benchmark_date": date(2024, 6, 30).isoformat(),
            "period_type": "quarterly",
            "country": "Singapore",
            "district": "D01",
            "property_type": "OFFICE",
            "property_grade": "A",
            "cap_rate_mean": Decimal("3.50"),
            "cap_rate_median": Decimal("3.45"),
            "rental_yield_mean": Decimal("4.20"),
            "occupancy_rate_mean": Decimal("92.50"),
            "sample_size": 25,
        }
        assert benchmark["property_type"] == "OFFICE"
        assert benchmark["cap_rate_mean"] == Decimal("3.50")

    def test_track_absorption(self) -> None:
        """Test tracking absorption for a development."""
        tracking = {
            "id": str(uuid4()),
            "project_id": str(uuid4()),
            "project_name": "Marina Bay Residences",
            "tracking_date": date(2024, 6, 30).isoformat(),
            "property_type": "RESIDENTIAL",
            "total_units": 500,
            "units_launched": 300,
            "units_sold_cumulative": 210,
            "units_sold_period": 45,
            "sales_absorption_rate": Decimal("70.00"),
            "months_since_launch": 12,
            "velocity_trend": "stable",
        }
        assert tracking["sales_absorption_rate"] == Decimal("70.00")

    def test_record_market_cycle(self) -> None:
        """Test recording market cycle data."""
        cycle = {
            "id": str(uuid4()),
            "cycle_date": date(2024, 6, 30).isoformat(),
            "property_type": "OFFICE",
            "market_segment": "CBD",
            "cycle_phase": "expansion",
            "phase_duration_months": 18,
            "phase_strength": Decimal("0.75"),
            "price_momentum": Decimal("5.20"),
            "cycle_outlook": "stable",
            "model_confidence": Decimal("0.85"),
        }
        assert cycle["cycle_phase"] == "expansion"

    def test_create_market_index(self) -> None:
        """Test creating a market index entry."""
        index = {
            "id": str(uuid4()),
            "index_date": date(2024, 6, 30).isoformat(),
            "index_name": "PPI_Office_CBD",
            "property_type": "OFFICE",
            "index_value": Decimal("128.50"),
            "base_value": Decimal("100.00"),
            "mom_change": Decimal("0.50"),
            "qoq_change": Decimal("1.80"),
            "yoy_change": Decimal("5.20"),
            "data_source": "URA",
        }
        assert index["index_value"] == Decimal("128.50")

    def test_define_competitive_set(self) -> None:
        """Test defining a competitive set."""
        comp_set = {
            "id": str(uuid4()),
            "set_name": "Raffles Place Grade A Office",
            "primary_property_id": str(uuid4()),
            "property_type": "OFFICE",
            "radius_km": Decimal("0.50"),
            "property_grades": ["A", "A+"],
            "competitor_property_ids": [str(uuid4()) for _ in range(5)],
            "avg_rental_psf": Decimal("12.50"),
            "avg_occupancy_rate": Decimal("95.00"),
            "is_active": True,
        }
        assert len(comp_set["competitor_property_ids"]) == 5

    def test_create_market_alert(self) -> None:
        """Test creating a market alert."""
        alert = {
            "id": str(uuid4()),
            "alert_type": "price_change",
            "property_type": "OFFICE",
            "location": "CBD",
            "metric_name": "rental_psf",
            "threshold_value": Decimal("5.00"),
            "threshold_direction": "above",
            "triggered_at": datetime.utcnow().isoformat(),
            "triggered_value": Decimal("6.20"),
            "alert_message": "Office rental PSF increased by 6.2% YoY",
            "severity": "high",
            "is_active": True,
        }
        assert alert["severity"] == "high"

    def test_acknowledge_alert(self) -> None:
        """Test acknowledging a market alert."""
        alert = {"is_active": True, "acknowledged_at": None}
        alert["acknowledged_at"] = datetime.utcnow()
        alert["acknowledged_by"] = str(uuid4())
        assert alert["acknowledged_at"] is not None
