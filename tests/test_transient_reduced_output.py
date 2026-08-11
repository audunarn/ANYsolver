from __future__ import annotations

import numpy as np

from anysolver import AnalysisSession, BoundaryCondition, FixedSupport, LoadCase
from anysolver.dynamics import TransientConfig, solve_transient_newmark
from anysolver.elements import BeamElement
from anysolver.fe_core import FEModel
from anysolver.recovery import RecoveryConfig


def _model_and_load() -> tuple[FEModel, LoadCase]:
    model = FEModel("selected_output_sdof")
    model.add_material("steel", elastic_modulus=100.0, poisson_ratio=0.3, density=2.0)
    model.add_node(1, 0.0, 0.0, 0.0)
    model.add_node(2, 1.0, 0.0, 0.0)
    model.add_element(
        1,
        BeamElement(
            1,
            [1, 2],
            "steel",
            {"area": 1.0, "Iy": 1.0e-6, "Iz": 1.0e-6, "J": 1.0e-6},
        ),
    )
    model.add_boundary_condition(FixedSupport("fixed", [1]))
    model.add_boundary_condition(
        BoundaryCondition(
            "slider",
            [2],
            {"uy": 0.0, "uz": 0.0, "rx": 0.0, "ry": 0.0, "rz": 0.0},
        )
    )
    load = LoadCase("step")
    load.add_nodal_load(2, [1.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    return model, load


def test_selected_history_matches_full_without_saved_full_reconstruction() -> None:
    model, load = _model_and_load()
    full_config = TransientConfig(dt=0.001, t_end=0.02, save_every=2, output_nodes=[2])
    selected_config = TransientConfig(
        dt=0.001,
        t_end=0.02,
        save_every=2,
        output_nodes=[2],
        recovery=RecoveryConfig(
            node_ids=[2],
            include_stresses=False,
            history_mode="selected",
            store_full_histories=False,
        ),
    )

    with AnalysisSession(model) as session:
        full = solve_transient_newmark(model, full_config, base_load_case=load, session=session)
        selected = solve_transient_newmark(
            model,
            selected_config,
            base_load_case=load,
            session=session,
        )
        session_diagnostics = session.diagnostics()

    node_dofs = np.asarray(model.mesh.get_node(2).dofs, dtype=np.intp)
    np.testing.assert_allclose(selected.times, full.times, rtol=0.0, atol=0.0)
    np.testing.assert_allclose(selected.displacements, full.displacements[:, node_dofs], rtol=1.0e-12, atol=1.0e-14)
    np.testing.assert_allclose(selected.velocities, full.velocities[:, node_dofs], rtol=1.0e-12, atol=1.0e-14)
    np.testing.assert_allclose(selected.accelerations, full.accelerations[:, node_dofs], rtol=1.0e-12, atol=1.0e-14)
    np.testing.assert_allclose(selected.node_histories[2], full.node_histories[2], rtol=1.0e-12, atol=1.0e-14)
    np.testing.assert_allclose(selected.load_impulse, full.load_impulse, rtol=0.0, atol=1.0e-14)
    assert selected.peak_displacement == full.peak_displacement
    assert selected.peak_displacement_node == full.peak_displacement_node
    assert selected.diagnostics["preprojected_load_basis_count"] == 1
    assert selected.diagnostics["full_vector_reconstruction_count"] == 0
    assert selected.diagnostics["selected_output_reconstruction_count"] == len(selected.times)
    assert session_diagnostics["counters"]["stiffness_builds"] == 1
    assert session_diagnostics["counters"]["mass_builds"] == 1
    assert session_diagnostics["counters"]["stiffness_hits"] >= 1
    assert session_diagnostics["counters"]["mass_hits"] >= 1


def test_selected_stress_history_explicitly_materializes_full_displacement() -> None:
    model, load = _model_and_load()
    config = TransientConfig(
        dt=0.002,
        t_end=0.006,
        output_nodes=[2],
        output_elements=[1],
        include_stress_history=True,
        recovery=RecoveryConfig(
            node_ids=[2],
            element_ids=[1],
            history_mode="selected",
            store_full_histories=False,
        ),
    )

    result = solve_transient_newmark(model, config, base_load_case=load)

    assert result.stress_history is not None
    assert len(result.stress_history) == len(result.times)
    assert result.diagnostics["full_vector_reconstruction_count"] == len(result.times)
    assert result.diagnostics["selected_output_reconstruction_count"] == len(result.times)

