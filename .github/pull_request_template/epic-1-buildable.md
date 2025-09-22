# Epic 1: Parcel/Zoning Data → Buildable (HARDEN)

## Summary
Harden “address → parcel/zoning → rules → buildable” so `/api/v1/screen/buildable` yields deterministic, provenance-rich results for SG.

## Changes
- [ ] Extend zoning seed with overlays: airport, coastal, daylight, heritage
- [ ] Add provenance block in buildable response (rule id, clause_ref, document_id, zone_source)
- [ ] Golden tests for 3 seeded addresses (GFA cap, floors, footprint, NSA)
- [ ] PostGIS path for polygon buffer (fallback: GeoJSON approximate)
- [ ] Configurable assumptions in API (typ_floor_to_floor_m, efficiency_ratio); sensible defaults
- [ ] README “Buildable flow” section

## API Surface
- POST /api/v1/screen/buildable (adds `rules[*].provenance`, `zone_source`)

## Verification
```bash
make dev-start
make db.upgrade
make seed-data
pytest tests/pwp/test_buildable_golden.py -q
curl -sX POST :8000/api/v1/screen/buildable -H content-type:application/json \
  -d '{"address":"<seeded>","typFloorToFloorM":3.4,"efficiencyRatio":0.8}' | jq
Acceptance
Correct caps + provenance in response

P90 < 2s cached; goldens pass

Risks/Mitigations
Data licensing → keep dev seeds; support user GeoJSON

No PostGIS → feature-flag precise/approx path

bash
Copy code

**Path:** `.github/pull_request_template/epic-2-rules-ingestion.md`
```markdown
# Epic 2: Singapore Rules Ingestion (RKP v1)

## Summary
Automate URA/BCA/SCDF/PUB ingestion → clauses → normalized rules. Approvals power buildable with approved values.

## Changes
- [ ] Seed ref_sources (URA/BCA/SCDF/PUB) with landing URLs
- [ ] Prefect flow: watch_fetch (ETag/Last-Modified → S3/MinIO → ref_documents, suspected_update)
- [ ] Prefect flow: parse_segment (PDF/HTML → ref_clauses with clause_ref, heading, text_span, pages)
- [ ] Normalizers: zoning.max_far, zoning.max_building_height_m, zoning.site_coverage.max_percent, zoning.setback.front_min_m
- [ ] Review UI: Approve/Reject + Publish
- [ ] Rules API: serve only approved; include provenance
- [ ] Buildable prefers approved rules; falls back to zoning attributes if missing

## API Surface
- GET /api/v1/review/sources|documents|clauses|queue
- POST /api/v1/rules/{id}/review
- GET /api/v1/rules?jurisdiction=SG&parameter_key=…

## Verification
```bash
make dev-start && make db.upgrade && make seed-data
python -m backend.flows.watch_fetch --once
python -m backend.flows.parse_segment --once
# approve in ui-admin
curl ':8000/api/v1/rules?jurisdiction=SG&parameter_key=zoning.max_far' | jq
pytest tests/rkp/test_rules_ingestion.py -q
Acceptance
≥1 URA doc → 20+ clauses → 4 normalized rules approved

Buildable cites approved rules (not seeds)

Risks/Mitigations
PDF/HTML variance → dual parser (PyMuPDF/pdfminer + Readability)

Clause ambiguity → human review required

bash
Copy code

**Path:** `.github/pull_request_template/epic-3-feasibility-wizard.md`
```markdown
# Epic 3: Feasibility Wizard → Live Backend

## Summary
Replace client-side mocks; wizard consumes buildable + citations; assumptions are tunable.

## Changes
- [ ] Wire SPA to /api/v1/screen/buildable
- [ ] Render zone_code, overlays, citations (clause_ref, authority), computed caps
- [ ] Assumptions panel (typFloorToFloorM, efficiencyRatio) with debounce
- [ ] Error/empty states
- [ ] Playwright E2E for 3 seeded addresses

## Verification
```bash
make dev-start
pnpm -C frontend dev
pnpm -C frontend test:e2e
Acceptance
UI matches backend JSON

Recompute < 500ms client / < 2s server

E2E green in CI

Risks/Mitigations
Network variance → optimistic UI + loaders

Contract drift → TS types pinned to OpenAPI

bash
Copy code

**Path:** `.github/pull_request_template/epic-4-nonreg-datasets.md`
```markdown
# Epic 4: Fold Back Non-Regulatory Datasets (Ergo, Products, Standards, Costs)

## Summary
Add modular reference knowledge that augments feasibility without blocking core regulatory flow.

## Changes
- [ ] Ergonomics seed: turning_radius_mm_min, reach_forward_mm, counter.height_mm_range, accessibility.ramp.max_slope_ratio
- [ ] Products adapter: 1 vendor (IKEA/Toto) → ref_products (W/D/H, BIM/spec URI); nightly cron stub
- [ ] Standards seed: wall.partition.thickness_mm_min, structure.live_load.kN_m2_min with license/provenance
- [ ] Costs: 1 SG public index → /api/v1/costs/indices/latest; pro-forma scalar in PWP
- [ ] Wizard advisories (non-blocking)

## Verification
```bash
make dev-start && make db.upgrade
python -m backend.flows.sync_products --once
curl :8000/api/v1/ergonomics | jq
curl :8000/api/v1/products | jq
curl :8000/api/v1/standards | jq
curl :8000/api/v1/costs/indices/latest | jq
Acceptance
Endpoints return seeded data + provenance

Products ≥20 items; deprecations timestamped

Wizard shows advisories when relevant

Risks/Mitigations
Licensing → license_ref; restrict redistribution

Vendor drift → schema validators + adapter tests

pgsql
Copy code

**Path:** `.github/pull_request_template/epic-5-observability.md`
```markdown
# Epic 5: Observability & Governance

## Summary
Operational visibility for ingestion and buildable; enforce lineage and auditable decisions.

## Changes
- [ ] Prometheus counters: rkp_fetch_total, rkp_parse_total, rkp_normalize_total, rkp_review_approved_total, pwp_buildable_total, pwp_buildable_errors_total
- [ ] Alert on ref_documents.suspected_update=true
- [ ] Buildable audit snapshot (inputs, outputs, rule versions, durations) → AuditLog
- [ ] Grafana dashboard JSON (ingestion & screening)
- [ ] Runbook for failures & rollbacks

## Verification
```bash
make dev-start
curl :8000/health/metrics
python -m backend.flows.watch_fetch --simulate-change
pytest tests/observability/test_audit_snapshot.py -q
Acceptance
7-day dashboard visible

Simulated update triggers alert

Each buildable call writes audit entry

Risks/Mitigations
Alert noise → thresholds & dedup

PII → ensure no user PII in audit

bash
Copy code

**Path:** `.github/pull_request_template/epic-6-security.md`
```markdown
# Epic 6: Minimal Security Hardening (v1)

## Summary
Protect /api/v1/* with lightweight auth and role gates for reviewer actions; add rate limiting.

## Changes
- [ ] Header token or OAuth2 bearer; /health open
- [ ] RBAC roles: viewer, reviewer, admin; enforce on review/publish
- [ ] Rate limit public endpoints (IP-based)
- [ ] Tests for 401/403/429
- [ ] Docs: tokens/issuer; dev bypass flag

## Verification
```bash
pytest tests/security/test_auth_rbac_rate.py -q
curl -H "authorization: Bearer $API_TOKEN" :8000/api/v1/rules | jq
Acceptance
Unauth /api/v1/* → 401

Reviewer can approve; viewer cannot

Rate limit returns 429 under load

Risks/Mitigations
Dev friction → feature flag to disable locally

Token handling → read from env; never log tokens

css
Copy code

**Path:** `.github/pull_request_template/epic-7-ci-smokes.md`
```markdown
# Epic 7: CI/CD Polish & Smokes

## Summary
CI reliably catches regressions in buildable, ingestion, and frontend integration; speed via caches.

## Changes
- [ ] CI: spin Postgres/Redis/MinIO; alembic upgrade; make seed-data
- [ ] Backend smoke: curl /api/v1/screen/buildable for 1 seeded address; assert JSON shape
- [ ] RKP smoke: run watch_fetch + parse_segment once; assert rows
- [ ] Frontend E2E: Playwright against seeds; assert citations render
- [ ] Cache pip/node deps + Playwright browsers
- [ ] Publish artifacts (OpenAPI, screenshots)

## Verification
- Open draft PR; ensure all smokes pass
- Force failing seed; CI blocks merge

## Acceptance
- PR fails if smokes fail
- CI < 10 min; artifacts available

## Risks/Mitigations
- Flaky E2E → retries + artifact uploads
- Slow CI → parallelize jobs; cache aggressively
B) Code-quality & tooling configs
Path: pyproject.toml

toml
Copy code
[tool.black]
line-length = 88
target-version = ["py311"]
include = "\\.pyi?$"
exclude = """
/(
  \.git
 | \.venv
 | build
 | dist
)/
"""

[tool.isort]
profile = "black"
line_length = 88
combine_as_imports = true

[tool.ruff]
line-length = 88
target-version = "py311"
select = ["E","F","I","UP","B","S","N","T20"]
ignore = ["E501"]  # handled by black
src = ["backend","app","flows","jobs","scripts"]
exclude = [".venv",".git","build","dist","frontend","ui-admin"]

[tool.mypy]
python_version = "3.11"
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
ignore_missing_imports = true
no_implicit_optional = true
strict_optional = true
exclude = "frontend|ui-admin|tests"
Path: .pre-commit-config.yaml

yaml
Copy code
repos:
- repo: https://github.com/psf/black
  rev: 24.8.0
  hooks: [{id: black}]
- repo: https://github.com/pycqa/isort
  rev: 5.13.2
  hooks: [{id: isort}]
- repo: https://github.com/astral-sh/ruff-pre-commit
  rev: v0.6.9
  hooks: [{id: ruff}]
- repo: https://github.com/pre-commit/pre-commit-hooks
  rev: v4.6.0
  hooks:
    - id: check-merge-conflict
    - id: end-of-file-fixer
    - id: trailing-whitespace
- repo: https://github.com/pre-commit/mirrors-prettier
  rev: v3.3.3
  hooks:
    - id: prettier
      additional_dependencies: ["prettier@3.3.3"]
      files: "\\.(ts|tsx|js|jsx|json|md|yaml|yml)$"
Path: .editorconfig

ini
Copy code
root = true

[*]
end_of_line = lf
insert_final_newline = true
charset = utf-8
indent_style = space
indent_size = 2
trim_trailing_whitespace = true

[*.py]
indent_size = 4

[Makefile]
indent_style = tab
C) CI workflow add-on (merge into .github/workflows/ci.yml)
yaml
Copy code
jobs:
  backend:
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - name: Install deps
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pre-commit
      - name: Pre-commit (black, isort, ruff)
        run: pre-commit run --all-files
      - name: Start services
        run: docker compose -f docker-compose.yml up -d postgres redis minio
      - name: DB migrate & seed
        run: |
          make db.upgrade
          make seed-data
      - name: Backend tests
        run: pytest -q
      - name: Buildable smoke
        run: |
          python -m backend.app.main & sleep 3
          curl -sX POST http://localhost:8000/api/v1/screen/buildable \
            -H 'content-type: application/json' \
            -d '{"address":"<seeded>","typFloorToFloorM":3.4,"efficiencyRatio":0.8}' | jq .

  frontend:
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '18' }
      - name: Install & build
        run: |
          pnpm -C frontend install
          pnpm -C frontend build
      - name: E2E
        run: pnpm -C frontend test:e2e
2) Codex multi-PR plan prompt (copy/paste)
Use this to have Codex create branches, module scaffolding, tests, and wire everything to the configs above. It’s modular (backend/app/flows/jobs/scripts) and follows Black 88, isort black, Ruff, mypy, and pre-commit.

sql
Copy code
You are a senior staff engineer. Operate on $REPO. Create 7 feature branches and PRs with the files and tests described below. Enforce best practices: Black line-length 88, isort profile=black, Ruff, mypy strict, pre-commit hooks, modular Python packages. Use our existing layout (backend/, app/, flows/, jobs/, scripts/). For any code you add, include unit tests and, where applicable, integration tests. Do not add inline comments in code or bash.

## Global tasks (root commit on each branch)
- Add pyproject.toml, .pre-commit-config.yaml, .editorconfig as provided.
- Update .github/workflows/ci.yml to add pre-commit and smokes.
- Add PR templates under .github/pull_request_template/ for the specific epic.

## Branch plan
1) feature/epic-1-buildable
   - Extend zoning seeds with overlays (airport, coastal, daylight, heritage).
   - Add provenance block in buildable responses.
   - Implement PostGIS optional path (polygon buffer) with GeoJSON fallback.
   - Add golden tests tests/pwp/test_buildable_golden.py.
   - Update README with “Buildable flow”.
   - Open PR using template epic-1-buildable.md.

2) feature/epic-2-rules-ingestion
   - Seed ref_sources (URA/BCA/SCDF/PUB).
   - Add flows: flows/watch_fetch.py, flows/parse_segment.py (Prefect).
   - Normalizers in backend/services/rules/normalizers_sg.py for 4 zoning params.
   - Wire Admin Approve/Reject/Publish in ui-admin and backend routes.
   - tests/rkp/test_rules_ingestion.py with fixtures for sample docs.
   - Open PR using epic-2-rules-ingestion.md.

3) feature/epic-3-feasibility-wizard
   - Frontend: wire to /api/v1/screen/buildable; assumptions panel; error states.
   - Add Playwright E2E for 3 seeded addresses.
   - Open PR using epic-3-feasibility-wizard.md.

4) feature/epic-4-nonreg-datasets
   - Seed ergonomics; add products adapter (1 vendor); seed standards; add costs index + pro-forma hook.
   - Routes: /api/v1/ergonomics, /api/v1/products, /api/v1/standards, /api/v1/costs/indices/latest.
   - tests/reference/test_ergonomics_products_standards_costs.py.
   - Open PR using epic-4-nonreg-datasets.md.

5) feature/epic-5-observability
   - Add Prometheus counters for ingestion & buildable; alert on suspected_update; audit snapshot on screening.
   - Grafana dashboard JSON in docs/observability/grafana.json.
   - tests/observability/test_audit_snapshot.py.
   - Open PR using epic-5-observability.md.

6) feature/epic-6-security
   - Add bearer-token auth; simple RBAC (viewer/reviewer/admin); rate limiting.
   - tests/security/test_auth_rbac_rate.py.
   - Open PR using epic-6-security.md.

7) feature/epic-7-ci-smokes
   - CI seeds DB; backend smoke curl; RKP flow smoke; frontend E2E; caching.
   - Update ci.yml accordingly.
   - Open PR using epic-7-ci-smokes.md.

## Output format (for each branch)
1) Plan
2) Unified diffs
3) New files (full contents)
4) Verification (commands + expected JSON snippets)
5) Assumptions & follow-ups

Proceed with feature/epic-1-buildable first; then produce remaining branches sequentially in the same reply.