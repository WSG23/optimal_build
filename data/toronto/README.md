# Toronto Geospatial Data

This folder stores Toronto parcels/zoning datasets and is gitignored (except this README).

## Parcels (Property Boundaries)

- **Source:** City of Toronto Open Data - Property Boundaries
- **Dataset ID:** `1acaa8b0-f235-4df6-8305-02025ccdeb07`
- **Official Page:** https://open.toronto.ca/dataset/property-boundaries/
- **Download (GeoJSON):** https://ckan0.cf.opendata.inter.prod-toronto.ca/dataset/1acaa8b0-f235-4df6-8305-02025ccdeb07/resource/4d4943a6-98ec-4442-9ced-f600f5bc8d27/download/property-boundaries-4326.geojson
- **Save as:** `data/toronto/parcels.geojson`
- **CRS:** EPSG:4326 (WGS84) - no reprojection needed!
- **Last Updated:** November 22, 2025
- **Ingest:** `PYTHONPATH=$REPO_ROOT .venv/bin/python -m backend.scripts.ingest_toronto_parcels --input-path data/toronto/parcels.geojson --source-epsg 4326 --persist`

### Alternative: ArcGIS REST API (paginated)
- **API Endpoint:** https://gis.toronto.ca/arcgis/rest/services/cot_geospatial27/FeatureServer/36
- **Max Records per Query:** 2,000
- **Key Fields:** PARCELID, ADDRESS_NUMBER, LINEAR_NAME_FULL, PLANID, PLAN_TYPE, STATEDAREA

## Zoning

- **Source:** City of Toronto Open Data - Zoning By-law 569-2013
- **Dataset ID:** `34927e44-fc11-4336-a8aa-a0dfb27658b7`
- **Official Page:** https://open.toronto.ca/dataset/zoning-by-law/
- **CRS:** EPSG:4326 (WGS84)
- **Last Updated:** October 15, 2024 (amendments through June 2023)
- **Contact:** zoningproject@toronto.ca

### Zoning Layers

Toronto zoning has multiple overlay layers. Download the ones needed:

#### 1. Zoning Area (Primary - Required)
- **Download (GeoJSON):** https://ckan0.cf.opendata.inter.prod-toronto.ca/dataset/34927e44-fc11-4336-a8aa-a0dfb27658b7/resource/d75fa1ed-cd04-4a0b-bb6d-2b928ffffa6e/download/zoning-area-4326.geojson
- **Save as:** `data/toronto/zoning-area.geojson`
- **Ingest:** `PYTHONPATH=$REPO_ROOT .venv/bin/python -m backend.scripts.ingest_toronto_zones --input-path data/toronto/zoning-area.geojson --layer-name zoning_area --source-epsg 4326 --persist`

#### 2. Zoning Height Overlay (Optional but Recommended)
- **Download (GeoJSON):** https://ckan0.cf.opendata.inter.prod-toronto.ca/dataset/34927e44-fc11-4336-a8aa-a0dfb27658b7/resource/eec27e60-7c2d-4c46-8fa1-b64f441bcc39/download/zoning-height-overlay-4326.geojson
- **Save as:** `data/toronto/zoning-height.geojson`
- **Ingest:** `PYTHONPATH=$REPO_ROOT .venv/bin/python -m backend.scripts.ingest_toronto_zones --input-path data/toronto/zoning-height.geojson --layer-name zoning_height --source-epsg 4326 --persist`

#### 3. Other Overlays (Optional)
- **Policy Area Overlay:** https://ckan0.cf.opendata.inter.prod-toronto.ca/dataset/34927e44-fc11-4336-a8aa-a0dfb27658b7/resource/a4502214-9441-4299-9f50-ecd5a5e4de35/download/zoning-policy-area-overlay-4326.geojson
- **Lot Coverage Overlay:** Available in shapefile format
- **Rooming House Overlay:** Available in shapefile format
- **Parking Zone Overlay:** Available in shapefile format
- **Policy Road Overlay:** Available in shapefile format

### Alternative: ArcGIS REST API
- **MapServer:** https://gis.toronto.ca/arcgis/rest/services/cot_geospatial11/MapServer/3
- **Note:** Read-only access, use for updates only

## Key Differences from Other Jurisdictions

| Feature | Singapore (URA) | Hong Kong (CSDI) | New Zealand (LINZ) | **Toronto** |
|---------|----------------|------------------|-------------------|-------------|
| **CRS** | EPSG:3414 (SVY21) | EPSG:2326 (HK80) | EPSG:2193 (NZGD2000) | **EPSG:4326 (WGS84)** ✅ |
| **API Type** | OGC WFS | OGC WFS | OGC WFS | **ArcGIS REST + CKAN** |
| **Download** | WFS queries | WFS queries | WFS queries | **Direct GeoJSON** |
| **Zoning Layers** | Single | Single | Single | **7+ overlays** |
| **Reprojection** | Required | Required | Required | **Not needed!** ✅ |

## Notes

- **No WFS support:** Unlike Singapore, Hong Kong, and New Zealand, Toronto does NOT provide OGC-compliant WFS. Use direct file downloads or ArcGIS REST API instead.
- **Already in WGS84:** Toronto data is provided in EPSG:4326, so no coordinate transformation is needed for the backend (which uses PostGIS with WGS84).
- **Multiple zoning layers:** Toronto zoning is more complex with 7+ overlay layers. Start with Zoning Area (primary) and Height Overlay.
- **Accuracy disclaimer:** Property boundaries are "suitable for general planning purposes only and is not a substitute for a plan of survey."
- **License:** City of Toronto provides royalty-free, non-exclusive license for use.
- **Do not commit datasets:** Keep this folder gitignored except for this README.

## Contact

- **City of Toronto Open Data:** opendata@toronto.ca
- **City Planning (Zoning):** zoningproject@toronto.ca
- **Portal:** https://open.toronto.ca/

## Alternative: Ontario Provincial Data

For province-wide coverage (includes Toronto):

- **Dataset:** Ontario Parcel (Assessment Parcel)
- **Source:** Ontario GeoHub (Land Information Ontario)
- **URL:** https://geohub.lio.gov.on.ca/datasets/ontario-parcel-assessment-parcel
- **Provider:** MNRF + MPAC + Teranet tripartite agreement
- **CRS:** EPSG:3857 (Web Mercator)
- **Contact:** Geospatial@ontario.ca
