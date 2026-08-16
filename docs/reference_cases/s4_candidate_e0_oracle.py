from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "docs/reference_cases/s4_candidate_e0_contract.json"
CANDIDATE_ID = "candidate_e0.wg2020_n7_k0_gww1992_allman_6dof_static_v1"
SOURCE_TERMINAL = "BLOCKED_CANDIDATE_E_SOURCE_OR_IDENTITY"
SOURCE_REASON = "MISSING_EXACT_ALL_NODE_DRILL_FORMULATION_AND_SOURCE_CONFLICT"
RELEASE_TERMINAL = "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"

RAW_INPUTS = {
    "governing_plan": (
        "docs/agent_plans/S4_CANDIDATE_E0_DNV_LINEAR_BUCKLING_QUALIFICATION_PLAN.md",
        5438,
        "082BABD49F20436BEFBC2C14C123F6904DAAA6597EA99A1F7D85FA13F80B1162",
    ),
    "derivation": (
        "docs/S4_CANDIDATE_E0_FORMULATION_DERIVATION.md",
        4103,
        "D9A443D2B7F92E72057AC7317083B34AD586899F5BE75F148E94C2C5798DD211",
    ),
    "baseline": (
        "docs/reference_cases/s4_candidate_e0_baseline.json",
        2624,
        "71831C68F5DEF66A3BD698ACE6CCAF06E1D3A08FA19C4C05C8F19E221F177397",
    ),
    "environment": (
        "docs/reference_cases/s4_candidate_e0_environment.json",
        984,
        "31D7C666BD68BCE48CD786554674F9C90D47ECABB831C51B20B8C8AE8349F84D",
    ),
    "source_registry": (
        "docs/reference_cases/s4_candidate_e0_source_registry.json",
        3705,
        "E31B419F141B4FC0C80010BE5BDE31A4F85ACE3A84E6B5F01E0D80B34CE617CC",
    ),
    "formulation_identity": (
        "docs/reference_cases/s4_candidate_e0_formulation_identity.json",
        1121,
        "2A0A1083C655262CDD5EBC19084C3CAC4E2EE9B988618C00EF607C1E821C90B3",
    ),
    "material_fixtures": (
        "docs/reference_cases/s4_candidate_e0_dnv_material_fixtures.json",
        2135,
        "A16024C81522FB783841CC790C11772A10C8D0D936F9E678BE1CA981FD3DD016",
    ),
    "gate_cases": (
        "docs/reference_cases/s4_candidate_e0_gate_cases.json",
        1909,
        "C2FB7EFF6AEAF084C00762B480288F1064D22A75527967D825742E9E91A18264",
    ),
    "test_inventory": (
        "docs/reference_cases/s4_candidate_e0_test_inventory.json",
        2169,
        "DC63B9868057080AFCF6ED229C07F967F8F95A36352D755F4329FDCA5FE79824",
    ),
    "gitattributes": (
        ".gitattributes",
        1328,
        "DA5B76EC3ECB83B28114668EE1425C33D3EDCBE8FB2E708F775BEA47477CEC87",
    ),
}

UPSTREAM = {
    "accepted_closeout": (
        "docs/reference_cases/s4_improved_qualification_final_status.json",
        3943,
        "E3E8F3AA2DD6BA4193358AEDFC7F01889A80544313041531A1840218C09C29C1",
    ),
    "candidate_a": (
        "docs/reference_cases/s4_candidate_a_open_output.json",
        2644,
        "C42911E11BB1F1FA091F29FD0E3F5A3617310EF5F06C686E57C013171242B63C",
    ),
    "candidate_b": (
        "docs/reference_cases/s4_stage_m_mechanics_output.json",
        5824196,
        "3A26052DB79CE914FF8A1FCA7835F3B86C15F1D351754B45CA904753D8EFDA0D",
    ),
    "candidate_c": (
        "docs/reference_cases/s4_candidate_c_quotient_output.json",
        3701,
        "A44ED2DD5F11A0BBF9A0CB8D01B869A1D7E12632B3E85E773A804FC2CCC140B6",
    ),
    "rank_four": (
        "docs/reference_cases/s4_drill_constraint_oracle_output.json",
        1434454,
        "8005C6D285263E33FF7F6D4B5138D5FBE4EFAB6A95834C401F94AF044ACD9E1B",
    ),
}

PRODUCTION = {
    "package_init": (
        "src/anysolver/__init__.py",
        24779,
        "0C782CCE93C1346F8A9B6DB832156A4F2689B33460C58F5966E9DE2169C2B8F0",
    ),
    "production_mode": (
        "src/anysolver/anystructure_fem_mode.py",
        60057,
        "2FEACAAFD2A516B8ACCD919124A18614B0C3096EC0EEAF02DF6BC4280A80616E",
    ),
    "elements": (
        "src/anysolver/elements.py",
        190422,
        "5D0AF716CD2E466EB831B1896553DE06236AC1BA80A84BD1B09C7E4CEBBDE670",
    ),
    "fe_core": (
        "src/anysolver/fe_core.py",
        17364,
        "553CE5A7C6FE86CD10D562A1B7683AF2CC84A7E43E77D201823651F3047B9EFD",
    ),
    "shell_sections": (
        "src/anysolver/shell_sections.py",
        11530,
        "C9ECF93AB0E0A9B2A0D57A0252A21C4BF2A885551D5C96C64C1E2D3167919456",
    ),
}


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
            raise ValueError(f"duplicate key: {key}")
        result[key] = value
    return result


def _decode_json(raw: bytes) -> object:
    if raw.startswith(b"\xef\xbb\xbf"):
        raise ValueError("UTF-8 BOM is forbidden")
    return json.loads(
        raw.decode("utf-8"),
        object_pairs_hook=_pairs,
        parse_constant=lambda token: (_ for _ in ()).throw(
            ValueError(f"nonfinite token: {token}")
        ),
    )


def _canonical_bytes(value: object) -> bytes:
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


def _verified_raw(record: tuple[str, int, str]) -> bytes:
    relative, expected_bytes, expected_sha = record
    raw = (ROOT / relative).read_bytes()
    if len(raw) != expected_bytes or _sha(raw) != expected_sha:
        raise BaselineMismatch(f"identity mismatch: {relative}")
    if raw.startswith(b"\xef\xbb\xbf") or b"\r" in raw or not raw.endswith(b"\n"):
        raise BaselineMismatch(f"transport mismatch: {relative}")
    return raw


def _verified_canonical_json(record: tuple[str, int, str]) -> dict[str, object]:
    raw = _verified_raw(record)
    value = _decode_json(raw)
    if not isinstance(value, dict) or raw != _canonical_bytes(value):
        raise BaselineMismatch(f"noncanonical JSON: {record[0]}")
    return value


def _verified_lf(record: tuple[str, int, str]) -> bytes:
    relative, expected_bytes, expected_sha = record
    raw = (ROOT / relative).read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raise BaselineMismatch(f"BOM mismatch: {relative}")
    lf = raw.replace(b"\r\n", b"\n")
    if b"\r" in lf or len(lf) != expected_bytes or _sha(lf) != expected_sha:
        raise BaselineMismatch(f"canonical LF mismatch: {relative}")
    return lf


def _validate_inputs() -> dict[str, dict[str, object]]:
    raw_records: dict[str, dict[str, object]] = {}
    json_names = {
        "baseline",
        "environment",
        "source_registry",
        "formulation_identity",
        "material_fixtures",
        "gate_cases",
        "test_inventory",
    }
    values: dict[str, dict[str, object]] = {}
    for name, record in RAW_INPUTS.items():
        raw = _verified_raw(record)
        if name in json_names:
            parsed = _decode_json(raw)
            if not isinstance(parsed, dict) or raw != _canonical_bytes(parsed):
                raise BaselineMismatch(f"noncanonical JSON: {record[0]}")
            values[name] = parsed
        raw_records[name] = {"bytes": len(raw), "path": record[0], "sha256": _sha(raw)}

    for record in UPSTREAM.values():
        _verified_canonical_json(record)
    for record in PRODUCTION.values():
        _verified_lf(record)

    baseline = values["baseline"]
    if baseline["authority"]["base_commit"] != "a9b45ca95303bc4b30b893fbb0d7177f9c98db03":
        raise BaselineMismatch("base commit mismatch")
    inventory = values["test_inventory"]
    if inventory["collection"]["count"] != 85:
        raise BaselineMismatch("accepted test count mismatch")
    base_record = inventory["composition"]["base_75"]
    if base_record != {
        "bytes": 10598,
        "path": "docs/reference_cases/s4_candidate_c_quotient_test_inventory.json",
        "sha256": "2A79F6E5F1683BC6D2F8FD049DFDBA9FF0457EDE486F1F9B0ACA8CEFCC5AA592",
    }:
        raise BaselineMismatch("accepted 75-test inventory identity mismatch")
    base_raw = _verified_raw((base_record["path"], base_record["bytes"], base_record["sha256"]))
    base_inventory = _decode_json(base_raw)
    if not isinstance(base_inventory, dict) or base_raw != _canonical_bytes(base_inventory):
        raise BaselineMismatch("accepted 75-test inventory is not canonical")
    base_files = base_inventory["files"]
    appended_files = inventory["composition"]["appended_files"]
    if len(base_files) != 11 or len(appended_files) != 3:
        raise BaselineMismatch("accepted test-file inventory count mismatch")
    for record in [*base_files, *appended_files]:
        _verified_lf(
            (
                record["path"],
                record["canonical_lf_bytes"],
                record["canonical_lf_sha256"],
            )
        )
    node_ids = list(base_inventory["collection"]["node_ids"])
    node_ids.extend(inventory["composition"]["appended_node_ids"])
    joined_node_ids = ("\n".join(node_ids) + "\n").encode("utf-8")
    if len(node_ids) != len(set(node_ids)) or len(node_ids) != 85:
        raise BaselineMismatch("accepted test node IDs are missing or duplicated")
    if (
        len(joined_node_ids) != inventory["collection"]["node_ids_canonical_lf_bytes"]
        or _sha(joined_node_ids) != inventory["collection"]["node_ids_canonical_lf_sha256"]
        or len(joined_node_ids) != 8910
        or _sha(joined_node_ids) != "966AA017D996DC3F83F0A2C98D269022803B44DBB411A934CC01BECA958E2873"
    ):
        raise BaselineMismatch("accepted 85-test node-list identity mismatch")

    registry = values["source_registry"]
    claims = {record["id"]: record["status"] for record in registry["claims"]}
    expected = {
        "hu_washizu_functional": "PRINTED_PRIMARY_SOURCE",
        "n7_k0_interpolation": "PRINTED_PRIMARY_SOURCE",
        "two_by_two_primary_rule": "PRINTED_PRIMARY_SOURCE",
        "mixed_block_and_condensation": "PRINTED_PRIMARY_SOURCE",
        "all_four_nodes_have_independent_six_dof": "CONFLICTING_PRIMARY_SOURCE",
        "exact_gww1992_allman_spin_skew_force_interpolation": "MISSING_FULL_TEXT",
        "nonduplicated_interface_between_2020_core_and_1992_drill": "UNSUBSTANTIATED_COMPOSITION",
        "complete_24dof_residual_and_consistent_tangent": "UNSUBSTANTIATED_COMPOSITION",
        "source_proven_local_condensation_for_24dof_specialization": "UNSUBSTANTIATED_COMPOSITION",
    }
    if claims != expected:
        raise BaselineMismatch("source claim matrix mismatch")
    if registry["source_gate"] != {
        "status": "blocked",
        "terminal": SOURCE_TERMINAL,
        "reason": SOURCE_REASON,
    }:
        raise BaselineMismatch("source terminal mismatch")

    materials = values["material_fixtures"]
    dataset = materials["rp_c208_dataset"]
    if sorted(dataset["grades"]) != ["S235", "S275", "S355", "S420", "S460"]:
        raise BaselineMismatch("RP-C208 grade inventory mismatch")
    if dataset["grade_count"] != 5 or dataset["row_count"] != 17:
        raise BaselineMismatch("RP-C208 count mismatch")
    if materials["qualification"]["candidate_element_material_compatibility"] != "NOT_RUN_DUE_TO_SOURCE_GATE":
        raise BaselineMismatch("material gate overclaim")

    upstream_values = {name: _verified_canonical_json(record) for name, record in UPSTREAM.items()}
    if upstream_values["candidate_a"]["pair_terminal"] != "NO_GO_CANDIDATE_A_DISCRETE_PAIR":
        raise BaselineMismatch("Candidate A terminal drift")
    if upstream_values["candidate_b"]["candidate_terminal"] != "NO_GO_CANDIDATE_B":
        raise BaselineMismatch("Candidate B terminal drift")
    if upstream_values["candidate_c"]["candidate_terminal"] != "NO_GO_CANDIDATE_C_QUOTIENT_INF_SUP":
        raise BaselineMismatch("Candidate C terminal drift")
    if upstream_values["rank_four"]["scientific_summary"]["outcome"] != RELEASE_TERMINAL:
        raise BaselineMismatch("rank-four terminal drift")

    return {"identities": raw_records, "values": values}


def _allowed_paths() -> list[str]:
    return [
        "docs/agent_plans/S4_CANDIDATE_E0_DNV_LINEAR_BUCKLING_QUALIFICATION_PLAN.md",
        "docs/S4_CANDIDATE_E0_FORMULATION_DERIVATION.md",
        "docs/S4_CANDIDATE_E0_QUALIFICATION_REPORT.md",
        "docs/S4_CANDIDATE_E0_INDEPENDENT_REVIEW.md",
        "docs/reference_cases/s4_candidate_e0_baseline.json",
        "docs/reference_cases/s4_candidate_e0_environment.json",
        "docs/reference_cases/s4_candidate_e0_source_registry.json",
        "docs/reference_cases/s4_candidate_e0_formulation_identity.json",
        "docs/reference_cases/s4_candidate_e0_dnv_material_fixtures.json",
        "docs/reference_cases/s4_candidate_e0_gate_cases.json",
        "docs/reference_cases/s4_candidate_e0_test_inventory.json",
        "docs/reference_cases/s4_candidate_e0_oracle.py",
        "docs/reference_cases/s4_candidate_e0_contract.json",
        "docs/reference_cases/s4_candidate_e0_output.json",
        "tests/test_s4_candidate_e0_source_gate.py",
        "tests/test_s4_candidate_e0_closeout.py",
    ]


def build_contract() -> dict[str, object]:
    validated = _validate_inputs()
    oracle_raw = Path(__file__).read_bytes()
    if oracle_raw.startswith(b"\xef\xbb\xbf") or b"\r" in oracle_raw or not oracle_raw.endswith(b"\n"):
        raise BaselineMismatch("oracle transport mismatch")
    identities = dict(validated["identities"])
    identities["oracle"] = {
        "bytes": len(oracle_raw),
        "path": "docs/reference_cases/s4_candidate_e0_oracle.py",
        "sha256": _sha(oracle_raw),
    }
    cases = validated["values"]["gate_cases"]
    return {
        "schema": "anysolver.s4.candidate-e0-contract-v1",
        "authority": {
            "base_commit": "a9b45ca95303bc4b30b893fbb0d7177f9c98db03",
            "base_tree": "6919b33851b63236fc150711a0ccb28fdfa2dbf8",
            "attached_proposal_sha256": "4499DA192F97D9BF7D89C3A9A8B5A68E6201CA5E2350E30918583464BF0E98EA",
        },
        "allowed_extent": {"modified": [".gitattributes"], "new_paths": _allowed_paths(), "production_paths": []},
        "candidate": {"id": CANDIDATE_ID, "registration_status": "PROPOSED_SOURCE_BLOCKED", "target_external_coordinates": 24, "target_verified": False},
        "execution": {"fresh_processes": 2, "mechanics": False, "mode": "source_gate_only", "standard_library_only": True},
        "identities": identities,
        "source_gate": {"status": "blocked", "terminal": SOURCE_TERMINAL, "reason": SOURCE_REASON},
        "material_boundary": {"input_shape_compatible": True, "candidate_element_qualification": "NOT_RUN_DUE_TO_SOURCE_GATE", "dnv_approval": False, "rp_c208_is_ru_ship_rule": False},
        "terminals": cases["terminal_precedence"],
        "exclusions": cases["exclusions"],
    }


def build_output(contract_sha256: str) -> dict[str, object]:
    validated = _validate_inputs()
    registry = validated["values"]["source_registry"]
    verified = sorted(record["id"] for record in registry["claims"] if record["status"] == "PRINTED_PRIMARY_SOURCE")
    blocked = sorted(record["id"] for record in registry["claims"] if record["status"] != "PRINTED_PRIMARY_SOURCE")
    stages = {
        "source_and_identity": SOURCE_TERMINAL,
        "exact_element_mechanics": "NOT_RUN_DUE_TO_SOURCE_GATE",
        "uniform_stability_and_locking": "NOT_RUN_DUE_TO_SOURCE_GATE",
        "dnv_material_and_recovery": "NOT_RUN_DUE_TO_SOURCE_GATE",
        "linear_eigenvalue_buckling": "NOT_RUN_DUE_TO_SOURCE_GATE",
        "nonlinear_mechanics": "NOT_IN_E0_SCOPE",
        "dynamics": "NOT_IN_E0_SCOPE",
        "performance": "NOT_IN_E0_SCOPE",
    }
    return {
        "schema": "anysolver.s4.candidate-e0-output-v1",
        "status": "blocked",
        "mode": "source_gate_only",
        "candidate_id": CANDIDATE_ID,
        "candidate_terminal": SOURCE_TERMINAL,
        "terminal_reason": SOURCE_REASON,
        "overall_release_terminal": RELEASE_TERMINAL,
        "contract_sha256": contract_sha256,
        "source_gate": {"verified_claim_ids": verified, "blocked_claim_ids": blocked},
        "stages": stages,
        "materials": {
            "ordinary_material_input_shape_compatible": True,
            "rp_c208_fixture_reproduction": True,
            "rp_c208_fixture_is_ru_ship_rule": False,
            "candidate_element_material_compatibility": "NOT_RUN_DUE_TO_SOURCE_GATE",
            "dnv_approval": False,
        },
        "mechanics_results_present": False,
        "immutable_results": {
            "candidate_a": "NO_GO_CANDIDATE_A_DISCRETE_PAIR",
            "candidate_b": "NO_GO_CANDIDATE_B",
            "candidate_c": "NO_GO_CANDIDATE_C_QUOTIENT_INF_SUP",
            "rank_four": RELEASE_TERMINAL,
        },
        "production": {"legacy_shell_default": True, "public_api_changed": False, "selector_available": False, "serialization_changed": False},
        "exclusions": validated["values"]["gate_cases"]["exclusions"],
    }


def _load_contract(path: Path, caller_sha256: str) -> tuple[dict[str, object], str]:
    try:
        resolved = path.resolve(strict=True)
        if resolved != CONTRACT_PATH.resolve(strict=True):
            raise ContractViolation("contract path is not allowlisted")
        raw = resolved.read_bytes()
        actual = _sha(raw)
        if caller_sha256.upper() != actual:
            raise ContractViolation("caller-bound contract hash mismatch")
        if raw.startswith(b"\xef\xbb\xbf") or b"\r" in raw or not raw.endswith(b"\n"):
            raise ContractViolation("contract transport mismatch")
        value = _decode_json(raw)
        if not isinstance(value, dict) or raw != _canonical_bytes(value):
            raise ContractViolation("contract is not canonical")
    except ContractViolation:
        raise
    except (OSError, UnicodeError, ValueError, KeyError, TypeError) as exc:
        raise ContractViolation(f"contract transport or parse failure: {exc}") from exc
    if value != build_contract():
        raise ContractViolation("contract semantic mismatch")
    return value, actual


def _blocked(terminal: str, detail: str) -> bytes:
    return _canonical_bytes({"schema": "anysolver.s4.candidate-e0-blocked-v1", "status": "blocked", "terminal": terminal, "detail": detail})


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--emit-contract", action="store_true")
    mode.add_argument("--run", action="store_true")
    parser.add_argument("--contract")
    parser.add_argument("--contract-sha256")
    args = parser.parse_args(argv)
    try:
        if args.emit_contract:
            if args.contract is not None or args.contract_sha256 is not None:
                raise ContractViolation("emit-contract accepts no contract arguments")
            sys.stdout.buffer.write(_canonical_bytes(build_contract()))
            return 0
        if args.contract is None or args.contract_sha256 is None:
            raise ContractViolation("run requires contract path and SHA-256")
        _, contract_sha = _load_contract(Path(args.contract), args.contract_sha256)
        sys.stdout.buffer.write(_canonical_bytes(build_output(contract_sha)))
        return 0
    except ContractViolation as exc:
        sys.stdout.buffer.write(_blocked("BLOCKED_CANDIDATE_E_NONDETERMINISTIC_EXECUTION", str(exc)))
        return 2
    except (BaselineMismatch, OSError, UnicodeError, ValueError, KeyError, TypeError) as exc:
        sys.stdout.buffer.write(_blocked("BLOCKED_CANDIDATE_E_BASELINE_MISMATCH", str(exc)))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
