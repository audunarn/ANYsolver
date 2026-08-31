from __future__ import annotations

import hashlib
import json
import math
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
AUTHORITY = ROOT / "docs/reference_cases/e4_pl_s3_v2_stage4a_authority.json"


def _reject_constant(value: str) -> None:
    raise ValueError(value)


def _reject_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
    made: dict[str, object] = {}
    for key, value in pairs:
        if key in made:
            raise ValueError(f"duplicate key: {key}")
        made[key] = value
    return made


def _canonical(value: object) -> bytes:
    def visit(item: object) -> None:
        if isinstance(item, float):
            assert math.isfinite(item)
        elif isinstance(item, list):
            for member in item:
                visit(member)
        elif isinstance(item, dict):
            for key, member in item.items():
                assert isinstance(key, str)
                visit(member)

    visit(value)
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


@pytest.fixture(scope="module")
def authority() -> dict[str, object]:
    raw = AUTHORITY.read_bytes()
    value = json.loads(
        raw.decode("utf-8"),
        object_pairs_hook=_reject_duplicates,
        parse_constant=_reject_constant,
    )
    assert raw == _canonical(value)
    return value


def test_stage4a_authority_binds_exact_parent_and_protocol(authority) -> None:
    assert authority["schema"] == "anysolver.e4-pl-s3-v2-stage4a-authority-v3"
    assert authority["parent"] == {
        "commit": "171df65eef875508effe16018875ffccf6b0f4f6",
        "subject": "docs: freeze S3 V2A Stage 4A execution",
        "tree": "e6fb4c15b70124c47615497e746ce9f5a6ed36f1",
    }
    assert authority["scope_base"] == {
        "commit": "d1f6d3d264882cc70a34b6a764476f5ec6baeb3b",
        "subject": "test: make S3 V2 evidence hashes checkout portable",
        "tree": "5fb2bfa183018e7365cb9fa5f864912fab003b97",
    }
    phase = authority["formal_phase"]
    assert phase["classifying_record_count"] == 81
    assert phase["v1_diagnostic_record_count"] == 72
    assert authority["formal_protocol"]["support"] == {
        "all_edge_translations": ["ux", "uy", "uz"],
        "constant_x_edge_rotation": "theta_x",
        "constant_y_edge_rotation": "theta_y",
        "identity": "HARD_NAVIER_TRANSLATIONS_PLUS_EDGE_ZERO_SHELL_ROTATIONS_V3",
    }
    assert authority["formal_protocol"]["reference_identity"] == (
        "INDEPENDENT_NAVIER_REISSNER_MINDLIN_UNIFORM_PRESSURE_SHELL_EMBEDDED_V3"
    )


def test_stage4a_advisory_margins_cannot_become_scientific_no_go(authority) -> None:
    advisory = authority["advisory_policy"]
    assert advisory["classification"] == "NONCLASSIFYING_INDEPENDENT_REVIEW_TRIGGER"
    assert advisory["successor_expansion_authorized_on_trigger"] is False
    assert authority["terminals"]["formal_no_go"] == (
        "NO_GO_E4_PL_S3_V2A_MIXED_FLEXURAL_CONVERGENCE"
    )


def test_stage4a_authority_preserves_defaults_and_mechanics_boundaries(authority) -> None:
    assert authority["production_boundary"] == {
        "default_s3_formulation": "legacy-s3",
        "default_s3_unchanged": True,
        "q4_default": "e4-pl",
        "q4_mechanics_unchanged": True,
        "v1_fallback_forbidden": True,
    }
    extent = authority["allowed_extent"]
    assert extent["q4_or_v1_mechanics_change_authorized"] is False
    assert extent["v2_matrix_or_equation_change_authorized"] is False
    assert "src/anysolver/e4_pl_element.py" not in extent["implementation_paths"]
    assert "src/anysolver/e4_pl_s3_element.py" not in extent["implementation_paths"]
    assert "src/anysolver/boundary.py" not in extent["implementation_paths"]


def test_stage4a_authority_correction_preserves_original_and_closes_paths(authority) -> None:
    correction = authority["correction"]
    assert correction["classification"] == (
        "INDEPENDENT_REVIEW_CORRECTION_AND_HISTORICAL_TEST_SCOPE"
    )
    assert correction["mechanics_or_protocol_changed"] is True
    assert correction["production_mechanics_changed"] is False
    assert correction["scientific_protocol_corrected"] is True
    assert correction["history"][:2] == [
        {
            "bytes": 3726,
            "commit": "0f0979db7548cf0e715451d052fa837da61cbdf6",
            "path": "docs/reference_cases/e4_pl_s3_v2_stage4a_authority.json",
            "reason": "INCOMPLETE_DOWNSTREAM_PATH_ENUMERATION",
            "sha256": "061BD82022D7FB6D6403057DA81389C8E59282FCD48E57CC3B2B824693AFE6B3",
            "subject": "docs: authorize S3 V2A flat mixed funnel",
            "tree": "873962fcfafbd71ff1be1240f47afa04e2acad41",
        },
        {
            "bytes": 4912,
            "commit": "9f332946ea91cc1ef45ae6776c72b7aa569f92df",
            "path": "docs/reference_cases/e4_pl_s3_v2_stage4a_authority.json",
            "reason": "PREDECESSOR_BINDING_TESTS_USED_MUTABLE_WORKING_BYTES",
            "sha256": "77688BCEB41A878109360CAF299DD415C45B102361E24A138A360C15F4187C60",
            "subject": "docs: correct S3 V2A Stage 4A authority extent",
            "tree": "732e87fdf2319405659f0685ae71d333a4645269",
        },
    ]
    extent = authority["allowed_extent"]
    assert {
        "tests/test_e4_pl_s3_v2_candidate_binding.py",
        "tests/test_e4_pl_s3_v2_flat_candidate_review.py",
    } <= set(extent["implementation_paths"])
    assert correction["review_incident"] == {
        "candidate_commit": "0f93779feded35846ce7a093d27a8a98f5c0fc81",
        "findings": [
            "BLOCKED_PROCESS_RETURNED_ZERO",
            "CANDIDATE_ARCHIVE_NOT_EXECUTED",
            "CANONICAL_PUBLICATION_NOT_ATOMIC",
            "CHECKER_PROOF_DIGESTS_NOT_JOINED_TO_PRODUCER",
            "GIT_ENGINE_AND_EXTERNAL_ATTRIBUTES_NOT_BOUND",
            "IMMUTABLE_LEDGER_SNAPSHOT_NOT_RECOMPUTED",
            "MINDLIN_SHELL_ROTATION_EMBEDDING_AND_SUPPORT_MISMATCH",
            "MIXED_Q4_NORMAL_AUTHORITY_MISSING",
            "PREDECESSOR_BINDING_TESTS_USED_MUTABLE_WORKING_BYTES",
        ],
        "p0_count": 0,
        "p1_count": 9,
        "process_review": "REJECT_PENDING_CORRECTION",
        "scientific_review": "REJECT_PENDING_CORRECTION",
    }
    assert authority["review_correction_requirements"] == {
        "atomic_canonical_publication": True,
        "blocked_process_exit_nonzero": True,
        "checker_producer_digest_join": True,
        "exact_candidate_archive_execution": True,
        "git_launcher_and_engine_binding": True,
        "immutable_pre_run_ledger_snapshot": True,
        "mixed_q4_reference_normal": ["0", "0", "1"],
        "shell_embedding": {"beta_x": "theta_y", "beta_y": "-theta_x"},
    }
    assert set(extent["freeze_authorization_paths"]) == {
        "docs/reference_cases/e4_pl_s3_v2_stage4a_contract.json",
        "docs/reference_cases/e4_pl_s3_v2_stage4a_execution_authorization.json",
        "docs/reference_cases/e4_pl_s3_v2_stage4a_process_implementation_review.json",
        "docs/reference_cases/e4_pl_s3_v2_stage4a_scientific_implementation_review.json",
    }
    assert set(extent["outcome_paths"]) == {
        "docs/reference_cases/e4_pl_s3_v2_stage4a_evidence.json",
        "docs/reference_cases/e4_pl_s3_v2_stage4a_result.json",
        "docs/reference_cases/e4_pl_s3_v2_stage4a_scientific_review.json",
        "docs/reference_cases/e4_pl_s3_v2_stage4a_status.json",
        "tests/test_e4_pl_s3_v2_stage4a_closeout.py",
    }


def test_registered_parent_objects_exist_and_match(authority) -> None:
    for identity in (authority["parent"], authority["scope_base"]):
        commit = subprocess.run(
            ["git", "rev-parse", identity["commit"]],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        tree = subprocess.run(
            ["git", "rev-parse", f"{identity['commit']}^{{tree}}"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        subject = subprocess.run(
            ["git", "show", "-s", "--format=%s", identity["commit"]],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        assert (commit, tree, subject) == (
            identity["commit"],
            identity["tree"],
            identity["subject"],
        )


def test_stage4a_authority_has_stable_identity() -> None:
    raw = AUTHORITY.read_bytes()
    assert len(raw) > 2_000
    assert len(hashlib.sha256(raw).hexdigest()) == 64
