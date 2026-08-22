"""Independently check a Q1X geometry proof with SymPy algebraic domains."""

from __future__ import annotations

import argparse
from fractions import Fraction
import re
import sys
import time
from pathlib import Path
from typing import Any, Iterable, Sequence

from e4_pl_q1x_common import (
    CHECK_SCHEMA,
    GAUSS_IDS,
    GEOMETRY_IDS,
    OPERATION_IDS,
    PATCH_IDS,
    PROOF_SCHEMA,
    PROOF_WRAPPER_SCHEMA,
    Q1XError,
    canonical_bytes,
    read_json,
    sha256,
    validate_contract,
    validate_environment,
    verify_file,
    write_exclusive,
)


def F(value: Any = 0) -> Fraction:
    if isinstance(value, Fraction):
        return value
    if isinstance(value, int):
        return Fraction(value)
    if isinstance(value, str):
        return Fraction(value)
    raise Q1XError(f"invalid rational token: {value!r}")


def _fraction_matrix(values: Sequence[Sequence[Any]]) -> list[list[Fraction]]:
    return [[F(value) for value in row] for row in values]


def _transpose(matrix: Sequence[Sequence[Any]]) -> list[list[Any]]:
    return [list(row) for row in zip(*matrix, strict=True)]


def _dot(left: Sequence[Any], right: Sequence[Any], zero: Any) -> Any:
    return sum((a * b for a, b in zip(left, right, strict=True)), zero)


def _matvec(matrix: Sequence[Sequence[Any]], vector: Sequence[Any], zero: Any) -> list[Any]:
    return [_dot(row, vector, zero) for row in matrix]


def _matmul(left: Sequence[Sequence[Any]], right: Sequence[Sequence[Any]], zero: Any) -> list[list[Any]]:
    columns = _transpose(right)
    return [[_dot(row, column, zero) for column in columns] for row in left]


def _cross(left: Sequence[Any], right: Sequence[Any]) -> list[Any]:
    return [
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    ]


def _matrix_equal(left: Sequence[Sequence[Any]], right: Sequence[Sequence[Any]]) -> bool:
    return len(left) == len(right) and all(
        len(a) == len(b) and all(x == y for x, y in zip(a, b, strict=True))
        for a, b in zip(left, right, strict=True)
    )


def _inverse(matrix: Sequence[Sequence[Fraction]]) -> list[list[Fraction]]:
    size = len(matrix)
    rows = [list(row) + [Fraction(int(i == j)) for j in range(size)] for i, row in enumerate(matrix)]
    for column in range(size):
        pivot = next((row for row in range(column, size) if rows[row][column]), None)
        if pivot is None:
            raise Q1XError("singular independently reconstructed D4 map")
        rows[column], rows[pivot] = rows[pivot], rows[column]
        divisor = rows[column][column]
        rows[column] = [value / divisor for value in rows[column]]
        for row in range(size):
            if row != column:
                factor = rows[row][column]
                rows[row] = [a - factor * b for a, b in zip(rows[row], rows[column], strict=True)]
    return [row[size:] for row in rows]


def _geometry_rows(contract: dict[str, Any]) -> dict[str, list[list[Fraction]]]:
    rows = {str(row["id"]): _fraction_matrix(row["nodes"]) for row in contract["geometries"]}
    transform = contract["global_transform"]
    rows[str(transform["id"])] = _fraction_matrix(transform["derived_nodes"])
    return rows


def _domain_fraction(domain: Any, sympy: Any, value: Fraction) -> Any:
    return domain.convert(sympy.QQ(value.numerator, value.denominator))


def _basis_expression(coefficients: Sequence[Any], roots: Sequence[Any], sympy: Any) -> Any:
    result = sympy.Rational(0)
    for mask, raw in enumerate(coefficients):
        coefficient = F(raw)
        term = sympy.Rational(coefficient.numerator, coefficient.denominator)
        for index, root in enumerate(roots):
            if mask & (1 << index):
                term *= root
        result += term
    return result


def _evaluate_dag(node: dict[str, Any], sympy: Any) -> Any:
    operation = node.get("operation")
    if operation == "rational" and set(node) == {"denominator", "numerator", "operation"}:
        return sympy.Rational(int(node["numerator"]), int(node["denominator"]))
    if operation in ("add", "multiply") and set(node) == {"arguments", "operation"} and len(node["arguments"]) == 2:
        left = _evaluate_dag(node["arguments"][0], sympy)
        right = _evaluate_dag(node["arguments"][1], sympy)
        return left + right if operation == "add" else left * right
    if operation == "positive_sqrt" and set(node) == {"arguments", "operation"} and len(node["arguments"]) == 1:
        return sympy.sqrt(_evaluate_dag(node["arguments"][0], sympy))
    raise Q1XError("expression DAG is outside the rational/positive-root grammar")


def _domain_rational(domain: Any, sympy: Any, value: Any) -> Any:
    rational = F(value)
    return domain.convert(sympy.QQ(rational.numerator, rational.denominator))


def _basis_element(coefficients: Sequence[Any], roots: Sequence[Any], domain: Any, sympy: Any) -> Any:
    result = domain.zero
    for mask, raw in enumerate(coefficients):
        term = _domain_rational(domain, sympy, raw)
        for index, root in enumerate(roots):
            if mask & (1 << index):
                term *= root
        result += term
    return result


def _dag_element(node: dict[str, Any], roots: Sequence[Any], domain: Any, sympy: Any) -> Any:
    operation = node.get("operation")
    if operation == "rational" and set(node) == {"denominator", "numerator", "operation"}:
        return domain.convert(sympy.QQ(int(node["numerator"]), int(node["denominator"])))
    if operation in ("add", "multiply") and set(node) == {"arguments", "operation"} and len(node["arguments"]) == 2:
        left = _dag_element(node["arguments"][0], roots, domain, sympy)
        right = _dag_element(node["arguments"][1], roots, domain, sympy)
        return left + right if operation == "add" else left * right
    if operation == "positive_sqrt" and set(node) == {"arguments", "operation"} and len(node["arguments"]) == 1:
        radicand = _dag_element(node["arguments"][0], roots, domain, sympy)
        candidate = next((root for root in roots if root * root == radicand), None)
        if candidate is not None:
            return candidate
    raise Q1XError("radicand DAG is outside the exact rational grammar")


def _build_domain(
    field_record: dict[str, Any],
    nodes: Sequence[Sequence[Fraction]],
    primitive_record: dict[str, Any],
    sympy: Any,
) -> tuple[Any, list[Any], list[Any], list[Any]]:
    if set(field_record) != {"dimension", "formal_degree_limit", "generators", "schedule"}:
        raise Q1XError("proof field schema mismatch")
    generators = field_record["generators"]
    if not isinstance(generators, list) or len(generators) > 5 or field_record["dimension"] != 1 << len(generators):
        raise Q1XError("proof field dimension mismatch")
    if field_record["formal_degree_limit"] != 32:
        raise Q1XError("formal degree authority mismatch")
    polynomial_coefficients = primitive_record["minimal_polynomial_coefficients"]
    representations = primitive_record["root_representations"]
    linear_combination = primitive_record["linear_combination"]
    if not isinstance(polynomial_coefficients, list) or not isinstance(representations, list) or len(representations) != len(generators):
        raise Q1XError("primitive field table shape mismatch")
    x = sympy.Symbol("x")
    polynomial = sympy.Poly.from_list([sympy.QQ(F(value).numerator, F(value).denominator) for value in polynomial_coefficients], gens=x, domain=sympy.QQ)
    seed_domain = sympy.QQ.alg_field_from_poly(polynomial)
    # Keep the checker contract explicit: the operational domain is created
    # through QQ.algebraic_field, with a single precomputed primitive element.
    domain = sympy.QQ.algebraic_field(seed_domain.ext)
    degree = len(polynomial_coefficients) - 1
    roots = []
    for representation in representations:
        if not isinstance(representation, list) or len(representation) != degree:
            raise Q1XError("primitive generator representation dimension mismatch")
        roots.append(domain.new([sympy.QQ(F(value).numerator, F(value).denominator) for value in representation]))
    theta = domain.new([sympy.QQ.one, sympy.QQ.zero])
    combined = sum(
        (_domain_rational(domain, sympy, coefficient) * root for coefficient, root in zip(linear_combination, roots, strict=True)),
        domain.zero,
    )
    if combined != theta:
        raise Q1XError("primitive field linear-combination identity mismatch")
    prior_roots: list[Any] = []
    for index, (row, root) in enumerate(zip(generators, roots, strict=True)):
        if set(row) != {"id", "radicand_coefficients", "radicand_dag", "root_dag"} or row["id"] != f"alpha_{index + 1}":
            raise Q1XError("field generator schema/order mismatch")
        coefficients = row["radicand_coefficients"]
        if not isinstance(coefficients, list) or len(coefficients) != 1 << index:
            raise Q1XError("field radicand basis dimension mismatch")
        radicand = _basis_element(coefficients, prior_roots, domain, sympy)
        if _dag_element(row["radicand_dag"], prior_roots, domain, sympy) != radicand:
            raise Q1XError("radicand DAG mismatch")
        root_dag = row["root_dag"]
        if set(root_dag) != {"arguments", "operation"} or root_dag["operation"] != "positive_sqrt" or len(root_dag["arguments"]) != 1:
            raise Q1XError("positive-root DAG mismatch")
        if _dag_element(root_dag["arguments"][0], prior_roots, domain, sympy) != radicand or root * root != radicand:
            raise Q1XError("primitive generator square identity mismatch")
        prior_roots.append(root)

    schedule = field_record["schedule"]
    if not isinstance(schedule, list) or [row.get("id") for row in schedule] != ["g1", "g2", "g3", "g4", "g5"]:
        raise Q1XError("generator schedule mismatch")
    schedule_values = [_basis_element(row["root_coefficients"], roots, domain, sympy) for row in schedule]
    rational_nodes = [[_domain_fraction(domain, sympy, value) for value in row] for row in nodes]
    d1 = [rational_nodes[2][i] - rational_nodes[0][i] for i in range(3)]
    d2 = [rational_nodes[1][i] - rational_nodes[3][i] for i in range(3)]
    g1, g2, g3, g4, g5 = schedule_values
    a = [value / g1 for value in d1]
    b = [value / g2 for value in d2]
    plus = [x + y for x, y in zip(a, b, strict=True)]
    if not (
        g1 * g1 == _dot(d1, d1, domain.zero)
        and g2 * g2 == _dot(d2, d2, domain.zero)
        and g3 * g3 == _dot(plus, plus, domain.zero)
        and g4 * g4 == _dot(_cross(d1, d2), _cross(d1, d2), domain.zero)
        and g5 * g5 == _domain_fraction(domain, sympy, F(3))
    ):
        raise Q1XError("generator schedule square identity mismatch")
    basis: list[Any] = []
    for mask in range(1 << len(roots)):
        value = domain.one
        for index, root in enumerate(roots):
            if mask & (1 << index):
                value *= root
        basis.append(value)
    return domain, roots, schedule_values, basis


def _token_element(values: Sequence[Any], basis: Sequence[Any], domain: Any, sympy: Any) -> Any:
    if len(values) != len(basis):
        raise Q1XError("algebraic token dimension mismatch")
    return sum(
        (_domain_rational(domain, sympy, coefficient) * monomial for coefficient, monomial in zip(values, basis, strict=True)),
        domain.zero,
    )


def _token_vector(values: Sequence[Sequence[Any]], basis: Sequence[Any], domain: Any, sympy: Any) -> list[Any]:
    return [_token_element(value, basis, domain, sympy) for value in values]


def _token_matrix(values: Sequence[Sequence[Sequence[Any]]], basis: Sequence[Any], domain: Any, sympy: Any) -> list[list[Any]]:
    return [_token_vector(row, basis, domain, sympy) for row in values]


def _frame_and_coords(
    nodes: Sequence[Sequence[Fraction]],
    node_tuple: Sequence[int],
    domain: Any,
    sympy: Any,
    schedule: Sequence[Any],
) -> tuple[list[list[Any]], list[list[Any]], list[list[Any]]]:
    rational = [[_domain_fraction(domain, sympy, value) for value in row] for row in nodes]
    numbered = [rational[int(index) - 1] for index in node_tuple]
    d1 = [numbered[2][i] - numbered[0][i] for i in range(3)]
    d2 = [numbered[1][i] - numbered[3][i] for i in range(3)]

    g1, g2, g3, g4, _ = schedule

    def diagonal_norm(vector: Sequence[Any]) -> Any:
        square = _dot(vector, vector, domain.zero)
        candidate = next((value for value in (g1, g2) if value * value == square), None)
        if candidate is None:
            raise Q1XError("numbered diagonal norm is outside the E schedule")
        return candidate

    root1 = diagonal_norm(d1)
    root2 = diagonal_norm(d2)
    a = [value / root1 for value in d1]
    b = [value / root2 for value in d2]
    plus = [x + y for x, y in zip(a, b, strict=True)]
    minus = [x - y for x, y in zip(a, b, strict=True)]
    plus_square = _dot(plus, plus, domain.zero)
    complement = 2 * g4 / (g1 * g2 * g3)
    t1_norm = g3 if g3 * g3 == plus_square else complement if complement * complement == plus_square else None
    if t1_norm is None:
        raise Q1XError("numbered first tangent norm is outside the E schedule")
    t2_norm = 2 * g4 / (root1 * root2 * t1_norm)
    if t2_norm * t2_norm != _dot(minus, minus, domain.zero):
        raise Q1XError("numbered second tangent norm identity mismatch")
    t1 = [value / t1_norm for value in plus]
    t2 = [value / t2_norm for value in minus]
    t3 = _cross(t1, t2)
    frame = [[t1[row], t2[row], t3[row]] for row in range(3)]
    centre = [sum((node[i] for node in numbered), domain.zero) / 4 for i in range(3)]
    coords = [[_dot([node[i] - centre[i] for i in range(3)], t1, domain.zero), _dot([node[i] - centre[i] for i in range(3)], t2, domain.zero)] for node in numbered]
    return numbered, frame, coords


def _maps(operation: dict[str, Any]) -> dict[str, list[list[Fraction]]]:
    (a, b), (c, d) = _fraction_matrix(operation["A"])
    determinant = F(operation["det"])
    return {
        "C_eng": [[a * a, b * b, a * b], [c * c, d * d, c * d], [2 * a * c, 2 * b * d, a * d + b * c]],
        "C_res": [[a * a, b * b, 2 * a * b], [c * c, d * d, 2 * c * d], [a * c, b * d, a * d + b * c]],
        "multiplier": [[determinant, 0, 0], [0, determinant * a, determinant * b], [0, determinant * c, determinant * d]],
        "pseudo_vector": [[determinant * a, determinant * b], [determinant * c, determinant * d]],
    }


def _patches(coords: Sequence[Sequence[Any]], domain: Any, sympy: Any) -> dict[str, list[Any]]:
    result = {patch_id: [] for patch_id in PATCH_IDS}
    q = lambda value: _domain_fraction(domain, sympy, F(value))
    for x, y in coords:
        zero = domain.zero
        u = 2 * x + y / 3
        v = -2 * x / 5 + 4 * y / 3
        td = q("-11/30")
        w = -x * x / 5 + y * y / 6 - 3 * x * y / 14
        bend_tx = y / 3 - 3 * x / 14
        bend_ty = 2 * x / 5 + 3 * y / 14
        shear_tx = q("1/4")
        shear_ty = q("2/3")
        result["MEMBRANE_PATCH"].extend((u, v, zero, zero, zero, td))
        result["BENDING_PATCH"].extend((zero, zero, w, bend_tx, bend_ty, zero))
        result["SHEAR_PATCH"].extend((zero, zero, zero, shear_tx, shear_ty, zero))
        result["COMBINED_PHYSICAL_PATCH"].extend((u, v, w, bend_tx + shear_tx, bend_ty + shear_ty, td))
    return result


def _transport_patch(base: Sequence[Any], operation: dict[str, Any], domain: Any, sympy: Any) -> list[Any]:
    a = _fraction_matrix(operation["A"])
    determinant = F(operation["det"])
    ahat = [
        [_domain_fraction(domain, sympy, value) for value in row]
        for row in ((a[0][0], a[0][1], 0), (a[1][0], a[1][1], 0), (0, 0, determinant))
    ]
    local_map = _transpose(ahat)
    result: list[Any] = []
    for old in operation["node_tuple"]:
        block = base[6 * (int(old) - 1) : 6 * int(old)]
        result.extend(_matvec(local_map, block[:3], domain.zero))
        result.extend(_matvec(local_map, block[3:], domain.zero))
    return result


def _normalise_historical(row: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {"station_id": row["station_id"]}
    for key, length in (("compatible", 8), ("independent", 8), ("N", 3), ("M", 3), ("Q", 2)):
        if not isinstance(row.get(key), list) or len(row[key]) != length:
            raise Q1XError("historical recovery shape mismatch")
        result[key] = []
        for token in row[key]:
            if not isinstance(token, list) or any(F(value) for value in token[1:]):
                raise Q1XError("historical local recovery is not rational")
            result[key].append(fs(F(token[0])))
    return result


def fs(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def _expected(operation: dict[str, Any], material: dict[str, Any]) -> dict[str, list[Fraction]]:
    maps = _maps(operation)
    determinant = F(operation["det"])
    eps = _matvec(_inverse(maps["C_eng"]), [F(2), F("4/3"), F("-1/15")], Fraction())
    kap = [determinant * value for value in _matvec(_inverse(maps["C_eng"]), [F("2/5"), F("-1/3"), F("3/7")], Fraction())]
    shear = _matvec(_inverse(maps["pseudo_vector"]), [F("2/3"), F("-1/4")], Fraction())
    constitutive = material["constitutive"]
    membrane = _fraction_matrix(constitutive["membrane_A"])
    bending = _fraction_matrix(constitutive["bending_D"])
    transverse = _fraction_matrix(constitutive["transverse_shear_A_s"])
    return {
        "M": _matvec(bending, kap, Fraction()),
        "N": _matvec(membrane, eps, Fraction()),
        "Q": _matvec(transverse, shear, Fraction()),
        "strain": eps + kap + shear,
    }


def _residual_paths(rows: Sequence[dict[str, Any]], expected: dict[str, list[Fraction]]) -> list[str]:
    result: list[str] = []
    for row in rows:
        for key, target in (("compatible", "strain"), ("independent", "strain"), ("N", "N"), ("M", "M"), ("Q", "Q")):
            result.extend(
                f"{row['station_id']}.{key}[{index}]"
                for index, (actual, wanted) in enumerate(zip(row[key], expected[target], strict=True))
                if F(actual) - wanted
            )
    return result


def _parse_natural(value: str, domain: Any, sympy: Any, sqrt3: Any) -> Any:
    match = re.fullmatch(r"(-?\d+)\*sqrt\(3\)/3", value)
    if not match:
        raise Q1XError("natural coordinate is outside the frozen grammar")
    return domain.convert(sympy.QQ(int(match.group(1)), 3)) * sqrt3


def verify_geometry_proof(
    *,
    repository_root: Path,
    contract_path: Path,
    contract_sha256: str,
    historical_reference: Path,
    historical_reference_sha256: str,
    proof_path: Path,
    environment_root: Path,
) -> dict[str, Any]:
    started = time.monotonic()

    def progress(phase: str, **extra: Any) -> None:
        sys.stderr.buffer.write(
            canonical_bytes({"elapsed_ms": int((time.monotonic() - started) * 1000), "phase": phase, **extra})
        )
        sys.stderr.buffer.flush()

    contract = validate_contract(repository_root, contract_path, contract_sha256)
    historical = contract["historical_reference"]
    verify_file(historical_reference, size=int(historical["bytes"]), digest=historical_reference_sha256)
    if historical_reference_sha256.upper() != historical["sha256"]:
        raise Q1XError("checker historical authority mismatch")
    validate_environment(repository_root, environment_root, contract)
    sys.path.insert(0, str(environment_root.resolve(strict=True)))
    try:
        import sympy  # type: ignore[import-not-found]
    except ImportError as exc:
        raise Q1XError("frozen SymPy environment is unavailable") from exc
    if sympy.__version__ != "1.14.0":
        raise Q1XError("SymPy version mismatch")
    progress("AUTHORITY_AND_ENVIRONMENT_VALIDATED")
    proof_raw, wrapper = read_json(proof_path)
    if set(wrapper) != {"proof", "proof_sha256", "schema"} or wrapper["schema"] != PROOF_WRAPPER_SCHEMA:
        raise Q1XError("proof wrapper schema mismatch")
    proof = wrapper["proof"]
    if proof.get("schema") != PROOF_SCHEMA or sha256(canonical_bytes(proof)) != wrapper["proof_sha256"]:
        raise Q1XError("proof body identity mismatch")
    geometry_id = proof.get("geometry_id")
    if geometry_id not in GEOMETRY_IDS:
        raise Q1XError("proof geometry identity mismatch")
    if proof.get("frozen_inputs") != contract["frozen_inputs"] or proof.get("producer_scope") != contract["scope"]:
        raise Q1XError("proof authority/scope mismatch")
    if proof.get("historical_reference") != {
        "bytes": historical["bytes"],
        "certificate_payload_sha256": historical["certificate_payload_sha256"],
        "role": historical["role"],
        "sha256": historical["sha256"],
    }:
        raise Q1XError("proof historical binding mismatch")
    root = repository_root.resolve(strict=True)
    geometry_contract = read_json(root / "docs/reference_cases/e4_pl_q1r_geometry_contract.json")[1]
    frame_contract = read_json(root / "docs/reference_cases/e4_pl_q1r_frame_contract.json")[1]
    material = read_json(root / "docs/reference_cases/e4_pl_q1r_material_contract.json")[1]
    primitive_table = read_json(root / contract["primitive_field_table"]["path"])[1]
    if set(primitive_table) != {"fields", "schema"} or primitive_table["schema"] != contract["primitive_field_table"]["schema"]:
        raise Q1XError("primitive field table schema mismatch")
    primitive_rows = primitive_table["fields"]
    if not isinstance(primitive_rows, list) or sorted(item for row in primitive_rows for item in row.get("geometry_ids", [])) != sorted(GEOMETRY_IDS):
        raise Q1XError("primitive field geometry coverage mismatch")
    primitive_record = next((row for row in primitive_rows if geometry_id in row["geometry_ids"]), None)
    if primitive_record is None or set(primitive_record) != {
        "geometry_ids",
        "linear_combination",
        "minimal_polynomial_coefficients",
        "root_representations",
    }:
        raise Q1XError("primitive field row schema mismatch")
    nodes = _geometry_rows(geometry_contract)[geometry_id]
    domain, roots, schedule, basis = _build_domain(proof["exact_field"], nodes, primitive_record, sympy)
    progress("PRIMITIVE_FIELD_CONSTRUCTED", geometry_id=geometry_id)
    _, base_frame, base_coords = _frame_and_coords(nodes, (1, 2, 3, 4), domain, sympy, schedule)
    base_patches = _patches(base_coords, domain, sympy)
    if not _matrix_equal(_token_matrix(proof["base_frame"], basis, domain, sympy), base_frame):
        raise Q1XError("base frame mismatch")
    historical_wrapper = read_json(historical_reference)[1]
    historical_cases = {str(row["id"]): row for row in historical_wrapper["implementation_diagnostics"]["cases"]}
    cases = proof["cases"]
    if not isinstance(cases, list) or [row.get("operation_id") for row in cases] != list(OPERATION_IDS):
        raise Q1XError("proof operation inventory mismatch")
    checks = {
        "field_schedule_exact": True,
        "frames_exact": True,
        "global_transform_exact": True,
        "historical_payload_bound": True,
        "maps_exact": True,
        "nodes_exact": True,
        "patch_vectors_exact": True,
        "recovery_exact": True,
        "station_correspondence_exact": True,
        "work_exact": True,
        "wrapper_canonical": proof_raw == canonical_bytes(wrapper),
    }
    contradiction_cases: list[str] = []
    legacy_diagnostic_count = 0
    operations = {str(row["id"]): row for row in frame_contract["d4"]["operations"]}
    for case in cases:
        operation_id = str(case["operation_id"])
        operation = operations[operation_id]
        case_id = f"{geometry_id}::{operation_id}"
        if case.get("case_id") != case_id or case.get("node_tuple") != operation["node_tuple"]:
            raise Q1XError("case identity/permutation mismatch")
        numbered, frame, coords = _frame_and_coords(nodes, operation["node_tuple"], domain, sympy, schedule)
        proof_nodes = _token_matrix(case["nodes"], basis, domain, sympy)
        proof_frame = _token_matrix(case["frame"], basis, domain, sympy)
        proof_coords = _token_matrix(case["source_coordinates"], basis, domain, sympy)
        checks["nodes_exact"] = checks["nodes_exact"] and _matrix_equal(proof_nodes, numbered)
        checks["frames_exact"] = checks["frames_exact"] and _matrix_equal(proof_frame, frame)
        checks["station_correspondence_exact"] = checks["station_correspondence_exact"] and _matrix_equal(proof_coords, coords)
        a = _fraction_matrix(operation["A"])
        determinant = F(operation["det"])
        ahat = [[_domain_fraction(domain, sympy, value) for value in row] for row in ((a[0][0], a[0][1], 0), (a[1][0], a[1][1], 0), (0, 0, determinant))]
        expected_numbered_frame = _matmul(base_frame, ahat, domain.zero)
        frame_residuals = [frame[i][j] - expected_numbered_frame[i][j] for i in range(3) for j in range(3)]
        proof_frame_residuals = _token_vector(case["frame_transport_residuals"], basis, domain, sympy)
        checks["frames_exact"] = checks["frames_exact"] and proof_frame_residuals == frame_residuals
        maps = _maps(operation)
        checks["maps_exact"] = checks["maps_exact"] and all(_fraction_matrix(case["field_maps"][key]) == value for key, value in maps.items())
        progress("CASE_FRAME_AND_MAPS_CHECKED", case_id=case_id)
        patch_rows = case["patch_vectors"]
        if [row.get("field_id") for row in patch_rows] != list(PATCH_IDS):
            raise Q1XError("patch vector inventory mismatch")
        for patch_row in patch_rows:
            base_patch = base_patches[patch_row["field_id"]]
            target_patch = _transport_patch(base_patch, operation, domain, sympy)
            checks["patch_vectors_exact"] = checks["patch_vectors_exact"] and _token_vector(patch_row["base_local"], basis, domain, sympy) == base_patch
            checks["patch_vectors_exact"] = checks["patch_vectors_exact"] and _token_vector(patch_row["numbered_local"], basis, domain, sympy) == target_patch
        progress("CASE_PATCHES_CHECKED", case_id=case_id)
        historical_rows = [_normalise_historical(row) for row in historical_cases[case_id]["recovery"]["rows"]]
        proof_rows = case["stations"]
        if [row.get("station_id") for row in proof_rows] != list(GAUSS_IDS):
            raise Q1XError("station inventory mismatch")
        expected = _expected(operation, material)
        legacy = _expected({"A": [[1, 0], [0, 1]], "det": 1}, material)
        signs = {"GP_MM": (-1, -1), "GP_PM": (1, -1), "GP_PP": (1, 1), "GP_MP": (-1, 1)}
        for proof_row, actual_row in zip(proof_rows, historical_rows, strict=True):
            checks["recovery_exact"] = checks["recovery_exact"] and all(proof_row[key] == actual_row[key] for key in ("compatible", "independent", "N", "M", "Q"))
            r_sign, s_sign = signs[proof_row["station_id"]]
            numbered_natural = [_parse_natural(value, domain, sympy, schedule[4]) for value in proof_row["numbered_natural_coordinates"]]
            base_natural = [_parse_natural(value, domain, sympy, schedule[4]) for value in proof_row["base_natural_coordinates"]]
            mapped = [
                _domain_fraction(domain, sympy, a[i][0]) * numbered_natural[0] + _domain_fraction(domain, sympy, a[i][1]) * numbered_natural[1]
                for i in range(2)
            ]
            checks["station_correspondence_exact"] = checks["station_correspondence_exact"] and base_natural == mapped
            expected_tokens = {key: [fs(value) for value in values] for key, values in expected.items()}
            if proof_row["expected_transported"] != expected_tokens:
                raise Q1XError("expected transported field values mismatch")
            transported = {
                field: [fs(F(actual) - wanted) for actual, wanted in zip(actual_row[field], expected[target], strict=True)]
                for field, target in (("compatible", "strain"), ("independent", "strain"), ("N", "N"), ("M", "M"), ("Q", "Q"))
            }
            legacy_residual = {
                field: [fs(F(actual) - wanted) for actual, wanted in zip(actual_row[field], legacy[target], strict=True)]
                for field, target in (("compatible", "strain"), ("independent", "strain"), ("N", "N"), ("M", "M"), ("Q", "Q"))
            }
            if proof_row["transport_residuals"] != transported or proof_row["legacy_untransformed_residuals"] != legacy_residual:
                raise Q1XError("proof residual serialization mismatch")
        residual_paths = _residual_paths(historical_rows, expected)
        residual_paths += [f"frame[{index}]" for index, value in enumerate(frame_residuals) if value != domain.zero]
        if case["exact_nonzero_transport_residuals"] != residual_paths:
            raise Q1XError("case contradiction index mismatch")
        if residual_paths:
            contradiction_cases.append(case_id)
        legacy_paths = _residual_paths(historical_rows, legacy)
        if case["legacy_untransformed_nonzero_residuals"] != legacy_paths:
            raise Q1XError("legacy diagnostic index mismatch")
        legacy_diagnostic_count += len(legacy_paths)
        progress("CASE_RECOVERY_CHECKED", case_id=case_id)
        base_expected = _expected({"A": [[1, 0], [0, 1]], "det": 1}, material)
        base_work = sum(a0 * b0 for a0, b0 in zip(base_expected["N"] + base_expected["M"] + base_expected["Q"], base_expected["strain"], strict=True))
        target_work = sum(a0 * b0 for a0, b0 in zip(expected["N"] + expected["M"] + expected["Q"], expected["strain"], strict=True))
        checks["work_exact"] = checks["work_exact"] and case["work"] == {"base": fs(base_work), "numbered": fs(target_work), "residual": fs(target_work - base_work)} and target_work == base_work
        progress("CASE_CHECKED", case_id=case_id)

    if geometry_id == "Q3_TAPERED_SKEW_RSTAR_TRANSLATED":
        global_record = proof["global_transform"]
        source_nodes = _geometry_rows(geometry_contract)["Q3_TAPERED_SKEW"]
        transform = geometry_contract["global_transform"]
        rotation_f = _fraction_matrix(transform["R_star"])
        translation = [F(value) for value in transform["b_star"]]
        rotation = [[_domain_fraction(domain, sympy, value) for value in row] for row in rotation_f]
        _, _, source_base_coords = _frame_and_coords(source_nodes, (1, 2, 3, 4), domain, sympy, schedule)
        _, _, target_base_coords = _frame_and_coords(nodes, (1, 2, 3, 4), domain, sympy, schedule)
        source_base_patch = _patches(source_base_coords, domain, sympy)["COMBINED_PHYSICAL_PATCH"]
        target_base_patch = _patches(target_base_coords, domain, sympy)["COMBINED_PHYSICAL_PATCH"]
        node_residuals: list[Fraction] = []
        for source, target in zip(source_nodes, nodes, strict=True):
            expected_node = [sum(rotation_f[i][j] * source[j] for j in range(3)) + translation[i] for i in range(3)]
            node_residuals.extend(target[i] - expected_node[i] for i in range(3))
        if global_record["node_residuals"] != [fs(value) for value in node_residuals]:
            raise Q1XError("global node residual mismatch")
        global_nonzero = [f"nodes[{index}]" for index, value in enumerate(node_residuals) if value]
        if [row.get("operation_id") for row in global_record["operations"]] != list(OPERATION_IDS):
            raise Q1XError("global operation inventory mismatch")
        for row in global_record["operations"]:
            operation_id = row["operation_id"]
            operation = operations[operation_id]
            _, source_frame, source_coords = _frame_and_coords(source_nodes, operation["node_tuple"], domain, sympy, schedule)
            _, target_frame, target_coords = _frame_and_coords(nodes, operation["node_tuple"], domain, sympy, schedule)
            expected_target_frame = _matmul(rotation, source_frame, domain.zero)
            frame_residuals = [target_frame[i][j] - expected_target_frame[i][j] for i in range(3) for j in range(3)]
            coordinate_residuals = [target_coords[i][j] - source_coords[i][j] for i in range(4) for j in range(2)]
            source_patch = _transport_patch(source_base_patch, operation, domain, sympy)
            target_patch = _transport_patch(target_base_patch, operation, domain, sympy)
            patch_residuals = [a - b for a, b in zip(target_patch, source_patch, strict=True)]
            source_rows = [_normalise_historical(item) for item in historical_cases[f"Q3_TAPERED_SKEW::{operation_id}"]["recovery"]["rows"]]
            target_rows = [_normalise_historical(item) for item in historical_cases[f"Q3_TAPERED_SKEW_RSTAR_TRANSLATED::{operation_id}"]["recovery"]["rows"]]
            recovery_residuals = {
                f"{GAUSS_IDS[station]}.{key}": [fs(F(a) - F(b)) for a, b in zip(target[key], source[key], strict=True)]
                for station, (source, target) in enumerate(zip(source_rows, target_rows, strict=True))
                for key in ("compatible", "independent", "N", "M", "Q")
            }
            nonzero = (
                [f"frame[{index}]" for index, value in enumerate(frame_residuals) if value != domain.zero]
                + [f"coordinates[{index}]" for index, value in enumerate(coordinate_residuals) if value != domain.zero]
                + [f"patch[{index}]" for index, value in enumerate(patch_residuals) if value != domain.zero]
                + [f"recovery.{name}[{index}]" for name, values in recovery_residuals.items() for index, value in enumerate(values) if F(value)]
            )
            if set(row) != {
                "coordinate_residuals",
                "exact_nonzero_residuals",
                "frame_residuals",
                "operation_id",
                "patch_residuals",
                "recovery_residuals",
            }:
                raise Q1XError("global operation record schema mismatch")
            if _token_vector(row["frame_residuals"], basis, domain, sympy) != frame_residuals:
                raise Q1XError("global frame residual mismatch")
            if _token_vector(row["coordinate_residuals"], basis, domain, sympy) != coordinate_residuals:
                raise Q1XError("global coordinate residual mismatch")
            if _token_vector(row["patch_residuals"], basis, domain, sympy) != patch_residuals:
                raise Q1XError("global patch residual mismatch")
            if row["recovery_residuals"] != recovery_residuals or row["exact_nonzero_residuals"] != nonzero:
                raise Q1XError("global recovery/index mismatch")
            global_nonzero.extend(f"{operation_id}.{path}" for path in nonzero)
            progress("GLOBAL_OPERATION_CHECKED", operation_id=operation_id)
        if global_record["exact_nonzero_residuals"] != global_nonzero:
            raise Q1XError("global contradiction index mismatch")
        if global_nonzero:
            contradiction_cases.append("Q3_TAPERED_SKEW_RSTAR_TRANSLATED::GLOBAL")
    elif proof["global_transform"] is not None:
        raise Q1XError("unexpected global transform record")

    if not all(checks.values()):
        raise Q1XError(f"independent exact checks failed: {sorted(key for key, value in checks.items() if not value)}")
    terminal = contract["terminals"]["exact_counterexample"] if contradiction_cases else contract["terminals"]["transport_closed_only"]
    return {
        "candidate_id": contract["candidate_id"],
        "case_count": 8,
        "checks": checks,
        "exact_counterexample_cases": contradiction_cases,
        "geometry_id": geometry_id,
        "legacy_untransformed_nonzero_residual_count": legacy_diagnostic_count,
        "production": contract["production"],
        "proof_sha256": wrapper["proof_sha256"],
        "q1b_execution": contract["q1b_execution"],
        "schema": CHECK_SCHEMA,
        "station_count": 32,
        "study_id": contract["study_id"],
        "terminal": terminal,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-proof", action="store_true", required=True)
    parser.add_argument("--repository-root", type=Path, required=True)
    parser.add_argument("--transport-contract", type=Path, required=True)
    parser.add_argument("--transport-contract-sha256", required=True)
    parser.add_argument("--historical-reference", type=Path, required=True)
    parser.add_argument("--historical-reference-sha256", required=True)
    parser.add_argument("--proof", type=Path, required=True)
    parser.add_argument("--environment-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        value = verify_geometry_proof(
            repository_root=args.repository_root,
            contract_path=args.transport_contract,
            contract_sha256=args.transport_contract_sha256,
            historical_reference=args.historical_reference,
            historical_reference_sha256=args.historical_reference_sha256,
            proof_path=args.proof,
            environment_root=args.environment_root,
        )
        write_exclusive(args.output, canonical_bytes(value))
        return 0
    except (Q1XError, KeyError, TypeError, ValueError, OSError) as exc:
        print(f"BLOCKED_E4_PL_Q1X_PROOF_OR_REVIEW: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
