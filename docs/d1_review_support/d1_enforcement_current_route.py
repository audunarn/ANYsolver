"""One source-bound complete eight-Q4 D1 enforcement comparison route."""

from __future__ import annotations

import argparse
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import numpy as np
import scipy

from anysolver import solve_static_nonlinear
from scripts.general_contact_d1_mixed_mesh_jet2_schur_press import build_case


def main(output: Path, enforcement: str):
    if output.exists():
        raise FileExistsError(output)
    if enforcement not in ("nested_augmented", "monolithic_active_set"):
        raise ValueError("unknown enforcement")
    began = time.perf_counter()
    model, definition, settings, program = build_case(
        8, load_profile="distributed", total_force_n=0.3,
        target_right_x_m=1.3,
    )
    if enforcement == "monolithic_active_set":
        settings = replace(
            settings, enforcement_solver=enforcement,
            complementarity_force_scale_n=0.3,
            augmentation_acceleration="none",
            augmentation_schur_maximum_modes=None,
            augmentation_schur_maximum_pressure_pa=None,
            augmentation_schur_maximum_step_pa=None,
            augmentation_schur_difference_step_m=None,
            augmentation_schur_maximum_attempts=1,
            augmentation_schur_maximum_relinearizations=0,
        )
    prepared = time.perf_counter()
    result = solve_static_nonlinear(
        model, contact=definition, contact_settings=settings,
        contact_path_program=program, max_iterations=18,
        emit_restart_checkpoint=True,
    )
    finished = time.perf_counter()
    displacement = np.asarray(result.displacements, dtype="<f8")
    history = result.info.get("force_displacement_history", ())
    record = {
        "source_commit": subprocess.check_output(
            ("git", "rev-parse", "HEAD"), text=True,
        ).strip(),
        "python": sys.version.split()[0],
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "openblas_threads": os.environ.get("OPENBLAS_NUM_THREADS"),
        "omp_threads": os.environ.get("OMP_NUM_THREADS"),
        "enforcement_solver": enforcement,
        "normal_stiffness_pa_per_m": definition.interactions[0].normal_stiffness,
        "gap_tolerance_m": definition.interactions[0].gap_tolerance,
        "status": result.status,
        "failure_reason": result.failure_reason,
        "accepted_steps": len(result.steps),
        "build_seconds": prepared-began,
        "solve_seconds": finished-prepared,
        "total_seconds": finished-began,
        "displacement_sha256": hashlib.sha256(displacement.tobytes()).hexdigest(),
        "displacements_mixed_dof": displacement.tolist(),
        "step_summary": [{
            "step_index": row["step_index"],
            "contact_force_n": row["contact"]["integration_force"],
            "minimum_gap_m": row["contact"]["minimum_gap"],
            "active_pressure_dofs": row["contact"]["active_pressure_dofs"],
            "numerical_pressure_pa": row["contact"]["numerical_pressure_pa"],
            "reference_support_m2": row["contact"]["reference_support_m2"],
            "equilibrium_norm": row.get("equilibrium_norm"),
            "newton_iterations": row.get("newton_iterations"),
            "candidate_evaluations": row.get("candidate_evaluations"),
            "backtracks": row.get("backtracks"),
        } for row in history],
        "checkpoint_sha256": (
            result.restart_checkpoint.get("checkpoint_sha256")
            if result.restart_checkpoint is not None else None
        ),
    }
    output.write_text(json.dumps(record, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({
        key: record[key] for key in (
            "enforcement_solver", "status", "accepted_steps", "solve_seconds",
        )
    }))
    if result.status != "completed":
        raise SystemExit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("--enforcement", required=True)
    args = parser.parse_args()
    main(args.output, args.enforcement)
