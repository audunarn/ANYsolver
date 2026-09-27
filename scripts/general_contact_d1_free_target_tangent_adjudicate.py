"""Adjudicate the frozen free-target force and moment directional gate."""

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
        "status": raw["status"] == criteria["status"],
        "free_dofs": raw.get("free_dofs") == criteria["free_dofs"],
        "force_rows": raw.get("free_force_rows")
        == criteria["free_force_rows"],
        "moment_rows": raw.get("free_moment_rows")
        == criteria["free_moment_rows"],
        "target_weights": raw.get("target_z_weights")
        == registration["direction"]["target_nodes_52_53_uz_weights"],
        "source_weight": raw.get("source_weight")
        == registration["direction"]["source_nodes_18_43_ux_uz_weight"],
        "active_modes": raw.get("base_active_modes")
        == criteria["base_active_modes"],
        "pair_branches": raw.get("overlap_pair_branches")
        == criteria["overlap_pair_branches"],
        "pressure_replay": raw.get("pressure_replay_error_pa", float("inf"))
        <= criteria["pressure_replay_error_pa"],
        "pose_constraints": raw.get("pose_constraint_error_m", float("inf"))
        <= criteria["pose_constraint_error_m"],
        "steps": [row["step_m"] for row in runs] == criteria["steps_m"],
        "smooth_branch": all(row["smooth_branch"]
                             == criteria["smooth_branch"] for row in runs),
        "wall_limit": raw.get("elapsed_seconds", float("inf"))
        <= registration["execution"]["maximum_wall_seconds"],
    }
    for kind in ("coupled", "mapped_contact"):
        for component in ("force", "moment"):
            lower = criteria[("minimum_force_action_n_per_m" if component
                              == "force" else
                              "minimum_moment_action_nm_per_m")]
            upper = criteria[("maximum_relative_force_error" if component
                              == "force" else
                              "maximum_relative_moment_error")]
            checks[f"{kind}_{component}_action"] = all(
                row[f"{kind}_{component}_action"] >= lower for row in runs)
            checks[f"{kind}_{component}_error"] = all(
                row[f"{kind}_{component}_error"] <= upper for row in runs)
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
        raise SystemExit("usage: free_target_tangent_adjudicate.py REG RAW VERDICT")
    main(*(Path(argument) for argument in sys.argv[1:]))
