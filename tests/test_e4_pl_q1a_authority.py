from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = "97c3150c9ecd41cf42fc108e9ff476497154428c"
BASE_TREE = "9ea7e81a17c246e41b3fdfc236200d9dbf3e2b60"
ORACLE = ROOT / "docs/reference_cases/e4_pl_q1a_oracle.py"


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        assert key not in result
        result[key] = value
    return result


def _json(relative: str) -> dict[str, object]:
    raw = (ROOT / relative).read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf") and b"\r" not in raw and raw.endswith(b"\n")
    value = json.loads(
        raw.decode("utf-8"), object_pairs_hook=_pairs,
        parse_constant=lambda token: (_ for _ in ()).throw(AssertionError(token)),
    )
    assert isinstance(value, dict)
    assert raw == (json.dumps(value, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")
    return value


def _git(*arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments], cwd=ROOT, check=True, capture_output=True, text=True,
    ).stdout.strip()


def test_e4_pl_q1a_exact_main_authority_and_immutable_e4_packet() -> None:
    baseline = _json("docs/reference_cases/e4_pl_q1a_baseline.json")
    assert baseline["authority"] == {
        "branch": "codex/s4-e4-pl-planar-linear-qualification",
        "commit": BASE_COMMIT,
        "tree": BASE_TREE,
    }
    assert _git("rev-parse", f"{BASE_COMMIT}^{{tree}}") == BASE_TREE
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", BASE_COMMIT, "HEAD"], cwd=ROOT, check=True,
    )
    assert baseline["attachment"] == {
        "bytes": 26423,
        "path_label": "Downloads/S4_E4_PL_PLANAR_LINEAR_QUALIFICATION_PLAN_MAIN_97C3150.md",
        "role": "B_BACKGROUND_DESIGN_INPUT",
        "sha256": "91CFD5305896AE4DAA5875BB55B70B3EE9D140F8E14165DBFD5904E6BA6D43BD",
    }
    for key in ("conditional_plan", "review", "status"):
        record = baseline["e4"][key]
        raw = (ROOT / record["path"]).read_bytes()
        assert (len(raw), _sha(raw)) == (record["bytes"], record["sha256"])
    assert baseline["e4"]["review"]["verdict"] == "ACCEPT_NO_P0_OR_P1"
    status = _json("docs/reference_cases/e4_status.json")
    assert status["components"]["core"]["terminal"] == "GO_E4_OPEN_CORE_IDENTITY"
    assert status["components"]["ws"]["terminal"] == "NO_GO_E4_WS_LOCAL_CONDENSATION_AND_RANK"
    assert status["components"]["pl"]["terminal"] == "PROVISIONAL_GO_E4_PL_LINEAR_QUALIFICATION_PLAN"
    assert status["production"]["terminal"] == "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"


def test_e4_pl_q1a_test_inventory_and_historical_roots_are_frozen() -> None:
    baseline = _json("docs/reference_cases/e4_pl_q1a_baseline.json")
    inventory = _json("docs/reference_cases/e4_pl_q1a_test_inventory.json")
    accepted = inventory["accepted_e4"]
    assert accepted == {
        "canonical_lf_bytes": 1795,
        "canonical_lf_sha256": "1C29534F6568AA2FF072F5D776E9D10BD71DE85F51C7562827FC6A3F0234E10F",
        "count": 20,
        "files": [
            "tests/test_e4_baseline.py", "tests/test_e4_core_identity.py",
            "tests/test_e4_ws_feasibility.py", "tests/test_e4_pl_identity.py",
            "tests/test_e4_route.py", "tests/test_e4_closeout.py",
        ],
        "run_location": "DETACHED_97C3150_ONLY",
    }
    accepted_result = baseline["e4"]["test_inventory"]
    assert {key: accepted_result[key] for key in (
        "canonical_lf_bytes", "canonical_lf_sha256", "count", "execution",
    )} == {
        "canonical_lf_bytes": accepted["canonical_lf_bytes"],
        "canonical_lf_sha256": accepted["canonical_lf_sha256"],
        "count": accepted["count"],
        "execution": "DETACHED_EXACT_AUTHORITY_WITH_WORKSPACE_BASETEMP",
    }
    assert accepted_result["result"].startswith("20_PASSED_IN_")
    assert baseline["preserved_untracked_roots"] == [
        ".s4_candidate_a_pinned/", ".s4_stage_m_execution/", ".s4_stage_m_mpmath/",
        ".s4_stage_m_mpmath_clean/", ".s4_stage_m_patch_tools/", "tmp/",
    ]


def test_e4_pl_q1a_material_and_production_boundaries() -> None:
    material = _json("docs/reference_cases/e4_pl_q1a_material_contract.json")
    assert material["anymaterial"] == {
        "commit": "4626887667f4c251479d26f321b9e73b046a2783",
        "tree": "0d40fe67ea5e0b52f11a47aeb467d6993b205a2b",
    }
    assert _git("-c", "safe.directory=C:/Github/ANYmaterial", "-C", "C:/Github/ANYmaterial",
                "rev-parse", "4626887667f4c251479d26f321b9e73b046a2783^{tree}") \
        == material["anymaterial"]["tree"]
    fixture = material["fixture"]
    raw = (ROOT / fixture["path"]).read_bytes()
    assert (len(raw), _sha(raw)) == (fixture["bytes"], fixture["sha256"])
    inherited = _json(str(fixture["path"]))
    assert inherited["rp_c208"]["grades"] == ["S235", "S275", "S355", "S420", "S460"]
    assert inherited["rp_c208"]["row_count"] == 17
    inherited_detail = material["inherited_detail"]
    detail_raw = (ROOT / inherited_detail["path"]).read_bytes()
    assert (len(detail_raw), _sha(detail_raw)) == (2135, inherited_detail["sha256"])
    detail = _json(inherited_detail["path"])
    exact_ranges = {
        "S235": [[0, 16], [16, 40], [40, 63], [63, 100]],
        "S275": [[0, 16], [16, 40], [40, 63]],
        "S355": [[0, 16], [16, 40], [40, 63], [63, 100]],
        "S420": [[0, 16], [16, 40], [40, 63]],
        "S460": [[0, 16], [16, 40], [40, 63]],
    }
    assert detail["rp_c208_dataset"]["grades"] == exact_ranges
    assert sum(len(ranges) for ranges in exact_ranges.values()) == 17
    assert material["compatibility"]["new_public_fields"] == []
    assert material["compatibility"]["dnv_approval"] is False

    # Exercise the exact pinned sibling package in an isolated process.  Both
    # the public property lookup and ordinary StructuralMaterial-compatible
    # isotropic object must construct for every registered range without a
    # drill/Cosserat/stabilization input.
    script = (
        "import dataclasses,json,sys; "
        "from anymaterial.library import dnv_c208_steel_properties,steel; "
        "ranges=json.loads(sys.argv[1]); rows=[]; "
        "ordinary={'name','elastic_modulus','poisson_ratio','density','yield_stress','hardening_curve'}; "
        "[(lambda p,m,grade,lo,hi: ("
        "rows.append({'grade':grade,'range':[lo,hi],'class':p['thickness_class']}), "
        "(_ for _ in ()).throw(AssertionError('material fields')) if set(dataclasses.asdict(m)) != ordinary else None, "
        "(_ for _ in ()).throw(AssertionError('grade')) if p['grade'] != grade else None"
        "))(dnv_c208_steel_properties(grade,hi/1000),steel(grade,hi/1000),grade,lo,hi) "
        "for grade,spans in ranges.items() for lo,hi in spans]; "
        "print(json.dumps({'count':len(rows),'rows':rows},sort_keys=True,separators=(',',':')))")
    environment = os.environ.copy()
    environment.update({
        "PYTHONPATH": "C:/Github/ANYmaterial/src",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONHASHSEED": "0",
    })
    process = subprocess.run(
        [sys.executable, "-c", script, json.dumps(exact_ranges, separators=(",", ":"))],
        cwd=ROOT, env=environment, check=False, capture_output=True, text=True, timeout=60,
    )
    assert process.returncode == 0, process.stderr
    constructed = json.loads(process.stdout)
    assert constructed["count"] == 17
    assert [(row["grade"], row["range"]) for row in constructed["rows"]] == [
        (grade, span) for grade, ranges in exact_ranges.items() for span in ranges
    ]

    allowed = _json("docs/reference_cases/e4_pl_q1a_allowed_extent.json")
    assert allowed["authority"] == {"commit": BASE_COMMIT, "tree": BASE_TREE}
    assert allowed["modified_paths"] == [] and allowed["production_paths"] == []
    for forbidden in ("src/", ".github/", "pyproject.toml"):
        changed = _git("diff", "--name-only", BASE_COMMIT, "--", forbidden)
        assert changed == ""


def test_e4_pl_q1a_source_gate_is_unique_closed_and_copyright_clean() -> None:
    source_map = _json("docs/reference_cases/e4_pl_q1a_source_map.json")
    assert source_map["candidate_id"] == (
        "candidate_e4_pl_q1.wg2020_n7_k0_surface_pl_planar_linear_iso_v1"
    )
    assert source_map["source_gate"] == "CLOSED_UNIQUE_NON_AFFINE_PLANAR_IDENTITY"
    assert len(source_map["indispensable_statements"]) == 11
    assert {row["status"] for row in source_map["indispensable_statements"][:-1]} == {"CLOSED"}
    assert source_map["indispensable_statements"][-1]["status"] == "DISPROVED_D4_AND_REVERSAL"
    assert source_map["qualification_terminal"] == "NO_GO_E4_PL_Q1A_PATCH_OR_COVARIANCE"
    assert "GAUSS_L2_PROJECTION_OF_FULL_RATIONAL_CURL" in source_map["rejected_non_equivalent_choices"]
    assert "FOURTH_GAUSS_INTERPOLATION_COEFFICIENT_AS_RESIDUAL" in (
        source_map["rejected_non_equivalent_choices"]
    )
    assert set(source_map["copyright_boundary"].values()) == {False}
    namespace = runpy.run_path(str(ORACLE))
    support = namespace["_validate_governance"]()
    assert support == {
        "forbidden_direct_drill_is_pure_QD": True,
        "full_clamp_is_hostile_physical_plus_drill": True,
        "physical_projector_idempotent": True,
        "physical_support_annihilates_QD": True,
        "projectors_orthogonal": True,
    }
    environment = _json("docs/reference_cases/e4_pl_q1a_environment.json")
    assert environment["oracle_runtime"]["python_executable"] == "C:/Python/Python313/python.exe"
    assert environment["oracle_runtime"]["python_version"] == "3.13.9"
    assert Path(sys.executable).as_posix().casefold() == "c:/python/python313/python.exe".casefold()
