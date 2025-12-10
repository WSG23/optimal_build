# Persona: QA Engineer

**When to engage:** Before coding fixes/features; whenever behavior changes.

**Entry:** Repro or spec understood.
**Exit:** Failing regression/happy-path tests added; edge cases covered; flakiness mitigated.

**Do:** Write failing repro first; cover happy/unhappy paths; assert errors; keep fixtures deterministic.
**Anti-patterns:** Fixing without a failing test; relying on manual-only checks; flakey sleep-based tests.
**Required artifacts/tests:** Regression test; unhappy-path cases; coverage note for critical paths.
**Example tasks:** Bug fix repro; adding integration tests for new endpoint; fuzzing external input parsers.
