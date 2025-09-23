# Feasibility Observability

The buildable screening endpoint (`/api/v1/screen/buildable`) emits Prometheus
metrics to expose request volumes and performance characteristics via the
`/health/metrics` endpoint.

* `pwp_buildable_total` – Counter incremented for every buildable screening
  request. Operators can alert on sustained drops or spikes to monitor feature
  usage.
* `pwp_buildable_duration_ms` – Histogram that records the duration of each
  request in milliseconds. The `_count`, `_sum`, and `_bucket` series allow
  latency SLO tracking and dashboarding.

Our backend tests assert that invoking the buildable screening flow increments
both metrics and that they are rendered in the health check metrics response.
