"""Transform raw heritage datasets into the canonical overlay GeoJSON."""

from __future__ import annotations

import argparse
import json
import logging
import math
import tempfile
import zipfile
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

from shapely import ops
from shapely.geometry import shape as shapely_shape

from . import DEFAULT_DATA_DIR
from ._shapefile_reader import iter_shapes

logger = logging.getLogger(__name__)

try:
    from shapely.geometry import mapping as shapely_mapping
except (
    ImportError
):  # pragma: no cover - shapely should be available, but guard defensively
    shapely_mapping = None


SVY21_A = 6378137.0
SVY21_F_INV = 298.257223563
SVY21_F = 1 / SVY21_F_INV
SVY21_K0 = 1.0
SVY21_LAT0 = math.radians(1 + 22 / 60)  # 1°22' N
SVY21_LON0 = math.radians(103 + 50 / 60)  # 103°50' E
SVY21_FALSE_E = 28001.642
SVY21_FALSE_N = 38744.572
SVY21_E2 = 2 * SVY21_F - SVY21_F**2
SVY21_E_PRIME2 = SVY21_E2 / (1 - SVY21_E2)


def _calc_meridian_arc(phi: float) -> float:
    e2 = SVY21_E2
    a = SVY21_A
    term1 = 1 - e2 / 4 - 3 * e2**2 / 64 - 5 * e2**3 / 256
    term2 = 3 * e2 / 8 + 3 * e2**2 / 32 + 45 * e2**3 / 1024
    term3 = 15 * e2**2 / 256 + 45 * e2**3 / 1024
    term4 = 35 * e2**3 / 3072
    return a * (
        term1 * phi
        - term2 * math.sin(2 * phi)
        + term3 * math.sin(4 * phi)
        - term4 * math.sin(6 * phi)
    )


def _svy21_xy_to_lonlat(
    x: float, y: float, z: float | None = None
) -> tuple[float, float]:
    easting = x - SVY21_FALSE_E
    northing = y - SVY21_FALSE_N

    m_prime = _calc_meridian_arc(SVY21_LAT0) + northing / SVY21_K0
    mu = m_prime / (
        SVY21_A * (1 - SVY21_E2 / 4 - 3 * SVY21_E2**2 / 64 - 5 * SVY21_E2**3 / 256)
    )

    e1 = (1 - math.sqrt(1 - SVY21_E2)) / (1 + math.sqrt(1 - SVY21_E2))
    j1 = (3 * e1 / 2) - (27 * e1**3 / 32)
    j2 = (21 * e1**2 / 16) - (55 * e1**4 / 32)
    j3 = 151 * e1**3 / 96
    j4 = 1097 * e1**4 / 512

    fp = (
        mu
        + j1 * math.sin(2 * mu)
        + j2 * math.sin(4 * mu)
        + j3 * math.sin(6 * mu)
        + j4 * math.sin(8 * mu)
    )

    sin_fp = math.sin(fp)
    cos_fp = math.cos(fp)
    tan_fp = math.tan(fp)

    c1 = SVY21_E_PRIME2 * cos_fp**2
    t1 = tan_fp**2
    r1 = SVY21_A * (1 - SVY21_E2) / ((1 - SVY21_E2 * sin_fp**2) ** 1.5)
    n1 = SVY21_A / math.sqrt(1 - SVY21_E2 * sin_fp**2)
    d = easting / (n1 * SVY21_K0)

    lat = fp - (n1 * tan_fp / r1) * (
        d**2 / 2
        - (5 + 3 * t1 + 10 * c1 - 4 * c1**2 - 9 * SVY21_E_PRIME2) * d**4 / 24
        + (61 + 90 * t1 + 298 * c1 + 45 * t1**2 - 252 * SVY21_E_PRIME2 - 3 * c1**2)
        * d**6
        / 720
    )

    lon = (
        SVY21_LON0
        + (
            d
            - (1 + 2 * t1 + c1) * d**3 / 6
            + (5 - 2 * c1 + 28 * t1 - 3 * c1**2 + 8 * SVY21_E_PRIME2 + 24 * t1**2)
            * d**5
            / 120
        )
        / cos_fp
    )

    return (math.degrees(lon), math.degrees(lat))


def _build_feature_from_geometry(
    geometry: Mapping[str, Any],
    bbox: Sequence[float],
    properties: Mapping[str, Any],
    *,
    source: str,
    risk: str = "high",
    notes: Iterable[str] | None = None,
) -> dict[str, Any]:
    geom = shapely_shape(geometry)
    geom_wgs = ops.transform(_svy21_xy_to_lonlat, geom)
    centroid = geom_wgs.centroid
    feature_notes = list(notes or [])
    return {
        "type": "Feature",
        "properties": {
            "name": str(
                properties.get("GROUP_NAME")
                or properties.get("NAME")
                or "Heritage Overlay"
            ),
            "risk": risk,
            "source": source,
            "notes": feature_notes,
            "heritage_premium_pct": 5.0,
            "attributes": {k: v for k, v in properties.items() if v not in (None, "")},
        },
        "geometry": shapely_mapping(geom_wgs) if shapely_mapping else geometry,
        "bbox": list(geom_wgs.bounds),
        "centroid": [centroid.x, centroid.y],
    }


def _transform_ura_conservation(raw_path: Path) -> Iterable[dict[str, Any]]:
    with tempfile.TemporaryDirectory() as tmp:
        working_dir = Path(tmp)
        if raw_path.is_file() and raw_path.suffix.lower() == ".zip":
            with zipfile.ZipFile(raw_path) as archive:
                archive.extractall(working_dir)
        elif raw_path.is_dir():
            for item in raw_path.iterdir():
                if item.is_file():
                    target = working_dir / item.name
                    target.write_bytes(item.read_bytes())
        else:
            raise FileNotFoundError(raw_path)

        shp_files = list(working_dir.glob("*.shp"))
        dbf_files = list(working_dir.glob("*.dbf"))
        if not shp_files or not dbf_files:
            raise FileNotFoundError("Missing .shp/.dbf files in extracted URA dataset")

        dbf_path = dbf_files[0]
        for geometry_info, record in iter_shapes(shp_files[0], dbf_path):
            properties = record
            group_name = properties.get("GROUP_NAME") or properties.get("DESCRIPTIO")
            planning_area = properties.get("PLANNING_AREA")
            category = properties.get("CATEGORY") or properties.get("DESCRIPTIO")
            notes = []
            if group_name:
                notes.append(f"{group_name} conservation area.")
            if category:
                notes.append(f"URA category: {category}.")
            if planning_area:
                notes.append(f"Located within planning area: {planning_area}.")
            yield _build_feature_from_geometry(
                geometry_info["geometry"],
                geometry_info["bbox"],
                properties,
                source="URA",
                notes=notes,
            )


def _transform_geojson(
    raw_path: Path, *, source: str, risk: str = "info"
) -> Iterable[dict[str, Any]]:
    if raw_path.is_file() and raw_path.suffix.lower() == ".zip":
        with zipfile.ZipFile(raw_path) as archive:
            inner_files = [
                name for name in archive.namelist() if name.lower().endswith(".geojson")
            ]
            if not inner_files:
                raise FileNotFoundError(f"No GeoJSON found in archive {raw_path}")
            with archive.open(inner_files[0]) as handle:
                data = json.load(handle)
    else:
        data = json.loads(raw_path.read_text(encoding="utf-8"))

    features = data.get("features", [])
    for feature in features:
        geometry = feature.get("geometry")
        if not geometry:
            continue
        props = feature.get("properties", {})
        name = (
            props.get("name")
            or props.get("NAME")
            or props.get("Title", "Heritage Site")
        )
        notes = [
            props.get("description") or props.get("DESCRIPTION", "Heritage record.")
        ]
        geom = shapely_shape(geometry)
        yield {
            "type": "Feature",
            "properties": {
                "name": str(name),
                "risk": risk,
                "source": source,
                "notes": [note for note in notes if note],
                "heritage_premium_pct": 2.5 if risk == "medium" else 1.0,
                "attributes": {k: v for k, v in props.items() if v not in (None, "")},
            },
            "geometry": shapely_mapping(geom) if shapely_mapping else geometry,
            "bbox": list(geom.bounds),
            "centroid": [geom.centroid.x, geom.centroid.y],
        }


TRANSFORMERS: dict[str, callable[[Path], Iterable[dict[str, Any]]]] = {
    "ura_conservation": _transform_ura_conservation,
    "nhb_historic_sites": lambda path: _transform_geojson(
        path, source="NHB Historic Site", risk="medium"
    ),
    "nhb_heritage_trails": lambda path: _transform_geojson(
        path, source="NHB Heritage Trail", risk="info"
    ),
    "nhb_monuments": lambda path: _transform_geojson(
        path, source="NHB National Monument", risk="high"
    ),
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Transform heritage raw inputs into canonical overlays"
    )
    parser.add_argument(
        "--dataset",
        choices=sorted(TRANSFORMERS.keys()),
        default="ura_conservation",
        help="Dataset key to transform",
    )
    parser.add_argument(
        "--input-path",
        default=f"{DEFAULT_DATA_DIR}/raw/ura_conservation",
        help="Raw dataset path (directory or zipfile)",
    )
    parser.add_argument(
        "--output",
        default=f"{DEFAULT_DATA_DIR}/processed/heritage_overlays.geojson",
        help="Destination GeoJSON path",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    transformer = TRANSFORMERS[args.dataset]
    raw_path = Path(args.input_path)

    features = list(transformer(raw_path))
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {
            "dataset": args.dataset,
            "source_path": str(raw_path),
            "feature_count": len(features),
        },
    }

    if output_path.exists():
        existing_payload = json.loads(output_path.read_text(encoding="utf-8"))
        existing_features = existing_payload.get("features", [])
        new_sources = {feat.get("properties", {}).get("source") for feat in features}
        filtered_existing = [
            feat
            for feat in existing_features
            if feat.get("properties", {}).get("source") not in new_sources
        ]
        payload["features"] = filtered_existing + features
        payload["metadata"]["feature_count"] = len(payload["features"])

    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    logger.info("Wrote %s features to %s", len(payload["features"]), output_path)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
