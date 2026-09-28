"""Bounded, source-only timing of the existing eight-Q4 coupled D1 fixture.

This temporarily wraps call sites in this process only. It does not change
the solver, its candidate decisions, or the registered historical cases.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from functools import wraps
import json
from pathlib import Path
import time

import anysolver.nonlinear_static as nonlinear_static
import anysolver.general_contact.s3_patch_augmented as augmented
import anysolver.general_contact.s3_patch_mortar_energy as mortar
import anysolver.general_contact.s3_patch_static as patch_static
import anysolver.general_contact.static_path as static_path
from scripts.general_contact_d1_selected_vs_fine_coupled_dev import _run


def main(output: Path) -> None:
    if output.exists():
        raise FileExistsError(output)
    records = defaultdict(lambda: {"calls": 0, "inclusive_seconds": 0.0,
                                  "exclusive_seconds": 0.0, "exceptions": 0})
    stack: list[list[float]] = []

    def watch(owner, attribute: str, label: str) -> None:
        original = getattr(owner, attribute)

        @wraps(original)
        def measured(*args, **kwargs):
            frame = [time.perf_counter(), 0.0]
            stack.append(frame)
            try:
                return original(*args, **kwargs)
            except BaseException:
                records[label]["exceptions"] += 1
                raise
            finally:
                elapsed = time.perf_counter() - frame[0]
                stack.pop()
                item = records[label]
                item["calls"] += 1
                item["inclusive_seconds"] += elapsed
                item["exclusive_seconds"] += elapsed - frame[1]
                if stack:
                    stack[-1][1] += elapsed

        setattr(owner, attribute, measured)

    # Each binding is process-local. The call-tree sums exclusive time once.
    watch(static_path, "_assemble_nonlinear_system", "coupled_assembly")
    watch(nonlinear_static, "_assemble_nonlinear_system_unchecked",
          "structural_assembly")
    watch(patch_static.GeneralS3PatchManager, "evaluate", "contact_evaluate")
    watch(patch_static.GeneralS3PatchManager, "admissible_step_fraction",
          "swept_step_check")
    watch(augmented.MovingS3PatchProjectedNormal, "prepare_work_state",
          "prepare_projected_state")
    watch(augmented.MovingS3PatchProjectedNormal, "_jet2_s3_work",
          "jet2_contact_work")
    watch(mortar.MovingS3PatchPrimalMortarPenalty, "evaluate",
          "aggregate_pair_geometry")
    watch(augmented, "q4_s3_overlap_derivatives", "q4_s3_jet2_pair")
    watch(static_path, "refined_patch_supported_schur", "supported_schur")
    watch(static_path, "factorize", "structural_factorization")
    watch(static_path, "assemble_stiffness_matrix", "initial_linear_stiffness")
    watch(patch_static, "supported_pressure_gram", "pressure_rank_diagnostics")

    started = time.perf_counter()
    case = _run("fine_nodal_q1", 8)
    elapsed = time.perf_counter() - started
    if stack:
        raise AssertionError("timing stack did not close")
    contacts = case.get("contact") or {}
    record = {
        "method": "process-local nested inclusive/exclusive perf_counter wrappers",
        "fixture": "eight-Q4/two-S3, 0.3 N distributed, target x=1.3 m, two force steps",
        "basis": "fine_nodal_q1",
        "status": case["status"],
        "failure_reason": case["failure_reason"],
        "accepted_steps": case["accepted_steps"],
        "elapsed_seconds": elapsed,
        "solver_elapsed_seconds": case["elapsed_seconds"],
        "unwrapped_seconds": elapsed - sum(
            item["exclusive_seconds"] for item in records.values()),
        "timings": dict(sorted(records.items())),
        "contact_force_z_n": (contacts.get("integration_force") or [None]*3)[2],
        "minimum_gap_m": contacts.get("minimum_gap"),
        "pressure_modes": len(contacts.get("source_pressure_node_ids") or ()),
        "final_displacements_m": case["final_displacements_m"],
        "step_augmentations": [step["augmentation_iterations"]
                               for step in case["history"]],
        "step_contact_energy_evaluations": [step["contact"]["energy_evaluations"]
                                             for step in case["history"]],
        "step_pair_geometry_evaluations": [step["contact"]["pair_geometry_evaluations"]
                                           for step in case["history"]],
    }
    output.write_text(json.dumps(record, indent=2, default=str) + "\n",
                      encoding="utf-8")
    print(json.dumps({key: value for key, value in record.items()
                      if key not in ("final_displacements_m", "timings")}, indent=2))
    if case["status"] != "completed":
        raise RuntimeError("timed D1 fixture did not complete")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    main(parser.parse_args().output)
