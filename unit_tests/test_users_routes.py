import importlib
import os
import types
from pathlib import Path
import sys

import pytest

try:
    from fastapi import HTTPException  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - fallback for test environments
    fastapi_stub = types.ModuleType("fastapi")

    class HTTPException(Exception):
        def __init__(self, status_code: int, detail: str, headers=None):
            super().__init__(detail)
            self.status_code = status_code
            self.detail = detail
            self.headers = headers

    class Depends:
        def __init__(self, dependency=None):
            self.dependency = dependency

    class APIRouter:
        def __init__(self, *_, **__):
            pass

        def get(self, *_, **__):
            def decorator(func):
                return func

            return decorator

        def post(self, *_, **__):
            def decorator(func):
                return func

            return decorator

        def include_router(self, *_args, **_kwargs):
            return None

    security_mod = types.ModuleType("fastapi.security")

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

    fastapi_stub.HTTPException = HTTPException
    fastapi_stub.Depends = Depends
    fastapi_stub.APIRouter = APIRouter
    fastapi_stub.status = types.SimpleNamespace(HTTP_401_UNAUTHORIZED=401)
    fastapi_stub.security = security_mod
    sys.modules["fastapi"] = fastapi_stub
    sys.modules["fastapi.security"] = security_mod
    from fastapi import HTTPException  # type: ignore  # noqa: E402

import pydantic as _pydantic  # noqa: E402

if not hasattr(_pydantic, "field_serializer"):
    def _field_serializer_stub(*_args, **_kwargs):
        def decorator(func):
            return func

        return decorator

    _pydantic.field_serializer = _field_serializer_stub  # type: ignore[attr-defined]
    all_attr = getattr(_pydantic, "__all__", None)
    if isinstance(all_attr, list) and "field_serializer" not in all_attr:
        all_attr.append("field_serializer")
if not hasattr(_pydantic, "computed_field"):
    def _computed_field_stub(*_args, **_kwargs):
        def decorator(func):
            return property(func)

        return decorator

    _pydantic.computed_field = _computed_field_stub  # type: ignore[attr-defined]
    all_attr = getattr(_pydantic, "__all__", None)
    if isinstance(all_attr, list) and "computed_field" not in all_attr:
        all_attr.append("computed_field")

# Ensure auth settings are satisfied during module import
os.environ.setdefault("SECRET_KEY", "test-secret-key")

from app.core.auth import TokenData  # noqa: E402
from app.services.account_lockout import reset_lockout_service  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = REPO_ROOT / "backend" / "app"
API_V1_PATH = APP_ROOT / "api" / "v1"
import app.core.auth.service as auth_service_module  # noqa: E402

# Provide a lightweight api.v1 package to avoid loading the router aggregator.
api_pkg = sys.modules.get("app.api")
if api_pkg is None:
    api_pkg = types.ModuleType("app.api")
    api_pkg.__path__ = [str(APP_ROOT / "api")]
    sys.modules["app.api"] = api_pkg

api_v1_pkg = types.ModuleType("app.api.v1")
api_v1_pkg.__path__ = [str(API_V1_PATH)]
sys.modules["app.api.v1"] = api_v1_pkg

test_users = importlib.import_module("app.api.v1.test_users")
users_secure = importlib.import_module("app.api.v1.users_secure")


@pytest.fixture(autouse=True)
def patch_password_hashing(monkeypatch):
    monkeypatch.setattr(auth_service_module, "hash_password", lambda pwd: f"hashed-{pwd}")
    monkeypatch.setattr(
        auth_service_module, "verify_password", lambda plain, hashed: hashed == f"hashed-{plain}"
    )


@pytest.fixture(autouse=True)
def reset_user_state():
    test_users.fake_users_db.clear()
    users_secure.memory_repo._users.clear()
    reset_lockout_service()
    yield
    test_users.fake_users_db.clear()
    users_secure.memory_repo._users.clear()
    reset_lockout_service()


@pytest.fixture
def users_db_module(monkeypatch):
    """Reload the users_db module using an in-memory SQLite database."""

    from sqlalchemy import create_engine as real_create_engine
    import sqlalchemy

    def _in_memory_engine(*_args, **_kwargs):
        return real_create_engine(
            "sqlite:///:memory:", connect_args={"check_same_thread": False}
        )

    monkeypatch.setattr(sqlalchemy, "create_engine", _in_memory_engine)

    module = importlib.import_module("app.api.v1.users_db")
    module = importlib.reload(module)
    try:
        yield module
    finally:
        module.engine.dispose()


def test_test_users_signup_and_listing():
    resp = test_users.signup(
        test_users.UserSignup(
            email="test@example.com",
            username="tester",
            full_name="Test User",
            password="Secret123!",
        )
    )
    assert resp.email == "test@example.com"
    assert resp.message == "User registered successfully!"

    with pytest.raises(HTTPException):
        test_users.signup(
            test_users.UserSignup(
                email="test@example.com",
                username="tester",
                full_name="Test User",
                password="Secret123!",
            )
        )

    listing = test_users.list_users()
    assert listing["total"] == 1
    assert "password" not in listing["users"][0]
    assert listing["users"][0]["email"] == "test@example.com"
    assert test_users.test_endpoint()["status"] == "success"


def test_users_secure_signup_validation_and_listing():
    with pytest.raises(ValueError):
        users_secure.UserSignup.validate_full_name("   ")

    assert users_secure.UserSignup.validate_full_name("  Alice  ") == "Alice"

    payload = users_secure.UserSignup(
        email="good@example.com",
        username="good_user",
        full_name="Good User",
        password="Password123!",
    )
    user_response = users_secure.signup(payload)
    assert user_response.email == payload.email

    repo_user = users_secure.memory_repo.get_by_email(payload.email)
    assert repo_user is not None
    assert repo_user.hashed_password != payload.password

    login_response = users_secure.login(
        users_secure.UserLogin(email=payload.email, password=payload.password)
    )
    assert login_response.message == "Login successful"
    assert login_response.tokens.token_type == "bearer"

    test_payload = users_secure.test()
    assert test_payload["status"] == "ok"

    listing = users_secure.list_users()
    assert listing["total"] == 1
    assert listing["users"][0].email == payload.email

    with pytest.raises(HTTPException):
        users_secure.signup(payload)


@pytest.mark.anyio
async def test_users_secure_get_me_returns_current_user():
    payload = users_secure.UserSignup(
        email="me@example.com",
        username="me_user",
        full_name="Me User",
        password="Password123!",
    )
    users_secure.signup(payload)
    token = TokenData(email=payload.email, username=payload.username, user_id="user-1")

    current = await users_secure.get_me(token)
    assert current.email == payload.email
    assert current.username == payload.username


@pytest.mark.anyio
async def test_users_db_signup_login_and_me(users_db_module):
    session = users_db_module.SessionLocal()
    try:
        payload = users_db_module.UserSignup(
            email="db@example.com",
            username="db_user",
            full_name="DB User",
            password="Password123!",
        )
        created = users_db_module.signup(payload, db=session)
        assert created.email == payload.email

        with pytest.raises(HTTPException):
            users_db_module.signup(payload, db=session)

        login_resp = users_db_module.login(
            users_db_module.UserLogin(
                email=payload.email,
                password=payload.password,
            ),
            db=session,
        )
        assert login_resp.user.email == payload.email

        token = TokenData(
            email=payload.email, username=payload.username, user_id=created.id
        )
        current = await users_db_module.get_me(token, db=session)
        assert current.email == payload.email

        listing = users_db_module.list_users(db=session)
        assert listing["total"] == 1
        assert listing["users"][0].email == payload.email

        assert users_db_module.test_endpoint()["status"] == "ok"
    finally:
        session.close()
