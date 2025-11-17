# Codebase Architecture Overview

_Last updated: 2025-10-23_

This document gives a working map of the Optimal Build codebase so that new and existing contributors can reason about behaviour, identify owners, and plan for 10×/100× load scenarios before starting Phase 2D.

## High-Level Package Map

| Package / Path | Primary Responsibility | Owner(s) | Notes |
| --- | --- | --- | --- |
| `backend/app/api` | FastAPI routers and request/response schemas | Platform API | Thin transport layer – pushes work into services/jobs. |
| `backend/app/services` | Domain logic (feasibility, finance, overlays, ingestion, storage, etc.) | Service leads per module | Each subpackage mirrors a user-facing capability; fan-out to jobs and utils. |
| `backend/app/flows` & `backend/app/jobs_registry.py` | Prefect flows / async background orchestration | Data Engineering | Orchestrates long-running tasks (preview renders, imports). |
| `backend/app/models` | SQLAlchemy models + Alembic migrations | Data Platform | Shared declarative base (`BaseModel`) and metadata helpers. |
| `backend/app/utils` | Cross-cutting helpers (metrics, logging, Prometheus stubs, Singapore compliance) | Platform Ops | High change velocity; target for additional tests/metrics coverage. |
| `frontend/` | React/Vite site acquisition + developer workspace | Frontend | Talks to `/api/v1/*` and preview jobs. |
| `docs/` | Product & engineering runbooks | PM/Platform | This document lives here; keep it current. |

See `docs/architecture/dependency-tree.txt` for the full pip dependency tree. For import relationships at the module level, review `docs/architecture/import_graph.dot` or the pre-rendered PNG `docs/architecture/import_graph.png` (generated via NetworkX/Matplotlib). If you prefer Graphviz-rendered SVG, install `dot` locally (e.g. `brew install graphviz`) and run `dot -Tsvg docs/architecture/import_graph.dot -o docs/architecture/import_graph.svg`.

## Import Graph & Ownership

The `pydeps` run (`pydeps backend/app --show-dot --max-bacon 2`) surfaces the hottest cross-package edges:

- `backend/app/api` → `backend/app/services/*`
- `backend/app/services/*` → `backend/app/models`, `backend/app/utils`, `backend/app/jobs_registry`
- `backend/app/services/finance` → `backend/app/utils/metrics`, external `numpy/pandas`
- `backend/app/services/heritage_overlay` → `backend/app/utils/singapore_compliance`
- `backend/app/services/preview_jobs` ↔ `backend/app/jobs_registry`

No circular imports were detected by the run. If new circular references appear, record them here with owners and remediation tasks.

## Known Hot Spots and Owners

| Area | Risk at 10× | Risk at 100× | Owner | Mitigation / Next Steps |
| --- | --- | --- | --- | --- |
| API request throughput | Current rate limiting is 10 rpm (default); at 10× traffic we need asyncio worker tuning and horizontal scaling. | Requires load balancing + autoscaling; document ingress strategy. | Platform API | Benchmark with Locust/ab before Phase 2D; capture metrics in audit doc. |
| Preview rendering queue | Prefect workers use in-memory SQLite; at 10× jobs queue latency spikes. | Needs dedicated task runner + Postgres/Redis backend. | Data Engineering | Migrate Prefect storage to Postgres/Redis once funding allows (recorded in transition checklist). |
| Heritage overlay ingestion | Long-running GeoPandas ops in-process; at 10× polygon count we risk timeouts. | Requires batching + caching, maybe move to async workers. | Compliance/Overlay services | Add spatial indexing + caching; profile with larger sample dataset. |
| Finance calculators | Heavy NumPy/StatsModels usage; CPU-bound. | Needs vectorised caching or async job offload. | Finance services | Extend regression tests & benchmark; consider Numba or job queue. |
| Utils metrics/logging | Sparse coverage; risk of silent failures. | Needs full instrumentation and Prometheus exporter. | Platform Ops | Expand tests (in progress) and introduce structured logging. |

## Developer Onboarding Quick Links

- **Run backend:** `make dev` (loads `.devstack/backend.log` for monitoring)
- **Test suite:** `SECRET_KEY=test JOB_QUEUE_BACKEND=inline .venv/bin/python -m pytest backend/tests`
- **Static checks:** `pre-commit run --all-files`
- **Generate dependency graphs:** see commands at top of this doc.

## Open Actions (tracked in audit)

1. Render `docs/architecture/import_graph.dot` to SVG/PNG once Graphviz is available in CI (ticket for Platform Ops).
2. Expand owners table once Phase 2D team assignments are finalised.
3. Record any new circular dependencies or architectural smells inside the [Unified Execution Backlog](../all_steps_to_product_completion.md#-unified-execution-backlog--deferred-work) (Ready/Blocked section).

Keep this document updated whenever we add new top-level packages or shift responsibilities.
