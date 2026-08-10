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


@pytest.mark.skipif(not JIT_ENABLED, reason="Numba is not installed")
def test_parallel_numba_scope_suppresses_nested_native_pools():
    with numba_thread_scope(2) as report:
        assert report["requested_numba_threads"] == 2
        assert report["active_numba_threads"] == 2
        if report["limiter_available"]:
            assert all(count == 1 for count in pool_counts(report["pools_active"]))
