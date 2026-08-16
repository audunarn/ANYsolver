from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
BASE = "a9b45ca95303bc4b30b893fbb0d7177f9c98db03"

EXPECTED = {
    ".gitattributes": (1328, "DA5B76EC3ECB83B28114668EE1425C33D3EDCBE8FB2E708F775BEA47477CEC87"),
    "docs/S4_CANDIDATE_E0_INDEPENDENT_REVIEW.md": (3988, "CFBDB755E5A9CB8901A1DE80DCBEE0872574D90465DC36A47084AC2F5675D849"),
    "docs/S4_CANDIDATE_E0_QUALIFICATION_REPORT.md": (4178, "EC6F8A468384D65A75F783CC1947F6F5AC9E49D0FD3CDE741FEB02A45037C6FE"),
    "docs/reference_cases/s4_candidate_e0_contract.json": (4528, "D3ACF44D4690E7ED8E257B1A1A5DB124CE91ADAFE98ACDD186305C56A4740B03"),
    "docs/reference_cases/s4_candidate_e0_output.json": (2159, "513465CB4993C398C9B10334244F07A26AC9A1980D49A24F79F5FC3CC7EB04AD"),
    "docs/reference_cases/s4_candidate_e0_oracle.py": (19683, "48FBD49E7011197A370492E61C76167BDC038054D47F3ADB2A7DA6DCEAF82A4A"),
    "tests/test_s4_candidate_e0_source_gate.py": (12555, "96366B71BBAAA07F4E34B9B02FC27FC2101F673BFF4AC16243C5504F71B4CE9D"),
}

NEW_PATHS = {
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
}


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        assert key not in result
        result[key] = value
    return result


def _strict_json(raw: bytes) -> dict[str, object]:
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


def test_candidate_e0_source_gate_closeout_is_exact_and_production_safe() -> None:
    for relative, (size, sha256) in EXPECTED.items():
        raw = (ROOT / relative).read_bytes()
        assert len(raw) == size
        assert _sha(raw) == sha256
        assert not raw.startswith(b"\xef\xbb\xbf")
        assert b"\r" not in raw and raw.endswith(b"\n")

    contract = _strict_json((ROOT / "docs/reference_cases/s4_candidate_e0_contract.json").read_bytes())
    output = _strict_json((ROOT / "docs/reference_cases/s4_candidate_e0_output.json").read_bytes())
    assert set(contract["allowed_extent"]["new_paths"]) == NEW_PATHS
    assert contract["allowed_extent"] == {
        "modified": [".gitattributes"],
        "new_paths": contract["allowed_extent"]["new_paths"],
        "production_paths": [],
    }
    assert output["candidate_terminal"] == "BLOCKED_CANDIDATE_E_SOURCE_OR_IDENTITY"
    assert output["terminal_reason"] == "MISSING_EXACT_ALL_NODE_DRILL_FORMULATION_AND_SOURCE_CONFLICT"
    assert output["overall_release_terminal"] == "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"
    assert output["mechanics_results_present"] is False
    assert output["materials"]["candidate_element_material_compatibility"] == "NOT_RUN_DUE_TO_SOURCE_GATE"
    assert output["materials"]["dnv_approval"] is False

    review = (ROOT / "docs/S4_CANDIDATE_E0_INDEPENDENT_REVIEW.md").read_text(encoding="utf-8")
    assert "`ACCEPT` — no P0 or P1 defect remains" in review
    assert "85 tests" in review and "eight\ntests" in review and "93 tests" in review

    diff = subprocess.run(
        ["git", "diff", "--name-only", BASE],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert diff.returncode == 0, diff.stderr.decode(errors="replace")
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert untracked.returncode == 0, untracked.stderr.decode(errors="replace")
    observed = set(diff.stdout.decode().splitlines()) | set(untracked.stdout.decode().splitlines())
    preserved = (
        ".s4_candidate_a_pinned/",
        ".s4_stage_m_execution/",
        ".s4_stage_m_mpmath/",
        ".s4_stage_m_mpmath_clean/",
        ".s4_stage_m_patch_tools/",
        "tmp/",
    )
    candidate_paths = {path for path in observed if not path.startswith(preserved)}
    assert candidate_paths == NEW_PATHS | {".gitattributes"}
    assert not any(path.startswith(("src/", ".github/", "pyproject.toml")) for path in candidate_paths)
