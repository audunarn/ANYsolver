#!/usr/bin/env python3
"""Emit one exact Q1Y base-geometry local-algebra proof."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time
from typing import Any, Mapping, Sequence

import e4_pl_q1v_reference as ref
from e4_pl_q1y_common import (
    GEOMETRY_IDS, OPERATION_IDS, PROOF_SCHEMA, PROOF_WRAPPER_SCHEMA, Q1YError,
    canonical_bytes, sha256, validate_contract, write_exclusive,
)


RIGID_IDS = (
    "RIGID_TRANSLATION_T1", "RIGID_TRANSLATION_T2", "RIGID_TRANSLATION_T3",
    "RIGID_ROTATION_T1", "RIGID_ROTATION_T2", "RIGID_ROTATION_T3_MATCHED_DRILL",
)
MODE_IDS = ("COMMON_DRILL", "TRANSLATION_ONLY_SPIN", "ALTERNATING_DRILL")

# Universal signed-permutation representations of the frozen Q1X D4 source
# spaces.  Nonnegative entries encode a +1 column; negative entries encode
# ``-column-1`` with coefficient -1.  The independent checker does not trust
# this table: it reconstructs every numbered operator and verifies congruence.
INTERNAL_MAPS = {
    "E": (0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37),
    "R90": (1,0,-3,4,3,-6,-8,6,9,-9,11,-11,-14,-13,15,14,-17,18,17,-20,-22,20,23,-23,25,-25,-28,-27,-30,28,31,-31,-34,-33,34,35,-38,36),
    "R180": (0,1,2,3,4,5,-7,-8,-9,-10,-11,-12,12,13,14,15,16,17,18,19,-21,-22,-23,-24,-25,-26,26,27,-29,-30,-31,-32,32,33,34,35,-37,-38),
    "R270": (1,0,-3,4,3,-6,7,-7,-10,8,-12,10,-14,-13,15,14,-17,18,17,-20,21,-21,-24,22,-26,24,-28,-27,29,-29,-32,30,-34,-33,34,35,37,-37),
    "MR": (0,1,-3,-4,-5,5,-7,7,-9,9,10,-12,12,13,14,15,-17,-18,-19,19,-21,21,-23,23,24,-26,26,27,28,-30,-31,31,-33,-34,34,-36,-37,37),
    "MS": (0,1,-3,-4,-5,5,6,-8,8,-10,-11,11,12,13,14,15,-17,-18,-19,19,20,-22,22,-24,-25,25,26,27,-29,29,30,-32,-33,-34,34,-36,36,-38),
    "MD": (1,0,2,-5,-4,-6,-8,-7,9,8,-12,-11,-14,-13,15,14,16,-19,-18,-20,-22,-21,23,22,-26,-25,-28,-27,29,28,31,30,33,32,34,-36,-38,-37),
    "MA": (1,0,2,-5,-4,-6,7,6,-10,-9,11,10,-14,-13,15,14,16,-19,-18,-20,21,20,-24,-23,25,24,-28,-27,-30,-29,-32,-31,33,32,34,-36,37,36),
}


def _progress(geometry_id: str, phase: str, started: float) -> None:
    sys.stderr.buffer.write(canonical_bytes({"elapsed_ms": int((time.perf_counter() - started) * 1000), "geometry_id": geometry_id, "phase": phase}))
    sys.stderr.buffer.flush()


def _tokens(matrix: ref.Matrix) -> list[list[list[str]]]:
    return [[value.token() for value in row] for row in matrix]


def _field_record(field: ref.Field) -> dict[str, Any]:
    """Serialize the producer's *actual* compact tower, not five formal roots.

    Rational or already-present scheduled roots do not extend the reference
    tower.  Binding its recursive radicands lets an independent checker decode
    coefficient witnesses without assuming the formal degree is 32.
    """
    return {
        "dimension": field.dimension,
        "radicands": [[str(value) for value in row] for row in field.radicands],
    }


def _h38(assembly: ref.Assembly) -> tuple[ref.Matrix, ref.Matrix, ref.Matrix]:
    h = ref.zeros(assembly.field, 38, 38)
    inverse = ref.zeros(assembly.field, 38, 38)
    coupling = ref.zeros(assembly.field, 38, 24)
    ref._add_block(h, assembly.h_core, 0, 0)
    ref._add_block(h, assembly.h_pl, 35, 35)
    ref._add_block(inverse, assembly.inv_core, 0, 0)
    ref._add_block(inverse, assembly.inv_pl, 35, 35)
    ref._add_block(coupling, assembly.c_core, 0, 0)
    ref._add_block(coupling, assembly.c_pl, 35, 0)
    return h, inverse, coupling


def _ldl(matrix: ref.Matrix) -> tuple[ref.Matrix, list[ref.Alg]]:
    field = matrix[0][0].field
    size = len(matrix)
    lower = ref.eye(field, size)
    pivots: list[ref.Alg] = []
    for row in range(size):
        pivot = matrix[row][row] - sum((lower[row][k] * lower[row][k] * pivots[k] for k in range(row)), field.rational())
        if pivot.is_zero:
            raise Q1YError("exact zero LDL pivot")
        pivots.append(pivot)
        for target in range(row + 1, size):
            residual = matrix[target][row] - sum((lower[target][k] * lower[row][k] * pivots[k] for k in range(row)), field.rational())
            lower[target][row] = residual / pivot
    return lower, pivots


def _operator_maps(base: ref.Assembly, operation: ref.Operation) -> tuple[ref.Matrix, ref.Matrix]:
    field = base.field
    encoded = INTERNAL_MAPS[operation.id]
    internal = ref.zeros(field, 38, 38)
    for row, value in enumerate(encoded):
        column = value if value >= 0 else -value - 1
        internal[row][column] = field.rational(1 if value >= 0 else -1)
    # Frame_g = Frame_E * Ahat.  Therefore local components transform by
    # Ahat^T after the frozen node permutation, for translations and rotations.
    a, b = operation.A[0]
    c, d = operation.A[1]
    ahat_t = ((a, c, 0), (b, d, 0), (0, 0, operation.det))
    qmap = ref.zeros(field, 24, 24)
    for new_node, base_node in enumerate(operation.permutation):
        for block in range(2):
            for i in range(3):
                for j in range(3):
                    qmap[6 * new_node + 3 * block + i][6 * base_node + 3 * block + j] = field.rational(ahat_t[i][j])
    return internal, qmap


def emit_proof(*, repository_root: Path, contract_path: Path, contract_sha256: str, geometry_id: str) -> dict[str, Any]:
    contract = validate_contract(repository_root, contract_path, contract_sha256)
    if geometry_id not in GEOMETRY_IDS:
        raise Q1YError("unregistered geometry")
    geometry_contract = json.loads((repository_root / "docs/reference_cases/e4_pl_q1r_geometry_contract.json").read_bytes())
    frame_contract = json.loads((repository_root / "docs/reference_cases/e4_pl_q1r_frame_contract.json").read_bytes())
    geometries = ref._geometries(geometry_contract)
    operations = ref._operations(frame_contract)
    geometry = next(row for row in geometries if row.id == geometry_id)
    e_operation = next(row for row in operations if row.id == "E")
    started = time.perf_counter()
    _progress(geometry_id, "BASE_ASSEMBLY_STARTED", started)
    assembly = ref.assemble(geometry, e_operation)
    _progress(geometry_id, "BASE_ASSEMBLY_COMPLETED", started)
    h38, inv38, c38 = _h38(assembly)
    fields = {name: ref._field_q(assembly, name) for name in RIGID_IDS + MODE_IDS}
    rigid = [[fields[name][row] for name in RIGID_IDS] for row in range(24)]
    complement = ref.lexicographic_nullspace(ref.transpose(rigid))
    quotient = ref.matmul(ref.matmul(ref.transpose(complement), assembly.k_total), complement)
    lower, pivots = _ldl(quotient)
    common_energy = ref.dot(fields["COMMON_DRILL"], ref.matvec(assembly.k_total, fields["COMMON_DRILL"]))
    spin_energy = ref.dot(fields["TRANSLATION_ONLY_SPIN"], ref.matvec(assembly.k_total, fields["TRANSLATION_ONLY_SPIN"]))
    alternating_energy = ref.dot(fields["ALTERNATING_DRILL"], ref.matvec(assembly.k_hg, fields["ALTERNATING_DRILL"]))
    _progress(geometry_id, "BASE_WITNESSES_COMPLETED", started)
    maps = []
    for operation in operations:
        internal, qmap = _operator_maps(assembly, operation)
        maps.append({"internal_g_to_base": _tokens(internal), "operation_id": operation.id, "q_base_to_numbered": _tokens(qmap)})
        _progress(geometry_id, f"OPERATOR_MAP_{operation.id}_COMPLETED", started)
    proof = {
        "base": {
            "h38_sha256": ref.matrix_digest(h38),
            "k_total": _tokens(assembly.k_total),
        },
        "case_ids": [f"{geometry_id}::{operation_id}" for operation_id in OPERATION_IDS],
        "field": _field_record(assembly.field),
        "geometry_id": geometry_id,
        "operator_maps": maps,
        "schema": PROOF_SCHEMA,
        "witnesses": {
            "complement": _tokens(complement),
            "h38_inverse": _tokens(inv38),
            "ldl_lower": _tokens(lower),
            "ldl_pivots": [value.token() for value in pivots],
            "mode_energies": {
                "alternating_hourglass": alternating_energy.token(),
                "common_drill": common_energy.token(),
                "translation_only_spin": spin_energy.token(),
            },
            "rigid": _tokens(rigid),
        },
    }
    wrapper = {
        "candidate_id": contract["candidate_id"],
        "contract_sha256": contract_sha256.upper(),
        "geometry_id": geometry_id,
        "proof": proof,
        "proof_sha256": sha256(canonical_bytes(proof)),
        "schema": PROOF_WRAPPER_SCHEMA,
        "study_id": contract["study_id"],
    }
    _progress(geometry_id, "PROOF_COMPLETED", started)
    return wrapper


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--emit-algebra-proof", action="store_true", required=True)
    parser.add_argument("--repository-root", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--contract-sha256", required=True)
    parser.add_argument("--geometry-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        value = emit_proof(repository_root=args.repository_root.resolve(strict=True), contract_path=args.contract, contract_sha256=args.contract_sha256, geometry_id=args.geometry_id)
        write_exclusive(args.output, canonical_bytes(value))
        return 0
    except (Q1YError, KeyError, TypeError, ValueError, ZeroDivisionError, OSError) as exc:
        print(f"BLOCKED_E4_PL_Q1Y_PROOF_OR_REVIEW: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
