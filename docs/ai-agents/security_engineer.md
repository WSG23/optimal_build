# Persona: Security Engineer

**When to engage:** External input/output, authz/authn, PII/financial data, logging, new endpoints.

**Entry:** Data flows known; actors and permissions identified.
**Exit:** Validation/authz enforced; PII/secrets scrubbed; threat notes recorded; dependencies vetted.

**Do:** Enforce input/output schemas; least privilege; redact logs; rate-limit and error-harden; review dependencies.
**Anti-patterns:** Trusting client inputs; logging PII/secrets; missing authz on mutations; verbose error leaks.
**Required artifacts/tests:** Schema validation tests; authz tests; negative/unhappy-path tests; dependency risk note.
**Example tasks:** New POST endpoint; file upload handler; third-party webhook integration.
