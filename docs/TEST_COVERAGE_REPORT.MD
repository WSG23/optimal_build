# Test Coverage Regression Review

## Artifact history
| Commit | Timestamp (UTC) | Combined line+branch coverage | Covered lines | Covered branches |
| --- | --- | --- | --- | --- |
| `b9df1ac4366e184e678a658eccddcba4a65e7a80` | 2025-10-30T19:18:02.891395 | 100.00% | 0 | n/a |
| `14a4fe29d96810b3d2fe42da901bf8722461dd27` | 2025-10-30T21:17:44.276875 | 29.90% | 5,412 | 481 / 4,084 |
| `684b3d326f4c313fde1386a03cb7665a91436688` | 2025-10-30T21:19:13.948891 | 22.31% | 4,374 | 24 / 4,084 |

> **Note:** There is no repository artifact showing 62 % coverage. The tracked `coverage.json` jumps directly from an empty baseline (100 % because zero statements were measured) to 29.90 % and then to 22.31 % once real data was captured.

## Where the regression shows up
The regression between commits `14a4fe29d96810b3d2fe42da901bf8722461dd27` (29.90 %) and `684b3d326f4c313fde1386a03cb7665a91436688` (22.31 %) is concentrated in high-level backend flows. Representative drops include:

- `backend/app/core/overlay/merge.py` – 93.22 % → 13.56 %
- `backend/app/core/geometry/serializer.py` – 100 % → 30.19 %
- `backend/app/services/reference_parsers.py` – 87.58 % → 20.50 %
- `backend/app/flows/ingestion.py` – 94.29 % → 31.43 %
- `backend/app/services/finance/calculator.py` – 66.45 % → 19.96 %

In total the suite now exercises 1,038 fewer lines and 457 fewer branches than it did in the prior snapshot.

## Why coverage fell
- **Backend integration tests are skipped.** The project-level `pytest.ini` excludes the entire `backend/` tree from discovery (`norecursedirs = backend`). As a result, 116 Python tests under `backend/tests/**` never run unless you invoke them manually.
- **Only unit-level suites are represented in `coverage.json`.** The latest artifact only sees activity from `tests/` and `unit_tests/`, which focus on lower-level helpers. End-to-end flows that previously drove the overlay, ingestion, reference, and finance services are no longer executed, so their branches register as uncovered.
- **Branch coverage is the dominant regressor.** Branch hits plummeted from 481 to 24 even though the total number of instrumented branches stayed constant (4,084). Because coverage.py averages line and branch data when `branch = True`, this branch shortfall alone costs roughly 7 percentage points.

## How to regain the lost coverage
1. **Re-enable backend suites in CI.** Either drop `backend` from `norecursedirs` or run a second `pytest` invocation rooted at `backend/tests`. Merge its `.coverage` data (`coverage combine`) before exporting `coverage.json`.
2. **Fail fast when integration suites are skipped.** Add a `pytest` assertion (or CI check) that warns when zero tests execute under `backend/tests/**` so regressions are caught immediately.
3. **Consider publishing separate artifacts.** If you need to report backend-only, frontend-only, or combined metrics, store each artifact explicitly instead of overwriting `coverage.json` with a partial run.

These steps should restore the missing integration coverage and push the combined metric back toward the pre-regression level.
