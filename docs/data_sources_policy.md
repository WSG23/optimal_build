# Data Source Policy

Our reference datasets are assembled from publicly available regulatory and
market sources.  The objectives of the policy are to guarantee legal usage,
traceability, and timely updates.

## Standards and Codes

* **Primary sources**: national building control agencies (e.g., BCA, SCDF,
  URA), ISO/EN committees, and statutory boards that publish requirements.
* **Acquisition**: prefer official downloads with explicit licensing
  statements; where web scraping is required ensure robots.txt compliance and
  capture the request headers alongside the retrieved artifact.
* **Licensing**: store the license reference identifier in
  `RefMaterialStandard.license_ref` and persist provenance metadata (publication
  URL, fetch timestamp, checksum) in `provenance`.

## Cost Indices and Catalogues

* **Cost indices**: ingest from recognised construction economics providers.
  Document the provider and methodology fields to allow downstream audit.
* **Catalogues**: capture vendor sourced price books or government catalogues.
  Use the `item_metadata` JSON payload to store unit definitions, minimum order
  quantities, and any regional adjustments.
* **Validation**: every batch run must compare the new scalar against the prior
  value and record deviations larger than five percent in the alerts table.

## Alerting and Escalation

* All suspected updates or anomalies must raise a `warning` level alert through
  the Prefect flow.  Critical discrepancies (e.g., missing chapters, malformed
  cost feeds) should use the `critical` level and page the data duty officer.
* Alerts must include actionable context such as upstream references, affected
  jurisdictions, and recommended next steps.

## Retention and Access

* Keep raw sources for at least two years to enable backfilling and regulatory
  audits.  Store them in the secure ingestion bucket with checksum validation.
* Only the ingestion service account and the review team should have write
  access.  Audit logs are exported weekly.
