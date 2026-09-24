"""B2 round beam pressing across the internal seam of two planar Q4 faces.

Run after installing ANYsolver: python examples/general_contact_round_beam_shell_patch.py
All dimensions use SI units. This is a development example, not qualification.
"""

from anysolver import (
    BoundaryCondition, ContactDefinition, ContactInteraction,
    ContactSolverSettings, ContactSurface, LoadCase, create_shell_element,
    solve_static_nonlinear, validate_general_contact,
)
from anysolver.elements import BeamElement
from anysolver.fe_core import FEModel


def main() -> None:
    model = FEModel("beam_across_internal_shell_seam")
    model.add_material("elastic", 1.0e3, 0.3, density=1.0)
    for node, point in enumerate((
        (-0.5, 0.0, 0.025), (0.5, 0.0, 0.025),
        (-1.0, -1.0, 0.0), (0.0, -1.0, 0.0),
        (0.0, 1.0, 0.0), (-1.0, 1.0, 0.0),
        (1.0, -1.0, 0.0), (1.0, 1.0, 0.0),
    ), 1):
        model.add_node(node, *point)
    model.add_element(1, BeamElement(
        1, [1, 2], "elastic",
        {"area": 1.0e-3, "Iy": 1.0e-4, "Iz": 1.0e-4, "J": 1.0e-4},
    ))
    for eid, nodes in ((2, (3, 4, 5, 6)), (3, (4, 7, 8, 5))):
        model.add_element(eid, create_shell_element(
            eid, nodes, "elastic", thickness=0.02, formulation="e4-pl",
            reference_normal=(0, 0, 1),
        ))
    model.add_boundary_condition(BoundaryCondition(
        "fixed_skin", (3, 4, 5, 6, 7, 8),
        {name: 0.0 for name in ("ux", "uy", "uz", "rx", "ry", "rz")},
    ))
    model.add_boundary_condition(BoundaryCondition(
        "fixed_beam_root", (1,),
        {name: 0.0 for name in ("ux", "uy", "uz", "rx", "ry", "rz")},
    ))
    model.add_boundary_condition(BoundaryCondition(
        "guided_beam_tip", (2,),
        {name: 0.0 for name in ("ux", "uy", "rx", "ry", "rz")},
    ))
    load = LoadCase("press_across_seam")
    load.add_nodal_load(2, forces=(0.0, 0.0, -1.0))
    definition = ContactDefinition(
        surfaces=(ContactSurface("tube", (1,), beam_radius=0.01),
                  ContactSurface("skin", (2, 3), side="top")),
        rigid_bodies=(),
        interactions=(ContactInteraction(
            "line_skin", "tube", "skin", None, 0.002,
            line_stiffness=1.0e4,
        ),),
    )
    settings = ContactSolverSettings(
        pair_motion="general", beam_shell_rim_clearance=0.02,
        beam_shell_difference_step=1.0e-8,
        line_integration_relative_tolerance=1.0e-8,
    )
    report = validate_general_contact(model, definition, settings)
    if not report.valid:
        raise RuntimeError("; ".join(report.issues))
    result = solve_static_nonlinear(
        model, load, contact=definition, contact_settings=settings,
        kinematics="von_karman", num_steps=2, max_iterations=12,
        emit_restart_checkpoint=True,
    )
    if result.status != "completed":
        raise RuntimeError(result.failure_reason)
    contact = result.info["general_contact"]
    print("profile:", contact["profile"])
    print("minimum gap [m]:", contact["minimum_gap"])
    print("beam force [N]:", contact["beam_force"])
    print("shell force [N]:", contact["shell_force"])
    print("minimum exterior rim clearance [m]:", contact["minimum_rim_clearance"])
    print("checkpoint version:", result.to_restart_checkpoint()["version"])


if __name__ == "__main__":
    main()
