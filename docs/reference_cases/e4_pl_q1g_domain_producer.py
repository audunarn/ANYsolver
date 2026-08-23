"""Exact Q1G rigid-range proof producer.

The producer certifies the corrected gauge theorem and deliberately leaves the
continuous K/H interval campaign unresolved until executable mechanics coverage
exists.  It never imports the checker.
"""

from __future__ import annotations

import argparse
import sys
from fractions import Fraction
from pathlib import Path
from typing import Any, Sequence

import e4_pl_q1g_common as common


PROOF_SCHEMA = "anysolver.s4.e4-pl-q1g-domain-proof-v1"
PRODUCER_ID = "Q1G_EXACT_RIGID_RANGE_PRODUCER"


def _rigid_matrix(nodes: Sequence[tuple[Fraction, Fraction]]) -> common.Matrix:
    result: common.Matrix = []
    for x, y in nodes:
        result.extend(
            [
                [1, 0, 0, 0, 0, -y],
                [0, 1, 0, 0, 0, x],
                [0, 0, 1, y, -x, 0],
                [0, 0, 0, 1, 0, 0],
                [0, 0, 0, 0, 1, 0],
                [0, 0, 0, 0, 0, 1],
            ]
        )
    return [[Fraction(value) for value in row] for row in result]


def _dof_pullback(rotation: common.Matrix, scale: Fraction) -> common.Matrix:
    block: common.Matrix = [
        [scale * rotation[0][0], scale * rotation[0][1], 0, 0, 0, 0],
        [scale * rotation[1][0], scale * rotation[1][1], 0, 0, 0, 0],
        [0, 0, scale, 0, 0, 0],
        [0, 0, 0, rotation[0][0], rotation[0][1], 0],
        [0, 0, 0, rotation[1][0], rotation[1][1], 0],
        [0, 0, 0, 0, 0, 1],
    ]
    result = [[Fraction() for _ in range(24)] for _ in range(24)]
    for node in range(4):
        for row in range(6):
            for column in range(6):
                result[6 * node + row][6 * node + column] = block[row][column]
    return result


def _parameter_map(translation: tuple[Fraction, Fraction], rotation: common.Matrix, scale: Fraction) -> common.Matrix:
    ax, ay = translation
    # b = R^T (-J a), where -J a = (ay,-ax).
    b0 = rotation[0][0] * ay + rotation[1][0] * (-ax)
    b1 = rotation[0][1] * ay + rotation[1][1] * (-ax)
    return [
        [scale * rotation[0][0], scale * rotation[0][1], 0, 0, 0, ay],
        [scale * rotation[1][0], scale * rotation[1][1], 0, 0, 0, -ax],
        [0, 0, scale, -b0, -b1, 0],
        [0, 0, 0, rotation[0][0], rotation[0][1], 0],
        [0, 0, 0, rotation[1][0], rotation[1][1], 0],
        [0, 0, 0, 0, 0, 1],
    ]


def _raw_nodes(nodes: Sequence[tuple[Fraction, Fraction]], translation: tuple[Fraction, Fraction], rotation: common.Matrix, scale: Fraction) -> list[tuple[Fraction, Fraction]]:
    ax, ay = translation
    return [
        (
            ax + scale * (rotation[0][0] * x + rotation[0][1] * y),
            ay + scale * (rotation[1][0] * x + rotation[1][1] * y),
        )
        for x, y in nodes
    ]


def _case(index: int, translation: tuple[Fraction, Fraction], rotation: common.Matrix, scale: Fraction) -> dict[str, Any]:
    common.validate_proper_rotation(rotation)
    if scale <= 0:
        raise common.Q1GError("scale must be positive")
    gauge_nodes = [(Fraction(-1), Fraction(-1)), (Fraction(1), Fraction(-1)), (Fraction(1), Fraction(1)), (Fraction(-1), Fraction(1))]
    raw_nodes = _raw_nodes(gauge_nodes, translation, rotation, scale)
    r_gauge = _rigid_matrix(gauge_nodes)
    r_raw = _rigid_matrix(raw_nodes)
    pullback = _dof_pullback(rotation, scale)
    transformed = common.multiply(pullback, r_gauge)
    parameter_map = _parameter_map(translation, rotation, scale)
    if not common.matrix_equal(transformed, common.multiply(r_raw, parameter_map)):
        raise common.Q1GError("G=R_raw*C exact identity failed")
    if common.determinant(parameter_map) != scale**3:
        raise common.Q1GError("rigid parameter determinant identity failed")
    pivot_rows = common.leftmost_independent_rows(transformed, 6)
    basis_change = common.multiply(common.inverse(common.subrows(transformed, pivot_rows)), common.subrows(r_raw, pivot_rows))
    if not common.matrix_equal(r_raw, common.multiply(transformed, basis_change)):
        raise common.Q1GError("R_raw=G*B exact identity failed")
    if not common.matrix_equal(basis_change, common.inverse(parameter_map)):
        raise common.Q1GError("deterministic basis change differs from C inverse")
    return {
        "basis_change": common.matrix_record(basis_change),
        "basis_change_determinant": common.token(common.determinant(basis_change)),
        "case_id": f"RIGID_TRANSFORM_{index}",
        "gauge_nodes": [[common.token(x), common.token(y)] for x, y in gauge_nodes],
        "parameter_map": common.matrix_record(parameter_map),
        "parameter_map_determinant": common.token(common.determinant(parameter_map)),
        "pivot_rows": list(pivot_rows),
        "raw_nodes": [[common.token(x), common.token(y)] for x, y in raw_nodes],
        "rotation": common.matrix_record(rotation),
        "scale": common.token(scale),
        "translation": [common.token(translation[0]), common.token(translation[1])],
    }


def produce(repository_root: Path, contract_path: Path, contract_sha256: str, shard_id: str, output: Path) -> None:
    contract = common.validate_contract(repository_root, contract_path, contract_sha256)
    shards = {row["shard_id"]: row for row in contract["domain"]["root_shards"]}
    if shard_id not in shards:
        raise common.Q1GError("unknown frozen shard")
    cases = [_case(index, *transform) for index, transform in enumerate(common.sample_transforms())]
    proof = {
        "candidate_id": common.CANDIDATE_ID,
        "contract_sha256": contract_sha256.upper(),
        "domain_leaf": {
            "classification": "UNRESOLVED",
            "reason": "EXECUTABLE_K_H_INTERVAL_COVERAGE_NOT_ESTABLISHED",
            "root_bounds": shards[shard_id]["bounds"],
        },
        "producer_id": PRODUCER_ID,
        "rigid_cases": cases,
        "schema": PROOF_SCHEMA,
        "shard_id": shard_id,
        "study_id": common.STUDY_ID,
    }
    common.write_exclusive(output, proof)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--emit-domain-proof", action="store_true")
    parser.add_argument("--repository-root", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--contract-sha256", required=True)
    parser.add_argument("--shard-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if not args.emit_domain_proof:
        return 2
    try:
        produce(args.repository_root, args.contract, args.contract_sha256, args.shard_id, args.output)
    except common.Q1GError as exc:
        print(f"BLOCKED_E4_PL_Q1G_REDUCTION_IDENTITY: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
