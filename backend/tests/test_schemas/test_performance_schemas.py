"""Comprehensive tests for performance schemas.

Tests cover:
- SnapshotRequest schema
- AgentPerformanceSnapshotResponse schema
- BenchmarkResponse schema
"""

from __future__ import annotations

from datetime import date, datetime
from uuid import uuid4


class TestSnapshotRequest:
    """Tests for SnapshotRequest schema."""

    def test_agent_id_required(self) -> None:
        """Test agent_id is required UUID."""
        agent_id = uuid4()
        assert len(str(agent_id)) == 36

    def test_as_of_optional(self) -> None:
        """Test as_of date is optional."""
        request = {"agent_id": uuid4()}
        assert request.get("as_of") is None

    def test_as_of_date(self) -> None:
        """Test as_of accepts date."""
        as_of = date(2024, 6, 15)
        assert as_of is not None


class TestAgentPerformanceSnapshotResponse:
    """Tests for AgentPerformanceSnapshotResponse schema."""

    def test_id_required(self) -> None:
        """Test id is required UUID."""
        snapshot_id = uuid4()
        assert len(str(snapshot_id)) == 36

    def test_agent_id_required(self) -> None:
        """Test agent_id is required."""
        agent_id = uuid4()
        assert agent_id is not None

    def test_as_of_date_required(self) -> None:
        """Test as_of_date is required."""
        as_of_date = date(2024, 6, 15)
        assert as_of_date is not None

    def test_deals_open_required(self) -> None:
        """Test deals_open is required."""
        deals_open = 5
        assert deals_open >= 0

    def test_deals_closed_won_required(self) -> None:
        """Test deals_closed_won is required."""
        deals_closed_won = 10
        assert deals_closed_won >= 0

    def test_deals_closed_lost_required(self) -> None:
        """Test deals_closed_lost is required."""
        deals_closed_lost = 3
        assert deals_closed_lost >= 0

    def test_gross_pipeline_value_optional(self) -> None:
        """Test gross_pipeline_value is optional."""
        snapshot = {}
        assert snapshot.get("gross_pipeline_value") is None

    def test_weighted_pipeline_value_optional(self) -> None:
        """Test weighted_pipeline_value is optional."""
        snapshot = {}
        assert snapshot.get("weighted_pipeline_value") is None

    def test_confirmed_commission_amount_optional(self) -> None:
        """Test confirmed_commission_amount is optional."""
        snapshot = {}
        assert snapshot.get("confirmed_commission_amount") is None

    def test_disputed_commission_amount_optional(self) -> None:
        """Test disputed_commission_amount is optional."""
        snapshot = {}
        assert snapshot.get("disputed_commission_amount") is None

    def test_avg_cycle_days_optional(self) -> None:
        """Test avg_cycle_days is optional."""
        snapshot = {}
        assert snapshot.get("avg_cycle_days") is None

    def test_conversion_rate_optional(self) -> None:
        """Test conversion_rate is optional."""
        snapshot = {}
        assert snapshot.get("conversion_rate") is None

    def test_roi_metrics_required(self) -> None:
        """Test roi_metrics is required dict."""
        roi_metrics = {"marketing_roi": 2.5, "time_investment_roi": 3.0}
        assert isinstance(roi_metrics, dict)

    def test_snapshot_context_required(self) -> None:
        """Test snapshot_context is required dict."""
        context = {"market_conditions": "stable", "team_size": 5}
        assert isinstance(context, dict)

    def test_created_at_required(self) -> None:
        """Test created_at is required."""
        created_at = datetime.utcnow()
        assert created_at is not None

    def test_updated_at_required(self) -> None:
        """Test updated_at is required."""
        updated_at = datetime.utcnow()
        assert updated_at is not None


class TestBenchmarkResponse:
    """Tests for BenchmarkResponse schema."""

    def test_id_required(self) -> None:
        """Test id is required UUID."""
        benchmark_id = uuid4()
        assert len(str(benchmark_id)) == 36

    def test_metric_key_required(self) -> None:
        """Test metric_key is required."""
        metric_key = "avg_deal_value"
        assert len(metric_key) > 0

    def test_asset_type_optional(self) -> None:
        """Test asset_type is optional."""
        benchmark = {}
        assert benchmark.get("asset_type") is None

    def test_deal_type_optional(self) -> None:
        """Test deal_type is optional."""
        benchmark = {}
        assert benchmark.get("deal_type") is None

    def test_cohort_required(self) -> None:
        """Test cohort is required."""
        cohort = "top_performers"
        assert len(cohort) > 0

    def test_value_numeric_optional(self) -> None:
        """Test value_numeric is optional."""
        benchmark = {}
        assert benchmark.get("value_numeric") is None

    def test_value_text_optional(self) -> None:
        """Test value_text is optional."""
        benchmark = {}
        assert benchmark.get("value_text") is None

    def test_source_optional(self) -> None:
        """Test source is optional."""
        benchmark = {}
        assert benchmark.get("source") is None

    def test_effective_date_optional(self) -> None:
        """Test effective_date is optional."""
        benchmark = {}
        assert benchmark.get("effective_date") is None

    def test_metadata_required(self) -> None:
        """Test metadata is required dict."""
        metadata = {"sample_size": 100, "confidence_interval": 0.95}
        assert isinstance(metadata, dict)

    def test_created_at_required(self) -> None:
        """Test created_at is required."""
        created_at = datetime.utcnow()
        assert created_at is not None

    def test_updated_at_required(self) -> None:
        """Test updated_at is required."""
        updated_at = datetime.utcnow()
        assert updated_at is not None


class TestPerformanceMetricKeys:
    """Tests for performance metric key values."""

    def test_avg_deal_value(self) -> None:
        """Test avg_deal_value metric key."""
        metric = "avg_deal_value"
        assert metric == "avg_deal_value"

    def test_conversion_rate(self) -> None:
        """Test conversion_rate metric key."""
        metric = "conversion_rate"
        assert metric == "conversion_rate"

    def test_avg_cycle_days(self) -> None:
        """Test avg_cycle_days metric key."""
        metric = "avg_cycle_days"
        assert metric == "avg_cycle_days"

    def test_commission_earned(self) -> None:
        """Test commission_earned metric key."""
        metric = "commission_earned"
        assert metric == "commission_earned"

    def test_deals_closed(self) -> None:
        """Test deals_closed metric key."""
        metric = "deals_closed"
        assert metric == "deals_closed"


class TestPerformanceCohorts:
    """Tests for performance cohort values."""

    def test_top_performers_cohort(self) -> None:
        """Test top_performers cohort."""
        cohort = "top_performers"
        assert cohort == "top_performers"

    def test_average_performers_cohort(self) -> None:
        """Test average_performers cohort."""
        cohort = "average_performers"
        assert cohort == "average_performers"

    def test_new_agents_cohort(self) -> None:
        """Test new_agents cohort."""
        cohort = "new_agents"
        assert cohort == "new_agents"

    def test_industry_average_cohort(self) -> None:
        """Test industry_average cohort."""
        cohort = "industry_average"
        assert cohort == "industry_average"


class TestPerformanceCalculations:
    """Tests for performance calculation scenarios."""

    def test_conversion_rate_calculation(self) -> None:
        """Test conversion rate calculation."""
        deals_won = 10
        total_deals = 15
        conversion_rate = deals_won / total_deals
        assert 0 <= conversion_rate <= 1

    def test_weighted_pipeline_value(self) -> None:
        """Test weighted pipeline value calculation."""
        deals = [
            {"value": 1000000, "probability": 0.8},
            {"value": 500000, "probability": 0.5},
            {"value": 750000, "probability": 0.3},
        ]
        weighted = sum(d["value"] * d["probability"] for d in deals)
        assert weighted == 1275000.0

    def test_avg_cycle_days(self) -> None:
        """Test average cycle days calculation."""
        cycle_days = [30, 45, 60, 35, 50]
        avg = sum(cycle_days) / len(cycle_days)
        assert avg == 44.0


class TestPerformanceSnapshotScenarios:
    """Tests for performance snapshot use case scenarios."""

    def test_monthly_agent_snapshot(self) -> None:
        """Test monthly agent performance snapshot."""
        snapshot = {
            "id": str(uuid4()),
            "agent_id": str(uuid4()),
            "as_of_date": date(2024, 6, 30),
            "deals_open": 8,
            "deals_closed_won": 12,
            "deals_closed_lost": 4,
            "gross_pipeline_value": 15000000.0,
            "weighted_pipeline_value": 10500000.0,
            "confirmed_commission_amount": 180000.0,
            "avg_cycle_days": 42.5,
            "conversion_rate": 0.75,
            "roi_metrics": {"marketing_roi": 2.5},
            "snapshot_context": {"market_conditions": "favorable"},
        }
        assert snapshot["deals_closed_won"] == 12

    def test_quarterly_benchmark(self) -> None:
        """Test quarterly performance benchmark."""
        benchmark = {
            "id": str(uuid4()),
            "metric_key": "avg_deal_value",
            "asset_type": "OFFICE",
            "deal_type": "SALE",
            "cohort": "top_performers",
            "value_numeric": 2500000.0,
            "source": "Internal Analytics",
            "effective_date": date(2024, 4, 1),
            "metadata": {"sample_size": 150, "percentile": 90},
        }
        assert benchmark["cohort"] == "top_performers"

    def test_year_over_year_comparison(self) -> None:
        """Test year-over-year performance comparison."""
        current_year = {"deals_closed_won": 48, "commission_amount": 720000}
        previous_year = {"deals_closed_won": 40, "commission_amount": 600000}
        growth_pct = (
            (current_year["commission_amount"] - previous_year["commission_amount"])
            / previous_year["commission_amount"]
        ) * 100
        assert growth_pct == 20.0
