"""Source-independent exact screens for the blocked E3-P HW29 identity.

This module exactly reproduces the newly source-closed drilling and hourglass
equations, then stops before the missing shell-EADG, mixed-shear,
condensation, load, and recovery equations.  It imports no candidate or
production code.
"""

from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
CASES_PATH = ROOT / "docs/reference_cases/e3_hw29_cases.json"
COVERAGE_PATH = ROOT / "docs/reference_cases/e3_hw29_source_coverage.json"
CONTRACT_PATH = ROOT / "docs/reference_cases/e3_hw29_contract.json"
CANDIDATE_ID = "study_e3_p.hw29_linear_isotropic_identity_v1"
TERMINAL = "BLOCKED_E3_P_HW29_PUBLIC_SOURCE"
RELEASE = "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"
CONTRACT_INPUTS = [
    "docs/agent_plans/S4_E3_HW29_MITC9I_ROUTE_SELECTION_PLAN.md",
    "docs/E3_HW29_SOURCE_IDENTITY.md",
    "docs/reference_cases/e3_baseline.json",
    "docs/reference_cases/e3_environment.json",
    "docs/reference_cases/e3_test_inventory.json",
    "docs/reference_cases/e3_source_registry.json",
    "docs/reference_cases/e3_search_log.json",
    "docs/reference_cases/e3_material_fixtures.json",
    "docs/reference_cases/e3_hw29_source_coverage.json",
    "docs/reference_cases/e3_hw29_cases.json",
]


class EvidenceError(Exception):
    """Raised when a frozen input is not canonical or self-consistent."""


class ContractError(Exception):
    """Raised when caller-bound contract evidence is invalid."""


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise EvidenceError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _canonical(value: object) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
        + "\n"
    ).encode("utf-8")


def _load_json(path: Path) -> dict[str, object]:
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf") or b"\r" in raw or not raw.endswith(b"\n"):
        raise EvidenceError(f"invalid UTF-8/LF transport: {path}")
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_pairs,
            parse_constant=lambda token: (_ for _ in ()).throw(EvidenceError(token)),
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EvidenceError(str(exc)) from exc
    if not isinstance(value, dict) or raw != _canonical(value):
        raise EvidenceError(f"noncanonical JSON: {path}")
    return value


def _fraction(value: object) -> Fraction:
    if not isinstance(value, (str, int)):
        raise EvidenceError(f"not an exact scalar: {value!r}")
    return Fraction(value)


def _q1_modal(values: list[Fraction], nodes: list[list[int]]) -> tuple[Fraction, ...]:
    if len(values) != 4 or len(nodes) != 4:
        raise EvidenceError("Q1 requires four nodes")
    return (
        sum(values) / 4,
        sum(Fraction(node[0]) * value for node, value in zip(nodes, values)) / 4,
        sum(Fraction(node[1]) * value for node, value in zip(nodes, values)) / 4,
        sum(Fraction(node[0] * node[1]) * value for node, value in zip(nodes, values)) / 4,
    )


def _constraint_coefficients(
    state: list[Fraction], nodes: list[list[int]]
) -> tuple[Fraction, Fraction, Fraction, Fraction]:
    if len(state) != 12:
        raise EvidenceError("flat in-plane/drill state must have 12 entries")
    u = _q1_modal([state[3 * node] for node in range(4)], nodes)
    v = _q1_modal([state[3 * node + 1] for node in range(4)], nodes)
    theta = _q1_modal([state[3 * node + 2] for node in range(4)], nodes)
    return (
        theta[0] + (u[2] - v[1]) / 2,
        theta[1] + u[3] / 2,
        theta[2] - v[3] / 2,
        theta[3],
    )


def _constraint_matrix(nodes: list[list[int]]) -> list[list[Fraction]]:
    columns: list[tuple[Fraction, ...]] = []
    for column in range(12):
        state = [Fraction(0) for _ in range(12)]
        state[column] = Fraction(1)
        columns.append(_constraint_coefficients(state, nodes))
    return [[column[row] for column in columns] for row in range(4)]


def _matvec(matrix: list[list[Fraction]], vector: list[Fraction]) -> list[Fraction]:
    return [sum(left * right for left, right in zip(row, vector)) for row in matrix]


def _rank(matrix: list[list[Fraction]]) -> int:
    if not matrix:
        return 0
    work = [row[:] for row in matrix]
    rows, columns = len(work), len(work[0])
    rank = 0
    for column in range(columns):
        pivot = next((row for row in range(rank, rows) if work[row][column]), None)
        if pivot is None:
            continue
        work[rank], work[pivot] = work[pivot], work[rank]
        scale = work[rank][column]
        work[rank] = [value / scale for value in work[rank]]
        for row in range(rows):
            if row != rank and work[row][column]:
                factor = work[row][column]
                work[row] = [left - factor * right for left, right in zip(work[row], work[rank])]
        rank += 1
    return rank


def _transpose(matrix: list[list[Fraction]]) -> list[list[Fraction]]:
    return [list(column) for column in zip(*matrix)]


def _multiply(
    left: list[list[Fraction]], right: list[list[Fraction]]
) -> list[list[Fraction]]:
    transposed = _transpose(right)
    return [[sum(a * b for a, b in zip(row, column)) for column in transposed] for row in left]


def _subtract(
    left: list[list[Fraction]], right: list[list[Fraction]]
) -> list[list[Fraction]]:
    return [[a - b for a, b in zip(left_row, right_row)] for left_row, right_row in zip(left, right)]


def _inverse2(matrix: list[list[Fraction]]) -> list[list[Fraction]]:
    determinant = matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0]
    if not determinant:
        raise EvidenceError("generic Schur example is singular")
    return [
        [matrix[1][1] / determinant, -matrix[0][1] / determinant],
        [-matrix[1][0] / determinant, matrix[0][0] / determinant],
    ]


def _signature(values: list[Fraction] | tuple[Fraction, ...]) -> list[str]:
    return [str(value) for value in values]


def _matrix_signature(matrix: list[list[Fraction]]) -> list[list[str]]:
    return [_signature(row) for row in matrix]


def _poly_terms(record: object) -> dict[tuple[int, int], Fraction]:
    if not isinstance(record, list):
        raise EvidenceError("polynomial term list missing")
    result: dict[tuple[int, int], Fraction] = {}
    for term in record:
        if not isinstance(term, list) or len(term) != 3:
            raise EvidenceError("malformed polynomial term")
        coefficient, r_power, s_power = term
        key = (int(r_power), int(s_power))
        result[key] = result.get(key, Fraction(0)) + _fraction(coefficient)
    return {key: value for key, value in result.items() if value}


def _boundary_zero(poly: dict[tuple[int, int], Fraction]) -> bool:
    for axis in range(2):
        for boundary in (Fraction(-1), Fraction(1)):
            restricted: dict[int, Fraction] = {}
            for (r_power, s_power), coefficient in poly.items():
                if axis == 0:
                    power, value = s_power, coefficient * boundary**r_power
                else:
                    power, value = r_power, coefficient * boundary**s_power
                restricted[power] = restricted.get(power, Fraction(0)) + value
            if any(restricted.values()):
                return False
    return True


def _validate_inputs(cases: dict[str, object], coverage: dict[str, object]) -> None:
    if cases.get("schema") != "anysolver.e3.hw29-cases-v2":
        raise EvidenceError("case schema mismatch")
    if coverage.get("schema") != "anysolver.e3.hw29-source-coverage-v2":
        raise EvidenceError("coverage schema mismatch")
    if cases.get("candidate_id") != CANDIDATE_ID or coverage.get("candidate_id") != CANDIDATE_ID:
        raise EvidenceError("candidate identity mismatch")
    if coverage.get("component_terminal") != TERMINAL:
        raise EvidenceError("coverage terminal mismatch")
    source_gate = cases.get("source_gate")
    if not isinstance(source_gate, dict) or source_gate.get("terminal") != TERMINAL:
        raise EvidenceError("case terminal mismatch")
    rows = coverage.get("mandatory_rows")
    if not isinstance(rows, list) or not any(
        isinstance(row, dict) and str(row.get("status", "")).startswith("MISSING_") for row in rows
    ):
        raise EvidenceError("source gate lacks an indispensable missing row")
    coverage_missing = sorted(
        str(row["id"])
        for row in rows
        if isinstance(row, dict) and str(row.get("status", "")).startswith("MISSING_")
    )
    case_missing = source_gate.get("missing_indispensable_rows")
    if case_missing != coverage_missing:
        raise EvidenceError("case and source-coverage missing rows disagree")


def _dot(left: list[Fraction], right: list[Fraction]) -> Fraction:
    return sum(a * b for a, b in zip(left, right))


def _gamma_certificate(
    record: dict[str, object], stabilization: dict[str, object]
) -> dict[str, object]:
    xi = [_fraction(value) for value in stabilization["xi"]]
    eta = [_fraction(value) for value in stabilization["eta"]]
    hourglass = [_fraction(value) for value in stabilization["h"]]
    s1 = [_fraction(value) for value in record["S1"]]
    s2 = [_fraction(value) for value in record["S2"]]
    area = _fraction(record["area_measure_A"])
    if any(len(vector) != 4 for vector in (xi, eta, hourglass, s1, s2)) or not area:
        raise EvidenceError("malformed gamma-stabilization case")
    b1 = [
        (_dot(eta, s2) * xi_i - _dot(xi, s2) * eta_i) / (4 * area)
        for xi_i, eta_i in zip(xi, eta)
    ]
    b2 = [
        (-_dot(eta, s1) * xi_i + _dot(xi, s1) * eta_i) / (4 * area)
        for xi_i, eta_i in zip(xi, eta)
    ]
    gamma = [
        (h_i - _dot(hourglass, s1) * b1_i - _dot(hourglass, s2) * b2_i) / 4
        for h_i, b1_i, b2_i in zip(hourglass, b1, b2)
    ]
    expected = [_fraction(value) for value in record["expected_gamma"]]
    if gamma != expected:
        raise EvidenceError(f"gamma-vector mismatch: {record['id']}")
    matrix = [[left * right for right in gamma] for left in gamma]
    theta_hourglass = _dot(gamma, hourglass)
    theta_constant = sum(gamma)
    alpha = _fraction(stabilization["alpha_HG"])
    return {
        "b1": _signature(b1),
        "b2": _signature(b2),
        "constant_drill_theta": str(theta_constant),
        "gamma": _signature(gamma),
        "hourglass_energy_over_GV": str(alpha * theta_hourglass**2),
        "hourglass_theta": str(theta_hourglass),
        "rank_gamma_outer_gamma": _rank(matrix),
        "zero_row_sum_ground_coupling": theta_constant == 0,
    }


def build_certificate() -> dict[str, object]:
    cases = _load_json(CASES_PATH)
    coverage = _load_json(COVERAGE_PATH)
    _validate_inputs(cases, coverage)

    raw_nodes = cases["nodes"]
    if not isinstance(raw_nodes, list):
        raise EvidenceError("node registry missing")
    nodes = [[int(value) for value in node] for node in raw_nodes if isinstance(node, list)]
    if nodes != [[-1, -1], [1, -1], [1, 1], [-1, 1]]:
        raise EvidenceError("node order mismatch")

    coefficient_matrix = _constraint_matrix(nodes)
    moment_scales = [Fraction(4), Fraction(4, 3), Fraction(4, 3)]
    retained_moment_matrix = [
        [scale * value for value in coefficient_matrix[row]]
        for row, scale in enumerate(moment_scales)
    ]

    alternating = []
    for theta in (1, -1, 1, -1):
        alternating.extend((Fraction(0), Fraction(0), Fraction(theta)))
    alternating_coefficients = _constraint_coefficients(alternating, nodes)
    alternating_moments = _matvec(retained_moment_matrix, alternating)

    pure_drill: list[Fraction] = []
    translation_spin: list[Fraction] = []
    combined: list[Fraction] = []
    for r, s in nodes:
        g = [Fraction(0), Fraction(0), Fraction(1)]
        spin = [Fraction(-s), Fraction(r), Fraction(0)]
        pure_drill.extend(g)
        translation_spin.extend(spin)
        combined.extend(left + right for left, right in zip(g, spin))

    exclusion = cases["e2_a_exclusion"]
    if not isinstance(exclusion, dict):
        raise EvidenceError("E2-A exclusion missing")
    bubble_u = _poly_terms(exclusion["bubble_u_monomials"])
    bubble_v = _poly_terms(exclusion["bubble_v_monomials"])
    q1_span = {tuple(int(power) for power in item) for item in exclusion["q1_span"]}

    field_count = cases["field_count"]
    if not isinstance(field_count, dict) or not isinstance(field_count.get("blocks"), list):
        raise EvidenceError("field-count registry missing")
    count_sum = sum(int(block["count"]) for block in field_count["blocks"] if isinstance(block, dict))

    stabilization = cases["stabilization"]
    gamma_cases = cases["gamma_cases"]
    if not isinstance(stabilization, dict) or not isinstance(gamma_cases, list):
        raise EvidenceError("gamma-stabilization registry missing")
    gamma_certificates = {
        str(record["id"]): _gamma_certificate(record, stabilization)
        for record in gamma_cases
        if isinstance(record, dict)
    }
    if set(gamma_certificates) != {"square", "rational_trapezoid"}:
        raise EvidenceError("gamma-stabilization cases are not total")

    schur = cases["generic_schur"]
    if not isinstance(schur, dict):
        raise EvidenceError("generic Schur case missing")
    matrices = {
        name: [[_fraction(value) for value in row] for row in schur[name]]
        for name in ("A", "B", "D")
    }


    d_inverse = _inverse2(matrices["D"])
    condensed = _subtract(
        matrices["A"],
        _multiply(_multiply(matrices["B"], d_inverse), _transpose(matrices["B"])),
    )

    mandatory_rows = coverage["mandatory_rows"]
    if not isinstance(mandatory_rows, list):
        raise EvidenceError("mandatory source rows missing")
    missing_ids = sorted(
        str(row["id"])
        for row in mandatory_rows
        if isinstance(row, dict) and str(row.get("status", "")).startswith("MISSING_")
    )

    return {
        "component_terminal": TERMINAL,
        "constraint_certificate": {
            "alternating_full_coefficients_1_r_s_rs": _signature(alternating_coefficients),
            "alternating_retained_moments_1_r_s": _signature(alternating_moments),
            "coefficient_matrix_rank": _rank(coefficient_matrix),
            "highest_rs_translation_columns_zero": all(
                coefficient_matrix[3][column] == 0 for column in range(12) if column % 3 != 2
            ),
            "retained_moment_matrix_rank": _rank(retained_moment_matrix),
            "rs_drill_row": _signature(coefficient_matrix[3]),
        },
        "e2_a_exclusion": {
            "bubble_boundary_zero": _boundary_zero(bubble_u) and _boundary_zero(bubble_v),
            "bubble_nonzero": bool(bubble_u) and bool(bubble_v),
            "outside_q1": any(power not in q1_span for power in bubble_u | bubble_v),
        },
        "field_count": {
            "arithmetic_sum": count_sum,
            "registered_total": int(field_count["registered_total"]),
            "source_closed": bool(field_count["source_closed"]),
        },
        "gamma_stabilization": {
            "alpha_HG": str(_fraction(stabilization["alpha_HG"])),
            "cases": gamma_certificates,
            "energy": stabilization["energy"],
            "source_status": "PRINTED_EQUATIONS_26_43_TO_26_45",
        },
        "generic_schur": {
            "D_determinant": str(matrices["D"][0][0] * matrices["D"][1][1]),
            "condensed_A_minus_B_Dinv_BT": _matrix_signature(condensed),
            "scope": schur["scope"],
        },
        "rigid_constraint": {
            "combined_physical_rigid": _signature(_constraint_coefficients(combined, nodes)),
            "pure_common_drill": _signature(_constraint_coefficients(pure_drill, nodes)),
            "translation_only_spin": _signature(_constraint_coefficients(translation_spin, nodes)),
        },
        "source_closure": {
            "closed_rows": sum(
                1
                for row in mandatory_rows
                if isinstance(row, dict) and row.get("status") == "CLOSED_PUBLIC_SOURCE"
            ),
            "missing_indispensable_ids": missing_ids,
            "total_rows": len(mandatory_rows),
        },
        "unsupported_outcomes": {
            "actual_HW29_condensation":"NOT_RUN_MISSING_PRINTED_BLOCKS",
            "linear_loads_and_recovery":"NOT_RUN_MISSING_PRINTED_MAPS",
            "mixed_shear":"NOT_RUN_MISSING_PRINTED_MAPS",
            "rank_patch_material_recovery":"NOT_RUN_PUBLIC_SOURCE_BLOCK",
            "shell_EADG2":"NOT_RUN_MISSING_SHELL_TRANSFORMATION",
        },
    }


def build_contract() -> dict[str, object]:
    build_certificate()
    identities: dict[str, object] = {}
    for relative in CONTRACT_INPUTS:
        raw = (ROOT / relative).read_bytes()
        identities[relative] = {"bytes": len(raw), "path": relative, "sha256": _sha(raw)}
    oracle_relative = Path(__file__).relative_to(ROOT).as_posix()
    oracle_raw = Path(__file__).read_bytes()
    identities[oracle_relative] = {
        "bytes": len(oracle_raw),
        "path": oracle_relative,
        "sha256": _sha(oracle_raw),
    }
    return {
        "candidate_id": CANDIDATE_ID,
        "input_identities": identities,
        "mechanics_execution": "NOT_RUN_PUBLIC_SOURCE_BLOCK",
        "production_paths": [],
        "schema": "anysolver.s4.e3-hw29-contract-v1",
        "scientific_terminal": TERMINAL,
    }


def build_output(contract_sha256: str) -> dict[str, object]:
    return {
        "candidate_id": CANDIDATE_ID,
        "certificate": build_certificate(),
        "component_terminal": TERMINAL,
        "contract_sha256": contract_sha256,
        "overall_release_terminal": RELEASE,
        "production_changed": False,
        "schema": "anysolver.s4.e3-hw29-output-v1",
        "status": "blocked",
    }


def _load_contract(path: Path, caller_sha256: str) -> str:
    try:
        if path.resolve(strict=True) != CONTRACT_PATH.resolve(strict=True):
            raise ContractError("contract path mismatch")
        raw = path.read_bytes()
        if _sha(raw) != caller_sha256:
            raise ContractError("contract raw hash mismatch")
        value = json.loads(
            raw.decode("utf-8"), object_pairs_hook=_pairs,
            parse_constant=lambda token: (_ for _ in ()).throw(ContractError(token)),
        )
        if not isinstance(value, dict) or raw != _canonical(value):
            raise ContractError("contract is not canonical")
        if value != build_contract():
            raise ContractError("contract semantic mismatch")
    except ContractError:
        raise
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, EvidenceError) as exc:
        raise ContractError(str(exc)) from exc
    return caller_sha256


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--certificate", action="store_true")
    modes.add_argument("--emit-contract", action="store_true")
    modes.add_argument("--run", action="store_true")
    parser.add_argument("--contract", type=Path)
    parser.add_argument("--contract-sha256")
    arguments = parser.parse_args(argv)
    try:
        if arguments.certificate:
            if arguments.contract is not None or arguments.contract_sha256 is not None:
                raise ContractError("contract arguments forbidden in certificate mode")
            sys.stdout.buffer.write(_canonical(build_certificate()))
            return 0
        if arguments.emit_contract:
            if arguments.contract is not None or arguments.contract_sha256 is not None:
                raise ContractError("contract arguments forbidden in emit mode")
            sys.stdout.buffer.write(_canonical(build_contract()))
            return 0
        if arguments.contract is None or arguments.contract_sha256 is None:
            raise ContractError("run mode requires caller-bound contract")
        contract_sha = _load_contract(arguments.contract, arguments.contract_sha256)
        sys.stdout.buffer.write(_canonical(build_output(contract_sha)))
    except ContractError as exc:
        sys.stdout.buffer.write(
            _canonical({"detail": str(exc), "terminal": "BLOCKED_E3_EVIDENCE_OR_REVIEW"})
        )
        return 2
    except (EvidenceError, OSError, AssertionError, ValueError) as exc:
        sys.stdout.buffer.write(
            _canonical({"detail": str(exc), "terminal": "BLOCKED_E3_EVIDENCE_OR_REVIEW"})
        )
        return 2
    except Exception as exc:
        sys.stdout.buffer.write(
            _canonical({"detail": f"{type(exc).__name__}: {exc}", "terminal": "BLOCKED_E3_EVIDENCE_OR_REVIEW"})
        )
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
