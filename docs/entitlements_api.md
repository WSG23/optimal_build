# Entitlements API

The Entitlements API tracks approvals, technical studies, stakeholder
engagement, and legal instruments associated with a project’s entitlement
process. After running the Singapore seeder
(`python scripts/seed_entitlements_sg.py --project-id 90301 --reset`) the API
exposes the following resources under `/api/v1/entitlements/{project_id}`:

## Roadmap

* `GET /roadmap` – returns ordered roadmap items. Supports `limit` and `offset`
  pagination parameters. Each item includes target/actual submission and
  decision dates plus reviewer notes.
* `POST /roadmap` – create a roadmap item. Reviewer or admin role required via
  `X-Role` header.
* `PUT /roadmap/{item_id}` – update roadmap status, sequencing, or metadata.
* `DELETE /roadmap/{item_id}` – remove a roadmap entry and resequence the
  remaining items.

## Studies

* `GET /studies` – list environmental, traffic, heritage, and other study
  requirements. Supports pagination.
* `POST /studies` – create a study record with optional consultant, due date,
  and attachment links (requires reviewer/admin role).
* `PUT /studies/{study_id}` – update status or metadata.
* `DELETE /studies/{study_id}` – remove a study record.

## Stakeholders

* `GET /stakeholders` – list stakeholder engagement records including contact
  details and notes.
* `POST /stakeholders` – add a stakeholder engagement (reviewer/admin role).
* `PUT /stakeholders/{engagement_id}` – update engagement status or notes.
* `DELETE /stakeholders/{engagement_id}` – delete an engagement record.

## Legal instruments

* `GET /legal` – list memoranda, agreements, waivers, and other legal
  instruments tied to entitlements.
* `POST /legal` – create a legal instrument with reference codes, effective and
  expiry dates, and attachments (reviewer/admin role).
* `PUT /legal/{instrument_id}` – update status or metadata.
* `DELETE /legal/{instrument_id}` – delete a legal instrument record.

## Export

`GET /export?format={csv|html|pdf}` streams a combined report covering roadmap,
studies, stakeholders, and legal registers. When the optional HTML-to-PDF
dependency is unavailable, the service falls back to HTML output.

## Metrics

Prometheus counters named `entitlements_*_requests_total` track per-endpoint
activity and are exposed via `/health/metrics`.
