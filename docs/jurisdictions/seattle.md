# Seattle / King County Jurisdiction Dossier

Last updated: 2025-11-22
Owner: Codex (implementation scaffolding), PM (API tokens/dataset IDs)

---

## 1. Summary

- **Jurisdiction code:** `sea`
- **Currency:** USD
- **Default units:** Square feet internally; convert to sqm in finance as needed
- **Covered area:** City of Seattle / King County
- **Primary data portals:** Seattle Open Data (SODA), King County GIS Open Data

---

## 2. Environment Variables

```
# Optional SODA app token for Seattle/King County open data
SEATTLE_SODA_APP_TOKEN=public
```

Tokens are optional for public calls but increase rate limits.

---

## 3. Datasets & Endpoints (placeholders to confirm)

| Dataset | Portal | Notes |
|---------|--------|-------|
| Parcels | King County GIS Open Data (ArcGIS) | Item ID `c7a17b7ad3ec44b7ae64796dca691d72`, layer 1722 (“Parcels for King County with Address with Property Information”), EPSG:2926. Download GeoJSON and save to `data/seattle/parcels.geojson`. |
| Zoning | Seattle GeoData (ArcGIS) | Item ID `dd29065b5d01420e9686570c2b77502b`, layer 0 (“Current Land Use Zoning Detail”), EPSG:2926. Download GeoJSON to `data/seattle/zoning.geojson`. |
| Zoning (alt) | Seattle Open Data SODA | Dataset `n8h3-r7is` (GeoJSON via SODA); EPSG:4326 typically. |
| Finance defaults | King County Assessor | Use for rent/opex/valuation benchmarks (future step). |

**SODA GeoJSON pattern:** `https://data.seattle.gov/resource/<DATASET_ID>.geojson?$limit=...&$offset=...`

---

## 4. Parcel Ingestion Workflow

Script: `backend/scripts/ingest_seattle_parcels.py`

Local GeoJSON (recommended for bulk):
```bash
export SECRET_KEY=dev-secret
export DATABASE_URL="postgresql+asyncpg://postgres:password@localhost:5432/building_compliance"
export PYTHONPATH=/Users/wakaekihara/GitHub/optimal_build

.venv/bin/python -m backend.scripts.ingest_seattle_parcels \
  --input-path data/seattle/parcels.geojson \
  --batch-size 1000 \
  --source-epsg 2926 \
  --persist
```

Direct SODA fetch (smaller pulls / testing):
```bash
export SEATTLE_SODA_APP_TOKEN=public
.venv/bin/python -m backend.scripts.ingest_seattle_parcels \
  --dataset-id <PARCEL_DATASET_ID> \
  --app-token "$SEATTLE_SODA_APP_TOKEN" \
  --limit 5000 \
  --source-epsg 2926 \
  --persist
```

Key behaviours:
- Streams GeoJSON to avoid memory spikes.
- Reprojects from EPSG:2926 (StatePlane) if needed; set `--source-epsg 4326` when exports are already WGS84.
- Persists to `ref_parcels` with `jurisdiction="SEA"`.

---

## 5. Zoning Ingestion Workflow

Script: `backend/scripts/ingest_seattle_zones.py`

Local GeoJSON:
```bash
.venv/bin/python -m backend.scripts.ingest_seattle_zones \
  --input-path data/seattle/zoning.geojson \
  --layer-name seattle_zoning \
  --source-epsg 2926 \
  --persist
```

SODA fetch:
```bash
.venv/bin/python -m backend.scripts.ingest_seattle_zones \
  --dataset-id <ZONING_DATASET_ID> \
  --app-token "$SEATTLE_SODA_APP_TOKEN" \
  --layer-name seattle_zoning \
  --persist
```

Notes:
- Auto-detects CRS and reprojects to WGS84 if needed.
- Persists zone code + attributes into `ref_zoning_layers` under `jurisdiction="SEA"`.

---

## 6. Handlers / Automation

- Overlay ingest registry: `jurisdiction="sea"` routes to `backend.scripts.ingest_seattle_zones:ingest_seattle_zones`.
- Parcel ingest registry: `jurisdiction="sea"` routes to `backend.scripts.ingest_seattle_parcels:ingest_parcels`.

---

## 7. Completed Setup ✅

- ✅ **Dataset IDs confirmed:**
  - Parcels: King County ArcGIS `c7a17b7ad3ec44b7ae64796dca691d72_1722`
  - Zoning: Seattle GeoData ArcGIS `dd29065b5d01420e9686570c2b77502b_0` (alt: SODA `n8h3-r7is`)

- ✅ **CRS defaults set:**
  - Both parcels and zoning use EPSG:2926 (NAD83(HARN) / Washington North - US Survey Feet)
  - Scripts auto-transform to WGS84 (EPSG:4326) for database storage

- ✅ **Demo property seeded:**
  - Space Needle (PIN: 1985200495)
  - Address: 400 Broad Street, Seattle, WA 98109
  - Property UUID: `aa3f0dbe-0b74-4f65-9f5e-0fbfa6c7f3b4`
  - Verify: `SELECT * FROM properties WHERE jurisdiction_code = 'SEA';`

- ✅ **Market assumptions added to `jurisdictions.json`:**
  - Office rent: $3.00/sqft/month
  - Retail rent: $2.75/sqft/month
  - Residential rent: $2.86/sqft/month
  - Industrial rent: $1.21/sqft/month
  - Operating expenses: property tax 0.85%, management 3.0%, utilities 2.0%, insurance 0.5%, maintenance 2.5%
  - Vacancy rates: office 33.6%, retail 3.8%, residential 5.0%, industrial 4.0%
  - Exit cap rate: 5.05%

## 8. Future Enhancements

- [ ] Schedule quarterly data refresh for parcel and zoning updates
- [ ] Capture a representative Seattle development property after each data refresh to validate preview/finance alignment
- [ ] Add neighborhood-specific market assumptions (Downtown vs. Capitol Hill vs. Ballard)
- [ ] Integrate Seattle building permit data for construction activity tracking
