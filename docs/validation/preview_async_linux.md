# Preview Generation Async Validation (Linux)

_Last updated: 2025-11-18 – authored by Codex._

## Goal
Verify that the developer preview pipeline runs successfully with a real Redis-backed RQ worker on **Linux**, capturing queue depth, job durations, and exported artifacts (GLTF/JSON/thumbnail). macOS is unsupported for fork-based preview workers, so this validation must run on a Linux workstation or VM.

## Prerequisites
- Linux host with Docker (for Redis) and Python 3.11
- Repo checked out with `.venv` created (`make venv`)
- Backend dependencies installed (`pip install -r backend/requirements.txt`)
- PostgreSQL populated with at least one developer property (any UUID is acceptable—the preview job stores the ID without additional lookups)

## Quick Runner (Recommended)
Use the helper script to execute the full workflow and capture logs:

```bash
# From repo root on Linux
export PREVIEW_PROPERTY_ID="00000000-0000-0000-0000-000000000001"  # replace with real property UUID
export DATABASE_URL="postgresql+asyncpg://postgres:password@localhost:5432/building_compliance"
bash scripts/validate_preview_async_linux.sh
```

The script creates `preview_validation_results_<timestamp>.md` with Redis/API/worker commands, job IDs, metrics snippets, and metadata download paths.

## Manual Steps

1. **Launch Redis**
   ```bash
   docker run --rm --name preview-redis -p 6379:6379 redis:7.2
   ```
   Confirm with `docker exec preview-redis redis-cli ping`.

2. **Start API (RQ backend)**
   ```bash
   export SECRET_KEY=dev-secret
   export DATABASE_URL="postgresql+asyncpg://postgres:password@localhost:5432/building_compliance"
   export JOB_QUEUE_BACKEND=rq
   export RQ_REDIS_URL=redis://127.0.0.1:6379/0
   export API_RATE_LIMIT=120
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```
   Wait for `http://127.0.0.1:8000/health` to return `{"status":"ok"}`.

3. **Start RQ Worker (preview queue)**
   ```bash
   cd backend
   source ../.venv/bin/activate
   export RQ_REDIS_URL=redis://127.0.0.1:6379/0
   export PYTHONPATH=/path/to/optimal_build
   RQ_CONNECTION_CLASS=rq.connections.RetryConnection rq worker preview
   ```
   Leave this terminal open to observe job logs.

4. **Enqueue Preview Job**
   ```bash
   cd backend
   ../.venv/bin/python -m backend.scripts.preview enqueue --property-id "${PREVIEW_PROPERTY_ID}"
   ```
   The CLI prints the new `job_id`. Record it along with the property UUID.

5. **Monitor Job Status**
   - CLI: `../.venv/bin/python -m backend.scripts.preview list --property-id "${PREVIEW_PROPERTY_ID}"`
   - API: `http GET http://127.0.0.1:8000/api/v1/developers/properties/${PREVIEW_PROPERTY_ID}/preview-jobs`

   Expect status transitions `QUEUED → PROCESSING → READY`.

6. **Download Artifacts**
   ```bash
   curl -o preview.gltf  "$(jq -r '.items[0].preview_url' <<<"$JOB_JSON")"
   curl -o preview.json  "$(jq -r '.items[0].metadata_url' <<<"$JOB_JSON")"
   curl -o preview.png   "$(jq -r '.items[0].thumbnail_url' <<<"$JOB_JSON")"
   ```
   Inspect `preview.json.layers` for color legend + geometry detail.

7. **Capture Metrics**
   ```bash
   curl -s http://127.0.0.1:8000/metrics | grep -E 'preview_generation_(job_duration_ms|jobs_)'
   ```
   Verify `preview_generation_jobs_completed_total{outcome="ready"}` increased and `preview_generation_job_duration_ms_bucket` shows the latest observation.

8. **Record Findings**
   Log distro, commands, job ID, duration (`finished_at - requested_at`), and any anomalies in `docs/all_steps_to_product_completion.md` (Phase 2B section).

9. **Cleanup**
   - Stop the worker (`Ctrl+C`) and API server.
   - `docker stop preview-redis`.

## Expected Output
- Preview job transitions to `READY` with valid GLTF/JSON/thumbnail URLs.
- `/metrics` exposes nonzero `preview_generation_job_duration_ms_count` and queue depth gauge is near zero after completion.
- Worker logs show `preview.generate` start/finish without fork warnings.

If any step fails, capture the log snippet and file an item in the unified backlog.
