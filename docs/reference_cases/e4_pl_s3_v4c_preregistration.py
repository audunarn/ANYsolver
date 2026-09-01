"""Standard-library-only V4C physical-first construction validator."""

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
CONTRACT = REFERENCE / "e4_pl_s3_v4c_preregistration_contract.json"
FORMULATION_ID = "CANDIDATE_E4_PL_S3_V4C_Q4_SUBCELL_PHYSICAL_FIRST_FLAT_LINEAR_V1"


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


def physical_restriction() -> list[list[F]]:
    made = [[F(0) for _ in range(20)] for _ in range(42)]
    for node in range(3):
        for physical in range(5):
            made[6 * node + physical][5 * node + physical] = F(1)
    for edge, (left, right) in enumerate(((0, 1), (1, 2), (2, 0))):
        point = edge + 3
        for physical in range(5):
            made[6 * point + physical][5 * left + physical] = F(1, 2)
            made[6 * point + physical][5 * right + physical] = F(1, 2)
    for physical in range(5):
        made[36 + physical][15 + physical] = F(1)
    return made


def external_embedding() -> list[list[F]]:
    made = [[F(0) for _ in range(15)] for _ in range(18)]
    for node in range(3):
        for physical in range(5):
            made[6 * node + physical][5 * node + physical] = F(1)
    return made


def validate() -> dict[str, Any]:
    contract = load_document(CONTRACT)
    if contract.get("schema") != "anysolver.e4-pl-s3-v4c-preregistration-contract-v1":
        raise ValueError("unexpected V4C preregistration contract")
    for item in contract["frozen_inputs"]:
        path = ROOT / item["path"]
        if not path.is_file() or path.is_symlink() or path.stat().st_size != item["bytes"] or sha256_file(path) != item["sha256"]:
            raise ValueError(f"frozen input mismatch: {path}")
    predecessor = load_document(REFERENCE / "e4_pl_s3_v4b_screen_status.json")
    if predecessor.get("terminal") != "NO_GO_E4_PL_S3_V4B_LOCAL_OPERATOR" or predecessor.get("stage4a_rerun_authorized") is not False:
        raise ValueError("V4B predecessor is not canonically closed")
    restriction = physical_restriction()
    embedding = external_embedding()
    restriction_rank = _rank(restriction)
    embedding_rank = _rank(embedding)
    zero_drill_rows = all(not any(restriction[6 * point + 5]) for point in range(7))
    construction_passed = bool(restriction_rank == 20 and embedding_rank == 15 and zero_drill_rows)
    return {
        "activation_authorized": False,
        "candidate_formulation_id": FORMULATION_ID,
        "construction": {
            "external_embedding_columns": 15,
            "external_embedding_rank": embedding_rank,
            "external_embedding_rows": 18,
            "internal_physical_coordinate_count": 5,
            "physical_restriction_columns": 20,
            "physical_restriction_rank": restriction_rank,
            "physical_restriction_rows": 42,
            "zero_q4_drill_row_count": 7,
            "zero_q4_drill_rows": zero_drill_rows,
        },
        "contract_sha256": sha256_file(CONTRACT),
        "next_gate": "BOUNDED_V4C_PHYSICAL_FIRST_IMPLEMENTATION_SCREEN",
        "next_gate_authorized": construction_passed,
        "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "schema": "anysolver.e4-pl-s3-v4c-preregistration-result-v1",
        "stage4a_rerun_authorized": False,
        "terminal": "PROVISIONAL_GO_E4_PL_S3_V4C_BOUNDED_PHYSICAL_FIRST_SCREEN" if construction_passed else "NO_GO_E4_PL_S3_V4C_CONSTRUCTION_IDENTITY",
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
