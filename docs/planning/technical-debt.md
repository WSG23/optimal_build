# Technical Debt Inventory

**Last updated:** 2025-10-29
**Purpose:** Comprehensive list of all known technical debt so AI agents don't forget about deferred work

---

## 🤖 ARCHIVAL INSTRUCTIONS (For AI Agents)

**⚠️ DO NOT ARCHIVE THIS FILE**

This is a **LIVING DOCUMENT** that tracks ongoing technical debt across all project phases.

**Why Keep This File:**
- Technical debt is never "done" - new debt accumulates as features are added
- Future AI agents need this for Tier 2 (dependency pinning) and Tier 3 (async refactoring)
- Phase 6 infrastructure work (performance, security) references this file
- Acts as single source of truth for all deferred work

**When Items Are Completed:**
- Move from priority section to "Completed" section (bottom of file)
- Add completion date, who fixed it, commit hash
- Update "Last updated" date at top
- Keep file in root directory (do NOT move to docs/archive/)

**Related Files That MAY Be Archived:**
- [PRE_PHASE_2D_INFRASTRUCTURE_AUDIT.md](PRE_PHASE_2D_INFRASTRUCTURE_AUDIT.md) - Archive after completion
- Phase-specific checklists in docs/ - Archive after phase complete

---

## 🚨 CRITICAL: Read This First

**AI Agents (Claude, Codex):**
- This file lists ALL known technical debt in the codebase
- Each item is categorized by priority (High/Medium/Low)
- Before starting new work, check if you're touching files with known debt
- When you fix debt, move it to "Completed" section with date

**Human (Program Manager):**
- Review this quarterly
- Technical debt grows if not actively managed
- Items marked "Low" today can become "High" tomorrow

---

## High Priority (Fix Soon)

### 1. Phase 1D: Business Performance Management UI
**Status:** READY - waiting for Infrastructure Audit to complete
**Priority:** HIGH (60% complete, UI missing)
**Estimate:** 3-4 weeks
**Risk:** Blocks Phase 1 completion

**What's Missing:**
- Pipeline Kanban board component
- Deal insights panel
- Analytics panel
- ROI panel
- Manual QA checklist (8 items)

**Documentation:** [feature_delivery_plan_v2.md](docs/feature_delivery_plan_v2.md) lines 274-392
**Tracked in:** [BACKLOG.md](BACKLOG.md)

---

### 2. Phase 2B: Asset-Specific Feasibility - 3D Visualization
**Status:** READY - waiting for Infrastructure Audit to complete
**Priority:** HIGH (85% complete, 3D preview missing)
**Estimate:** 2-3 weeks (40% backend, 60% frontend UI)
**Risk:** Blocks Phase 2B completion

**What's Done:**
- ✅ Asset optimizer (curve-driven scoring, constraint logging)
- ✅ Heritage overlay backend (NHB Historic Sites, National Monuments)
- ✅ Preview job pipeline (background renders, polling endpoints)
- ✅ Visualization stub (per-asset massing layers, color legend)
- ✅ Preview job model (`preview_jobs` table) and migration
- ✅ API endpoints for job status and polling

**What's Missing (Backend - ~1 week):**
- ❌ Renderer service (Blender/Three.js node script for GLB generation)
- ❌ Asset storage & versioning (S3 or local with version management)
- ❌ Geometry builder enhancements (floor plates, podiums, setbacks)
- ❌ Prefect flow orchestration (`developer_preview_flow`)

**What's Missing (Frontend UI - ~1.5 weeks):**
- ❌ Preview status polling hook (GET every 5s with exponential backoff)
- ❌ "Rendering" banner during preview generation
- ❌ GLB viewer integration with fallback to JSON stub
- ❌ Retry CTA on failed renders
- ❌ Status chip on scenario tabs showing preview readiness
- ❌ Thumbnail loading placeholders
- ❌ WebGL 2 detection with graceful fallback

**What's Missing (Observability - ~0.5 weeks):**
- ❌ Metrics (jobs_created, jobs_succeeded, jobs_failed, duration_ms)
- ❌ Structured logging (job_id, property_id, scenario, status)
- ❌ Alerts (failure rate >10%, median duration >5min)

**Documentation:**
- [feature_delivery_plan_v2.md](docs/feature_delivery_plan_v2.md) lines 455-508
- [docs/phase2b_visualisation_stub.md](docs/phase2b_visualisation_stub.md) - **Full 4-week implementation plan**
- Frontend integration: phase2b_visualisation_stub.md Section 5 (lines 136-148)
- Timeline: Section 7 (Week 1: API, Week 2: Renderer, Week 3: Frontend+QA, Week 4: Buffer)

**Tracked in:** [BACKLOG.md](BACKLOG.md)

---

### 3. Pre-Phase 2D Infrastructure Audit (47 Startup Failures Prevention)
**Status:** IN PROGRESS (Phase 2C complete 2025-10-28)
**Priority:** CRITICAL (must do IMMEDIATELY, before 1D/2B/jurisdictions)
**Estimate:** 2 weeks (10 working days)
**Risk:** Becoming one of 47 failed startups - codebase becomes unmaintainable

**Background:**
Inc.com article analyzed 47 failed startups. Common pattern:
- Month 0-12: Works fine
- Month 13-18: Adding features breaks things
- Month 19-24: Hiring engineers just to maintain, nothing new built
- Month 25: Startup dies or starts from scratch

**We're at Month 12-15. This is the critical window.**

**Required Actions (2-week sprint):**

**Week 1: Database & Testing**
- ❌ Database indexing audit (89% of failures had no indexes)
  - Index all foreign keys
  - Index frequently queried columns
  - Test 10x query performance improvement
- ❌ Automated testing infrastructure (91% of failures had no tests)
  - Achieve >80% backend coverage
  - Set up frontend E2E tests
  - CI blocks deploy without passing tests

**Week 2: Security & Infrastructure**
- ❌ Security vulnerabilities audit (68% had security issues)
  - Fix all high/critical vulnerabilities
  - Pin all dependencies (Tier 2 dependency pinning)
  - Set up rate limiting
  - Scan for exposed secrets
- ❌ Infrastructure optimization (76% overpaid for servers)
  - Measure server utilization (avg failed startups: 13%)
  - Right-size infrastructure
  - Set up monitoring/alerts
  - Load test for 10x traffic

**Documentation:** [docs/audits/PRE-PHASE-2D-AUDIT.MD](../audits/PRE-PHASE-2D-AUDIT.MD) - Complete checklist

**Article Source:** [47 Startups Failed - Inc.com](https://www.inc.com/maria-jose-gutierrez-chavez/47-startups-failed-most-made-the-same-coding-mistake/91251802)

**Why Critical:**
- Fixes infrastructure NOW vs. 18 months of technical debt hell
- Prevents "Month 25 death" pattern
- Tier 2 dependency pinning (7 packages) is included in this sprint

---

### 4. Entitlement Enum Case Sensitivity
**Status:** READY - waiting for Infrastructure Audit to complete
**Priority:** HIGH (data drift risk)
**Estimate:** 2-4 hours
**Risk:** Database inconsistency, query failures

**Problem:**
- `EntApprovalType.category` enum currently uses uppercase (SQLAlchemy `.name` default)
- Should use lowercase (`.value`) for consistency
- Existing data may have uppercase values in database

**Solution (2 stages):**
1. **Stage 1 (low risk):** Update `SAEnum` fields in `app/models/entitlements.py` to use `values_callable=lambda enum_cls: [member.value for member in enum_cls]`
2. **Stage 2 (needs coordination):** Migration to recreate Postgres enum with lowercase literals

**Documentation:** [NEXT_STEPS_FOR_AI_AGENTS_AND_DEVELOPERS.md](docs/NEXT_STEPS_FOR_AI_AGENTS_AND_DEVELOPERS.md) lines 15-21

**Note:** Phase 2C complete (2025-10-28), can start after Infrastructure Audit finishes.

---

## Medium Priority (Fix After Infrastructure Audit)

### 5. Dependency Pinning (Tier 2)
**Status:** READY - waiting for Infrastructure Audit + Phase 1D/2B residual work
**Priority:** Medium
**Estimate:** 1-2 hours
**Risk:** Security, reproducibility, CI non-determinism

**Problem:**
7 dependencies in `backend/requirements.txt` use `>=` instead of `==`:
- asyncpg>=0.30.0
- shapely>=2.0.6
- pandas>=2.2.3
- numpy>=1.26.0
- statsmodels>=0.14.0
- scikit-learn>=1.3.0
- reportlab>=4.0.0

**Solution:**
Full instructions in `.github/ISSUE_TEMPLATE/tier2-dependency-pinning.md`

**Quick steps:**
1. Run: `pip freeze | grep -E "asyncpg|shapely|pandas|numpy|statsmodels|scikit-learn|reportlab"`
2. Update `backend/requirements.txt` with exact versions
3. Run: `make verify` and `pytest backend/tests/`
4. Remove exception from `.coding-rules-exceptions.yml` (line 27-29)
5. Commit and push

**Exception:** `.coding-rules-exceptions.yml` lines 27-29 (rule_4_dependency_pinning)
**Tracked in:** [BACKLOG.md](BACKLOG.md)

---

### Documentation Consolidation – Link Remediation (Phase 1)
**Status:** In progress (paused 2025-10-29)
**Priority:** Medium
**Estimate:** 1-2 hours once resumed
**Risk:** Broken documentation guidance; AI agents following outdated instructions

**Background:** Root Markdown files relocated into `docs/` hierarchy; `scripts/verify_docs.py` now reports 81 broken references (legacy paths like `TESTING_KNOWN_ISSUES.md`, `UI_STATUS.md`, etc.).

**Next Steps:**
- Update doc references to new locations (e.g., `docs/development/testing/known-issues.md`, `docs/planning/ui-status.md`).
- Resolve references to removed files by linking to current equivalents or rewriting guidance.
- Re-run `.venv/bin/python scripts/verify_docs.py` until no broken references remain.
- Resume consolidation plan (docs/README index, CI hook) after link cleanup.

**Tracking:** Also logged in [docs/planning/backlog.md](backlog.md) (Active section) and detailed in [docs/documentation_consolidation_strategy.md](../documentation_consolidation_strategy.md).

---

### 5. Import Ordering Disagreement (isort vs ruff)
**Status:** Active exception
**Priority:** Medium
**Estimate:** 30 minutes
**Risk:** Pre-commit hook confusion

**Problem:**
isort and ruff disagree on `backend._compat` import ordering in 2 files:
- `backend/app/api/v1/advanced_intelligence.py`
- `backend/app/api/v1/agents.py`

**Solution:**
Either:
- Add `# isort: skip` comment to the import
- Configure ruff/isort to agree
- Pick one tool and remove the other

**Exception:** `.coding-rules-exceptions.yml` lines 48-51 (rule_7_code_quality)

---

## Low Priority (Fix When Touching Files)

### 6. Async/Await Refactoring (Tier 3)
**Status:** Deferred - fix when touching those files
**Priority:** Low
**Estimate:** 4-6 hours
**Risk:** Performance (minor), consistency

**Problem:**
3 legacy API files use sync `Session` instead of `AsyncSession`:
- `backend/app/api/v1/users_db.py`
- `backend/app/api/v1/singapore_property_api.py`
- `backend/app/api/v1/projects_api.py`

**Solution:**
Refactor to use AsyncSession when you need to modify these files anyway.

**When to fix:**
- When refactoring those modules for other reasons
- Or as part of async/await consistency sprint

**Exception:** `.coding-rules-exceptions.yml` lines 22-26 (rule_2_async)
**Tracked in:** [BACKLOG.md](BACKLOG.md)

---

### 7. Legacy Migrations with Enum Pattern Issues
**Status:** Grandfathered - do not modify
**Priority:** Low (isolated to old migrations)
**Estimate:** N/A
**Risk:** None (new migrations use correct pattern)

**Problem:**
10 pre-existing migrations use `sa.Enum(..., create_type=False)` pattern (now forbidden).

**Solution:**
DO NOT fix. These migrations are grandfathered and should never be modified.

**New migrations:** Use correct pattern (see CODING_RULES.md Section 1.2)

**Exception:** `.coding-rules-exceptions.yml` lines 33-46 (rule_1_2_enum_pattern)

---

### 8. Test DB Setup Issues (Singapore Property)
**Status:** Known issue
**Priority:** Low
**Estimate:** Unknown
**Risk:** Test failures (not production)

**Problem:**
`backend/app/models/singapore_property.py` triggers Rule 5 (Singapore compliance) failures due to test DB setup issues, not actual compliance violations.

**Solution:**
Fix test database setup to properly handle Singapore-specific schema.

**Exception:** `.coding-rules-exceptions.yml` lines 30-32 (rule_5_singapore)

---

### 9. Long URL in Documentation String
**Status:** Minor annoyance
**Priority:** Low
**Estimate:** 5 minutes
**Risk:** None (just a linter warning)

**Problem:**
`scripts/smoke_test_pdfs.py` has a long URL in a documentation string that triggers line length checks.

**Solution:**
Split URL across multiple lines or add exception comment.

**Exception:** `.coding-rules-exceptions.yml` lines 52-53 (rule_7_code_quality)

---

## Infrastructure Work (Phase 6 - After Phase 2D-5)

### 12. Performance Optimization (Phase 6D)
**Status:** Deferred - Phase 6 work
**Priority:** Low (20% complete, wait for Phase 6)
**Estimate:** 4-6 weeks
**Risk:** User experience, scalability

**What Exists:**
- ✅ Database indexes
- ✅ API pagination
- ⚠️ Basic caching

**What's Missing:**
- ❌ CDN for static assets
- ❌ Lazy loading for large datasets
- ❌ Query optimization
- ❌ Frontend bundle optimization
- ❌ Real-time performance monitoring

**Acceptance Criteria:**
- Page load < 2 seconds
- API responses < 500ms
- Large datasets paginated
- Real-time monitoring in place

**Documentation:** [feature_delivery_plan_v2.md](docs/feature_delivery_plan_v2.md) lines 1557-1578

---

### 13. Security Hardening (Phase 6E)
**Status:** Deferred - Phase 6 work
**Priority:** Low (50% complete, wait for Phase 6)
**Estimate:** 8-12 weeks
**Risk:** Security vulnerabilities, compliance

**What Exists:**
- ✅ JWT authentication
- ✅ Role-based access control
- ✅ HTTPS enforced
- ⚠️ Basic input validation

**What's Missing:**
- ❌ Penetration testing
- ❌ Security audit by third party
- ❌ Rate limiting
- ❌ Advanced threat detection
- ❌ Compliance certifications (ISO, SOC2)

**Acceptance Criteria:**
- Third-party security audit passed
- Rate limiting on all APIs
- Threat detection active
- Compliance certifications obtained

**Documentation:** [feature_delivery_plan_v2.md](docs/feature_delivery_plan_v2.md) lines 1582-1604

---

## Deferred (Not Urgent)

### 10. Legacy Migration Downgrade Guards
**Status:** Accepted technical debt
**Priority:** Low
**Estimate:** N/A (low value)
**Risk:** None (downgrades rarely used in production)

**Problem:**
7 migrations don't follow Rule 1 (migration idempotency) but use `if_exists=True` guards in downgrade() instead.

**Why deferred:**
- Downgrades are rarely run in production
- Fixing would require rewriting migration history (dangerous)
- Guards provide acceptable safety

**Files:**
- backend/migrations/versions/20250220_000009_add_agent_advisory_feedback.py
- backend/migrations/versions/20250220_000010_add_listing_integration_tables.py
- backend/migrations/versions/20250220_000011_add_business_performance_tables.py
- backend/migrations/versions/20250220_000012_add_commission_tables.py
- backend/migrations/versions/20250220_000013_add_performance_snapshots.py
- backend/migrations/versions/20251013_000014_add_developer_due_diligence_checklists.py
- backend/migrations/versions/20251013_000015_add_developer_condition_assessments.py

**Exception:** `.coding-rules-exceptions.yml` lines 4-18 (rule_1_migrations)

---

## Code TODOs (Found in Source)

### 11. Market Condition Adjustments
**Location:** `backend/app/services/agents/development_potential_scanner.py`
**Priority:** Low
**Estimate:** 2-4 hours
**Risk:** Inaccurate calculations

**TODO comments:**
```python
# TODO: Adjust based on market conditions and location factors
# TODO: Add market-based opportunities
```

**Context:** Development potential scanner needs market-aware adjustments.

**When to fix:** When implementing market intelligence integration (Phase 1B enhancements).

---

## Completed

### 2025-10-26: Migration Validation Infrastructure (Phases 1-3)
**Completed by:** Claude
**Commits:** 4cf497e, e7a987e, d848b49, d2b98c3

**What was done:**
- ✅ Phase 1: Pre-commit hook for ENUM pattern validation
- ✅ Phase 2: Schema validation tests (8 tests)
- ✅ Phase 3: CI workflow integration
- ✅ Fixed check_coding_rules.py to use venv Python
- ✅ Fixed missing Sequence import in finance.py

**Impact:**
- 90%+ reduction expected in migration issues
- 100% coverage of known migration patterns
- Clear error messages at commit time

---

## How to Use This File

### When Starting Work

**AI Agents:** Before implementing any feature:
1. Read this file
2. Check if you're touching files with known debt (grep for filename)
3. If debt is "Low" priority and you're modifying that file anyway, fix it!
4. If debt is "High" or "Medium", check if it's unblocked

### When Fixing Debt

1. Move item from priority section to "Completed"
2. Add date, who fixed it, commit hash
3. Update "Last updated" date at top
4. If exception exists in `.coding-rules-exceptions.yml`, remove it
5. Update [BACKLOG.md](BACKLOG.md) if the item was tracked there

### When Discovering New Debt

1. Add to appropriate priority section
2. Include: Status, Priority, Estimate, Risk, Problem, Solution
3. Add exception to `.coding-rules-exceptions.yml` if needed
4. Update "Last updated" date
5. Tell the user about the new debt item

---

## Related Documentation

- [BACKLOG.md](BACKLOG.md) - AI agent work queue (active tasks)
- [CODING_RULES.md](CODING_RULES.md) - Rules that created these exceptions
- [.coding-rules-exceptions.yml](.coding-rules-exceptions.yml) - Formal exception list
- [docs/feature_delivery_plan_v2.md](docs/feature_delivery_plan_v2.md) - Phase completion tracking
- [docs/NEXT_STEPS_FOR_AI_AGENTS_AND_DEVELOPERS.md](docs/NEXT_STEPS_FOR_AI_AGENTS_AND_DEVELOPERS.md) - Decision guide

---

## Metrics

**Total technical debt items:** 13 active + 1 completed
**High priority:** 3 items (5-7 weeks total)
**Medium priority:** 2 items (~2 hours total)
**Low priority:** 6 items (~10 hours total)
**Infrastructure (Phase 6):** 2 items (12-18 weeks total - deferred until Phase 6)

**Most common debt type:** Migration pattern issues (4 items)
**Biggest risk:** Phase 1D/2B incomplete (blocks phase progression)
**Easiest wins:** Dependency pinning (1-2 hours), import ordering (30 min)

**Last review:** 2025-10-27
**Next review:** 2026-01-27 (quarterly)
