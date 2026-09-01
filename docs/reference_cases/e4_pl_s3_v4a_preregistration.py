"""Standard-library validator for the V4A Q4-subcell preregistration."""

from __future__ import annotations

import argparse
from fractions import Fraction as F
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any, Sequence


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "docs" / "reference_cases"
CONTRACT = REFERENCE / "e4_pl_s3_v4a_preregistration_contract.json"
RESULT_SCHEMA = "anysolver.e4-pl-s3-v4a-preregistration-output-v1"


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("ascii")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


def _unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    made: dict[str, Any] = {}
    for key, value in pairs:
        if key in made:
            raise ValueError(f"duplicate key {key!r}")
        made[key] = value
    return made


def load_canonical(path: Path) -> dict[str, Any]:
    raw = Path(path).read_bytes()
    value = json.loads(raw, object_pairs_hook=_unique, parse_constant=lambda token: (_ for _ in ()).throw(ValueError(f"nonfinite {token}")))
    if raw != canonical_bytes(value):
        raise ValueError(f"{path.name} is not canonical JSON")
    return value


def _rank(matrix: list[list[F]]) -> int:
    work = [list(row) for row in matrix]
    row = 0
    for column in range(len(work[0])):
        pivot = next((index for index in range(row, len(work)) if work[index][column]), None)
        if pivot is None:
            continue
        work[row], work[pivot] = work[pivot], work[row]
        divisor = work[row][column]
        work[row] = [item / divisor for item in work[row]]
        for index in range(len(work)):
            if index == row or not work[index][column]:
                continue
            factor = work[index][column]
            work[index] = [item - factor * selected for item, selected in zip(work[index], work[row])]
        row += 1
    return row


def _signed_polygon_area(points: list[tuple[F, F]]) -> F:
    return sum((points[index][0] * points[(index + 1) % len(points)][1] - points[(index + 1) % len(points)][0] * points[index][1] for index in range(len(points))), F(0)) / 2


def validate() -> dict[str, Any]:
    contract = load_canonical(CONTRACT)
    if contract.get("schema") != "anysolver.e4-pl-s3-v4a-preregistration-contract-v1":
        raise ValueError("unexpected V4A contract schema")
    for item in contract["frozen_inputs"]:
        path = ROOT / item["path"]
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"frozen input is not a regular file: {path}")
        if path.stat().st_size != item["bytes"] or sha256_bytes(path.read_bytes()) != item["sha256"]:
            raise ValueError(f"frozen input mismatch: {path}")
    predecessor = load_canonical(REFERENCE / "e4_pl_s3_v3a_implementation_screen_status.json")
    if predecessor.get("terminal") != "NO_GO_E4_PL_S3_V3A_LOCAL_OPERATOR" or predecessor.get("stage4a_rerun_authorized") is not False:
        raise ValueError("V3A predecessor is not closed at its local NO-GO")
    q4 = load_canonical(REFERENCE / "e4_pl_q1m_gate_result.json")
    if q4.get("production_boundary", {}).get("mechanics_changed") is not False or q4.get("hard_gates", {}).get("q4_numerical_parity", {}).get("status") != "PASS":
        raise ValueError("qualified Q4 authority is not accepted and unchanged")

    vertices = ((F(0), F(0)), (F(1), F(0)), (F(0), F(1)))
    midpoints = tuple(((vertices[a][0] + vertices[b][0]) / 2, (vertices[a][1] + vertices[b][1]) / 2) for a, b in ((0, 1), (1, 2), (2, 0)))
    centre = (sum(point[0] for point in vertices) / 3, sum(point[1] for point in vertices) / 3)
    points = vertices + midpoints + (centre,)
    subcells = ((0, 3, 6, 5), (1, 4, 6, 3), (2, 5, 6, 4))
    areas = tuple(_signed_polygon_area([points[index] for index in cell]) for cell in subcells)
    scalar_constraint = [
        [F(1), F(0), F(0), F(0)],
        [F(0), F(1), F(0), F(0)],
        [F(0), F(0), F(1), F(0)],
        [F(1, 2), F(1, 2), F(0), F(0)],
        [F(0), F(1, 2), F(1, 2), F(0)],
        [F(1, 2), F(0), F(1, 2), F(0)],
        [F(0), F(0), F(0), F(1)],
    ]
    construction_passed = bool(all(area > 0 for area in areas) and sum(areas, F(0)) == F(1, 2) and _rank(scalar_constraint) == 4)
    if not construction_passed:
        raise ValueError("V4A subcell partition or affine constraint identity failed")
    execution = contract["execution"]
    if execution["child_wall_seconds"] > 600 or execution["complete_wave_wall_seconds"] > 1800 or execution["maximum_concurrent_workers"] > 3:
        raise ValueError("V4A execution exceeds preregistered safeguards")
    return {
        "activation_authorized": False,
        "candidate_formulation_id": contract["candidate"]["formulation_id"],
        "construction": {"constraint_scalar_rank": 4, "covered_area": "1/2", "positive_subcell_count": 3, "subcell_areas": [str(area) for area in areas]},
        "contract_sha256": sha256_bytes(CONTRACT.read_bytes()),
        "next_gate": "BOUNDED_V4A_Q4_SUBCELL_IMPLEMENTATION_SCREEN",
        "next_gate_authorized": True,
        "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "schema": RESULT_SCHEMA,
        "stage4a_rerun_authorized": False,
        "terminal": "PROVISIONAL_GO_E4_PL_S3_V4A_BOUNDED_SUBCELL_SCREEN",
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    raw = canonical_bytes(validate())
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_BINARY", 0)
    descriptor = os.open(output, flags, 0o600)
    try:
        os.write(descriptor, raw)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
