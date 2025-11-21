# Singapore Parcel Ingestion Guide

Last updated: 2025-11-22
Owner: Codex (implementation), PM (data/API keys)

---

## 1. Dataset Overview

| Dataset | Source | Format | Notes |
|---------|--------|--------|-------|
| Land Lot Boundary (Polygon) | Singapore Land Authority / OneMap Theme API (`land_lot_boundary`) | GeoJSON (SVY21/EPSG:3414) | Cadastral lots used for parcel snapping, GPS logging, and preview overlays. |

### Download Options

**Option 1: OneMap Theme API (Programmatic Access)**

The OneMap Theme API requires authentication via API token:

1. **Obtain ONEMAP_TOKEN:**
   - Register for OneMap API access at https://www.onemap.gov.sg/
   - Generate an API token from your account dashboard
   - Export token: `export ONEMAP_TOKEN="your_token_here"`

2. **Fetch the dataset:**
   ```bash
   # Get theme info (returns GeoJSON download link)
   curl -H "Authorization: $ONEMAP_TOKEN" \
     "https://www.onemap.gov.sg/api/public/themeservice/getThemeInfo?themeName=land_lot_boundary" \
     > data/sg/parcels/theme_info.json

   # Extract download URL from response and fetch GeoJSON
   # (Exact download pattern depends on API response structure)
   ```

3. **API Response Format:**
   - Returns metadata about the `land_lot_boundary` theme
   - Includes GeoJSON download URL or pagination parameters
   - Authentication required: returns `{"message":"Missing Authentication Token"}` without token

**Option 2: data.gov.sg Bulk Download (Manual)**

- Visit [data.gov.sg – Land Lot Boundary](https://data.gov.sg/datasets?query=land%20lot%20boundary)
- Download the latest ZIP export
- Extract GeoJSON and save to `data/sg/parcels/land_lot_boundary.geojson`

**Storage:**
Store the GeoJSON under `data/sg/parcels/land_lot_boundary.geojson` (gitignored). The ingestion script accepts any path via `--input-path` if you prefer a different filename.

---

## 2. CLI Recipe

```bash
export SECRET_KEY=dev-secret
export DATABASE_URL="postgresql+asyncpg://postgres:password@localhost:5432/building_compliance"
export PYTHONPATH=/Users/wakaekihara/GitHub/optimal_build

.venv/bin/python -m backend.scripts.ingest_sg_parcels \
  --batch-size 1000 \
  --input-path data/sg/parcels/land_lot_boundary.geojson
```

### Key Behaviours
- Reads the GeoJSON stream incrementally (no huge memory spikes).
- Converts SVY21 (EPSG:3414) to WGS84 (EPSG:4326) via `pyproj`.
- Writes parcel metadata + multipolygon geometry into `ref_parcels` with `jurisdiction="SG"`.
- Default run truncates existing SG parcels; add `--no-reset` for incremental upserts and `--limit/--skip` while debugging.
- `--source-label` defaults to `sla_onemap` to trace provenance in `RefParcel.source`.

### Verifying the import

```bash
psql "$DATABASE_URL" -c "
  select count(*)
  from ref_parcels
  where jurisdiction = 'SG';
"

psql "$DATABASE_URL" -c "
  select parcel_ref, area_m2
  from ref_parcels
  where jurisdiction = 'SG'
  order by random()
  limit 5;
"
```

---

## 3. Automation Hooks

- `backend/app/services/overlay_ingest.PARCEL_INGESTION_HANDLERS["sg"]` points to `backend.scripts.ingest_sg_parcels:ingest_parcels`, enabling orchestration to trigger a Singapore refresh programmatically.
- Preview/GPS flows automatically snap Singapore captures to these parcels once the table is populated.

---

## 4. TODO / Follow-ups

- [ ] Schedule a monthly refresh job after verifying the dataset cadence with SLA.
- [ ] Capture a representative Singapore property after each refresh and ensure preview/finance still line up with parcel footprints.
- [ ] Expand documentation with zoning ingestion (URA Master Plan layers) once the pipeline is generalized.
