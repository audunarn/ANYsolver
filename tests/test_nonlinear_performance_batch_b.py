from __future__ import annotations

import numpy as np
import pytest
from types import SimpleNamespace

from anysolver import nonlinear_performance, nonlinear_static
from anysolver.boundary import FixedSupport, LoadCase
from anysolver.elements import ShellElement
from anysolver.fe_core import FEModel
from anysolver.jit_compiler import JIT_DISABLED_REASON, JIT_ENABLED, jit_diagnostics
from anysolver.mesh_gen import generate_simple_panel_mesh
from anysolver.nonlinear_performance_batch_b import batch_b_status
from anysolver.nonlinear_performance_bootstrap import (
    clear_nonlinear_assembly_cache,
    get_nonlinear_assembly_plan,
    nonlinear_performance_status,
)
from anysolver.runtime import _runtime_display_stresses

pytestmark = pytest.mark.skipif(
    not JIT_ENABLED,
    reason=f"Batch B in-place shell kernel requires Numba ({JIT_DISABLED_REASON})",
)

nonlinear_static._ensure_nonlinear_acceleration()


def _tilted_shell_model() -> FEModel:
    model = FEModel("tilted_elastic_shell")
    model.add_material("steel", 210.0e9, 0.3)
    model.add_node(1, 0.0, 0.0, 0.0)
    model.add_node(2, 1.1, 0.2, 0.4)
    model.add_node(3, 1.0, 1.1, 0.9)
    model.add_node(4, -0.1, 0.9, 0.5)
    model.add_element(1, ShellElement(1, [1, 2, 3, 4], "steel", thickness=0.012))
    return model


def test_batch_b_is_active() -> None:
    status = nonlinear_performance_status()
    assert status["installed"] is True
    assert status["batch_b"]["eligible"] is True
    assert status["batch_b"]["installed"] is True
    assert batch_b_status()["installed"] is True
    assert status["batch_b"]["parallel_kernel"] is True
    assert jit_diagnostics()["num_threads"] is not None


def test_tilted_elastic_shell_matches_legacy() -> None:
    model = _tilted_shell_model()
    rng = np.random.default_rng(20260618)
    displacement = rng.normal(scale=1.0e-5, size=model.mesh.dof_manager.total_dofs)
    legacy = nonlinear_performance._ORIGINAL_ASSEMBLER
    assert legacy is not None
    force_ref, tangent_ref, states_ref = legacy(model, displacement, {}, 5, tangent=True)
    force_fast, tangent_fast, states_fast = nonlinear_static._assemble_nonlinear_system(
        model, displacement, {}, 5, tangent=True
    )
    np.testing.assert_allclose(force_fast, force_ref, rtol=2.0e-11, atol=1.0e-8)
    np.testing.assert_allclose(
        tangent_fast.toarray(), tangent_ref.toarray(), rtol=2.0e-11, atol=1.0e-5
    )
    assert set(states_fast) == set(states_ref)


def test_elastic_batch_releases_history_work_arrays() -> None:
    model = generate_simple_panel_mesh(
        1.2, 0.8, 0.01, num_divisions_x=2, num_divisions_y=2
    )
    clear_nonlinear_assembly_cache(model)
    plan = get_nonlinear_assembly_plan(model, 5)
    assert plan.shell_batches
    for batch in plan.shell_batches:
        assert batch.has_plasticity is False
        assert batch.plastic_work.size == 0
        assert batch.alpha_work.size == 0
        assert getattr(batch, "_batch_b_elastic", False) is True
        first_state = batch.elastic_states[0]
        assert first_state["plastic_strain"].flags.writeable is False
        assert first_state["alpha"].flags.writeable is False
        # Elastic recovery must fall back to displacement-based stresses; a
        # fabricated zero layer_strain would overwrite them with zero stress.
        assert "layer_strain" not in first_state


def test_elastic_batch_does_not_overwrite_recovered_stress_with_zero() -> None:
    model = _tilted_shell_model()
    displacement = np.zeros(model.mesh.dof_manager.total_dofs, dtype=float)
    displacement[model.mesh.get_node(2).dofs[0]] = 2.0e-4
    _force, _tangent, states = nonlinear_static._assemble_nonlinear_system(
        model,
        displacement,
        {},
        5,
        tangent=True,
    )
    stresses, state_based = _runtime_display_stresses(
        model,
        displacement,
        SimpleNamespace(element_states=states),
    )
    assert state_based == set()
    assert float(np.max(np.asarray(stresses[1]["von_mises"], dtype=float))) > 0.0


def test_final_result_recovers_elastic_layer_state_once() -> None:
    model = generate_simple_panel_mesh(
        1.0, 0.6, 0.01, num_divisions_x=1, num_divisions_y=1
    )
    left_nodes = [
        node_id
        for node_id, node in model.mesh.nodes.items()
        if np.isclose(node.x, 0.0)
    ]
    right_nodes = [
        node_id
        for node_id, node in model.mesh.nodes.items()
        if np.isclose(node.x, 1.0)
    ]
    model.add_boundary_condition(FixedSupport("fixed", left_nodes))
    load = LoadCase("membrane")
    for node_id in right_nodes:
        load.add_nodal_load(node_id, [5.0e4, 0.0, 0.0, 0.0, 0.0, 0.0])

    result = nonlinear_static.solve_static_nonlinear(
        model,
        load,
        num_steps=2,
        num_layers=5,
    )
    assert result.status == "completed"

    legacy = nonlinear_performance._ORIGINAL_ASSEMBLER
    assert legacy is not None
    _force, _tangent, reference_states = legacy(
        model,
        result.displacements,
        {},
        5,
        tangent=False,
    )
    assert set(result.element_states) == set(reference_states)
    for element_id, reference_state in reference_states.items():
        assert "layer_strain" in result.element_states[element_id]
        np.testing.assert_allclose(
            result.element_states[element_id]["layer_strain"],
            reference_state["layer_strain"],
            rtol=2.0e-12,
            atol=1.0e-15,
        )

    reference_summary = nonlinear_static._nonlinear_state_summary(reference_states)
    assert result.info["strain_summary"]["layer_strain_min"] == pytest.approx(
        reference_summary["layer_strain_min"],
        rel=2.0e-12,
        abs=1.0e-15,
    )
    assert result.info["strain_summary"]["layer_strain_max"] == pytest.approx(
        reference_summary["layer_strain_max"],
        rel=2.0e-12,
        abs=1.0e-15,
    )
    assert nonlinear_static.states_von_mises_map(
        model,
        result.element_states,
    ) == pytest.approx(
        nonlinear_static.states_von_mises_map(model, reference_states),
        rel=2.0e-12,
        abs=1.0e-6,
    )


def test_batch_b_reuses_plan_buffers() -> None:
    model = generate_simple_panel_mesh(
        1.0, 0.6, 0.01, num_divisions_x=2, num_divisions_y=1
    )
    plan = get_nonlinear_assembly_plan(model, 5)
    buffer_ids = (
        id(plan.force_values),
        id(plan.tangent_values),
        tuple(id(batch.u_work) for batch in plan.shell_batches),
    )
    displacement = np.zeros(model.mesh.dof_manager.total_dofs, dtype=float)
    nonlinear_static._assemble_nonlinear_system(model, displacement, {}, 5, tangent=True)
    nonlinear_static._assemble_nonlinear_system(model, displacement, {}, 5, tangent=True)
    assert buffer_ids == (
        id(plan.force_values),
        id(plan.tangent_values),
        tuple(id(batch.u_work) for batch in plan.shell_batches),
    )
    diagnostics = plan.diagnostics()
    assert diagnostics["batch_b_installed"] is True
    assert diagnostics["elastic_fast_path_element_count"] == model.mesh.num_elements
    assert diagnostics["plastic_batch_count"] == 0
