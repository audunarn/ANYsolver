"""Capture OpenSees coupled shell action under the E01 pure-torque load."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
import sys

from scripts.b3_e4_e01_external_coupled_shell_action import (
    CaptureShellForces, _assemble, _resultant,
)
from scripts.b3_e4_e01_opensees_torque_dev import solve


def _sha(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def main(site: Path, action_file: Path, report_file: Path):
    if sys.version_info[:2] != (3, 12):
        raise RuntimeError("pinned OpenSees binary requires Python 3.12")
    if action_file.exists() or report_file.exists():
        raise FileExistsError("preserve earlier E01 torque action evidence")
    sys.path.insert(0, str(site))
    import openseespy.opensees as ops
    from openseespywin import opensees as core
    proxy = CaptureShellForces(ops)
    try:
        coupled = solve(proxy, +1, 8, 4)
    finally:
        ops.wipe()
    action = _assemble(proxy.shell_forces)
    displacement = {int(k): v for k, v in
                    coupled["node_displacements"].items()}
    work = sum(sum(force[d]*displacement[node][d] for d in range(6))
               for node, force in action.items())
    total = coupled["element_internal_virtual_work_j"]
    if not math.isfinite(work) or work < 0. or work > total*(1.+1e-8):
        raise ValueError("external shell-work inventory inconsistent")
    roots = {1+row*9 for row in range(5)}
    free = {node: ([0.]*6 if node in roots else row)
            for node, row in action.items()}
    force, moment = _resultant(free)
    record = {
        "classification": "E01 same-action shell covector; development only",
        "source_sha256": _sha(__file__),
        "load_source": "external OpenSees coupled +100 N m beam-tip physical x",
        "shell_intervals": 8,
        "transverse_intervals": 4,
        "loads": {str(node): row for node, row in free.items()},
        "external_coupled_shell_displacements": {
            str(node): displacement[node] for node in free},
    }
    report = {
        "classification": "E01 external pure-torque shell action; development only",
        "source_sha256": _sha(__file__),
        "torque_runner_sha256": _sha(Path(__file__).with_name(
            "b3_e4_e01_opensees_torque_dev.py")),
        "binary_sha256": _sha(core.__file__),
        "python": sys.version.split()[0],
        "opensees_version": ops.version(),
        "shell_internal_work_j": work,
        "coupled_total_work_j": total,
        "coupled_link_gap": coupled["maximum_link_gap"],
        "coupled_support_force_error_n":
            coupled["support_force_residual_n"],
        "coupled_support_moment_error_nm":
            coupled["support_moment_residual_nm"],
        "free_shell_force_n": force,
        "free_shell_moment_nm": moment,
        "limit": "Action recovery requires independent isolated-shell replay.",
    }
    action_file.write_text(json.dumps(record, indent=2, sort_keys=True,
                                      allow_nan=False)+"\n", encoding="utf-8")
    report_file.write_text(json.dumps(report, indent=2, sort_keys=True,
                                      allow_nan=False)+"\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", required=True, type=Path)
    parser.add_argument("--action-output", required=True, type=Path)
    parser.add_argument("--report-output", required=True, type=Path)
    args = parser.parse_args()
    result = main(args.site, args.action_output, args.report_output)
    print(json.dumps({"shell_work_j": result["shell_internal_work_j"],
                      "coupled_work_j": result["coupled_total_work_j"]}))
