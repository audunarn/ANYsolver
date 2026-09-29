"""Bounded development press for an interior Q4/S3 two-body contact patch.

This is a feasibility fixture, not a qualification case. The source rotations
are free, the S3 target bends, and only the source's interior middle node is
loaded. Report active rim pressure explicitly rather than hiding it.
"""

from __future__ import annotations

import argparse
from dataclasses import replace
import json
from pathlib import Path
import time

import anysolver
from anysolver import (
    BoundaryCondition, ContactPathControl, ContactPathNodalForce,
    ContactPathProgram, solve_static_nonlinear, validate_general_contact,
)

from scripts.general_contact_d1_mixed_mesh_jet2_schur_press import (
    _json_default, build_case,
)


def build_interior_press(*, force_n: float = 0.08,
                         reference_slope: float = 0.01,
                         target_columns: int = 1,
                         source_support: str = "left",
                         source_columns: int = 4,
                         source_rows: int = 2,
                         load_shape: str = "point",
                         four_phase: bool = False,
                         steps_per_segment: int = 2):
    columns, rows = source_columns, source_rows
    stride = columns + 1
    model, definition, settings, _program = build_case(
        columns, source_rows=rows, full_width_target=True,
        target_right_x_m=1.3, common_reference_slope=reference_slope,
        target_columns=target_columns,
        load_profile="distributed", total_force_n=force_n,
    )
    target_start = (rows + 1) * (columns + 1) + 1
    model.boundary_conditions = [
        bc for bc in model.boundary_conditions
        if bc.name not in {"target_fixed", "source_guide"}
        and not (source_support == "perimeter"
                 and bc.name == "source_left_support")
    ]
    model.add_boundary_condition(BoundaryCondition(
        "source_lateral_guide", tuple(range(1, target_start)), {"uy": 0.0},
    ))
    if source_support == "left":
        model.add_boundary_condition(BoundaryCondition(
            "source_left_bending_clamp",
            tuple(1 + row * stride for row in range(rows + 1)),
            {"ry": 0.0},
        ))
    elif source_support == "perimeter":
        rim = (tuple(range(1, stride + 1))
               + tuple(node for row in range(1, rows)
                       for node in (1 + row * stride, (row + 1) * stride))
               + tuple(range(1 + rows * stride,
                             1 + (rows + 1) * stride)))
        model.add_boundary_condition(BoundaryCondition(
            "source_perimeter_support", rim, {"uz": 0.0},
        ))
    else:
        raise ValueError("source support must be left or perimeter")
    model.add_boundary_condition(BoundaryCondition(
        "target_left_clamp", (target_start,
                              target_start + target_columns + 1),
        {name: 0.0 for name in ("ux", "uy", "uz", "rx", "ry", "rz")},
    ))
    settings = replace(
        settings, enforcement_solver="monolithic_active_set",
        complementarity_force_scale_n=force_n,
        augmentation_acceleration="none",
        augmentation_schur_maximum_modes=None,
        augmentation_schur_maximum_pressure_pa=None,
        augmentation_schur_maximum_step_pa=None,
        augmentation_schur_difference_step_m=None,
        augmentation_schur_maximum_attempts=1,
        augmentation_schur_maximum_relinearizations=0,
        d1_interior_profile=True,
        d1_interior_coverage_tolerance_m2=1.0e-10,
        d1_interior_boundary_force_tolerance_n=1.0e-10,
    )
    interior = tuple(1 + row * stride + column
                     for row in range(1, rows)
                     for column in range(1, columns))
    if load_shape == "point":
        load_weights = {1 + (rows // 2) * stride + columns // 2: 1.0}
    elif load_shape == "interior_distributed":
        raw = {node: min(row, rows - row) * min(column, columns - column)
               for row in range(1, rows) for column in range(1, columns)
               for node in (1 + row * stride + column,)}
        total = float(sum(raw.values()))
        load_weights = {node: weight / total for node, weight in raw.items()}
    else:
        raise ValueError("load shape must be point or interior_distributed")
    waypoints = ((0.0, 0.0), (0.0, 0.0))
    force_factors = (0.0, 1.0)
    if four_phase:
        waypoints += ((0.05, 0.05), (0.05, 0.05), (0.05, 0.05))
        force_factors += (1.0, 0.0, 1.0)
    program = ContactPathProgram(
        controls=(ContactPathControl.node(1, "ux"),
                  ContactPathControl.node(columns + 2, "ux")),
        waypoints=waypoints,
        steps_per_segment=steps_per_segment,
        nodal_forces=tuple(ContactPathNodalForce(
            node, "uz", tuple(-force_n * weight * factor
                              for factor in force_factors),
        ) for node, weight in load_weights.items()),
    )
    return model, definition, settings, program


def main(output: Path, *, force_n: float, reference_slope: float,
         target_columns: int, source_support: str,
         source_columns: int, source_rows: int, load_shape: str,
         max_path_fraction: float, four_phase: bool,
         steps_per_segment: int):
    if output.exists():
        raise FileExistsError(output)
    started = time.perf_counter()
    model, definition, settings, program = build_interior_press(
        force_n=force_n, reference_slope=reference_slope,
        target_columns=target_columns, source_support=source_support,
        source_columns=source_columns, source_rows=source_rows,
        load_shape=load_shape,
        four_phase=four_phase, steps_per_segment=steps_per_segment,
    )
    report = validate_general_contact(model, definition, settings)
    if not report.valid:
        raise ValueError(f"fixture capability rejected: {report.issues}")
    result = solve_static_nonlinear(
        model, contact=definition, contact_settings=settings,
        contact_path_program=program, max_iterations=18,
        max_load_factor=max_path_fraction,
        emit_restart_checkpoint=True,
    )
    step_records = []
    stride = source_columns + 1
    interior_nodes = tuple(1 + row * stride + column
                           for row in range(1, source_rows)
                           for column in range(1, source_columns))
    for row in result.info.get("force_displacement_history", ()):
        contact = row.get("contact", {})
        pressure = dict(zip(contact.get("source_pressure_node_ids", ()),
                            contact.get("numerical_pressure_pa", ())))
        step_records.append({
            "step": row.get("step_index"),
            "accepted": row.get("accepted"),
            "contact": contact,
            "rim_pressure_pa": {
                str(node): value for node, value in pressure.items()
                if node not in interior_nodes and value > 0.0
            },
        })
    payload = {
        "candidate": "d1_interior_free_rotation_press_development",
        "anysolver_module": str(Path(anysolver.__file__).resolve()),
        "capability_profile": report.profile,
        "source_q4_faces": source_columns * source_rows,
        "target_s3_faces": 2 * target_columns,
        "interior_pressure_node_ids": list(interior_nodes),
        "force_n": force_n,
        "reference_slope": reference_slope,
        "source_support": source_support,
        "source_rows": source_rows,
        "source_columns": source_columns,
        "load_shape": load_shape,
        "max_path_fraction": max_path_fraction,
        "four_phase": four_phase,
        "steps_per_segment": steps_per_segment,
        "status": result.status,
        "failure_reason": result.failure_reason,
        "accepted_steps": len(result.steps),
        "elapsed_seconds": time.perf_counter() - started,
        "history": step_records,
        "contact_failure": result.info.get("contact_failure"),
    }
    output.write_text(json.dumps(payload, indent=2, default=_json_default) + "\n",
                      encoding="utf-8")
    print(json.dumps({key: payload[key] for key in (
        "status", "failure_reason", "accepted_steps", "elapsed_seconds",
        "contact_failure",
    )}, default=_json_default))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--force-n", type=float, default=0.08)
    parser.add_argument("--reference-slope", type=float, default=0.01)
    parser.add_argument("--target-columns", type=int, choices=(1, 2),
                        default=1)
    parser.add_argument("--source-support", choices=("left", "perimeter"),
                        default="left")
    parser.add_argument("--source-rows", type=int, choices=(2, 4, 8), default=2)
    parser.add_argument("--source-columns", type=int, choices=(4, 8), default=4)
    parser.add_argument("--load-shape", choices=("point", "interior_distributed"),
                        default="point")
    parser.add_argument("--max-path-fraction", type=float, choices=(0.5, 1.0),
                        default=1.0)
    parser.add_argument("--four-phase", action="store_true")
    parser.add_argument("--steps-per-segment", type=int, choices=(1, 2),
                        default=2)
    arguments = parser.parse_args()
    main(arguments.output, force_n=arguments.force_n,
         reference_slope=arguments.reference_slope,
         target_columns=arguments.target_columns,
         source_support=arguments.source_support,
         source_columns=arguments.source_columns,
         source_rows=arguments.source_rows, load_shape=arguments.load_shape,
         max_path_fraction=arguments.max_path_fraction,
         four_phase=arguments.four_phase,
         steps_per_segment=arguments.steps_per_segment)
