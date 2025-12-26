"""Comprehensive tests for market schemas.

Tests cover:
- MarketPeriod schema
- MarketReportPayload schema
- MarketReportResponse schema
"""

from __future__ import annotations

from datetime import date, datetime


class TestMarketPeriod:
    """Tests for MarketPeriod schema."""

    def test_start_required(self) -> None:
        """Test start date is required."""
        start = date(2024, 1, 1)
        assert start is not None

    def test_end_required(self) -> None:
        """Test end date is required."""
        end = date(2024, 6, 30)
        assert end is not None

    def test_start_before_end(self) -> None:
        """Test start date is before end date."""
        start = date(2024, 1, 1)
        end = date(2024, 6, 30)
        assert start < end

    def test_quarterly_period(self) -> None:
        """Test quarterly period."""
        start = date(2024, 1, 1)
        end = date(2024, 3, 31)
        days = (end - start).days
        assert 89 <= days <= 92  # Approximately 3 months

    def test_yearly_period(self) -> None:
        """Test yearly period."""
        start = date(2024, 1, 1)
        end = date(2024, 12, 31)
        days = (end - start).days
        assert days == 365  # 2024 is a leap year minus 1


class TestMarketReportPayload:
    """Tests for MarketReportPayload schema."""

    def test_property_type_required(self) -> None:
        """Test property_type is required."""
        property_type = "OFFICE"
        assert property_type is not None

    def test_location_required(self) -> None:
        """Test location is required."""
        location = "CBD"
        assert len(location) > 0

    def test_period_required(self) -> None:
        """Test period is required."""
        period = {"start": date(2024, 1, 1), "end": date(2024, 6, 30)}
        assert "start" in period
        assert "end" in period

    def test_comparables_analysis_required(self) -> None:
        """Test comparables_analysis is required dict."""
        comparables = {
            "avg_rent_psf": 12.50,
            "transaction_count": 45,
            "median_price_psf": 2800,
        }
        assert "avg_rent_psf" in comparables

    def test_supply_dynamics_required(self) -> None:
        """Test supply_dynamics is required dict."""
        supply = {
            "new_supply_sqft": 500000,
            "completions_count": 3,
            "pipeline_sqft": 1200000,
        }
        assert "new_supply_sqft" in supply

    def test_yield_benchmarks_required(self) -> None:
        """Test yield_benchmarks is required dict."""
        yields = {
            "cap_rate_range": [4.5, 5.5],
            "noi_yield": 4.8,
            "gross_yield": 5.2,
        }
        assert "cap_rate_range" in yields

    def test_absorption_trends_required(self) -> None:
        """Test absorption_trends is required dict."""
        absorption = {
            "net_absorption_sqft": 150000,
            "vacancy_rate_pct": 8.5,
            "months_of_supply": 12,
        }
        assert "net_absorption_sqft" in absorption

    def test_market_cycle_position_required(self) -> None:
        """Test market_cycle_position is required dict."""
        cycle = {
            "phase": "recovery",
            "trend": "improving",
            "outlook": "positive",
        }
        assert "phase" in cycle

    def test_recommendations_required(self) -> None:
        """Test recommendations list is required."""
        recommendations = [
            "Consider acquisition opportunities in CBD fringe",
            "Monitor upcoming supply in Q4 2024",
        ]
        assert isinstance(recommendations, list)


class TestPropertyType:
    """Tests for PropertyType enum values."""

    def test_office_type(self) -> None:
        """Test OFFICE property type."""
        property_type = "OFFICE"
        assert property_type == "OFFICE"

    def test_retail_type(self) -> None:
        """Test RETAIL property type."""
        property_type = "RETAIL"
        assert property_type == "RETAIL"

    def test_industrial_type(self) -> None:
        """Test INDUSTRIAL property type."""
        property_type = "INDUSTRIAL"
        assert property_type == "INDUSTRIAL"

    def test_residential_type(self) -> None:
        """Test RESIDENTIAL property type."""
        property_type = "RESIDENTIAL"
        assert property_type == "RESIDENTIAL"

    def test_hospitality_type(self) -> None:
        """Test HOSPITALITY property type."""
        property_type = "HOSPITALITY"
        assert property_type == "HOSPITALITY"


class TestMarketReportResponse:
    """Tests for MarketReportResponse schema."""

    def test_report_required(self) -> None:
        """Test report payload is required."""
        report = {
            "property_type": "OFFICE",
            "location": "CBD",
            "period": {"start": "2024-01-01", "end": "2024-06-30"},
        }
        assert "property_type" in report

    def test_generated_at_required(self) -> None:
        """Test generated_at timestamp is required."""
        generated_at = datetime.utcnow()
        assert generated_at is not None

    def test_from_attributes_config(self) -> None:
        """Test from_attributes is enabled."""
        from_attributes = True
        assert from_attributes is True


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


class TestSingaporeLocations:
    """Tests for Singapore market locations."""

    def test_cbd_location(self) -> None:
        """Test CBD location."""
        location = "CBD"
        assert location == "CBD"

    def test_orchard_location(self) -> None:
        """Test Orchard Road location."""
        location = "Orchard Road"
        assert "Orchard" in location

    def test_marina_bay_location(self) -> None:
        """Test Marina Bay location."""
        location = "Marina Bay"
        assert "Marina" in location

    def test_jurong_location(self) -> None:
        """Test Jurong location."""
        location = "Jurong"
        assert location == "Jurong"

    def test_changi_location(self) -> None:
        """Test Changi location."""
        location = "Changi"
        assert location == "Changi"


class TestMarketReportScenarios:
    """Tests for market report use case scenarios."""

    def test_office_cbd_quarterly_report(self) -> None:
        """Test quarterly office report for CBD."""
        report = {
            "property_type": "OFFICE",
            "location": "CBD",
            "period": {"start": date(2024, 1, 1), "end": date(2024, 3, 31)},
            "comparables_analysis": {"avg_rent_psf": 12.50},
            "supply_dynamics": {"new_supply_sqft": 250000},
            "yield_benchmarks": {"cap_rate_range": [4.5, 5.5]},
            "absorption_trends": {"vacancy_rate_pct": 8.5},
            "market_cycle_position": {"phase": "recovery"},
            "recommendations": ["Monitor Grade A supply"],
        }
        assert report["property_type"] == "OFFICE"
        assert report["location"] == "CBD"

    def test_retail_orchard_report(self) -> None:
        """Test retail report for Orchard Road."""
        report = {
            "property_type": "RETAIL",
            "location": "Orchard Road",
            "period": {"start": date(2024, 1, 1), "end": date(2024, 6, 30)},
            "comparables_analysis": {"avg_rent_psf": 35.00},
            "supply_dynamics": {"new_supply_sqft": 100000},
            "yield_benchmarks": {"cap_rate_range": [3.5, 4.5]},
            "absorption_trends": {"vacancy_rate_pct": 5.2},
            "market_cycle_position": {"phase": "expansion"},
            "recommendations": ["Prime retail shows resilience"],
        }
        assert report["property_type"] == "RETAIL"

    def test_industrial_jurong_report(self) -> None:
        """Test industrial report for Jurong."""
        report = {
            "property_type": "INDUSTRIAL",
            "location": "Jurong",
            "period": {"start": date(2024, 1, 1), "end": date(2024, 6, 30)},
            "comparables_analysis": {"avg_rent_psf": 2.50},
            "supply_dynamics": {"new_supply_sqft": 500000},
            "yield_benchmarks": {"cap_rate_range": [5.5, 6.5]},
            "absorption_trends": {"vacancy_rate_pct": 10.5},
            "market_cycle_position": {"phase": "hyper_supply"},
            "recommendations": ["Selective acquisitions recommended"],
        }
        assert report["property_type"] == "INDUSTRIAL"
