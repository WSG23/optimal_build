# Export API

The export service allows CAD overlays and source geometry to be downloaded in
DWG, DXF, IFC, or PDF formats. The endpoint streams a binary payload and exposes
metadata via HTTP headers so that the frontend can surface rendering and
watermark details.

## Endpoint

`POST /api/v1/export/{project_id}`

### Request body

```
{
  "format": "dxf",
  "include_source": true,
  "include_approved_overlays": true,
  "include_pending_overlays": false,
  "include_rejected_overlays": false,
  "pending_watermark": "PRELIMINARY – Pending overlay approvals",
  "layer_map": {
    "source": {"building": "A-BUILD"},
    "overlays": {"heritage_conservation": "A-OVER-HERITAGE"},
    "styles": {"heritage_conservation": {"color": "red"}},
    "default_source_layer": "MODEL",
    "default_overlay_layer": "OVERLAYS"
  }
}
```

- `format` – required. One of `dxf`, `dwg`, `ifc`, or `pdf`.
- `include_source` – include base geometry layers (defaults to `true`).
- `include_approved_overlays` / `include_pending_overlays` /
  `include_rejected_overlays` – control which overlay decision states are
  exported.
- `pending_watermark` – optional override for the default pending watermark
  string when the project still has outstanding overlays.
- `layer_map` – optional layer/style overrides. Provide CAD layer names for
  geometry kinds, overlay codes, and custom styles.

### Response

The response streams a binary payload. Clients should inspect the following
headers for metadata:

- `Content-Disposition` – contains the suggested filename.
- `X-Export-Renderer` – indicates whether an external renderer like `ezdxf`
  produced the file or the JSON fallback was used.
- `X-Export-Watermark` – present when pending overlays triggered a watermark.

The response body is the generated CAD/BIM export in the requested format. When
optional dependencies are unavailable the service emits a JSON manifest that
lists the layers and overlay metadata, allowing round-trip verification in the
frontend.
