# Phase 2B Visualisation Stub Specification

The developer and feasibility APIs now expose placeholder metadata for 3D previews. This note describes the current fields and how the future rendering workflow should consume them.

## 1. Backend Fields (already available)

`DeveloperVisualizationSummary` and `SiteAcquisitionResult.visualization` now include:

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | Preview status flag (`placeholder`, `processing`, `ready`, etc.). Currently `placeholder`. |
| `preview_available` | bool | Whether a preview asset is ready. Now `true` once the JSON massing file is generated. |
| `notes` | array[str] | User-facing notes/messages. Stub includes callouts for upcoming Phase 2B work. |
| `concept_mesh_url` | string/null | URL to a coarse GLB mesh. Stub path: `/static/dev-previews/{property_id}.glb`. Replace with real asset when available. |
| `camera_orbit_hint` | object/null | Suggested orbit parameters for the viewer, e.g. `{ "theta": 48, "phi": 32, "radius": 1.6 }`. |
| `preview_seed` | int/null | Seed used to generate deterministic placeholder previews (e.g., based on scenario count). |
| `massing_layers` | array[object] | Per-asset stub massing data (`asset_type`, `allocation_pct`, `gfa_sqm`, `nia_sqm`, `estimated_height_m`, `color`). |
| `color_legend` | array[object] | Colour legend entries (`asset_type`, `label`, `color`, `description`) used by the frontend to label the preview. |

## 2. Intended Rendering Behaviour

1. **Load preview asset**
   If `concept_mesh_url` is present, fetch the JSON payload and render the per-asset extrusions. The JSON file lives at `/static/dev-previews/{property_id}.json` and contains `layers` matching `massing_layers`.

2. **Default camera orbit**
   If `camera_orbit_hint` is provided, use it to set the initial viewpoint in the WebGL viewer. These values match a standard orbit control interface (theta/phi in degrees, radius in scene units).

3. **Status handling**
   - `preview_available == false`: show a message (“High-fidelity preview coming soon”) and render only the stub mesh.
   - `preview_available == true`: switch to the real asset once the rendering pipeline is live (Phase 2B/TODO).

4. **Metadata overlay (future)**
   Use `notes`, `massing_layers`, and the financial snapshot to annotate the preview (e.g., colouring floors by asset type or risk level).

## 3. TODO / Integration Checklist

- [ ] Replace JSON massing stub with production-ready geometry export.
- [ ] Store real preview assets (e.g., in S3) and update `concept_mesh_url`.
- [ ] Extend `camera_orbit_hint` to include pitch/target coordinates if required.
- [ ] Add API endpoint for preview status polling once renders become asynchronous.

With these fields in place, the frontend can already show a consistent placeholder experience while the rendering pipeline is being built.
