"""Bounded development probe for Q4 pressure resolution in one coupled path.

The two-column, one-row case reproduces the geometry and controls of the
existing two-Q4/two-S3 node-1 fixture. Additional rows or columns refine
the source Q4 pressure and structural mesh together. This script records
development evidence, not a qualification result.
"""

import argparse
from dataclasses import replace
import json
from pathlib import Path
import time

from anysolver import (
    BoundaryCondition, ContactDefinition, ContactInteraction,
    ContactPathControl, ContactPathProgram, ContactSolverSettings,
    ContactSurface, create_shell_element, solve_static_nonlinear,
    validate_general_contact,
)
from anysolver.fe_core import FEModel


def build_case(columns, rows=1, edge_control=False, *,
               gap_certificate="whole_face", gap_tolerance=0.005,
               normal_approach=0.01505):
    if columns < 2 or columns % 2:
        raise ValueError("columns must be an even integer of at least two")
    if rows < 1:
        raise ValueError("rows must be a positive integer")
    model = FEModel(
        f"general_contact_d1_{columns}_columns_{rows}_rows_"
        f"{'edge' if edge_control else 'node'}_control_{gap_certificate}"
    )
    model.add_material("elastic", 1.0e5, 0.3, density=1.0)
    stride = columns + 1
    source_nodes = tuple(range(1, (rows+1)*stride + 1))
    for row in range(rows+1):
        for column in range(stride):
            node = 1 + row*stride + column
            model.add_node(node, 0.1 + column/columns,
                           0.1 + row/rows, 0.055)
    target_nodes = tuple(range((rows+1)*stride + 1,
                               (rows+1)*stride + 5))
    for node, (x, y) in zip(target_nodes, (
        (-0.5, 0.0), (0.5, 0.0), (0.5, 1.0), (-0.5, 1.0),
    )):
        model.add_node(node, x, y, 0.0)
    for row in range(rows):
        for column in range(columns):
            element_id = 1+row*columns+column
            first = 1+row*stride+column
            nodes = (first, first+1, first+stride+1, first+stride)
            model.add_element(element_id, create_shell_element(
                element_id, nodes, "elastic", thickness=0.05,
                reference_normal=(0.0, 0.0, 1.0),
            ))
    face_count = columns*rows
    for element_id, nodes in (
        (face_count+1, (target_nodes[0], target_nodes[1], target_nodes[3])),
        (face_count+2, (target_nodes[1], target_nodes[2], target_nodes[3])),
    ):
        model.add_element(element_id, create_shell_element(
            element_id, nodes, "elastic", thickness=0.05,
            formulation="e4-pl-s3-v2d", reference_normal=(0.0, 0.0, 1.0),
            reference_surface_offset=0.01,
        ))
    definition = ContactDefinition(
        surfaces=(ContactSurface("q4_source", tuple(range(1, face_count+1)),
                                 "bottom"),
                  ContactSurface("s3_target", (face_count+1, face_count+2),
                                 "top")),
        rigid_bodies=(),
        interactions=(ContactInteraction(
            "pair", "q4_source", "s3_target", 1000.0, gap_tolerance,
            normal_law="augmented",
        ),),
    )
    settings = ContactSolverSettings(
        pair_motion="general", normal_discretization="primal_mortar",
        q4_source_gap_certificate=gap_certificate,
        general_s3_difference_step=2.0e-5,
        maximum_general_s3_energy_evaluations=5000*face_count,
        q4_source_area_tolerance=1.0e-9,
        q4_source_weighted_gap_tolerance=1.0e-10,
        maximum_q4_source_integration_triangles=128,
        pressure_tolerance=0.002,
        maximum_augmentations=7,
        augmentation_acceleration="supported_schur_dev",
        augmentation_schur_maximum_modes=16,
        augmentation_schur_maximum_pressure_pa=100.0,
        augmentation_schur_maximum_step_pa=50.0,
        augmentation_schur_difference_step_m=2.0e-6,
        augmentation_schur_maximum_attempts=2,
        augmentation_schur_maximum_relinearizations=1,
        general_s3_differentiation="jet2_q4_s3_dev",
        q4_source_support_gradient_tolerance=1.0e-5,
        q4_source_support_hessian_tolerance=1.0e-5,
        q4_source_weighted_gap_gradient_tolerance=1.0e-5,
        q4_source_weighted_gap_hessian_tolerance=1.0e-5,
    )
    model.add_boundary_condition(BoundaryCondition(
        "target_fixed", target_nodes,
        {name: 0.0 for name in ("ux", "uy", "uz", "rx", "ry", "rz")},
    ))
    model.add_boundary_condition(BoundaryCondition(
        "source_guide", source_nodes,
        {name: 0.0 for name in ("uy", "rx", "ry", "rz")},
    ))
    if edge_control:
        for row in range(1, rows+1):
            slave_node = 1+row*stride
            for axis, name in ((0, "ux"), (2, "uz")):
                master = int(model.mesh.dof_manager.get_node_dofs(1)[axis])
                slave = int(model.mesh.dof_manager.get_node_dofs(slave_node)[axis])
                model.add_constraint_equation(
                    terms=((slave, 1.0), (master, -1.0)),
                    dependent_dof=slave,
                    source_id=f"source_left_{name}_{slave_node}",
                )
    program = ContactPathProgram(
        controls=(ContactPathControl.node(1, "ux"),
                  ContactPathControl.node(1, "uz")),
        waypoints=((0.0, 0.0), (0.0, -normal_approach)),
        steps_per_segment=1,
    )
    return model, definition, settings, program


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("columns", type=int)
    parser.add_argument("output", type=Path)
    parser.add_argument("--rows", type=int, default=1)
    parser.add_argument("--edge-control", action="store_true")
    parser.add_argument("--gap-certificate", choices=("whole_face", "projected_matching"),
                        default="whole_face")
    parser.add_argument("--gap-tolerance", type=float, default=0.005)
    parser.add_argument("--normal-approach", type=float, default=0.01505)
    args = parser.parse_args()
    model, definition, settings, program = build_case(
        args.columns, args.rows, args.edge_control,
        gap_certificate=args.gap_certificate,
        gap_tolerance=args.gap_tolerance,
        normal_approach=args.normal_approach,
    )
    capability = validate_general_contact(model, definition, settings)
    if not capability.valid:
        raise ValueError(f"contact model invalid: {capability.issues}")
    start = time.perf_counter()
    result = solve_static_nonlinear(
        model, contact=definition, contact_settings=settings,
        contact_path_program=program, max_iterations=12,
        emit_restart_checkpoint=True,
    )
    record = {
        "columns": args.columns,
        "rows": args.rows,
        "edge_control": args.edge_control,
        "gap_certificate": args.gap_certificate,
        "gap_tolerance_m": args.gap_tolerance,
        "normal_approach_m": args.normal_approach,
        "elapsed_seconds": time.perf_counter()-start,
        "status": result.status,
        "failure_reason": result.failure_reason,
        "accepted_steps": len(result.steps),
        "contact_failure": result.info.get("contact_failure"),
        "force_displacement_history": result.info.get(
            "force_displacement_history"),
        "has_restart_checkpoint": result.restart_checkpoint is not None,
        "final_nodal_displacements": {
            str(node_id): [float(value) for value in result.displacements[
                model.mesh.get_node(node_id).dofs]]
            for node_id in (*range(1, (args.rows+1)*(args.columns+1)+1),
                            *range((args.rows+1)*(args.columns+1)+1,
                                   (args.rows+1)*(args.columns+1)+5))
        },
    }
    args.output.write_text(json.dumps(record, indent=2, default=str) + "\n",
                           encoding="utf-8")
    print(json.dumps({key: value for key, value in record.items()
                      if key not in ("contact_failure",
                                     "force_displacement_history",
                                     "final_nodal_displacements")},
                     indent=2))


if __name__ == "__main__":
    main()
