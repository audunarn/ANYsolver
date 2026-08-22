from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BRANCH = "codex/s4-e4-pl-q1v-local-completion"
BASE = "7d4ac30b4d50a1ee62edefbe5fb0198b47276360"
COMMIT1 = "7a33044aee429557d770b914130df47105d6bec9"
COMMIT1_TREE = "7ae5c3278aed1e5937d90c308db6f570e424b1f7"
COMMIT2 = "c51f4705a1f0f547ec2265a7846894dba098307d"
COMMIT2_TREE = "b627b32312178e67ee746362fe9233ca97931543"
COMMIT3 = "8cc1824a4fa83b11c025a4aa46ac31608072b424"
COMMIT3_TREE = "45b7a1754aaf91020ca01abc86f83313ee292c89"
CLOSEOUT_SUBJECT = "docs: close E4 PL Q1V oracle-or-review block"

PLAN14 = {
    "docs/agent_plans/S4_E4_PL_Q1V_LOCAL_COMPLETION_PLAN.md",
    "docs/reference_cases/e4_pl_q1v_plan_review.json",
    "docs/reference_cases/e4_pl_q1v_baseline.json",
    "docs/reference_cases/e4_pl_q1v_inheritance_manifest.json",
    "docs/reference_cases/e4_pl_q1v_allowed_extent.json",
    "docs/reference_cases/e4_pl_q1v_q1u_backend_incident.json",
    "docs/reference_cases/e4_pl_q1v_exact_backend_contract.json",
    "docs/reference_cases/e4_pl_q1v_commissioning_contract.json",
    "docs/reference_cases/e4_pl_q1v_mechanics_equivalence_contract.json",
    "docs/reference_cases/e4_pl_q1v_certificate_schema.json",
    "docs/reference_cases/e4_pl_q1v_authority_contract.json",
    "docs/reference_cases/e4_pl_q1v_terminal_table.json",
    "docs/reference_cases/e4_pl_q1v_test_inventory.json",
    "tests/test_e4_pl_q1v_preregistration_authority.py",
}
IMPLEMENTATION20 = {
    "docs/reference_cases/e4_pl_q1v_authority_guard.py",
    "docs/reference_cases/e4_pl_q1v_reference.py",
    "docs/reference_cases/e4_pl_q1v_oracle.py",
    "docs/reference_cases/e4_pl_q1v_scientific_test_runner.py",
    "docs/reference_cases/e4_pl_q1v_commissioning_runner.py",
    "docs/reference_cases/e4_pl_q1v_implementation_manifest.json",
    "docs/reference_cases/e4_pl_q1v_mechanics_equivalence.json",
    "docs/reference_cases/e4_pl_q1v_backend_conformance.json",
    "docs/reference_cases/e4_pl_q1v_commissioning_reference.json",
    "docs/reference_cases/e4_pl_q1v_commissioning_oracle.json",
    "docs/reference_cases/e4_pl_q1v_commissioning_agreement.json",
    "docs/reference_cases/e4_pl_q1v_implementation_review.json",
    "tests/test_e4_pl_q1v_exact_backend.py",
    "tests/test_e4_pl_q1v_commissioning.py",
    "tests/test_e4_pl_q1v_authority_guard.py",
    "tests/test_e4_pl_q1v_frame_and_fields.py",
    "tests/test_e4_pl_q1v_local_algebra.py",
    "tests/test_e4_pl_q1v_recovery.py",
    "tests/test_e4_pl_q1v_global_supports.py",
    "tests/test_e4_pl_q1v_terminal_and_agreement.py",
}
CONTRACT3 = {
    "docs/reference_cases/e4_pl_q1v_execution_contract.json",
    "docs/reference_cases/e4_pl_q1v_contract_review.json",
    "tests/test_e4_pl_q1v_contract.py",
}
BLOCKED5 = {
    "docs/reference_cases/e4_pl_q1v_status.json",
    "docs/E4_PL_Q1V_LOCAL_QUALIFICATION.md",
    "docs/reference_cases/e4_pl_q1v_scientific_review.json",
    "docs/E4_PL_Q1V_COMPLETION.md",
    "tests/test_e4_pl_q1v_closeout.py",
}
ROUTE6 = BLOCKED5 | {"docs/reference_cases/e4_pl_q1v_execution_authority.json"}
BOUND = {
    "docs/reference_cases/e4_pl_q1v_execution_authority.json": (2189, "B656921FBDF760464E3649B311E301FC3E8017C0CD1079300557451026F1DDBE"),
    "docs/reference_cases/e4_pl_q1v_status.json": (5539, "D9DE342FBE2A2B241919E2913D16CE0B3A944B8DAE7A4E6565EEDAAF74C67AEB"),
    "docs/E4_PL_Q1V_LOCAL_QUALIFICATION.md": (2443, "BA509741DDF0F926BB30AC5CFDF0ED72E8B32A0C7646C8626444B4F80565FED2"),
    "docs/reference_cases/e4_pl_q1v_scientific_review.json": (745, "A4C5F1097A0D8B2FC918307C95E2613E3CEF766FF778EF97212063F82AB74932"),
    "docs/E4_PL_Q1V_COMPLETION.md": (2622, "5AEFFEBBF160D6A7C9B2A3C2ED92F736EFAC78CC7DE3C82488BCA835910752FF"),
}
ABSENT = {
    "docs/agent_plans/S4_E4_PL_Q1B_NONINTRUSION_STABILITY_LOCKING_PLAN.md",
    "docs/reference_cases/e4_pl_q1v_reference_raw.json",
    "docs/reference_cases/e4_pl_q1v_oracle_raw.json",
    "docs/reference_cases/e4_pl_q1v_agreement.json",
    "docs/reference_cases/e4_pl_q1v_output.json",
    "docs/reference_cases/e4_pl_q1v_scientific_test_result.json",
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
    expected = (json.dumps(value, allow_nan=False, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n").encode()
    assert raw == expected
    return value


def test_q1v_closeout_hash_dag_extent_terminal_and_production_boundary() -> None:
    assert _git("branch", "--show-current").stdout.strip() == BRANCH
    assert _git("rev-parse", f"{COMMIT1}^{{tree}}").stdout.strip() == COMMIT1_TREE
    assert _git("rev-parse", f"{COMMIT1}^").stdout.strip() == BASE
    assert _git("show", "-s", "--format=%s", COMMIT1).stdout.strip() == "docs: preregister E4 PL Q1V local completion"
    assert _commit_paths(COMMIT1) == PLAN14
    assert _git("rev-parse", f"{COMMIT2}^{{tree}}").stdout.strip() == COMMIT2_TREE
    assert _git("rev-parse", f"{COMMIT2}^").stdout.strip() == COMMIT1
    assert _git("show", "-s", "--format=%s", COMMIT2).stdout.strip() == "docs: freeze E4 PL Q1V commissioned exact implementations"
    assert _commit_paths(COMMIT2) == IMPLEMENTATION20
    assert _git("rev-parse", f"{COMMIT3}^{{tree}}").stdout.strip() == COMMIT3_TREE
    assert _git("rev-parse", f"{COMMIT3}^").stdout.strip() == COMMIT2
    assert _git("show", "-s", "--format=%s", COMMIT3).stdout.strip() == "docs: authorize E4 PL Q1V scientific execution"
    assert _commit_paths(COMMIT3) == CONTRACT3

    for path, (size, digest) in BOUND.items():
        raw = _raw(path)
        assert len(raw) == size, path
        assert hashlib.sha256(raw).hexdigest().upper() == digest, path
        assert raw.endswith(b"\n") and b"\r" not in raw and not raw.startswith(b"\xef\xbb\xbf")

    allowed = _canonical("docs/reference_cases/e4_pl_q1v_allowed_extent.json")
    assert allowed["stage_counts"] == {
        "BLOCKED5": 5, "CONTRACT3": 3, "IMPLEMENTATION20": 20,
        "OUTCOME11": 11, "PLAN14": 14,
    }
    assert set(allowed["path_sets"]["PLAN14"]) == PLAN14
    assert set(allowed["path_sets"]["IMPLEMENTATION20"]) == IMPLEMENTATION20
    assert set(allowed["path_sets"]["CONTRACT3"]) == CONTRACT3
    assert set(allowed["path_sets"]["BLOCKED5"]) == BLOCKED5
    assert allowed["blocked_routes"]["post_authority_or_reauthorization"] == {
        "exact_parent": "LATEST_ACCEPTED_AUTHORIZATION", "path_count": 6,
        "path_expression": "EXECUTION_AUTHORITY_COPY_UNION_BLOCKED5",
    }

    authority = _canonical("docs/reference_cases/e4_pl_q1v_execution_authority.json")
    assert authority["commit"] == COMMIT3 and authority["tree"] == COMMIT3_TREE
    assert authority["authorization_cycle"] == 0 and authority["correction_cycles_used"] == 0
    assert authority["execution_contract_sha256"] == "405234439AA06288F005BA543B37719CA127C0C70C6DD432B429A0F4211D2543"
    assert authority["review_verdicts"] == {
        "contract": "ACCEPT_Q1V_EXECUTION_CONTRACT_NO_P0_P1",
        "implementation": "ACCEPT_Q1V_IMPLEMENTATION_FREEZE_NO_P0_P1",
        "plan": "ACCEPT_Q1V_PREREGISTRATION_NO_P0_P1",
    }

    review = _canonical("docs/reference_cases/e4_pl_q1v_scientific_review.json")
    assert set(review) == {"findings", "reviewed_inputs", "reviewer_independence", "schema", "verdict"}
    assert review["verdict"] == "ACCEPT_Q1V_BLOCKED_CLOSEOUT_NO_P0_P1"
    assert review["reviewer_independence"]["mechanics_executed"] is False

    status = _canonical("docs/reference_cases/e4_pl_q1v_status.json")
    assert status["terminal_application"]["first_match"] == "BLOCKED_E4_PL_Q1V_ORACLE_OR_REVIEW"
    assert status["terminal_application"]["precedence"] == 8
    assert status["candidate"] == {
        "id": "candidate_e4_pl_q1v.wg2020_numbered_frame_surface_pl_planar_linear_iso_v1",
        "production_registration": False, "scientific_classification": "NOT_ESTABLISHED",
        "status": "DORMANT_UNQUALIFIED",
    }
    assert status["external_evidence"]["reference_attempts"] == {
        "attempts": 2, "byte_identical": True, "each_bytes": 2688589,
        "each_sha256": "4B570FC89FEA9DE0D9DE1A2E97B8B7B245BEBAEFCDD3B78CD08B4C8803A3F04E",
        "promoted": False,
    }
    assert status["execution_incident"]["hard_freeze_event_occurred"] is True
    assert status["execution_incident"]["post_execution_source_changes"] is False
    assert status["component_ledger"]["mechanics"]["oracle_processes_started"] == 2
    assert status["component_ledger"]["mechanics"]["oracle_raw_outputs_created"] == 0
    assert status["final"] == {
        "production_terminal": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "q1b_execution_authorized": False,
        "q1b_plan_preparation_authorized": False,
        "terminal": "BLOCKED_E4_PL_Q1V_ORACLE_OR_REVIEW",
    }
    assert set(status["mandatory_absences"]) == ABSENT

    for path in ABSENT:
        assert not (ROOT / path).exists(), path
    for path in ("docs/E4_PL_Q1V_LOCAL_QUALIFICATION.md", "docs/E4_PL_Q1V_COMPLETION.md"):
        text = _raw(path).decode()
        assert "`BLOCKED_E4_PL_Q1V_ORACLE_OR_REVIEW`" in text
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

    assert _paths(_git("diff", "--name-only", BASE, "--").stdout) | untracked == PLAN14 | IMPLEMENTATION20 | CONTRACT3 | ROUTE6
    assert _git("diff", "--name-only", BASE, "--", ".gitattributes", ".github", "pyproject.toml", "setup.cfg", "setup.py", "src").stdout == ""
