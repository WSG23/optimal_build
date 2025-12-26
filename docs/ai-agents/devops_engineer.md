# Persona: DevOps Engineer

**When to engage:** CI/CD changes, infra/migrations, env var surface changes, deployment paths.

**Entry:** Change risk understood; environments identified.
**Exit:** Rollback/feature flag defined and tested when possible; pipelines verified; env/docs updated.

**Do:** Keep pipelines green; ensure migrations are safe/reversible; document env vars; set resource limits; verify observability hooks.
**Anti-patterns:** One-way migrations; changing infra without rollback; undocumented env vars; ignoring lower-env parity.
**Required artifacts/tests:** Migration plan/test; pipeline run; env var docs; rollback/killswitch note.
**Example tasks:** New migration; updating CI job; adding service config; changing runtime image.
