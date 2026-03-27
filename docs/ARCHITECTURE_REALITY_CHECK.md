# Optimal Build - Actual System Architecture

> **Documentation Philosophy**: This document reflects the **actual implementation** as of 2025-10-19, including working features, broken/disabled code, and technical debt. For the aspirational/product vision, see [architecture.md](architecture.md).

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
└── imports.py            # Import workflows

✅ Additional working routers:
├── deals.py                # Business performance pipeline endpoints
├── performance.py          # Agent performance analytics endpoints
├── advanced_intelligence.py # Investigation analytics stubs
├── listings.py             # Listing management endpoints
└── developers.py           # Developer workspace endpoints (site acquisition, checklists)

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
├── metrics/            # ⚙️ ROI metrics only (no Prometheus)
│   └── roi.py
├── audit/              # ✅ Audit utilities
├── export/             # ✅ Export utilities
├── geometry/           # ✅ Geometry processing
├── overlay/            # ✅ Overlay processing
├── rules/              # ✅ Rules engine
└── models/             # ✅ Core model utilities

❌ Missing: security.py, Prometheus metrics instrumentation
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

✅ Agents subdirectory (11 agents - mostly undocumented):
└── agents/
    ├── market_intelligence_analytics.py  # Market analysis
    ├── development_potential_scanner.py  # Development potential
    ├── gps_property_logger.py            # GPS logging
    ├── investment_memorandum.py          # Investment docs
    ├── market_data_service.py            # Market data
    ├── marketing_materials.py            # Marketing generation
    ├── pdf_generator.py                  # PDF generation
    ├── photo_documentation.py            # Photo management
    ├── scenario_builder_3d.py            # 3D scenarios
    ├── universal_site_pack.py            # Site packs
    └── ura_integration.py                # URA integration
```

**Middleware** (`backend/app/middleware/`)
```
⚙️ Minimal implementation:
└── security.py           # 2KB file

❌ Missing: Rate limiting middleware (documented but not implemented)
📝 Note: CORS configured in main.py, not middleware/
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
- **Migrations**: ✅ Alembic 1.13.0 **fully initialized** with 19+ migration files in versions/

**Key Tables** (actual):
- `users` - User authentication & management
- `projects` - Development projects
- `singapore_property` - Singapore-specific regulatory data
- `yield_benchmarks` - Financial yield data
- `absorption_tracking` - Market absorption
- `market_cycle` - Market cycle data
- `market_index` - Market indices
- `competitive_set` - Competition data
- `market_alert` - Market alerts
- `ai_agents` - AI agent configurations

📝 Note: No `market_transactions` table (different schema than documented)

#### **Redis** (Port: 6379) — ✅ Working
- **Version**: Redis 7-alpine
- **Use Cases**:
  - Celery/RQ task queue ✅
  - Session caching ✅
  - Rate limiting ❌ (documented but not implemented)
  - Real-time data caching ⚙️

#### **MinIO S3 Storage** (Ports: 9000/9001) — ✅ Working
- **Purpose**: Object storage (S3-compatible)
- **Configured Buckets**:
  - `cad-imports` ✅
  - `cad-exports` ✅
  - `documents` ⚙️ (mentioned in docs but not in docker-compose.yml)
- **Features**:
  - Lifecycle management ⚙️ (optional via STORAGE_RETENTION_DAYS)
  - Webhook notifications ✅ (in generate_reports.py)

---

## 🔐 Security Architecture

### Authentication & Authorization — ⚙️ Partial
- **JWT**: ✅ local HS256 codec in `app/core/jwt_codec.py`
- **Password Hashing**: ✅ PBKDF2-HMAC-SHA256 for new hashes, with legacy bcrypt verification support
- **Token Storage**: ⚙️ Documented as HTTP-only cookies (not verified in code)
- **RBAC**: ⚙️ Roles mentioned (admin/user/developer/consultant) but not fully verified
- **Auth Logic**: Centralised in `app/core/auth/service.py` (legacy wrappers kept for backwards compatibility)

### API Security
- **CORS**: ✅ Configured in main.py
- **Rate Limiting**: ✅ SlowAPI limiter backed by Redis (`RATE_LIMIT_STORAGE_URI`, defaults to DB 3)
- **Input Validation**: ✅ Pydantic 2.5.0
- **SQL Injection Prevention**: ✅ SQLAlchemy ORM

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
| Validation | Pydantic | 2.12.5 | ✅ |
| Task Queue | Prefect | 2.20.17 | ✅ |
| Data Analysis | pandas, numpy, scikit-learn | Latest | ✅ |
| Auth | local HS256 codec | Current | ✅ |
| Auth | PBKDF2-HMAC-SHA256, bcrypt legacy verify | Current | ✅ |
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

### Critical
1. ~~**Disabled APIs**: `market_intelligence.py` and `agents.py` commented out~~ **✅ RESOLVED** - Both routers are now active and registered (as of 2025-10-19)
2. ~~**No Database Migrations**: Alembic installed but not initialized~~ **✅ RESOLVED** - Alembic fully initialized with 19+ migration files (as of 2025-10-19)
3. ~~**No Metrics**: Prometheus client installed but no instrumentation (latency, errors, throughput all missing)~~ **✅ RESOLVED** – RequestMetricsMiddleware records request/latency counters and `/metrics` now exposes the Prometheus registry.

### High
4. ~~**Rate Limiting Missing**: Documented but not implemented in middleware~~ **✅ RESOLVED** – SlowAPI now enforces limits with Redis-backed storage.
5. **Inconsistent Naming**: Mix of plural/singular models, `_api` suffixes, no clear convention
6. ~~**Auth Split**: Authentication logic fragmented across 4 files (users_secure, users_db, jwt_auth, auth/policy)~~ **✅ RESOLVED** – Consolidated into `app/core/auth/service.py` with thin wrappers for compatibility.

### Medium
7. ~~**MinIO Bucket**: `documents` bucket documented but not in docker-compose.yml~~ **✅ RESOLVED** – `DOCUMENTS_BUCKET_NAME` default added; MinIOService bootstraps documents/imports/exports buckets.
8. **Market Schema Mismatch**: Docs mention `market_transactions` table but actual schema has YieldBenchmark, AbsorptionTracking, etc.
9. **Compliance Model**: No standalone compliance.py model (embedded as enum in singapore_property.py)

### Low
10. ~~**Directory Naming**: `ui-admin/` vs documented `admin/`~~ **✅ Documented** – Frontend references now point to the canonical `ui-admin/` directory.
11. ~~**Script Location**: `ingest.py` in top-level `/scripts/` not `backend/scripts/`~~ **✅ Documented** – Runbook now references `/scripts/ingest.py` as the supported entry point.
12. **Undocumented Features**: 10 of 11 AI agents not mentioned in docs

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

---

## 🔄 Recent Updates (2025-10-19)

**Resolved Issues:**
- ✅ **API Routers Restored**: `market_intelligence.py` and `agents.py` are now active and fully functional
- ✅ **Database Migrations Initialized**: Alembic fully operational with 19+ migration files tracking schema evolution
- ✅ **Additional Routers Added**: Phase 1 completion brought 5+ new working routers (deals, performance, listings, developers, advanced_intelligence)
- ✅ **Prometheus Instrumentation**: RequestMetricsMiddleware + `/metrics` endpoint now emit latency/error/throughput metrics for the API tier

**Remaining Critical Issues:**
- ❌ Prometheus metrics instrumentation still missing
- ⚠️ Rate limiting middleware not yet implemented

---

*Last Updated: 2025-10-19*
*Reflects actual implementation, not aspirational design*
*Previous update: 2025-10-04*
