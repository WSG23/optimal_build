# Duplicate Files Report

## How the Scan Was Performed
- Command: `python scripts/find_duplicate_files.py --min-size 1`
- Directories ignored by default: `.git`, `node_modules`, `__pycache__`, build artefact folders, and virtual environments.
- Files smaller than one byte are skipped to avoid noise from intentionally empty markers (for example, namespace `__init__.py` files).

## High-Confidence Duplicates

### Parallel Alembic Trees (Resolved 2025-10-16)
Two Alembic directory trees (`backend/migrations` and `backend/alembic`) previously stored the same migration templates and a shared subset of migration revisions. The duplicated `backend/alembic` tree has now been removed; all canonical migrations live under `backend/migrations`. The table below is retained for historical context.

| Duplicate Content | Paths |
| --- | --- |
| Alembic README stub | `backend/migrations/README`, `backend/alembic/README` |
| `script.py.mako` template | `backend/migrations/script.py.mako`, `backend/alembic/script.py.mako` |
| Revision `20240115_000001_add_reference_tables.py` | `backend/migrations/versions/20240115_000001_add_reference_tables.py`, `backend/alembic/versions/20240115_000001_add_reference_tables.py` |
| Revision `20240626_000002_add_review_notes_to_ref_rules.py` | `backend/migrations/versions/20240626_000002_add_review_notes_to_ref_rules.py`, `backend/alembic/versions/20240626_000002_add_review_notes_to_ref_rules.py` |
| Revision `20240711_000000_initial_schema.py` | `backend/migrations/versions/20240711_000000_initial_schema.py`, `backend/alembic/versions/20240711_000000_initial_schema.py` |
| Revision `20240801_000003_add_finance_tables.py` | `backend/migrations/versions/20240801_000003_add_finance_tables.py`, `backend/alembic/versions/20240801_000003_add_finance_tables.py` |
| Revision `20240816_000004_add_entitlements_tables.py` | `backend/migrations/versions/20240816_000004_add_entitlements_tables.py`, `backend/alembic/versions/20240816_000004_add_entitlements_tables.py` |
| Revision `20240919_000005_enable_postgis_geometry.py` | `backend/migrations/versions/20240919_000005_enable_postgis_geometry.py`, `backend/alembic/versions/20240919_000005_enable_postgis_geometry.py` |

> **Follow-up consideration:** When running Alembic from the backend root, use `backend/alembic.ini` (now pointing at `backend/migrations`) or `python -m backend.migrations`. Additional duplicate Alembic trees should not be reintroduced.

### Sample CAD Fixtures and Upload Mirrors
Multiple copies of identical CAD samples and their derived metadata exist under `.storage/uploads` alongside the canonical fixtures in `samples/` and `backend/tests/samples/`.

| Asset | Canonical Path | Duplicate Upload Mirrors |
| --- | --- | --- |
| `flat_two_bed.dxf` | `samples/dxf/flat_two_bed.dxf` | Multiple entries under `.storage/uploads/*/flat_two_bed.dxf` |
| `flat_two_bed.dxf.layers.json` | *(generated metadata)* | Matching copies under `.storage/uploads/*/flat_two_bed.dxf.layers.json` |
| `sample_floorplan.json` | `backend/tests/samples/sample_floorplan.json` | `.storage/uploads/{28518173-…, 5e33a63b-…, e55bd26a-…}/sample_floorplan.json` |
| `sample_floorplan.json.layers.json` | *(generated metadata)* | `.storage/uploads/{28518173-…, 5e33a63b-…, e55bd26a-…}/sample_floorplan.json.layers.json` |
| `minimal_test.dxf` | `samples/dxf/minimal_test.dxf` | `.storage/uploads/90aa2839-054a-43a1-b1f9-ed0c1783cabd/minimal_test.dxf` |
| `flat_two_bed.dxf` (secondary batch) | *(see above)* | `.storage/uploads/{64127711-…, 97477f8b-…, b0965fd2-…, e750c268-…}/flat_two_bed.dxf` |
| `flat_two_bed.dxf.layers.json` (secondary batch) | *(generated metadata)* | `.storage/uploads/{64127711-…, 68230a48-…, 90aa2839-…, 97477f8b-…, b0965fd2-…, e750c268-…}/*.layers.json` |

> **Follow-up consideration:** if these upload artefacts are kept only for local testing, consider replacing them with symlinks or a fixture generation step to avoid storing repeated binaries.

## Usage Notes
- Run `python scripts/find_duplicate_files.py --json` for a machine-readable summary.
- Append `--ignore-dir <name>` to skip additional directories (for example, CI artefacts) without editing the script.
- Adjust `--min-size` when you need to include empty placeholder files in the scan.
- Pass `--max-groups <n>` to stop scanning after *n* duplicate hashes, or `--fail-on-duplicates` to exit with a non-zero status when duplicates are detected.

## Automation
- `.github/workflows/duplicate-scan.yml` runs automatically on every push to `main`, every Monday at 06:00 UTC, and whenever triggered manually from the Actions tab.
- Each run uploads `duplicate_scan.json` as an artifact and uses `--fail-on-duplicates` to ensure new duplicate hashes break the build.
- The workflow skips `.storage` artefacts so the focus stays on repository-managed files.
- The latest local baseline JSON (generated via `python scripts/find_duplicate_files.py --ignore-dir .storage --json`) lives at `docs/duplicate_scan_baseline.json`.
