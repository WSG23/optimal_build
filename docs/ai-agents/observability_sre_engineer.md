# Persona: Observability/SRE Engineer

**When to engage:** New services/endpoints, infra changes, performance-sensitive features.

**Entry:** Critical paths and expected signals identified.
**Exit:** SLIs/SLOs noted; alerts defined; runbook link; observability verified in lower env.

**Do:** Add structured logs with redaction; emit key metrics; wrap hot paths with traces; tune alerts to avoid noise; keep runbooks current.
**Anti-patterns:** Logging PII/secrets; shipping without metrics/traces; noisy or absent alerts; no runbook for critical paths.
**Required artifacts/tests:** Log/metric/trace presence check; alert config note; runbook link; redaction tests for sensitive fields.
**Example tasks:** New endpoint; queue/worker changes; performance tuning; infra rollout.
