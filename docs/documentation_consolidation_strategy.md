# Documentation Consolidation Strategy

**Status**: Recommendation
**Created**: 2025-10-29
**Verification Results (2025-10-29)**: Phase 1 relocation complete; current `scripts/verify_docs.py` run reports **81 broken references** pending link updates.

## 📊 Current State Analysis

### Files Inventory
- **Total MD files**: 76 (67 after excluding .pytest_cache/README.md duplicates)
- **Root level**: 29 files (38% of total) ⚠️ **TOO MANY**
- **docs/ directory**: 40 files (well organized)
- **Other**: 7 files (GitHub templates, frontend READMEs)

### Issues Found
- **Broken references**: 70 (mostly to moved/renamed files)
- **Stale content**: TODO items, old year references, deprecated markers
- **Root directory clutter**: 29 top-level MD files create confusion

---

## 🎯 Consolidation Goals

1. **Reduce root-level files from 29 → 10** (keep only essential entry points)
2. **Fix all 70 broken references**
3. **Create clear documentation hierarchy**
4. **Establish single source of truth** for each topic
5. **Make it easy for AI agents to find what they need**

---

## 📁 Proposed Structure

```
optimal_build/
├── README.md                          # Project overview (keep)
├── START_HERE.md                      # AI agent entry point (keep)
├── CONTRIBUTING.md                    # Contributor guide (keep)
├── CODING_RULES.md                    # Development standards (keep)
│
├── docs/
│   ├── README.md                      # Documentation index
│   │
│   ├── ai-agents/                     # NEW: AI agent instructions
│   │   ├── claude.md                  # ← Move from /CLAUDE.md
│   │   ├── codex.md                   # ← Move from /CODEX.md
│   │   ├── handoff_playbook.md        # (already here)
│   │   └── next_steps.md              # ← Rename from NEXT_STEPS_FOR_AI_AGENTS_AND_DEVELOPERS.md
│   │
│   ├── architecture/                  # Architecture docs
│   │   ├── overview.md                # ← Merge architecture.md + architecture_honest.md
│   │   ├── data-models.md             # ← Move from /DATA_MODELS_TREE.md
│   │   ├── api-endpoints.md           # ← Move from /API_ENDPOINTS.md
│   │   └── geometry-contracts.md      # (already here)
│   │
│   ├── development/                   # Developer guides
│   │   ├── testing/                   # NEW: Testing docs
│   │   │   ├── overview.md            # ← Move from /TEST_ALL_FEATURES.md
│   │   │   ├── known-issues.md        # ← Move from /TESTING_KNOWN_ISSUES.md
│   │   │   ├── pdf-checklist.md       # (already here)
│   │   │   └── advisory.md            # ← Move from /TESTING_ADVISORY.md
│   │   │
│   │   ├── debugging/                 # NEW: Debugging guides
│   │   │   ├── cad-detection.md       # ← Merge CAD_DETECTION_QUICK_FIX + DEBUG_CAD_DETECTION
│   │   │   └── numpy-fix.md           # ← Move from /NUMPY_FIX_STATUS.md
│   │   │
│   │   └── ci.md                      # (already here)
│   │
│   ├── planning/                      # Project planning
│   │   ├── roadmap.md                 # ← Move from /PROJECT_ROADMAP.md
│   │   ├── features.md                # ← Move from /FEATURES.md
│   │   ├── backlog.md                 # ← Move from /BACKLOG.md
│   │   ├── technical-debt.md          # ← Move from /TECHNICAL_DEBT.md
│   │   ├── transition-checklist.md    # ← Move from /TRANSITION_PHASE_CHECKLIST.md
│   │   └── ui-status.md               # ← Move from /UI_STATUS.md
│   │
│   ├── audits/                        # NEW: Audit/compliance reports
│   │   ├── PRE-PHASE-2D-AUDIT.MD      # ← Move from /PRE_PHASE_2D_INFRASTRUCTURE_AUDIT.md
│   │   └── smoke-test-fix-report.md   # ← Move from /SMOKE_TEST_FIX_REPORT.md
│   │
│   ├── phases/                        # Phase delivery plans
│   │   ├── phase-1d-business-performance.md
│   │   ├── phase-2b-asset-optimizer.md
│   │   ├── phase-2b-heritage-ingestion.md
│   │   ├── phase-2b-finance-architecture.md
│   │   ├── phase-2b-visualisation-stub.md
│   │   └── phase-2c-finance-delivery.md
│   │
│   ├── api/                           # API documentation
│   │   ├── feasibility.md
│   │   ├── finance.md
│   │   ├── export.md
│   │   └── entitlements.md
│   │
│   ├── playbooks/                     # Operational playbooks
│   │   ├── jurisdiction-expansion.md
│   │   ├── solo-founder-guide.md
│   │   └── reviewer-sop.md
│   │
│   ├── agents/                        # Agent-specific docs
│   │   ├── marketing-pack-quickstart.md
│   │   └── site-capture.md            # ← Move from frontend/
│   │
│   ├── validation/                    # User validation
│   │   ├── live-testing-guide.md
│   │   ├── live-walkthrough-plan.md
│   │   └── outreach-drafts.md
│   │
│   └── archive/                       # Deprecated docs
│       └── feature_delivery_plan_v1_deprecated.md
│
└── .github/
    ├── PULL_REQUEST_TEMPLATE.md
    └── ISSUE_TEMPLATE/
        └── tier2-dependency-pinning.md
```

---

## 🚀 Implementation Plan

### Phase 1: Fix Broken References (Priority 1)
**Goal**: Make all existing docs valid before moving them

1. Run `python scripts/verify_docs.py` to get full report
2. For each broken reference:
   - If file was moved: Update path
   - If file was deleted: Remove reference or mark as deprecated
   - If file was renamed: Update to new name
3. Verify with `python scripts/verify_docs.py` until 0 errors

**Estimated effort**: 2-4 hours

### Phase 2: Consolidate Root Files (Priority 1)
**Goal**: Move 19 files from root → docs/ subdirectories

```bash
# Create new directories
mkdir -p docs/{ai-agents,development/testing,development/debugging,planning,audits}

# Move AI agent docs
git mv CLAUDE.md docs/ai-agents/claude.md
git mv CODEX.md docs/ai-agents/codex.md
git mv docs/NEXT_STEPS_FOR_AI_AGENTS_AND_DEVELOPERS.md docs/ai-agents/next_steps.md

# Move testing docs
git mv TEST_ALL_FEATURES.md docs/development/testing/overview.md
git mv TESTING_KNOWN_ISSUES.md docs/development/testing/known-issues.md
git mv TESTING_ADVISORY.md docs/development/testing/advisory.md
git mv TESTING_DOCUMENTATION_SUMMARY.md docs/development/testing/summary.md

# Move debugging docs
git mv DEBUG_CAD_DETECTION.md docs/development/debugging/cad-detection-debug.md
git mv CAD_DETECTION_QUICK_FIX.md docs/development/debugging/cad-detection-quickfix.md
git mv NUMPY_FIX_STATUS.md docs/development/debugging/numpy-fix.md
git mv DETECTION_PAGE_REALITY_CHECK.md docs/development/debugging/detection-page-reality-check.md

# Move planning docs
git mv PROJECT_ROADMAP.md docs/planning/roadmap.md
git mv FEATURES.md docs/planning/features.md
git mv BACKLOG.md docs/planning/backlog.md
git mv TECHNICAL_DEBT.md docs/planning/technical-debt.md
git mv TRANSITION_PHASE_CHECKLIST.md docs/planning/transition-checklist.md
git mv UI_STATUS.md docs/planning/ui-status.md

# Move audit reports
git mv PRE_PHASE_2D_INFRASTRUCTURE_AUDIT.md docs/audits/PRE-PHASE-2D-AUDIT.MD
git mv SMOKE_TEST_FIX_REPORT.md docs/audits/smoke-test-fix-report.md

# Move architecture docs
git mv DATA_MODELS_TREE.md docs/architecture/data-models.md
git mv API_ENDPOINTS.md docs/architecture/api-endpoints.md
```

**Estimated effort**: 1 hour (+ fixing all updated links)

### Phase 3: Merge Duplicate/Overlapping Content (Priority 2)
**Goal**: Eliminate redundancy

1. **Merge architecture.md + architecture_honest.md** → `docs/architecture/overview.md`
   - Keep the "honest" technical details
   - Add executive summary from architecture.md

2. **Merge CAD detection docs** → `docs/development/debugging/cad-detection.md`
   - Combine DEBUG_CAD_DETECTION + CAD_DETECTION_QUICK_FIX + DETECTION_PAGE_REALITY_CHECK
   - Create sections: Overview, Quick Fix, Deep Debugging, Reality Check

3. **Consolidate testing docs** → Create master `docs/development/testing/README.md`
   - Link to all testing sub-docs
   - Single entry point for testing guidance

**Estimated effort**: 3-4 hours

### Phase 4: Update START_HERE.md (Priority 1)
**Goal**: Update the authoritative AI agent entry point

Update [START_HERE.md](../START_HERE.md) to reflect new structure:

```markdown
## 📚 Complete Documentation Inventory

### Essential Entry Points
- [README.md](README.md) - Project overview
- [CONTRIBUTING.md](CONTRIBUTING.md) - How to contribute
- [CODING_RULES.md](CODING_RULES.md) - Development standards

### For AI Agents
- [docs/ai-agents/claude.md](docs/ai-agents/claude.md) - Claude-specific instructions
- [docs/ai-agents/codex.md](docs/ai-agents/codex.md) - Codex-specific instructions
- [docs/ai-agents/handoff_playbook.md](docs/ai-agents/handoff_playbook.md) - Session handoff guide
- [docs/ai-agents/next_steps.md](docs/ai-agents/next_steps.md) - Mandatory next actions

### Architecture & APIs
- [docs/architecture/overview.md](docs/architecture/overview.md) - System architecture
- [docs/architecture/api-endpoints.md](docs/architecture/api-endpoints.md) - All API endpoints
- [docs/architecture/data-models.md](docs/architecture/data-models.md) - Database models

### Development & Testing
- [docs/development/testing/overview.md](docs/development/testing/overview.md) - Testing guide
- [docs/development/testing/known-issues.md](docs/development/testing/known-issues.md) - Known test issues
- [docs/development/debugging/cad-detection.md](docs/development/debugging/cad-detection.md) - CAD debugging

### Planning & Status
- [docs/planning/roadmap.md](docs/planning/roadmap.md) - Product roadmap
- [docs/planning/features.md](docs/planning/features.md) - Feature inventory
- [docs/planning/technical-debt.md](docs/planning/technical-debt.md) - Tech debt tracking
- [docs/audits/PRE-PHASE-2D-AUDIT.MD](docs/audits/PRE-PHASE-2D-AUDIT.MD) - Infrastructure audit (80% coverage requirement)
```

**Estimated effort**: 30 minutes

### Phase 5: Create Documentation Index (Priority 2)
**Goal**: Make docs/README.md the comprehensive guide

Create `docs/README.md` with:
- Table of contents for all subdirectories
- Quick links to most common docs
- Search tips for AI agents

**Estimated effort**: 1 hour

### Phase 6: Add Automated Verification (Priority 3)
**Goal**: Prevent documentation rot

1. Add `scripts/verify_docs.py` to pre-commit hooks (warning only)
2. Add to CI pipeline (fail on broken links)
3. Create GitHub Action to run weekly and open issues for broken links

**Estimated effort**: 2 hours

---

## ✅ Success Criteria

1. **Root directory has ≤ 10 MD files** (down from 29)
2. **Zero broken references** (verify with `scripts/verify_docs.py`)
3. **All docs have clear ownership** (no topic duplication)
4. **AI agents can find docs in < 2 steps** from START_HERE.md
5. **Automated verification runs in CI**

---

## 📋 Files to Keep in Root (10 total)

These are the ONLY files that should remain in the project root:

1. **README.md** - Project overview (first thing people see)
2. **START_HERE.md** - AI agent entry point (mandatory for agents)
3. **CONTRIBUTING.md** - Contributor onboarding
4. **CODING_RULES.md** - Development standards (enforced by CI)
5. **.github/** - GitHub templates (must be here for GitHub to find them)

**Everything else moves to docs/**

---

## 🔄 Maintenance Strategy

### For Humans
- **Before creating new doc**: Check if existing doc can be updated instead
- **When moving/renaming files**: Run `scripts/verify_docs.py` before committing
- **Weekly**: Review [docs/planning/technical-debt.md](planning/technical-debt.md) for stale docs

### For AI Agents
- **Always start with [START_HERE.md](../START_HERE.md)** - it's the single source of truth
- **When referencing files**: Use relative paths from project root
- **When creating new docs**: Place in appropriate `docs/` subdirectory, not root
- **After making changes**: Suggest running `python scripts/verify_docs.py`

---

## 📊 Before/After Comparison

### Before (Current State)
```
Root:    29 MD files ❌ (cluttered, hard to find things)
docs/:   40 MD files ✅ (organized but incomplete)
Broken:  70 references ❌
Dupes:   0 (good!) ✅
```

### After (Target State)
```
Root:    5 MD files ✅ (clean, clear entry points)
docs/:   64 MD files ✅ (comprehensive, organized by purpose)
Broken:  0 references ✅
Dupes:   0 ✅
```

**Net improvement**: 87% fewer root files, 100% fewer broken refs, same zero duplicates

---

## 🎬 Next Steps

1. **Get approval** for this consolidation strategy
2. **Create feature branch**: `git checkout -b docs/consolidation`
3. **Execute Phase 1** (fix broken refs) - can be done in parallel with other work
4. **Execute Phase 2** (move files) - requires coordination with team
5. **Execute Phase 3-6** - incremental improvements
6. **Create PR** with summary of changes
7. **Update all AI agent prompts** to reference new locations

**Total estimated effort**: 8-12 hours
**Recommended timeline**: 2-3 days (to allow for review between phases)

---

## 🔗 Related Tools

- **Verification script**: [scripts/verify_docs.py](../scripts/verify_docs.py)
- **Run verification**: `python scripts/verify_docs.py`
- **AI agent instructions**: Update [START_HERE.md](../START_HERE.md) after consolidation

---

**Approval Status**: ⏳ Awaiting user approval
**Implementation Status**: 📝 Planning phase
