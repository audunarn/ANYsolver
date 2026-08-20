from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COMMIT1 = "00d6a66c34712c8f3fd1e38113c83d0a03b2de43"
COMMIT1_TREE = "661bf7ce0c509adb3f8e0f0559974ce24171dda1"
COMMIT1_PARENT = "46231c56d4c7d24000421fc3ba0f4800239e64bd"
COMMIT1_SUBJECT = "docs: preregister E4 PL Q1S implementation completion"
CLOSEOUT_SUBJECT = "docs: close E4 PL Q1S implementation-identity block"
TERMINAL = "BLOCKED_E4_PL_Q1S_IMPLEMENTATION_IDENTITY"

IMPLEMENTATION_PATHS = {
    "docs/reference_cases/e4_pl_q1s_reference.py",
    "docs/reference_cases/e4_pl_q1s_oracle.py",
    "docs/reference_cases/e4_pl_q1s_scientific_test_runner.py",
    "docs/reference_cases/e4_pl_q1s_implementation_manifest.json",
    "docs/reference_cases/e4_pl_q1s_implementation_review.json",
    "tests/test_e4_pl_q1s_frame_and_fields.py",
    "tests/test_e4_pl_q1s_local_algebra.py",
    "tests/test_e4_pl_q1s_recovery.py",
    "tests/test_e4_pl_q1s_global_supports.py",
    "tests/test_e4_pl_q1s_terminal_and_agreement.py",
}

BLOCKED_PATHS = {
    "docs/reference_cases/e4_pl_q1s_status.json",
    "docs/E4_PL_Q1S_LOCAL_QUALIFICATION.md",
    "docs/reference_cases/e4_pl_q1s_scientific_review.json",
    "docs/E4_PL_Q1S_COMPLETION.md",
    "tests/test_e4_pl_q1s_closeout.py",
}

CLOSEOUT_PATHS = IMPLEMENTATION_PATHS | BLOCKED_PATHS

BOUND = {
    "docs/reference_cases/e4_pl_q1s_reference.py": (
        163929,
        "811DE7A662FA5C1B6804CEB62D50D663B36B8FAE248BD07D7B8FE0F9E54E3AFB",
    ),
    "docs/reference_cases/e4_pl_q1s_oracle.py": (
        158075,
        "169E1ABA4179C23758A623B4F951889F4A20CD182E0EF0FF9B97CDF8033140EF",
    ),
    "docs/reference_cases/e4_pl_q1s_scientific_test_runner.py": (
        25309,
        "81206B3BD938831828ACF69E3D12519445C8C4A800B8CC518819B9AAD63C8706",
    ),
    "docs/reference_cases/e4_pl_q1s_implementation_manifest.json": (
        15862,
        "40FFB09ABF16C66D5F23BDEDC63E8A7465C7EFB44545EC765129781153DECF3F",
    ),
    "docs/reference_cases/e4_pl_q1s_implementation_review.json": (
        2035,
        "489D77ADE3B8621EC99F60A80D769F40603B38D863B97192FDBEB82067EE3E86",
    ),
    "tests/test_e4_pl_q1s_frame_and_fields.py": (
        5375,
        "4441839B450519B4983976C681F5EA8AE477DC26A4646B72FA3298D2B76BA52E",
    ),
    "tests/test_e4_pl_q1s_local_algebra.py": (
        2306,
        "E87EDA1DA42153010194F1A2FA6C1159D05DFEAE67D9EB2C11EAF4E5ACAD3FC3",
    ),
    "tests/test_e4_pl_q1s_recovery.py": (
        3137,
        "B220C7BDE34D23900823D83A32C27982497A63B9D05304EC11AEAB4683E9E296",
    ),
    "tests/test_e4_pl_q1s_global_supports.py": (
        2035,
        "9B3DFBDCBC9457ED63E5302D75AD828DF430564C16ACEC4A12CBB45FA7F7B2D9",
    ),
    "tests/test_e4_pl_q1s_terminal_and_agreement.py": (
        5329,
        "65B358C5077E657E48BD15ACEB0257261632E19BBE33F90744ABC86081C679D7",
    ),
    "docs/reference_cases/e4_pl_q1s_status.json": (
        4654,
        "66265903D6D4C9AE14EEFB13D4D1A278064817EC6AEE9FF6D4EC52E892E2199E",
    ),
    "docs/E4_PL_Q1S_LOCAL_QUALIFICATION.md": (
        4580,
        "5DA2BE2C26BBA41F7AF53F82BB2510711870BE792E696E80E5570E959A46F62E",
    ),
    "docs/reference_cases/e4_pl_q1s_scientific_review.json": (
        3594,
        "68EEAF434E1C9E02C4B147C92D5573E8A05C666FD019433F8EF7B042A3FBEF31",
    ),
    "docs/E4_PL_Q1S_COMPLETION.md": (
        2723,
        "D9E86D6F7DEF49B272C9C1063E8E3EC4BD1F1FC1A25B9503DDC769216C19F87A",
    ),
}

REQUIRED_ABSENCES = {
    "docs/agent_plans/S4_E4_PL_Q1B_NONINTRUSION_STABILITY_LOCKING_PLAN.md",
    "docs/reference_cases/e4_pl_q1s_execution_contract.json",
    "docs/reference_cases/e4_pl_q1s_contract_review.json",
    "tests/test_e4_pl_q1s_contract.py",
    "docs/reference_cases/e4_pl_q1s_reference_raw.json",
    "docs/reference_cases/e4_pl_q1s_oracle_raw.json",
    "docs/reference_cases/e4_pl_q1s_agreement.json",
    "docs/reference_cases/e4_pl_q1s_output.json",
    "docs/reference_cases/e4_pl_q1s_execution_authority.json",
    "docs/reference_cases/e4_pl_q1s_scientific_test_result.json",
}

PRESERVED_ROOTS = {
    ".s4_candidate_a_pinned/",
    ".s4_stage_m_execution/",
    ".s4_stage_m_mpmath/",
    ".s4_stage_m_mpmath_clean/",
    ".s4_stage_m_patch_tools/",
    "tmp/",
}


def _git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _raw(path: str) -> bytes:
    return (ROOT / path).read_bytes()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def _strict_json(path: str) -> dict[str, object]:
    def pairs(items: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"duplicate key: {key}")
            result[key] = value
        return result

    def nonfinite(token: str) -> object:
        raise ValueError(f"nonfinite JSON token: {token}")

    raw = _raw(path)
    value = json.loads(raw, object_pairs_hook=pairs, parse_constant=nonfinite)
    assert isinstance(value, dict)
    canonical = (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")
    assert raw == canonical
    return value


def _outside_preserved(path: str) -> bool:
    return not any(path.startswith(prefix) for prefix in PRESERVED_ROOTS)


def _paths(lines: str) -> set[str]:
    return {
        line.replace("\\", "/")
        for line in lines.splitlines()
        if line.strip()
    }


def test_q1s_closeout_hash_dag_extent_terminal_and_production_boundary() -> None:
    # This node is deliberately static: it never imports either implementation,
    # constructs a registered case, or collects the five scientific nodes.
    for path, (size, digest) in BOUND.items():
        raw = _raw(path)
        assert len(raw) == size, path
        assert _sha256(raw) == digest, path
        assert not raw.startswith(b"\xef\xbb\xbf"), path
        assert b"\r" not in raw, path
        assert raw.endswith(b"\n"), path

    self_raw = _raw("tests/test_e4_pl_q1s_closeout.py")
    assert not self_raw.startswith(b"\xef\xbb\xbf")
    assert b"\r" not in self_raw
    assert self_raw.endswith(b"\n")

    status = _strict_json("docs/reference_cases/e4_pl_q1s_status.json")
    manifest = _strict_json(
        "docs/reference_cases/e4_pl_q1s_implementation_manifest.json"
    )
    implementation_review = _strict_json(
        "docs/reference_cases/e4_pl_q1s_implementation_review.json"
    )
    scientific_review = _strict_json(
        "docs/reference_cases/e4_pl_q1s_scientific_review.json"
    )
    authority = _strict_json(
        "docs/reference_cases/e4_pl_q1s_authority_contract.json"
    )
    allowed = _strict_json("docs/reference_cases/e4_pl_q1s_allowed_extent.json")

    assert status["schema"] == "anysolver.s4.e4-pl-q1s-blocked-status-v1"
    assert status["terminal_application"] == {
        "first_match": TERMINAL,
        "precedence": 6,
        "reason": (
            "THE_ACCEPTED_IMPLEMENTATION_FREEZE_VERDICT_IS_UNAVAILABLE_AFTER_"
            "THE_SOLE_STATIC_CORRECTION_CYCLE"
        ),
    }
    assert status["final"] == {
        "production_terminal": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "q1b_execution_authorized": False,
        "q1b_plan_preparation_authorized": False,
        "terminal": TERMINAL,
    }
    assert status["candidate"] == {
        "id": (
            "candidate_e4_pl_q1s."
            "wg2020_numbered_frame_surface_pl_planar_linear_iso_v1"
        ),
        "production_registration": False,
        "scientific_classification": "NOT_ESTABLISHED",
        "status": "DORMANT_UNQUALIFIED",
    }
    assert status["component_ledger"]["implementation_identity"][
        "correction_cycle"
    ] == {"max": 1, "used": 1}
    assert status["component_ledger"]["implementation_identity"]["status"] == (
        "REJECT_P1"
    )
    assert status["component_ledger"]["mechanics"] == {
        "registered_cases": "NOT_RUN",
        "scientific_tests": "NOT_RUN",
        "status": "NOT_RUN",
    }
    assert status["evidence_chain"]["registered_mechanics_run"] is False
    assert status["evidence_chain"]["accepted_implementation_freeze_commit"] is False
    assert status["evidence_chain"]["caller_bound_contract_created"] is False
    assert status["implementation_evidence"]["mechanics_executed"] is False

    assert manifest["implementation_stage"]["static_correction_max"] == 1
    assert manifest["implementation_stage"]["static_correction_used"] == 1
    assert manifest["implementation_stage"]["mechanics_executed"] is False
    assert manifest["implementation_stage"]["registered_cases_executed"] is False
    assert manifest["static_verification"]["sole_correction_cycle_closed"] is True
    assert manifest["static_verification"]["mechanics_executed"] is False
    assert manifest["scientific_tests"]["execution_state"] == "FROZEN_NOT_RUN"

    exact_review_keys = {
        "findings",
        "reviewed_inputs",
        "reviewer_independence",
        "schema",
        "verdict",
    }
    assert set(implementation_review) == exact_review_keys
    assert implementation_review["schema"] == (
        "anysolver.s4.e4-pl-q1s-implementation-review-v1"
    )
    assert implementation_review["verdict"] == "REJECT_Q1S_IMPLEMENTATION_FREEZE_P1"
    assert implementation_review["findings"][0]["terminal"] == TERMINAL
    assert implementation_review["findings"][0]["mechanics_executed"] is False
    assert implementation_review["reviewer_independence"]["reviewed_input_authorship"] is False

    assert set(scientific_review) == exact_review_keys
    assert scientific_review["schema"] == (
        "anysolver.s4.e4-pl-q1s-blocked-closeout-review-v1"
    )
    assert scientific_review["verdict"] == "ACCEPT_Q1S_BLOCKED_CLOSEOUT_NO_P0_P1"
    assert scientific_review["reviewer_independence"]["reviewed_input_authorship"] is False
    assert scientific_review["reviewer_independence"]["mechanics_executed"] is False
    route = scientific_review["findings"][0]["route"]
    assert route == {
        "parent": COMMIT1,
        "path_count": 15,
        "path_expression": "IMPLEMENTATION10_UNION_BLOCKED5",
        "subject": CLOSEOUT_SUBJECT,
    }

    report = _raw("docs/E4_PL_Q1S_LOCAL_QUALIFICATION.md").decode("utf-8")
    completion = _raw("docs/E4_PL_Q1S_COMPLETION.md").decode("utf-8")
    for text in (report, completion):
        assert TERMINAL in text
        assert "DORMANT_UNQUALIFIED" in text
        assert "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED" in text
        assert "ShellElement" in text
        assert "not a scientific" in text.lower()
    assert "REJECT_Q1S_IMPLEMENTATION_FREEZE_P1" in completion
    assert "ACCEPT_Q1S_BLOCKED_CLOSEOUT_NO_P0_P1" in completion

    blocked = authority["blocked_closeout_protocol"]
    assert blocked["path_sets"]["BLOCKED5"] == [
        "docs/reference_cases/e4_pl_q1s_status.json",
        "docs/E4_PL_Q1S_LOCAL_QUALIFICATION.md",
        "docs/reference_cases/e4_pl_q1s_scientific_review.json",
        "docs/E4_PL_Q1S_COMPLETION.md",
        "tests/test_e4_pl_q1s_closeout.py",
    ]
    impl_route = next(
        row
        for row in blocked["alternative_commits"]
        if row["id"] == "IMPLEMENTATION_IDENTITY_BLOCKED_CLOSEOUT"
    )
    assert impl_route == {
        "exact_parent": "ACCEPTED_COMMIT1",
        "id": "IMPLEMENTATION_IDENTITY_BLOCKED_CLOSEOUT",
        "path_count": 15,
        "path_expression": "IMPLEMENTATION10_UNION_BLOCKED5",
        "required_path_sets": ["IMPLEMENTATION", "BLOCKED5"],
        "subject": CLOSEOUT_SUBJECT,
    }
    assert set(authority["stage_extents"]["IMPLEMENTATION"]) == IMPLEMENTATION_PATHS
    assert allowed["stage_counts"] == {
        "CONTRACT": 3,
        "IMPLEMENTATION": 10,
        "OUTCOME": 11,
        "PLAN": 11,
    }

    for path in REQUIRED_ABSENCES:
        assert not (ROOT / path).exists(), path

    assert _git("diff", "--cached", "--quiet", check=False).returncode == 0
    assert _git("diff", "--quiet", check=False).returncode == 0

    tracked = _paths(_git("diff", "--name-only", COMMIT1, "--").stdout)
    untracked = {
        path
        for path in _paths(_git("ls-files", "--others", "--exclude-standard").stdout)
        if _outside_preserved(path)
    }
    assert tracked | untracked == CLOSEOUT_PATHS
    assert tracked <= CLOSEOUT_PATHS

    head = _git("rev-parse", "HEAD").stdout.strip()
    tree = _git("rev-parse", "HEAD^{tree}").stdout.strip()
    if head == COMMIT1:
        assert tree == COMMIT1_TREE
        assert _git("rev-parse", "HEAD^").stdout.strip() == COMMIT1_PARENT
        assert _git("show", "-s", "--format=%s", "HEAD").stdout.strip() == (
            COMMIT1_SUBJECT
        )
        assert tracked == set()
        assert untracked == CLOSEOUT_PATHS
    else:
        assert _git("rev-parse", "HEAD^").stdout.strip() == COMMIT1
        assert _git("show", "-s", "--format=%s", "HEAD").stdout.strip() == (
            CLOSEOUT_SUBJECT
        )
        commit_paths = _paths(
            _git("diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD").stdout
        )
        assert commit_paths == CLOSEOUT_PATHS
        assert tracked == CLOSEOUT_PATHS
        assert untracked == set()

    production_delta = _paths(
        _git(
            "diff",
            "--name-only",
            COMMIT1,
            "--",
            ".gitattributes",
            ".github",
            "pyproject.toml",
            "setup.cfg",
            "setup.py",
            "src",
        ).stdout
    )
    assert production_delta == set()
    assert status["production_boundary"] == {
        "api_change": False,
        "dispatch_change": False,
        "gitattributes_change": False,
        "legacy_default": "ShellElement",
        "package_change": False,
        "production_source_change": False,
        "recovery_change": False,
        "serialization_change": False,
        "workflow_change": False,
    }
