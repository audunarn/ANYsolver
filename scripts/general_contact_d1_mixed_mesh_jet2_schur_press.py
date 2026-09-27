"""Bounded Q4 bending-direction mixed-contact press refinement probe."""

from __future__ import annotations

import argparse
from dataclasses import replace
import json
from pathlib import Path
import sys
import time

import anymaterial
import anysolver
import numpy as np

from anysolver import (
    BoundaryCondition, ContactDefinition, ContactInteraction,
    ContactPathControl, ContactPathNodalForce, ContactPathProgram,
    ContactSolverSettings, ContactSurface, create_shell_element,
    solve_static_nonlinear, validate_general_contact,
)
from anysolver.fe_core import FEModel


def _json_default(value):
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    return str(value)


def build_case(columns: int, *, four_phase: bool = False,
               steps_per_segment: int = 2,
               load_profile: str = "tip",
               total_force_n: float = 0.1):
    if columns not in (4, 8, 16):
        raise ValueError("only the bounded four/eight/sixteen-Q4 refinements are admitted")
    stride = columns+1
    source_nodes = tuple(range(1, 2*stride+1))
    target_nodes = tuple(range(2*stride+1, 2*stride+5))
    model = FEModel(f"mixed_{columns}_q4_x_jet2_schur_press")
    model.add_material("elastic", 1.0e5, 0.3, density=1.0)
    for row, y in enumerate((0.1, 1.1)):
        for column in range(stride):
            model.add_node(1+row*stride+column,
                           0.1+column/columns, y, 0.04004)
    for node, position in zip(target_nodes, (
        (0.0, 0.0, 0.0), (1.0, 0.0, 0.0),
        (1.0, 1.0, 0.0), (0.0, 1.0, 0.0),
    )):
        model.add_node(node, *position)
    for column in range(columns):
        element_id = column+1
        model.add_element(element_id, create_shell_element(
            element_id,
            (1+column, 2+column, stride+2+column, stride+1+column),
            "elastic", thickness=0.05, reference_normal=(0.0, 0.0, 1.0),
        ))
    for element_id, nodes in (
        (columns+1, (target_nodes[0], target_nodes[1], target_nodes[3])),
        (columns+2, (target_nodes[1], target_nodes[2], target_nodes[3])),
    ):
        model.add_element(element_id, create_shell_element(
            element_id, nodes, "elastic", thickness=0.05,
            formulation="e4-pl-s3-v2d",
            reference_normal=(0.0, 0.0, 1.0),
            reference_surface_offset=0.01,
        ))
    model.add_boundary_condition(BoundaryCondition(
        "target_fixed", target_nodes,
        {name: 0.0 for name in ("ux", "uy", "uz", "rx", "ry", "rz")},
    ))
    model.add_boundary_condition(BoundaryCondition(
        "source_guide", source_nodes,
        {name: 0.0 for name in ("uy", "rx", "ry", "rz")},
    ))
    model.add_boundary_condition(BoundaryCondition(
        "source_left_support", (1, stride+1), {"uz": 0.0},
    ))
    definition = ContactDefinition(
        surfaces=(
            ContactSurface("q4_source", tuple(range(1, columns+1)), "bottom"),
            ContactSurface("s3_target", (columns+1, columns+2), "top"),
        ),
        rigid_bodies=(),
        interactions=(ContactInteraction(
            "pair", "q4_source", "s3_target", 10000.0, 5.0e-5,
            normal_law="augmented",
        ),),
    )
    settings = ContactSolverSettings(
        pair_motion="general", normal_discretization="primal_mortar",
        q4_source_gap_certificate="projected_matching",
        general_s3_difference_step=2.0e-5,
        maximum_general_s3_energy_evaluations=14144,
        maximum_candidate_pairs=32,
        q4_source_area_tolerance=1.0e-9,
        q4_source_weighted_gap_tolerance=1.0e-10,
        maximum_q4_source_integration_triangles=300,
        general_s3_differentiation="jet2_q4_s3_dev",
        q4_source_support_gradient_tolerance=1.0e-5,
        q4_source_support_hessian_tolerance=1.0e-5,
        q4_source_weighted_gap_gradient_tolerance=1.0e-5,
        q4_source_weighted_gap_hessian_tolerance=1.0e-5,
        pressure_tolerance=1.0e-5, maximum_augmentations=7,
        augmentation_acceleration="supported_schur_dev",
        augmentation_schur_maximum_modes=2*stride,
        augmentation_schur_maximum_pressure_pa=10.0,
        augmentation_schur_maximum_step_pa=5.0,
        augmentation_schur_difference_step_m=2.0e-6,
        augmentation_schur_maximum_attempts=2,
        augmentation_schur_maximum_relinearizations=0,
    )
    waypoints = ((0.0, 0.0), (0.0, 0.0))
    force_factors = (0.0, 1.0)
    if four_phase:
        waypoints += ((0.05, 0.05), (0.05, 0.05), (0.05, 0.05))
        force_factors += (1.0, 0.0, 1.0)
    if load_profile == "tip":
        nodal_weights = {stride: 0.5, 2*stride: 0.5}
    elif load_profile == "distributed":
        nodal_weights = {
            1+row*stride+column:
            (0.5 if column in (0, columns) else 1.0)/(2*columns)
            for row in range(2) for column in range(stride)
        }
    else:
        raise ValueError("load profile must be tip or distributed")
    if total_force_n <= 0.0:
        raise ValueError("total downward force magnitude must be positive")
    program = ContactPathProgram(
        controls=(ContactPathControl.node(1, "ux"),
                  ContactPathControl.node(stride+1, "ux")),
        waypoints=waypoints, steps_per_segment=steps_per_segment,
        nodal_forces=tuple(ContactPathNodalForce(
            node, "uz", tuple(-total_force_n*weight*factor
                              for factor in force_factors),
        ) for node, weight in nodal_weights.items()),
    )
    return model, definition, settings, program


def main(columns: int, output: Path, pressure_cap_pa: float = 10.0,
         four_phase: bool = False, steps_per_segment: int = 2,
         schur_step_cap_pa: float = 5.0,
         load_profile: str = "tip", total_force_n: float = 0.1,
         schur_relinearizations: int = 0) -> None:
    if output.exists():
        raise FileExistsError(f"development output already exists: {output}")
    model, definition, settings, program = build_case(
        columns, four_phase=four_phase,
        steps_per_segment=steps_per_segment, load_profile=load_profile,
        total_force_n=total_force_n,
    )
    if pressure_cap_pa <= 0.0 or schur_step_cap_pa <= 0.0:
        raise ValueError("Schur pressure and step caps must be positive")
    if schur_relinearizations not in (0, 1):
        raise ValueError("this probe admits zero or one Schur relinearization")
    settings = replace(settings,
                       augmentation_schur_maximum_pressure_pa=pressure_cap_pa,
                       augmentation_schur_maximum_step_pa=schur_step_cap_pa,
                       augmentation_schur_maximum_relinearizations=(
                           schur_relinearizations))
    capability = validate_general_contact(model, definition, settings)
    if not capability.valid:
        raise ValueError(f"unsupported refinement: {capability.issues}")
    started = time.perf_counter()
    result = solve_static_nonlinear(
        model, contact=definition, contact_settings=settings,
        contact_path_program=program, max_iterations=18,
        emit_restart_checkpoint=True,
    )
    record = {
        "candidate": ("mixed_bending_refinement_jet2_schur_four_phase_dev"
                      if four_phase else
                      "mixed_bending_refinement_jet2_schur_press_dev"),
        "four_phase": four_phase,
        "steps_per_segment": steps_per_segment,
        "load_profile": load_profile,
        "total_downward_force_n": total_force_n,
        "columns": columns,
        "status": result.status,
        "failure_reason": result.failure_reason,
        "accepted_steps": len(result.steps),
        "elapsed_seconds": time.perf_counter()-started,
        "profile": capability.profile,
        "gap_tolerance_m": definition.interactions[0].gap_tolerance,
        "pressure_tolerance_pa": settings.pressure_tolerance,
        "maximum_augmentations": settings.maximum_augmentations,
        "supported_pressure_mode_cap": settings.augmentation_schur_maximum_modes,
        "schur_maximum_pressure_pa": pressure_cap_pa,
        "schur_maximum_step_pa": schur_step_cap_pa,
        "schur_maximum_relinearizations": schur_relinearizations,
        "has_checkpoint": result.restart_checkpoint is not None,
        "contact_failure": result.info.get("contact_failure"),
        "contact": result.info.get("general_contact"),
        "history": result.info.get("force_displacement_history"),
        "support_vertical_reactions_n": [
            sum(float(values[2]) for values in step.support_reactions.values())
            for step in result.steps
        ],
        "support_reactions": [step.support_reactions for step in result.steps],
        "augmentation_attempts": result.info.get("contact_augmentation_attempts"),
        "final_displacements": result.displacements.tolist(),
        "runtime_identity": {
            "python": sys.version.split()[0],
            "anysolver_module": str(Path(anysolver.__file__).resolve()),
            "anymaterial_module": str(Path(anymaterial.__file__).resolve()),
        },
    }
    output.write_text(json.dumps(record, indent=2, default=_json_default) + "\n",
                      encoding="utf-8")
    print(json.dumps({key: record[key] for key in (
        "columns", "status", "failure_reason", "accepted_steps",
        "elapsed_seconds", "has_checkpoint",
    )}, indent=2, default=_json_default))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("columns", type=int)
    parser.add_argument("output", type=Path)
    parser.add_argument("--pressure-cap-pa", type=float, default=10.0)
    parser.add_argument("--four-phase", action="store_true")
    parser.add_argument("--steps-per-segment", type=int, default=2)
    parser.add_argument("--schur-step-cap-pa", type=float, default=5.0)
    parser.add_argument("--load-profile", choices=("tip", "distributed"),
                        default="tip")
    parser.add_argument("--total-force-n", type=float, default=0.1)
    parser.add_argument("--schur-relinearizations", type=int, default=0)
    args = parser.parse_args()
    main(args.columns, args.output, args.pressure_cap_pa, args.four_phase,
         args.steps_per_segment, args.schur_step_cap_pa,
         args.load_profile, args.total_force_n,
         args.schur_relinearizations)
