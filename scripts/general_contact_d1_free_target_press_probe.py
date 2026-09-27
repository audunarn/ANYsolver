"""Development press with a deformable two-S3 target clamped at one edge."""

from __future__ import annotations

import argparse
from dataclasses import replace
import json
from pathlib import Path
import time

from anysolver import BoundaryCondition, solve_static_nonlinear
from scripts.general_contact_d1_mixed_mesh_jet2_schur_press import (
    _json_default, build_case,
)


def main(output_path: Path, *, columns: int,
         relinearizations: int = 0) -> None:
    if output_path.exists():
        raise FileExistsError(output_path)
    started = time.perf_counter()
    report = {"candidate": "free_target_left_clamped_press_dev",
              "columns": columns, "target_support": "left_edge_clamped",
              "maximum_schur_relinearizations": relinearizations}
    try:
        model, definition, settings, program = build_case(
            columns, four_phase=False, steps_per_segment=3,
            load_profile="distributed", total_force_n=0.3,
            target_right_x_m=1.3)
        settings = replace(settings,
                           augmentation_schur_maximum_pressure_pa=250,
                           augmentation_schur_maximum_step_pa=200,
                           augmentation_schur_maximum_relinearizations=(
                               relinearizations))
        target_ids = tuple(range(2*(columns+1)+1, 2*(columns+1)+5))
        model.boundary_conditions = [
            bc for bc in model.boundary_conditions if bc.name != "target_fixed"]
        model.add_boundary_condition(BoundaryCondition(
            "target_left_clamp", (target_ids[0], target_ids[3]),
            {name: 0.0 for name in ("ux", "uy", "uz", "rx", "ry", "rz")},
        ))
        result = solve_static_nonlinear(
            model, contact=definition, contact_settings=settings,
            contact_path_program=program, max_iterations=18,
            emit_restart_checkpoint=True,
        )
        history = result.info.get("force_displacement_history", ())
        report.update({
            "status": result.status,
            "failure_reason": result.failure_reason,
            "accepted_steps": len(result.steps),
            "has_checkpoint": result.restart_checkpoint is not None,
            "history": [{
                "step": int(row["step_index"]),
                "normal_force_n": float(row["contact"][
                    "integration_force"][2]),
                "target_force_n": row["contact"].get("target_force"),
                "minimum_gap_m": float(row["contact"]["minimum_gap"]),
                "active_pressure_dofs": int(row["contact"][
                    "active_pressure_dofs"]),
                "pressure_change_pa": float(row["normal_multiplier_change"]),
                "pressure_rank": row["contact"].get(
                    "pressure_gram_scaled_rank"),
                "residual_norm": float(row["residual_norm"]),
                "augmentation_iterations": int(row[
                    "augmentation_iterations"]),
            } for row in history],
            "contact_failure": result.info.get("contact_failure"),
        })
    except Exception as exc:
        report.update({"status": "exception",
                       "failure_reason": f"{type(exc).__name__}: {exc}"})
    report["elapsed_seconds"] = time.perf_counter()-started
    output_path.write_text(json.dumps(report, indent=2,
                                      default=_json_default)+"\n",
                           encoding="utf-8")
    print(json.dumps({key: report[key] for key in
                      ("status", "failure_reason", "accepted_steps",
                       "elapsed_seconds", "history") if key in report},
                     indent=2, default=_json_default))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--columns", type=int, choices=(8, 16, 24), default=8)
    parser.add_argument("--relinearizations", type=int, choices=(0, 1),
                        default=0)
    args = parser.parse_args()
    main(args.output, columns=args.columns,
         relinearizations=args.relinearizations)
