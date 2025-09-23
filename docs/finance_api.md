# Finance Feasibility API

The finance service exposes endpoints used by the feasibility workflow to
persist model runs and to provide downloadable summaries for finance teams.
Requests are authenticated with the same mechanisms as the rest of the
`/api/v1` namespace.

## Run a finance scenario

`POST /api/v1/finance/feasibility`

Submit a project scenario to calculate escalated construction costs, net present
value (NPV), internal rate of return (IRR), and optionally a debt-service
coverage ratio (DSCR) timeline. When the request succeeds the scenario is
persisted and a summary of the results is returned.

### Request body

```jsonc
{
  "project_id": 101,
  "project_name": "Emerald Logistics Hub",
  "fin_project_id": null,
  "scenario": {
    "name": "Base Case",
    "description": "Primary development case for investor deck",
    "currency": "SGD",
    "is_primary": true,
    "cost_escalation": {
      "amount": "12500000",
      "base_period": "2023-Q4",
      "series_name": "construction_cost_index",
      "jurisdiction": "SG",
      "provider": "BCA"
    },
    "cash_flow": {
      "discount_rate": "0.085",
      "cash_flows": ["-12500000", "3200000", "4300000", "5100000"]
    },
    "dscr": {
      "net_operating_incomes": ["2200000", "2400000", "2600000"],
      "debt_services": ["1800000", "1800000", "1800000"],
      "period_labels": ["2025", "2026", "2027"]
    }
  }
}
```

### Response body

```jsonc
{
  "scenario_id": 42,
  "project_id": 101,
  "fin_project_id": 12,
  "scenario_name": "Base Case",
  "currency": "SGD",
  "escalated_cost": "13450000.00",
  "cost_index": {
    "series_name": "construction_cost_index",
    "jurisdiction": "SG",
    "provider": "BCA",
    "base_period": "2023-Q4",
    "latest_period": "2024-Q2",
    "scalar": "1.0760",
    "base_index": {
      "period": "2023-Q4",
      "value": "115.1",
      "unit": "index",
      "source": "Construction Economics Digest"
    },
    "latest_index": {
      "period": "2024-Q2",
      "value": "123.8",
      "unit": "index",
      "provider": "BCA"
    }
  },
  "results": [
    {
      "name": "escalated_cost",
      "value": "13450000.00",
      "unit": "SGD",
      "metadata": {
        "base_amount": "12500000",
        "base_period": "2023-Q4",
        "cost_index": {"scalar": "1.0760"}
      }
    },
    {
      "name": "npv",
      "value": "2419234.17",
      "unit": "SGD",
      "metadata": {
        "discount_rate": "0.085",
        "cash_flows": ["-12500000", "3200000", "4300000", "5100000"]
      }
    },
    {
      "name": "irr",
      "value": "0.1125",
      "unit": "ratio",
      "metadata": {
        "cash_flows": ["-12500000", "3200000", "4300000", "5100000"]
      }
    },
    {
      "name": "dscr_timeline",
      "metadata": {
        "entries": [
          {
            "period": "2025",
            "noi": "2200000",
            "debt_service": "1800000",
            "dscr": "1.2222",
            "currency": "SGD"
          }
        ]
      }
    }
  ],
  "dscr_timeline": [
    {
      "period": "2025",
      "noi": "2200000",
      "debt_service": "1800000",
      "dscr": "1.2222",
      "currency": "SGD"
    }
  ]
}
```

## Export a finance scenario

`GET /api/v1/finance/export?scenario_id={id}`

Streams a CSV attachment that mirrors the persisted scenario. The CSV includes
all headline metrics and, when available, the DSCR timeline with one row per
period.

### Response headers

- `Content-Disposition` – contains the suggested filename for the download.
- `Content-Type` – set to `text/csv`.

### CSV structure

The export begins with metric name/value/unit rows and, when present, DSCR and
cost index provenance sections. Consumers can ingest the file directly in Excel
or Google Sheets for reporting workflows.
