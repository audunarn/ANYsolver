"""Scoped native/solver thread controls with observable diagnostics."""

from __future__ import annotations

import contextlib
import contextvars
import functools
import inspect
from typing import Any, Callable, Dict, Iterator, Mapping, Optional, TypeVar

try:
    from threadpoolctl import threadpool_info, threadpool_limits

    _HAS_THREADPOOLCTL = True
    _THREADPOOLCTL_ERROR: Optional[str] = None
except ImportError as exc:  # pragma: no cover - exercised in isolated tests
    threadpool_info = None  # type: ignore[assignment]
    threadpool_limits = None  # type: ignore[assignment]
    _HAS_THREADPOOLCTL = False
    _THREADPOOLCTL_ERROR = str(exc)


F = TypeVar("F", bound=Callable[..., Any])
_SOLVER_THREADS: contextvars.ContextVar[Optional[int]] = contextvars.ContextVar(
    "anysolver_solver_threads", default=None
)
_ACTIVE_NATIVE_LIMIT: contextvars.ContextVar[Optional[int]] = contextvars.ContextVar(
    "anysolver_active_native_limit", default=None
)


def _pool_snapshot() -> list[Dict[str, Any]]:
    if not _HAS_THREADPOOLCTL or threadpool_info is None:
        return []
    pools = []
    for pool in threadpool_info():
        pools.append(
            {
                "user_api": pool.get("user_api"),
                "internal_api": pool.get("internal_api"),
                "prefix": pool.get("prefix"),
                "num_threads": pool.get("num_threads"),
                "version": pool.get("version"),
            }
        )
    return pools


def current_solver_threads() -> Optional[int]:
    """Return the solver-thread limit active in the current context."""

    return _SOLVER_THREADS.get()


@contextlib.contextmanager
def native_thread_scope(
    requested_threads: Optional[int], *, phase: str
) -> Iterator[Dict[str, Any]]:
    """Temporarily limit BLAS/OpenMP pools and expose the effective policy."""

    requested = None if requested_threads is None else int(requested_threads)
    if requested is not None and requested <= 0:
        raise ValueError("requested_threads must be positive when provided")
    report: Dict[str, Any] = {
        "phase": str(phase),
        "requested_threads": requested,
        "limiter_available": _HAS_THREADPOOLCTL,
        "fallback_reason": _THREADPOOLCTL_ERROR,
        "pools_before": [] if requested is None else _pool_snapshot(),
        "pools_active": [],
        "pools_after": [],
        "restored": False,
    }
    if requested is None:
        report["status"] = "unlimited_default"
        try:
            yield report
        finally:
            report["restored"] = True
        return
    if _ACTIVE_NATIVE_LIMIT.get() == requested:
        report["status"] = "inherited_limit"
        try:
            yield report
        finally:
            report["restored"] = True
        return
    if not _HAS_THREADPOOLCTL or threadpool_limits is None:
        report["status"] = "backend_unavailable"
        report["fallback_reason"] = _THREADPOOLCTL_ERROR or "threadpoolctl unavailable"
        try:
            yield report
        finally:
            report["pools_after"] = _pool_snapshot()
            report["restored"] = True
        return
    token = _ACTIVE_NATIVE_LIMIT.set(requested)
    try:
        with threadpool_limits(limits=requested):
            report["status"] = "limited"
            report["pools_active"] = _pool_snapshot()
            yield report
    finally:
        report["pools_after"] = _pool_snapshot()
        report["restored"] = True
        _ACTIVE_NATIVE_LIMIT.reset(token)


@contextlib.contextmanager
def solver_thread_scope(resource_config: Any) -> Iterator[Dict[str, Any]]:
    """Apply ``ResourceConfig.solver_threads`` for a complete solver call."""

    requested = current_solver_threads() if resource_config is None else resource_config.solver_threads
    token = _SOLVER_THREADS.set(None if requested is None else int(requested))
    try:
        with native_thread_scope(requested, phase="solver") as report:
            yield report
    finally:
        _SOLVER_THREADS.reset(token)


def _resource_config_from_call(func: F, args: tuple[Any, ...], kwargs: Mapping[str, Any]) -> Any:
    bound = inspect.signature(func).bind_partial(*args, **kwargs)
    config = bound.arguments.get("resource_config")
    if config is not None:
        return config
    for name in ("config", "transient_config"):
        container = bound.arguments.get(name)
        if container is not None and getattr(container, "resource_config", None) is not None:
            return container.resource_config
    return None


def resource_threaded(func: F) -> F:
    """Decorate a public solver while preserving its callable signature."""

    @functools.wraps(func)
    def wrapped(*args: Any, **kwargs: Any):
        resource_config = _resource_config_from_call(func, args, kwargs)
        with solver_thread_scope(resource_config):
            return func(*args, **kwargs)

    return wrapped  # type: ignore[return-value]


def thread_policy_diagnostics(resource_config: Any = None) -> Dict[str, Any]:
    """Return requested settings and currently detected native pools."""

    return {
        "requested_solver_threads": (
            None if resource_config is None else resource_config.solver_threads
        ),
        "requested_assembly_threads": (
            None if resource_config is None else resource_config.assembly_threads
        ),
        "active_solver_threads": current_solver_threads(),
        "limiter_available": _HAS_THREADPOOLCTL,
        "fallback_reason": _THREADPOOLCTL_ERROR,
        "runtime_pools": _pool_snapshot(),
    }
