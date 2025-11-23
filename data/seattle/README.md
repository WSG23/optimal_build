# Seattle Parcel and Zoning Data Download Instructions

This directory stores Seattle/King County cadastral parcel and zoning data for ingestion into the `ref_parcels` and `ref_zoning_layers` tables.

## Quick Start

### Option 1: ArcGIS Bulk Download (Recommended - No API Token Required)

**Parcels (King County):**
1. Visit https://gis-kingcounty.opendata.arcgis.com/datasets/c7a17b7ad3ec44b7ae64796dca691d72_1722
2. Click "Download" → Select "GeoJSON"
3. Save as `data/seattle/parcels.geojson`

**Zoning (Seattle City):**
1. Visit https://data-seattlecitygis.opendata.arcgis.com/datasets/dd29065b5d01420e9686570c2b77502b_0
2. Click "Download" → Select "GeoJSON"
3. Save as `data/seattle/zoning.geojson`

### Option 2: SODA API (Programmatic - Requires Token for High Volume)

**Step 1: Obtain SODA App Token (Optional)**
1. Visit https://data.seattle.gov/profile/app_tokens
2. Register for an app token
3. Export: `export SEATTLE_SODA_APP_TOKEN="your_token_here"`

**Step 2: Fetch via API**
The ingestion scripts can fetch directly from SODA APIs using dataset IDs.

## Running Ingestion

### Parcels (King County)

```bash
# From repository root
export PYTHONPATH=/Users/wakaekihara/GitHub/optimal_build
export DATABASE_URL="postgresql+asyncpg://postgres:password@localhost:5432/building_compliance"
export SECRET_KEY=dev-secret

# Option A: From local GeoJSON file
.venv/bin/python -m backend.scripts.ingest_seattle_parcels \
  --source-epsg 2926 \
  --input-path data/seattle/parcels.geojson \
  --batch-size 1000

# Option B: Fetch from ArcGIS REST API (requires dataset configured in script)
.venv/bin/python -m backend.scripts.ingest_seattle_parcels \
  --source-epsg 2926 \
  --batch-size 1000
```

### Zoning (Seattle City)

```bash
# Option A: From local GeoJSON file
.venv/bin/python -m backend.scripts.ingest_seattle_zones \
  --source-epsg 2926 \
  --input-path data/seattle/zoning.geojson \
  --layer-name seattle_zoning

# Option B: Fetch from SODA API
.venv/bin/python -m backend.scripts.ingest_seattle_zones \
  --soda-dataset-id n8h3-r7is \
  --layer-name seattle_zoning
```

## Dataset Details

**Parcels:**
- **Format:** GeoJSON (FeatureCollection)
- **Source CRS:** EPSG:2926 (NAD83(HARN) / Washington North - US Survey Feet)
- **Target CRS:** EPSG:4326 (WGS84 - GPS coordinates, automatically converted)
- **Parcel Identifiers:** PIN, PARCEL_NUM, parcel_id, parcelnumber
- **Dataset ID:** `c7a17b7ad3ec44b7ae64796dca691d72_1722`
- **Source:** King County GIS Open Data

**Zoning:**
- **Format:** GeoJSON (FeatureCollection)
- **Source CRS:** EPSG:2926 (NAD83(HARN) / Washington North - US Survey Feet)
- **Target CRS:** EPSG:4326 (WGS84 - GPS coordinates, automatically converted)
- **Zone Fields:** zone, zoning, zoning_symbol, ZONE_CLASS
- **Dataset ID:** `dd29065b5d01420e9686570c2b77502b_0` (ArcGIS) or `n8h3-r7is` (SODA)
- **Source:** Seattle GeoData

## Expected Files

```
data/seattle/
├── README.md (this file)
├── parcels.geojson (DOWNLOAD THIS - King County parcels, ~500MB)
└── zoning.geojson (DOWNLOAD THIS - Seattle zoning, ~50MB)
```

## Verifying Ingestion

### Parcels

```bash
# Check parcel count
psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM ref_parcels WHERE jurisdiction = 'SEA';"

# Sample parcels
psql "$DATABASE_URL" -c "
  SELECT parcel_ref, area_m2, source
  FROM ref_parcels
  WHERE jurisdiction = 'SEA'
  ORDER BY random()
  LIMIT 5;
"
```

### Zoning

```bash
# Check zone count
psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM ref_zoning_layers WHERE layer_name = 'seattle_zoning';"

# Sample zones
psql "$DATABASE_URL" -c "
  SELECT zone_code, zone_name, area_m2
  FROM ref_zoning_layers
  WHERE layer_name = 'seattle_zoning'
  ORDER BY random()
  LIMIT 5;
"
```

## Troubleshooting

**"Missing SODA app token"**
- Token is optional for low-volume access
- Use bulk download (Option 1) if API limits are hit
- Register for token at https://data.seattle.gov/profile/app_tokens

**"File not found" during ingestion**
- Ensure files are named exactly `parcels.geojson` and `zoning.geojson`
- Ensure they're in `data/seattle/` directory
- Use `--input-path` flag if files are saved elsewhere

**"Coordinate transformation error"**
- Verify `--source-epsg 2926` flag is set (Washington State Plane North)
- Both parcels and zoning use EPSG:2926 by default

**"SODA API rate limit exceeded"**
- Use bulk download instead (Option 1)
- Or register for SODA app token for higher limits (10,000 → 100,000 requests/day)

## Demo Property

A Seattle demo property (Space Needle) has been seeded for testing:
- **Address:** 400 Broad Street, Seattle, WA 98109
- **Parcel ID:** 1985200495 (King County PIN)
- **Coordinates:** 47.6205054, -122.3493129
- **Property UUID:** aa3f0dbe-0b74-4f65-9f5e-0fbfa6c7f3b4

Verify it exists:
```bash
psql "$DATABASE_URL" -c "SELECT id, name, jurisdiction_code FROM properties WHERE jurisdiction_code = 'SEA';"
```

## Need Help?

See complete documentation: [docs/jurisdictions/seattle.md](../../docs/jurisdictions/seattle.md)
