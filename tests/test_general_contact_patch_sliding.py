"""Local physical work-map checks for mixed planar shell patches."""

import numpy as np
import pytest

from anysolver import (
    BoundaryCondition, ContactDefinition, ContactInteraction,
    ContactSolverSettings, ContactSurface, LoadCase, create_shell_element,
    solve_static_nonlinear, validate_general_contact,
)
from anysolver.fe_core import FEModel
from anysolver.general_contact.patch_sliding import _RestrictedSlidingPatchFEManager


def test_q4_against_two_s3_faces_uses_physical_offsets_and_shared_pressure():
    model = FEModel("mixed_patch_local")
    model.add_material("elastic", 1.0e5, 0.3, density=1.0)
    lower = ((0.2, 0.1), (1.2, 0.1), (1.2, 1.1), (0.2, 1.1))
    upper = ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0))
    for node, (x, y) in enumerate(lower, 1):
        model.add_node(node, x, y, 0.0)
    for node, (x, y) in enumerate(upper, 5):
        model.add_node(node, x, y, 0.04)
    for element, nodes in ((1, (1, 2, 3)), (2, (1, 3, 4))):
        model.add_element(element, create_shell_element(
            element, nodes, "elastic", thickness=0.05,
            formulation="e4-pl-s3-v2d", reference_normal=(0, 0, 1),
            reference_surface_offset=0.01,
        ))
    model.add_element(3, create_shell_element(
        3, (5, 6, 7, 8), "elastic", thickness=0.05,
    ))
    definition = ContactDefinition(
        surfaces=(ContactSurface("upper", (3,), side="bottom"),
                  ContactSurface("lower", (1, 2), side="top")),
        rigid_bodies=(),
        interactions=(ContactInteraction(
            "mixed", "upper", "lower", 1.0e6, 6.0e-6,
        ),),
    )
    settings = ContactSolverSettings(
        pair_motion="restricted_sliding", sliding_difference_step=1.0e-8,
    )
    report = validate_general_contact(model, definition, settings)
    assert report.valid, report.issues
    manager = _RestrictedSlidingPatchFEManager(model, definition, settings)
    assert len(manager.patch.source_node_ids) == 4
    assert len(manager.patch.target_node_ids) == 4
    displacement = np.zeros(model.mesh.dof_manager.total_dofs)
    for node in (5, 6, 7, 8):
        displacement[model.mesh.dof_manager.get_node_dofs(node)[2]] = -1.0e-6
    force, _tangent, summary = manager.evaluate(displacement, tangent=False)
    assert summary.overlapping_pairs == 2
    assert summary.current_overlap_area == pytest.approx(0.72)
    assert summary.integration_force[2] == pytest.approx(0.72, rel=1e-7)
    assert summary.target_force[2] == pytest.approx(-0.72, rel=1e-7)
    assert summary.gap_tolerance_met
    assert sum(force[model.mesh.dof_manager.get_node_dofs(node)[2]]
               for node in (5, 6, 7, 8)) == pytest.approx(-0.72)
    model.add_boundary_condition(BoundaryCondition(
        "lower_fixed", (1, 2, 3, 4),
        {name: 0.0 for name in ("ux", "uy", "uz", "rx", "ry", "rz")},
    ))
    model.add_boundary_condition(BoundaryCondition(
        "upper_guide", (5, 6, 7, 8),
        {name: 0.0 for name in ("ux", "uy", "rx", "ry", "rz")},
    ))
    load = LoadCase("press")
    for node in (5, 6, 7, 8):
        load.add_nodal_load(node, forces=(0.0, 0.0, -0.1))
    result = solve_static_nonlinear(
        model, load, contact=definition, contact_settings=settings,
        kinematics="von_karman", num_steps=1, max_iterations=12,
    )
    assert result.status == "completed", (
        result.failure_reason, result.load_factor, result.info.get("general_contact"),
    )
    coupled = result.info["general_contact"]
    assert coupled["gap_tolerance_met"]
    assert coupled["integration_force"][2] == pytest.approx(0.4, rel=1e-5)


def test_two_s3_integration_faces_share_four_material_pressure_nodes():
    model = FEModel("s3_integration_patch_local")
    model.add_material("elastic", 1.0e5, 0.3, density=1.0)
    lower = ((0.2, 0.1), (1.2, 0.1), (1.2, 1.1), (0.2, 1.1))
    upper = ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0))
    for node, (x, y) in enumerate(lower, 1):
        model.add_node(node, x, y, 0.0)
    for node, (x, y) in enumerate(upper, 5):
        model.add_node(node, x, y, 0.06)
    model.add_element(1, create_shell_element(
        1, (1, 2, 3, 4), "elastic", thickness=0.05,
    ))
    for element, nodes in ((2, (5, 6, 7)), (3, (5, 7, 8))):
        model.add_element(element, create_shell_element(
            element, nodes, "elastic", thickness=0.05,
            formulation="e4-pl-s3-v2d", reference_normal=(0, 0, 1),
            reference_surface_offset=0.01,
        ))
    definition = ContactDefinition(
        surfaces=(ContactSurface("upper", (2, 3), side="bottom"),
                  ContactSurface("lower", (1,), side="top")),
        rigid_bodies=(),
        interactions=(ContactInteraction(
            "mixed", "upper", "lower", 1.0e6, 6.0e-6,
        ),),
    )
    settings = ContactSolverSettings(
        pair_motion="restricted_sliding", sliding_difference_step=1.0e-8,
    )
    report = validate_general_contact(model, definition, settings)
    assert report.valid, report.issues
    manager = _RestrictedSlidingPatchFEManager(model, definition, settings)
    assert len(manager.patch.source_node_ids) == 4
    displacement = np.zeros(model.mesh.dof_manager.total_dofs)
    for node in (5, 6, 7, 8):
        displacement[model.mesh.dof_manager.get_node_dofs(node)[2]] = -1.0e-6
    _force, _tangent, summary = manager.evaluate(displacement, tangent=False)
    assert summary.overlapping_pairs == 2
    assert summary.pressure_rank == 4
    assert summary.current_overlap_area == pytest.approx(0.72)
    assert summary.integration_force[2] == pytest.approx(0.72, rel=1e-7)
    assert summary.target_force[2] == pytest.approx(-0.72, rel=1e-7)
    assert summary.gap_tolerance_met
