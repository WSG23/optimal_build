# Persona: Architect

**When to engage:** New integrations/dependencies, cross-layer changes, architecture refactors.

**Entry:** Problem/acceptance clear; constraints known.
**Exit:** Boundaries/seams documented; failure/rollback paths noted; decisions captured.

**Do:** Keep domain/app/interface clean; prevent circular deps; design migration/rollback; map data and error flows.
**Anti-patterns:** Sneaking infra into domain; coupling UI directly to persistence; ignoring failure modes.
**Required artifacts/tests:** ADR/notes; dependency diagram or text; plan for rollback/migrations; integration tests for seams.
**Example tasks:** New API/service integration; refactoring to modules; introducing messaging or caching layers.
