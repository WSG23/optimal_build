# Test Isolation Infrastructure Analysis

## Problem Summary

Test coverage improvement blocked by test isolation failures:
- Tests pass individually ✅
- Tests fail when run together ❌
- Coverage drops from 61.78% → 48.91%
- Pattern occurred twice in one week

## Root Cause Identified

Located in [`backend/tests/conftest.py`](backend/tests/conftest.py):

> **2025-11-05 Update**
> The fixtures have now been refactored to eliminate the problems identified below.
> Each test spins up its own in-memory SQLite engine, cleanup raises on failure, and the database is wiped before/after every test.
> The remainder of this document is retained for historical context.

### Current Architecture (Lines 419-532)

```
┌─────────────────────────────────────────┐
│ flow_session_factory                    │
│ scope: session (SHARED ACROSS ALL TESTS)│
│ ├─ In-memory SQLite database            │
│ └─ async_sessionmaker instance          │
└─────────────────────────────────────────┘
          │
          ├─→ _cleanup_flow_session_factory (autouse=True, function scope)
          │   ├─ Calls _reset_database() before test
          │   └─ Calls _reset_database() after test
          │
          ├─→ async_session_factory (function scope)
          │   └─ Wraps flow_session_factory with cleanup
          │
          └─→ session (function scope)
              └─ Individual DB session with _truncate_all()
```

### The Pollution Mechanism

**Problem 1: Session Scope Mismatch**
- `flow_session_factory` is **session-scoped** (one instance for entire test suite)
- Cleanup fixtures are **function-scoped** (run per test)
- Session-scoped factory creates connections that persist beyond cleanup

**Problem 2: Incomplete Cleanup**
```python
async def _truncate_all(session: AsyncSession) -> None:
    """Remove all rows from every mapped table in metadata order."""
    await session.rollback()
    for table in reversed(_SORTED_TABLES):
        try:
            await session.execute(table.delete())
        except SQLAlchemyError:
            continue  # ⚠️ SILENTLY IGNORES CLEANUP FAILURES
    await session.commit()
```

**Problem 3: Global Singleton Pollution**
The `_override_async_session_factory` (lines 481-507) monkeypatches global modules:
```python
targets = [
    import_module("app.core.database"),
    import_module("backend.flows.watch_fetch"),
    import_module("backend.flows.parse_segment"),
    import_module("backend.flows.sync_products"),
]
```

These monkeypatches create **global state** that persists across tests.

## Evidence from Failed Attempts

### Attempt 1: market_demo_data fixture (Nov 2)
- **Symptom**: test_preview_jobs.py tests failed in full suite
- **Root Cause**: Fixture created market demo data that polluted other tests
- **Fix**: Refactored fixture to isolate data creation (commit 125a038)

### Attempt 2: test_pwp.py coverage (Nov 3)
- **Symptom**: 75 failures + 16 errors when PWP tests added to suite
- **Tests affected**:
  - test_preview_jobs.py (3 failures)
  - test_rules.py (multiple failures)
  - test_rulesets.py (multiple failures)
  - Many test_api/* files
- **Root Cause**: PWP tests modified RefCostIndex table, affecting downstream tests
- **Fix**: Reverted (commit 125a038 restored)

### Attempt 3: base.py + ingestion.py coverage (Nov 5 - Batch 5)
- **Symptom**: 99 failures + 16 errors - `sqlalchemy.exc.InvalidRequestError: One or more mappers failed to initialize`
- **Tests affected**: Entire test suite including previously passing Batch 4 (test_deals_utils.py)
- **Tests created**:
  - test_base.py (2 tests for AsyncClientService)
  - test_ingestion.py (9 tests for RefIngestionRun lifecycle)
- **Root Cause**: Tests imported models with relationships (RefIngestionRun), triggering mapper initialization when combined with existing pollution
- **Coverage Impact**: Dropped from 62.10% → 49.23%
- **Fix**: Reverted both test files

## Affected Test Files

These files pass individually but fail in full suite:

1. **backend/tests/test_services/test_pwp.py**
   - Creates RefCostIndex entries
   - Leaves cost index data in database
   - Affects tests expecting clean cost tables

2. **backend/tests/test_services/test_preview_jobs.py**
   - Creates market demo data (properties, assets)
   - Affects tests expecting specific property counts

3. **backend/tests/test_api/test_developer_site_acquisition.py**
   - Creates GPS location data
   - Affects tests querying by location

4. **backend/tests/test_api/test_finance_asset_breakdown.py**
   - Creates finance scenarios
   - Affects tests expecting empty finance data

5. **backend/tests/test_services/test_base.py** (reverted)
   - Tests AsyncClientService.close() method
   - No database operations, but imports httpx

6. **backend/tests/test_services/test_ingestion.py** (reverted)
   - Creates RefIngestionRun records in database
   - Imports models with SQLAlchemy relationships
   - Triggers mapper initialization failures when combined with pollution

    _ensure_sqlalchemy_dialects()

    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )

    # ... rest of setup ...

    factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        yield factory
    finally:
        await engine.dispose()  # Ensures complete cleanup
```

**Pros:**
- Complete isolation - each test gets fresh database
- No cleanup failures possible
- Simple to understand

**Cons:**
- Slower tests (recreate DB per test)
- May need to optimize with class-scoped fixtures for test classes

### Option 2: Enhanced Cleanup (Faster but Complex)

Keep session-scope but improve cleanup:

```python
async def _truncate_all(session: AsyncSession) -> None:
    """Remove all rows from every mapped table in metadata order."""
    await session.rollback()

    errors = []
    for table in reversed(_SORTED_TABLES):
        try:
            await session.execute(table.delete())
        except SQLAlchemyError as exc:
            errors.append((table.name, str(exc)))

    if errors:
        # Log or raise to catch cleanup failures early
        logger.warning(f"Cleanup failed for tables: {errors}")

    await session.commit()

    # Verify cleanup succeeded
    for table in _SORTED_TABLES:
        result = await session.execute(
            select(func.count()).select_from(table)
        )
        count = result.scalar()
        if count > 0:
            raise RuntimeError(
                f"Table {table.name} not empty after cleanup: {count} rows remain"
            )
```

**Pros:**
- Faster tests (reuse same DB)
- Catches cleanup failures immediately

**Cons:**
- More complex
- Still vulnerable to SQLAlchemy connection pooling issues
- Monkeypatch global state still problematic

    # Implementation similar to flow_session_factory but function-scoped
    pass
```

## Next Steps

- Unskip database-heavy test batches (PWP, ingestion, preview jobs) and verify they pass under the new per-test fixtures.
- Trim `_SKIPPED_TEST_PATTERNS` as soon as the migrated tests are stable.
- Monitor runtime. If the new isolation increases suite time significantly, consider introducing a class-scoped variant that keeps an engine alive per test module.
- Update CODING_RULES.md with guidance on choosing the appropriate fixture (`session` vs. `no_db`) now that isolation is enforced.

## Success Criteria

- [ ] All tests pass in isolation
- [ ] All tests pass in full suite
- [ ] Coverage >= 61.78% (no regression)
- [ ] No global state pollution detected
- [ ] Test execution time < 2x current baseline

## References

- [`backend/tests/conftest.py:419-532`](backend/tests/conftest.py#L419-L532) - Database fixtures
- [`backend/tests/test_services/test_pwp.py`](backend/tests/test_services/test_pwp.py) - Example of isolated test
- Commit 125a038: market_demo_data fixture fix
- Commit ea5db34 (reverted): PWP coverage attempt that revealed pollution
