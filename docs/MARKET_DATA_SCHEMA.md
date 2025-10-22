# Market Data Schema Documentation

**Last Updated:** 2025-10-22

This document describes the actual market data schema implementation, explaining why it differs from early documentation references to `market_transactions`.

---

## Table of Contents

1. [Overview](#overview)
2. [Schema Design Philosophy](#schema-design-philosophy)
3. [Core Tables](#core-tables)
4. [Data Flow](#data-flow)
5. [Why Not Transaction-Based](#why-not-transaction-based)
6. [External Data Sources](#external-data-sources)
7. [Query Patterns](#query-patterns)

---

## Overview

The optimal_build platform uses a **metric-based market data schema** rather than a raw transaction database. This design choice prioritizes **aggregated analytics** over granular transaction tracking.

### Actual Schema (Production)

**File:** `backend/app/models/market.py`

**Tables:**
- `yield_benchmarks` - Cap rates and rental yields by property type/location
- `absorption_tracking` - Sales and leasing absorption rates
- `market_cycles` - Market phase tracking and indicators
- `market_indices` - Property market index values
- `competitive_sets` - Competitive property groupings
- `market_alerts` - Market intelligence alerts

**Plus transaction tables in property.py:**
- `market_transactions` - Historical transactions (for reference)
- `rental_listings` - Active rental listings

---

## Schema Design Philosophy

### Metric-Based vs Transaction-Based

**Decision:** Store **aggregated metrics** instead of raw transactions

**Rationale:**

| Metric-Based (Current) | Transaction-Based (Alternative) |
|------------------------|--------------------------------|
| ✅ Faster queries (pre-aggregated) | ❌ Requires GROUP BY on every query |
| ✅ Smaller data volume | ❌ 10x-100x more rows |
| ✅ Easier integration with URA/JTC APIs | ❌ Raw data not always available |
| ✅ Better for advisory agents (what they need) | ❌ Over-engineered for use case |
| ⚠️ Harder to drill down to individual transactions | ✅ Full granularity |

**Use Case Alignment:**

Our AI advisory agents need answers to questions like:
- "What's the average cap rate for Grade A offices in CBD?"
- "What's the absorption rate for new developments in District 9?"
- "Is the market in expansion or recession phase?"

These questions are **naturally metric-based**, not transaction-based.

---

## Core Tables

### 1. YieldBenchmark

**Purpose:** Store cap rate and rental yield benchmarks by property type and location

**Table:** `yield_benchmarks`

**Key Columns:**
```sql
-- Period
benchmark_date DATE NOT NULL
period_type VARCHAR(20)  -- monthly, quarterly, yearly

-- Location
district VARCHAR(100)
subzone VARCHAR(100)
location_tier VARCHAR(20)  -- prime, secondary, suburban

-- Property Classification
property_type ENUM(PropertyType) NOT NULL
property_grade VARCHAR(20)  -- A, B, C

-- Cap Rate Metrics (percentiles for distribution)
cap_rate_mean DECIMAL(5,3)
cap_rate_median DECIMAL(5,3)
cap_rate_p25 DECIMAL(5,3)  -- 25th percentile
cap_rate_p75 DECIMAL(5,3)  -- 75th percentile

-- Rental Yield Metrics
rental_yield_mean DECIMAL(5,3)
rental_yield_median DECIMAL(5,3)

-- Rental Rate (PSF/month)
rental_psf_mean DECIMAL(8,2)
rental_psf_median DECIMAL(8,2)

-- Occupancy
occupancy_rate_mean DECIMAL(5,2)
vacancy_rate_mean DECIMAL(5,2)

-- Sale Price (PSF)
sale_psf_mean DECIMAL(10,2)
sale_psf_median DECIMAL(10,2)

-- Transaction Volume
transaction_count INTEGER
total_transaction_value DECIMAL(15,2)

-- Data Quality
sample_size INTEGER
data_quality_score DECIMAL(3,2)  -- 0-1
data_sources JSON
```

**Unique Constraint:** `(benchmark_date, property_type, district)`

**Indexes:**
- `benchmark_date`
- `(district, subzone)`

**Example Row:**
```json
{
  "benchmark_date": "2025-09-30",
  "period_type": "quarterly",
  "district": "Downtown Core",
  "subzone": "Raffles Place",
  "location_tier": "prime",
  "property_type": "OFFICE",
  "property_grade": "A",
  "cap_rate_median": 0.045,  // 4.5%
  "rental_psf_median": 12.50,
  "occupancy_rate_mean": 95.2,
  "transaction_count": 15,
  "sample_size": 15,
  "data_quality_score": 0.95
}
```

---

### 2. AbsorptionTracking

**Purpose:** Track sales and leasing absorption rates for developments

**Table:** `absorption_tracking`

**Key Columns:**
```sql
-- Reference
project_id UUID  -- Links to properties/development_pipeline
project_name VARCHAR(255)
tracking_date DATE NOT NULL

-- Sales Absorption (for residential/new developments)
total_units INTEGER
units_launched INTEGER
units_sold_cumulative INTEGER
units_sold_period INTEGER  -- This period only
sales_absorption_rate DECIMAL(5,2)  -- Percentage

-- Time Metrics
months_since_launch INTEGER
avg_units_per_month DECIMAL(8,2)
projected_sellout_months INTEGER

-- Price Performance
launch_price_psf DECIMAL(10,2)
current_price_psf DECIMAL(10,2)
price_change_percentage DECIMAL(5,2)

-- Leasing Absorption (for commercial)
total_nla_sqm DECIMAL(10,2)
nla_leased_cumulative DECIMAL(10,2)
nla_leased_period DECIMAL(10,2)
leasing_absorption_rate DECIMAL(5,2)

-- Market Context
competing_supply_units INTEGER
competing_projects_count INTEGER
market_absorption_rate DECIMAL(5,2)  -- Market average
relative_performance DECIMAL(5,2)  -- vs market

-- Velocity
avg_days_to_sale INTEGER
avg_days_to_lease INTEGER
velocity_trend VARCHAR(20)  -- accelerating, stable, decelerating
```

**Indexes:**
- `(project_id, tracking_date)`
- `(property_type, tracking_date)`

**Example Row:**
```json
{
  "project_name": "Marina Bay Residences",
  "tracking_date": "2025-10-01",
  "total_units": 500,
  "units_sold_cumulative": 320,
  "sales_absorption_rate": 64.0,  // 64%
  "months_since_launch": 8,
  "avg_units_per_month": 40.0,
  "projected_sellout_months": 4.5,
  "market_absorption_rate": 55.0,  // Market average
  "relative_performance": 9.0  // 9% better than market
}
```

---

### 3. MarketCycle

**Purpose:** Track market cycles and phases for each property type/segment

**Table:** `market_cycles`

**Key Columns:**
```sql
-- Period
cycle_date DATE NOT NULL
property_type ENUM(PropertyType) NOT NULL
market_segment VARCHAR(50)  -- CBD, suburban, industrial zones

-- Cycle Phase
cycle_phase VARCHAR(50)  -- recovery, expansion, hyper_supply, recession
phase_duration_months INTEGER
phase_strength DECIMAL(3,2)  -- 0-1

-- Leading Indicators
price_momentum DECIMAL(5,2)  -- YoY %
rental_momentum DECIMAL(5,2)  -- YoY %
transaction_volume_change DECIMAL(5,2)  -- YoY %

-- Supply/Demand Balance
new_supply_sqm DECIMAL(12,2)
net_absorption_sqm DECIMAL(12,2)
supply_demand_ratio DECIMAL(5,2)

-- Forward Looking
pipeline_supply_12m DECIMAL(12,2)
expected_demand_12m DECIMAL(12,2)
cycle_outlook VARCHAR(20)  -- improving, stable, deteriorating
```

**Unique Constraint:** `(cycle_date, property_type, market_segment)`

**Example Row:**
```json
{
  "cycle_date": "2025-10-01",
  "property_type": "OFFICE",
  "market_segment": "CBD",
  "cycle_phase": "expansion",
  "phase_duration_months": 18,
  "price_momentum": 8.5,  // 8.5% YoY
  "rental_momentum": 5.2,  // 5.2% YoY
  "supply_demand_ratio": 0.85,  // Supply < Demand (good)
  "cycle_outlook": "improving"
}
```

---

### 4. MarketIndex

**Purpose:** Track property market indices (e.g., URA Property Price Index)

**Table:** `market_indices`

**Key Columns:**
```sql
-- Index Details
index_date DATE NOT NULL
index_name VARCHAR(100) NOT NULL  -- e.g., "PPI_Office", "RRI_Retail"
property_type ENUM(PropertyType)

-- Values
index_value DECIMAL(10,2) NOT NULL
base_value DECIMAL(10,2) DEFAULT 100

-- Changes
mom_change DECIMAL(5,2)  -- Month-on-month %
qoq_change DECIMAL(5,2)  -- Quarter-on-quarter %
yoy_change DECIMAL(5,2)  -- Year-on-year %

-- Components (if composite)
component_values JSON

-- Source
data_source VARCHAR(50)
```

**Unique Constraint:** `(index_date, index_name)`

**Example Row:**
```json
{
  "index_date": "2025-09-30",
  "index_name": "PPI_Office_CBD",
  "property_type": "OFFICE",
  "index_value": 185.4,
  "base_value": 100.0,  // Q1 2009 = 100
  "mom_change": 0.8,  // 0.8% MoM
  "qoq_change": 2.1,  // 2.1% QoQ
  "yoy_change": 7.5,  // 7.5% YoY
  "data_source": "URA"
}
```

---

### 5. CompetitiveSet

**Purpose:** Define and track competitive property sets for benchmarking

**Table:** `competitive_sets`

**Key Columns:**
```sql
-- Set Definition
set_name VARCHAR(255) NOT NULL
primary_property_id UUID

-- Criteria
property_type ENUM(PropertyType) NOT NULL
location_bounds GEOMETRY(POLYGON)  -- PostGIS polygon
radius_km DECIMAL(5,2)

-- Filters
min_gfa_sqm DECIMAL(10,2)
max_gfa_sqm DECIMAL(10,2)
property_grades JSON  -- ['A', 'B']
age_range_years JSON  -- {min: 0, max: 10}

-- Members
competitor_property_ids JSON  -- Array of UUIDs

-- Aggregated Metrics
avg_rental_psf DECIMAL(8,2)
avg_occupancy_rate DECIMAL(5,2)
avg_cap_rate DECIMAL(5,3)

-- Metadata
is_active BOOLEAN DEFAULT TRUE
last_refreshed TIMESTAMP
```

**Example Row:**
```json
{
  "set_name": "Grade A Offices within 500m of Raffles Place MRT",
  "primary_property_id": "uuid-123",
  "property_type": "OFFICE",
  "radius_km": 0.5,
  "property_grades": ["A"],
  "competitor_property_ids": ["uuid-456", "uuid-789", "uuid-012"],
  "avg_rental_psf": 13.20,
  "avg_occupancy_rate": 94.5,
  "avg_cap_rate": 0.042
}
```

---

### 6. MarketAlert

**Purpose:** Market intelligence alerts based on threshold triggers

**Table:** `market_alerts`

**Key Columns:**
```sql
-- Alert Configuration
alert_type VARCHAR(50) NOT NULL  -- price_change, new_supply, absorption_spike
property_type ENUM(PropertyType)
location VARCHAR(255)

-- Trigger Conditions
metric_name VARCHAR(100)
threshold_value DECIMAL(10,2)
threshold_direction VARCHAR(20)  -- above, below, change_percentage

-- Alert Details
triggered_at TIMESTAMP
triggered_value DECIMAL(10,2)
alert_message VARCHAR(1000)
severity VARCHAR(20)  -- low, medium, high, critical

-- Context
market_context JSON
affected_properties JSON

-- Status
is_active BOOLEAN DEFAULT TRUE
acknowledged_at TIMESTAMP
acknowledged_by UUID  -- User ID
```

**Example Row:**
```json
{
  "alert_type": "price_change",
  "property_type": "RESIDENTIAL",
  "location": "District 9",
  "metric_name": "sale_psf_median",
  "threshold_value": 10.0,  // 10% change
  "threshold_direction": "change_percentage",
  "triggered_at": "2025-10-15T09:30:00",
  "triggered_value": 12.5,  // Actual: 12.5% increase
  "alert_message": "District 9 residential prices increased 12.5% QoQ",
  "severity": "high",
  "is_active": true
}
```

---

## Data Flow

### Ingestion Pipeline

```
External Sources (URA, JTC, PropertyGuru)
    ↓
Prefect Flow: analytics_flow.py (Daily @ 3am UTC)
    ↓
Extract API data
    ↓
Transform to metrics (aggregation, percentiles)
    ↓
Load into database (yield_benchmarks, market_cycles, etc.)
    ↓
Trigger Prometheus metrics update
    ↓
Check alert thresholds
    ↓
Notify if threshold exceeded
```

**Prefect Deployment:** `flows/deployments.py`
```python
# Market intelligence analytics deployment
analytics_deployment = Deployment.build_from_flow(
    flow=market_intelligence_analytics_flow,
    name="market-intelligence-analytics",
    schedule=CronSchedule(cron="0 3 * * *"),  # Daily at 3am UTC
    tags=["market", "analytics", "production"],
)
```

---

### API Consumption

```
Frontend/Agent Request
    ↓
GET /api/v1/market-intelligence/benchmarks?district=CBD&type=OFFICE
    ↓
Query yield_benchmarks table
    ↓
Return aggregated metrics (no aggregation needed - pre-computed)
    ↓
Response in <50ms (indexed query)
```

---

## Why Not Transaction-Based

### Common Question: "Why not store raw transactions?"

**Answer:** We do! But not as the primary source of truth for analytics.

**Transaction tables exist:**
- `market_transactions` (in `app/models/property.py:MarketTransaction`)
- `rental_listings` (in `app/models/property.py:RentalListing`)

**But they're used differently:**

| Use Case | Table | Why |
|----------|-------|-----|
| Market intelligence analytics | `yield_benchmarks` | Pre-aggregated, fast queries |
| Compliance/audit trail | `market_transactions` | Granular record-keeping |
| Active listing management | `rental_listings` | Live data |

---

### Performance Comparison

**Metric-Based (Current):**
```sql
-- Get median cap rate for CBD offices
SELECT cap_rate_median
FROM yield_benchmarks
WHERE district = 'CBD'
  AND property_type = 'OFFICE'
  AND benchmark_date = '2025-10-01';

-- Query time: ~10ms (indexed)
-- Rows scanned: 1
```

**Transaction-Based (Alternative):**
```sql
-- Same query with raw transactions
SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY cap_rate)
FROM market_transactions
WHERE district = 'CBD'
  AND property_type = 'OFFICE'
  AND transaction_date BETWEEN '2025-07-01' AND '2025-09-30'
  AND transaction_type = 'SALE';

-- Query time: ~500ms (full scan + aggregation)
-- Rows scanned: 10,000+
```

**50x faster** with pre-aggregated metrics

---

### Data Volume Comparison

**Metric-Based:**
- 1 row per (date, property_type, location) combination
- ~500 locations × 5 property types × 12 months = **30,000 rows/year**
- Storage: ~50MB/year

**Transaction-Based:**
- 1 row per transaction
- Singapore: ~30,000 transactions/year
- 10-year history: **300,000 rows**
- Storage: ~500MB (10 years)

**Hybrid Approach (Actual):**
- Store both (metrics for speed, transactions for audit)
- Query metrics by default
- Drill down to transactions when needed

---

## External Data Sources

### 1. URA (Urban Redevelopment Authority)

**Data Provided:**
- Property price indices (PPI)
- Rental indices (RRI)
- Transaction volumes
- GFA approvals

**Ingestion:**
```python
# File: jurisdictions/sg_bca/ura_integration.py
from app.services.agents.ura_integration import ura_service

# Fetch latest index
index_data = await ura_service.get_property_price_index()

# Save to market_indices table
await save_market_index(index_data)
```

**Frequency:** Monthly (official release)

---

### 2. JTC (Jurong Town Corporation)

**Data Provided:**
- Industrial property data
- Factory space metrics
- Warehouse absorption rates

**Usage:** Populate `yield_benchmarks` and `absorption_tracking` for industrial properties

---

### 3. PropertyGuru / EdgeProp (Listing APIs)

**Data Provided:**
- Active rental listings
- Asking rents (PSF)
- Occupancy indicators

**Usage:** Populate `rental_listings` table, used to calculate `rental_psf` benchmarks

---

## Query Patterns

### Pattern 1: Get Market Benchmarks

```python
# Get latest cap rate for CBD offices
from app.models.market import YieldBenchmark
from app.models.property import PropertyType

benchmark = await session.execute(
    select(YieldBenchmark)
    .where(YieldBenchmark.district == "CBD")
    .where(YieldBenchmark.property_type == PropertyType.OFFICE)
    .order_by(YieldBenchmark.benchmark_date.desc())
    .limit(1)
)
result = benchmark.scalar_one_or_none()

# Returns: cap_rate_median, rental_psf_median, etc.
```

---

### Pattern 2: Track Absorption Over Time

```python
# Get absorption history for a project
from app.models.market import AbsorptionTracking

history = await session.execute(
    select(AbsorptionTracking)
    .where(AbsorptionTracking.project_id == project_id)
    .order_by(AbsorptionTracking.tracking_date)
)
absorption_data = history.scalars().all()

# Plot sales_absorption_rate over time
```

---

### Pattern 3: Identify Market Phase

```python
# Get current market cycle for office properties
from app.models.market import MarketCycle

cycle = await session.execute(
    select(MarketCycle)
    .where(MarketCycle.property_type == PropertyType.OFFICE)
    .where(MarketCycle.market_segment == "CBD")
    .order_by(MarketCycle.cycle_date.desc())
    .limit(1)
)
market_phase = cycle.scalar_one_or_none()

# Returns: expansion, recovery, hyper_supply, or recession
```

---

### Pattern 4: Compare to Competitive Set

```python
# Get competitive set metrics
from app.models.market import CompetitiveSet

comp_set = await session.execute(
    select(CompetitiveSet)
    .where(CompetitiveSet.primary_property_id == property_id)
    .where(CompetitiveSet.is_active == True)
)
metrics = comp_set.scalar_one_or_none()

# Compare property performance to competitive set
property_rental = 14.50  # Subject property
comp_avg = metrics.avg_rental_psf  # 13.20
performance = ((property_rental - comp_avg) / comp_avg) * 100
# Result: +9.8% premium vs competitive set
```

---

## Schema Evolution

### Future Enhancements

**Short-term:**
1. Add `market_forecasts` table (predicted values)
2. Add `tenant_profiles` table (occupier analytics)
3. Add `lease_comps` table (comparable leases)

**Medium-term:**
1. Add spatial analysis tables (heat maps)
2. Add sentiment indicators (news/social media)
3. Add development pipeline tracking

**Long-term:**
1. Machine learning feature store
2. Real-time streaming data (IoT sensors)
3. Alternative data sources (satellite, mobile location)

---

## Related Documentation

- [architecture_honest.md](architecture_honest.md) - Current system architecture
- [feasibility.md](feasibility.md) - How market data feeds feasibility analysis
- [ingestion.md](ingestion.md) - Data ingestion pipelines

---

**Last Updated:** 2025-10-22
**Schema Version:** 1.0
**Next Review:** Q1 2026 (or when adding forecast models)
