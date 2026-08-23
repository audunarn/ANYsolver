"""Independent exact checker for Q1G rigid-range proof records.

The checker imports canonical/matrix primitives only.  It does not import or
inspect the producer and independently reconstructs every scientific matrix.
"""

from __future__ import annotations

import argparse
import sys
from fractions import Fraction
from pathlib import Path
from typing import Any, Sequence

import e4_pl_q1g_common as common


CHECK_SCHEMA = "anysolver.s4.e4-pl-q1g-domain-check-v1"
PROOF_SCHEMA = "anysolver.s4.e4-pl-q1g-domain-proof-v1"


def _rigid(nodes: Sequence[tuple[Fraction, Fraction]]) -> common.Matrix:
    columns: list[list[Fraction]] = [[] for _ in range(6)]
    for x, y in nodes:
        node_columns = (
            (1, 0, 0, 0, 0, 0),
            (0, 1, 0, 0, 0, 0),
            (0, 0, 1, 0, 0, 0),
            (0, 0, y, 1, 0, 0),
            (0, 0, -x, 0, 1, 0),
            (-y, x, 0, 0, 0, 1),
        )
        for column, values in zip(columns, node_columns):
            column.extend(Fraction(value) for value in values)
    return common.transpose(columns)


def _pullback(rotation: common.Matrix, scale: Fraction) -> common.Matrix:
    block = [[Fraction() for _ in range(6)] for _ in range(6)]
    for i in range(2):
        for j in range(2):
            block[i][j] = scale * rotation[i][j]
            block[3 + i][3 + j] = rotation[i][j]
    block[2][2] = scale
    block[5][5] = 1
    result = [[Fraction() for _ in range(24)] for _ in range(24)]
    for n in range(4):
        for i in range(6):
            for j in range(6):
                result[6 * n + i][6 * n + j] = block[i][j]
    return result


def _analytic_parameter_map(a: tuple[Fraction, Fraction], rotation: common.Matrix, scale: Fraction) -> common.Matrix:
    ax, ay = a
    minus_j_a = (ay, -ax)
    projected = (
        rotation[0][0] * minus_j_a[0] + rotation[1][0] * minus_j_a[1],
        rotation[0][1] * minus_j_a[0] + rotation[1][1] * minus_j_a[1],
    )
    matrix = [[Fraction() for _ in range(6)] for _ in range(6)]
    for i in range(2):
        for j in range(2):
            matrix[i][j] = scale * rotation[i][j]
            matrix[3 + i][3 + j] = rotation[i][j]
    matrix[0][5], matrix[1][5] = ay, -ax
    matrix[2][2] = scale
    matrix[2][3], matrix[2][4] = -projected[0], -projected[1]
    matrix[5][5] = 1
    return matrix


def _verify_case(value: Any) -> bool:
    common.exact_keys(value, {"basis_change", "basis_change_determinant", "case_id", "gauge_nodes", "parameter_map", "parameter_map_determinant", "pivot_rows", "raw_nodes", "rotation", "scale", "translation"}, "rigid case")
    gauge_nodes = [(common.rational(row[0]), common.rational(row[1])) for row in value["gauge_nodes"]]
    raw_nodes = [(common.rational(row[0]), common.rational(row[1])) for row in value["raw_nodes"]]
    if len(gauge_nodes) != 4 or len(raw_nodes) != 4:
        raise common.Q1GError("rigid case node count mismatch")
    rotation = common.matrix_from_record(value["rotation"], 2, 2, "rotation")
    common.validate_proper_rotation(rotation)
    scale = common.rational(value["scale"])
    translation = (common.rational(value["translation"][0]), common.rational(value["translation"][1]))
    if scale <= 0:
        raise common.Q1GError("nonpositive scale")
    reconstructed_nodes = [
        (
            translation[0] + scale * (rotation[0][0] * x + rotation[0][1] * y),
            translation[1] + scale * (rotation[1][0] * x + rotation[1][1] * y),
        )
        for x, y in gauge_nodes
    ]
    if reconstructed_nodes != raw_nodes:
        raise common.Q1GError("raw node reconstruction mismatch")
    r_gauge, r_raw = _rigid(gauge_nodes), _rigid(raw_nodes)
    transformed = common.multiply(_pullback(rotation, scale), r_gauge)
    analytic_c = _analytic_parameter_map(translation, rotation, scale)
    recorded_c = common.matrix_from_record(value["parameter_map"], 6, 6, "parameter map")
    recorded_b = common.matrix_from_record(value["basis_change"], 6, 6, "basis change")
    if not common.matrix_equal(recorded_c, analytic_c):
        raise common.Q1GError("analytic parameter map mismatch")
    if common.determinant(analytic_c) != scale**3 or common.rational(value["parameter_map_determinant"]) != scale**3:
        raise common.Q1GError("parameter determinant mismatch")
    if not common.matrix_equal(transformed, common.multiply(r_raw, analytic_c)):
        raise common.Q1GError("independent G=R*C identity mismatch")
    pivots = common.leftmost_independent_rows(transformed, 6)
    if value["pivot_rows"] != list(pivots):
        raise common.Q1GError("leftmost pivot-row mismatch")
    independent_b = common.multiply(common.inverse(common.subrows(transformed, pivots)), common.subrows(r_raw, pivots))
    if not common.matrix_equal(recorded_b, independent_b) or not common.matrix_equal(recorded_b, common.inverse(analytic_c)):
        raise common.Q1GError("basis-change reconstruction mismatch")
    if common.rational(value["basis_change_determinant"]) != 1 / scale**3:
        raise common.Q1GError("basis-change determinant mismatch")
    if not common.matrix_equal(r_raw, common.multiply(transformed, recorded_b)):
        raise common.Q1GError("independent range identity mismatch")
    return True


def verify(repository_root: Path, contract_path: Path, contract_sha256: str, proof_path: Path, replica_id: str, output: Path) -> None:
    common.validate_contract(repository_root, contract_path, contract_sha256)
    proof_raw, proof = common.read_json(proof_path)
    common.exact_keys(proof, {"candidate_id", "contract_sha256", "domain_leaf", "producer_id", "rigid_cases", "schema", "shard_id", "study_id"}, "proof")
    if proof["schema"] != PROOF_SCHEMA or proof["study_id"] != common.STUDY_ID or proof["candidate_id"] != common.CANDIDATE_ID or proof["contract_sha256"] != contract_sha256.upper():
        raise common.Q1GError("proof identity mismatch")
    if proof["domain_leaf"].get("classification") not in {"POSITIVE", "NEGATIVE", "UNRESOLVED"}:
        raise common.Q1GError("invalid domain classification")
    exact = len(proof["rigid_cases"]) == 3 and all(_verify_case(row) for row in proof["rigid_cases"])
    result = {
        "basis_change_nonsingular": exact,
        "candidate_id": common.CANDIDATE_ID,
        "checker_id": "Q1G_INDEPENDENT_RIGID_RANGE_CHECKER",
        "contract_sha256": contract_sha256.upper(),
        "findings": [],
        "proof_sha256": common.sha256(proof_raw),
        "replica_id": replica_id,
        "rigid_range_exact": exact,
        "schema": CHECK_SCHEMA,
        "shard_id": proof["shard_id"],
        "status": "PASS" if exact else "INVALID",
        "study_id": common.STUDY_ID,
    }
    common.write_exclusive(output, result)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-domain-proof", action="store_true")
    parser.add_argument("--repository-root", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--contract-sha256", required=True)
    parser.add_argument("--proof", type=Path, required=True)
    parser.add_argument("--replica-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if not args.verify_domain_proof:
        return 2
    try:
        verify(args.repository_root, args.contract, args.contract_sha256, args.proof, args.replica_id, args.output)
    except common.Q1GError as exc:
        print(f"BLOCKED_E4_PL_Q1G_PROOF_OR_NONDETERMINISM: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
