from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Tuple
import importlib.util
import sys
import types

import pytest

pytestmark = pytest.mark.no_db

_ROOT = Path(__file__).resolve().parents[3]


def _load_module(name: str, relative_path: str):
    module_path = _ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module {name} from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


class _SelectStatement:
    def __init__(self, model: Any) -> None:
        self.model = model
        self._where_criteria: list[Any] = []

    def where(self, *criteria: Any) -> "_SelectStatement":
        self._where_criteria.extend(criteria)
        return self


_sqlalchemy = types.ModuleType("sqlalchemy")
_sqlalchemy.select = lambda model: _SelectStatement(model)
_sqlalchemy.__all__ = ["select"]

_ext_pkg = types.ModuleType("sqlalchemy.ext")
_asyncio_pkg = types.ModuleType("sqlalchemy.ext.asyncio")


class AsyncSession:  # pragma: no cover - compatibility shim
    pass


_asyncio_pkg.AsyncSession = AsyncSession
_ext_pkg.asyncio = _asyncio_pkg

_sqlalchemy.ext = _ext_pkg

sys.modules.setdefault("sqlalchemy", _sqlalchemy)
sys.modules.setdefault("sqlalchemy.ext", _ext_pkg)
sys.modules.setdefault("sqlalchemy.ext.asyncio", _asyncio_pkg)

_models_pkg = sys.modules.setdefault("app.models", types.ModuleType("app.models"))
_models_pkg.__path__ = []  # type: ignore[attr-defined]
_audit_module = types.ModuleType("app.models.audit")


class AuditLog:  # pragma: no cover - compatibility shim
    pass


_audit_module.AuditLog = AuditLog
_models_pkg.audit = _audit_module  # type: ignore[attr-defined]
sys.modules["app.models.audit"] = _audit_module


@dataclass
class ImportRecord:
    id: str
    project_id: int
    filename: str
    content_type: str
    size_bytes: int
    storage_path: str
    parse_result: dict[str, Any] | None = None
    vector_summary: dict[str, Any] | None = None
    metric_overrides: dict[str, Any] | None = None
    zone_code: str | None = None
    uploaded_at: datetime | None = None


class _Column:
    def __init__(self, key: str) -> None:
        self.key = key

    def __eq__(self, other: Any) -> "_Expression":  # pragma: no cover - comparison stub
        return _Expression(self, other)


class _Expression:
    def __init__(self, left: _Column, right: Any) -> None:
        self.left = left
        self.right = types.SimpleNamespace(value=right)


class OverlaySourceGeometry:  # pragma: no cover - lightweight stand-in
    project_id = _Column("project_id")
    source_geometry_key = _Column("source_geometry_key")

    def __init__(
        self,
        *,
        project_id: int,
        source_geometry_key: str,
        graph: dict[str, Any],
        metadata: dict[str, Any],
        checksum: str,
    ) -> None:
        self.id: int | None = None
        self.project_id = project_id
        self.source_geometry_key = source_geometry_key
        self.graph = graph
        self.metadata = metadata
        self.checksum = checksum


_imports_module = types.ModuleType("app.models.imports")
_imports_module.ImportRecord = ImportRecord
_models_pkg.imports = _imports_module  # type: ignore[attr-defined]
sys.modules["app.models.imports"] = _imports_module

_overlay_module = types.ModuleType("app.models.overlay")
_overlay_module.OverlaySourceGeometry = OverlaySourceGeometry
_models_pkg.overlay = _overlay_module  # type: ignore[attr-defined]
sys.modules["app.models.overlay"] = _overlay_module

overlay_ingest = _load_module(
    "overlay_ingest_stub", "backend/app/services/overlay_ingest.py"
)

sys.modules.pop("sqlalchemy", None)
sys.modules.pop("sqlalchemy.ext", None)
sys.modules.pop("sqlalchemy.ext.asyncio", None)
sys.modules.pop("app.models", None)
sys.modules.pop("app.models.audit", None)
sys.modules.pop("app.models.imports", None)
sys.modules.pop("app.models.overlay", None)


@dataclass
class StubImportRecord:
    id: str
    project_id: int
    filename: str
    content_type: str
    size_bytes: int
    storage_path: str
    parse_result: dict[str, Any] | None = None
    vector_summary: dict[str, Any] | None = None
    metric_overrides: dict[str, Any] | None = None
    zone_code: str | None = None
    uploaded_at: datetime | None = None


class StubResult:
    def __init__(self, record: overlay_ingest.OverlaySourceGeometry | None) -> None:
        self._record = record

    def scalars(self) -> "StubResult":
        return self

    def first(self) -> overlay_ingest.OverlaySourceGeometry | None:
        return self._record


class StubAsyncSession:
    """Minimal async session emulating SQLAlchemy behaviour for tests."""

    def __init__(self) -> None:
        self._records: Dict[Tuple[int, str], overlay_ingest.OverlaySourceGeometry] = {}
        self._next_id = 1
        self.add_calls: list[overlay_ingest.OverlaySourceGeometry] = []
        self.flush_calls = 0

    async def execute(self, stmt: Any) -> StubResult:
        criteria: dict[str, Any] = {}
        for expression in getattr(stmt, "_where_criteria", ()):  # type: ignore[attr-defined]
            left = getattr(expression, "left", None)
            right = getattr(expression, "right", None)
            if left is None or right is None:
                continue
            key = getattr(left, "key", None)
            value = getattr(right, "value", None)
            if key is not None:
                criteria[key] = value
        lookup = (criteria.get("project_id"), criteria.get("source_geometry_key"))
        record = self._records.get(lookup) if None not in lookup else None
        return StubResult(record)

    def add(self, record: overlay_ingest.OverlaySourceGeometry) -> None:
        if record.id is None:
            record.id = self._next_id
            self._next_id += 1
        key = (record.project_id, record.source_geometry_key)
        self._records[key] = record
        self.add_calls.append(record)

    async def flush(self) -> None:  # pragma: no cover - trivial counter
        self.flush_calls += 1


@pytest.mark.asyncio
async def test_ingest_parsed_import_geometry_persists_and_updates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The helper should insert new records and update existing ones."""

    session = StubAsyncSession()

    import_record = StubImportRecord(
        id="import-1",
        project_id=101,
        filename="layout.json",
        content_type="application/json",
        size_bytes=4096,
        storage_path="/tmp/layout.json",
        vector_summary={"levels": 2},
        metric_overrides={"density": 1.2},
        zone_code="R1",
        uploaded_at=datetime.now(timezone.utc),
    )

    events: list[dict[str, Any]] = []

    async def fake_append_event(
        session_arg: Any,
        *,
        project_id: int,
        event_type: str,
        context: dict[str, Any],
        **kwargs: Any,
    ) -> object:
        events.append(
            {
                "session": session_arg,
                "project_id": project_id,
                "event_type": event_type,
                "context": dict(context),
            }
        )
        return object()

    monkeypatch.setattr(overlay_ingest, "append_event", fake_append_event)

    def make_fingerprint(graph_payload: dict[str, Any]) -> str:
        return f"{graph_payload['id']}-fingerprint"

    class DummyGeometry:
        def __init__(self, fingerprint: str) -> None:
            self._fingerprint = fingerprint

        def fingerprint(self) -> str:
            return self._fingerprint

    def fake_from_export(payload: dict[str, Any]) -> DummyGeometry:
        return DummyGeometry(make_fingerprint(payload))

    def fake_to_export(geometry: DummyGeometry) -> dict[str, str]:
        return {"fingerprint": geometry.fingerprint()}

    monkeypatch.setattr(
        overlay_ingest.GeometrySerializer,
        "from_export",
        staticmethod(fake_from_export),
    )
    monkeypatch.setattr(
        overlay_ingest.GeometrySerializer,
        "to_export",
        staticmethod(fake_to_export),
    )

    initial_payload = {
        "graph": {"id": "initial"},
        "metadata": {"source": "cad-parser", "ignored": None},
        "floors": 5,
        "units": 20,
    }

    record = await overlay_ingest.ingest_parsed_import_geometry(
        session,
        project_id=import_record.project_id,
        import_record=import_record,  # type: ignore[arg-type]
        parse_payload=initial_payload,
        source_key="custom-key",
    )

    assert record.project_id == import_record.project_id
    assert record.source_geometry_key == "custom-key"
    assert record.graph == {"fingerprint": "initial-fingerprint"}

    metadata = record.metadata
    assert metadata["import_id"] == import_record.id
    assert metadata["filename"] == import_record.filename
    assert metadata["parser"] == "cad-parser"
    assert metadata["floors"] == 5
    assert metadata["vector_summary"] == import_record.vector_summary
    assert metadata["zone_code"] == "R1"
    assert "ignored" not in metadata
    assert "ingested_at" in metadata

    assert len(events) == 1
    context = events[0]["context"]
    assert context["checksum"] == "initial-fingerprint"
    assert context["parser"] == "cad-parser"

    updated_payload = {
        "graph": {"id": "updated"},
        "metadata": {"source": "cad-parser", "version": "v2"},
        "floors": 7,
        "units": None,
    }

    updated_record = await overlay_ingest.ingest_parsed_import_geometry(
        session,
        project_id=import_record.project_id,
        import_record=import_record,  # type: ignore[arg-type]
        parse_payload=updated_payload,
        source_key="custom-key",
    )

    assert updated_record.id == record.id
    assert updated_record.graph == {"fingerprint": "updated-fingerprint"}
    updated_metadata = updated_record.metadata
    assert updated_metadata["floors"] == 7
    assert "units" not in updated_metadata
    assert updated_metadata["parser"] == "cad-parser"

    assert len(events) == 2
    assert events[-1]["context"]["checksum"] == "updated-fingerprint"


@pytest.mark.asyncio
async def test_ingest_parsed_import_geometry_validates_payload() -> None:
    """The helper should guard against malformed parse payloads."""

    session = StubAsyncSession()
    import_record = StubImportRecord(
        id="import-2",
        project_id=202,
        filename="layout.json",
        content_type="application/json",
        size_bytes=2048,
        storage_path="/tmp/layout.json",
    )

    with pytest.raises(ValueError):
        await overlay_ingest.ingest_parsed_import_geometry(
            session,
            project_id=import_record.project_id,
            import_record=import_record,  # type: ignore[arg-type]
            parse_payload="not a mapping",  # type: ignore[arg-type]
        )

    with pytest.raises(ValueError):
        await overlay_ingest.ingest_parsed_import_geometry(
            session,
            project_id=import_record.project_id,
            import_record=import_record,  # type: ignore[arg-type]
            parse_payload={},
        )
