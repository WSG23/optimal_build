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

## ROI metrics

The frontend ROI dashboard queries `/api/v1/roi/{project_id}` for automation
insights such as time saved, acceptance rates, and iteration counts. The
underlying heuristics and instrumentation assumptions are documented in
[`docs/roi_metrics.md`](docs/roi_metrics.md).
