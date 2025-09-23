# Feasibility API README snippet

The buildable screening endpoint (`POST /api/v1/screen/buildable`) accepts both
snake_case and camelCase for the adjustable assumptions documented in the
frontend README. Either casing may be used for the request body:

```json
{
  "address": "123 Example Ave",
  "typ_floor_to_floor_m": 3.4,
  "efficiency_ratio": 0.8,
  "defaults": {
    "plot_ratio": 3.5,
    "site_area_m2": 1000,
    "site_coverage": 0.45,
    "floor_height_m": 3.4,
    "efficiency_factor": 0.8
  }
}
```

Legacy clients may continue sending camelCase keys and the backend will
normalise them automatically. The service recognises the following aliases:

* `typFloorToFloorM` → `typ_floor_to_floor_m`
* `efficiencyRatio` → `efficiency_ratio`
* `defaults` → `defaults` (including nested keys like `plotRatio`,
  `siteAreaM2`, `siteCoverage`, `floorHeightM`, and `efficiencyFactor`)

For example:

```json
{
  "address": "123 Example Ave",
  "typFloorToFloorM": 3.4,
  "efficiencyRatio": 0.8,
  "defaults": {
    "plotRatio": 3.5,
    "siteAreaM2": 1000,
    "siteCoverage": 45,
    "floorHeightM": 3.4,
    "efficiencyFactor": 0.8
  }
}
```

Both payloads resolve to the same `BuildableRequest` object, ensuring the API
remains backwards compatible with older Feasibility Wizard builds.

## Observability

The buildable screening service exposes Prometheus metrics to track throughput
and performance:

* `pwp_buildable_total` &mdash; increments for every successful buildable
  screening request processed.
* `pwp_buildable_duration_ms` &mdash; histogram measuring the time spent computing
  a response in milliseconds.

Both metrics are included in the `/health/metrics` endpoint and in the output of
`app.utils.metrics.render_latest_metrics()`, enabling dashboards and alerts to
verify that requests are flowing and that latency stays within expected
thresholds.
