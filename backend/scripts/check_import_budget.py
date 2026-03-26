#!/usr/bin/env python3
"""Enforce clean-process backend startup import budgets."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = REPO_ROOT / "backend"
ROUTE_MODULES = [
    "app.api.v1.agents",
    "app.api.v1.deals",
    "app.api.v1.developers_gps",
    "app.api.v1.export",
    "app.api.v1.imports",
    "app.api.v1.market_intelligence",
]
HEAVY_MAIN_MODULES = [
    "app.core.export",
    "app.models.rkp",
    "app.schemas.buildable",
    "app.schemas.finance",
]
DEFAULT_MAIN_IMPORT_BUDGET_SECONDS = 2.0
DEFAULT_API_ROUTER_BUDGET_SECONDS = 4.0


def _child_environment() -> dict[str, str]:
    env = os.environ.copy()
    pythonpath_entries = [str(REPO_ROOT), str(BACKEND_ROOT)]
    existing_pythonpath = env.get("PYTHONPATH")
    if existing_pythonpath:
        pythonpath_entries.append(existing_pythonpath)
    env["PYTHONPATH"] = os.pathsep.join(pythonpath_entries)
    env.setdefault("SECRET_KEY", "ci-import-budget-secret")
    return env


def _measure_startup() -> dict[str, Any]:
    script = f"""
import importlib
import json
import sys
import time

route_modules = {json.dumps(ROUTE_MODULES)}
heavy_main_modules = {json.dumps(HEAVY_MAIN_MODULES)}

for name in route_modules + heavy_main_modules + ["app.main", "app.api.v1"]:
    sys.modules.pop(name, None)

start = time.perf_counter()
main_module = importlib.import_module("app.main")
main_import_s = time.perf_counter() - start

loaded_after_main = {{
    "routes": [name for name in route_modules if name in sys.modules],
    "heavy_main": [name for name in heavy_main_modules if name in sys.modules],
}}

start = time.perf_counter()
router = main_module.build_api_router()
build_api_router_s = time.perf_counter() - start

print(
    json.dumps(
        {{
            "main_import_s": round(main_import_s, 3),
            "build_api_router_s": round(build_api_router_s, 3),
            "loaded_after_main": loaded_after_main,
            "route_count": len(router.routes),
        }}
    )
)
"""
    completed = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        check=False,
        env=_child_environment(),
        text=True,
    )
    if completed.returncode != 0:
        sys.stderr.write(completed.stdout)
        sys.stderr.write(completed.stderr)
        raise SystemExit(completed.returncode)

    lines = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
    if not lines:
        raise SystemExit("import budget probe returned no output")
    return json.loads(lines[-1])


def main() -> int:
    payload = _measure_startup()
    main_budget = float(
        os.getenv(
            "MAIN_IMPORT_BUDGET_SECONDS",
            str(DEFAULT_MAIN_IMPORT_BUDGET_SECONDS),
        )
    )
    router_budget = float(
        os.getenv(
            "API_ROUTER_BUDGET_SECONDS",
            str(DEFAULT_API_ROUTER_BUDGET_SECONDS),
        )
    )

    failures: list[str] = []
    loaded_after_main = payload.get("loaded_after_main", {})
    if loaded_after_main.get("routes"):
        failures.append(
            f"import app.main eagerly loaded route modules: {loaded_after_main['routes']}"
        )
    if loaded_after_main.get("heavy_main"):
        failures.append(
            "import app.main eagerly loaded heavyweight modules: "
            f"{loaded_after_main['heavy_main']}"
        )

    main_import_s = float(payload["main_import_s"])
    build_api_router_s = float(payload["build_api_router_s"])
    if main_import_s > main_budget:
        failures.append(
            f"main import budget exceeded: {main_import_s:.3f}s > {main_budget:.3f}s"
        )
    if build_api_router_s > router_budget:
        failures.append(
            "API router build budget exceeded: "
            f"{build_api_router_s:.3f}s > {router_budget:.3f}s"
        )

    print(json.dumps(payload, indent=2, sort_keys=True))
    if failures:
        for failure in failures:
            print(f"ERROR: {failure}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
