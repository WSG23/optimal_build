"""Lightweight subset of the Pydantic API used in the tests."""

from __future__ import annotations

import inspect
import json
from collections.abc import Callable, Iterable, Mapping, MutableMapping, MutableSequence, Sequence
from datetime import date, datetime
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

T = TypeVar("T")


class HttpUrl(str):
    """Simplified representation of :class:`pydantic.HttpUrl`."""


def _build_constrained_number(
    base_type: type[T], *, ge: float | None = None, le: float | None = None
) -> type[T]:
    class Constrained(base_type):  # type: ignore[misc]
        def __new__(cls, value: Any) -> T:  # type: ignore[override]
            try:
                converted = base_type(value)  # type: ignore[arg-type]
            except Exception as exc:  # pragma: no cover - defensive
                raise ValidationError(str(exc)) from exc
            if ge is not None and converted < ge:
                raise ValidationError(f"value must be >= {ge}")
            if le is not None and converted > le:
                raise ValidationError(f"value must be <= {le}")
            return base_type.__new__(cls, converted)  # type: ignore[call-arg]

    Constrained.ge = ge  # type: ignore[attr-defined]
    Constrained.le = le  # type: ignore[attr-defined]
    return Constrained


def conint(*, ge: int | None = None, le: int | None = None) -> type[int]:
    """Return a constrained integer type."""

    return _build_constrained_number(int, ge=ge, le=le)


def confloat(*, ge: float | None = None, le: float | None = None) -> type[float]:
    """Return a constrained float type."""

    return _build_constrained_number(float, ge=ge, le=le)


class _Undefined:
    """Sentinel used to represent unspecified defaults."""


Undefined = _Undefined()


@dataclass
class FieldInfo:
    """Metadata attached to model fields."""

    default: Any = Undefined
    default_factory: Callable[[], Any] | None = None
    description: str | None = None
    extra: dict[str, Any] | None = None

    def __post_init__(self) -> None:  # pragma: no cover - trivial initialiser
        if self.extra is None:
            self.extra = {}


def Field(
    default: Any = Undefined,
    *,
    default_factory: Callable[[], Any] | None = None,
    description: str | None = None,
    **kwargs: Any,
) -> FieldInfo:
    """Return metadata describing a model field."""

    if default is ...:
        default = Undefined
    return FieldInfo(
        default=default,
        default_factory=default_factory,
        description=description,
        extra=dict(kwargs) if kwargs else {},
    )


class ValidationError(ValueError):
    """Raised when model validation fails."""


def _is_optional(annotation: Any) -> bool:
    origin = get_origin(annotation)
    if origin is Union:
        return type(None) in get_args(annotation)
    return False


def _strip_optional(annotation: Any) -> Any:
    if get_origin(annotation) is Union:
        args = [arg for arg in get_args(annotation) if arg is not type(None)]
        if len(args) == 1:
            return args[0]
    return annotation


def _build_field(type_annotation: Any, field: FieldInfo) -> FieldInfo:
    field = FieldInfo(
        default=field.default,
        default_factory=field.default_factory,
        description=field.description,
        extra=dict(field.extra or {}),
    )
    field.annotation = type_annotation
    field.required = (
        field.default is Undefined
        and field.default_factory is None
        and not _is_optional(type_annotation)
    )
    return field


def _convert_primitive(value: Any, expected: type[Any]) -> Any:
    if value is None:
        return None
    try:
        if expected is bool:
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                lowered = value.strip().lower()
                if lowered in {"true", "1", "yes", "on"}:
                    return True
                if lowered in {"false", "0", "no", "off"}:
                    return False
            return bool(value)
        if expected in {int, float, str}:
            return expected(value)
        if expected is datetime and isinstance(value, str):
            return datetime.fromisoformat(value)
        if expected is date and isinstance(value, str):
            return date.fromisoformat(value)
    except Exception as exc:  # pragma: no cover - defensive
        raise ValidationError(str(exc)) from exc
    return value


def _convert_value(value: Any, annotation: Any) -> Any:
    if annotation is Any or annotation is inspect._empty:
        return value

    origin = get_origin(annotation)
    if origin is Union:
        if value is None:
            return None
        for arg in get_args(annotation):
            if arg is type(None):
                continue
            try:
                return _convert_value(value, arg)
            except ValidationError:
                continue
        return value

    if origin in {list, list, Sequence, MutableSequence}:  # type: ignore[name-defined]
        item_type = get_args(annotation)[0] if get_args(annotation) else Any
        if value is None:
            return []
        if not isinstance(value, list):
            value = list(value)
        return [_convert_value(item, item_type) for item in value]

    if origin in {dict, dict, Mapping, MutableMapping}:  # type: ignore[name-defined]
        key_type, value_type = (Any, Any)
        if get_args(annotation):
            args = get_args(annotation)
            if len(args) == 2:
                key_type, value_type = args
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise ValidationError("dictionary required")
        return {
            _convert_value(key, key_type) if key_type is not Any else key: (
                _convert_value(item, value_type) if value_type is not Any else item
            )
            for key, item in value.items()
        }

    if inspect.isclass(annotation) and issubclass(annotation, BaseModel):
        if isinstance(value, annotation):
            return value
        if isinstance(value, dict):
            return annotation(**value)
        return annotation.model_validate(value, from_attributes=True)

    if isinstance(annotation, type):
        return _convert_primitive(value, annotation)

    return value


def _apply_field_validators(
    cls: type[BaseModel],
    name: str,
    value: Any,
) -> Any:
    for validator in cls.__field_validators__.get(name, []):
        value = validator(cls, value)
    return value


def _apply_model_validators(
    cls: type[BaseModel], instance: BaseModel
) -> BaseModel:
    for validator in cls.__model_validators__:
        result = validator(cls, instance)
        if isinstance(result, cls):
            instance = result
    return instance


class BaseModelMeta(type):
    """Collect field definitions and validators for :class:`BaseModel`."""

    def __new__(mcls, name, bases, namespace, **kwargs):
        annotations = dict(namespace.get("__annotations__", {}))
        fields: dict[str, FieldInfo] = {}

        for base in reversed(bases):
            if hasattr(base, "model_fields"):
                for field_name, field_info in getattr(base, "model_fields", {}).items():
                    if field_name.startswith("model_") or field_name.startswith("__"):
                        continue
                    fields[field_name] = field_info

        for field_name, annotation in annotations.items():
            if field_name.startswith("model_") or field_name.startswith("__"):
                continue
            default_value = namespace.get(field_name, Undefined)
            if isinstance(default_value, FieldInfo):
                field_info = default_value
                if field_info.default is not Undefined:
                    namespace[field_name] = field_info.default
                elif field_info.default_factory is not None:
                    namespace[field_name] = field_info.default_factory()
                else:
                    namespace.pop(field_name, None)
            else:
                field_info = FieldInfo(default=default_value)
            fields[field_name] = _build_field(annotation, field_info)

        field_validators: dict[str, list[Callable[[type[BaseModel], Any], Any]]] = {}
        model_validators: list[
            Callable[[type[BaseModel], BaseModel], BaseModel]
        ] = []

        for attr_name, attr_value in list(namespace.items()):
            func = None
            if isinstance(attr_value, classmethod):
                func = attr_value.__func__
            elif isinstance(attr_value, staticmethod):
                func = attr_value.__func__
            elif inspect.isfunction(attr_value):
                func = attr_value
            if func is None:
                continue
            info = getattr(func, "__pydantic_field_validator__", None)
            if info:
                for target in info["fields"]:
                    field_validators.setdefault(target, []).append(func)
            info = getattr(func, "__pydantic_model_validator__", None)
            if info:
                model_validators.append(func)

        config = namespace.get("Config")
        model_config: dict[str, Any] = {}
        if config is not None:
            for key in dir(config):
                if key.startswith("_"):
                    continue
                model_config[key] = getattr(config, key)

        namespace["model_fields"] = fields
        namespace["__field_validators__"] = field_validators
        namespace["__model_validators__"] = model_validators
        namespace["model_config"] = model_config

        cls = super().__new__(mcls, name, bases, namespace, **kwargs)

        try:
            resolved = get_type_hints(cls)
        except Exception:
            resolved = {}
        for field_name, annotation in resolved.items():
            field = cls.model_fields.get(field_name)
            if field is not None:
                field.annotation = annotation

        return cls


class BaseModel(metaclass=BaseModelMeta):
    """Small subset of the behaviour of :class:`pydantic.BaseModel`."""

    model_fields: dict[str, FieldInfo]
    __field_validators__: dict[str, list[Callable[[type[BaseModel], Any], Any]]]
    __model_validators__: list[Callable[[type[BaseModel], BaseModel], BaseModel]]
    model_config: dict[str, Any]

    def __init__(self, **data: Any) -> None:
        provided_fields = set(data.keys())
        values: dict[str, Any] = {}
        for name, field in self.model_fields.items():
            if name in data:
                value = data[name]
            elif field.default_factory is not None:
                value = field.default_factory()
            elif field.default is not Undefined:
                value = field.default
            else:
                if _is_optional(field.annotation):
                    value = None
                else:
                    raise ValidationError(f"Field '{name}' is required")

            try:
                value = _convert_value(value, field.annotation)
            except ValidationError:
                raise
            value = _apply_field_validators(type(self), name, value)
            values[name] = value

        object.__setattr__(self, "__dict__", values)
        object.__setattr__(self, "__provided_fields__", provided_fields)
        _apply_model_validators(type(self), self)

    def __setattr__(self, key: str, value: Any) -> None:
        if key in self.model_fields:
            object.__setattr__(self, key, value)
        else:
            raise AttributeError(f"Unknown attribute '{key}'")

    @classmethod
    def model_validate(
        cls: type[T],
        obj: Any,
        *,
        from_attributes: bool = False,
    ) -> T:
        if isinstance(obj, cls):
            return obj
        data: dict[str, Any]
        if isinstance(obj, Mapping):
            data = dict(obj)
        elif from_attributes:
            data = {}
            for name in cls.model_fields:
                if hasattr(obj, name):
                    data[name] = getattr(obj, name)
        else:
            raise ValidationError("Unsupported object for validation")
        return cls(**data)

    def model_dump(
        self,
        *,
        mode: str = "python",
        exclude_unset: bool = False,
    ) -> dict[str, Any]:
        if exclude_unset:
            provided = getattr(self, "__provided_fields__", set())
            items = (
                (name, getattr(self, name))
                for name in self.model_fields
                if name in provided
            )
        else:
            items = ((name, getattr(self, name)) for name in self.model_fields)
        return {name: _dump_value(value, mode) for name, value in items}

    def __repr__(self) -> str:  # pragma: no cover - human-readable convenience
        fields = ", ".join(f"{key}={value!r}" for key, value in self.__dict__.items())
        return f"{self.__class__.__name__}({fields})"


def _dump_value(value: Any, mode: str) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode=mode)
    if isinstance(value, (list, tuple)):
        return [_dump_value(item, mode) for item in value]
    if isinstance(value, dict):
        return {key: _dump_value(val, mode) for key, val in value.items()}
    if mode == "json":
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, date):
            return value.isoformat()
    return value


def field_validator(
    *fields: str, mode: str = "after"
) -> Callable[[Callable[..., Any]], classmethod]:
    """Decorator registering a field level validator."""

    def decorator(func: Callable[..., Any]) -> classmethod:
        underlying = func.__func__ if isinstance(func, classmethod) else func
        underlying.__pydantic_field_validator__ = {"fields": fields, "mode": mode}
        return classmethod(underlying)

    return decorator


def model_validator(
    *, mode: str = "after"
) -> Callable[[Callable[..., Any]], classmethod]:
    """Decorator registering a model level validator."""

    def decorator(func: Callable[..., Any]) -> classmethod:
        underlying = func.__func__ if isinstance(func, classmethod) else func
        underlying.__pydantic_model_validator__ = {"mode": mode}
        return classmethod(underlying)

    return decorator


__all__ = [
    "BaseModel",
    "confloat",
    "conint",
    "HttpUrl",
    "Field",
    "ValidationError",
    "field_validator",
    "model_validator",
]
