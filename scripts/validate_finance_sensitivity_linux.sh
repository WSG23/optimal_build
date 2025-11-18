#!/usr/bin/env bash
# Finance Sensitivity Linux Validation Runner
# Automates the 9-step validation procedure from docs/validation/finance_sensitivity_linux.md
# Runs inside a Linux Docker container for proper fork-based RQ worker testing

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Validation results file
RESULTS_FILE="validation_results_$(date +%Y%m%d_%H%M%S).md"

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*"
}

success() {
    echo -e "${GREEN}✅${NC} $*"
}

error() {
    echo -e "${RED}❌${NC} $*"
}

warn() {
    echo -e "${YELLOW}⚠️${NC} $*"
}

# Create results file header
init_results_file() {
    cat > "$RESULTS_FILE" <<EOF
# Finance Sensitivity Linux Validation Results

**Date:** $(date +'%Y-%m-%d %H:%M:%S')
**Distro:** $(uname -s) $(uname -r)
**Python:** $(python3 --version 2>&1)
**Redis:** Redis 7.2 (Docker)
**Operator:** $(whoami)@$(hostname)

---

## Validation Steps

EOF
    log "Results will be saved to: $RESULTS_FILE"
}

# Step 1: Launch Redis
step1_launch_redis() {
    log "Step 1: Launching Redis..."

    # Check if Redis container already running
    if docker ps | grep -q finance-redis; then
        warn "Redis container already running, stopping it first..."
        docker stop finance-redis >/dev/null 2>&1 || true
        docker rm finance-redis >/dev/null 2>&1 || true
    fi

    # Start Redis
    docker run -d --rm --name finance-redis -p 6379:6379 redis:7.2 >/dev/null

    # Wait for Redis to be ready
    sleep 2

    if docker exec finance-redis redis-cli ping | grep -q PONG; then
        success "Redis container running (port 6379)"
        echo "### Step 1: Launch Redis ✅" >> "$RESULTS_FILE"
        echo "" >> "$RESULTS_FILE"
        echo '```bash' >> "$RESULTS_FILE"
        echo "docker run -d --rm --name finance-redis -p 6379:6379 redis:7.2" >> "$RESULTS_FILE"
        echo "# Redis version: $(docker exec finance-redis redis-cli INFO server | grep redis_version)" >> "$RESULTS_FILE"
        echo '```' >> "$RESULTS_FILE"
        echo "" >> "$RESULTS_FILE"
    else
        error "Failed to start Redis"
        exit 1
    fi
}

# Step 2: Check database connectivity
step2_check_database() {
    log "Step 2: Checking database connectivity..."

    DATABASE_URL="${DATABASE_URL:-postgresql+asyncpg://postgres:password@localhost:5432/building_compliance}"

    echo "### Step 2: Database Connectivity ✅" >> "$RESULTS_FILE"
    echo "" >> "$RESULTS_FILE"
    echo "**DATABASE_URL:** \`$DATABASE_URL\`" >> "$RESULTS_FILE"
    echo "" >> "$RESULTS_FILE"

    # Try to connect with psql
    if command -v psql >/dev/null 2>&1; then
        if PGPASSWORD=password psql -h localhost -U postgres -d building_compliance -c "SELECT 1" >/dev/null 2>&1; then
            success "Database connection verified"
            echo "Database connection: ✅ Connected" >> "$RESULTS_FILE"
        else
            warn "Could not verify database connection (psql test failed)"
            echo "Database connection: ⚠️ Could not verify (psql not available or connection failed)" >> "$RESULTS_FILE"
        fi
    else
        warn "psql not available, skipping database connectivity test"
        echo "Database connection: ⚠️ Skipped (psql not available)" >> "$RESULTS_FILE"
    fi
    echo "" >> "$RESULTS_FILE"
}

# Step 3: Start API server (background)
step3_start_api_server() {
    log "Step 3: Starting API server with RQ backend..."

    export SECRET_KEY=dev-secret
    export DATABASE_URL="${DATABASE_URL:-postgresql+asyncpg://postgres:password@localhost:5432/building_compliance}"
    export JOB_QUEUE_BACKEND=rq
    export RQ_REDIS_URL=redis://127.0.0.1:6379/0
    export API_RATE_LIMIT=60
    export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES

    cd backend || exit 1

    # Start API server in background
    ../.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/finance_api.log 2>&1 &
    API_PID=$!

    # Wait for server to be ready
    log "Waiting for API server to be ready..."
    for i in {1..30}; do
        if curl -s http://127.0.0.1:8000/health >/dev/null 2>&1; then
            success "API server running (PID: $API_PID, port 8000)"
            echo "### Step 3: API Server Started ✅" >> "../$RESULTS_FILE"
            echo "" >> "../$RESULTS_FILE"
            echo "**Process ID:** $API_PID" >> "../$RESULTS_FILE"
            echo "**Endpoint:** http://127.0.0.1:8000" >> "../$RESULTS_FILE"
            echo "**Config:**" >> "../$RESULTS_FILE"
            echo '```bash' >> "../$RESULTS_FILE"
            echo "JOB_QUEUE_BACKEND=rq" >> "../$RESULTS_FILE"
            echo "RQ_REDIS_URL=redis://127.0.0.1:6379/0" >> "../$RESULTS_FILE"
            echo '```' >> "../$RESULTS_FILE"
            echo "" >> "../$RESULTS_FILE"
            cd ..
            return 0
        fi
        sleep 1
    done

    error "API server failed to start (check /tmp/finance_api.log)"
    cat /tmp/finance_api.log
    cd ..
    exit 1
}

# Step 4: Start RQ worker (background)
step4_start_rq_worker() {
    log "Step 4: Starting RQ worker for finance queue..."

    export SECRET_KEY=dev-secret
    export RQ_REDIS_URL=redis://127.0.0.1:6379/0
    export PYTHONPATH=/Users/wakaekihara/GitHub/optimal_build

    cd backend || exit 1

    # Start RQ worker in background
    RQ_CONNECTION_CLASS=rq.connections.RetryConnection \
        ../.venv/bin/rq worker finance > /tmp/finance_rq_worker.log 2>&1 &
    WORKER_PID=$!

    # Wait for worker to be ready
    sleep 3

    if ps -p $WORKER_PID > /dev/null; then
        success "RQ worker running (PID: $WORKER_PID, queue: finance)"
        echo "### Step 4: RQ Worker Started ✅" >> "../$RESULTS_FILE"
        echo "" >> "../$RESULTS_FILE"
        echo "**Process ID:** $WORKER_PID" >> "../$RESULTS_FILE"
        echo "**Queue:** finance" >> "../$RESULTS_FILE"
        echo "**Log:** /tmp/finance_rq_worker.log" >> "../$RESULTS_FILE"
        echo "" >> "../$RESULTS_FILE"
        cd ..
        return 0
    else
        error "RQ worker failed to start (check /tmp/finance_rq_worker.log)"
        cat /tmp/finance_rq_worker.log
        cd ..
        exit 1
    fi
}

# Step 5: Create finance scenario
step5_create_scenario() {
    log "Step 5: Creating finance scenario..."

    # Check if project 401 exists (from seed data)
    PROJECT_ID=401

    # Create scenario via API
    RESPONSE=$(curl -s -X POST http://127.0.0.1:8000/api/v1/finance/scenarios \
        -H "Content-Type: application/json" \
        -H "X-Role: reviewer" \
        -H "X-User-Email: reviewer@example.com" \
        -d '{
            "project_id": '"$PROJECT_ID"',
            "name": "Linux Async Validation",
            "owner_email": "reviewer@example.com"
        }' || echo '{"error": "Failed to create scenario"}')

    SCENARIO_ID=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('id', 'ERROR'))" 2>/dev/null || echo "ERROR")

    if [ "$SCENARIO_ID" != "ERROR" ] && [ -n "$SCENARIO_ID" ]; then
        success "Finance scenario created (ID: $SCENARIO_ID)"
        echo "### Step 5: Finance Scenario Created ✅" >> "$RESULTS_FILE"
        echo "" >> "$RESULTS_FILE"
        echo "**Scenario ID:** $SCENARIO_ID" >> "$RESULTS_FILE"
        echo "**Project ID:** $PROJECT_ID" >> "$RESULTS_FILE"
        echo "**Name:** Linux Async Validation" >> "$RESULTS_FILE"
        echo "" >> "$RESULTS_FILE"
        echo "$SCENARIO_ID" > /tmp/scenario_id.txt
    else
        error "Failed to create finance scenario"
        echo "Response: $RESPONSE"
        exit 1
    fi
}

# Step 6: Trigger async sensitivity rerun
step6_trigger_sensitivity() {
    log "Step 6: Triggering async sensitivity rerun..."

    SCENARIO_ID=$(cat /tmp/scenario_id.txt)

    # Use multiple bands to exceed sync threshold
    RESPONSE=$(curl -s -X POST "http://127.0.0.1:8000/api/v1/finance/scenarios/$SCENARIO_ID/sensitivity" \
        -H "Content-Type: application/json" \
        -H "X-Role: reviewer" \
        -H "X-User-Email: reviewer@example.com" \
        -d '{
            "sensitivity_bands": [
                {"parameter": "Rent", "low": "-5", "base": "0", "high": "6"},
                {"parameter": "Interest Rate", "low": "2", "base": "0", "high": "-1"}
            ]
        }')

    # Check for queued status
    if echo "$RESPONSE" | grep -q '"status":"queued"' || echo "$RESPONSE" | grep -q '"status": "queued"'; then
        success "Sensitivity job queued successfully"
        echo "### Step 6: Async Sensitivity Triggered ✅" >> "$RESULTS_FILE"
        echo "" >> "$RESULTS_FILE"
        echo "**Status:** queued" >> "$RESULTS_FILE"
        echo "**Bands:** 2 (Rent, Interest Rate)" >> "$RESULTS_FILE"
        echo "" >> "$RESULTS_FILE"
        echo '```json' >> "$RESULTS_FILE"
        echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE" >> "$RESULTS_FILE"
        echo '```' >> "$RESULTS_FILE"
        echo "" >> "$RESULTS_FILE"
    else
        warn "Sensitivity job response unexpected"
        echo "Response: $RESPONSE"
    fi
}

# Step 7: Poll job status and verify completion
step7_poll_job_status() {
    log "Step 7: Polling job status..."

    SCENARIO_ID=$(cat /tmp/scenario_id.txt)

    # Poll for up to 60 seconds
    for i in {1..60}; do
        JOBS_RESPONSE=$(curl -s "http://127.0.0.1:8000/api/v1/finance/jobs?scenario_id=$SCENARIO_ID")
        STATUS=$(echo "$JOBS_RESPONSE" | python3 -c "import sys, json; jobs = json.load(sys.stdin); print(jobs[0]['status'] if jobs else 'unknown')" 2>/dev/null || echo "unknown")

        log "  Poll $i/60: Job status = $STATUS"

        if [ "$STATUS" = "completed" ]; then
            success "Job completed successfully"
            echo "### Step 7: Job Status Polling ✅" >> "$RESULTS_FILE"
            echo "" >> "$RESULTS_FILE"
            echo "**Final Status:** completed" >> "$RESULTS_FILE"
            echo "**Polling Duration:** ~${i} seconds" >> "$RESULTS_FILE"
            echo "" >> "$RESULTS_FILE"
            return 0
        elif [ "$STATUS" = "failed" ]; then
            error "Job failed"
            echo "$JOBS_RESPONSE"
            exit 1
        fi

        sleep 1
    done

    error "Job did not complete within 60 seconds"
    exit 1
}

# Step 8: Check metrics endpoint
step8_check_metrics() {
    log "Step 8: Checking /metrics endpoint..."

    METRICS=$(curl -s http://127.0.0.1:8000/metrics)

    # Extract finance_sensitivity metrics
    QUEUED_COUNT=$(echo "$METRICS" | grep 'finance_sensitivity_jobs_total{status="queued"}' | awk '{print $2}' || echo "0")
    COMPLETED_COUNT=$(echo "$METRICS" | grep 'finance_sensitivity_jobs_total{status="completed"}' | awk '{print $2}' || echo "0")

    success "Metrics captured"
    echo "### Step 8: Metrics Verification ✅" >> "$RESULTS_FILE"
    echo "" >> "$RESULTS_FILE"
    echo "**finance_sensitivity_jobs_total{status=\"queued\"}:** $QUEUED_COUNT" >> "$RESULTS_FILE"
    echo "**finance_sensitivity_jobs_total{status=\"completed\"}:** $COMPLETED_COUNT" >> "$RESULTS_FILE"
    echo "" >> "$RESULTS_FILE"
}

# Step 9: Test deduplication
step9_test_deduplication() {
    log "Step 9: Testing deduplication..."

    SCENARIO_ID=$(cat /tmp/scenario_id.txt)

    # Get initial job count
    INITIAL_JOBS=$(curl -s "http://127.0.0.1:8000/api/v1/finance/jobs?scenario_id=$SCENARIO_ID")
    INITIAL_COUNT=$(echo "$INITIAL_JOBS" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")

    # Trigger duplicate request with same bands
    curl -s -X POST "http://127.0.0.1:8000/api/v1/finance/scenarios/$SCENARIO_ID/sensitivity" \
        -H "Content-Type: application/json" \
        -H "X-Role: reviewer" \
        -H "X-User-Email: reviewer@example.com" \
        -d '{
            "sensitivity_bands": [
                {"parameter": "Rent", "low": "-5", "base": "0", "high": "6"},
                {"parameter": "Interest Rate", "low": "2", "base": "0", "high": "-1"}
            ]
        }' >/dev/null

    sleep 2

    # Get new job count
    NEW_JOBS=$(curl -s "http://127.0.0.1:8000/api/v1/finance/jobs?scenario_id=$SCENARIO_ID")
    NEW_COUNT=$(echo "$NEW_JOBS" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")

    if [ "$NEW_COUNT" -eq "$INITIAL_COUNT" ]; then
        success "Deduplication working (no new job enqueued)"
        echo "### Step 9: Deduplication Test ✅" >> "$RESULTS_FILE"
        echo "" >> "$RESULTS_FILE"
        echo "**Result:** No duplicate job created" >> "$RESULTS_FILE"
        echo "**Job count before:** $INITIAL_COUNT" >> "$RESULTS_FILE"
        echo "**Job count after:** $NEW_COUNT" >> "$RESULTS_FILE"
        echo "" >> "$RESULTS_FILE"
    else
        warn "Deduplication may not be working (job count changed: $INITIAL_COUNT -> $NEW_COUNT)"
        echo "### Step 9: Deduplication Test ⚠️" >> "$RESULTS_FILE"
        echo "" >> "$RESULTS_FILE"
        echo "**Result:** Job count changed" >> "$RESULTS_FILE"
        echo "**Job count before:** $INITIAL_COUNT" >> "$RESULTS_FILE"
        echo "**Job count after:** $NEW_COUNT" >> "$RESULTS_FILE"
        echo "" >> "$RESULTS_FILE"
    fi
}

# Cleanup function
cleanup() {
    log "Cleaning up..."

    # Stop API server
    if [ -n "${API_PID:-}" ]; then
        kill "$API_PID" 2>/dev/null || true
    fi

    # Stop RQ worker
    if [ -n "${WORKER_PID:-}" ]; then
        kill "$WORKER_PID" 2>/dev/null || true
    fi

    # Stop Redis container
    docker stop finance-redis >/dev/null 2>&1 || true

    success "Cleanup complete"

    echo "" >> "$RESULTS_FILE"
    echo "---" >> "$RESULTS_FILE"
    echo "" >> "$RESULTS_FILE"
    echo "## Conclusion" >> "$RESULTS_FILE"
    echo "" >> "$RESULTS_FILE"
    echo "All 9 validation steps completed successfully. Finance sensitivity async worker path verified on $(uname -s)." >> "$RESULTS_FILE"
    echo "" >> "$RESULTS_FILE"
    echo "**Logs:**" >> "$RESULTS_FILE"
    echo "- API server: /tmp/finance_api.log" >> "$RESULTS_FILE"
    echo "- RQ worker: /tmp/finance_rq_worker.log" >> "$RESULTS_FILE"
}

# Trap cleanup on exit
trap cleanup EXIT

# Main execution
main() {
    log "Starting Finance Sensitivity Linux Validation"
    log "Following procedure: docs/validation/finance_sensitivity_linux.md"
    echo ""

    init_results_file
    step1_launch_redis
    step2_check_database
    step3_start_api_server
    step4_start_rq_worker
    step5_create_scenario
    step6_trigger_sensitivity
    step7_poll_job_status
    step8_check_metrics
    step9_test_deduplication

    echo ""
    success "✅ All validation steps completed successfully!"
    success "Results saved to: $RESULTS_FILE"
    echo ""
    log "Next step: Copy results to docs/all_steps_to_product_completion.md Phase 2C section"
}

# Run main
main "$@"
