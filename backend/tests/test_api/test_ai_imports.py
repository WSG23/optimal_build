"""Tests ensuring the AI router does not eagerly load heavyweight services."""

from __future__ import annotations

import importlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

pytestmark = [pytest.mark.no_db]


def _service_modules() -> list[str]:
    return [
        "app.services.ai.natural_language_query",
        "app.services.ai.rag_knowledge_base",
        "app.services.ai.report_generator",
        "app.services.ai.document_extractor",
        "app.services.ai.conversational_assistant",
        "app.services.ai.scenario_optimizer",
        "app.services.ai.communication_drafter",
        "app.services.ai.portfolio_optimizer",
        "app.services.ai.multi_modal_analyzer",
        "app.services.ai.competitive_intelligence",
    ]


def _pythonpath() -> str:
    repo_root = Path(__file__).resolve().parents[3]
    entries = [str(repo_root), str(repo_root / "backend")]
    existing = os.environ.get("PYTHONPATH")
    if existing:
        entries.append(existing)
    return os.pathsep.join(entries)


def test_ai_router_import_does_not_eagerly_load_ai_services() -> None:
    """Importing the AI router should not instantiate AI service modules."""

    service_modules = _service_modules()

    for module_name in service_modules:
        sys.modules.pop(module_name, None)
    sys.modules.pop("app.api.v1.ai", None)

    ai_module = importlib.import_module("app.api.v1.ai")

    assert hasattr(ai_module, "router")
    for module_name in service_modules:
        assert module_name not in sys.modules


def test_rulesets_router_import_does_not_eagerly_load_geometry_or_rules_engine() -> (
    None
):
    """The rulesets router should defer geometry/rules engine imports until use."""

    helper_modules = [
        "app.core.geometry.serializer",
        "app.core.geometry.builder",
        "app.core.rules.engine",
    ]
    script = f"""
import importlib
import json
import sys

helper_modules = {json.dumps(helper_modules)}
for name in helper_modules + ["app.api.v1.rulesets"]:
    sys.modules.pop(name, None)

rulesets_module = importlib.import_module("app.api.v1.rulesets")
print(
    json.dumps(
        {{
            "has_router": hasattr(rulesets_module, "router"),
            "loaded_helpers": [name for name in helper_modules if name in sys.modules],
        }}
    )
)
"""

    completed = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        check=False,
        env={
            **os.environ,
            "PYTHONPATH": _pythonpath(),
            "SECRET_KEY": os.environ.get("SECRET_KEY", "test-secret"),
        },
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout.strip().splitlines()[-1])
    assert payload == {"has_router": True, "loaded_helpers": []}


def test_projects_router_import_does_not_eagerly_load_finance_or_team_helpers() -> None:
    """Projects router import should stay off finance/team helper stacks."""

    helper_modules = [
        "app.api.v1.finance_common",
        "app.models.development_phase",
        "app.models.finance",
        "app.models.workflow",
        "app.services.team.team_service",
        "app.schemas.finance",
    ]
    script = f"""
import importlib
import json
import sys

helper_modules = {json.dumps(helper_modules)}
for name in helper_modules + ["app.api.v1.projects"]:
    sys.modules.pop(name, None)

projects_module = importlib.import_module("app.api.v1.projects")
print(
    json.dumps(
        {{
            "has_router": hasattr(projects_module, "router"),
            "loaded_helpers": [name for name in helper_modules if name in sys.modules],
        }}
    )
)
"""

    completed = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        check=False,
        env={
            **os.environ,
            "PYTHONPATH": _pythonpath(),
            "SECRET_KEY": os.environ.get("SECRET_KEY", "test-secret"),
        },
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout.strip().splitlines()[-1])
    assert payload == {"has_router": True, "loaded_helpers": []}


def test_main_import_does_not_eagerly_load_ai_services() -> None:
    """Importing the full app should not pre-initialize heavyweight AI modules."""

    route_modules = [
        "app.api.v1.agents",
        "app.api.v1.deals",
        "app.api.v1.developers_gps",
        "app.api.v1.export",
        "app.api.v1.imports",
        "app.api.v1.market_intelligence",
    ]
    heavy_main_modules = [
        "app.core.export",
        "app.models.rkp",
        "app.schemas.buildable",
        "app.schemas.finance",
    ]
    script = f"""
import importlib
import json
import sys

service_modules = {json.dumps(_service_modules())}
route_modules = {json.dumps(route_modules)}
heavy_main_modules = {json.dumps(heavy_main_modules)}
for name in service_modules + route_modules + heavy_main_modules + [
    "app.main",
    "app.api.v1",
    "app.api.v1.ai_config",
    "app.services.ai",
    "app.services.ai.config_service",
]:
    sys.modules.pop(name, None)

main_module = importlib.import_module("app.main")
print(
    json.dumps(
        {{
            "has_app": hasattr(main_module, "app"),
            "loaded": [name for name in service_modules if name in sys.modules],
            "loaded_routes": [name for name in route_modules if name in sys.modules],
            "loaded_heavy_main": [name for name in heavy_main_modules if name in sys.modules],
        }}
    )
)
"""

    completed = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        check=False,
        env={
            **os.environ,
            "PYTHONPATH": _pythonpath(),
            "SECRET_KEY": os.environ.get("SECRET_KEY", "test-secret"),
        },
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout.strip().splitlines()[-1])

    assert payload == {
        "has_app": True,
        "loaded": [],
        "loaded_routes": [],
        "loaded_heavy_main": [],
    }


def test_non_api_request_does_not_load_api_router_tree() -> None:
    """Health and metrics routes should stay cheap without forcing API router import."""

    route_modules = [
        "app.api.v1.agents",
        "app.api.v1.deals",
        "app.api.v1.developers_gps",
        "app.api.v1.market_intelligence",
        "app.api.v1.imports",
    ]
    script = f"""
import asyncio
import importlib
import json
import sys

from httpx import ASGITransport, AsyncClient

for name in {json.dumps(route_modules)} + [
    "app.main",
    "app.api.v1",
]:
    sys.modules.pop(name, None)

main_module = importlib.import_module("app.main")
app = main_module.app

async def _run():
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://testserver",
        headers={{"X-Role": "admin"}},
    ) as client:
        response = await client.get("/health/metrics")
    print(
        json.dumps(
            {{
                "status_code": response.status_code,
                "loaded_routes": [
                    name for name in {json.dumps(route_modules)} if name in sys.modules
                ],
            }}
        )
    )

asyncio.run(_run())
"""

    completed = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        check=False,
        env={
            **os.environ,
            "PYTHONPATH": _pythonpath(),
            "SECRET_KEY": os.environ.get("SECRET_KEY", "test-secret"),
        },
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout.strip().splitlines()[-1])

    assert payload == {"status_code": 200, "loaded_routes": []}


def test_build_api_router_does_not_eagerly_load_auth_or_entitlements_helpers() -> None:
    """Route registration should stay light and avoid request-time helper imports."""

    route_modules = [
        "app.api.v1.entitlements",
        "app.api.v1.users_db",
        "app.api.v1.users_secure",
    ]
    helper_modules = [
        "app.core.export.entitlements",
        "app.services.account_lockout",
        "app.utils.security",
    ]
    script = f"""
import importlib
import json
import sys

route_modules = {json.dumps(route_modules)}
helper_modules = {json.dumps(helper_modules)}

for name in route_modules + helper_modules + ["app.api.v1"]:
    sys.modules.pop(name, None)

api_module = importlib.import_module("app.api.v1")
router = api_module.build_api_router()
print(
    json.dumps(
        {{
            "route_count": len(router.routes),
            "loaded_helpers": [name for name in helper_modules if name in sys.modules],
            "loaded_routes": [name for name in route_modules if name in sys.modules],
        }}
    )
)
"""

    completed = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        check=False,
        env={
            **os.environ,
            "PYTHONPATH": _pythonpath(),
            "SECRET_KEY": os.environ.get("SECRET_KEY", "test-secret"),
        },
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout.strip().splitlines()[-1])

    assert payload["route_count"] > 0
    assert payload["loaded_routes"] == route_modules
    assert payload["loaded_helpers"] == []
