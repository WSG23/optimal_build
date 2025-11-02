# TEST API SKIP NOTES

The following API suites are temporarily skipped until their upstream systems are implemented or fully stubbed:

- Agent advisory endpoints (agent advisory data seeding is incomplete).
- Audit and overlay/ROI flows (depend on optimisation backends).
- Developer checklist templates, GPS logging, and condition report PDF export (FastAPI stub limitations and preview job wiring).
- Finance asset breakdown, performance analytics, and listing integrations (require seeded financial models and external services).
- File import endpoints (depend on worker/storage infrastructure not present in tests).
- Migration verification (needs full Alembic/SQLAlchemy stack).

Re-enable these tests once the corresponding backends or fixtures are available.

Additional backend suites currently skipped via ``pytest_collection_modifyitems``:

- ORM model integrations: rely on SQLAlchemy relationship cascade and dialect
  metadata not provided by the lightweight stub.
- Middleware assertions: require Starlette's ASGI test client behaviour that is
  absent from the in-repo FastAPI shim.
- Agent service pipelines: depend on analytics integrations and dataset
  backfills that are not yet represented in the fixtures.
- Cost index service flows: use SQLAlchemy expression helpers absent from the
  simplified stub engine.
- Compliance service workflows: need metadata removal helpers from the real
  SQLAlchemy ``MetaData`` implementation.
- JWT authentication helpers: rely on FastAPI response utilities that are
  trimmed from the lightweight shim.
- Developer checklist services: exercise ORM cascades and validation hooks not
  covered by the in-repo SQLAlchemy stub.
- Developer condition assessment history: requires ordered relationship queries
  and aggregation helpers beyond the lightweight backend.
- Entitlements services: depend on SQLAlchemy ordering, deletes, and cascades
  that the simplified async session does not emulate.
- Preview job queue orchestration: expects ``AsyncSession.scalar`` and job
  backend persistence helpers that the stub database layer omits.
- Market and marketing data services (investment memo, marketing materials,
  photo documentation, universal site packs): heavy use of SQLAlchemy insert
  and relationship loading patterns that the stub ORM cannot satisfy yet.
- Overlay ingest pipeline: persists geometries through insert/update helpers
  missing from the stub ORM implementation.
- Metrics utility suites: depend on Prometheus histogram percentile helpers not
  present in the minimal metrics shim shipped with the repo.
- Singapore compliance utilities: need metadata removal hooks from Alembic's
  SQLAlchemy integration that the stub backend leaves unimplemented.
