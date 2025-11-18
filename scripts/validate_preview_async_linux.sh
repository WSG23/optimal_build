#!/usr/bin/env bash
# Preview Generation Async Validation Runner (Linux)
# Mirrors docs/validation/preview_async_linux.md

set -euo pipefail

if [[ "$(uname -s)" != "Linux" ]]; then
  echo "This validation must run on Linux." >&2
  exit 1
fi

PROPERTY_ID="${PREVIEW_PROPERTY_ID:-${1:-}}"
if [[ -z "$PROPERTY_ID" ]]; then
  echo "Usage: PREVIEW_PROPERTY_ID=<uuid> bash scripts/validate_preview_async_linux.sh" >&2
  exit 1
fi

DATABASE_URL="${DATABASE_URL:-postgresql+asyncpg://postgres:password@localhost:5432/building_compliance}"
RESULTS_FILE="preview_validation_results_$(date +%Y%m%d_%H%M%S).md"
API_LOG="/tmp/preview_api.log"
WORKER_LOG="/tmp/preview_worker.log"
REDIS_NAME="preview-redis"
API_PID=""
WORKER_PID=""

log() {
  printf "\033[0;34m[%s]\033[0m %s\n" "$(date +'%Y-%m-%d %H:%M:%S')" "$*"
}

success() {
  printf "\033[0;32m%s\033[0m\n" "$*"
}

cleanup() {
  log "Cleaning up processes..."
  [[ -n "$WORKER_PID" ]] && kill "$WORKER_PID" 2>/dev/null || true
  [[ -n "$API_PID" ]] && kill "$API_PID" 2>/dev/null || true
  docker stop "$REDIS_NAME" >/dev/null 2>&1 || true
}

trap cleanup EXIT

cat >"$RESULTS_FILE" <<EOF
# Preview Async Validation

- Date: $(date +'%Y-%m-%d %H:%M:%S')
- Host: $(hostname)
- Kernel: $(uname -sr)
- Property ID: $PROPERTY_ID
- Database URL: $DATABASE_URL

---

EOF

log "Starting Redis container..."
docker run -d --rm --name "$REDIS_NAME" -p 6379:6379 redis:7.2 >/dev/null
sleep 2
docker exec "$REDIS_NAME" redis-cli ping >/dev/null
echo "1. Redis ✅ (\`docker run --name $REDIS_NAME redis:7.2\`)" >>"$RESULTS_FILE"

log "Starting API server (RQ backend)..."
(
  export SECRET_KEY=dev-secret
  export DATABASE_URL="$DATABASE_URL"
  export JOB_QUEUE_BACKEND=rq
  export RQ_REDIS_URL=redis://127.0.0.1:6379/0
  export API_RATE_LIMIT=120
  export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
  cd backend
  ../.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 >"$API_LOG" 2>&1 &
  API_PID=$!
  echo "$API_PID" > /tmp/preview_api.pid
)
API_PID=$(cat /tmp/preview_api.pid)
rm /tmp/preview_api.pid
for _ in {1..30}; do
  if curl -s http://127.0.0.1:8000/health >/dev/null 2>&1; then
    success "API running (PID: $API_PID)"
    echo "2. API ✅ (PID $API_PID, JOB_QUEUE_BACKEND=rq)" >>"$RESULTS_FILE"
    break
  fi
  sleep 1
done

log "Starting RQ worker (preview queue)..."
(
  export SECRET_KEY=dev-secret
  export RQ_REDIS_URL=redis://127.0.0.1:6379/0
  export PYTHONPATH="$(pwd)"
  cd backend
  RQ_CONNECTION_CLASS=rq.connections.RetryConnection \
    ../.venv/bin/rq worker preview >"$WORKER_LOG" 2>&1 &
  echo $! > /tmp/preview_worker.pid
)
WORKER_PID=$(cat /tmp/preview_worker.pid)
rm /tmp/preview_worker.pid
sleep 3
ps -p "$WORKER_PID" >/dev/null
success "Worker PID $WORKER_PID"
echo "3. Worker ✅ (PID $WORKER_PID, queue preview)" >>"$RESULTS_FILE"

log "Enqueueing preview job..."
JOB_ID=$(cd backend && ../.venv/bin/python -m backend.scripts.preview enqueue --property-id "$PROPERTY_ID" | awk '/Preview job enqueued/ {print $5}')
JOB_ID="${JOB_ID:-unknown}"
echo "4. Queue ✅ (job $JOB_ID)" >>"$RESULTS_FILE"

log "Polling job status..."
STATUS=""
for _ in {1..60}; do
  STATUS=$(cd backend && ../.venv/bin/python -m backend.scripts.preview list --property-id "$PROPERTY_ID" | awk '/Status:/ {print $2}')
  if [[ "$STATUS" == "READY" ]]; then
    break
  fi
  sleep 2
done

echo "5. Job status: $STATUS" >>"$RESULTS_FILE"
[[ "$STATUS" != "READY" ]] && { log "Job did not finish in time"; exit 1; }

log "Capturing metrics snapshot..."
METRICS=$(curl -s http://127.0.0.1:8000/metrics | grep preview_generation || true)
{
  echo "6. Metrics snapshot"
  echo '```'
  echo "$METRICS"
  echo '```'
} >>"$RESULTS_FILE"

log "Validation complete → $RESULTS_FILE"
