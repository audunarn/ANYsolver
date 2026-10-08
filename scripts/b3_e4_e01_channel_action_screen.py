"""Allocate the E01 coupled-action difference across shell load channels.

This bounded development screen keeps the native 8x4 shell operator fixed.
It does not identify why the two coupled models produce different actions.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path

from scripts.b3_e4_e01_shell_only_native import solve


CLASSIFICATION = "E01 same-action shell covector; development only"


def _read_action(path: Path):
    raw = path.read_bytes()
    record = json.loads(raw)
    if (record.get("classification") != CLASSIFICATION
            or record.get("shell_intervals") != 8
            or record.get("transverse_intervals") != 4):
        raise ValueError("incompatible E01 8x4 shell action")
    loads = {int(node): tuple(map(float, row))
             for node, row in record["loads"].items()}
    if (len(loads) != 45 or any(len(row) != 6 or
                               not all(map(math.isfinite, row))
                               for row in loads.values())):
        raise ValueError("complete finite E01 action required")
    return raw, loads


def main(native_path: Path, external_path: Path, output: Path):
    if output.exists():
        raise FileExistsError("preserve earlier E01 channel evidence")
    native_raw, native = _read_action(native_path)
    external_raw, external = _read_action(external_path)
    if native.keys() != external.keys():
        raise ValueError("same shell node identities required")
    differences = {node: tuple(external[node][d]-native[node][d]
                               for d in range(6)) for node in native}
    cases = []
    for channel in range(6):
        load = {node: tuple(row[d] if d == channel else 0.
                            for d in range(6))
                for node, row in differences.items()}
        result = solve(None, load, 4)
        cases.append({
            "channel": ("Fx", "Fy", "Fz", "Mx", "My", "Mz")[channel],
            "bond_tip_roll_rad": result["node_displacements"][9][3],
            "max_abs_load": max(abs(row[channel]) for row in load.values()),
            "free_residual": result["free_residual_n"],
            "force_error_n": result["force_error_n"],
            "moment_error_nm": result["moment_error_nm"],
            "work_error_j": result["work_error_j"],
        })
    full = solve(None, differences, 4)
    summed = sum(case["bond_tip_roll_rad"] for case in cases)
    actual = full["node_displacements"][9][3]
    if abs(summed-actual) > 1e-9*max(abs(actual), 1e-12):
        raise ValueError("channel superposition failed")
    record = {
        "classification": "E01 action-channel allocation; development only",
        "source_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "native_action_sha256": sha256(native_raw).hexdigest(),
        "external_action_sha256": sha256(external_raw).hexdigest(),
        "shell_intervals": 8,
        "transverse_intervals": 4,
        "cases": cases,
        "sum_channel_roll_rad": summed,
        "full_difference_roll_rad": actual,
        "superposition_error_rad": abs(summed-actual),
        "limit": "Fixed native shell operator only; no causal attribution or E01 qualification.",
    }
    output.write_text(json.dumps(record, indent=2, sort_keys=True,
                                 allow_nan=False)+"\n", encoding="utf-8")
    return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native-action", required=True, type=Path)
    parser.add_argument("--external-action", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = main(args.native_action, args.external_action, args.output)
    print(json.dumps({case["channel"]: case["bond_tip_roll_rad"]
                      for case in result["cases"]}))
