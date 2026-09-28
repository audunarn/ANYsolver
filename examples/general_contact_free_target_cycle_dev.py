"""Development example: deformable Q4/S3 press, slide, open and recontact.

Run with ``python general_contact_free_target_cycle_dev.py`` against an
installed ANYsolver package. The contact route is implemented and locally
tested; the complete D1 capability is not independently accepted or released.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

import anysolver
from anysolver import (
    BoundaryCondition, ContactDefinition, ContactInteraction,
    ContactPathControl, ContactPathNodalForce, ContactPathProgram,
    ContactSolverSettings, ContactSurface, create_shell_element,
    solve_static_nonlinear, validate_general_contact,
)
from anysolver.fe_core import FEModel


def build_case():
    """Build the bounded two-body example without a source-checkout helper."""
    model = FEModel("mixed_4_q4_x_jet2_schur_press")
    model.add_material("elastic", 1.0e5, 0.3, density=1.0)
    for row, y in enumerate((0.1, 1.1)):
        for column in range(5):
            model.add_node(1+5*row+column, 0.1+column/4, y, 0.04004)
    for node, (x, y) in zip((11, 12, 13, 14),
                             ((0.0, 0.0), (1.3, 0.0),
                              (1.3, 1.0), (0.0, 1.0)), strict=True):
        model.add_node(node, x, y, 0.0)
    for element_id in range(1, 5):
        model.add_element(element_id, create_shell_element(
            element_id,
            (element_id, element_id+1, element_id+6, element_id+5),
            "elastic", thickness=0.05,
            reference_normal=(0.0, 0.0, 1.0),
        ))
    for element_id, nodes in ((5, (11, 12, 14)), (6, (12, 13, 14))):
        model.add_element(element_id, create_shell_element(
            element_id, nodes, "elastic", thickness=0.05,
            formulation="e4-pl-s3-v2d",
            reference_normal=(0.0, 0.0, 1.0),
            reference_surface_offset=0.01,
        ))
    model.add_boundary_condition(BoundaryCondition(
        "source_guide", tuple(range(1, 11)),
        {name: 0.0 for name in ("uy", "rx", "ry", "rz")},
    ))
    model.add_boundary_condition(BoundaryCondition(
        "source_left_support", (1, 6), {"uz": 0.0},
    ))
    model.add_boundary_condition(BoundaryCondition(
        "target_left_clamp", (11, 14),
        {name: 0.0 for name in ("ux", "uy", "uz", "rx", "ry", "rz")},
    ))
    definition = ContactDefinition(
        surfaces=(
            ContactSurface("q4_source", (1, 2, 3, 4), "bottom"),
            ContactSurface("s3_target", (5, 6), "top"),
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
        enforcement_solver="monolithic_active_set",
        complementarity_force_scale_n=0.3,
        augmentation_acceleration="none",
        augmentation_schur_maximum_modes=None,
        augmentation_schur_maximum_pressure_pa=None,
        augmentation_schur_maximum_step_pa=None,
        augmentation_schur_difference_step_m=None,
        augmentation_schur_maximum_attempts=1,
        augmentation_schur_maximum_relinearizations=0,
    )
    force_factors = (0.0, 1.0, 1.0, 0.0, 1.0)
    nodal_weights = {
        1+5*row+column:
        (0.5 if column in (0, 4) else 1.0)/4*0.5
        for row in range(2) for column in range(5)
    }
    program = ContactPathProgram(
        controls=(ContactPathControl.node(1, "ux"),
                  ContactPathControl.node(6, "ux")),
        waypoints=((0.0, 0.0), (0.0, 0.0), (0.05, 0.05),
                   (0.05, 0.05), (0.05, 0.05)),
        steps_per_segment=2,
        nodal_forces=tuple(ContactPathNodalForce(
            node, "uz", tuple(-0.3*weight*factor
                              for factor in force_factors),
        ) for node, weight in nodal_weights.items()),
    )
    return model, definition, settings, program


def run() -> dict:
    model, definition, settings, program = build_case()
    capability = validate_general_contact(model, definition, settings)
    if not capability.valid:
        raise RuntimeError("unsupported contact: " + "; ".join(capability.issues))
    result = solve_static_nonlinear(
        model, contact=definition, contact_settings=settings,
        contact_path_program=program, max_iterations=18,
        emit_restart_checkpoint=True,
    )
    if result.status != "completed" or len(result.steps) != 8:
        raise RuntimeError(
            f"contact stopped after {len(result.steps)} steps: "
            f"{result.status}: {result.failure_reason}"
        )
    history = result.info["force_displacement_history"]
    records = []
    for index, row in enumerate(history):
        contact = row["contact"]
        source = np.asarray(contact["integration_force"], dtype=float)
        target = np.asarray(contact["target_force"], dtype=float)
        source_moment = np.asarray(contact["integration_moment"], dtype=float)
        target_moment = np.asarray(contact["target_moment"], dtype=float)
        force_balance = float(np.linalg.norm(source+target))
        moment_balance = float(np.linalg.norm(source_moment+target_moment))
        complementarity = float(row["complementarity_relative_force"])
        if (not contact["gap_tolerance_met"]
                or complementarity > 1e-8
                or force_balance > 1e-9
                or moment_balance > 1e-9):
            raise RuntimeError(f"contact gate failed at step {index+1}")
        records.append({
            "step": int(row["step_index"]),
            "normal_force_n": float(source[2]),
            "minimum_gap_m": float(contact["minimum_gap"]),
            "active_pressure_modes": int(contact["active_pressure_dofs"]),
            "complementarity_relative_force": complementarity,
            "pair_force_balance_n": force_balance,
            "pair_moment_balance_nm": moment_balance,
        })
    if not (records[1]["normal_force_n"] > 0.0
            and records[5]["active_pressure_modes"] == 0
            and records[5]["normal_force_n"] == 0.0
            and records[6]["normal_force_n"] > 0.0):
        raise RuntimeError("expected press, opening and recontact sequence missing")
    if result.restart_checkpoint is None:
        raise RuntimeError("contact checkpoint missing")
    return {
        "status": result.status,
        "capability_profile": capability.profile,
        "qualification_status": "development_only",
        "source_q4_faces": 4,
        "deformable_target_s3_faces": 2,
        "gap_tolerance_m": definition.interactions[0].gap_tolerance,
        "has_restart_checkpoint": True,
        "anysolver_module": str(Path(anysolver.__file__).resolve()),
        "steps": records,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = run()
    payload = json.dumps(report, indent=2) + "\n"
    if args.output is None:
        print(payload, end="")
    else:
        if args.output.exists():
            raise FileExistsError(args.output)
        args.output.write_text(payload, encoding="utf-8")
        print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
