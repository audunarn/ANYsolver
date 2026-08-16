#!/usr/bin/env python3
"""Independent fail-closed oracle for the Stage-M Candidate-A prerequisite.

This module is proof infrastructure only.  It never imports ``anysolver`` and
does not implement or select a production shell formulation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import platform
import sys
from fractions import Fraction
from itertools import combinations
from typing import Any


SCHEMA = "anysolver.s4.stage-m-candidate-a-discretization-output-v1"
CONTRACT_SCHEMA = "anysolver.s4.stage-m-candidate-a-discretization-contract-v1"
CASES_SCHEMA = "anysolver.s4.stage-m-candidate-a-discretization-cases-v1"
CASES_PATH = pathlib.Path("docs/reference_cases/s4_stage_m_candidate_a_discretization_cases.json")
BASE_CONTRACT_PATH = pathlib.Path("docs/reference_cases/s4_stage_m_mechanics_contract.json")
CASES_SHA256 = "BB29F6AE7AE53E961C992BBC2EA764D50B73F935C9B5F9C21C1E21462DCC3E9C"
BASE_CONTRACT_SHA256 = "2FBB419F0C09D909F2B6A1D4FF77285EB078E8A6E7DB10286ECC47282D1F90DA"
DERIVATION_SHA256 = "A8E012E69E3FCFCDAF94E73C97C413B4715CE51A6A1DA8FDA3A50C0467580BF8"
INTERVAL_SHA256 = "05C086DB11548AA4B77A5B31A5171792E08C053F93682D5FBED2D16425C16CC3"
CANDIDATE_B_OUTPUT_SHA256 = "3A26052DB79CE914FF8A1FCA7835F3B86C15F1D351754B45CA904753D8EFDA0D"
EPS64 = Fraction(1, 2**52)


class InputIdentityError(RuntimeError):
    """A raw input identity or transport invariant failed."""


class ContractError(RuntimeError):
    """A semantically validly transported contract is inconsistent."""


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def _no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise InputIdentityError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise InputIdentityError(f"nonfinite JSON number: {value}")


def strict_bytes(path: pathlib.Path, expected_sha256: str | None = None) -> bytes:
    data = path.read_bytes()
    digest = _sha(data)
    if expected_sha256 is not None and digest != expected_sha256:
        raise InputIdentityError(f"raw SHA mismatch for {path}: {digest}")
    if data.startswith(b"\xef\xbb\xbf"):
        raise InputIdentityError(f"UTF-8 BOM forbidden: {path}")
    if b"\r" in data:
        raise InputIdentityError(f"CR bytes forbidden: {path}")
    if not data.endswith(b"\n"):
        raise InputIdentityError(f"terminal LF required: {path}")
    data.decode("utf-8", errors="strict")
    return data


def strict_json(path: pathlib.Path, expected_sha256: str | None = None) -> tuple[Any, bytes]:
    data = strict_bytes(path, expected_sha256)
    value = json.loads(
        data.decode("utf-8"),
        object_pairs_hook=_no_duplicates,
        parse_constant=_reject_constant,
    )
    return value, data


def _repo_root() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parents[2]


def _path_record(root: pathlib.Path, relative: str, expected: str) -> dict[str, Any]:
    path = root / relative
    data = path.read_bytes()
    digest = _sha(data)
    if digest != expected:
        raise InputIdentityError(f"authority SHA mismatch for {relative}: {digest}")
    return {"bytes": len(data), "path": relative, "raw_sha256": digest}


def load_cases(root: pathlib.Path) -> dict[str, Any]:
    cases, _ = strict_json(root / CASES_PATH, CASES_SHA256)
    if cases.get("schema") != CASES_SCHEMA:
        raise InputIdentityError("unexpected cases schema")
    if cases.get("authority", {}).get("derivation_sha256") != DERIVATION_SHA256:
        raise InputIdentityError("cases derivation binding mismatch")
    if cases.get("execution", {}).get("decimal_digits") != [80, 160, 320]:
        raise InputIdentityError("precision catalog mismatch")
    if cases.get("execution", {}).get("repeat_sets") != 2:
        raise InputIdentityError("repeat-set catalog mismatch")
    _validate_cases(cases)
    return cases


def _validate_cases(cases: dict[str, Any]) -> None:
    pair_ids = [row.get("id") for row in cases.get("candidate_pairs", [])]
    if pair_ids != ["candidate_a.d4.span_r_s", "candidate_a.d4.span_1_rs"]:
        raise InputIdentityError("candidate-pair order mismatch")
    expected_projectors = [["0", "1", "1", "0"], ["1", "0", "0", "1"]]
    if [row.get("projector_diagonal") for row in cases["candidate_pairs"]] != expected_projectors:
        raise InputIdentityError("candidate projector mismatch")
    for pair in cases["candidate_pairs"]:
        if len(pair.get("multiplier_basis", [])) != 2:
            raise InputIdentityError("each candidate requires two multiplier modes")
        for mode in pair["multiplier_basis"]:
            coefficient = mode.get("coefficient", {})
            if coefficient.get("kind") not in {"rational", "sqrt_rational"}:
                raise InputIdentityError("invalid multiplier coefficient grammar")
            value = Fraction(int(coefficient["numerator"]), int(coefficient["denominator"]))
            if value <= 0:
                raise InputIdentityError("multiplier normalization must be positive")
    rows = cases.get("constraint", {}).get("moment_rows_raw", {})
    if list(sorted(rows)) != ["1", "r", "rs", "s"]:
        raise InputIdentityError("moment-row catalog mismatch")
    for name, row in rows.items():
        if len(row) != 24:
            raise InputIdentityError(f"moment row {name} must contain 24 values")
        for value in row:
            Fraction(value)
    if cases.get("fixed_lambda_checkpoint") != {
        "director_norm": "1",
        "lambda": "1",
        "physical_offset": "zeta*(thickness/2)*director",
        "required_pullbacks": ["constraint", "force", "energy", "tangent", "mass", "rotary_inertia", "load", "section_ABDAs", "state", "recovery"],
        "thickness_is_separate": True,
    }:
        raise InputIdentityError("fixed-lambda checkpoint mismatch")
    rotation_ids = [row.get("id") for row in cases.get("rotation_cases", [])]
    if rotation_ids != ["identity", "common_rational_rotation", "heterogeneous_positive", "singular_center_guard"]:
        raise InputIdentityError("rotation-case order mismatch")
    for case in cases["rotation_cases"]:
        quaternions = case.get("nodal_quaternions")
        if not isinstance(quaternions, list) or len(quaternions) != 4:
            raise InputIdentityError("every rotation case requires four nodal quaternions")
        for quaternion in quaternions:
            if quaternion.get("kind") != "normalized_quaternion" or len(quaternion.get("components", [])) != 4:
                raise InputIdentityError("invalid quaternion grammar")
            values = [Fraction(value) for value in quaternion["components"]]
            if not any(values):
                raise InputIdentityError("zero quaternion is forbidden")
        for point in case.get("sample_points", []):
            if len(point) != 2:
                raise InputIdentityError("sample points require r and s")
            if any(abs(Fraction(value)) > 1 for value in point):
                raise InputIdentityError("sample point lies outside the reference square")
    multipliers = cases.get("execution", {}).get("svd_multipliers")
    if multipliers != [
        {"denominator": "4", "numerator": "1"},
        {"denominator": "1", "numerator": "1"},
        {"denominator": "1", "numerator": "4"},
    ]:
        raise InputIdentityError("SVD multiplier catalog mismatch")
    if any(cases.get("exclusions", {}).values()):
        raise InputIdentityError("all authority exclusions must remain false")


def _coverage_contract(root: pathlib.Path, pair_ids: list[str]) -> list[dict[str, Any]]:
    base, _ = strict_json(root / BASE_CONTRACT_PATH, BASE_CONTRACT_SHA256)
    base_rows = base.get("required_execution_coverage")
    if not isinstance(base_rows, list) or len(base_rows) != 174:
        raise ContractError("preserved mechanics coverage must contain 174 rows")
    ledgers: list[dict[str, Any]] = []
    for pair_id in pair_ids:
        rows: list[dict[str, Any]] = []
        for row in base_rows:
            source_digest = _sha(canonical_bytes(row))
            rows.append(
                {
                    "base_coverage_key": row["coverage_key"],
                    "pair_id": pair_id,
                    "source_record_sha256": source_digest,
                }
            )
        ledgers.append(
            {
                "pair_id": pair_id,
                "row_count": len(rows),
                "row_ledger_sha256": _sha(canonical_bytes(rows)),
            }
        )
    return ledgers


def emit_contract(root: pathlib.Path, cases: dict[str, Any]) -> dict[str, Any]:
    pair_ids = [row["id"] for row in cases["candidate_pairs"]]
    coverage_ledgers = _coverage_contract(root, pair_ids)
    oracle_data = pathlib.Path(__file__).read_bytes()
    authority_inputs = [
        _path_record(root, "docs/S4_STAGE_M_CANDIDATE_A_DISCRETIZATION_DERIVATION.md", DERIVATION_SHA256),
        _path_record(root, str(CASES_PATH).replace("\\", "/"), CASES_SHA256),
        _path_record(root, "docs/reference_cases/s4_stage_m_dyadic_interval.py", INTERVAL_SHA256),
        _path_record(root, str(BASE_CONTRACT_PATH).replace("\\", "/"), BASE_CONTRACT_SHA256),
        _path_record(root, "docs/reference_cases/s4_stage_m_mechanics_output.json", CANDIDATE_B_OUTPUT_SHA256),
    ]
    candidate_gate_ids = [
        "candidate_a.fixed_lambda.constraint_sector",
        "candidate_a.fixed_lambda.physical_pullback",
        "candidate_a.rotation.positive_polar",
        "candidate_a.rotation.objectivity",
        "candidate_a.rotation.first_second_variation",
        "candidate_a.rotation.qh_qp_equivalence",
        "candidate_a.pair.rank_rigid_energy",
        "candidate_a.pair.uniform_inf_sup",
        "candidate_a.pair.topology_covariance",
    ]
    result = {
        "authority": cases["authority"],
        "authority_inputs": authority_inputs,
        "candidate_gate_ids": candidate_gate_ids,
        "candidate_pairs": pair_ids,
        "cases_sha256": CASES_SHA256,
        "counts": {"base_rows": 174, "pair_rows": 174 * len(pair_ids), "pairs": len(pair_ids)},
        "coverage_binding": {
            "base_contract_sha256": BASE_CONTRACT_SHA256,
            "base_rows": 174,
            "derivation": "for each candidate pair, retain the exact base-row order and bind pair_id plus canonical base-row SHA-256",
            "pair_ledgers": coverage_ledgers,
            "status_until_prerequisites_close": "NOT_RUN_PREREQUISITE_UNCLOSED",
        },
        "execution": cases["execution"],
        "exclusions": cases["exclusions"],
        "oracle": {"bytes": len(oracle_data), "raw_sha256": _sha(oracle_data)},
        "schema": CONTRACT_SCHEMA,
        "terminal_precedence": cases["terminal_precedence"],
    }
    result["ledger_sha256"] = _sha(canonical_bytes(coverage_ledgers))
    return result


# Exact bivariate polynomial helpers: {(power_r,power_s): coefficient}.
Poly = dict[tuple[int, int], Fraction]


def _poly_add(*polys: Poly) -> Poly:
    out: Poly = {}
    for poly in polys:
        for key, value in poly.items():
            out[key] = out.get(key, Fraction(0)) + value
    return {key: value for key, value in out.items() if value}


def _poly_scale(poly: Poly, scale: Fraction) -> Poly:
    return {key: value * scale for key, value in poly.items() if value * scale}


def _poly_mul(left: Poly, right: Poly) -> Poly:
    out: Poly = {}
    for (ir, is_), a in left.items():
        for (jr, js), b in right.items():
            key = (ir + jr, is_ + js)
            out[key] = out.get(key, Fraction(0)) + a * b
    return {key: value for key, value in out.items() if value}


def _poly_derivative(poly: Poly, axis: int) -> Poly:
    out: Poly = {}
    for (ir, is_), value in poly.items():
        powers = [ir, is_]
        if powers[axis] == 0:
            continue
        factor = powers[axis]
        powers[axis] -= 1
        out[(powers[0], powers[1])] = value * factor
    return out


def _poly_integral(poly: Poly) -> Fraction:
    total = Fraction(0)
    for (ir, is_), value in poly.items():
        if ir % 2 or is_ % 2:
            continue
        total += value * Fraction(2, ir + 1) * Fraction(2, is_ + 1)
    return total


def _shape_polynomials() -> list[Poly]:
    one: Poly = {(0, 0): Fraction(1)}
    r: Poly = {(1, 0): Fraction(1)}
    s: Poly = {(0, 1): Fraction(1)}
    result = []
    for sr, ss in [(-1, -1), (1, -1), (1, 1), (-1, 1)]:
        result.append(_poly_scale(_poly_mul(_poly_add(one, _poly_scale(r, Fraction(sr))), _poly_add(one, _poly_scale(s, Fraction(ss)))), Fraction(1, 4)))
    return result


def _moment_rows() -> dict[str, list[Fraction]]:
    modes: dict[str, Poly] = {
        "1": {(0, 0): Fraction(1)},
        "r": {(1, 0): Fraction(1)},
        "s": {(0, 1): Fraction(1)},
        "rs": {(1, 1): Fraction(1)},
    }
    rows: dict[str, list[Fraction]] = {}
    for name, mode in modes.items():
        row: list[Fraction] = []
        for shape in _shape_polynomials():
            u = _poly_integral(_poly_mul(mode, _poly_derivative(shape, 1)))
            v = -_poly_integral(_poly_mul(mode, _poly_derivative(shape, 0)))
            psi = 2 * _poly_integral(_poly_mul(mode, shape))
            row.extend([u, v, Fraction(0), Fraction(0), Fraction(0), psi])
        rows[name] = row
    return rows


def _fraction(text: str) -> Fraction:
    return Fraction(text)


def exact_certificate(cases: dict[str, Any]) -> dict[str, Any]:
    rows = _moment_rows()
    expected = {name: [_fraction(value) for value in row] for name, row in cases["constraint"]["moment_rows_raw"].items()}
    if rows != expected:
        raise ContractError("independent exact moment rows disagree with cases")
    generators = {
        "R": [[1, 0, 0, 0], [0, 0, -1, 0], [0, 1, 0, 0], [0, 0, 0, -1]],
        "S": [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, -1, 0], [0, 0, 0, -1]],
    }
    invariant_subsets: list[list[int]] = []
    for subset in combinations(range(4), 2):
        selected = set(subset)
        invariant = True
        for matrix in generators.values():
            for column in subset:
                support = {row for row in range(4) if matrix[row][column]}
                if not support.issubset(selected):
                    invariant = False
        if invariant:
            invariant_subsets.append(list(subset))
    if invariant_subsets != [[0, 3], [1, 2]]:
        raise ContractError(f"unexpected D4 rank-two images: {invariant_subsets}")
    return {
        "d4_invariant_index_sets": invariant_subsets,
        "moment_rows": {name: [f"{v.numerator}/{v.denominator}" for v in row] for name, row in rows.items()},
        "rank_two_images_exact": True,
        "row_sha256": _sha(canonical_bytes({name: [str(v) for v in row] for name, row in rows.items()})),
    }


def _environment_manifest(mp: Any) -> dict[str, Any]:
    package_root = pathlib.Path(mp.__file__).resolve().parent
    files = []
    for located in sorted(package_root.rglob("*.py"), key=lambda item: item.relative_to(package_root).as_posix()):
        relative = located.relative_to(package_root).as_posix()
        data = located.read_bytes()
        files.append({"path": relative, "raw_sha256": _sha(data), "bytes": len(data)})
    executable = pathlib.Path(sys.executable).read_bytes()
    backend = str(getattr(getattr(mp, "libmp", object()), "BACKEND", "unknown"))
    if backend != "python":
        raise ContractError("mpmath pure-Python backend is required")
    manifest = {
        "byteorder": sys.byteorder,
        "implementation": platform.python_implementation().lower(),
        "mpmath_backend": backend,
        "mpmath_source_file_count": len(files),
        "mpmath_source_tree_sha256": _sha(canonical_bytes(files)),
        "mpmath_version": str(mp.__version__),
        "python_hexversion": sys.hexversion,
        "sys_executable_sha256": _sha(executable),
    }
    return {"digest": _sha(canonical_bytes(manifest)), "manifest": manifest}


def _mp_token(value: Any) -> list[Any]:
    sign, man, exp, bc = value._mpf_
    return [int(sign), str(man), int(exp), int(bc)]


def _parse_quaternion(mp: Any, record: dict[str, Any]) -> list[Any]:
    if record.get("kind") != "normalized_quaternion":
        raise ContractError("unknown quaternion grammar")
    values = [mp.mpf(Fraction(text).numerator) / Fraction(text).denominator for text in record["components"]]
    norm = mp.sqrt(sum(value * value for value in values))
    if norm == 0:
        raise ContractError("zero quaternion")
    return [value / norm for value in values]


def _quat_matrix(mp: Any, q: list[Any]) -> Any:
    w, x, y, z = q
    return mp.matrix(
        [
            [1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)],
            [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
            [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)],
        ]
    )


def _shape_values(mp: Any, r: Any, s: Any) -> list[Any]:
    return [
        (1 - r) * (1 - s) / 4,
        (1 + r) * (1 - s) / 4,
        (1 + r) * (1 + s) / 4,
        (1 - r) * (1 + s) / 4,
    ]


def _polar_positive(mp: Any, matrix: Any) -> tuple[Any | None, Any, Any]:
    gram = matrix.T * matrix
    eigenvalues, vectors = mp.eigsy(gram)
    minimum = min(eigenvalues)
    maximum = max(eigenvalues)
    if minimum <= 0 or mp.det(matrix) <= 0:
        return None, minimum, maximum
    inverse_sqrt = vectors * mp.diag([1 / mp.sqrt(value) for value in eigenvalues]) * vectors.T
    return matrix * inverse_sqrt, minimum, maximum


def _frobenius(mp: Any, matrix: Any) -> Any:
    return mp.sqrt(sum(matrix[i, j] ** 2 for i in range(matrix.rows) for j in range(matrix.cols)))


def _rotation_record(mp: Any, cases: dict[str, Any], dps: int) -> dict[str, Any]:
    mp.mp.dps = dps
    tolerance = mp.mpf(4096 * 3) / (2**52)
    records = []
    positive_pass = True
    objectivity_pass = True
    guard_pass = True
    for case in cases["rotation_cases"]:
        rotations = [_quat_matrix(mp, _parse_quaternion(mp, item)) for item in case["nodal_quaternions"]]
        samples = []
        for r_text, s_text in case["sample_points"]:
            r = mp.mpf(Fraction(r_text).numerator) / Fraction(r_text).denominator
            s = mp.mpf(Fraction(s_text).numerator) / Fraction(s_text).denominator
            values = _shape_values(mp, r, s)
            blend = mp.zeros(3, 3)
            for weight, rotation in zip(values, rotations):
                blend += weight * rotation
            polar, minimum, maximum = _polar_positive(mp, blend)
            rejected = polar is None
            if case["id"] == "singular_center_guard":
                guard_pass = guard_pass and rejected
            else:
                positive_pass = positive_pass and not rejected
            residual = None
            determinant = None
            if polar is not None:
                residual = _frobenius(mp, polar.T * polar - mp.eye(3))
                determinant = mp.det(polar)
                positive_pass = positive_pass and residual <= tolerance and abs(determinant - 1) <= tolerance
                if case["id"] == "common_rational_rotation":
                    objectivity_pass = objectivity_pass and _frobenius(mp, polar - rotations[0]) <= tolerance
            samples.append(
                {
                    "determinant": None if determinant is None else _mp_token(determinant),
                    "gram_maximum": _mp_token(maximum),
                    "gram_minimum": _mp_token(minimum),
                    "orthogonality_residual": None if residual is None else _mp_token(residual),
                    "point": [r_text, s_text],
                    "rejected": rejected,
                }
            )
        records.append({"id": case["id"], "samples": samples})
    return {
        "decimal_digits": dps,
        "guard_pass": guard_pass,
        "objectivity_pass": objectivity_pass,
        "positive_polar_pass": positive_pass,
        "records": records,
        "r_tol": _mp_token(tolerance),
    }


def _coverage_evidence(contract: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "pair_id": row["pair_id"],
            "row_count": row["row_count"],
            "row_ledger_sha256": row["row_ledger_sha256"],
            "status": "NOT_RUN_PREREQUISITE_UNCLOSED",
        }
        for row in contract["coverage_binding"]["pair_ledgers"]
    ]


def run_oracle(root: pathlib.Path, cases: dict[str, Any], contract: dict[str, Any], contract_sha256: str) -> dict[str, Any]:
    # Third-party science dependency is imported only after cases and contract validation.
    import mpmath as mp

    environment = _environment_manifest(mp)
    exact = exact_certificate(cases)
    precision_records = [_rotation_record(mp, cases, dps) for dps in cases["execution"]["decimal_digits"]]
    polar_pass = all(record["positive_polar_pass"] and record["objectivity_pass"] and record["guard_pass"] for record in precision_records)
    fixed_obligations = {
        "constraint": "PASS",
        "energy": "UNCLASSIFIED",
        "force": "UNCLASSIFIED",
        "load": "UNCLASSIFIED",
        "mass": "UNCLASSIFIED",
        "recovery": "UNCLASSIFIED",
        "rotary_inertia": "UNCLASSIFIED",
        "section_ABDAs": "UNCLASSIFIED",
        "state": "UNCLASSIFIED",
        "tangent": "UNCLASSIFIED",
    }
    rotation_obligations = {
        "finite_sample_positive_polar": "PASS" if polar_pass else "PROVEN_FAIL",
        "first_second_variation": "UNCLASSIFIED",
        "global_qh_qp_equivalence": "UNCLASSIFIED",
        "production_multiplicative_state": "UNCLASSIFIED",
    }
    fixed_terminal = "UNCLASSIFIED_CANDIDATE_A_FIXED_LAMBDA_SPECIALIZATION"
    rotation_terminal = "UNCLASSIFIED_CANDIDATE_A_ROTATION_MAPPING" if polar_pass else "NO_GO_CANDIDATE_A_ROTATION_MAPPING"
    pair_terminal = "NOT_RUN_PREREQUISITE_UNCLOSED"
    result = {
        "candidate_b_preserved": {"output_sha256": CANDIDATE_B_OUTPUT_SHA256, "terminal": "NO_GO_CANDIDATE_B"},
        "candidate_terminal": "BLOCKED_CANDIDATE_A_DISCRETIZATION_UNREGISTERED",
        "contract_sha256": contract_sha256,
        "coverage_evidence": _coverage_evidence(contract),
        "environment": environment,
        "exact_certificate": exact,
        "exclusions": cases["exclusions"],
        "fixed_lambda_checkpoint": {"lambda": "1", "obligations": fixed_obligations, "terminal": fixed_terminal},
        "mode": "full",
        "overall_stage_m_terminal": "BLOCKED_CANDIDATE_A_DISCRETIZATION_UNREGISTERED",
        "pair_results": [
            {"id": row["id"], "status": "NOT_RUN_PREREQUISITE_UNCLOSED"}
            for row in cases["candidate_pairs"]
        ],
        "pair_terminal": pair_terminal,
        "precision_records": precision_records,
        "rotation_checkpoint": {"obligations": rotation_obligations, "terminal": rotation_terminal},
        "schema": SCHEMA,
        "status": "complete",
    }
    return result


def _load_contract(root: pathlib.Path, path: pathlib.Path, expected_sha256: str, cases: dict[str, Any]) -> tuple[dict[str, Any], str]:
    contract, data = strict_json(path, expected_sha256)
    if contract.get("schema") != CONTRACT_SCHEMA:
        raise ContractError("unexpected contract schema")
    expected = emit_contract(root, cases)
    if contract != expected:
        raise ContractError("contract semantic mismatch")
    return contract, _sha(data)


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--emit-contract", action="store_true")
    modes.add_argument("--run", action="store_true")
    parser.add_argument("--contract", type=pathlib.Path)
    parser.add_argument("--contract-sha256")
    return parser.parse_args()


def main() -> int:
    args = _arguments()
    root = _repo_root()
    try:
        cases = load_cases(root)
        if args.emit_contract:
            if args.contract is not None or args.contract_sha256 is not None:
                raise ContractError("contract arguments are forbidden in emit mode")
            sys.stdout.buffer.write(canonical_bytes(emit_contract(root, cases)))
            return 0
        if args.contract is None or not args.contract_sha256:
            raise ContractError("run mode requires --contract and --contract-sha256")
        contract, digest = _load_contract(root, args.contract, args.contract_sha256.upper(), cases)
        sys.stdout.buffer.write(canonical_bytes(run_oracle(root, cases, contract, digest)))
        return 0
    except InputIdentityError as exc:
        sys.stdout.buffer.write(canonical_bytes({"schema": SCHEMA, "status": "blocked", "terminal": "BLOCKED_INPUT_IDENTITY", "detail": str(exc)}))
        return 2
    except ContractError as exc:
        sys.stdout.buffer.write(canonical_bytes({"schema": SCHEMA, "status": "blocked", "terminal": "BLOCKED_CONTRACT_VIOLATION", "detail": str(exc)}))
        return 2
    except Exception as exc:  # diagnostic only; never a scientific terminal
        sys.stdout.buffer.write(canonical_bytes({"schema": SCHEMA, "status": "blocked", "terminal": "UNCLASSIFIED_CANDIDATE_A_EXECUTION_ERROR", "detail": f"{type(exc).__name__}: {exc}"}))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
