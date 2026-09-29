"""Bounded D1 coupled press with free interior Q4 bending rotation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

import numpy as np

from anysolver import BoundaryCondition, solve_static_nonlinear
from anysolver.general_contact.core import suspend_contact
from anysolver.general_contact.s3_patch_static import GeneralS3PatchManager
from anysolver.general_contact.semismooth import linearize
from anysolver.general_contact import static_path
from anysolver.general_contact.q4_source_overlap import q4_source_projected_gap_lower
from anysolver.nonlinear_static import _assemble_nonlinear_system
from scripts.general_contact_d1_free_target_press_probe import build_free_target_case


def _json_default(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    raise TypeError(f"cannot serialize {type(value).__name__}")


def build_case(steps_per_segment: int = 2, columns: int = 4,
               right_support: bool = False):
    model, definition, settings, program = build_free_target_case(
        columns, steps_per_segment=steps_per_segment,
        enforcement_solver="monolithic_active_set",
    )
    source = definition.surfaces[0]
    source_nodes = tuple(sorted({
        node_id for element_id in source.element_ids
        for node_id in model.mesh.elements[element_id].node_ids
    }))
    left_support = next(
        bc for bc in model.boundary_conditions
        if bc.name == "source_left_support"
    )
    model.boundary_conditions = [
        bc for bc in model.boundary_conditions if bc.name != "source_guide"
    ]
    model.add_boundary_condition(BoundaryCondition(
        "source_guide_free_bending", source_nodes,
        {name: 0.0 for name in ("uy", "rx", "rz")},
    ))
    model.add_boundary_condition(BoundaryCondition(
        "source_left_bending_rotation", left_support.node_ids,
        {"ry": 0.0},
    ))
    right_nodes = ()
    if right_support:
        right_x = max(model.mesh.nodes[node].x for node in source_nodes)
        right_nodes = tuple(
            node for node in source_nodes
            if abs(model.mesh.nodes[node].x-right_x) < 1e-12
        )
        model.add_boundary_condition(BoundaryCondition(
            "source_right_vertical_support", right_nodes, {"uz": 0.0},
        ))
    return (model, definition, settings, program, source_nodes,
            left_support.node_ids, right_nodes)


def _assembled(model, manager, snapshot, pose, forces, tangent):
    with suspend_contact():
        residual, stiffness, _states = _assemble_nonlinear_system(
            model, pose, snapshot.element_states, 5, tangent=tangent,
            kinematics="von_karman", require_full_coordinates=True,
        )
    contact = linearize(manager, pose, forces, tangent=tangent)
    return residual + contact.force, (
        stiffness + contact.tangent if tangent else None
    ), contact


def _sample_projected_gap(source, target, source_faces, target_faces):
    """Separate dense bilinear/Q1 versus planar/P1 vertical-gap sample."""
    grid = np.linspace(0., 1., 81)
    records = []
    for source_face in source_faces:
        corners = source[source_face]
        for target_face in target_faces:
            triangle = target[target_face]
            projected = np.column_stack((
                triangle[1, :2]-triangle[0, :2],
                triangle[2, :2]-triangle[0, :2],
            ))
            if abs(float(np.linalg.det(projected))) < 1e-12:
                raise ValueError("sampled target projection is singular")
            lowest = float("inf")
            points = 0
            location = None
            for a in grid:
                for b in grid:
                    shape = np.asarray((
                        (1-a)*(1-b), a*(1-b), a*b, (1-a)*b,
                    ))
                    point = shape @ corners
                    bary = np.linalg.solve(projected, point[:2]-triangle[0, :2])
                    if min(bary[0], bary[1], 1.-sum(bary)) < -1e-12:
                        continue
                    target_z = (
                        triangle[0, 2]
                        + bary[0]*(triangle[1, 2]-triangle[0, 2])
                        + bary[1]*(triangle[2, 2]-triangle[0, 2])
                    )
                    gap = float(point[2]-target_z)
                    points += 1
                    if gap < lowest:
                        lowest = gap
                        location = [float(a), float(b)]
            if points:
                records.append({
                    "source_face": np.asarray(source_face).tolist(),
                    "target_face": np.asarray(target_face).tolist(),
                    "sampled_vertical_gap_m": lowest,
                    "sampled_parametric_location": location,
                    "sampled_overlap_points": points,
                    "certified_pair_lower_m": q4_source_projected_gap_lower(
                        corners, triangle,
                    ),
                })
    return records


def main(output: Path, steps_per_segment: int, columns: int,
         trace_swept: bool, capture_failed_pose: bool,
         right_support: bool):
    if output.exists():
        raise FileExistsError(output)
    began = time.perf_counter()
    model, definition, settings, program, source_nodes, left_nodes, right_nodes = build_case(
        steps_per_segment, columns, right_support,
    )
    swept_calls = []
    if trace_swept:
        original_admissible = GeneralS3PatchManager.admissible_step_fraction

        def traced_admissible(self, start, end):
            fraction = original_admissible(self, start, end)
            swept_calls.append({
                "fraction": float(fraction),
                "start_gap_lower_m": float(self._gap_lower(self._positions(start))),
                "end_gap_lower_m": float(self._gap_lower(self._positions(end))),
                "step_norm": float(np.linalg.norm(np.asarray(end)-start)),
            })
            return fraction

        GeneralS3PatchManager.admissible_step_fraction = traced_admissible
    captured = []
    if capture_failed_pose:
        original_increment = static_path.solve_semismooth_increment

        def traced_increment(**kwargs):
            step_result = original_increment(**kwargs)
            if not step_result.completed:
                manager = kwargs["manager"]
                pose = np.asarray(
                    kwargs["transform"] @ step_result.q + kwargs["offset"],
                ).reshape(-1)
                source, target = manager._positions(pose)
                captured.append({
                    "certified_global_lower_m": float(
                        manager._gap_lower((source, target))
                    ),
                    "sampled_pairs": _sample_projected_gap(
                        source, target, manager.law.source_face_indices,
                        manager.law.target_face_indices,
                    ),
                    "physical_source_positions_m": source,
                    "physical_target_positions_m": target,
                })
            return step_result

        static_path.solve_semismooth_increment = traced_increment
    result = solve_static_nonlinear(
        model, contact=definition, contact_settings=settings,
        contact_path_program=program, max_iterations=18,
        record_increment_snapshots=True,
    )
    report = {
        "source": "current working tree",
        "status": result.status,
        "failure_reason": result.failure_reason,
        "accepted_steps": len(result.steps),
        "requested_steps": steps_per_segment,
        "source_columns": columns,
        "elapsed_seconds": time.perf_counter()-began,
        "source_nodes": source_nodes,
        "left_rotation_support_nodes": left_nodes,
        "right_vertical_support_nodes": right_nodes,
    }
    if result.status != "completed":
        report["available_info_keys"] = sorted(result.info)
        report["contact_failure"] = result.info.get("contact_failure")
        report["contact_path"] = result.info.get("contact_path")
        if trace_swept:
            report["swept_calls_count"] = len(swept_calls)
            report["last_swept_calls"] = swept_calls[-10:]
        if capture_failed_pose:
            report["rejected_pose_geometry"] = captured[-1] if captured else None
    if result.status == "completed" and len(result.steps) == steps_per_segment:
        history = result.info["force_displacement_history"]
        report["integration_forces_n"] = [
            row["contact"]["integration_force"] for row in history
        ]
        report["minimum_gaps_m"] = [
            row["contact"]["minimum_gap"] for row in history
        ]
        snapshots = result.snapshots
        snapshot = snapshots[-1]
        pose = np.asarray(snapshot.displacements)
        source_ry = {
            str(node): float(pose[model.mesh.dof_manager.get_node_dofs(node)[4]])
            for node in source_nodes
        }
        report["source_ry_rad"] = source_ry
        interior = next(
            node for node in source_nodes if node not in left_nodes
            and abs(source_ry[str(node)]) > 1e-10
        )
        column = model.mesh.dof_manager.get_node_dofs(interior)[4]
        certificate = history[-1]["contact"]
        forces = (
            np.asarray(certificate["numerical_pressure_pa"])
            * np.asarray(certificate["reference_support_m2"])
        )
        manager = GeneralS3PatchManager(model, definition, settings)
        base_residual, tangent, base_contact = _assembled(
            model, manager, snapshot, pose, forces, True,
        )
        step = 1e-7
        direction = np.zeros_like(pose)
        direction[column] = 1.0
        plus_residual, _, plus_contact = _assembled(
            model, manager, snapshot, pose+step*direction, forces, False,
        )
        minus_residual, _, minus_contact = _assembled(
            model, manager, snapshot, pose-step*direction, forces, False,
        )
        observed = (plus_residual-minus_residual)/(2*step)
        predicted = tangent @ direction
        contact_observed = (
            plus_contact.force-minus_contact.force
        )/(2*step)
        contact_predicted = base_contact.tangent @ direction
        report["directional_check"] = {
            "node": interior,
            "coordinate": "ry",
            "step_rad": step,
            "branch_stable": (
                base_contact.state.overlap_signature
                == plus_contact.state.overlap_signature
                == minus_contact.state.overlap_signature
            ),
            "integration_triangles_stable": (
                base_contact.state.integration_triangles
                == plus_contact.state.integration_triangles
                == minus_contact.state.integration_triangles
            ),
            "contact_relative_error": float(
                np.linalg.norm(contact_observed-contact_predicted)
                / max(np.linalg.norm(contact_observed),
                      np.linalg.norm(contact_predicted), 1e-12)
            ),
            "full_relative_error": float(
                np.linalg.norm(observed-predicted)
                / max(np.linalg.norm(observed), np.linalg.norm(predicted), 1e-12)
            ),
            "contact_source_moment_nm": float(base_contact.force[column]),
            "full_residual_norm": float(np.linalg.norm(base_residual)),
        }
    output.write_text(json.dumps(report, indent=2, default=_json_default)+"\n",
                      encoding="utf-8")
    print(json.dumps({
        key: report[key] for key in (
            "status", "failure_reason", "accepted_steps", "elapsed_seconds"
        )
    }))
    if result.status != "completed":
        raise SystemExit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("--steps-per-segment", type=int, default=2)
    parser.add_argument("--columns", type=int, default=4)
    parser.add_argument("--trace-swept", action="store_true")
    parser.add_argument("--capture-failed-pose", action="store_true")
    parser.add_argument("--right-support", action="store_true")
    args = parser.parse_args()
    main(args.output, args.steps_per_segment, args.columns, args.trace_swept,
         args.capture_failed_pose, args.right_support)
