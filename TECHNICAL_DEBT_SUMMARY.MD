# Outstanding Technical Debt Overview

This summary aggregates the open technical debt recorded in the actual system architecture documentation (`docs/architecture_honest.md`). Items are grouped by severity as described in that source.

## Critical Issues
- _None_ – Market intelligence & agent routers are live, Alembic migrations are versioned, and RequestMetricsMiddleware plus `/metrics` expose throughput/latency/error collectors (see `docs/architecture_honest.md`).

## High Priority
- **Rate limiting unimplemented** – Documented middleware behavior is absent; Redis-backed throttling is still pending.
- **Inconsistent domain naming** – Mixed pluralization and `_api` suffix usage create ambiguity across models and schemas.
- **Fragmented authentication logic** – Auth responsibilities span `users_secure.py`, `users_db.py`, `core/jwt_auth.py`, and `core/auth/policy.py`, increasing maintenance overhead.

## Medium Priority
- **Incomplete MinIO configuration** – The `documents` bucket appears in docs but not in `docker-compose.yml`.
- **Market schema divergence** – Documentation references a `market_transactions` table, while production uses YieldBenchmark, AbsorptionTracking, MarketCycle, and related tables.
- **Compliance model placement** – Compliance data lives inside `singapore_property.py` rather than a dedicated `compliance.py` module as described elsewhere.

## Low Priority
- **Undocumented AI agents** – Ten of the eleven implemented agents are absent from the high-level documentation.

*Source: `docs/architecture_honest.md`, last updated 2025-11-10.*
