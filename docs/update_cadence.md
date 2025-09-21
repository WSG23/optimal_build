# Update Cadence and Monitoring

The ingestion scheduler coordinates multiple upstream feeds.  Each flow records
run metadata in `RefIngestionRun` and exposes Prometheus counters for
automation.

| Data set | Source | Frequency | Monitoring |
|----------|--------|-----------|------------|
| Building standards | BCA / SCDF bulletins | Weekly watch on Thursdays | Prefect flow `material-standard-ingestion`; alert on any suspected updates. |
| Cost indices | Government construction economics bulletin | Monthly, second business day | Prefect flow `cost-index-refresh`; compare scalar with previous period and alert when delta > 5%. |
| Vendor catalogues | Strategic supplier uploads | Quarterly, first Monday | Manual trigger with review sign-off; store version metadata in `RefCostCatalog`. |

### Monitoring Hooks

* Prefect flows must call the ingestion service helpers so that every run
  persists start/finish timestamps, record counts, and suspected update totals.
* The `/health/metrics` endpoint should be scraped every minute.  Missing
  samples for five minutes require investigation of the API deployment.
* Alert volumes are tracked by `ingestion_alerts_total` and should remain under
  five per week during steady state.
