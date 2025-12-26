"""Comprehensive tests for developers_common API utilities and models.

Tests cover:
- Helper functions (_to_mapping, _coerce_float, etc.)
- DeveloperBuildEnvelope model
- DeveloperMassingLayer model
- DeveloperColorLegendEntry model
- PreviewJobSchema model
- DeveloperConstraintViolation model
- DeveloperAssetOptimization model
- DeveloperVisualizationSummary model
- Finance blueprint models
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from app.api.v1.developers_common import (
    _to_mapping,
    _coerce_float,
    _round_optional,
    _decimal_or_none,
    _convert_area_to_sqm,
    _convert_rent_to_psm,
    _normalise_scenario_param,
    _format_scenario_label,
    DeveloperBuildEnvelope,
    DeveloperMassingLayer,
    DeveloperColorLegendEntry,
    PreviewJobSchema,
    DeveloperConstraintViolation,
    DeveloperAssetOptimization,
    DeveloperVisualizationSummary,
    DeveloperCapitalStructureScenario,
    DeveloperDebtFacility,
    DeveloperEquityWaterfallTier,
    DeveloperEquityWaterfall,
    DeveloperCashFlowMilestone,
    DeveloperExitAssumptions,
    DeveloperSensitivityBand,
    DeveloperFinanceBlueprint,
    DeveloperFinancialSummary,
)

# Mark all tests in this module as not requiring database
pytestmark = pytest.mark.no_db


class TestToMapping:
    """Tests for _to_mapping helper function."""

    def test_none_input(self) -> None:
        """Test None input returns None."""
        assert _to_mapping(None) is None

    def test_dict_input(self) -> None:
        """Test dict input returns same dict."""
        d = {"key": "value"}
        result = _to_mapping(d)
        assert result == d

    def test_mapping_input(self) -> None:
        """Test mapping-like input."""
        from collections import OrderedDict

        od = OrderedDict([("a", 1), ("b", 2)])
        result = _to_mapping(od)
        assert result == od


class TestCoerceFloat:
    """Tests for _coerce_float helper function."""

    def test_none_input(self) -> None:
        """Test None returns None."""
        assert _coerce_float(None) is None

    def test_float_input(self) -> None:
        """Test float returns same float."""
        assert _coerce_float(3.14) == 3.14

    def test_int_input(self) -> None:
        """Test int converts to float."""
        assert _coerce_float(42) == 42.0

    def test_decimal_input(self) -> None:
        """Test Decimal converts to float."""
        assert _coerce_float(Decimal("3.14")) == 3.14

    def test_string_input(self) -> None:
        """Test string converts to float."""
        assert _coerce_float("3.14") == 3.14

    def test_invalid_string(self) -> None:
        """Test invalid string returns None."""
        assert _coerce_float("not a number") is None


class TestRoundOptional:
    """Tests for _round_optional helper function."""

    def test_none_input(self) -> None:
        """Test None returns None."""
        assert _round_optional(None) is None

    def test_round_to_two_decimals(self) -> None:
        """Test rounding to 2 decimal places."""
        assert _round_optional(3.14159) == 3.14
        assert _round_optional(2.556) == 2.56
        assert _round_optional(10.0) == 10.0


class TestDecimalOrNone:
    """Tests for _decimal_or_none helper function."""

    def test_none_input(self) -> None:
        """Test None returns None."""
        assert _decimal_or_none(None) is None

    def test_valid_input(self) -> None:
        """Test valid input converts to Decimal."""
        result = _decimal_or_none("123.45")
        assert result == Decimal("123.45")

    def test_invalid_input(self) -> None:
        """Test invalid input returns None."""
        assert _decimal_or_none("not a number") is None


class TestConvertAreaToSqm:
    """Tests for _convert_area_to_sqm helper function."""

    def test_none_input(self) -> None:
        """Test None returns None."""
        assert _convert_area_to_sqm(None, from_units="sqft") is None

    def test_sqft_to_sqm(self) -> None:
        """Test sqft conversion to sqm."""
        result = _convert_area_to_sqm(Decimal("1000"), from_units="sqft")
        assert result is not None
        # 1000 sqft ≈ 92.90 sqm
        assert float(result) == pytest.approx(92.90, rel=0.01)

    def test_sqm_unchanged(self) -> None:
        """Test sqm remains unchanged."""
        result = _convert_area_to_sqm(Decimal("100"), from_units="sqm")
        assert result == Decimal("100")


class TestConvertRentToPsm:
    """Tests for _convert_rent_to_psm helper function."""

    def test_none_input(self) -> None:
        """Test None returns None."""
        assert _convert_rent_to_psm(None, rent_metric="psf_month") is None

    def test_psf_to_psm(self) -> None:
        """Test psf conversion to psm."""
        result = _convert_rent_to_psm(Decimal("10"), rent_metric="psf_month")
        assert result is not None
        # 10 psf ≈ 107.64 psm
        assert float(result) == pytest.approx(107.64, rel=0.01)

    def test_psm_unchanged(self) -> None:
        """Test psm remains unchanged."""
        result = _convert_rent_to_psm(Decimal("100"), rent_metric="psm_month")
        assert result == Decimal("100")


class TestNormaliseScenarioParam:
    """Tests for _normalise_scenario_param helper function."""

    def test_none_returns_none(self) -> None:
        """Test None returns None."""
        assert _normalise_scenario_param(None) is None

    def test_empty_string_returns_none(self) -> None:
        """Test empty string returns None."""
        assert _normalise_scenario_param("") is None

    def test_all_returns_none(self) -> None:
        """Test 'all' returns None."""
        assert _normalise_scenario_param("all") is None
        assert _normalise_scenario_param("ALL") is None

    def test_normalises_to_lowercase(self) -> None:
        """Test normalises to lowercase."""
        assert _normalise_scenario_param("NEW_DEVELOPMENT") == "new_development"
        assert _normalise_scenario_param("  Heritage  ") == "heritage"


class TestFormatScenarioLabel:
    """Tests for _format_scenario_label helper function."""

    def test_none_returns_all_scenarios(self) -> None:
        """Test None returns 'All scenarios'."""
        assert _format_scenario_label(None) == "All scenarios"

    def test_formats_snake_case(self) -> None:
        """Test formats snake_case to title case."""
        assert _format_scenario_label("new_development") == "New Development"
        assert _format_scenario_label("heritage_property") == "Heritage Property"


class TestDeveloperBuildEnvelope:
    """Tests for DeveloperBuildEnvelope model."""

    def test_default_values(self) -> None:
        """Test default values."""
        envelope = DeveloperBuildEnvelope()
        assert envelope.zone_code is None
        assert envelope.assumptions == []

    def test_with_values(self) -> None:
        """Test with values."""
        envelope = DeveloperBuildEnvelope(
            zone_code="R-5",
            zone_description="Residential 5",
            site_area_sqm=1000.0,
            allowable_plot_ratio=3.0,
            max_buildable_gfa_sqm=3000.0,
            current_gfa_sqm=500.0,
            additional_potential_gfa_sqm=2500.0,
            assumptions=["Standard setbacks apply"],
        )
        assert envelope.zone_code == "R-5"
        assert envelope.max_buildable_gfa_sqm == 3000.0


class TestDeveloperMassingLayer:
    """Tests for DeveloperMassingLayer model."""

    def test_required_fields(self) -> None:
        """Test required fields."""
        layer = DeveloperMassingLayer(
            asset_type="residential",
            allocation_pct=60.0,
            color="#FF5733",
        )
        assert layer.asset_type == "residential"
        assert layer.allocation_pct == 60.0

    def test_optional_fields(self) -> None:
        """Test optional fields."""
        layer = DeveloperMassingLayer(
            asset_type="office",
            allocation_pct=40.0,
            gfa_sqm=5000.0,
            nia_sqm=4000.0,
            estimated_height_m=50.0,
            color="#3366FF",
        )
        assert layer.gfa_sqm == 5000.0
        assert layer.estimated_height_m == 50.0


class TestDeveloperColorLegendEntry:
    """Tests for DeveloperColorLegendEntry model."""

    def test_required_fields(self) -> None:
        """Test required fields."""
        entry = DeveloperColorLegendEntry(
            asset_type="retail",
            label="Retail Space",
            color="#00FF00",
        )
        assert entry.asset_type == "retail"
        assert entry.label == "Retail Space"

    def test_with_description(self) -> None:
        """Test with description."""
        entry = DeveloperColorLegendEntry(
            asset_type="hotel",
            label="Hotel",
            color="#FFD700",
            description="Hospitality accommodation",
        )
        assert entry.description == "Hospitality accommodation"


class TestPreviewJobSchema:
    """Tests for PreviewJobSchema model."""

    def test_required_fields(self) -> None:
        """Test required fields."""
        job_id = uuid4()
        prop_id = uuid4()
        schema = PreviewJobSchema(
            id=job_id,
            property_id=prop_id,
            scenario="new_development",
            status="pending",
            requested_at=datetime.now(),
        )
        assert schema.id == job_id
        assert schema.status == "pending"

    def test_completed_job(self) -> None:
        """Test completed job with URLs."""
        job_id = uuid4()
        prop_id = uuid4()
        now = datetime.now()
        schema = PreviewJobSchema(
            id=job_id,
            property_id=prop_id,
            scenario="heritage_property",
            status="ready",
            preview_url="https://storage.example.com/preview.glb",
            metadata_url="https://storage.example.com/metadata.json",
            thumbnail_url="https://storage.example.com/thumbnail.png",
            requested_at=now,
            started_at=now,
            finished_at=now,
            asset_version="1.0.0",
            geometry_detail_level="high",
        )
        assert schema.preview_url is not None
        assert schema.status == "ready"


class TestDeveloperConstraintViolation:
    """Tests for DeveloperConstraintViolation model."""

    def test_constraint_violation(self) -> None:
        """Test constraint violation."""
        violation = DeveloperConstraintViolation(
            constraint_type="height_limit",
            severity="error",
            message="Exceeds maximum building height of 50m",
            asset_type="residential",
        )
        assert violation.constraint_type == "height_limit"
        assert violation.severity == "error"


class TestDeveloperAssetOptimization:
    """Tests for DeveloperAssetOptimization model."""

    def test_basic_optimization(self) -> None:
        """Test basic optimization."""
        opt = DeveloperAssetOptimization(
            asset_type="residential",
            allocation_pct=60.0,
        )
        assert opt.asset_type == "residential"
        assert opt.allocation_pct == 60.0

    def test_detailed_optimization(self) -> None:
        """Test detailed optimization."""
        opt = DeveloperAssetOptimization(
            asset_type="office",
            allocation_pct=40.0,
            nia_efficiency=0.85,
            allocated_gfa_sqm=10000.0,
            rent_psm_month=50.0,
            estimated_revenue_sgd=6000000.0,
            risk_level="medium",
            confidence_score=0.85,
        )
        assert opt.nia_efficiency == 0.85
        assert opt.risk_level == "medium"


class TestDeveloperVisualizationSummary:
    """Tests for DeveloperVisualizationSummary model."""

    def test_unavailable_preview(self) -> None:
        """Test unavailable preview."""
        summary = DeveloperVisualizationSummary(
            status="pending",
            preview_available=False,
        )
        assert not summary.preview_available
        assert summary.massing_layers == []

    def test_available_preview(self) -> None:
        """Test available preview."""
        layer = DeveloperMassingLayer(
            asset_type="residential",
            allocation_pct=100.0,
            color="#FF0000",
        )
        summary = DeveloperVisualizationSummary(
            status="ready",
            preview_available=True,
            concept_mesh_url="https://example.com/mesh.glb",
            massing_layers=[layer],
        )
        assert summary.preview_available
        assert len(summary.massing_layers) == 1


class TestDeveloperCapitalStructureScenario:
    """Tests for DeveloperCapitalStructureScenario model."""

    def test_capital_structure(self) -> None:
        """Test capital structure scenario."""
        scenario = DeveloperCapitalStructureScenario(
            scenario="base_case",
            equity_pct=30.0,
            debt_pct=70.0,
            preferred_equity_pct=0.0,
            target_ltv=0.65,
            target_ltc=0.70,
            target_dscr=1.25,
            comments="Standard financing structure",
        )
        assert scenario.equity_pct + scenario.debt_pct == 100.0
        assert scenario.target_dscr == 1.25


class TestDeveloperDebtFacility:
    """Tests for DeveloperDebtFacility model."""

    def test_debt_facility(self) -> None:
        """Test debt facility."""
        facility = DeveloperDebtFacility(
            facility_type="construction_loan",
            amount_expression="0.7 * total_development_cost",
            interest_rate="SOFR + 250bps",
            tenor_years=3.0,
        )
        assert facility.facility_type == "construction_loan"
        assert facility.tenor_years == 3.0


class TestDeveloperEquityWaterfall:
    """Tests for DeveloperEquityWaterfall model."""

    def test_equity_waterfall(self) -> None:
        """Test equity waterfall structure."""
        tiers = [
            DeveloperEquityWaterfallTier(hurdle_irr_pct=8.0, promote_pct=0.0),
            DeveloperEquityWaterfallTier(hurdle_irr_pct=12.0, promote_pct=20.0),
            DeveloperEquityWaterfallTier(hurdle_irr_pct=15.0, promote_pct=30.0),
        ]
        waterfall = DeveloperEquityWaterfall(
            tiers=tiers,
            preferred_return_pct=8.0,
        )
        assert len(waterfall.tiers) == 3
        assert waterfall.preferred_return_pct == 8.0


class TestDeveloperCashFlowMilestone:
    """Tests for DeveloperCashFlowMilestone model."""

    def test_cash_flow_milestone(self) -> None:
        """Test cash flow milestone."""
        milestone = DeveloperCashFlowMilestone(
            item="Land acquisition",
            start_month=0,
            duration_months=1,
            notes="Initial equity deployment",
        )
        assert milestone.item == "Land acquisition"
        assert milestone.start_month == 0


class TestDeveloperExitAssumptions:
    """Tests for DeveloperExitAssumptions model."""

    def test_exit_assumptions(self) -> None:
        """Test exit assumptions."""
        assumptions = DeveloperExitAssumptions(
            exit_cap_rates={"residential": 4.0, "office": 5.0},
            sale_costs_pct=2.5,
        )
        assert assumptions.exit_cap_rates["residential"] == 4.0
        assert assumptions.sale_costs_pct == 2.5


class TestDeveloperSensitivityBand:
    """Tests for DeveloperSensitivityBand model."""

    def test_sensitivity_band(self) -> None:
        """Test sensitivity band."""
        band = DeveloperSensitivityBand(
            parameter="construction_cost",
            low=-10.0,
            base=0.0,
            high=10.0,
            comments="Cost variance sensitivity",
        )
        assert band.parameter == "construction_cost"
        assert band.low == -10.0


class TestDeveloperFinanceBlueprint:
    """Tests for DeveloperFinanceBlueprint model."""

    def test_empty_blueprint(self) -> None:
        """Test empty blueprint."""
        blueprint = DeveloperFinanceBlueprint()
        assert blueprint.capital_structure == []
        assert blueprint.debt_facilities == []

    def test_full_blueprint(self) -> None:
        """Test full blueprint."""
        blueprint = DeveloperFinanceBlueprint(
            capital_structure=[
                DeveloperCapitalStructureScenario(
                    scenario="base",
                    equity_pct=30.0,
                    debt_pct=70.0,
                    preferred_equity_pct=0.0,
                    target_ltv=0.65,
                    target_ltc=0.70,
                    target_dscr=1.25,
                )
            ],
            exit_assumptions=DeveloperExitAssumptions(
                exit_cap_rates={"all": 4.5},
                sale_costs_pct=2.5,
            ),
        )
        assert len(blueprint.capital_structure) == 1
        assert blueprint.exit_assumptions is not None


class TestDeveloperFinancialSummary:
    """Tests for DeveloperFinancialSummary model."""

    def test_default_values(self) -> None:
        """Test default values."""
        summary = DeveloperFinancialSummary()
        assert summary.currency_code == "SGD"
        assert summary.currency_symbol == "S$"
        assert summary.notes == []

    def test_with_values(self) -> None:
        """Test with values."""
        summary = DeveloperFinancialSummary(
            total_estimated_revenue_sgd=50000000.0,
            total_estimated_capex_sgd=40000000.0,
            dominant_risk_profile="medium",
            notes=["Strong rental market", "Heritage premium applies"],
        )
        assert summary.total_estimated_revenue_sgd == 50000000.0
        assert len(summary.notes) == 2
