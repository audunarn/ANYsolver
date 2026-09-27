"""Adjudicate the registered fixed-pose partial-pressure resolution case."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(registration_path: Path, result_path: Path, verdict_path: Path) -> None:
    if verdict_path.exists():
        raise FileExistsError(verdict_path)
    registration = json.loads(registration_path.read_text(encoding="utf-8"))
    result = json.loads(result_path.read_text(encoding="utf-8"))
    criteria = registration["criteria"]
    rows = result["rows"]
    reference_force = float(registration["independent_reference"]["force_n"])
    errors = [abs(float(row["reaction_z_n"])-reference_force)
              for row in rows]
    predictors = registration["development_predictors"]
    checks = {
        "row_count_and_divisions": [int(row["divisions"]) for row in rows]
        == criteria["divisions"],
        "row_count_per_division": all(int(row["rows"]) == criteria["rows"]
                                      for row in rows),
        "reference_replay": all(abs(float(
            row["continuous_local_plane_reference_z_n"])
            - reference_force) <= 1e-12 for row in rows),
        "full_supported_rank": all(
            int(row["scaled_pressure_rank"])
            == int(row["supported_pressure_modes"])
            for row in rows),
        "active_modes_increase": all(
            int(left["active_pressure_dofs"])
            < int(right["active_pressure_dofs"])
            for left, right in zip(rows[:-1], rows[1:])),
        "absolute_force_error_decreases": all(
            left > right for left, right in zip(errors[:-1], errors[1:])),
        "finest_relative_reference_error": (
            errors[-1]/reference_force
            <= criteria["finest_relative_reference_error"]),
        "development_predictor": all(
            abs(float(row["reaction_z_n"])
                - float(predictors[str(row["divisions"])]["force_n"]))
            / max(abs(float(predictors[str(row["divisions"])]["force_n"])),
                  1e-30)
            <= criteria["each_force_vs_development_relative"]
            for row in rows),
        "force_balance": all(float(row["force_balance_norm_n"])
                             <= criteria["force_balance_norm_n"]
                             for row in rows),
        "moment_balance": all(float(row["moment_balance_norm_nm"])
                              <= criteria["moment_balance_norm_nm"]
                              for row in rows),
        "finest_integration_indicator": (
            float(rows[-1]["integration_force_error_indicator_n"])
            <= criteria["finest_integration_indicator_fraction_of_force_error"]
            * errors[-1]),
        "gap_tolerances": all(bool(row["gap_tolerance_met"])
                              == criteria["all_gap_tolerances_met"]
                              for row in rows),
        "wall_limit": float(result["elapsed_seconds_total"])
        <= registration["execution"]["maximum_wall_seconds"],
    }
    summary = [{
        "divisions": int(row["divisions"]),
        "force_n": float(row["reaction_z_n"]),
        "absolute_reference_error_n": error,
        "pressure_rank": int(row["scaled_pressure_rank"]),
        "supported_modes": int(row["supported_pressure_modes"]),
        "active_modes": int(row["active_pressure_dofs"]),
        "force_balance_n": float(row["force_balance_norm_n"]),
        "moment_balance_nm": float(row["moment_balance_norm_nm"]),
        "integration_indicator_n": float(
            row["integration_force_error_indicator_n"]),
    } for row, error in zip(rows, errors)]
    verdict = {
        "registration": str(registration_path),
        "registration_sha256": _sha256(registration_path),
        "raw_result": str(result_path),
        "raw_result_sha256": _sha256(result_path),
        "checks": checks,
        "summary": summary,
        "status": "pass" if all(checks.values()) else "fail",
    }
    verdict_path.write_text(json.dumps(verdict, indent=2)+"\n",
                            encoding="utf-8")
    print(json.dumps({key: verdict[key] for key in
                      ("status", "checks", "summary")}, indent=2))


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("usage: partial_pressure_adjudicate.py REG RAW VERDICT")
    main(*(Path(argument) for argument in sys.argv[1:]))
