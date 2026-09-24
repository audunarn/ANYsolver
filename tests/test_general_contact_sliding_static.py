"""End-to-end development checks for explicitly selected restricted sliding."""

import numpy as np
import pytest

from anysolver import (
    BoundaryCondition,
    ContactDefinition,
    ContactInteraction,
    ContactSolverSettings,
    ContactSurface,
    DisplacementControl,
    LoadCase,
    create_shell_element,
    solve_static_nonlinear,
    validate_general_contact,
)
from anysolver.fe_core import FEModel


def test_restricted_sliding_pair_runs_through_nonlinear_static():
    model = FEModel("restricted_sliding_static")
    model.add_material("elastic", 1.0e5, 0.3, density=1.0)
    corners = ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0))
    for node, (x, y) in enumerate(corners, 1):
        model.add_node(node, x, y, 0.0)
    for node, (x, y) in enumerate(corners, 5):
        model.add_node(node, x + 0.2, y + 0.1, 0.05)
    for element, nodes in ((1, (1, 2, 3, 4)), (2, (5, 6, 7, 8))):
        model.add_element(element, create_shell_element(
            element, nodes, "elastic", thickness=0.05,
        ))
    model.add_boundary_condition(BoundaryCondition(
        "lower_fixed", (1, 2, 3, 4),
        {name: 0.0 for name in ("ux", "uy", "uz", "rx", "ry", "rz")},
    ))
    model.add_boundary_condition(BoundaryCondition(
        "upper_guided", (5, 6, 7, 8),
        {name: 0.0 for name in ("ux", "uy", "rx", "ry", "rz")},
    ))
    load = LoadCase("press")
    for node in (5, 6, 7, 8):
        load.add_nodal_load(node, forces=(0.0, 0.0, -0.1))
    contact = ContactDefinition(
        surfaces=(ContactSurface("upper", (2,), side="bottom"),
                  ContactSurface("lower", (1,), side="top")),
        rigid_bodies=(),
        interactions=(ContactInteraction(
            "pair", "upper", "lower", 1.0e6, 6.0e-6,
        ),),
    )
    settings = ContactSolverSettings(
        pair_motion="restricted_sliding", sliding_difference_step=1.0e-8,
    )
    report = validate_general_contact(model, contact, settings)
    assert report.valid
    assert "RESTRICTED_SLIDING" in report.profile
    result = solve_static_nonlinear(
        model, load, contact=contact, contact_settings=settings,
        kinematics="von_karman", num_steps=1, max_iterations=12,
    )
    assert result.status == "completed", (
        result.failure_reason, result.load_factor,
        result.info.get("general_contact"), len(result.steps),
    )
    summary = result.info["general_contact"]
    assert summary["gap_tolerance_met"]
    assert summary["current_overlap_area"] == pytest.approx(0.72)
    np.testing.assert_allclose(
        np.asarray(summary["integration_force"])
        + np.asarray(summary["target_force"]),
        0.0, atol=1.0e-6,
    )
    assert summary["integration_force"][2] == pytest.approx(0.4, rel=1e-5)
    half = solve_static_nonlinear(
        model, load, contact=contact, contact_settings=settings,
        kinematics="von_karman", num_steps=1, max_iterations=12,
        max_load_factor=0.5, emit_restart_checkpoint=True,
    )
    assert half.status == "completed", half.failure_reason
    assert half.restart_checkpoint["version"] == 2
    resumed = solve_static_nonlinear(
        model, load, contact=contact, contact_settings=settings,
        kinematics="von_karman", num_steps=1, max_iterations=12,
        max_load_factor=1.0,
        restart_checkpoint=half.to_restart_checkpoint(),
    )
    assert resumed.status == "completed", resumed.failure_reason
    np.testing.assert_allclose(
        resumed.displacements, result.displacements, rtol=1.0e-7, atol=1.0e-9,
    )
    assert resumed.info["general_contact"]["integration_force"] == pytest.approx(
        summary["integration_force"], rel=1.0e-7, abs=1.0e-7,
    )
    with pytest.raises(ValueError, match="analysis contract is incompatible"):
        solve_static_nonlinear(
            model, load, contact=contact,
            contact_settings=ContactSolverSettings(
                pair_motion="restricted_sliding", sliding_difference_step=2.0e-8,
            ),
            kinematics="von_karman", num_steps=1, max_iterations=12,
            max_load_factor=1.0,
            restart_checkpoint=half.to_restart_checkpoint(),
        )


def test_restricted_sliding_pair_follows_prescribed_lateral_path():
    model = FEModel("restricted_sliding_displacement_path")
    model.add_material("elastic", 1.0e5, 0.3, density=1.0)
    corners = ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0))
    for node, (x, y) in enumerate(corners, 1):
        model.add_node(node, x, y, 0.0)
    for node, (x, y) in enumerate(corners, 5):
        model.add_node(node, x + 0.2, y + 0.1, 0.05)
    for element, nodes in ((1, (1, 2, 3, 4)), (2, (5, 6, 7, 8))):
        model.add_element(element, create_shell_element(
            element, nodes, "elastic", thickness=0.05,
        ))
    model.add_boundary_condition(BoundaryCondition(
        "lower_fixed", (1, 2, 3, 4),
        {name: 0.0 for name in ("ux", "uy", "uz", "rx", "ry", "rz")},
    ))
    model.add_boundary_condition(BoundaryCondition(
        "upper_lateral_guide", (5, 6, 7, 8),
        {name: 0.0 for name in ("uy", "rx", "ry", "rz")},
    ))
    master_x = int(model.mesh.dof_manager.get_node_dofs(5)[0])
    for node in (6, 7, 8):
        slave_x = int(model.mesh.dof_manager.get_node_dofs(node)[0])
        model.add_constraint_equation(
            terms=((slave_x, 1.0), (master_x, -1.0)),
            source_id=f"upper_uniform_x_{node}",
        )
    press = LoadCase("press")
    for node in (5, 6, 7, 8):
        press.add_nodal_load(node, forces=(0.0, 0.0, -0.1))
    drive = LoadCase("lateral_drive")
    drive.add_nodal_load(5, forces=(1.0, 0.0, 0.0))
    contact = ContactDefinition(
        surfaces=(ContactSurface("upper", (2,), side="bottom"),
                  ContactSurface("lower", (1,), side="top")),
        rigid_bodies=(),
        interactions=(ContactInteraction(
            "pair", "upper", "lower", 1.0e6, 6.0e-6,
        ),),
    )
    settings = ContactSolverSettings(
        pair_motion="restricted_sliding", sliding_difference_step=1.0e-8,
    )
    result = solve_static_nonlinear(
        model, drive, constant_load_case=press,
        contact=contact, contact_settings=settings, kinematics="von_karman",
        control="displacement",
        displacement_control=DisplacementControl(
            node_id=5, dof="ux", target_displacement=0.1,
        ),
        num_steps=2, max_iterations=12,
    )
    assert result.status == "completed", (
        result.failure_reason, result.load_factor, result.info.get("general_contact"),
    )
    summary = result.info["general_contact"]
    assert summary["current_overlap_area"] == pytest.approx(0.63, rel=1e-8)
    assert summary["gap_tolerance_met"]
    assert summary["integration_force"][2] == pytest.approx(0.4, rel=1e-5)
