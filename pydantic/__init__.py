"""Compatibility shim for environments where Pydantic is not installed.

When the real dependency is available this module delegates to it. The fallback
keeps lightweight route/unit tests importable in stripped-down environments.
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeVar

_THIS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _THIS_DIR.parent
_T = TypeVar("_T")


def _external_search_paths() -> list[str]:
    paths: list[str] = []
    for raw_entry in sys.path:
        entry = Path(raw_entry or ".").resolve()
        if (entry / "pydantic").resolve() != _THIS_DIR:
            paths.append(str(entry))
    return paths


def _load_real_pydantic() -> object | None:
    spec = importlib.machinery.PathFinder.find_spec(
        "pydantic", _external_search_paths()
    )
    if spec is None or spec.loader is None or spec.origin == __file__:
        return None

    module = importlib.util.module_from_spec(spec)
    previous = sys.modules.get(__name__)
    sys.modules[__name__] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        if previous is not None:
            sys.modules[__name__] = previous
        else:
            sys.modules.pop(__name__, None)
        raise
    return module


_real_pydantic = _load_real_pydantic()

if _real_pydantic is not None:
    globals().update(_real_pydantic.__dict__)
else:

    class ValidationError(Exception):
        """Fallback validation exception."""

    class BaseModel:
        """Small subset of Pydantic's BaseModel used by lightweight tests."""

        model_config: dict[str, Any] = {}

        def __init__(self, **data: Any) -> None:
            annotations = getattr(self.__class__, "__annotations__", {})
            for name, _annotation in annotations.items():
                if name in data:
                    setattr(self, name, data.pop(name))
                elif hasattr(self.__class__, name):
                    setattr(self, name, getattr(self.__class__, name))
                else:
                    setattr(self, name, None)
            for name, value in data.items():
                setattr(self, name, value)

        @classmethod
        def model_validate(cls: type[_T], value: Any) -> _T:
            if isinstance(value, cls):
                return value
            if isinstance(value, dict):
                return cls(**value)
            data = {
                key: getattr(value, key)
                for key in dir(value)
                if not key.startswith("_") and not callable(getattr(value, key))
            }
            return cls(**data)

        def model_dump(self, **_kwargs: Any) -> dict[str, Any]:
            return dict(self.__dict__)

        def dict(self, **kwargs: Any) -> dict[str, Any]:
            return self.model_dump(**kwargs)

        def model_dump_json(self, **_kwargs: Any) -> str:
            return json.dumps(self.model_dump())

    def ConfigDict(**kwargs: Any) -> dict[str, Any]:
        return dict(kwargs)

    def Field(
        default: Any = None,
        *,
        default_factory: Callable[[], Any] | None = None,
        **_kwargs: Any,
    ) -> Any:
        if default_factory is not None:
            return default_factory()
        return default

    def _identity_decorator(*_args: Any, **_kwargs: Any) -> Callable[[_T], _T]:
        def decorator(func: _T) -> _T:
            return func

        return decorator

    field_validator = _identity_decorator
    model_validator = _identity_decorator
    field_serializer = _identity_decorator
    computed_field = _identity_decorator
    EmailStr = str

    __all__ = [
        "BaseModel",
        "ConfigDict",
        "EmailStr",
        "Field",
        "ValidationError",
        "computed_field",
        "field_serializer",
        "field_validator",
        "model_validator",
    ]
