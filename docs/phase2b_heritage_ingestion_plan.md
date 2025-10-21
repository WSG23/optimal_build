# Phase 2B Heritage Ingestion Plan

## Overview

This document tracks the ingestion of heritage/historic site data to support the heritage constraint integration feature in Phase 2B (Asset-Specific Feasibility).

## Data Sources

### 1. National Heritage Board (NHB) Historic Sites

**Source:** Singapore OneMap API - Historic Sites layer
**Endpoint:** `https://www.onemap.gov.sg/api/public/themesvc/retrieveTheme`
**Layer ID:** `historicsites`

**Fields Available:**
- NAME: Site name
- ADDRESSBLOCKHOUSENUMBER: Address details
- ADDRESSFLOORNUMBER: Floor number
- ADDRESSBUILDINGNAME: Building name
- ADDRESSPOSTALCODE: Postal code
- DESCRIPTION: Description
- HYPERLINK: Reference URL
- PHOTOURL: Photo URL
- Lat/Lng coordinates

**Status:** ⚠️ **BLOCKED - Network Access Required**

### Outstanding Issues

#### Network Access Blocker (2025-10-21)

**Issue:** Cannot download NHB historic sites GeoJSON due to network restrictions in sandbox environment.

**Attempted:**
- Tried to fetch data from OneMap API using curl
- Host resolution failed (network restricted)

**Workaround Required:**
Once network access is available:

1. Download the NHB historic sites data:
   ```bash
   curl 'https://www.onemap.gov.sg/api/public/themesvc/retrieveTheme' \
     -H 'Content-Type: application/json' \
     --data-raw '{"queryName":"historicsites"}' \
     -o data/heritage/raw/nhb_historic_sites.json
   ```

2. Transform to GeoJSON format:
   ```bash
   python -m scripts.transform_nhb_to_geojson \
     data/heritage/raw/nhb_historic_sites.json \
     data/heritage/raw/nhb_historic_sites.geojson
   ```

3. Load into database:
   ```bash
   python -m scripts.load_heritage_data \
     --source nhb \
     --file data/heritage/raw/nhb_historic_sites.geojson
   ```

**Expected Output:**
- Raw data: `data/heritage/raw/nhb_historic_sites.json`
- GeoJSON: `data/heritage/raw/nhb_historic_sites.geojson`
- Database: `heritage_sites` table populated with ~150-200 historic sites

**Dependencies:**
- Database schema: `heritage_sites` table (already exists)
- Transform script: `scripts/transform_nhb_to_geojson.py` (needs creation)
- Load script: `scripts/load_heritage_data.py` (needs creation)

## Integration with Phase 2B Features

Once heritage data is loaded, it will be integrated into:

1. **Asset-Specific Feasibility** - Heritage constraints will affect development scenarios
2. **Multi-use Development Optimizer** - Heritage sites will limit certain use types
3. **Space Efficiency Calculator** - Heritage preservation requirements will adjust NIA calculations
4. **Program Modeling** - Special heritage scenario will be available

## Next Steps

1. ⏳ **Waiting:** Network access to download NHB data from OneMap API
2. ⏳ **Todo:** Create transform script to convert OneMap JSON to GeoJSON
3. ⏳ **Todo:** Create load script to import heritage sites into database
4. ⏳ **Todo:** Wire heritage data into optimizer/service logic
5. ⏳ **Todo:** Add heritage overlay to developer UI
6. ⏳ **Todo:** Add heritage scenario to feasibility calculator

## Additional Data Sources (Future)

### Urban Redevelopment Authority (URA) Conservation Areas
- Source: URA Master Plan data
- Status: Not yet investigated

### Singapore Tourism Board (STB) Gazetted Buildings
- Source: STB API (if available)
- Status: Not yet investigated

## References

- Feature Delivery Plan: `docs/feature_delivery_plan_v2.md` (Phase 2B)
- FEATURES.md: Lines 98-108 (Phase 2B requirements)
- Database Schema: `backend/alembic/versions/*heritage*.py`
