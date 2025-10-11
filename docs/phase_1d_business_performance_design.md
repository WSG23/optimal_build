# Phase 1D – Business Performance Management Design

_Last updated: 2025-10-11 (Codex)_

> **Implementation snapshot (2025-10-11):** Milestone M1 delivered – database schema, models, service layer, and deal CRUD/stage APIs are now in place with backend tests validating the workflow. Stage transitions emit `deal_stage_transition` audit ledger entries (deterministic UUID→int mapping) and timeline responses now include `duration_seconds`. Remaining milestones (commissions, analytics, benchmarks) are pending.

## 1. Objectives & Scope
- Deliver the four Phase 1D deliverables listed in `FEATURES.md`: Cross-Asset Deal Pipeline, ROI Analytics dashboard, Commission Protection system, and Performance Benchmarking.
- Provide a cohesive foundation that reuses existing Phase 1A–1C data (properties, projects, advisory outputs, listings) while remaining functional even if some upstream data is missing.
- Ensure all new events that could drive disputes (commission timestamps, stage changes) are audit-stamped using the existing `audit_logs` chain.

## 2. Data Model Additions
All new tables live under `backend/app/models/business_performance.py`.

### 2.1 Core tables
| Table | Purpose | Key Columns (all tables include `created_at`, `updated_at`) |
|-------|---------|-------------------------------------------------------------|
| `agent_deals` | Primary pipeline entity representing an opportunity/deal across any asset class. | `id (UUID PK)`, `project_id (FK→projects.id, nullable)`, `property_id (FK→properties.id, nullable)`, `agent_id (FK→users.id, required)`, `title`, `asset_type (Enum aligned with property.PropertyType plus “portfolio”)`, `deal_type (Enum: buy_side, sell_side, lease, management, other)`, `pipeline_stage (Enum)`, `status (Enum: open, closed_won, closed_lost, cancelled)`, `lead_source`, `estimated_value_amount (Numeric 16,2)`, `estimated_value_currency (String(3))`, `expected_close_date`, `actual_close_date`, `confidence (Numeric 4,2)`, `metadata (JSONB)` |
| `agent_deal_stage_events` | Immutable stage history enabling timeline views and SLA calculations. | `id`, `deal_id (FK)`, `from_stage (Enum, nullable)`, `to_stage (Enum)`, `changed_by (FK→users.id)`, `note (Text)`, `recorded_at (timezone aware)` |
| `agent_deal_contacts` | Counterparty/company contacts involved in a deal. | `id`, `deal_id`, `contact_type (Enum: principal, co_broke, legal, finance, other)`, `name`, `email`, `phone`, `company`, `notes` |
| `agent_deal_documents` | References to artefacts supporting the deal. Stored as metadata pointing to S3/Drive/etc. | `id`, `deal_id`, `document_type (Enum: loi, valuation, agreement, financials, other)`, `title`, `uri`, `mime_type`, `uploaded_by`, `uploaded_at`, `metadata` |

### 2.2 Commission & audit tables
| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `agent_commission_records` | Commission ledger per agent/deal with audit-stamped lifecycle. | `id`, `deal_id`, `agent_id`, `commission_type (Enum: introducer, exclusive, co_broke, referral, bonus)`, `basis_amount`, `basis_currency`, `commission_rate (Numeric 5,4)`, `commission_amount (Numeric 16,2, nullable until calculated)`, `status (Enum: pending, confirmed, invoiced, paid, disputed, written_off)`, `introduced_at (timestamp)`, `confirmed_at`, `invoiced_at`, `paid_at`, `disputed_at`, `resolved_at`, `audit_log_id (FK→audit_logs.id, nullable)` |
| `agent_commission_adjustments` | Track clawbacks/adjustments to keep the ledger auditable. | `id`, `commission_id`, `adjustment_type (Enum: clawback, bonus, correction)`, `amount`, `currency`, `note`, `recorded_by`, `recorded_at`, `audit_log_id` |

### 2.3 Analytics support tables
| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `agent_performance_snapshots` | Materialised daily snapshot powering dashboards; recalculated nightly. | `id`, `agent_id`, `as_of_date`, `deals_open`, `deals_closed_won`, `gross_pipeline_value`, `weighted_pipeline_value`, `avg_cycle_days`, `conversion_rate`, `roi_metrics (JSONB)` |
| `performance_benchmarks` | Industry reference metrics (imported from CSV/API). | `id`, `metric_key`, `asset_type`, `deal_type`, `cohort (Enum: industry_avg, top_quartile, internal_avg)`, `value_numeric`, `value_text`, `source`, `effective_date` |

### 2.4 Enumerations
- `PipelineStage`: `lead_captured`, `qualification`, `needs_analysis`, `proposal`, `negotiation`, `agreement`, `due_diligence`, `awaiting_closure`, `closed_won`, `closed_lost`.
- `DealStatus`: `open`, `closed_won`, `closed_lost`, `cancelled`.
- `DealType`: `buy_side`, `sell_side`, `lease`, `management`, `capital_raise`, `other`.
- `CommissionStatus`: `pending`, `confirmed`, `invoiced`, `paid`, `disputed`, `written_off`.
- `CommissionType`: `introducer`, `exclusive`, `co_broke`, `referral`, `bonus`.

Indices:
- `agent_deals`: composite index on `(agent_id, pipeline_stage)` for Kanban queries; `(project_id, status)` for reporting.
- `agent_deal_stage_events`: `(deal_id, recorded_at)` and `(to_stage, recorded_at DESC)` to quickly fetch recent transitions.
- `agent_commission_records`: `(agent_id, status)` and `(deal_id)` for lookups; optional unique constraint on `(deal_id, agent_id, commission_type)` to prevent duplicates.
- `agent_performance_snapshots`: unique `(agent_id, as_of_date)`.
- `performance_benchmarks`: composite `(metric_key, asset_type, cohort, effective_date DESC)`.

## 3. Backend Architecture

### 3.1 Services
- `app/services/deals/pipeline.py`: CRUD for `AgentDeal`, stage transition helpers that append `AgentDealStageEvent`, weighted pipeline calculations, and `timeline_with_audit()` to enrich stage history with hashed audit ledger entries.
- `app/services/deals/commission.py`: Commission ledger helper wrapping create/status/adjustment flows, each emitting audit log entries (`deal_commission_*` events).
- `app/services/deals/commission.py`: Commission lifecycle management; emits audit log events (`deal_commission_introduced`, `deal_commission_confirmed`, etc.) via the existing `audit_logs` chain.
- `app/services/deals/performance.py`: Aggregation routines to compute metrics per agent/property type; writes to `agent_performance_snapshots`.
- `app/services/deals/benchmark_ingest.py`: Loader for CSV/JSON benchmark data (invoked via Prefect or management CLI).

### 3.2 API routes (`backend/app/api/v1/deals.py`)
- `GET /api/v1/deals`: Paginated filter by agent, stage, property, search text.
- `POST /api/v1/deals`: Create a new deal.
- `PATCH /api/v1/deals/{deal_id}`: Update metadata, expected close, etc.
- `POST /api/v1/deals/{deal_id}/stage`: Transition stage (body contains `to_stage`, optional note). Internally records event + audit log (`deal_stage_transition`).
- `GET /api/v1/deals/{deal_id}/timeline`: Stage history + commission events aggregated for timeline display.
- `GET /api/v1/deals/{deal_id}/commissions`, `POST /api/v1/deals/{deal_id}/commissions`: Manage commission records.
- `POST /api/v1/commissions/{commission_id}/status`: Update status, optionally attach supporting doc reference; logs to audit.
- `GET /api/v1/performance/summary?agent_id=…&period=…`: Returns latest snapshot metrics plus ROI breakdown.
- `GET /api/v1/performance/benchmarks?asset_type=…`: Pulls benchmark entries filtered by asset type/cohort.

Authentication/authorization:
- Reuse existing `require_agent` / `require_viewer` dependencies (`app/api/deps.py`). Stage transitions and commission operations require write permissions.

### 3.3 Background jobs
- Nightly `compute_agent_performance_snapshots` (Prefect flow) to roll up per-agent metrics (conversion rate by property type, weighted pipeline, average cycle).
- Optional hourly job to recompute snapshots for active deals (Kanban performance numbers).
- Benchmark ingest job triggered manually or via scheduled fetch if remote source available.

### 3.4 Integration with Audit Log
- Every stage change writes an `AuditLog` row (`event_type="deal_stage_transition"`) with deterministic hash linking to previous entry for that project/deal; context includes IDs, stage, user.
- Commission lifecycle events log `event_type` such as `deal_commission_status_change` with the same chaining rules to satisfy audit requirements.
- Store `audit_log_id` on commission tables to allow direct traceability.

## 4. Frontend Plan
- **New route:** `/agents/performance` (or extend integrations page) containing two tabs: `Pipeline` (Kanban) and `Analytics`.
- **Pipeline Kanban (`PipelineBoard` component)**: Columns map to `PipelineStage`; cards display counterparty, asset type, estimated value, latest activity, and quick actions (move stage, log note). Initial implementation lives at `/agents/performance` with audit-aware timeline panel.
- **Deal detail drawer:** Shows timeline (stage events + commission history) with audit hash/signature badges, contact list, documents, manual adjustments.
- **Analytics dashboard:** charts using existing design-system components (bar charts, donut). Data sources: `/performance/summary` and `/performance/benchmarks`.
- **Commission dispute UI:** modal to mark commission as disputed, collects reason, optionally attaches doc (URI stored via `agent_deal_documents`).
- **State management:** use React Query hooks hitting new API layer functions (`frontend/src/api/deals.ts`). Align with patterns used in listing integrations.
- **Testing:** Add component tests for pipeline board interactions and API hook mocks; snapshot tests for analytics charts referencing known data.

## 5. Implementation Phasing
1. **Foundation (Milestone M1):** Migrations, models, basic CRUD service, API list/create/update, Kanban read-only view. Tests for models and pipeline service.
2. **Stage transitions & timeline (M2):** Stage event endpoints, audit logging, timeline API, Kanban drag/drop.
3. **Commission ledger (M3):** Commission models/services APIs, audit integration, dispute handling UI.
4. **Analytics & benchmarks (M4):** Snapshot job, performance API, dashboard charts, benchmark ingestion script + sample dataset.
   5. **Polish & docs (M5):** Update `feature_delivery_plan_v2.md`, add docs (`docs/agents/business_performance.md`), expand `TESTING_DOCUMENTATION_SUMMARY.md`.

### Milestone M4 design details

**Snapshot goals**

- Capture a daily roll-up of per-agent performance using the canonical metrics surfaced in the Agent Performance UI: open deal count, closed-won volume, weighted pipeline value (amount × confidence), average cycle duration, conversion rate, and ROI metadata (`roi_metrics` JSON for extensibility).
- Compute snapshots via a scheduled async job (Prefect/management command) that iterates over active deals, reusing `AgentDealService.list_deals` and the commission ledger to include revenue-impact metrics (e.g., confirmed commission total).

**Schema additions**

- Extend `agent_performance_snapshots` with the following columns:
  - `confirmed_commission_amount Numeric(16,2)`
  - `disputed_commission_amount Numeric(16,2)`
  - `snapshot_context JSONB` (storage for derived ratios, e.g., avg commission per won deal or pipeline coverage).
- Add supporting index `idx_agent_performance_snapshots_agent_date (agent_id, as_of_date DESC)` for fast latest snapshot queries.
- Create `performance_benchmarks` table (if not already present) seeded from static CSV import; columns include `metric_key`, `asset_type`, `deal_type`, `cohort`, `value_numeric`, `value_text`, `source`, `effective_date`.

**Service/API outline**

- New module `backend/app/services/deals/performance.py` with:
  - `compute_agent_snapshot(session, agent_id, as_of_date) -> AgentPerformanceSnapshot`
  - `generate_daily_snapshots(session, *, as_of_date=datetime.date)`, invoked by Prefect flow/CLI.
  - Helper to merge commission data (confirmed/disputed) and timeline durations (average lead-to-close).
- REST endpoints (FastAPI) under `/api/v1/deals/performance`:
  - `GET /api/v1/deals/performance/summary?agent_id=…` returning latest snapshot via new schema `AgentPerformanceSnapshotResponse`.
  - `GET /api/v1/deals/performance/benchmarks?metric_key=…,asset_type=…` returning filtered benchmark rows for charts.

**Analytics flow**

1. Daily job acquires active deal IDs, runs `compute_agent_snapshot`, persists to snapshot table (upsert on `(agent_id, as_of_date)`).
2. Commission data piped through `AgentCommissionService.list_commissions` to aggregate confirmed/disputed totals and compute pay-out velocity metrics.
3. Frontend dashboard (next milestone) reads `/summary` + `/benchmarks` to render trend lines (sparkline over previous 30 days), donut chart by stage, and benchmark comparisons.

**Testing plan**

- Unit tests for `compute_agent_snapshot` using fixture deals/commissions exercising various lifecycle combinations (open only, mixture of closed stages, disputed commissions).
- API tests verifying `/performance/summary` returns latest snapshot, respects agent filtering, and merges ROI metrics from the legacy `roi` service when available.
- Snapshot job integration test using in-memory SQLite to ensure idempotent upsert and accurate index usage.

## 6. Testing & Observability
- **Backend tests:** Model integrity, service logic, API routers (FastAPI TestClient), Prefect flow unit tests guarded by feature flag.
- **Frontend tests:** React Testing Library for Kanban interactions, chart rendering sanity with mock data, regression test for dispute flow.
- **Data validation:** DB constraints and SQLAlchemy validators ensure enums/decimals valid; nightly job adds summary logs to `jobs_registry`.
- **Metrics:** Extend existing logging to emit structured events when snapshot job runs (duration, number of deals processed).

## 7. Open Questions / Assumptions
- Benchmark source: assume initial CSV manual load; revisit once official dataset available.
- Document storage: current system stores URIs only; out of scope to implement file upload service now.
- Multi-agent deals: design supports multiple commission records per deal; assume a single primary agent per deal for now; revisit if team-based workflows needed.
- Currency handling: default to SGD but keep column configurable; conversions/FX out of scope for Phase 1D.

Once approved, proceed with Milestone M1 (deal pipeline foundation) as the first implementation task.
