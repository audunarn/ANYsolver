from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BRANCH = "codex/s4-e4-pl-q1t-exact-oracle-completion"

BASE_COMMIT = "914a9a633c585d45a419d97f92b4faf7fa1e4486"
BASE_TREE = "569c0b15c9e5d50835fa5fe16414d5d1864d0106"
BASE_PARENT = "00d6a66c34712c8f3fd1e38113c83d0a03b2de43"
BASE_SUBJECT = "docs: close E4 PL Q1S implementation-identity block"

COMMIT1 = "658619184d354401f55fc7a6640a4770d900ded7"
COMMIT1_TREE = "c4b9d5ef80779ba26912bbb2d53e5d547a47c629"
COMMIT1_SUBJECT = "docs: preregister E4 PL Q1T exact-oracle completion"

COMMIT2 = "083044167f9826e9868851c2709017112bc7553d"
COMMIT2_TREE = "3b52b601e509b1348145cffdb40cb1d478b9227f"
COMMIT2_SUBJECT = "docs: freeze E4 PL Q1T exact reference and oracle"
CLOSEOUT_SUBJECT = "docs: close E4 PL Q1T contract-authority block"

PLAN14 = {
    "docs/agent_plans/S4_E4_PL_Q1T_EXACT_ORACLE_COMPLETION_PLAN.md",
    "docs/reference_cases/e4_pl_q1t_allowed_extent.json",
    "docs/reference_cases/e4_pl_q1t_authority_contract.json",
    "docs/reference_cases/e4_pl_q1t_baseline.json",
    "docs/reference_cases/e4_pl_q1t_certificate_schema.json",
    "docs/reference_cases/e4_pl_q1t_environment.json",
    "docs/reference_cases/e4_pl_q1t_environment_builder.py",
    "docs/reference_cases/e4_pl_q1t_exact_backend_contract.json",
    "docs/reference_cases/e4_pl_q1t_inheritance_manifest.json",
    "docs/reference_cases/e4_pl_q1t_plan_review.json",
    "docs/reference_cases/e4_pl_q1t_rejected_evidence_manifest.json",
    "docs/reference_cases/e4_pl_q1t_terminal_table.json",
    "docs/reference_cases/e4_pl_q1t_test_inventory.json",
    "tests/test_e4_pl_q1t_preregistration_authority.py",
}

IMPLEMENTATION11 = {
    "docs/reference_cases/e4_pl_q1t_reference.py",
    "docs/reference_cases/e4_pl_q1t_oracle.py",
    "docs/reference_cases/e4_pl_q1t_scientific_test_runner.py",
    "docs/reference_cases/e4_pl_q1t_implementation_manifest.json",
    "docs/reference_cases/e4_pl_q1t_implementation_review.json",
    "tests/test_e4_pl_q1t_exact_backend.py",
    "tests/test_e4_pl_q1t_frame_and_fields.py",
    "tests/test_e4_pl_q1t_local_algebra.py",
    "tests/test_e4_pl_q1t_recovery.py",
    "tests/test_e4_pl_q1t_global_supports.py",
    "tests/test_e4_pl_q1t_terminal_and_agreement.py",
}

CONTRACT3 = {
    "docs/reference_cases/e4_pl_q1t_execution_contract.json",
    "docs/reference_cases/e4_pl_q1t_contract_review.json",
    "tests/test_e4_pl_q1t_contract.py",
}

BLOCKED5 = {
    "docs/reference_cases/e4_pl_q1t_status.json",
    "docs/E4_PL_Q1T_LOCAL_QUALIFICATION.md",
    "docs/reference_cases/e4_pl_q1t_scientific_review.json",
    "docs/E4_PL_Q1T_COMPLETION.md",
    "tests/test_e4_pl_q1t_closeout.py",
}

ROUTE8 = CONTRACT3 | BLOCKED5

BOUND_ROUTE = {
    "docs/reference_cases/e4_pl_q1t_execution_contract.json": (
        26735,
        "473A36EBCA88B553F068DD19CAC0AB112632BEAEB96ECE77672CAEB03F57E062",
    ),
    "docs/reference_cases/e4_pl_q1t_contract_review.json": (
        2411,
        "5D5359EC96158455A3CF86C0C137400FEB714573910F49AD064CCBD0EB15356A",
    ),
    "tests/test_e4_pl_q1t_contract.py": (
        6300,
        "3BBC0B0A47AF511A5686D0321035B1F372AA4BE5BB5724E043A12BCC9C07EFD6",
    ),
    "docs/reference_cases/e4_pl_q1t_status.json": (
        6178,
        "0A718447DDB1AAC9399A5E395E902329D420372024483F612CF67391B2EAE088",
    ),
    "docs/E4_PL_Q1T_LOCAL_QUALIFICATION.md": (
        5017,
        "121648333F45B6499067FAC5F610AA0F504764D7A9C42CEDDDF2337705ED20FA",
    ),
    "docs/reference_cases/e4_pl_q1t_scientific_review.json": (
        3150,
        "D552248598B10891D7AB3EBFFED9167285354FA4912A77BC6958081B73B53021",
    ),
    "docs/E4_PL_Q1T_COMPLETION.md": (
        3121,
        "3B296B3F3B31625F0BC8D0E8BB15BBA39C7023619E25896FC3A729E3EE627BB3",
    ),
}

MANDATORY_ABSENCES = {
    "docs/agent_plans/S4_E4_PL_Q1B_NONINTRUSION_STABILITY_LOCKING_PLAN.md",
    "docs/reference_cases/e4_pl_q1t_execution_authority.json",
    "docs/reference_cases/e4_pl_q1t_reference_raw.json",
    "docs/reference_cases/e4_pl_q1t_oracle_raw.json",
    "docs/reference_cases/e4_pl_q1t_agreement.json",
    "docs/reference_cases/e4_pl_q1t_output.json",
    "docs/reference_cases/e4_pl_q1t_scientific_test_result.json",
}

P1_IDS = [
    "P1_SCIENTIFIC_RUNNER_ENVIRONMENT_KEY_MISMATCH",
    "P1_SCIENTIFIC_RUNNER_AGREEMENT_ENUM_MISMATCH",
    "P1_REVIEW_CONTENT_GUARDS_INCOMPLETE",
    "P1_CONTRACT_HASH_DAG_TEST_INCOMPLETE",
]


def _git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _paths(output: str) -> set[str]:
    return {
        line.replace("\\", "/")
        for line in output.splitlines()
        if line
    }


def _raw(path: str) -> bytes:
    return (ROOT / path).read_bytes()


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def _loads_strict(raw: bytes) -> object:
    def pairs(items: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"duplicate key: {key}")
            result[key] = value
        return result

    def nonfinite(token: str) -> object:
        raise ValueError(f"nonfinite JSON token: {token}")

    return json.loads(raw, object_pairs_hook=pairs, parse_constant=nonfinite)


def _canonical(path: str) -> dict[str, object]:
    raw = _raw(path)
    value = _loads_strict(raw)
    assert isinstance(value, dict), path
    expected = (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")
    assert raw == expected, path
    return value


def _assert_transport(path: str) -> None:
    raw = _raw(path)
    assert not raw.startswith(b"\xef\xbb\xbf"), path
    assert b"\r" not in raw, path
    assert raw.endswith(b"\n"), path


def _commit_paths(commit: str) -> set[str]:
    return _paths(
        _git(
            "diff-tree",
            "--no-commit-id",
            "--name-only",
            "-r",
            commit,
        ).stdout
    )


def test_q1t_closeout_hash_dag_extent_terminal_and_production_boundary() -> None:
    assert _git("branch", "--show-current").stdout.strip() == BRANCH

    assert _git("rev-parse", f"{BASE_COMMIT}^{{tree}}").stdout.strip() == BASE_TREE
    assert _git("rev-parse", f"{BASE_COMMIT}^").stdout.strip() == BASE_PARENT
    assert _git("show", "-s", "--format=%s", BASE_COMMIT).stdout.strip() == (
        BASE_SUBJECT
    )

    assert _git("rev-parse", f"{COMMIT1}^{{tree}}").stdout.strip() == COMMIT1_TREE
    assert _git("rev-parse", f"{COMMIT1}^").stdout.strip() == BASE_COMMIT
    assert _git("show", "-s", "--format=%s", COMMIT1).stdout.strip() == (
        COMMIT1_SUBJECT
    )
    assert _commit_paths(COMMIT1) == PLAN14

    assert _git("rev-parse", f"{COMMIT2}^{{tree}}").stdout.strip() == COMMIT2_TREE
    assert _git("rev-parse", f"{COMMIT2}^").stdout.strip() == COMMIT1
    assert _git("show", "-s", "--format=%s", COMMIT2).stdout.strip() == (
        COMMIT2_SUBJECT
    )
    assert _commit_paths(COMMIT2) == IMPLEMENTATION11

    for path, (size, digest) in BOUND_ROUTE.items():
        raw = _raw(path)
        assert len(raw) == size, path
        assert _sha256(raw) == digest, path
        _assert_transport(path)

    for path in (
        "docs/reference_cases/e4_pl_q1t_allowed_extent.json",
        "docs/reference_cases/e4_pl_q1t_authority_contract.json",
        "docs/reference_cases/e4_pl_q1t_plan_review.json",
        "docs/reference_cases/e4_pl_q1t_implementation_manifest.json",
        "docs/reference_cases/e4_pl_q1t_implementation_review.json",
        "docs/reference_cases/e4_pl_q1t_terminal_table.json",
        "docs/reference_cases/e4_pl_q1t_test_inventory.json",
    ):
        _assert_transport(path)

    allowed = _canonical("docs/reference_cases/e4_pl_q1t_allowed_extent.json")
    assert allowed["path_count"] == 39
    assert allowed["stage_counts"] == {
        "CONTRACT": 3,
        "IMPLEMENTATION": 11,
        "OUTCOME": 11,
        "PLAN": 14,
    }
    assert set(allowed["path_sets"]["PLAN"]) == PLAN14
    assert set(allowed["path_sets"]["IMPLEMENTATION"]) == IMPLEMENTATION11
    assert set(allowed["path_sets"]["CONTRACT"]) == CONTRACT3
    assert set(allowed["path_sets"]["BLOCKED5"]) == BLOCKED5
    assert allowed["blocked_routes"]["contract"] == {
        "exact_parent": "ACCEPTED_COMMIT2",
        "path_count": 8,
        "path_expression": "CONTRACT3_UNION_BLOCKED5",
    }
    assert allowed["production_changes_permitted"] is False
    assert allowed["q1b_paths_permitted"] is False

    authority = _canonical("docs/reference_cases/e4_pl_q1t_authority_contract.json")
    assert set(authority["stage_extents"]["PLAN"]) == PLAN14
    assert set(authority["stage_extents"]["IMPLEMENTATION"]) == IMPLEMENTATION11
    assert set(authority["stage_extents"]["CONTRACT"]) == CONTRACT3
    assert set(authority["blocked_closeout_protocol"]["blocked5"]) == BLOCKED5
    assert authority["blocked_closeout_protocol"]["routes"]["contract"] == {
        "exact_parent": "ACCEPTED_COMMIT2",
        "path_count": 8,
        "path_expression": "CONTRACT3_UNION_BLOCKED5",
    }
    assert authority["blocked_closeout_protocol"]["exact_review_verdict"] == (
        "ACCEPT_Q1T_BLOCKED_CLOSEOUT_NO_P0_P1"
    )

    plan_review = _canonical("docs/reference_cases/e4_pl_q1t_plan_review.json")
    implementation_review = _canonical(
        "docs/reference_cases/e4_pl_q1t_implementation_review.json"
    )
    for review in (plan_review, implementation_review):
        assert set(review) == {
            "findings",
            "reviewed_inputs",
            "reviewer_independence",
            "schema",
            "verdict",
        }
    assert plan_review["verdict"] == "ACCEPT_Q1T_PREREGISTRATION_NO_P0_P1"
    assert implementation_review["verdict"] == (
        "ACCEPT_Q1T_IMPLEMENTATION_FREEZE_NO_P0_P1"
    )
    assert implementation_review["findings"] == []
    assert implementation_review["reviewer_independence"]["mechanics_executed"] is False

    contract_review = _canonical(
        "docs/reference_cases/e4_pl_q1t_contract_review.json"
    )
    blocked_review = _canonical(
        "docs/reference_cases/e4_pl_q1t_scientific_review.json"
    )
    for review in (contract_review, blocked_review):
        assert set(review) == {
            "findings",
            "reviewed_inputs",
            "reviewer_independence",
            "schema",
            "verdict",
        }
        assert review["reviewer_independence"]["mechanics_executed"] is False
    assert contract_review["schema"] == (
        "anysolver.s4.e4-pl-q1t-contract-review-v1"
    )
    assert contract_review["verdict"] == "REJECT_Q1T_EXECUTION_CONTRACT_P1"
    assert [row["id"] for row in contract_review["findings"]] == P1_IDS
    assert all(row["priority"] == "P1" for row in contract_review["findings"])
    assert all(row["mechanics_executed"] is False for row in contract_review["findings"])

    assert blocked_review["schema"] == (
        "anysolver.s4.e4-pl-q1t-blocked-closeout-review-v1"
    )
    assert blocked_review["verdict"] == "ACCEPT_Q1T_BLOCKED_CLOSEOUT_NO_P0_P1"
    assert blocked_review["findings"][0]["rejected_gate"] == {
        "finding_ids": P1_IDS,
        "mechanics_executed": False,
        "review_verdict": "REJECT_Q1T_EXECUTION_CONTRACT_P1",
        "stage": "CONTRACT3",
    }
    expected_reviewed = [
        {"bytes": BOUND_ROUTE[path][0], "path": path, "sha256": BOUND_ROUTE[path][1]}
        for path in (
            "docs/E4_PL_Q1T_LOCAL_QUALIFICATION.md",
            "docs/reference_cases/e4_pl_q1t_contract_review.json",
            "docs/reference_cases/e4_pl_q1t_execution_contract.json",
            "docs/reference_cases/e4_pl_q1t_status.json",
            "tests/test_e4_pl_q1t_contract.py",
        )
    ]
    assert blocked_review["reviewed_inputs"] == expected_reviewed

    status = _canonical("docs/reference_cases/e4_pl_q1t_status.json")
    assert status["schema"] == "anysolver.s4.e4-pl-q1t-blocked-status-v1"
    assert status["authority"]["base"] == {
        "branch_source": "codex/s4-e4-pl-q1s-implementation-completion",
        "commit": BASE_COMMIT,
        "parent": BASE_PARENT,
        "subject": BASE_SUBJECT,
        "tree": BASE_TREE,
    }
    assert status["authority"]["commit1"]["commit"] == COMMIT1
    assert status["authority"]["commit1"]["tree"] == COMMIT1_TREE
    assert status["authority"]["commit1"]["path_count"] == 14
    assert set(status["authority"]["commit1"]["paths"]) == PLAN14
    assert status["authority"]["commit2"]["commit"] == COMMIT2
    assert status["authority"]["commit2"]["tree"] == COMMIT2_TREE
    assert status["authority"]["commit2"]["path_count"] == 11
    assert set(status["authority"]["commit2"]["paths"]) == IMPLEMENTATION11
    assert status["contract_evidence"]["review"]["verdict"] == (
        "REJECT_Q1T_EXECUTION_CONTRACT_P1"
    )
    assert [row["id"] for row in status["contract_evidence"]["findings"]] == P1_IDS
    assert status["candidate"] == {
        "id": "candidate_e4_pl_q1t.wg2020_numbered_frame_surface_pl_planar_linear_iso_v1",
        "production_registration": False,
        "scientific_classification": "NOT_ESTABLISHED",
        "status": "DORMANT_UNQUALIFIED",
    }
    assert status["terminal_application"]["first_match"] == (
        "BLOCKED_E4_PL_Q1T_CONTRACT_OR_NONDETERMINISM"
    )
    assert status["terminal_application"]["precedence"] == 6
    assert status["final"] == {
        "production_terminal": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "q1b_execution_authorized": False,
        "q1b_plan_preparation_authorized": False,
        "terminal": "BLOCKED_E4_PL_Q1T_CONTRACT_OR_NONDETERMINISM",
    }
    assert set(status["mandatory_absences"]) == MANDATORY_ABSENCES
    assert status["evidence_chain"]["accepted_commit3"] is False
    assert status["evidence_chain"]["registered_mechanics_run"] is False
    assert status["component_ledger"]["mechanics"] == {
        "registered_execution": "NOT_RUN",
        "scientific_classification": "NOT_ESTABLISHED",
        "scientific_tests": "NOT_RUN",
        "status": "NOT_RUN",
    }
    assert status["production_boundary"] == {
        "api_change": False,
        "dependency_change": False,
        "dispatch_change": False,
        "gitattributes_change": False,
        "legacy_default": "ShellElement",
        "package_change": False,
        "production_source_change": False,
        "recovery_change": False,
        "serialization_change": False,
        "workflow_change": False,
    }

    manifest = _canonical("docs/reference_cases/e4_pl_q1t_implementation_manifest.json")
    assert manifest["registered_mechanics_executed"] is False
    assert manifest["static_verification"]["scientific_nodes_executed"] == 0
    assert manifest["stage"]["exact_path_count"] == 11

    terminals = _canonical("docs/reference_cases/e4_pl_q1t_terminal_table.json")
    assert [row["precedence"] for row in terminals["terminals"]] == list(range(1, 12))
    assert terminals["terminals"][5]["id"] == (
        "BLOCKED_E4_PL_Q1T_CONTRACT_OR_NONDETERMINISM"
    )
    assert terminals["global_effect"] == {
        "legacy_default": "ShellElement",
        "production": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "q1b_execution": "UNAUTHORIZED_FOR_EVERY_Q1T_TERMINAL",
        "q1b_plan_preparation": "AUTHORIZED_ONLY_BY_PRECEDENCE_11",
    }

    inventory = _canonical("docs/reference_cases/e4_pl_q1t_test_inventory.json")
    assert inventory["closeout_inventory"] == {
        "count": 1,
        "execution": "STATIC_ONLY_AFTER_COMMIT4_NO_MECHANICS_RERUN",
        "node_ids": [
            "tests/test_e4_pl_q1t_closeout.py::test_q1t_closeout_hash_dag_extent_terminal_and_production_boundary"
        ],
    }

    report = _raw("docs/E4_PL_Q1T_LOCAL_QUALIFICATION.md").decode("utf-8")
    completion = _raw("docs/E4_PL_Q1T_COMPLETION.md").decode("utf-8")
    for text in (report, completion):
        assert "`BLOCKED_E4_PL_Q1T_CONTRACT_OR_NONDETERMINISM`" in text
        assert "`DORMANT_UNQUALIFIED`" in text
        assert "`NO_GO_PRODUCTION_RESTRICTION_UNCHANGED`" in text
        assert "`ShellElement` remains the default" in text
    assert "`REJECT_Q1T_EXECUTION_CONTRACT_P1`" in completion
    assert "`ACCEPT_Q1T_BLOCKED_CLOSEOUT_NO_P0_P1`" in completion

    for path in MANDATORY_ABSENCES:
        assert not (ROOT / path).exists(), path

    assert _git("diff", "--cached", "--quiet", check=False).returncode == 0
    assert _git("diff", "--quiet", check=False).returncode == 0
    assert _git("status", "--porcelain=v1", "--untracked-files=no").stdout == ""

    tracked = _paths(_git("diff", "--name-only", COMMIT2, "--").stdout)
    untracked = _paths(
        _git("ls-files", "--others", "--exclude-standard").stdout
    )
    head = _git("rev-parse", "HEAD").stdout.strip()
    if head == COMMIT2:
        assert tracked == set()
        assert untracked == ROUTE8
    else:
        parents = _git("rev-list", "--parents", "-n", "1", "HEAD").stdout.split()
        assert parents == [head, COMMIT2]
        assert _git("show", "-s", "--format=%s", "HEAD").stdout.strip() == (
            CLOSEOUT_SUBJECT
        )
        assert _commit_paths("HEAD") == ROUTE8
        assert tracked == ROUTE8
        assert untracked == set()
        closeout_blob = _git(
            "rev-parse", "HEAD:tests/test_e4_pl_q1t_closeout.py"
        ).stdout.strip()
        assert _git(
            "hash-object", "tests/test_e4_pl_q1t_closeout.py"
        ).stdout.strip() == closeout_blob

    full_tracked = _paths(_git("diff", "--name-only", BASE_COMMIT, "--").stdout)
    assert full_tracked | untracked == PLAN14 | IMPLEMENTATION11 | ROUTE8
    assert (
        _git(
            "diff",
            "--name-only",
            BASE_COMMIT,
            "--",
            ".gitattributes",
            ".github",
            "MANIFEST.in",
            "pyproject.toml",
            "setup.cfg",
            "setup.py",
            "src",
            "tests/production",
        ).stdout.splitlines()
        == []
    )
