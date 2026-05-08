"""Bootstrap Singapore source datasets required by Capture.

This command is intended for deployment/bootstrap operations. It ingests the
public URA Master Plan zoning layer and SLA cadastral parcel layer into the
backend database, then prints a readiness summary.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_dotenv(path: Path, *, override: bool = False) -> None:
    """Load simple KEY=VALUE pairs before importing app settings."""

    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if override:
            os.environ[key] = value
        else:
            os.environ.setdefault(key, value)


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Bootstrap Singapore zoning and parcel data for Capture."
    )
    parser.add_argument(
        "--skip-zoning",
        action="store_true",
        help="Do not ingest URA Master Plan zoning polygons.",
    )
    parser.add_argument(
        "--skip-parcels",
        action="store_true",
        help="Do not ingest SLA cadastral parcel polygons.",
    )
    parser.add_argument(
        "--skip-buildings",
        action="store_true",
        help="Do not ingest URA Master Plan building footprints.",
    )
    parser.add_argument(
        "--download",
        action="store_true",
        help="Fetch latest public datasets from data.gov.sg before ingestion.",
    )
    parser.add_argument(
        "--zoning-input",
        type=Path,
        default=Path("data/sg/zoning/master_plan_2019_land_use.geojson"),
        help="Local URA Master Plan zoning GeoJSON path.",
    )
    parser.add_argument(
        "--parcel-input",
        type=Path,
        default=Path("data/sg/parcels/land_lot_boundary.geojson"),
        help="Local SLA cadastral parcel GeoJSON path.",
    )
    parser.add_argument(
        "--building-input",
        type=Path,
        default=Path("data/sg/buildings/master_plan_2019_building.geojson"),
        help="Local URA Master Plan building footprint GeoJSON path.",
    )
    parser.add_argument(
        "--parcel-source-epsg",
        type=int,
        default=4326,
        help="EPSG code for parcel source coordinates; data.gov.sg is 4326.",
    )
    parser.add_argument(
        "--max-zoning-features",
        type=int,
        default=None,
        help="Optional debug cap for zoning features.",
    )
    parser.add_argument(
        "--max-parcels",
        type=int,
        default=None,
        help="Optional debug cap for parcel features.",
    )
    parser.add_argument(
        "--max-buildings",
        type=int,
        default=None,
        help="Optional debug cap for building footprint features.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1000,
        help="Parcel insert batch size; increase for production database loads.",
    )
    return parser


async def _run(args: argparse.Namespace) -> dict[str, Any]:
    _load_dotenv(REPO_ROOT / ".env")
    _load_dotenv(REPO_ROOT / ".env.local", override=True)

    from app.core.database import AsyncSessionLocal
    from app.services.capture_data_readiness import get_capture_data_readiness
    from backend.scripts import (
        ingest_sg_building_footprints,
        ingest_sg_parcels,
        ingest_sg_zones,
    )

    results: dict[str, Any] = {}

    if not args.skip_zoning:
        zone_stats = await ingest_sg_zones.ingest_sg_zones(
            ingest_sg_zones.SGZoneIngestionOptions(
                input_path=args.zoning_input if args.zoning_input.exists() else None,
                output_path=args.zoning_input,
                layer_name="ura_master_plan_2019_land_use",
                max_features=args.max_zoning_features,
                persist=True,
                reset_layer=True,
                download=args.download or not args.zoning_input.exists(),
            )
        )
        results["zoning"] = zone_stats

    if not args.skip_parcels:
        parcel_stats = await ingest_sg_parcels.ingest_parcels(
            ingest_sg_parcels.ParcelIngestionOptions(
                input_path=args.parcel_input,
                jurisdiction="SG",
                batch_size=args.batch_size,
                limit=args.max_parcels,
                skip=0,
                reset=True,
                source_epsg=args.parcel_source_epsg,
                source_label="sla_data_gov",
                download=args.download or not args.parcel_input.exists(),
            )
        )
        results["parcels"] = parcel_stats.as_dict()

    if not args.skip_buildings:
        building_stats = await ingest_sg_building_footprints.ingest_building_footprints(
            ingest_sg_building_footprints.BuildingFootprintIngestionOptions(
                input_path=args.building_input,
                jurisdiction="SG",
                layer_name="ura_master_plan_2019_building",
                batch_size=args.batch_size,
                limit=args.max_buildings,
                reset=True,
                source_label="ura_data_gov",
                download=args.download or not args.building_input.exists(),
            )
        )
        results["buildings"] = building_stats.as_dict()

    async with AsyncSessionLocal() as session:
        results["readiness"] = await get_capture_data_readiness(
            session,
            jurisdiction="SG",
        )

    return results


def main() -> None:
    args = _build_arg_parser().parse_args()
    result = asyncio.run(_run(args))
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
