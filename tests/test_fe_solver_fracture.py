from __future__ import annotations

import numpy as np
import pytest

from anysolver.boundary import BoundaryCondition, FixedSupport, LoadCase
from anysolver.elements import ShellElement
from anysolver.fe_core import FEModel
from anysolver.fracture import (
    FractureConfig,
    deleted_pressure_load_resultant,
    filtered_load_case_for_deleted_elements,
)
from anysolver.material_curves import DNVC208MaterialCurve
from anysolver.matrix_assembly import assemble_load_vector
from anysolver.nonlinear_static import _assemble_nonlinear_system, solve_static_nonlinear


E = 210.0e9
NU = 0.3

CURVE = DNVC208MaterialCurve(
    sigma_prop=320.0e6,
    sigma_yield=357.0e6,
    sigma_yield_2=363.3e6,
    eps_p_y1=0.004,
    eps_p_y2=0.015,
    K=740.0e6,
    n=0.166,
)


def _one_shell_model(curve=CURVE) -> FEModel:
    model = FEModel("fracture_panel")
    model.add_material("steel", E, NU, hardening_curve=curve)
    model.add_node(1, 0.0, 0.0, 0.0)
    model.add_node(2, 1.0, 0.0, 0.0)
    model.add_node(3, 1.0, 0.2, 0.0)
    model.add_node(4, 0.0, 0.2, 0.0)
    model.add_element(1, ShellElement(1, [1, 2, 3, 4], "steel", 0.01))
    model.add_boundary_condition(BoundaryCondition("left_x", [1, 4], {"ux": 0.0}))
    model.add_boundary_condition(BoundaryCondition("plane", [1, 2, 3, 4], {"uz": 0.0, "rx": 0.0, "ry": 0.0}))
    model.add_boundary_condition(BoundaryCondition("pin_y", [1], {"uy": 0.0}))
    return model


def _tension_load(model: FEModel, stress: float = 340.0e6) -> LoadCase:
    load = LoadCase("pull")
    total = stress * 0.2 * 0.01
    load.add_nodal_load(2, [0.5 * total, 0, 0, 0, 0, 0])
    load.add_nodal_load(3, [0.5 * total, 0, 0, 0, 0, 0])
    return load


def test_fracture_config_validates_inputs() -> None:
    with pytest.raises(ValueError):
        FractureConfig(threshold=0.0)
    with pytest.raises(ValueError):
        FractureConfig(threshold=1.0e-3, residual_stiffness_fraction=-1.0)
    with pytest.raises(ValueError):
        FractureConfig(threshold=1.0e-3, max_deleted_fraction=1.5)
    with pytest.raises(ValueError):
        FractureConfig(threshold=1.0e-3, element_scope=("solid",))


def test_deleted_element_assembly_uses_residual_stiffness_without_state_update() -> None:
    model = _one_shell_model()
    displacement = np.linspace(0.0, 1.0e-4, model.mesh.dof_manager.total_dofs)
    active_force, active_tangent, active_states = _assemble_nonlinear_system(model, displacement, {}, 3, tangent=True)
    deleted_force, deleted_tangent, deleted_states = _assemble_nonlinear_system(
        model,
        displacement,
        active_states,
        3,
        tangent=True,
        deleted_element_ids=(1,),
        residual_stiffness_fraction=0.2,
    )
    assert np.linalg.norm(deleted_force) == pytest.approx(0.2 * np.linalg.norm(active_force), rel=1.0e-12)
    assert np.linalg.norm(deleted_tangent.toarray()) == pytest.approx(
        0.2 * np.linalg.norm(active_tangent.toarray()),
        rel=1.0e-12,
    )
    assert deleted_states[1] is active_states[1]


def test_deleted_pressure_loads_are_filtered_from_subsequent_load_vectors() -> None:
    model = _one_shell_model(curve=None)
    load = LoadCase("pressure")
    load.add_pressure_load(1, 11.0)
    full, _ = assemble_load_vector(model, load)
    filtered = filtered_load_case_for_deleted_elements(load, (1,))
    reduced, _ = assemble_load_vector(model, filtered)
    removed = deleted_pressure_load_resultant(model, load, (1,))

    assert np.linalg.norm(full) > 0.0
    assert np.linalg.norm(reduced) == pytest.approx(0.0)
    assert removed[2] == pytest.approx(11.0 * 1.0 * 0.2)


def test_plastic_strain_threshold_deletes_after_converged_increment() -> None:
    model = _one_shell_model()
    load = _tension_load(model)
    result = solve_static_nonlinear(
        model,
        load,
        num_steps=4,
        num_layers=3,
        fracture_config=FractureConfig(threshold=1.0e-5, max_deleted_fraction=1.0),
    )

    summary = result.info["fracture_summary"]
    assert summary["deleted_count"] == 1
    assert summary["deleted_element_ids"] == [1]
    assert summary["records"][0]["trigger_name"] == "max_equivalent_plastic_strain"
    assert summary["records"][0]["load_factor"] > 0.0
    assert any(step.deleted_element_count == 1 for step in result.steps)


def test_high_threshold_produces_no_deletions() -> None:
    model = _one_shell_model()
    result = solve_static_nonlinear(
        model,
        _tension_load(model),
        num_steps=4,
        num_layers=3,
        fracture_config=FractureConfig(threshold=1.0, max_deleted_fraction=1.0),
    )
    assert result.info["fracture_summary"]["deleted_count"] == 0
    assert all(step.deleted_element_count == 0 for step in result.steps)


def test_max_deleted_fraction_stops_after_converged_deletion() -> None:
    model = _one_shell_model()
    state = model.mesh.get_element(1).init_nonlinear_state(3)
    state["alpha"][:] = 0.01
    result = solve_static_nonlinear(
        model,
        _tension_load(model, stress=100.0e6),
        num_steps=2,
        num_layers=3,
        initial_element_states={1: state},
        fracture_config=FractureConfig(threshold=0.001, max_deleted_fraction=0.5),
    )
    assert result.status == "stopped_at_limit"
    assert result.failure_reason == "max_deleted_fraction_reached"
    assert result.info["fracture_summary"]["deleted_count"] == 1


def test_fracture_displacement_control_is_explicitly_unsupported() -> None:
    from anysolver.nonlinear_static import DisplacementControl

    model = _one_shell_model()
    with pytest.raises(ValueError, match="force control"):
        solve_static_nonlinear(
            model,
            _tension_load(model),
            control="displacement",
            displacement_control=DisplacementControl(node_id=2, dof="ux", target_displacement=1.0e-3),
            fracture_config=FractureConfig(threshold=1.0e-4),
        )
