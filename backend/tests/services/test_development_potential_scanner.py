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


def test_heritage_helpers_cover_branches(stub_services):
    buildable, finance, ura, zoning_info = stub_services
    scanner = DevelopmentPotentialScanner(buildable, finance, ura)
    monument = make_property(conservation_status="monument", is_conservation=True)
    assert "National Monument" in scanner._assess_heritage_value(monument)
    requirements = scanner._get_conservation_requirements(monument)
    assert "No structural alterations allowed" in requirements
    allowable = scanner._get_allowable_modifications(monument, requirements)
    assert "Reversible installations only" in allowable
    grants = scanner._identify_heritage_grants(
        make_property(
            is_conservation=True,
            conservation_status="conserved",
            property_type=PropertyType.RETAIL,
        )
    )
    assert any("Grant" in grant for grant in grants)
    considerations = scanner._get_heritage_special_considerations(monument)
    assert any("National Heritage Board" in item for item in considerations)
    reuse = scanner._get_heritage_adaptive_reuse_options(monument)
    assert any(option["use"] == "Boutique Heritage Hotel" for option in reuse)
