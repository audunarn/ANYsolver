from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BRANCH = "codex/s4-e4-pl-q1u-execution-guard-completion"
BASE = "850733cc9d2f9185d0a73c5fa6c0acd89067caba"
COMMIT1 = "2404ec3cec03fe9ddef131d9bfd39a24e4e7eabc"
COMMIT1_TREE = "25bc45287495e9349eeebf552e76f88ec70c13b6"
COMMIT2 = "9add6b937d4e2bd5668717f9a9b8d6bd1dfe6cda"
COMMIT2_TREE = "4a4656a8f713d5ed9618f37fe185132c45d08fe2"
COMMIT3 = "d40506aee079d19ce7a1ec658a03dd499565bd0f"
COMMIT3_TREE = "0003d9d653e456630cfc15fb0725a739232c1edf"
CLOSEOUT_SUBJECT = "docs: close E4 PL Q1U oracle-or-review block"

PLAN12 = {
    "docs/agent_plans/S4_E4_PL_Q1U_EXECUTION_GUARD_COMPLETION_PLAN.md",
    "docs/reference_cases/e4_pl_q1u_plan_review.json",
    "docs/reference_cases/e4_pl_q1u_baseline.json",
    "docs/reference_cases/e4_pl_q1u_inheritance_manifest.json",
    "docs/reference_cases/e4_pl_q1u_allowed_extent.json",
    "docs/reference_cases/e4_pl_q1u_contract_vocabulary.json",
    "docs/reference_cases/e4_pl_q1u_review_schema.json",
    "docs/reference_cases/e4_pl_q1u_mechanics_equivalence_contract.json",
    "docs/reference_cases/e4_pl_q1u_authority_contract.json",
    "docs/reference_cases/e4_pl_q1u_terminal_table.json",
    "docs/reference_cases/e4_pl_q1u_test_inventory.json",
    "tests/test_e4_pl_q1u_preregistration_authority.py",
}
IMPLEMENTATION14 = {
    "docs/reference_cases/e4_pl_q1u_authority_guard.py",
    "docs/reference_cases/e4_pl_q1u_reference.py",
    "docs/reference_cases/e4_pl_q1u_oracle.py",
    "docs/reference_cases/e4_pl_q1u_scientific_test_runner.py",
    "docs/reference_cases/e4_pl_q1u_implementation_manifest.json",
    "docs/reference_cases/e4_pl_q1u_mechanics_equivalence.json",
    "docs/reference_cases/e4_pl_q1u_implementation_review.json",
    "tests/test_e4_pl_q1u_frame_and_fields.py",
    "tests/test_e4_pl_q1u_local_algebra.py",
    "tests/test_e4_pl_q1u_recovery.py",
    "tests/test_e4_pl_q1u_global_supports.py",
    "tests/test_e4_pl_q1u_terminal_and_agreement.py",
    "tests/test_e4_pl_q1u_exact_backend.py",
    "tests/test_e4_pl_q1u_authority_guard.py",
}
CONTRACT3 = {
    "docs/reference_cases/e4_pl_q1u_execution_contract.json",
    "docs/reference_cases/e4_pl_q1u_contract_review.json",
    "tests/test_e4_pl_q1u_contract.py",
}
BLOCKED5 = {
    "docs/reference_cases/e4_pl_q1u_status.json",
    "docs/E4_PL_Q1U_LOCAL_QUALIFICATION.md",
    "docs/reference_cases/e4_pl_q1u_scientific_review.json",
    "docs/E4_PL_Q1U_COMPLETION.md",
    "tests/test_e4_pl_q1u_closeout.py",
}
ROUTE6 = BLOCKED5 | {"docs/reference_cases/e4_pl_q1u_execution_authority.json"}
BOUND = {
    "docs/reference_cases/e4_pl_q1u_execution_authority.json": (1105, "A50526DB53BB632876B122CD527A08DBB7CCB605CDAB5286D8D87A27B6202E75"),
    "docs/reference_cases/e4_pl_q1u_status.json": (4896, "78694EB0C514DFC89965711B1DBEFAC67A0386C130F47248C3314184DF3176AD"),
    "docs/E4_PL_Q1U_LOCAL_QUALIFICATION.md": (2058, "2A570AE76EC752A2C674950D609A525E0827BBDD92843ADB0AD7D84BC9FA8961"),
    "docs/reference_cases/e4_pl_q1u_scientific_review.json": (745, "DC38C5A035C47E994BF27735FD7222941DBF460698474BCEFF4FFD43CCAF15DC"),
    "docs/E4_PL_Q1U_COMPLETION.md": (2378, "81B98D1A9B282D6D44448A996A19EC34A50D34E7D3C41EDA9D5E4F9E4BAA04EF"),
}
ABSENT = {
    "docs/agent_plans/S4_E4_PL_Q1B_NONINTRUSION_STABILITY_LOCKING_PLAN.md",
    "docs/reference_cases/e4_pl_q1u_reference_raw.json",
    "docs/reference_cases/e4_pl_q1u_oracle_raw.json",
    "docs/reference_cases/e4_pl_q1u_agreement.json",
    "docs/reference_cases/e4_pl_q1u_output.json",
    "docs/reference_cases/e4_pl_q1u_scientific_test_result.json",
}


def _git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=check, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )


def _paths(value: str) -> set[str]:
    return {line.replace("\\", "/") for line in value.splitlines() if line}


def _commit_paths(commit: str) -> set[str]:
    return _paths(_git("diff-tree", "--no-commit-id", "--name-only", "-r", commit).stdout)


def _raw(path: str) -> bytes:
    return (ROOT / path).read_bytes()


def _canonical(path: str) -> dict[str, object]:
    raw = _raw(path)
    value = json.loads(raw, parse_constant=lambda token: (_ for _ in ()).throw(ValueError(token)))
    assert isinstance(value, dict)
    assert raw == (json.dumps(value, allow_nan=False, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n").encode()
    return value


def test_q1u_closeout_hash_dag_extent_terminal_and_production_boundary() -> None:
    assert _git("branch", "--show-current").stdout.strip() == BRANCH
    assert _git("rev-parse", f"{COMMIT1}^{{tree}}").stdout.strip() == COMMIT1_TREE
    assert _git("rev-parse", f"{COMMIT1}^").stdout.strip() == BASE
    assert _git("show", "-s", "--format=%s", COMMIT1).stdout.strip() == "docs: preregister E4 PL Q1U execution-guard completion"
    assert _commit_paths(COMMIT1) == PLAN12
    assert _git("rev-parse", f"{COMMIT2}^{{tree}}").stdout.strip() == COMMIT2_TREE
    assert _git("rev-parse", f"{COMMIT2}^").stdout.strip() == COMMIT1
    assert _git("show", "-s", "--format=%s", COMMIT2).stdout.strip() == "docs: freeze E4 PL Q1U guard-corrected implementations"
    assert _commit_paths(COMMIT2) == IMPLEMENTATION14
    assert _git("rev-parse", f"{COMMIT3}^{{tree}}").stdout.strip() == COMMIT3_TREE
    assert _git("rev-parse", f"{COMMIT3}^").stdout.strip() == COMMIT2
    assert _git("show", "-s", "--format=%s", COMMIT3).stdout.strip() == "docs: authorize E4 PL Q1U scientific execution"
    assert _commit_paths(COMMIT3) == CONTRACT3

    for path, (size, digest) in BOUND.items():
        raw = _raw(path)
        assert len(raw) == size, path
        assert hashlib.sha256(raw).hexdigest().upper() == digest, path
        assert raw.endswith(b"\n") and b"\r" not in raw and not raw.startswith(b"\xef\xbb\xbf")

    allowed = _canonical("docs/reference_cases/e4_pl_q1u_allowed_extent.json")
    assert allowed["stage_counts"] == {
        "BLOCKED5": 5, "CONTRACT3": 3, "IMPLEMENTATION14": 14,
        "OUTCOME11": 11, "PLAN12": 12,
    }
    assert set(allowed["path_sets"]["PLAN12"]) == PLAN12
    assert set(allowed["path_sets"]["IMPLEMENTATION14"]) == IMPLEMENTATION14
    assert set(allowed["path_sets"]["CONTRACT3"]) == CONTRACT3
    assert set(allowed["path_sets"]["BLOCKED5"]) == BLOCKED5
    assert allowed["blocked_routes"]["post_authority"] == {
        "exact_parent": "ACCEPTED_COMMIT3", "path_count": 6,
        "path_expression": "EXECUTION_AUTHORITY_COPY_UNION_BLOCKED5",
    }

    authority = _canonical("docs/reference_cases/e4_pl_q1u_execution_authority.json")
    assert authority["commit"] == COMMIT3 and authority["tree"] == COMMIT3_TREE
    assert authority["execution_contract_sha256"] == "3E0ABFF5A6097B2789A1CB1D19027ABA131F63E9470AB117560FD87DB117840F"
    assert authority["review_verdicts"] == {
        "contract": "ACCEPT_Q1U_EXECUTION_CONTRACT_NO_P0_P1",
        "implementation": "ACCEPT_Q1U_IMPLEMENTATION_FREEZE_NO_P0_P1",
        "plan": "ACCEPT_Q1U_PREREGISTRATION_NO_P0_P1",
    }
    assert authority["runner_ids"] == ["REFERENCE_RUNNER", "ORACLE_RUNNER", "SCIENTIFIC_TEST_RUNNER"]

    review = _canonical("docs/reference_cases/e4_pl_q1u_scientific_review.json")
    assert set(review) == {"findings", "reviewed_inputs", "reviewer_independence", "schema", "verdict"}
    assert review["verdict"] == "ACCEPT_Q1U_BLOCKED_CLOSEOUT_NO_P0_P1"
    assert review["reviewer_independence"]["mechanics_executed"] is False

    status = _canonical("docs/reference_cases/e4_pl_q1u_status.json")
    assert status["terminal_application"]["first_match"] == "BLOCKED_E4_PL_Q1U_ORACLE_OR_REVIEW"
    assert status["terminal_application"]["precedence"] == 7
    assert status["candidate"] == {
        "id": "candidate_e4_pl_q1u.wg2020_numbered_frame_surface_pl_planar_linear_iso_v1",
        "production_registration": False, "scientific_classification": "NOT_ESTABLISHED",
        "status": "DORMANT_UNQUALIFIED",
    }
    assert status["execution_incident"]["exception_type"] == "ValueError"
    assert status["execution_incident"]["exception_message"] == "equation-7 second diagonal normalization identity failed"
    assert status["execution_incident"]["post_execution_source_changes"] is False
    assert status["component_ledger"]["mechanics"]["oracle_processes_started"] == 0
    assert status["component_ledger"]["mechanics"]["raw_outputs_created"] == 0
    assert status["final"] == {
        "production_terminal": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "q1b_execution_authorized": False,
        "q1b_plan_preparation_authorized": False,
        "terminal": "BLOCKED_E4_PL_Q1U_ORACLE_OR_REVIEW",
    }
    assert set(status["mandatory_absences"]) == ABSENT

    for path in ABSENT:
        assert not (ROOT / path).exists(), path
    for path in ("docs/E4_PL_Q1U_LOCAL_QUALIFICATION.md", "docs/E4_PL_Q1U_COMPLETION.md"):
        text = _raw(path).decode()
        assert "`BLOCKED_E4_PL_Q1U_ORACLE_OR_REVIEW`" in text
        assert "`DORMANT_UNQUALIFIED`" in text
        assert "`NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`" in text

    assert _git("diff", "--cached", "--quiet", check=False).returncode == 0
    assert _git("diff", "--quiet", check=False).returncode == 0
    assert _git("status", "--porcelain=v1", "--untracked-files=no").stdout == ""
    head = _git("rev-parse", "HEAD").stdout.strip()
    untracked = _paths(_git("ls-files", "--others", "--exclude-standard").stdout)
    if head == COMMIT3:
        assert untracked == ROUTE6
    else:
        assert _git("rev-list", "--parents", "-n", "1", head).stdout.split() == [head, COMMIT3]
        assert _git("show", "-s", "--format=%s", head).stdout.strip() == CLOSEOUT_SUBJECT
        assert _commit_paths(head) == ROUTE6
        assert untracked == set()

    assert _paths(_git("diff", "--name-only", BASE, "--").stdout) | untracked == PLAN12 | IMPLEMENTATION14 | CONTRACT3 | ROUTE6
    assert _git("diff", "--name-only", BASE, "--", ".gitattributes", ".github", "pyproject.toml", "setup.cfg", "setup.py", "src").stdout == ""
