"""Development example: bounded nonmatching Q4/S3 contact under both controls.

Run against an installed ANYsolver package. This example is implemented and
locally tested; D1 scientific acceptance and release remain open.
"""

from __future__ import annotations

import argparse
from dataclasses import replace
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


def build_model():
    columns = rows = 4
    stride = columns+1
    slope = 1.0e-4
    normal = np.asarray((-slope, 0.0, 1.0))
    normal /= np.linalg.norm(normal)
    model = FEModel("d1_interior_q4_s3_controls_dev")
    model.add_material("elastic", 1.0e5, 0.3, density=1.0)
    for row in range(rows+1):
        y = 0.1+row/rows
        for column in range(columns+1):
            x = 0.1+column/columns
            model.add_node(1+row*stride+column, x, y,
                           0.04004/normal[2]+slope*(x-0.65))
    target_nodes = (26, 27, 28, 29)
    for node, (x, y) in zip(target_nodes,
                            ((0.0, -0.1), (1.3, -0.1),
                             (1.3, 1.2), (0.0, 1.2)), strict=True):
        model.add_node(node, x, y, slope*(x-0.65))
    for row in range(rows):
        for column in range(columns):
            element_id = 1+row*columns+column
            bottom = 1+row*stride+column
            model.add_element(element_id, create_shell_element(
                element_id,
                (bottom, bottom+1, bottom+stride+1, bottom+stride),
                "elastic", thickness=0.05,
                reference_normal=tuple(normal),
            ))
    for element_id, nodes in ((17, (26, 27, 29)),
                              (18, (27, 28, 29))):
        model.add_element(element_id, create_shell_element(
            element_id, nodes, "elastic", thickness=0.05,
            formulation="e4-pl-s3-v2d", reference_normal=tuple(normal),
            reference_surface_offset=0.01,
        ))
    model.add_boundary_condition(BoundaryCondition(
        "source_lateral_guide", tuple(range(1, 26)), {"uy": 0.0},
    ))
    model.add_boundary_condition(BoundaryCondition(
        "source_perimeter_support",
        (1, 2, 3, 4, 5, 6, 10, 11, 15, 16, 20, 21, 22, 23, 24, 25),
        {"uz": 0.0},
    ))
    model.add_boundary_condition(BoundaryCondition(
        "target_control_support", (26, 29),
        {name: 0.0 for name in ("uy", "uz", "rx", "ry", "rz")},
    ))
    model.add_boundary_condition(BoundaryCondition(
        "source_x_anchor", (1,), {"ux": 0.0},
    ))
    definition = ContactDefinition(
        surfaces=(ContactSurface("q4_source", tuple(range(1, 17)), "bottom"),
                  ContactSurface("s3_target", (17, 18), "top")),
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
        complementarity_force_scale_n=0.04,
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
    return model, definition, settings


def force_program(full_cycle: bool):
    raw = {1+row*5+column: min(row, 4-row)*min(column, 4-column)
           for row in range(1, 4) for column in range(1, 4)}
    total = float(sum(raw.values()))
    factors = (0.0, 1.0, 1.0, 0.0, 1.0) if full_cycle else (0.0, 1.0)
    waypoints = ((0.0, 0.0), (0.0, 0.0), (0.05, 0.05),
                 (0.05, 0.05), (0.05, 0.05)) if full_cycle else (
                     (0.0, 0.0), (0.0, 0.0))
    return ContactPathProgram(
        controls=(ContactPathControl.node(26, "ux"),
                  ContactPathControl.node(29, "ux")),
        waypoints=waypoints, steps_per_segment=2,
        nodal_forces=tuple(ContactPathNodalForce(
            node, "uz", tuple(-0.04*weight/total*factor
                              for factor in factors),
        ) for node, weight in raw.items()),
    )


def displacement_program(ring_motion: float):
    ring = ContactPathControl(tuple((node, "uz", 0.25)
                                    for node in (7, 8, 13, 17)))
    return ContactPathProgram(
        controls=(ContactPathControl.node(26, "ux"),
                  ContactPathControl.node(29, "ux"), ring),
        waypoints=((0.0, 0.0, 0.0), (0.0, 0.0, ring_motion),
                   (0.05, 0.05, ring_motion), (0.05, 0.05, 0.0),
                   (0.05, 0.05, ring_motion)),
        steps_per_segment=2,
    )


def _solve(model, definition, settings, program, **extra):
    capability = validate_general_contact(model, definition, settings)
    if not capability.valid:
        raise RuntimeError("contact capability rejected: "
                           + "; ".join(capability.issues))
    result = solve_static_nonlinear(
        model, contact=definition, contact_settings=settings,
        contact_path_program=program, max_iterations=18,
        emit_restart_checkpoint=True, **extra,
    )
    if result.status != "completed":
        raise RuntimeError(f"contact stopped: {result.failure_reason}")
    return result, capability.profile


def _records(result):
    output = []
    for row in result.info["force_displacement_history"]:
        contact = row["contact"]
        source = np.asarray(contact["integration_force"])
        target = np.asarray(contact["target_force"])
        source_moment = np.asarray(contact["integration_moment"])
        target_moment = np.asarray(contact["target_moment"])
        force_error = float(np.linalg.norm(source+target))
        moment_error = float(np.linalg.norm(source_moment+target_moment))
        if (not contact["gap_tolerance_met"]
                or row["complementarity_relative_force"] > 1.0e-8
                or force_error > 1.0e-6 or moment_error > 1.0e-6):
            raise RuntimeError("contact gate failed at step "
                               + str(row["step_index"]))
        output.append({
            "step": row["step_index"],
            "active_pressure_modes": contact["active_pressure_dofs"],
            "minimum_gap_m": contact["minimum_gap"],
            "sampled_overlap_gap_m": contact["sampled_overlap_gap"],
            "source_contact_force_n": source.tolist(),
            "generalized_reactions_n": row["reaction_generalized"],
            "complementarity_relative_force": row["complementarity_relative_force"],
            "pair_force_balance_n": force_error,
            "pair_moment_balance_nm": moment_error,
        })
    if len(output) != 8 or output[5]["active_pressure_modes"] != 0 or (
            output[6]["active_pressure_modes"] == 0):
        raise RuntimeError("four-phase contact sequence was not observed")
    return output


def run():
    press_model, definition, settings = build_model()
    press, _ = _solve(press_model, definition, settings,
                      force_program(full_cycle=False))
    dofs = press_model.mesh.dof_manager
    ring_motion = float(np.mean([press.displacements[
        dofs.get_node_dofs(node)[2]] for node in (7, 8, 13, 17)]))
    control = displacement_program(ring_motion)
    displacement_settings = replace(
        settings, complementarity_force_scale_n=0.019110708219619046,
    )
    model, definition, _ = build_model()
    full, profile = _solve(model, definition, displacement_settings, control)
    records = _records(full)
    open_model, open_definition, _ = build_model()
    opened, _ = _solve(open_model, open_definition,
                       displacement_settings, control, max_load_factor=0.75)
    if (len(opened.steps) != 6
            or opened.info["force_displacement_history"][-1]["contact"][
                "active_pressure_dofs"] != 0):
        raise RuntimeError("open-state checkpoint missing")
    resumed_model, resumed_definition, _ = build_model()
    resumed, _ = _solve(resumed_model, resumed_definition,
                         displacement_settings, control,
                         restart_checkpoint=opened.to_restart_checkpoint())
    displacement_error = float(np.max(np.abs(
        resumed.displacements-full.displacements)))
    force_error = float(np.max(np.abs(
        np.asarray(resumed.info["general_contact"]["integration_force"])
        - full.info["general_contact"]["integration_force"])))
    if displacement_error > 1.0e-10 or force_error > 1.0e-10:
        raise RuntimeError("split restart differs from uninterrupted result")
    return {
        "status": "completed", "qualification_status": "development_only",
        "capability_profile": profile,
        "source_q4_faces": 16, "deformable_target_s3_faces": 2,
        "gap_tolerance_m": definition.interactions[0].gap_tolerance,
        "force_control_press_active_pressure_modes": press.info[
            "general_contact"]["active_pressure_dofs"],
        "ring_control_motion_m": ring_motion,
        "split_restart_verified": True,
        "restart_maximum_displacement_difference_m": displacement_error,
        "restart_maximum_contact_force_difference_n": force_error,
        "anysolver_module": str(Path(anysolver.__file__).resolve()),
        "steps": records,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = run()
    payload = json.dumps(report, indent=2)+"\n"
    if args.output is None:
        print(payload, end="")
    else:
        if args.output.exists():
            raise FileExistsError(args.output)
        args.output.write_text(payload, encoding="utf-8")
        print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
