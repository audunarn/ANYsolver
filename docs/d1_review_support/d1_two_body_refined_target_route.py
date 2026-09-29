"""Bounded two-body Q4/S3 press with a parameterized target mesh.

Development geometry/cost preflight for a later spatial reference. Interior
target knots are deliberately generic; physical rectangle and supports stay
fixed. This does not qualify any target mesh or pressure space.
"""

from __future__ import annotations

import argparse
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import subprocess
import time

import numpy as np

import anysolver
from anysolver import (
    BoundaryCondition, ContactDefinition, ContactInteraction,
    ContactPathControl, ContactPathNodalForce, ContactPathProgram,
    ContactSurface, create_shell_element, solve_static_nonlinear,
)
from anysolver.fe_core import FEModel
from examples.general_contact_free_target_cycle_dev import (
    _independent_projected_gap_bound, build_case,
)


def _knots(length, cells, shift):
    if cells < 1:
        raise ValueError("positive target cell count required")
    values = np.linspace(0.0, length, cells+1)
    values[1:-1] -= shift*np.sin(np.pi*np.arange(1, cells)/cells)
    if np.any(np.diff(values) <= 0.0):
        raise ValueError("target grid is not ordered")
    return values


def build_refined_case(source_columns, target_x_cells, target_y_cells):
    if source_columns < 1:
        raise ValueError("positive source cell count required")
    model = FEModel("d1_two_body_target_grid_dev")
    model.add_material("elastic", 1.0e5, 0.3, density=1.0)
    source_stride = source_columns+1
    source_node_count = 2*source_stride
    for row, y in enumerate((0.1, 1.1)):
        for column in range(source_stride):
            model.add_node(1+row*source_stride+column,
                           0.1+column/source_columns, y, 0.04004)
    for column in range(source_columns):
        model.add_element(column+1, create_shell_element(
            column+1,
            (1+column, 2+column,
             2+source_stride+column, 1+source_stride+column),
            "elastic", thickness=0.05,
            reference_normal=(0.0, 0.0, 1.0),
        ))

    x_knots = _knots(1.3, target_x_cells, 0.04)
    y_knots = _knots(1.0, target_y_cells, 0.03)
    target_start = source_node_count+1
    target_stride = target_x_cells+1

    def target_node(column, row):
        return target_start+row*target_stride+column

    for row, y in enumerate(y_knots):
        for column, x in enumerate(x_knots):
            model.add_node(target_node(column, row), float(x), float(y), 0.0)
    target_elements = []
    for row in range(target_y_cells):
        for column in range(target_x_cells):
            bl = target_node(column, row)
            br = target_node(column+1, row)
            tl = target_node(column, row+1)
            tr = target_node(column+1, row+1)
            for nodes in ((bl, br, tl), (br, tr, tl)):
                element_id = source_columns+1+len(target_elements)
                model.add_element(element_id, create_shell_element(
                    element_id, nodes, "elastic", thickness=0.05,
                    formulation="e4-pl-s3-v2d",
                    reference_normal=(0.0, 0.0, 1.0),
                    reference_surface_offset=0.01,
                ))
                target_elements.append(element_id)

    model.add_boundary_condition(BoundaryCondition(
        "source_guide", tuple(range(1, source_node_count+1)),
        {name: 0.0 for name in ("uy", "rx", "ry", "rz")},
    ))
    model.add_boundary_condition(BoundaryCondition(
        "source_left_support", (1, 1+source_stride), {"uz": 0.0},
    ))
    model.add_boundary_condition(BoundaryCondition(
        "target_left_clamp",
        tuple(target_node(0, row) for row in range(target_y_cells+1)),
        {name: 0.0 for name in ("ux", "uy", "uz", "rx", "ry", "rz")},
    ))
    definition = ContactDefinition(
        surfaces=(
            ContactSurface("q4_source", tuple(range(1, source_columns+1)),
                           "bottom"),
            ContactSurface("s3_target", tuple(target_elements), "top"),
        ),
        rigid_bodies=(),
        interactions=(ContactInteraction(
            "pair", "q4_source", "s3_target", 10000.0, 5.0e-5,
            normal_law="augmented",
        ),),
    )
    _original, _definition, settings, _program = build_case()
    settings = replace(settings,
                       maximum_candidate_pairs=max(
                           32, source_columns*len(target_elements)),
                       maximum_q4_source_integration_triangles=max(
                           300, 30*source_columns*len(target_elements)))
    force_weights = {
        1+row*source_stride+column:
            (0.5 if column in (0, source_columns) else 1.0)
            /source_columns*0.5
        for row in range(2) for column in range(source_stride)
    }
    program = ContactPathProgram(
        controls=(ContactPathControl.node(1, "ux"),
                  ContactPathControl.node(1+source_stride, "ux")),
        waypoints=((0.0, 0.0), (0.0, 0.0)),
        steps_per_segment=2,
        nodal_forces=tuple(ContactPathNodalForce(
            node, "uz", (0.0, -0.3*weight))
            for node, weight in force_weights.items()),
    )
    return model, definition, settings, program, x_knots, y_knots


def run(source_columns, target_x_cells, target_y_cells, *, original_two_s3=False):
    started = time.perf_counter()
    if original_two_s3:
        if (source_columns, target_x_cells, target_y_cells) != (4, 1, 1):
            raise ValueError("original control is the four-Q4/two-S3 case")
        model, definition, settings, program = build_case()
        program = replace(
            program, waypoints=program.waypoints[:2],
            nodal_forces=tuple(replace(force, values_n=force.values_n[:2])
                               for force in program.nodal_forces),
        )
        x_knots, y_knots = np.asarray((0.0, 1.3)), np.asarray((0.0, 1.0))
    else:
        model, definition, settings, program, x_knots, y_knots = (
            build_refined_case(source_columns, target_x_cells, target_y_cells))
    result = solve_static_nonlinear(
        model, contact=definition, contact_settings=settings,
        contact_path_program=program, max_iterations=18,
        record_increment_snapshots=True,
    )
    history = result.info.get("force_displacement_history", ())
    if len(history) != len(result.snapshots):
        raise RuntimeError("accepted pose snapshots and history differ")
    return {
        "status": result.status,
        "failure_reason": result.failure_reason,
        "source_commit": subprocess.check_output(
            ("git", "rev-parse", "HEAD"), text=True).strip(),
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "anysolver_module": str(Path(anysolver.__file__).resolve()),
        "source_q4_faces": source_columns,
        "target_s3_faces": 2*target_x_cells*target_y_cells,
        "original_two_s3_control": original_two_s3,
        "target_x_knots_m": x_knots.tolist(),
        "target_y_knots_m": y_knots.tolist(),
        "gap_tolerance_m": definition.interactions[0].gap_tolerance,
        "maximum_candidate_pairs": settings.maximum_candidate_pairs,
        "maximum_integration_triangles":
            settings.maximum_q4_source_integration_triangles,
        "accepted_steps": len(result.steps),
        "contact_failure": result.info.get("contact_failure"),
        "steps": [{
            "index": int(row["step_index"]),
            "active_pressure_modes": int(row["contact"]["active_pressure_dofs"]),
            "source_contact_force_n": row["contact"]["integration_force"],
            "target_contact_force_n": row["contact"].get("target_force"),
            "minimum_gap_m": row["contact"]["minimum_gap"],
            "independent_projected_gap_lower_m":
                _independent_projected_gap_bound(
                    model, definition, snapshot.displacements,
                    definition.interactions[0].gap_tolerance,
                ),
            "complementarity_relative_force": row.get(
                "complementarity_relative_force"),
            "equilibrium_residual_norm": row["residual_norm"],
            "accepted_displacements": snapshot.displacements.tolist(),
        } for row, snapshot in zip(history, result.snapshots, strict=True)],
        "final_displacements": result.displacements.tolist(),
        "elapsed_seconds": time.perf_counter()-started,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-columns", type=int, default=4)
    parser.add_argument("--target-x-cells", type=int, required=True)
    parser.add_argument("--target-y-cells", type=int, required=True)
    parser.add_argument("--original-two-s3", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output already exists")
    record = run(args.source_columns, args.target_x_cells,
                 args.target_y_cells,
                 original_two_s3=args.original_two_s3)
    args.output.write_text(json.dumps(record, indent=2)+"\n",
                           encoding="utf-8")
    print(json.dumps({key: record[key] for key in (
        "status", "failure_reason", "source_q4_faces", "target_s3_faces",
        "accepted_steps", "elapsed_seconds")}, indent=2))
    raise SystemExit(0 if record["status"] == "completed" else 2)


if __name__ == "__main__":
    main()
