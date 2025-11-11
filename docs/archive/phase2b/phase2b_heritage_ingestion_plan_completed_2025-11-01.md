# Phase 2B Heritage Overlay Ingestion Plan (v0.5)

This document outlines the work required to replace the stub `heritage_overlays.json` file with a production ingestion pipeline that sources official heritage/conservation boundaries and makes them available to the optimizer and capture flows.

---

## Changelog

**v0.5 (2025-10-22)** - Full NHB coverage (sites, monuments, trails)
- Added NHB National Monuments (`data/heritage/raw/MonumentsGEOJSON.geojson`) and Heritage Trails (`data/heritage/raw/HeritageTrailsKML.geojson`) to the ingest pipeline; the published bundle now includes 194 features across URA + three NHB sources.
- CLI `transform`/`load` commands re-run after manual KML→GeoJSON conversion to merge trails.
- Docs/UI updated so developer capture surfaces heritage overlay source/risk/premium information.

**v0.4 (2025-10-22)** - URA + NHB overlays available in optimiser pipeline
- NHB Historic Sites GeoJSON downloaded (`data/heritage/raw/nhb_historic_sites.geojson`) and merged with URA polygons – 102 features now ship in `backend/app/data/heritage_overlays.geojson`.
- CLI transform now handles GeoJSON datasets (Historic Sites) alongside the URA shapefile, converting SVY21 coordinates to WGS84.
- Developer API surfaces `heritage_context` with overlay metadata so capture/optimiser flows consume risk, notes, and premium information.

**v0.3 (2025-10-22)** - CLI scaffolding + data.gov.sg workflow
- Added heritage ingestion CLI (`python -m scripts.heritage`) with `fetch`, `transform`, `load`, and `pipeline` commands.
- Documented data.gov.sg poll-download flow as the canonical source for URA + NHB datasets (no separate URA Maps key required).
- Stored raw URA conservation shapefile under `data/heritage/raw/ura_conservation/` and normalised output in `data/heritage/processed/`.
- Load step now copies processed GeoJSON into `backend/app/data/heritage_overlays.geojson` with metadata snapshot.
- Added regression test for shapefile resolution helper to protect CLI assumptions.

**v0.2 (2025-10-22)** - Technical review polish
- Added explicit NHB data source links (OneMap, data.gov.sg) with expected columns
- Documented repository structure (`data/heritage/raw|processed|overrides/`)
- Documented optional geospatial helpers (shapely core dependency; pyproj/fiona/geopandas install on demand)
- Clarified geometry simplification strategy (Douglas-Peucker, tolerance 0.00001)
- Added `heritage_premium_pct` to output schema
- Added STRtree spatial indexing for performance optimization
- Added performance testing requirements (<10ms P95 benchmark)
- Documented pytest-regressions fixtures location
- Added rollback retention policy (90 days, last 2 versions)
- Split Week 2 into 2a/2b to unblock parallel development
- Added outstanding questions #4 (URA/NHB overlap handling) and #5 (override storage)

**v0.1 (2025-10-20)** - Initial draft

---

## 1. Data Sources

| Dataset | Owner | Format | Notes |
|---------|-------|--------|-------|
| URA Conservation Areas | Urban Redevelopment Authority | Shapefile / GeoJSON | Published on [data.gov.sg](https://data.gov.sg/datasets/d_f105660dd749c0aafa1a858f435603f2/view). Latest download stored at `data/heritage/raw/ura_conservation/ura_conservation.zip`. |
| National Heritage Board Sites | National Heritage Board | CSV / GeoJSON | Historic Sites GeoJSON downloaded via data.gov.sg/OneMap (`data/heritage/raw/nhb_historic_sites.geojson`). |
| National Heritage Board Monuments | National Heritage Board | GeoJSON | National Monuments GeoJSON downloaded via data.gov.sg/OneMap (`data/heritage/raw/MonumentsGEOJSON.geojson`). |
| National Heritage Board Heritage Trails | National Heritage Board | GeoJSON (converted from KML) | KML downloaded from data.gov.sg and converted to GeoJSON (`data/heritage/raw/HeritageTrailsKML.geojson`). |
| Internal Overrides | Product/Heritage team | YAML/JSON | Manual adjustments or overrides (e.g. pilot areas, premium adjustments) to be merged on top of authoritative datasets. **Storage:** `data/heritage/overrides/manual_overrides.yaml` (repo) or S3 bucket `s3://optimal-build-data/heritage/overrides/` (production). |

### Access Requirements
1. Download URA + NHB datasets from data.gov.sg (manual or via CLI) — no credentials required for initial development.
2. Optional: register for data.gov.sg API key (waitlist open, rate limits enforced from Nov 2025) for higher throughput.
3. For address geocoding, sign up for a free OneMap account (token refresh every 3 days) — not required for static overlay ingestion.
4. Decide on refresh cadence (initially weekly; align on SLA with stakeholders).

---

## 2. Pipeline Architecture

```
fetch_raw_data (CLI)
  ├─ downloads URA conservation polygons → data/heritage/raw/ura_conservation.zip
  ├─ downloads NHB site list → data/heritage/raw/nhb_historic_sites.geojson
  ├─ downloads NHB monuments → data/heritage/raw/MonumentsGEOJSON.geojson
  └─ downloads/ingests NHB trails (manual KML conversion) → data/heritage/raw/HeritageTrailsKML.geojson
  └─ fetches override file from repo or S3 → data/heritage/raw/manual_overrides.yaml

transform_boundaries
  ├─ simplifies/validates polygons (using shapely)
  ├─ computes bounding boxes & centroids
  ├─ maps attributes → {name, risk, notes, effective_date, source}
  └─ outputs normalized GeoJSON → data/heritage/processed/heritage_overlays.geojson

load_into_db
  ├─ writes polygons to overlay source tables via `overlay_ingest.py`
  ├─ stores metadata snapshot (checksum, version)
  └─ emits audit events

publish_runtime_assets
  ├─ copies processed GeoJSON into backend/app/data/heritage_overlays.geojson
  ├─ writes publish metadata (`data/heritage/processed/metadata.json`)
  └─ uploads processed GeoJSON to S3 (if required for frontend)
```

**Repository structure:**
```
data/heritage/
├── raw/                    # Raw downloads from URA/NHB APIs
├── processed/              # Normalized GeoJSON outputs
└── overrides/              # Manual override files (YAML/JSON)
```

### Components Delivered / To Build
- ✅ `scripts/heritage/fetch.py`: poll-download helper for data.gov.sg datasets (requests-based).
- ✅ `scripts/heritage/transform.py`: shapely-based transformer (handles URA shapefiles + NHB GeoJSON, converts SVY21 → WGS84, computes bbox/centroid, risk metadata).
- ✅ `scripts/heritage/load.py`: copies processed GeoJSON into `backend/app/data/` and records publish metadata.
- ✅ `scripts/heritage/__main__.py`: argparse-based CLI (`fetch`, `transform`, `load`, `pipeline`).
- ⏳ Prefect/cron job (future) to run weekly refresh; store latest run metadata in Import records.

### Python Dependencies
Add to your virtual environment when running the CLI locally:
```
shapely>=2.0.0          # Polygon operations, simplification
pyproj>=3.6.0           # Coordinate transformations (optional)
fiona>=1.9.0            # Shapefile I/O (optional, only for shapefile inputs)
geopandas>=0.14.0       # GeoJSON handling (optional convenience layer)
```

---

## 3. Normalized Output Schema

```jsonc
{
  "name": "Telok Ayer Conservation",
  "risk": "high",                 // values: high | medium | low | info
  "source": "URA",
  "boundary": {                     // GeoJSON Polygon or MultiPolygon
    "type": "Polygon",
    "coordinates": [ ... ]
  },
  "bbox": [min_lon, min_lat, max_lon, max_lat],
  "centroid": [lon, lat],
  "notes": [
    "Facade retention mandatory",
    "Consult URA Conservation Department prior to structural works"
  ],
  "effective_date": "2025-10-01",
  "heritage_premium_pct": 5.0,      // Optional: premium uplift for optimizer (% basis)
  "attributes": {
    "ura_category": "Historic District",
    "planning_area": "Outram"
  }
}
```

**Geometry handling:**
- **Full geometry retention:** Store complete polygon coordinates for accurate point-in-polygon checks
- **Simplification:** Apply Douglas-Peucker algorithm with tolerance `0.00001` (~1m at equator) to reduce vertex count while preserving shape
- **Validation:** Ensure polygons are valid (no self-intersections) using `shapely.is_valid()` before storage

Additional optional fields:
- `manual_override`: boolean, indicates if entry comes from overrides file.
- `nhb_id`: for NHB joined records.
- `simplified_geometry`: Pre-computed simplified version for fast rendering (if needed).

---

## 4. Integration Points

1. **Python service layer**
   - Update `HeritageOverlayService` to load GeoJSON polygons (rather than bounding boxes) and perform point-in-polygon checks using shapely.
   - **Performance optimization:** Use `shapely.STRtree` (R-tree spatial index) to avoid O(n) lookups per query. Build index on service startup from all polygons.
   - Publish helper to return combined risk/notes for a coordinate; fallback to bounding box if polygon check fails (performance).

2. **Developer GPS Capture (`gps_property_logger`)**
   - Replace JSON lookup with service call to `HeritageOverlayService.lookup`. Include `risk`, `notes`, `overlay_name`, `source`, and `heritage_premium_pct` in the response.

3. **Optimiser (`asset_mix.py`)**
   - Accept new overlay metadata (name, risk, premium) to drive heritage adjustments.
   - **Risk mapping alignment:** Use the same `high | medium | low | info` values defined in the optimizer spec (§3.8). Ensure risk classification logic is consistent across ingestion and optimizer.

4. **Persistence / Analytics**
   - Store overlay hits in project metadata for audits (`project_metadata.heritage_overlay`).
   - Log the heritage overlay version used in each optimizer run (tie into §6 versioning).
   - Optionally expose API endpoint `GET /heritage-overlays` for frontend shading (future).

---

## 5. Testing Strategy

| Area | Tests |
|------|-------|
| Fetch | Mock URA/NHB endpoints; verify HTTP failures handled; ensure raw files persisted with checksum. |
| Transform | Unit tests for polygon simplification, risk mapping, override merging. |
| Load | Integration tests creating in-memory DB, ensuring `overlay_ingest` writes records and audit events. |
| Service | Unit tests for point-in-polygon lookup (hit/miss, boundaries, risk overrides). |
| Performance | Benchmark point-in-polygon lookup with STRtree (target: <10ms P95 for 100 overlays). Ensure no latency spikes when scaling to 500+ polygons. |
| Regression | Snapshot tests comparing historical JSON vs. generated fallback using `pytest-regressions`. **Fixtures:** Store sample URA/NHB responses in `tests/fixtures/heritage/` for reproducible testing. |

---

## 6. Operational Considerations

- **Versioning**: store output version (`YYYYMMDD`) in metadata and processed filenames (e.g., `heritage_overlays_20251022.geojson`). Optimizer should log which heritage version was used in each run (stored in project metadata).
- **Refresh cadence**: weekly; manual rerun via CLI pipeline command for urgent updates.
- **Alerting**: emit metrics (`heritage_ingestion.duration_ms`, `heritage_ingestion.records_loaded`, `heritage_ingestion.fetch_failures`, `heritage_ingestion.version_used`). Hook into existing monitoring.
- **Rollback**: keep last 2 versions in S3 (`s3://optimal-build-data/heritage/archive/`). **Retention policy:** 90 days for archived versions. **Rollback process:** Manual via CLI `pipeline --version <YYYYMMDD>` to re-publish a previous snapshot if ingestion fails. **Owner:** Backend Lead + Ops.

---

## 7. Timeline & Owners

| Week | Deliverable | Owner | Dependencies |
|------|-------------|-------|--------------|
| Week 1 | Data access approved, CLI scaffold created (`fetch`, `transform`, `load`) | Backend Lead | **Blocker:** URA API access approval (Product Ops) |
| Week 2a | Point-in-polygon service with STRtree indexing (backend only) | Backend Lead | Week 1 CLI scaffold complete |
| Week 2b | Optimiser integration updated (consuming heritage metadata from service) | Backend Lead | Week 2a service deployed |
| Week 3 | Automated weekly job configured; QA sign-off (heritage + finance) | Ops / Data Engineering | Weeks 1-2 complete |

*Note:* Weeks align with the broader Phase 2B schedule. Week 2 split into 2a (backend service) and 2b (optimizer) to unblock parallel development. API updates don't block ingestion.

---

## 8. Outstanding Questions

1. Do we need to support multiple heritage risk tiers beyond high/medium/low? **[Owner: Heritage Team]**
2. Should optimiser treat NHB monuments differently from URA conservation zones? **[Owner: Finance + Heritage]**
3. Where should processed GeoJSON be stored for frontend consumption (S3 bucket, CDN, etc.)? **[Owner: Platform Ops]**
4. **Do we need to merge URA + NHB overlays into combined polygons when they overlap?** For example, if an NHB monument sits within a URA conservation area, should we union the geometries or keep them as separate overlays with priority rules? **[Owner: Heritage Team]**
5. **Where should heritage premium overrides be stored/uploaded?** Should manual overrides (e.g., pilot area premiums) be committed to the repo (`data/heritage/overrides/`), uploaded to S3, or managed via an admin UI? What's the update workflow? **[Owner: Product + Platform Ops]**

Feedback welcome. Once agreed, we can start implementation following the priority list above.
