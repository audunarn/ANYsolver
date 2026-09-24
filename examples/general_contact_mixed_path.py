"""Press, slide, open and recontact a Q4/S3 shell patch pair.

Run from the repository root with the installed package on Python's path:
    python examples/general_contact_mixed_path.py
"""

from __future__ import annotations

import json

from anysolver import (
    BoundaryCondition, ContactDefinition, ContactInteraction,
    ContactPathControl, ContactPathProgram, ContactSolverSettings,
    ContactSurface, create_shell_element, solve_static_nonlinear,
    validate_general_contact,
)
from anysolver.fe_core import FEModel


def main() -> None:
    model = FEModel("restricted_mixed_patch_sliding_example")
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
    model.add_boundary_condition(BoundaryCondition(
        "lower_fixed", (1, 2, 3, 4),
        {dof: 0.0 for dof in ("ux", "uy", "uz", "rx", "ry", "rz")},
    ))
    model.add_boundary_condition(BoundaryCondition(
        "upper_guide", (5, 6, 7, 8),
        {dof: 0.0 for dof in ("uy", "rx", "ry", "rz")},
    ))
    master = int(model.mesh.dof_manager.get_node_dofs(5)[0])
    for node in (6, 7, 8):
        slave = int(model.mesh.dof_manager.get_node_dofs(node)[0])
        model.add_constraint_equation(
            terms=((slave, 1.0), (master, -1.0)),
            source_id=f"uniform_upper_x_{node}",
        )
    definition = ContactDefinition(
        surfaces=(ContactSurface("upper_bottom", (3,), side="bottom"),
                  ContactSurface("lower_top", (1, 2), side="top")),
        rigid_bodies=(),
        interactions=(ContactInteraction(
            "patch_pair", "upper_bottom", "lower_top", 1.0e6, 6.0e-6,
        ),),
    )
    settings = ContactSolverSettings(
        pair_motion="restricted_sliding", sliding_difference_step=1.0e-8,
    )
    report = validate_general_contact(model, definition, settings)
    if not report.valid:
        raise RuntimeError("unsupported contact: " + "; ".join(report.issues))
    program = ContactPathProgram(
        controls=(
            ContactPathControl.node(5, "ux"),
            ContactPathControl(tuple((node, "uz", 0.25)
                                     for node in (5, 6, 7, 8))),
        ),
        waypoints=((0.0, 0.0), (0.0, -5.0e-7),
                   (0.1, -5.0e-7), (0.1, 1.0e-6),
                   (0.1, -5.0e-7)),
        steps_per_segment=1,
    )
    result = solve_static_nonlinear(
        model, contact=definition, contact_settings=settings,
        contact_path_program=program,
        max_iterations=15, emit_restart_checkpoint=True,
    )
    summary = result.info.get("general_contact", {})
    if result.status != "completed" or not summary.get("gap_tolerance_met", False):
        raise RuntimeError(f"contact stopped: {result.status}: {result.failure_reason}")
    print(json.dumps({
        "profile": result.info["contact_path"]["profile"],
        "status": result.status,
        "accepted_steps": len(result.steps),
        "phase_contact": [
            {
                "target_m": record["target"],
                "active_pressure_dofs": record["contact"]["active_pressure_dofs"],
                "lower_gap_m": record["contact"]["conservative_lower_gap"],
                "normal_force_N": record["contact"]["integration_force"][2],
            }
            for record in result.info["force_displacement_history"]
        ],
        "overlapping_face_pairs": summary["overlapping_pairs"],
        "current_overlap_area_m2": summary["current_overlap_area"],
        "restart_checkpoint_version": result.restart_checkpoint["version"],
    }, indent=2))


if __name__ == "__main__":
    main()
