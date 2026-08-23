#!/usr/bin/env python3
"""Independent exact checker for one bounded Q1Z support/KKT proof.

The accepted Q1Y3 stiffness matrix is a hashed input.  This module does not
assemble, condense, or otherwise reconstruct the 38-field stationary system.
It independently reconstructs only the frozen frame, physical/drill split,
load, support, supported KKT identities, D4 transports, and the registered
proper-global covariance identity.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
import sys
from typing import Any, Callable, Sequence

import e4_pl_q1z_common as q1z


CHECK_SCHEMA = q1z.CHECK_SCHEMA
CONTRACT_SCHEMA = q1z.CONTRACT_SCHEMA
PROOF_SCHEMA = q1z.PROOF_SCHEMA
PROOF_WRAPPER_SCHEMA = q1z.PROOF_WRAPPER_SCHEMA
Q1Y_PROOF_SCHEMA = "anysolver.s4.e4-pl-q1y-algebra-proof-v1"
Q1Y_PROOF_WRAPPER_SCHEMA = "anysolver.s4.e4-pl-q1y-algebra-proof-wrapper-v1"

_GEOMETRY_CONTRACT = "docs/reference_cases/e4_pl_q1r_geometry_contract.json"
_FRAME_CONTRACT = "docs/reference_cases/e4_pl_q1r_frame_contract.json"
_SUPPORT_CONTRACT = "docs/reference_cases/e4_pl_q1r_support_contract.json"
_CASES = "docs/reference_cases/e4_pl_q1r_cases.json"
_Q1X_CONTRACT = "docs/reference_cases/e4_pl_q1x_transport_contract.json"
_Q1Y_CONTRACT = "docs/reference_cases/e4_pl_q1y_local_algebra_contract.json"
_Q1Y3_CONTRACT = "docs/reference_cases/e4_pl_q1y3_local_algebra_contract.json"
_Q1Y3_RESULT = "docs/reference_cases/e4_pl_q1y3_bounded_result.json"

_BASE_KEYS = {
    "drill_block",
    "drill_inverse",
    "drill_projector",
    "frame",
    "load",
    "multiplier",
    "physical_projector",
    "qd",
    "reaction",
    "support",
    "t5",
    "virtual",
}
_CASE_KEYS = {
    "case_id",
    "operation_id",
    "covariance_exact",
    "kkt_constraint_exact",
    "kkt_equilibrium_exact",
    "kkt_unique",
    "load_exact",
    "numerical_reaction_separate",
    "projectors_exact",
    "reaction_drill_free",
    "reaction_exact",
    "support_admissible",
    "support_factorization_exact",
    "virtual_work_exact",
}
_PROPER_KEYS = {
    "applicable",
    "drill_block",
    "frame",
    "load",
    "numbering_commutes",
    "projectors",
    "reaction",
    "stiffness",
    "support",
}


Scalar = Any
Vector = list[Scalar]
Matrix = list[Vector]


def _keys(value: Any, expected: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != expected:
        raise q1z.Q1ZError(f"{label} exact-key mismatch")
    return value


def _row_by_path(rows: Any, path: str, label: str) -> dict[str, Any]:
    if not isinstance(rows, list):
        raise q1z.Q1ZError(f"{label} inventory malformed")
    matches = [row for row in rows if isinstance(row, dict) and row.get("path") == path]
    if len(matches) != 1:
        raise q1z.Q1ZError(f"{label} path authority mismatch: {path}")
    return matches[0]


def _bound_json(root: Path, rows: Any, path: str, label: str) -> dict[str, Any]:
    row = _keys(_row_by_path(rows, path, label), {"bytes", "path", "sha256"}, label)
    q1z.verify_file(root / path, size=int(row["bytes"]), digest=str(row["sha256"]))
    _, value = q1z.read_json(root / path)
    if not isinstance(value, dict):
        raise q1z.Q1ZError(f"{label} must be a JSON object")
    return value


def _fraction(value: Any, label: str) -> Fraction:
    if isinstance(value, bool):
        raise q1z.Q1ZError(f"{label} is not an exact rational")
    if isinstance(value, int):
        return Fraction(value)
    if not isinstance(value, str):
        raise q1z.Q1ZError(f"{label} is not an exact rational string")
    try:
        result = Fraction(value)
    except (ValueError, ZeroDivisionError) as exc:
        raise q1z.Q1ZError(f"{label} is not an exact rational string") from exc
    if str(result) != value:
        raise q1z.Q1ZError(f"{label} rational is not canonical")
    return result


@dataclass(frozen=True)
class ExactField:
    """One SymPy AlgebraicField and its producer-independent tower basis."""

    sympy: Any
    domain: Any
    basis: tuple[Scalar, ...]

    @property
    def zero(self) -> Scalar:
        return self.domain.zero

    @property
    def one(self) -> Scalar:
        return self.domain.one

    def rational(self, value: Any, label: str = "rational") -> Scalar:
        fraction = _fraction(value, label)
        expression = self.sympy.Rational(fraction.numerator, fraction.denominator)
        return self.domain.from_sympy(expression)

    def square_root(self, value: Scalar, label: str) -> Scalar:
        try:
            expression = self.sympy.sqrt(self.domain.to_sympy(value))
            root = self.domain.from_sympy(expression)
        except Exception as exc:  # SymPy raises several domain-specific errors.
            raise q1z.Q1ZError(f"{label} is not contained in the frozen field") from exc
        if root * root != value:
            raise q1z.Q1ZError(f"{label} exact square-root identity failed")
        return root


def _load_sympy(environment_root: Path) -> Any:
    environment = str(environment_root.resolve(strict=True))
    if environment not in sys.path:
        sys.path.insert(0, environment)
    try:
        import sympy  # type: ignore[import-not-found]
    except Exception as exc:
        raise q1z.Q1ZError("failed to import the exact SymPy environment") from exc
    if sympy.__version__ != "1.14.0":
        raise q1z.Q1ZError("unexpected SymPy version")
    return sympy


def _field(sympy: Any, record: Any) -> ExactField:
    field_record = _keys(record, {"dimension", "radicands"}, "field")
    radicands = field_record["radicands"]
    dimension = field_record["dimension"]
    if (
        isinstance(dimension, bool)
        or not isinstance(dimension, int)
        or not isinstance(radicands, list)
        or dimension != 1 << len(radicands)
        or dimension > 32
    ):
        raise q1z.Q1ZError("field tower dimension mismatch")
    root_expressions: list[Any] = []
    for index, coefficients in enumerate(radicands):
        if not isinstance(coefficients, list) or len(coefficients) != 1 << index:
            raise q1z.Q1ZError("field radicand coefficient dimension mismatch")
        monomials: list[Any] = []
        for mask in range(1 << index):
            monomial = sympy.Integer(1)
            for root_index, root in enumerate(root_expressions):
                if mask & (1 << root_index):
                    monomial *= root
            monomials.append(monomial)
        radicand = sympy.Integer(0)
        for coefficient, monomial in zip(coefficients, monomials, strict=True):
            rational = _fraction(coefficient, "field radicand coefficient")
            radicand += sympy.Rational(rational.numerator, rational.denominator) * monomial
        root_expressions.append(sympy.sqrt(radicand))
    try:
        domain = sympy.QQ.algebraic_field(*root_expressions)
        roots = [domain.from_sympy(root) for root in root_expressions]
    except Exception as exc:
        raise q1z.Q1ZError("failed to construct the frozen algebraic field") from exc
    if int(domain.ext.minpoly.degree()) != dimension:
        raise q1z.Q1ZError("algebraic field degree mismatch")
    basis: list[Scalar] = []
    for mask in range(dimension):
        monomial = domain.one
        for index, root in enumerate(roots):
            if mask & (1 << index):
                monomial *= root
        basis.append(monomial)
    for index, coefficients in enumerate(radicands):
        radicand = domain.zero
        for coefficient, monomial in zip(coefficients, basis[: 1 << index], strict=True):
            rational = _fraction(coefficient, "field radicand coefficient")
            radicand += domain.from_sympy(
                sympy.Rational(rational.numerator, rational.denominator)
            ) * monomial
        if roots[index] * roots[index] != radicand:
            raise q1z.Q1ZError("field tower square identity failed")
    return ExactField(sympy=sympy, domain=domain, basis=tuple(basis))


def _decoder(field: ExactField) -> tuple[
    Callable[[Any], Scalar], Callable[[Any], Vector], Callable[[Any], Matrix]
]:
    cache: dict[tuple[str, ...], Scalar] = {}

    def scalar(token: Any) -> Scalar:
        if not isinstance(token, list) or len(token) != len(field.basis):
            raise q1z.Q1ZError("algebraic coefficient-token dimension mismatch")
        key: tuple[str, ...] = tuple(token) if all(isinstance(value, str) for value in token) else ()
        if len(key) != len(token):
            raise q1z.Q1ZError("algebraic coefficient token is not a string")
        if key not in cache:
            value = field.zero
            for coefficient, monomial in zip(key, field.basis, strict=True):
                value += field.rational(coefficient, "algebraic coefficient") * monomial
            cache[key] = value
        return cache[key]

    def vector(values: Any) -> Vector:
        if not isinstance(values, list):
            raise q1z.Q1ZError("algebraic vector is malformed")
        return [scalar(value) for value in values]

    def matrix(values: Any) -> Matrix:
        if not isinstance(values, list):
            raise q1z.Q1ZError("algebraic matrix is malformed")
        rows = [vector(row) for row in values]
        if rows and any(len(row) != len(rows[0]) for row in rows):
            raise q1z.Q1ZError("algebraic matrix is ragged")
        return rows

    return scalar, vector, matrix


def _shape(matrix: Matrix) -> tuple[int, int]:
    if not isinstance(matrix, list):
        raise q1z.Q1ZError("matrix is malformed")
    if not matrix:
        return (0, 0)
    columns = len(matrix[0])
    if any(len(row) != columns for row in matrix):
        raise q1z.Q1ZError("matrix is ragged")
    return len(matrix), columns


def _require_shape(matrix: Matrix, rows: int, columns: int, label: str) -> Matrix:
    if _shape(matrix) != (rows, columns):
        raise q1z.Q1ZError(f"{label} dimension mismatch")
    return matrix


def _require_vector(vector: Vector, length: int, label: str) -> Vector:
    if len(vector) != length:
        raise q1z.Q1ZError(f"{label} dimension mismatch")
    return vector


def _zeros(field: ExactField, rows: int, columns: int) -> Matrix:
    return [[field.zero for _ in range(columns)] for _ in range(rows)]


def _identity(field: ExactField, dimension: int) -> Matrix:
    result = _zeros(field, dimension, dimension)
    for index in range(dimension):
        result[index][index] = field.one
    return result


def _transpose(matrix: Matrix) -> Matrix:
    rows, columns = _shape(matrix)
    return [[matrix[row][column] for row in range(rows)] for column in range(columns)]


def _matmul(left: Matrix, right: Matrix, field: ExactField) -> Matrix:
    rows, shared = _shape(left)
    right_rows, columns = _shape(right)
    if shared != right_rows:
        raise q1z.Q1ZError("matrix product dimension mismatch")
    result = _zeros(field, rows, columns)
    for row in range(rows):
        for index in range(shared):
            coefficient = left[row][index]
            if coefficient == field.zero:
                continue
            for column in range(columns):
                result[row][column] += coefficient * right[index][column]
    return result


def _matvec(matrix: Matrix, vector: Vector, field: ExactField) -> Vector:
    rows, columns = _shape(matrix)
    if columns != len(vector):
        raise q1z.Q1ZError("matrix-vector product dimension mismatch")
    return [
        sum((matrix[row][column] * vector[column] for column in range(columns)), field.zero)
        for row in range(rows)
    ]


def _equal(left: Matrix, right: Matrix) -> bool:
    return _shape(left) == _shape(right) and all(
        a == b
        for left_row, right_row in zip(left, right, strict=True)
        for a, b in zip(left_row, right_row, strict=True)
    )


def _vector_equal(left: Vector, right: Vector) -> bool:
    return len(left) == len(right) and all(a == b for a, b in zip(left, right, strict=True))


def _all_zero(matrix: Matrix, field: ExactField) -> bool:
    return all(value == field.zero for row in matrix for value in row)


def _all_zero_vector(vector: Vector, field: ExactField) -> bool:
    return all(value == field.zero for value in vector)


def _dot(left: Vector, right: Vector, field: ExactField) -> Scalar:
    if len(left) != len(right):
        raise q1z.Q1ZError("dot-product dimension mismatch")
    return sum((a * b for a, b in zip(left, right, strict=True)), field.zero)


def _vector_sub(left: Vector, right: Vector) -> Vector:
    if len(left) != len(right):
        raise q1z.Q1ZError("vector subtraction dimension mismatch")
    return [a - b for a, b in zip(left, right, strict=True)]


def _columns_matrix(columns: Sequence[Vector]) -> Matrix:
    if not columns or any(len(column) != len(columns[0]) for column in columns):
        raise q1z.Q1ZError("column matrix is malformed")
    return [[column[row] for column in columns] for row in range(len(columns[0]))]


def _cross(left: Vector, right: Vector) -> Vector:
    if len(left) != 3 or len(right) != 3:
        raise q1z.Q1ZError("cross product requires three-vectors")
    return [
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    ]


def _norm(vector: Vector, field: ExactField, label: str) -> Scalar:
    return field.square_root(_dot(vector, vector, field), label)


def _frame(nodes: Sequence[Vector], field: ExactField) -> Matrix:
    if len(nodes) != 4 or any(len(node) != 3 for node in nodes):
        raise q1z.Q1ZError("geometry node inventory mismatch")
    d1 = _vector_sub(nodes[2], nodes[0])
    d2 = _vector_sub(nodes[1], nodes[3])
    h1 = [value / _norm(d1, field, "first diagonal norm") for value in d1]
    h2 = [value / _norm(d2, field, "second diagonal norm") for value in d2]
    plus = [a + b for a, b in zip(h1, h2, strict=True)]
    minus = [a - b for a, b in zip(h1, h2, strict=True)]
    t1 = [value / _norm(plus, field, "frame plus norm") for value in plus]
    t2 = [value / _norm(minus, field, "frame minus norm") for value in minus]
    t3 = _cross(t1, t2)
    result = _columns_matrix((t1, t2, t3))
    if not _equal(_matmul(_transpose(result), result, field), _identity(field, 3)):
        raise q1z.Q1ZError("equation-7 frame is not exactly orthonormal")
    return result


def _frame6(frame: Matrix, field: ExactField) -> Matrix:
    _require_shape(frame, 3, 3, "frame")
    result = _zeros(field, 24, 24)
    for node in range(4):
        for block in range(2):
            for row in range(3):
                for column in range(3):
                    result[6 * node + 3 * block + row][6 * node + 3 * block + column] = frame[row][column]
    return result


def _t5(frame: Matrix, field: ExactField) -> Matrix:
    result = _zeros(field, 24, 20)
    for node in range(4):
        for row in range(3):
            for column in range(3):
                result[6 * node + row][5 * node + column] = frame[row][column]
            for column in range(2):
                result[6 * node + 3 + row][5 * node + 3 + column] = frame[row][column]
    return result


def _qd(frame: Matrix, field: ExactField) -> Matrix:
    result = _zeros(field, 24, 4)
    for node in range(4):
        for row in range(3):
            result[6 * node + 3 + row][node] = frame[row][2]
    return result


def _permutation(node_tuple: Sequence[Any], width: int, field: ExactField) -> Matrix:
    if len(node_tuple) != 4 or sorted(node_tuple) != [1, 2, 3, 4]:
        raise q1z.Q1ZError("D4 node tuple mismatch")
    result = _zeros(field, 4 * width, 4 * width)
    for target, source_one_based in enumerate(node_tuple):
        source = int(source_one_based) - 1
        for dof in range(width):
            result[width * target + dof][width * source + dof] = field.one
    return result


def _nodes(value: Any, field: ExactField, label: str) -> list[Vector]:
    if not isinstance(value, list) or len(value) != 4:
        raise q1z.Q1ZError(f"{label} node inventory mismatch")
    result: list[Vector] = []
    for node_index, node in enumerate(value):
        if not isinstance(node, list) or len(node) != 3:
            raise q1z.Q1ZError(f"{label} node dimension mismatch")
        result.append([
            field.rational(coordinate, f"{label} node {node_index} coordinate")
            for coordinate in node
        ])
    return result


def _load_inputs(cases: dict[str, Any], field: ExactField) -> Vector:
    physical = _keys(
        cases.get("physical_load"),
        {
            "construction",
            "direct_drill_components",
            "id",
            "local_order_per_node",
            "numbered_local_transport",
            "numbered_transport",
            "orthogonality",
            "p_f_node_major",
            "work_identity",
        },
        "physical load",
    )
    if (
        physical["id"] != "PHYSICAL_RANGE_T5_LOAD"
        or physical["construction"] != "f=T5*p_f"
        or physical["direct_drill_components"] != "NONE"
    ):
        raise q1z.Q1ZError("physical load authority mismatch")
    rows = physical["p_f_node_major"]
    if not isinstance(rows, list) or len(rows) != 4 or any(not isinstance(row, list) or len(row) != 5 for row in rows):
        raise q1z.Q1ZError("physical load coordinate dimension mismatch")
    return [
        field.rational(value, "physical load coordinate")
        for row in rows
        for value in row
    ]


def _frozen_documents(root: Path, contract: dict[str, Any]) -> dict[str, dict[str, Any]]:
    q1x = _bound_json(root, contract["frozen_inputs"], _Q1X_CONTRACT, "Q1X contract")
    if q1x.get("schema") != "anysolver.s4.e4-pl-q1x-transport-contract-v1":
        raise q1z.Q1ZError("Q1X contract schema mismatch")
    geometry = _bound_json(root, q1x.get("frozen_inputs"), _GEOMETRY_CONTRACT, "geometry contract")
    direct = contract["frozen_inputs"]
    frame = _bound_json(root, direct, _FRAME_CONTRACT, "frame contract")
    support = _bound_json(root, direct, _SUPPORT_CONTRACT, "support contract")
    cases = _bound_json(root, direct, _CASES, "registered cases")
    q1y3 = _bound_json(root, direct, _Q1Y3_CONTRACT, "Q1Y3 contract")
    q1y3_result = _bound_json(root, direct, _Q1Y3_RESULT, "Q1Y3 result")
    q1y = _bound_json(root, q1y3.get("frozen_inputs"), _Q1Y_CONTRACT, "Q1Y contract")
    if geometry.get("schema") != "anysolver.e4.pl-q1r-geometry-contract-v1":
        raise q1z.Q1ZError("geometry contract schema mismatch")
    if frame.get("schema") != "anysolver.e4.pl-q1r-frame-contract-v1":
        raise q1z.Q1ZError("frame contract schema mismatch")
    if support.get("schema") != "anysolver.e4.pl-q1r-support-contract-v1":
        raise q1z.Q1ZError("support contract schema mismatch")
    if cases.get("schema") != "anysolver.e4.pl-q1r-cases-v1":
        raise q1z.Q1ZError("registered cases schema mismatch")
    if q1y3.get("schema") != "anysolver.s4.e4-pl-q1y3-local-algebra-contract-v1":
        raise q1z.Q1ZError("Q1Y3 contract schema mismatch")
    if q1y3_result.get("schema") != "anysolver.s4.e4-pl-q1y3-algebra-aggregate-v1":
        raise q1z.Q1ZError("Q1Y3 result schema mismatch")
    if q1y.get("schema") != "anysolver.s4.e4-pl-q1y-local-algebra-contract-v1":
        raise q1z.Q1ZError("Q1Y contract schema mismatch")
    if support.get("registered_support_probes", [None, None])[1] != {
        "A_5": "I_20",
        "classification_use": "RESTRICTED_BOUNDARY_PROJECTOR_AND_REACTION_SEPARATION_ONLY",
        "id": "FULL_PHYSICAL_ZERO_PROJECTOR_PROBE",
        "prescribed_values": "ZERO_20",
    }:
        raise q1z.Q1ZError("registered full-physical support mismatch")
    return {
        "cases": cases,
        "frame": frame,
        "geometry": geometry,
        "q1y": q1y,
        "q1y3": q1y3,
        "q1y3_result": q1y3_result,
        "support": support,
    }


def _q1y3_proof(
    root: Path,
    evidence_root: Path,
    contract: dict[str, Any],
    documents: dict[str, dict[str, Any]],
    geometry_id: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    authority = _keys(
        q1z.proof_authority(contract, geometry_id),
        {"bytes", "geometry_id", "name", "sha256"},
        "Q1Y3 proof authority",
    )
    evidence = evidence_root.resolve(strict=True)
    if evidence.is_symlink() or not evidence.is_dir():
        raise q1z.Q1ZError("Q1Y3 evidence root is invalid")
    candidate = (evidence / authority["name"]).resolve(strict=True)
    try:
        candidate.relative_to(evidence)
    except ValueError as exc:
        raise q1z.Q1ZError("Q1Y3 evidence path escapes its root") from exc
    raw = q1z.verify_file(candidate, size=int(authority["bytes"]), digest=str(authority["sha256"]))
    _, wrapper = q1z.read_json(candidate)
    wrapper = _keys(
        wrapper,
        {"candidate_id", "contract_sha256", "geometry_id", "proof", "proof_sha256", "schema", "study_id"},
        "Q1Y3 proof wrapper",
    )
    if wrapper["schema"] != Q1Y_PROOF_WRAPPER_SCHEMA or wrapper["geometry_id"] != geometry_id:
        raise q1z.Q1ZError("Q1Y3 proof wrapper authority mismatch")
    q1y = documents["q1y"]
    q1y_row = _row_by_path(documents["q1y3"]["frozen_inputs"], _Q1Y_CONTRACT, "Q1Y authority")
    if (
        wrapper["candidate_id"] != q1y["candidate_id"]
        or wrapper["study_id"] != q1y["study_id"]
        or wrapper["contract_sha256"] != str(q1y_row["sha256"]).upper()
    ):
        raise q1z.Q1ZError("Q1Y3 proof inherited authority mismatch")
    proof = _keys(
        wrapper["proof"],
        {"base", "case_ids", "field", "geometry_id", "operator_maps", "schema", "witnesses"},
        "Q1Y3 proof payload",
    )
    if (
        wrapper["proof_sha256"] != q1z.sha256(q1z.canonical_bytes(proof))
        or proof["schema"] != Q1Y_PROOF_SCHEMA
        or proof["geometry_id"] != geometry_id
    ):
        raise q1z.Q1ZError("Q1Y3 proof payload hash/schema mismatch")
    _keys(proof["base"], {"h38_sha256", "k_total"}, "Q1Y3 proof base")
    _keys(proof["field"], {"dimension", "radicands"}, "Q1Y3 proof field")
    _keys(
        proof["witnesses"],
        {"complement", "h38_inverse", "ldl_lower", "ldl_pivots", "mode_energies", "rigid"},
        "Q1Y3 proof witnesses",
    )
    expected_cases = [f"{geometry_id}::{operation}" for operation in q1z.OPERATION_IDS]
    if proof["case_ids"] != expected_cases:
        raise q1z.Q1ZError("Q1Y3 proof case inventory mismatch")
    maps = proof["operator_maps"]
    if not isinstance(maps, list) or len(maps) != 8:
        raise q1z.Q1ZError("Q1Y3 operator-map inventory mismatch")
    for operation_id, row in zip(q1z.OPERATION_IDS, maps, strict=True):
        _keys(row, {"internal_g_to_base", "operation_id", "q_base_to_numbered"}, "Q1Y3 operator map")
        if row["operation_id"] != operation_id:
            raise q1z.Q1ZError("Q1Y3 operator-map order mismatch")
    shards = documents["q1y3_result"].get("shards")
    if not isinstance(shards, list):
        raise q1z.Q1ZError("Q1Y3 result shard inventory mismatch")
    shard = [row for row in shards if isinstance(row, dict) and row.get("geometry_id") == geometry_id]
    if len(shard) != 1 or shard[0].get("proof_sha256") != q1z.sha256(raw):
        raise q1z.Q1ZError("Q1Y3 result proof binding mismatch")
    return wrapper, proof


def _support_proof(
    path: Path,
    contract: dict[str, Any],
    source_wrapper: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    _, wrapper = q1z.read_json(path)
    wrapper = _keys(
        wrapper,
        {
            "candidate_id",
            "contract_sha256",
            "geometry_id",
            "proof",
            "proof_sha256",
            "q1y3_proof_sha256",
            "schema",
            "study_id",
        },
        "support proof wrapper",
    )
    if wrapper["schema"] != PROOF_WRAPPER_SCHEMA:
        raise q1z.Q1ZError("support proof wrapper schema mismatch")
    proof = _keys(
        wrapper["proof"],
        {"base", "case_records", "field", "geometry_id", "proper_global", "q1y3_proof_sha256", "schema"},
        "support proof payload",
    )
    if wrapper["proof_sha256"] != q1z.sha256(q1z.canonical_bytes(proof)):
        raise q1z.Q1ZError("support proof payload hash mismatch")
    geometry_id = wrapper["geometry_id"]
    authority = q1z.proof_authority(contract, geometry_id)
    if (
        wrapper["candidate_id"] != contract["candidate_id"]
        or wrapper["study_id"] != contract["study_id"]
        or wrapper["contract_sha256"] != contract["_caller_sha256"]
        or wrapper["q1y3_proof_sha256"] != str(authority["sha256"]).upper()
        or proof["q1y3_proof_sha256"] != str(authority["sha256"]).upper()
        or proof["geometry_id"] != geometry_id
        or proof["schema"] != PROOF_SCHEMA
    ):
        raise q1z.Q1ZError("support proof authority mismatch")
    if source_wrapper["geometry_id"] != geometry_id:
        raise q1z.Q1ZError("support/Q1Y3 proof geometry mismatch")
    _keys(proof["base"], _BASE_KEYS, "support proof base")
    _keys(proof["field"], {"dimension", "radicands"}, "support proof field")
    if proof["field"] != source_wrapper["proof"]["field"]:
        raise q1z.Q1ZError("support proof field differs from bound Q1Y3 field")
    records = proof["case_records"]
    if not isinstance(records, list) or len(records) != 8:
        raise q1z.Q1ZError("support proof case inventory mismatch")
    for operation_id, record in zip(q1z.OPERATION_IDS, records, strict=True):
        _keys(record, _CASE_KEYS, "support proof case")
        if (
            record["operation_id"] != operation_id
            or record["case_id"] != f"{geometry_id}::{operation_id}"
            or any(not isinstance(record[key], bool) for key in _CASE_KEYS - {"case_id", "operation_id"})
        ):
            raise q1z.Q1ZError("support proof case order/type mismatch")
    proper = _keys(proof["proper_global"], _PROPER_KEYS, "proper-global proof")
    if any(not isinstance(proper[key], bool) for key in _PROPER_KEYS):
        raise q1z.Q1ZError("proper-global proof values must be booleans")
    expected_applicable = geometry_id == "Q3_TAPERED_SKEW_RSTAR_TRANSLATED"
    if proper["applicable"] is not expected_applicable:
        raise q1z.Q1ZError("proper-global applicability mismatch")
    return wrapper, proof


def _geometry_nodes(geometry: dict[str, Any], geometry_id: str, field: ExactField) -> list[Vector]:
    rows = geometry.get("geometries")
    if not isinstance(rows, list):
        raise q1z.Q1ZError("geometry inventory mismatch")
    matches = [row for row in rows if isinstance(row, dict) and row.get("id") == geometry_id]
    if len(matches) == 1:
        return _nodes(matches[0].get("nodes"), field, geometry_id)
    transform = geometry.get("global_transform")
    if geometry_id == "Q3_TAPERED_SKEW_RSTAR_TRANSLATED" and isinstance(transform, dict):
        if transform.get("id") != geometry_id:
            raise q1z.Q1ZError("proper-global geometry authority mismatch")
        return _nodes(transform.get("derived_nodes"), field, geometry_id)
    raise q1z.Q1ZError("unregistered geometry")


def _operations(frame_contract: dict[str, Any]) -> list[dict[str, Any]]:
    d4 = frame_contract.get("d4")
    if not isinstance(d4, dict) or not isinstance(d4.get("operations"), list):
        raise q1z.Q1ZError("D4 operation inventory mismatch")
    rows = d4["operations"]
    if len(rows) != 8 or [row.get("id") for row in rows if isinstance(row, dict)] != list(q1z.OPERATION_IDS):
        raise q1z.Q1ZError("D4 operation order mismatch")
    return rows


def _decode_base(base: dict[str, Any], decoder: tuple[Callable[[Any], Scalar], Callable[[Any], Vector], Callable[[Any], Matrix]]) -> dict[str, Any]:
    _, vector, matrix = decoder
    return {
        "drill_block": _require_shape(matrix(base["drill_block"]), 4, 4, "drill block"),
        "drill_inverse": _require_shape(matrix(base["drill_inverse"]), 4, 4, "drill inverse"),
        "drill_projector": _require_shape(matrix(base["drill_projector"]), 24, 24, "drill projector"),
        "frame": _require_shape(matrix(base["frame"]), 3, 3, "frame"),
        "load": _require_vector(vector(base["load"]), 24, "load"),
        "multiplier": _require_vector(vector(base["multiplier"]), 20, "multiplier"),
        "physical_projector": _require_shape(matrix(base["physical_projector"]), 24, 24, "physical projector"),
        "qd": _require_shape(matrix(base["qd"]), 24, 4, "QD"),
        "reaction": _require_vector(vector(base["reaction"]), 24, "reaction"),
        "support": _require_shape(matrix(base["support"]), 20, 24, "support"),
        "t5": _require_shape(matrix(base["t5"]), 24, 20, "T5"),
        "virtual": _require_vector(vector(base["virtual"]), 24, "virtual vector"),
    }


def _case_claims(record: dict[str, Any]) -> dict[str, bool]:
    return {key: bool(record[key]) for key in _CASE_KEYS - {"case_id", "operation_id"}}


def _proper_rotation(geometry: dict[str, Any], field: ExactField) -> tuple[Matrix, Vector]:
    transform = geometry.get("global_transform")
    if not isinstance(transform, dict):
        raise q1z.Q1ZError("proper-global transform is missing")
    rotation = [
        [field.rational(value, "proper rotation") for value in row]
        for row in transform.get("R_star", [])
    ]
    translation = [field.rational(value, "proper translation") for value in transform.get("b_star", [])]
    _require_shape(rotation, 3, 3, "proper rotation")
    _require_vector(translation, 3, "proper translation")
    if not _equal(_matmul(_transpose(rotation), rotation, field), _identity(field, 3)):
        raise q1z.Q1ZError("proper rotation is not orthogonal")
    return rotation, translation


def _global_rotation(rotation: Matrix, field: ExactField) -> Matrix:
    result = _zeros(field, 24, 24)
    for node in range(4):
        for block in range(2):
            for row in range(3):
                for column in range(3):
                    result[6 * node + 3 * block + row][6 * node + 3 * block + column] = rotation[row][column]
    return result


def _proper_certificate(
    geometry_id: str,
    geometry: dict[str, Any],
    evidence_root: Path,
    root: Path,
    contract: dict[str, Any],
    documents: dict[str, dict[str, Any]],
    field: ExactField,
    decoder: tuple[Callable[[Any], Scalar], Callable[[Any], Vector], Callable[[Any], Matrix]],
    local_k: Matrix,
    base_frame: Matrix,
    base_t5: Matrix,
    base_qd: Matrix,
    base_load: Vector,
    base_support: Matrix,
    base_reaction: Vector,
    base_drill: Matrix,
    operations: list[dict[str, Any]],
) -> dict[str, bool]:
    if geometry_id != "Q3_TAPERED_SKEW_RSTAR_TRANSLATED":
        return {key: (key != "applicable") for key in _PROPER_KEYS}
    source_wrapper, source_proof = _q1y3_proof(
        root, evidence_root, contract, documents, "Q3_TAPERED_SKEW"
    )
    if source_proof["field"] != source_wrapper["proof"]["field"] or source_proof["field"] != documents.get("_active_field", source_proof["field"]):
        raise q1z.Q1ZError("proper-global source field mismatch")
    _, _, matrix = decoder
    source_k = _require_shape(matrix(source_proof["base"]["k_total"]), 24, 24, "proper-global source K")
    source_nodes = _geometry_nodes(geometry, "Q3_TAPERED_SKEW", field)
    source_frame = _frame(source_nodes, field)
    source_frame6 = _frame6(source_frame, field)
    source_t5 = _t5(source_frame, field)
    source_qd = _qd(source_frame, field)
    load_coordinates = _load_inputs(documents["cases"], field)
    source_load = _matvec(source_t5, load_coordinates, field)
    source_support = _transpose(source_t5)
    source_reaction = list(source_load)
    source_global_k = _matmul(_matmul(source_frame6, source_k, field), _transpose(source_frame6), field)
    rotation, _ = _proper_rotation(geometry, field)
    global_rotation = _global_rotation(rotation, field)
    expected_frame = _matmul(rotation, source_frame, field)
    expected_t5 = _matmul(global_rotation, source_t5, field)
    expected_qd = _matmul(global_rotation, source_qd, field)
    base_frame6 = _frame6(base_frame, field)
    base_global_k = _matmul(_matmul(base_frame6, local_k, field), _transpose(base_frame6), field)
    stiffness = _equal(
        base_global_k,
        _matmul(_matmul(global_rotation, source_global_k, field), _transpose(global_rotation), field),
    )
    frame_exact = _equal(base_frame, expected_frame)
    projectors = (
        _equal(base_t5, expected_t5)
        and _equal(base_qd, expected_qd)
    )
    load_exact = _vector_equal(base_load, _matvec(global_rotation, source_load, field))
    support_exact = _equal(base_support, _matmul(source_support, _transpose(global_rotation), field))
    reaction_exact = _vector_equal(base_reaction, _matvec(global_rotation, source_reaction, field))
    source_drill = _matmul(
        _matmul(_transpose(source_qd), source_global_k, field), source_qd, field
    )
    drill_exact = _equal(base_drill, source_drill)
    commutes = True
    for operation in operations:
        permutation = _permutation(operation.get("node_tuple", []), 6, field)
        commutes = commutes and _equal(
            _matmul(permutation, global_rotation, field),
            _matmul(global_rotation, permutation, field),
        )
    return {
        "applicable": True,
        "drill_block": drill_exact,
        "frame": frame_exact,
        "load": load_exact,
        "numbering_commutes": commutes,
        "projectors": projectors,
        "reaction": reaction_exact,
        "stiffness": stiffness,
        "support": support_exact,
    }


def verify_proof(
    *,
    repository_root: Path,
    contract_path: Path,
    contract_sha256: str,
    q1y3_evidence_root: Path,
    proof_path: Path,
    environment_root: Path,
) -> dict[str, Any]:
    root = repository_root.resolve(strict=True)
    contract = q1z.validate_contract(root, contract_path, contract_sha256)
    contract = dict(contract)
    contract["_caller_sha256"] = contract_sha256.upper()
    q1z.validate_environment(root, environment_root, contract)
    documents = _frozen_documents(root, contract)

    # Parse just enough of the support wrapper to select its independently
    # hashed Q1Y3 input before importing SymPy or decoding algebra.
    _, preliminary = q1z.read_json(proof_path)
    if not isinstance(preliminary, dict) or not isinstance(preliminary.get("geometry_id"), str):
        raise q1z.Q1ZError("support proof geometry is missing")
    geometry_id = preliminary["geometry_id"]
    if geometry_id not in q1z.GEOMETRY_IDS:
        raise q1z.Q1ZError("support proof geometry is unregistered")
    source_wrapper, source_proof = _q1y3_proof(
        root, q1y3_evidence_root, contract, documents, geometry_id
    )
    wrapper, proof = _support_proof(proof_path, contract, source_wrapper)
    sympy = _load_sympy(environment_root)
    field = _field(sympy, proof["field"])
    decoder = _decoder(field)
    _, _, matrix = decoder
    local_k = _require_shape(matrix(source_proof["base"]["k_total"]), 24, 24, "bound Q1Y3 K")
    if not _equal(local_k, _transpose(local_k)):
        raise q1z.Q1ZError("bound Q1Y3 K is not symmetric")
    base = _decode_base(proof["base"], decoder)

    geometry = documents["geometry"]
    nodes = _geometry_nodes(geometry, geometry_id, field)
    expected_frame = _frame(nodes, field)
    expected_frame6 = _frame6(expected_frame, field)
    expected_t5 = _t5(expected_frame, field)
    expected_qd = _qd(expected_frame, field)
    expected_physical = _matmul(expected_t5, _transpose(expected_t5), field)
    expected_drill_projector = _matmul(expected_qd, _transpose(expected_qd), field)
    expected_support = _transpose(expected_t5)
    load_coordinates = _load_inputs(documents["cases"], field)
    expected_load = _matvec(expected_t5, load_coordinates, field)
    global_k = _matmul(_matmul(expected_frame6, local_k, field), _transpose(expected_frame6), field)
    expected_drill = _matmul(_matmul(_transpose(expected_qd), global_k, field), expected_qd, field)
    expected_multiplier = load_coordinates
    expected_reaction = _matvec(_transpose(expected_support), expected_multiplier, field)
    identity4 = _identity(field, 4)

    base_witness_exact = all((
        _equal(base["frame"], expected_frame),
        _equal(base["t5"], expected_t5),
        _equal(base["qd"], expected_qd),
        _equal(base["physical_projector"], expected_physical),
        _equal(base["drill_projector"], expected_drill_projector),
        _equal(base["support"], expected_support),
        _vector_equal(base["load"], expected_load),
        _equal(base["drill_block"], expected_drill),
        _vector_equal(base["multiplier"], expected_multiplier),
        _vector_equal(base["reaction"], expected_reaction),
    ))
    projector_partition = _equal(
        [
            [expected_physical[row][column] + expected_drill_projector[row][column] for column in range(24)]
            for row in range(24)
        ],
        _identity(field, 24),
    ) and _all_zero(_matmul(_transpose(expected_t5), expected_qd, field), field)
    support_admissible = _all_zero(_matmul(expected_support, expected_qd, field), field)
    support_factorization = _equal(expected_support, _transpose(expected_t5))
    load_exact = _all_zero_vector(_matvec(_transpose(expected_qd), expected_load, field), field)
    reaction_exact = _vector_equal(expected_reaction, expected_load)
    reaction_drill_free = _all_zero_vector(
        _matvec(_transpose(expected_qd), expected_reaction, field), field
    )
    inverse_exact = (
        _equal(_matmul(expected_drill, base["drill_inverse"], field), identity4)
        and _equal(_matmul(base["drill_inverse"], expected_drill, field), identity4)
    )
    zero_solution = [field.zero for _ in range(24)]
    kkt_constraint = _all_zero_vector(
        _matvec(expected_support, zero_solution, field), field
    )
    kkt_equilibrium = _all_zero_vector(
        _vector_sub(
            [
                stiffness + reaction
                for stiffness, reaction in zip(
                    _matvec(global_k, zero_solution, field),
                    expected_reaction,
                    strict=True,
                )
            ],
            expected_load,
        ),
        field,
    )
    virtual_work = _dot(expected_reaction, base["virtual"], field) == _dot(
        expected_multiplier, _matvec(expected_support, base["virtual"], field), field
    )

    boundary_base_exact = all((
        base_witness_exact,
        projector_partition,
        support_admissible,
        support_factorization,
        load_exact,
        reaction_drill_free,
        virtual_work,
    ))
    kkt_base_exact = all((inverse_exact, kkt_constraint, kkt_equilibrium, reaction_exact))

    operations = _operations(documents["frame"])
    source_maps = source_proof["operator_maps"]
    actual_cases: list[dict[str, bool]] = []
    support_boundary_contradictions: list[str] = []
    kkt_contradictions: list[str] = []
    covariance_contradictions: list[str] = []
    if not boundary_base_exact:
        support_boundary_contradictions.append(f"{geometry_id}::E")
    if not kkt_base_exact:
        kkt_contradictions.append(f"{geometry_id}::E")

    for operation, source_map in zip(operations, source_maps, strict=True):
        operation_id = operation["id"]
        case_id = f"{geometry_id}::{operation_id}"
        node_tuple = operation.get("node_tuple", [])
        numbered_nodes = [nodes[int(index) - 1] for index in node_tuple]
        numbered_frame = _frame(numbered_nodes, field)
        numbered_frame6 = _frame6(numbered_frame, field)
        numbered_t5 = _t5(numbered_frame, field)
        numbered_qd = _qd(numbered_frame, field)
        permutation = _permutation(node_tuple, 6, field)
        expected_qmap = _matmul(
            _matmul(_transpose(numbered_frame6), permutation, field), expected_frame6, field
        )
        qmap = _require_shape(
            matrix(source_map["q_base_to_numbered"]), 24, 24, "Q1Y3 numbered q map"
        )
        qmap_exact = _equal(qmap, expected_qmap)
        numbered_local_k = _matmul(_matmul(qmap, local_k, field), _transpose(qmap), field)
        numbered_global_k = _matmul(
            _matmul(numbered_frame6, numbered_local_k, field), _transpose(numbered_frame6), field
        )
        covariance_exact = qmap_exact and _equal(
            numbered_global_k,
            _matmul(_matmul(permutation, global_k, field), _transpose(permutation), field),
        )
        numbered_load = _matvec(permutation, expected_load, field)
        numbered_support = _matmul(expected_support, _transpose(permutation), field)
        numbered_physical = _matmul(numbered_t5, _transpose(numbered_t5), field)
        numbered_drill_projector = _matmul(numbered_qd, _transpose(numbered_qd), field)
        projectors_exact = (
            _equal(
                numbered_physical,
                _matmul(_matmul(permutation, expected_physical, field), _transpose(permutation), field),
            )
            and _equal(
                numbered_drill_projector,
                _matmul(_matmul(permutation, expected_drill_projector, field), _transpose(permutation), field),
            )
        )
        local_numbered_load = _matvec(_transpose(numbered_t5), numbered_load, field)
        load_case_exact = (
            _vector_equal(_matvec(numbered_t5, local_numbered_load, field), numbered_load)
            and _all_zero_vector(_matvec(_transpose(numbered_qd), numbered_load, field), field)
        )
        support_case_admissible = _all_zero(
            _matmul(numbered_support, numbered_qd, field), field
        )
        selector = _matmul(numbered_support, numbered_t5, field)
        support_case_factorization = _equal(
            numbered_support, _matmul(selector, _transpose(numbered_t5), field)
        )
        numbered_reaction = _matvec(permutation, expected_reaction, field)
        reaction_case_exact = _vector_equal(
            numbered_reaction,
            _matvec(_transpose(numbered_support), expected_multiplier, field),
        )
        reaction_case_drill_free = _all_zero_vector(
            _matvec(_transpose(numbered_qd), numbered_reaction, field), field
        )
        numbered_zero_solution = [field.zero for _ in range(24)]
        equilibrium_case = _all_zero_vector(
            _vector_sub(
                [
                    stiffness + reaction
                    for stiffness, reaction in zip(
                        _matvec(numbered_global_k, numbered_zero_solution, field),
                        numbered_reaction,
                        strict=True,
                    )
                ],
                numbered_load,
            ),
            field,
        )
        constraint_case = _all_zero_vector(
            _matvec(numbered_support, numbered_zero_solution, field), field
        )
        drill_map = _matmul(_matmul(_transpose(numbered_qd), permutation, field), expected_qd, field)
        numbered_drill = _matmul(
            _matmul(_transpose(numbered_qd), numbered_global_k, field), numbered_qd, field
        )
        numbered_drill_inverse = _matmul(
            _matmul(drill_map, base["drill_inverse"], field), _transpose(drill_map), field
        )
        unique = (
            _equal(_matmul(numbered_drill, numbered_drill_inverse, field), identity4)
            and _equal(_matmul(numbered_drill_inverse, numbered_drill, field), identity4)
        )
        numbered_virtual = _matvec(permutation, base["virtual"], field)
        virtual_case = _dot(numbered_reaction, numbered_virtual, field) == _dot(
            expected_multiplier,
            _matvec(numbered_support, numbered_virtual, field),
            field,
        )
        values = {
            "covariance_exact": covariance_exact,
            "kkt_constraint_exact": constraint_case,
            "kkt_equilibrium_exact": equilibrium_case,
            "kkt_unique": unique,
            "load_exact": load_case_exact,
            "numerical_reaction_separate": reaction_case_drill_free,
            "projectors_exact": projectors_exact,
            "reaction_drill_free": reaction_case_drill_free,
            "reaction_exact": reaction_case_exact,
            "support_admissible": support_case_admissible,
            "support_factorization_exact": support_case_factorization,
            "virtual_work_exact": virtual_case,
        }
        actual_cases.append(values)
        if not all((load_case_exact, projectors_exact, support_case_admissible, support_case_factorization, reaction_case_drill_free, virtual_case)):
            support_boundary_contradictions.append(case_id)
        if not all((constraint_case, equilibrium_case, unique, reaction_case_exact)):
            kkt_contradictions.append(case_id)
        if not covariance_exact:
            covariance_contradictions.append(case_id)

    documents["_active_field"] = proof["field"]
    proper = _proper_certificate(
        geometry_id,
        geometry,
        q1y3_evidence_root,
        root,
        contract,
        documents,
        field,
        decoder,
        local_k,
        expected_frame,
        expected_t5,
        expected_qd,
        expected_load,
        expected_support,
        expected_reaction,
        expected_drill,
        operations,
    )
    proper_global_exact = all(value for key, value in proper.items() if key != "applicable")
    if not proper_global_exact:
        covariance_contradictions.append(f"{geometry_id}::PROPER_GLOBAL")

    claimed_cases = [_case_claims(record) for record in proof["case_records"]]
    proof_disagreement = (
        not base_witness_exact
        or claimed_cases != actual_cases
        or proof["proper_global"] != proper
    )
    return {
        "base_support_system_count": 1,
        "case_count": 8,
        "exact_kkt_reaction_contradictions": list(dict.fromkeys(kkt_contradictions)),
        "exact_support_boundary_contradictions": list(
            dict.fromkeys(support_boundary_contradictions)
        ),
        "exact_support_covariance_contradictions": list(
            dict.fromkeys(covariance_contradictions)
        ),
        "geometry_id": geometry_id,
        "proper_global_exact": proper_global_exact,
        "proof_disagreement": proof_disagreement,
        "schema": CHECK_SCHEMA,
        "support_proof_sha256": wrapper["proof_sha256"],
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-support-proof", action="store_true", required=True)
    parser.add_argument("--repository-root", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--contract-sha256", required=True)
    parser.add_argument("--q1y3-evidence-root", type=Path, required=True)
    parser.add_argument("--proof", type=Path, required=True)
    parser.add_argument("--environment-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        result = verify_proof(
            repository_root=args.repository_root,
            contract_path=args.contract,
            contract_sha256=args.contract_sha256,
            q1y3_evidence_root=args.q1y3_evidence_root,
            proof_path=args.proof,
            environment_root=args.environment_root,
        )
        q1z.write_exclusive(args.output, q1z.canonical_bytes(result))
        return 0
    except (KeyError, OSError, TypeError, ValueError, ZeroDivisionError, q1z.Q1ZError) as exc:
        print(f"BLOCKED_E4_PL_Q1Z_PROOF_OR_REVIEW: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
