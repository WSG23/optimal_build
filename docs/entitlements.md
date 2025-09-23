# Entitlements API

The entitlements module models the core milestones required to secure planning
approval for a project. Six resource families are available:

* **Authorities** and **approval types** describe Singapore agencies and their
  typical submissions. These are seeded via
  `python -m scripts.seed_entitlements_sg` and exposed in exports.
* **Roadmap items** represent the sequenced entitlement plan for a project.
* **Studies**, **stakeholder engagements**, and **legal instruments** capture
  supporting artefacts collected along the way.

## API overview

All endpoints are served under `/api/v1/entitlements` and require the
`X-User-Roles` header for RBAC. Supply `viewer` to access read endpoints and
`reviewer` or `admin` to mutate records.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/roadmap/{project_id}` | GET | List roadmap milestones with `limit` and `offset` pagination. |
| `/roadmap/{project_id}` | POST | Create a roadmap item. Optional `sequence` values insert before existing items. |
| `/roadmap/{project_id}/{item_id}` | PUT | Update status, sequence, metadata, and attachments. |
| `/roadmap/{project_id}/{item_id}` | DELETE | Remove a roadmap entry and resequence remaining items. |
| `/studies/{project_id}` | GET/POST/PUT/DELETE | Manage consultant or authority studies feeding the entitlement package. |
| `/stakeholders/{project_id}` | GET/POST/PUT/DELETE | Track agency and community engagements. |
| `/legal/{project_id}` | GET/POST/PUT/DELETE | Record legal instruments agreed during the process. |
| `/export/{project_id}` | GET | Render CSV, HTML, or PDF summaries (`fmt` query parameter). When PDF support is missing the API returns HTML with an `X-Export-Fallback: html` header. |

The Prometheus metrics at `/health/metrics` expose
`entitlements_requests_total{resource,method}` counters for observability and
`entitlements_exports_total{format,fallback}` for export tracking.

## Export formats

The CSV export contains section headers for each resource family. HTML exports
ship with a compact dark theme suitable for browser review. PDF exports reuse
the HTML rendering and require a local PDF renderer (WeasyPrint or pdfkit). When
no renderer is available the HTML payload is returned instead.

## Seeding and verification

1. Apply migrations: `cd backend && alembic upgrade head`.
2. Seed the defaults: `python -m scripts.seed_entitlements_sg 101`.
3. Hit `GET /api/v1/entitlements/roadmap/101` with `X-User-Roles: viewer` to
   verify the roadmap sequence.
4. Use `POST /api/v1/entitlements/roadmap/101` with `X-User-Roles: reviewer` to
   append milestones and observe sequence renumbering.
5. Call `GET /api/v1/entitlements/export/101?fmt=html` to download a report.

The admin dashboard exposes these resources under the new **Entitlements** tab,
offering quick visibility into roadmap status, supporting studies, stakeholder
conversations, and legal agreements.
