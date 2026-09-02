"""Standard-library-only V4B construction preregistration validator."""

from __future__ import annotations

import argparse
from fractions import Fraction as F
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Sequence


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "docs" / "reference_cases"
CONTRACT = REFERENCE / "e4_pl_s3_v4b_preregistration_contract.json"
FORMULATION_ID = "CANDIDATE_E4_PL_S3_V4B_Q4_SUBCELL_DRILL_RELEASE_FLAT_LINEAR_V1"


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("ascii")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()


def _unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate key {key!r}")
        value[key] = item
    return value


def load_document(path: Path) -> dict[str, Any]:
    raw = Path(path).read_bytes()
    value = json.loads(raw, object_pairs_hook=_unique, parse_constant=lambda token: (_ for _ in ()).throw(ValueError(token)))
    if raw != canonical_bytes(value):
        raise ValueError(f"{path.name} is not canonical JSON")
    return value


def _rank(matrix: list[list[F]]) -> int:
    work = [list(row) for row in matrix]
    row = 0
    for column in range(len(work[0])):
        pivot = next((candidate for candidate in range(row, len(work)) if work[candidate][column]), None)
        if pivot is None:
            continue
        work[row], work[pivot] = work[pivot], work[row]
        divisor = work[row][column]
        work[row] = [item / divisor for item in work[row]]
        for other in range(len(work)):
            if other == row or not work[other][column]:
                continue
            factor = work[other][column]
            work[other] = [item - factor * selected for item, selected in zip(work[other], work[row])]
        row += 1
    return row


def restriction() -> list[list[F]]:
    made = [[F(0) for _ in range(27)] for _ in range(42)]
    for node in range(3):
        for component in range(6):
            made[6 * node + component][6 * node + component] = F(1)
    edges = ((0, 1), (1, 2), (2, 0))
    for edge, (left, right) in enumerate(edges):
        point = edge + 3
        for component in range(5):
            made[6 * point + component][6 * left + component] = F(1, 2)
            made[6 * point + component][6 * right + component] = F(1, 2)
        made[6 * point + 5][18 + edge] = F(1)
    for component in range(6):
        made[36 + component][21 + component] = F(1)
    return made


def validate() -> dict[str, Any]:
    contract = load_document(CONTRACT)
    if contract.get("schema") != "anysolver.e4-pl-s3-v4b-preregistration-contract-v1":
        raise ValueError("unexpected V4B preregistration contract")
    for item in contract["frozen_inputs"]:
        path = ROOT / item["path"]
        if not path.is_file() or path.is_symlink() or path.stat().st_size != item["bytes"] or sha256_file(path) != item["sha256"]:
            raise ValueError(f"frozen input mismatch: {path}")
    predecessor = load_document(REFERENCE / "e4_pl_s3_v4a_screen_status.json")
    if predecessor.get("terminal") != "NO_GO_E4_PL_S3_V4A_LOCAL_OPERATOR" or predecessor.get("stage4a_rerun_authorized") is not False:
        raise ValueError("V4A predecessor is not canonically closed")
    mapping = restriction()
    mapping_rank = _rank(mapping)
    rows_nonempty = all(any(row) for row in mapping)
    areas = (F(1, 6), F(1, 6), F(1, 6))
    construction_passed = bool(mapping_rank == 27 and rows_nonempty and sum(areas, F(0)) == F(1, 2))
    terminal = (
        "PROVISIONAL_GO_E4_PL_S3_V4B_BOUNDED_DRILL_RELEASE_SCREEN"
        if construction_passed
        else "NO_GO_E4_PL_S3_V4B_CONSTRUCTION_IDENTITY"
    )
    return {
        "activation_authorized": False,
        "candidate_formulation_id": FORMULATION_ID,
        "construction": {
            "barycentre_internal_coordinate_count": 6,
            "covered_area": "1/2",
            "external_coordinate_count": 18,
            "midpoint_drill_internal_coordinate_count": 3,
            "physical_midpoint_affine_row_count": 15,
            "positive_subcell_count": 3,
            "restriction_columns": 27,
            "restriction_rank": mapping_rank,
            "restriction_rows": 42,
            "rows_nonempty": rows_nonempty,
            "total_internal_coordinate_count": 9,
        },
        "contract_sha256": sha256_file(CONTRACT),
        "next_gate": "BOUNDED_V4B_Q4_SUBCELL_DRILL_RELEASE_IMPLEMENTATION_SCREEN",
        "next_gate_authorized": construction_passed,
        "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "schema": "anysolver.e4-pl-s3-v4b-preregistration-result-v1",
        "stage4a_rerun_authorized": False,
        "terminal": terminal,
    }


def exclusive_write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(canonical_bytes(value))
        stream.flush()
        os.fsync(stream.fileno())


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    exclusive_write(args.output, validate())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
