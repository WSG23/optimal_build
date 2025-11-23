# Hong Kong Parcel/Zoning Data

This folder holds large CSDI geospatial exports and is gitignored.

## Parcels (Lots)
- Source: CSDI Lot bundle (e.g., `LandParcel_Lot_PUBLIC_20251014.gdb_*_converted.json`)
- Expected file: `data/hk/lots/LandParcel_Lot_PUBLIC_20251014.gdb_LOT_converted.json` (and related lookup tables)
- Ingest: `PYTHONPATH=$REPO_ROOT .venv/bin/python -m backend.scripts.ingest_hk_parcels --input-path data/hk/lots/LandParcel_Lot_PUBLIC_20251014.gdb_LOT_converted.json --batch-size 2000`
- CRS: EPSG:2326 (HK80 Grid) → reprojected to WGS84 by the script

## Zoning
- Source: Planning Dept. WFS (e.g., RA_PLAN_CSDI)
- Output: GeoJSON saved under `data/hk/zoning/` by `ingest_hk_zones.py`
- Ingest: use `backend/scripts/ingest_hk_zones.py` (WFS fetch) and persist to `ref_zoning_layers`

## Notes
- Do not commit these files; they are too large.
- Keep a small fixture under `backend/tests/fixtures/` if needed for offline tests.
