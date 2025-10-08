# Regstack Jurisdiction Plug-in Architecture

Regstack provides a jurisdiction-agnostic pipeline for normalising building regulations. This
implementation introduces a plug-in registry, canonical schema, Alembic migrations, and a CLI for
fetching and parsing regulations into PostgreSQL (or SQLite for tests).

## Quickstart

1. **Create a virtual environment** (Python 3.11):
   ```bash
   python3.11 -m venv .venv
   source .venv/bin/activate
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```
2. **Export a database URL** (PostgreSQL recommended, SQLite supported):
   ```bash
   export REGSTACK_DB="postgresql://user:pass@localhost:5432/regstack"
   ```
3. **Run migrations**:
   ```bash
   alembic -c db/alembic.ini upgrade head
   ```
4. **Ingest the Singapore BCA sample**:
   ```bash
   python -m scripts.ingest --jurisdiction sg_bca --since 2025-01-01 --store "$REGSTACK_DB"
   ```

## Repository Layout

```
core/                  # Canonical models, registry, utilities, global taxonomy
jurisdictions/         # Plug-ins (one folder per jurisdiction)
  └── sg_bca/          # Mock Singapore BCA implementation
scripts/               # CLI entry points (ingest)
db/                    # Alembic environment and migrations
docs/architecture.md   # Diagram of the system
```

Key components:
- `core/canonical_models.py` exposes both Pydantic and SQLAlchemy models with shared metadata.
- `core/registry.py` loads jurisdiction plug-ins dynamically via `jurisdictions.<code>.parse`.
- `core/mapping.py` merges the global taxonomy (`core/global_categories.yaml`) with local overrides.
- `scripts/ingest.py` orchestrates fetch, parse, map, and persistence steps.
- `jurisdictions/sg_bca/` contains a self-contained mock parser, fetcher, overrides, and tests.

## Development Workflow

Before committing changes, follow this workflow to ensure clean commits:

```bash
# 1. Make your changes
# ... edit files ...

# 2. Run hooks FIRST (auto-formats files)
make hooks        # Black, Prettier, ruff --fix, etc.

# 3. Stage the formatted files
git add .

# 4. Quick sanity check
make test         # ~10s, verify nothing broke

# 5. Commit
git commit -m "Your feature"
```

**Why this order matters:** `make hooks` modifies files (formatting, fixing imports, adding newlines). Running hooks before `git add` ensures auto-formatting changes are included in the commit, not left as unstaged changes.

For a full verification suite:
```bash
make verify    # formatting, linting, coding rules, and tests
```

## Running the Pipeline

Once dependencies and migrations are installed:

```bash
python -m scripts.ingest --jurisdiction sg_bca --since 2025-01-01 --store "$REGSTACK_DB"
```

The command will fetch mock data, parse it into the canonical schema, apply keyword-based mappings,
and write both the regulation and provenance entries into the configured database.

### Inspecting the Database

Example SQL to verify inserted data:

```sql
SELECT code, name FROM jurisdictions;
SELECT jurisdiction_code, external_id, global_tags FROM regulations;
SELECT regulation_id, source_uri FROM provenance;
```

For quick checks during development you can use SQLite:

```bash
python -m scripts.ingest --jurisdiction sg_bca --since 2025-01-01 --store sqlite:///regstack.db
sqlite3 regstack.db 'SELECT jurisdiction_code, external_id FROM regulations;'
```

## Adding a New Jurisdiction

Follow this five-step checklist:

1. **Create the plug-in folder** under `jurisdictions/<code>/` with `__init__.py`.
2. **Implement `fetch.py`** returning iterable `ProvenanceRecord` objects from `fetch_raw()`.
3. **Implement `parse.py`** exposing `PARSER` that fulfils `JurisdictionParser`, maps raw payloads to
   `CanonicalReg` instances, and returns an override path if needed. Parsers may also set an optional
   `display_name` attribute to control the human-friendly jurisdiction name stored in the registry.
4. **Add `map_overrides.yaml` (optional)** to extend or override global taxonomy keywords.
5. **Write tests** under `jurisdictions/<code>/tests/` to cover parse + persistence, using
   SQLite and the shared ingestion helpers.

After implementing the plug-in, rerun `alembic upgrade head` if migrations changed, and execute the
CLI with the new jurisdiction code.

## Tooling

- `requirements.txt` pin core dependencies (SQLAlchemy 2.x, Pydantic v2, Alembic, PyYAML).
- `pyproject.toml` configures packaging metadata and Ruff linting baseline.
- `Makefile` offers helper targets for migrations and ingestion (`make regstack-ingest`).
- `ruff.toml` defines lint rules aligned with the lightweight scaffold.

## Further Reading

See [`docs/architecture.md`](docs/architecture.md) for the Mermaid system diagram and textual
legend outlining the data flow from fetchers to downstream analytics.
### Bypass dev_mode CORS
