# Seattle / King County Geospatial Data

This folder stores parcel and zoning GeoJSON exports and is gitignored.

## Parcels
- Source: King County GIS Open Data (ArcGIS)
- Item/Layer: `c7a17b7ad3ec44b7ae64796dca691d72` layer `1722`
- Download: Export GeoJSON from https://gis-kingcounty.opendata.arcgis.com/datasets/c7a17b7ad3ec44b7ae64796dca691d72_1722
- Save as: `data/seattle/parcels.geojson`
- CRS: EPSG:2926 (StatePlane WA North) in the ArcGIS export; use `--source-epsg 2926`
- Ingest: `PYTHONPATH=$REPO_ROOT .venv/bin/python -m backend.scripts.ingest_seattle_parcels --input-path data/seattle/parcels.geojson --source-epsg 2926 --persist`

## Zoning
- Source: Seattle GeoData (ArcGIS)
- Item/Layer: `dd29065b5d01420e9686570c2b77502b` layer `0` (“Current Land Use Zoning Detail”)
- Download: Export GeoJSON from https://data-seattlecitygis.opendata.arcgis.com/datasets/dd29065b5d01420e9686570c2b77502b_0
- Save as: `data/seattle/zoning.geojson`
- CRS: EPSG:2926 in ArcGIS exports; set `--source-epsg 2926`. SODA alt dataset `n8h3-r7is` is usually WGS84 (4326).
- Ingest: `PYTHONPATH=$REPO_ROOT .venv/bin/python -m backend.scripts.ingest_seattle_zones --input-path data/seattle/zoning.geojson --layer-name seattle_zoning --source-epsg 2926 --persist`

## Notes
- Do not commit these datasets.
- If tests need sample data, create tiny fixtures under `backend/tests/fixtures/`.
