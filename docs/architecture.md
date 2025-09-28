# Regstack Architecture

```mermaid
flowchart TD
  UI[UI / API\n(queries, checks, diffs)]
  CORE[Jurisdiction-agnostic Core]
  CANON[Canonical Schema\n(Pydantic/SQLAlchemy)]
  PARSERS[Parser Adapters\n(one per jurisdiction)]
  FETCH[Source Fetchers\n(HTTP / PDF / XML)]
  MAP[Mapping Layer\n(global tags, conflicts)]
  VER[Versioning & Provenance\n(ledger)]
  AI[Compliance/AI Reasoners]
  ANA[Analytics\n(diffs, overlap)]

  UI --> CORE
  CORE --> CANON
  CORE --> PARSERS --> FETCH
  CORE --> MAP
  CORE --> VER
  CORE --> AI
  CORE --> ANA
```

**Legend:**
- **UI / API** — external entry points for regulation queries and comparisons.
- **Core** — orchestration logic, registry, CLI.
- **Canonical Schema** — SQLAlchemy + Pydantic models persisted via Alembic.
- **Parser Adapters** — jurisdiction plug-ins handling fetch + parse.
- **Source Fetchers** — HTTP/XML/PDF collectors per jurisdiction.
- **Mapping Layer** — applies global taxonomy with local overrides.
- **Versioning & Provenance** — ledger of fetch timestamps and raw payloads.
- **Compliance/AI Reasoners** — downstream analytics consumers.
- **Analytics** — reporting and cross-jurisdiction insights.

```
UI/API → Core (jurisdiction-agnostic)
       ├─ Canonical Schema (Pydantic/SQLAlchemy)
       ├─ Parser Adapters (per jurisdiction) → Source Fetchers (http/pdf/xml)
       ├─ Mapping Layer (global tags/conflicts)
       ├─ Versioning & Provenance (ledger)
       ├─ Compliance/AI reasoners
       └─ Analytics (diffs/overlap)
```

## Reference deployment footprint

The current reference deployment bundles a fairly heavy backing stack:

- **PostgreSQL** stores the regulation corpus and feeds downstream analytics.
- **Neo4j** powers the graph-relations service that materialises regulation
  relationships for the UI and automated checks.
- **Kafka** acts as the event backbone that streams regulation changes to graph
  processors and other consumers.
- **Graph-relations service** depends on both Kafka and Neo4j to build the
  real-time relationship views exposed to clients.

Teams evaluating the platform should plan for this footprint, especially if
they do not already operate managed graph or streaming infrastructure.
