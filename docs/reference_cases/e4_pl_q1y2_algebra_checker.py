"""Independent base-only checker for the pipelined Q1Y2 algebra proof."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

import e4_pl_q1y_algebra_checker as prior
import e4_pl_q1y_common as q1y
import e4_pl_q1v_oracle as oracle


CHECK_SCHEMA = "anysolver.s4.e4-pl-q1y2-algebra-check-v1"
SUCCESSOR_SCHEMA = "anysolver.s4.e4-pl-q1y2-local-algebra-contract-v1"


def _successor_contract(path: Path, expected_sha256: str) -> dict[str, Any]:
    raw, value = q1y.read_json(path)
    if q1y.sha256(raw) != expected_sha256.upper():
        raise q1y.Q1YError("successor contract caller hash mismatch")
    if not isinstance(value, dict) or value.get("schema") != SUCCESSOR_SCHEMA:
        raise q1y.Q1YError("successor contract schema mismatch")
    return value


def _proof(path: Path, contract_sha256: str, contract: dict[str, Any]) -> dict[str, Any]:
    _, wrapper = q1y.read_json(path)
    if set(wrapper) != {
        "candidate_id", "contract_sha256", "geometry_id", "proof",
        "proof_sha256", "schema", "study_id",
    } or wrapper["schema"] != q1y.PROOF_WRAPPER_SCHEMA:
        raise q1y.Q1YError("proof wrapper schema mismatch")
    proof = wrapper["proof"]
    if q1y.sha256(q1y.canonical_bytes(proof)) != wrapper["proof_sha256"]:
        raise q1y.Q1YError("proof payload hash mismatch")
    if proof.get("schema") != q1y.PROOF_SCHEMA:
        raise q1y.Q1YError("proof schema mismatch")
    if wrapper["candidate_id"] != contract["candidate_id"] or wrapper["study_id"] != contract["study_id"]:
        raise q1y.Q1YError("proof Q1Y authority mismatch")
    if wrapper["contract_sha256"] != contract_sha256.upper():
        raise q1y.Q1YError("proof Q1Y contract mismatch")
    return wrapper


def _base_certificate(
    geometry: oracle.Geometry,
    material: dict[str, Any],
    proof: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    basis = prior._basis(geometry, proof["field"])
    scalar, _, matrix = prior._decoder(basis)
    witnesses = proof["witnesses"]
    inverse = matrix(witnesses["h38_inverse"])
    rigid = matrix(witnesses["rigid"])
    complement = matrix(witnesses["complement"])
    lower = matrix(witnesses["ldl_lower"])
    pivots = [scalar(value) for value in witnesses["ldl_pivots"]]
    blocks = prior._blocks(geometry, material)
    if isinstance(blocks, oracle.MechanicsFailure):
        return {
            "checks": {},
            "exact_failure": not blocks.unresolved,
            "ordered_unresolved": blocks.unresolved,
            "proof_disagreement": False,
            "reason": blocks.reason,
        }, {}
    d38, q38, hourglass = blocks["d38"], blocks["q38"], blocks["hourglass"]
    identity38 = oracle.identity(geometry.field, 38)
    inverse_exact = (
        oracle.matrix_equal(oracle.matmul(d38, inverse), identity38)
        and oracle.matrix_equal(oracle.matmul(inverse, d38), identity38)
    )
    k24 = oracle.matrix_add(
        oracle.scalar_matrix(
            geometry.field.exact(-1),
            oracle.matmul(oracle.matmul(q38, inverse), oracle.transpose(q38)),
        ),
        hourglass,
    )
    proof_k = matrix(proof["base"]["k_total"])
    stiffness_exact = oracle.matrix_equal(k24, proof_k)
    symmetry_exact = oracle.matrix_equal(k24, oracle.transpose(k24))
    expected_rigid = oracle._rigid_matrix(geometry)
    rigid_witness_exact = oracle.matrix_equal(rigid, expected_rigid)
    rigid_mechanics_exact = (
        oracle.matrix_rank(expected_rigid) == 6
        and oracle.all_zero_matrix(oracle.matmul(k24, expected_rigid))
    )
    expected_complement = oracle.nullspace_rref(oracle.transpose(rigid))
    complement_exact = (
        oracle.shape(complement) == (24, 18)
        and oracle.matrix_equal(complement, expected_complement)
    )
    restricted = oracle.matmul(oracle.matmul(oracle.transpose(complement), k24), complement)
    diagonal = oracle.zeros(geometry.field, 18, 18)
    for index, pivot in enumerate(pivots):
        diagonal[index][index] = pivot
    ldl_exact = oracle.matrix_equal(
        restricted,
        oracle.matmul(oracle.matmul(lower, diagonal), oracle.transpose(lower)),
    )
    pivot_signs = [prior._tower_sign(value, proof["field"]) for value in witnesses["ldl_pivots"]]
    probes = oracle._base_numerical_probe_vectors(geometry)
    mode_values = [
        oracle.dot(probes["common_drill"], oracle.matvec(k24, probes["common_drill"])),
        oracle.dot(probes["translation_only_spin"], oracle.matvec(k24, probes["translation_only_spin"])),
        oracle.dot(probes["alternating_drill"], oracle.matvec(hourglass, probes["alternating_drill"])),
    ]
    mode_names = ("common_drill", "translation_only_spin", "alternating_hourglass")
    claimed_modes = [scalar(witnesses["mode_energies"][name]) for name in mode_names]
    mode_signs = [prior._tower_sign(witnesses["mode_energies"][name], proof["field"]) for name in mode_names]
    modes_witness_exact = all(left.is_equal(right) for left, right in zip(claimed_modes, mode_values, strict=True))
    matched_rigid_exact = oracle.all_zero_vector(oracle.matvec(k24, probes["matched_rigid"]))
    stationarity_exact = prior._stationarity(d38, inverse, q38, hourglass, k24)
    exact_sign_failure = any(value in {"ZERO", "NEGATIVE"} for value in pivot_signs + mode_signs)
    unresolved = any(value == "UNRESOLVED" for value in pivot_signs + mode_signs)
    proof_disagreement = not all((
        inverse_exact, stiffness_exact, rigid_witness_exact, complement_exact,
        ldl_exact, modes_witness_exact, stationarity_exact,
    ))
    mechanics_failure = (not symmetry_exact) or (not rigid_mechanics_exact) or (not matched_rigid_exact) or exact_sign_failure
    return {
        "checks": {
            "complement_exact": complement_exact,
            "inverse_exact": inverse_exact,
            "ldl_exact": ldl_exact,
            "matched_rigid_exact": matched_rigid_exact,
            "modes_witness_exact": modes_witness_exact,
            "pivots_and_modes_positive": not exact_sign_failure,
            "rigid_mechanics_exact": rigid_mechanics_exact,
            "rigid_witness_exact": rigid_witness_exact,
            "stationarity_exact": stationarity_exact,
            "stiffness_exact": stiffness_exact,
            "symmetry_exact": symmetry_exact,
        },
        "exact_failure": mechanics_failure,
        "ordered_unresolved": unresolved,
        "proof_disagreement": proof_disagreement,
        "reason": "LOCAL_ALGEBRA" if mechanics_failure else "",
    }, {
        "d38": d38,
        "hourglass": hourglass,
        "inverse": inverse,
        "k24": k24,
        "q38": q38,
        "rigid": rigid,
        "matrix": matrix,
    }


def _operator_certificate(
    geometry_id: str,
    node_text: Any,
    base_geometry: oracle.Geometry,
    operations: Sequence[oracle.Operation],
    proof: dict[str, Any],
    base: dict[str, Any],
    sympy: Any,
    cache: dict[str, tuple[oracle.FieldContext, tuple[oracle.Expr, ...]]],
) -> list[str]:
    contradictions: list[str] = []
    rows = proof["operator_maps"]
    if [row.get("operation_id") for row in rows] != list(q1y.OPERATION_IDS):
        raise q1y.Q1YError("operator-map order mismatch")
    matrix = base["matrix"]
    for operation, row in zip(operations, rows, strict=True):
        internal = matrix(row["internal_g_to_base"])
        qmap = matrix(row["q_base_to_numbered"])
        maps_exact = prior._signed_permutation(internal) and prior._signed_permutation(qmap)
        block_diagonal = all(
            internal[i][j].is_zero()
            for i in range(38)
            for j in range(38)
            if not ((i < 14 and j < 14) or (14 <= i < 35 and 14 <= j < 35) or (35 <= i and 35 <= j))
        )
        _, _, lambda_map = prior._physical_maps(base_geometry.field, operation)
        maps_exact = maps_exact and block_diagonal and oracle.matrix_equal(
            [row_values[35:38] for row_values in internal[35:38]], lambda_map
        )
        current = oracle._numbered_geometry(geometry_id, node_text, operation, sympy, cache)
        expected_qmap = oracle.matmul(
            oracle.matmul(
                oracle.transpose(oracle._block_frame(current.frame)),
                oracle._permutation(base_geometry.field, operation, 6),
            ),
            oracle._block_frame(base_geometry.frame),
        )
        maps_exact = maps_exact and oracle.matrix_equal(qmap, expected_qmap)
        transpose_internal = oracle.transpose(internal)
        transpose_qmap = oracle.transpose(qmap)
        transported_d38 = oracle.matmul(oracle.matmul(transpose_internal, base["d38"]), internal)
        transported_inverse = oracle.matmul(oracle.matmul(transpose_internal, base["inverse"]), internal)
        transported_q38 = oracle.matmul(oracle.matmul(qmap, base["q38"]), internal)
        transported_hourglass = oracle.matmul(oracle.matmul(qmap, base["hourglass"]), transpose_qmap)
        transported_k = oracle.matmul(oracle.matmul(qmap, base["k24"]), transpose_qmap)
        congruence_exact = (
            prior._stationarity(
                transported_d38,
                transported_inverse,
                transported_q38,
                transported_hourglass,
                transported_k,
            )
            and oracle.matrix_equal(transported_k, oracle.transpose(transported_k))
            and oracle.all_zero_matrix(oracle.matmul(transported_k, oracle.matmul(qmap, base["rigid"])))
        )
        base_global = oracle._global_matrix(base["k24"], base_geometry.frame)
        current_global = oracle._global_matrix(transported_k, current.frame)
        permutation = oracle._permutation(base_geometry.field, operation, 6)
        global_exact = oracle.matrix_equal(
            oracle.matmul(oracle.matmul(oracle.transpose(permutation), current_global), permutation),
            base_global,
        )
        if not (maps_exact and congruence_exact and global_exact):
            contradictions.append(f"{geometry_id}::{operation.operation_id}")
    return contradictions


def verify_proof(
    *,
    repository_root: Path,
    q1y_contract_path: Path,
    q1y_contract_sha256: str,
    successor_contract_path: Path,
    successor_contract_sha256: str,
    proof_path: Path,
    environment_root: Path,
) -> dict[str, Any]:
    successor = _successor_contract(successor_contract_path, successor_contract_sha256)
    contract = q1y.validate_contract(repository_root, q1y_contract_path, q1y_contract_sha256)
    q1y.validate_environment(repository_root, environment_root, contract)
    environment_text = str(environment_root.resolve(strict=True))
    if environment_text not in sys.path:
        sys.path.insert(0, environment_text)
    sympy = oracle._load_sympy()
    wrapper = _proof(proof_path, q1y_contract_sha256, contract)
    proof = wrapper["proof"]
    geometry_id = wrapper["geometry_id"]
    if geometry_id not in q1y.GEOMETRY_IDS or proof.get("geometry_id") != geometry_id:
        raise q1y.Q1YError("proof geometry mismatch")
    if proof.get("case_ids") != [f"{geometry_id}::{operation}" for operation in q1y.OPERATION_IDS]:
        raise q1y.Q1YError("proof case coverage mismatch")
    geometries, operations, material, _ = oracle._frozen_inputs()
    node_text = dict(geometries)[geometry_id]
    cache: dict[str, tuple[oracle.FieldContext, tuple[oracle.Expr, ...]]] = {}
    base_geometry = oracle._numbered_geometry(geometry_id, node_text, operations[0], sympy, cache)
    local, base = _base_certificate(base_geometry, material, proof)
    operator_contradictions: list[str] = []
    if base:
        operator_contradictions = _operator_certificate(
            geometry_id, node_text, base_geometry, operations, proof, base, sympy, cache
        )
    local_contradictions = [f"{geometry_id}::E::{local['reason']}"] if local["exact_failure"] else []
    if local.get("proof_disagreement", False):
        terminal = successor["terminals"]["blocked"]
    elif local_contradictions:
        terminal = successor["terminals"]["local_algebra"]
    elif operator_contradictions:
        terminal = successor["terminals"]["operator_covariance"]
    elif local["ordered_unresolved"]:
        terminal = successor["terminals"]["ordered_sign"]
    else:
        terminal = successor["terminals"]["success"]
    return {
        "base_reconstruction_count": 1,
        "case_count": 8,
        "exact_local_contradictions": local_contradictions,
        "exact_operator_contradictions": operator_contradictions,
        "geometry_id": geometry_id,
        "local_checks": local["checks"],
        "local_k_sha256": q1y.sha256(q1y.canonical_bytes(proof["base"]["k_total"])),
        "ordered_unresolved": bool(local["ordered_unresolved"]),
        "proof_disagreement": bool(local.get("proof_disagreement", False)),
        "q1x_transport_bound": True,
        "schema": CHECK_SCHEMA,
        "station_count": 32,
        "terminal": terminal,
    }


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
