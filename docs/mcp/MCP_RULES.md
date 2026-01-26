# MCP Rules & Constraints

**Source:** Extracted from [CODING_RULES.md](../../CODING_RULES.md) and [CLAUDE.md](../../CLAUDE.md)
**Last Updated:** 2026-01-26
**Status:** Active

This document contains all DO and DON'T rules for the Optimal Build project with machine-readable IDs.

---

## Rule ID System

All rules are assigned unique identifiers for tracking and validation:

| Format          | Description                    | Example        |
| --------------- | ------------------------------ | -------------- |
| `OB-DO-###`     | Positive rules (what TO do)    | `OB-DO-001`    |
| `OB-DONT-###`   | Anti-patterns (what NOT to do) | `OB-DONT-001`  |
| `OB-SEC-###`    | Security guardrails            | `OB-SEC-001`   |
| `OB-PERF-###`   | Performance requirements       | `OB-PERF-001`  |
| `OB-TEST-###`   | Testing requirements           | `OB-TEST-001`  |
| `OB-AI-###`     | AI code generation rules       | `OB-AI-001`    |

---

## DO (Positive Rules)

### Code Quality

1. **[OB-DO-001]** **Always run pre-commit hooks before pushing**
   - Command: `make hooks` or `pre-commit run --all-files`
   - **Enforced by:** Git pre-commit hooks

2. **[OB-DO-002]** **Use type hints everywhere**
   - All public APIs must have complete type annotations
   - Use `AsyncSession` not `Session` for database operations
   - **Enforced by:** mypy, code review

3. **[OB-DO-003]** **Use async/await for ALL database operations**
   - ALL database calls use `async`/`await`
   - ALL API routes use `async def`
   - **Enforced by:** Code review, runtime errors
   ```python
   # CORRECT
   async def get_item(db: AsyncSession, id: int):
       result = await db.execute(select(Item).where(Item.id == id))
       return result.scalar_one_or_none()
   ```

4. **[OB-DO-004]** **Format with Black (Python)** - 88 character line length
   - Command: `make format`
   - **Enforced by:** Pre-commit hooks

5. **[OB-DO-005]** **Write Google-style docstrings** with Args, Returns, Raises sections
   - Required for all public functions and classes
   - **Enforced by:** Code review

6. **[OB-DO-006]** **Use `sa.String()` for ENUM columns in migrations**
   - NEVER use `sa.Enum()` with `create_type=False`
   - Create ENUM types explicitly with raw SQL
   - **Enforced by:** Pre-commit hook (check-migration-enums)
   ```python
   # CORRECT
   op.execute("CREATE TYPE deal_status AS ENUM ('open', 'closed')")
   op.create_table("deals", sa.Column("status", sa.String()))
   op.execute("ALTER TABLE deals ALTER COLUMN status TYPE deal_status USING status::deal_status")
   ```

7. **[OB-DO-007]** **Index ALL foreign keys**
   - Every foreign key column MUST have an index
   - **Enforced by:** Code review
   ```python
   op.create_index("ix_scenarios_project_id", "scenarios", ["project_id"])
   ```

8. **[OB-DO-008]** **Use exception chaining with `from e`**
   - Preserves full traceback for debugging
   - **Enforced by:** Ruff B904
   ```python
   except ValueError as e:
       raise HTTPException(status_code=422, detail=str(e)) from e
   ```

### Git Practices

9. **[OB-DO-009]** **Use imperative mood in commit messages**
   - Include "why" context, not just "what"
   - Example: "Add compliance scoring to Property model to track regulatory violations"
   - **Enforced by:** Code review

10. **[OB-DO-010]** **Run `git status` before committing**
    - Verify no unintended files are staged
    - **Enforced by:** Manual check

11. **[OB-DO-011]** **Small, reviewable PRs preferred**
    - Break large changes into smaller, focused commits
    - **Enforced by:** Code review

### Documentation

12. **[OB-DO-012]** **Update canonical files instead of creating new docs**
    - Add to existing `docs/` files when possible
    - Get approval before creating new .md files
    - **Enforced by:** Code review

13. **[OB-DO-013]** **Use relative paths for links**
    - Links between docs should use relative paths
    - **Enforced by:** Code review

### Testing

14. **[OB-DO-014]** **Provide test commands after completing features**
    - Backend: `pytest backend/tests/test_api/test_[feature].py -v`
    - Frontend: `cd frontend && npm test -- src/modules/[feature]`
    - Manual testing steps for UI changes
    - **Enforced by:** Code review

15. **[OB-DO-015]** **Mark tests with appropriate markers**
    - `@pytest.mark.unit` for unit tests
    - `@pytest.mark.integration` for integration tests
    - **Enforced by:** pytest configuration

16. **[OB-DO-016]** **Maintain test coverage >80% for critical paths**
    - Backend overall: >70%
    - Backend critical paths: >80%
    - **Enforced by:** CI coverage gates

### Frontend

17. **[OB-DO-017]** **Use design tokens, never hardcoded values**
    - Spacing: `--ob-space-*` tokens
    - Colors: semantic tokens only
    - Radius: `--ob-radius-*` tokens
    - **Enforced by:** ESLint, code review
    ```tsx
    // CORRECT
    <Box sx={{ p: 'var(--ob-space-200)', borderRadius: 'var(--ob-radius-sm)' }}>
    ```

18. **[OB-DO-018]** **Use canonical components from `src/components/canonical/`**
    - Check for existing components before creating new ones
    - **Enforced by:** Code review

### Database

19. **[OB-DO-019]** **Create new migrations, never edit existing ones**
    - Command: `cd backend && alembic revision -m "description"`
    - **Enforced by:** Pre-commit hook (audit-migrations)

20. **[OB-DO-020]** **Match ENUM values exactly between Python and SQL**
    - Python enum VALUES must match PostgreSQL ENUM values exactly (case-sensitive)
    - **Enforced by:** Runtime errors, code review

### Error Handling

21. **[OB-DO-021]** **Define application exception hierarchy**
    - All custom exceptions inherit from base `OptimalBuildError`
    - **Enforced by:** Code review
    ```python
    class OptimalBuildError(Exception):
        """Base exception for all Optimal Build errors."""
        def __init__(self, message: str, details: dict[str, Any] | None = None):
            self.message = message
            self.details = details or {}
            super().__init__(message)

    class ValidationError(OptimalBuildError):
        """Invalid input data."""
        pass

    class ResourceNotFoundError(OptimalBuildError):
        """Requested resource doesn't exist."""
        pass
    ```

22. **[OB-DO-022]** **Use context managers for resource cleanup**
    - Guarantees cleanup even on exceptions
    - **Enforced by:** Code review
    ```python
    # CORRECT - Connection auto-returned to pool
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(query)
            # Auto-rollback on exception, auto-commit on success
    ```

23. **[OB-DO-023]** **Log errors with structured context**
    - Never log without context information
    - **Enforced by:** Code review
    ```python
    try:
        validate_property_data(property_id, data)
    except ValidationError as e:
        logger.error(
            "Property validation failed",
            property_id=property_id,
            error_type=e.__class__.__name__,
            error_details=e.details,
            exc_info=True
        )
        raise
    ```

24. **[OB-DO-024]** **Implement retry logic for transient failures**
    - Use tenacity for external API calls
    - **Enforced by:** Code review
    ```python
    from tenacity import retry, stop_after_attempt, wait_exponential

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    async def call_ura_api(endpoint: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(endpoint)
            response.raise_for_status()
            return response.json()
    ```

25. **[OB-DO-025]** **Implement graceful degradation**
    - Don't fail completely if optional services unavailable
    - **Enforced by:** Code review
    ```python
    async def get_property_data(property_id: str) -> PropertyData:
        try:
            return await cache.get(property_id)  # Fast path
        except CacheConnectionError:
            logger.warning("Cache unavailable, using database", property_id=property_id)
            return await db.get_property(property_id)  # Fallback
    ```

### Memory Management

26. **[OB-DO-026]** **Use generators for large sequences**
    - Only keep one item in memory at a time
    - **Enforced by:** Code review
    ```python
    # CORRECT - Generator yields one at a time
    def get_all_property_ids(project_id: str) -> Iterator[str]:
        for row in db.fetch_all_properties(project_id):
            yield row['id']

    # WRONG - Loads entire list into memory
    def get_all_property_ids(project_id: str) -> list[str]:
        return [row['id'] for row in db.fetch_all_properties(project_id)]
    ```

27. **[OB-DO-027]** **Limit cache size with LRU eviction**
    - Prevent unbounded memory growth
    - **Enforced by:** Code review
    ```python
    from functools import lru_cache

    # CORRECT - Bounded cache (max 256 entries)
    @lru_cache(maxsize=256)
    def expensive_property_computation(property_id: str) -> ComplexAnalysis:
        return compute_analysis(property_id)
    ```

---

## DON'T (Anti-Patterns)

### Code Anti-Patterns

1. **[OB-DONT-001]** **Never edit existing migration files**
   - Always create new migrations for changes
   - **Enforced by:** Pre-commit hook

2. **[OB-DONT-002]** **Never use `sa.Enum()` with `create_type=False` in migrations**
   - Causes "type already exists" errors
   - **Enforced by:** Pre-commit hook

3. **[OB-DONT-003]** **Never use sync database code**
   - No `Session` (use `AsyncSession`)
   - No `.query()` (use `select()` with `await`)
   - **Enforced by:** Code review

4. **[OB-DONT-004]** **Never use bare `except:` clauses**
   - Always specify exception types
   - **Enforced by:** Ruff E722
   ```python
   # WRONG
   except:
       pass

   # CORRECT
   except ValueError as e:
       logger.error(f"Validation failed: {e}")
       raise
   ```

5. **[OB-DONT-005]** **Never use mutable default arguments**
   - **Enforced by:** Ruff B006
   ```python
   # WRONG
   def process(items: list = []):  # Shared across calls!

   # CORRECT
   def process(items: list | None = None):
       if items is None:
           items = []
   ```

6. **[OB-DONT-006]** **Never leave unused variables**
   - Remove or prefix with `_` if intentionally ignored
   - **Enforced by:** Ruff F841

7. **[OB-DONT-007]** **Never lose exception context**
   - Always use `from e` or `from None` when re-raising
   - **Enforced by:** Ruff B904

### Git Anti-Patterns

8. **[OB-DONT-008]** **Never commit generated artifacts**
   - Check `git status` before committing
   - **Enforced by:** `.gitignore`, pre-commit hooks

9. **[OB-DONT-009]** **Never push without running tests**
   - `make verify` must pass before commit
   - **Enforced by:** Pre-commit hooks

10. **[OB-DONT-010]** **Never mark incomplete phases as COMPLETE**
    - All checklist items must be checked
    - User approval required
    - **Enforced by:** Pre-commit hook (phase-gate)

### Frontend Anti-Patterns

11. **[OB-DONT-011]** **Never use hardcoded pixel values**
    - Use design tokens instead
    - **Enforced by:** ESLint, code review
    ```tsx
    // WRONG
    <Box sx={{ p: '16px', borderRadius: '12px' }}>

    // CORRECT
    <Box sx={{ p: 'var(--ob-space-400)', borderRadius: 'var(--ob-radius-sm)' }}>
    ```

12. **[OB-DONT-012]** **Never use hardcoded colors**
    - Use semantic tokens (`--ob-color-*`)
    - **Enforced by:** ESLint, code review

13. **[OB-DONT-013]** **Never use MUI spacing numbers directly**
    - Use design token variables
    - **Enforced by:** Code review

### Database Anti-Patterns

14. **[OB-DONT-014]** **Never forget foreign key indexes**
    - Every FK column needs an index
    - **Enforced by:** Code review

15. **[OB-DONT-015]** **Never create shadow directories matching Python packages**
    - FORBIDDEN: `fastapi/`, `sqlalchemy/`, `pydantic/`, `pytest/`
    - **Enforced by:** Pre-commit hook

### Performance Anti-Patterns

16. **[OB-DONT-016]** **Never create N+1 query patterns**
    - Use `selectinload()` or `joinedload()` for relationships
    - **Enforced by:** Code review
    ```python
    # WRONG - N+1 queries
    users = await get_all_users()
    for user in users:
        orders = await get_user_orders(user.id)  # N queries!

    # CORRECT - Single query with eager loading
    stmt = select(User).options(selectinload(User.orders))
    users = await session.execute(stmt)
    ```

17. **[OB-DONT-017]** **Never use unbounded queries**
    - Always add LIMIT for large tables
    - **Enforced by:** Code review

18. **[OB-DONT-018]** **Never load entire files into memory**
    - Stream large files line-by-line
    - **Enforced by:** Code review

### Security Anti-Patterns

19. **[OB-DONT-019]** **Never commit secrets**
    - Use environment variables and `.env` files (never committed)
    - **Enforced by:** `.gitignore`, detect-secrets

20. **[OB-DONT-020]** **Never use f-strings for SQL queries**
    - Use parameterized queries via ORM
    - **Enforced by:** Code review
    ```python
    # WRONG - SQL injection risk
    query = f"SELECT * FROM users WHERE id = {user_id}"

    # CORRECT
    stmt = select(User).where(User.id == user_id)
    ```

21. **[OB-DONT-021]** **Never skip authentication on sensitive endpoints**
    - Use `Depends(get_current_user)` for all protected routes
    - **Enforced by:** Code review

22. **[OB-DONT-022]** **Never log sensitive data (PII, passwords, tokens)**
    - Redact before logging
    - **Enforced by:** Code review

### Frontend React Anti-Patterns

23. **[OB-DONT-023]** **Never mutate state directly**
    - Always create new arrays/objects
    - **Enforced by:** ESLint react/no-direct-mutation-state
    ```typescript
    // WRONG - Mutates state
    users.push(newUser);
    setUsers(users);

    // CORRECT - Creates new array
    setUsers([...users, newUser]);
    ```

24. **[OB-DONT-024]** **Never use array index as key**
    - Causes re-render bugs when list changes
    - **Enforced by:** ESLint react/no-array-index-key
    ```typescript
    // WRONG - Index as key breaks updates
    {users.map((user, i) => <UserCard key={i} user={user} />)}

    // CORRECT - Use stable ID
    {users.map((user) => <UserCard key={user.id} user={user} />)}
    ```

25. **[OB-DONT-025]** **Never call hooks conditionally**
    - Breaks Rules of Hooks
    - **Enforced by:** ESLint react-hooks/rules-of-hooks
    ```typescript
    // WRONG - Conditional hook
    if (condition) {
      const data = useQuery(...);
    }

    // CORRECT - Conditional fetch, not hook
    const { data } = useQuery(..., { enabled: condition });
    ```

26. **[OB-DONT-026]** **Never forget effect dependencies**
    - Include all dependencies in array
    - **Enforced by:** ESLint react-hooks/exhaustive-deps
    ```typescript
    // WRONG - Missing userId dependency
    useEffect(() => {
      fetchData(userId);
    }, []);

    // CORRECT - All dependencies included
    useEffect(() => {
      fetchData(userId);
    }, [userId, fetchData]);
    ```

27. **[OB-DONT-027]** **Never skip memoization for expensive computations**
    - Use useMemo for costly calculations
    - **Enforced by:** Code review
    ```typescript
    // WRONG - Recomputes on every render
    const sortedProperties = properties.sort((a, b) => a.price - b.price);

    // CORRECT - Memoize expensive computation
    const sortedProperties = useMemo(
      () => properties.sort((a, b) => a.price - b.price),
      [properties]
    );
    ```

28. **[OB-DONT-028]** **Never skip memoization for callbacks to children**
    - Use useCallback for callbacks passed as props
    - **Enforced by:** Code review
    ```typescript
    // WRONG - Creates new function every render
    const handleSelect = (id: string) => setSelected(id);

    // CORRECT - Memoize callback
    const handleSelect = useCallback((id: string) => setSelected(id), []);
    ```

29. **[OB-DONT-029]** **Never create components over 200 lines**
    - Extract sub-components or custom hooks
    - **Enforced by:** Code review
    ```typescript
    // WRONG - Monolithic 500-line component
    function FinanceWorkspace() { /* 500 lines */ }

    // CORRECT - Decomposed into focused components
    function FinanceWorkspace() {
      return (
        <>
          <FinanceHeader />
          <FinanceMetrics />
          <FinanceCharts />
          <FinanceTable />
        </>
      );
    }
    ```

### Error Handling Anti-Patterns

30. **[OB-DONT-030]** **Never catch exceptions just to log them**
    - Let middleware handle logging
    - **Enforced by:** Code review
    ```python
    # WRONG - Pointless catch-and-re-raise
    try:
        result = process_data()
    except Exception as e:
        logger.error(str(e))
        raise  # Why catch at all?

    # CORRECT - Let exception propagate to error handler
    result = process_data()
    ```

31. **[OB-DONT-031]** **Never use exceptions for control flow**
    - Use explicit checks instead
    - **Enforced by:** Code review
    ```python
    # WRONG - Using KeyError for logic
    try:
        user = users[user_id]
    except KeyError:
        user = None

    # CORRECT - Use .get() method
    user = users.get(user_id)
    ```

32. **[OB-DONT-032]** **Never swallow exceptions silently**
    - Always log or re-raise
    - **Enforced by:** Ruff B001
    ```python
    # WRONG - Silent failure
    try:
        critical_operation()
    except Exception:
        pass  # ERROR IGNORED!

    # CORRECT - At minimum, log the error
    try:
        critical_operation()
    except Exception as e:
        logger.error("Critical operation failed", exc_info=e)
        raise
    ```

---

## Quick Reference Table

| Rule ID        | Summary                           | Enforcement          |
| -------------- | --------------------------------- | -------------------- |
| OB-DO-001      | Run pre-commit hooks              | Git hooks            |
| OB-DO-003      | Async/await for database          | Code review          |
| OB-DO-006      | sa.String() for ENUMs             | Pre-commit           |
| OB-DO-007      | Index foreign keys                | Code review          |
| OB-DO-014      | Provide test commands             | Code review          |
| OB-DO-017      | Use design tokens                 | ESLint               |
| OB-DO-019      | New migrations only               | Pre-commit           |
| OB-DONT-001    | Never edit migrations             | Pre-commit           |
| OB-DONT-004    | No bare except                    | Ruff E722            |
| OB-DONT-010    | No incomplete phase marking       | Pre-commit           |
| OB-DONT-016    | No N+1 queries                    | Code review          |
| OB-DONT-019    | No secrets in code                | .gitignore           |
| OB-DONT-020    | No f-string SQL                   | Code review          |

---

**Related:** [MCP Hub](../../MCP.md) | [Guardrails](MCP_GUARDRAILS.md) | [Shared Core](../ai/SHARED_CORE.md)
