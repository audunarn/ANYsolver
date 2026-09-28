"""Development example: deformable Q4/S3 press, slide, open and recontact.

Run with ``python -m examples.general_contact_free_target_cycle_dev`` from the
ANYsolver source distribution. The contact route is implemented and locally
tested; the complete D1 capability is not independently accepted or released.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

import anysolver
from anysolver import solve_static_nonlinear, validate_general_contact
from scripts.general_contact_d1_free_target_press_probe import (
    build_free_target_case,
)


def run() -> dict:
    model, definition, settings, program = build_free_target_case(
        4, steps_per_segment=2, four_phase=True,
        enforcement_solver="monolithic_active_set",
    )
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
