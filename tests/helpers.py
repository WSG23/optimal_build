"""Test helpers for analytics modules."""

from __future__ import annotations

import sys
from types import ModuleType


def install_property_stub(monkeypatch) -> None:
    """Register lightweight stubs for property models to avoid SQLAlchemy metadata."""

    from app.models.base import BaseModel as _BaseModel

    if "properties" in _BaseModel.metadata.tables:
        _BaseModel.metadata.remove(_BaseModel.metadata.tables["properties"])

    module = ModuleType("backend.app.models.property")
    from enum import Enum

    class PropertyType(str, Enum):
        OFFICE = "office"
        RETAIL = "retail"

    module.PropertyType = PropertyType
    module.Property = object
    monkeypatch.setitem(sys.modules, "backend.app.models.property", module)
    monkeypatch.setitem(sys.modules, "app.models.property", module)


def install_market_data_stub(monkeypatch) -> None:
    module = ModuleType("app.services.agents.market_data_service")
    module.MarketDataService = object
    monkeypatch.setitem(sys.modules, "app.services.agents.market_data_service", module)
    monkeypatch.setitem(
        sys.modules, "backend.app.services.agents.market_data_service", module
    )


def install_market_analytics_stub(monkeypatch, analytics_cls) -> None:
    module = ModuleType("app.services.agents.market_intelligence_analytics")
    module.MarketIntelligenceAnalytics = analytics_cls
    monkeypatch.setitem(
        sys.modules, "app.services.agents.market_intelligence_analytics", module
    )
    monkeypatch.setitem(
        sys.modules, "backend.app.services.agents.market_intelligence_analytics", module
    )


def ensure_sqlite_uuid(monkeypatch) -> None:
    from sqlalchemy.dialects.sqlite.base import SQLiteTypeCompiler

    if not hasattr(SQLiteTypeCompiler, "visit_UUID"):

        def visit_UUID(self, _type, **_):  # pragma: no cover
            return "CHAR(36)"

        monkeypatch.setattr(SQLiteTypeCompiler, "visit_UUID", visit_UUID, raising=False)

    if not hasattr(SQLiteTypeCompiler, "visit_JSONB"):

        def visit_JSONB(self, _type, **_):  # pragma: no cover
            return "TEXT"

        monkeypatch.setattr(
            SQLiteTypeCompiler, "visit_JSONB", visit_JSONB, raising=False
        )


__all__ = [
    "install_property_stub",
    "install_market_data_stub",
    "install_market_analytics_stub",
    "ensure_sqlite_uuid",
]
