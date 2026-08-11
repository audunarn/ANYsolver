import contextlib
import contextvars
import threading

import numpy as np
import pytest
from scipy import sparse

import anysolver.threading_policy as policy_module
from anysolver.jit_compiler import JIT_ENABLED, numba_thread_scope
from anysolver.linalg import MatrixClass, factorize
from anysolver.assembly import solve_linear
from anysolver.boundary import LoadCase
from anysolver.mesh_gen import generate_beam_mesh
from anysolver.recovery import ResourceConfig
from anysolver.threading_policy import native_thread_scope


def pool_counts(pools):
    return [pool["num_threads"] for pool in pools if pool["num_threads"] is not None]


@pytest.mark.parametrize("threads", [1, 2, 4])
def test_native_thread_limits_are_active_and_restored(threads):
    with native_thread_scope(threads, phase="test") as report:
        assert report["status"] in {"limited", "backend_unavailable"}
        if report["limiter_available"]:
            assert all(count == threads for count in pool_counts(report["pools_active"]))
    assert report["restored"]
    assert pool_counts(report["pools_after"]) == pool_counts(report["pools_before"])


def test_native_thread_limit_restores_after_exception():
    report = None
    with pytest.raises(RuntimeError):
        with native_thread_scope(1, phase="exception") as active:
            report = active
            raise RuntimeError("expected")
    assert report is not None and report["restored"]
    assert pool_counts(report["pools_after"]) == pool_counts(report["pools_before"])


def test_factorization_and_solve_record_effective_policy():
    matrix = sparse.csr_matrix([[4.0, 1.0], [1.0, 3.0]])
    handle = factorize(matrix, MatrixClass.SPD, options={"solver_threads": 2})
    result = handle.solve(np.array([1.0, 2.0]))
    assert np.allclose(matrix @ result, [1.0, 2.0])
    diagnostics = handle.diagnostics()
    assert diagnostics["thread_policy"]["requested_threads"] == 2
    assert diagnostics["last_solve_thread_policy"]["requested_threads"] == 2
    assert diagnostics["backend"]


def test_unlimited_default_is_unchanged():
    with native_thread_scope(None, phase="default") as report:
        assert report["status"] == "unlimited_default"
        assert report["requested_threads"] is None


def test_public_solver_applies_and_reports_resource_config():
    model = generate_beam_mesh(1.0, num_divisions=1)
    load = LoadCase("tip")
    load.add_nodal_load(2, [1.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    displacement, info = solve_linear(
        model,
        load,
        resource_config=ResourceConfig(solver_threads=2, assembly_threads=4),
    )
    assert np.all(np.isfinite(displacement))
    assert info["thread_policy"]["requested_solver_threads"] == 2
    assert info["thread_policy"]["requested_assembly_threads"] == 4
    backend = info["convergence_info"]["backend"]
    assert backend["thread_policy"]["requested_threads"] == 2
    assert backend["last_solve_thread_policy"]["requested_threads"] == 2


def test_backend_unavailable_is_reported(monkeypatch):
    monkeypatch.setattr(policy_module, "_HAS_THREADPOOLCTL", False)
    monkeypatch.setattr(policy_module, "_THREADPOOLCTL_ERROR", "isolated unavailable")
    with native_thread_scope(2, phase="fallback") as report:
        assert report["status"] == "backend_unavailable"
        assert report["fallback_reason"] == "isolated unavailable"


def test_overlapping_explicit_native_limits_are_serialized(monkeypatch):
    first_entered = threading.Event()
    release_first = threading.Event()
    second_entered = threading.Event()
    errors = []

    @contextlib.contextmanager
    def fake_limits(*, limits):
        del limits
        yield

    monkeypatch.setattr(policy_module, "_HAS_THREADPOOLCTL", True)
    monkeypatch.setattr(policy_module, "threadpool_limits", fake_limits)
    monkeypatch.setattr(policy_module, "_pool_snapshot", lambda: [])

    def worker(name):
        try:
            with native_thread_scope(1, phase=name):
                if name == "first":
                    first_entered.set()
                    assert release_first.wait(timeout=2.0)
                else:
                    second_entered.set()
        except BaseException as exc:  # pragma: no cover - surfaced below
            errors.append(exc)

    first = threading.Thread(target=worker, args=("first",))
    second = threading.Thread(target=worker, args=("second",))
    first.start()
    assert first_entered.wait(timeout=2.0)
    second.start()
    assert not second_entered.wait(timeout=0.1)
    release_first.set()
    first.join(timeout=2.0)
    second.join(timeout=2.0)

    assert not first.is_alive()
    assert not second.is_alive()
    assert second_entered.is_set()
    assert errors == []


def test_unlimited_default_native_scopes_can_overlap():
    rendezvous = threading.Barrier(2)
    errors = []

    def worker():
        try:
            with native_thread_scope(None, phase="concurrent_default") as report:
                assert report["status"] == "unlimited_default"
                rendezvous.wait(timeout=2.0)
        except BaseException as exc:  # pragma: no cover - surfaced below
            errors.append(exc)

    workers = [threading.Thread(target=worker) for _ in range(2)]
    for worker_thread in workers:
        worker_thread.start()
    for worker_thread in workers:
        worker_thread.join(timeout=2.0)

    assert all(not worker_thread.is_alive() for worker_thread in workers)
    assert errors == []


def test_default_scope_can_upgrade_to_explicit_limit_and_restore():
    with native_thread_scope(None, phase="outer_default") as outer:
        with native_thread_scope(1, phase="inner_explicit") as inner:
            assert inner["status"] in {"limited", "backend_unavailable"}
        assert inner["restored"] is True
        assert outer["restored"] is False
    assert outer["restored"] is True


def test_snapshot_failure_does_not_strand_native_scope_coordinator(monkeypatch):
    def fail_snapshot():
        raise RuntimeError("isolated snapshot failure")

    monkeypatch.setattr(policy_module, "_pool_snapshot", fail_snapshot)
    with pytest.raises(RuntimeError, match="isolated snapshot failure"):
        with native_thread_scope(1, phase="snapshot_failure"):
            pass

    monkeypatch.setattr(policy_module, "_pool_snapshot", lambda: [])
    with native_thread_scope(1, phase="after_snapshot_failure") as report:
        assert report["status"] in {"limited", "backend_unavailable"}
    assert report["restored"] is True


def test_copied_context_cannot_inherit_another_threads_native_limit():
    child_started = threading.Event()
    child_entered = threading.Event()
    child_status = []

    def child():
        child_started.set()
        with native_thread_scope(1, phase="copied_context_child") as report:
            child_status.append(report["status"])
            child_entered.set()

    with native_thread_scope(1, phase="copied_context_parent"):
        copied_context = contextvars.copy_context()
        worker = threading.Thread(target=lambda: copied_context.run(child))
        worker.start()
        assert child_started.wait(timeout=2.0)
        assert not child_entered.wait(timeout=0.1)

    worker.join(timeout=2.0)
    assert not worker.is_alive()
    assert child_entered.is_set()
    assert child_status[0] in {"limited", "backend_unavailable"}


@pytest.mark.skipif(not JIT_ENABLED, reason="Numba is not installed")
def test_parallel_numba_scope_suppresses_nested_native_pools():
    with numba_thread_scope(2) as report:
        assert report["requested_numba_threads"] == 2
        assert report["active_numba_threads"] == 2
        if report["limiter_available"]:
            assert all(count == 1 for count in pool_counts(report["pools_active"]))
