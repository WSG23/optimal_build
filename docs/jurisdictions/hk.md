# Hong Kong Jurisdiction Dossier

Last updated: 2025-11-18
Owner: Codex (implementation), Claude (validation), PM (data/API keys)

---

## 1. Summary

- **Jurisdiction code:** `hk`
- **Currency:** HKD
- **Default units:** Square feet (sqft)
- **Primary data portals:**
  - [DATA.GOV.HK](https://data.gov.hk/en/) – parcel polygons, planning areas, heritage lists
  - [Lands Department GeoSpatial Data Store](https://geodata.gov.hk/) – zoning shapefiles (requires API token)
  - [Rating and Valuation Department](https://www.rvd.gov.hk/) – rent/vacancy statistics (PDF/CSV downloads)

---

## 2. Environment Variables

Add the following to `.env` (or your secrets manager):

```
# DATA.GOV.HK application token
HK_DATA_GOV_API_KEY=todo_replace_with_real_key

# Optional: Lands Department geospatial token (if separate)
HK_GEOSPATIAL_TOKEN=todo_replace_with_real_token
```

These values are read by `backend/scripts/ingest_hk_zones.py`.

---

## 3. Datasets & Endpoints

| Dataset | Source | Format | Notes |
|--------|--------|--------|-------|
| Zoning polygons | Lands Department (`https://api.data.gov.hk/v2/filter`) | GeoJSON | Provide `$format=geojson` and include API key header `key: HK_DATA_GOV_API_KEY` |
| Historical parcels | DATA.GOV.HK cadastral dataset | GeoJSON/CSV | Used to generate preview footprints when developer capture lacks precise outlines |
| Heritage list | Antiquities and Monuments Office CSV | CSV | For overlay service (heritage warnings) |
| Rent & vacancy | Rating and Valuation Department | CSV/PDF | Populate `data/hk_market_assumptions.yaml` (see Section 8) |

Working query example (zoning polygons):

```
curl -X POST "https://api.data.gov.hk/v2/filter" \
  -H "Content-Type: application/json" \
  -H "key: ${HK_DATA_GOV_API_KEY}" \
  -d '{
    "resource": "https://www.landsd.gov.hk/datagovhk/zoning_latest.geojson",
    "section": 1,
    "format": "json"
  }'
```

*Endpoints and parameters may change; confirm once credentials arrive.*

---

## 4. Parcel Ingestion Workflow

The cadastral parcel bundle from CSDI lives inside `data/hk/lots/` (gitignored). The
primary geometry file is `LandParcel_Lot_PUBLIC_20251014.gdb_LOT_converted.json`
which ships with EPSG:2326 coordinates. Use the ingestion helper to convert every
polygon into WGS84 and persist it to `ref_parcels`:

```
PYTHONPATH=$REPO_ROOT \
  .venv/bin/python -m backend.scripts.ingest_hk_parcels \
  --input-path data/hk/lots/LandParcel_Lot_PUBLIC_20251014.gdb_LOT_converted.json \
  --batch-size 1000
```

Key behaviours:

- Streams the GeoJSON without loading the 1.1 GB file entirely into memory (custom
  parser, no external network calls required).
- Detects invalid HK80 polygons, fixes them via `shapely.validation.make_valid`, and
  projects them to WGS84 using `pyproj`.
- Stores parcel metadata and multipolygon geometry in `ref_parcels` with
  `jurisdiction="HK"` so the buildable + preview stacks can resolve Hong Kong lots.
- `--no-reset` toggles incremental upserts; by default the loader truncates the
  previous HK parcel rows to avoid duplicates.

You can dry-run a subset with `--limit 500` or skip a block with `--skip 10000` when
debugging a broken record. For extremely large batches, raise `--batch-size` to 2 000+
so the script commits less frequently.

---

## 5. Regulated Area / Zoning Persistence

Use the Planning Department WFS helper to both download and persist the regulated area
polygons into `ref_zoning_layers`:

```
PYTHONPATH=$REPO_ROOT \
  .venv/bin/python -m backend.scripts.ingest_hk_zones \
  --typename "RA_PLAN_CSDI:TPIS_ADM.OD_RA_PLAN_CSDI" \
  --skip-transform \
  --persist \
  --layer-name regulated_area
```

Key notes:

- The script auto-detects whether reprojection is needed; pass `--skip-transform`
  when the feed already returns WGS84.
- `--persist` converts each feature into a MultiPolygon and stores it under
  `jurisdiction="HK"` / `layer_name="regulated_area"`. The default is to truncate
  existing HK rows for that layer; supply `--no-reset-layer` for incremental upserts.
- Attributes such as plan number, gazette date, and scheme names are persisted in the
  `attributes` JSON column to feed preview/buildable services.

If you only need to download the GeoJSON (no DB writes), omit `--persist` and the
script will simply write to `data/hk/zoning/`.

### Developer Preview & Finance Hooks

- Developer GPS logging now accepts `jurisdictionCode` so HK captures can bypass the
  Singapore-only OneMap defaults:

  ```bash
  http POST :8000/api/v1/developers/properties/log-gps \
    latitude=22.2854 longitude=114.1589 \
    jurisdictionCode=HK \
    previewGeometryDetailLevel=medium
  ```

- Any preview job queued for a property tagged with `jurisdiction_code="HK"` stores the
  code in `PreviewJob.metadata.jurisdiction_code`, making the frontend aware of local
  units/currency when rendering `preview.json`.
- Finance feasibility requests can supply `scenario.jurisdictionCode="HK"` (or inherit it
  from a property/project) to auto-default the scenario currency to HKD and enforce the
  correct cost-escalation jurisdiction code.

---

## 6. Implementation Tasks

### Ingestion
- [ ] Finalize dataset URLs for zoning + parcels (see table above).
- [ ] Flesh out `backend/scripts/ingest_hk_zones.py` to:
  - Fetch GeoJSON (streaming to disk)
  - Reproject into WGS84 (use `shapely` / `pyproj` if dataset not already EPSG:4326)
  - Persist polygons to the `zoning_overlays` / `ref_zoning_layers` table with `jurisdiction_code="hk"`
  - Register the parser in `backend/app/services/overlay_ingest.py`
- [ ] Create pytest fixture `hk_property()` with sample parcel geometry for regression tests.

### Preview & Finance Validation
- Seed data already includes a deterministic HK demo property: `Central Harbour Gateway`
  (`88a5b6d4-2d25-4ff1-a549-7bbd2d5e81c2`). Use it when triggering automation scripts.
- Queue a preview job locally once the property exists:
  ```bash
  PYTHONPATH=$REPO_ROOT \
    .venv/bin/python -m backend.scripts.preview enqueue \
    --property-id 88a5b6d4-2d25-4ff1-a549-7bbd2d5e81c2
  ```
- To validate finance output, post a feasibility payload with `jurisdictionCode="HK"`
  inside `scenario`. Currency defaults to HKD and cost-escalation uses the HK indices.

### Finance/Preview Integration
- [ ] Load `data/hk_market_assumptions.yaml` via market-data service.
- [ ] Ensure finance engine uses HKD currency + sqft conversions.
- [ ] Update preview generator to respect Hong Kong-specific `geometry_detail_level` defaults (no change expected, but document).

### Validation
- [ ] Add CLI recipe to `docs/validation/preview_async_linux.md` for `jurisdiction=hk`.
- [ ] Manual QA script: capture property in Kowloon, generate feasibility + finance export, attach screenshots/results to `docs/archive/expansion/hk_validation_<date>.md`.

---

## 7. Testing Plan

1. **Unit tests**
   - `tests/services/test_overlay_ingest.py::test_ingest_hk_zones`
   - `tests/services/test_market_data.py::test_load_hk_assumptions`
2. **Integration tests**
   - `tests/test_api/test_developers_site_acquisition.py::test_log_property_hk`
   - `tests/test_api/test_finance_asset_breakdown.py::test_finance_export_uses_hkd`
3. **Manual**
   - Follow the workflow documented above once sample data is available.

---

## 8. Market Assumptions Snapshot

The file `data/hk_market_assumptions.yaml` contains the canonical assumptions for finance calculations. Values are placeholders until we ingest real statistics (replace with actual data once confirmed):

```yaml
hk_market_data:
  currency: "HKD"
  units: "sqft"
  rent_psf_month:
    office: 11.5
    retail: 18.7
    residential: 9.2
    industrial: 5.8
  opex_assumptions:
    property_tax_percent: 5.0
    management_fee_percent: 2.5
    utilities_percent: 1.8
    insurance_percent: 0.4
    maintenance_percent: 2.0
  vacancy_rates:
    office: 0.10
    retail: 0.07
    residential: 0.05
    industrial: 0.08
  finance_assumptions:
    construction_loan_rate: 4.2
    equity_debt_split: [30, 70]
    exit_cap_rate: 4.5
```

---

## 9. Open Questions / TODOs

- [ ] Confirm whether Lands Department API permits bulk downloads without paid account.
- [ ] Decide on geocoding source (OneMap HK vs Google Maps fallback).
- [ ] Validate rent/opex numbers with latest CBRE quarterly report.
- [ ] Determine if Hong Kong heritage overlays require separate ingestion workflow.

Document findings in this file as they arrive.

---

**Ready for Implementation:** As soon as API keys and dataset URLs are confirmed, Codex can complete the ingestion script and add regression tests following this guide.
