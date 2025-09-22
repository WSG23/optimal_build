# Optimal Build

## Frontend environment configuration

The frontend reads API locations from the `VITE_API_BASE_URL` variable that is loaded by Vite at build time. The value is resolved with `new URL(path, base)` so that links behave correctly whether the backend is exposed on the same origin, via a sub-path proxy, or through a separate host. For local development we provide a default of `/` in `frontend/.env` (copy `frontend/.env.example`) so the app talks to whichever host serves the frontend.

### Configuring `VITE_API_BASE_URL`

| Environment | Suggested value | Notes |
|-------------|-----------------|-------|
| Local development with Vite proxy or reverse proxy | `/` | Default value. Requests are routed relative to the web origin, allowing a dev proxy (e.g., Vite's `server.proxy`) or an ingress controller to forward traffic to the API service. |
| Local development without a proxy | `http://localhost:8000/` | Point directly at the backend when running it on a different host/port than the frontend dev server. |
| Staging/production behind a proxy prefix | `/api/` (or another sub-path) | Useful when a load balancer terminates TLS and exposes the API under a path prefix on the same domain as the UI. |
| Staging/production on a dedicated API domain | `https://api.example.com/` | Use a fully-qualified URL when the API is hosted on a different domain. |

Set the variable in the environment that builds the frontend (e.g., `frontend/.env`, `.env.production`, Docker/CI environment variables, or hosting provider settings). Because the variable name starts with `VITE_`, it is inlined at build time and no additional runtime configuration is required.

## Backend environment configuration

Copy `.env.example` to `.env` at the repository root to configure the FastAPI backend and background workers. The template now includes the following groups of variables:

| Variable | Default | Purpose |
|----------|---------|---------|
| `ODA_LICENSE_KEY` | _(empty)_ | Inject the proprietary license string issued by the Open Design Alliance (or other CAD SDK vendor). Provide the real value via your local `.env`, container secrets, or CI/CD secret store — never commit the key. |
| `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` | Derived from `REDIS_URL` (defaults to `redis://localhost:6379/0` and `/1`) | Connection strings used by Celery for task dispatch and result storage. Override if your Redis deployment lives elsewhere or you use a different broker. |
| `RQ_REDIS_URL` | Derived from `REDIS_URL` (defaults to `redis://localhost:6379/2`) | Redis connection used by any RQ workers. |
| `OVERLAY_QUEUE_LOW`, `OVERLAY_QUEUE_DEFAULT`, `OVERLAY_QUEUE_HIGH` | `overlay:low`, `overlay:default`, `overlay:high` | Named queues for overlay-processing jobs so workers can prioritise workloads. |
| `IMPORTS_BUCKET_NAME`, `EXPORTS_BUCKET_NAME` | `cad-imports`, `cad-exports` | Object-storage buckets used for CAD uploads and generated exports. |

These values are consumed by `backend/app/core/config.py`. When only `REDIS_URL` is provided the backend reuses the same host and credentials for Celery and RQ while automatically splitting work across database indices `0`, `1`, and `2`. In staging or production deployments, configure the same variables through your orchestrator (Docker Compose, Kubernetes, managed task queue, etc.) so that the backend API, Celery workers, and any RQ workers share consistent queue and storage names.

## Database bootstrapping

The development Docker Compose files now start PostgreSQL, Redis, and MinIO without mounting an initialization SQL file. Instead, the schema is created through Alembic migrations that live under `backend/migrations/` and are configured via `backend/alembic.ini`.

1. Run `make dev-start` to launch the supporting containers. The command no longer fails due to a missing `scripts/init-db.sql` file.
2. Execute `make init-db` from the repository root after the containers are healthy. This target calls `alembic -c alembic.ini upgrade head` inside the `backend/` directory so that the full schema is created (or upgraded) against the running PostgreSQL instance.
3. Optionally invoke `make seed-data` to load any sample fixtures once the schema exists.

Alembic migrations are idempotent: the new base revision creates all SQLAlchemy models if the database is empty, and later revisions check for existing columns before attempting to add them. This allows developers to reset their environment with `make reset` without juggling manual SQL scripts.

## Running the AEC sample flow

The repository ships with a lightweight CLI (`backend/scripts/aec_flow.py`) and Make
targets that exercise the import, overlay, and export pipeline end-to-end using the
sample fixtures checked into the test suite. Each command boots the FastAPI
application in-process, configures an inline job queue, and stores artefacts under
`.devstack/` by default (override with `AEC_RUNTIME_DIR=/custom/path`).

1. `make import-sample` — uploads `tests/samples/sample_floorplan.json` through the
   `/api/v1/import` endpoint, triggers parsing, and seeds an `OverlaySourceGeometry`
   record for `AEC_PROJECT_ID` (defaults to `101`). The command writes a summary to
   `.devstack/import_sample.json` so that subsequent steps can inspect the import ID
   and detection metadata.
2. `make run-overlay` — invokes `/api/v1/overlay/{project_id}/run` via the inline
   queue, materialising overlay suggestions and storing them in
   `.devstack/overlay_run.json` for review. Re-running the command updates existing
   suggestions to reflect any geometry changes.
3. `make export-approved` — approves the highest-severity suggestion (customise the
   reviewer identity with `AEC_DECIDED_BY`/`AEC_APPROVAL_NOTES`) and downloads a CAD
   export using `/api/v1/export/{project_id}`. The artefact lands in
   `.devstack/exports/` alongside a JSON manifest when optional CAD dependencies are
   unavailable. Set `AEC_EXPORT_FORMAT` to switch between `pdf`, `dxf`, `dwg`, or
   `ifc` payloads.
4. `make test-aec` — chains the three commands above before running the dedicated
   backend regression (`pytest tests/test_workflows/test_aec_pipeline.py`) and the
   frontend test suite. CI reuses this target to validate the AEC flow.

Override `AEC_SAMPLE`, `AEC_PROJECT_ID`, and related variables to experiment with
different fixtures or project identifiers. All commands stream human-readable JSON
summaries to stdout so that the flow can be incorporated into local scripts or
monitoring jobs.

## ROI metrics

The frontend ROI dashboard queries `/api/v1/roi/{project_id}` for automation
insights such as time saved, acceptance rates, and iteration counts. The
underlying heuristics and instrumentation assumptions are documented in
[`docs/roi_metrics.md`](docs/roi_metrics.md).
