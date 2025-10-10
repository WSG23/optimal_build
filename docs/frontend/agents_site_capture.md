# Agent GPS Capture & Marketing Pack – Developer Guide

This document explains how the agent capture experience, market intelligence integration, and marketing pack generation are wired together so contributors can extend or debug the feature set safely.

## 1. High-Level Architecture

- **Frontend**
  - `frontend/src/pages/AgentsGpsCapturePage.tsx` renders the capture form, quick analysis cards, amenity summary, and marketing pack controls.
  - Supporting modules:
    - `frontend/src/api/agents.ts` – fetches GPS capture payloads, market intelligence, and marketing pack metadata.
    - `frontend/src/modules/feasibility/FeasibilityWizard.tsx` – consumes the same pack API for the developer workflow.
  - Map rendering uses Mapbox via `mapbox-gl`. A CSS import is dynamically gated to avoid breaking Node-based test runs.
- **Backend APIs**
  - `POST /api/v1/agents/commercial-property/properties/log-gps` – returns address, scenarios, amenities, and quick analysis.
  - `GET /api/v1/agents/commercial-property/properties/{id}/market-intelligence` – supplies transactions, pipeline, and yield benchmarks.
  - `POST /api/v1/agents/commercial-property/properties/{id}/generate-pack/{type}` – produces the professional pack and responds with metadata (download URL, timestamp, size).
- **Storage**
  - Generated packs are stored in the configured object store (S3/MinIO). In staging environments the download URL may be null when public access is disabled.

## 2. Environment Configuration

| Variable | Purpose | Notes |
| --- | --- | --- |
| `VITE_API_BASE_URL` | Base URL for agent APIs | Defaulted to `/` for same-origin deployments; ensure this is set when hosting separately. |
| `VITE_MAPBOX_ACCESS_TOKEN` | Enables interactive map view | Without this token the UI shows fallback text. |
| `MARKETING_PACK_STORAGE_BUCKET` | Backend setting for PDF storage | Required for production environments; staging may reuse the default bucket. |

Ensure any new env vars have entries in `frontend/.env.example`, the deployment manifests, and the contributor docs if they are mandatory.

## 3. Data & Seeding

- Staging coordinates are stored in the `samples/` directory and referenced during walkthroughs (Harbourfront, Telok Ayer, Jurong).
- Market intelligence uses seeded analytics services; when offline it falls back to mock payloads defined in `backend/app/api/v1/agents.py::_build_mock_market_report`.
- Marketing pack generation relies on the PDF templates bundled in the backend service (`app/services/agents/marketing_materials.py`). Update asset paths carefully to avoid breaking S3 uploads.

## 4. Testing Strategy

### Frontend

| Test | Location | Purpose |
| --- | --- | --- |
| `frontend/src/api/__tests__/agents.test.ts` | Verifies API mapping for GPS capture, market intelligence fetch, and marketing pack metadata. |
| `frontend/src/pages/__tests__/AgentsGpsCapturePage.test.tsx` | Exercises the capture UI, map fallback, market intelligence hook, and marketing pack button wiring. |
| `frontend/src/modules/feasibility/__tests__/FeasibilityWizard.test.tsx` | Confirms the developer workflow can generate packs when given a property ID. |

Run with:

```bash
cd frontend
NODE_ENV=test node --test --import tsx --import ./scripts/test-bootstrap.mjs \
  src/api/__tests__/agents.test.ts \
  src/pages/__tests__/AgentsGpsCapturePage.test.tsx \
  src/modules/feasibility/__tests__/FeasibilityWizard.test.tsx
```

### Backend

- Unit and integration coverage for market intelligence live under `tests/services/test_market_intelligence_api_routes.py`.
- Marketing pack endpoints currently rely on service-level tests; when adding new pack types include contract tests that validate payload shape.

## 5. Working Offline

- GPS capture flow requires backend APIs; there is no offline stub. If you need to work without network access, record the JSON response (use `LogTransport` override in tests) and feed it into local fixtures.
- Marketing pack generation can be short-circuited by injecting a test transport:

```ts
import { generateProfessionalPack } from '../api/agents'

await generateProfessionalPack('property-id', 'universal', new AbortController().signal)
// Replace fetch globally in tests to return deterministic payloads.
```

## 6. Updating the UI

When you modify copy, labels, or pack options:

1. Update `frontend/src/i18n/locales/en.json` (and other locales) under `agentsCapture.*` keys.
2. Adjust `PACK_OPTIONS` in both `AgentsGpsCapturePage.tsx` and `FeasibilityWizard.tsx` if new pack types become available.
3. Review CSS additions in `frontend/src/index.css` for `.agents-capture__*` and `.feasibility-pack__*` classes to ensure design consistency.

## 7. Extending Marketing Packs

To add a new pack type or change existing content:

1. Implement the generator on the backend (`InvestmentMemorandumGenerator` / `MarketingMaterialsGenerator` variants).
2. Expose it through `generate_pack` endpoint with appropriate validation.
3. Update frontend `ProfessionalPackType` union and UI labels.
4. Add fixtures to frontend tests covering successful generation and error handling.
5. Update agent and developer documentation to reflect the new option.

## 8. Support & Ownership

| Area | Owner | Contact |
| --- | --- | --- |
| Agent capture UI | Frontend guild | `#frontend` channel |
| Market intelligence analytics | Data insights pod | `#analytics` channel |
| Marketing pack templates | Agent services team | `#agents-pilot` channel |

Use the labels `agent-capture`, `marketing-pack`, and `market-intelligence` when filing tickets so follow-up work is routed correctly.
