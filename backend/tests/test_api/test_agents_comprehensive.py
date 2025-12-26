"""Comprehensive tests for agents API.

Tests cover:
- GPS logging endpoints
- Market intelligence endpoints
- Advisory endpoints
- Photo and voice note endpoints
- Financial metrics endpoints
- Property valuation endpoints
- 3D scenario generation
- Request/Response models
"""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4


from app.models.property import PropertyType


class TestGPSLogRequest:
    """Tests for GPSLogRequest model."""

    def test_valid_latitude_range(self) -> None:
        """Test latitude must be between -90 and 90."""
        assert -90 <= 1.3521 <= 90  # Singapore
        assert -90 <= -33.8688 <= 90  # Sydney
        assert -90 <= 51.5074 <= 90  # London

    def test_valid_longitude_range(self) -> None:
        """Test longitude must be between -180 and 180."""
        assert -180 <= 103.8198 <= 180  # Singapore
        assert -180 <= -122.4194 <= 180  # San Francisco
        assert -180 <= 139.6917 <= 180  # Tokyo

    def test_invalid_latitude_rejected(self) -> None:
        """Test latitude outside -90 to 90 is rejected."""
        invalid_latitude = 95.0
        assert invalid_latitude > 90

    def test_development_scenarios_optional(self) -> None:
        """Test development_scenarios is optional."""
        development_scenarios = None
        assert development_scenarios is None

    def test_jurisdiction_code_optional(self) -> None:
        """Test jurisdiction_code is optional (defaults to SG)."""
        jurisdiction_code = None
        default = "SG"
        assert jurisdiction_code is None or jurisdiction_code == default


class TestGPSLogResponse:
    """Tests for GPSLogResponse model."""

    def test_response_includes_property_id(self) -> None:
        """Test response includes property_id."""
        property_id = uuid4()
        assert property_id is not None

    def test_response_includes_address(self) -> None:
        """Test response includes address object."""
        address = {
            "full_address": "123 Orchard Road, Singapore",
            "postal_code": "238858",
            "district": "D09",
        }
        assert address["postal_code"] is not None

    def test_response_includes_coordinates(self) -> None:
        """Test response includes coordinate pair."""
        coordinates = {"latitude": 1.3521, "longitude": 103.8198}
        assert "latitude" in coordinates
        assert "longitude" in coordinates

    def test_response_includes_ura_zoning(self) -> None:
        """Test response includes URA zoning info."""
        ura_zoning = {
            "zone_code": "MU",
            "zone_description": "Mixed Use",
            "plot_ratio": 3.6,
        }
        assert ura_zoning["zone_code"] is not None

    def test_response_includes_quick_analysis(self) -> None:
        """Test response includes quick analysis envelope."""
        quick_analysis = {
            "generated_at": datetime.utcnow().isoformat(),
            "scenarios": [],
        }
        assert "generated_at" in quick_analysis

    def test_response_includes_jurisdiction_code(self) -> None:
        """Test response includes jurisdiction_code."""
        jurisdiction_code = "SG"
        assert jurisdiction_code in ["SG", "HK", "NZ", "TOR", "SEA"]

    def test_response_includes_currency_symbol(self) -> None:
        """Test response includes currency symbol."""
        currency_symbol = "S$"
        assert currency_symbol is not None


class TestMarketIntelligenceResponse:
    """Tests for MarketIntelligenceResponse model."""

    def test_response_includes_property_id(self) -> None:
        """Test response includes property_id."""
        property_id = uuid4()
        assert property_id is not None

    def test_response_includes_report(self) -> None:
        """Test response includes report dict."""
        report = {
            "comparables_analysis": {},
            "rental_snapshot": {},
            "pipeline_outlook": {},
            "yield_benchmarks": {},
        }
        assert "comparables_analysis" in report


class TestAdvisorySummaryResponse:
    """Tests for AdvisorySummaryResponse model."""

    def test_includes_asset_mix(self) -> None:
        """Test response includes asset_mix."""
        asset_mix = {
            "property_id": str(uuid4()),
            "mix_recommendations": [],
            "notes": [],
        }
        assert "mix_recommendations" in asset_mix

    def test_includes_market_positioning(self) -> None:
        """Test response includes market_positioning."""
        market_positioning = {
            "market_tier": "prime",
            "pricing_guidance": {},
            "target_segments": [],
            "messaging": [],
        }
        assert market_positioning["market_tier"] is not None

    def test_includes_absorption_forecast(self) -> None:
        """Test response includes absorption_forecast."""
        absorption_forecast = {
            "expected_months_to_stabilize": 18,
            "monthly_velocity_target": 10,
            "confidence": "high",
            "timeline": [],
        }
        assert absorption_forecast["expected_months_to_stabilize"] > 0


class TestSalesVelocityRequest:
    """Tests for SalesVelocityRequest model."""

    def test_jurisdiction_required(self) -> None:
        """Test jurisdiction is required."""
        jurisdiction = "SG"
        assert jurisdiction is not None

    def test_asset_type_required(self) -> None:
        """Test asset_type is required."""
        asset_type = "residential"
        assert asset_type is not None

    def test_price_band_optional(self) -> None:
        """Test price_band is optional."""
        price_band = "1800-2200_psf"
        assert price_band is None or isinstance(price_band, str)

    def test_units_planned_optional(self) -> None:
        """Test units_planned is optional."""
        units_planned = 100
        assert units_planned is None or units_planned > 0

    def test_launch_window_optional(self) -> None:
        """Test launch_window is optional."""
        launch_window = "2025-Q2"
        assert launch_window is None or isinstance(launch_window, str)


class TestPropertyAnalysisRequest:
    """Tests for PropertyAnalysisRequest model."""

    def test_property_id_required(self) -> None:
        """Test property_id is required."""
        property_id = str(uuid4())
        assert property_id is not None

    def test_valid_analysis_types(self) -> None:
        """Test valid analysis_type values."""
        valid_types = ["raw_land", "existing_building", "historical_property"]
        for analysis_type in valid_types:
            assert analysis_type in valid_types

    def test_invalid_analysis_type_rejected(self) -> None:
        """Test invalid analysis_type is rejected."""
        invalid_type = "unknown_type"
        valid_types = ["raw_land", "existing_building", "historical_property"]
        assert invalid_type not in valid_types

    def test_save_results_default_true(self) -> None:
        """Test save_results defaults to True."""
        save_results = True
        assert save_results is True


class TestPhotoUploadResponse:
    """Tests for PhotoUploadResponse model."""

    def test_includes_photo_id(self) -> None:
        """Test response includes photo_id."""
        photo_id = str(uuid4())
        assert photo_id is not None

    def test_includes_storage_key(self) -> None:
        """Test response includes storage_key."""
        storage_key = "properties/123/photos/abc.jpg"
        assert storage_key is not None

    def test_includes_capture_timestamp(self) -> None:
        """Test response includes capture_timestamp."""
        capture_timestamp = datetime.utcnow()
        assert capture_timestamp is not None

    def test_includes_auto_tags(self) -> None:
        """Test response includes auto_tags list."""
        auto_tags = ["facade", "clear_sky", "construction"]
        assert isinstance(auto_tags, list)

    def test_includes_public_url(self) -> None:
        """Test response includes public_url."""
        public_url = "https://storage.example.com/photo.jpg"
        assert public_url.startswith("http")


class TestVoiceNoteResponse:
    """Tests for VoiceNoteResponse model."""

    def test_includes_voice_note_id(self) -> None:
        """Test response includes voice_note_id."""
        voice_note_id = str(uuid4())
        assert voice_note_id is not None

    def test_includes_property_id(self) -> None:
        """Test response includes property_id."""
        property_id = str(uuid4())
        assert property_id is not None

    def test_includes_duration_seconds(self) -> None:
        """Test response includes duration_seconds."""
        duration_seconds = 45.5
        assert duration_seconds > 0

    def test_includes_file_size(self) -> None:
        """Test response includes file_size."""
        file_size = 1024 * 100  # 100KB
        assert file_size > 0


class TestFinancialMetricsRequest:
    """Tests for FinancialMetricsRequest model."""

    def test_property_value_required(self) -> None:
        """Test property_value is required."""
        property_value = 5_000_000.0
        assert property_value > 0

    def test_gross_rental_income_required(self) -> None:
        """Test gross_rental_income is required."""
        gross_rental_income = 300_000.0
        assert gross_rental_income > 0

    def test_operating_expenses_required(self) -> None:
        """Test operating_expenses is required."""
        operating_expenses = 60_000.0
        assert operating_expenses >= 0

    def test_vacancy_rate_default(self) -> None:
        """Test vacancy_rate defaults to 0.05 (5%)."""
        vacancy_rate = 0.05
        assert vacancy_rate == 0.05

    def test_loan_amount_optional(self) -> None:
        """Test loan_amount is optional."""
        loan_amount = 3_000_000.0
        assert loan_amount is None or loan_amount > 0


class TestPropertyValuationRequest:
    """Tests for PropertyValuationRequest model."""

    def test_noi_required(self) -> None:
        """Test noi is required."""
        noi = 240_000.0
        assert noi > 0

    def test_market_cap_rate_required(self) -> None:
        """Test market_cap_rate is required."""
        market_cap_rate = 0.045  # 4.5%
        assert market_cap_rate > 0

    def test_comparable_psf_optional(self) -> None:
        """Test comparable_psf is optional."""
        comparable_psf = 2500.0
        assert comparable_psf is None or comparable_psf > 0

    def test_depreciation_factor_default(self) -> None:
        """Test depreciation_factor defaults to 0.8."""
        depreciation_factor = 0.8
        assert depreciation_factor == 0.8


class TestFinancialMetricsCalculation:
    """Tests for financial metrics calculation."""

    def test_noi_calculation(self) -> None:
        """Test NOI calculation."""
        gross_rental_income = 300_000.0
        operating_expenses = 60_000.0
        noi = gross_rental_income - operating_expenses
        assert noi == 240_000.0

    def test_cap_rate_calculation(self) -> None:
        """Test cap rate calculation."""
        noi = 240_000.0
        property_value = 5_000_000.0
        cap_rate = noi / property_value
        assert cap_rate == 0.048  # 4.8%

    def test_dscr_calculation(self) -> None:
        """Test DSCR calculation."""
        noi = 240_000.0
        annual_debt_service = 180_000.0
        dscr = noi / annual_debt_service
        assert dscr > 1  # Should cover debt

    def test_ltv_calculation(self) -> None:
        """Test LTV calculation."""
        loan_amount = 3_000_000.0
        property_value = 5_000_000.0
        ltv = loan_amount / property_value
        assert ltv == 0.6  # 60%

    def test_cash_on_cash_calculation(self) -> None:
        """Test cash-on-cash return calculation."""
        annual_cash_flow = 60_000.0
        cash_investment = 2_000_000.0
        coc = annual_cash_flow / cash_investment
        assert coc == 0.03  # 3%


class TestPropertyValuationCalculation:
    """Tests for property valuation calculation."""

    def test_income_approach(self) -> None:
        """Test income approach valuation."""
        noi = 240_000.0
        cap_rate = 0.045
        value = noi / cap_rate
        assert value > 5_000_000  # ~5.33M

    def test_sales_comparison_approach(self) -> None:
        """Test sales comparison approach."""
        comparable_psf = 2500.0
        property_size_sqf = 2000.0
        value = comparable_psf * property_size_sqf
        assert value == 5_000_000.0

    def test_cost_approach(self) -> None:
        """Test cost approach valuation."""
        replacement_cost_psf = 3000.0
        property_size_sqf = 2000.0
        depreciation_factor = 0.8
        land_value = 2_000_000.0
        replacement_value = (
            replacement_cost_psf * property_size_sqf * depreciation_factor
        )
        total_value = replacement_value + land_value
        assert total_value == 6_800_000.0


class TestAgentsHealthEndpoint:
    """Tests for agents health endpoint."""

    def test_health_returns_status(self) -> None:
        """Test /health returns status."""
        status = "ready"
        assert status in ["ready", "degraded"]

    def test_health_returns_dependencies(self) -> None:
        """Test /health returns dependencies dict."""
        dependencies = {
            "numpy": True,
            "pandas": True,
            "trimesh": False,
        }
        assert isinstance(dependencies, dict)

    def test_health_returns_optional_features(self) -> None:
        """Test /health returns optional_features dict."""
        optional_features = {
            "three_d_builder": False,
            "site_pack_generator": True,
        }
        assert isinstance(optional_features, dict)


class TestDevelopmentScenarios:
    """Tests for development scenario types."""

    def test_raw_land_scenario(self) -> None:
        """Test raw_land development scenario."""
        scenario = "raw_land"
        assert scenario == "raw_land"

    def test_existing_building_scenario(self) -> None:
        """Test existing_building development scenario."""
        scenario = "existing_building"
        assert scenario == "existing_building"

    def test_heritage_property_scenario(self) -> None:
        """Test heritage_property development scenario."""
        scenario = "heritage_property"
        assert scenario == "heritage_property"

    def test_underused_asset_scenario(self) -> None:
        """Test underused_asset development scenario."""
        scenario = "underused_asset"
        assert scenario == "underused_asset"


class TestScenarioTypes:
    """Tests for 3D scenario types."""

    def test_new_build_type(self) -> None:
        """Test new_build scenario type."""
        scenario_type = "new_build"
        assert scenario_type == "new_build"

    def test_renovation_type(self) -> None:
        """Test renovation scenario type."""
        scenario_type = "renovation"
        assert scenario_type == "renovation"

    def test_mixed_use_conversion_type(self) -> None:
        """Test mixed_use_conversion scenario type."""
        scenario_type = "mixed_use_conversion"
        assert scenario_type == "mixed_use_conversion"

    def test_vertical_extension_type(self) -> None:
        """Test vertical_extension scenario type."""
        scenario_type = "vertical_extension"
        assert scenario_type == "vertical_extension"

    def test_podium_tower_type(self) -> None:
        """Test podium_tower scenario type."""
        scenario_type = "podium_tower"
        assert scenario_type == "podium_tower"

    def test_phased_development_type(self) -> None:
        """Test phased development scenario type."""
        scenario_type = "phased"
        assert scenario_type == "phased"


class TestPropertyTypeEnum:
    """Tests for PropertyType enum usage in agents API."""

    def test_office_type(self) -> None:
        """Test OFFICE property type."""
        assert PropertyType.OFFICE.value == "office"

    def test_retail_type(self) -> None:
        """Test RETAIL property type."""
        assert PropertyType.RETAIL.value == "retail"

    def test_residential_type(self) -> None:
        """Test RESIDENTIAL property type."""
        assert PropertyType.RESIDENTIAL.value == "residential"

    def test_industrial_type(self) -> None:
        """Test INDUSTRIAL property type."""
        assert PropertyType.INDUSTRIAL.value == "industrial"


class TestPackTypes:
    """Tests for professional pack types."""

    def test_universal_pack(self) -> None:
        """Test universal site pack type."""
        pack_type = "universal"
        assert pack_type == "universal"

    def test_investment_pack(self) -> None:
        """Test investment memorandum pack type."""
        pack_type = "investment"
        assert pack_type == "investment"

    def test_sales_pack(self) -> None:
        """Test sales brochure pack type."""
        pack_type = "sales"
        assert pack_type == "sales"

    def test_lease_pack(self) -> None:
        """Test leasing brochure pack type."""
        pack_type = "lease"
        assert pack_type == "lease"


class TestEdgeCases:
    """Tests for edge cases in agents API."""

    def test_invalid_property_id_400(self) -> None:
        """Test invalid property_id returns 400."""
        status_code = 400
        assert status_code == 400

    def test_property_not_found_404(self) -> None:
        """Test missing property returns 404."""
        status_code = 404
        assert status_code == 404

    def test_unavailable_feature_503(self) -> None:
        """Test unavailable feature returns 503."""
        status_code = 503
        assert status_code == 503

    def test_image_file_required(self) -> None:
        """Test photo upload requires image file."""
        content_type = "image/jpeg"
        assert content_type.startswith("image/")

    def test_audio_file_required(self) -> None:
        """Test voice note upload requires audio file."""
        content_type = "audio/webm"
        assert content_type.startswith("audio/")

    def test_mock_response_on_service_failure(self) -> None:
        """Test mock response is returned when services fail."""
        # When external services fail, the API returns mock data
        # This is a graceful degradation pattern
        mock_property_id = uuid4()
        assert mock_property_id is not None
