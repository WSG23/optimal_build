# Outstanding Technical Debt Overview

This summary aggregates the open technical debt recorded in the actual system architecture documentation (`docs/architecture_honest.md`). Items are grouped by severity as described in that source.

## Critical Issues
- **Disabled APIs** – `market_intelligence.py` and `agents.py` routers remain commented out while model dependencies are repaired. [Ref: backend/app/api/v1/__init__.py lines 69-70 in documentation.]
- **Database migrations uninitialized** – Alembic 1.13.0 is installed but no `versions/` directory exists, so schema changes rely on manual operations.
- **Metrics instrumentation missing** – `prometheus-client` is present without any collectors for latency, errors, or throughput.

## High Priority
- **Rate limiting unimplemented** – Documented middleware behavior is absent; Redis-backed throttling is still pending.
- **Inconsistent domain naming** – Mixed pluralization and `_api` suffix usage create ambiguity across models and schemas.
- **Fragmented authentication logic** – Auth responsibilities span `users_secure.py`, `users_db.py`, `core/jwt_auth.py`, and `core/auth/policy.py`, increasing maintenance overhead.

## Medium Priority
- **Incomplete MinIO configuration** – The `documents` bucket appears in docs but not in `docker-compose.yml`.
- **Market schema divergence** – Documentation references a `market_transactions` table, while production uses YieldBenchmark, AbsorptionTracking, MarketCycle, and related tables.
- **Compliance model placement** – Compliance data lives inside `singapore_property.py` rather than a dedicated `compliance.py` module as described elsewhere.

## Low Priority
- **Directory naming mismatch** – The admin frontend lives in `ui-admin/` instead of the documented `admin/` path.
- **Script relocation** – The expected `backend/scripts/ingest.py` actually sits in `/scripts/ingest.py`.
- **Undocumented AI agents** – Ten of the eleven implemented agents are absent from the high-level documentation.

*Source: `docs/architecture_honest.md`, last updated 2025-10-04.*
