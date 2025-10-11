# IMMEDIATE NEXT STEPS FOR CODEX

> **Last Updated:** 2025-10-11 by Claude
> **Current Phase:** Phase 1C completion → Next options

---

## 📋 Current Status

**You just completed:** Phase 1C Listing Integrations (Mock Flow with Token Lifecycle) ✅

### ✅ Recently Completed Phases:

| Phase | Feature | Status | Test Status |
|-------|---------|--------|-------------|
| **1A** | Agent GPS Capture | ✅ Complete | ✅ Backend passing |
| **1A** | Marketing Pack Generation | ✅ Complete | ✅ Backend passing |
| **1B** | Agent Advisory (Asset Mix, Positioning, Absorption, Feedback) | ✅ Complete | ✅ Backend passing, ⚠️ Frontend timing issue (documented) |
| **1C** | Listing Integrations Mock (PropertyGuru + Token Lifecycle) | ✅ Complete | ✅ Backend passing, ⚠️ Frontend timing issue (documented) |

### 📊 Overall Progress:
- ✅ **~75%** of Phase 1 (Agent Foundation) complete
- ⏸️ Waiting for human-led agent validation sessions
- ⚠️ Frontend tests have known JSDOM timing issues → See [TESTING_KNOWN_ISSUES.md](../TESTING_KNOWN_ISSUES.md)

### 🔍 What We Just Verified (2025-10-11):
- ✅ Backend test passes: `test_propertyguru_mock_flow` exercises full token lifecycle
- ✅ Token helpers work: `is_token_valid()` and `needs_refresh()` in accounts.py
- ✅ 401 on expired tokens works correctly
- ✅ Database migration applied: `listing_integration_accounts` and `listing_publications` tables exist
- ⚠️ Frontend test fails due to documented JSDOM async timing issue (feature works)

---

## 🎯 What You Should Work On Next

### CHOOSE ONE OF THESE OPTIONS:

#### ⭐ **Option A: Harden Phase 1C - Token Encryption** (RECOMMENDED)

**Why this first:**
- Security requirement before accepting real OAuth credentials
- Prevents storing plaintext tokens in production
- Relatively small, focused task

**What to build:**
1. Add encryption/decryption for `access_token` and `refresh_token` fields
   - Use `cryptography.fernet.Fernet` or AWS KMS
   - Store encryption key in environment variable
   - Encrypt before save, decrypt on load
2. Update `ListingIntegrationAccountService` to handle encryption
3. Add tests for encrypted token storage/retrieval

**Files to modify:**
- `backend/app/services/integrations/accounts.py` - Add encryption helpers
- `backend/app/models/listing_integration.py` - Add property methods for token access
- `backend/tests/test_services/test_listing_integration_accounts.py` - Test encryption

**Acceptance criteria:**
- Tokens stored encrypted in database
- Service can decrypt and use tokens
- Tests verify encryption/decryption works
- Environment variable for encryption key

**Estimated effort:** 1-2 days

**References:**
- [Cryptography docs](https://cryptography.io/en/latest/fernet/)
- Similar pattern in existing codebase: `backend/app/core/security.py`

---

#### **Option B: Extend Mock Pattern to EdgeProp + Zoho**

**Why this:**
- Completes the mock integration foundation
- Validates the abstraction pattern works for multiple providers
- Enables testing multi-platform publishing

**What to build:**
1. Create `EdgePropClient` similar to `PropertyGuruClient`
2. Create `ZohoCRMClient` for lead management
3. Add endpoints for EdgeProp and Zoho in `listings.py`
4. Update frontend to show all three providers

**Files to create/modify:**
- `backend/app/services/integrations/edgeprop.py` - New client
- `backend/app/services/integrations/zoho.py` - New client
- `backend/app/api/v1/listings.py` - Add new endpoints
- `frontend/src/pages/AgentIntegrationsPage.tsx` - Show all providers
- `backend/tests/test_api/test_listing_integrations.py` - Test new flows

**Acceptance criteria:**
- Can connect/disconnect EdgeProp and Zoho accounts
- Can publish listings to all three platforms
- Token lifecycle works for all providers
- Tests exercise all three mocks

**Estimated effort:** 3-4 days

---

#### **Option C: Real PropertyGuru OAuth Implementation**

**Why this:**
- Enables real production integration
- Tests with actual API
- Validates token refresh flow

**BLOCKERS:**
- ⚠️ Requires PropertyGuru API credentials from user
- ⚠️ Requires Option A (encryption) to be done first
- ⚠️ May need production OAuth callback URL

**What to build:**
1. Implement real OAuth flow (authorization_code grant)
2. Implement token refresh using refresh_token
3. Implement real listing publish API call
4. Handle API errors and rate limiting

**Files to modify:**
- `backend/app/services/integrations/propertyguru.py` - Replace mocks with real HTTP
- `backend/app/api/v1/listings.py` - Update OAuth callback handling
- `frontend/src/pages/AgentIntegrationsPage.tsx` - Real OAuth redirect flow

**Acceptance criteria:**
- OAuth flow redirects to PropertyGuru and back
- Stores real access/refresh tokens (encrypted)
- Can publish real listing to PropertyGuru
- Token refresh works automatically

**Estimated effort:** 5-7 days

**Prerequisites:**
1. Complete Option A (encryption) first
2. Obtain PropertyGuru API credentials from user
3. Configure OAuth callback URL

---

#### **Option D: Move to Phase 1D - Business Performance**

**What this is:**
- Agent deal tracking
- Commission calculations
- Performance analytics
- Portfolio management

**Why NOT recommended yet:**
- Phase 1B/1C validation hasn't happened yet
- Better to harden existing work first
- User may have feedback on advisory/integrations

**When to do this:**
- After user validates Phase 1A-1C
- After at least Option A (encryption) is done

---

## 🚫 What NOT to Do Next

**DO NOT start these yet:**
- ❌ Phase 2 (Developer Tools) - must finish Phase 1 and validate first
- ❌ Phase 3 (Architects) - way too early
- ❌ Phase 4 (Engineers) - way too early
- ❌ Phase 5 (Gov APIs) - can start later in parallel
- ❌ Phase 6 (Polish) - much later

**Why?**
- The delivery plan follows logical dependencies
- Each phase must be validated before moving on
- Jumping ahead creates integration debt

---

## 📚 Key Documents You Must Reference

**Before starting work:**
1. ✅ Read this file (NEXT_STEPS_FOR_CODEX.md)
2. ✅ Check [TESTING_KNOWN_ISSUES.md](../TESTING_KNOWN_ISSUES.md) - Known test issues
3. ✅ Review [FEATURES.md](../FEATURES.md) - Source of truth for requirements
4. ✅ Check [feature_delivery_plan_v2.md](feature_delivery_plan_v2.md) - Full roadmap

**While coding:**
- [CODING_RULES.md](../CODING_RULES.md) - Code standards and patterns
- [TESTING_DOCUMENTATION_SUMMARY.md](../TESTING_DOCUMENTATION_SUMMARY.md) - Testing workflows

**After completing features:**
- Update this file (NEXT_STEPS_FOR_CODEX.md)
- Update [feature_delivery_plan_v2.md](feature_delivery_plan_v2.md)
- Run tests and document status

---

## ✅ Definition of Done

Before marking ANY feature complete, ensure:

### Code Quality:
- [ ] All backend tests pass
- [ ] Code follows CODING_RULES.md
- [ ] No linting errors
- [ ] Imports properly ordered

### Functionality:
- [ ] Feature works as described in FEATURES.md
- [ ] Manual testing confirms behavior
- [ ] Error cases handled gracefully

### Documentation:
- [ ] Code comments explain complex logic
- [ ] API documentation updated (if applicable)
- [ ] This file (NEXT_STEPS_FOR_CODEX.md) updated
- [ ] feature_delivery_plan_v2.md status updated

### Testing:
- [ ] Backend tests written and passing
- [ ] Frontend tests written (even if timing issues exist)
- [ ] Test coverage documented

### Known Issues:
- [ ] Frontend JSDOM timing issues documented in TESTING_KNOWN_ISSUES.md
- [ ] Workarounds clearly noted
- [ ] Manual testing confirms feature works despite test issues

---

## 📊 Progress Tracking

### Current Phase Status:
```
Phase 1A: GPS Capture + Marketing ✅ COMPLETE
Phase 1B: Agent Advisory ✅ COMPLETE
Phase 1C: Listing Integrations (Mock) ✅ COMPLETE
Phase 1C: Token Encryption ❌ NOT STARTED ← RECOMMENDED NEXT
Phase 1C: EdgeProp/Zoho Mocks ❌ NOT STARTED
Phase 1C: Real PropertyGuru OAuth ❌ NOT STARTED (blocked on credentials)
Phase 1D: Business Performance ❌ NOT STARTED
```

### When You Complete a Feature:
1. Update status in this file
2. Update `feature_delivery_plan_v2.md`
3. Commit with message: `Complete [feature name] - Phase [X][Y]`
4. Run tests and document results
5. Update TESTING_KNOWN_ISSUES.md if new issues found

---

## 🤝 When to Ask for Help

**ASK the user when:**
- ✅ You need PropertyGuru/EdgeProp/Zoho API credentials
- ✅ You're unsure about encryption key management approach
- ✅ You need validation of implementation decisions
- ✅ You encounter blockers that prevent progress
- ✅ You want to clarify feature requirements from FEATURES.md
- ✅ You discover new test issues that need documenting

**DON'T ask about:**
- ❌ General implementation decisions (you can make those)
- ❌ Code structure (follow CODING_RULES.md)
- ❌ Testing approach (follow existing patterns)
- ❌ Documentation format (follow existing docs)
- ❌ Known test timing issues (documented in TESTING_KNOWN_ISSUES.md)

---

## 🔄 Validation Checkpoint

**After Phase 1 is complete:**
- Human will conduct agent validation sessions
- Feedback will be incorporated
- Then proceed to Phase 2 (Developer tools)

**Do not skip validation!** It's critical for ensuring product-market fit.

---

## 📞 Quick Reference for New AI Agents

**"I'm a new AI agent picking up this project. Where do I start?"**

1. ✅ Read [docs/README.md](README.md) - Start here (5 min)
2. ✅ Read this file - Current status and next tasks (10 min)
3. ✅ Read [TESTING_KNOWN_ISSUES.md](../TESTING_KNOWN_ISSUES.md) - Don't waste time on known issues (5 min)
4. ✅ Choose Option A, B, or C above and start building

**"What's the current state?"**
- Phase 1A/1B/1C mock flows are complete
- Backend tests passing
- Frontend tests have known timing issues (not bugs)
- Next: Choose token encryption, extend mocks, or real OAuth

**"Are there any known issues?"**
- Yes! Frontend JSDOM timing issues → See TESTING_KNOWN_ISSUES.md
- Don't try to fix them - they're documented test harness limitations
- Features work correctly in manual testing

**"What should I build next?"**
- **Recommended:** Option A (Token Encryption) - 1-2 days, critical for security
- **Alternative:** Option B (EdgeProp/Zoho Mocks) - 3-4 days, extends pattern
- **Blocked:** Option C (Real OAuth) - needs credentials and encryption first

---

**Ready to start? Pick Option A (Token Encryption) and let's make it production-ready!** 🔐
