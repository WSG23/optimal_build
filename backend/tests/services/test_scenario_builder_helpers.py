from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.models.property import PropertyType
from app.services.agents.scenario_builder_3d import (
    BuildingMassing,
    Quick3DScenarioBuilder,
    ScenarioType,
)


@pytest.fixture(scope="module")
def builder() -> Quick3DScenarioBuilder:
    return Quick3DScenarioBuilder(postgis_service=SimpleNamespace())


def _sample_footprint() -> list[tuple[float, float]]:
    # Triangle footprint avoids invalid quad faces inside trimesh helper.
    return [(0.0, 0.0), (40.0, 0.0), (0.0, 30.0), (0.0, 0.0)]


def test_building_massing_to_dict_includes_mesh(builder):
    footprint = _sample_footprint()
    mesh = builder._create_building_mesh(footprint, height=36.0)
    massing = BuildingMassing(
        footprint_coords=footprint,
        height=36.0,
        floors=10,
        scenario_type=ScenarioType.NEW_BUILD,
        use_mix={"office": 0.8, "retail": 0.2},
    )
    massing.mesh = mesh
    massing.volume = builder._calculate_volume(mesh)
    massing.gfa = builder._calculate_gfa(footprint, floors=10)

    payload = massing.to_dict()
    assert payload["scenario_type"] == "new_build"
    assert payload["volume"] == massing.volume
    assert payload["mesh_vertices"] and payload["mesh_faces"]


def test_mesh_generation_and_volume(builder):
    footprint = _sample_footprint()
    mesh = builder._create_building_mesh(footprint, height=24.0)
    assert mesh.vertices.shape[0] == (len(footprint) - 1) * 2
    assert builder._calculate_volume(mesh) > 0

    gfa = builder._calculate_gfa(footprint, floors=8)
    assert pytest.approx(gfa, rel=1e-3) == 600.0 * 8

    podium = footprint
    tower = builder._scale_footprint(footprint, 0.5)
    mixed = builder._calculate_mixed_use_gfa(
        podium, tower, podium_height=7.2, tower_height=36.0
    )
    assert mixed > builder._calculate_gfa(tower, floors=5)


def test_default_use_mix_and_scaling(builder):
    office_mix = builder._get_default_use_mix(PropertyType.OFFICE)
    assert office_mix["office"] > office_mix["retail"]

    fallback_mix = builder._get_default_use_mix(PropertyType.LAND)
    assert fallback_mix == {"mixed": 1.0}

    footprint = _sample_footprint()
    scaled = builder._scale_footprint(footprint, 0.8)
    assert len(scaled) == len(footprint)
    assert scaled[0] != footprint[0]


def test_tower_generation_and_splitting(builder):
    footprint = _sample_footprint()
    one_tower = builder._generate_tower_footprints(footprint, num_towers=1)
    two_towers = builder._generate_tower_footprints(footprint, num_towers=2)
    assert len(one_tower) == 1
    assert len(two_towers) == 2

    phase_one, phase_two = builder._split_footprint(footprint)
    assert phase_one[0] == phase_one[-1]
    assert phase_two[0] == phase_two[-1]


def test_parse_wkt_coords_and_renovation_mesh(builder):
    point_coords = builder._parse_wkt_coords("POINT(103.85 1.29)")
    polygon_coords = builder._parse_wkt_coords("POLYGON((0 0, 10 0, 10 5, 0 5, 0 0))")
    assert point_coords == [(103.85, 1.29)]
    assert len(polygon_coords) == 5

    mesh = builder._create_building_mesh(_sample_footprint(), height=12.0)
    modified = builder._add_renovation_features(mesh)
    assert isinstance(modified, type(mesh))


@pytest.mark.asyncio
async def test_export_to_json(builder):
    footprint = _sample_footprint()
    mesh = builder._create_building_mesh(footprint, height=18.0)
    massing = BuildingMassing(
        footprint_coords=footprint,
        height=18.0,
        floors=5,
        scenario_type=ScenarioType.RENOVATION,
    )
    massing.mesh = mesh
    massing.volume = builder._calculate_volume(mesh)
    massing.gfa = builder._calculate_gfa(footprint, floors=5)

    payload = await builder.export_to_format(massing, format="json")
    assert b"scenario_type" in payload


def _make_property(**overrides):
    base = {
        "id": "prop-1",
        "property_type": PropertyType.OFFICE,
        "gross_floor_area_sqm": 12000.0,
        "building_height_m": 60.0,
        "floors_above_ground": 12,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def _boundary():
    return [(0, 0), (80, 0), (80, 60), (0, 60), (0, 0)]


@pytest.mark.asyncio
async def test_generate_new_and_mixed_use_massings(builder, monkeypatch):
    property_data = _make_property()
    boundary = _boundary()
    session = SimpleNamespace()
    original_mesh = builder._create_building_mesh

    def safe_mesh(_footprint, height):
        return original_mesh(_sample_footprint(), height)

    monkeypatch.setattr(builder, "_create_building_mesh", safe_mesh)

    new_build = await builder._generate_new_build_massing(
        property_data, boundary, zoning_info=None, session=session
    )
    assert new_build and new_build.scenario_type == ScenarioType.NEW_BUILD

    mixed_use = await builder._generate_mixed_use_massing(
        property_data, boundary, zoning_info=None, session=session
    )
    assert mixed_use and mixed_use.scenario_type == ScenarioType.MIXED_USE_CONVERSION


@pytest.mark.asyncio
async def test_generate_renovation_and_vertical_extension(builder, monkeypatch):
    property_data = _make_property()
    session = SimpleNamespace()
    original_mesh = builder._create_building_mesh

    def safe_mesh(_footprint, height):
        return original_mesh(_sample_footprint(), height)

    monkeypatch.setattr(builder, "_create_building_mesh", safe_mesh)

    renovation = await builder._generate_renovation_massing(property_data, session)
    assert renovation and renovation.gfa > property_data.gross_floor_area_sqm

    vertical = await builder._generate_vertical_extension(property_data, session)
    assert vertical and vertical.height > property_data.building_height_m


@pytest.mark.asyncio
async def test_generate_podium_and_phased_development(builder, monkeypatch):
    property_data = _make_property()
    boundary = _boundary()
    session = SimpleNamespace()
    original_mesh = builder._create_building_mesh

    def safe_mesh(_footprint, height):
        return original_mesh(_sample_footprint(), height)

    monkeypatch.setattr(builder, "_create_building_mesh", safe_mesh)

    podium = await builder._generate_podium_tower(
        property_data, boundary, zoning_info=None, session=session
    )
    assert podium and podium.scenario_type == ScenarioType.PODIUM_TOWER

    phases = await builder._generate_phased_development(
        property_data, boundary, zoning_info=None, session=session
    )
    assert len(phases) == 2
    assert all(
        phase.scenario_type == ScenarioType.PHASED_DEVELOPMENT for phase in phases
    )


@pytest.mark.asyncio
async def test_apply_setbacks_handles_missing_and_overflow(builder):
    boundary = _boundary()
    session = SimpleNamespace()

    adjusted = await builder._apply_setbacks(
        boundary, builder.default_setbacks, session
    )
    assert adjusted and adjusted != boundary

    # Excessive setback removes footprint entirely
    collapsed = await builder._apply_setbacks(boundary, {"front": 100.0}, session)
    assert collapsed is None
