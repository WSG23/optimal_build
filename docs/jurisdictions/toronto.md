# Toronto / Ontario Jurisdiction Dossier

Last updated: 2025-11-22
Owner: Codex (scaffolding), PM (dataset IDs/tokens)

---

## 1. Summary

- **Jurisdiction code:** `tor`
- **Currency:** CAD
- **Default units:** Square meters internally (convert from sqft where needed)
- **Covered area:** City of Toronto (parcels from King County equivalent not applicable)
- **Primary data portals:** Toronto Open Data (CKAN/SODA), City GIS (ArcGIS)

---

## 2. Environment Variables

```
# Optional app token for Toronto Open Data
TORONTO_SODA_APP_TOKEN=public
```

---

## 3. Datasets & Endpoints (placeholders)

| Dataset | Portal | Notes |
|---------|--------|-------|
| Parcels | Toronto Open Data (CKAN/SODA) | Dataset ID TBD; export GeoJSON; CRS likely 4326 or 26917 (UTM 17N) |
| Zoning  | Toronto Open Data (CKAN/SODA) | Dataset ID TBD; GeoJSON; check CRS (4326 vs 26917) |
| Finance defaults | MPAC/market reports | Future step to source rent/opex/vacancy |

---

## 4. Parcel Ingestion Workflow

Script: `backend/scripts/ingest_toronto_parcels.py`

Local GeoJSON:
```bash
export SECRET_KEY=dev-secret
export DATABASE_URL="postgresql+asyncpg://postgres:password@localhost:5432/building_compliance"
export PYTHONPATH=/Users/wakaekihara/GitHub/optimal_build

.venv/bin/python -m backend.scripts.ingest_toronto_parcels \
  --input-path data/toronto/parcels.geojson \
  --batch-size 1000 \
  --source-epsg 4326 \
  --persist
```

SODA/CKAN fetch:
```bash
export TORONTO_SODA_APP_TOKEN=public
.venv/bin/python -m backend.scripts.ingest_toronto_parcels \
  --dataset-id <PARCEL_DATASET_ID> \
  --app-token "$TORONTO_SODA_APP_TOKEN" \
  --limit 5000 \
  --source-epsg 4326 \
  --persist
```

---

## 5. Zoning Ingestion Workflow

Script: `backend/scripts/ingest_toronto_zones.py`

Local GeoJSON:
```bash
.venv/bin/python -m backend.scripts.ingest_toronto_zones \
  --input-path data/toronto/zoning.geojson \
  --layer-name toronto_zoning \
  --source-epsg 4326 \
  --persist
```

SODA/CKAN fetch:
```bash
.venv/bin/python -m backend.scripts.ingest_toronto_zones \
  --dataset-id <ZONING_DATASET_ID> \
  --app-token "$TORONTO_SODA_APP_TOKEN" \
  --layer-name toronto_zoning \
  --persist
```

---

## 6. Automation Hooks

- Zoning registry: `jurisdiction="tor"` → `backend.scripts.ingest_toronto_zones:ingest_toronto_zones`
- Parcel registry: `jurisdiction="tor"` → `backend.scripts.ingest_toronto_parcels:ingest_parcels`

---

## 7. Open TODOs

- Confirm parcel and zoning dataset IDs on the Toronto portal.
- Confirm CRS per dataset (4326 vs 26917) and set defaults accordingly.
- Seed a demo Toronto property for preview/finance validation.
- Add market assumptions (rent/opex) for Toronto in `jurisdictions.json` once benchmarks are sourced.
