from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs/reference_cases/s4_e2_a_contract.json"
OUTPUT = ROOT / "docs/reference_cases/s4_e2_a_output.json"
REPORT = ROOT / "docs/S4_E2_A_QUALIFICATION_REPORT.md"
CONTRACT_SHA256 = "E3AA3BC6AD8FAD7EB64564851FC558B0D1B2ACB533B292EEBA580EBA47B02D3E"
OUTPUT_SHA256 = "37C803C565602E1AF983AA8374C3DA090EFD1CC73F2B672F2C815CC6A56B623D"
REPORT_SHA256 = "28FA4039DA2E47D9B91CD6C21620685E7DD710C6EE79AF7745022242429CE074"
E1_NODE_LIST_SHA256 = "9835FB4580C886B52BFF5961A30CD78E921B5CEED92A918312149032748A7F63"


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        assert key not in result
        result[key] = value
    return result


def _json(path: Path, expected_sha256: str | None = None) -> dict[str, object]:
    raw = path.read_bytes()
    if expected_sha256 is not None:
        assert _sha(raw) == expected_sha256
    assert not raw.startswith(b"\xef\xbb\xbf")
    assert b"\r" not in raw and raw.endswith(b"\n")
    value = json.loads(
        raw.decode("utf-8"),
        object_pairs_hook=_pairs,
        parse_constant=lambda token: (_ for _ in ()).throw(AssertionError(token)),
    )
    assert isinstance(value, dict)
    canonical = (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
        + "\n"
    ).encode("utf-8")
    assert raw == canonical
    return value


def _canonical_lf(path: Path) -> bytes:
    raw = path.read_bytes().replace(b"\r\n", b"\n")
    assert b"\r" not in raw
    return raw


def _record(path: str, size: int, sha256: str) -> bytes:
    raw = (ROOT / path).read_bytes()
    assert len(raw) == size and _sha(raw) == sha256
    return raw


def test_e2_a_contract_output_report_and_source_boundary_are_exact() -> None:
    contract = _json(CONTRACT, CONTRACT_SHA256)
    output = _json(OUTPUT, OUTPUT_SHA256)
    report_raw = REPORT.read_bytes()
    assert len(report_raw) == 5579 and _sha(report_raw) == REPORT_SHA256
    assert not report_raw.startswith(b"\xef\xbb\xbf") and b"\r" not in report_raw
    assert report_raw.endswith(b"\n")

    for record in contract["input_identities"].values():
        _record(record["path"], record["bytes"], record["sha256"])
    assert contract["candidate_id"] == output["candidate_id"]
    assert contract["scientific_terminal"] == {
        "reason": "RANK_SUFFICIENT_DISPLACEMENT_ENRICHMENT_NONUNIQUE",
        "value": "BLOCKED_E2_A_SOURCE_OR_FORMULATION_IDENTITY",
    }
    assert output["candidate_terminal"] == contract["scientific_terminal"]["value"]
    assert output["reason"] == contract["scientific_terminal"]["reason"]
    assert output["contract_sha256"] == CONTRACT_SHA256
    assert output["e1_rh"] == "DEFERRED_NOT_RUN"
    assert set(output["downstream_gates"].values()) == {"NOT_RUN_IDENTITY_AMBIGUOUS"}
    assert output["overall_release_terminal"] == "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"
    assert contract["mechanics_execution"] == "FORBIDDEN_AFTER_SOURCE_IDENTITY_BLOCK"
    assert contract["allowed_extent"]["modified"] == [".gitattributes"]
    assert contract["allowed_extent"]["production_paths"] == []
    assert contract["production_paths"] == []

    source = _json(ROOT / "docs/reference_cases/s4_e2_a_source_registry.json")
    identity = _json(ROOT / "docs/reference_cases/s4_e2_a_identity.json")
    assert source["design_input"]["sha256"] == (
        "5BF221C0B75425E292D80EF59CA4B6613445DD0621664F9350043E3B5B9B3C68"
    )
    assert source["identity_gate"]["complete_H_selected"] is False
    assert {record["class"] for record in source["statements"]} == {None, "B", "D", "P"}
    assert source["copyright_boundary"] == {
        "committed_external_pdf_content": False,
        "committed_manual_content": False,
        "committed_page_images": False,
        "committed_quotations": False,
        "permitted_record": "bibliography_raw_identity_equation_map_and_independent_derivation_only",
    }
    sestra = [record for record in source["statements"] if record["id"] == "sestra_formulation_context"]
    assert len(sestra) == 1 and sestra[0]["class"] == "B"
    assert identity["enrichment_gate"]["selected_H"] is None
    assert identity["enrichment_gate"]["selected_B"] is None
    assert identity["relationship"]["e1_rh"] == "DEFERRED_NOT_RUN"


def test_e2_a_exact_certificate_proves_nonuniqueness_without_rank_selection() -> None:
    output = _json(OUTPUT, OUTPUT_SHA256)
    certificate = output["certificate"]
    hostile = certificate["hostile_e1_a"]
    assert hostile == {
        "common_image": ["0", "0", "0", "0"],
        "drill_rank": 3,
        "full_rank_upper_bound": 17,
        "immutable_terminal": "NO_GO_CANDIDATE_E1_A_RANK_DEFICIENCY",
    }
    nonunique = certificate["nonuniqueness"]
    assert nonunique["status"] == "TWO_NON_EQUIVALENT_AFFINE_COVARIANT_DISPLACEMENT_LIFTS"
    assert all(nonunique["boundary_trace_difference_zero"].values())
    assert nonunique["members"] == [
        "cubic_boundary_lift",
        "cubic_boundary_lift_plus_interior_mode",
    ]
    assert certificate["scope_invariants"] == {
        "center_curl": "EXACT_U_XI_TIMES_A_INVERSE",
        "physical_mapping": "CHI_J_A_A_G_INVERSE_EQ_CHI_ABS_DET_A_A_INVERSE_TRANSPOSE",
        "production_mechanics": "NOT_RUN_IDENTITY_AMBIGUOUS",
    }

    expected = {
        "square": {
            "determinant": "1",
            "cofactor_map": [["1", "0"], ["0", "1"]],
            "cofactor_pairing": [["1", "0"], ["0", "1"]],
            "difference_strain": ["8/27", "-1/4", "-5/18"],
            "difference_energy": "128/35",
            "member_energies": ["32/5", "1952/105"],
        },
        "skew_rational": {
            "determinant": "16",
            "cofactor_map": [["12", "-4"], ["-5", "3"]],
            "cofactor_pairing": [["16", "0"], ["0", "16"]],
            "difference_strain": ["13/4", "1007/1728", "-203/72"],
            "difference_energy": "305584/175",
            "member_energies": ["2266", "3692602/525"],
        },
    }
    witnesses = certificate["affine_geometry_witnesses"]
    assert set(witnesses) == set(expected)
    for geometry_name, frozen in expected.items():
        witness = witnesses[geometry_name]
        assert witness["determinant"] == frozen["determinant"]
        assert witness["cofactor_map"] == frozen["cofactor_map"]
        assert witness["cofactor_pairing"] == frozen["cofactor_pairing"]
        assert witness["affine_patch_lift_activation"] == ["0"] * 5
        assert witness["difference_engineering_strain_at_r_1_2_s_1_3"] == frozen["difference_strain"]
        assert witness["difference_strain_energy"] == frozen["difference_energy"]
        assert all(witness["same_boundary_trace"].values())
        for vertices in witness["same_vertices"].values():
            assert vertices == [["0", "0"]] * 4
        assert witness["eta_states"] == {
            "combined_rigid_r": "0",
            "pure_common_drill_g": "1",
            "translation_spin_s": "-1",
        }
        energies = list(witness["member_state_strain_energies"].values())
        assert [record["pure_common_drill_g"] for record in energies] == frozen["member_energies"]
        for record in energies:
            assert record["combined_rigid_r"] == "0"
            assert record["pure_common_drill_g"] == record["translation_spin_s"]
            assert record["pure_common_drill_g"] != "0"
        covariance = witness["covariance"]
        operations = covariance["d4_reparameterizations"]
        assert len(operations) == 8
        assert {record["determinant"] for record in operations} == {-1, 1}
        assert all(record["a3_sign"] == record["determinant"] for record in operations)
        assert all(record["chi"] == 1 for record in operations)
        assert all(record["eta_pseudoscalar"] and record["physical_lift_invariant"] for record in operations)
        assert covariance["frame_rotation"] is True
        assert covariance["normal_reversal"] is True
        assert covariance["origin_shift"] is True
        assert covariance["unit_scale"] == "7/3"


def test_e2_a_preserves_two_tier_baseline_and_all_historical_results() -> None:
    baseline = _json(ROOT / "docs/reference_cases/s4_e2_a_baseline.json")
    inventory = _json(ROOT / "docs/reference_cases/s4_e2_a_test_inventory.json")
    assert baseline["authority"] == {
        "branch": "codex/s4-e2-a-source-kinematics",
        "commit": "281ed90e148c125edbec27e7336a8f9f0df08edc",
        "e0_commit": "87b639499187736c59d87bc4aa8e6bd7f819d28b",
        "e0_tree": "c01fd5cab7b63325e6cb5b70000f4586d4788563",
        "tree": "1ee60da4717055f5cc1b37ff9369877bb1867861",
    }
    assert inventory["total_reference_count"] == 110
    assert inventory["total_reference_is_not_one_live_suite"] is True
    assert inventory["tiers"]["e0_immutable"]["count"] == 94
    assert inventory["tiers"]["e1_committed"]["count"] == 16
    assert inventory["tiers"]["e1_committed"]["historical_report_statement_preserved"] == 15

    e1_nodes: list[str] = []
    for record in inventory["tiers"]["e1_committed"]["files"]:
        raw = _record(record["path"], record["bytes"], record["sha256"])
        tree = ast.parse(raw.decode("utf-8"), filename=record["path"])
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
                e1_nodes.append(f"{record['path']}::{node.name}")
    node_raw = ("\n".join(e1_nodes) + "\n").encode("utf-8")
    assert len(e1_nodes) == 16 and len(node_raw) == 1692
    assert _sha(node_raw) == E1_NODE_LIST_SHA256

    immutable = baseline["immutable_e1"]
    e1_baseline = _json(
        ROOT / immutable["baseline"]["path"], immutable["baseline"]["sha256"]
    )
    for name in ("a_output", "r_output", "status"):
        record = immutable[name]
        value = _json(ROOT / record["path"], record["sha256"])
        assert len((ROOT / record["path"]).read_bytes()) == record["bytes"]
        if "terminal" in record:
            assert value["candidate_terminal"] == record["terminal"]
    for name, record in e1_baseline["immutable_results"].items():
        value = _json(ROOT / record["path"], record["sha256"])
        if name == "candidate_a":
            observed = value["pair_terminal"]
        elif name == "rank_four":
            observed = value["scientific_summary"]["outcome"]
        else:
            observed = value["candidate_terminal"]
        assert observed == record["terminal"]

    for relative, record in e1_baseline["production_sources"].items():
        raw = _canonical_lf(ROOT / relative)
        assert len(raw) == record["canonical_lf_bytes"]
        assert _sha(raw) == record["canonical_lf_sha256"]
