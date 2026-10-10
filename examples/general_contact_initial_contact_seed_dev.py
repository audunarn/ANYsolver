"""Development example: coupled 2x2 Q4/S3 contact with the initial-contact seed.

Run against an installed ANYsolver package. The opt-in
``initial_contact_seed='linearized_kkt_dev'`` selector adds one
origin-linearized KKT pressure proposal at the cold start of the explicit
contact path; every acceptance, derivative, integration and physical
commit gate is unchanged, and a refused seed leaves the origin untouched.

This example is UNVERIFIED to completion: no installed end-to-end
execution of this coupled fixture has finished under any recorded
receipt (the default-none reference half solve of the same fixture
diverged, and the seeded run reached its execution cap while still
running), so the printed status and seed record are not demonstrated
outputs. The passing source-bound checks (oracle, settings, real
validation and the static example contract) are not installed testing
and do not establish physical completion. The original completion
obligations — one completed coupled solve with the enabled seed and a
truthful comparison against the default-none reference — remain open.
D1 scientific acceptance and release remain open.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import replace

import numpy as np

from anysolver import (
    BoundaryCondition, ContactDefinition, ContactInteraction,
    ContactPathControl, ContactPathNodalForce, ContactPathProgram,
    ContactSolverSettings, ContactSurface, create_shell_element,
    solve_static_nonlinear,
)
from anysolver.fe_core import FEModel


def build_model():
    """Smallest physical 2x2 Q4 press patch: 20um gap, 0.04 N ramp."""
    columns = rows = 2
    stride = columns + 1
    slope = 1.0e-4
    normal = np.asarray((-slope, 0.0, 1.0))
    normal /= np.linalg.norm(normal)
    model = FEModel("initial_contact_seed_coupled_2x2_dev")
    model.add_material("elastic", 1.0e5, 0.3, density=1.0)
    source_reference_height = 0.04002/normal[2]
    for row in range(rows + 1):
        y = 0.1 + row/rows
        for column in range(stride):
            x = 0.1 + column/columns
            model.add_node(1 + row*stride + column, x, y,
                           source_reference_height + slope*(x - 0.65))
    target_nodes = tuple(range((rows + 1)*stride + 1,
                               (rows + 1)*stride + 1 + 4))
    target_positions = ((0.0, -0.1, 0.0), (1.3, -0.1, 0.0),
                        (1.3, 1.2, 0.0), (0.0, 1.2, 0.0))
    for node, (x, y, z) in zip(target_nodes, target_positions):
        model.add_node(node, x, y, z + slope*(x - 0.65))
    for row in range(rows):
        for column in range(columns):
            element_id = 1 + row*columns + column
            bottom = 1 + row*stride + column
            model.add_element(element_id, create_shell_element(
                element_id,
                (bottom, bottom + 1, bottom + stride + 1, bottom + stride),
                "elastic", thickness=0.05,
                reference_normal=tuple(normal),
            ))
    target_faces = ((target_nodes[0], target_nodes[1], target_nodes[3]),
                    (target_nodes[1], target_nodes[2], target_nodes[3]))
    for element_id, nodes in enumerate(target_faces,
                                       start=columns*rows + 1):
        model.add_element(element_id, create_shell_element(
            element_id, nodes, "elastic", thickness=0.05,
            formulation="e4-pl-s3-v2d",
            reference_normal=tuple(normal),
            reference_surface_offset=0.01,
        ))
    model.add_boundary_condition(BoundaryCondition(
        "source_lateral_guide", tuple(range(1, target_nodes[0])),
        {"uy": 0.0}))
    rim = (tuple(range(1, stride + 1))
           + tuple(node for row in range(1, rows)
                   for node in (1 + row*stride, (row + 1)*stride))
           + tuple(range(1 + rows*stride, 1 + (rows + 1)*stride)))
    model.add_boundary_condition(BoundaryCondition(
        "source_perimeter_support", rim, {"uz": 0.0}))
    model.add_boundary_condition(BoundaryCondition(
        "target_control_support", (target_nodes[0], target_nodes[3]),
        {name: 0.0 for name in ("ux", "uy", "uz", "rx", "ry", "rz")}))
    definition = ContactDefinition(
        surfaces=(
            ContactSurface("q4_source", tuple(range(1, columns*rows + 1)),
                           "bottom"),
            ContactSurface("s3_target", (columns*rows + 1, columns*rows + 2),
                           "top"),
        ),
        rigid_bodies=(),
        interactions=(ContactInteraction(
            "pair", "q4_source", "s3_target", 10000.0, 5.0e-5,
            normal_law="augmented"),),
    )
    settings = ContactSolverSettings(
        pair_motion="general", normal_discretization="primal_mortar",
        q4_source_gap_certificate="overlap_local_dev",
        q4_source_overlap_dual_dev=True,
        general_s3_difference_step=2.0e-5,
        maximum_general_s3_energy_evaluations=14144,
        maximum_candidate_pairs=max(32, columns*rows*len(target_faces)),
        q4_source_area_tolerance=1.0e-9,
        q4_source_weighted_gap_tolerance=1.0e-10,
        maximum_q4_source_integration_triangles=300,
        general_s3_differentiation="jet2_q4_s3_dev",
        q4_source_support_gradient_tolerance=1.0e-5,
        q4_source_support_hessian_tolerance=1.0e-5,
        q4_source_weighted_gap_gradient_tolerance=1.0e-5,
        q4_source_weighted_gap_hessian_tolerance=1.0e-5,
        pressure_tolerance=1.0e-5, maximum_augmentations=7,
        enforcement_solver="monolithic_active_set",
        complementarity_force_scale_n=0.04,
        d1_interior_profile=True,
        d1_interior_coverage_tolerance_m2=1.0e-10,
        d1_interior_boundary_force_tolerance_n=1.0e-10,
        path_continuation_maximum_halvings=6,
    )
    interior_load_node = 1 + stride + 1
    program = ContactPathProgram(
        controls=(ContactPathControl.node(1, "ux"),
                  ContactPathControl.node(columns + 2, "ux")),
        waypoints=((0.0, 0.0), (0.0, 0.0)), steps_per_segment=2,
        nodal_forces=(ContactPathNodalForce(
            interior_load_node, "uz", (0.0, -0.04)),),
    )
    return model, definition, settings, program


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", default="linearized_kkt_dev",
                        choices=("none", "linearized_kkt_dev"),
                        help="initial_contact_seed selector")
    parser.add_argument("--max-load-factor", type=float, default=0.5)
    options = parser.parse_args()
    model, definition, settings, program = build_model()
    settings = replace(settings, initial_contact_seed=options.seed)
    result = solve_static_nonlinear(
        model, contact=definition, contact_settings=settings,
        contact_path_program=program, max_iterations=18,
        max_load_factor=options.max_load_factor,
        emit_restart_checkpoint=True,
    )
    print(json.dumps({
        "initial_contact_seed": options.seed,
        "status": result.status,
        "steps": len(result.steps),
        "failure_reason": result.failure_reason,
        "seed_record": result.info.get("contact_initial_seed"),
        "interior_displacement_m":
            float(result.displacements[model.mesh.dof_manager
                                       .get_node_dofs(1 + 3 + 1)[2]]),
    }, indent=2, sort_keys=True))
    return 0 if result.status == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
