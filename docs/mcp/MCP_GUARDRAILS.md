# MCP Guardrails

**Source:** Extracted from [CODING_RULES.md](../../CODING_RULES.md) and [SECURITY.md](../SECURITY.md)
**Last Updated:** 2026-01-26
**Status:** Active

This document contains security, performance, accessibility, and testing guardrails.

---

## 1. Security Guardrails (CRITICAL)

**These security rules are MANDATORY and enforced through automated tooling and code review.**

### Authentication & Authorization

1. **[OB-SEC-001]** **Never skip authentication checks on sensitive endpoints**
   - All endpoints accessing user data, financial information, or admin functions MUST verify authentication
   - Use dependency injection: `current_user: User = Depends(get_current_user)`
   - **Enforced by:** Code review, security audit

   ```python
   # CORRECT
   @router.get("/users/{user_id}/profile")
   async def get_profile(
       user_id: str,
       current_user: User = Depends(get_current_user)
   ):
       if current_user.id != user_id and not current_user.is_admin:
           raise HTTPException(status_code=403, detail="Forbidden")
   ```

2. **[OB-SEC-002]** **Always validate JWT tokens with proper expiration**
   - Access tokens: 15-60 minutes
   - Refresh tokens: 7-30 days
   - Verify signature, expiration, and issuer on every request
   - **Enforced by:** Security audit

3. **[OB-SEC-003]** **Implement role-based access control (RBAC) for all resources**
   - Check permissions before any data access or modification
   - Common roles: `admin`, `developer`, `viewer`, `agent`
   - **Enforced by:** Code review, integration tests

### Input Validation

4. **[OB-SEC-004]** **Sanitize all user inputs before database queries**
   - NEVER use string concatenation or f-strings for SQL
   - Always use parameterized queries via SQLAlchemy ORM
   - **Enforced by:** Code review

   ```python
   # WRONG - SQL injection risk
   query = f"SELECT * FROM properties WHERE id = {property_id}"

   # CORRECT - Parameterized
   stmt = select(Property).where(Property.id == property_id)
   result = await session.execute(stmt)
   ```

5. **[OB-SEC-005]** **Use Pydantic validators for all API request models**
   - Validate data types, ranges, formats, and business rules
   - Reject invalid data before processing
   - **Enforced by:** FastAPI framework

   ```python
   class ScenarioCreate(BaseModel):
       project_id: int = Field(..., gt=0)
       name: str = Field(..., min_length=1, max_length=200)
       budget: float = Field(..., gt=0, le=1e9)
   ```

6. **[OB-SEC-006]** **Never trust client-side validation alone**
   - Always re-validate on backend
   - Client-side validation is UX enhancement, not security
   - **Enforced by:** Code review

### Secrets Management

7. **[OB-SEC-007]** **Never commit secrets to version control**
   - Use environment variables for configuration
   - Store secrets in `.env` files (never committed)
   - **Enforced by:** `.gitignore`, detect-secrets pre-commit

8. **[OB-SEC-008]** **Never log sensitive data (passwords, tokens, PII)**
   - Redact sensitive fields before logging
   - Log only non-sensitive identifiers (user_id, request_id)
   - **Enforced by:** Code review

9. **[OB-SEC-009]** **Use environment variables for configuration**
   - Configuration (non-sensitive): `.env` files
   - Never hardcode database URLs, API keys, or credentials
   - **Enforced by:** Code review

   ```python
   # CORRECT
   from pydantic_settings import BaseSettings

   class Settings(BaseSettings):
       database_url: str
       jwt_secret: str
       class Config:
           env_file = ".env"

   # WRONG
   DATABASE_URL = "postgresql://user:password@localhost/db"
   ```

### Data Protection

10. **[OB-SEC-010]** **Encrypt PII at rest**
    - PII includes: email, phone, address, financial data
    - Use database-level encryption where available
    - **Enforced by:** Security audit

11. **[OB-SEC-011]** **Validate file uploads**
    - Check file type, size, and content
    - Sanitize filenames
    - Store outside web root
    - **Enforced by:** Code review

---

## 2. Performance Benchmarks

**Performance requirements for Optimal Build.**

### API Endpoint Performance

| Metric | Target |
|--------|--------|
| P95 latency (read) | < 200ms |
| P95 latency (write) | < 500ms |
| P99 latency (all) | < 1000ms |
| Error rate | < 0.1% |

### Database Query Performance

| Metric | Target |
|--------|--------|
| Simple queries | < 100ms |
| Complex aggregations | < 500ms |
| Connection acquisition | < 10ms |
| Index hit ratio | > 95% |

### Frontend Performance (Core Web Vitals)

| Metric | Target |
|--------|--------|
| First Contentful Paint (FCP) | < 1.5s |
| Largest Contentful Paint (LCP) | < 2.5s |
| Time to Interactive (TTI) | < 3.5s |
| Cumulative Layout Shift (CLS) | < 0.1 |
| First Input Delay (FID) | < 100ms |

### Memory Usage

| Component | Limit |
|-----------|-------|
| Backend process | < 512MB per worker |
| Frontend bundle (gzipped) | < 500KB main bundle |
| Database connection pool | < 100 connections |

### Performance Rules

12. **[OB-PERF-001]** **Never create N+1 query patterns**
    - Use `selectinload()` or `joinedload()` for relationships
    - **Enforced by:** Code review

13. **[OB-PERF-002]** **Always add LIMIT for large result sets**
    - Use pagination for unbounded queries
    - Default page size: 50-100 items
    - **Enforced by:** Code review

14. **[OB-PERF-003]** **Use streaming for large files**
    - Never load entire files into memory
    - Use generators or async iterators
    - **Enforced by:** Code review

15. **[OB-PERF-004]** **Index all foreign keys and frequently queried columns**
    - Every FK needs an index
    - Add indexes for columns in WHERE/ORDER BY clauses
    - **Enforced by:** Code review

---

## 3. Accessibility (a11y) Guardrails

**WCAG AA compliance is required for all user-facing features.**

### Mandatory Rules

16. **[OB-A11Y-001]** **Contrast ratio >= 4.5:1 for normal text**
    - Use design tokens that meet contrast requirements
    - **Enforced by:** Automated a11y testing

17. **[OB-A11Y-002]** **Touch targets >= 44x44px**
    - Buttons and interactive elements must be easily tappable
    - **Enforced by:** Code review

18. **[OB-A11Y-003]** **All interactive elements must be keyboard accessible**
    - Tab/Enter/Space navigation
    - Focus indicators visible
    - **Enforced by:** Code review, manual testing

19. **[OB-A11Y-004]** **All images must have alt text**
    - Decorative images: `alt=""`
    - Meaningful images: descriptive alt text
    - **Enforced by:** ESLint jsx-a11y

20. **[OB-A11Y-005]** **Form inputs must have labels**
    - Use `<label>` elements or `aria-label` attributes
    - **Enforced by:** ESLint jsx-a11y

21. **[OB-A11Y-006]** **Use proper ARIA attributes where semantic HTML is insufficient**
    - Prefer semantic HTML first
    - Add ARIA when needed for complex widgets
    - **Enforced by:** Code review

---

## 4. Testing Pyramid Strategy

**Test distribution for optimal coverage and speed.**

### Test Distribution (Target Ratios)

| Type | Ratio | Speed | Coverage |
|------|-------|-------|----------|
| Unit Tests | 70% | < 100ms/test | Business logic, validators |
| Integration Tests | 20% | < 1s/test | Database, service interactions |
| E2E Tests | 10% | < 10s/test | Critical user flows |

### Coverage Requirements by Layer

| Layer | Minimum Coverage |
|-------|------------------|
| Business Logic (services/) | 100% |
| API Routes (api/v1/) | 90% |
| Database Repositories | 85% |
| UI Components | 80% |
| Utility Functions | 100% |

### Testing Rules

22. **[OB-TEST-001]** **Write tests first (TDD recommended)**
    - Create test file before implementation
    - Tests should fail initially
    - **Enforced by:** Code review

23. **[OB-TEST-002]** **Use descriptive test naming**
    - Pattern: `test_<what>_<when>_<expected>`
    - Example: `test_create_scenario_when_invalid_budget_raises_validation_error`
    - **Enforced by:** Code review

24. **[OB-TEST-003]** **Test isolation - no interdependencies**
    - Tests must run in any order
    - Use fixtures for setup/teardown
    - **Enforced by:** pytest configuration

25. **[OB-TEST-004]** **Provide test commands after completing features**
    - Backend: `pytest backend/tests/test_api/test_[feature].py -v`
    - Frontend: `cd frontend && npm test -- src/modules/[feature]`
    - Manual testing steps for UI
    - **Enforced by:** Code review

26. **[OB-TEST-005]** **Mark tests with appropriate markers**
    - `@pytest.mark.unit` - Unit tests
    - `@pytest.mark.integration` - Integration tests
    - `@pytest.mark.slow` - Slow tests (>5s)
    - **Enforced by:** pytest configuration

### Test Commands

```bash
# Backend tests
make test                                    # All backend tests
pytest backend/tests/ -v                     # Verbose output
pytest backend/tests/ --cov=app             # With coverage

# Frontend tests
cd frontend && npm test                     # All frontend tests
cd frontend && npm test -- --coverage       # With coverage

# Specific tests
pytest backend/tests/test_api/test_finance.py -v
pytest backend/tests/test_api/test_finance.py::test_create_scenario -v
```

---

## 5. Dependency Management

### Version Pinning Strategy

- **Python:** Pin exact versions in `requirements.txt`
- **Node.js:** Use `package-lock.json` (committed)
- **Docker:** Pin base image versions

### Security Patching SLAs

| Severity | CVSS Score | Patch Deadline |
|----------|------------|----------------|
| Critical | >= 9.0 | 24 hours |
| High | 7.0-8.9 | 7 days |
| Medium | 4.0-6.9 | 30 days |
| Low | < 4.0 | 90 days |

### Dependency Rules

27. **[OB-DEP-001]** **Sync formatter versions across config files**
    - Black version must match in `requirements.txt` AND `.pre-commit-config.yaml`
    - **Enforced by:** Pre-commit hooks

28. **[OB-DEP-002]** **Review new dependencies for security**
    - Check for known vulnerabilities
    - Verify active maintenance
    - **Enforced by:** Code review

---

## 6. Severity Classification

When reviewing code or issues, use this classification:

| Level | Symbol | Description | Action |
|-------|--------|-------------|--------|
| Critical | :red_circle: | Security vulnerability, data loss risk | Must fix before merge |
| Major | :orange_circle: | Bug, performance issue | Should fix before merge |
| Minor | :yellow_circle: | Code quality, style | Consider fixing |
| Nitpick | :blue_circle: | Preference, suggestion | Optional |
| Praise | :green_circle: | Good practice noticed | No action |

---

## 7. Real Estate Domain Guardrails

**Domain-specific rules for Singapore property development and financial modeling.**

### Singapore Compliance

29. **[OB-RE-001]** **Validate against URA constraints**
    - Check land constraints (reserved land, restricted zones)
    - Validate zoning compliance (residential, commercial, industrial)
    - Verify development type restrictions
    - **Enforced by:** Integration tests, code review

    ```python
    # CORRECT - Validates URA constraints
    async def create_property(data: PropertyCreate) -> Property:
        # Validate against URA geospatial constraints
        await validate_ura_constraints(
            location=data.location,
            development_type=data.type,
            gfa=data.gross_floor_area
        )
        return await db.create(Property, data)
    ```

30. **[OB-RE-002]** **GFA calculations must follow URA guidelines**
    - Gross Floor Area (GFA) calculations are jurisdiction-specific
    - Singapore: Follow URA DC Handbook
    - Include exclusions: balconies (50% up to 10sqm), AC ledges, etc.
    - **Enforced by:** Unit tests with known test cases

    ```python
    def calculate_gfa_singapore(areas: PropertyAreas) -> Decimal:
        """Calculate GFA per URA guidelines."""
        base_gfa = areas.gross_area
        # Balcony exclusion: 50% up to 10sqm
        balcony_exclusion = min(areas.balcony_area * Decimal("0.5"), Decimal("10"))
        # AC ledge exclusion
        ac_exclusion = areas.ac_ledge_area
        return base_gfa - balcony_exclusion - ac_exclusion
    ```

### Financial Data Integrity

31. **[OB-RE-003]** **Financial calculations require audit logging**
    - All NOI, IRR, cap rate calculations must be logged
    - Include input parameters and results
    - **Enforced by:** Code review

    ```python
    async def calculate_financial_metrics(scenario_id: str) -> FinanceMetrics:
        metrics = await compute_metrics(scenario_id)
        await audit_log(
            action="CALCULATE_FINANCIAL_METRICS",
            resource_id=scenario_id,
            user_id=current_user.id,
            details={
                "noi": str(metrics.noi),
                "irr": str(metrics.irr),
                "cap_rate": str(metrics.cap_rate)
            }
        )
        return metrics
    ```

32. **[OB-RE-004]** **Use Decimal for all financial calculations**
    - Never use float for money/percentages
    - Prevent floating-point precision errors
    - **Enforced by:** Type hints, code review

    ```python
    from decimal import Decimal

    # CORRECT - Precise financial calculations
    price = Decimal("1500000.00")
    noi = Decimal("75000.00")
    cap_rate = noi / price  # Decimal("0.05")

    # WRONG - Float precision errors
    price = 1500000.0
    noi = 75000.0
    cap_rate = noi / price  # 0.05000000000000001
    ```

### Project Phase Constraints

33. **[OB-RE-005]** **Enforce valid phase transitions**
    - Projects cannot skip phases or go backwards
    - **Enforced by:** API validation, state machine

    ```python
    VALID_PHASE_TRANSITIONS = {
        "site_acquisition": ["feasibility_analysis"],
        "feasibility_analysis": ["financing", "approval_process"],
        "financing": ["construction"],
        "approval_process": ["construction"],
        "construction": ["stabilization"],
        "stabilization": ["exit"]
    }

    async def update_project_phase(project_id: str, new_phase: str):
        project = await get_project(project_id)
        if new_phase not in VALID_PHASE_TRANSITIONS.get(project.phase, []):
            raise ValidationError(
                f"Cannot transition from {project.phase} to {new_phase}",
                details={"valid_transitions": VALID_PHASE_TRANSITIONS[project.phase]}
            )
    ```

### Geospatial Data

34. **[OB-RE-006]** **Never expose exact property coordinates to unauthorized users**
    - Fuzzy coordinates for public views
    - Exact coordinates only for authorized users
    - **Enforced by:** Code review, authorization checks

    ```python
    def get_property_location(property: Property, user: User) -> Coordinates:
        if user.has_permission("view_exact_locations"):
            return property.exact_coordinates
        # Fuzzy to ~500m radius for unauthorized users
        return fuzzy_coordinates(property.exact_coordinates, radius_meters=500)
    ```

35. **[OB-RE-007]** **Validate PostGIS geometry types**
    - Ensure correct SRID (4326 for WGS84)
    - Validate geometry bounds for Singapore (1.1-1.5°N, 103.6-104.1°E)
    - **Enforced by:** Database constraints, API validation

---

## 8. Performance Anti-Patterns (Detailed)

### Database Performance

36. **[OB-PERF-005]** **Never use individual inserts in loops**
    - Use bulk operations instead
    - **Enforced by:** Code review

    ```python
    # WRONG - 1000 INSERT queries
    for property_id in property_ids:
        await db.execute(
            "INSERT INTO favorites (user_id, property_id) VALUES ($1, $2)",
            [user_id, property_id]
        )

    # CORRECT - Single bulk insert
    await db.execute_many(
        "INSERT INTO favorites (user_id, property_id) VALUES ($1, $2)",
        [(user_id, pid) for pid in property_ids]
    )
    ```

37. **[OB-PERF-006]** **Use correct data structure for lookups**
    - Set for O(1) membership tests
    - Dict for O(1) key lookup
    - **Enforced by:** Code review

    ```python
    # WRONG - O(n) lookup on list
    valid_statuses = ["listed", "sold", "under_offer", "withdrawn"]
    if property.status in valid_statuses:  # Linear scan!
        process(property)

    # CORRECT - O(1) lookup with set
    valid_statuses = {"listed", "sold", "under_offer", "withdrawn"}
    if property.status in valid_statuses:  # Hash lookup
        process(property)
    ```

38. **[OB-PERF-007]** **Avoid string concatenation in loops**
    - Use list.join() for string building
    - **Enforced by:** Code review

    ```python
    # WRONG - O(n²) string concatenation
    result = ""
    for item in items:
        result += f"{item.name}, "  # Creates new string each time!

    # CORRECT - O(n) join
    result = ", ".join(item.name for item in items)
    ```

### Memory Performance

39. **[OB-PERF-008]** **Release database connections promptly**
    - Return connections to pool immediately after use
    - Don't hold connections during external API calls
    - **Enforced by:** Code review

    ```python
    # WRONG - Holds connection during external call
    async def process_property(property_id: str):
        async with get_db() as db:
            property = await db.get(Property, property_id)
            # Still holding connection!
            external_data = await call_external_api(property.address)
            property.external_data = external_data
            await db.commit()

    # CORRECT - Release connection before external call
    async def process_property(property_id: str):
        async with get_db() as db:
            property = await db.get(Property, property_id)
            address = property.address

        # Connection released, now call external API
        external_data = await call_external_api(address)

        async with get_db() as db:
            property = await db.get(Property, property_id)
            property.external_data = external_data
            await db.commit()
    ```

40. **[OB-PERF-009]** **No side effects at import time**
    - Don't initialize caches, connections, or listeners at import
    - Use lazy initialization
    - **Enforced by:** Code review

    ```python
    # WRONG - Side effect at import
    # backend/app/services/property_service.py
    cache = redis.Redis()  # Runs when module imported!
    settings = load_all_settings()  # Slow import!

    # CORRECT - Lazy initialization
    _cache = None
    def get_cache():
        global _cache
        if _cache is None:
            _cache = redis.Redis()
        return _cache
    ```

---

**Related:** [MCP Hub](../../MCP.md) | [Rules](MCP_RULES.md) | [Shared Core](../ai/SHARED_CORE.md)
