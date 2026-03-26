"""Small helpers for deferring heavyweight object construction."""

from __future__ import annotations

from threading import Lock
from typing import Any, Callable, Generic, TypeVar, cast

_UNINITIALIZED = object()
T = TypeVar("T")


class LazyProxy(Generic[T]):
    """Resolve an object on first attribute access and cache the instance."""

    __slots__ = ("_factory", "_instance", "_lock")

    def __init__(self, factory: Callable[[], T]) -> None:
        object.__setattr__(self, "_factory", factory)
        object.__setattr__(self, "_instance", _UNINITIALIZED)
        object.__setattr__(self, "_lock", Lock())

    @property
    def initialized(self) -> bool:
        """Return whether the target object has already been created."""

        return object.__getattribute__(self, "_instance") is not _UNINITIALIZED

    @property
    def instance(self) -> T:
        """Return the cached target instance, creating it on first use."""

        instance = object.__getattribute__(self, "_instance")
        if instance is _UNINITIALIZED:
            lock = object.__getattribute__(self, "_lock")
            with lock:
                instance = object.__getattribute__(self, "_instance")
                if instance is _UNINITIALIZED:
                    factory = object.__getattribute__(self, "_factory")
                    instance = factory()
                    object.__setattr__(self, "_instance", instance)
        return cast(T, instance)

    def __getattr__(self, name: str) -> Any:
        return getattr(self.instance, name)

    def __setattr__(self, name: str, value: Any) -> None:
        if name in self.__slots__:
            object.__setattr__(self, name, value)
            return
        setattr(self.instance, name, value)

    def __repr__(self) -> str:
        if not self.initialized:
            return "LazyProxy(<uninitialized>)"
        return repr(self.instance)


__all__ = ["LazyProxy"]
