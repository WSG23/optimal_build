import pytest

from backend.app.core.export import ExportFormat, ExportOptions, LayerMapping, LocalExportStorage, generate_project_export
from backend.app.core.models.geometry import CanonicalGeometry, GeometryNode
from backend.app.models.overlay import OverlaySourceGeometry, OverlaySuggestion


async def _seed_project(async_session_factory, project_id: int = 1) -> int:
    geometry = CanonicalGeometry(
        root=GeometryNode(
            node_id="site-1",
            kind="site",
            properties={"name": "Test Site"},
            children=[
                GeometryNode(
                    node_id="bldg-1",
                    kind="building",
                    properties={"height_m": 52.0, "usage": "residential"},
                )
            ],
        ),
        metadata={"project": project_id},
    )
    payload = geometry.to_dict()
    checksum = geometry.fingerprint()

    async with async_session_factory() as session:
        source = OverlaySourceGeometry(
            project_id=project_id,
            source_geometry_key="primary",
            graph=payload,
            metadata={"source": "unit-test"},
            checksum=checksum,
        )
        session.add(source)
        await session.flush()

        approved = OverlaySuggestion(
            project_id=project_id,
            source_geometry_id=source.id,
            code="heritage_conservation",
            type="review",
            title="Heritage conservation review",
            status="approved",
            severity="high",
            engine_payload={"nodes": ["bldg-1"]},
            target_ids=["bldg-1"],
            props={"score": 0.95},
            rule_refs=["heritage.review"],
            geometry_checksum=checksum,
        )
        pending = OverlaySuggestion(
            project_id=project_id,
            source_geometry_id=source.id,
            code="tall_building_review",
            type="assessment",
            title="Tall building review",
            status="pending",
            severity="medium",
            engine_payload={"nodes": ["bldg-1"]},
            target_ids=["bldg-1"],
            props={"score": 0.75},
            rule_refs=["building.height"],
            geometry_checksum=checksum,
        )
        session.add_all([approved, pending])
        await session.commit()
    return project_id


@pytest.mark.parametrize("format_", [ExportFormat.DXF, ExportFormat.IFC, ExportFormat.PDF])
@pytest.mark.asyncio
async def test_generate_export_creates_files_per_format(format_, async_session_factory, tmp_path):
    project_id = await _seed_project(async_session_factory)
    storage_root = tmp_path / format_.value
    storage = LocalExportStorage(base_dir=storage_root)

    async with async_session_factory() as session:
        options = ExportOptions(
            format=format_,
            layer_mapping=LayerMapping(
                source={"building": "A-BUILD"},
                overlays={"heritage_conservation": "A-OVER-HERITAGE"},
                styles={"heritage_conservation": {"color": "red"}},
            ),
        )
        artifact = await generate_project_export(
            session,
            project_id=project_id,
            options=options,
            storage=storage,
        )

    assert artifact.format is format_
    assert artifact.path.exists()
    manifest = artifact.manifest
    assert manifest["format"] == format_.value
    assert "A-BUILD" in manifest["layers"]
    assert manifest["layers"]["A-BUILD"][0]["kind"] == "building"
    assert "A-OVER-HERITAGE" in manifest["overlays"]
    overlay_entries = manifest["overlays"]["A-OVER-HERITAGE"]
    assert all(entry["status"] == "approved" for entry in overlay_entries)
    assert overlay_entries[0]["style"].get("color") == "red"
    assert overlay_entries[0]["target_ids"] == ["bldg-1"]
    assert overlay_entries[0]["rule_refs"] == ["heritage.review"]
    assert overlay_entries[0]["props"].get("score") == 0.95
    assert manifest.get("watermark"), "Watermark should be applied when pending overlays exist"

    with artifact.open() as stream:
        payload = stream.read()
    assert payload, "Export payload should not be empty"


@pytest.mark.asyncio
async def test_pending_overlays_mapped_to_separate_layers(async_session_factory, tmp_path):
    project_id = await _seed_project(async_session_factory)
    storage = LocalExportStorage(base_dir=tmp_path / "dwg")

    async with async_session_factory() as session:
        options = ExportOptions(
            format=ExportFormat.DWG,
            include_approved_overlays=False,
            include_pending_overlays=True,
            layer_mapping=LayerMapping(
                overlays={
                    "tall_building_review": "A-OVER-TALL",
                    "pending": "A-OVER-PENDING",
                }
            ),
        )
        artifact = await generate_project_export(
            session,
            project_id=project_id,
            options=options,
            storage=storage,
        )

    manifest = artifact.manifest
    overlays = manifest["overlays"]
    assert overlays, "Pending overlays should be present in the export manifest"
    pending_layers = set(overlays.keys())
    assert any(layer.startswith("A-OVER") for layer in pending_layers)
    all_statuses = {entry["status"] for entries in overlays.values() for entry in entries}
    assert all_statuses == {"pending"}, "Only pending overlays should be exported when toggled"
    for entries in overlays.values():
        codes = {entry["code"] for entry in entries}
        assert "heritage_conservation" not in codes
    assert manifest["layers"], "Source geometry layers should still be included"
    assert manifest.get("watermark"), "Watermark should flag presence of pending overlays"

    with artifact.open() as stream:
        payload = stream.read()
    assert payload
