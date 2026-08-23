"""Q1Y3 independent checker with the corrected MITC tying construction."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Sequence

import e4_pl_q1v_oracle as oracle
import e4_pl_q1y2_algebra_checker as previous
import e4_pl_q1y_common as q1y


CHECK_SCHEMA = "anysolver.s4.e4-pl-q1y3-algebra-check-v1"
CONTRACT_SCHEMA = "anysolver.s4.e4-pl-q1y3-local-algebra-contract-v1"
TYING_POLICY = "INTERPOLATE_COVARIANT_TYING_ROWS_THEN_APPLY_CURRENT_J_INVERSE_TRANSPOSE"
_REJECTED_BLOCKS = previous.prior._blocks


def _shape(field: Any, r: Any, s: Any) -> list[Any]:
    one = field.exact(1)
    return [
        (one - r) * (one - s) / 4,
        (one + r) * (one - s) / 4,
        (one + r) * (one + s) / 4,
        (one - r) * (one + s) / 4,
    ]


def _natural_shear_row(geometry: Any, r: Any, s: Any, direction: int) -> list[Any]:
    field = geometry.field
    shape = _shape(field, r, s)
    nr, ns = oracle._shape_derivatives(field, r, s)
    derivative = nr if direction == 0 else ns
    zero = field.exact(0)
    x_derivative = sum((geometry.local_nodes[index][0] * derivative[index] for index in range(4)), zero)
    y_derivative = sum((geometry.local_nodes[index][1] * derivative[index] for index in range(4)), zero)
    row = [zero for _ in range(20)]
    for index in range(4):
        base = 5 * index
        row[base + 2] = derivative[index]
        row[base + 3] = -y_derivative * shape[index]
        row[base + 4] = x_derivative * shape[index]
    return row


def _mitc_shear_rows(geometry: Any, r: Any, s: Any) -> tuple[list[Any], list[Any]]:
    field = geometry.field
    zero, one = field.exact(0), field.exact(1)
    half = one / 2
    gr_a = _natural_shear_row(geometry, zero, -one, 0)
    gr_c = _natural_shear_row(geometry, zero, one, 0)
    gs_b = _natural_shear_row(geometry, one, zero, 1)
    gs_d = _natural_shear_row(geometry, -one, zero, 1)
    gr = [half * (one - s) * left + half * (one + s) * right for left, right in zip(gr_a, gr_c, strict=True)]
    gs = [half * (one + r) * left + half * (one - r) * right for left, right in zip(gs_b, gs_d, strict=True)]
    xr, xs, yr, ys, determinant = oracle._jacobian(geometry, r, s)
    gx = [(ys * gr[index] - yr * gs[index]) / determinant for index in range(20)]
    gy = [(-xs * gr[index] + xr * gs[index]) / determinant for index in range(20)]
    return gx, gy


def _corrected_compatible_b(geometry: Any, r: Any, s: Any) -> oracle.Matrix:
    compatible = oracle._compatible_b(geometry, r, s)
    gx, gy = _mitc_shear_rows(geometry, r, s)
    compatible[6] = gx
    compatible[7] = gy
    return compatible


def _corrected_blocks(geometry: oracle.Geometry, material: dict[str, Any]) -> dict[str, Any] | oracle.MechanicsFailure:
    blocks = _REJECTED_BLOCKS(geometry, material)
    if isinstance(blocks, oracle.MechanicsFailure):
        return blocks
    field = geometry.field
    gq = oracle.zeros(field, 14, 20)
    for (r, s), nsigma in zip(blocks["gauss"], blocks["n_sigma"], strict=True):
        determinant = oracle._jacobian(geometry, r, s)[4]
        compatible = _corrected_compatible_b(geometry, r, s)
        gq = oracle.matrix_add(
            gq,
            oracle.scalar_matrix(
                determinant,
                oracle.matmul(oracle.transpose(nsigma), compatible),
            ),
        )
    q20 = oracle.zeros(field, 20, 35)
    gq_transpose = oracle.transpose(gq)
    for physical in range(20):
        for stress in range(14):
            q20[physical][stress] = gq_transpose[physical][stress]
    q_core = oracle._embed_20x35(field, q20)
    q38 = [row[:] for row in blocks["q38"]]
    for physical in range(24):
        for internal in range(35):
            q38[physical][internal] = q_core[physical][internal]
    corrected = dict(blocks)
    corrected["q38"] = q38
    return corrected


def verify_proof(**kwargs: Any) -> dict[str, Any]:
    old_contract_schema = previous.SUCCESSOR_SCHEMA
    old_check_schema = previous.CHECK_SCHEMA
    old_blocks = previous.prior._blocks
    previous.SUCCESSOR_SCHEMA = CONTRACT_SCHEMA
    previous.CHECK_SCHEMA = CHECK_SCHEMA
    previous.prior._blocks = _corrected_blocks
    try:
        value = previous.verify_proof(**kwargs)
    finally:
        previous.SUCCESSOR_SCHEMA = old_contract_schema
        previous.CHECK_SCHEMA = old_check_schema
        previous.prior._blocks = old_blocks
    value["mitc_tying_policy"] = TYING_POLICY
    return value


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-algebra-proof", action="store_true")
    parser.add_argument("--repository-root", type=Path, required=True)
    parser.add_argument("--q1y-contract", type=Path, required=True)
    parser.add_argument("--q1y-contract-sha256", required=True)
    parser.add_argument("--successor-contract", type=Path, required=True)
    parser.add_argument("--successor-contract-sha256", required=True)
    parser.add_argument("--proof", type=Path, required=True)
    parser.add_argument("--environment-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if not args.verify_algebra_proof:
        return 2
    try:
        value = verify_proof(
            repository_root=args.repository_root,
            q1y_contract_path=args.q1y_contract,
            q1y_contract_sha256=args.q1y_contract_sha256,
            successor_contract_path=args.successor_contract,
            successor_contract_sha256=args.successor_contract_sha256,
            proof_path=args.proof,
            environment_root=args.environment_root,
        )
        q1y.write_exclusive(args.output, q1y.canonical_bytes(value))
        return 0
    except (OSError, TypeError, ValueError, q1y.Q1YError, oracle.OracleError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
