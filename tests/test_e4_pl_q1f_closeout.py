"""Static closeout authority for the blocked E4-PL-Q1F plan packet.

This test deliberately uses only the standard library and Git metadata.  It
does not import, locate outside the repository, or execute any Q1F proof draft.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = "61195c18a704438b4b3cf66e6e93d7839723b0fb"
BASE_TREE = "1249c9e9280d626c11c7194c1f2f5b164e5d99b7"
BRANCH = "codex/s4-e4-pl-q1f-domain-coercivity"
CLOSEOUT_SUBJECT = "docs: close E4 PL Q1F authority-review block"
CANDIDATE_ID = "candidate_e4_pl_q1f.wg2020_g1_domain_coercivity_v1"
STUDY_ID = "study_e4_pl_q1f.q1e_domain_coercivity_reduction_v1"

PLAN_BLOCK_PATHS = (
    "docs/E4_PL_Q1F_COMPLETION.md",
    "docs/E4_PL_Q1F_DOMAIN_COERCIVITY.md",
    "docs/agent_plans/S4_E4_PL_Q1F_DOMAIN_COERCIVITY_PLAN.md",
    "docs/reference_cases/e4_pl_q1f_allowed_extent.json",
    "docs/reference_cases/e4_pl_q1f_baseline.json",
    "docs/reference_cases/e4_pl_q1f_plan_review.json",
    "docs/reference_cases/e4_pl_q1f_reduction_contract.json",
    "docs/reference_cases/e4_pl_q1f_scientific_review.json",
    "docs/reference_cases/e4_pl_q1f_status.json",
    "docs/reference_cases/e4_pl_q1f_terminal_table.json",
    "docs/reference_cases/e4_pl_q1f_test_inventory.json",
    "tests/test_e4_pl_q1f_closeout.py",
    "tests/test_e4_pl_q1f_preregistration_authority.py",
)

PLAN_INPUTS = (
    (
        "docs/agent_plans/S4_E4_PL_Q1F_DOMAIN_COERCIVITY_PLAN.md",
        7582,
        "97D0127A31EAA3015537B315D320B47CCAC41CCE76F105B5C27682F37DB7007C",
    ),
    (
        "docs/reference_cases/e4_pl_q1f_allowed_extent.json",
        5767,
        "FD88E83DDBB2023562CB744C1FE4B0A0A817F312C236186942D91D00DD7ACAF4",
    ),
    (
        "docs/reference_cases/e4_pl_q1f_baseline.json",
        4911,
        "405FDCBA4549C498E9EF5770402CBC1EC7B47A06B796724C6784FAA5039D910C",
    ),
    (
        "docs/reference_cases/e4_pl_q1f_reduction_contract.json",
        18219,
        "F1B240053A5A4DC8E4E53B7352995EDFBE934DEB398BEC64DD06351AD99617A7",
    ),
    (
        "docs/reference_cases/e4_pl_q1f_terminal_table.json",
        1856,
        "BCA057F31BC239FFC316B12FC7B071E1C7D26F4075BCA8E73DC7482FD5609D4B",
    ),
    (
        "docs/reference_cases/e4_pl_q1f_test_inventory.json",
        2206,
        "8BE3B0E08CF5E1B1B18D29A6D8E22B2FAA93A635309A61C66880353D704B8103",
    ),
    (
        "tests/test_e4_pl_q1f_preregistration_authority.py",
        16000,
        "91A1ACC8011356608173D660F818A2B6270348FBEDD8B35710C943848A1344FF",
    ),
)

BOUND_CLOSEOUT_INPUTS = (
    (
        "docs/reference_cases/e4_pl_q1f_plan_review.json",
        2273,
        "DD3721F9E6C3CEC20E0C57B815467B695F37139DE444F9A9623790E511BB9891",
    ),
    (
        "docs/reference_cases/e4_pl_q1f_status.json",
        5072,
        "884C34D0F168221A1E656C4F42715FC1A55E444CCE73334429CCE17A00FE8F8E",
    ),
    (
        "docs/E4_PL_Q1F_DOMAIN_COERCIVITY.md",
        4159,
        "E91B2B2353448F9A41AB732683D8FCFDA4F565557888BBEC966090726B7864E0",
    ),
    (
        "docs/reference_cases/e4_pl_q1f_scientific_review.json",
        891,
        "139F5A41882A9B303E231A118D4E0C9377FA933E3677F67F790DAE1402EDA2DD",
    ),
    (
        "docs/E4_PL_Q1F_COMPLETION.md",
        1989,
        "1399274A1B401087DCCAC6245E98842673AAAEAED2BFCE71491928C1BB666ABA",
    ),
)

EXTERNAL_DRAFTS = (
    (
        "docs/reference_cases/e4_pl_q1f_bounded_runner.py",
        9390,
        "F225DE8E8F9354007CF3AE733B8871D56789CB20AD7754489A715FC273674A6B",
    ),
    (
        "docs/reference_cases/e4_pl_q1f_common.py",
        19330,
        "1F1A751A1BFC3FA7EC40A254443EA3FF4BB6F654192E0A2E1D03B170B870017A",
    ),
    (
        "docs/reference_cases/e4_pl_q1f_domain_checker.py",
        3270,
        "DC451EBC0B91E58F6E3A43C8D376F166ED954B66275DD614C1F375BFD561A53A",
    ),
    (
        "docs/reference_cases/e4_pl_q1f_domain_producer.py",
        3711,
        "4836A4F58F51A4EBD3AAE4DA6B15EE13AA0455A916517CE0BD83AC0714196703",
    ),
    (
        "docs/reference_cases/e4_pl_q1f_reduction_verifier.py",
        9508,
        "7CF74C57C0B9EFC2B608FC275C3D166106CBE6C5631233E1FD63553217112420",
    ),
    (
        "tests/test_e4_pl_q1f_interval_proof.py",
        1552,
        "438211EFD61AE68129784A01CD3F156129FA060DC053A13A3AA49B9F966B4C8E",
    ),
    (
        "tests/test_e4_pl_q1f_reduction.py",
        3171,
        "640BF4908055154DCD6FFE9171377A2A5B93AFE0BE9BD7B2205E98A5026337F7",
    ),
    (
        "tests/test_e4_pl_q1f_runner_bounds.py",
        4042,
        "B9BD8AC3482AB12F7AEC48194A940CF811EDF58A1186822B82C9525792A5704F",
    ),
)

IMPLEMENTATION10_PATHS = (
    "docs/reference_cases/e4_pl_q1f_common.py",
    "docs/reference_cases/e4_pl_q1f_reduction_verifier.py",
    "docs/reference_cases/e4_pl_q1f_domain_producer.py",
    "docs/reference_cases/e4_pl_q1f_domain_checker.py",
    "docs/reference_cases/e4_pl_q1f_bounded_runner.py",
    "docs/reference_cases/e4_pl_q1f_implementation_manifest.json",
    "docs/reference_cases/e4_pl_q1f_implementation_review.json",
    "tests/test_e4_pl_q1f_reduction.py",
    "tests/test_e4_pl_q1f_interval_proof.py",
    "tests/test_e4_pl_q1f_runner_bounds.py",
)

CONTRACT3_PATHS = (
    "docs/reference_cases/e4_pl_q1f_execution_contract.json",
    "docs/reference_cases/e4_pl_q1f_contract_review.json",
    "tests/test_e4_pl_q1f_contract.py",
)

FORBIDDEN_SCIENTIFIC_PATHS = (
    "docs/reference_cases/e4_pl_q1f_domain_aggregate.json",
    "docs/reference_cases/e4_pl_q1f_execution_authority.json",
    "docs/reference_cases/e4_pl_q1f_scientific_test_result.json",
    "docs/reference_cases/e4_pl_q1f_domain_proof.json",
)


def _git(*arguments: str) -> str:
    completed = subprocess.run(
        ("git", *arguments),
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert completed.returncode == 0, (
        f"git {' '.join(arguments)} failed: {completed.stderr.strip()}"
    )
    return completed.stdout.strip()


def _lines(value: str) -> tuple[str, ...]:
    return tuple(line for line in value.splitlines() if line)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def _assert_file_identity(path: str, byte_count: int, sha256: str) -> bytes:
    data = (REPOSITORY_ROOT / path).read_bytes()
    assert len(data) == byte_count, path
    assert _sha256(data) == sha256, path
    return data


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise AssertionError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_nonfinite(token: str) -> Any:
    raise AssertionError(f"non-finite JSON token: {token}")


def _canonical_json(path: str) -> dict[str, Any]:
    raw = (REPOSITORY_ROOT / path).read_bytes()
    document = json.loads(
        raw.decode("utf-8"),
        object_pairs_hook=_reject_duplicate_keys,
        parse_constant=_reject_nonfinite,
    )
    assert isinstance(document, dict), path
    canonical = (
        json.dumps(document, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
        + "\n"
    ).encode("utf-8")
    assert raw == canonical, path
    return document


def _row(path: str, byte_count: int, sha256: str) -> dict[str, Any]:
    return {"bytes": byte_count, "path": path, "sha256": sha256}


def test_q1f_static_plan_block_closeout() -> None:
    # The source packet and every closeout authority are fixed by byte identity.
    for path, byte_count, sha256 in PLAN_INPUTS + BOUND_CLOSEOUT_INPUTS:
        _assert_file_identity(path, byte_count, sha256)

    allowed = _canonical_json(
        "docs/reference_cases/e4_pl_q1f_allowed_extent.json"
    )
    plan_review = _canonical_json(
        "docs/reference_cases/e4_pl_q1f_plan_review.json"
    )
    status = _canonical_json("docs/reference_cases/e4_pl_q1f_status.json")
    terminal_table = _canonical_json(
        "docs/reference_cases/e4_pl_q1f_terminal_table.json"
    )
    scientific_review = _canonical_json(
        "docs/reference_cases/e4_pl_q1f_scientific_review.json"
    )

    expected_plan_rows = [_row(*identity) for identity in PLAN_INPUTS]
    assert plan_review["reviewed_inputs"] == expected_plan_rows
    assert status["plan_inputs"] == expected_plan_rows

    # The sole correction was consumed and rejected for the explicit translation
    # congruence P1.  No mechanics are needed to preserve that authority result.
    assert set(plan_review) == {
        "findings",
        "reviewed_inputs",
        "reviewer_independence",
        "schema",
        "verdict",
    }
    assert plan_review["schema"] == "anysolver.s4.e4-pl-q1f-plan-review-v1"
    assert plan_review["verdict"] == "REJECT_Q1F_COERCIVITY_REDUCTION_P1"
    assert plan_review["reviewer_independence"] == {
        "mechanics_executed": False,
        "reviewer_role": "INDEPENDENT_Q1F_REDUCTION_REVIEWER",
        "same_agent_as_packet_author": False,
    }
    assert len(plan_review["findings"]) == 1
    finding = plan_review["findings"][0]
    assert finding == {
        "correction_cycle": {"allowed": 1, "used": 1},
        "id": "P1_TRANSLATION_RIGID_MATRIX_CONGRUENCE",
        "locations": [
            "docs/reference_cases/e4_pl_q1f_reduction_contract.json:gauge_congruence.r",
            "docs/reference_cases/e4_pl_q1f_reduction_contract.json:gauge_congruence.translation",
            "docs/reference_cases/e4_pl_q1f_reduction_contract.json:local_reduction.rigid_matrix.columns",
        ],
        "mechanics_executed": False,
        "priority": "P1",
        "required_identity": "FREEZE_THE_NONSINGULAR_6X6_RIGID_COLUMN_BASIS_CHANGE_OR_REQUIRE_RANGE_R_raw_EQUALS_RANGE_T_Q_S_scale_R_gauge_AND_USE_THE_RANGE_IN_THE_QUOTIENT",
        "summary": "The frozen rigid columns contain physical x and y, so translating the element adds translation-column combinations to the three rotation columns. Therefore R_raw=T_Q*S_scale*R_gauge and the claim that translation does not enter R are false as matrix identities; only the rigid range is translation invariant.",
        "terminal": "BLOCKED_E4_PL_Q1F_REDUCTION_IDENTITY",
    }

    # First-match precedence 1 is the closeout result; the reduction P1 remains
    # recorded as the underlying precedence-2 finding, never as a proof result.
    assert terminal_table["schema"] == (
        "anysolver.s4.e4-pl-q1f-terminal-table-v2"
    )
    assert terminal_table["candidate_id"] == CANDIDATE_ID
    assert terminal_table["study_id"] == STUDY_ID
    assert terminal_table["first_match_wins"] is True
    terminals = terminal_table["terminals"]
    assert [item["precedence"] for item in terminals] == [1, 2, 3, 4, 5, 6]
    assert [item["id"] for item in terminals] == [
        "BLOCKED_E4_PL_Q1F_AUTHORITY_OR_REVIEW",
        "BLOCKED_E4_PL_Q1F_REDUCTION_IDENTITY",
        "BLOCKED_E4_PL_Q1F_PROOF_OR_NONDETERMINISM",
        "NO_GO_E4_PL_Q1F_DOMAIN_COERCIVITY",
        "UNCLASSIFIED_E4_PL_Q1F_INTERVAL_COVERAGE",
        "PROVISIONAL_GO_E4_PL_Q1F_Q1B_INTEGRATION_PLAN",
    ]
    assert status["schema"] == "anysolver.s4.e4-pl-q1f-status-v1"
    assert status["candidate_id"] == CANDIDATE_ID
    assert status["study_id"] == STUDY_ID
    assert status["terminal"] == "BLOCKED_E4_PL_Q1F_AUTHORITY_OR_REVIEW"
    assert status["terminal_basis"] == (
        "FIRST_MATCH_PRECEDENCE_1_REQUIRED_PLAN_REVIEW_REJECTED_AND_"
        "PREMATURE_IMPLEMENTATION_DRAFT_PATHS_CREATED_BEFORE_ACCEPTED_PLAN_AUTHORITY"
    )
    assert status["underlying_reduction_finding"] == (
        "BLOCKED_E4_PL_Q1F_REDUCTION_IDENTITY"
    )
    assert status["correction_budget"] == {"maximum": 1, "used": 1}
    assert status["reduction_identity"] == {
        "asserted_identity": "R_raw=T_Q*S_scale*R_gauge",
        "correct_invariant": "range(R_raw)=range(T_Q*S_scale*R_gauge)",
        "finding_id": "P1_TRANSLATION_RIGID_MATRIX_CONGRUENCE",
        "reason": "TRANSLATION_ADDS_TRANSLATION_COLUMN_COMBINATIONS_TO_THE_THREE_COORDINATE_DEPENDENT_ROTATION_COLUMNS",
        "required_missing_identity": "R_raw=T_Q*S_scale*R_gauge*B_translation_WITH_NONSINGULAR_6X6_B_translation",
        "truth_value": False,
    }

    # The eight drafts are identified only through the status authority.  Every
    # intended path is absent here; the test never opens an external draft.
    assert status["external_draft_preservation"] == {
        "drafts": [
            {
                "bytes": byte_count,
                "intended_stage_path": path,
                "sha256": sha256,
            }
            for path, byte_count, sha256 in EXTERNAL_DRAFTS
        ],
        "label": "EXTERNAL_SIBLING_Q1F_IMPLEMENTATION_DRAFTS",
        "moved_intact_outside_all_git_authority": True,
        "preservation_policy": "NOT_AUTHORITY_DO_NOT_PROMOTE_OR_EXECUTE",
    }
    evidence = status["evidence_disposition"]
    assert evidence == {
        "contract_created": False,
        "current_q1f_worktree_implementation_paths_absent": True,
        "implementation_stage_promoted": False,
        "premature_unpromoted_drafts_created": True,
        "q1b_integration": "UNAUTHORIZED",
        "registered_proof_executed": False,
        "scientific_mechanics_executed": False,
        "scientific_outcome_generated": False,
        "static_draft_tests": {
            "executed": True,
            "result": "2_PASSED_IN_2_42_SECONDS",
        },
    }

    # PLAN_BLOCK is the one legal extent, both in the extent authority and in
    # the status record for the prospective closeout commit.
    plan_block = allowed["blocked_routes"]["PLAN_BLOCK"]
    assert plan_block == {
        "expected_parent": BASE_COMMIT,
        "path_count": 13,
        "paths": list(PLAN_BLOCK_PATHS),
    }
    assert status["base_authority"] == {
        "commit": BASE_COMMIT,
        "tree": BASE_TREE,
    }
    assert status["prospective_blocked_commit"] == {
        "parent": BASE_COMMIT,
        "path_count": 13,
        "paths": list(PLAN_BLOCK_PATHS),
        "subject": CLOSEOUT_SUBJECT,
    }
    assert allowed["plan_correction"] == {"allowed": 1, "used": 1}
    assert allowed["production_forbidden_paths"] == [
        ".gitattributes",
        ".github",
        "pyproject.toml",
        "src",
    ]
    assert tuple(allowed["stage_paths"]["IMPLEMENTATION10"]) == (
        IMPLEMENTATION10_PATHS
    )
    assert tuple(allowed["stage_paths"]["CONTRACT3"]) == CONTRACT3_PATHS

    assert scientific_review == {
        "findings": [],
        "reviewed_inputs": [
            _row(
                "docs/E4_PL_Q1F_DOMAIN_COERCIVITY.md",
                4159,
                "E91B2B2353448F9A41AB732683D8FCFDA4F565557888BBEC966090726B7864E0",
            ),
            _row(*PLAN_INPUTS[0]),
            _row(
                "docs/reference_cases/e4_pl_q1f_plan_review.json",
                2273,
                "DD3721F9E6C3CEC20E0C57B815467B695F37139DE444F9A9623790E511BB9891",
            ),
            _row(
                "docs/reference_cases/e4_pl_q1f_status.json",
                5072,
                "884C34D0F168221A1E656C4F42715FC1A55E444CCE73334429CCE17A00FE8F8E",
            ),
        ],
        "reviewer_independence": {
            "authored_review_only": True,
            "mechanics_executed": False,
            "reviewed_input_authorship": False,
            "role": "INDEPENDENT_BLOCKED_CLOSEOUT_REVIEWER",
        },
        "schema": "anysolver.s4.e4-pl-q1f-blocked-closeout-review-v1",
        "verdict": "ACCEPT_Q1F_BLOCKED_CLOSEOUT_NO_P0_P1",
    }

    report = (REPOSITORY_ROOT / "docs/E4_PL_Q1F_DOMAIN_COERCIVITY.md").read_text(
        encoding="utf-8"
    )
    completion = (REPOSITORY_ROOT / "docs/E4_PL_Q1F_COMPLETION.md").read_text(
        encoding="utf-8"
    )
    for required in (
        "BLOCKED_E4_PL_Q1F_AUTHORITY_OR_REVIEW",
        "P1_TRANSLATION_RIGID_MATRIX_CONGRUENCE",
        "range(R_raw) = range(T_Q S_scale R_gauge)",
        "B[T3,R1]=c_y",
        "EXTERNAL_SIBLING_Q1F_IMPLEMENTATION_DRAFTS",
        "NOT_AUTHORITY_DO_NOT_PROMOTE_OR_EXECUTE",
        CLOSEOUT_SUBJECT,
        BASE_COMMIT,
        "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
    ):
        assert required in report
    for required in (
        "BLOCKED_E4_PL_Q1F_AUTHORITY_OR_REVIEW",
        "DD3721F9E6C3CEC20E0C57B815467B695F37139DE444F9A9623790E511BB9891",
        "EXTERNAL_SIBLING_Q1F_IMPLEMENTATION_DRAFTS",
        "NOT_AUTHORITY_DO_NOT_PROMOTE_OR_EXECUTE",
        CLOSEOUT_SUBJECT,
        BASE_COMMIT,
        "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
    ):
        assert required in completion

    forbidden = set(IMPLEMENTATION10_PATHS + CONTRACT3_PATHS)
    forbidden.update(FORBIDDEN_SCIENTIFIC_PATHS)
    for path in forbidden:
        assert not (REPOSITORY_ROOT / path).exists(), path

    # No additional Q1F path can silently introduce an implementation, contract,
    # proof, aggregate, or outcome.  The exact delta also excludes Q1B changes.
    visible_paths = set(
        _lines(_git("ls-files", "--cached", "--others", "--exclude-standard"))
    )
    visible_q1f_paths = {
        path for path in visible_paths if "q1f" in path.casefold()
    }
    assert visible_q1f_paths == set(PLAN_BLOCK_PATHS)
    assert all("q1b" not in path.casefold() for path in PLAN_BLOCK_PATHS)

    assert _git("branch", "--show-current") == BRANCH
    assert _git("rev-parse", f"{BASE_COMMIT}^{{tree}}") == BASE_TREE
    head = _git("rev-parse", "HEAD")
    if head == BASE_COMMIT:
        # Precommit profile: tracked tree and index are clean; the entire legal
        # packet, including this node, is the exact untracked 13-path extent.
        assert not _lines(_git("diff", "--name-only"))
        assert not _lines(_git("diff", "--cached", "--name-only"))
        untracked = set(
            _lines(_git("ls-files", "--others", "--exclude-standard"))
        )
        assert untracked == set(PLAN_BLOCK_PATHS)
        delta_paths = untracked
    else:
        # Postcommit profile: the direct child is the frozen closeout commit and
        # there is no remaining index or worktree delta.
        assert _git("rev-parse", "HEAD^") == BASE_COMMIT
        assert _git("log", "-1", "--format=%s") == CLOSEOUT_SUBJECT
        assert not _lines(_git("status", "--porcelain=v1", "--untracked-files=all"))
        diff_tree = set(
            _lines(
                _git(
                    "diff-tree",
                    "--no-commit-id",
                    "--name-only",
                    "-r",
                    "HEAD",
                )
            )
        )
        assert diff_tree == set(PLAN_BLOCK_PATHS)
        delta_paths = set(
            _lines(_git("diff", "--name-only", BASE_COMMIT, "HEAD", "--"))
        )
        assert delta_paths == set(PLAN_BLOCK_PATHS)

    assert len(delta_paths) == 13
    assert not any(
        path == ".gitattributes"
        or path == "pyproject.toml"
        or path == ".github"
        or path.startswith(".github/")
        or path == "src"
        or path.startswith("src/")
        for path in delta_paths
    )
    assert status["production"] == "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"
    assert terminal_table["production"] == (
        "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"
    )
