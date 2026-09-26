"""Bounded development probe for Q4 pressure resolution in one coupled path.

The two-column case reproduces the geometry and controls of the existing
two-Q4/two-S3 node-1 fixture. Additional columns refine only the source Q4
pressure/structural mesh. This script records development evidence, not a
qualification result.
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


def build_case(columns):
    if columns < 2 or columns % 2:
        raise ValueError("columns must be an even integer of at least two")
    model = FEModel(f"general_contact_d1_{columns}_columns")
    model.add_material("elastic", 1.0e5, 0.3, density=1.0)
    stride = columns + 1
    source_nodes = tuple(range(1, 2*stride + 1))
    for row in range(2):
        for column in range(stride):
            node = 1 + row*stride + column
            model.add_node(node, 0.1 + column/columns, 0.1 + row, 0.055)
    target_nodes = tuple(range(2*stride + 1, 2*stride + 5))
    for node, (x, y) in zip(target_nodes, (
        (-0.5, 0.0), (0.5, 0.0), (0.5, 1.0), (-0.5, 1.0),
    )):
        model.add_node(node, x, y, 0.0)
    for column in range(columns):
        nodes = (1+column, 2+column, stride+2+column, stride+1+column)
        model.add_element(column+1, create_shell_element(
            column+1, nodes, "elastic", thickness=0.05,
            reference_normal=(0.0, 0.0, 1.0),
        ))
    for element_id, nodes in (
        (columns+1, (target_nodes[0], target_nodes[1], target_nodes[3])),
        (columns+2, (target_nodes[1], target_nodes[2], target_nodes[3])),
    ):
        model.add_element(element_id, create_shell_element(
            element_id, nodes, "elastic", thickness=0.05,
            formulation="e4-pl-s3-v2d", reference_normal=(0.0, 0.0, 1.0),
            reference_surface_offset=0.01,
        ))
    definition = ContactDefinition(
        surfaces=(ContactSurface("q4_source", tuple(range(1, columns+1)),
                                 "bottom"),
                  ContactSurface("s3_target", (columns+1, columns+2),
                                 "top")),
        rigid_bodies=(),
        interactions=(ContactInteraction(
            "pair", "q4_source", "s3_target", 1000.0, 0.005,
            normal_law="augmented",
        ),),
    )
    settings = ContactSolverSettings(
        pair_motion="general", normal_discretization="primal_mortar",
        general_s3_difference_step=2.0e-5,
        maximum_general_s3_energy_evaluations=5000*columns,
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
    program = ContactPathProgram(
        controls=(ContactPathControl.node(1, "ux"),
                  ContactPathControl.node(1, "uz")),
        waypoints=((0.0, 0.0), (0.0, -0.01505)),
        steps_per_segment=1,
    )
    return model, definition, settings, program


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("columns", type=int)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    model, definition, settings, program = build_case(args.columns)
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
        "elapsed_seconds": time.perf_counter()-start,
        "status": result.status,
        "failure_reason": result.failure_reason,
        "accepted_steps": len(result.steps),
        "contact_failure": result.info.get("contact_failure"),
        "force_displacement_history": result.info.get(
            "force_displacement_history"),
        "has_restart_checkpoint": result.restart_checkpoint is not None,
    }
    args.output.write_text(json.dumps(record, indent=2, default=str) + "\n",
                           encoding="utf-8")
    print(json.dumps({key: value for key, value in record.items()
                      if key not in ("contact_failure",
                                     "force_displacement_history")},
                     indent=2))


if __name__ == "__main__":
    main()
