# Infrastructure Monitoring and Load Testing

This guide summarises the new monitoring utilities added for the Phase 2D audit items.

## Slow Query Logging
- Configure the threshold via `SLOW_QUERY_THRESHOLD_SECONDS` (default `0.5` seconds) in your environment or `.env` file.
- Queries exceeding the threshold emit a warning under the `app.database` logger, including truncated SQL and bound parameters.
- For ad-hoc analysis, tail the structured logs: `tail -f .devstack/backend.log`.

## API Error Logging
- The backend now includes `ApiErrorLoggingMiddleware`, which records unhandled exceptions (`api_exception`) and HTTP 5xx responses (`api_error_response`).
- Both events are emitted via the structured logging stack, so they appear alongside other telemetry in `backend.log` or your configured sink.

## Local Resource Checks
- Run `./scripts/check_system_resources.sh` to capture current disk, memory, and top CPU consumers.
- All commands are guarded so the script degrades gracefully when utilities are missing.

## Local Load Testing
- The preferred benchmark remains Apache Bench: `ab -n 1000 -c 10 http://localhost:9400/api/v1/health`.
- The sandbox image used for automated testing does not bundle `ab`; when it is unavailable you can execute the Python fallback script: `python scripts/load_test_healthcheck.py --requests 1000 --concurrency 10`.
- Due to the missing FastAPI runtime in this environment the benchmark could not be executed here; run it locally once the API server is available and record the latency percentiles above for the audit log.
