# Finance Feasibility API

The finance service exposes endpoints used by the feasibility workflow to
persist model runs and to provide downloadable summaries for finance teams.
Include an `X-Role: reviewer` header when submitting scenarios and an
`X-Role: viewer` header when downloading exports so that the backend can
enforce reviewer-only mutations while allowing read access to viewers.

## Run a finance scenario

`POST /api/v1/finance/feasibility`

Submit a project scenario to calculate escalated construction costs, net present
value (NPV), internal rate of return (IRR), an optional debt-service coverage
ratio (DSCR) timeline, plus the associated capital stack and drawdown schedule.
When the request succeeds the scenario is persisted and a comprehensive summary
is returned for the frontend to render.

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
    },
    "capital_stack": [
      {
        "name": "Sponsor Equity",
        "source_type": "equity",
        "amount": "5000000"
      },
      {
        "name": "Senior Loan",
        "source_type": "debt",
        "amount": "8500000",
        "rate": "0.065",
        "tranche_order": 1
      }
    ],
    "drawdown_schedule": [
      { "period": "2025-Q1", "equity_draw": "2500000", "debt_draw": "0" },
      { "period": "2025-Q2", "equity_draw": "2500000", "debt_draw": "4000000" },
      { "period": "2025-Q3", "equity_draw": "0", "debt_draw": "4500000" }
    ]
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
  ],
  "capital_stack": {
    "currency": "SGD",
    "total": "13450000.00",
    "equity_total": "5000000.00",
    "debt_total": "8450000.00",
    "other_total": "0.00",
    "equity_ratio": "0.3717",
    "debt_ratio": "0.6283",
    "other_ratio": "0.0000",
    "loan_to_cost": "0.6283",
    "weighted_average_debt_rate": "0.0650",
    "slices": [
      {
        "name": "Sponsor Equity",
        "source_type": "equity",
        "category": "equity",
        "amount": "5000000.00",
        "share": "0.3717",
        "rate": null,
        "tranche_order": 0,
        "metadata": {}
      },
      {
        "name": "Senior Loan",
        "source_type": "debt",
        "category": "debt",
        "amount": "8450000.00",
        "share": "0.6283",
        "rate": "0.0650",
        "tranche_order": 1,
        "metadata": {}
      }
    ]
  },
  "drawdown_schedule": {
    "currency": "SGD",
    "entries": [
      {
        "period": "2025-Q1",
        "equity_draw": "2500000.00",
        "debt_draw": "0.00",
        "total_draw": "2500000.00",
        "cumulative_equity": "2500000.00",
        "cumulative_debt": "0.00",
        "outstanding_debt": "0.00"
      },
      {
        "period": "2025-Q2",
        "equity_draw": "2500000.00",
        "debt_draw": "4000000.00",
        "total_draw": "6500000.00",
        "cumulative_equity": "5000000.00",
        "cumulative_debt": "4000000.00",
        "outstanding_debt": "4000000.00"
      }
    ],
    "total_equity": "5000000.00",
    "total_debt": "8450000.00",
    "peak_debt_balance": "8450000.00",
    "final_debt_balance": "8450000.00"
  }
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
