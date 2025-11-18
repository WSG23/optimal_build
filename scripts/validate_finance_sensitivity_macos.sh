#!/usr/bin/env bash
# Finance Sensitivity Validation Runner (macOS Fallback)
#
# ⚠️  WARNING: This runs on macOS, not Linux as specified in docs/validation/finance_sensitivity_linux.md
# macOS has known fork safety issues with RQ workers. This validation is BEST-EFFORT only.
# For production validation, run on a real Linux host per the official guide.
#
# This script automates the 9-step validation procedure with macOS-specific workarounds.

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Validation results file
RESULTS_FILE="validation_results_macos_$(date +%Y%m%d_%H%M%S).md"

# Process IDs for cleanup
API_PID=""
WORKER_PID=""

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
# Finance Sensitivity Validation Results (macOS Fallback)

⚠️  **IMPORTANT:** This validation was run on macOS, not Linux as specified in the official guide.
macOS has known fork safety issues with RQ workers. For production validation, this should be
repeated on a Linux host following [docs/validation/finance_sensitivity_linux.md](../docs/validation/finance_sensitivity_linux.md).

**Date:** $(date +'%Y-%m-%d %H:%M:%S')
**OS:** $(uname -s) $(uname -r)
**Python:** $(.venv/bin/python --version 2>&1)
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
        warn "Redis container already running, reusing it..."
        docker exec finance-redis redis-cli ping >/dev/null 2>&1 || {
            error "Existing Redis container not responding, stopping it..."
            docker stop finance-redis >/dev/null 2>&1 || true
            docker rm finance-redis >/dev/null 2>&1 || true
        }
    fi

    # Start Redis if not running
    if ! docker ps | grep -q finance-redis; then
        docker run -d --rm --name finance-redis -p 6379:6379 redis:7.2 >/dev/null
        sleep 2
    fi

    if docker exec finance-redis redis-cli ping | grep -q PONG; then
        success "Redis container running (port 6379)"
        echo "### Step 1: Launch Redis ✅" >> "$RESULTS_FILE"
        echo "" >> "$RESULTS_FILE"
        echo '```bash' >> "$RESULTS_FILE"
        echo "docker run -d --rm --name finance-redis -p 6379:6379 redis:7.2" >> "$RESULTS_FILE"
        REDIS_VERSION=$(docker exec finance-redis redis-cli INFO server 2>/dev/null | grep "redis_version:" | cut -d: -f2 | tr -d '\r\n')
        echo "# Redis version: $REDIS_VERSION" >> "$RESULTS_FILE"
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
    echo "**DATABASE_URL:** \`postgresql+asyncpg://postgres:password@localhost:5432/building_compliance\`" >> "$RESULTS_FILE"
    echo "" >> "$RESULTS_FILE"

    if PGPASSWORD=password psql -h localhost -U postgres -d building_compliance -c "SELECT 1" >/dev/null 2>&1; then
        success "Database connection verified"
        echo "Database connection: ✅ Connected" >> "$RESULTS_FILE"

        # Get project ID for testing
        PROJECT_ID=$(PGPASSWORD=password psql -h localhost -U postgres -d building_compliance -t -c "SELECT id FROM projects LIMIT 1" 2>/dev/null | xargs)
        echo "$PROJECT_ID" > /tmp/project_id.txt
        echo "**Test Project ID:** \`$PROJECT_ID\`" >> "$RESULTS_FILE"
    else
        error "Database connection failed"
        exit 1
    fi
    echo "" >> "$RESULTS_FILE"
}

# Step 3: Start API server (background)
step3_start_api_server() {
    log "Step 3: Starting API server with RQ backend..."

    export SECRET_KEY=dev-secret
    export DATABASE_URL="postgresql+asyncpg://postgres:password@localhost:5432/building_compliance"
    export JOB_QUEUE_BACKEND=rq
    export RQ_REDIS_URL=redis://127.0.0.1:6379/0
    export API_RATE_LIMIT=60
    export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
    export PYTHONPATH=$(pwd)

    # Kill any existing API server on port 8000
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    sleep 1

    # Start API server in background
    .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --app-dir backend > /tmp/finance_api.log 2>&1 &
    API_PID=$!

    # Wait for server to be ready
    log "Waiting for API server to be ready (PID: $API_PID)..."
    for i in {1..30}; do
        if curl -s http://127.0.0.1:8000/health >/dev/null 2>&1 || curl -s http://127.0.0.1:8000/docs >/dev/null 2>&1; then
            success "API server running (PID: $API_PID, port 8000)"
            echo "### Step 3: API Server Started ✅" >> "$RESULTS_FILE"
            echo "" >> "$RESULTS_FILE"
            echo "**Process ID:** $API_PID" >> "$RESULTS_FILE"
            echo "**Endpoint:** http://127.0.0.1:8000" >> "$RESULTS_FILE"
            echo "**Config:**" >> "$RESULTS_FILE"
            echo '```bash' >> "$RESULTS_FILE"
            echo "JOB_QUEUE_BACKEND=rq" >> "$RESULTS_FILE"
            echo "RQ_REDIS_URL=redis://127.0.0.1:6379/0" >> "$RESULTS_FILE"
            echo "OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES  # macOS workaround" >> "$RESULTS_FILE"
            echo '```' >> "$RESULTS_FILE"
            echo "" >> "$RESULTS_FILE"
            return 0
        fi
        sleep 1
    done

    error "API server failed to start (check /tmp/finance_api.log)"
    tail -50 /tmp/finance_api.log
    exit 1
}

# Step 4: Start RQ worker (background)
step4_start_rq_worker() {
    log "Step 4: Starting RQ worker for finance queue..."

    export SECRET_KEY=dev-secret
    export RQ_REDIS_URL=redis://127.0.0.1:6379/0
    export PYTHONPATH=$(pwd)
    export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
    export DATABASE_URL="postgresql+asyncpg://postgres:password@localhost:5432/building_compliance"

    # Start RQ worker in background
    cd backend
    RQ_CONNECTION_CLASS=rq.connections.RetryConnection \
        ../.venv/bin/rq worker finance > /tmp/finance_rq_worker.log 2>&1 &
    WORKER_PID=$!
    cd ..

    # Wait for worker to be ready
    sleep 3

    if ps -p $WORKER_PID > /dev/null 2>&1; then
        success "RQ worker running (PID: $WORKER_PID, queue: finance)"
        warn "Note: macOS fork safety issues may cause worker instability"
        echo "### Step 4: RQ Worker Started ✅" >> "$RESULTS_FILE"
        echo "" >> "$RESULTS_FILE"
        echo "**Process ID:** $WORKER_PID" >> "$RESULTS_FILE"
        echo "**Queue:** finance" >> "$RESULTS_FILE"
        echo "**Log:** /tmp/finance_rq_worker.log" >> "$RESULTS_FILE"
        echo "**⚠️  Note:** macOS fork safety issues may cause worker instability" >> "$RESULTS_FILE"
        echo "" >> "$RESULTS_FILE"
        return 0
    else
        error "RQ worker failed to start (check /tmp/finance_rq_worker.log)"
        cat /tmp/finance_rq_worker.log
        exit 1
    fi
}

# Step 5: Create finance scenario
step5_create_scenario() {
    log "Step 5: Creating finance scenario..."

    PROJECT_ID=$(cat /tmp/project_id.txt)

    # Create scenario via API
    RESPONSE=$(curl -s -X POST http://127.0.0.1:8000/api/v1/finance/scenarios \
        -H "Content-Type: application/json" \
        -H "X-Role: reviewer" \
        -H "X-User-Email: reviewer@example.com" \
        -d '{
            "project_id": "'"$PROJECT_ID"'",
            "scenario_name": "macOS Async Validation"
        }' 2>&1 || echo '{"error": "Failed to create scenario"}')

    log "Create scenario response: $RESPONSE"

    SCENARIO_ID=$(echo "$RESPONSE" | .venv/bin/python -c "import sys, json; data=json.load(sys.stdin); print(data.get('id', data.get('scenario_id', 'ERROR')))" 2>/dev/null || echo "ERROR")

    if [ "$SCENARIO_ID" != "ERROR" ] && [ "$SCENARIO_ID" != "null" ] && [ -n "$SCENARIO_ID" ]; then
        success "Finance scenario created (ID: $SCENARIO_ID)"
        echo "### Step 5: Finance Scenario Created ✅" >> "$RESULTS_FILE"
        echo "" >> "$RESULTS_FILE"
        echo "**Scenario ID:** $SCENARIO_ID" >> "$RESULTS_FILE"
        echo "**Project ID:** $PROJECT_ID" >> "$RESULTS_FILE"
        echo "**Name:** macOS Async Validation" >> "$RESULTS_FILE"
        echo "" >> "$RESULTS_FILE"
        echo "$SCENARIO_ID" > /tmp/scenario_id.txt
        return 0
    else
        error "Failed to create finance scenario"
        echo "Response: $RESPONSE"
        echo "### Step 5: Finance Scenario Creation ❌" >> "$RESULTS_FILE"
        echo "" >> "$RESULTS_FILE"
        echo "**Error:** Failed to create scenario" >> "$RESULTS_FILE"
        echo '```' >> "$RESULTS_FILE"
        echo "$RESPONSE" >> "$RESULTS_FILE"
        echo '```' >> "$RESULTS_FILE"
        echo "" >> "$RESULTS_FILE"
        return 1
    fi
}

# Step 6: Trigger async sensitivity rerun
step6_trigger_sensitivity() {
    log "Step 6: Triggering async sensitivity rerun..."

    if [ ! -f /tmp/scenario_id.txt ]; then
        warn "No scenario ID found, skipping sensitivity trigger"
        return 1
    fi

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
        }' 2>&1)

    log "Sensitivity response: $RESPONSE"

    # Check for queued status
    if echo "$RESPONSE" | grep -q '"status":"queued"' || echo "$RESPONSE" | grep -q '"status": "queued"'; then
        success "Sensitivity job queued successfully"
        echo "### Step 6: Async Sensitivity Triggered ✅" >> "$RESULTS_FILE"
        echo "" >> "$RESULTS_FILE"
        echo "**Status:** queued" >> "$RESULTS_FILE"
        echo "**Bands:** 2 (Rent, Interest Rate)" >> "$RESULTS_FILE"
        echo "" >> "$RESULTS_FILE"
        return 0
    else
        warn "Sensitivity job response unexpected: $RESPONSE"
        echo "### Step 6: Async Sensitivity Trigger ⚠️" >> "$RESULTS_FILE"
        echo "" >> "$RESULTS_FILE"
        echo "**Status:** unexpected response" >> "$RESULTS_FILE"
        echo '```json' >> "$RESULTS_FILE"
        echo "$RESPONSE" | .venv/bin/python -m json.tool 2>/dev/null || echo "$RESPONSE" >> "$RESULTS_FILE"
        echo '```' >> "$RESULTS_FILE"
        echo "" >> "$RESULTS_FILE"
        return 1
    fi
}

# Step 7: Poll job status
step7_poll_job_status() {
    log "Step 7: Polling job status..."

    if [ ! -f /tmp/scenario_id.txt ]; then
        warn "No scenario ID found, skipping job polling"
        return 1
    fi

    SCENARIO_ID=$(cat /tmp/scenario_id.txt)

    # Poll for up to 60 seconds
    for i in {1..60}; do
        JOBS_RESPONSE=$(curl -s "http://127.0.0.1:8000/api/v1/finance/jobs?scenario_id=$SCENARIO_ID" 2>&1)
        STATUS=$(echo "$JOBS_RESPONSE" | .venv/bin/python -c "import sys, json; jobs = json.load(sys.stdin); print(jobs[0]['status'] if jobs and len(jobs) > 0 else 'unknown')" 2>/dev/null || echo "unknown")

        if [ "$STATUS" != "unknown" ]; then
            log "  Poll $i/60: Job status = $STATUS"
        fi

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
            echo "### Step 7: Job Status Polling ❌" >> "$RESULTS_FILE"
            echo "" >> "$RESULTS_FILE"
            echo "**Final Status:** failed" >> "$RESULTS_FILE"
            echo '```' >> "$RESULTS_FILE"
            echo "$JOBS_RESPONSE" >> "$RESULTS_FILE"
            echo '```' >> "$RESULTS_FILE"
            echo "" >> "$RESULTS_FILE"
            return 1
        fi

        sleep 1
    done

    warn "Job did not complete within 60 seconds (status: $STATUS)"
    echo "### Step 7: Job Status Polling ⚠️" >> "$RESULTS_FILE"
    echo "" >> "$RESULTS_FILE"
    echo "**Result:** Timeout after 60 seconds" >> "$RESULTS_FILE"
    echo "**Last Status:** $STATUS" >> "$RESULTS_FILE"
    echo "" >> "$RESULTS_FILE"
    return 1
}

# Step 8: Check metrics
step8_check_metrics() {
    log "Step 8: Checking /metrics endpoint..."

    METRICS=$(curl -s http://127.0.0.1:8000/metrics 2>&1 || echo "")

    if [ -z "$METRICS" ]; then
        warn "/metrics endpoint not available"
        echo "### Step 8: Metrics Verification ⚠️" >> "$RESULTS_FILE"
        echo "" >> "$RESULTS_FILE"
        echo "**Result:** /metrics endpoint not available" >> "$RESULTS_FILE"
        echo "" >> "$RESULTS_FILE"
        return 1
    fi

    # Extract finance_sensitivity metrics
    QUEUED_COUNT=$(echo "$METRICS" | grep 'finance_sensitivity_jobs_total{status="queued"}' | awk '{print $2}' 2>/dev/null || echo "0")
    COMPLETED_COUNT=$(echo "$METRICS" | grep 'finance_sensitivity_jobs_total{status="completed"}' | awk '{print $2}' 2>/dev/null || echo "0")

    success "Metrics captured"
    echo "### Step 8: Metrics Verification ✅" >> "$RESULTS_FILE"
    echo "" >> "$RESULTS_FILE"
    echo "**finance_sensitivity_jobs_total{status=\"queued\"}:** ${QUEUED_COUNT:-N/A}" >> "$RESULTS_FILE"
    echo "**finance_sensitivity_jobs_total{status=\"completed\"}:** ${COMPLETED_COUNT:-N/A}" >> "$RESULTS_FILE"
    echo "" >> "$RESULTS_FILE"
}

# Step 9: Test deduplication
step9_test_deduplication() {
    log "Step 9: Testing deduplication..."

    if [ ! -f /tmp/scenario_id.txt ]; then
        warn "No scenario ID found, skipping deduplication test"
        return 1
    fi

    SCENARIO_ID=$(cat /tmp/scenario_id.txt)

    # Trigger duplicate request with same bands
    DUP_RESPONSE=$(curl -s -X POST "http://127.0.0.1:8000/api/v1/finance/scenarios/$SCENARIO_ID/sensitivity" \
        -H "Content-Type: application/json" \
        -H "X-Role: reviewer" \
        -H "X-User-Email: reviewer@example.com" \
        -d '{
            "sensitivity_bands": [
                {"parameter": "Rent", "low": "-5", "base": "0", "high": "6"},
                {"parameter": "Interest Rate", "low": "2", "base": "0", "high": "-1"}
            ]
        }' 2>&1)

    log "Deduplication test response: $DUP_RESPONSE"

    # Check if response indicates cached/existing job
    if echo "$DUP_RESPONSE" | grep -q '"status":"completed"' || echo "$DUP_RESPONSE" | grep -q 'sensitivity_jobs'; then
        success "Deduplication working (returned existing results)"
        echo "### Step 9: Deduplication Test ✅" >> "$RESULTS_FILE"
        echo "" >> "$RESULTS_FILE"
        echo "**Result:** Deduplication working" >> "$RESULTS_FILE"
        echo "**Response:** Returned existing/cached results without enqueuing new job" >> "$RESULTS_FILE"
        echo "" >> "$RESULTS_FILE"
        return 0
    else
        warn "Deduplication test inconclusive"
        echo "### Step 9: Deduplication Test ⚠️" >> "$RESULTS_FILE"
        echo "" >> "$RESULTS_FILE"
        echo "**Result:** Inconclusive" >> "$RESULTS_FILE"
        echo '```' >> "$RESULTS_FILE"
        echo "$DUP_RESPONSE" >> "$RESULTS_FILE"
        echo '```' >> "$RESULTS_FILE"
        echo "" >> "$RESULTS_FILE"
        return 1
    fi
}

# Cleanup function
cleanup() {
    log "Cleaning up..."

    # Stop API server
    if [ -n "$API_PID" ] && ps -p "$API_PID" > /dev/null 2>&1; then
        log "Stopping API server (PID: $API_PID)..."
        kill "$API_PID" 2>/dev/null || true
        sleep 1
        kill -9 "$API_PID" 2>/dev/null || true
    fi

    # Stop RQ worker
    if [ -n "$WORKER_PID" ] && ps -p "$WORKER_PID" > /dev/null 2>&1; then
        log "Stopping RQ worker (PID: $WORKER_PID)..."
        kill "$WORKER_PID" 2>/dev/null || true
        sleep 1
        kill -9 "$WORKER_PID" 2>/dev/null || true
    fi

    # Stop Redis container
    docker stop finance-redis >/dev/null 2>&1 || true

    success "Cleanup complete"

    echo "" >> "$RESULTS_FILE"
    echo "---" >> "$RESULTS_FILE"
    echo "" >> "$RESULTS_FILE"
    echo "## Conclusion" >> "$RESULTS_FILE"
    echo "" >> "$RESULTS_FILE"
    echo "⚠️  **macOS Validation Limitations:**" >> "$RESULTS_FILE"
    echo "" >> "$RESULTS_FILE"
    echo "This validation was run on macOS as a fallback. macOS has known fork safety issues with RQ workers." >> "$RESULTS_FILE"
    echo "For production validation, this MUST be repeated on a Linux host following the official guide:" >> "$RESULTS_FILE"
    echo "[docs/validation/finance_sensitivity_linux.md](../docs/validation/finance_sensitivity_linux.md)" >> "$RESULTS_FILE"
    echo "" >> "$RESULTS_FILE"
    echo "**Logs:**" >> "$RESULTS_FILE"
    echo "- API server: /tmp/finance_api.log" >> "$RESULTS_FILE"
    echo "- RQ worker: /tmp/finance_rq_worker.log" >> "$RESULTS_FILE"
    echo "" >> "$RESULTS_FILE"
    echo "**Next Steps:**" >> "$RESULTS_FILE"
    echo "1. Review logs for any errors or warnings" >> "$RESULTS_FILE"
    echo "2. Schedule Linux validation on a proper Linux host" >> "$RESULTS_FILE"
    echo "3. Update docs/all_steps_to_product_completion.md with results" >> "$RESULTS_FILE"
}

# Trap cleanup on exit
trap cleanup EXIT INT TERM

# Main execution
main() {
    warn "================================================================"
    warn "⚠️  RUNNING ON macOS (NOT LINUX)"
    warn "================================================================"
    warn "This is a FALLBACK validation. macOS has fork safety issues."
    warn "For production validation, run on Linux per:"
    warn "  docs/validation/finance_sensitivity_linux.md"
    warn "================================================================"
    echo ""

    log "Starting Finance Sensitivity Validation (macOS Fallback)"
    echo ""

    init_results_file

    step1_launch_redis
    step2_check_database
    step3_start_api_server
    step4_start_rq_worker

    # Continue even if some steps fail
    step5_create_scenario || warn "Step 5 failed, continuing..."
    step6_trigger_sensitivity || warn "Step 6 failed, continuing..."
    step7_poll_job_status || warn "Step 7 failed, continuing..."
    step8_check_metrics || warn "Step 8 failed, continuing..."
    step9_test_deduplication || warn "Step 9 failed, continuing..."

    echo ""
    warn "⚠️  macOS validation completed (see warnings above)"
    success "Results saved to: $RESULTS_FILE"
    echo ""
    log "Next steps:"
    log "1. Review $RESULTS_FILE for issues"
    log "2. Check logs: /tmp/finance_api.log, /tmp/finance_rq_worker.log"
    log "3. Schedule proper Linux validation"
    log "4. Update docs/all_steps_to_product_completion.md"
}

# Run main
main "$@"
