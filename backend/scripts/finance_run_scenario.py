"""Quick helper to run a finance feasibility scenario and download the export."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import httpx

DEFAULT_PROJECT_ID = 401
DEFAULT_SCENARIO_NAME = "Workspace Quick Run"
DEFAULT_PROJECT_NAME = "Finance Workspace"


def _default_payload(
    project_id: int, scenario_name: str, project_name: str
) -> dict[str, Any]:
    """Return a pre-canned payload similar to the workspace seed."""

    return {
        "project_id": project_id,
        "project_name": project_name,
        "scenario": {
            "name": scenario_name,
            "description": "Automated run from finance_run_scenario.py",
            "currency": "SGD",
            "is_primary": False,
            "cost_escalation": {
                "amount": "1200000",
                "base_period": "2024-Q1",
                "series_name": "construction_all_in",
                "jurisdiction": "SG",
                "provider": "Public",
            },
            "cash_flow": {
                "discount_rate": "0.08",
                "cash_flows": [
                    "-1000",
                    "-500",
                    "1500",
                    "700",
                ],
            },
            "dscr": {
                "net_operating_incomes": ["0", "1200", "-300"],
                "debt_services": ["0", "1000", "800"],
                "period_labels": ["M0", "M1", "M2"],
            },
            "capital_stack": [
                {
                    "name": "Equity",
                    "source_type": "equity",
                    "amount": "400",
                },
                {
                    "name": "Senior Loan",
                    "source_type": "debt",
                    "amount": "800",
                    "rate": "0.065",
                    "tranche_order": 1,
                },
            ],
            "drawdown_schedule": [
                {"period": "M0", "equity_draw": "150", "debt_draw": "0"},
                {"period": "M1", "equity_draw": "250", "debt_draw": "300"},
                {"period": "M2", "equity_draw": "0", "debt_draw": "500"},
            ],
        },
    }


def _load_payload(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:  # pragma: no cover - CLI surface
        raise SystemExit(f"Failed to read payload file: {exc}") from exc
    except json.JSONDecodeError as exc:  # pragma: no cover - CLI surface
        raise SystemExit(f"Payload file is not valid JSON: {exc}") from exc


def run_feasibility(
    *,
    api_base: str,
    payload: dict[str, Any],
    export_path: Path,
    timeout: float,
) -> None:
    export_path.parent.mkdir(parents=True, exist_ok=True)

    with httpx.Client(base_url=api_base, timeout=timeout) as client:
        reviewer_headers = {"X-Role": "reviewer"}
        response = client.post(
            "/api/v1/finance/feasibility", json=payload, headers=reviewer_headers
        )
        if response.status_code != 200:
            detail = response.text
            raise SystemExit(
                "Finance feasibility request failed: "
                f"status={response.status_code} body={detail}"
            )

        body = response.json()
        scenario_id = body.get("scenario_id")
        if not isinstance(scenario_id, int):
            raise SystemExit(
                "Finance feasibility response missing scenario_id; received "
                f"payload: {json.dumps(body, indent=2)}"
            )

        print(f"Created finance scenario {scenario_id}")

        viewer_headers = {"X-Role": "viewer"}
        export = client.get(
            "/api/v1/finance/export",
            params={"scenario_id": scenario_id},
            headers=viewer_headers,
        )
        if export.status_code != 200:
            raise SystemExit(
                "Finance export failed: "
                f"status={export.status_code} body={export.text}"
            )

    export_path.write_bytes(export.content)
    print(f"Saved export CSV to {export_path}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a finance feasibility scenario via the API and download the CSV export.",
    )
    parser.add_argument(
        "--api-base",
        default="http://127.0.0.1:8000",
        help="Base URL for the backend API (default: %(default)s)",
    )
    parser.add_argument(
        "--project-id",
        type=int,
        default=DEFAULT_PROJECT_ID,
        help="Project identifier to attach the scenario to (default: %(default)s)",
    )
    parser.add_argument(
        "--project-name",
        default=DEFAULT_PROJECT_NAME,
        help="Display name for the project (default: %(default)s)",
    )
    parser.add_argument(
        "--scenario-name",
        default=DEFAULT_SCENARIO_NAME,
        help="Name to assign to the scenario (default: %(default)s)",
    )
    parser.add_argument(
        "--payload",
        type=Path,
        help="Optional path to a JSON payload to send instead of the default template.",
    )
    parser.add_argument(
        "--export-path",
        type=Path,
        default=Path("artifacts/finance_export.csv"),
        help="Where to write the export CSV (default: %(default)s)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="HTTP request timeout in seconds (default: %(default)s)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(list(sys.argv[1:] if argv is None else argv))

    if args.payload:
        payload = _load_payload(args.payload)
        payload.setdefault("project_id", args.project_id)
        payload.setdefault("project_name", args.project_name)
        scenario = payload.get("scenario")
        if isinstance(scenario, dict):
            scenario.setdefault("name", args.scenario_name)
    else:
        payload = _default_payload(
            project_id=args.project_id,
            scenario_name=args.scenario_name,
            project_name=args.project_name,
        )

    run_feasibility(
        api_base=args.api_base,
        payload=payload,
        export_path=args.export_path,
        timeout=args.timeout,
    )


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
