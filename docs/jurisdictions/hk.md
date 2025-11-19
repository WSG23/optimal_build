# Hong Kong Jurisdiction Dossier

Last updated: 2025-11-18  
Owner: Codex (implementation), Claude (validation), PM (data/API keys)

---

## 1. Summary

- **Jurisdiction code:** `hk`
- **Currency:** HKD  
- **Default units:** Square feet (sqft)
- **Primary data portals:**
  - [DATA.GOV.HK](https://data.gov.hk/en/) – parcel polygons, planning areas, heritage lists
  - [Lands Department GeoSpatial Data Store](https://geodata.gov.hk/) – zoning shapefiles (requires API token)
  - [Rating and Valuation Department](https://www.rvd.gov.hk/) – rent/vacancy statistics (PDF/CSV downloads)

---

## 2. Environment Variables

Add the following to `.env` (or your secrets manager):

```
# DATA.GOV.HK application token
HK_DATA_GOV_API_KEY=todo_replace_with_real_key

# Optional: Lands Department geospatial token (if separate)
HK_GEOSPATIAL_TOKEN=todo_replace_with_real_token
```

These values are read by `backend/scripts/ingest_hk_zones.py`.

---

## 3. Datasets & Endpoints

| Dataset | Source | Format | Notes |
|--------|--------|--------|-------|
| Zoning polygons | Lands Department (`https://api.data.gov.hk/v2/filter`) | GeoJSON | Provide `$format=geojson` and include API key header `key: HK_DATA_GOV_API_KEY` |
| Historical parcels | DATA.GOV.HK cadastral dataset | GeoJSON/CSV | Used to generate preview footprints when developer capture lacks precise outlines |
| Heritage list | Antiquities and Monuments Office CSV | CSV | For overlay service (heritage warnings) |
| Rent & vacancy | Rating and Valuation Department | CSV/PDF | Populate `data/hk_market_assumptions.yaml` (see Section 6) |

Working query example (zoning polygons):

```
curl -X POST "https://api.data.gov.hk/v2/filter" \
  -H "Content-Type: application/json" \
  -H "key: ${HK_DATA_GOV_API_KEY}" \
  -d '{
    "resource": "https://www.landsd.gov.hk/datagovhk/zoning_latest.geojson",
    "section": 1,
    "format": "json"
  }'
```

*Endpoints and parameters may change; confirm once credentials arrive.*

---

## 4. Implementation Tasks

### Ingestion
- [ ] Finalize dataset URLs for zoning + parcels (see table above).
- [ ] Flesh out `backend/scripts/ingest_hk_zones.py` to:
  - Fetch GeoJSON (streaming to disk)
  - Reproject into WGS84 (use `shapely` / `pyproj` if dataset not already EPSG:4326)
  - Persist polygons to the `zoning_overlays` table with `jurisdiction_code="hk"`
  - Register the parser in `backend/app/services/overlay_ingest.py`
- [ ] Create pytest fixture `hk_property()` with sample parcel geometry for regression tests.

### Finance/Preview Integration
- [ ] Load `data/hk_market_assumptions.yaml` via market-data service.
- [ ] Ensure finance engine uses HKD currency + sqft conversions.
- [ ] Update preview generator to respect Hong Kong-specific `geometry_detail_level` defaults (no change expected, but document).

### Validation
- [ ] Add CLI recipe to `docs/validation/preview_async_linux.md` for `jurisdiction=hk`.
- [ ] Manual QA script: capture property in Kowloon, generate feasibility + finance export, attach screenshots/results to `docs/archive/expansion/hk_validation_<date>.md`.

---

## 5. Testing Plan

1. **Unit tests**
   - `tests/services/test_overlay_ingest.py::test_ingest_hk_zones`
   - `tests/services/test_market_data.py::test_load_hk_assumptions`
2. **Integration tests**
   - `tests/test_api/test_developers_site_acquisition.py::test_log_property_hk`
   - `tests/test_api/test_finance_asset_breakdown.py::test_finance_export_uses_hkd`
3. **Manual**
   - Follow the workflow documented above once sample data is available.

---

## 6. Market Assumptions Snapshot

The file `data/hk_market_assumptions.yaml` contains the canonical assumptions for finance calculations. Values are placeholders until we ingest real statistics (replace with actual data once confirmed):

```yaml
hk_market_data:
  currency: "HKD"
  units: "sqft"
  rent_psf_month:
    office: 11.5
    retail: 18.7
    residential: 9.2
    industrial: 5.8
  opex_assumptions:
    property_tax_percent: 5.0
    management_fee_percent: 2.5
    utilities_percent: 1.8
    insurance_percent: 0.4
    maintenance_percent: 2.0
  vacancy_rates:
    office: 0.10
    retail: 0.07
    residential: 0.05
    industrial: 0.08
  finance_assumptions:
    construction_loan_rate: 4.2
    equity_debt_split: [30, 70]
    exit_cap_rate: 4.5
```

---

## 7. Open Questions / TODOs

- [ ] Confirm whether Lands Department API permits bulk downloads without paid account.
- [ ] Decide on geocoding source (OneMap HK vs Google Maps fallback).
- [ ] Validate rent/opex numbers with latest CBRE quarterly report.
- [ ] Determine if Hong Kong heritage overlays require separate ingestion workflow.

Document findings in this file as they arrive.

---

**Ready for Implementation:** As soon as API keys and dataset URLs are confirmed, Codex can complete the ingestion script and add regression tests following this guide.
