"""Independent checks for the fixed-plane Q4 Newmark development slice."""

import math

import numpy as np
import pytest

from anysolver import (
    BoundaryCondition,
    ContactDefinition,
    ContactInteraction,
    ContactSurface,
    ContactTransientSolverControls,
    RigidContactBody,
    TransientConfig,
    TransientContactSettings,
    create_shell_element,
    solve_transient_contact,
)
from anysolver.fe_core import FEModel
from anysolver.general_contact.core import _PlanarQ4PlaneManager, active_contact_manager
from anysolver.general_contact.transient import _minimum_hermite_gap


def _guided_plate():
    model = FEModel("uniform_q4_impact")
    model.add_material("elastic", 1.0e5, 0.3, density=1.0)
    for node_id, xyz in enumerate(
        ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0),
         (1.0, 1.0, 0.0), (0.0, 1.0, 0.0)), 1
    ):
        model.add_node(node_id, *xyz)
    model.add_element(1, create_shell_element(
        1, [1, 2, 3, 4], "elastic", thickness=0.05,
    ))
    model.add_boundary_condition(BoundaryCondition(
        "guide", [1, 2, 3, 4],
        {name: 0.0 for name in ("ux", "uy", "rx", "ry", "rz")},
    ))
    contact = ContactDefinition(
        surfaces=(ContactSurface("skin", (1,)),),
        rigid_bodies=(RigidContactBody(
            "floor", "plane", (0.0, 0.0, -0.01), (0.0, 0.0, 1.0),
        ),),
        interactions=(ContactInteraction(
            "support", "skin", "floor", 1.0e5, 0.001,
        ),),
    )
    velocity = np.zeros(model.mesh.dof_manager.total_dofs)
    for node_id in (1, 2, 3, 4):
        velocity[model.mesh.dof_manager.get_node_dofs(node_id)[2]] = -1.0
    return model, contact, velocity


def test_uniform_impact_matches_independent_mass_spring_solution():
    model, contact, velocity = _guided_plate()
    result = solve_transient_contact(
        model, contact, TransientContactSettings(0.0002, 0.016, velocity),
    )
    # The guided plate has one rigid normal mode: m = density*area*thickness,
    # k = declared pressure stiffness*area.  Its first contact starts at .01 s.
    omega = math.sqrt(1.0e5 / 0.05)
    release_time = 0.01 + math.pi / omega
    exact_final_displacement = -0.01 + (0.016 - release_time)
    assert result.profile.endswith("NEWMARK_PENALTY_DEV_V1")
    assert result.times[-1] == pytest.approx(0.016)
    assert result.cutbacks == 0
    assert result.displacements[-1, 2] == pytest.approx(
        exact_final_displacement, abs=1.0e-5,
    )
    assert result.velocities[-1, 2] == pytest.approx(1.0, abs=0.01)
    assert min(result.swept_minimum_gaps) == pytest.approx(
        -1.0 / omega, abs=2.0e-6,
    )
    assert max(abs(value) for value in result.equilibrium_residuals) < 1.0e-7
    assert all(value.gap_tolerance_met for value in result.contact)
    assert active_contact_manager() is None
    finer_model, finer_contact, finer_velocity = _guided_plate()
    finer = solve_transient_contact(
        finer_model, finer_contact,
        TransientContactSettings(0.0001, 0.016, finer_velocity),
    )
    assert abs(finer.velocities[-1, 2] - 1.0) < abs(result.velocities[-1, 2] - 1.0)
    assert abs(finer.velocities[-1, 2] ** 2 - 1.0) < 0.01
    assert abs(finer.displacements[-1, 2] - exact_final_displacement) < 5.0e-6


def test_hermite_sweep_detects_interior_crossing_with_open_endpoints():
    model, contact, _ = _guided_plate()
    manager = _PlanarQ4PlaneManager(model, contact)
    size = model.mesh.dof_manager.total_dofs
    start = np.zeros(size)
    end = start.copy()
    first_velocity = np.zeros(size)
    last_velocity = np.zeros(size)
    for node_id in (1, 2, 3, 4):
        dof = model.mesh.dof_manager.get_node_dofs(node_id)[2]
        first_velocity[dof] = -10.0
        last_velocity[dof] = 10.0
    assert manager.evaluate(start)[2].minimum_gap == pytest.approx(0.01)
    assert manager.evaluate(end)[2].minimum_gap == pytest.approx(0.01)
    assert _minimum_hermite_gap(
        manager, start, end, first_velocity, last_velocity, 0.01,
    ) == pytest.approx(-0.015)


def test_rejected_step_leaves_model_reusable():
    model, contact, velocity = _guided_plate()
    with pytest.raises(RuntimeError, match="committed state retained"):
        solve_transient_contact(
            model, contact,
            TransientContactSettings(
                0.012, 0.012, velocity,
                maximum_newton_iterations=1, maximum_cutbacks=0,
            ),
        )
    assert active_contact_manager() is None
    result = solve_transient_contact(
        model, contact, TransientContactSettings(0.0002, 0.012, velocity),
    )
    assert result.times[-1] == pytest.approx(0.012)
    assert result.contact[-1].active_pressure_dofs > 0


def test_transient_config_initial_state_and_sparse_output_keep_event_checks():
    full_model, full_contact, velocity = _guided_plate()
    initial = np.zeros_like(velocity)
    for node_id in (1, 2, 3, 4):
        initial[full_model.mesh.dof_manager.get_node_dofs(node_id)[2]] = -0.002
    full = solve_transient_contact(
        full_model, full_contact,
        TransientConfig(0.0002, 0.012, initial_displacement=initial,
                        initial_velocity=velocity),
    )
    sampled_model, sampled_contact, sampled_velocity = _guided_plate()
    sampled = solve_transient_contact(
        sampled_model, sampled_contact,
        TransientConfig(0.0002, 0.012, save_every=7,
                        initial_displacement=initial,
                        initial_velocity=sampled_velocity),
        solver_controls=ContactTransientSolverControls(),
    )
    assert len(sampled.newton_iterations) == len(full.newton_iterations)
    assert len(sampled.times) < len(full.times)
    assert sampled.times[0] == 0.0
    assert sampled.times[-1] == pytest.approx(0.012)
    assert sampled.displacements[0, 2] == pytest.approx(-0.002)
    omega = math.sqrt(1.0e5 / 0.05)
    release_time = 0.008 + math.pi / omega
    assert sampled.displacements[-1, 2] == pytest.approx(
        -0.01 + (0.012 - release_time), abs=1.0e-5,
    )
    np.testing.assert_allclose(sampled.displacements[-1], full.displacements[-1])
    np.testing.assert_allclose(sampled.velocities[-1], full.velocities[-1])
    assert min(sampled.swept_minimum_gaps) == pytest.approx(
        min(full.swept_minimum_gaps), abs=1.0e-12,
    )
    assert max(sampled.equilibrium_residuals) == pytest.approx(
        max(full.equilibrium_residuals), abs=1.0e-12,
    )
    for output_index in range(1, len(sampled.times)):
        previous_step = int(np.argmin(np.abs(
            full.times - sampled.times[output_index - 1]
        )))
        current_step = int(np.argmin(np.abs(
            full.times - sampled.times[output_index]
        )))
        assert full.times[previous_step] == pytest.approx(
            sampled.times[output_index - 1], abs=1.0e-14,
        )
        assert full.times[current_step] == pytest.approx(
            sampled.times[output_index], abs=1.0e-14,
        )
        assert sampled.swept_minimum_gaps[output_index] == pytest.approx(
            min(full.swept_minimum_gaps[previous_step + 1:current_step + 1]),
            abs=1.0e-12,
        )
        assert sampled.equilibrium_residuals[output_index] == pytest.approx(
            max(full.equilibrium_residuals[previous_step + 1:current_step + 1]),
            abs=1.0e-12,
        )


@pytest.mark.parametrize("option", (
    {"beta": 0.3}, {"rayleigh_alpha": 0.01}, {"output_nodes": (1,)},
))
def test_transient_config_rejects_unadmitted_options(option):
    model, contact, velocity = _guided_plate()
    with pytest.raises(ValueError, match="not admitted|only undamped"):
        solve_transient_contact(
            model, contact,
            TransientConfig(0.0002, 0.001, initial_velocity=velocity, **option),
        )


def test_transient_config_rejects_inconsistent_initial_displacement():
    model, contact, velocity = _guided_plate()
    initial = np.zeros_like(velocity)
    initial[model.mesh.dof_manager.get_node_dofs(1)[0]] = 0.001
    with pytest.raises(ValueError, match="initial_displacement does not satisfy"):
        solve_transient_contact(
            model, contact,
            TransientConfig(0.0002, 0.001,
                            initial_displacement=initial,
                            initial_velocity=velocity),
        )
