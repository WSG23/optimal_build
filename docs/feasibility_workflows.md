# Feasibility Wizard Backend Contract

The Feasibility Wizard calls `POST /api/v1/screen/buildable` to resolve a
seeded address to its zoning overlays, calculate gross floor area caps, and
surface the rules that justify the result. The endpoint is idempotent — the
frontend resubmits the full payload whenever assumptions change so the backend
remains stateless and easy to debug.

## Request payload

```json
{
  "address": "123 Example Ave",
  "typ_floor_to_floor_m": 3.4,
  "efficiency_ratio": 0.8
}
```

* `address` – Textual address that maps to a seeded parcel via
  `ref_geocode_cache`.
* `typ_floor_to_floor_m` – Optional override for typical floor-to-floor height
  in metres. Defaults to `settings.BUILDABLE_TYP_FLOOR_TO_FLOOR_M` when omitted.
* `efficiency_ratio` – Optional net-to-gross efficiency multiplier. Defaults to
  `settings.BUILDABLE_EFFICIENCY_RATIO` and is clamped between 0 and 1.

The backend automatically normalises whitespace on the address, enforces the
parameter ranges and requires either an address or a geometry payload (the SPA
uses addresses exclusively).

## Response shape

```json
{
  "input_kind": "address",
  "zone_code": "R2",
  "overlays": ["heritage", "daylight"],
  "metrics": {
    "gfa_cap_m2": 4375,
    "floors_max": 8,
    "footprint_m2": 563,
    "nsa_est_m2": 3588
  },
  "zone_source": {
    "kind": "parcel",
    "layer_name": "MasterPlan",
    "parcel_ref": "MK01-01234",
    "parcel_source": "sample_loader"
  },
  "rules": [
    {
      "id": 10,
      "authority": "URA",
      "parameter_key": "zoning.max_far",
      "operator": "<=",
      "value": "3.5",
      "unit": null,
      "provenance": {
        "rule_id": 10,
        "clause_ref": "4.2.1",
        "document_id": 345,
        "pages": [7],
        "seed_tag": "zoning"
      }
    }
  ]
}
```

Important fields surfaced in the wizard:

* `zone_code` and `overlays` power the zone banner.
* `metrics` contains the gross floor area cap, footprint, maximum floors and
  net saleable estimate in square metres.
* Every rule entry now includes `authority` and a provenance object with
  `document_id` and `pages` when available so the frontend can display proper
  citations.

If the address cannot be resolved to a seeded parcel, `zone_code` is `null`, the
metric values fall back to zero and `rules` is empty. The SPA treats this as an
"empty" state while still rendering the zoning overlays (if any) returned from
reference layers.

## Provenance guarantees

Each rule in the response contains a `provenance` object with:

* `rule_id` – Primary key of the published rule.
* `clause_ref` – Clause identifier when present in the source document.
* `document_id` – Identifier of the originating reference document.
* `pages` – List of page numbers derived from the source provenance metadata.
* `seed_tag` – Optional tag describing the ingestion seed that produced the rule.

The backend contract test (`backend/tests/pwp/test_buildable_golden.py`) asserts
that provenance data is always present for seeded parcels.
