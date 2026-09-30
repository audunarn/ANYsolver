"""Controlled partial-cut press/open/recontact with active source reaction rows.

A new capability fixture, not a regrade of the retained refined point-load case.
Physical source left edge is controlled, not dropped from mortar pressure/work.
"""
from dataclasses import replace
import argparse
import json
from pathlib import Path
import time
import traceback
import numpy as np
from anysolver import BoundaryCondition, ContactPathControl, ContactPathProgram, solve_static_nonlinear
from anysolver.general_contact.s3_patch_static import GeneralS3PatchManager
from anysolver.nonlinear_static import _assemble_nonlinear_system, _discard_nonlinear_state_candidate
from docs.d1_review_support.d2_projected_penalty_shell_dev import fixture, pose_diagnostics, file_identity, json_default


def build():
    model, definition, settings, _ = fixture(1e7)
    model.boundary_conditions = [replace(bc, dof_constraints={k: v for k, v in bc.dof_constraints.items()
        if k != "uz"}) if bc.name == "left" else bc for bc in model.boundary_conditions]
    model.add_boundary_condition(BoundaryCondition("formerly_zero_inplane_controls", (2,), {"ux": 0., "uy": 0.}))
    program = ContactPathProgram(controls=(ContactPathControl.node(1, "uz"), ContactPathControl.node(4, "uz")),
        waypoints=((0., 0.), (-130e-6, -130e-6), (0., 0.), (-130e-6, -130e-6)), steps_per_segment=2)
    return model, definition, settings, program


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists(): raise FileExistsError(args.output)
    started = time.perf_counter()
    record = {"accepted": False, "released": False, "adapter": file_identity(__file__),
        "kind": "active_prescribed_source_edge_controlled_lifecycle_development", "poses": [],
        "inputs": {"initial_clearance_m": 1e-4, "prescribed_press_m": -130e-6,
            "physical_gap_budget_m": 5e-5, "normal_regularization_pa_per_m": 1e7,
            "force_balance_relative_target": 1e-6, "full_work_relative_target": 1e-10,
            "source_normal_control_nodes": [1, 4], "source_free_normal_nodes": [2, 3, 5, 6],
            "external_nodal_force_n": 0., "steps_per_segment": 2,
            "time_cap_s": 180, "memory_cap_bytes": 1000000000},
        "production": {name: file_identity(Path("src/anysolver")/name) for name in (
            "nonlinear_static.py", "general_contact/s3_patch_static.py", "general_contact/static_path.py")}}
    try:
        model, definition, settings, program = build()
        record["program"] = program.contract()
        result = solve_static_nonlinear(model, contact=definition, contact_settings=settings,
            contact_path_program=program, max_iterations=18, tolerance=1e-8,
            emit_restart_checkpoint=True, record_increment_snapshots=True)
        record.update(status=result.status, failure=result.failure_reason, info=result.info,
            steps=[step.to_dict() for step in result.steps], checkpoint=result.restart_checkpoint,
            actual_pose_displacements=[s.displacements.tolist() for s in result.snapshots])
        if result.status != "completed" or len(result.snapshots) != 6:
            raise RuntimeError("controlled active-edge lifecycle did not complete")
        manager = GeneralS3PatchManager(model, definition, settings)
        for snapshot, history, step in zip(result.snapshots, result.info["force_displacement_history"], result.steps, strict=True):
            pose = pose_diagnostics(model, definition, manager, snapshot, program, history)
            record["poses"].append(pose)
            u = snapshot.displacements
            structural, _, trials = _assemble_nonlinear_system(model, u, snapshot.element_states, 5,
                tangent=False, kinematics="von_karman", require_full_coordinates=True)
            _discard_nonlinear_state_candidate(trials)
            _discard_nonlinear_state_candidate(snapshot.element_states)
            contact = manager.evaluate(u, tangent=False)[0]
            b = structural+contact  # No applied nodal forces in this control fixture.
            multipliers = np.asarray(history["reaction_generalized"])
            control_dofs = [model.mesh.dof_manager.get_node_dofs(n)[2] for n in (1, 4)]
            control_error = float(np.max(abs(b[control_dofs]-multipliers))/.5)
            remaining = b.copy()
            remaining[control_dofs] -= multipliers
            support_errors = []
            for bc in model.boundary_conditions:
                expected = np.zeros(6)
                for node in bc.node_ids:
                    dofs = model.mesh.dof_manager.get_node_dofs(node)
                    for name in bc.dof_constraints:
                        axis = ("ux", "uy", "uz", "rx", "ry", "rz").index(name)
                        expected[axis] += remaining[dofs[axis]]
                actual = np.asarray(step.support_reactions[bc.name])
                support_errors.append(float(np.max(abs(actual-expected))/.5))
            pose["control_reaction_reconciliation"] = {"reported_generalized_reactions_n": multipliers.tolist(),
                "independent_residual_at_control_dofs_n": b[control_dofs].tolist(),
                "control_error_relative": control_error, "support_report_error_relative": max(support_errors),
                "convention": "controls.T @ multipliers acts on model; no external-force substitution"}
            pose["development_checks"]["actual_control_and_support_reactions"] = max([control_error]+support_errors) <= 1e-6
            pose["development_checks"]["production_gap_admission"] = bool(pose["certificate"]["gap_tolerance_met"])
            if not all(pose["development_checks"].values()):
                raise RuntimeError("controlled pose mechanics check failed")
        counts = [p["certificate"]["active_pressure_dofs"] for p in record["poses"]]
        presses = [record["poses"][1], record["poses"][5]]
        controlled_pressures = [[r["pressure_pa"] for r in p["prescribed_source_pressure_rows"]] for p in presses]
        record["checks"] = {"press_open_recontact": counts[1] > 0 and counts[3] == 0 and counts[5] > 0,
            "both_controlled_pressure_rows_active": all(value > 0 for values in controlled_pressures for value in values),
            "complete_pose_mechanics": all(all(p["development_checks"].values()) for p in record["poses"]),
            "active_final_checkpoint": result.restart_checkpoint is not None}
        record["active_counts"] = counts
        record["controlled_pressures_pa"] = controlled_pressures
        record["development_checks_met"] = all(record["checks"].values())
        if not record["development_checks_met"]: raise RuntimeError("active-edge lifecycle predicate failed")
    except Exception as exc:
        record["error"] = {"type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc()}
        record["development_checks_met"] = False
    finally:
        record["elapsed_seconds"] = time.perf_counter()-started
        args.output.write_text(json.dumps(record, indent=2, default=json_default)+"\n", encoding="utf-8")
        print(json.dumps({"status": record.get("status"), "development_checks_met": record["development_checks_met"],
            "elapsed_seconds": record["elapsed_seconds"], "error": record.get("error", {}).get("message")}), flush=True)
    raise SystemExit(0 if record["development_checks_met"] else 1)


if __name__ == "__main__": main()
