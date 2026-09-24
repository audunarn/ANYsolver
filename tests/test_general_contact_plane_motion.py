"""Prescribed plane translation through the guided shell-pressure profile."""

from dataclasses import replace

import numpy as np
import pytest

from anysolver import (
    BoundaryCondition, ContactDefinition, ContactInteraction,
    ContactSolverSettings, ContactSurface, LoadCase, NonlinearConvergenceSettings,
    RigidContactBody, create_shell_element, solve_static_nonlinear,
    validate_general_contact,
)
from anysolver.fe_core import FEModel
from anysolver.general_contact.core import _PlanarQ4PlaneManager


def _moving_plane():
    model = FEModel("q4_moving_plane")
    model.add_material("elastic", 1.0e5, 0.3, density=1.0)
    for node_id, (x, y) in enumerate((
        (-0.1, -0.1), (0.1, -0.1), (0.1, 0.1), (-0.1, 0.1),
    ), 1):
        model.add_node(node_id, x, y, -0.01)
    model.add_element(1, create_shell_element(
        1, (1, 2, 3, 4), "elastic", thickness=0.02,
    ))
    definition = ContactDefinition(
        surfaces=(ContactSurface("skin", (1,), side="top"),),
        rigid_bodies=(RigidContactBody(
            "tool", "plane", (0.0, 0.0, -0.002),
            normal=(0.0, 0.0, 1.0),
            path_translation=(0.0, 0.0, 0.003),
        ),),
        interactions=(ContactInteraction(
            "skin_tool", "skin", "tool", 1.0e5, 4.0e-3,
        ),),
    )
    return model, definition, ContactSolverSettings(pair_motion="guided")


def test_moving_plane_relative_motion_gap_work_and_restart_contract():
    model, definition, settings = _moving_plane()
    report = validate_general_contact(model, definition, settings)
    assert report.valid and "TRANSLATING_PLANE" in report.profile
    manager = _PlanarQ4PlaneManager(model, definition, settings)
    zero = np.zeros(model.mesh.dof_manager.total_dofs)
    assert manager.evaluate(zero, tangent=False)[2].minimum_gap == pytest.approx(0.002)
    manager.set_path_factor(1.0)
    moving_force, _K, result = manager.evaluate(zero, tangent=False)
    assert result.minimum_gap == pytest.approx(-0.001)
    assert result.active_pressure_dofs > 0
    assert manager.restart_contract()["rigid_bodies"][0]["path_translation"] == [
        0.0, 0.0, 0.003,
    ]
    fixed = replace(definition, rigid_bodies=(replace(
        definition.rigid_bodies[0], path_translation=None,
    ),))
    fixed_manager = _PlanarQ4PlaneManager(model, fixed, settings)
    downward = zero.copy()
    for node_id in range(1, 5):
        downward[model.mesh.dof_manager.get_node_dofs(node_id)[2]] = -0.003
    fixed_force, _K, fixed_result = fixed_manager.evaluate(
        downward, tangent=False,
    )
    np.testing.assert_allclose(fixed_force, moving_force, atol=1.0e-9)
    assert fixed_result.penalty_energy == pytest.approx(result.penalty_energy)
    assert "path_translation" not in fixed_manager.restart_contract()["rigid_bodies"][0]
    assert manager.swept_increment_admissible(zero, zero, 0.0, 1.0)
    assert not manager.swept_increment_admissible(zero, zero, 0.0, 3.0)


def test_moving_plane_s3_physical_offset():
    model = FEModel("s3_moving_plane")
    model.add_material("elastic", 1.0e5, 0.3, density=1.0)
    for node_id, (x, y) in enumerate(((0.0, 0.0), (1.0, 0.0),
                                      (0.0, 1.0)), 1):
        model.add_node(node_id, x, y, 0.035)
    model.add_element(1, create_shell_element(
        1, (1, 2, 3), "elastic", formulation="e4-pl-s3-v2d",
        thickness=0.05, reference_normal=(0, 0, 1),
        reference_surface_offset=0.01,
    ))
    definition = ContactDefinition(
        surfaces=(ContactSurface("skin", (1,), side="bottom"),),
        rigid_bodies=(RigidContactBody(
            "tool", "plane", (0.0, 0.0, 0.0),
            normal=(0.0, 0.0, 1.0),
            path_translation=(0.0, 0.0, 0.001),
        ),),
        interactions=(ContactInteraction(
            "skin_tool", "skin", "tool", 1.0e6, 0.002,
        ),),
    )
    manager = _PlanarQ4PlaneManager(model, definition)
    zero = np.zeros(model.mesh.dof_manager.total_dofs)
    manager.set_path_factor(1.0)
    moving_force, _K, result = manager.evaluate(zero, tangent=False)
    assert result.minimum_gap == pytest.approx(-0.001)
    assert result.active_pressure_dofs > 0
    fixed = replace(definition, rigid_bodies=(replace(
        definition.rigid_bodies[0], path_translation=None,
    ),))
    fixed_manager = _PlanarQ4PlaneManager(model, fixed)
    downward = zero.copy()
    for node_id in (1, 2, 3):
        downward[model.mesh.dof_manager.get_node_dofs(node_id)[2]] = -0.001
    fixed_force, _K, fixed_result = fixed_manager.evaluate(
        downward, tangent=False,
    )
    np.testing.assert_allclose(moving_force, fixed_force, atol=1.0e-9)
    assert fixed_result.penalty_energy == pytest.approx(result.penalty_energy)


def test_fast_moving_plane_cuts_back_before_uncertified_pose():
    model, definition, settings = _moving_plane()
    fast = replace(definition, rigid_bodies=(replace(
        definition.rigid_bodies[0], path_translation=(0.0, 0.0, 0.03),
    ),))
    model.add_boundary_condition(BoundaryCondition(
        "guide", (1, 2, 3, 4),
        {name: 0.0 for name in ("ux", "uy", "rx", "ry", "rz")},
    ))
    model.add_boundary_condition(BoundaryCondition("normal_anchor", (1,),
                                                    {"uz": 0.0}))
    result = solve_static_nonlinear(
        model, LoadCase("fast_plane"), contact=fast,
        contact_settings=settings, num_steps=1,
        min_step_fraction=0.125, max_iterations=18,
    )
    assert result.info["general_contact"]["swept_trial_cutbacks"] > 0
    assert result.info["general_contact"]["gap_tolerance_met"]


def test_moving_plane_s3_force_control():
    model = FEModel("s3_moving_plane_static")
    model.add_material("elastic", 1.0e5, 0.3, density=1.0)
    for node_id, (x, y) in enumerate(((0.0, 0.0), (1.0, 0.0),
                                      (0.0, 1.0)), 1):
        model.add_node(node_id, x, y, 0.035)
    model.add_element(1, create_shell_element(
        1, (1, 2, 3), "elastic", formulation="e4-pl-s3-v2d",
        thickness=0.05, reference_normal=(0, 0, 1),
        reference_surface_offset=0.01,
    ))
    model.add_boundary_condition(BoundaryCondition(
        "guide", (1, 2, 3),
        {name: 0.0 for name in ("ux", "uy", "rx", "ry", "rz")},
    ))
    model.add_boundary_condition(BoundaryCondition("normal_anchor", (1,),
                                                    {"uz": 0.0}))
    definition = ContactDefinition(
        surfaces=(ContactSurface("skin", (1,), side="bottom"),),
        rigid_bodies=(RigidContactBody(
            "tool", "plane", (0.0, 0.0, -1.0e-6),
            normal=(0.0, 0.0, 1.0),
            path_translation=(0.0, 0.0, 2.0e-6),
        ),),
        interactions=(ContactInteraction(
            "skin_tool", "skin", "tool", 1.0e6, 2.0e-6,
        ),),
    )
    result = solve_static_nonlinear(
        model, LoadCase("s3_plane_drive"), contact=definition,
        contact_settings=ContactSolverSettings(pair_motion="guided"),
        num_steps=4, max_iterations=18, emit_restart_checkpoint=True,
    )
    assert result.status == "completed", result.failure_reason
    summary = result.info["general_contact"]
    assert summary["active_pressure_dofs"] > 0
    assert summary["gap_tolerance_met"]
    assert summary["rigid_contact_work_trapezoid"] < 0.0
    assert result.restart_checkpoint["version"] == 2


def test_moving_plane_force_path_work_and_restart():
    model, definition, settings = _moving_plane()
    model.add_boundary_condition(BoundaryCondition(
        "guide", (1, 2, 3, 4),
        {name: 0.0 for name in ("ux", "uy", "rx", "ry", "rz")},
    ))
    model.add_boundary_condition(BoundaryCondition("normal_anchor", (1,),
                                                    {"uz": 0.0}))
    policy = NonlinearConvergenceSettings(growth_factor=1.0,
                                          max_step_factor=1.0)

    def solve(factor, steps, checkpoint=None, contact=definition):
        return solve_static_nonlinear(
            model, LoadCase("plane_drive"), contact=contact,
            contact_settings=settings, convergence_settings=policy,
            max_load_factor=factor, num_steps=steps, max_iterations=18,
            restart_checkpoint=checkpoint, emit_restart_checkpoint=True,
        )

    full = solve(1.0, 8)
    assert full.status == "completed", full.failure_reason
    summary = full.info["general_contact"]
    assert summary["active_pressure_dofs"] > 0
    assert summary["gap_tolerance_met"]
    assert summary["rigid_tool_position"][2] == pytest.approx(0.001)
    assert summary["rigid_contact_work_trapezoid"] < 0.0
    assert summary["prescribed_actuator_work_trapezoid"] > 0.0
    np.testing.assert_allclose(summary["shell_force"],
                               -np.asarray(summary["rigid_force"]), atol=1.0e-9)
    half = solve(0.5, 4)
    assert half.status == "completed", half.failure_reason
    resumed = solve(1.0, 8, checkpoint=half.to_restart_checkpoint())
    assert resumed.status == "completed", resumed.failure_reason
    np.testing.assert_allclose(resumed.displacements, full.displacements,
                               rtol=1.0e-6, atol=1.0e-8)
    assert resumed.info["general_contact"]["rigid_contact_work_trapezoid"] == pytest.approx(
        summary["rigid_contact_work_trapezoid"], rel=1.0e-5, abs=1.0e-8,
    )
    changed_motion = replace(definition, rigid_bodies=(replace(
        definition.rigid_bodies[0], path_translation=(0.0, 0.0, 0.004),
    ),))
    with pytest.raises(ValueError, match="restart|incompatible|contract"):
        solve(1.0, 8, checkpoint=half.to_restart_checkpoint(),
              contact=changed_motion)
