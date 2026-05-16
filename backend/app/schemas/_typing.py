"""Typed helpers for strict mypy with Pydantic models."""

from __future__ import annotations

from collections.abc import Mapping
from importlib import import_module
from types import ModuleType
from typing import Any, Literal, TypeVar, cast

from pydantic import BaseModel

ModelT = TypeVar("ModelT", bound=BaseModel)


def typed_import_module(name: str) -> ModuleType:
    return cast(ModuleType, import_module(name))


def validate_model(
    model_cls: type[ModelT],
    value: Any,
    *,
    from_attributes: bool = False,
) -> ModelT:
    if from_attributes:
        return cast(ModelT, model_cls.model_validate(value, from_attributes=True))
    return cast(ModelT, model_cls.model_validate(value))


def dump_model(
    model: BaseModel,
    *,
    mode: Literal["json", "python"] = "python",
    exclude_none: bool = False,
    exclude_unset: bool = False,
    by_alias: bool = False,
) -> dict[str, Any]:
    return cast(
        dict[str, Any],
        cast(Any, model).model_dump(
            mode=mode,
            exclude_none=exclude_none,
            exclude_unset=exclude_unset,
            by_alias=by_alias,
        ),
    )


def copy_model(
    model: ModelT,
    *,
    update: Mapping[str, Any] | None = None,
    deep: bool = False,
) -> ModelT:
    payload = dict(update) if update is not None else None
    return cast(ModelT, cast(Any, model).model_copy(update=payload, deep=deep))
