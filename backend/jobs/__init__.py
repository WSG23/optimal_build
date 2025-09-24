"""Background job infrastructure and helpers."""

from __future__ import annotations

import asyncio
import inspect
import os
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, Mapping, Optional, Tuple

try:  # pragma: no cover - optional dependency, available in some deployments
    from celery import Celery  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - keep inline fallback working
    Celery = None  # type: ignore[assignment]

try:  # pragma: no cover - optional dependency, available in some deployments
    from redis import Redis  # type: ignore
    from rq import Queue  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - keep inline fallback working
    Redis = None  # type: ignore[assignment]
    Queue = None  # type: ignore[assignment]

from app.core.config import settings

JobFunc = Callable[..., Awaitable[Any] | Any]


@dataclass(slots=True)
class JobDispatch:
    """Metadata describing a scheduled job."""

    backend: str
    job_name: str
    queue: Optional[str]
    status: str
    task_id: Optional[str] = None
    result: Any | None = None

    def as_dict(self) -> Dict[str, Any]:
        """Return a JSON serialisable representation."""

        payload: Dict[str, Any] = {
            "backend": self.backend,
            "job_name": self.job_name,
            "queue": self.queue,
            "status": self.status,
        }
        if self.task_id:
            payload["task_id"] = self.task_id
        if self.result is not None:
            payload["result"] = self.result
        return payload


class _BaseBackend:
    """Protocol implemented by queue backends."""

    name: str

    def register(self, func: JobFunc, name: str, queue: Optional[str]) -> JobFunc:
        raise NotImplementedError

    async def enqueue(
        self,
        name: str,
        queue: Optional[str],
        args: Tuple[Any, ...],
        kwargs: Mapping[str, Any],
    ) -> JobDispatch:
        raise NotImplementedError


class _InlineBackend(_BaseBackend):
    """Execute jobs synchronously in the current event loop."""

    name = "inline"

    def __init__(self) -> None:
        self._registry: Dict[str, Tuple[JobFunc, Optional[str]]] = {}

    def register(self, func: JobFunc, name: str, queue: Optional[str]) -> JobFunc:
        self._registry[name] = (func, queue)
        return func

    async def enqueue(
        self,
        name: str,
        queue: Optional[str],
        args: Tuple[Any, ...],
        kwargs: Mapping[str, Any],
    ) -> JobDispatch:
        if name not in self._registry:
            raise KeyError(f"Job '{name}' is not registered")
        func, registered_queue = self._registry[name]
        result = func(*args, **kwargs)
        if inspect.isawaitable(result):
            result = await result  # type: ignore[assignment]
        return JobDispatch(
            backend=self.name,
            job_name=name,
            queue=registered_queue or queue,
            status="completed",
            result=result,
        )


class _CeleryBackend(
    _BaseBackend
):  # pragma: no cover - executed when celery is installed
    name = "celery"

    def __init__(self) -> None:
        if Celery is None:  # pragma: no cover - defensive guard
            raise RuntimeError("Celery backend requested but celery is not installed")
        self.app = Celery(
            "optimal_build_jobs",
            broker=settings.CELERY_BROKER_URL,
            backend=settings.CELERY_RESULT_BACKEND,
        )
        self._registry: Dict[str, Tuple[JobFunc, Optional[str]]] = {}

    def register(self, func: JobFunc, name: str, queue: Optional[str]) -> JobFunc:
        task = self.app.task(name=name, bind=False)(func)
        self._registry[name] = (task, queue)
        return task

    async def enqueue(
        self,
        name: str,
        queue: Optional[str],
        args: Tuple[Any, ...],
        kwargs: Mapping[str, Any],
    ) -> JobDispatch:
        if name not in self._registry:
            raise KeyError(f"Job '{name}' is not registered")
        _, registered_queue = self._registry[name]
        selected_queue = queue or registered_queue
        async_result = await asyncio.to_thread(
            self.app.send_task,
            name,
            args=args,
            kwargs=dict(kwargs),
            queue=selected_queue,
        )
        return JobDispatch(
            backend=self.name,
            job_name=name,
            queue=selected_queue,
            status="queued",
            task_id=getattr(async_result, "id", None),
        )


class _RQBackend(
    _BaseBackend
):  # pragma: no cover - executed when rq/redis are installed
    name = "rq"

    def __init__(self) -> None:
        if Queue is None or Redis is None:  # pragma: no cover - defensive guard
            raise RuntimeError("RQ backend requested but rq/redis are not installed")
        self.redis = Redis.from_url(settings.RQ_REDIS_URL)
        self._queues: Dict[str, Queue] = {}
        self._registry: Dict[str, Tuple[JobFunc, Optional[str]]] = {}

    def _get_queue(self, queue_name: Optional[str]) -> Queue:
        name = queue_name or "default"
        if name not in self._queues:
            self._queues[name] = Queue(name, connection=self.redis)
        return self._queues[name]

    def register(self, func: JobFunc, name: str, queue: Optional[str]) -> JobFunc:
        self._registry[name] = (func, queue)
        return func

    async def enqueue(
        self,
        name: str,
        queue: Optional[str],
        args: Tuple[Any, ...],
        kwargs: Mapping[str, Any],
    ) -> JobDispatch:
        if name not in self._registry:
            raise KeyError(f"Job '{name}' is not registered")
        func, registered_queue = self._registry[name]
        target_queue = self._get_queue(queue or registered_queue)
        job = await asyncio.to_thread(target_queue.enqueue, func, *args, **dict(kwargs))
        return JobDispatch(
            backend=self.name,
            job_name=name,
            queue=target_queue.name,
            status="queued",
            task_id=getattr(job, "id", None),
        )


def _select_backend() -> _BaseBackend:
    """Choose a backend based on configuration and installed libraries."""

    preferred = os.getenv("JOB_QUEUE_BACKEND", "").strip().lower()
    if preferred == "celery" and Celery is not None:
        return _CeleryBackend()
    if preferred == "rq" and Queue is not None and Redis is not None:
        return _RQBackend()
    if Celery is not None:
        try:
            return _CeleryBackend()
        except Exception:  # pragma: no cover - celery misconfiguration fallback
            pass
    if Queue is not None and Redis is not None:
        try:
            return _RQBackend()
        except Exception:  # pragma: no cover - rq misconfiguration fallback
            pass
    return _InlineBackend()


class JobQueue:
    """Facade encapsulating dispatch to the configured backend."""

    def __init__(self) -> None:
        object.__setattr__(self, "_enqueue_proxy_depth", 0)
        self._backend = _select_backend()
        self._queues: Dict[str, Optional[str]] = {}

    def __setattr__(self, name: str, value: Any) -> None:
        """Allow tests to replace ``enqueue`` without mutating the class."""

        if name == "enqueue":
            if (
                hasattr(value, "__func__")
                and getattr(value, "__func__", None) is type(self).enqueue
            ):
                self.__dict__.pop("enqueue", None)
            else:
                self.__dict__["enqueue"] = value
            return
        object.__setattr__(self, name, value)

    def __getattribute__(self, name: str) -> Any:
        if name == "enqueue":
            instance_value = self.__dict__.get("enqueue")
            if instance_value is not None:
                return instance_value
        return object.__getattribute__(self, name)

    def __delattr__(self, name: str) -> None:
        if name == "enqueue":
            self.__dict__.pop("enqueue", None)
            return
        object.__delattr__(self, name)

    @property
    def backend_name(self) -> str:
        """Return the name of the active backend."""

        return self._backend.name

    def register(self, func: JobFunc, name: str, queue: Optional[str]) -> JobFunc:
        """Register a function with the backend."""

        registered = self._backend.register(func, name, queue)
        self._queues[name] = queue
        return registered

    async def enqueue(
        self,
        job: str | JobFunc,
        *args: Any,
        queue: Optional[str] = None,
        **kwargs: Any,
    ) -> JobDispatch:
        """Enqueue a job identified by name or by callable."""

        proxy = self.__dict__.get("enqueue")
        if proxy is not None:
            depth = object.__getattribute__(self, "_enqueue_proxy_depth")
            if depth == 0:
                object.__setattr__(self, "_enqueue_proxy_depth", depth + 1)
                try:
                    result = proxy(job, *args, queue=queue, **kwargs)
                    if inspect.isawaitable(result):
                        result = await result  # type: ignore[assignment]
                    return result  # type: ignore[return-value]
                finally:
                    object.__setattr__(self, "_enqueue_proxy_depth", depth)
        if callable(job):
            job_name = getattr(job, "job_name", None)
            if not job_name:
                job_name = f"{job.__module__}.{job.__qualname__}"
        else:
            job_name = job
        return await self._backend.enqueue(
            job_name, queue or self._queues.get(job_name), args, kwargs
        )


job_queue = JobQueue()


def job(
    name: Optional[str] = None, *, queue: Optional[str] = None
) -> Callable[[JobFunc], JobFunc]:
    """Decorator used to register job functions with the active backend."""

    def decorator(func: JobFunc) -> JobFunc:
        task_name = name or f"{func.__module__}.{func.__qualname__}"
        registered = job_queue.register(func, task_name, queue)
        setattr(registered, "job_name", task_name)
        setattr(registered, "job_queue", job_queue)
        return registered

    return decorator


celery_app = (
    job_queue._backend.app if isinstance(job_queue._backend, _CeleryBackend) else None
)


__all__ = ["JobDispatch", "JobQueue", "job", "job_queue", "celery_app"]
