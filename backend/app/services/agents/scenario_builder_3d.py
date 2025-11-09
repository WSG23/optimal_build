"""Quick 3D Scenarios builder for property development visualization."""

from __future__ import annotations

import json
from enum import Enum
from typing import Any

import numpy as np
import structlog
import trimesh
from geoalchemy2.functions import ST_AsText

from app.models.property import Property, PropertyType
from app.services.agents.ura_integration import URAZoningInfo
from app.services.postgis import PostGISService
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class ScenarioType(str, Enum):
    """Types of 3D development scenarios."""

    NEW_BUILD = "new_build"
    RENOVATION = "renovation"
    MIXED_USE_CONVERSION = "mixed_use_conversion"
    VERTICAL_EXTENSION = "vertical_extension"
    PODIUM_TOWER = "podium_tower"
    PHASED_DEVELOPMENT = "phased"


class BuildingMassing:
    """3D building massing representation."""

    def __init__(
        self,
        footprint_coords: list[tuple[float, float]],
        height: float,
        floors: int,
        scenario_type: ScenarioType,
        use_mix: dict[str, float] = None,
    ):
        self.footprint_coords = footprint_coords
        self.height = height
        self.floors = floors
        self.scenario_type = scenario_type
        self.use_mix = use_mix or {}
        self.mesh = None
        self.volume = None
        self.gfa = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "footprint": self.footprint_coords,
            "height": self.height,
            "floors": self.floors,
            "scenario_type": self.scenario_type.value,
            "use_mix": self.use_mix,
            "volume": self.volume,
            "gfa": self.gfa,
            "mesh_vertices": self.mesh.vertices.tolist() if self.mesh else None,
            "mesh_faces": self.mesh.faces.tolist() if self.mesh else None,
        }


class Quick3DScenarioBuilder:
    """Service for generating quick 3D massing scenarios."""

    def __init__(self, postgis_service: PostGISService):
        self.postgis = postgis_service
        self.default_floor_height = 3.6  # meters
        self.default_setbacks = {"front": 7.5, "side": 3.0, "rear": 7.5}

    async def generate_massing_scenarios(
        self,
        property_data: Property,
        scenario_types: list[ScenarioType],
        session: AsyncSession,
        zoning_info: URAZoningInfo | None = None,
    ) -> list[BuildingMassing]:
        """
        Generate 3D massing scenarios for property development.

        Args:
            property_data: Property information
            scenario_types: Types of scenarios to generate
            session: Database session
            zoning_info: Zoning information (optional)

        Returns:
            List of 3D building massing scenarios
        """
        scenarios = []

        # Get property boundary geometry
        property_boundary = await self._get_property_boundary(property_data, session)

        # Generate each requested scenario
        for scenario_type in scenario_types:
            if scenario_type == ScenarioType.NEW_BUILD:
                massing = await self._generate_new_build_massing(
                    property_data, property_boundary, zoning_info, session
                )
                if massing:
                    scenarios.append(massing)

            elif scenario_type == ScenarioType.RENOVATION:
                massing = await self._generate_renovation_massing(
                    property_data, session
                )
                if massing:
                    scenarios.append(massing)

            elif scenario_type == ScenarioType.MIXED_USE_CONVERSION:
                massing = await self._generate_mixed_use_massing(
                    property_data, property_boundary, zoning_info, session
                )
                if massing:
                    scenarios.append(massing)

            elif scenario_type == ScenarioType.VERTICAL_EXTENSION:
                massing = await self._generate_vertical_extension(
                    property_data, session
                )
                if massing:
                    scenarios.append(massing)

            elif scenario_type == ScenarioType.PODIUM_TOWER:
                massing = await self._generate_podium_tower(
                    property_data, property_boundary, zoning_info, session
                )
                if massing:
                    scenarios.append(massing)

            elif scenario_type == ScenarioType.PHASED_DEVELOPMENT:
                phased_massings = await self._generate_phased_development(
                    property_data, property_boundary, zoning_info, session
                )
                scenarios.extend(phased_massings)

        return scenarios

    async def _get_property_boundary(
        self, property_data: Property, session: AsyncSession
    ) -> list[tuple[float, float]]:
        """Get property boundary coordinates."""

        # If we have actual geometry, extract coordinates
        if property_data.location:
            # Get boundary as text
            result = await session.execute(select(ST_AsText(property_data.location)))
            boundary_wkt = result.scalar_one()

            # Parse WKT to get coordinates
            # This is simplified - assumes POINT geometry
            # In production, handle POLYGON boundaries
            coords = self._parse_wkt_coords(boundary_wkt)

            # If just a point, create a default rectangle
            if len(coords) == 1:
                center_x, center_y = coords[0]
                # Create 50x50m default plot
                return [
                    (center_x - 25, center_y - 25),
                    (center_x + 25, center_y - 25),
                    (center_x + 25, center_y + 25),
                    (center_x - 25, center_y + 25),
                    (center_x - 25, center_y - 25),  # Close polygon
                ]

            return coords

        # Default boundary if no geometry
        return [(0, 0), (50, 0), (50, 50), (0, 50), (0, 0)]

    async def _generate_new_build_massing(
        self,
        property_data: Property,
        boundary: list[tuple[float, float]],
        zoning_info: URAZoningInfo | None,
        session: AsyncSession,
    ) -> BuildingMassing | None:
        """Generate new building massing based on zoning."""

        # Apply setbacks to get buildable footprint
        buildable_footprint = await self._apply_setbacks(
            boundary, self.default_setbacks, session
        )

        if not buildable_footprint:
            return None

        # Determine height from zoning or defaults
        if zoning_info and zoning_info.building_height_limit:
            max_height = zoning_info.building_height_limit
        else:
            # Default heights by property type
            height_defaults = {
                PropertyType.OFFICE: 100,
                PropertyType.RESIDENTIAL: 80,
                PropertyType.RETAIL: 20,
                PropertyType.INDUSTRIAL: 15,
                PropertyType.MIXED_USE: 60,
            }
            max_height = height_defaults.get(property_data.property_type, 50)

        # Calculate floors
        floors = int(max_height / self.default_floor_height)

        # Create massing
        massing = BuildingMassing(
            footprint_coords=buildable_footprint,
            height=max_height,
            floors=floors,
            scenario_type=ScenarioType.NEW_BUILD,
            use_mix=self._get_default_use_mix(property_data.property_type),
        )

        # Generate 3D mesh
        massing.mesh = self._create_building_mesh(buildable_footprint, max_height)

        # Calculate volume and GFA
        massing.volume = self._calculate_volume(massing.mesh)
        massing.gfa = self._calculate_gfa(buildable_footprint, floors)

        return massing

    async def _generate_renovation_massing(
        self, property_data: Property, session: AsyncSession
    ) -> BuildingMassing | None:
        """Generate renovation massing (existing building with modifications)."""

        if not property_data.gross_floor_area_sqm:
            return None

        # Use existing building parameters
        existing_height = float(property_data.building_height_m or 50)
        existing_floors = property_data.floors_above_ground or int(existing_height / 4)

        # Simple rectangular footprint based on GFA
        floor_area = float(property_data.gross_floor_area_sqm) / existing_floors
        # Protect against invalid floor_area values
        if floor_area <= 0:
            logger.warning(
                "Invalid floor_area for renovation massing",
                floor_area=floor_area,
                property_id=property_data.id,
            )
            return None
        side_length = np.sqrt(floor_area)

        footprint = [
            (0, 0),
            (side_length, 0),
            (side_length, side_length),
            (0, side_length),
            (0, 0),
        ]

        massing = BuildingMassing(
            footprint_coords=footprint,
            height=existing_height,
            floors=existing_floors,
            scenario_type=ScenarioType.RENOVATION,
            use_mix=self._get_default_use_mix(property_data.property_type),
        )

        # Create mesh with renovation modifications
        base_mesh = self._create_building_mesh(footprint, existing_height)

        # Add facade extensions or modifications
        massing.mesh = self._add_renovation_features(base_mesh)
        massing.volume = self._calculate_volume(massing.mesh)
        massing.gfa = float(property_data.gross_floor_area_sqm) * 1.1  # 10% increase

        return massing

    async def _generate_mixed_use_massing(
        self,
        property_data: Property,
        boundary: list[tuple[float, float]],
        zoning_info: URAZoningInfo | None,
        session: AsyncSession,
    ) -> BuildingMassing | None:
        """Generate mixed-use development massing."""

        # Apply setbacks
        buildable_footprint = await self._apply_setbacks(
            boundary, self.default_setbacks, session
        )

        if not buildable_footprint:
            return None

        # Mixed use typically has larger podium, smaller tower
        # Create podium footprint (full buildable area)
        podium_height = 20  # 5-6 floors retail/commercial

        # Tower footprint (60% of podium)
        tower_footprint = self._scale_footprint(buildable_footprint, 0.6)
        tower_height = 80  # Additional height above podium

        # Create combined massing
        total_height = podium_height + tower_height
        total_floors = int(total_height / self.default_floor_height)

        massing = BuildingMassing(
            footprint_coords=buildable_footprint,
            height=total_height,
            floors=total_floors,
            scenario_type=ScenarioType.MIXED_USE_CONVERSION,
            use_mix={"retail": 0.2, "office": 0.3, "residential": 0.5},
        )

        # Create complex mesh with podium and tower
        podium_mesh = self._create_building_mesh(buildable_footprint, podium_height)
        tower_mesh = self._create_building_mesh(tower_footprint, tower_height)

        # Translate tower up by podium height
        tower_mesh.vertices[:, 2] += podium_height

        # Combine meshes
        massing.mesh = trimesh.util.concatenate([podium_mesh, tower_mesh])
        massing.volume = self._calculate_volume(massing.mesh)
        massing.gfa = self._calculate_mixed_use_gfa(
            buildable_footprint, tower_footprint, podium_height, tower_height
        )

        return massing

    async def _generate_vertical_extension(
        self, property_data: Property, session: AsyncSession
    ) -> BuildingMassing | None:
        """Generate vertical extension on existing building."""

        if not property_data.building_height_m:
            return None

        existing_height = float(property_data.building_height_m)
        existing_floors = property_data.floors_above_ground or int(existing_height / 4)

        # Check if vertical extension is feasible
        # Assume we can add 20-30% more height
        additional_height = existing_height * 0.25
        additional_floors = int(additional_height / self.default_floor_height)

        # Use existing footprint approximation
        if property_data.gross_floor_area_sqm and existing_floors:
            floor_area = float(property_data.gross_floor_area_sqm) / existing_floors
            # Protect against invalid floor_area values
            if floor_area > 0:
                side_length = np.sqrt(floor_area)
            else:
                logger.warning(
                    "Invalid floor_area for vertical extension",
                    floor_area=floor_area,
                    property_id=property_data.id,
                )
                side_length = 30  # Default
        else:
            side_length = 30  # Default

        footprint = [
            (0, 0),
            (side_length, 0),
            (side_length, side_length),
            (0, side_length),
            (0, 0),
        ]

        # Create extension with setback
        extension_footprint = self._scale_footprint(footprint, 0.8)  # 20% setback

        total_height = existing_height + additional_height
        total_floors = existing_floors + additional_floors

        massing = BuildingMassing(
            footprint_coords=footprint,
            height=total_height,
            floors=total_floors,
            scenario_type=ScenarioType.VERTICAL_EXTENSION,
            use_mix=self._get_default_use_mix(property_data.property_type),
        )

        # Create mesh showing extension
        existing_mesh = self._create_building_mesh(footprint, existing_height)
        extension_mesh = self._create_building_mesh(
            extension_footprint, additional_height
        )
        extension_mesh.vertices[:, 2] += existing_height

        # Add visual distinction
        existing_mesh.visual.face_colors = [200, 200, 200, 255]
        extension_mesh.visual.face_colors = [150, 150, 250, 255]

        massing.mesh = trimesh.util.concatenate([existing_mesh, extension_mesh])
        massing.volume = self._calculate_volume(massing.mesh)
        massing.gfa = self._calculate_gfa(
            footprint, existing_floors
        ) + self._calculate_gfa(extension_footprint, additional_floors)

        return massing

    async def _generate_podium_tower(
        self,
        property_data: Property,
        boundary: list[tuple[float, float]],
        zoning_info: URAZoningInfo | None,
        session: AsyncSession,
    ) -> BuildingMassing | None:
        """Generate podium-tower configuration."""

        buildable_footprint = await self._apply_setbacks(
            boundary, self.default_setbacks, session
        )

        if not buildable_footprint:
            return None

        # Podium configuration
        podium_height = 24  # 6-7 floors
        podium_floors = 6

        # Multiple towers on podium
        tower_footprints = self._generate_tower_footprints(
            buildable_footprint, num_towers=2
        )

        tower_height = 100  # Above podium
        tower_floors = int(tower_height / self.default_floor_height)

        total_height = podium_height + tower_height
        total_floors = podium_floors + tower_floors

        massing = BuildingMassing(
            footprint_coords=buildable_footprint,
            height=total_height,
            floors=total_floors,
            scenario_type=ScenarioType.PODIUM_TOWER,
            use_mix={"retail": 0.15, "parking": 0.1, "residential": 0.75},
        )

        # Create podium mesh
        podium_mesh = self._create_building_mesh(buildable_footprint, podium_height)
        podium_mesh.visual.face_colors = [180, 180, 180, 255]

        # Create tower meshes
        tower_meshes = []
        for tower_footprint in tower_footprints:
            tower_mesh = self._create_building_mesh(tower_footprint, tower_height)
            tower_mesh.vertices[:, 2] += podium_height
            tower_mesh.visual.face_colors = [150, 180, 220, 255]
            tower_meshes.append(tower_mesh)

        # Combine all meshes
        all_meshes = [podium_mesh] + tower_meshes
        massing.mesh = trimesh.util.concatenate(all_meshes)
        massing.volume = self._calculate_volume(massing.mesh)

        # Calculate GFA
        podium_gfa = self._calculate_gfa(buildable_footprint, podium_floors)
        tower_gfa = sum(
            self._calculate_gfa(fp, tower_floors) for fp in tower_footprints
        )
        massing.gfa = podium_gfa + tower_gfa

        return massing

    async def _generate_phased_development(
        self,
        property_data: Property,
        boundary: list[tuple[float, float]],
        zoning_info: URAZoningInfo | None,
        session: AsyncSession,
    ) -> list[BuildingMassing]:
        """Generate phased development scenarios."""

        phases = []
        buildable_footprint = await self._apply_setbacks(
            boundary, self.default_setbacks, session
        )

        if not buildable_footprint:
            return phases

        # Split site into phases (simplified - just divide in half)
        phase1_footprint, phase2_footprint = self._split_footprint(buildable_footprint)

        # Phase 1 - Lower density to test market
        phase1_height = 40
        phase1_floors = int(phase1_height / self.default_floor_height)

        phase1_massing = BuildingMassing(
            footprint_coords=phase1_footprint,
            height=phase1_height,
            floors=phase1_floors,
            scenario_type=ScenarioType.PHASED_DEVELOPMENT,
            use_mix={"office": 0.6, "retail": 0.4},
        )

        phase1_massing.mesh = self._create_building_mesh(
            phase1_footprint, phase1_height
        )
        phase1_massing.mesh.visual.face_colors = [200, 150, 150, 255]
        phase1_massing.volume = self._calculate_volume(phase1_massing.mesh)
        phase1_massing.gfa = self._calculate_gfa(phase1_footprint, phase1_floors)

        phases.append(phase1_massing)

        # Phase 2 - Higher density based on phase 1 success
        phase2_height = 80
        phase2_floors = int(phase2_height / self.default_floor_height)

        phase2_massing = BuildingMassing(
            footprint_coords=phase2_footprint,
            height=phase2_height,
            floors=phase2_floors,
            scenario_type=ScenarioType.PHASED_DEVELOPMENT,
            use_mix={"residential": 0.7, "retail": 0.3},
        )

        phase2_massing.mesh = self._create_building_mesh(
            phase2_footprint, phase2_height
        )
        phase2_massing.mesh.visual.face_colors = [150, 200, 150, 255]
        phase2_massing.volume = self._calculate_volume(phase2_massing.mesh)
        phase2_massing.gfa = self._calculate_gfa(phase2_footprint, phase2_floors)

        phases.append(phase2_massing)

        return phases

    # Helper methods

    async def _apply_setbacks(
        self,
        boundary: list[tuple[float, float]],
        setbacks: dict[str, float],
        session: AsyncSession,
    ) -> list[tuple[float, float]] | None:
        """Apply setbacks to property boundary using PostGIS."""

        # For simplicity, apply uniform setback
        # In production, apply directional setbacks
        setback_values = list(setbacks.values())
        if not setback_values:
            logger.warning("No setback values provided, using default")
            avg_setback = 3.0  # Default setback
        else:
            avg_setback = np.mean(setback_values)

        # Use PostGIS to buffer inward
        from shapely.geometry import Polygon

        poly = Polygon(boundary[:-1])  # Remove duplicate last point
        buffered = poly.buffer(-avg_setback)  # Negative for inward

        if buffered.is_empty:
            return None

        # Extract coordinates
        if hasattr(buffered, "exterior"):
            coords = list(buffered.exterior.coords)
        else:
            return None

        return coords

    def _create_building_mesh(
        self, footprint: list[tuple[float, float]], height: float
    ) -> trimesh.Trimesh:
        """Create a 3D building mesh from footprint and height."""

        # Convert footprint to numpy array
        vertices_2d = np.array(footprint[:-1])  # Remove duplicate last point
        n_vertices = len(vertices_2d)

        # Create bottom vertices (z=0)
        bottom_vertices = np.column_stack(
            [vertices_2d[:, 0], vertices_2d[:, 1], np.zeros(n_vertices)]
        )

        # Create top vertices (z=height)
        top_vertices = np.column_stack(
            [vertices_2d[:, 0], vertices_2d[:, 1], np.full(n_vertices, height)]
        )

        # Combine all vertices
        vertices = np.vstack([bottom_vertices, top_vertices])

        # Create faces
        faces = []

        # Bottom face
        faces.append(list(range(n_vertices)))

        # Top face
        faces.append(list(range(n_vertices, 2 * n_vertices)))

        # Side faces
        for i in range(n_vertices):
            next_i = (i + 1) % n_vertices
            # Create two triangles for each side
            faces.append([i, next_i, next_i + n_vertices])
            faces.append([i, next_i + n_vertices, i + n_vertices])

        # Create mesh
        mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
        mesh.fix_normals()

        return mesh

    def _calculate_volume(self, mesh: trimesh.Trimesh) -> float:
        """Calculate building volume from mesh."""
        return float(mesh.volume)

    def _calculate_gfa(
        self, footprint: list[tuple[float, float]], floors: int
    ) -> float:
        """Calculate gross floor area."""
        from shapely.geometry import Polygon

        poly = Polygon(footprint[:-1])
        floor_area = poly.area

        return floor_area * floors

    def _calculate_mixed_use_gfa(
        self,
        podium_footprint: list[tuple[float, float]],
        tower_footprint: list[tuple[float, float]],
        podium_height: float,
        tower_height: float,
    ) -> float:
        """Calculate GFA for mixed-use development."""
        podium_floors = int(podium_height / self.default_floor_height)
        tower_floors = int(tower_height / self.default_floor_height)

        podium_gfa = self._calculate_gfa(podium_footprint, podium_floors)
        tower_gfa = self._calculate_gfa(tower_footprint, tower_floors)

        return podium_gfa + tower_gfa

    def _get_default_use_mix(self, property_type: PropertyType) -> dict[str, float]:
        """Get default use mix by property type."""
        use_mixes = {
            PropertyType.OFFICE: {"office": 0.9, "retail": 0.1},
            PropertyType.RETAIL: {"retail": 0.8, "f&b": 0.2},
            PropertyType.RESIDENTIAL: {"residential": 0.95, "retail": 0.05},
            PropertyType.INDUSTRIAL: {
                "industrial": 0.7,
                "office": 0.2,
                "warehouse": 0.1,
            },
            PropertyType.MIXED_USE: {"residential": 0.5, "office": 0.3, "retail": 0.2},
            PropertyType.HOTEL: {"hotel": 0.8, "f&b": 0.1, "retail": 0.1},
        }

        return use_mixes.get(property_type, {"mixed": 1.0})

    def _scale_footprint(
        self, footprint: list[tuple[float, float]], scale: float
    ) -> list[tuple[float, float]]:
        """Scale footprint around its centroid."""
        from shapely.affinity import scale as shapely_scale
        from shapely.geometry import Polygon

        poly = Polygon(footprint[:-1])
        scaled = shapely_scale(poly, xfact=scale, yfact=scale)

        return list(scaled.exterior.coords)

    def _generate_tower_footprints(
        self, podium_footprint: list[tuple[float, float]], num_towers: int = 2
    ) -> list[list[tuple[float, float]]]:
        """Generate tower footprints on podium."""
        from shapely.geometry import Polygon, box

        podium_poly = Polygon(podium_footprint[:-1])
        bounds = podium_poly.bounds  # minx, miny, maxx, maxy

        # Simple grid layout for towers
        tower_footprints = []

        if num_towers == 1:
            # Single central tower
            tower = self._scale_footprint(podium_footprint, 0.5)
            tower_footprints.append(tower)

        elif num_towers == 2:
            # Two towers side by side
            width = (bounds[2] - bounds[0]) * 0.35
            height = (bounds[3] - bounds[1]) * 0.4

            # Tower 1
            tower1 = box(
                bounds[0] + width * 0.2,
                bounds[1] + height * 0.3,
                bounds[0] + width * 1.2,
                bounds[1] + height * 1.3,
            )
            tower_footprints.append(list(tower1.exterior.coords))

            # Tower 2
            tower2 = box(
                bounds[2] - width * 1.2,
                bounds[1] + height * 0.3,
                bounds[2] - width * 0.2,
                bounds[1] + height * 1.3,
            )
            tower_footprints.append(list(tower2.exterior.coords))

        return tower_footprints

    def _split_footprint(
        self, footprint: list[tuple[float, float]]
    ) -> tuple[list[tuple[float, float]], list[tuple[float, float]]]:
        """Split footprint into two phases."""
        from shapely.geometry import Polygon, box

        poly = Polygon(footprint[:-1])
        bounds = poly.bounds

        mid_x = (bounds[0] + bounds[2]) / 2

        # Phase 1 - left half
        phase1 = box(bounds[0], bounds[1], mid_x, bounds[3])

        # Phase 2 - right half
        phase2 = box(mid_x, bounds[1], bounds[2], bounds[3])

        return (list(phase1.exterior.coords), list(phase2.exterior.coords))

    def _parse_wkt_coords(self, wkt: str) -> list[tuple[float, float]]:
        """Parse coordinates from WKT string."""
        import re

        # Extract coordinate pairs
        coord_pattern = r"(-?\d+\.?\d*)\s+(-?\d+\.?\d*)"
        matches = re.findall(coord_pattern, wkt)

        return [(float(x), float(y)) for x, y in matches]

    def _add_renovation_features(self, base_mesh: trimesh.Trimesh) -> trimesh.Trimesh:
        """Add renovation features to existing building mesh."""
        # Add simple roof extension or facade treatment
        # This is simplified - in production, add more complex modifications

        # Get top vertices
        vertices = base_mesh.vertices
        max_z = np.max(vertices[:, 2])
        top_vertices = vertices[vertices[:, 2] > max_z - 0.1]

        # Create roof feature
        roof_height = 5
        roof_vertices = top_vertices.copy()
        roof_vertices[:, 2] += roof_height

        # Combine with original mesh
        # (Simplified - just return original for now)
        return base_mesh

    async def export_to_format(
        self, massing: BuildingMassing, format: str = "obj"
    ) -> bytes:
        """Export massing to various 3D formats."""

        if not massing.mesh:
            raise ValueError("No mesh to export")

        if format == "obj":
            return trimesh.exchange.obj.export_obj(massing.mesh)
        elif format == "stl":
            return massing.mesh.export(file_type="stl")
        elif format == "glb":
            return massing.mesh.export(file_type="glb")
        elif format == "json":
            # Custom JSON format for web visualization
            return json.dumps(
                {
                    "vertices": massing.mesh.vertices.tolist(),
                    "faces": massing.mesh.faces.tolist(),
                    "metadata": {
                        "height": massing.height,
                        "floors": massing.floors,
                        "gfa": massing.gfa,
                        "volume": massing.volume,
                        "scenario_type": massing.scenario_type.value,
                        "use_mix": massing.use_mix,
                    },
                }
            ).encode()
        else:
            raise ValueError(f"Unsupported export format: {format}")
