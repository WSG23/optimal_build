# Jurisdiction Expansion Playbook

**Version:** 1.0
**Last Updated:** 2025-10-23
**Purpose:** Step-by-step guide for adding new jurisdictions to the optimal_build platform

---

## 📋 Table of Contents

1. [Purpose & When to Use](#purpose--when-to-use)
2. [Prerequisites](#prerequisites)
3. [PM Preparation Checklist](#pm-preparation-checklist)
4. [Codex Workflow: Adding a Jurisdiction](#codex-workflow-adding-a-jurisdiction)
5. [Claude Workflow: Testing & Validation](#claude-workflow-testing--validation)
6. [PM Validation Checklist](#pm-validation-checklist)
7. [Completion Gate](#completion-gate)
8. [Troubleshooting Guide](#troubleshooting-guide)
9. [Reference: Existing Jurisdictions](#reference-existing-jurisdictions)

---

## 1. Purpose & When to Use

### Purpose

This playbook provides a reusable, step-by-step process for adding new jurisdictions to the platform. It ensures consistency across all jurisdiction additions and captures lessons learned from previous expansions.

### When to Use This Playbook

**Expansion Window 1: After Phase 2C (Dec 2025 - Jan 2026)**
- Add: Hong Kong, New Zealand, Washington State (Seattle), Ontario (Toronto)
- Goal: Validate multi-jurisdiction architecture before Phase 2D-6

**Expansion Window 2: After Phase 6 (2027+)**
- Add: UK, Australia, Ireland, Vancouver, California, etc.
- Goal: Scale to mature platform across 10+ jurisdictions

**Ad-hoc Additions:**
- Customer-requested jurisdictions (e.g., "We need Dubai for Client X")
- Strategic market expansions

### Who Uses This Playbook

- **PM (You):** Follow "PM Preparation Checklist" (Section 3) and "PM Validation Checklist" (Section 6)
- **Codex (AI Agent):** Follow "Codex Workflow" (Section 4) for implementation
- **Claude (AI Agent):** Follow "Claude Workflow" (Section 5) for testing and bug fixes

---

## 2. Prerequisites

### Before Starting Any Jurisdiction Addition

**System Requirements:**
- [ ] All existing jurisdictions have `make verify` passing
- [ ] Previous jurisdiction expansion complete (or Singapore baseline complete)
- [ ] No blocking bugs in current jurisdictions
- [ ] Git branch created for new jurisdiction work

**Project Status:**
- [ ] Phase 2C complete (for Expansion Window 1)
- [ ] Phase 6 complete (for Expansion Window 2)
- [ ] PM has approved jurisdiction for addition

**Architecture Validation:**
- [ ] Jurisdiction plugin system exists (`core/registry.py`, `JurisdictionParser` protocol)
- [ ] RefRule database supports `jurisdiction` field
- [ ] Services support `jurisdiction` parameter (after first new jurisdiction added)

**Environment:**
- [ ] Database accessible
- [ ] `.env` file configured with existing API keys
- [ ] `make dev` runs successfully for current jurisdictions

---

## 3. PM Preparation Checklist

### Overview

**Critical:** Codex and Claude cannot gather this data autonomously. You (PM) must research and provide it BEFORE asking AI agents to build.

**Estimated time:** 2-3 days per jurisdiction

---

### 3.1 API Access & Credentials

**Government Data Portal:**
- [ ] Identify primary government open data portal
  - Examples: DATA.GOV.HK (Hong Kong), LINZ (New Zealand), Seattle Open Data
- [ ] Create account (if required)
- [ ] Obtain API key (if required)
- [ ] Document API endpoints for:
  - [ ] Land registry/property data
  - [ ] Planning/zoning data
  - [ ] Building regulations
  - [ ] Heritage/conservation data (if available)
- [ ] Test API access (make a sample request)

**Geocoding:**
- [ ] Decide: Use local government geocoding (free) or Google Maps (paid)?
- [ ] If Google Maps: Ensure `GOOGLE_MAPS_API_KEY` env var is set
- [ ] If local government: Document API endpoint and authentication

**Example for Hong Kong:**
```bash
# .env additions needed
HK_DATA_GOV_API_KEY=your_key_here
GOOGLE_MAPS_API_KEY=your_existing_key  # For HK geocoding
```

**Example for New Zealand:**
```bash
# LINZ Data Service (free, no key needed)
NZ_LINZ_BASE_URL=https://data.linz.govt.nz/services
```

---

### 3.2 Market Data (Financial Modeling)

**Rent Data (in local currency):**
- [ ] Office rent per sqft/month (or per sqm/month)
- [ ] Retail rent per sqft/month
- [ ] Residential rent per sqft/month
- [ ] Industrial rent per sqft/month

**Operating Expenses (OPEX) Assumptions:**
- [ ] Property tax rate (% of property value or annual fixed amount)
- [ ] Management fees (% of gross revenue)
- [ ] Utilities (% of gross revenue or fixed amount)
- [ ] Insurance (% of property value)
- [ ] Maintenance/repairs (% of gross revenue)

**Vacancy Rates:**
- [ ] Office vacancy rate (%)
- [ ] Retail vacancy rate (%)
- [ ] Residential vacancy rate (%)
- [ ] Industrial vacancy rate (%)

**Other Financial Assumptions:**
- [ ] Typical construction loan interest rate (%)
- [ ] Typical equity/debt split (e.g., 30/70)
- [ ] Average exit cap rate (%)

**Data Source Examples:**
- Government statistics agencies (e.g., Census, Bureau of Statistics)
- Commercial real estate reports (CBRE, JLL, Colliers, Knight Frank)
- Industry associations (e.g., Urban Land Institute)
- Local broker contacts

**Template (copy to separate document):**
```yaml
{JURISDICTION}_MARKET_DATA:
  currency: "HKD"  # or "NZD", "USD", "CAD", etc.
  units: "sqft"    # or "sqm"

  rent_psf_month:
    office: 12.00      # HKD/sqft/month
    retail: 18.00
    residential: 8.50
    industrial: 6.00

  opex_assumptions:
    property_tax_percent: 5.0
    management_fee_percent: 3.0
    utilities_percent: 2.0
    insurance_percent: 0.5
    maintenance_percent: 2.5

  vacancy_rates:
    office: 0.08       # 8%
    retail: 0.05       # 5%
    residential: 0.04  # 4%
    industrial: 0.10   # 10%

  finance_assumptions:
    construction_loan_rate: 4.5
    equity_debt_split: [30, 70]
    exit_cap_rate: 5.0
```

---

### 3.3 Regulatory Data (Zoning & Building Codes)

**Building Code:**
- [ ] Identify official building code document
- [ ] Document URL or source
- [ ] Note key differences from Singapore:
  - Different height limits?
  - Different floor-to-floor height standards?
  - Different plot ratio calculation methods?

**Zoning Regulations:**
- [ ] List 5-10 primary zoning codes
  - Examples: Commercial, Residential, Industrial, Mixed-Use, Open Space
- [ ] For each zone, document:
  - [ ] Maximum plot ratio (FAR/GFA ratio)
  - [ ] Maximum building height (meters)
  - [ ] Maximum site coverage (%)
  - [ ] Allowed uses
  - [ ] Special conditions (if any)

**Template (copy to separate document):**
```yaml
{JURISDICTION}_ZONING_CODES:
  - code: "HK:Commercial"
    name: "Commercial"
    max_plot_ratio: 15.0
    max_height_m: 200.0
    max_site_coverage: 100.0
    allowed_uses: ["Office", "Retail", "Hotel", "Restaurant"]
    special_conditions: "Subject to urban design guidelines"

  - code: "HK:Residential"
    name: "Residential"
    max_plot_ratio: 8.0
    max_height_m: 100.0
    max_site_coverage: 50.0
    allowed_uses: ["Residential", "Community Facilities"]
    special_conditions: "Minimum unit size applies"

  # Add 3-8 more zones
```

**Where to find zoning data:**
- Government planning department websites
- Municipal zoning maps (often available as PDFs or GIS data)
- Planning consultants (may need to hire for complex jurisdictions)

---

### 3.4 Heritage/Conservation Data

**Heritage Sites:**
- [ ] Identify official heritage/conservation authority
  - Examples: Antiquities and Monuments Office (HK), Heritage NZ, Seattle Landmarks Board
- [ ] Check if GIS data or API available
- [ ] Download heritage site boundaries (GeoJSON, Shapefile, KML, or API)
- [ ] Document coordinate reference system (CRS) - most use WGS84 (EPSG:4326)

**Example Sources:**
- Hong Kong: Antiquities and Monuments Office (AAM)
- New Zealand: Heritage New Zealand Pouhere Taonga
- Seattle: Seattle Landmarks Preservation Board
- Toronto: Heritage Toronto

**If NO API/GIS data available:**
- [ ] Document manual process (e.g., "Download PDF map, manually trace boundaries")
- [ ] Or note "Heritage data not available for this jurisdiction"

---

### 3.5 Validation Data

**Test Addresses (for geocoding validation):**
- [ ] List 3-5 well-known addresses in jurisdiction
- [ ] Include expected latitude/longitude (use Google Maps to verify)

**Template:**
```yaml
{JURISDICTION}_TEST_ADDRESSES:
  - address: "1 Connaught Place, Central, Hong Kong"
    expected_lat: 22.2830
    expected_lon: 114.1580
    description: "IFC Mall, Central"

  - address: "8 Finance Street, Central, Hong Kong"
    expected_lat: 22.2850
    expected_lon: 114.1586
    description: "Two IFC Tower"

  # Add 3 more
```

**Known Developments (for calculation validation):**
- [ ] Find 1-2 completed developments with public data
- [ ] Document: site area, GFA, height, plot ratio
- [ ] Use these to validate your calculations match reality

**Template:**
```yaml
{JURISDICTION}_VALIDATION_PROJECTS:
  - name: "International Finance Centre (IFC)"
    address: "1 Harbour View Street, Central"
    site_area_sqm: 18000
    gfa_sqm: 436000
    plot_ratio: 24.2     # GFA/site area - should match our calculations
    height_m: 420
    source: "https://en.wikipedia.org/wiki/Two_International_Finance_Centre"
```

---

### 3.6 PM Checklist Summary

**Before asking Codex to add a jurisdiction, you MUST have:**

- [ ] ✅ API keys obtained and tested
- [ ] ✅ Market data gathered (rent, OPEX, vacancy) in structured format
- [ ] ✅ Zoning codes documented (minimum 5 zones)
- [ ] ✅ Building code source identified
- [ ] ✅ Heritage data sourced (or marked "not available")
- [ ] ✅ Test addresses prepared (3-5 with lat/lon)
- [ ] ✅ Validation projects identified (1-2)
- [ ] ✅ All data saved to document (e.g., `{jurisdiction}_prep_data.md`)

**Handoff to Codex:**
Provide PM prep document to Codex with instruction:
```
"Codex, add {Jurisdiction Name} jurisdiction using the data in {jurisdiction}_prep_data.md.
Follow the Codex Workflow in docs/jurisdiction_expansion_playbook.md."
```

---

## 4. Codex Workflow: Adding a Jurisdiction

### Overview

Codex will:
1. Create jurisdiction plugin structure
2. Implement fetch.py and parse.py
3. Refactor services for jurisdiction-awareness (first new jurisdiction only)
4. Seed RefRule database with zoning rules
5. Add market data to finance services
6. Update tests

**Estimated time:**
- **First new jurisdiction (e.g., Hong Kong):** 2-3 weeks (includes service refactoring)
- **Subsequent jurisdictions:** 1 week (pattern exists)

---

### Step 1: Create Jurisdiction Plugin Structure

**Naming Convention:**
- Singapore: `sg_bca`
- Hong Kong: `hk`
- New Zealand: `nz`
- US States: `us_{state_code}` (e.g., `us_wa` for Washington State)
- Canadian Provinces: `ca_{province_code}` (e.g., `ca_on` for Ontario)

**Command:**
```bash
# Replace {code} with jurisdiction code
mkdir -p jurisdictions/{code}/
touch jurisdictions/{code}/__init__.py
touch jurisdictions/{code}/fetch.py
touch jurisdictions/{code}/parse.py
touch jurisdictions/{code}/README.md
touch jurisdictions/{code}/map_overrides.yaml  # Optional
```

**Example for Hong Kong:**
```bash
mkdir -p jurisdictions/hk/
touch jurisdictions/hk/__init__.py
touch jurisdictions/hk/fetch.py
touch jurisdictions/hk/parse.py
touch jurisdictions/hk/README.md
```

---

### Step 2: Implement fetch.py

**Purpose:** Download regulations/rules from government API and convert to `ProvenanceRecord` format

**Reference:** `jurisdictions/sg_bca/fetch.py` (lines 1-313)

**Key requirements:**
- Must implement `fetch(since: date) -> Iterable[ProvenanceRecord]` function
- Should handle pagination if API returns large datasets
- Should include retry logic for transient failures
- Should support mock data for offline development

**Template:** (See `jurisdictions/sg_bca/fetch.py` for detailed structure)

**Minimal implementation:**
```python
"""HTTP fetcher for {Jurisdiction Name} government data."""

from datetime import date
from collections.abc import Iterable
import json
from core.canonical_models import ProvenanceRecord
from backend._compat.datetime import UTC
from datetime import datetime

def fetch(since: date) -> Iterable[ProvenanceRecord]:
    """Fetch regulations since date from {Government Portal}."""

    # TODO: Implement API fetching logic
    # For now, return mock data

    mock_record = ProvenanceRecord(
        regulation_external_id="MOCK-001",
        source_uri="https://example.gov/{jurisdiction}",
        fetched_at=datetime.now(UTC),
        fetch_parameters={"since": since.isoformat()},
        raw_content=json.dumps({
            "id": "MOCK-001",
            "title": "Mock Zoning Regulation",
            "zone": "Commercial",
            "max_plot_ratio": 5.0,
        }),
    )

    return [mock_record]
```

**Production implementation:** Add API client, pagination, error handling (see SG BCA example)

---

### Step 3: Implement parse.py

**Purpose:** Convert jurisdiction-specific data format to `CanonicalReg` format

**Reference:** `jurisdictions/sg_bca/parse.py` (lines 1-410)

**Key requirements:**
- Must expose `PARSER: JurisdictionParser` instance at module level
- Must implement `code`, `display_name`, `fetch_raw()`, `parse()`, `map_overrides_path()`
- Should extract: external_id, title, text, issued_on, effective_on, metadata

**Minimal implementation:**
```python
"""Parser for {Jurisdiction Name} government data."""

from datetime import date
from collections.abc import Iterable
from pathlib import Path
from backend._compat import compat_dataclass
from core.canonical_models import CanonicalReg, ProvenanceRecord
from core.registry import JurisdictionParser
from . import fetch
import json

@compat_dataclass(slots=True)
class {Jurisdiction}Parser:
    """Parser for {Jurisdiction}."""

    code: str = "{code}"
    display_name: str = "{Full Jurisdiction Name}"

    def fetch_raw(self, since: date) -> Iterable[ProvenanceRecord]:
        return fetch.fetch(since)

    def parse(self, records: Iterable[ProvenanceRecord]) -> Iterable[CanonicalReg]:
        """Transform raw payloads into canonical regulations."""
        regulations = []

        for record in records:
            payload = json.loads(record.raw_content)

            regulation = CanonicalReg(
                jurisdiction_code=self.code,
                external_id=payload.get("id", "UNKNOWN"),
                title=payload.get("title", "Untitled"),
                text=payload.get("description", "No description"),
                issued_on=None,  # TODO: Parse date
                effective_on=None,
                version=None,
                metadata={"source_uri": record.source_uri},
                global_tags=[],
            )

            regulations.append(regulation)

        return regulations

    def map_overrides_path(self) -> Path | None:
        return Path(__file__).resolve().parent / "map_overrides.yaml"

# REQUIRED: Export PARSER instance
PARSER: JurisdictionParser = {Jurisdiction}Parser()
```

**Production implementation:** Add robust date parsing, field extraction, tag mapping (see SG BCA example)

---

### Step 4: Refactor Services for Jurisdiction-Awareness

**⚠️ ONLY REQUIRED FOR FIRST NEW JURISDICTION**

If adding Hong Kong (first after Singapore), you must refactor services to support `jurisdiction` parameter.

If adding New Zealand (second), Seattle (third), Toronto (fourth), skip this step - pattern already exists.

---

#### 4.1 Update geocoding.py

**File:** `backend/app/services/geocoding.py`

**Find method:**
```python
async def reverse_geocode(self, latitude: float, longitude: float) -> Optional[Address]:
```

**Change to:**
```python
async def reverse_geocode(
    self, latitude: float, longitude: float, jurisdiction: str
) -> Optional[Address]:
    """Convert coordinates to address using jurisdiction-specific geocoding."""

    if jurisdiction == "SG":
        return await self._onemap_geocode(latitude, longitude)
    elif jurisdiction in ["HK", "NZ", "US_WA", "CA_ON"]:
        # Use Google Maps for non-Singapore jurisdictions
        return await self._google_geocode(latitude, longitude)
    else:
        logger.warning(f"Unsupported jurisdiction for geocoding: {jurisdiction}")
        return await self._google_geocode(latitude, longitude)  # Fallback
```

**Also add Google Maps implementation if not exists:**
```python
async def _google_geocode(self, latitude: float, longitude: float) -> Optional[Address]:
    """Geocode using Google Maps API (works globally)."""

    if not self.google_maps_api_key:
        logger.error("Google Maps API key not configured")
        return self._build_mock_address(latitude, longitude)

    try:
        response = await self.client.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params={
                "latlng": f"{latitude},{longitude}",
                "key": self.google_maps_api_key,
            }
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("results"):
                result = data["results"][0]
                return Address(
                    full_address=result.get("formatted_address", "Unknown"),
                    country=self._extract_country(result),
                )

        return self._build_mock_address(latitude, longitude)

    except Exception as e:
        logger.error(f"Google geocoding error: {e}")
        return self._build_mock_address(latitude, longitude)
```

---

#### 4.2 Update finance/asset_models.py

**File:** `backend/app/services/finance/asset_models.py`

**Add jurisdiction-aware market data:**
```python
# Market data by jurisdiction (use PM-provided data)
MARKET_DATA = {
    "SG": {
        "currency": "SGD",
        "units": "sqm",
        "rent_psf_month": {
            "office": 8.50,
            "retail": 12.00,
            "residential": 6.00,
            "industrial": 4.00,
        },
        "opex_percent": {
            "property_tax": 4.0,
            "management": 3.0,
            "utilities": 2.0,
            "insurance": 0.5,
            "maintenance": 2.5,
        },
        "vacancy_rate": {
            "office": 0.07,
            "retail": 0.05,
            "residential": 0.04,
            "industrial": 0.08,
        },
    },
    "{CODE}": {
        "currency": "{CURRENCY}",
        "units": "{sqft or sqm}",
        "rent_psf_month": {
            # Copy from PM prep data
            "office": 12.00,
            "retail": 18.00,
            "residential": 8.50,
            "industrial": 6.00,
        },
        "opex_percent": {
            # Copy from PM prep data
            "property_tax": 5.0,
            "management": 3.0,
            "utilities": 2.0,
            "insurance": 0.5,
            "maintenance": 2.5,
        },
        "vacancy_rate": {
            # Copy from PM prep data
            "office": 0.08,
            "retail": 0.05,
            "residential": 0.04,
            "industrial": 0.10,
        },
    },
}

def get_rent_psf(asset_type: str, jurisdiction: str) -> float:
    """Get rent PSF for asset type in jurisdiction."""
    if jurisdiction not in MARKET_DATA:
        raise ValueError(f"No market data for jurisdiction: {jurisdiction}")
    return MARKET_DATA[jurisdiction]["rent_psf_month"][asset_type]

def get_opex_percent(category: str, jurisdiction: str) -> float:
    """Get OPEX percentage for category in jurisdiction."""
    return MARKET_DATA[jurisdiction]["opex_percent"][category]

def get_vacancy_rate(asset_type: str, jurisdiction: str) -> float:
    """Get vacancy rate for asset type in jurisdiction."""
    return MARKET_DATA[jurisdiction]["vacancy_rate"][asset_type]

def get_currency(jurisdiction: str) -> str:
    """Get currency code for jurisdiction."""
    return MARKET_DATA[jurisdiction]["currency"]
```

---

#### 4.3 Rename compliance.py

**Rename file:**
```bash
mv backend/app/utils/singapore_compliance.py backend/app/utils/compliance.py
```

**Update imports across codebase:**
```bash
# Find all files importing singapore_compliance
grep -r "from app.utils.singapore_compliance" backend/

# Update each to:
# from app.utils.compliance import ...
```

**Generalize compliance functions:**
```python
# backend/app/utils/compliance.py

async def check_zoning_compliance(
    property: Property,
    session: AsyncSession,
    jurisdiction: str
) -> Dict[str, Any]:
    """Check zoning compliance for any jurisdiction."""

    # Query RefRule database for jurisdiction-specific rules
    stmt = select(RefRule).where(
        RefRule.jurisdiction == jurisdiction,  # Dynamic!
        RefRule.topic == "zoning",
        RefRule.review_status == "approved",
        RefRule.is_published,
    )

    result = await session.execute(stmt)
    all_rules = result.scalars().all()

    # Rest of logic remains similar
    # ...
```

---

### Step 5: Seed RefRule Database

**Create seed script:** `backend/scripts/seed_{jurisdiction}_rules.py`

**Use PM-provided zoning data** to populate RefRule database.

**Template:**
```python
"""Seed {Jurisdiction} zoning rules into RefRule database."""

import asyncio
from datetime import datetime
from sqlalchemy import select
from app.core.database import get_async_session_factory
from app.models.rkp import RefRule, RefSource

async def seed_{jurisdiction}_rules():
    """Seed {Jurisdiction} zoning rules."""

    session_factory = get_async_session_factory()

    async with session_factory() as session:
        # Create RefSource
        stmt = select(RefSource).where(
            RefSource.jurisdiction == "{CODE}",
            RefSource.authority == "PLANNING"
        )
        source = await session.execute(stmt)
        source = source.scalar_one_or_none()

        if not source:
            source = RefSource(
                jurisdiction="{CODE}",
                authority="PLANNING",
                source_name="{Government Planning Authority}",
                source_uri="{URL}",
                fetch_enabled=True,
            )
            session.add(source)
            await session.flush()

        # Add zoning rules from PM prep data
        rules = [
            RefRule(
                jurisdiction="{CODE}",
                authority="PLANNING",
                source_id=source.id,
                topic="zoning",
                parameter_key="zoning.max_far",
                value="5.0",  # From PM data
                applicability={"zone_code": "{CODE}:Commercial"},
                citation="Building Code Section X",
                review_status="approved",
                is_published=True,
                effective_date=datetime(2020, 1, 1),
            ),
            RefRule(
                jurisdiction="{CODE}",
                authority="PLANNING",
                source_id=source.id,
                topic="zoning",
                parameter_key="zoning.max_building_height_m",
                value="50.0",  # From PM data
                applicability={"zone_code": "{CODE}:Commercial"},
                citation="Building Code Section Y",
                review_status="approved",
                is_published=True,
                effective_date=datetime(2020, 1, 1),
            ),
            # Add rules for Residential, Industrial, Mixed-Use, etc.
        ]

        for rule in rules:
            session.add(rule)

        await session.commit()
        print(f"✅ Seeded {len(rules)} {jurisdiction} rules")

if __name__ == "__main__":
    asyncio.run(seed_{jurisdiction}_rules())
```

**Run script:**
```bash
cd backend
python -m scripts.seed_{jurisdiction}_rules
```

**Verify:**
```bash
psql $DATABASE_URL -c "SELECT COUNT(*) FROM ref_rules WHERE jurisdiction='{CODE}';"
# Should return number of rules added
```

---

### Step 6: Add Heritage Overlay Data (Optional)

**If PM provided heritage GIS data:**

```bash
mkdir -p data/heritage/{code}/raw
mkdir -p data/heritage/{code}/processed

# Copy PM-provided data
cp {source_file} data/heritage/{code}/raw/heritage_sites.geojson
```

**Update heritage service:**

**File:** `backend/app/services/heritage_overlay.py`

```python
def get_heritage_data(jurisdiction: str) -> dict:
    """Load heritage overlay data for jurisdiction."""

    heritage_files = {
        "SG": "backend/app/data/heritage_overlays.geojson",
        "{CODE}": "data/heritage/{code}/processed/heritage_overlays.geojson",
    }

    if jurisdiction not in heritage_files:
        return {"type": "FeatureCollection", "features": []}

    file_path = heritage_files[jurisdiction]
    if not os.path.exists(file_path):
        return {"type": "FeatureCollection", "features": []}

    with open(file_path) as f:
        return json.load(f)
```

**If NO heritage data:**
- Skip this step
- Service returns empty FeatureCollection (no overlays shown)

---

### Step 7: Update Tests

**Add test fixtures:**

**File:** `backend/tests/conftest.py`

```python
@pytest.fixture
def {jurisdiction}_property():
    """Test property in {Jurisdiction}."""
    return SiteAcquisition(
        latitude={test_lat},  # From PM test addresses
        longitude={test_lon},
        jurisdiction="{CODE}",
        address="{test_address}",
        land_area_sqm=5000.0,
        zoning="{CODE}:Commercial",
    )
```

**Create test file:**

**File:** `backend/tests/test_jurisdictions/test_{code}.py`

```python
"""Tests for {Jurisdiction} jurisdiction."""

import pytest
from app.services.geocoding import GeocodingService
from app.services.finance.asset_models import get_rent_psf
from sqlalchemy import select
from app.models.rkp import RefRule


@pytest.mark.asyncio
async def test_{jurisdiction}_geocoding({jurisdiction}_property):
    """Test geocoding works for {Jurisdiction}."""
    geocoder = GeocodingService()
    address = await geocoder.reverse_geocode(
        {jurisdiction}_property.latitude,
        {jurisdiction}_property.longitude,
        jurisdiction="{CODE}"
    )
    assert address is not None


def test_{jurisdiction}_market_data():
    """Test market data exists for {Jurisdiction}."""
    rent = get_rent_psf("office", jurisdiction="{CODE}")
    assert rent > 0


@pytest.mark.asyncio
async def test_{jurisdiction}_refRule_query(async_session):
    """Test RefRule database has {Jurisdiction} rules."""
    stmt = select(RefRule).where(RefRule.jurisdiction == "{CODE}")
    result = await async_session.execute(stmt)
    rules = result.scalars().all()
    assert len(rules) > 0, f"No RefRule entries found for {CODE}"
```

---

### Step 8: Document in README.md

**File:** `jurisdictions/{code}/README.md`

```markdown
# {Jurisdiction Name} Fetcher

Integration with {Government Portal Name} for building regulations and zoning data.

## Configuration

Environment variables:

| Variable | Description |
|----------|-------------|
| `{JURISDICTION}_API_KEY` | API key for {Government Portal} |
| `{JURISDICTION}_BASE_URL` | API endpoint (defaults to `{url}`) |
| `GOOGLE_MAPS_API_KEY` | For geocoding (required) |

## Data Sources

- **Planning/Zoning:** {Government Department URL}
- **Building Code:** {Building Code URL}
- **Heritage:** {Heritage Authority URL or "Not available"}

## Testing

```bash
python -m scripts.ingest --jurisdiction {code} --since 2025-01-01 --store $DATABASE_URL
```

## Market Data Sources

- Rent data: {Source, e.g., "CBRE Hong Kong Market Report Q4 2024"}
- OPEX assumptions: {Source}
- Vacancy rates: {Source}
```

---

### Codex Checklist: Before Marking Complete

- [ ] `jurisdictions/{code}/` created with fetch.py, parse.py, README.md
- [ ] PARSER instance exposed in parse.py
- [ ] Services refactored for jurisdiction (if first new jurisdiction)
- [ ] RefRule database seeded (seed script created and run)
- [ ] Market data added to asset_models.py
- [ ] Heritage data added (or skipped if unavailable)
- [ ] Tests created in `test_jurisdictions/test_{code}.py`
- [ ] `make verify` passes locally

**Handoff to Claude:** Request testing and bug fixes

---

## 5. Claude Workflow: Testing & Validation

### Overview

Claude runs tests, fixes failures, and validates jurisdiction works end-to-end.

**Estimated time:**
- First jurisdiction: 2-3 days
- Subsequent jurisdictions: 1 day

---

### Step 1: Run Test Suite

```bash
cd backend
make test
```

**Expected output:**
```
test_jurisdictions/test_{code}.py::test_{jurisdiction}_geocoding ✅
test_jurisdictions/test_{code}.py::test_{jurisdiction}_market_data ✅
test_jurisdictions/test_{code}.py::test_{jurisdiction}_refRule_query ✅
...
PASSED
```

**If failures occur, proceed to Step 2.**

---

### Step 2: Fix Common Test Failures

#### Failure Pattern 1: Missing `jurisdiction` parameter

**Error:**
```
TypeError: reverse_geocode() missing 1 required positional argument: 'jurisdiction'
```

**Fix:** Add jurisdiction parameter to all calling code

**Files to check:**
- `backend/app/api/v1/developers.py`
- `backend/app/api/v1/site_acquisition.py`
- `backend/tests/test_api/test_developer_site_acquisition.py`

**Example fix:**
```python
# Before:
address = await geocoder.reverse_geocode(lat, lon)

# After:
address = await geocoder.reverse_geocode(lat, lon, jurisdiction=property.jurisdiction)
```

---

#### Failure Pattern 2: RefRule query returns empty

**Error:**
```
AssertionError: No RefRule entries found for {CODE}
```

**Diagnosis:**
```bash
psql $DATABASE_URL -c "SELECT * FROM ref_rules WHERE jurisdiction='{CODE}' LIMIT 5;"
```

**If returns 0 rows:**
```bash
# Seed script didn't run or failed
cd backend
python -m scripts.seed_{jurisdiction}_rules
```

**If still failing:** Check jurisdiction code matches exactly (no typos, extra spaces)

---

#### Failure Pattern 3: Currency formatting wrong

**Error:**
```
AssertionError: Expected HK$, got S$
```

**Fix:** Update currency formatter

**File:** `backend/app/services/finance/calculator.py`

```python
def get_currency_symbol(jurisdiction: str) -> str:
    symbols = {
        "SG": "S$",
        "HK": "HK$",
        "NZ": "NZ$",
        "US_WA": "$",
        "CA_ON": "C$",
    }
    return symbols.get(jurisdiction, "$")
```

---

#### Failure Pattern 4: Unit conversion (sqft vs sqm)

**Error:**
```
AssertionError: Rent calculation off by factor of 10.764
```

**Fix:** Check if jurisdiction uses sqft or sqm

```python
SQFT_JURISDICTIONS = ["HK", "US_WA", "CA_ON"]
SQM_JURISDICTIONS = ["SG", "NZ"]

def normalize_area(area_sqm: float, jurisdiction: str) -> float:
    """Convert area to jurisdiction's preferred units."""
    if jurisdiction in SQFT_JURISDICTIONS:
        return area_sqm * 10.764  # Convert to sqft
    return area_sqm  # Keep sqm
```

---

### Step 3: Run Integration Test

**File:** `backend/tests/test_integration/test_{code}_full_workflow.py`

**Create if doesn't exist:**
```python
"""Integration test: GPS → Feasibility → Finance for {Jurisdiction}."""

import pytest

@pytest.mark.asyncio
async def test_{jurisdiction}_full_workflow(async_session, {jurisdiction}_property):
    """Test complete workflow."""

    from app.services.geocoding import GeocodingService
    from app.services.buildable import BuildableService, BuildableInput
    from app.services.finance.calculator import calculate_feasibility

    # Step 1: Geocoding
    geocoder = GeocodingService()
    address = await geocoder.reverse_geocode(
        {jurisdiction}_property.latitude,
        {jurisdiction}_property.longitude,
        jurisdiction="{CODE}"
    )
    assert address is not None

    # Step 2: Buildable calculation
    buildable_service = BuildableService(async_session)
    buildable_calc = await buildable_service.calculate_parameters(
        BuildableInput(
            land_area={jurisdiction}_property.land_area_sqm,
            zone_code="{CODE}:Commercial",
            plot_ratio=None,  # Should come from RefRule
        )
    )
    assert buildable_calc.metrics.gfa_cap_m2 > 0

    # Step 3: Finance
    finance_result = await calculate_feasibility(
        session=async_session,
        project_id=1,
        scenario_data={
            "site_area_m2": {jurisdiction}_property.land_area_sqm,
            "gfa_m2": buildable_calc.metrics.gfa_cap_m2,
            "jurisdiction": "{CODE}",
        }
    )
    assert finance_result["npv"] is not None
```

**Run:**
```bash
pytest backend/tests/test_integration/test_{code}_full_workflow.py -v
```

---

### Step 4: Regression Test (Singapore)

**Ensure Singapore still works:**

```bash
pytest backend/tests/test_integration/test_sg_full_workflow.py -v
```

**If Singapore tests fail:**
- Refactoring broke something
- Check `jurisdiction="SG"` is passed in Singapore tests
- Verify MARKET_DATA still has "SG" entry

---

### Step 5: Final Validation

**Run full test suite:**
```bash
cd backend
make verify
```

**Should see:**
```
All tests passed ✅
Linting passed ✅
Type checking passed ✅
```

**Handoff to PM:** Request manual validation

---

## 6. PM Validation Checklist

### Overview

Manual testing in UI to validate real-world usage.

**Estimated time:** 1 day per jurisdiction

---

### 6.1 GPS Capture (Phase 2A)

**Test:**
1. Open browser: `http://localhost:4400/app/site-acquisition`
2. Select jurisdiction: `{Jurisdiction Name}` from dropdown
3. Enter test address (from PM prep checklist)
4. Click "Capture Site"

**Validation:**
- [ ] Map marker appears at correct location
- [ ] Address displayed matches test address
- [ ] Coordinates match expected lat/lon (±0.01 degrees)

**If failing:**
- Check browser console for JS errors
- Check Network tab for API errors
- Verify `GOOGLE_MAPS_API_KEY` in `.env`

---

### 6.2 Feasibility Analysis (Phase 2B)

**Test:**
1. After GPS capture, click "Analyze Feasibility"
2. Select asset type scenario
3. Wait for optimizer to run

**Validation:**
- [ ] Plot ratio matches jurisdiction rules (e.g., 5.0 for Commercial)
- [ ] GFA calculation reasonable (site area × plot ratio)
- [ ] Height limit applied (if defined)
- [ ] Heritage overlays display (if applicable)

**If failing:**
- Check RefRule database: `SELECT * FROM ref_rules WHERE jurisdiction='{CODE}' AND topic='zoning';`
- Check buildable service logs for errors

---

### 6.3 Finance Modeling (Phase 2C)

**Test:**
1. After feasibility, click "Generate Financial Model"
2. Review finance summary panel

**Validation:**
- [ ] Rent PSF matches PM-provided data
- [ ] Currency correct (HK$, NZ$, $, C$, etc.)
- [ ] OPEX percentages match PM data
- [ ] Vacancy rate applied correctly
- [ ] NPV/IRR seem reasonable

**Spot-check calculation:**
```
Expected monthly rent = GFA (sqft) × rent PSF × (1 - vacancy rate)

Example (Hong Kong, 100,000 sqft office):
= 100,000 × HK$12.00 × (1 - 0.08)
= HK$1,104,000/month
```

**If wrong:**
- Check MARKET_DATA in `asset_models.py`
- Check currency formatter
- Check unit conversion (sqft vs sqm)

---

### 6.4 Regression Test (Singapore)

**Test:**
1. Switch jurisdiction to "Singapore"
2. Enter Singapore test address
3. Run GPS → Feasibility → Finance

**Validation:**
- [ ] Singapore still works
- [ ] Rent values correct (S$8.50 office PSF)
- [ ] Plot ratios correct

---

### 6.5 PM Approval Decision

**Before approving:**
- [ ] All test workflows passed
- [ ] Calculations match expectations (validated against known projects)
- [ ] No major UI bugs
- [ ] Singapore regression test passed

**If approved:**
- Update `docs/ROADMAP.MD` and `docs/WORK_QUEUE.MD` → Mark jurisdiction ✅ and log follow-up actions
- Move to next jurisdiction (if in expansion window)

**If NOT approved:**
- Document issues
- Send back to Codex/Claude for fixes

---

## 7. Completion Gate

### Checklist

**Before marking jurisdiction as "Complete":**

**Code:**
- [ ] `jurisdictions/{code}/` exists with all files
- [ ] PARSER instance exposed in parse.py
- [ ] README.md documented

**Database:**
- [ ] RefRule has 10+ rules for jurisdiction
- [ ] RefSource entry exists
- [ ] Seed script created and run

**Services:**
- [ ] Geocoding supports jurisdiction
- [ ] Finance has market data
- [ ] Heritage data added (or N/A)

**Testing:**
- [ ] `make verify` passes
- [ ] Integration test passes
- [ ] Singapore regression passes

**PM Validation:**
- [ ] GPS capture tested
- [ ] Feasibility tested
- [ ] Finance tested
- [ ] PM approved

**Documentation:**
- [ ] `ROADMAP.MD` and `WORK_QUEUE.MD` updated
- [ ] `NEXT_STEPS` updated (if last jurisdiction)

---

## 8. Troubleshooting Guide

### RefRule queries return empty

**Symptom:** `AssertionError: No rules found for {CODE}`

**Fix:**
```bash
cd backend
python -m scripts.seed_{jurisdiction}_rules
psql $DATABASE_URL -c "SELECT COUNT(*) FROM ref_rules WHERE jurisdiction='{CODE}';"
```

---

### Geocoding fails

**Symptom:** `ERROR: Geocoding client unavailable`

**Fix:**
```bash
# Check .env
echo $GOOGLE_MAPS_API_KEY

# Add if missing
echo "GOOGLE_MAPS_API_KEY=your_key_here" >> .env
```

---

### Currency wrong

**Symptom:** Shows S$ instead of HK$

**Fix:** Check `get_currency_symbol()` in finance calculator

---

### Unit conversion issues

**Symptom:** Rent calculations off by 10x

**Fix:** Check if jurisdiction uses sqft (HK/US/CA) or sqm (SG/NZ)

---

## 9. Reference: Existing Jurisdictions

### Singapore (Baseline)

- **Code:** `sg_bca`
- **APIs:** OneMap, URA, BCA
- **Currency:** SGD
- **Units:** Square meters
- **Lessons:** OneMap very reliable, heritage data from NHB

### Future Jurisdictions (Expansion Window 2)

- UK (England & Wales)
- Australia (NSW, VIC)
- Ireland
- Canada (BC)
- US (California, Massachusetts)

**Expected effort:** 1 week each (pattern mature)

---

**END OF PLAYBOOK**
