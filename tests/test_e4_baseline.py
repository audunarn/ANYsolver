from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = "c55ad9e5f8e78b1749c4152e4ba66b6f9e20b198"
BASE_TREE = "e7e35bb880a88a8f7d736d32652c80442d8b9ec1"

COMMON = {
    "docs/agent_plans/S4_E4_VARIATIONAL_DRILL_CLOSURE_PLAN.md": (
        5570,
        "BE515556E2019CDE69E4E7489FD9200F16CDE8D82C032131776EA0520DEB59A1",
    ),
    "docs/E4_BASELINE_AND_AUTHORITY.md": (
        1010,
        "41088EDEEB9B7A2DB8A13FFD22F476AAD69E7D86E8BD3AB8DB086688807F0D01",
    ),
    "docs/reference_cases/e4_allowed_extent.json": (
        2052,
        "A34D96E442DADA69F7EBD2A9E3888B2885386431BC82D6BF80AD57B851A9842E",
    ),
    "docs/reference_cases/e4_baseline.json": (
        3309,
        "7A404185E3F15FA56B589264FA5C816031B3BF25BA8003D081844B517EABB793",
    ),
    "docs/reference_cases/e4_environment.json": (
        1235,
        "EC3FE4B95C556F8CF6983083FD29EBA974D9FB953E33017CA3C37CBDC37B3B6F",
    ),
    "docs/reference_cases/e4_source_registry.json": (
        3421,
        "66C395568FB4BCC90BCD57D9B8167E204C92A4390BBA643F3FA8516470CA4FA3",
    ),
    "docs/reference_cases/e4_test_inventory.json": (
        3581,
        "9B6F67242586BFC5A661D2790AFA8774254D68116871D8ACA4E3D1F126D220DA",
    ),
}

E3_CLOSEOUT = {
    "docs/E3_ROUTE_SELECTION_COMPLETION.md": (
        2292,
        "6312D75B196146811E3AC731A4641AFC7C9F5BA4981D2C8B1301EF97685DE704",
    ),
    "docs/E3_ROUTE_SELECTION_INDEPENDENT_REVIEW.md": (
        12187,
        "4AFF194BB36ADF2D12A477917A8289C67E9DEAAB48EC29522FE0432CD6813617",
    ),
    "docs/reference_cases/e3_route_status.json": (
        5577,
        "2A13A3C2AA0C86303A7EDC0DAF018133370565E091ADB0E2C76D93E535930790",
    ),
}


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        assert key not in result
        result[key] = value
    return result


def _strict_json(relative: str, expected: tuple[int, str] | None = None) -> dict[str, object]:
    raw = (ROOT / relative).read_bytes()
    if expected is not None:
        assert (len(raw), _sha(raw)) == expected
    assert not raw.startswith(b"\xef\xbb\xbf")
    assert b"\r" not in raw and raw.endswith(b"\n")
    value = json.loads(
        raw.decode("utf-8"),
        object_pairs_hook=_pairs,
        parse_constant=lambda token: (_ for _ in ()).throw(AssertionError(token)),
    )
    canonical = (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
        + "\n"
    ).encode("utf-8")
    assert raw == canonical
    return value


def _verify_record(record: dict[str, object]) -> None:
    relative = str(record["path"])
    raw = (ROOT / relative).read_bytes()
    assert len(raw) == record["bytes"]
    assert _sha(raw) == record["sha256"]


def test_e4_baseline_authority_and_canonical_common_packet() -> None:
    for relative, identity in COMMON.items():
        raw = (ROOT / relative).read_bytes()
        assert (len(raw), _sha(raw)) == identity
        assert not raw.startswith(b"\xef\xbb\xbf") and b"\r" not in raw
        assert raw.endswith(b"\n")
        if relative.endswith(".json"):
            _strict_json(relative, identity)

    tree = subprocess.run(
        ["git", "rev-parse", f"{BASE_COMMIT}^{{tree}}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert tree == BASE_TREE

    baseline = _strict_json("docs/reference_cases/e4_baseline.json", COMMON["docs/reference_cases/e4_baseline.json"])
    assert baseline["authority"] == {
        "branch": "codex/s4-e4-variational-drill-closure",
        "commit": BASE_COMMIT,
        "parent": "2ac678a7f94c250fe433f66378a83508d86ee499",
        "tree": BASE_TREE,
    }
    assert baseline["attachment"] == {
        "bytes": 30628,
        "path_label": "Downloads/S4_E4_VARIATIONAL_DRILL_CLOSURE_PLAN.md",
        "role": "LONG_RANGE_DESIGN_INPUT_SUPERSEDED_BY_E4_0_EXECUTABLE_PLAN",
        "sha256": "EF02CDFD814F57704EA6CC1972340C09563B35123393645353371EFFC2BCBFC8",
    }


def test_e4_detached_tier_evidence_is_exact_and_not_one_live_suite() -> None:
    inventory = _strict_json(
        "docs/reference_cases/e4_test_inventory.json",
        COMMON["docs/reference_cases/e4_test_inventory.json"],
    )
    baseline = _strict_json("docs/reference_cases/e4_baseline.json", COMMON["docs/reference_cases/e4_baseline.json"])
    assert inventory["one_live_combined_suite"] is False
    assert inventory["verification_policy"] == "RUN_EACH_CLOSED_WORLD_TIER_ONLY_AT_ITS_EXACT_AUTHORITY"

    expected = {
        "e0": (
            94,
            "87b639499187736c59d87bc4aa8e6bd7f819d28b",
            "c01fd5cab7b63325e6cb5b70000f4586d4788563",
            "29EF584E9B51E8420934A519B3C1E71BDD3082EFDC89DBADA4FCE0FFE8997B9F",
        ),
        "e1": (
            16,
            "281ed90e148c125edbec27e7336a8f9f0df08edc",
            "1ee60da4717055f5cc1b37ff9369877bb1867861",
            "9835FB4580C886B52BFF5961A30CD78E921B5CEED92A918312149032748A7F63",
        ),
        "e2_a": (
            8,
            "2ac678a7f94c250fe433f66378a83508d86ee499",
            "f7382e2b88343ac29c9a9e3c424f618a3652cc01",
            "5AC3AA31523FE4ED3F5498614E0A574E9BCB1D1C5C8833D7C9B41FC8A18FA3DF",
        ),
    }
    for key, (count, commit, tree, node_hash) in expected.items():
        tier = inventory["historical_tiers"][key]
        assert tier["count"] == count and tier["commit"] == commit and tier["tree"] == tree
        assert tier["node_ids_canonical_lf_sha256"] == node_hash
        assert tier["result"] == "PASS"
        assert baseline["tier_execution"][key]["result"] == "PASS"
        assert baseline["tier_execution"][key]["node_ids_canonical_lf_sha256"] == node_hash
        actual_tree = subprocess.run(
            ["git", "rev-parse", f"{commit}^{{tree}}"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        assert actual_tree == tree
        for record in tier.get("files", []):
            _verify_record(record)
        if "inventory" in tier:
            _verify_record(tier["inventory"])

    assert inventory["historical_tiers"]["e1"]["historical_report_statement_preserved"] == 15
    e3 = inventory["e3_committed"]
    assert (e3["count"], e3["scientific_count"], e3["closeout_count"]) == (15, 14, 1)
    assert e3["node_ids_canonical_lf_sha256"] == (
        "8BD3A80D30B72F6C53E65220584191D2DDAB117C6098DF1ED045498895378863"
    )
    for record in e3["files"]:
        _verify_record(record)


def test_e4_historical_terminals_sources_and_production_boundary_are_immutable() -> None:
    for relative, identity in E3_CLOSEOUT.items():
        raw = (ROOT / relative).read_bytes()
        assert (len(raw), _sha(raw)) == identity

    baseline = _strict_json("docs/reference_cases/e4_baseline.json", COMMON["docs/reference_cases/e4_baseline.json"])
    e3 = _strict_json("docs/reference_cases/e3_route_status.json", E3_CLOSEOUT["docs/reference_cases/e3_route_status.json"])
    assert baseline["historical_results"] == {
        **e3["historical_results"],
        "candidate_e1_rh": "DEFERRED_NOT_RUN",
        "e3_hw29": "BLOCKED_E3_P_HW29_PUBLIC_SOURCE",
        "e3_mitc9i": "GO_REFERENCE_E3_Q9_MITC9I_PARTIAL_PACKET",
        "e3_route": "UNCLASSIFIED_E3_Q4_FORMULATION_ROUTE",
    }
    assert e3["components"]["hw29"]["terminal"] == "BLOCKED_E3_P_HW29_PUBLIC_SOURCE"
    assert e3["components"]["mitc9i"]["terminal"] == "GO_REFERENCE_E3_Q9_MITC9I_PARTIAL_PACKET"
    assert e3["route"]["terminal"] == "UNCLASSIFIED_E3_Q4_FORMULATION_ROUTE"

    sources = _strict_json(
        "docs/reference_cases/e4_source_registry.json",
        COMMON["docs/reference_cases/e4_source_registry.json"],
    )
    assert sources["sources"]["wg2020"]["license"] == "CC-BY-4.0"
    assert sources["sources"]["mitc9i"]["role"] == (
        "P_SHELL_SCALAR_PL_NORMALIZATION_ONLY"
    )
    assert sources["sources"]["mitc9i"]["license"] == "CC-BY-4.0"
    assert sources["sources"]["wt2011"]["license"] == "COPYRIGHT_RESTRICTED_OR_UNCLEAR_REUSE"
    assert sources["sources"]["wt2011"]["access"] == (
        "PUBLIC_AUTHOR_UPLOAD_AND_USER_SUPPLIED_LAWFUL_LOCAL_COPY"
    )
    assert sources["sources"]["wt2011"]["url"].startswith("https://www.researchgate.net/")
    assert sources["sources"]["afw_quadrilateral"]["role"] == (
        "B_GENERAL_WEAK_SYMMETRY_THEORY_NOT_SHELL_IDENTITY"
    )
    assert set(sources["copyright_boundary"].values()) == {False}

    changed = subprocess.run(
        ["git", "diff", "--name-only", BASE_COMMIT, "--", "src", ".github", "pyproject.toml"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert changed == ""
    assert baseline["production"] == {
        "legacy_shell_default": True,
        "overall_release_terminal": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "production_changes_authorized": False,
    }
