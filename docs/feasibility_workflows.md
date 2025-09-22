# Feasibility Workflows

The feasibility wizard calls two backend endpoints to guide users from project
setup through buildability assessment. The workflow is intentionally
stateless—the frontend sends the full project payload for each step so that the
API remains idempotent and easy to replay during reviews or automated testing.

## 1. Fetch recommended rules

`POST /api/v1/feasibility/rules`

**Request body**

```json
{
  "name": "Harbour View Residences",
  "siteAddress": "12 Marina Way",
  "siteAreaSqm": 5000,
  "landUse": "residential",
  "targetGrossFloorAreaSqm": 14000,
  "buildingHeightMeters": 45
}
```

**Response shape**

- `projectId` — deterministic identifier derived from the project name.
- `rules[]` — ordered list of rules that the wizard can display.
- `recommendedRuleIds[]` — subset of rule identifiers to select by default.
- `summary` — high-level narrative describing why the rules were recommended.

Each rule includes the source authority, parameter key, requirement, severity,
and whether it should be selected by default. The frontend persists the payload
so that re-running the step is instantaneous.

## 2. Submit assessment

`POST /api/v1/feasibility/assessment`

**Request body**

```json
{
  "project": { /* same shape as above */ },
  "selectedRuleIds": ["ura-plot-ratio", "bca-site-coverage", "scdf-access"]
}
```

**Response shape**

- `summary` — buildable area metrics and human-readable remarks.
- `rules[]` — each selected rule enriched with status, actual value (if
  available) and advisory notes.
- `recommendations[]` — follow-up actions triggered by failed or warning rules.

If any unknown rule identifiers are supplied, the endpoint returns `400` with a
clear error message so the UI can highlight the offending selection.

## Testing

API regression tests live in `backend/tests/test_api/test_feasibility.py`. They
cover the happy path and the error response for unknown rule identifiers so the
contract stays stable as the heuristics evolve.
