# Singapore Zoning Data

This folder stores Singapore zoning datasets and is gitignored except for this README.

## URA Master Plan 2019 Land Use layer

- Source: data.gov.sg dataset `d_90d86daa5bfaa371668b84fa5f01424f`
- Dataset page: https://data.gov.sg/dataset/master-plan-2019-land-use-layer
- CRS: EPSG:4326 / CRS84 GeoJSON
- Save as: `data/sg/zoning/master_plan_2019_land_use.geojson`
- Ingest from download:

```bash
PYTHONPATH=$REPO_ROOT .venv/bin/python -m backend.scripts.ingest_sg_zones \
  --download \
  --persist
```

- Ingest from a local file:

```bash
PYTHONPATH=$REPO_ROOT .venv/bin/python -m backend.scripts.ingest_sg_zones \
  --input-path data/sg/zoning/master_plan_2019_land_use.geojson \
  --persist
```

## URA Data Service live smoke

Capture uses imported zoning polygons for zoning/envelope lookup. URA Data Service is used for adjacent live property signals such as approved residential use, private residential transactions, residential pipeline, and rentals.

Add the key to local or deployment secrets only:

```bash
URA_ACCESS_KEY=...
```

Run the smoke check from the repo root:

```bash
.venv/bin/python backend/scripts/smoke_ura_data_service.py
```

Useful stricter variants:

```bash
.venv/bin/python backend/scripts/smoke_ura_data_service.py --require-live
.venv/bin/python backend/scripts/smoke_ura_data_service.py --require-live --require-all
.venv/bin/python backend/scripts/smoke_ura_data_service.py --district D08
```

Without `URA_ACCESS_KEY`, the smoke command reports `status: skipped`. With a key, token failure exits non-zero. With `--require-all`, any live capability that returns no data exits non-zero.

## SLA / OneMap Land Lot Boundary parcels

Capture uses imported parcel boundaries to resolve site area. This is the source
path for today's planning-envelope GFA:

```text
captured point -> ref_parcels containing parcel -> parcel area x URA plot ratio
```

Source: data.gov.sg dataset `d_e7395d743076a2bcc487b0d12b9bf33b`
("SLA Cadastral Land Parcel").

Download the latest SLA Cadastral Land Parcel GeoJSON export and save it as:

```text
data/sg/parcels/land_lot_boundary.geojson
```

Then ingest it from the repo root:

```bash
PYTHONPATH=$REPO_ROOT .venv/bin/python -m backend.scripts.ingest_sg_parcels --download
```

The data.gov.sg GeoJSON is WGS84. The loader stores WGS84 parcel geometry in
`ref_parcels`. If you use a legacy SVY21 export, run with `--source-epsg 3414`.

## URA Master Plan 2019 Building layer

Capture uses imported building footprints to detect whether the parcel appears
vacant or developed before current GFA evidence is available:

```text
captured point -> containing parcel -> intersecting building footprints
```

Source: data.gov.sg dataset `d_e8e3249d4433845bdd8034ae44329d9e`
("Master Plan 2019 Building layer").

Download and save as:

```text
data/sg/buildings/master_plan_2019_building.geojson
```

Then ingest it from the repo root:

```bash
PYTHONPATH=$REPO_ROOT .venv/bin/python -m backend.scripts.ingest_sg_building_footprints --download
```

## Production Capture Bootstrap

Run the Singapore Capture bootstrap to load official zoning, parcel, and
building-footprint source layers and print readiness:

```bash
PYTHONPATH=$REPO_ROOT .venv/bin/python -m backend.scripts.bootstrap_sg_capture_data --download
```

The readiness endpoint used by deployment checks is:

```text
GET /api/v1/data-readiness/capture?jurisdiction=SG
```
