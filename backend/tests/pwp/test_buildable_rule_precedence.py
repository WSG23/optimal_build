"""Ensure buildable rule overrides take precedence over defaults."""

from __future__ import annotations

import asyncio
import sys
from types import ModuleType

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("pydantic")
pytest.importorskip("sqlalchemy")
pytest.importorskip("pytest_asyncio")
import pytest_asyncio  # noqa: F401  # Ensure plugin is registered for async fixtures

if (
    "structlog" not in sys.modules
):  # pragma: no cover - test shim for optional dependency

    class _StubBoundLogger:
        def bind(self, **kwargs):
            return self

        def info(self, *args, **kwargs):
            return None

        def warning(self, *args, **kwargs):
            return None

        def error(self, *args, **kwargs):
            return None

    def _noop(*args, **kwargs):
        return None

    class _StubProcessors(ModuleType):
        def __init__(self) -> None:
            super().__init__("structlog.processors")
            self.add_log_level = _noop
            self.format_exc_info = _noop

        def TimeStamper(self, *args, **kwargs):
            return _noop

        def StackInfoRenderer(self, *args, **kwargs):
            return _noop

        def JSONRenderer(self, *args, **kwargs):
            return _noop

    class _StubStdLib(ModuleType):
        class LoggerFactory:  # noqa: D401 - simple stub
            def __call__(self, *args, **kwargs):  # pragma: no cover - minimal stub
                return _StubBoundLogger()

        class BoundLogger(_StubBoundLogger):
            pass

    structlog_module = ModuleType("structlog")
    structlog_module._IS_VENDORED_STRUCTLOG = False
    structlog_module.processors = _StubProcessors()
    structlog_module.configure = _noop
    structlog_module.get_logger = lambda *args, **kwargs: _StubBoundLogger()
    structlog_module.make_filtering_bound_logger = (
        lambda *args, **kwargs: _StubBoundLogger
    )
    structlog_module.stdlib = _StubStdLib("structlog.stdlib")
    structlog_module.stdlib.LoggerFactory = _StubStdLib.LoggerFactory
    structlog_module.stdlib.BoundLogger = _StubStdLib.BoundLogger
    structlog_module.BoundLogger = _StubStdLib.BoundLogger

    sys.modules.setdefault("structlog", structlog_module)
    sys.modules.setdefault("structlog.processors", structlog_module.processors)
    sys.modules.setdefault("structlog.stdlib", structlog_module.stdlib)

from app.models.rkp import RefParcel, RefRule, RefZoningLayer
from app.schemas.buildable import BuildableDefaults
from app.services.buildable import ResolvedZone, calculate_buildable


def test_ingested_rule_overrides_seed_defaults(session_factory) -> None:
    zone_code = "R-PREC"
    defaults = BuildableDefaults(
        plot_ratio=4.0,
        site_area_m2=1000.0,
        site_coverage=0.45,
        floor_height_m=4.0,
        efficiency_factor=0.82,
    )

    async def _run() -> None:
        async with session_factory() as session:
            parcel = RefParcel(
                jurisdiction="SG",
                parcel_ref="MK99-00001",
                bounds_json={"type": "Polygon", "coordinates": []},
                area_m2=1500.0,
                source="test",
            )
            zoning_layer = RefZoningLayer(
                jurisdiction="SG",
                layer_name="MasterPlan",
                zone_code=zone_code,
                attributes={
                    "plot_ratio": 3.5,
                    "site_coverage_percent": 40,
                    "front_setback_min_m": 3.0,
                    "height_m": 30.0,
                    "floors_max": 10,
                },
            )
            session.add_all([parcel, zoning_layer])
            await session.flush()

            base_far = RefRule(
                jurisdiction="SG",
                authority="URA",
                topic="zoning",
                parameter_key="zoning.max_far",
                operator="<=",
                value="3.5",
                applicability={"zone_code": zone_code},
                review_status="approved",
                is_published=True,
                source_provenance={"seed_tag": "defaults"},
            )
            base_setback = RefRule(
                jurisdiction="SG",
                authority="URA",
                topic="zoning",
                parameter_key="zoning.setback.front_min_m",
                operator=">=",
                value="3.0",
                unit="m",
                applicability={"zone_code": zone_code},
                review_status="approved",
                is_published=True,
                source_provenance={"seed_tag": "defaults"},
            )
            override_far = RefRule(
                jurisdiction="SG",
                authority="URA",
                topic="zoning",
                parameter_key="zoning.max_far",
                operator="<=",
                value="2.1",
                applicability={"zone_code": zone_code},
                review_status="approved",
                is_published=True,
                source_provenance={"seed_tag": "ingested"},
            )
            override_setback = RefRule(
                jurisdiction="SG",
                authority="URA",
                topic="zoning",
                parameter_key="zoning.setback.front_min_m",
                operator=">=",
                value="5.0",
                unit="m",
                applicability={"zone_code": zone_code},
                review_status="approved",
                is_published=True,
                source_provenance={"seed_tag": "ingested"},
            )

            session.add_all([base_far, base_setback, override_far, override_setback])
            await session.flush()

            resolved = ResolvedZone(
                zone_code=zone_code,
                parcel=parcel,
                zone_layers=[zoning_layer],
                input_kind="parcel",
            )

            calculation = await calculate_buildable(session, resolved, defaults)

            assert calculation.metrics.gfa_cap_m2 == 3150

            rule_lookup = {rule.id: rule for rule in calculation.rules}
            assert override_far.id in rule_lookup
            assert override_setback.id in rule_lookup

            far_rule = rule_lookup[override_far.id]
            assert far_rule.parameter_key == "zoning.max_far"
            assert far_rule.value == "2.1"

            setback_rule = rule_lookup[override_setback.id]
            assert setback_rule.parameter_key == "zoning.setback.front_min_m"
            assert setback_rule.value == "5.0"
            assert setback_rule.unit == "m"

            # The less restrictive defaults should still be surfaced
            # and must not override overrides.
            assert base_far.id in rule_lookup
            assert base_setback.id in rule_lookup
            assert calculation.metrics.gfa_cap_m2 == 3150

    asyncio.run(_run())
