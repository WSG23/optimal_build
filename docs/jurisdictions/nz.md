# New Zealand Jurisdiction Dossier

Last updated: 2025-11-20
Owner: Codex (implementation), Claude (validation), PM (data/API keys)

---

## 1. Summary

- **Jurisdiction code:** `nz`
- **Currency:** NZD
- **Default units:** Square meters (sqm)
- **Covered cities:** Auckland, Wellington, Christchurch
- **Primary data portals:**
  - [LINZ Data Service](https://data.linz.govt.nz/) – parcel polygons, zoning, address data
  - [Stats NZ](https://www.stats.govt.nz/) – demographic and economic data
  - [CBRE NZ Research](https://www.cbre.co.nz/insights/reports) – market rent/vacancy data

---

## 2. Environment Variables

Add the following to `.env` (or your secrets manager):

```
# LINZ Data Service API key (Koordinates)
NZ_LINZ_API_KEY=87058cae575f4685bb3101d5c88e726f

# Google Maps Geocoding API (shared with other jurisdictions)
GOOGLE_MAPS_API_KEY=<existing_key>
```

These values are read by `backend/scripts/ingest_nz_parcels.py`.

---

## 3. Datasets & Endpoints

| Dataset | Source | Format | Notes |
|--------|--------|--------|-------|
| NZ Primary Parcels | LINZ `layer-50804` | GeoJSON via WFS | Cadastral parcel boundaries (NZGD2000/EPSG:2193) |
| District Plan Zones | LINZ `layer-50780` | GeoJSON | Zoning overlays by territorial authority |
| Heritage Sites | Heritage NZ / LINZ `layer-50071` | GeoJSON | Historic places register |
| Address Points | LINZ `layer-3353` | GeoJSON | NZ Building Outlines with addresses |
| Rent & Vacancy | CBRE NZ / Colliers NZ | PDF/Web | Populate `data/nz_market_assumptions.yaml` |

### Working WFS Query Example (Parcels)

```bash
curl "https://data.linz.govt.nz/services;key=87058cae575f4685bb3101d5c88e726f/wfs?service=WFS&version=2.0.0&request=GetFeature&typeNames=layer-50804&outputFormat=application/json&cql_filter=land_district='Auckland'"
```

**Note:** LINZ WFS supports CQL filtering for performance. Use `land_district` to filter by region.

---

## 4. Parcel Ingestion Workflow

The NZ parcel data from LINZ uses NZGD2000 / NZTM (EPSG:2193) projection. The ingestion
helper converts to WGS84 (EPSG:4326) and persists to `ref_parcels`:

```bash
PYTHONPATH=$REPO_ROOT \
  SECRET_KEY=dev-secret \
  DATABASE_URL="postgresql+asyncpg://postgres:password@localhost:5432/building_compliance" \
  .venv/bin/python -m backend.scripts.ingest_nz_parcels \
  --city auckland \
  --batch-size 1000 \
  --persist
```

### Key Behaviors

- Fetches parcel polygons from LINZ WFS API for specified city (Auckland/Wellington/Christchurch)
- Reprojects from EPSG:2193 (NZTM) to WGS84 (EPSG:4326) using `pyproj`
- Validates geometries with `shapely.validation.make_valid`
- Stores parcel metadata and multipolygon geometry in `ref_parcels` with `jurisdiction="NZ"`
- `--no-reset` toggles incremental upserts; by default truncates previous NZ parcels for the specified city
- Use `--limit 500` for testing or `--skip 10000` to skip broken records

### City-Specific Filters

| City | Land District Filter | Approx. Parcel Count |
|------|---------------------|---------------------|
| Auckland | `land_district='Auckland'` | ~600,000 |
| Wellington | `land_district='Wellington'` | ~180,000 |
| Christchurch | `land_district='Canterbury'` | ~250,000 |

---

## 5. Zoning Ingestion Workflow

Use the LINZ WFS helper to download and persist district plan zoning polygons into `ref_zoning_layers`:

```bash
PYTHONPATH=$REPO_ROOT \
  SECRET_KEY=dev-secret \
  DATABASE_URL="postgresql+asyncpg://postgres:password@localhost:5432/building_compliance" \
  .venv/bin/python -m backend.scripts.ingest_nz_zones \
  --city auckland \
  --layer-name district_plan_zones \
  --persist
```

### Key Notes

- Script auto-detects CRS and reprojects if needed (LINZ typically provides EPSG:2193)
- `--persist` converts each feature into a MultiPolygon and stores under `jurisdiction="NZ"`
- Default behavior truncates existing NZ rows for that layer; use `--no-reset-layer` for incremental upserts
- Attributes (zone code, zone name, rules URL) persisted in `attributes` JSON column

---

## 6. Developer Preview & Finance Hooks

### GPS Property Logging

Developer GPS logging accepts `jurisdictionCode=NZ` for New Zealand captures:

```bash
http POST :8000/api/v1/developers/properties/log-gps \
  latitude=-36.8432 longitude=174.7660 \
  jurisdictionCode=NZ \
  previewGeometryDetailLevel=medium
```

### Finance Integration

- Any preview job for a property with `jurisdiction_code="NZ"` stores the code in `PreviewJob.metadata.jurisdiction_code`
- Finance feasibility requests with `scenario.jurisdictionCode="NZ"` auto-default to NZD currency
- Unit conversions: NZ uses **sqm** (no conversion needed from internal representation)

---

## 7. Implementation Tasks

### Ingestion
- [x] Document LINZ layer IDs and WFS endpoints
- [x] Implement `backend/scripts/ingest_nz_parcels.py` (WFS → PostGIS, EPSG:2193 → 4326)
- [x] Implement `backend/scripts/ingest_nz_zones.py` (district plan zones)
- [x] Add NZ jurisdiction config to `backend/app/data/jurisdictions.json`
- [x] Create pytest tests in `backend/tests/test_nz_jurisdiction.py` (7/7 passing)

### Preview & Finance Validation
- Seed data includes demo property: **Commercial Bay** (`-36.8432, 174.7660`)
  - Property ID: `f2a9c1e5-3b7d-4c8f-9a2e-5d6b8e4f1a3c`
- Queue preview job locally:
  ```bash
  PYTHONPATH=$REPO_ROOT \
    .venv/bin/python -m backend.scripts.preview enqueue \
    --property-id f2a9c1e5-3b7d-4c8f-9a2e-5d6b8e4f1a3c
  ```
- Validate finance output with `jurisdictionCode="NZ"` in scenario

### Finance/Preview Integration
- [x] Create `data/nz_market_assumptions.yaml` with CBRE/Colliers data
- [x] Add NZ to `backend/app/data/jurisdictions.json` (NZD, sqm, market data)
- [x] Add `NZ_LINZ_API_KEY` to `backend/app/core/config.py`
- [x] Add Commercial Bay demo property to `backend/scripts/seed_properties_projects.py`
- [x] Run seeding script to create Commercial Bay in database
- [ ] Test GPS logging with `jurisdictionCode=NZ` (manual testing instructions below)
- [ ] Test finance calculations with NZD currency (manual testing instructions below)

### Validation
- [x] Add CLI recipe to `docs/validation/preview_async_linux.md` for `jurisdiction=nz`
- [ ] Manual QA: Capture Auckland property, generate feasibility + finance export
- [ ] Attach results to validation log

---

## 8. Testing Plan

### Unit Tests
- `tests/services/test_overlay_ingest.py::test_ingest_nz_zones`
- `tests/services/test_market_data.py::test_load_nz_assumptions`

### Integration Tests
- `tests/test_api/test_developers_site_acquisition.py::test_log_property_nz`
- `tests/test_api/test_finance_asset_breakdown.py::test_finance_export_uses_nzd`

### Manual Testing
Follow workflow documented above once sample data is available.

---

## 9. Market Assumptions Snapshot

The file `data/nz_market_assumptions.yaml` contains canonical assumptions for finance calculations.

Values extracted from:
- **CBRE Auckland Q4 2025 Figures Report**
- **Colliers NZ Research Report November 2025**

### Rent (NZD/sqm/month)

| Asset Type | Value |
|------------|-------|
| Office | 33.0 |
| Retail | 150.0 |
| Industrial | 16.0 |
| Residential | 28.0 (estimate) |

### Vacancy Rates (%)

| Asset Type | Rate |
|------------|------|
| Office | 12.0% |
| Retail | 2.0% |
| Industrial | 1.7% |
| Residential | 3.0% (estimate) |

### OPEX (% of rent)

- Property Tax (Rates): 2.0%
- Management Fee: 2.5%
- Utilities: 1.5%
- Insurance: 0.6% (higher due to seismic risk)
- Maintenance: 2.0%

### Finance Assumptions

- Construction Loan Rate: 6.3% (Nov 2025 floating rate)
- Equity/Debt Split: 30/70
- Exit Cap Rate: 6.5% (blended across asset classes)

---

## 10. Coordinate Reference Systems

| System | EPSG Code | Usage |
|--------|-----------|-------|
| **NZGD2000 / NZTM** | EPSG:2193 | LINZ default projection (meters) |
| **WGS84** | EPSG:4326 | Application standard (lat/lng) |

**Transformation:** All LINZ data in EPSG:2193 is reprojected to EPSG:4326 during ingestion using `pyproj`.

---

## 11. Multi-City Support

### City Codes

| City | Code | Land District |
|------|------|---------------|
| Auckland | `auckland` | Auckland |
| Wellington | `wellington` | Wellington |
| Christchurch | `christchurch` | Canterbury |

### City-Specific Ingestion

Ingest parcels per city to manage dataset size:

```bash
# Auckland
.venv/bin/python -m backend.scripts.ingest_nz_parcels --city auckland --persist

# Wellington
.venv/bin/python -m backend.scripts.ingest_nz_parcels --city wellington --persist

# Christchurch
.venv/bin/python -m backend.scripts.ingest_nz_parcels --city christchurch --persist
```

---

## 12. Manual Testing Instructions

### Demo Property Seeding (Commercial Bay)

Run once per environment to create the deterministic Auckland seed.

```bash
export SECRET_KEY=dev-secret
export DATABASE_URL="postgresql+asyncpg://postgres:password@localhost:5432/building_compliance"
export PYTHONPATH=/Users/wakaekihara/GitHub/optimal_build
.venv/bin/python -m backend.scripts.seed_properties_projects
```

Optional: add `--reset` to purge existing demo properties before reseeding. After the script succeeds, confirm the insert:

```bash
psql "$DATABASE_URL" -c \
  "select id,name,jurisdiction_code from properties where id='f2a9c1e5-3b7d-4c8f-9a2e-5d6b8e4f1a3c';"
```

Expected output: single row with `Commercial Bay` and `jurisdiction_code = NZ`.

### GPS Logging Test

To test GPS logging with NZ jurisdiction code:

```bash
# Start backend if not running
SECRET_KEY=dev-secret \
  DATABASE_URL="postgresql+asyncpg://postgres:password@localhost:5432/building_compliance" \
  PYTHONPATH=/Users/wakaekihara/GitHub/optimal_build \
  JOB_QUEUE_BACKEND=inline \
  /Users/wakaekihara/GitHub/optimal_build/.venv/bin/uvicorn app.main:app \
  --host 0.0.0.0 --port 8000 --app-dir backend

# In another terminal, test GPS logging for Commercial Bay
curl -X POST http://localhost:8000/api/v1/developers/properties/log-gps \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": -36.8432,
    "longitude": 174.7660,
    "jurisdictionCode": "NZ",
    "previewGeometryDetailLevel": "medium"
  }'
```

**Expected Result:**
- Response should normalize `jurisdictionCode` to `"NZ"` (uppercase)
- Property should be geocoded with Google Maps API
- Preview job should be queued with `metadata.jurisdiction_code="NZ"`

### Preview Job Validation (Linux quick runner)

Use the shared Linux validation harness with the NZ property ID:

```bash
cd /Users/wakaekihara/GitHub/optimal_build
export PREVIEW_PROPERTY_ID="f2a9c1e5-3b7d-4c8f-9a2e-5d6b8e4f1a3c"
export DATABASE_URL="postgresql+asyncpg://postgres:password@localhost:5432/building_compliance"
bash scripts/validate_preview_async_linux.sh
```

Expected output (see `docs/validation/preview_async_linux.md` for details):
- Job metadata contains `"jurisdiction_code": "NZ"`
- `preview.json.market.currency_code == "NZD"` and `area_units == "sqm"`
- Finance defaults inside the preview payload show NZ rent/OPEX numbers

### Finance Calculation Test

To test finance calculations with NZD currency:

```bash
# 1. Create a finance project for Commercial Bay
curl -X POST http://localhost:8000/api/v1/finance/projects \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <YOUR_TOKEN>" \
  -d '{
    "propertyId": "f2a9c1e5-3b7d-4c8f-9a2e-5d6b8e4f1a3c",
    "name": "Commercial Bay Finance Analysis",
    "jurisdictionCode": "NZ"
  }'

# 2. Create a scenario with NZ market assumptions
curl -X POST http://localhost:8000/api/v1/finance/scenarios \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <YOUR_TOKEN>" \
  -d '{
    "projectId": "<PROJECT_ID_FROM_STEP_1>",
    "name": "Base Case NZ",
    "assetMix": [
      {
        "assetType": "office",
        "niaSqm": 50000,
        "rentPsmMonth": 33.0
      },
      {
        "assetType": "retail",
        "niaSqm": 35000,
        "rentPsmMonth": 150.0
      }
    ],
    "jurisdictionCode": "NZ"
  }'
```

**Expected Result:**
- All currency values should be in NZD (NZ$)
- Market assumptions should use NZ rates:
  - Office rent: 33.0 NZD/sqm/month
  - Retail rent: 150.0 NZD/sqm/month
  - Vacancy: Office 12%, Retail 2%
  - Construction loan rate: 6.3%
  - Exit cap rate: 6.5%
- Area units should remain in sqm (no conversion needed)

### Finance Validation Workflow (CLI)

For deterministic regression runs, drive the finance API via the helper script:

```bash
cd /Users/wakaekihara/GitHub/optimal_build/backend
PYTHONPATH=/Users/wakaekihara/GitHub/optimal_build \
  python -m backend.scripts.finance_run_scenario \
  --api-base http://127.0.0.1:8000 \
  --project-id 401 \
  --project-name "Commercial Bay NZ" \
  --scenario-name "NZ Base Case" \
  --payload ../data/nz_finance_scenario_payload.json \
  --export-path /tmp/commercial-bay-nz-finance.csv
```

The sample payload in `data/nz_finance_scenario_payload.json` already sets `scenario.currency="NZD"` and `scenario.cost_escalation.jurisdiction="NZ"`. Modify it as needed to mirror the rent/OPEX defaults from `data/nz_market_assumptions.yaml`. After the script downloads the CSV, confirm the header rows reference NZD currency and that asset rows show the NZ rent levels.

---

## 13. Open Questions / TODOs

- [ ] Validate rent/OPEX numbers with latest CBRE/Colliers quarterly reports
- [ ] Determine Wellington and Christchurch market assumptions (currently using Auckland data)
- [ ] Confirm heritage overlay ingestion workflow (Heritage NZ API vs LINZ layer)
- [ ] Test zoning parser with Auckland Unitary Plan structure

Document findings in this file as they arrive.

---

**Ready for Implementation:** Codex can now implement ingestion scripts following this guide. API key confirmed, market data extracted, demo property coordinates validated.
