"""Correct the v1 path-only adjudicator defect on the same frozen raw run."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(registration_path: Path, report_path: Path, output_path: Path) -> None:
    if output_path.exists():
        raise FileExistsError(output_path)
    registration = json.loads(registration_path.read_text(encoding="utf-8"))
    root = registration_path.parents[2]
    reference_path = root / registration["reference_report"]
    checks: dict[str, bool] = {
        "reference_hash": _hash(reference_path) == registration["reference_sha256"],
        "probe_blob": subprocess.check_output(
            ["git", "hash-object", registration["runner"]["script"]],
            cwd=root, text=True,
        ).strip() == registration["restart_probe_blob"],
    }
    report = json.loads(report_path.read_text(encoding="utf-8"))
    criteria = registration["criteria"]
    checks["reference_identity"] = (
        Path(report.get("reference", "")) == Path(registration["reference_report"])
        and report.get("columns") == 24
        and report.get("target_right_x_m") == 1.3
    )
    checks["step_records"] = (
        len(report.get("differences", ())) == 12
        and [item.get("step") for item in report.get("differences", ())]
        == list(range(1, 13))
    )
    for key, limit in criteria.items():
        if key in ("force_wrench_imbalance_n", "moment_wrench_imbalance_nm"):
            continue
        actual = report.get(key)
        if isinstance(limit, bool):
            checks[key] = actual is limit
        elif key.endswith("_steps"):
            checks[key] = actual == limit
        else:
            checks[key] = isinstance(actual, (float, int)) and 0 <= actual <= limit
    checks["all_step_wrenches"] = all(
        0 <= item.get("force_wrench_imbalance_n", float("inf"))
        <= criteria["force_wrench_imbalance_n"]
        and 0 <= item.get("moment_wrench_imbalance_nm", float("inf"))
        <= criteria["moment_wrench_imbalance_nm"]
        for item in report.get("differences", ())
    )
    verdict = {
        "case_id": registration["case_id"],
        "status": "pass" if all(checks.values()) else "fail",
        "registration_sha256": _hash(registration_path),
        "reference_sha256": _hash(reference_path),
        "report_sha256": _hash(report_path),
        "checks": checks,
        "independent_review": "pending",
    }
    output_path.write_text(json.dumps(verdict, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": verdict["status"],
                      "failed": [key for key, value in checks.items() if not value]}))


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("usage: adjudicator REGISTRATION REPORT OUTPUT")
    main(*(Path(argument) for argument in sys.argv[1:]))
