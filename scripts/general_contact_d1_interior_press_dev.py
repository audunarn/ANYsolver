"""Bounded development press for an interior Q4/S3 two-body contact patch.

This is a feasibility fixture, not a qualification case. The source rotations
are free, the S3 target bends, and source loads act on declared interior nodes.
Report active rim pressure explicitly rather than hiding it.
"""

from __future__ import annotations

import argparse
from dataclasses import replace
import json
from pathlib import Path
import time

import anysolver
import numpy as np
from anysolver import (
    BoundaryCondition, ContactPathControl, ContactPathNodalForce,
    ContactPathProgram, solve_static_nonlinear, validate_general_contact,
)

from scripts.general_contact_d1_mixed_mesh_jet2_schur_press import (
    _json_default, build_case,
)


def _physical_bump_axis_weights(count: int) -> np.ndarray:
    """Consistent Q1 loads from one fixed physical-axis traction shape."""
    roots, quadrature = np.polynomial.legendre.leggauss(8)
    nodal = np.zeros(count+1)
    for element in range(count):
        cell_left, cell_right = element/count, (element+1)/count
        left, right = max(cell_left, 0.25), min(cell_right, 0.75)
        if right <= left:
            continue
        position = 0.5*(left+right)+0.5*(right-left)*roots
        weight = 0.5*(right-left)*quadrature
        density = np.sin(2*np.pi*(position-0.25))**2
        local = (position-cell_left)*count
        nodal[element] += float(np.sum(weight*density*(1-local)))
        nodal[element+1] += float(np.sum(weight*density*local))
    # Integral of sin² over the fixed half-width support is 1/4.
    if abs(float(np.sum(nodal))-0.25) > 1.0e-12:
        raise RuntimeError("physical bump load quadrature did not converge")
    return nodal/0.25


def build_interior_press(*, force_n: float = 0.08,
                         reference_slope: float = 0.01,
                         target_columns: int = 1,
                         target_rows: int = 1,
                         source_support: str = "left",
                         source_columns: int = 4,
                         source_rows: int = 2,
                         source_y_profile: str | None = None,
                         offline_structural_reference_y16: bool = False,
                         load_shape: str = "point",
                         four_phase: bool = False,
                         steps_per_segment: int = 2,
                         slide_distance_m: float = 0.05,
                         slide_intervals: int = 1,
                         slide_body: str = "source",
                         shared_edge_tie: bool = False):
    if not np.isfinite(slide_distance_m) or slide_distance_m <= 0.0:
        raise ValueError("slide distance must be positive and finite")
    if type(slide_intervals) is not int or not 1 <= slide_intervals <= 10:
        raise ValueError("slide intervals must be an integer in [1, 10]")
    if slide_body not in {"source", "target", "target_diagonal_dev"}:
        raise ValueError("slide body must be source, target or target_diagonal_dev")
    if (slide_body == "target_diagonal_dev"
            and (target_columns != 1 or target_rows != 1)):
        raise ValueError("diagonal target development control needs two S3 faces")
    columns, rows = source_columns, source_rows
    stride = columns + 1
    model, definition, settings, _program = build_case(
        columns, source_rows=rows, full_width_target=True,
        target_right_x_m=1.3, common_reference_slope=reference_slope,
        target_columns=target_columns, target_rows=target_rows,
        load_profile="distributed", total_force_n=force_n,
        source_y_profile=source_y_profile,
        offline_structural_reference_y16=offline_structural_reference_y16,
    )
    target_start = (rows + 1) * (columns + 1) + 1
    target_left_top = target_start + (
        3 if target_columns == 1 and target_rows == 1
        else target_rows*(target_columns+1))
    target_control_top = (target_start + 2 if slide_body == "target_diagonal_dev"
                          else target_left_top)
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
        "target_control_support", (target_start, target_control_top),
        {name: 0.0 for name in (("ux", "uy", "uz", "rx", "ry", "rz")
                                    if slide_body == "source"
                                    else ("uy", "uz", "rx", "ry", "rz"))},
    ))
    if slide_body != "source":
        model.add_boundary_condition(BoundaryCondition(
            "source_x_anchor", (1,), {"ux": 0.0},
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
        **({
            "q4_s3_shared_edge_tie_step_m": 3.0e-8,
            "q4_s3_shared_edge_tie_direction": (1.0, 0.0, 0.0),
            "q4_s3_shared_edge_tie_relative_tolerance": 1.0e-6,
        } if shared_edge_tie else {}),
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
    elif load_shape == "interior_uniform":
        load_weights = {node: 1.0 / len(interior) for node in interior}
    elif load_shape == "physical_bump":
        if source_y_profile not in (None, "uniform_ref16"):
            raise ValueError("physical bump requires uniform source coordinates")
        x_weights = _physical_bump_axis_weights(columns)
        y_weights = _physical_bump_axis_weights(rows)
        load_weights = {
            1+row*stride+column: float(x_weights[column]*y_weights[row])
            for row in range(rows+1) for column in range(columns+1)
            if x_weights[column]*y_weights[row] > 1.0e-15
        }
        if abs(sum(load_weights.values())-1.0) > 1.0e-11:
            raise RuntimeError("physical bump nodal loads do not balance")
    else:
        raise ValueError("unknown bounded interior load shape")
    waypoints = ((0.0, 0.0), (0.0, 0.0))
    force_factors = (0.0, 1.0)
    if four_phase:
        waypoints += tuple((slide_distance_m * i / slide_intervals,) * 2
                           for i in range(1, slide_intervals + 1))
        waypoints += ((slide_distance_m, slide_distance_m),) * 2
        force_factors += (1.0,) * slide_intervals + (0.0, 1.0)
    controlled_nodes = ((1, columns + 2) if slide_body == "source" else
                        (target_start, target_control_top))
    program = ContactPathProgram(
        controls=tuple(ContactPathControl.node(node, "ux")
                       for node in controlled_nodes),
        waypoints=waypoints,
        steps_per_segment=steps_per_segment,
        nodal_forces=tuple(ContactPathNodalForce(
            node, "uz", tuple(-force_n * weight * factor
                              for factor in force_factors),
        ) for node, weight in load_weights.items()),
    )
    return model, definition, settings, program


def main(output: Path, *, force_n: float, reference_slope: float,
         target_columns: int, target_rows: int, source_support: str,
         source_columns: int, source_rows: int, load_shape: str,
         source_y_profile: str | None,
         offline_structural_reference_y16: bool,
         max_path_fraction: float, four_phase: bool,
         steps_per_segment: int, slide_distance_m: float,
         slide_intervals: int, slide_body: str,
         shared_edge_tie: bool):
    if output.exists():
        raise FileExistsError(output)
    started = time.perf_counter()
    model, definition, settings, program = build_interior_press(
        force_n=force_n, reference_slope=reference_slope,
        target_columns=target_columns, target_rows=target_rows,
        source_support=source_support,
        source_columns=source_columns, source_rows=source_rows,
        source_y_profile=source_y_profile,
        offline_structural_reference_y16=offline_structural_reference_y16,
        load_shape=load_shape,
        four_phase=four_phase, steps_per_segment=steps_per_segment,
        slide_distance_m=slide_distance_m,
        slide_intervals=slide_intervals,
        slide_body=slide_body,
        shared_edge_tie=shared_edge_tie,
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
        "target_s3_faces": 2 * target_columns * target_rows,
        "target_rows": target_rows,
        "interior_pressure_node_ids": list(interior_nodes),
        "force_n": force_n,
        "reference_slope": reference_slope,
        "source_support": source_support,
        "source_rows": source_rows,
        "source_columns": source_columns,
        "source_y_profile": source_y_profile,
        "offline_structural_reference_y16": offline_structural_reference_y16,
        "load_shape": load_shape,
        "max_path_fraction": max_path_fraction,
        "four_phase": four_phase,
        "steps_per_segment": steps_per_segment,
        "slide_distance_m": slide_distance_m,
        "slide_intervals": slide_intervals,
        "slide_body": slide_body,
        "shared_edge_tie": shared_edge_tie,
        "status": result.status,
        "failure_reason": result.failure_reason,
        "accepted_steps": len(result.steps),
        "elapsed_seconds": time.perf_counter() - started,
        "displacements": result.displacements.tolist(),
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
    parser.add_argument("--target-columns", type=int, choices=(1, 2, 3),
                        default=1)
    parser.add_argument("--target-rows", type=int, choices=(1, 2, 3),
                        default=1)
    parser.add_argument("--source-support", choices=("left", "perimeter"),
                        default="left")
    parser.add_argument("--source-rows", type=int, choices=(2, 4, 8, 16), default=2)
    parser.add_argument("--source-columns", type=int, choices=(4, 8), default=4)
    parser.add_argument("--source-y-profile", choices=("uniform_ref16",),
                        default=None)
    parser.add_argument("--offline-structural-reference-y16",
                        action="store_true")
    parser.add_argument("--load-shape", choices=("point", "interior_distributed",
                                                 "interior_uniform", "physical_bump"),
                        default="point")
    parser.add_argument("--max-path-fraction", type=float,
                        default=1.0)
    parser.add_argument("--four-phase", action="store_true")
    parser.add_argument("--slide-distance-m", type=float, default=0.05)
    parser.add_argument("--slide-intervals", type=int, default=1)
    parser.add_argument("--slide-body", choices=("source", "target",
                                                 "target_diagonal_dev"),
                        default="source")
    parser.add_argument("--shared-edge-tie", action="store_true")
    parser.add_argument("--steps-per-segment", type=int, choices=(1, 2),
                        default=2)
    arguments = parser.parse_args()
    main(arguments.output, force_n=arguments.force_n,
         reference_slope=arguments.reference_slope,
         target_columns=arguments.target_columns,
         target_rows=arguments.target_rows,
         source_support=arguments.source_support,
         source_columns=arguments.source_columns,
         source_rows=arguments.source_rows, load_shape=arguments.load_shape,
         source_y_profile=arguments.source_y_profile,
         offline_structural_reference_y16=(
             arguments.offline_structural_reference_y16),
         max_path_fraction=arguments.max_path_fraction,
         four_phase=arguments.four_phase,
         steps_per_segment=arguments.steps_per_segment,
         slide_distance_m=arguments.slide_distance_m,
         slide_intervals=arguments.slide_intervals,
         slide_body=arguments.slide_body,
         shared_edge_tie=arguments.shared_edge_tie)
