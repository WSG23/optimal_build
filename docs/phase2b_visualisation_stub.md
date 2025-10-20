# Phase 2B Visualisation Stub Specification

The developer and feasibility APIs now expose placeholder metadata for 3D previews. This note describes the current fields and how the future rendering workflow should consume them.

## 1. Backend Fields (already available)

`DeveloperVisualizationSummary` and `SiteAcquisitionResult.visualization` now include:

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | Preview status flag (`placeholder`, `processing`, `ready`, etc.). Currently `placeholder`. |
| `preview_available` | bool | Whether a high-fidelity preview is ready. Currently `false`. |
| `notes` | array[str] | User-facing notes/messages. Stub includes callouts for upcoming Phase 2B work. |
| `concept_mesh_url` | string/null | URL to a coarse GLB mesh. Stub path: `/static/dev-previews/{property_id}.glb`. Replace with real asset when available. |
| `camera_orbit_hint` | object/null | Suggested orbit parameters for the viewer, e.g. `{ "theta": 48, "phi": 32, "radius": 1.6 }`. |
| `preview_seed` | int/null | Seed used to generate deterministic placeholder previews (e.g., based on scenario count). |

## 2. Intended Rendering Behaviour

1. **Load stub mesh**
   If `concept_mesh_url` is present, the viewer should attempt to load this GLB into the scene. For now it can be a simple extrusion generated from zoning metrics.

2. **Default camera orbit**
   If `camera_orbit_hint` is provided, use it to set the initial viewpoint in the WebGL viewer. These values match a standard orbit control interface (theta/phi in degrees, radius in scene units).

3. **Status handling**
   - `preview_available == false`: show a message (“High-fidelity preview coming soon”) and render only the stub mesh.
   - `preview_available == true`: switch to the real asset once the rendering pipeline is live (Phase 2B/TODO).

4. **Metadata overlay (future)**
   Use `notes` and the financial snapshot to annotate the preview (e.g., colouring floors by asset type or risk level).

## 3. TODO / Integration Checklist

- [ ] Replace stub GLB generation with actual massing based on envelope + asset mix.
- [ ] Store real preview assets (e.g., in S3) and update `concept_mesh_url`.
- [ ] Extend `camera_orbit_hint` to include pitch/target coordinates if required.
- [ ] Add API endpoint for preview status polling once renders become asynchronous.

With these fields in place, the frontend can already show a consistent placeholder experience while the rendering pipeline is being built.
