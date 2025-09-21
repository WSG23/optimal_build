"""Command-line helpers for exercising the AEC import/overlay/export flow."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional

# Configure runtime directories before importing the application settings.
_DEFAULT_RUNTIME_DIR = (
    os.environ.get("AEC_RUNTIME_DIR")
    or os.environ.get("DEV_RUNTIME_DIR")
    or ".devstack"
)
RUNTIME_DIR = Path(_DEFAULT_RUNTIME_DIR).expanduser().resolve()
RUNTIME_DIR.mkdir(parents=True, exist_ok=True)

_DB_PATH = (RUNTIME_DIR / "aec_flow.db").resolve()
os.environ.setdefault(
    "SQLALCHEMY_DATABASE_URI", f"sqlite+aiosqlite:///{_DB_PATH.as_posix()}"
)
os.environ.setdefault("STORAGE_LOCAL_PATH", str((RUNTIME_DIR / "storage").resolve()))
os.environ.setdefault("EXPORT_STORAGE_DIR", str((RUNTIME_DIR / "exports").resolve()))
os.environ.setdefault(
    "JOB_QUEUE_BACKEND", os.environ.get("JOB_QUEUE_BACKEND", "inline")
)

from sqlalchemy import select

from app.core.database import AsyncSessionLocal, engine
from app.core.geometry.builder import GraphBuilder
from app.core.geometry.serializer import GeometrySerializer
from app.core.models.geometry import CanonicalGeometry, GeometryNode
from app.main import app
from app.models.base import BaseModel
from app.models.overlay import OverlaySourceGeometry
from ..httpx import AsyncClient


STORAGE_PATH = Path(os.environ["STORAGE_LOCAL_PATH"]).resolve()
STORAGE_PATH.mkdir(parents=True, exist_ok=True)
EXPORT_PATH = Path(os.environ["EXPORT_STORAGE_DIR"]).resolve()
EXPORT_PATH.mkdir(parents=True, exist_ok=True)


_SCHEMA_INITIALISED = False


async def ensure_schema() -> None:
    """Create database tables if they do not yet exist."""

    global _SCHEMA_INITIALISED
    if _SCHEMA_INITIALISED:
        return
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)
    _SCHEMA_INITIALISED = True


def write_summary(name: str, payload: Mapping[str, Any]) -> Path:
    """Persist ``payload`` as JSON beneath the runtime directory."""

    path = RUNTIME_DIR / f"{name}.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def load_sample_payload(sample_path: Path) -> Dict[str, Any]:
    """Return the parsed sample payload located at ``sample_path``."""

    if not sample_path.exists():
        raise FileNotFoundError(f"Sample payload not found: {sample_path}")
    return json.loads(sample_path.read_text(encoding="utf-8"))


def _coerce_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


@dataclass
class SampleGeometry:
    canonical: CanonicalGeometry
    unit_ids: List[str]
    floor_names: List[str]


def build_canonical_geometry(sample: Mapping[str, Any]) -> SampleGeometry:
    """Recreate the canonical geometry used by the AEC workflow tests."""

    builder = GraphBuilder.new()
    level_lookup: Dict[str, Mapping[str, Any]] = {}
    collected_units: List[str] = []
    floor_names: List[str] = []

    layers = sample.get("layers") if isinstance(sample.get("layers"), Iterable) else []
    for index, layer in enumerate(layers, start=1):
        if not isinstance(layer, Mapping):
            continue
        level_id = f"L{index:02d}"
        metadata = dict(layer.get("metadata") or {})
        metadata.setdefault("layer_type", layer.get("type"))
        builder.add_level(
            {
                "id": level_id,
                "name": layer.get("name"),
                "elevation": metadata.get("elevation", 0.0),
                "metadata": metadata,
            }
        )
        level_lookup[level_id] = layer
        units: Iterable[Any] = (
            layer.get("units", []) if isinstance(layer.get("units"), Iterable) else []
        )
        floor_names.append(str(layer.get("name") or level_id))
        for unit_index, unit in enumerate(units, start=1):
            if not isinstance(unit, Mapping):
                continue
            space_id = f"{level_id}-U{unit_index:02d}"
            area_value = _coerce_float(unit.get("area_m2") or unit.get("area"))
            side = max((area_value or 1.0) ** 0.5, 1.0)
            boundary = [
                {"x": 0.0, "y": 0.0},
                {"x": side, "y": 0.0},
                {"x": side, "y": side},
                {"x": 0.0, "y": side},
            ]
            collected_units.append(space_id)
            metadata_payload = {
                key: value for key, value in unit.items() if key != "id"
            }
            metadata_payload.setdefault("status", unit.get("status", "pending"))
            builder.add_space(
                {
                    "id": space_id,
                    "name": unit.get("id") or space_id,
                    "level_id": level_id,
                    "boundary": boundary,
                    "metadata": metadata_payload,
                }
            )
            builder.add_relationship(
                {
                    "type": "contains",
                    "source_id": level_id,
                    "target_id": space_id,
                }
            )

    graph = builder.graph
    builder.validate_integrity()

    site_layer = next(
        (
            layer
            for layer in layers
            if isinstance(layer, Mapping)
            and str(layer.get("type", "")).lower() in {"site", "reference"}
        ),
        None,
    )
    root_properties: Dict[str, Any] = {"project": sample.get("project")}
    if isinstance(site_layer, Mapping):
        metadata = site_layer.get("metadata")
        if isinstance(metadata, Mapping):
            root_properties.update(metadata)

    root = GeometryNode(node_id="site-root", kind="site", properties=root_properties)

    for level_id, layer in level_lookup.items():
        if (
            not isinstance(layer, Mapping)
            or str(layer.get("type", "")).lower() != "floor"
        ):
            continue
        units = (
            list(layer.get("units", []))
            if isinstance(layer.get("units"), Iterable)
            else []
        )
        floor_metadata = {
            "name": layer.get("name"),
            "unit_count": len(units),
        }
        layer_meta = layer.get("metadata")
        if isinstance(layer_meta, Mapping) and "elevation" in layer_meta:
            floor_metadata["elevation"] = layer_meta["elevation"]
        floor_node = root.add_child(
            GeometryNode(node_id=level_id, kind="floor", properties=floor_metadata)
        )
        for unit_index, unit in enumerate(units, start=1):
            if not isinstance(unit, Mapping):
                continue
            space_id = f"{level_id}-U{unit_index:02d}"
            unit_properties = {
                "label": unit.get("id"),
                "area_m2": unit.get("area_m2"),
                "status": unit.get("status", "pending"),
            }
            if "height_m" in unit:
                unit_properties["height_m"] = unit["height_m"]
            floor_node.add_child(
                GeometryNode(node_id=space_id, kind="unit", properties=unit_properties)
            )

    canonical = CanonicalGeometry(
        root=root,
        metadata={"project": sample.get("project")},
        graph=graph.to_dict(),
    )
    return SampleGeometry(
        canonical=canonical, unit_ids=collected_units, floor_names=floor_names
    )


async def upsert_overlay_geometry(
    *,
    project_id: int,
    canonical: CanonicalGeometry,
    source_key: str,
    metadata: Mapping[str, Any],
) -> int:
    """Create or update an overlay source geometry for ``project_id``."""

    payload = canonical.to_dict()
    checksum = canonical.fingerprint()

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(OverlaySourceGeometry).where(
                OverlaySourceGeometry.project_id == project_id,
                OverlaySourceGeometry.source_geometry_key == source_key,
            )
        )
        record = result.scalar_one_or_none()
        if record is None:
            record = OverlaySourceGeometry(
                project_id=project_id,
                source_geometry_key=source_key,
                graph=payload,
                metadata=dict(metadata),
                checksum=checksum,
            )
            session.add(record)
        else:
            record.graph = payload
            updated_meta = dict(record.metadata or {})
            updated_meta.update(metadata)
            record.metadata = updated_meta
            record.checksum = checksum
        await session.commit()
        await session.refresh(record)
        return int(record.id)


async def import_sample(
    *,
    sample_path: Path,
    project_id: int,
    infer_walls: bool,
) -> Dict[str, Any]:
    """Upload the sample payload and seed overlay geometry."""

    await ensure_schema()
    sample_payload = load_sample_payload(sample_path)
    geometry = build_canonical_geometry(sample_payload)

    files = {
        "file": (
            sample_path.name,
            sample_path.read_bytes(),
            "application/json",
        )
    }
    form_data = {
        "enable_raster_processing": "true",
        "infer_walls": "true" if infer_walls else "false",
    }

    async with AsyncClient(app=app, base_url="http://testserver") as client:
        upload_response = await client.post(
            "/api/v1/import", files=files, data=form_data
        )
        if upload_response.status_code != 201:
            raise RuntimeError(
                f"Import failed with status {upload_response.status_code}: {upload_response.text}"
            )
        upload_payload = upload_response.json()

        import_id = upload_payload.get("import_id")
        parse_response = await client.post(f"/api/v1/parse/{import_id}")
        if parse_response.status_code != 200:
            raise RuntimeError(
                f"Parse trigger failed with status {parse_response.status_code}: {parse_response.text}"
            )
        parse_payload = parse_response.json()

    overlay_metadata = {
        "source": "sample-cli",
        "import_id": import_id,
        "project_name": sample_payload.get("project"),
    }
    source_id = await upsert_overlay_geometry(
        project_id=project_id,
        canonical=geometry.canonical,
        source_key="sample-floorplan",
        metadata=overlay_metadata,
    )

    summary = {
        "project_id": project_id,
        "import_id": import_id,
        "filename": upload_payload.get("filename"),
        "detected_units": upload_payload.get("detected_units"),
        "detected_floors": [
            floor.get("name") for floor in upload_payload.get("detected_floors", [])
        ],
        "parse_status": parse_payload.get("status"),
        "overlay_source_id": source_id,
        "unit_count": len(geometry.unit_ids),
        "floor_names": geometry.floor_names,
    }
    write_summary("import_sample", summary)
    return summary


def _summarise_overlays(items: Iterable[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    summary: List[Dict[str, Any]] = []
    for item in items:
        summary.append(
            {
                "id": item.get("id"),
                "code": item.get("code"),
                "status": item.get("status"),
                "severity": item.get("severity"),
                "score": item.get("score"),
            }
        )
    return summary


async def run_overlay(project_id: int) -> Dict[str, Any]:
    """Execute the overlay engine and return suggestion summaries."""

    await ensure_schema()
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        response = await client.post(f"/api/v1/overlay/{project_id}/run")
        if response.status_code != 200:
            raise RuntimeError(
                f"Overlay run failed with status {response.status_code}: {response.text}"
            )
        run_payload = response.json()

        listing = await client.get(f"/api/v1/overlay/{project_id}")
        if listing.status_code != 200:
            raise RuntimeError(
                f"Overlay listing failed with status {listing.status_code}: {listing.text}"
            )
        items = listing.json().get("items", [])

    summary = {
        "project_id": project_id,
        "job": run_payload,
        "suggestions": _summarise_overlays(items),
    }
    write_summary("overlay_run", summary)
    return summary


_SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}


def _select_candidate(
    items: Iterable[Mapping[str, Any]],
) -> Optional[Mapping[str, Any]]:
    ranked = sorted(
        (item for item in items if item.get("status") != "rejected"),
        key=lambda entry: (
            _SEVERITY_ORDER.get(str(entry.get("severity", "")).lower(), 5),
            entry.get("code") or "",
        ),
    )
    return ranked[0] if ranked else None


async def approve_overlay(
    *,
    project_id: int,
    suggestion_id: int,
    decided_by: str,
    notes: str,
) -> Mapping[str, Any]:
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        response = await client.post(
            f"/api/v1/overlay/{project_id}/decision",
            json={
                "suggestion_id": suggestion_id,
                "decision": "approve",
                "decided_by": decided_by,
                "notes": notes,
            },
        )
        if response.status_code != 200:
            raise RuntimeError(
                f"Overlay approval failed with status {response.status_code}: {response.text}"
            )
        payload = response.json().get("item", {})
    return payload


def _extract_filename(disposition: Optional[str]) -> Optional[str]:
    if not disposition:
        return None
    parts = [part.strip() for part in disposition.split(";")]
    for part in parts:
        if part.lower().startswith("filename="):
            value = part.split("=", 1)[1].strip()
            return value.strip('"')
    return None


async def export_approved(
    *,
    project_id: int,
    export_format: str,
    approver: str,
    notes: str,
) -> Dict[str, Any]:
    """Generate an export containing approved overlays for ``project_id``."""

    await ensure_schema()
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        listing = await client.get(f"/api/v1/overlay/{project_id}")
        if listing.status_code != 200:
            raise RuntimeError(
                f"Overlay listing failed with status {listing.status_code}: {listing.text}"
            )
        payload = listing.json()
        items: List[Mapping[str, Any]] = list(payload.get("items", []))
        if not items:
            raise RuntimeError(
                "No overlays available to export. Run the overlay job first."
            )

        approved = [item for item in items if item.get("status") == "approved"]
        candidate = approved[0] if approved else _select_candidate(items)
        approved_item: Mapping[str, Any] | None = approved[0] if approved else None

        if candidate and candidate.get("status") != "approved":
            approved_item = await approve_overlay(
                project_id=project_id,
                suggestion_id=int(candidate["id"]),
                decided_by=approver,
                notes=notes,
            )

        export_payload = {
            "format": export_format,
            "include_source": True,
            "include_approved_overlays": True,
            "include_pending_overlays": False,
            "include_rejected_overlays": False,
            "layer_map": {
                "source": {"floor": "A-FLOOR", "unit": "A-UNIT"},
                "overlays": {"heritage_conservation": "A-OVER-HERITAGE"},
                "styles": {
                    "heritage_conservation": {"color": "red"},
                    "approved": {"color": "green"},
                },
                "default_source_layer": "MODEL",
                "default_overlay_layer": "OVERLAYS",
            },
        }

        export_response = await client.post(
            f"/api/v1/export/{project_id}",
            json=export_payload,
        )
        if export_response.status_code != 200:
            raise RuntimeError(
                f"Export failed with status {export_response.status_code}: {export_response.text}"
            )

        disposition = export_response.headers.get("content-disposition")
        filename = (
            _extract_filename(disposition) or f"project-{project_id}.{export_format}"
        )
        artifact_path = EXPORT_PATH / filename
        artifact_path.write_bytes(export_response.content)

        manifest: Mapping[str, Any] | None = None
        try:
            manifest = json.loads(export_response.content.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            manifest = None

    summary: Dict[str, Any] = {
        "project_id": project_id,
        "artifact": {
            "path": str(artifact_path),
            "size_bytes": artifact_path.stat().st_size,
            "content_type": export_response.headers.get("content-type"),
            "renderer": export_response.headers.get("x-export-renderer"),
            "watermark": export_response.headers.get("x-export-watermark"),
        },
        "approved_overlay": approved_item,
        "overlay_count": len(items),
    }
    if manifest is not None:
        manifest_path = artifact_path.with_suffix(
            artifact_path.suffix + ".manifest.json"
        )
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
        )
        summary["manifest_path"] = str(manifest_path)
    write_summary("export_approved", summary)
    return summary


async def dispatch(args: argparse.Namespace) -> Dict[str, Any]:
    if args.command == "import-sample":
        return await import_sample(
            sample_path=Path(args.sample),
            project_id=args.project_id,
            infer_walls=args.infer_walls,
        )
    if args.command == "run-overlay":
        run_summary = await run_overlay(args.project_id)
        return run_summary
    if args.command == "export-approved":
        return await export_approved(
            project_id=args.project_id,
            export_format=args.format,
            approver=args.decided_by,
            notes=args.notes,
        )
    raise RuntimeError(f"Unsupported command: {args.command}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    import_parser = subparsers.add_parser(
        "import-sample",
        help="Upload the bundled sample and seed overlay geometry",
    )
    import_parser.add_argument(
        "--sample",
        default="tests/samples/sample_floorplan.json",
        help="Path to the sample payload (relative to backend/).",
    )
    import_parser.add_argument(
        "--project-id",
        type=int,
        default=101,
        help="Project identifier used when seeding overlay geometry.",
    )
    import_parser.add_argument(
        "--infer-walls",
        action="store_true",
        help="Enable wall inference during raster/vector processing.",
    )

    overlay_parser = subparsers.add_parser(
        "run-overlay",
        help="Execute the overlay engine for the seeded project",
    )
    overlay_parser.add_argument(
        "--project-id",
        type=int,
        default=101,
        help="Project identifier used for overlay evaluation.",
    )

    export_parser = subparsers.add_parser(
        "export-approved",
        help="Approve overlays and generate an export artefact",
    )
    export_parser.add_argument(
        "--project-id",
        type=int,
        default=101,
        help="Project identifier used for export generation.",
    )
    export_parser.add_argument(
        "--format",
        default="pdf",
        choices=["dxf", "dwg", "ifc", "pdf"],
        help="Export format to request from the API.",
    )
    export_parser.add_argument(
        "--decided-by",
        default="Planner Bot",
        help="Name recorded on the approval decision.",
    )
    export_parser.add_argument(
        "--notes",
        default="Automated approval via scripts.aec_flow",
        help="Notes to attach to the approval decision.",
    )

    return parser


def main(argv: Optional[Iterable[str]] = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result = asyncio.run(dispatch(args))
        print(json.dumps(result, indent=2, sort_keys=True))
    finally:
        # Ensure connections are released between invocations.
        asyncio.run(engine.dispose())


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
