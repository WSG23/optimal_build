# Sample CAD/BIM Fixtures

The `samples/` directory provides lightweight CAD and BIM assets that mirror the
scenarios covered by our automated tests. These files are intentionally small so
they can live in the repository while still exercising key paths in the import
and export pipelines.

## Directory Layout

```
samples/
├── dxf/
│   └── flat_two_bed.dxf
├── ifc/
│   └── office_small.ifc
└── pdf/
    └── floor_simple.pdf
```

## Fixture Details

### `ifc/office_small.ifc`

* **Purpose:** Validates multi-storey detection when running the IFC parsing job.
* **Structure:** Two `IfcBuildingStorey` levels ("Ground Floor" and "Level 02")
  with three `IfcSpace` units distributed across the storeys.
* **Usage:** Exercised by
  `backend/tests/test_jobs/test_parse_cad_samples.py::test_ifc_sample_detects_multiple_storeys`
  to confirm that storeys and space counts are emitted by the parser.

### `dxf/flat_two_bed.dxf`

* **Purpose:** Provides two lightweight polylines on distinct layers to surface
  layer naming metadata during DXF ingestion.
* **Structure:** The `LEVEL_01` and `LEVEL_02` layers each contain a closed
  `LWPOLYLINE` footprint representing one residential unit.
* **Usage:** Exercised by
  `backend/tests/test_jobs/test_parse_cad_samples.py::test_dxf_sample_exposes_layered_units`
  to assert that entity counts and layer names are preserved when processing DXF
  payloads.

### `pdf/floor_simple.pdf`

* **Purpose:** Supplies a two-page vector PDF for the raster/vector conversion
  job so that wall candidates can be derived from multiple floors.
* **Structure:** Each page contains a stroked rectangle representing the floor
  boundary; page numbers surface as layer identifiers in the resulting vector
  paths.
* **Usage:** Exercised by
  `backend/tests/test_jobs/test_parse_cad_samples.py::test_pdf_sample_vectorizes_multiple_pages`
  to confirm that multi-page PDF payloads yield layer-aware vector paths and
  baseline wall detection results.

## Manual Validation

To manually inspect or regenerate test outcomes when working on the import and
export pipelines:

1. Run the CAD parsing tests (dependencies such as `ifcopenshell`, `ezdxf`, and
   `PyMuPDF` must be available):
   ```bash
   pytest backend/tests/test_jobs/test_parse_cad_samples.py
   ```
2. Open the fixtures in your preferred CAD/BIM tooling to review geometry,
   layer assignments, and floor naming conventions before extending parsers or
   exporters.

The fixtures are synthetic and were authored for regression coverage; they do
not originate from customer data.
