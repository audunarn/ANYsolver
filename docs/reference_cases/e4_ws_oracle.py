"""Exact necessary theorem for the frozen E4-WS local-multiplier route."""

from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
CASES_PATH = ROOT / "docs/reference_cases/e4_ws_cases.json"
CONTRACT_PATH = ROOT / "docs/reference_cases/e4_ws_contract.json"
STUDY_ID = "study_e4_ws.wg2020_local_weak_symmetry_feasibility_v1"
TERMINAL = "NO_GO_E4_WS_LOCAL_CONDENSATION_AND_RANK"
BLOCKED = "BLOCKED_E4_CONTRACT_NONDETERMINISM_OR_REVIEW"
RELEASE = "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"
CONTRACT_INPUTS = [
    "docs/agent_plans/S4_E4_VARIATIONAL_DRILL_CLOSURE_PLAN.md",
    "docs/E4_OPEN_CORE_IDENTITY.md",
    "docs/E4_WS_FEASIBILITY_THEOREM.md",
    "docs/reference_cases/e4_baseline.json",
    "docs/reference_cases/e4_environment.json",
    "docs/reference_cases/e4_test_inventory.json",
    "docs/reference_cases/e4_source_registry.json",
    "docs/reference_cases/e4_allowed_extent.json",
    "docs/reference_cases/e4_core_source_map.json",
    "docs/reference_cases/e4_ws_source_map.json",
    "docs/reference_cases/e4_core_contract.json",
    "docs/reference_cases/e4_core_output.json",
    "docs/reference_cases/e4_ws_cases.json",
]


class EvidenceError(Exception):
    """Frozen theorem evidence is invalid."""


class ContractError(Exception):
    """Caller-bound execution evidence is invalid."""


Matrix = list[list[Fraction]]


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
            raw.decode("utf-8"), object_pairs_hook=_pairs,
            parse_constant=lambda token: (_ for _ in ()).throw(EvidenceError(token)),
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EvidenceError(str(exc)) from exc
    if not isinstance(value, dict) or raw != _canonical(value):
        raise EvidenceError(f"noncanonical JSON: {path}")
    return value


def _zeros(rows: int, columns: int) -> Matrix:
    return [[Fraction(0) for _ in range(columns)] for _ in range(rows)]


def _transpose(matrix: Matrix) -> Matrix:
    return [list(column) for column in zip(*matrix)] if matrix else []


def _rank(matrix: Matrix) -> int:
    if not matrix:
        return 0
    work = [row[:] for row in matrix]
    row_count, column_count = len(work), len(work[0])
    rank = 0
    for column in range(column_count):
        pivot = next((row for row in range(rank, row_count) if work[row][column]), None)
        if pivot is None:
            continue
        work[rank], work[pivot] = work[pivot], work[rank]
        scale = work[rank][column]
        work[rank] = [value / scale for value in work[rank]]
        for row in range(row_count):
            if row != rank and work[row][column]:
                factor = work[row][column]
                work[row] = [a - factor * b for a, b in zip(work[row], work[rank])]
        rank += 1
    return rank


def _validate_cases(cases: dict[str, object]) -> None:
    if cases.get("schema") != "anysolver.e4.ws-cases-v1" or cases.get("study_id") != STUDY_ID:
        raise EvidenceError("WS case identity mismatch")
    requirements = cases.get("frozen_requirements")
    if requirements != {
        "added_energy": False,
        "external_coordinates": 24,
        "finite_condensed_psd_rank": 18,
        "global_mixed_unknown": False,
        "local_multiplier_dimension": "m>0",
        "local_multiplier_exactly_condensed": True,
        "regularization": False,
    }:
        raise EvidenceError("WS simultaneous requirements changed")
    expected = cases.get("expected")
    if expected != {"local_multiplier_schur_exists": False, "terminal": TERMINAL}:
        raise EvidenceError("WS expected theorem changed")
    alternatives = cases.get("alternatives_required_by_theorem")
    if alternatives != [
        "retain_saddle_multiplier",
        "reduce_external_coordinates_to_ker(C)",
        "add_multiplier_compliance_or_regularization",
        "add_primal_penalty_or_stabilization",
    ]:
        raise EvidenceError("WS theorem alternatives are not total")


def build_certificate() -> dict[str, object]:
    cases = _load_json(CASES_PATH)
    _validate_cases(cases)
    # A four-row exact witness is sufficient because the open core has four
    # independent drill-null coordinates.  The theorem itself holds for every
    # m>0; this witness makes all dimension and rank consequences explicit.
    multiplier_dimension = 4
    k0 = _zeros(24, 24)
    for index in range(14):
        k0[index][index] = Fraction(1)
    c = _zeros(multiplier_dimension, 24)
    for row in range(multiplier_dimension):
        c[row][20 + row] = Fraction(1)
    zero_block = _zeros(multiplier_dimension, multiplier_dimension)
    kkt = [
        k0[row] + _transpose(c)[row] for row in range(24)
    ] + [c[row] + zero_block[row] for row in range(multiplier_dimension)]
    penalty_completion = [row[:] for row in k0]
    for row in c:
        for i, left in enumerate(row):
            for j, right in enumerate(row):
                penalty_completion[i][j] += left * right
    if _rank(k0) != 14 or _rank(c) != 4 or _rank(zero_block) != 0:
        raise EvidenceError("WS exact witness ranks changed")
    if _rank(penalty_completion) != 18:
        raise EvidenceError("WS prohibited regularized witness did not expose rank tradeoff")

    proof_cases = cases.get("proof_cases")
    if not isinstance(proof_cases, list) or [row.get("id") for row in proof_cases if isinstance(row, dict)] != [
        "nonzero_constraint", "coordinate_reduction", "zero_constraint"
    ]:
        raise EvidenceError("WS proof cases changed")
    external_after_reduction = 24 - _rank(c)
    return {
        "alternatives": {
            "add_multiplier_compliance_or_regularization": "VIOLATES_ZERO_ADDED_ENERGY",
            "add_primal_penalty_or_stabilization": "VIOLATES_ZERO_ADDED_ENERGY",
            "reduce_external_coordinates_to_ker_C": {
                "dimension": external_after_reduction,
                "violates_24_unconstrained": external_after_reduction != 24,
            },
            "retain_saddle_multiplier": "VIOLATES_NO_GLOBAL_MIXED_UNKNOWN",
        },
        "exact_witness": {
            "C_rank": _rank(c),
            "K0_rank": _rank(k0),
            "KKT_rank": _rank(kkt),
            "lambda_block_rank": _rank(zero_block),
            "prohibited_CtC_completion_rank": _rank(penalty_completion),
        },
        "local_condensation": {
            "d_stationarity_lambda_d_lambda_rank": 0,
            "finite_multiplier_schur_exists": False,
            "stationarity_lambda": "C*q=0_contains_no_lambda",
            "unique_lambda_at_fixed_q": False,
        },
        "scope": {
            "counterexample_functional_found": False,
            "inf_sup_or_macroelement_work": "STOPPED_NECESSARY_THEOREM",
            "weak_symmetry_methods_generally_impossible": False,
        },
        "study_id": STUDY_ID,
        "terminal": TERMINAL,
        "theorem": "FIVE_FROZEN_REQUIREMENTS_CANNOT_HOLD_SIMULTANEOUSLY",
    }


def build_contract() -> dict[str, object]:
    build_certificate()
    identities: dict[str, object] = {}
    for relative in CONTRACT_INPUTS:
        raw = (ROOT / relative).read_bytes()
        identities[relative] = {"bytes": len(raw), "path": relative, "sha256": _sha(raw)}
    oracle_path = Path(__file__).relative_to(ROOT).as_posix()
    oracle_raw = Path(__file__).read_bytes()
    identities[oracle_path] = {
        "bytes": len(oracle_raw), "path": oracle_path, "sha256": _sha(oracle_raw)
    }
    return {
        "core_prerequisite": "GO_E4_OPEN_CORE_IDENTITY",
        "input_identities": identities,
        "production_paths": [],
        "proof_program": [
            "ZERO_MULTIPLIER_BLOCK_HAS_NO_INVERSE",
            "EXACT_CONSTRAINT_REDUCES_EXTERNAL_DIMENSION",
            "C_ZERO_CANNOT_LIFT_CORE_RANK",
            "EVERY_ESCAPE_VIOLATES_A_FROZEN_REQUIREMENT",
        ],
        "schema": "anysolver.s4.e4-ws-contract-v1",
        "scientific_terminal": TERMINAL,
        "study_id": STUDY_ID,
    }


def build_output(contract_sha256: str) -> dict[str, object]:
    return {
        "certificate": build_certificate(),
        "contract_sha256": contract_sha256,
        "overall_release_terminal": RELEASE,
        "production_changed": False,
        "schema": "anysolver.s4.e4-ws-output-v1",
        "status": "no_go",
        "study_id": STUDY_ID,
        "terminal": TERMINAL,
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


def _blocked(detail: str) -> bytes:
    return _canonical({"detail": detail, "status": "blocked", "terminal": BLOCKED})


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
        return 0
    except (EvidenceError, ContractError, OSError, AssertionError, ValueError) as exc:
        sys.stdout.buffer.write(_blocked(str(exc)))
        return 2
    except Exception as exc:
        sys.stdout.buffer.write(_blocked(f"{type(exc).__name__}: {exc}"))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
