"""Shared fixtures for reference tests."""

from __future__ import annotations

import asyncio
import inspect
import json
import os
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_BACKEND_ROOT = _PROJECT_ROOT / "backend"
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))


class AttrDict(dict):
    """Dictionary allowing attribute-style access for stub payloads."""

    def __getattr__(self, key: str):
        try:
            return self[key]
        except KeyError as exc:  # pragma: no cover - missing key
            raise AttributeError(key) from exc


# Ensure SQLAlchemy is loaded BEFORE attempting any imports
try:
    from backend._sqlalchemy_stub import ensure_sqlalchemy

    _SQLALCHEMY_AVAILABLE = ensure_sqlalchemy()
    if not _SQLALCHEMY_AVAILABLE:
        # Try importing directly if ensure_sqlalchemy didn't find it
        import importlib

        try:
            importlib.import_module("sqlalchemy")
            _SQLALCHEMY_AVAILABLE = True
        except Exception:
            pass
except ImportError:
    _SQLALCHEMY_AVAILABLE = False

# IMPORTANT: Patch SQLite type compiler BEFORE any other imports
# This ensures SQLite can handle PostgreSQL-specific types (UUID, JSONB)
if _SQLALCHEMY_AVAILABLE:
    try:
        from sqlalchemy.dialects.sqlite.base import SQLiteTypeCompiler
    except ImportError:
        SQLiteTypeCompiler = None
else:
    SQLiteTypeCompiler = None

if SQLiteTypeCompiler is not None:
    if not hasattr(SQLiteTypeCompiler, "visit_UUID"):

        def _visit_UUID(self, _type, **_):  # pragma: no cover
            return "CHAR(36)"

        SQLiteTypeCompiler.visit_UUID = _visit_UUID

    if not hasattr(SQLiteTypeCompiler, "visit_JSONB"):

        def _visit_JSONB(self, _type, **_):  # pragma: no cover
            return "TEXT"

        SQLiteTypeCompiler.visit_JSONB = _visit_JSONB

# FastAPI stubs for environments without the dependency installed.
import importlib.util
import math
from types import ModuleType, SimpleNamespace

if importlib.util.find_spec("fastapi") is not None:  # pragma: no cover
    pass  # FastAPI available, no stub needed
else:  # pragma: no cover
    fastapi_stub = ModuleType("fastapi")
    fastapi_stub.__path__ = []  # mark as package for submodule imports

    class HTTPException(Exception):
        def __init__(
            self, status_code: int = 500, detail: object | None = None, headers=None
        ):
            super().__init__(detail)
            self.status_code = status_code
            self.detail = detail
            self.headers = headers

    class Depends:
        def __init__(self, dependency=None):
            self.dependency = dependency

    def _identity(value=None, *_args, **_kwargs):
        return value

    Query = Path = Body = Header = Cookie = File = Form = _identity

    class UploadFile:
        def __init__(self, filename: str = "", content_type: str = "text/plain"):
            self.filename = filename
            self.content_type = content_type
            self.file = None

    class APIRouter:
        def __init__(self, *_, prefix: str = "", **__):
            self.routes = []
            self.prefix = prefix

        def include_router(self, router, *_args, **_kwargs):
            if hasattr(router, "routes"):
                self.routes.extend(router.routes)
            return None

        def add_api_route(self, path, *_args, **_kwargs):
            route = SimpleNamespace(path=path)
            self.routes.append(route)
            return None

        def _route(self, path):
            full_path = f"{self.prefix}{path}"
            route = SimpleNamespace(path=full_path, endpoint=None)
            self.routes.append(route)

            def decorator(func):
                route.endpoint = func
                return func

            return decorator

        def get(self, path, *_, **__):
            return self._route(path)

        def post(self, path, *_, **__):
            return self._route(path)

        def put(self, path, *_, **__):
            return self._route(path)

        def patch(self, path, *_, **__):
            return self._route(path)

        def delete(self, path, *_, **__):
            return self._route(path)

        def websocket(self, path, *_, **__):
            return self._route(path)

        def api_route(self, path, *_, **__):
            return self._route(path)

    class FastAPI(APIRouter):
        def __init__(self, *_, **__):
            super().__init__()
            self.router = self
            self.dependency_overrides = {}

        async def handle_request(
            self,
            *,
            method: str,
            path: str,
            query_params=None,
            json_body=None,
            form_data=None,
            files=None,
            headers=None,
        ):
            for route in self.routes:
                if route.path == path:
                    endpoint = getattr(route, "endpoint", None)
                    if endpoint is None:
                        return 404, {}, {"detail": "not found"}
                    kwargs = {}
                    sig = inspect.signature(endpoint)
                    for name, param in sig.parameters.items():
                        default = param.default
                        if isinstance(default, Depends):
                            dep_fn = default.dependency
                            provider = self.dependency_overrides.get(dep_fn, dep_fn)
                            kwargs[name] = provider()
                        elif name in ("payload", "body"):
                            kwargs[name] = AttrDict(json_body or {})
                        else:
                            kwargs[name] = None
                    try:
                        result = endpoint(**kwargs)
                        if inspect.iscoroutine(result):
                            result = await result
                    except HTTPException as exc:  # type: ignore[name-defined]
                        payload = json.dumps(
                            {"detail": getattr(exc, "detail", str(exc))}, default=str
                        ).encode("utf-8")
                        return getattr(exc, "status_code", 500), {}, payload
                    status_code = getattr(result, "status_code", 200)
                    payload = (
                        result.model_dump()
                        if hasattr(result, "model_dump")
                        else getattr(result, "__dict__", result)
                    )
                    if isinstance(payload, AttrDict):
                        payload = dict(payload)
                    return (
                        status_code,
                        {},
                        json.dumps(payload, default=str).encode("utf-8"),
                    )
            return 404, {}, json.dumps({"detail": "not found"}).encode("utf-8")

        async def __call__(self, scope, receive, send):
            body = b""
            while True:
                message = await receive()
                if message.get("body"):
                    body += message["body"]
                if not message.get("more_body"):
                    break
            json_body = None
            if body:
                try:
                    json_body = json.loads(body.decode("utf-8"))
                except Exception:
                    json_body = None
            status_code, headers, payload = await self.handle_request(
                method=scope.get("method", "GET"),
                path=scope.get("path", "/"),
                json_body=json_body,
            )
            header_list = [
                (str(k).encode("utf-8"), str(v).encode("utf-8"))
                for k, v in (headers or {}).items()
            ]
            body_bytes = (
                payload
                if isinstance(payload, bytes | bytearray)
                else json.dumps(payload, default=str).encode("utf-8")
            )
            await send(
                {
                    "type": "http.response.start",
                    "status": status_code,
                    "headers": header_list,
                }
            )
            await send(
                {
                    "type": "http.response.body",
                    "body": body_bytes,
                    "more_body": False,
                }
            )

    class Request:
        def __init__(self):
            self.client = SimpleNamespace(host="testclient")
            self.url = SimpleNamespace(path="/")

    class Response:
        def __init__(
            self, content: object | None = None, media_type: str | None = None
        ):
            self.content = content
            self.media_type = media_type

    class WebSocketDisconnect(Exception):
        pass

    class WebSocket:
        def __init__(self):
            self.accepted = False
            self.sent = []
            self.received_queue = []

        async def accept(self):
            self.accepted = True

        async def receive_json(self):
            if self.received_queue:
                return self.received_queue.pop(0)
            raise WebSocketDisconnect()

        async def send_json(self, data):
            self.sent.append(data)

    fastapi_stub.HTTPException = HTTPException
    fastapi_stub.Depends = Depends
    fastapi_stub.Query = Query
    fastapi_stub.Path = Path
    fastapi_stub.Body = Body
    fastapi_stub.Header = Header
    fastapi_stub.Cookie = Cookie
    fastapi_stub.File = File
    fastapi_stub.Form = Form
    fastapi_stub.UploadFile = UploadFile
    fastapi_stub.APIRouter = APIRouter
    fastapi_stub.Request = Request
    fastapi_stub.Response = Response
    fastapi_stub.FastAPI = FastAPI
    fastapi_stub.WebSocket = WebSocket
    fastapi_stub.WebSocketDisconnect = WebSocketDisconnect
    fastapi_stub.status = SimpleNamespace(
        HTTP_200_OK=200,
        HTTP_201_CREATED=201,
        HTTP_400_BAD_REQUEST=400,
        HTTP_401_UNAUTHORIZED=401,
        HTTP_403_FORBIDDEN=403,
        HTTP_404_NOT_FOUND=404,
        HTTP_429_TOO_MANY_REQUESTS=429,
        HTTP_500_INTERNAL_SERVER_ERROR=500,
        HTTP_204_NO_CONTENT=204,
    )

    security_mod = ModuleType("fastapi.security")

    class HTTPAuthorizationCredentials:
        def __init__(self, credentials: str = "", scheme: str = "Bearer"):
            self.credentials = credentials
            self.scheme = scheme

    class HTTPBearer:
        def __init__(self, auto_error: bool = True):
            self.auto_error = auto_error

        def __call__(self, *_args, **_kwargs):
            return HTTPAuthorizationCredentials()

    security_mod.HTTPAuthorizationCredentials = HTTPAuthorizationCredentials
    security_mod.HTTPBearer = HTTPBearer

    fastapi_stub.security = security_mod
    responses_mod = ModuleType("fastapi.responses")

    class FileResponse(Response):
        def __init__(self, path: str, *_, **__):
            super().__init__(content=path)

    class StreamingResponse(Response):
        def __init__(self, content=None, *_, **__):
            super().__init__(content=content)

    class JSONResponse(Response):
        def __init__(self, content=None, *_, **__):
            super().__init__(content=content, media_type="application/json")

    responses_mod.FileResponse = FileResponse
    responses_mod.StreamingResponse = StreamingResponse
    responses_mod.Response = Response
    responses_mod.JSONResponse = JSONResponse

    fastapi_stub.responses = responses_mod
    sys.modules.setdefault("fastapi", fastapi_stub)
    sys.modules.setdefault("fastapi.security", security_mod)
    sys.modules.setdefault("fastapi.responses", responses_mod)

# Optional heavy deps used in import-time guards
if "numpy" not in sys.modules:
    numpy_stub = ModuleType("numpy")
    numpy_stub.sqrt = math.sqrt
    numpy_stub.float64 = float
    numpy_stub.int64 = int
    numpy_stub.int32 = int
    numpy_stub.int8 = int
    numpy_stub.array = lambda data, dtype=None: list(data)
    numpy_stub.asarray = lambda data, dtype=None: list(data)
    numpy_stub.mean = lambda data, axis=None: (sum(data) / len(data)) if data else 0
    numpy_stub.finfo = lambda _dtype=float: SimpleNamespace(resolution=0.0)
    numpy_stub.isscalar = lambda obj: isinstance(obj, int | float | bool | str)
    sys.modules["numpy"] = numpy_stub

if "pandas" not in sys.modules:
    pandas_stub = ModuleType("pandas")
    pandas_stub.DataFrame = object
    pandas_stub.Series = object
    sys.modules["pandas"] = pandas_stub

# Lightweight shapely stub to avoid heavy geometry dependency during unit tests.
if "shapely" not in sys.modules:
    shapely_stub = ModuleType("shapely")
    shapely_stub.__path__ = []

    class _Geometry:
        def __init__(self):
            self.bounds = (0.0, 0.0, 0.0, 0.0)
            self.centroid = SimpleNamespace(x=0.0, y=0.0)

        def contains(self, _point):
            return False

        def touches(self, _point):
            return False

    class Point(_Geometry):
        def __init__(self, x=0.0, y=0.0):
            super().__init__()
            self.x = x
            self.y = y

    def shape(_geometry):
        return _Geometry()

    class STRtree:
        def __init__(self, items=None):
            self.items = list(items or [])

        def query(self, *_args, **_kwargs):
            return self.items

    geometry_mod = ModuleType("shapely.geometry")
    geometry_mod.Point = Point
    geometry_mod.shape = shape

    strtree_mod = ModuleType("shapely.strtree")
    strtree_mod.STRtree = STRtree

    shapely_stub.geometry = geometry_mod
    shapely_stub.strtree = strtree_mod
    sys.modules["shapely"] = shapely_stub
    sys.modules["shapely.geometry"] = geometry_mod
    sys.modules["shapely.strtree"] = strtree_mod

for _optional_pkg in (
    "ezdxf",
    "ifcopenshell",
    "reportlab",
    "reportlab.pdfgen",
    "reportlab.pdfgen.canvas",
):
    if _optional_pkg not in sys.modules:
        stub = ModuleType(_optional_pkg)
        stub.__path__ = []
        sys.modules[_optional_pkg] = stub

if "trimesh" not in sys.modules:
    trimesh_stub = ModuleType("trimesh")
    trimesh_stub.__path__ = []

    class _SimpleMesh:
        def __init__(self, vertices=None, faces=None):
            self.vertices = numpy_stub.array(vertices or [])
            self.faces = numpy_stub.array(faces or [])
            self.visual = SimpleNamespace(face_colors=[])

    trimesh_stub.Trimesh = _SimpleMesh

    util_mod = ModuleType("trimesh.util")
    util_mod.concatenate = lambda meshes: _SimpleMesh()

    exchange_mod = ModuleType("trimesh.exchange")
    obj_mod = ModuleType("trimesh.exchange.obj")

    def _export_obj(mesh):
        return "mesh-obj"

    obj_mod.export_obj = _export_obj
    exchange_mod.obj = obj_mod

    trimesh_stub.util = util_mod
    trimesh_stub.exchange = exchange_mod

    sys.modules["trimesh"] = trimesh_stub
    sys.modules["trimesh.util"] = util_mod
    sys.modules["trimesh.exchange"] = exchange_mod
    sys.modules["trimesh.exchange.obj"] = obj_mod

# Stub heavy scenario builder to avoid importing optional 3D deps
if "app.services.agents.scenario_builder_3d" not in sys.modules:
    from enum import Enum

    scenario_builder_stub = ModuleType("app.services.agents.scenario_builder_3d")

    class ScenarioType(str, Enum):  # type: ignore[misc]
        NEW_BUILD = "new_build"
        RENOVATION = "renovation"
        MIXED_USE_CONVERSION = "mixed_use_conversion"
        VERTICAL_EXTENSION = "vertical_extension"
        PODIUM_TOWER = "podium_tower"
        PHASED_DEVELOPMENT = "phased"

    class Quick3DScenarioBuilder:
        def __init__(self, *_args, **_kwargs):
            self.generated = True

        async def generate_massing_scenarios(self, *_args, **_kwargs):
            return []

    scenario_builder_stub.ScenarioType = ScenarioType
    scenario_builder_stub.Quick3DScenarioBuilder = Quick3DScenarioBuilder

    sys.modules["app.services.agents.scenario_builder_3d"] = scenario_builder_stub

# Jose stubs
try:
    from jose import JWTError, jwt  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    jose_stub = ModuleType("jose")

    class JWTError(Exception):
        pass

    def _encode(payload, *_args, **_kwargs):
        return "token"

    def _decode(token, *_args, **_kwargs):
        return {}

    jose_stub.JWTError = JWTError
    jose_stub.jwt = SimpleNamespace(encode=_encode, decode=_decode)
    sys.modules.setdefault("jose", jose_stub)
else:
    JWTError = JWTError  # re-export for callers
    jwt = jwt  # re-export for callers

import importlib
from importlib import import_module

import pytest

if _SQLALCHEMY_AVAILABLE:
    try:
        from sqlalchemy.dialects.postgresql import UUID as PGUUID  # type: ignore
    except ImportError:  # pragma: no cover
        pg_module = ModuleType("sqlalchemy.dialects.postgresql")

        class _UUID:
            def __init__(self, *_, **__):
                pass

        pg_module.UUID = _UUID
        sys.modules.setdefault("sqlalchemy.dialects.postgresql", pg_module)
        PGUUID = _UUID
else:
    pg_module = ModuleType("sqlalchemy.dialects.postgresql")

    class _UUID:
        def __init__(self, *_, **__):
            pass

    pg_module.UUID = _UUID
    sys.modules.setdefault("sqlalchemy.dialects.postgresql", pg_module)
    PGUUID = _UUID

try:
    import geoalchemy2.admin.dialects.sqlite as _geo_sqlite
except ModuleNotFoundError:  # pragma: no cover
    _geo_sqlite = None

if _geo_sqlite is not None:

    def _noop_after_create(*_, **__):  # pragma: no cover
        return None

    class _NoopDialect:
        def after_create(self, *_, **__):  # pragma: no cover
            return None

    _geo_sqlite.select_dialect = lambda name: _NoopDialect()

try:  # pragma: no cover - optional dependency for async fixtures
    import pytest_asyncio
except ModuleNotFoundError:  # pragma: no cover - fallback stub when plugin missing
    pytest_asyncio = ModuleType("pytest_asyncio")
    pytest_asyncio.fixture = pytest.fixture  # type: ignore[attr-defined]
    sys.modules.setdefault("pytest_asyncio", pytest_asyncio)

if os.environ.get("ENABLE_BACKEND_TEST_FIXTURES") == "1":
    try:
        from backend.tests import (  # noqa: F401 - ensure fallback stubs are registered
            conftest as backend_conftest,
        )
    except Exception:  # pragma: no cover - fallback when backend fixtures unavailable
        backend_conftest = SimpleNamespace(
            flow_session_factory=None,
            async_session_factory=None,
            session=None,
            session_factory=None,
            reset_metrics=lambda *args, **kwargs: None,
            app_client=None,
            client_fixture=None,
        )
else:  # pragma: no cover - default to lightweight stubs
    backend_conftest = SimpleNamespace(
        flow_session_factory=None,
        async_session_factory=None,
        session=None,
        session_factory=None,
        reset_metrics=lambda *args, **kwargs: None,
        app_client=None,
        client_fixture=None,
    )


@pytest_asyncio.fixture(scope="session")
def event_loop():
    """Provide a session-scoped event loop compatible with session fixtures."""

    loop = asyncio.new_event_loop()
    try:
        yield loop
    finally:
        loop.close()


def _missing_fixture(*_args, **_kwargs):
    raise RuntimeError("backend test fixtures unavailable")


# Re-export backend fixtures in this namespace for pytest discovery.
_backend_flow_session_factory = getattr(
    backend_conftest, "flow_session_factory", _missing_fixture
)

# Only define our own fixtures if backend fixtures are not available
if _backend_flow_session_factory in (None, _missing_fixture):
    pytest_plugins = []
    from collections.abc import AsyncGenerator
    from contextlib import asynccontextmanager

    # Only skip if we're supposed to use local fixtures AND SQLAlchemy is not available
    if (
        not _SQLALCHEMY_AVAILABLE
        and os.environ.get("ENABLE_BACKEND_TEST_FIXTURES") != "1"
    ):
        pytest.skip("SQLAlchemy is required for test fixtures", allow_module_level=True)

    import app.utils.metrics as _metrics_module
    from app.core.database import get_session as _get_session
    from app.models.base import BaseModel as _FallbackBaseModel

    try:
        from app.main import app as _fastapi_app
    except Exception:  # pragma: no cover - FastAPI app unavailable
        _fastapi_app = None
    from sqlalchemy.ext.asyncio import (
        AsyncSession,
        async_sessionmaker,
        create_async_engine,
    )

    from httpx import AsyncClient as _AsyncClient

    try:
        from sqlalchemy.pool import StaticPool as _StaticPool
    except (ImportError, AttributeError):  # pragma: no cover - stub fallback

        class _StaticPool:  # type: ignore[too-many-ancestors]
            """Fallback StaticPool used when SQLAlchemy pool is unavailable."""

            pass

    _SORTED_TABLES = tuple(_FallbackBaseModel.metadata.sorted_tables)

    async def _truncate_all(session: AsyncSession) -> None:
        await session.rollback()
        for table in reversed(_SORTED_TABLES):
            await session.execute(table.delete())
        await session.commit()

    async def _reset_database(factory: async_sessionmaker[AsyncSession]) -> None:
        async with factory() as db_session:
            await _truncate_all(db_session)

    @pytest_asyncio.fixture(scope="session")
    async def flow_session_factory() -> (
        AsyncGenerator[async_sessionmaker[AsyncSession], None]
    ):
        engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=_StaticPool,
            future=True,
        )
        async with engine.begin() as conn:
            await conn.run_sync(_FallbackBaseModel.metadata.create_all)

        factory = async_sessionmaker(engine, expire_on_commit=False)

        override_targets: list[tuple[ModuleType, object]] = []
        for module_name in (
            "app.core.database",
            "backend.flows.watch_fetch",
            "backend.flows.parse_segment",
            "backend.flows.sync_products",
        ):
            try:
                module = import_module(module_name)
            except ModuleNotFoundError:  # pragma: no cover - optional modules
                continue
            previous = getattr(module, "AsyncSessionLocal", None)
            module.AsyncSessionLocal = factory
            override_targets.append((module, previous))

        try:
            yield factory
        finally:
            for module, previous in override_targets:
                if previous is None:
                    try:
                        delattr(module, "AsyncSessionLocal")
                    except AttributeError:  # pragma: no cover - already absent
                        pass
                else:
                    module.AsyncSessionLocal = previous
            await engine.dispose()

    @pytest_asyncio.fixture(autouse=True)
    async def _cleanup_flow_session_factory(flow_session_factory):
        await _reset_database(flow_session_factory)
        try:
            yield
        finally:
            await _reset_database(flow_session_factory)

    @pytest_asyncio.fixture
    async def async_session_factory(flow_session_factory):
        await _reset_database(flow_session_factory)
        try:
            yield flow_session_factory
        finally:
            await _reset_database(flow_session_factory)

    @pytest_asyncio.fixture
    async def session(async_session_factory):
        async with async_session_factory() as db_session:
            try:
                yield db_session
            finally:
                await _truncate_all(db_session)

    @pytest.fixture
    def session_factory(async_session_factory):
        @asynccontextmanager
        async def _factory():
            async with async_session_factory() as db_session:
                yield db_session

        return _factory

    @pytest.fixture(autouse=True)
    def reset_metrics():
        _metrics_module.reset_metrics()
        try:
            yield
        finally:
            _metrics_module.reset_metrics()

    @pytest_asyncio.fixture
    async def app_client(async_session_factory):
        if _fastapi_app is None:
            pytest.skip("FastAPI app is unavailable in the current test environment")

        async def _override_get_session():
            async with async_session_factory() as db_session:
                yield db_session

        _fastapi_app.dependency_overrides[_get_session] = _override_get_session
        async with _AsyncClient(
            app=_fastapi_app,
            base_url="http://testserver",
            headers={"X-Role": "admin"},
        ) as client_instance:
            yield client_instance
        _fastapi_app.dependency_overrides.pop(_get_session, None)
        await _reset_database(async_session_factory)

    @pytest_asyncio.fixture(name="client")
    async def client_fixture(app_client):
        yield app_client

    client = client_fixture
else:
    pytest_plugins = ["backend.tests.conftest"]
    flow_session_factory = _backend_flow_session_factory
    async_session_factory = getattr(
        backend_conftest, "async_session_factory", _missing_fixture
    )
    session = getattr(backend_conftest, "session", _missing_fixture)
    session_factory = getattr(backend_conftest, "session_factory", _missing_fixture)
    reset_metrics = getattr(backend_conftest, "reset_metrics", _missing_fixture)
    app_client = getattr(backend_conftest, "app_client", _missing_fixture)
    client = getattr(backend_conftest, "client_fixture", _missing_fixture)


from backend.app.core import database as app_database

base_module = importlib.import_module("backend.app.models.base")
app_base_module = importlib.import_module("app.models.base")
if not hasattr(base_module, "TimestampMixin"):

    class TimestampMixin:  # pragma: no cover - compatibility stub
        created_at = None
        updated_at = None

    base_module.TimestampMixin = TimestampMixin
    if not hasattr(app_base_module, "TimestampMixin"):
        app_base_module.TimestampMixin = TimestampMixin


base_module = sys.modules.get("backend.app.models.base")
app_base_module = sys.modules.get("app.models.base")
if base_module is not None and not hasattr(base_module, "TimestampMixin"):

    class _TimestampMixin:
        created_at = None
        updated_at = None

    base_module.TimestampMixin = _TimestampMixin
    if app_base_module is not None and not hasattr(app_base_module, "TimestampMixin"):
        app_base_module.TimestampMixin = _TimestampMixin

from app.models.base import BaseModel as _BaseModel

if not hasattr(_BaseModel.__class__, "metadata"):
    _BaseModel = _BaseModel  # pragma: no cover
if not hasattr(_BaseModel, "TimestampMixin") and "TimestampMixin" not in globals():

    class TimestampMixinStub:
        created_at = None
        updated_at = None

    backend_base_module = sys.modules.get("backend.app.models.base")
    if backend_base_module is not None:
        backend_base_module.TimestampMixin = TimestampMixinStub
    app_base_module = sys.modules.get("app.models.base")
    if app_base_module is not None and not hasattr(app_base_module, "TimestampMixin"):
        app_base_module.TimestampMixin = TimestampMixinStub
from backend.scripts.seed_market_demo import seed_market_demo
from backend.scripts.seed_nonreg import seed_nonregulated_reference_data


def pytest_configure(config: pytest.Config) -> None:
    """Register project-specific markers to silence pytest warnings."""

    config.addinivalue_line(
        "markers", "asyncio: mark test as requiring asyncio event loop support"
    )


@pytest_asyncio.fixture(autouse=True)
async def _override_app_database(monkeypatch):
    async_session_factory = getattr(backend_conftest, "async_session_factory", None)
    if async_session_factory in (None, _missing_fixture):
        yield
        return
    """Ensure application session factories use the in-memory test database."""

    monkeypatch.setattr(
        app_database, "AsyncSessionLocal", async_session_factory, raising=False
    )

    sync_products = import_module("backend.flows.sync_products")
    watch_fetch = import_module("backend.flows.watch_fetch")
    parse_segment = import_module("backend.flows.parse_segment")

    for module in (sync_products, watch_fetch, parse_segment):
        monkeypatch.setattr(
            module, "AsyncSessionLocal", async_session_factory, raising=False
        )
    try:
        yield
    except Exception:  # pragma: no cover - best-effort fallback
        return


@pytest_asyncio.fixture
async def reference_data(async_session_factory):
    """Populate non-regulated reference data for tests that require it."""

    if async_session_factory in (None, _missing_fixture):  # pragma: no cover - safety
        yield None
        return

    async with async_session_factory() as session:
        await seed_nonregulated_reference_data(session, commit=True)
    yield True


@pytest_asyncio.fixture
async def market_demo_data(async_session_factory):
    """Populate representative market intelligence demo data."""

    if async_session_factory in (None, _missing_fixture):  # pragma: no cover - safety
        yield None
        return

    async with async_session_factory() as session:
        await seed_market_demo(session, reset_existing=True)
    yield True
