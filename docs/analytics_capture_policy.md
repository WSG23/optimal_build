# Analytics Capture Retention And Access Policy

## Scope

The analytics capture layer stores operational event envelopes, external API call payloads, status transitions, entity lifecycle events, and raw artifact metadata. It is append-only by default so future analytics, audits, replay, and model-training work can inspect what the system actually saw.

## Defaults

- Store raw JSON payloads broadly, but redact secrets before persistence.
- Keep API keys, passwords, cookies, authorization headers, refresh tokens, access tokens, and similarly named fields out of plaintext storage.
- Keep stable hashes for redacted values when correlation is useful.
- Keep large binary payloads out of hot capture rows. Store checksum, byte size, MIME type, source, URI/storage key, and linked entity/request metadata in `raw_artifacts`.
- Keep oversized JSON payloads out of hot capture rows. `ANALYTICS_CAPTURE_MAX_JSON_BYTES` defaults to 256 KiB; larger payloads are replaced by a bounded preview plus `sha256`, original byte size, and truncation reason.
- Keep capture previews small. `ANALYTICS_CAPTURE_PREVIEW_BYTES` defaults to 4 KiB.
- Treat capture rows as production data. They may include user-generated content and third-party payloads.

## Retention

- `data_capture_events`: retain 18 months online by default.
- `external_api_calls`: retain 18 months online by default; retain failures and non-2xx responses for 24 months where contract/debugging value is high.
- `status_transitions`: retain indefinitely unless legal deletion is required.
- `entity_lifecycle_events`: retain indefinitely unless legal deletion is required.
- `raw_artifacts`: retain metadata indefinitely; retain large payload objects according to source-specific policy.

Retention jobs should archive before delete where possible. Hard deletion should leave an aggregate retention tombstone so analytics can distinguish "never captured" from "captured then expired."

## Access

- Default query access should be limited to engineering, data, security, and explicitly approved product analytics roles.
- Raw payload columns require a higher-privilege role than promoted filter columns.
- Production support access should be request-scoped and time-limited.
- Exports containing raw payloads should be logged and tied to a ticket, incident, or approved analysis request.

## Observability

- Capture write failures increment `analytics_capture_failures_total` with `source`, `table`, and `mode` labels.
- Production Prometheus loads `AnalyticsCaptureFailures`, which pages the data/platform owner on sustained non-zero failure rates.
- Capture failures should not mask the primary user workflow unless the environment is configured for strict test behavior.

## CI And Completeness Guardrails

- CI runs `backend/scripts/prove_analytics_capture_paths.py` against Postgres after migrations and fails if representative capture tables do not receive new rows.
- `backend/scripts/audit_analytics_write_surfaces.py` inventories mutating DB callsites, capture helper usage, and background task scheduling so lower-priority write surfaces stay reviewable.
- The write-surface audit is intentionally an inventory guardrail, not a replacement for product judgment. Seed/reference ingestion scripts and read-model refreshers may remain normalized-only when raw source artifacts are already stored or reproducible.

## Security Review Triggers

- Database encryption at rest is required for production. Add application-layer encryption before storing regulated identifiers, payment data, health data, or provider payloads whose terms require field-level encryption.
- Tenant-specific retention overrides are not enabled by default. Add them before selling contractual retention terms that differ from this policy.
- Third-party provider terms override these defaults. Add field-level suppression or shorter retention when a provider contract requires it.
- Break-glass workflow is required before broad production raw-payload access is granted outside engineering, data, security, or approved product analytics roles.
