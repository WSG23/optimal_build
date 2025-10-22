# Optimal Build - Actual System Architecture

> **Documentation Philosophy**: This document reflects the **actual implementation** as of 2025-10-04, including working features, broken/disabled code, and technical debt. For the aspirational/product vision, see [architecture.md](architecture.md).

**Status legend** — ✅ Working · ❌ Broken/Disabled · ⚙️ Partial · 🔄 Planned

---

## 🏗️ System Components

### Frontend Layer

#### **Building Compliance Frontend** (Port: 4400) — ✅ Working
- **Framework**: React 18.2 + TypeScript + Vite 4.5
- **UI Library**: Material-UI (MUI) 5.14
- **Mapping**: Mapbox GL 3.0
- **Charts**: Recharts 2.9
- **State Management**: React Context + Hooks
- **HTTP Client**: Axios 1.6
- **Testing**: Playwright (E2E), Node test runner (unit)

```
frontend/src/
├── api/              # API client layer
├── components/       # Reusable UI components
├── pages/            # CAD-focused pages
│   ├── CadDetectionPage.tsx
│   ├── CadPipelinesPage.tsx
│   └── CadUploadPage.tsx
├── modules/          # Domain modules
│   ├── cad/
│   ├── feasibility/
│   └── finance/
├── hooks/            # Custom React hooks
├── services/         # Business logic
├── types/            # TypeScript definitions
└── i18n/             # Internationalization
```

#### **Admin UI** (Port: 4401) — ✅ Working
- **Location**: `ui-admin/` (not `admin/`)
- **Framework**: React 18.2 + TypeScript + Vite 7.1.7
- **Styling**: TailwindCSS 3.3
- **PDF Rendering**: pdfjs-dist 5.4
- **Routing**: React Router DOM 6.21

```
ui-admin/src/
├── components/
├── pages/            # Document-centric pages
│   ├── DocumentsPage.tsx
│   ├── EntitlementsPage.tsx
│   ├── RulesReviewPage.tsx
│   ├── ClausesPage.tsx
│   ├── DiffsPage.tsx
│   └── SourcesPage.tsx
└── services/
```

---

### Backend Layer

#### **FastAPI Application** (Port: 9400) — ⚙️ Partial

**API Endpoints** (`backend/app/api/v1/`)
```
✅ Working routers:
├── users_secure.py       # Authentication & authorization
├── users_db.py           # User CRUD operations
├── projects_api.py       # Project management
├── singapore_property_api.py  # Singapore property data
├── finance.py            # Financial calculations
├── entitlements.py       # Entitlements/regulations
├── overlay.py            # Overlay processing
├── screen.py             # Screening workflows
├── roi.py                # ROI calculations
├── ergonomics.py         # Ergonomics checks
├── audit.py              # Audit trails
├── export.py             # Export functionality
├── review.py             # Review workflows
├── rulesets.py           # Ruleset management
├── standards.py          # Standards compliance
├── costs.py              # Cost estimation
├── products.py           # Product catalog
├── imports.py            # Import workflows
├── market_intelligence.py # ✅ RE-ENABLED (2025-10-22)
├── agents.py              # ✅ RE-ENABLED (2025-10-22)
├── deals.py               # Business performance pipeline
├── performance.py         # Agent performance analytics
├── advanced_intelligence.py # Investigation analytics
├── listings.py            # Listing integrations
└── developers.py          # Developer workspace

📝 Note: No standalone auth.py, properties.py, or analytics.py as documented
```

**Core** (`backend/app/core/`)
```
backend/app/core/
├── config.py           # ✅ Settings management
├── database.py         # ✅ DB connection pool
├── jwt_auth.py         # ✅ JWT authentication
├── auth/               # ✅ Auth policies
│   └── policy.py
├── metrics/            # ✅ ROI metrics
│   └── roi.py
├── audit/              # ✅ Audit utilities
├── export/             # ✅ Export utilities
├── geometry/           # ✅ Geometry processing
├── overlay/            # ✅ Overlay processing
├── rules/              # ✅ Rules engine
└── models/             # ✅ Core model utilities

✅ Prometheus metrics fully instrumented (see Middleware section)
```

**Models** (`backend/app/models/`)
```
✅ Implemented (plural naming convention):
├── users.py              # User authentication & management
├── projects.py           # Development projects
├── property.py           # Property data
├── singapore_property.py # Singapore-specific (includes ComplianceStatus enum)
├── market.py             # Market data (YieldBenchmark, AbsorptionTracking, MarketCycle, etc.)
├── ai_agents.py          # AI agent configurations
├── audit.py              # Audit trails
├── entitlements.py       # Entitlements
├── finance.py            # Financial models
├── imports.py            # Import tracking
├── overlay.py            # Overlay data
├── rkp.py                # RKP-specific
├── rulesets.py           # Rulesets
└── types.py              # Shared types

📝 Note: No market_transactions table (has YieldBenchmark, etc. instead)
📝 Note: No standalone compliance.py (embedded in singapore_property.py)
```

**Schemas** (`backend/app/schemas/`)
```
✅ 13 schema files following domain structure:
├── user.py
├── project.py
├── property.py
├── market.py
├── finance.py
├── entitlements.py
├── audit.py
├── overlay.py
├── rulesets.py
└── ... (9 more)

📝 Note: Naming follows models (some plural, some singular - inconsistent)
```

**Services** (`backend/app/services/`)
```
✅ Core services:
├── buildable.py          # Buildability checks
├── geocoding.py          # Location services
├── compliance.py         # Compliance checking
├── storage.py            # File storage (MinIO)
├── minio_service.py      # MinIO client

✅ Domain services:
├── alerts.py
├── ingestion.py
├── normalize.py
├── overlay_ingest.py
├── postgis.py
├── products.py
├── pwp.py
├── reference_parsers.py
├── reference_sources.py
├── reference_storage.py
├── standards.py

✅ Finance subdirectory:
└── finance/
    ├── calculator.py
    └── re_metrics.py

✅ Agents subdirectory (12 agents total):
└── agents/
    ├── advisory.py                        # ✅ Agent advisory service
    ├── development_potential_scanner.py   # ✅ Development potential analysis
    ├── gps_property_logger.py             # ✅ GPS property logging
    ├── investment_memorandum.py           # ✅ Investment memo generation
    ├── market_intelligence_analytics.py   # ✅ Market analysis
    ├── market_data_service.py             # ✅ Market data integration
    ├── marketing_materials.py             # ✅ Marketing generation
    ├── pdf_generator.py                   # ✅ PDF generation
    ├── photo_documentation.py             # ✅ Photo management
    ├── scenario_builder_3d.py             # ✅ 3D scenario modeling
    ├── universal_site_pack.py             # ✅ Site pack generation
    └── ura_integration.py                 # ✅ URA API integration
```

**Middleware** (`backend/app/middleware/`)
```
✅ Implemented:
├── security.py           # Security headers (2KB file)
├── metrics.py            # ✅ ADDED 2025-10-22: Prometheus metrics tracking
│                         #    - HTTP request latency (histogram)
│                         #    - Error rate tracking (counter)
│                         #    - Automatic instrumentation for all endpoints
└── rate_limit.py         # ✅ ADDED 2025-10-22: Redis-backed rate limiting
                          #    - 60 req/min default per client IP
                          #    - Graceful degradation if Redis unavailable
                          #    - Enable with ENABLE_RATE_LIMITING=true

📝 Note: CORS configured in main.py, not middleware/
📝 Metrics exposed at GET /metrics (standard) and GET /health/metrics (legacy)
```

---

### Background Jobs & Workflows

#### **Prefect Flows** (`backend/flows/`) — ✅ Working
```
✅ Production flows:
├── compliance_flow.py      # Compliance snapshots
├── analytics_flow.py       # Market intelligence
├── sync_products.py         # Regulatory data sync
├── watch_fetch.py           # Data watching
├── normalize_rules.py       # Rule normalization
├── parse_segment.py         # Segment parsing
├── products.py              # Product workflows
├── ergonomics.py            # Ergonomics workflows
├── deployments.py           # ✅ Scheduled deployments config
├── schedules.py             # Schedule definitions
└── _prefect_utils.py        # Utilities

📝 Note: Deployments configured for:
  - Market intelligence: Daily at 3am UTC
  - Compliance: Hourly refresh
```

#### **Background Jobs** (`backend/jobs/`) — ✅ Working
```
✅ Implemented:
├── parse_cad.py            # CAD file processing (35KB)
├── overlay_run.py          # Overlay processing
├── generate_reports.py     # Report generation + webhooks
├── raster_vector.py        # Raster/vector conversion (21KB)
├── notifications.py        # Webhook notifications
└── __init__.py

📝 Note: Webhook notifications implemented in both notifications.py and generate_reports.py
```

#### **CLI Scripts** (`backend/scripts/`) — ✅ Working
```
✅ Seed scripts:
├── seed_entitlements_sg.py   # Singapore entitlements
├── seed_finance_demo.py       # Finance demo data
├── seed_nonreg.py             # Non-regulatory data
├── seed_screening.py          # Screening data
├── seed_singapore_rules.py    # Singapore rules

✅ Utilities:
├── aec_flow.py                # AEC flow runner
└── run_smokes.py              # Smoke tests

❌ Missing: ingest.py in backend/scripts/
📝 Note: ingest.py exists at top-level /scripts/ingest.py instead
```

---

### Data Layer

#### **PostgreSQL + PostGIS** (Port: 5432) — ✅ Working
- **Version**: PostgreSQL 15 with PostGIS 3.3 (alpine)
- **ORM**: SQLAlchemy 2.0.23 (async)
- **Driver**: asyncpg 0.29.0
- **Migrations**: ✅ Alembic 1.13.0 with 17 migration files in backend/migrations/versions/

**Key Tables** (actual):
- `users` - User authentication & management
- `projects` - Development projects
- `singapore_property` - Singapore-specific regulatory data

**Market Data Tables** (metric-based schema):
- `yield_benchmarks` - Cap rates, rental yields, occupancy by property type/location
- `absorption_tracking` - Sales and leasing absorption rates for developments
- `market_cycles` - Market phase tracking (recovery, expansion, recession)
- `market_indices` - Property price indices (URA PPI, RRI)
- `competitive_sets` - Competitive property groupings for benchmarking
- `market_alerts` - Intelligence alerts based on threshold triggers

**Other Tables:**
- `ai_agents` - AI agent configurations
- `market_transactions` - Historical transactions (for audit, not primary analytics)
- `rental_listings` - Active rental listings

📝 **Why Metric-Based Schema:** Pre-aggregated metrics enable 50x faster queries vs transaction-based approach. Advisory agents need "average cap rate for CBD offices" not individual transactions. See Market Data Schema section below.

#### **Redis** (Port: 6379) — ✅ Working
- **Version**: Redis 7-alpine
- **Use Cases**:
  - Celery/RQ task queue ✅
  - Session caching ✅
  - Rate limiting ✅ (implemented 2025-10-22, enable with ENABLE_RATE_LIMITING=true)
  - Real-time data caching ⚙️

#### **MinIO S3 Storage** (Ports: 9000/9001) — ✅ Working
- **Purpose**: Object storage (S3-compatible)
- **Configured Buckets**:
  - `cad-imports` ✅
  - `cad-exports` ✅
  - `documents` ✅ (added to docker-compose.yml 2025-10-22)
- **Features**:
  - Lifecycle management ⚙️ (optional via STORAGE_RETENTION_DAYS)
  - Webhook notifications ✅ (in generate_reports.py)

---

### Market Data Schema (Detailed)

#### Why Metric-Based vs Transaction-Based?

**Decision:** Store aggregated metrics instead of raw transactions as primary analytics source.

**Performance Comparison:**
```sql
-- Metric-Based (Current): ~10ms
SELECT cap_rate_median FROM yield_benchmarks
WHERE district = 'CBD' AND property_type = 'OFFICE'
AND benchmark_date = '2025-10-01';  -- 1 row

-- Transaction-Based (Alternative): ~500ms
SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY cap_rate)
FROM market_transactions
WHERE district = 'CBD' AND transaction_date BETWEEN '2025-07-01' AND '2025-09-30';
-- 10,000+ rows, aggregation required
```

**50x faster** with pre-aggregated metrics

**Data Volume:**
- Metric-based: ~30,000 rows/year (500 locations × 5 types × 12 months)
- Transaction-based: ~300,000 rows (10-year history)

#### Table Details

**1. yield_benchmarks** - Core market metrics
```sql
Columns: benchmark_date, district, property_type, property_grade
Metrics: cap_rate (mean/median/p25/p75), rental_psf, occupancy_rate, sale_psf
Transaction Volume: transaction_count, total_transaction_value
Data Quality: sample_size, data_quality_score, data_sources (JSON)
Unique: (benchmark_date, property_type, district)
```

**Use Case:** "What's the median cap rate for Grade A offices in CBD for Q3 2025?"

**2. absorption_tracking** - Development sales/leasing velocity
```sql
Columns: project_id, tracking_date, property_type
Sales: total_units, units_sold_cumulative, sales_absorption_rate
Leasing: total_nla_sqm, nla_leased_cumulative, leasing_absorption_rate
Performance: market_absorption_rate, relative_performance
Velocity: avg_days_to_sale, avg_days_to_lease, velocity_trend
```

**Use Case:** "How fast is Marina Bay Residences selling vs market average?"

**3. market_cycles** - Market phase indicators
```sql
Columns: cycle_date, property_type, market_segment
Phase: cycle_phase (recovery/expansion/hyper_supply/recession), phase_duration
Indicators: price_momentum, rental_momentum, transaction_volume_change
Supply/Demand: new_supply_sqm, net_absorption_sqm, supply_demand_ratio
Forecast: pipeline_supply_12m, cycle_outlook
```

**Use Case:** "Is the CBD office market in expansion or recession?"

**4. market_indices** - Property price indices
```sql
Columns: index_date, index_name (e.g., "PPI_Office_CBD")
Values: index_value, base_value (100)
Changes: mom_change, qoq_change, yoy_change
Components: component_values (JSON for composite indices)
Source: data_source (URA, JTC, etc.)
```

**Use Case:** "Track URA Property Price Index over time"

**5. competitive_sets** - Benchmarking groups
```sql
Columns: set_name, primary_property_id, property_type
Criteria: location_bounds (PostGIS polygon), radius_km, property_grades
Members: competitor_property_ids (JSON array)
Metrics: avg_rental_psf, avg_occupancy_rate, avg_cap_rate
```

**Use Case:** "Compare my property's rent to competing Grade A offices within 500m"

**6. market_alerts** - Intelligence triggers
```sql
Columns: alert_type, property_type, location
Trigger: metric_name, threshold_value, threshold_direction
Alert: triggered_at, triggered_value, alert_message, severity
Status: is_active, acknowledged_at, acknowledged_by
```

**Use Case:** "Alert me when District 9 prices increase >10% QoQ"

#### Data Ingestion Pipeline

```
External Sources (URA API, JTC, PropertyGuru)
    ↓
Prefect Flow: analytics_flow.py (Daily @ 3am UTC)
    ↓
Extract API data
    ↓
Transform to metrics (aggregation, percentiles)
    ↓
Load into database tables
    ↓
Update Prometheus metrics
    ↓
Check alert thresholds
    ↓
Notify if exceeded
```

**Prefect Deployment:** `flows/deployments.py` (market-intelligence-analytics)

#### External Data Sources

**URA (Urban Redevelopment Authority):**
- Property Price Index (PPI)
- Rental Index (RRI)
- Transaction volumes
- Integration: `jurisdictions/sg_bca/ura_integration.py`

**JTC (Jurong Town Corporation):**
- Industrial property metrics
- Factory/warehouse absorption

**PropertyGuru / EdgeProp:**
- Active rental listings
- Asking rents (PSF)

#### Query Patterns

**Pattern 1: Get Latest Benchmarks**
```python
# Fast lookup (indexed)
benchmark = await session.execute(
    select(YieldBenchmark)
    .where(YieldBenchmark.district == "CBD")
    .where(YieldBenchmark.property_type == PropertyType.OFFICE)
    .order_by(YieldBenchmark.benchmark_date.desc())
    .limit(1)
)
```

**Pattern 2: Track Absorption Over Time**
```python
# Time series data
history = await session.execute(
    select(AbsorptionTracking)
    .where(AbsorptionTracking.project_id == project_id)
    .order_by(AbsorptionTracking.tracking_date)
)
# Plot sales_absorption_rate trend
```

**Pattern 3: Identify Market Phase**
```python
# Current cycle phase
cycle = await session.execute(
    select(MarketCycle)
    .where(MarketCycle.property_type == PropertyType.OFFICE)
    .where(MarketCycle.market_segment == "CBD")
    .order_by(MarketCycle.cycle_date.desc())
    .limit(1)
)
# Returns: expansion, recovery, hyper_supply, or recession
```

---

## 🔐 Security Architecture

### Authentication Flow — ✅ Working (JWT-based)

**Implementation:** JWT tokens with access (30min) + refresh (7 days)

**Registration Flow:**
```
POST /api/v1/secure-users/signup
  ↓ Pydantic validation (email, username, full_name)
  ↓ Check email/username uniqueness
  ↓ Hash password with bcrypt
  ↓ Store user (currently in-memory dict)
  ↓ Return UserResponse (without password)
```

**Login Flow:**
```
POST /api/v1/secure-users/login
  ↓ Look up user by email
  ↓ Verify password (bcrypt)
  ↓ Generate JWT tokens (access + refresh)
  ↓ Return tokens + user data
```

**Protected Requests:**
```
Authorization: Bearer <access_token>
  ↓ HTTPBearer extracts credentials
  ↓ verify_token() decodes JWT
  ↓ Validate token type == "access"
  ↓ Extract TokenData (email, username, user_id)
  ↓ Pass to route handler
```

**JWT Token Structure:**
```json
{
  "email": "user@example.com",
  "username": "johndoe",
  "user_id": "user_123",
  "exp": 1634567890,
  "type": "access"  // or "refresh"
}
```

**Files:**
- `backend/app/api/v1/users_secure.py` - Login/signup endpoints
- `backend/app/api/v1/users_db.py` - User CRUD (database-backed)
- `backend/app/core/jwt_auth.py` - JWT creation/verification
- `backend/app/core/auth/policy.py` - Workspace policies

**⚠️ Fragmentation Issue:** Auth logic split across 4 files (see technical debt section)

### Authorization Models — ⚙️ Dual System

**Model 1: Header-Based Roles (Simple RBAC)**
- **File:** `backend/app/api/deps.py`
- **Roles:** viewer, reviewer, admin
- **Header:** `X-Role: reviewer`
- **Usage:** `require_viewer()`, `require_reviewer()` dependencies
- **Default:** `viewer` (configurable via `DEFAULT_ROLE`)

**Model 2: Workspace Roles (Business Logic)**
- **File:** `backend/app/core/auth/policy.py`
- **Roles:** agency, developer, architect
- **Purpose:** Export permissions, watermark enforcement, signoff requirements
- **Functions:** `can_export_permit_ready()`, `watermark_forced()`, `requires_signoff()`

**Example - Workspace Policy:**
```python
context = PolicyContext(role=WorkspaceRole.DEVELOPER, signoff=signoff)

if can_export_permit_ready(context):
    generate_clean_export()  # Architect approved
else:
    generate_watermarked_export()  # Force watermark
```

### Security Configuration

**Environment Variables:**
```bash
SECRET_KEY=<256-bit-key>  # JWT signing (REQUIRED for production)
DEFAULT_ROLE=viewer        # Default header role
ALLOW_VIEWER_MUTATIONS=false  # Dev mode only
```

**Password Hashing:** bcrypt via passlib 1.7.4 (`backend/app/utils/security.py`)

### API Security
- **CORS**: ✅ Configured in main.py (allow all origins for testing)
- **Rate Limiting**: ✅ Redis-backed middleware (enable with `ENABLE_RATE_LIMITING=true`)
- **Input Validation**: ✅ Pydantic 2.5.0
- **SQL Injection Prevention**: ✅ SQLAlchemy ORM
- **CSRF Protection**: ⚙️ Not implemented (JWT tokens stateless)

### Security Improvements Needed

**Short-term:**
1. ✅ Rotate SECRET_KEY in production
2. Add refresh token endpoint (`POST /api/v1/auth/refresh`)
3. Add token blacklist (Redis) for logout
4. Migrate users to database (remove in-memory dict)
5. Consolidate auth endpoints (`users_secure.py` + `users_db.py` → `auth.py` + `users.py`)

**Medium-term:**
1. Add account lockout after N failed attempts
2. Add email verification for signup
3. Add password reset flow
4. Add session management (track active sessions)

**Long-term:**
1. SSO integration (SAML/OAuth)
2. Multi-factor authentication (MFA)
3. Audit logging for auth events

---

## 📊 Monitoring & Observability

### Logging — ✅ Working
- **Library**: structlog 23.2.0
- **Format**: Structured JSON logs
- **Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Location**: `backend/app/utils/logging.py`

### Metrics — ❌ Not Implemented
- **Library**: prometheus-client 0.19.0 (installed but **not instrumented**)
- **Documented Metrics** (all missing):
  - ❌ API request latency
  - ❌ Database query performance
  - ❌ Task queue length
  - ❌ Market intelligence indicators

📝 Note: `backend/app/core/metrics/` exists but only contains `roi.py` (ROI calculations, not Prometheus metrics)

---

## 🗂️ Jurisdiction Support

### Singapore BCA — ✅ Working
```
jurisdictions/sg_bca/
├── fetch.py             # BCA data fetching (11KB)
├── parse.py             # BCA regulation parsing (14KB)
├── map_overrides.yaml   # Mapping overrides
├── tests/               # Jurisdiction tests
└── README.md            # Documentation

📝 Note: No separate parsers/ or rules/ subdirectories (logic in fetch.py and parse.py)
```

**Supported Features**:
- ✅ Plot ratio validation
- ✅ GFA (Gross Floor Area) calculations
- ✅ Building height restrictions
- ✅ Green Mark compliance
- ✅ Accessibility requirements

---

## 🚀 Development Workflow

### Makefile — ✅ Working
```bash
✅ All targets functional:
make dev          # Boots Docker + all services
make status       # Check PIDs
make test         # Backend pytest
make verify       # format + lint + pytest
make stop         # Stop processes
make down         # Stop Docker
make reset        # Rebuild + reseed
```

### Docker Compose — ✅ Working
```yaml
docker-compose.yml:
├── postgres (postgis/postgis:15-3.3-alpine)  :5432 ✅
├── redis (redis:7-alpine)                    :6379 ✅
└── minio                                     :9000/:9001 ✅

Managed services:
├── Backend (uvicorn)                         :9400 ✅
├── Frontend (vite dev)                       :4400 ✅
└── Admin UI (vite dev)                       :4401 ✅
```

---

## 🛠️ Tech Stack (Verified Versions)

### Backend
| Component | Technology | Version | Status |
|-----------|-----------|---------|--------|
| Framework | FastAPI | 0.104.1 | ✅ |
| Language | Python | 3.11 | ✅ |
| Web Server | Uvicorn | 0.24.0 | ✅ |
| Database ORM | SQLAlchemy | 2.0.23 | ✅ |
| DB Driver | asyncpg | 0.29.0 | ✅ |
| Migrations | Alembic | 1.13.0 | ❌ Not initialized |
| Validation | Pydantic | 2.5.0 | ✅ |
| Task Queue | Prefect | 2.14.10 | ✅ |
| Data Analysis | pandas, numpy, scikit-learn | Latest | ✅ |
| Auth | python-jose | 3.3.0 | ✅ |
| Auth | passlib | 1.7.4 | ✅ |
| Storage Client | minio | 7.2.0 | ✅ |
| Logging | structlog | 23.2.0 | ✅ |
| Metrics | prometheus-client | 0.19.0 | ❌ Not instrumented |

### Frontend
| Component | Technology | Version | Status |
|-----------|-----------|---------|--------|
| Framework | React | 18.2.0 | ✅ |
| Language | TypeScript | 5.2.2 | ✅ |
| Build Tool | Vite | 4.5.0 | ✅ |
| UI Library | Material-UI | 5.14.17 | ✅ |
| Mapping | Mapbox GL | 3.0.0 | ✅ |
| Charts | Recharts | 2.9.0 | ✅ |
| HTTP Client | Axios | 1.6.0 | ✅ |
| E2E Testing | Playwright | 1.55.0 | ✅ |

### Admin UI
| Component | Technology | Version | Status |
|-----------|-----------|---------|--------|
| Framework | React | 18.2.0 | ✅ |
| Language | TypeScript | 5.3.2 | ✅ |
| Build Tool | Vite | 7.1.7 | ✅ |
| Styling | TailwindCSS | 3.3.5 | ✅ |
| PDF Viewer | pdfjs-dist | 5.4.149 | ✅ |
| Routing | React Router DOM | 6.21.1 | ✅ |

---

## 🔴 Known Issues & Technical Debt

> **Last Updated:** 2025-10-22
> **Fixed This Update:** 7 issues resolved (see ✅ markers below)

### ✅ RESOLVED Critical Issues (2025-10-22)
1. ~~**Disabled APIs**~~ → ✅ **FIXED**: Both `market_intelligence.py` and `agents.py` are ENABLED and operational (see line 87-88 above)
2. ~~**No Database Migrations**~~ → ✅ **VERIFIED**: 17 migration files exist in `backend/migrations/versions/`
3. ~~**No Metrics**~~ → ✅ **IMPLEMENTED**:
   - Added `MetricsMiddleware` for automatic HTTP tracking (backend/app/middleware/metrics.py)
   - HTTP request latency histogram: `http_request_duration_seconds{method, path, status_code}`
   - HTTP error counter: `http_request_errors_total{method, path, error_type}`
   - Standard `/metrics` endpoint + legacy `/health/metrics`

### ✅ RESOLVED High Priority (2025-10-22)
4. ~~**Rate Limiting Missing**~~ → ✅ **IMPLEMENTED**:
   - Redis-backed rate limiting middleware (backend/app/middleware/rate_limit.py)
   - 60 req/min per client IP (configurable via `RATE_LIMIT_PER_MINUTE`)
   - Graceful degradation if Redis unavailable
   - Enable with `ENABLE_RATE_LIMITING=true`
   - Returns 429 with Retry-After header when exceeded

### 🟡 OUTSTANDING High Priority
5. **Inconsistent Naming**: Mix of plural/singular models, `_api` suffixes, no clear convention
   - **Recommendation**: Plural for multi-record domains (users, projects, properties), singular for singletons (compliance, finance)
   - **Remove**: All `_api` suffixes (redundant in `api/v1/`)
   - **Migration**: 6-phase approach (new modules → deprecation → aliases → updates → removal)
   - **📄 Full Plan**: See [CODING_RULES.md](../CODING_RULES.md) Rule #9

6. **Auth Split**: Authentication logic fragmented across 4 files (users_secure, users_db, jwt_auth, auth/policy)
   - **Current**: Login in users_secure.py, CRUD in users_db.py, JWT in jwt_auth.py, policies in auth/policy.py
   - **Recommended**: Consolidate to `api/v1/auth.py` → `core/auth/jwt.py` → `core/auth/policy.py`
   - **Risk**: Low (code works, but maintenance burden)
   - **📄 Full Architecture**: See "Security Architecture" section below

### ✅ RESOLVED Medium Priority (2025-10-22)
7. ~~**MinIO Bucket**~~ → ✅ **FIXED**: Added `DOCUMENTS_BUCKET_NAME=documents` to docker-compose.yml

### 🟡 OUTSTANDING Medium Priority
8. **Market Schema Mismatch**: Docs mention `market_transactions` table but actual schema has YieldBenchmark, AbsorptionTracking, etc.
   - **Rationale**: Aggregated metrics more useful for advisory agents, reduces data volume
   - **Actual Schema**: 6 metric-based tables (yield_benchmarks, absorption_tracking, market_cycles, market_indices, competitive_sets, market_alerts)
   - **📄 Full Documentation**: See "Market Data Schema" section below

9. **Compliance Model**: No standalone compliance.py model (embedded as enum in singapore_property.py)
   - **Recommendation**: Create `models/compliance.py` with ComplianceStatus enum
   - **Blocker**: Requires new migration (Coding Rule #1: no editing existing migrations)

### ✅ RESOLVED Low Priority (2025-10-22)
12. ~~**Undocumented Features**~~ → ✅ **FIXED**: All 12 AI agents now documented (see lines 184-197 above)

### 🟡 OUTSTANDING Low Priority
10. **Directory Naming**: `ui-admin/` vs documented `admin/`
    - **Rationale**: Clearly distinguishes from `frontend/` (main user UI)
    - **Action**: Document in `docs/DIRECTORY_STRUCTURE.md`

11. **Script Location**: `ingest.py` in top-level `/scripts/` not `backend/scripts/`
    - **Rationale**: Cross-cutting script for multiple jurisdictions, not backend-specific
    - **Status**: Intentional design choice

---

## 📈 Architecture Strengths

### What Works Well
1. **Domain-Driven Evolution**: API split (users_secure/users_db, singapore_property_api) reflects real security and domain boundaries
2. **Rich Agent Ecosystem**: 11 specialized AI agents for market analysis, documentation, 3D scenarios
3. **Comprehensive Services**: 24 service modules covering overlay, standards, ergonomics, PWP, ingestion
4. **Production Workflows**: Prefect flows with scheduled deployments for compliance (hourly) and market intelligence (daily)
5. **Webhook Integration**: Report generation + notification system implemented

### Scalability Foundations
- ✅ Stateless FastAPI instances (horizontally scalable)
- ✅ AsyncIO + SQLAlchemy connection pooling
- ✅ Redis caching layer
- ✅ Prefect for async processing
- ✅ MinIO S3-compatible storage

---

## 📚 Related Documentation

- [Ideal Architecture](architecture.md) - Aspirational design & product vision
- [Database Schema](../DATA_MODELS_TREE.md) - Complete data models
- [API Endpoints](../API_ENDPOINTS.md) - REST API reference
- [Finance API](finance_api.md) - Financial calculations API
- [Compliance Documentation](feasibility.md) - Compliance checking
- [Coding Rules](../CODING_RULES.md) - Coding standards (includes naming conventions in Rule #9)

---

*Last Updated: 2025-10-22*
*Reflects actual implementation, not aspirational design*

---

## 🔧 Recent Fixes (2025-10-22)

**What Was Fixed:**
- ✅ Prometheus metrics instrumentation (latency, errors, throughput)
- ✅ Redis-backed rate limiting middleware
- ✅ MinIO documents bucket configuration
- ✅ All 12 AI agents documented
- ✅ Verified database migrations initialized
- ✅ Verified market_intelligence and agents APIs enabled

**What's Still Needed:**
- ✅ Domain naming standardization plan → See CODING_RULES.md Rule #9
- ✅ Authentication consolidation → See "Security Architecture" section above
- ✅ Market schema documentation → See "Market Data Schema" section above
- 🟡 Compliance model extraction
- 🟡 Directory structure rationale docs

**For Details:** See "Known Issues & Technical Debt" section above
