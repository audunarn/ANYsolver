from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = "46231c56d4c7d24000421fc3ba0f4800239e64bd"
BASE_TREE = "c04f7f784d25790da105ae321636a7cae288d53e"
Q1R_PREREG_COMMIT = "97edc4265a7ce5ca9763f66875d1336e419bcef4"
COMMIT1_SUBJECT = "docs: preregister E4 PL Q1S implementation completion"
BRANCH = "codex/s4-e4-pl-q1s-implementation-completion"

PLAN_PATHS = {
    "docs/agent_plans/S4_E4_PL_Q1S_IMPLEMENTATION_COMPLETION_PLAN.md",
    "docs/reference_cases/e4_pl_q1s_plan_review.json",
    "docs/reference_cases/e4_pl_q1s_baseline.json",
    "docs/reference_cases/e4_pl_q1s_inheritance_manifest.json",
    "docs/reference_cases/e4_pl_q1s_draft_preservation_manifest.json",
    "docs/reference_cases/e4_pl_q1s_allowed_extent.json",
    "docs/reference_cases/e4_pl_q1s_implementation_completeness.json",
    "docs/reference_cases/e4_pl_q1s_authority_contract.json",
    "docs/reference_cases/e4_pl_q1s_terminal_table.json",
    "docs/reference_cases/e4_pl_q1s_test_inventory.json",
    "tests/test_e4_pl_q1s_preregistration_authority.py",
}

BOUND_PLAN_INPUTS = {
    "docs/agent_plans/S4_E4_PL_Q1S_IMPLEMENTATION_COMPLETION_PLAN.md": (
        19627,
        "3FE4D21CA8A92EDF4A5D136F4BE6A6DA29A1DF139EF54AE204B208C3AE6285B2",
    ),
    "docs/reference_cases/e4_pl_q1s_baseline.json": (
        4554,
        "DE0AB7F20A8588AE7E72214F31763729F65D97682DA435294BF5FE52B45127E6",
    ),
    "docs/reference_cases/e4_pl_q1s_inheritance_manifest.json": (
        8382,
        "DBE7ACE7498AE971D891F5182BAAD8DEA2021C33A27F78D827C84FEC438B860E",
    ),
    "docs/reference_cases/e4_pl_q1s_draft_preservation_manifest.json": (
        4001,
        "8309F0E8FE82C8AFAB14E69F275C90662D2E9E8EB47115304B43F07B4678A410",
    ),
    "docs/reference_cases/e4_pl_q1s_allowed_extent.json": (
        3663,
        "8E14AE1E46A097F16C1CC0986F4AB578C4D385FD53EA8E5E9610AF249420214C",
    ),
    "docs/reference_cases/e4_pl_q1s_implementation_completeness.json": (
        15735,
        "C567F51F0EF97E5D2D33961A96D765E390D9E97B5E6BF4B659CD8B6980E67469",
    ),
    "docs/reference_cases/e4_pl_q1s_authority_contract.json": (
        14890,
        "0CE5590AF73F5B7A9ED3D2A6B4D1381CB0625A52940FD978E253C34C47F790C0",
    ),
    "docs/reference_cases/e4_pl_q1s_terminal_table.json": (
        4296,
        "A046AD7786502B204EDB83AD4235EC96C634166C6D423CC1AB291B8AA8A76D8E",
    ),
    "docs/reference_cases/e4_pl_q1s_test_inventory.json": (
        4085,
        "E95C190A1C2D6859FCDE2EB73961CE3C755D75736D1AA25F441104A04147A527",
    ),
}

EXPECTED_STAGES = {
    "PLAN": PLAN_PATHS,
    "IMPLEMENTATION": {
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
    },
    "CONTRACT": {
        "docs/reference_cases/e4_pl_q1s_execution_contract.json",
        "docs/reference_cases/e4_pl_q1s_contract_review.json",
        "tests/test_e4_pl_q1s_contract.py",
    },
    "OUTCOME": {
        "docs/reference_cases/e4_pl_q1s_reference_raw.json",
        "docs/reference_cases/e4_pl_q1s_oracle_raw.json",
        "docs/reference_cases/e4_pl_q1s_agreement.json",
        "docs/reference_cases/e4_pl_q1s_output.json",
        "docs/reference_cases/e4_pl_q1s_status.json",
        "docs/reference_cases/e4_pl_q1s_execution_authority.json",
        "docs/reference_cases/e4_pl_q1s_scientific_test_result.json",
        "docs/E4_PL_Q1S_LOCAL_QUALIFICATION.md",
        "docs/reference_cases/e4_pl_q1s_scientific_review.json",
        "docs/E4_PL_Q1S_COMPLETION.md",
        "tests/test_e4_pl_q1s_closeout.py",
    },
}

TERMINALS = [
    "BLOCKED_E4_PL_Q1S_BASELINE_MISMATCH",
    "BLOCKED_E4_PL_Q1S_INHERITANCE_MISMATCH",
    "BLOCKED_E4_PL_Q1S_PLAN_AUTHORITY",
    "BLOCKED_E4_PL_Q1S_FRAME_IDENTITY",
    "NO_GO_E4_PL_Q1S_FRAME_IDENTITY",
    "BLOCKED_E4_PL_Q1S_IMPLEMENTATION_IDENTITY",
    "BLOCKED_E4_PL_Q1S_CONTRACT_OR_NONDETERMINISM",
    "BLOCKED_E4_PL_Q1S_ORACLE_OR_REVIEW",
    "NO_GO_E4_PL_Q1S_LOCAL_ALGEBRA",
    "NO_GO_E4_PL_Q1S_PATCH_OR_COVARIANCE",
    "UNCLASSIFIED_E4_PL_Q1S_LOCAL_PLANAR_IDENTITY",
    "PROVISIONAL_GO_E4_PL_Q1S_Q1B_PLAN",
]

SCIENTIFIC_NODES = [
    "tests/test_e4_pl_q1s_frame_and_fields.py::test_q1s_all_56_numbered_frames_and_field_work",
    "tests/test_e4_pl_q1s_local_algebra.py::test_q1s_actual_38_field_condensation_rank_and_rigid_modes",
    "tests/test_e4_pl_q1s_recovery.py::test_q1s_all_224_station_recovery_and_numerical_separation",
    "tests/test_e4_pl_q1s_global_supports.py::test_q1s_global_transform_load_support_solution_and_reactions",
    "tests/test_e4_pl_q1s_terminal_and_agreement.py::test_q1s_evidence_terminal_and_cross_implementation_contract",
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


def _raw(path: str) -> bytes:
    return (ROOT / path).read_bytes()


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def _loads_strict(raw: bytes) -> object:
    def pairs(items: list[tuple[str, object]]) -> dict[str, object]:
        out: dict[str, object] = {}
        for key, value in items:
            if key in out:
                raise ValueError(f"duplicate key: {key}")
            out[key] = value
        return out

    def nonfinite(token: str) -> object:
        raise ValueError(f"nonfinite token: {token}")

    return json.loads(raw, object_pairs_hook=pairs, parse_constant=nonfinite)


def _canonical(path: str) -> dict[str, object]:
    raw = _raw(path)
    value = _loads_strict(raw)
    assert isinstance(value, dict)
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


def test_q1s_baseline_inheritance_and_plan_authority_are_exact() -> None:
    assert _git("branch", "--show-current").stdout.strip() == BRANCH
    assert _git("rev-parse", f"{BASE_COMMIT}^{{tree}}").stdout.strip() == BASE_TREE
    assert _git("show", "-s", "--format=%s", BASE_COMMIT).stdout.strip() == (
        "docs: close E4 PL Q1R implementation-identity block"
    )

    for path, (size, digest) in BOUND_PLAN_INPUTS.items():
        raw = _raw(path)
        assert len(raw) == size, path
        assert _sha(raw) == digest, path
        _assert_transport(path)

    baseline = _canonical("docs/reference_cases/e4_pl_q1s_baseline.json")
    assert baseline["q1r_blocked_closeout"]["commit"] == BASE_COMMIT
    assert baseline["q1r_blocked_closeout"]["tree"] == BASE_TREE
    assert baseline["q1r_blocked_closeout"]["terminal"] == (
        "BLOCKED_E4_PL_Q1R_IMPLEMENTATION_IDENTITY"
    )
    assert baseline["accepted_e4_detached"]["result"] == "20_PASSED_IN_7_42_SECONDS"
    assert baseline["accepted_e4_detached"]["node_count"] == 20

    inherited = _canonical("docs/reference_cases/e4_pl_q1s_inheritance_manifest.json")
    assert inherited["counts"] == {
        "inherited_e4_core_inputs": 2,
        "inherited_q1r_inputs": 16,
        "q1r_closeout_inputs": 5,
        "total_bound_inputs": 23,
    }
    assert inherited["q1r_preregistration"]["commit"] == Q1R_PREREG_COMMIT
    for key in (
        "inherited_q1r_inputs",
        "q1r_closeout_inputs",
        "inherited_e4_core_inputs",
    ):
        rows = inherited[key]
        assert isinstance(rows, list)
        for row in rows:
            path = row["path"]
            raw = _raw(path)
            assert len(raw) == row["bytes"]
            assert _sha(raw) == row["sha256"]
            assert _git(
                "rev-parse", f"{row['source_commit']}:{path}"
            ).stdout.strip() == row["git_blob"]

    status = _canonical("docs/reference_cases/e4_pl_q1r_status.json")
    draft_manifest = _canonical(
        "docs/reference_cases/e4_pl_q1s_draft_preservation_manifest.json"
    )
    draft_rows = {
        row["source_path"]: (row["bytes"], row["sha256"])
        for row in draft_manifest["drafts"]
    }
    status_rows = {
        row["path"]: (row["bytes"], row["sha256"])
        for row in status["implementation_drafts"]["files"]
    }
    assert draft_rows == status_rows
    assert status["implementation_drafts"]["classification_authority"] is False

    review = _canonical("docs/reference_cases/e4_pl_q1s_plan_review.json")
    assert set(review) == {
        "findings",
        "reviewed_inputs",
        "reviewer_independence",
        "schema",
        "verdict",
    }
    assert review["verdict"] == "ACCEPT_Q1S_PREREGISTRATION_NO_P0_P1"
    expected_reviewed = [
        {"bytes": size, "path": path, "sha256": digest}
        for path, (size, digest) in BOUND_PLAN_INPUTS.items()
    ]
    test_raw = _raw("tests/test_e4_pl_q1s_preregistration_authority.py")
    expected_reviewed.append(
        {
            "bytes": len(test_raw),
            "path": "tests/test_e4_pl_q1s_preregistration_authority.py",
            "sha256": _sha(test_raw),
        }
    )
    assert review["reviewed_inputs"] == sorted(
        expected_reviewed, key=lambda row: row["path"]
    )
    assert review["reviewer_independence"] == {
        "authored_review_only": True,
        "mechanics_executed": False,
        "reviewed_input_authorship": False,
        "role": "INDEPENDENT_PLAN_ONLY_REVIEWER",
    }
    assert review["findings"] == []


def test_q1s_plan_packet_schemas_extent_and_stage_barriers() -> None:
    with pytest.raises(ValueError):
        _loads_strict(b'{"a":1,"a":2}\n')
    with pytest.raises(ValueError):
        _loads_strict(b'{"a":NaN}\n')

    allowed = _canonical("docs/reference_cases/e4_pl_q1s_allowed_extent.json")
    actual_stages = {stage: set() for stage in EXPECTED_STAGES}
    for row in allowed["paths"]:
        actual_stages[row["stage"]].add(row["path"])
    assert actual_stages == EXPECTED_STAGES
    assert allowed["stage_counts"] == {
        "CONTRACT": 3,
        "IMPLEMENTATION": 10,
        "OUTCOME": 11,
        "PLAN": 11,
    }
    assert allowed["path_count"] == 35
    assert allowed["sole_existing_file_modifications"] == []
    assert allowed["q1b_paths_permitted"] is False

    completeness = _canonical(
        "docs/reference_cases/e4_pl_q1s_implementation_completeness.json"
    )
    required = completeness["required_rows"]
    assert len(required) == 25
    assert len({row["id"] for row in required}) == 25
    assert completeness["coverage"]["numbered_case_count"] == 56
    assert completeness["coverage"]["gauss_station_count"] == 224
    assert completeness["exact_arithmetic"]["precision_bits"] == [256, 512, 1024]
    assert (
        completeness["required_rows"][7]["forbidden"][0]
        == "GAUSS_L2_PROJECTION_OF_FULL_RATIONAL_CURL"
    )

    authority = _canonical("docs/reference_cases/e4_pl_q1s_authority_contract.json")
    assert authority["stage_extents"] == {
        stage: sorted(paths, key=lambda path: authority["stage_extents"][stage].index(path))
        for stage, paths in EXPECTED_STAGES.items()
    }
    assert authority["runtime"]["python_implementation"] == "CPython"
    assert authority["runtime"]["python_version"] == "3.13.9"
    assert authority["runtime"]["python_executable_path_authority"] == "DIAGNOSTIC_ONLY"
    assert authority["correction_limits"] == {
        "contract_before_commit3": {"max": 1, "used": 0},
        "implementation_before_commit2": {"max": 1, "used": 0},
        "outcome_or_science_after_first_registered_process": {"max": 0, "used": 0},
        "plan_before_commit1": {"max": 1, "used": 1},
        "review_required_after_each_permitted_correction": True,
    }
    blocked = authority["blocked_closeout_protocol"]
    assert len(blocked["path_sets"]["BLOCKED5"]) == 5
    assert len(blocked["path_sets"]["POST_AUTHORITY_BLOCKED6"]) == 6
    assert [row["path_count"] for row in blocked["alternative_commits"]] == [
        16,
        15,
        8,
        6,
        11,
    ]
    assert set(blocked["terminal_route_map"]) == set(TERMINALS)
    assert blocked["blocked_artifact_rules"]["blocked_review_exact_verdict"] == (
        "ACCEPT_Q1S_BLOCKED_CLOSEOUT_NO_P0_P1"
    )

    terminals = _canonical("docs/reference_cases/e4_pl_q1s_terminal_table.json")
    assert [row["precedence"] for row in terminals["terminals"]] == list(range(1, 13))
    assert [row["id"] for row in terminals["terminals"]] == TERMINALS
    assert terminals["global_effect"]["production"] == (
        "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"
    )

    inventory = _canonical("docs/reference_cases/e4_pl_q1s_test_inventory.json")
    assert inventory["preregistration_inventory"]["count"] == 3
    assert inventory["scientific_inventory"]["node_ids"] == SCIENTIFIC_NODES
    assert inventory["scientific_inventory"]["count"] == 5
    assert inventory["inventories_must_not_be_combined"] is True

    tracked = {
        line.replace("\\", "/")
        for line in _git("diff", "--name-only", BASE_COMMIT, "--").stdout.splitlines()
        if line
    }
    untracked = {
        line.replace("\\", "/")
        for line in _git("ls-files", "--others", "--exclude-standard").stdout.splitlines()
        if line
    }
    assert tracked | untracked == PLAN_PATHS
    assert tracked <= PLAN_PATHS

    head = _git("rev-parse", "HEAD").stdout.strip()
    if head == BASE_COMMIT:
        assert untracked == PLAN_PATHS
    else:
        assert _git("rev-parse", "HEAD^").stdout.strip() == BASE_COMMIT
        assert _git("show", "-s", "--format=%s", "HEAD").stdout.strip() == COMMIT1_SUBJECT
        commit_paths = {
            line.replace("\\", "/")
            for line in _git(
                "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"
            ).stdout.splitlines()
            if line
        }
        assert commit_paths == PLAN_PATHS
        assert tracked == PLAN_PATHS
        assert untracked == set()


def test_q1s_production_boundary_and_mandatory_absences() -> None:
    baseline = _canonical("docs/reference_cases/e4_pl_q1s_baseline.json")
    for path in baseline["mandatory_absences"]:
        assert not (ROOT / path).exists(), path

    assert _git("diff", "--cached", "--quiet", check=False).returncode == 0
    assert _git("diff", "--quiet", check=False).returncode == 0
    assert (
        _git(
            "diff",
            "--name-only",
            BASE_COMMIT,
            "--",
            ".gitattributes",
            ".github",
            "pyproject.toml",
            "setup.cfg",
            "setup.py",
            "src",
            "tests/production",
        ).stdout.splitlines()
        == []
    )
    assert not (
        ROOT / "docs/agent_plans/S4_E4_PL_Q1B_NONINTRUSION_STABILITY_LOCKING_PLAN.md"
    ).exists()
