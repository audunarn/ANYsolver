#!/usr/bin/env python3
"""Independently verify one Q1Y exact local-algebra proof with SymPy."""

from __future__ import annotations

import argparse
from fractions import Fraction
from math import isqrt
from pathlib import Path
import sys
from typing import Any, Sequence

import e4_pl_q1v_oracle as oracle
from e4_pl_q1y_common import (
    CHECK_SCHEMA, GEOMETRY_IDS, OPERATION_IDS, PROOF_SCHEMA, PROOF_WRAPPER_SCHEMA,
    Q1YError, canonical_bytes, read_json, sha256, validate_contract, validate_environment,
    verify_file, write_exclusive,
)


def _basis(geometry: oracle.Geometry, record: dict[str, Any]) -> list[oracle.Exact]:
    """Reconstruct the compact producer tower inside the independent field."""
    radicands = record.get("radicands")
    dimension = record.get("dimension")
    if not isinstance(radicands, list) or dimension != 1 << len(radicands):
        raise Q1YError("compact field record is malformed")
    roots: list[oracle.Exact] = []
    for index, coefficients in enumerate(radicands):
        prior: list[oracle.Exact] = []
        for mask in range(1 << index):
            value = geometry.field.exact(1)
            for root_index, root in enumerate(roots):
                if mask & (1 << root_index):
                    value *= root
            prior.append(value)
        if not isinstance(coefficients, list) or len(coefficients) != len(prior):
            raise Q1YError("compact field radicand dimension mismatch")
        radicand = sum(
            (Fraction(value) * monomial for value, monomial in zip(coefficients, prior, strict=True)),
            geometry.field.exact(0),
        )
        root = geometry.field.positive_root(radicand.expression)
        if not (root * root).is_equal(radicand) or oracle.exact_sign(root)[0] != "POSITIVE":
            raise Q1YError("compact field root reconstruction failed")
        roots.append(root)
    result: list[oracle.Exact] = []
    for mask in range(1 << len(roots)):
        value = geometry.field.exact(1)
        for index, root in enumerate(roots):
            if mask & (1 << index):
                value *= root
        result.append(value)
    if len(result) != dimension:
        raise Q1YError("compact field basis dimension mismatch")
    return result


def _decoder(basis: Sequence[oracle.Exact]):
    cache: dict[tuple[str, ...], oracle.Exact] = {}

    def scalar(token: Sequence[str]) -> oracle.Exact:
        key = tuple(str(value) for value in token)
        if key not in cache:
            if len(key) != len(basis):
                raise Q1YError("witness token dimension mismatch")
            field = basis[0].field
            cache[key] = sum((Fraction(value) * monomial for value, monomial in zip(key, basis, strict=True)), field.exact(0))
        return cache[key]

    def vector(values: Sequence[Sequence[str]]) -> oracle.Vector:
        return [scalar(value) for value in values]

    def matrix(values: Sequence[Sequence[Sequence[str]]]) -> oracle.Matrix:
        return [vector(row) for row in values]

    return scalar, vector, matrix


def _floor_fraction(value: Fraction) -> int:
    return value.numerator // value.denominator


def _ceil_fraction(value: Fraction) -> int:
    return -((-value.numerator) // value.denominator)


def _round_interval(lo: Fraction, hi: Fraction, bits: int) -> tuple[Fraction, Fraction]:
    scale = 1 << bits
    return Fraction(_floor_fraction(lo * scale), scale), Fraction(_ceil_fraction(hi * scale), scale)


def _interval_add(left: tuple[Fraction, Fraction], right: tuple[Fraction, Fraction], bits: int) -> tuple[Fraction, Fraction]:
    return _round_interval(left[0] + right[0], left[1] + right[1], bits)


def _interval_mul(left: tuple[Fraction, Fraction], right: tuple[Fraction, Fraction], bits: int) -> tuple[Fraction, Fraction]:
    values = (left[0] * right[0], left[0] * right[1], left[1] * right[0], left[1] * right[1])
    return _round_interval(min(values), max(values), bits)


def _sqrt_interval(value: tuple[Fraction, Fraction], bits: int) -> tuple[Fraction, Fraction]:
    if value[0] <= 0:
        raise Q1YError("positive-root DAG has nonpositive lower bound")
    scale2 = 1 << (2 * bits)
    lower_scaled = _floor_fraction(value[0] * scale2)
    upper_scaled = _ceil_fraction(value[1] * scale2)
    lower = isqrt(lower_scaled)
    upper_floor = isqrt(upper_scaled)
    upper = upper_floor if upper_floor * upper_floor == upper_scaled else upper_floor + 1
    return Fraction(lower, 1 << bits), Fraction(upper, 1 << bits)


def _tower_interval(token: Sequence[str], record: dict[str, Any], bits: int) -> tuple[Fraction, Fraction]:
    radicands = record["radicands"]
    roots: list[tuple[Fraction, Fraction]] = []
    for index, coefficients in enumerate(radicands):
        basis: list[tuple[Fraction, Fraction]] = []
        for mask in range(1 << index):
            value = (Fraction(1), Fraction(1))
            for root_index, root in enumerate(roots):
                if mask & (1 << root_index):
                    value = _interval_mul(value, root, bits)
            basis.append(value)
        radicand = (Fraction(0), Fraction(0))
        for coefficient, monomial in zip(coefficients, basis, strict=True):
            rational = Fraction(coefficient)
            radicand = _interval_add(radicand, _interval_mul((rational, rational), monomial, bits), bits)
        roots.append(_sqrt_interval(radicand, bits))
    basis = []
    for mask in range(1 << len(roots)):
        value = (Fraction(1), Fraction(1))
        for index, root in enumerate(roots):
            if mask & (1 << index):
                value = _interval_mul(value, root, bits)
        basis.append(value)
    if len(token) != len(basis):
        raise Q1YError("ordered-sign token dimension mismatch")
    result = (Fraction(0), Fraction(0))
    for coefficient, monomial in zip(token, basis, strict=True):
        rational = Fraction(coefficient)
        result = _interval_add(result, _interval_mul((rational, rational), monomial, bits), bits)
    return result


def _tower_sign(token: Sequence[str], record: dict[str, Any]) -> str:
    if all(Fraction(value) == 0 for value in token):
        return "ZERO"
    for bits in (256, 512, 1024):
        lo, hi = _tower_interval(token, record, bits)
        if lo > 0:
            return "POSITIVE"
        if hi < 0:
            return "NEGATIVE"
    return "UNRESOLVED"


def _blocks(geometry: oracle.Geometry, material: dict[str, Any]) -> dict[str, Any] | oracle.MechanicsFailure:
    field = geometry.field
    gauss = oracle._gauss_points(field, geometry.roots[4])
    signs = [oracle.exact_sign(geometry.coefficients["jc"])[0]] + [oracle.exact_sign(oracle._jacobian(geometry, r, s)[4])[0] for r, s in gauss]
    if any(value == "UNRESOLVED" for value in signs):
        return oracle.MechanicsFailure(geometry, "UNCLASSIFIED", "JACOBIAN_SIGN_UNRESOLVED", True)
    if any(value != "POSITIVE" for value in signs):
        return oracle.MechanicsFailure(geometry, "LOCAL", "JACOBIAN_NOT_POSITIVE", False)
    constitutive = oracle._constitutive(field, material)
    f_block = oracle.zeros(field, 21, 14)
    gq = oracle.zeros(field, 14, 20)
    h_block = oracle.zeros(field, 21, 21)
    nsigma_rows: list[oracle.Matrix] = []
    nepsilon_rows: list[oracle.Matrix] = []
    for r, s in gauss:
        _, _, _, _, jac = oracle._jacobian(geometry, r, s)
        nsigma, nepsilon = oracle._independent_interpolations(geometry, r, s)
        compatible = oracle._compatible_b(geometry, r, s)
        nsigma_rows.append(nsigma)
        nepsilon_rows.append(nepsilon)
        f_block = oracle.matrix_sub(f_block, oracle.scalar_matrix(jac, oracle.matmul(oracle.transpose(nepsilon), nsigma)))
        gq = oracle.matrix_add(gq, oracle.scalar_matrix(jac, oracle.matmul(oracle.transpose(nsigma), compatible)))
        h_block = oracle.matrix_add(h_block, oracle.scalar_matrix(jac, oracle.matmul(oracle.matmul(oracle.transpose(nepsilon), constitutive), nepsilon)))
    d35 = oracle.zeros(field, 35, 35)
    for i in range(14):
        for j in range(21):
            d35[i][14 + j] = f_block[j][i]
            d35[14 + j][i] = f_block[j][i]
    for i in range(21):
        for j in range(21):
            d35[14 + i][14 + j] = h_block[i][j]
    q20 = oracle.zeros(field, 20, 35)
    gqt = oracle.transpose(gq)
    for i in range(20):
        for j in range(14):
            q20[i][j] = gqt[i][j]
    q_core = oracle._embed_20x35(field, q20)
    c_taylor = oracle._centre_taylor(geometry)
    thickness = field.exact(oracle.expr_q(oracle._parse_q(material["exact_parameters"]["t"])))
    shear = field.exact(oracle.expr_q(oracle._parse_q(material["exact_parameters"]["G"])))
    epsilon = field.exact(oracle.expr_q(oracle._parse_q(material["exact_parameters"]["epsilon_hg"])))
    gram = oracle.zeros(field, 3, 3)
    for r, s in gauss:
        _, _, _, _, jac = oracle._jacobian(geometry, r, s)
        p = [field.exact(1), r, s]
        gram = oracle.matrix_add(gram, oracle.scalar_matrix(thickness * jac, oracle.outer(p, p)))
    b_pl = oracle.matmul(gram, c_taylor)
    d38 = oracle.zeros(field, 38, 38)
    for i in range(35):
        for j in range(35):
            d38[i][j] = d35[i][j]
    compliance = oracle.scalar_matrix(-field.exact(1) / shear, gram)
    for i in range(3):
        for j in range(3):
            d38[35 + i][35 + j] = compliance[i][j]
    q38 = oracle.zeros(field, 24, 38)
    for i in range(24):
        for j in range(35):
            q38[i][j] = q_core[i][j]
        for j in range(3):
            q38[i][35 + j] = b_pl[j][i]
    gamma = oracle._residual_gamma(geometry)
    gamma24 = [field.exact(0) for _ in range(24)]
    for node in range(4):
        gamma24[6 * node + 5] = gamma[node]
    factor = 2 * epsilon * shear * thickness * (4 * geometry.coefficients["jc"])
    hourglass = oracle.scalar_matrix(factor, oracle.outer(gamma24, gamma24))
    return {"d38": d38, "gauss": gauss, "gram": gram, "hourglass": hourglass, "n_epsilon": nepsilon_rows, "n_sigma": nsigma_rows, "q38": q38}


def _signed_permutation(matrix: oracle.Matrix) -> bool:
    field = matrix[0][0].field
    for row in matrix:
        if sum(not value.is_zero() for value in row) != 1:
            return False
        if not any(value.is_equal(1) or value.is_equal(-1) for value in row):
            return False
    for column in range(len(matrix[0])):
        if sum(not row[column].is_zero() for row in matrix) != 1:
            return False
    return oracle.matrix_equal(oracle.matmul(oracle.transpose(matrix), matrix), oracle.identity(field, len(matrix)))


def _stationarity(d38: oracle.Matrix, inverse: oracle.Matrix, q38: oracle.Matrix, hourglass: oracle.Matrix, k24: oracle.Matrix) -> bool:
    field = d38[0][0].field
    probe = [field.exact((index % 7) - 3) for index in range(24)]
    internal = [-value for value in oracle.matvec(inverse, oracle.matvec(oracle.transpose(q38), probe))]
    mixed = [a + b for a, b in zip(oracle.matvec(q38, internal), oracle.matvec(hourglass, probe), strict=True)]
    condensed = oracle.matvec(k24, probe)
    residual = oracle.all_zero_vector([a - b for a, b in zip(mixed, condensed, strict=True)])
    mixed_energy = oracle.dot(internal, oracle.matvec(d38, internal)) / 2 + oracle.dot(probe, oracle.matvec(q38, internal)) + oracle.dot(probe, oracle.matvec(hourglass, probe)) / 2
    condensed_energy = oracle.dot(probe, condensed) / 2
    virtual = [field.exact(((index * 3) % 11) - 5) for index in range(24)]
    return residual and (mixed_energy - condensed_energy).is_zero() and (oracle.dot(virtual, mixed) - oracle.dot(virtual, condensed)).is_zero()


def _physical_maps(field: oracle.FieldContext, operation: oracle.Operation) -> tuple[oracle.Matrix, oracle.Matrix, oracle.Matrix]:
    a, b = operation.natural_map[0]
    c, d = operation.natural_map[1]
    det = operation.determinant
    c_eng = [[field.exact(a*a),field.exact(b*b),field.exact(a*b)],[field.exact(c*c),field.exact(d*d),field.exact(c*d)],[field.exact(2*a*c),field.exact(2*b*d),field.exact(a*d+b*c)]]
    c_res = [[field.exact(a*a),field.exact(b*b),field.exact(2*a*b)],[field.exact(c*c),field.exact(d*d),field.exact(2*c*d)],[field.exact(a*c),field.exact(b*d),field.exact(a*d+b*c)]]
    shear = [[field.exact(det*a),field.exact(det*b)],[field.exact(det*c),field.exact(det*d)]]
    stress = oracle.zeros(field,8,8); strain = oracle.zeros(field,8,8)
    def add_block(target: oracle.Matrix, block: oracle.Matrix, row: int, column: int) -> None:
        for i, values in enumerate(block):
            for j, value in enumerate(values):
                target[row + i][column + j] = value
    add_block(stress,c_res,0,0); add_block(stress,oracle.scalar_matrix(field.exact(det),c_res),3,3); add_block(stress,shear,6,6)
    add_block(strain,c_eng,0,0); add_block(strain,oracle.scalar_matrix(field.exact(det),c_eng),3,3); add_block(strain,shear,6,6)
    lambda_map = [[field.exact(det),field.exact(0),field.exact(0)],[field.exact(0),field.exact(det*a),field.exact(det*b)],[field.exact(0),field.exact(det*c),field.exact(det*d)]]
    return stress, strain, lambda_map


def verify_proof(*, repository_root: Path, contract_path: Path, contract_sha256: str, proof_path: Path, environment_root: Path) -> dict[str, Any]:
    contract = validate_contract(repository_root, contract_path, contract_sha256)
    validate_environment(repository_root, environment_root, contract)
    env = str(environment_root.resolve(strict=True))
    if env not in sys.path:
        sys.path.insert(0, env)
    sympy = oracle._load_sympy()
    raw, wrapper = read_json(proof_path)
    if set(wrapper) != {"candidate_id","contract_sha256","geometry_id","proof","proof_sha256","schema","study_id"} or wrapper["schema"] != PROOF_WRAPPER_SCHEMA:
        raise Q1YError("proof wrapper schema mismatch")
    proof = wrapper["proof"]
    if sha256(canonical_bytes(proof)) != wrapper["proof_sha256"] or proof.get("schema") != PROOF_SCHEMA:
        raise Q1YError("proof payload hash/schema mismatch")
    if wrapper["candidate_id"] != contract["candidate_id"] or wrapper["study_id"] != contract["study_id"] or wrapper["contract_sha256"] != contract_sha256.upper():
        raise Q1YError("proof authority binding mismatch")
    if set(proof) != {"base","case_ids","field","geometry_id","operator_maps","schema","witnesses"}:
        raise Q1YError("proof exact-key mismatch")
    if set(proof["base"]) != {"h38_sha256","k_total"} or set(proof["field"]) != {"dimension","radicands"}:
        raise Q1YError("proof base/field schema mismatch")
    if set(proof["witnesses"]) != {"complement","h38_inverse","ldl_lower","ldl_pivots","mode_energies","rigid"}:
        raise Q1YError("proof witness schema mismatch")
    geometry_id = wrapper["geometry_id"]
    if geometry_id not in GEOMETRY_IDS or proof.get("geometry_id") != geometry_id:
        raise Q1YError("proof geometry mismatch")
    if proof["case_ids"] != [f"{geometry_id}::{operation_id}" for operation_id in OPERATION_IDS]:
        raise Q1YError("proof case inventory mismatch")
    geometries, operations, material, _ = oracle._frozen_inputs()
    node_text = dict(geometries)[geometry_id]
    cache: dict[str, tuple[oracle.FieldContext, tuple[oracle.Expr, ...]]] = {}
    base_geometry = oracle._numbered_geometry(geometry_id, node_text, operations[0], sympy, cache)
    field_record = proof.get("field", {})
    basis = _basis(base_geometry, field_record)
    scalar, _, matrix = _decoder(basis)
    witnesses = proof["witnesses"]
    inverse = matrix(witnesses["h38_inverse"])
    rigid = matrix(witnesses["rigid"])
    complement = matrix(witnesses["complement"])
    lower = matrix(witnesses["ldl_lower"])
    pivots = [scalar(value) for value in witnesses["ldl_pivots"]]
    base_blocks = _blocks(base_geometry, material)
    if isinstance(base_blocks, oracle.MechanicsFailure):
        return {"case_count":8,"exact_local_contradictions":[f"{geometry_id}::E::{base_blocks.reason}"],"exact_operator_contradictions":[],"geometry_id":geometry_id,"local_k_sha256":"","ordered_unresolved":base_blocks.unresolved,"schema":CHECK_SCHEMA,"station_count":32,"terminal":contract["terminals"]["ordered_sign" if base_blocks.unresolved else "local_algebra"]}
    d38, q38, hourglass = base_blocks["d38"], base_blocks["q38"], base_blocks["hourglass"]
    identity38 = oracle.identity(base_geometry.field,38)
    inverse_exact = oracle.matrix_equal(oracle.matmul(d38,inverse),identity38) and oracle.matrix_equal(oracle.matmul(inverse,d38),identity38)
    k24 = oracle.matrix_add(oracle.scalar_matrix(base_geometry.field.exact(-1),oracle.matmul(oracle.matmul(q38,inverse),oracle.transpose(q38))),hourglass)
    proof_k = matrix(proof["base"]["k_total"])
    stiffness_exact = oracle.matrix_equal(k24,proof_k)
    symmetry = oracle.matrix_equal(k24,oracle.transpose(k24))
    expected_rigid = oracle._rigid_matrix(base_geometry)
    rigid_exact = oracle.matrix_equal(rigid,expected_rigid) and oracle.matrix_rank(rigid)==6 and oracle.all_zero_matrix(oracle.matmul(k24,rigid))
    expected_complement = oracle.nullspace_rref(oracle.transpose(rigid))
    complement_exact = oracle.matrix_equal(complement,expected_complement) and oracle.shape(complement)==(24,18)
    restricted = oracle.matmul(oracle.matmul(oracle.transpose(complement),k24),complement)
    diagonal = oracle.zeros(base_geometry.field,18,18)
    for i,pivot in enumerate(pivots): diagonal[i][i]=pivot
    ldl_exact = oracle.matrix_equal(restricted,oracle.matmul(oracle.matmul(lower,diagonal),oracle.transpose(lower)))
    pivot_signs = [_tower_sign(value, field_record) for value in witnesses["ldl_pivots"]]
    unresolved = any(value=="UNRESOLVED" for value in pivot_signs)
    probes = oracle._base_numerical_probe_vectors(base_geometry)
    common = oracle.dot(probes["common_drill"],oracle.matvec(k24,probes["common_drill"]))
    spin = oracle.dot(probes["translation_only_spin"],oracle.matvec(k24,probes["translation_only_spin"]))
    alt = oracle.dot(probes["alternating_drill"],oracle.matvec(hourglass,probes["alternating_drill"]))
    mode_tokens = witnesses["mode_energies"]
    if set(mode_tokens) != {"alternating_hourglass","common_drill","translation_only_spin"}:
        raise Q1YError("mode-energy witness schema mismatch")
    claimed_modes = [scalar(mode_tokens[name]) for name in ("common_drill","translation_only_spin","alternating_hourglass")]
    mode_values = [common, spin, alt]
    mode_signs = [_tower_sign(mode_tokens[name], field_record) for name in ("common_drill","translation_only_spin","alternating_hourglass")]
    unresolved = unresolved or any(value=="UNRESOLVED" for value in mode_signs)
    mode_identity_exact = all(a.is_equal(b) for a,b in zip(claimed_modes,mode_values,strict=True)) and oracle.all_zero_vector(oracle.matvec(k24,probes["matched_rigid"]))
    stationarity = _stationarity(d38,inverse,q38,hourglass,k24)
    structural_exact = inverse_exact and stiffness_exact and symmetry and rigid_exact and complement_exact and ldl_exact and mode_identity_exact and stationarity
    exact_sign_failure = any(value in {"ZERO","NEGATIVE"} for value in pivot_signs + mode_signs)
    map_rows = proof["operator_maps"]
    if [row.get("operation_id") for row in map_rows] != list(OPERATION_IDS) or any(set(row) != {"internal_g_to_base","operation_id","q_base_to_numbered"} for row in map_rows):
        raise Q1YError("operator-map order mismatch")
    covariance: list[dict[str,Any]]=[]
    for operation,row in zip(operations,map_rows,strict=True):
        current = oracle._numbered_geometry(geometry_id,node_text,operation,sympy,cache)
        blocks = _blocks(current,material)
        if isinstance(blocks,oracle.MechanicsFailure):
            covariance.append({"case_id":f"{geometry_id}::{operation.operation_id}","exact":False,"unresolved":blocks.unresolved}); unresolved = unresolved or blocks.unresolved; continue
        internal = matrix(row["internal_g_to_base"]); qmap = matrix(row["q_base_to_numbered"])
        maps_exact = _signed_permutation(internal) and _signed_permutation(qmap)
        stress, strain, lambda_map = _physical_maps(base_geometry.field,operation)
        smap = [r[:14] for r in internal[:14]]
        emap = [r[14:35] for r in internal[14:35]]
        lmap = [r[35:38] for r in internal[35:38]]
        block_diagonal = all(
            internal[i][j].is_zero()
            for i in range(38)
            for j in range(38)
            if not ((i < 14 and j < 14) or (14 <= i < 35 and 14 <= j < 35) or (35 <= i and 35 <= j))
        )
        maps_exact = maps_exact and block_diagonal and oracle.matrix_equal(lmap,lambda_map)
        for station,(nsg,neg) in enumerate(zip(blocks["n_sigma"],blocks["n_epsilon"],strict=True)):
            rg,sg=blocks["gauss"][station]; r0=operation.natural_map[0][0]*rg+operation.natural_map[0][1]*sg; s0=operation.natural_map[1][0]*rg+operation.natural_map[1][1]*sg
            base_index=next((i for i,(r,s) in enumerate(base_blocks["gauss"]) if r.is_equal(r0) and s.is_equal(s0)),None)
            if base_index is None: maps_exact=False; break
            maps_exact = maps_exact and oracle.matrix_equal(oracle.matmul(base_blocks["n_sigma"][base_index],smap),oracle.matmul(stress,nsg))
            maps_exact = maps_exact and oracle.matrix_equal(oracle.matmul(base_blocks["n_epsilon"][base_index],emap),oracle.matmul(strain,neg))
        expected_d=oracle.matmul(oracle.matmul(oracle.transpose(internal),d38),internal)
        expected_q=oracle.matmul(oracle.matmul(qmap,q38),internal)
        expected_hg=oracle.matmul(oracle.matmul(qmap,hourglass),oracle.transpose(qmap))
        blocks_exact=oracle.matrix_equal(blocks["d38"],expected_d) and oracle.matrix_equal(blocks["q38"],expected_q) and oracle.matrix_equal(blocks["hourglass"],expected_hg)
        current_k=oracle.matmul(oracle.matmul(qmap,k24),oracle.transpose(qmap))
        expected_qmap=oracle.matmul(oracle.matmul(oracle.transpose(oracle._block_frame(current.frame)),oracle._permutation(base_geometry.field,operation,6)),oracle._block_frame(base_geometry.frame))
        maps_exact=maps_exact and oracle.matrix_equal(qmap,expected_qmap)
        base_global=oracle._global_matrix(k24,base_geometry.frame)
        current_global=oracle._global_matrix(current_k,current.frame)
        permutation=oracle._permutation(base_geometry.field,operation,6)
        global_exact=oracle.matrix_equal(oracle.matmul(oracle.matmul(oracle.transpose(permutation),current_global),permutation),base_global)
        covariance.append({"case_id":f"{geometry_id}::{operation.operation_id}","exact":maps_exact and blocks_exact and global_exact,"unresolved":False})
    covariance_exact=all(row["exact"] for row in covariance)
    local_contradictions=[] if structural_exact and not exact_sign_failure else [f"{geometry_id}::E"]
    covariance_contradictions=[] if covariance_exact else [row["case_id"] for row in covariance if not row["exact"] and not row["unresolved"]]
    if local_contradictions: terminal=contract["terminals"]["local_algebra"]
    elif covariance_contradictions: terminal=contract["terminals"]["operator_covariance"]
    elif unresolved: terminal=contract["terminals"]["ordered_sign"]
    else: terminal=contract["terminals"]["success"]
    return {"case_count":8,"exact_local_contradictions":local_contradictions,"exact_operator_contradictions":covariance_contradictions,"geometry_id":geometry_id,"local_k_sha256":sha256(canonical_bytes(proof["base"]["k_total"])),"ordered_unresolved":unresolved,"schema":CHECK_SCHEMA,"station_count":32,"terminal":terminal}


def _parser() -> argparse.ArgumentParser:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-algebra-proof",action="store_true",required=True)
    parser.add_argument("--repository-root",type=Path,required=True); parser.add_argument("--contract",type=Path,required=True); parser.add_argument("--contract-sha256",required=True)
    parser.add_argument("--proof",type=Path,required=True); parser.add_argument("--environment-root",type=Path,required=True); parser.add_argument("--output",type=Path,required=True)
    return parser


def main(argv:Sequence[str]|None=None)->int:
    args=_parser().parse_args(argv)
    try:
        value=verify_proof(repository_root=args.repository_root.resolve(strict=True),contract_path=args.contract,contract_sha256=args.contract_sha256,proof_path=args.proof,environment_root=args.environment_root)
        write_exclusive(args.output,canonical_bytes(value)); return 0
    except (Q1YError,KeyError,TypeError,ValueError,ZeroDivisionError,OSError) as exc:
        print(f"BLOCKED_E4_PL_Q1Y_PROOF_OR_REVIEW: {exc}",file=sys.stderr); return 2


if __name__=="__main__": raise SystemExit(main())
