#!/usr/bin/env python3
"""Emit one bounded Q1Z support/KKT proof from an accepted Q1Y3 stiffness proof."""

from __future__ import annotations

import argparse
import json
from fractions import Fraction
from pathlib import Path
import sys
import time
from typing import Any, Sequence

import e4_pl_q1v_reference as ref
from e4_pl_q1z_common import (
    GEOMETRY_IDS,
    OPERATION_IDS,
    PROOF_SCHEMA,
    PROOF_WRAPPER_SCHEMA,
    Q1ZError,
    canonical_bytes,
    proof_authority,
    read_json,
    sha256,
    validate_contract,
    write_exclusive,
)


Q1Y_PROOF_WRAPPER_SCHEMA = "anysolver.s4.e4-pl-q1y-algebra-proof-wrapper-v1"


def _progress(geometry_id: str, phase: str, started: float) -> None:
    sys.stderr.buffer.write(
        canonical_bytes(
            {
                "elapsed_ms": int((time.perf_counter() - started) * 1000),
                "geometry_id": geometry_id,
                "phase": phase,
            }
        )
    )
    sys.stderr.buffer.flush()


def _tokens_matrix(values: ref.Matrix) -> list[list[list[str]]]:
    return [[value.token() for value in row] for row in values]


def _tokens_vector(values: ref.Vector) -> list[list[str]]:
    return [value.token() for value in values]


def _field_from_record(record: dict[str, Any]) -> ref.Field:
    if set(record) != {"dimension", "radicands"}:
        raise Q1ZError("Q1Y3 field record mismatch")
    field = ref.Field(tuple(tuple(ref.F(value) for value in row) for row in record["radicands"]))
    if field.dimension != record["dimension"]:
        raise Q1ZError("Q1Y3 field dimension mismatch")
    return field


def _matrix(field: ref.Field, values: Any, rows: int, columns: int) -> ref.Matrix:
    if not isinstance(values, list) or len(values) != rows:
        raise Q1ZError("matrix row count mismatch")
    result: ref.Matrix = []
    for row in values:
        if not isinstance(row, list) or len(row) != columns:
            raise Q1ZError("matrix column count mismatch")
        result.append([ref.Alg(field, tuple(ref.F(item) for item in token)) for token in row])
    return result


def _load_q1y3_proof(
    contract: dict[str, Any], evidence_root: Path, geometry_id: str
) -> tuple[dict[str, Any], str]:
    authority = proof_authority(contract, geometry_id)
    path = evidence_root / authority["name"]
    if path.is_symlink() or not path.is_file():
        raise Q1ZError("Q1Y3 proof is absent or not a regular file")
    raw, wrapper = read_json(path)
    if len(raw) != authority["bytes"] or sha256(raw) != authority["sha256"]:
        raise Q1ZError("Q1Y3 proof authority mismatch")
    if not isinstance(wrapper, dict) or set(wrapper) != {
        "candidate_id",
        "contract_sha256",
        "geometry_id",
        "proof",
        "proof_sha256",
        "schema",
        "study_id",
    }:
        raise Q1ZError("Q1Y3 wrapper exact-key mismatch")
    if wrapper["schema"] != Q1Y_PROOF_WRAPPER_SCHEMA or wrapper["geometry_id"] != geometry_id:
        raise Q1ZError("Q1Y3 wrapper identity mismatch")
    if sha256(canonical_bytes(wrapper["proof"])) != wrapper["proof_sha256"]:
        raise Q1ZError("Q1Y3 payload hash mismatch")
    return wrapper["proof"], sha256(raw)


def _contracts(repository_root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    geometry = json.loads(
        (repository_root / "docs/reference_cases/e4_pl_q1r_geometry_contract.json").read_bytes()
    )
    frame = json.loads(
        (repository_root / "docs/reference_cases/e4_pl_q1r_frame_contract.json").read_bytes()
    )
    return geometry, frame


def _local_drill_block(local: ref.Matrix) -> ref.Matrix:
    """Extract QD_local^T K_local QD_local without dense global products."""

    indices = (5, 11, 17, 23)
    return [[local[i][j] for j in indices] for i in indices]


def _sparse_matmul(left: ref.Matrix, right: ref.Matrix) -> ref.Matrix:
    if not left or not right or len(left[0]) != len(right):
        raise Q1ZError("sparse matrix shape mismatch")
    field = left[0][0].field
    result = ref.zeros(field, len(left), len(right[0]))
    for i, row in enumerate(left):
        for k, value in enumerate(row):
            if value.is_zero:
                continue
            for j, other in enumerate(right[k]):
                if not other.is_zero:
                    result[i][j] = result[i][j] + value * other
    return result


def _embeddings(field: ref.Field, frame: ref.Matrix) -> tuple[ref.Matrix, ref.Matrix]:
    t5 = ref.zeros(field, 24, 20)
    qd = ref.zeros(field, 24, 4)
    for node in range(4):
        for i in range(3):
            for j in range(3):
                t5[6 * node + i][5 * node + j] = frame[i][j]
            for j in range(2):
                t5[6 * node + 3 + i][5 * node + 3 + j] = frame[i][j]
            qd[6 * node + 3 + i][node] = frame[i][2]
    return t5, qd


def _derived_frame(field: ref.Field, base: ref.Matrix, operation: ref.Operation) -> ref.Matrix:
    ahat = [
        [field.rational(operation.A[0][0]), field.rational(operation.A[0][1]), field.rational()],
        [field.rational(operation.A[1][0]), field.rational(operation.A[1][1]), field.rational()],
        [field.rational(), field.rational(), field.rational(operation.det)],
    ]
    return _sparse_matmul(base, ahat)


def _zero(field: ref.Field, count: int) -> ref.Vector:
    return [field.rational() for _ in range(count)]


def _same_matrix(left: ref.Matrix, right: ref.Matrix) -> bool:
    return left == right


def _case_record(
    *,
    field: ref.Field,
    operation: ref.Operation,
    geometry: ref.Geometry,
    frame_base: ref.Matrix,
    drill_base: ref.Matrix,
    drill_inverse_base: ref.Matrix,
    t5_base: ref.Matrix,
    qd_base: ref.Matrix,
    load_base: ref.Vector,
    support_base: ref.Matrix,
    reaction_base: ref.Vector,
    multiplier: ref.Vector,
    virtual_base: ref.Vector,
) -> dict[str, Any]:
    frame = _derived_frame(field, frame_base, operation)
    t5, qd = _embeddings(field, frame)
    permutation = ref._permutation24(field, operation)
    load = ref.matvec(permutation, load_base)
    support = _sparse_matmul(support_base, ref.transpose(permutation))
    reaction = ref.matvec(ref.transpose(support), multiplier)
    virtual = ref.matvec(permutation, virtual_base)
    local5 = ref._numbered_local5_map(field, operation)
    rebuilt_load = ref.matvec(t5, ref.matvec(local5, multiplier))
    a5 = _sparse_matmul(support, t5)
    drill_map = ref._numbered_drill_map(field, operation)
    drill = ref.matmul(ref.matmul(drill_map, drill_base), ref.transpose(drill_map))
    drill_inverse = ref.matmul(
        ref.matmul(drill_map, drill_inverse_base), ref.transpose(drill_map)
    )
    drill_unique = (
        ref.matmul(drill, drill_inverse) == ref.eye(field, 4)
        and ref.matmul(drill_inverse, drill) == ref.eye(field, 4)
    )
    equilibrium = [a - b for a, b in zip(reaction, load, strict=True)]
    zero24 = _zero(field, 24)
    constraint = ref.matvec(support, zero24)
    t5_transport = _sparse_matmul(t5, local5) == _sparse_matmul(permutation, t5_base)
    qd_transport = _sparse_matmul(qd, drill_map) == _sparse_matmul(permutation, qd_base)
    frame_orthonormal = _sparse_matmul(ref.transpose(frame), frame) == ref.eye(field, 3)
    projectors_exact = t5_transport and qd_transport and frame_orthonormal
    support_admissible = ref.matrix_is_zero(_sparse_matmul(support, qd))
    support_factorization = (
        support == _sparse_matmul(a5, ref.transpose(t5))
        and _sparse_matmul(a5, ref.transpose(a5)) == ref.eye(field, 20)
    )
    load_exact = load == rebuilt_load and ref.vector_is_zero(ref.matvec(ref.transpose(qd), load))
    reaction_drill_free = ref.vector_is_zero(ref.matvec(ref.transpose(qd), reaction))
    reaction_exact = reaction == ref.matvec(permutation, reaction_base)
    virtual_work = ref.dot(reaction, virtual) == ref.dot(multiplier, ref.matvec(support, virtual))
    numerical_separate = (
        support_admissible and reaction_drill_free
    )
    covariance = (
        load == ref.matvec(permutation, load_base)
        and support == _sparse_matmul(support_base, ref.transpose(permutation))
        and reaction == ref.matvec(permutation, reaction_base)
    )
    return {
        "case_id": f"{geometry.id}::{operation.id}",
        "covariance_exact": covariance,
        "kkt_constraint_exact": ref.vector_is_zero(constraint),
        "kkt_equilibrium_exact": ref.vector_is_zero(equilibrium),
        "kkt_unique": drill_unique and projectors_exact,
        "load_exact": load_exact,
        "numerical_reaction_separate": numerical_separate,
        "operation_id": operation.id,
        "projectors_exact": projectors_exact,
        "reaction_drill_free": reaction_drill_free,
        "reaction_exact": reaction_exact,
        "support_admissible": support_admissible,
        "support_factorization_exact": support_factorization,
        "virtual_work_exact": virtual_work,
    }


def _proper_global(
    *,
    repository_root: Path,
    contract: dict[str, Any],
    evidence_root: Path,
    geometry_contract: dict[str, Any],
    frame_contract: dict[str, Any],
    field: ref.Field,
    star_k_local: ref.Matrix,
) -> dict[str, bool]:
    base_proof, _ = _load_q1y3_proof(contract, evidence_root, "Q3_TAPERED_SKEW")
    base_field = _field_from_record(base_proof["field"])
    if base_field != field:
        raise Q1ZError("Q3 proper-global fields differ")
    base_k_local = _matrix(field, base_proof["base"]["k_total"], 24, 24)
    geometries = ref._geometries(geometry_contract)
    operations = ref._operations(frame_contract)
    base_geometry = next(row for row in geometries if row.id == "Q3_TAPERED_SKEW")
    star_geometry = next(row for row in geometries if row.id == "Q3_TAPERED_SKEW_RSTAR_TRANSLATED")
    identity = next(row for row in operations if row.id == "E")
    _, _, base_frame, _ = ref._equation7_frame(base_geometry, identity)
    _, _, star_frame, _ = ref._equation7_frame(star_geometry, identity)
    base_t5, base_qd = _embeddings(field, base_frame)
    star_t5, star_qd = _embeddings(field, star_frame)
    base_p5 = _sparse_matmul(base_t5, ref.transpose(base_t5))
    base_pd = _sparse_matmul(base_qd, ref.transpose(base_qd))
    star_p5 = _sparse_matmul(star_t5, ref.transpose(star_t5))
    star_pd = _sparse_matmul(star_qd, ref.transpose(star_qd))
    transform = geometry_contract["global_transform"]
    rotation = [[field.rational(value) for value in row] for row in transform["R_star"]]
    global_map = ref.zeros(field, 24, 24)
    for node in range(4):
        for block in range(2):
            for i in range(3):
                for j in range(3):
                    global_map[6 * node + 3 * block + i][6 * node + 3 * block + j] = rotation[i][j]
    p_f = ref._frozen_physical_load(field)
    base_load = ref.matvec(base_t5, p_f)
    star_load = ref.matvec(star_t5, p_f)
    base_support = ref.transpose(base_t5)
    star_support = ref.transpose(star_t5)
    base_reaction = ref.matvec(ref.transpose(base_support), p_f)
    star_reaction = ref.matvec(ref.transpose(star_support), p_f)
    base_drill = _local_drill_block(base_k_local)
    star_drill = _local_drill_block(star_k_local)
    numbering_commutes = True
    for operation in operations:
        permutation = ref._permutation24(field, operation)
        numbering_commutes = numbering_commutes and (
            _sparse_matmul(permutation, global_map) == _sparse_matmul(global_map, permutation)
        )
    return {
        "applicable": True,
        "drill_block": base_drill == star_drill,
        "frame": star_t5 == ref.matmul(global_map, base_t5) and star_qd == ref.matmul(global_map, base_qd),
        "load": star_load == ref.matvec(global_map, base_load),
        "numbering_commutes": numbering_commutes,
        "projectors": (
            star_p5
            == _sparse_matmul(_sparse_matmul(global_map, base_p5), ref.transpose(global_map))
            and star_pd
            == _sparse_matmul(_sparse_matmul(global_map, base_pd), ref.transpose(global_map))
        ),
        "reaction": star_reaction == ref.matvec(global_map, base_reaction),
        "stiffness": base_k_local == star_k_local,
        "support": star_support == _sparse_matmul(base_support, ref.transpose(global_map)),
    }


def emit_support_proof(
    *,
    repository_root: Path,
    contract_path: Path,
    contract_sha256: str,
    q1y3_evidence_root: Path,
    geometry_id: str,
) -> dict[str, Any]:
    started = time.perf_counter()
    contract = validate_contract(repository_root, contract_path, contract_sha256)
    if geometry_id not in GEOMETRY_IDS:
        raise Q1ZError("unregistered geometry")
    evidence_root = q1y3_evidence_root.resolve(strict=True)
    _progress(geometry_id, "AUTHORITY_VALIDATED", started)
    q1y3_proof, q1y3_raw_sha = _load_q1y3_proof(contract, evidence_root, geometry_id)
    field = _field_from_record(q1y3_proof["field"])
    k_local = _matrix(field, q1y3_proof["base"]["k_total"], 24, 24)
    geometry_contract, frame_contract = _contracts(repository_root)
    geometries = ref._geometries(geometry_contract)
    operations = ref._operations(frame_contract)
    geometry = next(row for row in geometries if row.id == geometry_id)
    identity = next(row for row in operations if row.id == "E")
    frame_field, _, frame, _ = ref._equation7_frame(geometry, identity)
    if frame_field != field:
        raise Q1ZError("Q1Y3 stiffness and equation-7 fields differ")
    t5, qd = _embeddings(field, frame)
    p5 = _sparse_matmul(t5, ref.transpose(t5))
    pd = _sparse_matmul(qd, ref.transpose(qd))
    p_f = ref._frozen_physical_load(field)
    load = ref.matvec(t5, p_f)
    support = ref.transpose(t5)
    reaction = ref.matvec(ref.transpose(support), p_f)
    drill = _local_drill_block(k_local)
    drill_inverse = ref.matrix_inverse(drill)
    if (
        ref.matmul(drill, drill_inverse) != ref.eye(field, 4)
        or ref.matmul(drill_inverse, drill) != ref.eye(field, 4)
    ):
        raise Q1ZError("drill inverse witness failed")
    virtual = [field.rational(Fraction((index % 9) - 4, (index % 4) + 1)) for index in range(24)]
    _progress(geometry_id, "BASE_SUPPORT_COMPLETED", started)
    cases = []
    for operation in operations:
        cases.append(
            _case_record(
                field=field,
                operation=operation,
                geometry=geometry,
                frame_base=frame,
                drill_base=drill,
                drill_inverse_base=drill_inverse,
                t5_base=t5,
                qd_base=qd,
                load_base=load,
                support_base=support,
                reaction_base=reaction,
                multiplier=p_f,
                virtual_base=virtual,
            )
        )
        _progress(geometry_id, f"CASE_{operation.id}_COMPLETED", started)
    proper_global = {
        "applicable": False,
        "drill_block": True,
        "frame": True,
        "load": True,
        "numbering_commutes": True,
        "projectors": True,
        "reaction": True,
        "stiffness": True,
        "support": True,
    }
    if geometry_id == "Q3_TAPERED_SKEW_RSTAR_TRANSLATED":
        proper_global = _proper_global(
            repository_root=repository_root,
            contract=contract,
            evidence_root=evidence_root,
            geometry_contract=geometry_contract,
            frame_contract=frame_contract,
            field=field,
            star_k_local=k_local,
        )
    proof = {
        "base": {
            "drill_block": _tokens_matrix(drill),
            "drill_inverse": _tokens_matrix(drill_inverse),
            "drill_projector": _tokens_matrix(pd),
            "frame": _tokens_matrix(frame),
            "load": _tokens_vector(load),
            "multiplier": _tokens_vector(p_f),
            "physical_projector": _tokens_matrix(p5),
            "qd": _tokens_matrix(qd),
            "reaction": _tokens_vector(reaction),
            "support": _tokens_matrix(support),
            "t5": _tokens_matrix(t5),
            "virtual": _tokens_vector(virtual),
        },
        "case_records": cases,
        "field": q1y3_proof["field"],
        "geometry_id": geometry_id,
        "proper_global": proper_global,
        "q1y3_proof_sha256": q1y3_raw_sha,
        "schema": PROOF_SCHEMA,
    }
    wrapper = {
        "candidate_id": contract["candidate_id"],
        "contract_sha256": contract_sha256.upper(),
        "geometry_id": geometry_id,
        "proof": proof,
        "proof_sha256": sha256(canonical_bytes(proof)),
        "q1y3_proof_sha256": q1y3_raw_sha,
        "schema": PROOF_WRAPPER_SCHEMA,
        "study_id": contract["study_id"],
    }
    _progress(geometry_id, "PROOF_COMPLETED", started)
    return wrapper


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--emit-support-proof", action="store_true", required=True)
    parser.add_argument("--repository-root", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--contract-sha256", required=True)
    parser.add_argument("--q1y3-evidence-root", type=Path, required=True)
    parser.add_argument("--geometry-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        value = emit_support_proof(
            repository_root=args.repository_root.resolve(strict=True),
            contract_path=args.contract,
            contract_sha256=args.contract_sha256,
            q1y3_evidence_root=args.q1y3_evidence_root,
            geometry_id=args.geometry_id,
        )
        write_exclusive(args.output, canonical_bytes(value))
        return 0
    except (KeyError, OSError, TypeError, ValueError, ZeroDivisionError, Q1ZError) as exc:
        print(f"BLOCKED_E4_PL_Q1Z_PROOF_OR_REVIEW: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
