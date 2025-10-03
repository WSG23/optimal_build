"""Minimal backport to evaluate modern typing syntax on Python <3.10."""

from __future__ import annotations

import typing

__all__ = ["eval_type_backport"]


def _build_union_expression(parts: list[str]) -> str:
    optional = "None" in parts
    filtered = [part for part in parts if part != "None"]
    if optional:
        if not filtered:
            return "type(None)"
        inner = (
            filtered[0]
            if len(filtered) == 1
            else f"typing.Union[{', '.join(filtered)}]"
        )
        return f"typing.Optional[{inner}]"
    if len(parts) == 1:
        return parts[0]
    return f"typing.Union[{', '.join(parts)}]"


def _normalise_expression(expr: str) -> str:
    expr = expr.strip()
    if "|" not in expr:
        return expr
    parts: list[str] = [part.strip() for part in expr.split("|") if part.strip()]
    return _build_union_expression(parts)


def eval_type_backport(
    value: typing.ForwardRef | str,
    globalns: dict[str, typing.Any] | None = None,
    localns: dict[str, typing.Any] | None = None,
    type_params: tuple[typing.Any, ...] | None = None,
    **_: typing.Any,
):
    """Evaluate forward reference expressions containing modern typing syntax."""

    namespace: dict[str, typing.Any] = {}
    if globalns:
        namespace.update(globalns)
    namespace.setdefault("typing", typing)
    namespace.setdefault("__builtins__", __builtins__)

    if localns:
        namespace.update(localns)

    if isinstance(value, typing.ForwardRef):
        expr = value.__forward_arg__
    else:
        expr = str(value)

    expr = _normalise_expression(expr)

    try:
        return eval(expr, namespace, {})
    except Exception:  # pragma: no cover - fallback for unsupported constructs
        return typing.Any
