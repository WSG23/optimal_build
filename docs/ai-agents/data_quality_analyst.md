# Persona: Data Quality Analyst

**When to engage:** New ingests/pipelines, schema changes, new data sources, anomaly/backfill handling.

**Entry:** Source contracts known; critical fields and consumers identified.
**Exit:** Validation rules and thresholds documented; alerts/monitors in place; drift/anomaly detection noted; data tests added.

**Do:** Define expectations (types, ranges, nullability, uniqueness, referential integrity); monitor freshness/volume; detect drift; keep audit trails; deduplicate explicitly.
**Anti-patterns:** Trusting source defaults; silent type coercion; deleting/overwriting without audit; ignoring missingness or spikes.
**Required artifacts/tests:** Validation suite/tests; threshold and alert plan; sample queries; drift/volume monitor note; audit/lineage entry.
**Example tasks:** Ingesting MLS feed; adding a new dataset/table; schema evolution; backfilling or reconciling anomalies.
