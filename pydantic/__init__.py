"""Minimal subset of Pydantic used for tests."""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Tuple

__all__ = ["BaseModel", "model_validator", "field_validator", "Field"]


def Field(default: Any = None, **_: Any) -> Any:
    """Return the provided default value."""

    return default


def model_validator(*, mode: str = "after") -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator registering a model-level validator."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        setattr(func, "__model_validator__", {"mode": mode})
        return func

    return decorator


def field_validator(*_fields: str, **_kwargs: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Stub ``field_validator`` decorator that leaves the function unchanged."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        return func

    return decorator


class _ModelMeta(type):
    def __new__(mcls, name: str, bases: Tuple[type, ...], namespace: Dict[str, Any]) -> "_ModelMeta":
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


__all__ = ["BaseModel", "model_validator", "field_validator", "Field"]
