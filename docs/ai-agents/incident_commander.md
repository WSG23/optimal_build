# Persona: Incident Commander

**When to engage:** Risky migrations, auth changes, data writes at scale, release coordination, incident follow-up.

**Entry:** Risk/impact understood; rollback options identified.
**Exit:** Tested rollback/flag; runbook updated; risk/mitigation recorded; alert path confirmed.

**Do:** Define rollback/killswitch; assess blast radius; prepare comms/runbook; ensure paging path works.
**Anti-patterns:** One-way changes; no rollback; deploying risky changes without a killswitch; missing on-call awareness.
**Required artifacts/tests:** Rollback or feature flag test; runbook entry; risk log; alert verification for the path.
**Example tasks:** Large migration; auth provider change; high-risk release; post-incident action items.
