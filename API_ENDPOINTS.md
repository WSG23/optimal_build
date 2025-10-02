# API Endpoints Documentation

**Base URL:** `http://localhost:9400`
**API Version:** `/api/v1`

All authenticated endpoints require JWT Bearer token in `Authorization` header:
```
Authorization: Bearer <access_token>
```

---

## Public Endpoints (No Auth Required)

### Root & Health Checks

#### `GET /`
Root endpoint showing API info.

**Response:**
```json
{
  "message": "Building Compliance Platform API",
  "version": "0.1.0",
  "docs": "/docs"
}
```

#### `GET /health`
Health check with database connectivity status.

**Response:**
```json
{
  "status": "healthy",
  "service": "Building Compliance Platform",
  "database": "connected",
  "rules_count": 18
}
```

#### `GET /health/metrics`
Prometheus metrics endpoint (returns plain text metrics).

#### `GET /docs`
Auto-generated Swagger/OpenAPI documentation (interactive API explorer).

#### `GET /redoc`
Alternative API documentation (ReDoc format).

---

## Authentication Endpoints

### `POST /api/v1/secure-users/signup`
Register a new user with validation and password hashing.

**Request Body:**
```json
{
  "email": "user@example.com",
  "username": "testuser",
  "full_name": "Test User",
  "password": "SecurePass123",
  "company_name": "Optional Company"
}
```

**Validation Rules:**
- Email: Valid email format
- Username: 3-50 chars, alphanumeric + underscores only
- Password: Min 8 chars, must contain uppercase, lowercase, number
- Full name: Cannot be empty/whitespace

**Response:** `201 Created`
```json
{
  "id": "user_74c9a2e6",
  "email": "user@example.com",
  "username": "testuser",
  "full_name": "Test User",
  "company_name": "Optional Company",
  "created_at": "2025-01-15T10:30:00",
  "is_active": true
}
```

### `POST /api/v1/secure-users/login`
Login with email and password to receive JWT tokens.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123"
}
```

**Response:** `200 OK`
```json
{
  "message": "Login successful",
  "user": {
    "id": "user_74c9a2e6",
    "email": "user@example.com",
    "username": "testuser",
    "full_name": "Test User",
    "company_name": null,
    "created_at": "2025-01-15T10:30:00",
    "is_active": true
  },
  "tokens": {
    "access_token": "eyJhbGc...",
    "refresh_token": "eyJhbGc...",
    "token_type": "bearer",
    "expires_in": 86400
  }
}
```

**Token Expiry:**
- Access token: 24 hours
- Refresh token: 7 days

---

## Projects API (Authenticated)

**Tag:** `Projects`
**Prefix:** `/api/v1/projects`

### `POST /api/v1/projects/create`
Create a new project for the authenticated user.

**Request Body:**
```json
{
  "name": "Marina Bay Development",
  "description": "Mixed-use residential and commercial",
  "location": "Marina Bay, Singapore",
  "project_type": "mixed_use",
  "status": "planning",
  "budget": 5000000.00
}
```

**Response:** `201 Created`
```json
{
  "id": "proj_a1b2c3d4",
  "name": "Marina Bay Development",
  "description": "Mixed-use residential and commercial",
  "location": "Marina Bay, Singapore",
  "project_type": "mixed_use",
  "status": "planning",
  "budget": 5000000.00,
  "owner_email": "user@example.com",
  "created_at": "2025-01-15T10:30:00",
  "updated_at": "2025-01-15T10:30:00",
  "is_active": true
}
```

### `GET /api/v1/projects/list`
Get all projects for the authenticated user.

**Response:** `200 OK`
```json
{
  "projects": [
    {
      "id": "proj_a1b2c3d4",
      "name": "Marina Bay Development",
      "status": "planning",
      "created_at": "2025-01-15T10:30:00"
    }
  ],
  "count": 1
}
```

### `GET /api/v1/projects/{project_id}`
Get a specific project by ID.

**Response:** `200 OK` (same structure as create response)

### `PUT /api/v1/projects/{project_id}`
Update a project (only owner can update).

**Request Body:** (all fields optional)
```json
{
  "name": "Updated Project Name",
  "status": "in_progress",
  "budget": 6000000.00
}
```

**Response:** `200 OK` (returns updated project)

### `DELETE /api/v1/projects/{project_id}`
Delete a project (soft delete - sets is_active=false).

**Response:** `200 OK`
```json
{
  "message": "Project deleted successfully",
  "project_id": "proj_a1b2c3d4"
}
```

---

## Singapore Property API (Authenticated)

**Tag:** `Singapore Property`
**Prefix:** `/api/v1/singapore-property`

### `POST /api/v1/singapore-property/create`
Create a new Singapore property with BCA/URA compliance validation.

**Request Body:**
```json
{
  "property_name": "Orchard Road Tower",
  "address": "123 Orchard Road",
  "postal_code": "238858",
  "zoning": "commercial",
  "tenure": "freehold",
  "land_area_sqm": 1500.0,
  "gross_plot_ratio": 3.5,
  "gross_floor_area_sqm": 5250.0,
  "building_height_m": 50.0,
  "num_storeys": 12,
  "acquisition_status": "available",
  "feasibility_status": "analyzing",
  "estimated_acquisition_cost": 10000000.00,
  "estimated_development_cost": 5000000.00,
  "expected_revenue": 20000000.00,
  "project_id": "proj_a1b2c3d4"
}
```

**Zoning Options:**
- `residential` - Residential zones
- `commercial` - Commercial zones
- `industrial` - Industrial/warehouse
- `mixed_use` - Mixed residential/commercial
- `business_park` - Business park zones

**Tenure Options:**
- `freehold` - Freehold ownership
- `leasehold_99` - 99-year lease
- `leasehold_999` - 999-year lease

**Response:** `201 Created`
```json
{
  "id": "prop_e5f6g7h8",
  "property_name": "Orchard Road Tower",
  "address": "123 Orchard Road",
  "postal_code": "238858",
  "zoning": "commercial",
  "tenure": "freehold",
  "land_area_sqm": 1500.0,
  "gross_plot_ratio": 3.5,
  "gross_floor_area_sqm": 5250.0,
  "building_height_m": 50.0,
  "num_storeys": 12,
  "acquisition_status": "available",
  "feasibility_status": "analyzing",
  "estimated_acquisition_cost": 10000000.00,
  "actual_acquisition_cost": null,
  "estimated_development_cost": 5000000.00,
  "expected_revenue": 20000000.00,
  "bca_compliance_status": "pending",
  "ura_compliance_status": "pending",
  "created_at": "2025-01-15T10:30:00",
  "updated_at": "2025-01-15T10:30:00"
}
```

### `GET /api/v1/singapore-property/list`
Get all properties for the authenticated user.

**Query Parameters:**
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Max records to return (default: 100)

**Response:** `200 OK`
```json
{
  "properties": [
    {
      "id": "prop_e5f6g7h8",
      "property_name": "Orchard Road Tower",
      "zoning": "commercial",
      "land_area_sqm": 1500.0,
      "feasibility_status": "analyzing"
    }
  ],
  "count": 1
}
```

### `GET /api/v1/singapore-property/{property_id}`
Get a specific property by ID.

**Response:** `200 OK` (same structure as create response)

### `PUT /api/v1/singapore-property/{property_id}`
Update a property.

**Request Body:** (all fields optional, same structure as create)

**Response:** `200 OK` (returns updated property)

### `DELETE /api/v1/singapore-property/{property_id}`
Delete a property.

**Response:** `200 OK`
```json
{
  "message": "Property deleted successfully",
  "property_id": "prop_e5f6g7h8"
}
```

### `POST /api/v1/singapore-property/calculate/buildable` ⭐
**NEW: Jurisdiction-Agnostic Buildable Calculation**

Calculate buildable metrics using database-driven building code rules (URA zoning + BCA requirements).

**Request Body:**
```json
{
  "land_area_sqm": 1500.0,
  "zoning": "residential",
  "jurisdiction": "SG"
}
```

**Response:** `200 OK`
```json
{
  "plot_ratio": 2.8,
  "max_height_m": 36.0,
  "site_coverage": 0.40,
  "max_gfa_sqm": 4200.0,
  "max_footprint_sqm": 600.0,
  "max_floors": 7,
  "net_saleable_area_sqm": 3444.0,
  "efficiency_ratio": 0.82,
  "floor_to_floor_height_m": 4.0
}
```

**How It Works:**
1. Queries RefRule database for rules matching `jurisdiction=SG` and `zone_code=SG:residential`
2. Loads both "zoning" (URA) and "building" (BCA) topic rules
3. Applies building science constants:
   - Floor-to-floor height: 4.0m (ceiling + slab + MEP space)
   - Efficiency ratio: 82% (accounts for walls, structure, circulation)
4. Returns constrained buildable metrics:
   - Max floors = min(height constraint, GFA constraint)
   - GFA = land_area × plot_ratio
   - Footprint = land_area × site_coverage
   - NSA = GFA × efficiency_ratio

**Database Rules Applied (18 Singapore Rules):**

| Authority | Topic | Parameter | Residential | Commercial | Industrial |
|-----------|-------|-----------|------------|------------|------------|
| URA | zoning | max_far (Plot Ratio) | 2.8 | 3.5 | 2.5 |
| URA | zoning | max_building_height_m | 36m | 50m | 40m |
| BCA | building | site_coverage.max_percent | 40% | 50% | 60% |

### `POST /api/v1/singapore-property/check-compliance` ⭐
**NEW: Pass/Fail Compliance Checking**

Check proposed building design against Singapore URA/BCA regulations. Compares proposed parameters against maximum allowed values from RefRule database and returns pass/fail status with detailed violations.

**Request Body:**
```json
{
  "land_area_sqm": 1500,
  "zoning": "residential",
  "proposed_gfa_sqm": 5000,
  "proposed_height_m": 40,
  "proposed_storeys": 10,
  "jurisdiction": "SG"
}
```

**Response:** `200 OK`

**PASSING Design Example:**
```json
{
  "status": "PASSED",
  "violations": [],
  "warnings": [],
  "recommendations": [
    "BCA Green Mark certification may be required for this development type",
    "Ensure compliance with BCA Accessibility Code (barrier-free access)",
    "SCDF Fire Safety Certificate required before obtaining Temporary Occupation Permit"
  ],
  "ura_check": {
    "status": "passed",
    "violations": [],
    "rules_applied": {
      "max_plot_ratio": "2.8",
      "max_height_m": "36"
    }
  },
  "bca_check": {
    "status": "passed",
    "violations": [],
    "requirements_applied": {
      "max_site_coverage": "0.4"
    }
  },
  "proposed_design": {
    "land_area_sqm": 1500.0,
    "zoning": "residential",
    "proposed_gfa_sqm": 4000.0,
    "proposed_height_m": 32.0,
    "proposed_storeys": 8,
    "calculated_plot_ratio": 2.67
  }
}
```

**FAILING Design Example:**
```json
{
  "status": "FAILED",
  "violations": [
    "Plot ratio 3.33 exceeds maximum 2.8 for residential zone",
    "Building height 40m exceeds maximum 36m for residential zone",
    "Actual plot ratio 3.33 (GFA/land area) exceeds maximum 2.8 for residential zone"
  ],
  "warnings": [],
  "recommendations": [
    "BCA Green Mark certification may be required for this development type",
    "Ensure compliance with BCA Accessibility Code (barrier-free access)",
    "SCDF Fire Safety Certificate required before obtaining Temporary Occupation Permit"
  ],
  "ura_check": {
    "status": "failed",
    "violations": [
      "Plot ratio 3.33 exceeds maximum 2.8 for residential zone",
      "Building height 40m exceeds maximum 36m for residential zone",
      "Actual plot ratio 3.33 (GFA/land area) exceeds maximum 2.8 for residential zone"
    ],
    "rules_applied": {
      "max_plot_ratio": "2.8",
      "max_height_m": "36"
    }
  },
  "bca_check": {
    "status": "passed",
    "violations": [],
    "requirements_applied": {
      "max_site_coverage": "0.4"
    }
  },
  "proposed_design": {
    "land_area_sqm": 1500.0,
    "zoning": "residential",
    "proposed_gfa_sqm": 5000.0,
    "proposed_height_m": 40.0,
    "proposed_storeys": 10,
    "calculated_plot_ratio": 3.33
  }
}
```

**How It Works:**
1. Creates temporary SingaporeProperty object with proposed design parameters
2. Queries RefRule database for applicable URA zoning and BCA building rules
3. Compares proposed values against allowed maximums:
   - **URA checks**: Plot ratio, building height
   - **BCA checks**: Site coverage
4. Returns overall status (PASSED/FAILED/WARNING) with detailed violations list
5. Provides authority-specific results (URA vs BCA) for granular feedback

**Use Cases:**
- **Pre-submission validation**: Check design before submitting to authorities
- **Design iteration**: Quickly test multiple design options for compliance
- **Client education**: Show why certain designs won't be approved
- **Optimization**: Find maximum allowable building envelope

---

## Rules & Compliance API (Authenticated)

**Tag:** `Rules`
**Prefix:** `/api/v1`

### `GET /api/v1/rules/count`
Get count of rules in database by authority.

**Response:** `200 OK`
```json
{
  "total_rules": 18,
  "by_authority": {
    "URA": 12,
    "BCA": 6
  },
  "sample_rule": {
    "parameter_key": "zoning.max_far",
    "value": "2.8",
    "unit": "ratio"
  }
}
```

### `GET /api/v1/database/status`
Get database status and rules breakdown by topic.

**Response:** `200 OK`
```json
{
  "database_connected": true,
  "tables": ["ref_rules", "ref_sources", "singapore_properties", "users"],
  "rules_by_topic": {
    "zoning": 12,
    "building": 6
  },
  "total_rules": 18
}
```

### `GET /api/v1/rules`
List all rules with optional filtering.

**Query Parameters:**
- `jurisdiction` (optional): Filter by jurisdiction code (e.g., "SG")
- `parameter_key` (optional): Filter by parameter key (e.g., "zoning.max_far")
- `authority` (optional): Filter by authority (e.g., "URA", "BCA")
- `topic` (optional): Filter by topic (e.g., "zoning", "building")
- `review_status` (optional): Filter by status (default: "approved")

**Response:** `200 OK`
```json
{
  "items": [
    {
      "id": 1,
      "jurisdiction": "SG",
      "authority": "URA",
      "topic": "zoning",
      "parameter_key": "zoning.max_far",
      "operator": "<=",
      "value": "2.8",
      "unit": "ratio",
      "applicability": {"zone_code": "SG:residential"},
      "review_status": "approved",
      "is_published": true
    }
  ],
  "count": 18
}
```

---

## Buildable Screening API (Authenticated)

**Tag:** `Screening`
**Prefix:** `/api/v1/screen`

### `POST /api/v1/screen/buildable`
Advanced buildable screening with parcel lookup and zoning layers (production-grade endpoint).

**Request Body:**
```json
{
  "address": "123 Orchard Road, Singapore",
  "defaults": {
    "plot_ratio": 2.8,
    "site_area_m2": 1500.0,
    "site_coverage": 0.40,
    "floor_height_m": 4.0,
    "efficiency_factor": 0.82
  },
  "typ_floor_to_floor_m": 4.0,
  "efficiency_ratio": 0.82
}
```

**Alternative Request (Geometry-based):**
```json
{
  "geometry": {
    "type": "Feature",
    "properties": {
      "zone_code": "SG:residential"
    },
    "geometry": {
      "type": "Polygon",
      "coordinates": [...]
    }
  },
  "defaults": {...}
}
```

**Response:** `200 OK`
```json
{
  "input_kind": "address",
  "zone_code": "SG:residential",
  "overlays": [],
  "advisory_hints": [],
  "metrics": {
    "gfa_cap_m2": 4200.0,
    "footprint_m2": 600.0,
    "floors_max": 7,
    "nsa_est_m2": 3444.0
  },
  "zone_source": "RefRule database",
  "rules": [
    {
      "id": 1,
      "parameter_key": "zoning.max_far",
      "value": "2.8",
      "unit": "ratio"
    }
  ]
}
```

---

## Error Responses

All endpoints return standard error responses:

### `400 Bad Request`
```json
{
  "detail": "Validation error message"
}
```

### `401 Unauthorized`
```json
{
  "detail": "Not authenticated"
}
```

### `403 Forbidden`
```json
{
  "detail": "Not authorized to access this resource"
}
```

### `404 Not Found`
```json
{
  "detail": "Resource not found"
}
```

### `500 Internal Server Error`
```json
{
  "detail": "Internal server error message"
}
```

---

## Data Flow Examples

### User Registration & Property Creation Flow

```
1. User Signup
   POST /api/v1/secure-users/signup
   → Returns user_id and JWT tokens

2. Create Project
   POST /api/v1/projects/create
   (with Authorization: Bearer <access_token>)
   → Returns project_id

3. Calculate Buildable Metrics
   POST /api/v1/singapore-property/calculate/buildable
   (with land_area, zoning)
   → Returns plot_ratio, max_gfa, max_floors, site_coverage

4. Create Property
   POST /api/v1/singapore-property/create
   (with project_id and calculated metrics)
   → Property stored with compliance status
```

### GFA Analysis Flow (User Action → API → Service → Database)

```
User enters:
- Land Area: 1500 sqm
- Zoning: Residential

Frontend calls:
POST /api/v1/singapore-property/calculate/buildable
{
  "land_area_sqm": 1500,
  "zoning": "residential",
  "jurisdiction": "SG"
}

Backend (singapore_property_api.py):
1. Creates BuildableDefaults(site_area_m2=1500, floor_height_m=4.0, efficiency_factor=0.82)
2. Creates ResolvedZone(zone_code="SG:residential")
3. Calls calculate_buildable(session, resolved, defaults)

Service (buildable.py):
1. Queries RefRule table:
   - WHERE jurisdiction = "SG"
   - WHERE zone_code = "SG:residential"
   - WHERE topic IN ["zoning", "building"]
   - WHERE review_status = "approved"
   - WHERE is_published = true
2. Loads rules:
   - zoning.max_far = 2.8 (URA)
   - zoning.max_building_height_m = 36 (URA)
   - zoning.site_coverage.max_percent = 40 (BCA)
3. Applies building science:
   - Max GFA = 1500 × 2.8 = 4200 sqm
   - Max footprint = 1500 × 0.40 = 600 sqm
   - Floors from height = 36 ÷ 4 = 9
   - Floors from GFA = 4200 ÷ 600 = 7
   - Max floors = min(9, 7) = 7 ← constrained by GFA
   - NSA = 4200 × 0.82 = 3444 sqm
4. Returns BuildableCalculation with metrics and applied rules

Frontend displays:
- Plot Ratio: 2.8
- Max Height: 36.0m
- Site Coverage: 40%
- Max GFA: 4,200 sqm
- Max Buildable Floors: 7 (constrained by GFA, footprint, and height)
- Net Saleable Area: 3,444 sqm
```

---

## Database Models

### Users
- `id`: string (primary key, e.g., "user_74c9a2e6")
- `email`: string (unique, indexed)
- `username`: string (unique)
- `full_name`: string
- `password_hash`: string (hashed with sha256_crypt)
- `company_name`: string (optional)
- `created_at`: datetime
- `is_active`: boolean

### Projects
- `id`: string (primary key, e.g., "proj_a1b2c3d4")
- `name`: string
- `description`: text
- `location`: string
- `project_type`: string
- `status`: string (planning, in_progress, completed)
- `budget`: decimal
- `owner_email`: string (foreign key to users)
- `created_at`: datetime
- `updated_at`: datetime
- `is_active`: boolean

### SingaporeProperty
- `id`: string (primary key, e.g., "prop_e5f6g7h8")
- `property_name`: string
- `address`: string
- `postal_code`: string (6 digits)
- `zoning`: enum (residential, commercial, industrial, mixed_use, business_park)
- `tenure`: enum (freehold, leasehold_99, leasehold_999)
- `land_area_sqm`: decimal
- `gross_plot_ratio`: decimal
- `gross_floor_area_sqm`: decimal
- `building_height_m`: decimal
- `num_storeys`: integer
- `street_width_m`: decimal (placeholder for jurisdictions like NYC)
- `acquisition_status`: enum
- `feasibility_status`: enum
- `bca_compliance_status`: enum
- `ura_compliance_status`: enum
- `estimated_acquisition_cost`: decimal
- `actual_acquisition_cost`: decimal
- `estimated_development_cost`: decimal
- `expected_revenue`: decimal
- `project_id`: string (foreign key)
- `owner_email`: string (foreign key to users)
- `created_at`: datetime
- `updated_at`: datetime

### RefRule (Building Code Rules)
- `id`: integer (primary key)
- `jurisdiction`: string (e.g., "SG")
- `authority`: string (e.g., "URA", "BCA")
- `topic`: string (e.g., "zoning", "building")
- `parameter_key`: string (e.g., "zoning.max_far")
- `operator`: string (e.g., "<=", ">=", "=")
- `value`: string (e.g., "2.8", "36", "40%")
- `unit`: string (e.g., "ratio", "m", "percent")
- `applicability`: json (e.g., {"zone_code": "SG:residential"})
- `review_status`: string (needs_review, approved, rejected)
- `is_published`: boolean
- `source_id`: integer (foreign key to RefSource)
- `created_at`: datetime

### RefSource (Regulatory Documents)
- `id`: integer (primary key)
- `jurisdiction`: string
- `authority`: string
- `topic`: string
- `doc_title`: string
- `landing_url`: string
- `fetch_kind`: string (html, pdf, api)
- `is_active`: boolean

---

## Architecture Notes

### Jurisdiction-Agnostic Design
- **RefRule table** stores all building codes in database (not hardcoded)
- **zone_code format**: `{jurisdiction}:{zone}` (e.g., "SG:residential", "NYC:R7A")
- **Pluggable**: Add new jurisdictions by seeding RefRule table with new rules
- **Database-driven**: Rules can be updated without code changes

### Building Science Constants
- **Floor-to-floor height**: 4.0m (includes ceiling, floor slab, MEP space)
- **Efficiency ratio**: 82% (accounts for exterior walls, structure, MEP, circulation)
- **GFA vs NSA**: NSA = GFA × efficiency_ratio (82%)

### Authentication
- **JWT tokens**: Access token (24h), refresh token (7d)
- **Password hashing**: sha256_crypt via passlib
- **Token claims**: email, username, user_id, expiry

### Database
- **Production**: PostgreSQL (via asyncpg)
- **Development**: PostgreSQL via Docker Compose
- **Migrations**: Alembic
- **Sessions**: Async SQLAlchemy (AsyncSession)

---

## Seeding Data

### Seed Singapore Rules (18 Rules)
```bash
POSTGRES_SERVER=localhost \
POSTGRES_USER=postgres \
POSTGRES_PASSWORD=password \
POSTGRES_DB=building_compliance \
python -m backend.scripts.seed_singapore_rules
```

This populates:
- 12 URA zoning rules (plot ratio, height for 5 zones)
- 6 BCA building rules (site coverage for 5 zones)

---

## Frontend Integration

**Frontend URL:** `http://localhost:4400`
**Frontend Auth Page:** `http://localhost:8888/index.html`
**Frontend Property Management:** `http://localhost:8888/singapore-properties.html`

Frontend calls backend API with:
```javascript
const response = await fetch('http://localhost:9400/api/v1/singapore-property/calculate/buildable', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${accessToken}`
  },
  body: JSON.stringify({
    land_area_sqm: 1500,
    zoning: 'residential',
    jurisdiction: 'SG'
  })
});
```

---

## Testing

### Manual Testing via Swagger
1. Start backend: `make dev`
2. Open browser: `http://localhost:9400/docs`
3. Use "Try it out" to test endpoints interactively

### cURL Examples

**Signup:**
```bash
curl -X POST http://localhost:9400/api/v1/secure-users/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "full_name": "Test User",
    "password": "SecurePass123"
  }'
```

**Login:**
```bash
curl -X POST http://localhost:9400/api/v1/secure-users/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123"
  }'
```

**Calculate Buildable (with token):**
```bash
TOKEN="eyJhbGc..."
curl -X POST http://localhost:9400/api/v1/singapore-property/calculate/buildable \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "land_area_sqm": 1500,
    "zoning": "residential",
    "jurisdiction": "SG"
  }'
```

---

## Known Limitations & Future Work

### Current MVP Limitations
1. **No file uploads** - Cannot upload building plans, photos, or documents yet
2. **No external API integration** - OneMap, URA Space, DataMall APIs not integrated
3. **Basic compliance** - Only calculates buildable metrics, no pass/fail compliance checking
4. **No role-based access** - All authenticated users have same permissions
5. **No caching** - Every request hits database (no Redis)
6. **Simple error handling** - Error responses not fully standardized

### Planned Features (Not Yet Built)
1. **GFA optimization service** - Suggest optimal floor plans and unit mix
2. **Compliance report generation** - PDF reports with pass/fail checklist
3. **External data fetching** - Auto-populate zoning from government APIs
4. **File attachment system** - Store building plans, site photos
5. **Multi-user collaboration** - Architects, developers, authority reviewers
6. **Audit trail** - Track all changes to properties and compliance status
7. **Email notifications** - Alerts for compliance updates, rule changes

---

**Last Updated:** 2025-01-15
**Product Focus:** Singapore market (real users available)
**Architecture:** Jurisdiction-agnostic (ready for future expansion to NYC, Tokyo, etc.)
