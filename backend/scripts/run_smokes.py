"""Orchestrate backend smoke checks for local and CI environments."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, MutableMapping, Optional

import httpx

from ..flows import parse_segment, watch_fetch
from . import seed_finance_demo, seed_nonreg, seed_screening
from . import seed_entitlements_sg


DEFAULT_ARTIFACT_DIR = Path("artifacts")
BACKEND_HOST = "127.0.0.1"
BACKEND_PORT = 8000
ENTITLEMENTS_PROJECT_ID = 90301


class SmokeError(RuntimeError):
    """Raised when a smoke step fails to produce the expected artefacts."""


def _log(message: str) -> None:
    print(f"[smokes] {message}")


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _augment_pythonpath(env: MutableMapping[str, str], backend_dir: Path) -> None:
    current = env.get("PYTHONPATH")
    parts = [part for part in (current.split(os.pathsep) if current else []) if part]
    backend_str = str(backend_dir)
    if backend_str not in parts:
        parts.append(backend_str)
    env["PYTHONPATH"] = os.pathsep.join(parts) if parts else backend_str


def run_alembic_upgrades(backend_dir: Path) -> None:
    _log("Applying database migrations via Alembic")
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=backend_dir,
        check=True,
    )


def run_seeders() -> tuple[Dict[str, Dict[str, int]], seed_finance_demo.FinanceDemoSummary]:
    _log("Seeding screening reference data")
    screening_summary = seed_screening.main([])

    _log("Seeding finance demo data")
    finance_summary = seed_finance_demo.main([])

    _log("Seeding non-regulatory datasets")
    nonreg_summary = seed_nonreg.main([])

    _log("Seeding entitlements reference data")
    entitlements_summary = seed_entitlements_sg.main(
        ["--project-id", str(ENTITLEMENTS_PROJECT_ID), "--reset"]
    )

    summaries: Dict[str, Dict[str, int]] = {
        "screening": screening_summary.as_dict(),
        "finance": finance_summary.as_dict(),
        "non_reg": nonreg_summary.as_dict(),
        "entitlements": {
            **entitlements_summary.as_dict(),
            "project_id": ENTITLEMENTS_PROJECT_ID,
        },
    }
    return summaries, finance_summary


def run_reference_ingestion(storage_path: Path, artifacts_dir: Path) -> Dict[str, Any]:
    storage_path.mkdir(parents=True, exist_ok=True)

    _log("Running offline watch_fetch flow")
    watch_summary = watch_fetch.main(
        [
            "--once",
            "--offline",
            "--storage-path",
            str(storage_path),
            "--summary-path",
            str(artifacts_dir / "watch_fetch_summary.json"),
        ]
    )

    _log("Running parse_segment flow")
    parse_summary = parse_segment.main(
        [
            "--once",
            "--storage-path",
            str(storage_path),
            "--summary-path",
            str(artifacts_dir / "parse_segment_summary.json"),
        ]
    )

    return {
        "watch_fetch": watch_summary,
        "parse_segment": parse_summary,
    }


@contextmanager
def running_backend(backend_dir: Path, host: str, port: int) -> Iterator[str]:
    env = os.environ.copy()
    _augment_pythonpath(env, backend_dir)

    command = [
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        host,
        "--port",
        str(port),
    ]
    _log("Starting backend API server")
    process = subprocess.Popen(command, cwd=backend_dir, env=env)
    base_url = f"http://{host}:{port}"
    try:
        _wait_for_api(base_url)
        yield base_url
    finally:
        _log("Stopping backend API server")
        process.terminate()
        try:
            process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def _wait_for_api(base_url: str, attempts: int = 40, delay: float = 2.0) -> None:
    last_error: Optional[Exception] = None
    for _ in range(attempts):
        try:
            response = httpx.get(f"{base_url}/health", timeout=5.0)
            if response.status_code == 200:
                return
        except Exception as exc:  # pragma: no cover - best effort wait loop
            last_error = exc
        time.sleep(delay)
    raise SmokeError(f"Backend API failed readiness check: {last_error}")


def _retry_request(
    client: httpx.Client,
    method: str,
    url: str,
    *,
    retries: int = 30,
    delay: float = 1.0,
    timeout: float = 30.0,
    **kwargs: Any,
) -> httpx.Response:
    last_error: Optional[Exception] = None
    for _ in range(retries):
        try:
            response = client.request(method, url, timeout=timeout, **kwargs)
            response.raise_for_status()
            return response
        except Exception as exc:  # pragma: no cover - retries for flaky readiness
            last_error = exc
            time.sleep(delay)
    raise SmokeError(f"Request to {url} failed after {retries} attempts") from last_error


def run_buildable_smoke(client: httpx.Client, artifacts_dir: Path) -> Dict[str, Any]:
    _log("Executing buildable screening smoke request")
    payload = {
        "address": "123 Example Ave",
        "typ_floor_to_floor_m": 3.4,
        "efficiency_ratio": 0.8,
    }
    response = _retry_request(client, "POST", "/api/v1/screen/buildable", json=payload)
    data = response.json()

    metrics = data.get("metrics") or {}
    if "zone_code" not in data:
        raise SmokeError("Buildable smoke failed: missing zone_code")
    if "gfa_cap_m2" not in metrics:
        raise SmokeError("Buildable smoke failed: missing metrics.gfa_cap_m2")

    _write_json(artifacts_dir / "buildable_response.json", data)
    return data


def run_finance_smoke(
    client: httpx.Client,
    artifacts_dir: Path,
    finance_summary: seed_finance_demo.FinanceDemoSummary,
) -> Dict[str, Any]:
    _log("Executing finance feasibility smoke request")
    payload = {
        "project_id": finance_summary.project_id,
        "project_name": seed_finance_demo.DEMO_PROJECT_NAME,
        "fin_project_id": finance_summary.fin_project_id,
        "scenario": {
            "name": "Scenario A – Base Case",
            "description": "Baseline absorption with phased sales releases.",
            "currency": seed_finance_demo.DEMO_CURRENCY,
            "is_primary": True,
            "cost_escalation": {
                "amount": "38950000",
                "base_period": "2024-Q1",
                "series_name": "construction_all_in",
                "jurisdiction": "SG",
                "provider": "Public",
            },
            "cash_flow": {
                "discount_rate": "0.08",
                "cash_flows": [
                    "-2500000",
                    "-4100000",
                    "-4650000",
                    "-200000",
                    "4250000",
                    "10200000",
                ],
            },
            "dscr": {
                "net_operating_incomes": [
                    "0",
                    "0",
                    "3800000",
                    "5600000",
                    "7200000",
                    "7800000",
                ],
                "debt_services": [
                    "0",
                    "0",
                    "3200000",
                    "3300000",
                    "3400000",
                    "3400000",
                ],
                "period_labels": ["M1", "M2", "M3", "M4", "M5", "M6"],
            },
        },
    }
    response = _retry_request(client, "POST", "/api/v1/finance/feasibility", json=payload)
    data = response.json()

    if "scenario_id" not in data:
        raise SmokeError("Finance smoke failed: missing scenario_id")

    _write_json(artifacts_dir / "finance_feasibility_response.json", data)

    export_response = _retry_request(
        client,
        "GET",
        "/api/v1/finance/export",
        params={"scenario_id": data["scenario_id"]},
    )
    export_path = artifacts_dir / "finance_export.csv"
    export_path.write_text(export_response.text, encoding="utf-8")
    return data


def run_entitlements_smoke(client: httpx.Client, artifacts_dir: Path) -> Dict[str, Any]:
    _log("Executing entitlements roadmap smoke request")
    response = _retry_request(
        client,
        "GET",
        f"/api/v1/entitlements/{ENTITLEMENTS_PROJECT_ID}/roadmap",
        params={"limit": 5},
    )
    data = response.json()
    items = data.get("items") or []
    if not items:
        raise SmokeError("Entitlements smoke failed: empty roadmap response")

    _write_json(artifacts_dir / "entitlements_roadmap.json", data)
    return data


def fetch_openapi_schema(client: httpx.Client, artifacts_dir: Path) -> Dict[str, Any]:
    _log("Fetching OpenAPI schema")
    response = _retry_request(client, "GET", "/openapi.json")
    payload = response.json()
    _write_json(artifacts_dir / "openapi.json", payload)
    return payload


def orchestrate_smokes(artifacts_dir: Path) -> Dict[str, Any]:
    backend_dir = Path(__file__).resolve().parents[1]
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    run_alembic_upgrades(backend_dir)
    seed_summaries, finance_summary = run_seeders()
    _write_json(artifacts_dir / "seed_summary.json", seed_summaries)

    ingestion = run_reference_ingestion(artifacts_dir / "reference_storage", artifacts_dir)

    with running_backend(backend_dir, BACKEND_HOST, BACKEND_PORT) as base_url:
        with httpx.Client(base_url=base_url, timeout=30.0) as client:
            buildable = run_buildable_smoke(client, artifacts_dir)
            finance = run_finance_smoke(client, artifacts_dir, finance_summary)
            entitlements = run_entitlements_smoke(client, artifacts_dir)
            openapi = fetch_openapi_schema(client, artifacts_dir)

    summary = {
        "seeders": seed_summaries,
        "ingestion": ingestion,
        "buildable": buildable,
        "finance": finance,
        "entitlements": entitlements,
        "openapi": {"version": openapi.get("info", {}).get("version")},
    }
    _write_json(artifacts_dir / "smokes_summary.json", summary)
    return summary


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run backend smoke checks and persist artefacts for inspection.",
    )
    parser.add_argument(
        "--artifacts",
        type=Path,
        default=DEFAULT_ARTIFACT_DIR,
        help="Directory where smoke artefacts should be written.",
    )
    return parser


def main(argv: Optional[Iterable[str]] = None) -> Dict[str, Any]:
    parser = build_argument_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    return orchestrate_smokes(args.artifacts.resolve())


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
