"""Standard-library-only V4D Hermite-edge construction validator."""

from __future__ import annotations

import argparse
from fractions import Fraction as F
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Callable, Sequence


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "docs" / "reference_cases"
CONTRACT = REFERENCE / "e4_pl_s3_v4d_preregistration_contract.json"
FORMULATION_ID = "CANDIDATE_E4_PL_S3_V4D_Q4_SUBCELL_HERMITE_EDGE_FLAT_LINEAR_V1"
VERTICES = ((F(0), F(0)), (F(1), F(0)), (F(1, 5), F(9, 10)))
EDGES = ((0, 1), (1, 2), (2, 0))


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


def hermite_restriction(vertices: Sequence[tuple[F, F]] = VERTICES) -> list[list[F]]:
    made = [[F(0) for _ in range(20)] for _ in range(42)]
    for node in range(3):
        for physical in range(5):
            made[6 * node + physical][5 * node + physical] = F(1)
    for edge, (left, right) in enumerate(EDGES):
        point = edge + 3
        dx = vertices[right][0] - vertices[left][0]
        dy = vertices[right][1] - vertices[left][1]
        for physical in (0, 1, 3, 4):
            made[6 * point + physical][5 * left + physical] = F(1, 2)
            made[6 * point + physical][5 * right + physical] = F(1, 2)
        made[6 * point + 2][5 * left + 2] = F(1, 2)
        made[6 * point + 2][5 * right + 2] = F(1, 2)
        made[6 * point + 2][5 * left + 3] = dy / 8
        made[6 * point + 2][5 * left + 4] = -dx / 8
        made[6 * point + 2][5 * right + 3] = -dy / 8
        made[6 * point + 2][5 * right + 4] = dx / 8
    for physical in range(5):
        made[36 + physical][15 + physical] = F(1)
    return made


def external_embedding() -> list[list[F]]:
    made = [[F(0) for _ in range(15)] for _ in range(18)]
    for node in range(3):
        for physical in range(5):
            made[6 * node + physical][5 * node + physical] = F(1)
    return made


def _quadratic_cases() -> dict[str, tuple[Callable[[F, F], F], Callable[[F, F], F], Callable[[F, F], F]]]:
    return {
        "one": (lambda x, y: F(1), lambda x, y: F(0), lambda x, y: F(0)),
        "x": (lambda x, y: x, lambda x, y: F(1), lambda x, y: F(0)),
        "y": (lambda x, y: y, lambda x, y: F(0), lambda x, y: F(1)),
        "x2": (lambda x, y: x * x, lambda x, y: 2 * x, lambda x, y: F(0)),
        "y2": (lambda x, y: y * y, lambda x, y: F(0), lambda x, y: 2 * y),
        "xy": (lambda x, y: x * y, lambda x, y: y, lambda x, y: x),
    }


def _reproduction() -> tuple[int, bool]:
    checked = 0
    complete = True
    for value, derivative_x, derivative_y in _quadratic_cases().values():
        for left, right in EDGES:
            xi, yi = VERTICES[left]
            xj, yj = VERTICES[right]
            dx, dy = xj - xi, yj - yi
            slope_i = dx * derivative_x(xi, yi) + dy * derivative_y(xi, yi)
            slope_j = dx * derivative_x(xj, yj) + dy * derivative_y(xj, yj)
            hermite = (value(xi, yi) + value(xj, yj)) / 2 + (slope_i - slope_j) / 8
            exact = value((xi + xj) / 2, (yi + yj) / 2)
            checked += 1
            complete = complete and hermite == exact
    return checked, complete


def validate() -> dict[str, Any]:
    contract = load_document(CONTRACT)
    if contract.get("schema") != "anysolver.e4-pl-s3-v4d-preregistration-contract-v1":
        raise ValueError("unexpected V4D preregistration contract")
    for item in contract["frozen_inputs"]:
        path = ROOT / item["path"]
        if not path.is_file() or path.is_symlink() or path.stat().st_size != item["bytes"] or sha256_file(path) != item["sha256"]:
            raise ValueError(f"frozen input mismatch: {path}")
    predecessor = load_document(REFERENCE / "e4_pl_s3_v4c_screen_status.json")
    if predecessor.get("terminal") != "NO_GO_E4_PL_S3_V4C_MIXED_INTERFACE" or predecessor.get("stage4a_rerun_authorized") is not False:
        raise ValueError("V4C predecessor is not canonically closed")
    restriction_rank = _rank(hermite_restriction())
    embedding_rank = _rank(external_embedding())
    reproduction_count, reproduction_exact = _reproduction()
    complete = bool(restriction_rank == 20 and embedding_rank == 15 and reproduction_count == 18 and reproduction_exact)
    return {
        "activation_authorized": False,
        "candidate_formulation_id": FORMULATION_ID,
        "construction": {
            "external_embedding_rank": embedding_rank,
            "hermite_midpoint_coefficient": "1/8",
            "physical_restriction_rank": restriction_rank,
            "quadratic_reproduction_case_count": reproduction_count,
            "quadratic_reproduction_exact": reproduction_exact,
            "q4_drill_rows_excluded": True,
        },
        "contract_sha256": sha256_file(CONTRACT),
        "next_gate": "BOUNDED_V4D_HERMITE_EDGE_IMPLEMENTATION_SCREEN",
        "next_gate_authorized": complete,
        "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "schema": "anysolver.e4-pl-s3-v4d-preregistration-result-v1",
        "stage4a_rerun_authorized": False,
        "terminal": "PROVISIONAL_GO_E4_PL_S3_V4D_BOUNDED_HERMITE_EDGE_SCREEN" if complete else "NO_GO_E4_PL_S3_V4D_CONSTRUCTION_IDENTITY",
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
