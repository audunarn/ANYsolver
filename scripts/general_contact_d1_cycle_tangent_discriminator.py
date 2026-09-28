"""Bounded development check of mapped work along the Q4/S3 cycle.

This replays the ordinary static route and differentiates only accepted,
fixed-multiplier smooth branches. A branch change is reported as inconclusive.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from anysolver import solve_static_nonlinear
from anysolver.assembly import build_constraint_transformation
from anysolver.general_contact.core import contact_scope, suspend_contact
from anysolver.matrix_assembly import assemble_stiffness_matrix
from anysolver.nonlinear_static import _prepare_initial_states
from examples.general_contact_free_target_cycle_dev import build_case
from scripts.general_contact_d1_distributed_coupled_tangent_probe import _assemble
from scripts.general_contact_d1_distributed_tangent_probe import _branches


def _mapped_state(manager, pose, multipliers):
    source, target = manager._positions(pose)
    state = manager.law.evaluate(source, target, multipliers)
    branches = _branches(manager.law, source, target, set(range(len(source))))
    return state, branches


def _relative_error(actual, expected):
    scale = max(float(np.linalg.norm(actual)),
                float(np.linalg.norm(expected)), 1.0e-12)
    return float(np.linalg.norm(actual-expected))/scale, scale


def run():
    model, definition, settings, program = build_case()
    result = solve_static_nonlinear(
        model, contact=definition, contact_settings=settings,
        contact_path_program=program, max_iterations=18,
        record_increment_snapshots=True,
    )
    history = result.info.get("force_displacement_history", ())
    if (result.status != "completed" or len(result.snapshots) != 8
            or len(history) != 8):
        raise RuntimeError(
            f"cycle not replayed: {result.status}, {result.failure_reason}"
        )
    replay_model, replay_definition, replay_settings, _ = build_case()
    with contact_scope(replay_model, replay_definition, replay_settings,
                       allow_augmented=True) as manager:
        replay_model.apply_boundary_conditions()
        initial_stiffness, _ = assemble_stiffness_matrix(replay_model)
        zeros = np.zeros(replay_model.mesh.dof_manager.total_dofs)
        _, _, transform, prescribed, independent, _ = (
            build_constraint_transformation(initial_stiffness, zeros,
                                            replay_model))
        manager.restrict_tangent_to_reduced_variations(transform)
        index = {int(dof): col for col, dof in enumerate(independent)}
        source_dofs = {int(dof) for node in range(1, 11)
                       for dof in replay_model.mesh.dof_manager.get_node_dofs(node)}
        target_dofs = {int(dof) for node in range(11, 15)
                       for dof in replay_model.mesh.dof_manager.get_node_dofs(node)}
        source_rows = np.asarray([i for i, dof in enumerate(independent)
                                  if int(dof) in source_dofs], dtype=int)
        target_rows = np.asarray([i for i, dof in enumerate(independent)
                                  if int(dof) in target_dofs], dtype=int)
        translation_dofs = {int(dof) for node in replay_model.mesh.nodes
                            for dof in replay_model.mesh.dof_manager.get_node_dofs(
                                node)[:3]}
        row_groups = {
            "source_force": np.asarray([
                row for row in source_rows
                if int(independent[row]) in translation_dofs], dtype=int),
            "source_moment": np.asarray([
                row for row in source_rows
                if int(independent[row]) not in translation_dofs], dtype=int),
            "target_force": np.asarray([
                row for row in target_rows
                if int(independent[row]) in translation_dofs], dtype=int),
            "target_moment": np.asarray([
                row for row in target_rows
                if int(independent[row]) not in translation_dofs], dtype=int),
        }
        directions = {
            "source_slide_x": ((3, "ux", 0.5), (8, "ux", 0.5)),
            "target_normal_z": ((12, "uz", 0.5), (13, "uz", 0.5)),
            "target_director_ry": ((12, "ry", 0.5), (13, "ry", 0.5)),
        }
        axis = {"ux": 0, "uz": 2, "ry": 4}
        states, _ = _prepare_initial_states(replay_model, None, None, 5)
        records = []
        for step_index in (4, 7):
            snapshot = result.snapshots[step_index-1]
            row = history[step_index-1]
            pose = np.asarray(snapshot.displacements, dtype=float)
            multipliers = np.asarray(
                row["contact"]["normal_multiplier_estimate_pa"], dtype=float)
            manager.set_normal_multipliers(multipliers)
            pose_constraint_error = float(np.max(np.abs(
                pose-(prescribed+transform@pose[independent]))))
            if pose_constraint_error > 1.0e-12:
                raise ValueError("accepted pose does not replay supports")
            base_state, base_branches = _mapped_state(manager, pose, multipliers)
            if base_state.active_pressure_dofs < 1:
                raise ValueError("selected accepted pose has no active pressure")
            base_force, base_tangent = _assemble(
                replay_model, pose, states, tangent=True)
            with suspend_contact():
                structural_force, structural_tangent = _assemble(
                    replay_model, pose, states, tangent=True)
            for name, components in directions.items():
                reduced_direction = np.zeros(transform.shape[1])
                for node, component, weight in components:
                    dof = int(replay_model.mesh.dof_manager.get_node_dofs(node)[
                        axis[component]])
                    reduced_direction[index[dof]] += weight
                direction = np.asarray(transform@reduced_direction).reshape(-1)
                coupled_action = np.asarray(
                    transform.T@(base_tangent@direction)).reshape(-1)
                contact_action = np.asarray(transform.T@(
                    (base_tangent-structural_tangent)@direction)).reshape(-1)
                trials = []
                sizes = ((8.0e-7, 4.0e-7, 2.0e-7, 1.0e-7)
                         if name == "target_director_ry"
                         else (2.0e-7, 1.0e-7))
                for size in sizes:
                    branch_states = []
                    full_forces = []
                    structural_forces = []
                    for sign in (-1.0, 1.0):
                        trial_pose = pose+sign*size*direction
                        trial_state, trial_branches = _mapped_state(
                            manager, trial_pose, multipliers)
                        branch_states.append({
                            "active": bool(np.array_equal(
                                trial_state.pressure > 0,
                                base_state.pressure > 0)),
                            "support": bool(np.array_equal(
                                trial_state.reference_support > 0,
                                base_state.reference_support > 0)),
                            "overlap": (trial_state.overlap_signature
                                        == base_state.overlap_signature),
                            "pair": trial_branches == base_branches,
                        })
                        full, _ = _assemble(
                            replay_model, trial_pose, states, tangent=False)
                        with suspend_contact():
                            structural, _ = _assemble(
                                replay_model, trial_pose, states, tangent=False)
                        full_forces.append(full)
                        structural_forces.append(structural)
                    coupled_finite = np.asarray(transform.T@(
                        (full_forces[1]-full_forces[0])/(2*size))).reshape(-1)
                    contact_finite = np.asarray(transform.T@(
                        ((full_forces[1]-structural_forces[1])
                         -(full_forces[0]-structural_forces[0]))/(2*size)
                    )).reshape(-1)
                    errors = {}
                    for kind, action, finite in (
                            ("coupled", coupled_action, coupled_finite),
                            ("contact", contact_action, contact_finite)):
                        for body, rows in (("source", source_rows),
                                           ("target", target_rows),
                                           *row_groups.items()):
                            error, scale = _relative_error(
                                action[rows], finite[rows])
                            errors[f"{kind}_{body}_relative_error"] = error
                            errors[f"{kind}_{body}_action_scale"] = scale
                    trial_record = {"size": size,
                                    "branch_checks": branch_states,
                                    "smooth": all(all(check.values())
                                                  for check in branch_states),
                                    **errors}
                    if name == "target_normal_z":
                        plus2_pose = pose+2*size*direction
                        plus2_state, plus2_branches = _mapped_state(
                            manager, plus2_pose, multipliers)
                        plus2_check = {
                            "active": bool(np.array_equal(
                                plus2_state.pressure > 0,
                                base_state.pressure > 0)),
                            "support": bool(np.array_equal(
                                plus2_state.reference_support > 0,
                                base_state.reference_support > 0)),
                            "overlap": (plus2_state.overlap_signature
                                        == base_state.overlap_signature),
                            "pair": plus2_branches == base_branches,
                        }
                        plus2_force, _ = _assemble(
                            replay_model, plus2_pose, states, tangent=False)
                        with suspend_contact():
                            plus2_structural, _ = _assemble(
                                replay_model, plus2_pose, states,
                                tangent=False)
                        coupled_one_sided = np.asarray(transform.T@(
                            (-3*base_force+4*full_forces[1]-plus2_force)
                            /(2*size))).reshape(-1)
                        contact_one_sided = np.asarray(transform.T@(
                            (-3*(base_force-structural_force)
                             +4*(full_forces[1]-structural_forces[1])
                             -(plus2_force-plus2_structural))/(2*size)
                        )).reshape(-1)
                        one_sided = {
                            "positive_branch_checks": branch_states[1],
                            "double_positive_branch_checks": plus2_check,
                            "smooth_positive_branch": all(
                                branch_states[1].values())
                                and all(plus2_check.values()),
                        }
                        for kind, action, finite in (
                                ("coupled", coupled_action,
                                 coupled_one_sided),
                                ("contact", contact_action,
                                 contact_one_sided)):
                            for body, rows in (("source", source_rows),
                                               ("target", target_rows),
                                               *row_groups.items()):
                                error, scale = _relative_error(
                                    action[rows], finite[rows])
                                one_sided[f"{kind}_{body}_relative_error"] = error
                                one_sided[f"{kind}_{body}_action_scale"] = scale
                        trial_record["one_sided_positive"] = one_sided
                    trials.append(trial_record)
                records.append({
                    "step": step_index,
                    "direction": name,
                    "perturbation_unit": ("rad" if name == "target_director_ry"
                                          else "m"),
                    "active_pressure_modes": base_state.active_pressure_dofs,
                    "pose_constraint_error": pose_constraint_error,
                    "trials": trials,
                })
        # The delivered guide fixes every source rotation. Add one such
        # variation only for a full-coordinate local work-map discriminator.
        source_director_pose = np.asarray(
            result.snapshots[3].displacements, dtype=float)
        source_director_multipliers = np.asarray(
            history[3]["contact"]["normal_multiplier_estimate_pa"],
            dtype=float)
        source_director_direction = np.zeros_like(source_director_pose)
        for node in (3, 8):
            source_director_direction[
                replay_model.mesh.dof_manager.get_node_dofs(node)[4]] = 0.5
        # Full reaction rows are part of this comparison, including the
        # constrained target corners. The earlier narrowed Hessian selection
        # deliberately omitted them and could not test their derivatives.
        manager.law.set_tangent_active_coordinates(
            np.arange(manager.law.n_coordinates, dtype=np.intp))
        manager.set_normal_multipliers(source_director_multipliers)
        source_base, source_branches = _mapped_state(
            manager, source_director_pose, source_director_multipliers)
        source_base_force, source_base_tangent = _assemble(
            replay_model, source_director_pose, states, tangent=True)
        with suspend_contact():
            source_structural, source_structural_tangent = _assemble(
                replay_model, source_director_pose, states, tangent=True)
        source_action = np.asarray(
            (source_base_tangent-source_structural_tangent)
            @ source_director_direction).reshape(-1)
        full_groups = {
            "source_force": np.asarray(sorted(source_dofs & translation_dofs)),
            "source_moment": np.asarray(sorted(source_dofs-translation_dofs)),
            "target_force": np.asarray(sorted(target_dofs & translation_dofs)),
            "target_moment": np.asarray(sorted(target_dofs-translation_dofs)),
        }
        source_director_trials = []
        for size in (8.0e-7, 4.0e-7):
            side_forces = []
            side_branches = []
            for sign in (-1.0, 1.0):
                trial_pose = source_director_pose + (
                    sign*size*source_director_direction)
                trial_state, trial_signature = _mapped_state(
                    manager, trial_pose, source_director_multipliers)
                side_branches.append({
                    "active": bool(np.array_equal(
                        trial_state.pressure > 0,
                        source_base.pressure > 0)),
                    "support": bool(np.array_equal(
                        trial_state.reference_support > 0,
                        source_base.reference_support > 0)),
                    "overlap": (trial_state.overlap_signature
                                == source_base.overlap_signature),
                    "pair": trial_signature == source_branches,
                })
                trial_force, _ = _assemble(
                    replay_model, trial_pose, states, tangent=False)
                with suspend_contact():
                    trial_structural, _ = _assemble(
                        replay_model, trial_pose, states, tangent=False)
                side_forces.append(trial_force-trial_structural)
            source_finite = np.asarray(
                (side_forces[1]-side_forces[0])/(2*size)).reshape(-1)
            comparison = {}
            for label, rows in full_groups.items():
                error, scale = _relative_error(
                    source_action[rows], source_finite[rows])
                comparison[f"{label}_relative_error"] = error
                comparison[f"{label}_action_scale"] = scale
            source_director_trials.append({
                "step_rad": size,
                "branch_checks": side_branches,
                "smooth": all(all(check.values())
                              for check in side_branches),
                **comparison,
            })
        return {"status": "development_discriminator",
                "accepted_steps": len(result.steps),
                "reduced_row_counts": {key: len(rows)
                                       for key, rows in row_groups.items()},
                "records": records,
                "full_coordinate_source_director": {
                    "step": 4,
                    "active_pressure_modes": source_base.active_pressure_dofs,
                    "trials": source_director_trials,
                }}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    args.output.write_text(json.dumps(run(), indent=2)+"\n", encoding="utf-8")


if __name__ == "__main__":
    main()
