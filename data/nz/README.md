# New Zealand Geospatial Data

This folder stores NZ parcels/zoning datasets and is gitignored (except this README).

## Parcels
- Source: LINZ Data Service WFS `layer-50804` (NZ Primary Parcels)
- Download: Use WFS GeoJSON export (filtered by `land_district`) or bulk download
- Save as: `data/nz/parcels.geojson` (or city-specific files)
- CRS: EPSG:2193 (NZGD2000 / NZTM); set `--source-epsg 2193`
- Ingest: `PYTHONPATH=$REPO_ROOT .venv/bin/python -m backend.scripts.ingest_nz_parcels --city auckland --input-path data/nz/parcels.geojson --source-epsg 2193 --persist`

## Zoning
- Source: LINZ WFS `layer-50780` (District Plan Zones) or city zoning feeds
- Save as: `data/nz/zoning.geojson`
- CRS: Typically EPSG:2193; use `--source-epsg 2193`
- Ingest: `PYTHONPATH=$REPO_ROOT .venv/bin/python -m backend.scripts.ingest_nz_zones --input-path data/nz/zoning.geojson --layer-name district_plan_zones --source-epsg 2193 --persist`

## Notes
- Do not commit datasets; keep fixtures minimal under `backend/tests/fixtures/` if needed.
