"""Adjudicate the registered second coupled tangent direction."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(registration_path: Path, raw_path: Path, verdict_path: Path) -> None:
    if verdict_path.exists():
        raise FileExistsError(verdict_path)
    registration = json.loads(registration_path.read_text(encoding="utf-8"))
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    criteria = registration["criteria"]
    runs = raw.get("runs", [])
    checks = {
        "saved_pose_sha256": _sha256(Path(registration["saved_pose_report"]))
        == registration["saved_pose_sha256"],
        "raw_status": raw["status"] == criteria["status"],
        "source_nodes": raw.get("source_nodes")
        == registration["direction"]["source_nodes"],
        "free_dofs": raw.get("free_dofs") == criteria["free_dofs"],
        "active_modes": raw.get("base_active_modes")
        == criteria["base_active_modes"],
        "pressure_replay": raw.get("pressure_replay_error_pa", float("inf"))
        <= criteria["pressure_replay_error_pa"],
        "pose_constraints": raw.get("pose_constraint_error_m", float("inf"))
        <= criteria["pose_constraint_error_m"],
        "step_count_and_sizes": [row["step_m"] for row in runs]
        == criteria["steps_m"],
        "smooth_branches": all(row["smooth_branch"]
                               == criteria["smooth_branch"] for row in runs),
        "coupled_action": all(row["action_scale_n_per_m"]
                              >= criteria["minimum_coupled_action_n_per_m"]
                              for row in runs),
        "contact_action": all(
            row["mapped_contact_action_scale_n_per_m"]
            >= criteria["minimum_mapped_contact_action_n_per_m"]
            for row in runs),
        "coupled_error": all(
            row["relative_reduced_tangent_error"]
            <= criteria["maximum_relative_coupled_tangent_error"]
            for row in runs),
        "contact_error": all(
            row["relative_mapped_contact_tangent_error"]
            <= criteria["maximum_relative_mapped_contact_tangent_error"]
            for row in runs),
        "wall_limit": raw.get("elapsed_seconds", float("inf"))
        <= registration["execution"]["maximum_wall_seconds"],
    }
    verdict = {
        "registration": str(registration_path),
        "registration_sha256": _sha256(registration_path),
        "raw_report": str(raw_path),
        "raw_sha256": _sha256(raw_path),
        "checks": checks,
        "runs": runs,
        "status": "pass" if all(checks.values()) else "fail",
    }
    verdict_path.write_text(json.dumps(verdict, indent=2)+"\n",
                            encoding="utf-8")
    print(json.dumps({"status": verdict["status"], "checks": checks},
                     indent=2))


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("usage: coupled_tangent_adjudicate.py REG RAW VERDICT")
    main(*(Path(argument) for argument in sys.argv[1:]))
