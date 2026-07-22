"""Infrastructure checks for the SESTRA-inspired FE solver batch."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
from scipy import sparse

import anysolver
import anysolver.linalg as linalg
from anysolver import (
    AssemblyError,
    FactorizationCache,
    LoadCase,
    MatrixClass,
    TransientConfig,
    assemble_load_matrix,
    assemble_stiffness_matrix,
    create_fe_result,
    factorize,
    factorize_cached,
    generate_beam_mesh,
    run_infrastructure_benchmarks,
    solve_linear,
    solve_linear_many,
    solve_transient_newmark,
)
from anysolver.assembly import build_constraint_transformation, build_reduced_rigid_body_modes
from anysolver.baselines import compare_baseline_documents, generate_baseline_document
from anysolver.linalg import _HAS_PYPARDISO, AutoSparseSolverBackend
from anysolver.boundary import BoundaryCondition, FixedSupport
from anysolver.buckling import solve_eigenvalue_buckling
from anysolver.elements import BeamElement
from anysolver.fe_core import FEModel
from anysolver.nonlinear_static import solve_static_nonlinear


def test_public_all_symbols_importable() -> None:
    missing = [name for name in anysolver.__all__ if not hasattr(anysolver, name)]
    assert missing == []


def test_sparse_backend_solves_spd_indefinite_many_and_reports_failure() -> None:
    A = sparse.csr_matrix([[4.0, 1.0], [1.0, 3.0]])
    handle = factorize(A, MatrixClass.SPD, signature="spd_test")
    x = handle.solve(np.array([1.0, 2.0]))
    np.testing.assert_allclose(A @ x, [1.0, 2.0])

    rhs_many = np.eye(2)
    X = handle.solve_many(rhs_many)
    np.testing.assert_allclose(A @ X, rhs_many)
    diagnostics = handle.diagnostics()
    assert diagnostics["backend"] in ("scipy_superlu", "pypardiso")
    assert diagnostics["matrix_class"] == MatrixClass.SPD.value
    assert diagnostics["factorization_count"] == 1
    assert diagnostics["solve_count"] == 3

    augmented = sparse.csr_matrix([[0.0, 1.0], [1.0, 0.0]])
    indefinite = factorize(augmented, MatrixClass.SYMMETRIC_INDEFINITE)
    np.testing.assert_allclose(augmented @ indefinite.solve(np.array([2.0, 5.0])), [2.0, 5.0])

    singular = factorize(sparse.csr_matrix((2, 2)), MatrixClass.SYMMETRIC_SEMIDEFINITE)
    assert singular.status == "failed"
    assert singular.failure_reason


def test_default_sparse_backend_uses_superlu_for_small_matrices_and_can_force_pypardiso() -> None:
    A = sparse.csr_matrix([[4.0, 1.0], [1.0, 3.0]])

    default_handle = factorize(A, MatrixClass.SPD)
    assert default_handle.backend_name == "scipy_superlu"
    assert default_handle.metadata["auto_backend_policy"] == "scipy_small_matrix"

    forced = factorize(A, MatrixClass.SPD, options={"backend": "pypardiso"})
    assert forced.backend_name in ("pypardiso", "scipy_superlu")
    if _HAS_PYPARDISO and forced.backend_name == "pypardiso":
        assert forced.metadata["auto_backend_policy"] == "pypardiso_large_matrix"
    elif _HAS_PYPARDISO:
        assert forced.metadata["auto_backend_policy"] == "scipy_after_pypardiso_failure"
    else:
        assert forced.metadata["auto_backend_policy"] == "scipy_small_matrix"


def test_pypardiso_backend_symmetric_mtypes_pattern_reuse_and_stale_handles() -> None:
    if not _HAS_PYPARDISO:
        pytest.skip("pypardiso not installed")
    from anysolver.linalg import PyPardisoSolverBackend

    backend = PyPardisoSolverBackend(max_pattern_slots=2)
    rng = np.random.default_rng(0)
    n = 60
    lower = sparse.random(n, n, density=0.08, random_state=rng, format="csr")
    A = (lower + lower.T + sparse.eye(n) * float(n)).tocsr()
    b = rng.random(n)

    first = backend.factorize(A, MatrixClass.SPD, signature="pattern:v1")
    assert first.status == "ok"
    assert first.metadata["pardiso_mtype"] in (2, -2)
    assert first.metadata["pardiso_symbolic_reused"] is False
    x_first = first.solve(b)
    np.testing.assert_allclose(A @ x_first, b, atol=1.0e-8)

    A_scaled = (A * 1.5).tocsr()
    second = backend.factorize(A_scaled, MatrixClass.SPD, signature="pattern:v2")
    assert second.status == "ok"
    assert second.metadata["pardiso_symbolic_reused"] is True
    np.testing.assert_allclose(A_scaled @ second.solve(b), b, atol=1.0e-8)

    # The first handle's slot was refactorized for A_scaled; solving through
    # the stale handle must transparently rebuild and stay correct for A.
    np.testing.assert_allclose(A @ first.solve(b), b, atol=1.0e-8)
    assert first._solver.stale_rebuild_count == 1

    indefinite = sparse.csr_matrix([[0.0, 1.0], [1.0, 0.0]])
    handle_indef = backend.factorize(indefinite, MatrixClass.SYMMETRIC_INDEFINITE)
    assert handle_indef.status == "ok"
    np.testing.assert_allclose(indefinite @ handle_indef.solve(np.array([2.0, 5.0])), [2.0, 5.0], atol=1.0e-10)

    backend.release_pattern_slots()
    assert backend._slots == []
    # Handles remain usable after slot release via private rebuild.
    np.testing.assert_allclose(A_scaled @ second.solve(b), b, atol=1.0e-8)


def test_auto_sparse_backend_thresholds_are_environment_tunable(monkeypatch) -> None:
    monkeypatch.setenv("FE_SOLVER_PYPARDISO_MIN_DIMENSION", "123")
    monkeypatch.setenv("FE_SOLVER_PYPARDISO_MIN_NNZ", "456")
    backend = AutoSparseSolverBackend()
    assert backend.pypardiso_min_dimension == 123
    assert backend.pypardiso_min_nnz == 456

    A = sparse.eye(4, format="csr")
    handle = factorize(A, MatrixClass.SPD, backend=backend)
    assert handle.metadata["pypardiso_min_dimension"] == 123
    assert handle.metadata["pypardiso_min_nnz"] == 456


def test_factorization_cache_reuses_same_matrix_and_separates_changed_values() -> None:
    cache = FactorizationCache(name="unit_cache", max_entries=4)
    A = sparse.csr_matrix([[4.0, 1.0], [1.0, 3.0]])
    B = sparse.csr_matrix([[5.0, 1.0], [1.0, 3.0]])

    first = factorize_cached(A, MatrixClass.SPD, cache=cache)
    second = factorize_cached(A.copy(), MatrixClass.SPD, cache=cache)
    third = factorize_cached(B, MatrixClass.SPD, cache=cache)

    assert first is second
    assert third is not first
    diagnostics = cache.diagnostics()
    assert diagnostics["hits"] == 1
    assert diagnostics["misses"] == 2
    assert diagnostics["entries"] == 2
    np.testing.assert_allclose(A @ first.solve(np.array([1.0, 0.0])), [1.0, 0.0])


def test_multiple_rhs_static_solve_matches_individual_solves() -> None:
    model = generate_beam_mesh(1.0, num_divisions=2, cross_section={"area": 0.01, "Iy": 1.0e-6, "Iz": 1.0e-6, "J": 1.0e-6})
    load_x = LoadCase("x")
    load_x.add_nodal_load(3, [100.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    load_z = LoadCase("z")
    load_z.add_nodal_load(3, [0.0, 0.0, -100.0, 0.0, 0.0, 0.0])

    F_many, load_info = assemble_load_matrix(model, [load_x, load_z])
    assert F_many.shape[1] == 2
    assert load_info["num_load_cases"] == 2

    many, info = solve_linear_many(model, [load_x, load_z])
    one_x, _ = solve_linear(model, load_x)
    one_z, _ = solve_linear(model, load_z)
    assert info["status"] == "converged"
    assert info["backend"]["factorization_count"] == 1
    assert info["factorization_cache"]["misses"] == 1
    assert info["result_case"]["analysis_case"]["analysis_type"] == "linear_static_many"
    assert [item["name"] for item in info["result_case"]["analysis_case"]["load_cases"]] == ["x", "z"]
    np.testing.assert_allclose(many[:, 0], one_x, rtol=1.0e-9, atol=1.0e-12)
    np.testing.assert_allclose(many[:, 1], one_z, rtol=1.0e-9, atol=1.0e-12)


def test_static_result_provenance_is_attached_to_solver_info_and_fe_result() -> None:
    model = generate_beam_mesh(1.0, num_divisions=1)
    load_case = LoadCase("tip_z")
    load_case.add_nodal_load(2, [0.0, 0.0, -100.0, 0.0, 0.0, 0.0])

    displacements, solver_info = solve_linear(model, load_case)
    result_case = solver_info["result_case"]

    assert result_case["analysis_case"]["analysis_type"] == "linear_static"
    assert result_case["analysis_case"]["load_cases"][0]["name"] == "tip_z"
    assert result_case["matrix_signature"]
    assert result_case["load_signature"]
    assert result_case["solver_backend"] in ("scipy_superlu", "pypardiso")

    result = create_fe_result(model, displacements, solver_info)
    assert result.result_case == result_case


def test_buckling_transient_and_nonlinear_results_include_result_cases() -> None:
    column = FEModel("column")
    column.add_material("steel", 210.0e9, 0.3)
    section = {"area": 0.02, "Iy": 3.0e-6, "Iz": 5.0e-6, "J": 2.0e-6}
    for node_id, x in [(1, 0.0), (2, 1.0), (3, 2.0)]:
        column.add_node(node_id, x, 0.0, 0.0)
    column.add_element(1, BeamElement(1, [1, 2], "steel", section))
    column.add_element(2, BeamElement(2, [2, 3], "steel", section))
    column.add_boundary_condition(BoundaryCondition("suppress", [1, 2, 3], {"ux": 0.0, "uz": 0.0, "rx": 0.0, "ry": 0.0}))
    column.add_boundary_condition(BoundaryCondition("pins", [1, 3], {"uy": 0.0}))
    buckling = solve_eigenvalue_buckling(column, {1: {"axial_compression": 1.0}, 2: {"axial_compression": 1.0}}, num_modes=1)
    assert buckling.result_case["analysis_case"]["analysis_type"] == "linear_buckling"
    assert buckling.result_case["matrix_signature"]

    sdof = FEModel("sdof")
    sdof.add_material("steel", elastic_modulus=100.0, poisson_ratio=0.3, density=2.0)
    sdof.add_node(1, 0.0, 0.0, 0.0)
    sdof.add_node(2, 1.0, 0.0, 0.0)
    sdof.add_element(1, BeamElement(1, [1, 2], "steel", {"area": 1.0, "Iy": 1.0e-6, "Iz": 1.0e-6, "J": 1.0e-6}))
    sdof.add_boundary_condition(FixedSupport("fixed", [1]))
    sdof.add_boundary_condition(BoundaryCondition("slider", [2], {"uy": 0.0, "uz": 0.0, "rx": 0.0, "ry": 0.0, "rz": 0.0}))
    transient_load = LoadCase("step")
    transient_load.add_nodal_load(2, [1.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    transient = solve_transient_newmark(sdof, TransientConfig(dt=0.001, t_end=0.002), base_load_case=transient_load)
    assert transient.result_case["analysis_case"]["analysis_type"] == "linear_transient"
    assert transient.result_case == transient.diagnostics["result_case"]

    nonlinear_model = generate_beam_mesh(1.0, num_divisions=1)
    nonlinear_load = LoadCase("small_axial")
    nonlinear_load.add_nodal_load(2, [10.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    nonlinear = solve_static_nonlinear(nonlinear_model, nonlinear_load, num_steps=1, max_iterations=5)
    assert nonlinear.info["result_case"]["analysis_case"]["analysis_type"] == "nonlinear_static"


def test_revision_signatures_and_sparsity_cache_are_safe_for_geometry_and_topology() -> None:
    model = generate_beam_mesh(1.0, num_divisions=1)
    K1, info1 = assemble_stiffness_matrix(model)
    sig1 = info1["sparsity_signature"]
    rev1 = model.revision_signature()

    model.set_node_coordinates(2, 1.0, 0.0, 0.001)
    K2, info2 = assemble_stiffness_matrix(model)
    rev2 = model.revision_signature()
    assert info2["sparsity_signature"] == sig1
    assert rev2["geometry"] > rev1["geometry"]
    assert K2.shape == K1.shape

    model.add_node(3, 2.0, 0.0, 0.0)
    model.add_element(2, BeamElement(2, [2, 3], "steel", {"area": 0.01, "Iy": 1.0e-6, "Iz": 1.0e-6, "J": 1.0e-6}))
    _K3, info3 = assemble_stiffness_matrix(model)
    assert info3["sparsity_signature"] != sig1


class _BadElement:
    material_name = "steel"

    def __init__(self, values: np.ndarray):
        self.node_ids = [1, 2]
        self.values = np.asarray(values, dtype=float)

    def get_dof_mapping(self, mesh):
        return np.asarray(mesh.get_node(1).dofs + mesh.get_node(2).dofs, dtype=int)

    def compute_stiffness_matrix(self, mesh, material):
        return self.values


def _bad_model(values: np.ndarray) -> FEModel:
    model = FEModel("bad")
    model.add_material("steel", 210.0e9, 0.3)
    model.add_node(1, 0.0, 0.0, 0.0)
    model.add_node(2, 1.0, 0.0, 0.0)
    model.add_element(1, _BadElement(values))
    return model


def test_assembly_diagnostics_reject_nonfinite_and_nonsymmetric_element_matrices() -> None:
    with pytest.raises(AssemblyError, match="non-finite"):
        assemble_stiffness_matrix(_bad_model(np.full((12, 12), np.nan)))

    nonsymmetric = np.eye(12)
    nonsymmetric[0, 1] = 0.25
    with pytest.raises(AssemblyError, match="nonsymmetric"):
        assemble_stiffness_matrix(_bad_model(nonsymmetric))


def _free_two_body_model() -> FEModel:
    model = FEModel("two_free_beams")
    model.add_material("steel", 210.0e9, 0.3)
    section = {"area": 0.01, "Iy": 1.0e-6, "Iz": 1.0e-6, "J": 1.0e-6}
    for node_id, x in [(1, 0.0), (2, 1.0), (3, 3.0), (4, 4.0)]:
        model.add_node(node_id, x, 0.0, 0.0)
    model.add_element(1, BeamElement(1, [1, 2], "steel", section))
    model.add_element(2, BeamElement(2, [3, 4], "steel", section))
    return model


def test_connected_component_nullspace_counts_and_free_free_rejection() -> None:
    supported = generate_beam_mesh(1.0, num_divisions=1)
    supported.apply_boundary_conditions()
    K, _ = assemble_stiffness_matrix(supported)
    _, F_red, _T, _u0, independent, _constraint = build_constraint_transformation(K, np.zeros(K.shape[0]), supported)
    Q, supported_info = build_reduced_rigid_body_modes(supported, independent, K.shape[0])
    assert F_red.shape[0] == K.shape[0] - 6
    assert Q.shape[1] == 0
    assert supported_info["rank"] == 0

    one_free = generate_beam_mesh(1.0, num_divisions=1)
    one_free.boundary_conditions.clear()
    load = LoadCase("unbalanced")
    load.add_nodal_load(2, [1.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    _u, info = solve_linear(one_free, load)
    assert info["convergence_info"]["status"] == "incompatible_free_free_load"
    assert info["nullspace_info"]["rank"] == 6

    two_free = _free_two_body_model()
    _u2, info2 = solve_linear(two_free, None)
    assert info2["convergence_info"]["status"] == "converged"
    assert info2["nullspace_info"]["component_count"] == 2
    assert info2["nullspace_info"]["rank"] == 12


def test_baseline_generation_is_deterministic_for_values_and_comparison() -> None:
    first = generate_baseline_document(include_timing=False)
    second = generate_baseline_document(include_timing=False)
    first["generated_at"] = second["generated_at"] = "ignored"
    assert first == second
    assert compare_baseline_documents(first, second)["status"] == "passed"


def test_infrastructure_benchmarks_report_timing_and_memory() -> None:
    report = run_infrastructure_benchmarks()
    assert report["cases"]
    assert {
        "static_beam",
        "multi_rhs_static",
        "shell_stiffness_S4_cold_warm",
        "shell_stiffness_Q8_cold_warm",
        "shell_stiffness_Q8R_cold_warm",
        "shell_assembly",
        "beam_column_buckling",
        "transient_newmark",
        "factorization_reuse",
        "nonlinear_assembly",
        "fracture_damage",
    } <= set(report["cases"])
    for case in report["cases"].values():
        assert case["timing"]["wall_seconds"] >= 0.0
        assert case["memory"]["peak_bytes"] >= 0
        assert case["status"] in {"completed", "converged", "ok", "skipped"}
    nonlinear = report["cases"]["nonlinear_assembly"]
    if nonlinear["status"] == "completed":
        assert nonlinear["results"]["relative_force_error"] < 1.0e-10
        assert nonlinear["results"]["relative_tangent_error"] < 1.0e-9
    for name in ("shell_stiffness_S4_cold_warm", "shell_stiffness_Q8_cold_warm", "shell_stiffness_Q8R_cold_warm"):
        case = report["cases"][name]
        assert case["jit_enabled"] in {True, False}
        assert "parallel_threads" in case
        assert case["timing"]["cold_assembly_seconds"] >= 0.0
        assert case["timing"]["warm_assembly_seconds"] >= 0.0
        assert case["timing"]["warm_speedup"] >= 0.0
        assert case["results"]["matrix_difference_norm"] < 1.0e-12
    fracture = report["cases"]["fracture_damage"]
    assert fracture["timing"]["static_deletion_scan_seconds"] >= 0.0
    assert fracture["timing"]["impact_damage_state_update_count"] >= 0
    assert fracture["timing"]["impact_eroded_matrix_rebuild_count"] == 0
    assert fracture["results"]["sub_softening_rebuilds_skipped"] is True


def test_solve_linear_many_uses_revision_signature_for_factorization_cache(monkeypatch) -> None:
    model = generate_beam_mesh(1.0, num_divisions=2)
    load = LoadCase("tip")
    load.add_nodal_load(3, [0.0, 0.0, -1.0, 0.0, 0.0, 0.0])

    def fail_content_hash(_matrix):
        raise AssertionError("solve_linear_many should use a revision signature instead of content hashing K")

    monkeypatch.setattr(linalg, "sparse_matrix_signature", fail_content_hash)
    _U, info = solve_linear_many(model, [load])
    assert info["status"] == "converged"
    assert info["factorization_cache"]["misses"] == 1


def test_verification_report_quick_mode_writes_json_and_markdown() -> None:
    output_dir = Path(".pytest_tmp_fe_verification") / str(os.getpid())
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        completed = subprocess.run(
            [sys.executable, "scripts/run_fe_verification.py", "--quick", "--output-dir", str(output_dir)],
            text=True,
            capture_output=True,
            check=False,
        )
        assert completed.returncode == 0, completed.stderr + completed.stdout
        report_path = output_dir / "fe_verification_report.json"
        markdown_path = output_dir / "fe_verification_report.md"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        assert markdown_path.exists()
        assert report["status"] == "passed"
        assert report["environment"]["dependencies"]["scipy"] is not None
        assert {item["name"] for item in report["commands"]} == {"public_imports", "baseline_generation_smoke"}
    finally:
        if output_dir.exists():
            shutil.rmtree(output_dir)


def test_verification_report_family_mode_runs_independent_transient_family() -> None:
    output_dir = Path(".pytest_tmp_fe_verification_family") / str(os.getpid())
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        completed = subprocess.run(
            [sys.executable, "scripts/run_fe_verification.py", "--transient", "--output-dir", str(output_dir)],
            text=True,
            capture_output=True,
            check=False,
        )
        assert completed.returncode == 0, completed.stderr + completed.stdout
        report = json.loads((output_dir / "fe_verification_report.json").read_text(encoding="utf-8"))
        assert report["selected_families"] == ["transient"]
        assert [item["name"] for item in report["commands"]] == ["public_imports", "transient_tests"]
        assert report["status"] == "passed"
    finally:
        if output_dir.exists():
            shutil.rmtree(output_dir)
