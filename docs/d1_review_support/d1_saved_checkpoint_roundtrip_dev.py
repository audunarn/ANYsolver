"""Recreate and consume complete saved D1 force checkpoints without a solve.

The existing checkpoint owners perform every integrity, model, analysis and
qualified-state validation. This adapter changes no guard or authority and
compares complete canonical roots, including all reduced coordinates/history.
Installed import verification is supplied by d1_installed_entry.py.
"""
from __future__ import annotations

import argparse
import hashlib
import inspect
import json
from pathlib import Path
import sys
import time
import traceback


_FIXTURE = dict(force_n=.018, reference_slope=.0001,
    source_q4_faces=16, target_s3_faces=32,
    source_columns=4, source_rows=4, target_columns=4, target_rows=4,
    target_young_multiplier=5., target_y0_m=-.1,
    source_reference_downshift_m=0., source_support="perimeter",
    source_y_profile=None, offline_structural_reference_y16=False,
    load_shape="physical_bump", four_phase=True, steps_per_segment=2,
    slide_distance_m=.04, slide_intervals=1, slide_body="target",
    target_reference_full_left_clamp=True, target_left_edge_motion=True,
    shared_edge_tie=False, q4_gap_certificate="overlap_local_dev")

_RADIAL_FIXTURE = dict(target_cells=12, target_y0_m=-.113,
                      target_right_x_m=1.297)


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _hash(raw):
    return hashlib.sha256(raw).hexdigest()


def _file_identity(path):
    path = Path(path).resolve()
    return dict(path=str(path), sha256=_hash(path.read_bytes()))


def _contract(model, definition, settings, program):
    # Same inline reconstruction as the existing d1_cycle_restart_check_dev.py,
    # aligned with static_path.operation.run's force-control contract. Neither
    # helper exposes a reusable contract constructor; fingerprints must match.
    # radial_solve also explicitly passes max_iterations=18 and uses the public
    # solve defaults for num_layers/tolerance, so it has these same fields.
    from anysolver import solve_static_nonlinear
    from anysolver.general_contact.s3_patch_static import GeneralS3PatchManager
    from anysolver.general_contact.static_path import (
        GENERAL_Q4_S3_PATCH_REFINED_OVERLAP_LOCAL_AUGMENTED_PROFILE,
    )
    _require(settings.q4_source_gap_certificate == "overlap_local_dev"
             and settings.enforcement_solver == "monolithic_active_set"
             and settings.augmentation_acceleration == "none"
             and bool(program.nodal_forces), "unsupported force path contract")
    manager = GeneralS3PatchManager(model, definition, settings)
    return dict(schema="ANYSOLVER_STATIC_RESTART_CONTRACT_V2",
        control="contact_path",
        profile=GENERAL_Q4_S3_PATCH_REFINED_OVERLAP_LOCAL_AUGMENTED_PROFILE,
        general_contact=manager.restart_contract(), program=program.contract(),
        num_layers=5, max_iterations=18,
        tolerance=inspect.signature(solve_static_nonlinear).parameters["tolerance"].default,
        enforcement_solver="monolithic_active_set",
        control_residual_scaling="per_control_waypoint_max_v1")


def roundtrip_saved_checkpoint(saved_record, *, expected_step, radial=False,
                               diagnostics=None):
    """Return scalar diagnostics for one complete cycle or radial saved root.

    Any missing fixture metadata, owner rejection or byte difference raises.
    No solver increment is advanced. The radial builder verifies its frozen
    element operator while reconstructing the saved model.
    """
    from anysolver.nonlinear_restart import (
        analysis_configuration_fingerprint, canonical_checkpoint_json_bytes,
        create_nonlinear_checkpoint, load_nonlinear_checkpoint,
        model_configuration_fingerprint, validate_nonlinear_checkpoint,
    )
    from scripts.general_contact_d1_interior_press_dev import (
        build_radial_guided_case, build_saved_cycle,
    )

    _require(type(radial) is bool, "radial must be a boolean")
    _require(type(expected_step) is int
             and expected_step in ((2,) if radial else (2, 6)),
             "only radial-2, active-2 and open-6 force roots are admitted")
    _require(type(saved_record) is dict, "saved fixture must be a JSON object")
    fixture = _RADIAL_FIXTURE if radial else _FIXTURE
    for key, value in fixture.items():
        _require(key in saved_record and saved_record[key] == value,
                 f"missing or incompatible fixture metadata: {key}")
    _require(saved_record.get("status") == "completed"
             and saved_record.get("accepted_steps") == expected_step
             and (radial or saved_record.get("restart_checkpoint_available") is True),
             "incomplete or wrong accepted prefix")
    _require(len(saved_record.get("accepted_pose_displacements", ())) == expected_step,
             "saved prefix does not retain every accepted pose")

    # When supplied by the CLI, retain completed stages and attempted public
    # calls on a rejected checkpoint as well as on a successful roundtrip.
    diagnostics = {} if diagnostics is None else diagnostics
    _require(type(diagnostics) is dict, "diagnostics must be a dictionary")
    times = diagnostics.setdefault("timings_s", {})
    calls = dict(load_nonlinear_checkpoint=0, validate_nonlinear_checkpoint=0,
                 create_nonlinear_checkpoint=0)
    diagnostics["adapter_checkpoint_calls"] = calls
    root_started = time.perf_counter()

    def stage(name):
        diagnostics["last_stage"] = name
        print(json.dumps(dict(stage=name, kind="radial" if radial else "cycle",
                              expected_step=expected_step,
                              elapsed_from_root_start_s=time.perf_counter()-root_started)),
              flush=True)

    stage("load_integrity")
    started = time.perf_counter()
    calls["load_nonlinear_checkpoint"] += 1
    root = load_nonlinear_checkpoint(saved_record["restart_checkpoint"])
    times["load_integrity_s"] = time.perf_counter()-started
    _require(root["analysis_kind"] == "static", "wrong analysis kind")
    path = root["path_state"]
    _require(path["accepted_step"] == expected_step
             and len(path["history"]) == len(path["steps"]) == expected_step,
             "checkpoint lacks complete prefix history/step records")
    _require(root["activity_state"] is None and root["deleted_element_ids"] == []
             and root["contact_state"] == {},
             "this elastic fixture has no activity, deletions or contact history")
    active = path["history"][-1]["contact"]["active_pressure_dofs"]
    _require((active > 0 if expected_step == 2 else active == 0),
             "saved prefix has the wrong active/open state")
    if radial:
        _require(len(root["element_states"]) == 432,
                 "radial checkpoint must retain all 432 element states")
        _require(path["terminal_status"] == "completed",
                 "radial checkpoint is not the complete terminal state")
        _require(canonical_checkpoint_json_bytes(saved_record["history"])
                 == canonical_checkpoint_json_bytes(path["history"]),
                 "saved radial history differs from the complete root")
    started = time.perf_counter()
    stage("original_canonical_and_saved_parity")
    original_bytes = canonical_checkpoint_json_bytes(root)
    _require(canonical_checkpoint_json_bytes(saved_record["displacements"])
             == canonical_checkpoint_json_bytes(root["displacements"])
             == canonical_checkpoint_json_bytes(saved_record["accepted_pose_displacements"][-1]),
             "saved final displacement/snapshot differs from the complete root")
    times["original_canonical_and_saved_parity_s"] = time.perf_counter()-started

    started = time.perf_counter()
    stage("reconstruct_and_fingerprint")
    if radial:
        model, definition, settings, program, _reference, _record = (
            build_radial_guided_case(**{key: saved_record[key] for key in fixture}))
        _require(len(model.mesh.elements) == 432,
                 "reconstructed radial model must contain 432 elements")
    else:
        model, definition, settings, program = build_saved_cycle(saved_record)
    contract = _contract(model, definition, settings, program)
    model.apply_boundary_conditions()
    _require(model.mesh.element_activity is None, "unexpected fixture activity owner")
    observed_model = model_configuration_fingerprint(model)
    observed_analysis = analysis_configuration_fingerprint(contract)
    _require(observed_model == root["model_fingerprint"],
             "reconstructed model fingerprint differs from the saved root")
    _require(observed_analysis == root["analysis_fingerprint"],
             "reconstructed current path contract differs from the saved root")
    times["reconstruct_and_fingerprint_s"] = time.perf_counter()-started

    started = time.perf_counter()
    stage("preconsumer_validation")
    calls["validate_nonlinear_checkpoint"] += 1
    consumed = validate_nonlinear_checkpoint(root, analysis_kind="static",
        model=model, analysis_contract=contract, num_layers=contract["num_layers"])
    times["preconsumer_validation_s"] = time.perf_counter()-started
    _require(canonical_checkpoint_json_bytes(consumed.payload) == original_bytes,
             "preconsumer changed the canonical original root")

    started = time.perf_counter()
    stage("producer_including_its_validation")
    calls["create_nonlinear_checkpoint"] += 1
    produced = create_nonlinear_checkpoint(analysis_kind="static", model=model,
        analysis_contract=contract, displacements=consumed.displacements,
        element_states=consumed.element_states, path_state=consumed.path_state,
        deleted_element_ids=consumed.deleted_element_ids)
    times["producer_including_its_validation_s"] = time.perf_counter()-started

    started = time.perf_counter()
    stage("postconsumer_validation")
    calls["validate_nonlinear_checkpoint"] += 1
    reconsumed = validate_nonlinear_checkpoint(produced, analysis_kind="static",
        model=model, analysis_contract=contract, num_layers=contract["num_layers"])
    times["postconsumer_validation_s"] = time.perf_counter()-started
    started = time.perf_counter()
    stage("final_canonical_parity_and_model_identity")
    produced_bytes = canonical_checkpoint_json_bytes(produced)
    reconsumed_bytes = canonical_checkpoint_json_bytes(reconsumed.payload)
    _require(produced_bytes == original_bytes,
             "producer root differs from the complete canonical saved root")
    _require(reconsumed_bytes == original_bytes,
             "postconsumer root differs from the complete canonical saved root")
    _require(model_configuration_fingerprint(model) == observed_model,
             "model identity changed during producer/consumer validation")
    times["final_canonical_parity_and_model_identity_s"] = time.perf_counter()-started
    stage("complete")
    return dict(accepted_step=expected_step, active_pressure_dofs=active,
        total_dofs=root["total_dofs"], element_state_count=len(root["element_states"]),
        history_count=len(path["history"]), step_record_count=len(path["steps"]),
        reduced_coordinate_count=len(path["reduced_coordinates"]),
        control_multiplier_count=len(path["multipliers"]),
        normal_multiplier_count=len(path["normal_multipliers"]),
        normal_force_count=len(path["normal_forces"]),
        control_count=len(program.controls), nodal_force_count=len(program.nodal_forces),
        canonical_byte_count=len(original_bytes),
        original_canonical_sha256=_hash(original_bytes),
        produced_canonical_sha256=_hash(produced_bytes),
        reconsumed_canonical_sha256=_hash(reconsumed_bytes),
        original_checkpoint_sha256=root["checkpoint_sha256"],
        produced_checkpoint_sha256=produced["checkpoint_sha256"],
        reconstructed_model_fingerprint=observed_model,
        reconstructed_analysis_fingerprint=observed_analysis,
        analysis_contract=contract, fixture=dict(fixture), timings_s=times,
        adapter_checkpoint_calls=calls, last_stage="complete",
        preconsumer_complete_parity=True, producer_complete_parity=True,
        postconsumer_complete_parity=True)


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("output", type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--active", type=Path)
    mode.add_argument("--radial", type=Path)
    parser.add_argument("--open", type=Path)
    args = parser.parse_args()
    if args.radial is None and (args.active is None or args.open is None):
        parser.error("supply both --active and --open, or supply --radial")
    if args.radial is not None and args.open is not None:
        parser.error("--radial cannot be combined with --open")
    _require(not args.output.exists(), "output already exists")
    import anysolver
    from anysolver import nonlinear_restart, current_state_tangent, e4_pl_s3_state
    from anysolver.general_contact import s3_patch_static, static_path
    from scripts import general_contact_d1_interior_press_dev as builder

    started = time.perf_counter()
    result = dict(status="development_complete_saved_checkpoint_roundtrip",
        scope=("complete 432-element radial-2 development root; no solve; "
               "does not substitute for formal spatial evidence" if args.radial is not None
               else "complete elastic .018 N / .04 m active-2 and open-6 force roots; no solve"),
        roundtrip_checks_met=False, independently_accepted=False, released=False,
        python_executable=sys.executable, python_version=sys.version,
        actual_modules={module.__name__: _file_identity(module.__file__)
                        for module in (anysolver, nonlinear_restart, current_state_tangent, e4_pl_s3_state,
                                       s3_patch_static, static_path, builder)},
        adapter=_file_identity(__file__),
        contract_reconstruction_reference=_file_identity(
            Path(__file__).with_name("d1_cycle_restart_check_dev.py")), rows=[], failures=[])
    inputs = (("radial", args.radial, 2),) if args.radial is not None else (
        ("active", args.active, 2), ("open", args.open, 6))
    for name, path, step in inputs:
        row = dict(kind=name, input_path=str(path.resolve()), expected_step=step)
        row_started = time.perf_counter()
        print(json.dumps(dict(stage="saved_root", kind=name, expected_step=step)), flush=True)
        try:
            raw = path.read_bytes()
            row["input_sha256"] = _hash(raw)
            saved = json.loads(raw)
            row.update(roundtrip_saved_checkpoint(saved, expected_step=step,
                                                  radial=name == "radial",
                                                  diagnostics=row))
        except Exception as exc:
            row["failure"] = dict(type=type(exc).__name__, message=str(exc))
            row["traceback"] = traceback.format_exc()
            result["failures"].append(dict(kind=name, **row["failure"]))
        row["elapsed_s"] = time.perf_counter()-row_started
        result["rows"].append(row)
    result["elapsed_s"] = time.perf_counter()-started
    result["roundtrip_checks_met"] = not result["failures"]
    # Exclusive creation also protects a concurrently created output.
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps(dict(roundtrip_checks_met=result["roundtrip_checks_met"],
                          failures=result["failures"], output=str(args.output))))
    if not result["roundtrip_checks_met"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
