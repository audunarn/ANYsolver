"""Development probe for mesh-consistent finite-area Q4/S3 contact loading.

This case separates response refinement from the left-edge displacement fixture.
Its source patch, target, distributed load and supported edge occupy the same
physical region at every mesh size. Results are exploratory, not qualification.
"""

import argparse
import json
from pathlib import Path
import time

from anysolver import (
    BoundaryCondition, ContactDefinition, ContactInteraction,
    ContactSolverSettings, ContactSurface, LoadCase, create_shell_element,
    solve_static_nonlinear, validate_general_contact,
)
from anysolver.fe_core import FEModel


def build_case(divisions: int, *, total_load_n: float = 0.4,
               normal_stiffness: float = 1000.0):
    if divisions < 2 or divisions % 2:
        raise ValueError("divisions must be an even integer of at least two")
    model = FEModel(f"general_contact_finite_area_{divisions}")
    model.add_material("elastic", 1.0e5, 0.3, density=1.0)
    stride = divisions + 1
    source_nodes = tuple(range(1, stride*stride + 1))
    for row in range(stride):
        for column in range(stride):
            model.add_node(1 + row*stride + column,
                           0.1 + column/divisions, 0.1 + row/divisions,
                           0.04005)
    target_nodes = tuple(range(stride*stride + 1, stride*stride + 5))
    for node, (x, y) in zip(target_nodes, (
        (0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0),
    )):
        model.add_node(node, x, y, 0.0)

    source_elements = []
    load_weights = {node: 0.0 for node in source_nodes}
    for row in range(divisions):
        for column in range(divisions):
            element_id = 1 + row*divisions + column
            first = 1 + row*stride + column
            nodes = (first, first+1, first+stride+1, first+stride)
            model.add_element(element_id, create_shell_element(
                element_id, nodes, "elastic", thickness=0.05,
                reference_normal=(0.0, 0.0, 1.0),
            ))
            source_elements.append(element_id)
            for node in nodes:
                load_weights[node] += 0.25/divisions**2
    for element_id, nodes in (
        (divisions**2+1, (target_nodes[0], target_nodes[1], target_nodes[3])),
        (divisions**2+2, (target_nodes[1], target_nodes[2], target_nodes[3])),
    ):
        model.add_element(element_id, create_shell_element(
            element_id, nodes, "elastic", thickness=0.05,
            formulation="e4-pl-s3-v2d", reference_normal=(0.0, 0.0, 1.0),
            reference_surface_offset=0.01,
        ))

    model.add_boundary_condition(BoundaryCondition(
        "target_fixed", target_nodes,
        {axis: 0.0 for axis in ("ux", "uy", "uz", "rx", "ry", "rz")},
    ))
    model.add_boundary_condition(BoundaryCondition(
        "source_guide", source_nodes,
        {axis: 0.0 for axis in ("ux", "uy", "rx", "ry", "rz")},
    ))
    supported_edge = tuple(1 + row*stride for row in range(stride))
    model.add_boundary_condition(BoundaryCondition(
        "source_supported_edge", supported_edge, {"uz": 0.0},
    ))
    load = LoadCase("uniform_source_pressure")
    for node, weight in load_weights.items():
        load.add_nodal_load(node, forces=(0.0, 0.0, -total_load_n*weight))
    definition = ContactDefinition(
        surfaces=(ContactSurface("q4_source", tuple(source_elements), "bottom"),
                  ContactSurface("s3_target", (divisions**2+1, divisions**2+2),
                                 "top")),
        rigid_bodies=(),
        interactions=(ContactInteraction(
            "pair", "q4_source", "s3_target", normal_stiffness, 5.0e-5,
            normal_law="augmented",
        ),),
    )
    settings = ContactSolverSettings(
        pair_motion="general", normal_discretization="primal_mortar",
        q4_source_gap_certificate="whole_face",
        general_s3_difference_step=2.0e-5,
        maximum_general_s3_energy_evaluations=5000*divisions**2,
        q4_source_area_tolerance=1.0e-9,
        q4_source_weighted_gap_tolerance=1.0e-10,
        maximum_q4_source_integration_triangles=128,
        pressure_tolerance=1.0e-5,
        maximum_augmentations=7,
        general_s3_differentiation="jet2_q4_s3_dev",
        q4_source_support_gradient_tolerance=1.0e-5,
        q4_source_support_hessian_tolerance=1.0e-5,
        q4_source_weighted_gap_gradient_tolerance=1.0e-5,
        q4_source_weighted_gap_hessian_tolerance=1.0e-5,
    )
    return model, load, definition, settings


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("divisions", type=int)
    parser.add_argument("output", type=Path)
    parser.add_argument("--normal-stiffness", type=float, default=1000.0)
    args = parser.parse_args()
    model, load, definition, settings = build_case(
        args.divisions, normal_stiffness=args.normal_stiffness,
    )
    capability = validate_general_contact(model, definition, settings)
    if not capability.valid:
        raise ValueError(f"invalid contact model: {capability.issues}")
    start = time.perf_counter()
    result = solve_static_nonlinear(
        model, load, contact=definition, contact_settings=settings,
        control="force", kinematics="von_karman", num_steps=1,
        max_iterations=12, min_step_fraction=0.5,
        emit_restart_checkpoint=True,
    )
    record = {
        "divisions": args.divisions,
        "total_load_n": 0.4,
        "normal_law": "augmented",
        "normal_stiffness": args.normal_stiffness,
        "elapsed_seconds": time.perf_counter() - start,
        "status": result.status,
        "failure_reason": result.failure_reason,
        "accepted_steps": len(result.steps),
        "contact_failure": result.info.get("contact_failure"),
        "force_displacement_history": result.info.get("force_displacement_history"),
        "general_contact": result.info.get("general_contact"),
        "solver_info": result.info,
        "has_restart_checkpoint": result.restart_checkpoint is not None,
    }
    args.output.write_text(json.dumps(record, indent=2, default=str) + "\n",
                           encoding="utf-8")
    print(json.dumps({key: value for key, value in record.items()
                      if key not in ("contact_failure", "force_displacement_history",
                                     "general_contact", "solver_info")},
                     indent=2, default=str))


if __name__ == "__main__":
    main()
