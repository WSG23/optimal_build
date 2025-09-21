# Reviewer Standard Operating Procedure

Data reviewers are the final gate before new reference data is promoted to
production.  Follow this checklist for every batch:

1. **Confirm ingestion run**
   * Verify the Prefect run succeeded and the `RefIngestionRun` record contains
     non-zero `records_ingested`.
   * Review the structured log emitted for the run and capture any anomalies in
     the review notes.
2. **Inspect suspected updates**
   * Query `RefAlert` for warnings linked to the run.  Each alert must be
     triaged and either resolved (acknowledged) or escalated.
   * Cross-check the `provenance` payload on affected standards to ensure the
     source document matches the release notes.
3. **Validate cost adjustments**
   * Recompute a sample PWP pro-forma adjustment using the `/api/v1/costs`
     endpoint and ensure the scalar matches the provider bulletin.
   * Confirm the Prometheus gauge `pwp_cost_adjustment_scalar` reflects the
     latest index for the series under review.
4. **Sign-off**
   * Update the review log with reviewer name, timestamp, and a link to any
     supporting documents.
   * Acknowledge all alerts tied to the run and, if applicable, create follow-up
     tickets for the engineering backlog.
