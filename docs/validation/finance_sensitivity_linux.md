# Finance Sensitivity Linux Validation Guide

_Last updated: 2025-11-18 – authored by Codex._

## Goal
Verify that the `finance.sensitivity` queue executes successfully on a Linux host (where fork-based workers are stable), captures metrics, and surfaces job status back to the workspace without duplicate enqueues.

## Prerequisites
- Linux workstation or VM with Python 3.11, Redis, and Docker (Docker simplifies running Redis locally)
- Project repo checked out and `.venv` created (`make venv`)
- Backend dependencies installed (`pip install -r backend/requirements.txt`)

## 1. Launch Redis
Either start a native Redis service or run via Docker:

```bash
docker run --rm -p 6379:6379 redis:7.2
```

## 2. Start the API server (RQ backend)
In a shell with the virtual environment activated:

```bash
export SECRET_KEY=dev-secret
export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/optimal_build"
export JOB_QUEUE_BACKEND=rq
export RQ_REDIS_URL=redis://127.0.0.1:6379/0
export API_RATE_LIMIT=60
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES  # harmless on Linux
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The `JOB_QUEUE_BACKEND=rq` flag ensures async jobs leave the request thread; the Redis URL matches the container above.

## 3. Start an RQ worker dedicated to finance jobs
In a second shell:

```bash
source .venv/bin/activate
export SECRET_KEY=dev-secret
export RQ_REDIS_URL=redis://127.0.0.1:6379/0
export PYTHONPATH=/path/to/optimal_build
RQ_CONNECTION_CLASS=rq.connections.RetryConnection \
  .venv/bin/rq worker finance
```

The `finance` queue handles `finance.sensitivity` jobs. Leave this worker running; it will log when jobs start/finish.

## 4. Create a finance scenario via the CLI helper
The helper script issues the feasibility request and downloads the export bundle:

```bash
cd backend
python -m backend.scripts.finance_run_scenario \
  --api-base http://127.0.0.1:8000 \
  --project-id 401 \
  --scenario-name "Linux Async Validation" \
  --owner-email reviewer@example.com \
  --export-path /tmp/linux-finance-export.zip
```

Note the `scenario_id` printed – you’ll use it for reruns.

## 5. Trigger an async sensitivity rerun
From another shell (use `httpie` or `curl`). The payload uses multiple bands to exceed `FINANCE_SENSITIVITY_MAX_SYNC_BANDS` so the worker is exercised.

```bash
http POST http://127.0.0.1:8000/api/v1/finance/scenarios/SCENARIO_ID/sensitivity \
  "X-Role: reviewer" "X-User-Email: reviewer@example.com" \
  sensitivity_bands:='[
    {"parameter": "Rent", "low": "-5", "base": "0", "high": "6"},
    {"parameter": "Interest Rate", "low": "2", "base": "0", "high": "-1"}
  ]'
```

Expected response:
- HTTP 200 with `sensitivity_jobs[0].status == "queued"`
- `results` list already contains a placeholder `sensitivity_analysis` entry with `metadata.bands[0].parameter == "__async__"`

## 6. Observe worker + metrics
- Worker logs should show the task starting and finishing (look for `finance.sensitivity` log lines)
- After completion, poll `GET /api/v1/finance/jobs?scenario_id=SCENARIO_ID` – status should change to `completed`
- Optionally fetch `/metrics` and confirm counters update:
  - `finance_sensitivity_jobs_total{status="queued"}` increments
  - `finance_sensitivity_jobs_total{status="completed"}` increments when the worker finishes

## 7. Verify export bundle contains updated sensitivity results
Re-run the export helper or call `/api/v1/finance/export?scenario_id=SCENARIO_ID` and ensure `sensitivity.json` reflects the async run.

## 8. Negative / dedup test
Repeat step 5 immediately after the first request (same payload). Expected behavior:
- API returns cached job status (`queued`) without enqueuing another task (worker log stays quiet)
- Response includes `sensitivity_jobs` array with a single entry

## 9. Record findings
Add a short note to `docs/all_steps_to_product_completion.md` (Phase 2C section) with:
- Linux distro + kernel
- Redis/worker command used
- Confirmation that metrics + export bundle look correct
- Any issues observed (attach log snippets if needed)

## Troubleshooting
- Job stuck in `queued`: ensure worker process is connected to the same Redis DB and queue name (`finance`). Use `rq info` to inspect.
- Metrics missing: confirm `/metrics` endpoint is enabled (default when running `uvicorn app.main:app`).
- Validation on macOS is unsupported for forked workers; always perform this test on Linux or run Celery with prefork on Linux.
