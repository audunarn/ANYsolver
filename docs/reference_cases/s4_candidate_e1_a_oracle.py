"""Exact standard-library oracle for the Candidate E1-A rank screen."""

from __future__ import annotations

import argparse
import ast
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "docs/reference_cases/s4_candidate_e1_a_contract.json"
CANDIDATE_ID = "candidate_e1.wg2020_n7_k0_independent_allman_q4_static_v1"
TERMINAL = "NO_GO_CANDIDATE_E1_A_RANK_DEFICIENCY"
REASON = "COMMON_DRILL_NULL_RANK_AT_MOST_17"
RELEASE = "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"

STATIC_INPUTS = {
    "plan": ("docs/agent_plans/S4_CANDIDATE_E1_ALLMAN_SESTRA_QUALIFICATION_PLAN.md", 5885, "16093C1B1E95AAC790E5AC0F4A6D19927782A0D24194108367B77BCDB5CA6BBE"),
    "derivation": ("docs/S4_CANDIDATE_E1_A_DERIVATION.md", 2666, "BF40E075122C5F53DD7335F3A6FF3649393B5E25B98490DC389CCF2619B747E2"),
    "baseline": ("docs/reference_cases/s4_candidate_e1_baseline.json", 2622, "EA7E81C38912F14CB89CFD98302B6A8478D878939F7CFC1E3A60439667A745C1"),
    "environment": ("docs/reference_cases/s4_candidate_e1_environment.json", 1330, "F2DB5FF809FE0ED35ABE398FBFCECD133F2E8C36E96D1AB5C79354784F7216DE"),
    "source_registry": ("docs/reference_cases/s4_candidate_e1_source_registry.json", 2628, "C25197408932746D04C0651D082D5435369CEF94CFAF03BD3A12F8521A24B375"),
    "test_inventory": ("docs/reference_cases/s4_candidate_e1_test_inventory.json", 1751, "3290ACA0B30CD8C23A2508543DC8889D1F0795F38CF237AF7E826833E230EA16"),
    "materials": ("docs/reference_cases/s4_candidate_e1_material_fixtures.json", 737, "F29886ED86AC83081E04D4A352D3F25BA304393DB5C0FA64A3BCF4338D4EFA07"),
    "identity": ("docs/reference_cases/s4_candidate_e1_a_identity.json", 802, "1A5D7A2E174A1BF7903DD4B188F56D7BDF2F1BC53639D3BE14FFFA5C010110FE"),
    "cases": ("docs/reference_cases/s4_candidate_e1_a_cases.json", 571, "F654F446ECDCED1F80FE86C092425D1AC95EA2F244FD0D20BEE80D52F95EE11A"),
}

ALLOWED_NEW_PATHS = [
    "docs/agent_plans/S4_CANDIDATE_E1_ALLMAN_SESTRA_QUALIFICATION_PLAN.md",
    "docs/S4_CANDIDATE_E1_A_DERIVATION.md",
    "docs/S4_CANDIDATE_E1_R_DERIVATION.md",
    "docs/S4_CANDIDATE_E1_QUALIFICATION_REPORT.md",
    "docs/S4_CANDIDATE_E1_A_INDEPENDENT_REVIEW.md",
    "docs/S4_CANDIDATE_E1_R_INDEPENDENT_REVIEW.md",
    "docs/reference_cases/s4_candidate_e1_baseline.json",
    "docs/reference_cases/s4_candidate_e1_environment.json",
    "docs/reference_cases/s4_candidate_e1_source_registry.json",
    "docs/reference_cases/s4_candidate_e1_material_fixtures.json",
    "docs/reference_cases/s4_candidate_e1_test_inventory.json",
    "docs/reference_cases/s4_candidate_e1_a_identity.json",
    "docs/reference_cases/s4_candidate_e1_a_cases.json",
    "docs/reference_cases/s4_candidate_e1_a_oracle.py",
    "docs/reference_cases/s4_candidate_e1_a_contract.json",
    "docs/reference_cases/s4_candidate_e1_a_output.json",
    "docs/reference_cases/s4_candidate_e1_r_identity.json",
    "docs/reference_cases/s4_candidate_e1_r_cases.json",
    "docs/reference_cases/s4_candidate_e1_r_oracle.py",
    "docs/reference_cases/s4_candidate_e1_r_contract.json",
    "docs/reference_cases/s4_candidate_e1_r_output.json",
    "docs/reference_cases/s4_candidate_e1_status.json",
    "tests/test_s4_candidate_e1_a_exact_rank.py",
    "tests/test_s4_candidate_e1_a_qualification.py",
    "tests/test_s4_candidate_e1_r_exact_regularizer.py",
    "tests/test_s4_candidate_e1_r_qualification.py",
    "tests/test_s4_candidate_e1_closeout.py",
]


class BaselineMismatch(Exception):
    pass


class ContractViolation(Exception):
    pass


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise BaselineMismatch(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _decode(raw: bytes) -> object:
    if raw.startswith(b"\xef\xbb\xbf") or b"\r" in raw or not raw.endswith(b"\n"):
        raise BaselineMismatch("invalid UTF-8/LF transport")
    try:
        return json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_pairs,
            parse_constant=lambda token: (_ for _ in ()).throw(BaselineMismatch(token)),
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BaselineMismatch(str(exc)) from exc


def _canonical(value: object) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
        + "\n"
    ).encode("utf-8")


def _verified_raw(path: str, size: int, sha256: str) -> bytes:
    try:
        raw = (ROOT / path).read_bytes()
    except OSError as exc:
        raise BaselineMismatch(f"missing input: {path}") from exc
    if len(raw) != size or _sha(raw) != sha256:
        raise BaselineMismatch(f"identity mismatch: {path}")
    if raw.startswith(b"\xef\xbb\xbf") or b"\r" in raw or not raw.endswith(b"\n"):
        raise BaselineMismatch(f"transport mismatch: {path}")
    return raw


def _verified_json(path: str, size: int, sha256: str) -> dict[str, object]:
    raw = _verified_raw(path, size, sha256)
    value = _decode(raw)
    if not isinstance(value, dict) or raw != _canonical(value):
        raise BaselineMismatch(f"noncanonical JSON: {path}")
    return value


def _canonical_lf_file(path: str, size: int, sha256: str) -> bytes:
    try:
        raw = (ROOT / path).read_bytes().replace(b"\r\n", b"\n")
    except OSError as exc:
        raise BaselineMismatch(f"missing baseline path: {path}") from exc
    if b"\r" in raw or len(raw) != size or _sha(raw) != sha256:
        raise BaselineMismatch(f"baseline identity mismatch: {path}")
    return raw


def _test_names(path: Path) -> list[str]:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    return [f"{path.relative_to(ROOT).as_posix()}::{node.name}" for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_")]


def _validate_baseline(values: dict[str, dict[str, object]]) -> None:
    baseline = values["baseline"]
    if baseline["authority"] != {
        "branch": "codex/s4-candidate-e1-allman-sestra-qualification",
        "e0_commit": "87b639499187736c59d87bc4aa8e6bd7f819d28b",
        "e0_tree": "c01fd5cab7b63325e6cb5b70000f4586d4788563",
        "production_qualification_base": "a9b45ca95303bc4b30b893fbb0d7177f9c98db03",
    }:
        raise BaselineMismatch("authority mismatch")
    for record in baseline["immutable_results"].values():
        raw = (ROOT / record["path"]).read_bytes()
        if _sha(raw) != record["sha256"]:
            raise BaselineMismatch(f"immutable result drift: {record['path']}")
    for record in baseline["predecessor_packet"].values():
        _verified_raw(record["path"], record["bytes"], record["sha256"])
    for path, record in baseline["production_sources"].items():
        _canonical_lf_file(path, record["canonical_lf_bytes"], record["canonical_lf_sha256"])

    inventory = values["test_inventory"]
    inherited = inventory["composition"]["inherited_85"]
    e0_inventory = _verified_json(inherited["path"], inherited["bytes"], inherited["sha256"])
    base75_record = e0_inventory["composition"]["base_75"]
    base75 = _verified_json(base75_record["path"], base75_record["bytes"], base75_record["sha256"])
    ordered_files: list[str] = []
    for record in base75["files"]:
        _canonical_lf_file(record["path"], record["canonical_lf_bytes"], record["canonical_lf_sha256"])
        ordered_files.append(record["path"])
    nodes = list(base75["collection"]["node_ids"])
    for record in e0_inventory["composition"]["appended_files"]:
        _canonical_lf_file(record["path"], record["canonical_lf_bytes"], record["canonical_lf_sha256"])
        ordered_files.append(record["path"])
    nodes.extend(e0_inventory["composition"]["appended_node_ids"])
    for key in ("e0_source_gate", "e0_closeout"):
        record = inventory["composition"][key]
        _canonical_lf_file(record["path"], record["canonical_lf_bytes"], record["canonical_lf_sha256"])
        names = _test_names(ROOT / record["path"])
        if len(names) != record["node_count"]:
            raise BaselineMismatch(f"node count mismatch: {record['path']}")
        nodes.extend(names)
        ordered_files.append(record["path"])
    joined = ("\n".join(nodes) + "\n").encode("utf-8")
    expected = inventory["accepted_pre_e1"]
    if len(nodes) != len(set(nodes)) or len(nodes) != expected["count"]:
        raise BaselineMismatch("accepted node cardinality mismatch")
    if len(joined) != expected["node_ids_canonical_lf_bytes"] or _sha(joined) != expected["node_ids_canonical_lf_sha256"]:
        raise BaselineMismatch("accepted node identity mismatch")
    if ordered_files != expected["ordered_files"]:
        raise BaselineMismatch("accepted file order mismatch")


def _validate_inputs() -> dict[str, dict[str, object]]:
    values: dict[str, dict[str, object]] = {}
    for name, (path, size, sha256) in STATIC_INPUTS.items():
        if path.endswith(".json"):
            values[name] = _verified_json(path, size, sha256)
        else:
            _verified_raw(path, size, sha256)
    _validate_baseline(values)
    if values["identity"]["candidate_id"] != CANDIDATE_ID or values["cases"]["candidate_id"] != CANDIDATE_ID:
        raise BaselineMismatch("candidate identity mismatch")
    if values["identity"]["edge_enrichment"]["interior_bubble_allowed"] is not False:
        raise BaselineMismatch("interior bubble not frozen out")
    return values


def _rank(matrix: list[list[Fraction]]) -> int:
    if not matrix:
        return 0
    a = [row[:] for row in matrix]
    rows, cols = len(a), len(a[0])
    rank = 0
    for col in range(cols):
        pivot = next((r for r in range(rank, rows) if a[r][col]), None)
        if pivot is None:
            continue
        a[rank], a[pivot] = a[pivot], a[rank]
        scale = a[rank][col]
        a[rank] = [value / scale for value in a[rank]]
        for row in range(rows):
            if row != rank and a[row][col]:
                factor = a[row][col]
                a[row] = [left - factor * right for left, right in zip(a[row], a[rank])]
        rank += 1
        if rank == rows:
            break
    return rank


def _solve_unique(matrix: list[list[Fraction]], rhs: list[Fraction]) -> list[Fraction]:
    augmented = [row[:] + [value] for row, value in zip(matrix, rhs)]
    rows, cols = len(augmented), len(matrix[0])
    pivot_row = 0
    pivots: list[int] = []
    for col in range(cols):
        pivot = next((r for r in range(pivot_row, rows) if augmented[r][col]), None)
        if pivot is None:
            continue
        augmented[pivot_row], augmented[pivot] = augmented[pivot], augmented[pivot_row]
        scale = augmented[pivot_row][col]
        augmented[pivot_row] = [value / scale for value in augmented[pivot_row]]
        for row in range(rows):
            if row != pivot_row and augmented[row][col]:
                factor = augmented[row][col]
                augmented[row] = [left - factor * right for left, right in zip(augmented[row], augmented[pivot_row])]
        pivots.append(col)
        pivot_row += 1
    if len(pivots) != cols:
        raise AssertionError("system is not unique")
    if any(all(value == 0 for value in row[:cols]) and row[cols] for row in augmented):
        raise AssertionError("system is inconsistent")
    solution = [Fraction(0) for _ in range(cols)]
    for row, col in enumerate(pivots):
        solution[col] = augmented[row][cols]
    return solution


S2 = [(0, 0), (1, 0), (0, 1), (1, 1), (2, 0), (2, 1), (0, 2), (1, 2)]


def _trace_system(exponents: list[tuple[int, int]], target: int) -> tuple[list[list[Fraction]], list[Fraction]]:
    matrix: list[list[Fraction]] = []
    rhs: list[Fraction] = []
    for edge in range(4):
        for degree in range(3):
            row: list[Fraction] = []
            for power_r, power_s in exponents:
                if edge in (0, 2):
                    row.append(Fraction((-1 if edge == 0 else 1) ** power_s if power_r == degree else 0))
                else:
                    row.append(Fraction((1 if edge == 1 else -1) ** power_r if power_s == degree else 0))
            matrix.append(row)
            rhs.append(Fraction(1 if edge == target and degree == 0 else -1 if edge == target and degree == 2 else 0))
    return matrix, rhs


def _rigid_and_g_rank(nodes: list[list[int]]) -> int:
    columns: list[list[Fraction]] = [[] for _ in range(7)]
    for x_raw, y_raw, _ in nodes:
        x, y = Fraction(x_raw), Fraction(y_raw)
        blocks = [
            (1, 0, 0, 0, 0, 0),
            (0, 1, 0, 0, 0, 0),
            (0, 0, 1, 0, 0, 0),
            (0, 0, y, 1, 0, 0),
            (0, 0, -x, 0, 1, 0),
            (-y, x, 0, 0, 0, 1),
            (0, 0, 0, 0, 0, 1),
        ]
        for column, block in zip(columns, blocks):
            column.extend(Fraction(value) for value in block)
    matrix = [[columns[col][row] for col in range(7)] for row in range(24)]
    return _rank(matrix)


def _d4_permutations() -> list[list[int]]:
    nodes = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
    transforms = [
        lambda r, s: (r, s),
        lambda r, s: (-s, r),
        lambda r, s: (-r, -s),
        lambda r, s: (s, -r),
        lambda r, s: (r, -s),
        lambda r, s: (-r, s),
        lambda r, s: (s, r),
        lambda r, s: (-s, -r),
    ]
    return [[nodes.index(transform(*node)) for node in nodes] for transform in transforms]


def _matvec(matrix: list[list[Fraction]], vector: list[Fraction]) -> list[Fraction]:
    return [sum(left * right for left, right in zip(row, vector)) for row in matrix]


def _certificate(cases: dict[str, object]) -> dict[str, object]:
    expected_coefficients = [
        [Fraction(1, 2), 0, Fraction(-1, 2), 0, Fraction(-1, 2), Fraction(1, 2), 0, 0],
        [Fraction(1, 2), Fraction(1, 2), 0, 0, 0, 0, Fraction(-1, 2), Fraction(-1, 2)],
        [Fraction(1, 2), 0, Fraction(1, 2), 0, Fraction(-1, 2), Fraction(-1, 2), 0, 0],
        [Fraction(1, 2), Fraction(-1, 2), 0, 0, 0, 0, Fraction(-1, 2), Fraction(1, 2)],
    ]
    edge_records = []
    for edge in range(4):
        matrix, rhs = _trace_system(S2, edge)
        solution = _solve_unique(matrix, rhs)
        if solution != expected_coefficients[edge]:
            raise AssertionError("serendipity edge solution mismatch")
        edge_records.append({"edge": edge, "equations": 12, "rank": _rank(matrix), "solution": [str(value) for value in solution]})
    extended, _ = _trace_system(S2 + [(2, 2)], 0)

    coefficient_matrix = [[Fraction(value) for value in row] for row in cases["edge_coefficient_system"]["matrix"]]
    coefficient_rhs = [Fraction(value) for value in cases["edge_coefficient_system"]["rhs"]]
    coefficient_solution = _solve_unique(coefficient_matrix, coefficient_rhs)
    incidence = [[Fraction(value) for value in row] for row in cases["incidence"]]
    common = [Fraction(1) for _ in range(4)]
    common_image = [sum(left * right for left, right in zip(row, common)) for row in incidence]
    d4_records = []
    for permutation in _d4_permutations():
        permuted = [[row[permutation[column]] for column in range(4)] for row in incidence]
        stacked_rank = _rank(incidence + permuted)
        if stacked_rank != 3:
            raise AssertionError("D4 row-space covariance failed")
        d4_records.append({"permutation": permutation, "shared_rowspace_rank": stacked_rank})

    h_map = [[Fraction(1), Fraction(2), Fraction(3), Fraction(4)], [Fraction(4), Fraction(3), Fraction(2), Fraction(1)]]
    h_common = _matvec(h_map, common_image)
    b_common = _matvec([[Fraction(2), Fraction(-3)]], h_common)
    mass_column = _matvec([[h_map[row][column] for row in range(2)] for column in range(4)], h_common)
    kqq_common = [Fraction(0), Fraction(0), Fraction(0)]
    kyq_common = [Fraction(0), Fraction(0)]
    schur_correction = _matvec([[Fraction(1), Fraction(2)], [Fraction(3), Fraction(4)], [Fraction(5), Fraction(6)]], kyq_common)
    condensed_common = [left - right for left, right in zip(kqq_common, schur_correction)]
    rigid_g_rank = _rigid_and_g_rank(cases["reference_nodes"])
    core_rank_upper = 20 - 6
    drill_rank_upper = _rank(incidence)
    full_rank_upper = core_rank_upper + drill_rank_upper
    if coefficient_solution != [Fraction(-1, 8), Fraction(1, 8)]:
        raise AssertionError("edge normalization mismatch")
    if common_image != [0, 0, 0, 0] or h_common != [0, 0] or b_common != [0] or mass_column != [0, 0, 0, 0] or condensed_common != [0, 0, 0] or rigid_g_rank != 7 or full_rank_upper >= 18:
        raise AssertionError("rank certificate did not close")
    return {
        "d4_numbering_covariance": d4_records,
        "edge_coefficient_solution": [str(value) for value in coefficient_solution],
        "incidence": {"common_image": [str(value) for value in common_image], "kernel_dimension": 1, "rank": drill_rank_upper},
        "null_inheritance": {
            "condensed_common_column": [str(value) for value in condensed_common],
            "mass_gram_common_column": [str(value) for value in mass_column],
            "premise_B_common": [str(value) for value in b_common],
            "premise_H_common": [str(value) for value in h_common],
            "status": "EXACT_ZERO_FACTOR_INFERENCE",
        },
        "q2_extension": {"nullity": 9 - _rank(extended), "rank": _rank(extended), "status": "EXCLUDED_BY_MINIMAL_S2_REGISTRATION"},
        "rank_theorem": {"augmented_rigid_common_drill_rank": rigid_g_rank, "core_rank_upper_bound": core_rank_upper, "full_rank_upper_bound": full_rank_upper, "required_rank": 18},
        "s2_edges": edge_records,
    }


def build_contract() -> dict[str, object]:
    values = _validate_inputs()
    oracle_raw = Path(__file__).read_bytes()
    identities = {
        name: {"bytes": size, "path": path, "sha256": sha256}
        for name, (path, size, sha256) in STATIC_INPUTS.items()
    }
    identities["oracle"] = {"bytes": len(oracle_raw), "path": Path(__file__).relative_to(ROOT).as_posix(), "sha256": _sha(oracle_raw)}
    return {
        "allowed_extent": {"modified": [".gitattributes"], "new_paths": ALLOWED_NEW_PATHS, "production_paths": []},
        "candidate_id": CANDIDATE_ID,
        "input_identities": identities,
        "proof_program": ["S2_UNISOLVENCE", "Q2_INTERIOR_AMBIGUITY_EXCLUDED", "EDGE_L_OVER_8_UNIQUENESS", "D4_NUMBERING_REVERSAL_COVARIANCE", "CYCLIC_INCIDENCE_RANK", "RIGID_PLUS_COMMON_DRILL_RANK", "ZERO_FACTOR_CONDENSATION_AND_MASS_NULL_INHERITANCE"],
        "schema": "anysolver.s4.candidate-e1-a-contract-v1",
        "scientific_terminal": {"reason": REASON, "value": TERMINAL},
        "terminal_precedence": ["BLOCKED_CANDIDATE_E1_BASELINE_MISMATCH", "BLOCKED_CANDIDATE_E1_NONDETERMINISTIC_EXECUTION", TERMINAL, "UNCLASSIFIED_CANDIDATE_E1_A", "PROVISIONAL_GO_CANDIDATE_E1_A_DNV_LINEAR_BUCKLING"],
    }


def build_output(contract_sha256: str) -> dict[str, object]:
    values = _validate_inputs()
    certificate = _certificate(values["cases"])
    return {
        "candidate_id": CANDIDATE_ID,
        "candidate_terminal": TERMINAL,
        "certificate": certificate,
        "contract_sha256": contract_sha256,
        "downstream_stages": {"buckling": "NOT_RUN_DUE_TO_EXACT_RANK_SCREEN", "dnv_material_response": "NOT_RUN_DUE_TO_EXACT_RANK_SCREEN", "locking_and_stability": "NOT_RUN_DUE_TO_EXACT_RANK_SCREEN", "nonlinear": "NOT_IN_E1_SCOPE"},
        "e1_r_combined_or_used": False,
        "immutable_results": {key: record["terminal"] for key, record in values["baseline"]["immutable_results"].items()},
        "overall_release_terminal": RELEASE,
        "production": {"legacy_shell_default": True, "public_api_changed": False, "selector_available": False, "serialization_changed": False},
        "reason": REASON,
        "schema": "anysolver.s4.candidate-e1-a-output-v1",
        "status": "complete",
    }


def _load_contract(path: Path, caller_sha256: str) -> str:
    try:
        if path.resolve(strict=True) != CONTRACT_PATH.resolve(strict=True):
            raise ContractViolation("contract path mismatch")
        raw = path.read_bytes()
        if _sha(raw) != caller_sha256:
            raise ContractViolation("contract raw hash mismatch")
    except ContractViolation:
        raise
    except OSError as exc:
        raise ContractViolation(str(exc)) from exc
    try:
        value = _decode(raw)
    except BaselineMismatch as exc:
        raise ContractViolation(str(exc)) from exc
    if not isinstance(value, dict) or raw != _canonical(value):
        raise ContractViolation("contract is not canonical")
    expected = build_contract()
    if value != expected:
        raise ContractViolation("contract semantic mismatch")
    return caller_sha256


def _blocked(terminal: str, detail: str) -> bytes:
    return _canonical({"detail": detail, "schema": "anysolver.s4.candidate-e1-blocked-v1", "status": "blocked", "terminal": terminal})


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--emit-contract", action="store_true")
    modes.add_argument("--run", action="store_true")
    parser.add_argument("--contract", type=Path)
    parser.add_argument("--contract-sha256")
    args = parser.parse_args(argv)
    try:
        if args.emit_contract:
            if args.contract is not None or args.contract_sha256 is not None:
                raise ContractViolation("contract arguments forbidden in emit mode")
            sys.stdout.buffer.write(_canonical(build_contract()))
            return 0
        if args.contract is None or args.contract_sha256 is None:
            raise ContractViolation("run mode requires caller-bound contract")
        contract_sha = _load_contract(args.contract, args.contract_sha256)
        sys.stdout.buffer.write(_canonical(build_output(contract_sha)))
        return 0
    except BaselineMismatch as exc:
        sys.stdout.buffer.write(_blocked("BLOCKED_CANDIDATE_E1_BASELINE_MISMATCH", str(exc)))
        return 2
    except ContractViolation as exc:
        sys.stdout.buffer.write(_blocked("BLOCKED_CANDIDATE_E1_NONDETERMINISTIC_EXECUTION", str(exc)))
        return 2
    except Exception as exc:
        sys.stdout.buffer.write(_blocked("BLOCKED_CANDIDATE_E1_NONDETERMINISTIC_EXECUTION", f"{type(exc).__name__}: {exc}"))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
