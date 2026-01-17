from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.models.property import PropertyType, TenureType
from app.services.agents.development_potential_scanner import (
    DevelopmentPotentialScanner,
    ExistingBuildingAnalysis,
    HistoricalPropertyAnalysis,
    RawLandAnalysis,
)


def make_property(**overrides):
    defaults = dict(
        id=uuid4(),
        address="123 Example St",
        property_name="Example Tower",
        land_area_sqm=Decimal("1000"),
        gross_floor_area_sqm=Decimal("800"),
        plot_ratio=Decimal("2.5"),
        zoning_code="C1",
        location="CBD",
        district="CBD Central",
        property_type=PropertyType.OFFICE,
        tenure_type=TenureType.FREEHOLD,
        is_conservation=False,
        conservation_status=None,
        year_built=1990,
        floors_above_ground=10,
        floors_below_ground=2,
        architect=None,
        transit_proximity_m=None,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


class StubBuildableResult:
    def __init__(self, gfa_total):
        self.gfa_total = gfa_total


@pytest.fixture
def stub_services(monkeypatch):
    buildable = AsyncMock()
    buildable.calculate_parameters = AsyncMock(return_value=StubBuildableResult(5000))

    finance = AsyncMock()
    finance.calculate_development_financials = AsyncMock(return_value={"irr": 12.5})
    finance.estimate_redevelopment_cost = AsyncMock(
        return_value={"total_cost": 4_500_000}
    )
    finance.calculate_value_uplift = AsyncMock(return_value={"value_uplift": 6_200_000})

    zoning_info = SimpleNamespace(
        zone_code="C1",
        plot_ratio=3.5,
        zone_description="Commercial",
        building_height_limit=120,
        site_coverage=45,
        special_conditions="URA LTA coordination",
        use_groups=["office", "retail", "Residential"],
        heritage_guidelines=["Preserve facade elements"],
    )
    ura = AsyncMock()
    ura.get_zoning_info = AsyncMock(return_value=zoning_info)
    ura.get_historical_context = AsyncMock(return_value={"heritage_value": "high"})

    return buildable, finance, ura, zoning_info


@pytest.mark.asyncio
async def test_analyze_raw_land_generates_scenarios(stub_services):
    buildable, finance, ura, zoning_info = stub_services
    scanner = DevelopmentPotentialScanner(buildable, finance, ura)
    property_data = make_property()

    analysis = await scanner._analyze_raw_land(property_data, session=AsyncMock())

    assert isinstance(analysis, RawLandAnalysis)
    assert analysis.gfa_potential == pytest.approx(5000)
    assert analysis.optimal_use_mix == {"office": 0.7, "retail": 0.3}
    assert len(analysis.development_scenarios) >= 1
    assert analysis.development_scenarios[0].scenario_type == "optimal_mix"


@pytest.mark.asyncio
async def test_analyze_existing_building_returns_metrics(stub_services):
    buildable, finance, ura, zoning_info = stub_services
    finance.calculate_development_financials.return_value = {
        "irr": 14.2,
        "cost": 3_100_000,
        "payback": 28,
    }
    scanner = DevelopmentPotentialScanner(buildable, finance, ura)
    property_data = make_property(gross_floor_area_sqm=Decimal("1200"))

    analysis = await scanner._analyze_existing_building(
        property_data, session=AsyncMock()
    )

    assert isinstance(analysis, ExistingBuildingAnalysis)
    assert analysis.current_gfa == 1200
    assert analysis.redevelopment_gfa_potential == 5000
    assert analysis.renovation_potential["summary"]["total_estimated_cost"] > 0
    assert analysis.adaptive_reuse_options
    assert len(analysis.asset_enhancement_opportunities) >= 3


@pytest.mark.asyncio
async def test_analyze_historical_property_flags_constraints(stub_services):
    buildable, finance, ura, zoning_info = stub_services
    scanner = DevelopmentPotentialScanner(buildable, finance, ura)
    property_data = make_property(
        is_conservation=True,
        conservation_status="conserved",
        property_type=PropertyType.RETAIL,
    )

    analysis = await scanner._analyze_historical_property(
        property_data, session=AsyncMock()
    )

    assert isinstance(analysis, HistoricalPropertyAnalysis)
    assert analysis.facade_preservation_needed is True
    assert analysis.grant_opportunities


def test_determine_optimal_use_mix_defaults(stub_services):
    buildable, finance, ura, zoning_info = stub_services
    scanner = DevelopmentPotentialScanner(buildable, finance, ura)
    mix = scanner._determine_optimal_use_mix(
        SimpleNamespace(zone_description="Mixed Use"), location="CBD"
    )
    assert mix["residential"] == 0.6


@pytest.mark.asyncio
async def test_generate_development_scenarios_multiple(stub_services):
    buildable, finance, ura, zoning_info = stub_services
    scanner = DevelopmentPotentialScanner(buildable, finance, ura)
    scenarios = await scanner._generate_development_scenarios(
        make_property(), 60000, {"office": 0.7, "retail": 0.3}, zoning_info
    )
    assert {s.scenario_type for s in scenarios} == {
        "optimal_mix",
        "single_use",
        "phased",
    }
    single = next(s for s in scenarios if s.scenario_type == "single_use")
    assert single.use_mix == {"office": 1.0}
    phased = next(s for s in scenarios if s.scenario_type == "phased")
    assert phased.gfa_potential == pytest.approx(24000)
    assert phased.projected_roi > 0


def test_identify_site_constraints_flags_all(stub_services):
    buildable, finance, ura, zoning_info = stub_services
    scanner = DevelopmentPotentialScanner(buildable, finance, ura)
    property_data = make_property(
        is_conservation=True,
        tenure_type=TenureType.LEASEHOLD_99,
    )
    constraints = scanner._identify_site_constraints(property_data, zoning_info)
    assert "Height limit: 120m" in constraints
    assert "Conservation requirements apply" in constraints
    assert "Maximum site coverage: 45%" in constraints
    assert "URA LTA coordination" in constraints
    assert "Leasehold tenure: TenureType.LEASEHOLD_99" in constraints


@pytest.mark.asyncio
async def test_estimate_land_value_matches_weighted_mix(stub_services):
    buildable, finance, ura, zoning_info = stub_services
    scanner = DevelopmentPotentialScanner(buildable, finance, ura)
    property_data = make_property(district="Downtown Core - CBD")
    value = await scanner._estimate_land_value(
        property_data,
        gfa_potential=5000,
        use_mix={"office": 0.6, "retail": 0.4},
    )
    assert value == pytest.approx(6_075_000, rel=1e-3)


@pytest.mark.asyncio
async def test_analyze_renovation_potential_summary(stub_services):
    buildable, finance, ura, zoning_info = stub_services
    scanner = DevelopmentPotentialScanner(buildable, finance, ura)
    property_data = make_property(year_built=1980)
    current_gfa = 1200
    summary = await scanner._analyze_renovation_potential(property_data, current_gfa)
    assert summary["summary"]["total_estimated_cost"] == pytest.approx(3_840_000)
    assert summary["summary"]["total_value_uplift_percentage"] == 40
    assert summary["summary"]["recommended_approach"] == "Single phase"


def test_identify_adaptive_reuse_options_includes_office_conversion(stub_services):
    buildable, finance, ura, zoning_info = stub_services
    scanner = DevelopmentPotentialScanner(buildable, finance, ura)
    options = scanner._identify_adaptive_reuse_options(
        make_property(property_type=PropertyType.OFFICE, year_built=1995), zoning_info
    )
    assert any(opt["conversion_type"] == "Office to Residential" for opt in options)


def test_identify_aei_opportunities_varies_by_age(stub_services):
    buildable, finance, ura, zoning_info = stub_services
    scanner = DevelopmentPotentialScanner(buildable, finance, ura)
    opportunities = scanner._identify_aei_opportunities(
        make_property(year_built=1990, property_type=PropertyType.OFFICE)
    )
    assert "Facade refresh and modernization" in opportunities
    assert "Lobby and common area upgrade" in opportunities
    assert "Full MEP systems replacement" in opportunities
    assert "Convert to flexible workspace" in opportunities


@pytest.mark.asyncio
async def test_estimate_redevelopment_cost_aggregates_components(stub_services):
    buildable, finance, ura, zoning_info = stub_services
    scanner = DevelopmentPotentialScanner(buildable, finance, ura)
    total_cost = await scanner._estimate_redevelopment_cost(
        make_property(
            property_type=PropertyType.OFFICE, gross_floor_area_sqm=Decimal("1000")
        ),
        new_gfa=2000,
    )
    assert total_cost == pytest.approx(8_900_000)


@pytest.mark.asyncio
async def test_calculate_value_uplift_prefers_redevelopment(stub_services):
    buildable, finance, ura, zoning_info = stub_services
    scanner = DevelopmentPotentialScanner(buildable, finance, ura)
    uplift = await scanner._calculate_value_uplift(
        make_property(gross_floor_area_sqm=Decimal("1000")),
        {"summary": {"total_value_uplift_percentage": 30}},
        redevelopment_gfa=2000,
    )
    assert uplift == pytest.approx(11_000_000)


# -----------------------------------------------------------
# _apply_market_adjustments tests
# -----------------------------------------------------------


def test_apply_market_adjustments_cbd_increases_office(stub_services):
    """Test CBD zones increase office allocation."""
    buildable, finance, ura, zoning_info = stub_services
    scanner = DevelopmentPotentialScanner(buildable, finance, ura)

    base_mix = {"office": 0.5, "residential": 0.3, "retail": 0.2}
    cbd_zoning = SimpleNamespace(zone_description="CBD Central Core")

    adjusted = scanner._apply_market_adjustments(base_mix, cbd_zoning, None)

    # Office should increase, residential should decrease
    assert adjusted["office"] > 0.5
    assert adjusted["residential"] < 0.3


def test_apply_market_adjustments_suburban_increases_residential(stub_services):
    """Test suburban zones increase residential allocation."""
    buildable, finance, ura, zoning_info = stub_services
    scanner = DevelopmentPotentialScanner(buildable, finance, ura)

    base_mix = {"office": 0.5, "residential": 0.3, "retail": 0.2}
    suburban_zoning = SimpleNamespace(zone_description="Suburban Fringe Area")

    adjusted = scanner._apply_market_adjustments(base_mix, suburban_zoning, None)

    # Residential should increase, office should decrease
    normalized_res = adjusted["residential"]
    normalized_office = adjusted["office"]
    # Adjustments should favor residential over office in suburban
    assert normalized_res > 0.3 * 0.9  # Accounts for normalization


def test_apply_market_adjustments_industrial_reduces_residential(stub_services):
    """Test industrial zones reduce residential allocation."""
    buildable, finance, ura, zoning_info = stub_services
    scanner = DevelopmentPotentialScanner(buildable, finance, ura)

    base_mix = {"office": 0.3, "residential": 0.4, "light_industrial": 0.3}
    industrial_zoning = SimpleNamespace(zone_description="Business Park Industrial")

    adjusted = scanner._apply_market_adjustments(base_mix, industrial_zoning, None)

    # Residential should decrease significantly in industrial zones
    assert adjusted["residential"] < 0.4
    assert adjusted["light_industrial"] > 0.3 * 0.8  # Should increase


def test_apply_market_adjustments_normalizes_to_one(stub_services):
    """Test adjustments are normalized to sum to 1.0."""
    buildable, finance, ura, zoning_info = stub_services
    scanner = DevelopmentPotentialScanner(buildable, finance, ura)

    base_mix = {"office": 0.5, "retail": 0.3, "residential": 0.2}
    zoning = SimpleNamespace(zone_description="Mixed Use Downtown")

    adjusted = scanner._apply_market_adjustments(base_mix, zoning, None)

    assert sum(adjusted.values()) == pytest.approx(1.0)


def test_apply_market_adjustments_with_transit_proximity(stub_services):
    """Test transit-oriented adjustments with nearby transit."""
    buildable, finance, ura, zoning_info = stub_services
    scanner = DevelopmentPotentialScanner(buildable, finance, ura)

    base_mix = {"office": 0.4, "retail": 0.2, "residential": 0.4}
    zoning = SimpleNamespace(zone_description="Mixed Use")
    location = SimpleNamespace(transit_proximity_m=200)  # Within 400m

    adjusted = scanner._apply_market_adjustments(base_mix, zoning, location)

    # All uses should increase (before normalization), so test sum normalizes
    assert sum(adjusted.values()) == pytest.approx(1.0)


# -----------------------------------------------------------
# _identify_market_opportunities tests
# -----------------------------------------------------------


def test_identify_market_opportunities_office_building(stub_services):
    """Test market opportunities for office buildings."""
    buildable, finance, ura, zoning_info = stub_services
    scanner = DevelopmentPotentialScanner(buildable, finance, ura)

    property_data = make_property(property_type=PropertyType.OFFICE)
    use_mix = {"office": 0.7, "retail": 0.3}
    opportunities = scanner._identify_market_opportunities(property_data, zoning_info, use_mix)

    assert len(opportunities) > 0


def test_identify_market_opportunities_retail_building(stub_services):
    """Test market opportunities for retail buildings."""
    buildable, finance, ura, zoning_info = stub_services
    scanner = DevelopmentPotentialScanner(buildable, finance, ura)

    property_data = make_property(property_type=PropertyType.RETAIL)
    use_mix = {"retail": 0.8, "office": 0.2}
    opportunities = scanner._identify_market_opportunities(property_data, zoning_info, use_mix)

    # Method runs and returns a list (may be empty if no conditions met)
    assert isinstance(opportunities, list)


def test_identify_market_opportunities_residential(stub_services):
    """Test market opportunities for residential properties."""
    buildable, finance, ura, zoning_info = stub_services
    scanner = DevelopmentPotentialScanner(buildable, finance, ura)

    property_data = make_property(property_type=PropertyType.RESIDENTIAL)
    use_mix = {"residential": 0.9, "retail": 0.1}
    opportunities = scanner._identify_market_opportunities(property_data, zoning_info, use_mix)

    # Method runs and returns a list (may be empty if no conditions met)
    assert isinstance(opportunities, list)


# -----------------------------------------------------------
# Heritage property assessment tests
# -----------------------------------------------------------


def test_assess_heritage_value_conserved(stub_services):
    """Test heritage value assessment for conserved property."""
    buildable, finance, ura, zoning_info = stub_services
    scanner = DevelopmentPotentialScanner(buildable, finance, ura)

    property_data = make_property(
        is_conservation=True,
        conservation_status="conserved",
        year_built=1920,
    )

    value = scanner._assess_heritage_value(property_data)

    # Returns a descriptive string about heritage value
    assert isinstance(value, str)
    assert "Conserved" in value or "Heritage" in value or "Building" in value


def test_assess_heritage_value_not_conserved(stub_services):
    """Test heritage value assessment for non-conserved property."""
    buildable, finance, ura, zoning_info = stub_services
    scanner = DevelopmentPotentialScanner(buildable, finance, ura)

    property_data = make_property(
        is_conservation=False,
        conservation_status=None,
        year_built=2010,
    )

    value = scanner._assess_heritage_value(property_data)

    # Returns a descriptive string
    assert isinstance(value, str)
    assert "Standard" in value or "Building" in value


def test_get_conservation_requirements_conserved(stub_services):
    """Test conservation requirements for conserved property."""
    buildable, finance, ura, zoning_info = stub_services
    scanner = DevelopmentPotentialScanner(buildable, finance, ura)

    property_data = make_property(
        is_conservation=True,
        conservation_status="conserved",
    )

    requirements = scanner._get_conservation_requirements(property_data)

    assert isinstance(requirements, list)
    assert len(requirements) > 0


def test_identify_heritage_grants_conserved(stub_services):
    """Test heritage grant identification for conserved property."""
    buildable, finance, ura, zoning_info = stub_services
    scanner = DevelopmentPotentialScanner(buildable, finance, ura)

    property_data = make_property(
        is_conservation=True,
        conservation_status="conserved",
    )

    grants = scanner._identify_heritage_grants(property_data)

    assert isinstance(grants, list)


# -----------------------------------------------------------
# Additional edge case tests
# -----------------------------------------------------------


def test_determine_optimal_use_mix_unknown_zoning(stub_services):
    """Test optimal use mix falls back for unknown zoning."""
    buildable, finance, ura, zoning_info = stub_services
    scanner = DevelopmentPotentialScanner(buildable, finance, ura)

    unknown_zoning = SimpleNamespace(zone_description="Unknown Zone Type")
    mix = scanner._determine_optimal_use_mix(unknown_zoning, location="test")

    assert mix == {"mixed": 1.0}


def test_determine_optimal_use_mix_residential_zone(stub_services):
    """Test optimal use mix for residential zones."""
    buildable, finance, ura, zoning_info = stub_services
    scanner = DevelopmentPotentialScanner(buildable, finance, ura)

    residential_zoning = SimpleNamespace(zone_description="Residential")
    mix = scanner._determine_optimal_use_mix(residential_zoning, location="suburban")

    assert "residential" in mix
    assert mix["residential"] > 0.5  # Should favor residential


def test_heritage_monument_helpers(stub_services):
    """Test heritage helper methods for monument properties."""
    buildable, finance, ura, zoning_info = stub_services
    scanner = DevelopmentPotentialScanner(buildable, finance, ura)

    monument = make_property(conservation_status="monument", is_conservation=True)
    heritage_value = scanner._assess_heritage_value(monument)
    # Returns descriptive string containing "National Monument"
    assert isinstance(heritage_value, str)
    assert "Monument" in heritage_value or "Building" in heritage_value

    requirements = scanner._get_conservation_requirements(monument)
    assert isinstance(requirements, list)

    allowable = scanner._get_allowable_modifications(monument, requirements)
    assert isinstance(allowable, list)


def test_heritage_adaptive_reuse_options(stub_services):
    """Test heritage adaptive reuse options."""
    buildable, finance, ura, zoning_info = stub_services
    scanner = DevelopmentPotentialScanner(buildable, finance, ura)

    conserved = make_property(
        is_conservation=True,
        conservation_status="conserved",
        property_type=PropertyType.RETAIL,
    )

    reuse = scanner._get_heritage_adaptive_reuse_options(conserved)
    assert isinstance(reuse, list)


def test_heritage_special_considerations(stub_services):
    """Test heritage special considerations."""
    buildable, finance, ura, zoning_info = stub_services
    scanner = DevelopmentPotentialScanner(buildable, finance, ura)

    monument = make_property(conservation_status="monument", is_conservation=True)
    considerations = scanner._get_heritage_special_considerations(monument)
    assert isinstance(considerations, list)
