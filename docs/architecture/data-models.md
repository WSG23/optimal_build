# Optimal Build - Complete Data Models Reference

> **Comprehensive database schema** documenting all 20+ tables in the optimal_build system

**Last Updated:** 2025-11-11

---

## Table of Contents

1. [Core Tables](#core-tables) - Users, Projects, Properties
2. [Finance Tables](#finance-tables) - Financial modeling and scenarios
3. [Business Performance Tables](#business-performance-tables) - Deal pipeline and agent performance
4. [Developer Tools Tables](#developer-tools-tables) - Preview generation, checklists, conditions
5. [Entitlements Tables](#entitlements-tables) - Approvals, roadmap, risks
6. [Overlay Tables](#overlay-tables) - Heritage and regulatory overlays
7. [Market Data Tables](#market-data-tables) - Yield benchmarks, absorption tracking
8. [Supporting Tables](#supporting-tables) - Audit logs, AI agents, listings

---

## Core Tables

### users
**Purpose:** User authentication & management

| Column | Type | Description |
|--------|------|-------------|
| id | UUID (PK) | Primary key |
| email | String | Unique email address |
| username | String | Unique username |
| hashed_password | String | Bcrypt hashed password |
| full_name | String | User's full name |
| company_name | String | Optional company name |
| uen_number | String | Singapore company identifier (optional) |
| phone_number | String | Contact phone number |
| role | Enum | admin/user/developer/consultant |
| is_active | Boolean | Account enabled (default: true) |
| is_verified | Boolean | Email verified (default: false) |
| last_login | DateTime | Last login timestamp |
| created_at | DateTime | Account creation timestamp |
| updated_at | DateTime | Last update timestamp |

**Indexes:**
- `ix_users_email` (unique)
- `ix_users_username` (unique)
- `ix_users_role`

---

### projects
**Purpose:** Development projects (70+ columns)

| Column | Type | Description |
|--------|------|-------------|
| id | UUID (PK) | Primary key |
| name | String | Project name |
| description | Text | Project description |
| project_type | Enum | residential/commercial/industrial/mixed |
| project_phase | Enum | planning/approval/construction/completed |
| approval_status | Enum | pending/approved/rejected |
| location | String | Location address |
| latitude | Float | GPS coordinate |
| longitude | Float | GPS coordinate |
| budget | Float | Total budget |
| estimated_cost | Float | Estimated development cost |
| actual_cost | Float | Actual cost incurred |
| start_date | Date | Project start date |
| completion_date | Date | Expected completion date |
| owner_id | UUID (FK) | Foreign key → users.id |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last update timestamp |
| is_active | Boolean | Project active status |

**Note:** Full schema includes 70+ columns covering site metrics, planning parameters, financial metrics, etc. See [backend/app/models/project.py](../../backend/app/models/project.py) for complete schema.

**Indexes:**
- `ix_projects_owner_id`
- `ix_projects_project_type`
- `ix_projects_project_phase`
- `ix_projects_created_at`

**Unique Constraints:**
- `uq_projects_project_code` (project_code)

---

### properties
**Purpose:** Property data (linked to projects)

| Column | Type | Description |
|--------|------|-------------|
| id | UUID (PK) | Primary key |
| project_id | UUID (FK) | Foreign key → projects.id (optional) |
| address | String | Property address |
| latitude | Float | GPS coordinate |
| longitude | Float | GPS coordinate |
| property_type | Enum | office/retail/industrial/residential/mixed_use/hotel/warehouse/land |
| land_area | Float | Land area in sqm |
| gfa | Float | Gross Floor Area |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last update timestamp |

**Indexes:**
- `ix_properties_project_id`
- `ix_properties_property_type`

---

### singapore_properties
**Purpose:** Singapore regulatory data

| Column | Type | Description |
|--------|------|-------------|
| id | UUID (PK) | Primary key |
| project_id | UUID (FK) | Foreign key → projects.id |
| land_area | Float | Land area in sqm |
| gfa | Float | Gross Floor Area |
| gfa_approved | Float | Approved GFA |
| plot_ratio | Float | Plot ratio |
| site_coverage | Float | Site coverage percentage |
| building_height | Float | Building height in meters |
| storeys | Integer | Number of storeys |
| zoning | String | URA zoning type |
| land_use | String | Land use classification |
| tenure | Enum | freehold/99-year/60-year/30-year |
| region | String | Planning region |
| district | Integer | District number (1-28) |
| mukim | String | Mukim lot number |
| lot_number | String | Lot number |
| lease_start_date | Date | Lease start date |
| lease_end_date | Date | Lease end date |
| ura_approval_status | String | URA approval status |
| ura_approval_date | Date | URA approval date |
| bca_approval_status | String | BCA approval status |
| bca_approval_date | Date | BCA approval date |
| bca_submission_number | String | BCA submission number |
| green_mark_rating | String | Green Mark certification |
| accessibility_rating | String | Accessibility rating |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last update timestamp |

**Indexes:**
- `ix_singapore_properties_project_id`
- `ix_singapore_properties_district`

---

## Finance Tables

### fin_projects
**Purpose:** Finance workspace seeded for a project

| Column | Type | Description |
|--------|------|-------------|
| id | Integer (PK) | Primary key |
| project_id | UUID (FK) | Foreign key → projects.id |
| name | String(120) | Finance project name |
| currency | String(3) | Currency code (default: USD) |
| discount_rate | Numeric(5,4) | Discount rate for NPV |
| total_development_cost | Numeric(16,2) | Total development cost |
| total_gross_profit | Numeric(16,2) | Total gross profit |
| metadata | JSONB | Additional metadata |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last update timestamp |

**Relationships:**
- `scenarios` → fin_scenarios (one-to-many, cascade delete)

**Indexes:**
- `ix_fin_projects_project_id`
- `idx_fin_projects_project_name` (composite: project_id, name)
- `ix_fin_projects_created_at`

---

### fin_scenarios
**Purpose:** Scenario-specific underwriting assumptions

| Column | Type | Description |
|--------|------|-------------|
| id | Integer (PK) | Primary key |
| project_id | UUID (FK) | Foreign key → projects.id |
| fin_project_id | Integer (FK) | Foreign key → fin_projects.id |
| name | String(120) | Scenario name |
| description | Text | Scenario description |
| assumptions | JSONB | Financial assumptions |
| is_primary | Boolean | Primary scenario flag |
| is_private | Boolean | Private scenario flag |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last update timestamp |

**Relationships:**
- `fin_project` → fin_projects (many-to-one)
- `results` → fin_results (one-to-many, cascade delete)
- `capital_stacks` → fin_capital_stacks (one-to-many, cascade delete)
- `drawdowns` → fin_drawdowns (one-to-many, cascade delete)
- `asset_breakdowns` → fin_asset_breakdowns (one-to-many, cascade delete)

**Indexes:**
- `ix_fin_scenarios_project_id`
- `ix_fin_scenarios_fin_project_id`
- `ix_fin_scenarios_is_primary`
- `ix_fin_scenarios_is_private`
- `ix_fin_scenarios_created_at`

---

### fin_results
**Purpose:** Finance calculation results

| Column | Type | Description |
|--------|------|-------------|
| id | Integer (PK) | Primary key |
| scenario_id | Integer (FK) | Foreign key → fin_scenarios.id |
| npv | Numeric(16,2) | Net Present Value |
| irr | Numeric(5,4) | Internal Rate of Return |
| total_revenue | Numeric(16,2) | Total revenue |
| total_costs | Numeric(16,2) | Total costs |
| gross_profit | Numeric(16,2) | Gross profit |
| profit_margin | Numeric(5,4) | Profit margin percentage |
| sensitivity_data | JSONB | Sensitivity analysis data |
| created_at | DateTime | Calculation timestamp |

**Indexes:**
- `ix_fin_results_scenario_id`
- `ix_fin_results_created_at`

---

### fin_capital_stacks
**Purpose:** Capital stack configurations

| Column | Type | Description |
|--------|------|-------------|
| id | Integer (PK) | Primary key |
| scenario_id | Integer (FK) | Foreign key → fin_scenarios.id |
| layer_name | String(100) | Capital layer name (e.g., "Senior Debt") |
| layer_order | Integer | Stacking order |
| amount | Numeric(16,2) | Layer amount |
| rate | Numeric(5,4) | Interest/return rate |
| term_months | Integer | Term in months |
| notes | Text | Additional notes |

**Indexes:**
- `ix_fin_capital_stacks_scenario_id`

---

### fin_drawdowns
**Purpose:** Capital drawdown schedule

| Column | Type | Description |
|--------|------|-------------|
| id | Integer (PK) | Primary key |
| scenario_id | Integer (FK) | Foreign key → fin_scenarios.id |
| period | Integer | Period number |
| amount | Numeric(16,2) | Drawdown amount |
| cumulative | Numeric(16,2) | Cumulative drawdown |
| created_at | DateTime | Creation timestamp |

**Indexes:**
- `ix_fin_drawdowns_scenario_id`

---

### fin_asset_breakdowns
**Purpose:** Per-asset finance breakdowns

| Column | Type | Description |
|--------|------|-------------|
| id | Integer (PK) | Primary key |
| scenario_id | Integer (FK) | Foreign key → fin_scenarios.id |
| asset_type | String(50) | Asset type (office/retail/residential/etc) |
| nia | Numeric(12,2) | Net Internal Area (sqm) |
| revenue | Numeric(16,2) | Revenue from asset |
| costs | Numeric(16,2) | Costs for asset |
| profit | Numeric(16,2) | Profit from asset |
| created_at | DateTime | Creation timestamp |

**Indexes:**
- `ix_fin_asset_breakdowns_scenario_id`

---

## Business Performance Tables

### agent_deals
**Purpose:** Deal pipeline tracking

| Column | Type | Description |
|--------|------|-------------|
| id | UUID (PK) | Primary key |
| agent_id | UUID (FK) | Foreign key → users.id (agent owner) |
| deal_name | String(200) | Deal name |
| deal_type | Enum | buy_side/sell_side/lease/management/capital_raise/other |
| asset_type | Enum | office/retail/industrial/residential/mixed_use/hotel/warehouse/land/special_purpose/portfolio |
| pipeline_stage | Enum | lead_captured/qualification/needs_analysis/proposal/negotiation/agreement/due_diligence/awaiting_closure/closed_won/closed_lost |
| deal_status | Enum | open/closed_won/closed_lost/cancelled |
| property_id | UUID (FK) | Foreign key → properties.id (optional) |
| expected_value | Numeric(16,2) | Expected deal value |
| probability | Numeric(3,2) | Win probability (0-1) |
| expected_close_date | Date | Expected closing date |
| actual_close_date | Date | Actual closing date |
| notes | Text | Deal notes |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last update timestamp |

**Relationships:**
- `stage_events` → agent_deal_stage_events (one-to-many, cascade delete)
- `contacts` → agent_deal_contacts (one-to-many, cascade delete)
- `documents` → agent_deal_documents (one-to-many, cascade delete)
- `commissions` → agent_commission_records (one-to-many, cascade delete)

**Indexes:**
- `ix_agent_deals_agent_id`
- `ix_agent_deals_property_id`
- `ix_agent_deals_deal_status`
- `ix_agent_deals_pipeline_stage`
- `ix_agent_deals_expected_close_date`
- `ix_agent_deals_created_at`

---

### agent_deal_stage_events
**Purpose:** Stage transition history

| Column | Type | Description |
|--------|------|-------------|
| id | UUID (PK) | Primary key |
| deal_id | UUID (FK) | Foreign key → agent_deals.id |
| from_stage | Enum | Previous pipeline stage |
| to_stage | Enum | New pipeline stage |
| transition_date | DateTime | Transition timestamp |
| notes | Text | Transition notes |

**Indexes:**
- `ix_agent_deal_stage_events_deal_id`
- `ix_agent_deal_stage_events_transition_date`

---

### agent_deal_contacts
**Purpose:** Deal contact information

| Column | Type | Description |
|--------|------|-------------|
| id | UUID (PK) | Primary key |
| deal_id | UUID (FK) | Foreign key → agent_deals.id |
| contact_type | Enum | principal/co_broke/legal/finance/other |
| name | String(200) | Contact name |
| email | String(255) | Contact email |
| phone | String(50) | Contact phone |
| company | String(200) | Contact company |

**Indexes:**
- `ix_agent_deal_contacts_deal_id`

---

### agent_deal_documents
**Purpose:** Deal document references

| Column | Type | Description |
|--------|------|-------------|
| id | UUID (PK) | Primary key |
| deal_id | UUID (FK) | Foreign key → agent_deals.id |
| document_type | Enum | loi/valuation/due_diligence/contract/closing/other |
| document_url | String(500) | Document URL/path |
| uploaded_at | DateTime | Upload timestamp |

**Indexes:**
- `ix_agent_deal_documents_deal_id`

---

### agent_commission_records
**Purpose:** Commission ledger

| Column | Type | Description |
|--------|------|-------------|
| id | UUID (PK) | Primary key |
| deal_id | UUID (FK) | Foreign key → agent_deals.id |
| agent_id | UUID (FK) | Foreign key → users.id |
| commission_amount | Numeric(16,2) | Commission amount |
| commission_percentage | Numeric(5,4) | Commission percentage |
| payment_status | Enum | pending/paid/cancelled |
| payment_date | Date | Payment date |

**Indexes:**
- `ix_agent_commission_records_deal_id`
- `ix_agent_commission_records_agent_id`

---

### agent_performance_snapshots
**Purpose:** Agent performance metrics (time-series)

| Column | Type | Description |
|--------|------|-------------|
| id | UUID (PK) | Primary key |
| agent_id | UUID (FK) | Foreign key → users.id |
| snapshot_date | Date | Snapshot date |
| total_deals | Integer | Total deals count |
| deals_won | Integer | Won deals count |
| deals_lost | Integer | Lost deals count |
| pipeline_value | Numeric(16,2) | Total pipeline value |
| commissions_earned | Numeric(16,2) | Commissions earned |

**Indexes:**
- `ix_agent_performance_snapshots_agent_id`
- `ix_agent_performance_snapshots_snapshot_date`

---

## Developer Tools Tables

### preview_jobs
**Purpose:** 3D preview generation jobs

| Column | Type | Description |
|--------|------|-------------|
| id | UUID (PK) | Primary key |
| property_id | UUID (FK) | Foreign key → properties.id |
| scenario | String(80) | Scenario name (default: "base") |
| status | Enum | queued/processing/ready/failed/expired |
| requested_at | DateTime | Job request timestamp |
| started_at | DateTime | Job start timestamp |
| finished_at | DateTime | Job completion timestamp |
| error_message | Text | Error details (if failed) |
| gltf_url | String(500) | GLTF asset URL |
| thumbnail_url | String(500) | Thumbnail PNG URL |
| metadata_url | String(500) | Metadata JSON URL |
| asset_version | String(100) | Asset version identifier |

**Indexes:**
- `ix_preview_jobs_property_id`
- `ix_preview_jobs_status`
- `ix_preview_jobs_requested_at`

---

### developer_checklist_templates
**Purpose:** Developer checklist templates

| Column | Type | Description |
|--------|------|-------------|
| id | UUID (PK) | Primary key |
| name | String(200) | Template name |
| description | Text | Template description |
| category | String(100) | Category (e.g., "Due Diligence") |
| checklist_items | JSONB | Array of checklist items |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last update timestamp |

**Indexes:**
- `ix_developer_checklist_templates_category`

---

### developer_checklist_instances
**Purpose:** Developer checklist instances

| Column | Type | Description |
|--------|------|-------------|
| id | UUID (PK) | Primary key |
| template_id | UUID (FK) | Foreign key → developer_checklist_templates.id |
| property_id | UUID (FK) | Foreign key → properties.id |
| checklist_data | JSONB | Checklist state and responses |
| completion_percentage | Numeric(5,2) | Completion percentage |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last update timestamp |

**Indexes:**
- `ix_developer_checklist_instances_template_id`
- `ix_developer_checklist_instances_property_id`

---

### developer_conditions
**Purpose:** Developer conditions and requirements

| Column | Type | Description |
|--------|------|-------------|
| id | UUID (PK) | Primary key |
| property_id | UUID (FK) | Foreign key → properties.id |
| condition_type | String(100) | Condition type |
| description | Text | Condition description |
| status | Enum | pending/met/failed |
| due_date | Date | Due date |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last update timestamp |

**Indexes:**
- `ix_developer_conditions_property_id`
- `ix_developer_conditions_status`

---

## Entitlements Tables

### ent_roadmap
**Purpose:** Entitlements roadmap

| Column | Type | Description |
|--------|------|-------------|
| id | Integer (PK) | Primary key |
| project_id | UUID (FK) | Foreign key → projects.id |
| approval_category | Enum | planning/building/environmental/transport/utilities |
| roadmap_status | Enum | not_started/in_progress/submitted/approved/rejected |
| milestone_name | String(200) | Milestone name |
| target_date | Date | Target completion date |
| actual_date | Date | Actual completion date |
| notes | Text | Additional notes |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last update timestamp |

**Indexes:**
- `ix_ent_roadmap_project_id`
- `ix_ent_roadmap_roadmap_status`
- `ix_ent_roadmap_target_date`

---

### ent_risks
**Purpose:** Entitlement risks

| Column | Type | Description |
|--------|------|-------------|
| id | Integer (PK) | Primary key |
| project_id | UUID (FK) | Foreign key → projects.id |
| risk_category | String(100) | Risk category |
| risk_description | Text | Risk description |
| probability | Enum | low/medium/high |
| impact | Enum | low/medium/high |
| mitigation_plan | Text | Mitigation strategy |
| status | Enum | open/mitigated/closed |

**Indexes:**
- `ix_ent_risks_project_id`
- `ix_ent_risks_status`

---

## Overlay Tables

### overlay_source_geometries
**Purpose:** Stored canonical geometry inputs per project

| Column | Type | Description |
|--------|------|-------------|
| id | Integer (PK) | Primary key |
| project_id | Integer | Project ID |
| source_geometry_key | String(100) | Geometry identifier |
| graph | JSONB | Geometry graph data |
| metadata | JSONB | Additional metadata |
| checksum | String(64) | Geometry checksum |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last update timestamp |

**Relationships:**
- `suggestions` → overlay_suggestions (one-to-many, cascade delete)
- `decisions` → overlay_decisions (one-to-many, cascade delete)

**Indexes:**
- `ix_overlay_source_geometries_project_id`
- `ix_overlay_source_geometries_checksum`
- `ix_overlay_source_geometries_created_at`

---

### overlay_suggestions
**Purpose:** Overlay evaluation suggestions

| Column | Type | Description |
|--------|------|-------------|
| id | Integer (PK) | Primary key |
| source_geometry_id | Integer (FK) | Foreign key → overlay_source_geometries.id |
| overlay_type | String(100) | Overlay type (heritage/conservation/etc) |
| confidence_score | Float | Confidence score (0-1) |
| suggestion_data | JSONB | Suggestion details |
| created_at | DateTime | Creation timestamp |

**Indexes:**
- `ix_overlay_suggestions_source_geometry_id`

---

### overlay_decisions
**Purpose:** User decisions on overlay suggestions

| Column | Type | Description |
|--------|------|-------------|
| id | Integer (PK) | Primary key |
| source_geometry_id | Integer (FK) | Foreign key → overlay_source_geometries.id |
| suggestion_id | Integer (FK) | Foreign key → overlay_suggestions.id |
| decision | Enum | accepted/rejected/pending |
| decision_reason | Text | Decision rationale |
| decided_by | UUID (FK) | Foreign key → users.id |
| decided_at | DateTime | Decision timestamp |

**Indexes:**
- `ix_overlay_decisions_source_geometry_id`
- `ix_overlay_decisions_suggestion_id`
- `ix_overlay_decisions_decided_by`

---

## Market Data Tables

### yield_benchmarks
**Purpose:** Market yield benchmarks by property type and location

| Column | Type | Description |
|--------|------|-------------|
| id | UUID (PK) | Primary key |
| benchmark_date | Date | Benchmark date |
| period_type | String(20) | monthly/quarterly/yearly |
| country | String(50) | Country (default: Singapore) |
| district | String(100) | District |
| subzone | String(100) | Subzone |
| location_tier | String(20) | prime/secondary/suburban |
| property_type | Enum | office/retail/industrial/residential/etc |
| property_grade | String(20) | A/B/C grade |
| cap_rate_mean | Numeric(5,3) | Mean cap rate |
| cap_rate_median | Numeric(5,3) | Median cap rate |
| cap_rate_p25 | Numeric(5,3) | 25th percentile cap rate |
| cap_rate_p75 | Numeric(5,3) | 75th percentile cap rate |
| rental_yield_mean | Numeric(5,3) | Mean rental yield |
| rental_psf_mean | Numeric(8,2) | Mean rental PSF |
| occupancy_rate_mean | Numeric(5,2) | Mean occupancy rate |
| transaction_count | Integer | Number of transactions |
| sample_size | Integer | Sample size |
| data_quality_score | Numeric(3,2) | Data quality score (0-1) |

**Indexes:**
- `ix_yield_benchmarks_benchmark_date`
- `ix_yield_benchmarks_property_type`
- `ix_yield_benchmarks_district`

---

### absorption_tracking
**Purpose:** Absorption rate tracking

| Column | Type | Description |
|--------|------|-------------|
| id | UUID (PK) | Primary key |
| tracking_date | Date | Tracking date |
| property_type | Enum | Property type |
| district | String(100) | District |
| units_available | Integer | Units available |
| units_absorbed | Integer | Units absorbed |
| absorption_rate | Numeric(5,4) | Absorption rate |

**Indexes:**
- `ix_absorption_tracking_tracking_date`
- `ix_absorption_tracking_property_type`

---

## Supporting Tables

### audit_logs
**Purpose:** Recorded metrics emitted by automation workflows

| Column | Type | Description |
|--------|------|-------------|
| id | Integer (PK) | Primary key |
| project_id | Integer | Project ID |
| event_type | String(50) | Event type |
| version | Integer | Log version |
| baseline_seconds | Float | Baseline duration |
| actual_seconds | Float | Actual duration |
| context | JSONB | Event context |
| hash | String(64) | Event hash |
| prev_hash | String(64) | Previous hash (chain) |
| signature | String(128) | Event signature |
| recorded_at | DateTime | Recording timestamp |

**Indexes:**
- `ix_audit_logs_project_id`
- `ix_audit_logs_event_type`
- `ix_audit_logs_version`
- `ix_audit_logs_hash`
- `ix_audit_logs_recorded_at`
- `idx_audit_logs_project_event` (composite: project_id, event_type)
- `idx_audit_logs_project_version` (composite: project_id, version)

**Unique Constraints:**
- `uq_audit_logs_project_version` (project_id, version)

---

### ai_agents
**Purpose:** AI assistant configurations

| Column | Type | Description |
|--------|------|-------------|
| id | UUID (PK) | Primary key |
| name | String | Agent name |
| agent_type | Enum | compliance/cost_estimator/design/analysis |
| description | Text | Agent description |
| capabilities | JSONB | List of capabilities |
| configuration | JSONB | Agent-specific settings |
| model_version | String | AI model version |
| is_active | Boolean | Agent enabled status |
| created_by | UUID (FK) | Foreign key → users.id |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last update timestamp |

**Relationships:**
- `sessions` → ai_agent_sessions (one-to-many, cascade delete)

**Indexes:**
- `ix_ai_agents_agent_type`
- `ix_ai_agents_is_active`
- `ix_ai_agents_created_by`

---

### ai_agent_sessions
**Purpose:** AI interaction history

| Column | Type | Description |
|--------|------|-------------|
| id | UUID (PK) | Primary key |
| agent_id | UUID (FK) | Foreign key → ai_agents.id |
| user_id | UUID (FK) | Foreign key → users.id |
| project_id | UUID (FK) | Foreign key → projects.id (optional) |
| session_start | DateTime | Session start timestamp |
| session_end | DateTime | Session end timestamp |
| messages | JSONB | Conversation history |
| context | JSONB | Session context |
| recommendations | JSONB | AI recommendations |
| analysis_results | JSONB | Analysis output |
| feedback_rating | Integer | User rating (1-5) |
| feedback_text | Text | User feedback |
| created_at | DateTime | Creation timestamp |

**Indexes:**
- `ix_ai_agent_sessions_agent_id`
- `ix_ai_agent_sessions_user_id`
- `ix_ai_agent_sessions_project_id`
- `ix_ai_agent_sessions_session_start`

---

### listing_integration_configs
**Purpose:** External listing service configurations

| Column | Type | Description |
|--------|------|-------------|
| id | UUID (PK) | Primary key |
| service_name | String(100) | Service name (e.g., "PropertyGuru") |
| api_endpoint | String(500) | API endpoint URL |
| api_key_encrypted | String(500) | Encrypted API key |
| is_active | Boolean | Configuration enabled |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last update timestamp |

---

## Entity Relationships

```
users
  ├──< projects (owner_id)
  ├──< ai_agents (created_by)
  ├──< ai_agent_sessions (user_id)
  ├──< agent_deals (agent_id)
  └──< overlay_decisions (decided_by)

projects
  ├──── singapore_properties (project_id, 1:1)
  ├──< fin_projects (project_id)
  ├──< fin_scenarios (project_id)
  ├──< ent_roadmap (project_id)
  ├──< ent_risks (project_id)
  └──< overlay_source_geometries (project_id)

properties
  ├──< preview_jobs (property_id)
  ├──< developer_checklist_instances (property_id)
  ├──< developer_conditions (property_id)
  └──< agent_deals (property_id, optional)

fin_projects
  └──< fin_scenarios (fin_project_id)

fin_scenarios
  ├──< fin_results (scenario_id)
  ├──< fin_capital_stacks (scenario_id)
  ├──< fin_drawdowns (scenario_id)
  └──< fin_asset_breakdowns (scenario_id)

agent_deals
  ├──< agent_deal_stage_events (deal_id)
  ├──< agent_deal_contacts (deal_id)
  ├──< agent_deal_documents (deal_id)
  └──< agent_commission_records (deal_id)

ai_agents
  └──< ai_agent_sessions (agent_id)

overlay_source_geometries
  ├──< overlay_suggestions (source_geometry_id)
  └──< overlay_decisions (source_geometry_id)
```

---

## Notes

**ENUM Types:**
- All ENUM columns use `sa.String()` in migrations (per [CODING_RULES.md Rule 1.2](../../CODING_RULES.md#12-postgresql-enum-types-in-migrations))
- ENUM values are cast to PostgreSQL ENUM types using `ALTER TABLE ... ALTER COLUMN ... TYPE <enum_type> USING <column>::<enum_type>`

**Indexes:**
- All foreign keys have indexes (per [CODING_RULES.md Rule 9](../../CODING_RULES.md#9-database-indexes))
- Frequently queried columns (status, created_at, etc.) have indexes
- Composite indexes used for common query patterns

**Timestamps:**
- All tables use `DateTime(timezone=True)` for timestamps
- `created_at` defaults to `func.now()`
- `updated_at` uses `onupdate=func.now()`

**Related Documentation:**
- [ARCHITECTURE.md](../ARCHITECTURE.md) - System architecture overview
- [api-endpoints.md](api-endpoints.md) - REST API endpoints catalog
- [backend/app/models/](../../backend/app/models/) - SQLAlchemy model definitions

---

*This document is automatically maintained. Last verified: 2025-11-11*
