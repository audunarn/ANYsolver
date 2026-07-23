import numpy as np
import pytest

from anysolver.boundary import BoundaryCondition
from anysolver.buckling import solve_eigenvalue_buckling
from anysolver.elements import BeamElement
from anysolver.fe_core import FEModel
from anysolver.linalg import FactorizationCache
from anysolver.matrix_assembly import assemble_geometric_stiffness_matrix


def _beam_column_model(num_elements=8):
    length = 4.0
    model = FEModel("beam_column_buckling")
    model.add_material("steel", 210.0e9, 0.3, density=7850.0)
    model.current_material = "steel"

    for i in range(num_elements + 1):
        x = length * i / num_elements
        model.add_node(i + 1, x, 0.0, 0.0)

    section = {"area": 0.02, "Iy": 3.0e-6, "Iz": 5.0e-6, "J": 2.0e-6}
    for i in range(num_elements):
        element_id = i + 1
        model.add_element(element_id, BeamElement(element_id, [i + 1, i + 2], "steel", section))

    all_nodes = list(range(1, num_elements + 2))
    end_nodes = [1, num_elements + 1]
    model.add_boundary_condition(
        BoundaryCondition("suppress_unrelated_dofs", all_nodes, {"ux": 0.0, "uz": 0.0, "rx": 0.0, "ry": 0.0})
    )
    model.add_boundary_condition(BoundaryCondition("pinned_lateral_ends", end_nodes, {"uy": 0.0}))
    model.apply_boundary_conditions()
    return model, length, section


def test_beam_geometric_stiffness_is_symmetric_and_scales_with_compression():
    model, _, _ = _beam_column_model(num_elements=1)

    KG_100, info = assemble_geometric_stiffness_matrix(model, {1: {"axial_compression": 100.0}})
    KG_250, _ = assemble_geometric_stiffness_matrix(model, {1: {"axial_compression": 250.0}})

    assert info["matrix_type"] == "geometric_stiffness"
    assert KG_100.nnz > 0
    np.testing.assert_allclose(KG_100.toarray(), KG_100.toarray().T, rtol=0.0, atol=1.0e-12)
    np.testing.assert_allclose(KG_250.toarray(), 2.5 * KG_100.toarray(), rtol=1.0e-13, atol=1.0e-12)


def test_negative_axial_force_is_interpreted_as_compression_for_beam_kg():
    model, _, _ = _beam_column_model(num_elements=1)

    KG_compression, _ = assemble_geometric_stiffness_matrix(model, {1: {"axial_compression": 50.0}})
    KG_axial_force, _ = assemble_geometric_stiffness_matrix(model, {1: {"axial_force": -50.0}})

    np.testing.assert_allclose(KG_axial_force.toarray(), KG_compression.toarray(), rtol=0.0, atol=1.0e-12)


def test_eigenvalue_buckling_returns_euler_column_scale_for_pinned_beam():
    model, length, section = _beam_column_model(num_elements=10)
    states = {element_id: {"axial_compression": 1.0} for element_id in model.mesh.elements}

    result = solve_eigenvalue_buckling(model, states, num_modes=3)

    # Only uy/rz are free, so buckling happens in the x-y plane and is governed
    # by bending about local z, i.e. Iz.
    expected_euler = np.pi**2 * model.get_material("steel").elastic_modulus * section["Iz"] / length**2
    assert result.solver_status == "ok"
    assert result.num_modes_returned == 3
    assert result.critical_load_factor == pytest.approx(expected_euler, rel=0.08)
    assert [mode.load_factor for mode in result.modes] == sorted(mode.load_factor for mode in result.modes)
    assert np.max(np.abs(result.modes[0].mode_shape)) == pytest.approx(1.0)
    assert result.diagnostics["max_residual_norm"] < 1.0e-8
    assert result.modes[0].validity_status == "ok"
    assert result.result_case["solver_backend"] in {"scipy_superlu", None}


def test_buckling_applies_model_constraints_independent_of_prior_call_history():
    preapplied_model, _, _ = _beam_column_model(num_elements=8)
    fresh_model, _, _ = _beam_column_model(num_elements=8)
    fresh_model.mesh.dof_manager._constrained_dofs.clear()
    assert fresh_model.boundary_conditions
    assert fresh_model.mesh.dof_manager._constrained_dofs == set()
    states = {element_id: {"axial_compression": 1.0} for element_id in preapplied_model.mesh.elements}

    preapplied = solve_eigenvalue_buckling(preapplied_model, states, num_modes=2)
    fresh = solve_eigenvalue_buckling(fresh_model, states, num_modes=2)

    assert preapplied.solver_status == fresh.solver_status == "ok"
    assert fresh.critical_load_factor == pytest.approx(preapplied.critical_load_factor, rel=1.0e-12)
    assert fresh.num_modes_returned == preapplied.num_modes_returned
    constrained = sorted(fresh_model.mesh.dof_manager._constrained_dofs)
    assert constrained
    for mode in fresh.modes:
        np.testing.assert_allclose(mode.mode_shape[constrained], 0.0, atol=1.0e-12)


def test_buckling_mode_shapes_respect_fixed_constraint_dofs():
    model, _, _ = _beam_column_model(num_elements=6)
    states = {element_id: {"axial_compression": 1.0} for element_id in model.mesh.elements}

    result = solve_eigenvalue_buckling(model, states, num_modes=2)

    constrained = sorted(model.mesh.dof_manager._constrained_dofs)
    assert constrained
    assert result.solver_status == "ok"
    for mode in result.modes:
        np.testing.assert_allclose(mode.mode_shape[constrained], 0.0, atol=1.0e-12)
        assert np.max(np.abs(mode.mode_shape)) == pytest.approx(1.0)
        assert mode.residual_norm < 1.0e-8


def test_free_free_buckling_reports_and_filters_rigid_body_nullspace():
    model = FEModel("free_free_buckling_guard")
    model.add_material("steel", 210.0e9, 0.3)
    model.add_node(1, 0.0, 0.0, 0.0)
    model.add_node(2, 1.0, 0.0, 0.0)
    model.add_element(1, BeamElement(1, [1, 2], "steel", {"area": 0.02, "Iy": 1.0e-6, "Iz": 1.0e-6, "J": 1.0e-6}))

    result = solve_eigenvalue_buckling(model, {1: {"axial_compression": 1.0}}, num_modes=2, allow_dense_fallback=True)

    assert result.solver_status == "ok"
    assert result.num_modes_returned == 2
    assert result.diagnostics["nullspace_rank"] == 6
    assert result.diagnostics["free_mechanism_handling"] == "rigid_body_roots_filtered"
    assert result.assembly_info["nullspace"]["rank"] == 6
    assert all(mode.rigid_body_correlation <= 0.90 for mode in result.modes)


def test_buckling_load_factor_scales_inverse_to_reference_compression():
    model, _, _ = _beam_column_model(num_elements=6)
    unit_states = {element_id: {"axial_compression": 1.0} for element_id in model.mesh.elements}
    double_states = {element_id: {"axial_compression": 2.0} for element_id in model.mesh.elements}

    unit_result = solve_eigenvalue_buckling(model, unit_states, num_modes=1)
    double_result = solve_eigenvalue_buckling(model, double_states, num_modes=1)

    assert unit_result.solver_status == "ok"
    assert double_result.solver_status == "ok"
    assert double_result.critical_load_factor == pytest.approx(0.5 * unit_result.critical_load_factor, rel=1.0e-10)


def test_sparse_buckling_path_reports_residuals_and_rejected_roots():
    model, _, _ = _beam_column_model(num_elements=12)
    states = {element_id: {"axial_compression": 1.0} for element_id in model.mesh.elements}

    result = solve_eigenvalue_buckling(model, states, num_modes=2, dense_size_limit=2)

    assert result.solver_status == "ok"
    assert result.diagnostics["solver"] == "sparse_scipy_eigsh_inverted_pencil"
    assert result.diagnostics["num_roots_considered"] >= result.num_modes_returned
    assert result.diagnostics["max_residual_norm"] < 1.0e-8
    assert "rejected_roots" in result.diagnostics
    assert all(mode.residual_norm < 1.0e-8 for mode in result.modes)


def test_sparse_buckling_shift_invert_reports_factorization_cache():
    model, _, _ = _beam_column_model(num_elements=12)
    states = {element_id: {"axial_compression": 1.0} for element_id in model.mesh.elements}
    first = solve_eigenvalue_buckling(model, states, num_modes=1, dense_size_limit=2)
    cache = FactorizationCache(name="buckling_test", max_entries=2)

    shifted = solve_eigenvalue_buckling(
        model,
        states,
        num_modes=1,
        dense_size_limit=2,
        shift_load_factor=first.critical_load_factor,
        factorization_cache=cache,
    )

    assert shifted.solver_status == "ok"
    assert shifted.diagnostics["shift_invert"] is True
    assert shifted.diagnostics["factorization_cache"]["misses"] == 1
    assert cache.diagnostics()["entries"] == 1


def test_buckling_factor_range_can_target_higher_mode_family():
    model, _, _ = _beam_column_model(num_elements=14)
    states = {element_id: {"axial_compression": 1.0} for element_id in model.mesh.elements}
    first = solve_eigenvalue_buckling(model, states, num_modes=1)

    higher = solve_eigenvalue_buckling(
        model,
        states,
        num_modes=1,
        load_factor_range=(3.0 * first.critical_load_factor, 5.0 * first.critical_load_factor),
        dense_size_limit=2,
    )

    assert higher.solver_status == "ok"
    assert higher.critical_load_factor == pytest.approx(4.0 * first.critical_load_factor, rel=0.05)
    assert higher.diagnostics["num_rejected_roots"] > 0
    assert all(item.get("reason") != "invalid_load_factor" for item in higher.diagnostics["rejected_roots"])


def test_repeated_buckling_mode_groups_are_reported_for_symmetric_column():
    length = 4.0
    num_elements = 12
    model = FEModel("symmetric_column")
    model.add_material("steel", 210.0e9, 0.3)
    for i in range(num_elements + 1):
        model.add_node(i + 1, length * i / num_elements, 0.0, 0.0)
    section = {"area": 0.02, "Iy": 4.0e-6, "Iz": 4.0e-6, "J": 2.0e-6}
    for element_id in range(1, num_elements + 1):
        model.add_element(element_id, BeamElement(element_id, [element_id, element_id + 1], "steel", section))
    all_nodes = list(range(1, num_elements + 2))
    end_nodes = [1, num_elements + 1]
    model.add_boundary_condition(BoundaryCondition("suppress_axial_torsion", all_nodes, {"ux": 0.0, "rx": 0.0}))
    model.add_boundary_condition(BoundaryCondition("pinned_lateral_ends", end_nodes, {"uy": 0.0, "uz": 0.0}))
    states = {element_id: {"axial_compression": 1.0} for element_id in model.mesh.elements}

    result = solve_eigenvalue_buckling(
        model,
        states,
        num_modes=4,
        dense_size_limit=2,
        repeated_tolerance=1.0e-2,
        allow_free_mechanisms=True,
    )

    assert result.solver_status == "ok"
    # The declared supports remove every rigid mode; buckling applies them
    # itself rather than inheriting an empty constraint set from call history.
    assert result.assembly_info["nullspace"]["rank"] == 0
    assert result.diagnostics["num_repeated_mode_groups"] >= 1
    first_group = result.diagnostics["repeated_mode_groups"][0]
    assert first_group["mode_numbers"][:2] == [1, 2]
    assert result.modes[0].repeated_group == result.modes[1].repeated_group


def test_torsional_column_buckling_matches_wagner_analytic_load():
    """Axial compression + weak St. Venant torsion: P_cr = G*J*A/Ip (no warping)."""
    from anysolver.boundary import BoundaryCondition
    from anysolver.elements import BeamElement, QuadraticBeamElement
    from anysolver.fe_core import FEModel

    section = {"area": 1.0e-2, "Iy": 1.0e-5, "Iz": 1.0e-5, "J": 1.0e-9}

    def _column(quadratic: bool) -> FEModel:
        model = FEModel("torsion_column")
        model.add_material("steel", 2.1e11, 0.3, density=7850.0)
        n = 6
        grid = 2 * n if quadratic else n
        for i in range(grid + 1):
            model.add_node(i + 1, i / grid, 0.0, 0.0)
        for e in range(n):
            if quadratic:
                nodes = [2 * e + 1, 2 * e + 2, 2 * e + 3]
                model.add_element(e + 1, QuadraticBeamElement(e + 1, nodes, "steel", section))
            else:
                model.add_element(e + 1, BeamElement(e + 1, [e + 1, e + 2], "steel", section))
        end = grid + 1
        model.add_boundary_condition(BoundaryCondition("fork_a", [1], {"ux": 0.0, "uy": 0.0, "uz": 0.0, "rx": 0.0}))
        model.add_boundary_condition(BoundaryCondition("fork_b", [end], {"uy": 0.0, "uz": 0.0, "rx": 0.0}))
        return model

    material_G = 2.1e11 / (2.0 * (1.0 + 0.3))
    polar = section["Iy"] + section["Iz"]
    expected_torsional = material_G * section["J"] * section["area"] / polar
    euler = np.pi**2 * 2.1e11 * section["Iy"] / 1.0**2
    assert expected_torsional < 0.01 * euler  # torsion must govern

    for quadratic in (False, True):
        model = _column(quadratic)
        states = {element_id: {"axial_compression": 1.0} for element_id in model.mesh.elements}
        result = solve_eigenvalue_buckling(model, states, num_modes=2)
        assert result.solver_status == "ok"
        # Same linear twist-gradient field in K and KG for the 2-node beam makes
        # the torsional eigenvalue mesh-exact; the quadratic beam is near-exact.
        assert result.critical_load_factor == pytest.approx(expected_torsional, rel=1.0e-3)
