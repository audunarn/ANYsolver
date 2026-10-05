"""Public active/open prefix checkpoints and continuation of the D2 front path."""
from dataclasses import replace
import argparse
import json
from pathlib import Path
import time
import traceback
import numpy as np
from anysolver import solve_static_nonlinear
from anysolver.nonlinear_restart import canonical_checkpoint_json_bytes, load_nonlinear_checkpoint
from anysolver.general_contact.s3_patch_static import GeneralS3PatchManager
from docs.d1_review_support.d2_active_prescribed_edge_dev import build
from docs.d1_review_support.d2_projected_penalty_shell_dev import file_identity, json_default, pose_diagnostics


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root_paths = [args.output.with_name(args.output.stem+suffix+".checkpoint.json") for suffix in ("_active", "_open")]
    if any(p.exists() for p in [args.output]+root_paths): raise FileExistsError("output already exists")
    reference = json.loads(args.reference.read_text(encoding="utf-8"))
    started = time.perf_counter()
    record = {"accepted": False, "released": False, "kind": "public_moving_edge_active_open_restart_development",
        "adapter": file_identity(__file__), "reference": file_identity(args.reference), "segments": [],
        "inputs": {"prefix_fractions": [.6, .8, 1.], "relative_mechanics_tolerance": 1e-6,
            "physical_gap_budget_m": 5e-5, "time_limit_s": 180, "memory_limit_bytes": 1000000000},
        "production": {name: file_identity(Path("src/anysolver")/name) for name in (
            "nonlinear_static.py", "nonlinear_restart.py", "general_contact/s3_patch_static.py", "general_contact/static_path.py")}}
    checkpoint = None
    all_poses = []
    try:
        for index, fraction in enumerate((.6, .8, 1.)):
            model, definition, settings, program = build(slide=True)
            print(f"public prefix/continuation fraction {fraction}", flush=True)
            result = solve_static_nonlinear(model, contact=definition, contact_settings=settings,
                contact_path_program=program, max_load_factor=fraction, max_iterations=18,
                tolerance=1e-8, restart_checkpoint=checkpoint, emit_restart_checkpoint=True,
                record_increment_snapshots=True)
            row = {"fraction": fraction, "status": result.status, "failure": result.failure_reason,
                "info": result.info, "steps": [s.to_dict() for s in result.steps],
                "displacements": result.displacements.tolist(), "checkpoint": result.restart_checkpoint, "poses": []}
            record["segments"].append(row)
            if result.status != "completed" or result.restart_checkpoint is None:
                raise RuntimeError("public prefix/continuation failed")
            manager = GeneralS3PatchManager(model, definition, settings)
            histories = {h["step_index"]: h for h in result.info["force_displacement_history"]}
            for snapshot in result.snapshots:
                pose = pose_diagnostics(model, definition, manager, snapshot, program,
                    histories[snapshot.step_index], rigid_target_slide=True)
                pose["development_checks"]["production_gap_admission"] = bool(pose["certificate"]["gap_tolerance_met"])
                row["poses"].append(pose)
                all_poses.append(pose)
                if not all(pose["development_checks"].values()): raise RuntimeError("restart pose mechanics failed")
            if index < 2:
                raw = canonical_checkpoint_json_bytes(result.restart_checkpoint)
                with root_paths[index].open("xb") as stream: stream.write(raw)
                row["persisted_checkpoint"] = file_identity(root_paths[index])
                checkpoint = load_nonlinear_checkpoint(root_paths[index].read_bytes())
                if checkpoint != result.restart_checkpoint: raise RuntimeError("persisted checkpoint changed semantic payload")
        expected = {p["step_index"]: p for p in reference["poses"]}
        comparisons = []
        for pose in all_poses:
            old = expected[pose["step_index"]]
            u, uref = np.asarray(pose["displacements"]), np.asarray(old["displacements"])
            p = np.asarray(pose["certificate"]["numerical_pressure_pa"])
            pref = np.asarray(old["certificate"]["numerical_pressure_pa"])
            comparisons.append({"step": pose["step_index"],
                "displacement_relative": float(np.linalg.norm(u-uref)/max(np.linalg.norm(uref), 1e-4)),
                "pressure_relative": float(np.linalg.norm(p-pref)/max(np.linalg.norm(pref), 1.)),
                "gap_difference_m": abs(pose["independent_gap"]["minimum_gap_m"]-old["independent_gap"]["minimum_gap_m"]),
                "control_reaction_relative": float(np.linalg.norm(np.asarray(pose["history"]["reaction_generalized"])-
                    np.asarray(old["history"]["reaction_generalized"]))/.5)})
        record["comparisons"] = comparisons
        # An incompatible definition must be rejected with the unchanged authentic
        # checkpoint. No hash/fingerprint rebind or payload edit is permitted.
        model, definition, settings, program = build(slide=True)
        incompatible = replace(definition, interactions=(replace(definition.interactions[0], normal_stiffness=2e7),))
        rejection = None
        try:
            solve_static_nonlinear(model, contact=incompatible, contact_settings=settings,
                contact_path_program=program, max_iterations=18, tolerance=1e-8,
                restart_checkpoint=checkpoint)
        except Exception as exc:
            rejection = {"type": type(exc).__name__, "message": str(exc)}
        record["incompatible_definition_rejection"] = rejection
        final = record["segments"][-1]["checkpoint"]
        active = record["segments"][0]["checkpoint"]["path_state"]["history"][-1]["contact"]["active_pressure_dofs"]
        opened = record["segments"][1]["checkpoint"]["path_state"]["history"][-1]["contact"]["active_pressure_dofs"]
        record["checks"] = {"all_ten_actual_poses": [p["step_index"] for p in all_poses] == list(range(1, 11)),
            "active_and_open_prefixes": active > 0 and opened == 0,
            "same_mechanical_continuation": all(max(c["displacement_relative"], c["pressure_relative"],
                c["control_reaction_relative"]) <= 1e-6 and c["gap_difference_m"] <= 1e-10 for c in comparisons),
            "complete_material_state_parity": final["element_states"] == reference["checkpoint"]["element_states"],
            "same_definition_identities": final["model_fingerprint"] == reference["checkpoint"]["model_fingerprint"]
                and final["analysis_fingerprint"] == reference["checkpoint"]["analysis_fingerprint"],
            "incompatible_restart_rejected": rejection is not None and rejection["type"] == "NonlinearCheckpointError"
                and "analysis" in rejection["message"].lower()}
        record["development_checks_met"] = all(record["checks"].values())
        if not record["development_checks_met"]: raise RuntimeError("restart continuation predicate failed")
    except Exception as exc:
        record["development_checks_met"] = False
        record["error"] = {"type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc()}
    finally:
        record["elapsed_seconds"] = time.perf_counter()-started
        args.output.write_text(json.dumps(record, indent=2, default=json_default)+"\n", encoding="utf-8")
        print(json.dumps({"development_checks_met": record["development_checks_met"],
            "elapsed_seconds": record["elapsed_seconds"], "error": record.get("error", {}).get("message")}), flush=True)
    raise SystemExit(0 if record["development_checks_met"] else 1)


if __name__ == "__main__": main()
