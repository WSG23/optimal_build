"""Project-level proxy for the Pydantic package.

The repository keeps a tiny fallback implementation for environments where
the third-party dependency is unavailable. When the real distribution is
present (normal development workflow), this module transparently re-exports
it so application code sees the complete API surface.
"""

from __future__ import annotations

import sys
from importlib import machinery, util
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, Dict, Iterable, List, Tuple

_REPO_ROOT = Path(__file__).resolve().parents[1]


def _runtime_search_paths() -> list[str]:
    """Return interpreter search paths that may contain the real package."""

    search_paths: list[str] = []
    for entry in sys.path:
        if entry in {"", "."}:
            continue
        try:
            resolved = Path(entry).resolve()
        except OSError:
            search_paths.append(entry)
            continue

        inside_repo = resolved == _REPO_ROOT or _REPO_ROOT in resolved.parents
        if inside_repo and "site-packages" not in resolved.parts and "dist-packages" not in resolved.parts:
            continue

        search_paths.append(str(resolved))
    return search_paths


def _load_runtime() -> ModuleType:
    """Import the installed Pydantic distribution if it exists."""

    spec = machinery.PathFinder.find_spec("pydantic", _runtime_search_paths())
    if spec is None or spec.loader is None:
        raise ModuleNotFoundError("Runtime Pydantic distribution not found")

    module = util.module_from_spec(spec)
    sys.modules["pydantic"] = module
    spec.loader.exec_module(module)
    return module


def _reexport(module: ModuleType) -> None:
    """Expose the runtime module's public attributes from this proxy."""

    exported: Iterable[str]
    runtime_all = getattr(module, "__all__", None)
    if runtime_all is None:
        exported = [name for name in dir(module) if not name.startswith("_")]
    else:
        exported = runtime_all

    globals().update({name: getattr(module, name) for name in exported})
    globals()["__all__"] = list(exported)


try:
    _runtime_module = _load_runtime()
except ModuleNotFoundError:
    _runtime_module = None

if _runtime_module is not None:
    _reexport(_runtime_module)
else:

    __all__ = ["BaseModel", "ConfigDict", "model_validator", "field_validator", "Field"]

    class ConfigDict(dict):
        """Minimal representation of :class:`pydantic.ConfigDict`.

        Pydantic v2 exposes ``ConfigDict`` as a convenience helper that accepts
        keyword arguments and stores them in an immutable mapping. The stub only
        needs to preserve the supplied key/value pairs so downstream schemas can
        read flags such as ``from_attributes=True`` or ``extra=\"allow\"``.
        """

        def __init__(self, **kwargs: Any) -> None:
            super().__init__(kwargs)

    def Field(default: Any = None, **_: Any) -> Any:
        """Return the provided default value."""

        return default

    def model_validator(
        *, mode: str = "after"
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Decorator registering a model-level validator."""

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            setattr(func, "__model_validator__", {"mode": mode})
            return func

        return decorator

    def field_validator(
        *_fields: str, **_kwargs: Any
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Stub ``field_validator`` decorator that leaves the function unchanged."""

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            return func

        return decorator

    class _ModelMeta(type):
        def __new__(
            mcls, name: str, bases: Tuple[type, ...], namespace: Dict[str, Any]
        ) -> "_ModelMeta":
            validators: List[Tuple[str, Callable[..., Any]]] = []
            for base in bases:
                validators.extend(getattr(base, "_model_validators", []))
            for value in namespace.values():
                marker = getattr(value, "__model_validator__", None)
                if marker:
                    validators.append((marker["mode"], value))
            namespace["_model_validators"] = validators
            return super().__new__(mcls, name, bases, namespace)

    class BaseModel(metaclass=_ModelMeta):
        """Very small subset of :class:`pydantic.BaseModel`."""

        def __init__(self, **data: Any) -> None:
            annotations: Dict[str, Any] = getattr(self, "__annotations__", {})
            for name, _annotation in annotations.items():
                if name in data:
                    value = data.pop(name)
                else:
                    value = getattr(self.__class__, name, None)
                setattr(self, name, value)
            for key, value in data.items():
                setattr(self, key, value)
            for mode, validator in getattr(self, "_model_validators", []):
                if mode == "after":
                    result = validator(self.__class__, self)
                    if result is not None and result is not self:
                        if isinstance(result, BaseModel):
                            for key, value in result.__dict__.items():
                                setattr(self, key, value)
                        else:
                            raise TypeError("Validators must return the model instance")
                else:
                    validator(self.__class__, self)

        def model_dump(self, *, mode: str | None = None) -> Dict[str, Any]:
            return dict(self.__dict__)

        @classmethod
        def model_validate(cls, data: Dict[str, Any]) -> "BaseModel":
            return cls(**data)
