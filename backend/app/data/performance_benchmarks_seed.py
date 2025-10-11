"""Seed data for agent performance benchmarks."""

from __future__ import annotations

SEED_BENCHMARKS = [
    {
        "metric_key": "conversion_rate",
        "asset_type": "office",
        "deal_type": "sell_side",
        "cohort": "industry_avg",
        "value_numeric": 0.32,
        "source": "seed",
        "effective_date": "2024-01-01",
    },
    {
        "metric_key": "conversion_rate",
        "asset_type": "retail",
        "deal_type": "lease",
        "cohort": "industry_avg",
        "value_numeric": 0.28,
        "source": "seed",
        "effective_date": "2024-01-01",
    },
    {
        "metric_key": "avg_cycle_days",
        "asset_type": "office",
        "deal_type": "sell_side",
        "cohort": "industry_avg",
        "value_numeric": 95.0,
        "source": "seed",
        "effective_date": "2024-01-01",
    },
    {
        "metric_key": "avg_cycle_days",
        "asset_type": "retail",
        "deal_type": "lease",
        "cohort": "industry_avg",
        "value_numeric": 60.0,
        "source": "seed",
        "effective_date": "2024-01-01",
    },
    {
        "metric_key": "pipeline_weighted_value",
        "asset_type": None,
        "deal_type": None,
        "cohort": "top_quartile",
        "value_numeric": 1_500_000.0,
        "source": "seed",
        "effective_date": "2024-01-01",
    },
]

__all__ = ["SEED_BENCHMARKS"]
