# Preview Generation Monitoring Playbook

**Last updated:** 2025-11-04
**Phase:** 2B Visualisation

This note describes how to visualise and alert on the new `preview_generation_*` metrics emitted by the backend when developer preview jobs are queued and processed. A ready-to-import Grafana dashboard is checked into the repo at `infra/observability/grafana/phase2b_preview_dashboard.json`, and matching Prometheus alert rules live at `infra/observability/prometheus/preview_generation.rules.yml`.

---

## 1. Metric Summary

| Metric | Type | Labels | Meaning |
|--------|------|--------|---------|
| `preview_generation_jobs_total` | Counter | `scenario`, `backend` | Number of preview jobs enqueued (includes retries). |
| `preview_generation_jobs_completed_total` | Counter | `outcome ∈ {ready, failed}` | Jobs that reached a terminal state. |
| `preview_generation_job_duration_ms` | Histogram | `outcome` | End-to-end job latency (request → completion) in milliseconds. |
| `preview_generation_queue_depth` | Gauge | `backend` | Current number of jobs still marked as `queued`. |

> The `backend` label distinguishes inline execution (tests/local) from asynchronous queue runners (e.g., RQ, Celery).

---

## 2. Grafana Dashboard Suggestions

### 2.1 Importing the dashboard

1. In Grafana, go to **Dashboards → New → Import**.
2. Upload `infra/observability/grafana/phase2b_preview_dashboard.json` (or paste its contents in the JSON field).
3. Select your Prometheus datasource and click **Import**. Panels will populate automatically.

### 2.2 Job Throughput (manual reference)

**Panel title:** _Preview jobs per minute_
**PromQL:**
```promql
sum by (scenario) (
  rate(preview_generation_jobs_total[5m])
)
```

### 2.3 Success vs Failure Rate

**Panel title:** _Job outcomes (%)_
**PromQL:**
```promql
100 *
sum by (outcome) (rate(preview_generation_jobs_completed_total[15m]))
/
sum (rate(preview_generation_jobs_completed_total[15m]))
```

### 2.4 Queue Depth

**Panel title:** _Preview queue depth_
**PromQL:**
```promql
preview_generation_queue_depth
```

### 2.5 Latency (P95)

**Panel title:** _Job duration (p95 ms)_
**PromQL:**
```promql
histogram_quantile(
  0.95,
  sum by (le) (
    rate(preview_generation_job_duration_ms_bucket{outcome="ready"}[15m])
  )
)
```

---

## 3. Alert Rules

The following Prometheus-compatible alert examples assume recording rules described above.

### 3.1 High Failure Rate

```
alert: PreviewGenerationHighFailureRate
expr: |
  sum(rate(preview_generation_jobs_completed_total{outcome="failed"}[10m]))
    /
  sum(rate(preview_generation_jobs_completed_total[10m])) > 0.1
for: 10m
labels:
  severity: page
annotations:
  summary: "Preview jobs failing above 10% for 10 minutes"
  description: "Investigate renderer pod/logs – failure rate sustained above 10%."
```

### 3.2 Slow Renders

```
alert: PreviewGenerationSlow
expr: |
  histogram_quantile(
    0.95,
    sum by (le)(
      rate(preview_generation_job_duration_ms_bucket{outcome="ready"}[15m])
    )
  ) > 300000
for: 15m
labels:
  severity: warn
annotations:
  summary: "Preview job latency p95 > 5 min"
  description: "Renderer latency has degraded above 5 minutes (p95) for 15 minutes."
```

### 3.3 Queue Stuck

```
alert: PreviewQueueStalled
expr: preview_generation_queue_depth > 10
for: 5m
labels:
  severity: warn
annotations:
  summary: "Preview queue depth above 10 for 5 minutes"
  description: "Jobs are not draining – check worker status or queue backend."
```

---

## 4. Runbook Snippets

- **Investigate failures:** check `backend/app/logs/preview_jobs` (or the central log stack) for job IDs referenced in alerts.
- **Renderer health:** verify worker pods or local runner logs, ensure assets were written to `static/dev-previews/...`.
- **Retry strategy:** `POST /api/v1/developers/preview-jobs/{job_id}/refresh` can be used to manually requeue a stuck job; metrics will increment with the new attempt.

---

## 5. Next Actions

1. Import the PromQL panels into the central Grafana instance (phase owner: Platform SRE).
2. Create alertmanager routes for `preview_generation_*` alert groups.
3. Update `docs/WORK_QUEUE.MD` once dashboards are live and linked.
