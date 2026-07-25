from __future__ import annotations

import numpy as np

from anysolver.mesh_gen import generate_simple_panel_mesh
from anysolver import nonlinear_static
from anysolver import nonlinear_performance
from anysolver.jit_compiler import JIT_ENABLED
from anysolver import nonlinear_performance_batch_c
from anysolver.material_curves import dnv_c208_steel_curve
from anysolver.elements import ShellElement
from anysolver.fe_core import FEModel
from anysolver.nonlinear_performance_bootstrap import (
    clear_nonlinear_assembly_cache,
    get_nonlinear_assembly_plan,
    nonlinear_performance_status,
)


def _panel_model():
    return generate_simple_panel_mesh(
        1.2,
        0.8,
        0.01,
        num_divisions_x=2,
        num_divisions_y=2,
    )


def test_performance_layer_installs_on_first_nonlinear_use() -> None:
    nonlinear_static._ensure_nonlinear_acceleration()
    status = nonlinear_performance_status()
    assert status["installed"] is True
    if JIT_ENABLED:
        assert status["batch_c"]["installed"] is True
        assert (
            nonlinear_static._assemble_nonlinear_system
            is nonlinear_performance_batch_c._batch_c_assemble_nonlinear_system
        )
    else:
        assert status["batch_c"]["installed"] is False
        assert (
            nonlinear_static._assemble_nonlinear_system
            is nonlinear_performance._optimized_assemble_nonlinear_system
        )


def test_cached_assembly_matches_legacy_shell_assembly() -> None:
    model = _panel_model()
    rng = np.random.default_rng(1042)
    displacement = rng.normal(scale=2.0e-5, size=model.mesh.dof_manager.total_dofs)
    committed = {}

    assert nonlinear_performance._ORIGINAL_ASSEMBLER is not None
    force_reference, tangent_reference, states_reference = (
        nonlinear_performance._ORIGINAL_ASSEMBLER(
            model,
            displacement,
            committed,
            5,
            tangent=True,
        )
    )
    force_fast, tangent_fast, states_fast = (
        nonlinear_static._assemble_nonlinear_system(
            model,
            displacement,
            committed,
            5,
            tangent=True,
        )
    )

    np.testing.assert_allclose(
        force_fast,
        force_reference,
        rtol=1.0e-11,
        atol=1.0e-8,
    )
    np.testing.assert_allclose(
        tangent_fast.toarray(),
        tangent_reference.toarray(),
        rtol=1.0e-11,
        atol=1.0e-5,
    )
    assert set(states_fast) == set(states_reference)
    for element_id in states_reference:
        np.testing.assert_allclose(
            states_fast[element_id]["plastic_strain"],
            states_reference[element_id]["plastic_strain"],
        )
        np.testing.assert_allclose(
            states_fast[element_id]["alpha"],
            states_reference[element_id]["alpha"],
        )


def test_plastic_shell_batch_matches_scalar_algorithmic_tangent() -> None:
    nonlinear_static._ensure_nonlinear_acceleration()
    model = _panel_model()
    first_element = next(iter(model.mesh.elements.values()))
    material = model.get_material(first_element.material_name)
    material.hardening_curve = dnv_c208_steel_curve("S355", 0.01)
    model.bump_revision("material")
    displacement = np.zeros(model.mesh.dof_manager.total_dofs, dtype=float)
    for node in model.mesh.nodes.values():
        displacement[node.dofs[0]] = 0.004 * node.x
        displacement[node.dofs[1]] = -0.001 * node.y
        displacement[node.dofs[4]] = 0.003 * node.x

    legacy = nonlinear_performance._ORIGINAL_ASSEMBLER
    assert legacy is not None
    force_reference, tangent_reference, states_reference = legacy(
        model,
        displacement,
        {},
        5,
        tangent=True,
    )
    force_fast, tangent_fast, states_fast = nonlinear_static._assemble_nonlinear_system(
        model,
        displacement,
        {},
        5,
        tangent=True,
    )
    np.testing.assert_allclose(force_fast, force_reference, rtol=2.0e-11, atol=1.0e-6)
    np.testing.assert_allclose(
        tangent_fast.toarray(),
        tangent_reference.toarray(),
        rtol=2.0e-10,
        atol=1.0e-3,
    )
    for element_id in states_reference:
        np.testing.assert_allclose(states_fast[element_id]["alpha"], states_reference[element_id]["alpha"])
        np.testing.assert_allclose(
            states_fast[element_id]["plastic_strain"],
            states_reference[element_id]["plastic_strain"],
        )


def test_q8r_uses_scalar_nonlinear_path_with_hourglass_parity() -> None:
    nonlinear_static._ensure_nonlinear_acceleration()
    model = FEModel("q8r_nonlinear")
    model.add_material("steel", 210.0e9, 0.3)
    coordinates = (
        (0.0, 0.0, 0.0),
        (1.0, 0.0, 0.0),
        (1.0, 1.0, 0.0),
        (0.0, 1.0, 0.0),
        (0.5, 0.0, 0.0),
        (1.0, 0.5, 0.0),
        (0.5, 1.0, 0.0),
        (0.0, 0.5, 0.0),
    )
    for node_id, coordinate in enumerate(coordinates, start=1):
        model.add_node(node_id, *coordinate)
    element = ShellElement(
        1,
        list(range(1, 9)),
        "steel",
        thickness=0.01,
        reduced_integration=True,
    )
    model.add_element(1, element)
    clear_nonlinear_assembly_cache(model)
    plan = get_nonlinear_assembly_plan(model, 5)
    assert plan.shell_batches == ()
    assert [record.element_id for record in plan.non_shell_elements] == [1]

    displacement = np.linspace(-2.0e-5, 3.0e-5, model.mesh.dof_manager.total_dofs)
    legacy = nonlinear_performance._ORIGINAL_ASSEMBLER
    assert legacy is not None
    force_reference, tangent_reference, _states_reference = legacy(
        model,
        displacement,
        {},
        5,
        tangent=True,
    )
    force_fast, tangent_fast, _states_fast = nonlinear_static._assemble_nonlinear_system(
        model,
        displacement,
        {},
        5,
        tangent=True,
    )
    np.testing.assert_allclose(force_fast, force_reference, rtol=1.0e-12, atol=1.0e-8)
    np.testing.assert_allclose(tangent_fast.toarray(), tangent_reference.toarray(), rtol=1.0e-12, atol=1.0e-5)
    assert getattr(element, "_hourglass_stiffness_matrix", None) is not None


def test_residual_only_path_matches_tangent_path_force() -> None:
    model = _panel_model()
    displacement = np.linspace(
        -1.0e-5,
        1.0e-5,
        model.mesh.dof_manager.total_dofs,
        dtype=float,
    )
    force_tangent, tangent, _ = nonlinear_static._assemble_nonlinear_system(
        model,
        displacement,
        {},
        5,
        tangent=True,
    )
    force_only, no_tangent, _ = nonlinear_static._assemble_nonlinear_system(
        model,
        displacement,
        {},
        5,
        tangent=False,
    )
    assert tangent is not None
    assert no_tangent is None
    np.testing.assert_allclose(
        force_only,
        force_tangent,
        rtol=1.0e-12,
        atol=1.0e-8,
    )


def test_plan_is_reused_until_model_revision_changes() -> None:
    model = _panel_model()
    clear_nonlinear_assembly_cache(model)
    first = get_nonlinear_assembly_plan(model, 5)
    second = get_nonlinear_assembly_plan(model, 5)
    assert first is second

    node = next(iter(model.mesh.nodes.values()))
    model.mesh.set_node_coordinates(node.id, node.x, node.y, node.z + 1.0e-6)
    third = get_nonlinear_assembly_plan(model, 5)
    assert third is not first


def test_csr_pattern_is_reused_and_contains_unique_entries() -> None:
    model = _panel_model()
    plan = get_nonlinear_assembly_plan(model, 5)
    assert plan.csr_indices.size == plan.nnz
    assert plan.csr_indptr.size == model.mesh.dof_manager.total_dofs + 1
    for row in range(plan.total_dofs):
        start = int(plan.csr_indptr[row])
        stop = int(plan.csr_indptr[row + 1])
        row_indices = plan.csr_indices[start:stop]
        assert np.all(row_indices[:-1] < row_indices[1:])


def test_legacy_path_can_be_restored_for_ab_measurements() -> None:
    nonlinear_performance.uninstall_nonlinear_performance_optimizations()
    try:
        assert (
            nonlinear_static._assemble_nonlinear_system
            is nonlinear_performance._ORIGINAL_ASSEMBLER
        )
    finally:
        nonlinear_performance.install_nonlinear_performance_optimizations()
    if JIT_ENABLED:
        assert (
            nonlinear_static._assemble_nonlinear_system
            is nonlinear_performance_batch_c._batch_c_assemble_nonlinear_system
        )
    else:
        assert (
            nonlinear_static._assemble_nonlinear_system
            is nonlinear_performance._optimized_assemble_nonlinear_system
        )
