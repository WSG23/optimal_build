"""Export utilities for CAD and BIM artefacts."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import io
import json
import os
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Mapping
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models.geometry import CanonicalGeometry, GeometryNode
from app.models.overlay import OverlaySourceGeometry, OverlaySuggestion

try:  # pragma: no cover - optional dependency
    import ezdxf  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - handled gracefully at runtime
    ezdxf = None  # type: ignore

try:  # pragma: no cover - optional dependency
    import ifcopenshell  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - handled gracefully at runtime
    ifcopenshell = None  # type: ignore

try:  # pragma: no cover - optional dependency
    from reportlab.pdfgen import canvas as pdf_canvas  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - handled gracefully at runtime
    pdf_canvas = None  # type: ignore


DEFAULT_PENDING_WATERMARK = "PRELIMINARY – Pending overlay approvals"


class ExportFormat(str, Enum):
    """Supported export formats."""

    DXF = "dxf"
    DWG = "dwg"
    IFC = "ifc"
    PDF = "pdf"

    @property
    def media_type(self) -> str:
        mapping = {
            ExportFormat.DXF: "application/dxf",
            ExportFormat.DWG: "application/dwg",
            ExportFormat.IFC: "application/vnd.ifc",
            ExportFormat.PDF: "application/pdf",
        }
        return mapping[self]

    @property
    def extension(self) -> str:
        return self.value


@dataclass
class LayerMapping:
    """Mapping configuration for source and overlay layers."""

    source: Dict[str, str] = field(default_factory=dict)
    overlays: Dict[str, str] = field(default_factory=dict)
    styles: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    default_source_layer: str = "MODEL"
    default_overlay_layer: str = "OVERLAYS"

    def map_source(self, kind: str) -> str:
        """Return the layer to use for the supplied geometry node kind."""

        if kind in self.source:
            return self.source[kind]
        if kind:
            return kind.upper()
        return self.default_source_layer

    def map_overlay(self, code: str, *, status: str | None = None) -> str:
        """Return the layer assigned to the overlay suggestion."""

        if code in self.overlays:
            return self.overlays[code]
        if status and status in self.overlays:
            return self.overlays[status]
        return f"{self.default_overlay_layer}:{code}" if code else self.default_overlay_layer

    def style_for(self, code: str, severity: str | None) -> Dict[str, Any]:
        """Lookup a style configuration for a layer."""

        if code in self.styles:
            return dict(self.styles[code])
        if severity and severity in self.styles:
            return dict(self.styles[severity])
        return {}


@dataclass
class ExportOptions:
    """Runtime export options."""

    format: ExportFormat
    include_source: bool = True
    include_approved_overlays: bool = True
    include_pending_overlays: bool = False
    include_rejected_overlays: bool = False
    layer_mapping: LayerMapping = field(default_factory=LayerMapping)
    pending_watermark: str = DEFAULT_PENDING_WATERMARK


@dataclass
class ExportArtifact:
    """Metadata describing a generated export artefact."""

    project_id: int
    format: ExportFormat
    path: Path
    filename: str
    media_type: str
    manifest: Dict[str, Any]

    def open(self) -> io.BufferedReader:
        """Return a binary stream for the stored artefact."""

        return self.path.open("rb")


class ExportError(RuntimeError):
    """Base class for export failures."""


class ProjectGeometryMissing(ExportError):
    """Raised when no source geometry exists for a project."""


class ArtifactStorage:
    """Abstract interface for storing generated artefacts."""

    def store(
        self,
        *,
        project_id: int,
        fmt: ExportFormat,
        payload: bytes,
        manifest: Mapping[str, Any],
        filename: str | None = None,
    ) -> ExportArtifact:
        raise NotImplementedError


class LocalExportStorage(ArtifactStorage):
    """Filesystem backed artefact storage."""

    def __init__(self, base_dir: Path | str | None = None) -> None:
        if base_dir is not None:
            root = Path(base_dir)
        else:
            env_dir = os.getenv("EXPORT_STORAGE_DIR")
            if env_dir:
                root = Path(env_dir)
            else:
                tmp_root = os.getenv("TMPDIR", "/tmp")
                root = Path(tmp_root) / "optimal_build" / "exports"
        self.base_dir = root
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def store(
        self,
        *,
        project_id: int,
        fmt: ExportFormat,
        payload: bytes,
        manifest: Mapping[str, Any],
        filename: str | None = None,
    ) -> ExportArtifact:
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        suffix = filename or f"project-{project_id}-{timestamp}-{uuid.uuid4().hex[:8]}.{fmt.extension}"
        target = self.base_dir / suffix
        with target.open("wb") as stream:
            stream.write(payload)
        manifest_payload = dict(manifest)
        manifest_payload.setdefault("format", fmt.value)
        return ExportArtifact(
            project_id=project_id,
            format=fmt,
            path=target,
            filename=target.name,
            media_type=fmt.media_type,
            manifest=manifest_payload,
        )


def _iter_nodes(geometries: Iterable[CanonicalGeometry]) -> Iterator[GeometryNode]:
    for geometry in geometries:
        yield from geometry.iter_nodes()


def _normalise_geometry(
    geometries: Iterable[CanonicalGeometry],
    *,
    mapping: LayerMapping,
) -> List[Dict[str, Any]]:
    features: List[Dict[str, Any]] = []
    for node in _iter_nodes(geometries):
        layer = mapping.map_source(node.kind)
        features.append(
            {
                "layer": layer,
                "id": node.node_id,
                "kind": node.kind,
                "properties": dict(node.properties),
            }
        )
    return features


def _normalise_overlays(
    overlays: Iterable[OverlaySuggestion],
    *,
    mapping: LayerMapping,
    include_approved: bool,
    include_pending: bool,
    include_rejected: bool,
) -> List[Dict[str, Any]]:
    features: List[Dict[str, Any]] = []
    for overlay in overlays:
        status = (overlay.status or "pending").lower()
        include = False
        if status == "approved" and include_approved:
            include = True
        elif status == "pending" and include_pending:
            include = True
        elif status == "rejected" and include_rejected:
            include = True
        if not include:
            continue
        layer = mapping.map_overlay(overlay.code, status=status)
        payload = overlay.engine_payload or {}
        nodes = payload.get("nodes")
        if not isinstance(nodes, list):
            nodes = []
        features.append(
            {
                "layer": layer,
                "code": overlay.code,
                "title": overlay.title,
                "status": status,
                "severity": overlay.severity,
                "style": mapping.style_for(overlay.code, overlay.severity),
                "nodes": list(dict.fromkeys(str(node) for node in nodes)),
            }
        )
    return features


def _group_by_layer(features: Iterable[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for feature in features:
        layer = feature.get("layer", "MODEL")
        payload = dict(feature)
        payload.pop("layer", None)
        grouped.setdefault(layer, []).append(payload)
    return grouped


def _pending_failures(overlays: Iterable[OverlaySuggestion]) -> bool:
    for overlay in overlays:
        if (overlay.status or "pending").lower() == "pending":
            return True
    return False


class BaseWriter:
    """Base class for export writers."""

    format: ExportFormat

    def __init__(self, *, mapping: LayerMapping, options: ExportOptions) -> None:
        self.mapping = mapping
        self.options = options

    def _build_manifest(
        self,
        *,
        geometry: List[Dict[str, Any]],
        overlays: List[Dict[str, Any]],
        watermark: str | None,
    ) -> Dict[str, Any]:
        manifest: Dict[str, Any] = {
            "format": self.format.value,
            "renderer": "fallback",
            "options": {
                "include_source": self.options.include_source,
                "include_approved_overlays": self.options.include_approved_overlays,
                "include_pending_overlays": self.options.include_pending_overlays,
                "include_rejected_overlays": self.options.include_rejected_overlays,
            },
            "layers": _group_by_layer(geometry) if geometry else {},
            "overlays": _group_by_layer(overlays) if overlays else {},
        }
        if watermark:
            manifest["watermark"] = watermark
        if self.mapping.styles:
            manifest["styles"] = self.mapping.styles
        return manifest

    def render(
        self,
        geometry: List[Dict[str, Any]],
        overlays: List[Dict[str, Any]],
        watermark: str | None,
    ) -> tuple[bytes, Dict[str, Any]]:
        raise NotImplementedError


class DXFWriter(BaseWriter):
    format = ExportFormat.DXF

    def render(
        self,
        geometry: List[Dict[str, Any]],
        overlays: List[Dict[str, Any]],
        watermark: str | None,
    ) -> tuple[bytes, Dict[str, Any]]:
        manifest = self._build_manifest(geometry=geometry, overlays=overlays, watermark=watermark)
        if ezdxf is not None:  # pragma: no cover - exercised when dependency available
            try:
                doc = ezdxf.new()
                modelspace = doc.modelspace()
                for layer, entities in manifest["layers"].items():
                    if layer not in doc.layers:
                        doc.layers.new(name=layer)
                    for entity in entities:
                        label = entity.get("kind", "entity")
                        modelspace.add_text(label, dxfattribs={"layer": layer})
                for layer, items in manifest["overlays"].items():
                    if layer not in doc.layers:
                        doc.layers.new(name=layer)
                    for overlay in items:
                        label = f"{overlay.get('code')}:{overlay.get('status')}"
                        modelspace.add_text(label, dxfattribs={"layer": layer})
                if watermark:
                    modelspace.add_text(watermark, dxfattribs={"layer": "WATERMARK"})
                buffer = io.BytesIO()
                doc.write(buffer)
                manifest["renderer"] = "ezdxf"
                return buffer.getvalue(), manifest
            except Exception:  # pragma: no cover - fallback for unexpected writer errors
                pass
        payload = json.dumps(manifest, sort_keys=True).encode("utf-8")
        return payload, manifest


class DWGWriter(BaseWriter):
    format = ExportFormat.DWG

    def render(
        self,
        geometry: List[Dict[str, Any]],
        overlays: List[Dict[str, Any]],
        watermark: str | None,
    ) -> tuple[bytes, Dict[str, Any]]:
        manifest = self._build_manifest(geometry=geometry, overlays=overlays, watermark=watermark)
        manifest.setdefault("renderer", "fallback")
        return json.dumps(manifest, sort_keys=True).encode("utf-8"), manifest


class IFCWriter(BaseWriter):
    format = ExportFormat.IFC

    def render(
        self,
        geometry: List[Dict[str, Any]],
        overlays: List[Dict[str, Any]],
        watermark: str | None,
    ) -> tuple[bytes, Dict[str, Any]]:
        manifest = self._build_manifest(geometry=geometry, overlays=overlays, watermark=watermark)
        if ifcopenshell is not None:  # pragma: no cover - exercised when dependency available
            try:
                model = ifcopenshell.file(schema="IFC4")
                for entities in manifest["layers"].values():
                    for entity in entities:
                        model.create_entity(
                            "IfcAnnotation",
                            GlobalId=str(uuid.uuid4()),
                            Name=entity.get("kind", "Annotation"),
                            Description=json.dumps(entity.get("properties", {})),
                        )
                buffer = io.BytesIO()
                buffer.write(model.to_string().encode("utf-8"))
                manifest["renderer"] = "ifcopenshell"
                return buffer.getvalue(), manifest
            except Exception:  # pragma: no cover - fallback for optional dependency failure
                pass
        return json.dumps(manifest, sort_keys=True).encode("utf-8"), manifest


class PDFWriter(BaseWriter):
    format = ExportFormat.PDF

    def render(
        self,
        geometry: List[Dict[str, Any]],
        overlays: List[Dict[str, Any]],
        watermark: str | None,
    ) -> tuple[bytes, Dict[str, Any]]:
        manifest = self._build_manifest(geometry=geometry, overlays=overlays, watermark=watermark)
        if pdf_canvas is not None:  # pragma: no cover - exercised when dependency available
            try:
                buffer = io.BytesIO()
                pdf = pdf_canvas.Canvas(buffer)
                pdf.drawString(36, 800, "Optimal Build Export")
                y = 780
                for layer, entities in manifest["layers"].items():
                    pdf.drawString(36, y, f"Layer: {layer} ({len(entities)} entities)")
                    y -= 16
                if overlays:
                    pdf.drawString(36, y, "Overlays:")
                    y -= 16
                    for layer, entries in manifest["overlays"].items():
                        pdf.drawString(48, y, f"{layer}: {len(entries)}")
                        y -= 14
                if watermark:
                    pdf.setFont("Helvetica-Bold", 48)
                    pdf.setFillColorRGB(1, 0, 0)
                    pdf.drawString(120, 400, watermark)
                pdf.save()
                buffer.seek(0)
                manifest["renderer"] = "reportlab"
                return buffer.getvalue(), manifest
            except Exception:  # pragma: no cover - fallback for optional dependency failure
                pass
        return json.dumps(manifest, sort_keys=True).encode("utf-8"), manifest


_WRITERS: Dict[ExportFormat, type[BaseWriter]] = {
    ExportFormat.DXF: DXFWriter,
    ExportFormat.DWG: DWGWriter,
    ExportFormat.IFC: IFCWriter,
    ExportFormat.PDF: PDFWriter,
}


def get_writer(format: ExportFormat, *, options: ExportOptions) -> BaseWriter:
    """Return an instantiated writer for the requested format."""

    writer_cls = _WRITERS.get(format)
    if writer_cls is None:  # pragma: no cover - defensive guard
        raise ValueError(f"Unsupported export format: {format}")
    return writer_cls(mapping=options.layer_mapping, options=options)


async def generate_project_export(
    session: AsyncSession,
    *,
    project_id: int,
    options: ExportOptions,
    storage: ArtifactStorage | None = None,
) -> ExportArtifact:
    """Generate an export artefact for the given project."""

    result = await session.execute(
        select(OverlaySourceGeometry).where(OverlaySourceGeometry.project_id == project_id)
    )
    records = list(result.scalars().unique())
    if not records:
        raise ProjectGeometryMissing(f"No source geometry found for project {project_id}")

    geometries: List[CanonicalGeometry] = []
    for record in records:
        payload = record.graph
        if isinstance(payload, dict):
            geometries.append(CanonicalGeometry.from_dict(payload))
    if not geometries:
        raise ProjectGeometryMissing(f"Source geometry payload missing for project {project_id}")

    overlay_result = await session.execute(
        select(OverlaySuggestion).where(OverlaySuggestion.project_id == project_id)
    )
    overlay_suggestions = list(overlay_result.scalars().unique())

    geometry_features: List[Dict[str, Any]] = []
    if options.include_source:
        geometry_features = _normalise_geometry(geometries, mapping=options.layer_mapping)

    overlay_features = _normalise_overlays(
        overlay_suggestions,
        mapping=options.layer_mapping,
        include_approved=options.include_approved_overlays,
        include_pending=options.include_pending_overlays,
        include_rejected=options.include_rejected_overlays,
    )

    watermark = options.pending_watermark if _pending_failures(overlay_suggestions) else None

    writer = get_writer(options.format, options=options)
    payload, manifest = writer.render(geometry_features, overlay_features, watermark)
    manifest.setdefault("project_id", project_id)
    manifest.setdefault("generated_at", datetime.utcnow().isoformat())

    storage_backend = storage or LocalExportStorage()
    artifact = storage_backend.store(
        project_id=project_id,
        fmt=options.format,
        payload=payload,
        manifest=manifest,
    )
    return artifact


__all__ = [
    "ArtifactStorage",
    "DEFAULT_PENDING_WATERMARK",
    "ExportArtifact",
    "ExportError",
    "ExportFormat",
    "ExportOptions",
    "LayerMapping",
    "LocalExportStorage",
    "ProjectGeometryMissing",
    "generate_project_export",
    "get_writer",
]
