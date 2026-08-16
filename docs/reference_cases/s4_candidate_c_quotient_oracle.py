from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]

INPUTS = {
    "governing_plan": (
        "docs/agent_plans/S4_CANDIDATE_C_LINEAR_QUOTIENT_QUALIFICATION_PLAN.md",
        4044,
        "82762B0FAD7CC200B76C6262D3B2DFEDAA0E2261FD5E7DF1195F8BAEA85D8901",
    ),
    "derivation": (
        "docs/S4_CANDIDATE_C_QUOTIENT_DERIVATION.md",
        3962,
        "447AB70BE8D34A08FFAAE98C6FA5583A15DE7C384789AA8C31838A5B7FFB6ACE",
    ),
    "cases": (
        "docs/reference_cases/s4_candidate_c_quotient_cases.json",
        1858,
        "B41360811714ED7A52B40F6ED282EA9F89C91A6FD0FE818F7A0AA51CA9A84936",
    ),
    "test_inventory": (
        "docs/reference_cases/s4_candidate_c_quotient_test_inventory.json",
        10598,
        "2A79F6E5F1683BC6D2F8FD049DFDBA9FF0457EDE486F1F9B0ACA8CEFCC5AA592",
    ),
    "a_open_contract": (
        "docs/reference_cases/s4_candidate_a_open_contract.json",
        5539,
        "7A9334964FB9A248EA1D44653C04E1F71731B3E605B053434CE7F252CCAB0D92",
    ),
    "a_open_output": (
        "docs/reference_cases/s4_candidate_a_open_output.json",
        2644,
        "C42911E11BB1F1FA091F29FD0E3F5A3617310EF5F06C686E57C013171242B63C",
    ),
    "a1_certificate": (
        "docs/reference_cases/s4_candidate_a_open_a1_certificate.json",
        3902,
        "2198458DCDC7EFB4684B5CC59ADAF6E9A0EECF381951CBDD21B286D6DB11097C",
    ),
    "a2_certificate": (
        "docs/reference_cases/s4_candidate_a_open_a2_certificate.json",
        3196,
        "68691E4F1F23E23ED7DF00C4210436BDD1A730ADB58ED3E755E15CC01ECC5F3B",
    ),
    "a_open_review": (
        "docs/S4_CANDIDATE_A_OPEN_INDEPENDENT_REVIEW.md",
        3792,
        "1B7280D6534C9FA5B444F6B0867FC344575BC21BB6C38A97C398AB8A83116C6A",
    ),
    "accepted_a_cases": (
        "docs/reference_cases/s4_stage_m_candidate_a_discretization_cases.json",
        6616,
        "BB29F6AE7AE53E961C992BBC2EA764D50B73F935C9B5F9C21C1E21462DCC3E9C",
    ),
    "candidate_b_output": (
        "docs/reference_cases/s4_stage_m_mechanics_output.json",
        5824196,
        "3A26052DB79CE914FF8A1FCA7835F3B86C15F1D351754B45CA904753D8EFDA0D",
    ),
    "rank_four_output": (
        "docs/reference_cases/s4_drill_constraint_oracle_output.json",
        1434454,
        "8005C6D285263E33FF7F6D4B5138D5FBE4EFAB6A95834C401F94AF044ACD9E1B",
    ),
    "environment": (
        "docs/reference_cases/s4_candidate_a_open_environment.json",
        2870,
        "1348DF6CE0DBC19BE84A0A28243820EAFDD7EA361AB78A5F586EBC98391D28F5",
    ),
    "source_registry": (
        "docs/reference_cases/s4_candidate_a_open_source_registry.json",
        2017,
        "8EF2E09B76046A4070A7A2BCDAC52EC16A25D50C7557F789335AC6173E5A6986",
    ),
}

BASE_COMMIT = "2cb8c53cd1097380c872ba2802ec0eacc5198304"
BASE_TREE = "f95d74e3ed1bb760f622e188f75f62a8b7ae43f6"
CANDIDATE_ID = "candidate_c.d4.span_1_rs.l2_quotient_v1"
CANDIDATE_TERMINAL = "NO_GO_CANDIDATE_C_QUOTIENT_INF_SUP"
RELEASE_TERMINAL = "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"
CONTRACT_PATH = ROOT / "docs/reference_cases/s4_candidate_c_quotient_contract.json"


class InputIdentityError(RuntimeError):
    pass


class ContractError(RuntimeError):
    pass


class ProofError(RuntimeError):
    pass


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def _canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise InputIdentityError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _canonical_lf(raw: bytes) -> bytes:
    if raw.startswith(b"\xef\xbb\xbf"):
        raise InputIdentityError("UTF-8 BOM is forbidden")
    without_crlf = raw.replace(b"\r\n", b"")
    if b"\r" in without_crlf:
        raise InputIdentityError("lone CR is forbidden")
    if b"\r\n" in raw and b"\n" in without_crlf:
        raise InputIdentityError("mixed newlines are forbidden")
    return raw.replace(b"\r\n", b"\n")


def _parse_json(raw: bytes, *, canonical: bool) -> Any:
    if raw.startswith(b"\xef\xbb\xbf") or b"\r" in raw or not raw.endswith(b"\n"):
        raise InputIdentityError("JSON transport must be UTF-8/LF")
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_no_duplicates,
            parse_constant=lambda token: (_ for _ in ()).throw(
                InputIdentityError(f"nonfinite JSON token: {token}")
            ),
        )
    except UnicodeDecodeError as exc:
        raise InputIdentityError("JSON is not UTF-8") from exc
    if canonical and _canonical_bytes(value) != raw:
        raise InputIdentityError("JSON is not canonical")
    return value


def _read_input(name: str) -> bytes:
    relative, size, digest = INPUTS[name]
    canonical = _canonical_lf((ROOT / relative).read_bytes())
    if len(canonical) != size or _sha(canonical) != digest:
        raise InputIdentityError(f"identity mismatch: {name}")
    return canonical


def _fraction_text(value: Fraction) -> str:
    return f"{value.numerator}/{value.denominator}"


def _dot(left: list[Fraction], right: list[Fraction]) -> Fraction:
    if len(left) != len(right):
        raise ProofError("dot-product dimension mismatch")
    return sum((a * b for a, b in zip(left, right)), Fraction(0))


def _norm_squared(values: list[Fraction]) -> Fraction:
    return _dot(values, values)


def _matvec(matrix: list[list[Fraction]], vector: list[Fraction]) -> list[Fraction]:
    return [_dot(row, vector) for row in matrix]


def _kron(left: list[list[Fraction]], right: list[list[Fraction]]) -> list[list[Fraction]]:
    return [
        [left_value * right_value for left_value in left_row for right_value in right_row]
        for left_row in left
        for right_row in right
    ]


def _zeros(rows: int, columns: int) -> list[list[Fraction]]:
    return [[Fraction(0) for _ in range(columns)] for _ in range(rows)]


def _hstack(left: list[list[Fraction]], right: list[list[Fraction]]) -> list[list[Fraction]]:
    if len(left) != len(right):
        raise ProofError("horizontal stack dimension mismatch")
    return [a + b for a, b in zip(left, right)]


def _rank(matrix: list[list[Fraction]]) -> int:
    if not matrix:
        return 0
    columns = len(matrix[0])
    if any(len(row) != columns for row in matrix):
        raise ProofError("ragged exact matrix")
    work = [row[:] for row in matrix]
    pivot_row = 0
    for column in range(columns):
        pivot = next(
            (row for row in range(pivot_row, len(work)) if work[row][column]),
            None,
        )
        if pivot is None:
            continue
        work[pivot_row], work[pivot] = work[pivot], work[pivot_row]
        pivot_value = work[pivot_row][column]
        work[pivot_row] = [value / pivot_value for value in work[pivot_row]]
        for row in range(len(work)):
            if row == pivot_row or not work[row][column]:
                continue
            scale = work[row][column]
            work[row] = [
                work[row][entry] - scale * work[pivot_row][entry]
                for entry in range(columns)
            ]
        pivot_row += 1
        if pivot_row == len(work):
            break
    return pivot_row


def _free_maps(n: int) -> tuple[list[list[Fraction]], list[list[Fraction]]]:
    incidence = _zeros(n + 1, n)
    unsigned = _zeros(n + 1, n)
    for cell in range(n):
        incidence[cell][cell] = Fraction(-1)
        incidence[cell + 1][cell] = Fraction(1)
        unsigned[cell][cell] = Fraction(1)
        unsigned[cell + 1][cell] = Fraction(1)
    return incidence, unsigned


def _clamped_maps(n: int) -> tuple[list[list[Fraction]], list[list[Fraction]]]:
    difference = _zeros(n - 1, n)
    unsigned = _zeros(n - 1, n)
    for node in range(1, n):
        difference[node - 1][node - 1] = Fraction(-1)
        difference[node - 1][node] = Fraction(1)
        unsigned[node - 1][node - 1] = Fraction(1)
        unsigned[node - 1][node] = Fraction(1)
    return difference, unsigned


def _free_transpose(n: int) -> list[list[Fraction]]:
    incidence, unsigned = _free_maps(n)
    a = Fraction(1, 2 * n)
    count = n * n
    zero = _zeros((n + 1) ** 2, count)
    alpha_u = [[a * value / 2 for value in row] for row in _kron(incidence, unsigned)]
    alpha_v = [[-a * value / 2 for value in row] for row in _kron(unsigned, incidence)]
    alpha_psi = [[a * a * value for value in row] for row in _kron(unsigned, unsigned)]
    beta_psi = [[a * a * value / 3 for value in row] for row in _kron(incidence, incidence)]
    return _hstack(alpha_u, zero) + _hstack(alpha_v, zero) + _hstack(alpha_psi, beta_psi)


def _clamped_transpose(n: int) -> list[list[Fraction]]:
    difference, unsigned = _clamped_maps(n)
    a = Fraction(1, 2 * n)
    count = n * n
    zero = _zeros((n - 1) ** 2, count)
    alpha_u = [[a * value / 2 for value in row] for row in _kron(difference, unsigned)]
    alpha_v = [[-a * value / 2 for value in row] for row in _kron(unsigned, difference)]
    alpha_psi = [[a * a * value for value in row] for row in _kron(unsigned, unsigned)]
    beta_psi = [[a * a * value / 3 for value in row] for row in _kron(difference, difference)]
    return _hstack(alpha_u, zero) + _hstack(alpha_v, zero) + _hstack(alpha_psi, beta_psi)


def _free_witness(n: int) -> list[Fraction]:
    return [Fraction((index + 1) * (n - index)) for index in range(n)]


def _clamped_witness(n: int) -> list[Fraction]:
    centre = Fraction(n - 1, 2)
    mean_square = Fraction(n * n - 1, 12)
    return [
        (Fraction(index) - centre) ** 2 - mean_square
        for index in range(n)
    ]


def _tensor_vector(left: list[Fraction], right: list[Fraction]) -> list[Fraction]:
    return [a * b for a in left for b in right]


def _local_constant_row(a: Fraction) -> list[Fraction]:
    zero = [Fraction(0)] * 3
    return (
        [-a / 2, a / 2, *zero, a * a]
        + [-a / 2, -a / 2, *zero, a * a]
        + [a / 2, -a / 2, *zero, a * a]
        + [a / 2, a / 2, *zero, a * a]
    )


def _finite_differences(values: list[Fraction]) -> list[list[Fraction]]:
    result = [values]
    while len(result[-1]) > 1:
        prior = result[-1]
        result.append([prior[index + 1] - prior[index] for index in range(len(prior) - 1)])
    return result


def _preflight() -> dict[str, Any]:
    values: dict[str, Any] = {}
    for name, (relative, _, _) in INPUTS.items():
        raw = _read_input(name)
        if relative.endswith(".json"):
            values[name] = _parse_json(
                raw,
                canonical=name
                not in {"accepted_a_cases", "source_registry"},
            )

    cases = values["cases"]
    if cases["authority"] != {"base_commit": BASE_COMMIT, "base_tree": BASE_TREE}:
        raise InputIdentityError("Candidate-C base identity drift")
    if cases["candidate"]["id"] != CANDIDATE_ID:
        raise InputIdentityError("Candidate-C identity drift")
    if cases["candidate"]["primal_operator"] != "byte_equal_candidate_a_a2_C":
        raise InputIdentityError("Candidate-C primal operator drift")
    if cases["candidate"]["quotient"] != "Lambda/ker(C_adm^T)":
        raise InputIdentityError("Candidate-C quotient drift")
    if cases["corroborative_n"] != [4, 8, 16, 32]:
        raise InputIdentityError("corroborative mesh sequence drift")
    if any(cases["exclusions"].values()):
        raise InputIdentityError("Candidate-C exclusion drift")

    inventory = values["test_inventory"]
    nodes = inventory["collection"]["node_ids"]
    node_bytes = ("\n".join(nodes) + "\n").encode("utf-8")
    if len(nodes) != 75 or len(set(nodes)) != 75:
        raise InputIdentityError("accepted test inventory count drift")
    if len(node_bytes) != inventory["collection"]["node_ids_canonical_lf_bytes"]:
        raise InputIdentityError("accepted node-list size drift")
    if _sha(node_bytes) != inventory["collection"]["node_ids_canonical_lf_sha256"]:
        raise InputIdentityError("accepted node-list hash drift")
    for record in inventory["files"]:
        canonical = _canonical_lf((ROOT / record["path"]).read_bytes())
        if len(canonical) != record["canonical_lf_bytes"] or _sha(canonical) != record["canonical_lf_sha256"]:
            raise InputIdentityError(f"accepted test file drift: {record['path']}")

    a_output = values["a_open_output"]
    if a_output["pair_terminal"] != "NO_GO_CANDIDATE_A_DISCRETE_PAIR":
        raise InputIdentityError("Candidate-A terminal drift")
    if a_output["overall_release_terminal"] != RELEASE_TERMINAL:
        raise InputIdentityError("Candidate-A release drift")
    if values["a1_certificate"]["result"]["candidate_terminal"] != "PROVEN_FAIL_CANDIDATE_A1_FLAT_RANK":
        raise InputIdentityError("A1 certificate drift")
    if values["a2_certificate"]["terminal"]["terminal"] != "PROVEN_FAIL_CANDIDATE_A2_INF_SUP":
        raise InputIdentityError("raw A2 certificate drift")
    if values["candidate_b_output"]["candidate_terminal"] != "NO_GO_CANDIDATE_B":
        raise InputIdentityError("Candidate-B terminal drift")
    if values["rank_four_output"]["scientific_summary"]["outcome"] != RELEASE_TERMINAL:
        raise InputIdentityError("rank-four terminal drift")
    if values["environment"]["oracle_runtime"]["dependencies"] != "python_standard_library_only":
        raise InputIdentityError("oracle environment drift")
    if values["source_registry"]["remote_source_required"] is not False:
        raise InputIdentityError("offline source boundary drift")
    return values


def _proof() -> dict[str, Any]:
    free_norms = []
    free_actions = []
    for n in range(1, 13):
        incidence, _ = _free_maps(n)
        witness = _free_witness(n)
        witness_norm = _norm_squared(witness)
        action_norm = _norm_squared(_matvec(incidence, witness))
        expected_norm = Fraction(n * (n + 1) * (n + 2) * (n * n + 2 * n + 2), 30)
        expected_action = Fraction(n * (n + 1) * (n + 2), 3)
        if witness_norm != expected_norm or action_norm != expected_action:
            raise ProofError("free all-n polynomial identity failed")
        free_norms.append(witness_norm)
        free_actions.append(action_norm)
    if any(_finite_differences(free_norms)[6]) or any(_finite_differences(free_actions)[4]):
        raise ProofError("free polynomial degree certificate failed")

    clamped_norms = []
    clamped_actions = []
    for n in range(1, 13):
        difference, _ = _clamped_maps(n)
        witness = _clamped_witness(n)
        witness_norm = _norm_squared(witness)
        action_norm = _norm_squared(_matvec(difference, witness)) if n > 1 else Fraction(0)
        expected_norm = Fraction(n * (n * n - 1) * (n * n - 4), 180)
        expected_action = Fraction(n * (n - 1) * (n - 2), 3)
        if witness_norm != expected_norm or action_norm != expected_action:
            raise ProofError("clamped all-n polynomial identity failed")
        clamped_norms.append(witness_norm)
        clamped_actions.append(action_norm)
    if any(_finite_differences(clamped_norms)[6]) or any(_finite_differences(clamped_actions)[4]):
        raise ProofError("clamped polynomial degree certificate failed")

    rank_samples = []
    for n in (3, 4, 5, 8):
        free_rank = _rank(_free_transpose(n))
        clamped_rank = _rank(_clamped_transpose(n))
        if free_rank != 2 * n * n:
            raise ProofError("free transpose must be injective")
        if clamped_rank != 2 * n * n - (2 * n + 1):
            raise ProofError("clamped complete dual-kernel dimension drift")
        rank_samples.append(
            {
                "clamped_kernel_dimension": 2 * n + 1,
                "clamped_rank": clamped_rank,
                "free_rank": free_rank,
                "n": n,
            }
        )

    bounds = []
    prior_free: Fraction | None = None
    prior_clamped: Fraction | None = None
    for n in (4, 8, 16, 32):
        free = Fraction(10, n * n + 2 * n + 2)
        clamped = Fraction(30, (n + 1) * (n + 2))
        if free <= 0 or clamped <= 0:
            raise ProofError("quotient witness bound must be positive")
        if prior_free is not None and not (free < prior_free and clamped < prior_clamped):
            raise ProofError("quotient witness bounds must decrease")
        prior_free, prior_clamped = free, clamped
        x = _clamped_witness(n)
        r = [Fraction(index) - Fraction(n - 1, 2) for index in range(n)]
        if sum(x, Fraction(0)) or _dot(x, r):
            raise ProofError("clamped witness is not quotient-orthogonal")
        difference, _ = _clamped_maps(n)
        if not any(_matvec(difference, x)):
            raise ProofError("clamped quotient witness action vanished")
        bounds.append(
            {
                "clamped_upper_bound": _fraction_text(clamped),
                "free_upper_bound": _fraction_text(free),
                "n": n,
            }
        )

    a2 = _parse_json(_read_input("a2_certificate"), canonical=True)
    accepted_constant = [
        Fraction(value)
        for value in a2["counterexample"]["local_rows"]["normalized_1_full"]
    ]
    if _local_constant_row(Fraction(1)) != accepted_constant:
        raise ProofError("Candidate-C constant row is not byte-equal A2 mechanics")
    if a2["counterexample"]["assembly"]["c_adm_transpose_mu"] != ["0/1"] * 6:
        raise ProofError("raw A2 hostile-control annihilator drift")
    if a2["counterexample"]["multiplier"]["l2_norm_squared"] != "4/1":
        raise ProofError("raw A2 hostile-control norm drift")

    return {
        "all_n": {
            "clamped": {
                "bound": "30/((n+1)(n+2))",
                "limit": "0",
                "positive_near_kernel": True,
                "quotient_representative": "exact_minimum_physical_L2",
            },
            "free": {
                "bound": "10/(n^2+2n+2)",
                "dual_kernel_dimension": "0",
                "limit": "0",
                "positive_near_kernel": True,
            },
            "proof_arithmetic": "fractions.Fraction_and_polynomial_degree_identity",
        },
        "bounds": bounds,
        "local": {
            "constant_row_byte_equal_accepted_a2": True,
            "mode_mass": "a^2",
            "rs_drill_row": ["a^2/3", "-a^2/3", "a^2/3", "-a^2/3"],
        },
        "rank_samples": rank_samples,
        "raw_a2_hostile_control": {
            "beta": "0/1",
            "multiplier_norm_squared": "4/1",
            "terminal": "PROVEN_FAIL_CANDIDATE_A2_INF_SUP",
        },
    }


def _contract() -> dict[str, Any]:
    oracle_raw = Path(__file__).read_bytes()
    if b"\r" in oracle_raw or not oracle_raw.endswith(b"\n"):
        raise InputIdentityError("oracle source transport must be LF")
    return {
        "allowed_extent": {
            "modified": [".gitattributes"],
            "new_prefixes": [
                "docs/agent_plans/S4_CANDIDATE_C_",
                "docs/S4_CANDIDATE_C_QUOTIENT_",
                "docs/reference_cases/s4_candidate_c_quotient_",
                "tests/test_s4_candidate_c_quotient_",
            ],
            "production_paths": [],
        },
        "authority": {"base_commit": BASE_COMMIT, "base_tree": BASE_TREE},
        "candidate": {
            "id": CANDIDATE_ID,
            "primal_constraint_change": False,
            "quotient": "minimum_physical_L2_representative_modulo_exact_dual_kernel",
        },
        "execution": {
            "arithmetic": "fractions.Fraction",
            "finite_rotation": False,
            "high_precision_shards": False,
            "interval_arithmetic": False,
            "nonlinear": False,
            "numerical_svd_authoritative": False,
            "performance": False,
            "repeat_fresh_processes": 2,
        },
        "exclusions": _parse_json(_read_input("cases"), canonical=True)["exclusions"],
        "identities": {
            name: {
                "canonical_lf_bytes": size,
                "canonical_lf_sha256": digest,
                "path": path,
            }
            for name, (path, size, digest) in INPUTS.items()
        }
        | {
            "oracle": {
                "canonical_lf_bytes": len(oracle_raw),
                "canonical_lf_sha256": _sha(oracle_raw),
                "path": "docs/reference_cases/s4_candidate_c_quotient_oracle.py",
            }
        },
        "proof": {
            "authoritative_families": ["free_unit_square_all_n", "fully_clamped_unit_square_all_n"],
            "corroborative_n": [4, 8, 16, 32],
            "required_results": [
                "raw_A2_hostile_control",
                "free_injectivity",
                "clamped_complete_dual_kernel",
                "quotient_orthogonality",
                "positive_near_kernel",
                "all_n_rational_upper_bounds_to_zero",
            ],
        },
        "schema": "anysolver.s4.candidate-c-quotient-contract-v1",
        "terminals": {
            "failure": CANDIDATE_TERMINAL,
            "incomplete": "UNCLASSIFIED_CANDIDATE_C_LINEAR_QUOTIENT",
            "provisional_pass": "PROVISIONAL_GO_CANDIDATE_C_LINEAR_QUOTIENT",
            "release": RELEASE_TERMINAL,
        },
    }


def _load_contract(path: Path, expected_sha256: str) -> tuple[dict[str, Any], str]:
    resolved = path.resolve(strict=True)
    if resolved != CONTRACT_PATH.resolve(strict=True):
        raise ContractError("contract path is not the registered path")
    raw = path.read_bytes()
    digest = _sha(raw)
    if digest != expected_sha256.upper():
        raise ContractError("caller-bound contract identity mismatch")
    parsed = _parse_json(raw, canonical=True)
    if parsed != _contract():
        raise ContractError("contract content mismatch")
    return parsed, digest


def _result(contract_sha256: str) -> dict[str, Any]:
    proof = _proof()
    return {
        "candidate_id": CANDIDATE_ID,
        "candidate_terminal": CANDIDATE_TERMINAL,
        "contract_sha256": contract_sha256,
        "execution": {
            "arithmetic": "fractions.Fraction",
            "finite_rotation_run": False,
            "high_precision_shards_run": False,
            "interval_arithmetic_run": False,
            "nonlinear_run": False,
            "performance_run": False,
        },
        "exclusions": _parse_json(_read_input("cases"), canonical=True)["exclusions"],
        "identities": {
            name: digest for name, (_, _, digest) in INPUTS.items()
        }
        | {"oracle": _sha(Path(__file__).read_bytes())},
        "mode": "exact_linear_quotient_necessary_screen",
        "overall_release_terminal": RELEASE_TERMINAL,
        "preserved": {
            "candidate_a_pair_terminal": "NO_GO_CANDIDATE_A_DISCRETE_PAIR",
            "candidate_b_terminal": "NO_GO_CANDIDATE_B",
            "legacy_shell_default": True,
            "rank_four_terminal": RELEASE_TERMINAL,
        },
        "proof": proof,
        "schema": "anysolver.s4.candidate-c-quotient-output-v1",
        "status": "complete",
        "terminal_reason": "positive_quotient_near_kernel_has_O(n^-2)_upper_bound",
        "test_inventory": {
            "count": 75,
            "node_ids_sha256": "AA024AA5E14FAE296B854F6E2DDE289DE5978C6B795BE8D2CE58A12B7A170CC4",
        },
    }


def _blocked(terminal: str) -> bytes:
    return _canonical_bytes(
        {
            "candidate_id": CANDIDATE_ID,
            "overall_release_terminal": RELEASE_TERMINAL,
            "schema": "anysolver.s4.candidate-c-quotient-blocked-v1",
            "status": "blocked",
            "terminal": terminal,
        }
    )


def _main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--emit-contract", action="store_true")
    mode.add_argument("--run", action="store_true")
    parser.add_argument("--contract", type=Path)
    parser.add_argument("--contract-sha256")
    arguments = parser.parse_args()
    try:
        _preflight()
        if arguments.emit_contract:
            if arguments.contract is not None or arguments.contract_sha256 is not None:
                raise ContractError("contract arguments are invalid in emit mode")
            sys.stdout.buffer.write(_canonical_bytes(_contract()))
            return 0
        if arguments.contract is None or arguments.contract_sha256 is None:
            raise ContractError("run mode requires the caller-bound contract")
        _, digest = _load_contract(arguments.contract, arguments.contract_sha256)
        sys.stdout.buffer.write(_canonical_bytes(_result(digest)))
        return 0
    except InputIdentityError:
        sys.stdout.buffer.write(_blocked("BLOCKED_CANDIDATE_C_BASELINE_MISMATCH"))
        return 2
    except ContractError:
        sys.stdout.buffer.write(_blocked("BLOCKED_CANDIDATE_C_NONDETERMINISTIC_EXECUTION"))
        return 2
    except ProofError:
        sys.stdout.buffer.write(_blocked("BLOCKED_CANDIDATE_C_OPEN_REPRODUCIBILITY"))
        return 3
    except Exception:
        sys.stdout.buffer.write(_blocked("BLOCKED_CANDIDATE_C_OPEN_REPRODUCIBILITY"))
        return 3


if __name__ == "__main__":
    raise SystemExit(_main())
