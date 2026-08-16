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
    "governing_plan": ("docs/agent_plans/S4_CANDIDATE_A_OPEN_QUALIFICATION_PLAN.md", 3205, "630EEEFD846CCFC4DE5B61C5530F8E76F5ACD33A6014A78135F4A36D8FE90999"),
    "baseline": ("docs/reference_cases/s4_candidate_a_open_baseline.json", 5151, "C3BB5E4AB79C9B6278B6E39F642AE3F99DA001ABF5DE0D1E01274FBC0187199A"),
    "source_registry": ("docs/reference_cases/s4_candidate_a_open_source_registry.json", 2017, "8EF2E09B76046A4070A7A2BCDAC52EC16A25D50C7557F789335AC6173E5A6986"),
    "environment": ("docs/reference_cases/s4_candidate_a_open_environment.json", 2870, "1348DF6CE0DBC19BE84A0A28243820EAFDD7EA361AB78A5F586EBC98391D28F5"),
    "test_inventory": ("docs/reference_cases/s4_candidate_a_open_test_inventory.json", 8825, "4F016F85EFABFC459823BC3B290F5E2AB2143677AE8765246017D19CC2A4FC11"),
    "a1_certificate": ("docs/reference_cases/s4_candidate_a_open_a1_certificate.json", 3902, "2198458DCDC7EFB4684B5CC59ADAF6E9A0EECF381951CBDD21B286D6DB11097C"),
    "a2_certificate": ("docs/reference_cases/s4_candidate_a_open_a2_certificate.json", 3196, "68691E4F1F23E23ED7DF00C4210436BDD1A730ADB58ED3E755E15CC01ECC5F3B"),
    "accepted_candidate_a_cases": ("docs/reference_cases/s4_stage_m_candidate_a_discretization_cases.json", 6616, "BB29F6AE7AE53E961C992BBC2EA764D50B73F935C9B5F9C21C1E21462DCC3E9C"),
    "accepted_candidate_a_contract": ("docs/reference_cases/s4_stage_m_candidate_a_discretization_contract.json", 3907, "8861943D1339373FB36448EA376E75D4CBAB64DE1A8450D6B547A235AA62844C"),
    "candidate_b_output": ("docs/reference_cases/s4_stage_m_mechanics_output.json", 5824196, "3A26052DB79CE914FF8A1FCA7835F3B86C15F1D351754B45CA904753D8EFDA0D"),
    "rank_four_output": ("docs/reference_cases/s4_drill_constraint_oracle_output.json", 1434454, "8005C6D285263E33FF7F6D4B5138D5FBE4EFAB6A95834C401F94AF044ACD9E1B"),
}

BASE_COMMIT = "148ccb45ba79266d48dae1a84c4c500bdc1b4d85"
BASE_TREE = "0a0809b2111c07098058fd43891729c6f9266b06"
ATTACHMENT_SHA256 = "A27339F96DD798C93E0E3E16C441000C9C0FF57E8DEC454823DD466249DC2B25"
A1_TERMINAL = "PROVEN_FAIL_CANDIDATE_A1_FLAT_RANK"
A2_TERMINAL = "PROVEN_FAIL_CANDIDATE_A2_INF_SUP"
PAIR_TERMINAL = "NO_GO_CANDIDATE_A_DISCRETE_PAIR"
RELEASE_TERMINAL = "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"


class InputIdentityError(RuntimeError):
    pass


class ContractError(RuntimeError):
    pass


class IncompleteCertificate(RuntimeError):
    pass


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


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


def _parse_json(raw: bytes, *, canonical: bool) -> Any:
    if raw.startswith(b"\xef\xbb\xbf") or b"\r" in raw or not raw.endswith(b"\n"):
        raise InputIdentityError("JSON transport must be UTF-8/LF without BOM")
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


def _canonical_lf(raw: bytes) -> bytes:
    if raw.startswith(b"\xef\xbb\xbf"):
        raise InputIdentityError("text has a UTF-8 BOM")
    without_crlf = raw.replace(b"\r\n", b"")
    if b"\r" in without_crlf:
        raise InputIdentityError("text has a lone CR")
    if b"\r\n" in raw and b"\n" in without_crlf:
        raise InputIdentityError("text mixes CRLF and LF")
    return raw.replace(b"\r\n", b"\n")


def _read_input(name: str) -> bytes:
    relative, size, digest = INPUTS[name]
    raw = (ROOT / relative).read_bytes()
    canonical = _canonical_lf(raw)
    if len(canonical) != size or _sha(canonical) != digest:
        raise InputIdentityError(f"identity mismatch: {name}")
    return canonical


def _integer(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise IncompleteCertificate("integer field has invalid type")
    return int(value)


def _fractions(values: list[str]) -> list[Fraction]:
    if not isinstance(values, list) or any(not isinstance(value, str) for value in values):
        raise IncompleteCertificate("exact scalars must be strings")
    return [Fraction(value) for value in values]


def _rank(matrix: list[list[Fraction]]) -> int:
    if not matrix:
        return 0
    width = len(matrix[0])
    if any(len(row) != width for row in matrix):
        raise IncompleteCertificate("ragged exact matrix")
    work = [row[:] for row in matrix]
    pivot_row = 0
    for column in range(width):
        pivot = next(
            (index for index in range(pivot_row, len(work)) if work[index][column]),
            None,
        )
        if pivot is None:
            continue
        work[pivot_row], work[pivot] = work[pivot], work[pivot_row]
        scale = work[pivot_row][column]
        work[pivot_row] = [value / scale for value in work[pivot_row]]
        for index in range(len(work)):
            if index == pivot_row or not work[index][column]:
                continue
            scale = work[index][column]
            work[index] = [
                work[index][entry] - scale * work[pivot_row][entry]
                for entry in range(width)
            ]
        pivot_row += 1
        if pivot_row == len(work):
            break
    return pivot_row


def _determinant(matrix: list[list[Fraction]]) -> Fraction:
    if not matrix or any(len(row) != len(matrix) for row in matrix):
        raise IncompleteCertificate("determinant requires a square matrix")
    work = [row[:] for row in matrix]
    result = Fraction(1)
    for column in range(len(work)):
        pivot = next(
            (index for index in range(column, len(work)) if work[index][column]),
            None,
        )
        if pivot is None:
            return Fraction(0)
        if pivot != column:
            work[column], work[pivot] = work[pivot], work[column]
            result = -result
        pivot_value = work[column][column]
        result *= pivot_value
        for row in range(column + 1, len(work)):
            scale = work[row][column] / pivot_value
            for entry in range(column + 1, len(work)):
                work[row][entry] -= scale * work[column][entry]
    return result


def _preflight() -> dict[str, Any]:
    values: dict[str, Any] = {}
    for name in INPUTS:
        raw = _read_input(name)
        if INPUTS[name][0].endswith(".json"):
            values[name] = _parse_json(
                raw,
                canonical=name
                in {
                    "environment",
                    "test_inventory",
                    "a1_certificate",
                    "a2_certificate",
                    "accepted_candidate_a_contract",
                    "candidate_b_output",
                    "rank_four_output",
                },
            )

    baseline = values["baseline"]
    if baseline["git"]["baseline_commit"] != BASE_COMMIT or baseline["git"]["baseline_tree"] != BASE_TREE:
        raise InputIdentityError("baseline commit/tree mismatch")
    if baseline["attachment"]["raw_sha256"] != ATTACHMENT_SHA256:
        raise InputIdentityError("attached proposal identity mismatch")
    if baseline.get("scientific_output_serialization") != "json_sort_keys_compact_utf8_lf_no_bom_nonfinite_forbidden":
        raise InputIdentityError("scientific output serialization is not frozen")

    source_registry = values["source_registry"]
    if source_registry["offline_reproduction"] is not True or source_registry["remote_source_required"] is not False:
        raise InputIdentityError("offline source registry is not closed")

    environment = values["environment"]
    if environment["oracle_runtime"] != {
        "dependencies": "python_standard_library_only",
        "hash_order_independent": True,
        "python_hash_seed_requirement": "none",
        "runtime_fields_in_scientific_output": False,
        "two_fresh_process_byte_equality_required": True,
    }:
        raise InputIdentityError("oracle runtime policy drift")

    inventory = values["test_inventory"]
    nodes = inventory["collection"]["node_ids"]
    node_bytes = ("\n".join(nodes) + "\n").encode("utf-8")
    if len(nodes) != inventory["collection"]["count"] or len(nodes) != 64:
        raise InputIdentityError("baseline node count drift")
    if len(node_bytes) != inventory["collection"]["node_ids_canonical_lf_bytes"]:
        raise InputIdentityError("baseline node-list size drift")
    if _sha(node_bytes) != inventory["collection"]["node_ids_canonical_lf_sha256"]:
        raise InputIdentityError("baseline node-list identity drift")
    if len(set(nodes)) != 64:
        raise InputIdentityError("baseline node list has duplicates")
    for record in inventory["files"]:
        canonical = _canonical_lf((ROOT / record["path"]).read_bytes())
        if len(canonical) != record["canonical_lf_bytes"] or _sha(canonical) != record["canonical_lf_sha256"]:
            raise InputIdentityError(f"baseline test identity mismatch: {record['path']}")

    accepted = values["accepted_candidate_a_contract"]
    if accepted["counts"] != {"base_rows": 174, "pair_rows": 348, "pairs": 2}:
        raise InputIdentityError("accepted Candidate-A coverage count drift")
    if accepted["candidate_pairs"] != ["candidate_a.d4.span_r_s", "candidate_a.d4.span_1_rs"]:
        raise InputIdentityError("accepted Candidate-A pair IDs drift")

    candidate_b = values["candidate_b_output"]
    if candidate_b["candidate_terminal"] != "NO_GO_CANDIDATE_B":
        raise InputIdentityError("Candidate-B terminal drift")
    rank_four = values["rank_four_output"]
    if rank_four["formulation_identity"] != "mitc4_plus_d_published_2025_linear_spin_constrained_research_v1":
        raise InputIdentityError("rank-four formulation identity drift")
    if rank_four["scientific_summary"]["outcome"] != RELEASE_TERMINAL:
        raise InputIdentityError("rank-four outcome drift")
    return values


def _contract() -> dict[str, Any]:
    oracle_raw = Path(__file__).read_bytes()
    if b"\r" in oracle_raw or not oracle_raw.endswith(b"\n"):
        raise InputIdentityError("oracle transport is not LF")
    return {
        "allowed_extent": {
            "modified": [".gitattributes"],
            "new_prefixes": [
                "docs/agent_plans/S4_CANDIDATE_A_OPEN_QUALIFICATION_PLAN.md",
                "docs/S4_CANDIDATE_A_OPEN_",
                "docs/reference_cases/s4_candidate_a_open_",
                "tests/test_s4_candidate_a_open_",
            ],
            "production_paths": [],
        },
        "authority": {
            "attachment_sha256": ATTACHMENT_SHA256,
            "base_commit": BASE_COMMIT,
            "base_tree": BASE_TREE,
        },
        "coverage": {
            "base_rows": 174,
            "baseline_node_count": 64,
            "baseline_node_ids_sha256": "7D71339F0621328AF54BC4BDFC04E3C7082EDA333B58E100C4C9550F0E9C85D9",
            "pair_ledgers": [
                {"pair_id": "candidate_a.d4.span_r_s", "row_count": 174, "sha256": "C598C36EC04E7ED11A1B90F8C5D95935E86812AE55B522B32B4750A49C35F754"},
                {"pair_id": "candidate_a.d4.span_1_rs", "row_count": 174, "sha256": "3DAB9F109BA64F48373246880B372B06BF179A1E7925049C7C1687AE432542C9"},
            ],
        },
        "execution": {
            "arithmetic": "fractions.Fraction",
            "finite_rotation": False,
            "high_precision_shards": False,
            "numerical_svd_authoritative": False,
            "performance": False,
            "repeat_fresh_processes": 2,
        },
        "exclusions": {
            "candidate_b_rerun": False,
            "cleanup": False,
            "multiplier_quotient": False,
            "penalty_or_stabilization_or_ctc": False,
            "production_activation": False,
            "production_source_edit": False,
            "publication": False,
            "push": False,
            "selector": False,
            "serialization_change": False,
        },
        "identities": {
            name: {
                "canonical_lf_bytes": size,
                "canonical_lf_sha256": digest,
                "path": path,
                "text_identity": "canonical_git_lf",
            }
            for name, (path, size, digest) in INPUTS.items()
        }
        | {
            "oracle": {
                "canonical_lf_bytes": len(oracle_raw),
                "canonical_lf_sha256": _sha(oracle_raw),
                "path": "docs/reference_cases/s4_candidate_a_open_oracle.py",
                "text_identity": "canonical_git_lf",
            }
        },
        "preserved": {
            "candidate_b": {"output_sha256": INPUTS["candidate_b_output"][2], "terminal": "NO_GO_CANDIDATE_B"},
            "rank_four_constraint": {
                "formulation_identity": "mitc4_plus_d_published_2025_linear_spin_constrained_research_v1",
                "output_sha256": INPUTS["rank_four_output"][2],
                "terminal": RELEASE_TERMINAL,
            },
        },
        "quadrature": {
            "finite_constraint_future_primary": "surface_3x3",
            "finite_constraint_future_sensitivity": "surface_4x4",
            "flat_polynomial_reproduction": ["symbolic", "tensor_2x2_gauss"],
        },
        "schema": "anysolver.s4.candidate-a-open-contract-v1",
        "terminals": {
            "blocker_precedence": [
                "BLOCKED_CANDIDATE_A_BASELINE_MISMATCH",
                "BLOCKED_CANDIDATE_A_OPEN_REPRODUCIBILITY",
                "BLOCKED_CANDIDATE_A_NONDETERMINISTIC_EXECUTION",
                "BLOCKED_CANDIDATE_A_INDEPENDENT_REVIEW",
                "BLOCKED_CANDIDATE_A_TEST_GATE",
            ],
            "candidate_results": {"a1": A1_TERMINAL, "a2": A2_TERMINAL},
            "pair_truth_table": [
                {"a1": A1_TERMINAL, "a2": A2_TERMINAL, "pair": PAIR_TERMINAL, "release": RELEASE_TERMINAL},
                {"otherwise": True, "pair": "UNCLASSIFIED_CANDIDATE_A_DISCRETE_PAIR", "release": "BLOCKED_CANDIDATE_A_QUALIFICATION_INCOMPLETE"},
            ],
        },
    }


def _a1_result(certificate: dict[str, Any]) -> dict[str, Any]:
    if certificate["candidate"]["basis_id"] != "candidate_a.d4.span_r_s":
        raise IncompleteCertificate("A1 candidate ID drift")
    rows = [_fractions(certificate["exact_constraint_rows_raw"][name]) for name in certificate["candidate"]["basis_order"]]
    witness_ids = certificate["premises"]["accepted_B_kernel_witness_ids"]
    columns = [_fractions(certificate["witnesses"][name]) for name in witness_ids]
    witness_matrix = [[column[row] for column in columns] for row in range(24)]
    if _rank(rows) != 2 or _rank(witness_matrix) != 8:
        raise IncompleteCertificate("A1 exact rank premise did not close")
    for name, column in zip(witness_ids, columns, strict=True):
        action = [sum(row[index] * column[index] for index in range(24)) for row in rows]
        if action != [Fraction(0), Fraction(0)]:
            raise IncompleteCertificate(f"A1 does not annihilate {name}")
    selected = [int(value) for value in certificate["exact_identities"]["kernel_witness_minor"]["selected_coordinate_indices"]]
    witness_minor = [[witness_matrix[row][column] for column in range(8)] for row in selected]
    if _determinant(witness_minor) != 4:
        raise IncompleteCertificate("A1 kernel witness minor drift")
    raw_columns = [int(value) for value in certificate["exact_identities"]["raw_constraint_minor"]["column_indices"]]
    if _determinant([[row[column] for column in raw_columns] for row in rows]) != Fraction(-1, 9):
        raise IncompleteCertificate("A1 row minor drift")
    ambient = _integer(certificate["dimensions"]["ambient"])
    nullity_b = _integer(certificate["dimensions"]["accepted_nullity_B"])
    rank_stacked = ambient - nullity_b
    rank_bt = (ambient - _rank(rows)) - nullity_b
    terminal = certificate["result"].get("candidate_terminal")
    if rank_stacked != 16 or rank_bt != 14 or terminal != A1_TERMINAL:
        raise IncompleteCertificate("A1 exact failure terminal did not close")
    return {
        "candidate_id": "candidate_a.d4.span_r_s",
        "constraint_rank": 2,
        "kernel_witness_rank": 8,
        "ker_B_subset_ker_C": True,
        "rank_BT": 14,
        "rank_stacked_B_C": 16,
        "terminal": A1_TERMINAL,
    }


def _a2_result(certificate: dict[str, Any]) -> dict[str, Any]:
    if certificate["candidate_id"] != "candidate_a.d4.span_1_rs":
        raise IncompleteCertificate("A2 candidate ID drift")
    counterexample = certificate["counterexample"]
    topology = counterexample["topology"]
    rows = {
        "1": _fractions(counterexample["local_rows"]["normalized_1_full"]),
        "rs": _fractions(counterexample["local_rows"]["normalized_rs_full"]),
    }
    assembled: list[list[Fraction]] = []
    for element in topology["elements"]:
        local_index = element["nodes"].index("n11")
        for mode in ("1", "rs"):
            assembled.append(rows[mode][6 * local_index : 6 * (local_index + 1)])
    coefficients: list[Fraction] = []
    for record in counterexample["multiplier"]["coefficients_by_element"]:
        coefficients.extend([Fraction(record["one"]), Fraction(record["rs"])])
    transpose_product = [
        sum(coefficients[row] * assembled[row][column] for row in range(len(assembled)))
        for column in range(6)
    ]
    norm_squared = Fraction(3, 2) ** 2 * Fraction(2, 3) ** 2 * len(topology["elements"])
    terminal = certificate["terminal"].get("terminal")
    if not any(coefficients) or transpose_product != [Fraction(0)] * 6 or norm_squared != 4:
        raise IncompleteCertificate("A2 exact annihilator did not close")
    if certificate["exclusions"]["multiplier_quotient"] is not False or terminal != A2_TERMINAL:
        raise IncompleteCertificate("A2 registered-space terminal did not close")
    return {
        "admissible_columns": 6,
        "beta": "0",
        "candidate_id": "candidate_a.d4.span_1_rs",
        "multiplier_nonzero": True,
        "multiplier_norm_squared": "4",
        "transpose_action": ["0"] * 6,
        "terminal": A2_TERMINAL,
    }


def _result(contract_sha256: str, values: dict[str, Any]) -> dict[str, Any]:
    try:
        a1 = _a1_result(values["a1_certificate"])
    except IncompleteCertificate as exc:
        a1 = {"candidate_id": "candidate_a.d4.span_r_s", "detail": str(exc), "terminal": "UNCLASSIFIED"}
    try:
        a2 = _a2_result(values["a2_certificate"])
    except IncompleteCertificate as exc:
        a2 = {"candidate_id": "candidate_a.d4.span_1_rs", "detail": str(exc), "terminal": "UNCLASSIFIED"}
    closed = a1["terminal"] == A1_TERMINAL and a2["terminal"] == A2_TERMINAL
    return {
        "candidate_results": [a1, a2],
        "contract_sha256": contract_sha256,
        "execution": {
            "arithmetic": "fractions.Fraction",
            "authoritative_numerical_svd": False,
            "finite_rotation_run": False,
            "high_precision_shards_run": False,
            "performance_run": False,
        },
        "exclusions": _contract()["exclusions"],
        "identities": {
            name: digest for name, (_path, _size, digest) in INPUTS.items()
        }
        | {"oracle": _sha(Path(__file__).read_bytes())},
        "identity_semantics": "canonical_git_lf_sha256",
        "mode": "exact_necessary_screens",
        "overall_release_terminal": RELEASE_TERMINAL if closed else "BLOCKED_CANDIDATE_A_QUALIFICATION_INCOMPLETE",
        "pair_terminal": PAIR_TERMINAL if closed else "UNCLASSIFIED_CANDIDATE_A_DISCRETE_PAIR",
        "preserved": {
            "candidate_b": {"rerun": False, "terminal": "NO_GO_CANDIDATE_B"},
            "rank_four_constraint": {
                "formulation_identity": "mitc4_plus_d_published_2025_linear_spin_constrained_research_v1",
                "rerun": False,
                "terminal": RELEASE_TERMINAL,
            },
        },
        "schema": "anysolver.s4.candidate-a-open-output-v1",
        "status": "complete" if closed else "unclassified",
        "test_inventory": {
            "count": 64,
            "node_ids_sha256": "7D71339F0621328AF54BC4BDFC04E3C7082EDA333B58E100C4C9550F0E9C85D9",
        },
    }


def _blocked(terminal: str, detail: str) -> bytes:
    return _canonical_bytes(
        {
            "detail": detail,
            "schema": "anysolver.s4.candidate-a-open-blocked-v1",
            "status": "blocked",
            "terminal": terminal,
        }
    )


def _main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--emit-contract", action="store_true")
    modes.add_argument("--run", action="store_true")
    parser.add_argument("--contract")
    parser.add_argument("--contract-sha256")
    args = parser.parse_args(argv)
    try:
        values = _preflight()
        contract_value = _contract()
        if args.emit_contract:
            if args.contract is not None or args.contract_sha256 is not None:
                raise ContractError("emit-contract accepts no contract arguments")
            sys.stdout.buffer.write(_canonical_bytes(contract_value))
            return 0
        if not args.contract or not args.contract_sha256:
            raise ContractError("run requires caller-bound contract path and SHA-256")
        raw = Path(args.contract).read_bytes()
        if _sha(raw) != args.contract_sha256.upper():
            raise ContractError("caller-bound contract identity mismatch")
        parsed = _parse_json(raw, canonical=True)
        if parsed != contract_value:
            raise ContractError("contract semantic mismatch")
        sys.stdout.buffer.write(_canonical_bytes(_result(args.contract_sha256.upper(), values)))
        return 0
    except ContractError as exc:
        sys.stdout.buffer.write(_blocked("BLOCKED_CANDIDATE_A_NONDETERMINISTIC_EXECUTION", str(exc)))
        return 2
    except (InputIdentityError, FileNotFoundError, KeyError, TypeError, ValueError) as exc:
        terminal = (
            "BLOCKED_CANDIDATE_A_BASELINE_MISMATCH"
            if "baseline" in str(exc).lower()
            else "BLOCKED_CANDIDATE_A_OPEN_REPRODUCIBILITY"
        )
        sys.stdout.buffer.write(_blocked(terminal, str(exc)))
        return 3


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
