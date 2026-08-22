"""Independently verify one bounded Q1W exact proof with SymPy domains."""

from __future__ import annotations

import argparse
from fractions import Fraction
import re
import sys
import time
from pathlib import Path
from typing import Any, Iterable, Sequence

from e4_pl_q1w_common import (
    CHECK_SCHEMA,
    PROOF_SCHEMA,
    PROOF_WRAPPER_SCHEMA,
    Q1WError,
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
    raise Q1WError(f"invalid rational token: {value!r}")


def matvec(matrix: Sequence[Sequence[Fraction]], vector: Sequence[Fraction]) -> list[Fraction]:
    return [sum((a * b for a, b in zip(row, vector, strict=True)), Fraction()) for row in matrix]


def transpose(matrix: Sequence[Sequence[Any]]) -> list[list[Any]]:
    return [list(row) for row in zip(*matrix, strict=True)]


def inverse(matrix: Sequence[Sequence[Fraction]]) -> list[list[Fraction]]:
    size = len(matrix)
    rows = [list(row) + [Fraction(int(i == j)) for j in range(size)] for i, row in enumerate(matrix)]
    for column in range(size):
        pivot = next((row for row in range(column, size) if rows[row][column] != 0), None)
        if pivot is None:
            raise Q1WError("singular independently reconstructed field map")
        rows[column], rows[pivot] = rows[pivot], rows[column]
        divisor = rows[column][column]
        rows[column] = [value / divisor for value in rows[column]]
        for row in range(size):
            if row != column:
                factor = rows[row][column]
                rows[row] = [a - factor * b for a, b in zip(rows[row], rows[column], strict=True)]
    return [row[size:] for row in rows]


def _fraction_matrix(values: Sequence[Sequence[Any]]) -> list[list[Fraction]]:
    return [[F(value) for value in row] for row in values]


def _domain_fraction(domain: Any, sympy: Any, value: Fraction) -> Any:
    return domain.from_sympy(sympy.Rational(value.numerator, value.denominator))


def _domain_vector(domain: Any, sympy: Any, values: Iterable[Any]) -> list[Any]:
    return [_domain_fraction(domain, sympy, F(value)) for value in values]


def _dot(left: Sequence[Any], right: Sequence[Any], zero: Any) -> Any:
    return sum((a * b for a, b in zip(left, right, strict=True)), zero)


def _cross(left: Sequence[Any], right: Sequence[Any]) -> list[Any]:
    return [
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    ]


def _frame(nodes: Sequence[Sequence[Fraction]], domain: Any, sympy: Any) -> list[list[Any]]:
    vectors = [[_domain_fraction(domain, sympy, value) for value in node] for node in nodes]
    d1 = [vectors[2][i] - vectors[0][i] for i in range(3)]
    d2 = [vectors[1][i] - vectors[3][i] for i in range(3)]

    def norm(vector: Sequence[Any]) -> Any:
        square = _dot(vector, vector, domain.zero)
        return domain.from_sympy(sympy.sqrt(domain.to_sympy(square)))

    u1 = [value / norm(d1) for value in d1]
    u2 = [value / norm(d2) for value in d2]
    plus = [a + b for a, b in zip(u1, u2, strict=True)]
    minus = [a - b for a, b in zip(u1, u2, strict=True)]
    t1 = [value / norm(plus) for value in plus]
    t2 = [value / norm(minus) for value in minus]
    t3 = _cross(t1, t2)
    return [[t1[row], t2[row], t3[row]] for row in range(3)]


def _matrix_equal(left: Sequence[Sequence[Any]], right: Sequence[Sequence[Any]]) -> bool:
    return len(left) == len(right) and all(
        len(a) == len(b) and all(x == y for x, y in zip(a, b, strict=True))
        for a, b in zip(left, right, strict=True)
    )


def _matmul(left: Sequence[Sequence[Any]], right: Sequence[Sequence[Any]], zero: Any) -> list[list[Any]]:
    columns = transpose(right)
    return [[_dot(row, column, zero) for column in columns] for row in left]


def _maps(operation: dict[str, Any]) -> dict[str, list[list[Fraction]]]:
    (a, b), (c, d) = _fraction_matrix(operation["A"])
    det = F(operation["det"])
    return {
        "C_eng": [[a * a, b * b, a * b], [c * c, d * d, c * d], [2 * a * c, 2 * b * d, a * d + b * c]],
        "C_res": [[a * a, b * b, 2 * a * b], [c * c, d * d, 2 * c * d], [a * c, b * d, a * d + b * c]],
        "pseudo_vector": [[det * a, det * b], [det * c, det * d]],
        "multiplier": [[det, 0, 0], [0, det * a, det * b], [0, det * c, det * d]],
    }


def _base_patch() -> list[Fraction]:
    values: list[Fraction] = []
    for x_i, y_i in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        x, y = F(x_i), F(y_i)
        values.extend(
            (
                2 * x + y / 3,
                -2 * x / 5 + 4 * y / 3,
                -x * x / 5 + y * y / 6 - 3 * x * y / 14,
                y / 3 - 3 * x / 14 + F("1/4"),
                2 * x / 5 + 3 * y / 14 + F("2/3"),
                F("-11/30"),
            )
        )
    return values


def _numbered_patch(base: Sequence[Fraction], operation: dict[str, Any]) -> list[Fraction]:
    a = _fraction_matrix(operation["A"])
    det = F(operation["det"])
    ahat = [[a[0][0], a[0][1], 0], [a[1][0], a[1][1], 0], [0, 0, det]]
    local = transpose(ahat)
    result: list[Fraction] = []
    for old in operation["node_tuple"]:
        block = base[6 * (int(old) - 1) : 6 * int(old)]
        result.extend(matvec(local, block[:3]) + matvec(local, block[3:]))
    return result


def _expected(operation: dict[str, Any], material: dict[str, Any]) -> dict[str, list[Fraction]]:
    maps = _maps(operation)
    det = F(operation["det"])
    eps = matvec(inverse(maps["C_eng"]), [F(2), F("4/3"), F("-1/15")])
    kap = [det * value for value in matvec(inverse(maps["C_eng"]), [F("2/5"), F("-1/3"), F("3/7")])]
    shear = matvec(inverse(maps["pseudo_vector"]), [F("2/3"), F("-1/4")])
    constitutive = material["constitutive"]
    membrane = _fraction_matrix(constitutive["membrane_A"])
    bending = _fraction_matrix(constitutive["bending_D"])
    transverse = _fraction_matrix(constitutive["transverse_shear_A_s"])
    return {"strain": eps + kap + shear, "N": matvec(membrane, eps), "M": matvec(bending, kap), "Q": matvec(transverse, shear)}


def _residual_paths(stations: Sequence[dict[str, Any]], expected: dict[str, list[Fraction]]) -> list[str]:
    paths: list[str] = []
    for station in stations:
        for field, expected_key in (("compatible", "strain"), ("independent", "strain"), ("N", "N"), ("M", "M"), ("Q", "Q")):
            values = [F(value) for value in station[field]]
            for index, (actual, wanted) in enumerate(zip(values, expected[expected_key], strict=True)):
                if actual - wanted:
                    paths.append(f"{station['station_id']}.{field}[{index}]")
    return paths


def _residual_tokens(row: dict[str, Any], expected: dict[str, list[Fraction]]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for field, expected_key in (("compatible", "strain"), ("independent", "strain"), ("N", "N"), ("M", "M"), ("Q", "Q")):
        result[field] = []
        for actual, wanted in zip([F(value) for value in row[field]], expected[expected_key], strict=True):
            residual = actual - wanted
            result[field].append(
                str(residual.numerator)
                if residual.denominator == 1
                else f"{residual.numerator}/{residual.denominator}"
            )
    return result


def _parse_natural(value: str, domain: Any, sympy: Any) -> Any:
    match = re.fullmatch(r"(-?\d+)\*sqrt\(3\)/3", value)
    if not match:
        raise Q1WError("natural-coordinate expression is outside the frozen grammar")
    coefficient = int(match.group(1))
    return domain.from_sympy(sympy.Rational(coefficient, 3) * sympy.sqrt(3))


def verify_proof(
    *,
    repository_root: Path,
    contract_path: Path,
    contract_sha256: str,
    historical_reference: Path,
    historical_reference_sha256: str,
    proof_path: Path,
    environment_root: Path | None,
) -> dict[str, Any]:
    started = time.monotonic()
    contract = validate_contract(repository_root, contract_path, contract_sha256)
    historical = contract["historical_reference"]
    verify_file(historical_reference, size=int(historical["bytes"]), digest=historical_reference_sha256)
    if historical_reference_sha256.upper() != historical["sha256"]:
        raise Q1WError("checker historical-reference authority mismatch")
    proof_raw, wrapper = read_json(proof_path)
    if set(wrapper) != {"proof", "proof_sha256", "schema"} or wrapper["schema"] != PROOF_WRAPPER_SCHEMA:
        raise Q1WError("proof wrapper schema mismatch")
    proof = wrapper["proof"]
    if proof.get("schema") != PROOF_SCHEMA or sha256(canonical_bytes(proof)) != wrapper["proof_sha256"]:
        raise Q1WError("proof body identity mismatch")
    if proof["case_id"] not in contract["shards"] or proof["operation_id"] != proof["case_id"].split("::", 1)[1]:
        raise Q1WError("proof case identity mismatch")
    if proof["historical_reference"] != {
        "bytes": historical["bytes"],
        "certificate_payload_sha256": historical["certificate_payload_sha256"],
        "role": historical["role"],
        "sha256": historical["sha256"],
    }:
        raise Q1WError("proof historical binding mismatch")
    if proof["frozen_inputs"] != contract["frozen_inputs"]:
        raise Q1WError("proof frozen-input binding mismatch")

    if environment_root is not None:
        validate_environment(repository_root, environment_root, contract)
        resolved_environment = environment_root.resolve(strict=True)
        sys.path.insert(0, str(resolved_environment))
    try:
        import sympy  # type: ignore[import-not-found]
    except ImportError as exc:
        raise Q1WError("SymPy 1.14.0 is required from the frozen research environment") from exc
    if sympy.__version__ != "1.14.0":
        raise Q1WError("checker SymPy version mismatch")
    domain = sympy.QQ.algebraic_field(sympy.sqrt(2), sympy.sqrt(3))

    root = repository_root.resolve(strict=True)
    geometry = read_json(root / "docs/reference_cases/e4_pl_q1r_geometry_contract.json")[1]
    frame_contract = read_json(root / "docs/reference_cases/e4_pl_q1r_frame_contract.json")[1]
    material = read_json(root / "docs/reference_cases/e4_pl_q1r_material_contract.json")[1]
    q0 = next(row for row in geometry["geometries"] if row["id"] == "Q0_SQUARE")
    operation = next(row for row in frame_contract["d4"]["operations"] if row["id"] == proof["operation_id"])
    base_nodes = [[F(value) for value in row] for row in q0["nodes"]]
    numbered_nodes = [base_nodes[int(old) - 1] for old in operation["node_tuple"]]
    base_frame = _frame(base_nodes, domain, sympy)
    numbered_frame = _frame(numbered_nodes, domain, sympy)
    a = _fraction_matrix(operation["A"])
    det = F(operation["det"])
    ahat_f = [[a[0][0], a[0][1], 0], [a[1][0], a[1][1], 0], [0, 0, det]]
    ahat = [[_domain_fraction(domain, sympy, value) for value in row] for row in ahat_f]
    expected_frame = _matmul(base_frame, ahat, domain.zero)
    proof_frame = [[_domain_fraction(domain, sympy, F(value)) for value in row] for row in proof["frames"]["numbered"]]

    reconstructed_maps = _maps(operation)
    maps_exact = all(_fraction_matrix(proof["field_maps"][key]) == value for key, value in reconstructed_maps.items())
    base_patch = _base_patch()
    numbered_patch = _numbered_patch(base_patch, operation)
    patch_exact = [F(value) for value in proof["patch_vector"]["base_local"]] == base_patch and [F(value) for value in proof["patch_vector"]["numbered_local"]] == numbered_patch
    nodes_exact = [[F(value) for value in row] for row in proof["nodes"]["numbered"]] == numbered_nodes

    expected = _expected(operation, material)
    legacy_expected = _expected({"A": [[1, 0], [0, 1]], "det": 1}, material)
    stations = proof["stations"]
    if not isinstance(stations, list) or [row.get("station_id") for row in stations] != ["GP_MM", "GP_PM", "GP_PP", "GP_MP"]:
        raise Q1WError("proof station inventory mismatch")
    gauss_exact = True
    for row in stations:
        numbered = [_parse_natural(value, domain, sympy) for value in row["numbered_natural_coordinates"]]
        mapped = [_parse_natural(value, domain, sympy) for value in row["base_natural_coordinates"]]
        actual_map = [
            _domain_fraction(domain, sympy, a[i][0]) * numbered[0] + _domain_fraction(domain, sympy, a[i][1]) * numbered[1]
            for i in range(2)
        ]
        gauss_exact = gauss_exact and actual_map == mapped
        expected_tokens = {key: [str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}" for value in values] for key, values in expected.items()}
        if row["expected_transported"] != expected_tokens:
            raise Q1WError("proof expected transported values mismatch")
        if row["transport_residuals"] != _residual_tokens(row, expected):
            raise Q1WError("proof transported residual values mismatch")
        if row["legacy_untransformed_residuals"] != _residual_tokens(row, legacy_expected):
            raise Q1WError("proof legacy residual values mismatch")

    residual_paths = _residual_paths(stations, expected)
    if proof["exact_nonzero_transport_residuals"] != residual_paths:
        raise Q1WError("proof exact residual index mismatch")
    legacy_paths = _residual_paths(stations, legacy_expected)
    if proof["legacy_untransformed_nonzero_residuals"] != legacy_paths:
        raise Q1WError("proof legacy residual index mismatch")
    work_exact = True
    base_expected = legacy_expected
    base_work = sum((a * b for a, b in zip(base_expected["N"] + base_expected["M"] + base_expected["Q"], base_expected["strain"], strict=True)), Fraction())
    for row in stations:
        recovered_work = sum((F(a) * F(b) for a, b in zip(row["N"] + row["M"] + row["Q"], row["compatible"], strict=True)), Fraction())
        work_exact = work_exact and recovered_work == base_work

    checks = {
        "equation7_frame_exact": _matrix_equal(numbered_frame, expected_frame) and _matrix_equal(numbered_frame, proof_frame),
        "field_maps_exact": maps_exact,
        "gauss_correspondence_exact": gauss_exact,
        "historical_payload_bound": True,
        "nodes_exact": nodes_exact,
        "patch_vector_exact": patch_exact,
        "recovery_work_exact": work_exact,
        "replica_input_canonical": proof_raw == canonical_bytes(wrapper),
    }
    if not all(checks.values()):
        failed = sorted(key for key, value in checks.items() if not value)
        raise Q1WError(f"independent structural checks failed: {failed}")
    terminal = contract["terminals"]["exact_counterexample"] if residual_paths else contract["terminals"]["no_bounded_counterexample"]
    return {
        "schema": CHECK_SCHEMA,
        "candidate_id": contract["candidate_id"],
        "study_id": contract["study_id"],
        "case_id": proof["case_id"],
        "proof_sha256": wrapper["proof_sha256"],
        "checks": checks,
        "exact_nonzero_transport_residuals": residual_paths,
        "legacy_untransformed_nonzero_residual_count": len(proof["legacy_untransformed_nonzero_residuals"]),
        "production": contract["production"],
        "q1b_execution": contract["q1b_execution"],
        "terminal": terminal,
        "elapsed_bucket": "UNDER_600_SECONDS" if time.monotonic() - started < 600 else "LIMIT_EXCEEDED",
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-proof", action="store_true", required=True)
    parser.add_argument("--repository-root", type=Path, required=True)
    parser.add_argument("--proof-contract", type=Path, required=True)
    parser.add_argument("--proof-contract-sha256", required=True)
    parser.add_argument("--historical-reference", type=Path, required=True)
    parser.add_argument("--historical-reference-sha256", required=True)
    parser.add_argument("--proof", type=Path, required=True)
    parser.add_argument("--environment-root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        result = verify_proof(
            repository_root=args.repository_root,
            contract_path=args.proof_contract,
            contract_sha256=args.proof_contract_sha256,
            historical_reference=args.historical_reference,
            historical_reference_sha256=args.historical_reference_sha256,
            proof_path=args.proof,
            environment_root=args.environment_root,
        )
        write_exclusive(args.output, canonical_bytes(result))
        return 0
    except (Q1WError, KeyError, ValueError, OSError) as exc:
        print(f"BLOCKED_E4_PL_Q1W_PROOF_OR_REVIEW: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
