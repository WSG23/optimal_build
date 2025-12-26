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
from types import ModuleType, SimpleNamespace
from typing import Any, Callable, Dict, Iterable, List, Tuple
from datetime import datetime

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

    __all__ = [
        "BaseModel",
        "ConfigDict",
        "model_validator",
        "field_validator",
        "field_serializer",
        "computed_field",
        "Field",
        "ValidationError",
        "AliasChoices",
        "EmailStr",
        "HttpUrl",
        "confloat",
        "conint",
    ]

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

    def field_serializer(
        *_fields: str, **_kwargs: Any
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Stub ``field_serializer`` decorator that leaves the function unchanged."""

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            return func

        return decorator

    def computed_field(*_args: Any, **_kwargs: Any) -> Callable[[Callable[..., Any]], property]:
        """Stub ``computed_field`` decorator producing a property."""

        def decorator(func: Callable[..., Any]) -> property:
            return property(func)

        return decorator

    class ValidationError(Exception):
        """Lightweight ValidationError stub exposing ``errors``."""

        def __init__(self, errors: Iterable[dict[str, Any]] | None = None):
            super().__init__("Validation error")
            self._errors = list(errors or [])

        def errors(self) -> list[dict[str, Any]]:
            return list(self._errors)

    def _to_camel(string: str) -> str:
        parts = string.split("_")
        return parts[0] + "".join(part.title() for part in parts[1:])

    alias_generators = ModuleType("pydantic.alias_generators")
    alias_generators.to_camel = _to_camel
    sys.modules.setdefault("pydantic.alias_generators", alias_generators)

    class AliasChoices:
        """Stub for :class:`pydantic.AliasChoices` accepting any values."""

        def __init__(self, *choices: str) -> None:
            self.choices = choices

    class EmailStr(str):
        """Very small substitute for :class:`pydantic.EmailStr`."""

        @classmethod
        def validate(cls, value: str) -> "EmailStr":
            return cls(value)

    class HttpUrl(str):
        """Simplified URL type used only for validation placeholders."""

        @classmethod
        def validate(cls, value: str) -> "HttpUrl":
            return cls(value)

    def confloat(**_kwargs: Any) -> type:
        """Return a constrained float subtype placeholder."""

        class _ConstrainedFloat(float):
            pass

        return _ConstrainedFloat

    def conint(**_kwargs: Any) -> type:
        """Return a constrained int subtype placeholder."""

        class _ConstrainedInt(int):
            pass

        return _ConstrainedInt

    class AttrDict(dict):
        """Dict that also provides attribute-style access."""

        def __getattr__(self, key: str) -> Any:
            try:
                return self[key]
            except KeyError as exc:  # pragma: no cover - attribute missing
                raise AttributeError(key) from exc

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
                if isinstance(value, dict):
                    value = AttrDict(value)
                setattr(self, name, value)
            for key, value in data.items():
                if isinstance(value, dict):
                    value = AttrDict(value)
                setattr(self, key, value)
            for mode, validator in getattr(self, "_model_validators", []):
                func = validator.__func__ if isinstance(validator, classmethod) else validator
                if mode == "after":
                    result = func(self.__class__, self)
                    if result is not None and result is not self:
                        if isinstance(result, BaseModel):
                            for key, value in result.__dict__.items():
                                setattr(self, key, value)
                        else:
                            raise TypeError("Validators must return the model instance")
                else:
                    func(self.__class__, self)

        def model_dump(self, *, mode: str | None = None) -> Dict[str, Any]:
            def _convert(value: Any) -> Any:
                if isinstance(value, BaseModel):
                    return value.model_dump()
                if isinstance(value, AttrDict):
                    return {k: _convert(v) for k, v in value.items()}
                if isinstance(value, (list, tuple)):
                    return [_convert(v) for v in value]
                if isinstance(value, datetime):
                    return value.isoformat()
                return value

            return {k: _convert(v) for k, v in self.__dict__.items()}

        @classmethod
        def model_validate(cls, data: Dict[str, Any], **_kwargs: Any) -> "BaseModel":
            if not isinstance(data, dict):
                try:
                    data = dict(data.__dict__)
                except Exception:
                    data = {key: getattr(data, key) for key in dir(data) if not key.startswith("_")}
            return cls(**data)

        @classmethod
        def model_rebuild(cls, *args: Any, **kwargs: Any) -> None:
            return None
