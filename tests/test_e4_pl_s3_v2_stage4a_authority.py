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
    assert authority["schema"] == "anysolver.e4-pl-s3-v2-stage4a-authority-v6"
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
    assert "tests/test_e4_pl_s3_v2_component_cache.py" in extent["implementation_paths"]


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
        "docs/reference_cases/e4_pl_s3_v2_bounded_process.py",
        "tests/test_e4_pl_s3_v2_candidate_binding.py",
        "tests/test_e4_pl_s3_v2_bounded_process.py",
        "tests/test_e4_pl_s3_v2_flat_candidate_review.py",
    } <= set(extent["implementation_paths"])
    assert correction["predecessor_v5_current_change"] == {
        "cases_changed": False,
        "classification": "PROCESS_WALL_AND_CHECKER_TREE_DRAIN_ONLY",
        "consumed_request": {
            "checker_processes_started": 0,
            "classifying_records": 0,
            "producer_processes_started": 0,
            "request_id": "3725cb19803543bfa789903b2a11f59a",
            "request_reuse_forbidden": True,
            "terminal": "BLOCKED_E4_PL_S3_V2_PROCESS_OR_EVIDENCE",
            "wave_terminal": "RESOURCE_DEFERRED",
        },
        "defaults_changed": False,
        "mechanics_changed": False,
        "process_control_changed": True,
        "protocol_changed": False,
        "tolerances_changed": False,
    }
    assert correction["current_change"] == {
        "cases_changed": False,
        "classification": (
            "EXACT_COMPONENT_CACHE_AND_CONTENT_ADDRESSED_LEAF_PROCESS_ONLY"
        ),
        "defaults_changed": False,
        "mechanics_changed": False,
        "process_control_changed": True,
        "protocol_changed": False,
        "tolerances_changed": False,
        "v2_equations_changed": False,
        "v2_matrices_changed": False,
    }
    assert correction["history"][2] == {
        "bytes": 6458,
        "commit": "3bbf5d3e85b8ba218846004a4f84a2bbaf0818a0",
        "path": "docs/reference_cases/e4_pl_s3_v2_stage4a_authority.json",
        "reason": "RESOURCE_DEFERRED_WITH_ZERO_WORKER_LAUNCHES",
        "sha256": "17B7B768EDE593A600F4B37C120E0653BE3C522B2E5C62687EFCD8C02272C322",
        "subject": "docs: authorize S3 V2A Stage 4A review corrections",
        "tree": "95bdde42a9260b10cebfa59e7315d0530610c4cf",
    }
    assert correction["history"][3] == {
        "bytes": 7809,
        "commit": "3ba32964a75dfe077440692535876b3c3a6b076e",
        "path": "docs/reference_cases/e4_pl_s3_v2_stage4a_authority.json",
        "reason": "INCOMPLETE_COORDINATOR_WALL_AND_CHECKER_TREE_DRAIN_GUARDS",
        "sha256": "6F5D2C676D7728EEBC36E12A27678CDE95151E2747E721F10B5DCE80FC2E4C6D",
        "subject": "fix: serialize Stage 4A resource admission",
        "tree": "5666a6d729db322b49a7ce1b242dec7c0f98b960",
    }
    assert correction["history"][4] == {
        "bytes": 8668,
        "commit": "d085c097c434db396024d06c3f113b540189b75e",
        "parent": "3ba32964a75dfe077440692535876b3c3a6b076e",
        "path": "docs/reference_cases/e4_pl_s3_v2_stage4a_authority.json",
        "reason": "MONOLITHIC_SHARDS_EXCEEDED_BOUNDED_WORKER_WALL",
        "sha256": (
            "D145B76F394EC4733FB2EE2A5DD0844C49F9ED711918F53F539D81394A2F64AA"
        ),
        "subject": "fix: enforce Stage 4A hard process bounds",
        "tree": "d9208ec9d98fd9c7ac9f4156ee9dda97a1de86cb",
    }
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


def test_stage4a_correction4_exact_component_cache_policy(authority) -> None:
    assert authority["component_cache_policy"] == {
        "capacity": 512,
        "closure_owned": True,
        "deterministic_eviction": (
            "RETAIN_LEXICOGRAPHICALLY_SMALLEST_EXACT_CONTENT_KEYS"
        ),
        "fresh_writable_copies_on_every_return": True,
        "guard_before_lookup": True,
        "key": "FULL_VALIDATED_NUMERIC_CONTENT_AND_FROZEN_FORMULATION_IDENTITY",
        "key_validation": ["DTYPE", "FINITE", "SHAPE", "VALUE"],
        "lock": "THREADING_RLOCK",
        "pl_and_numerical_outputs_distinct": True,
        "v2_equations_or_matrices_changed": False,
    }


def test_stage4a_correction3_consumed_timeout_incident_is_exact(authority) -> None:
    assert authority["correction"]["correction3_incident"] == {
        "canonical_aggregate": {
            "byte_count": 681,
            "sha256": (
                "79E58C76EDE5DEEBC84C98014333FBBAEE7DB6A0A4BC978374138EAB4BEB42DB"
            ),
        },
        "classifying_record_count": 0,
        "completed_partial_records": {
            "alternating": {"completed": 17, "registered": 27},
            "backslash": {"completed": 16, "registered": 27},
            "slash": {"completed": 16, "registered": 27},
        },
        "partial_records_classification": "NONCLASSIFYING",
        "producer_result": {
            "byte_count": 7476,
            "sha256": (
                "23E56EF27DBF81C80EF79F1A888E89FCFF0F64787AF9892E2497ABA6A93BAB8A"
            ),
        },
        "producer_workers": {"count": 3, "terminal_counts": {"TIMEOUT": 3}},
        "request": {
            "request_id": "da3f0b058f124d8488dcd8bae341ac22",
            "request_reuse_forbidden": True,
        },
        "scientific_checker_count": 0,
        "scientific_proof_count": 0,
        "terminal": "BLOCKED_E4_PL_S3_V2_PROCESS_OR_EVIDENCE",
        "transcript": {
            "byte_count": 4526,
            "sha256": (
                "9C3214F6554D362CB881C1A5BBFC62156A8EE5B2E4933B34EE05BC71D46F617E"
            ),
        },
    }


def test_stage4a_correction4_content_addressed_leaf_bounds(authority) -> None:
    assert authority["execution"] == {
        "all_launched_process_terminals_bound": True,
        "candidate_authority_bound_in_every_leaf": True,
        "canonical_aggregate_requires_complete_leaf_union": True,
        "canonical_aggregate_requires_proven_empty_process_trees": True,
        "checker_replica_wall_seconds": 300,
        "checker_tree_drain_required_before_queue_advance": True,
        "classifying_leaf_count": 81,
        "common_leaf_wave_authorization_required": True,
        "complete_receipt_coverage_required": True,
        "consumed_request_reuse_forbidden": True,
        "content_addressed_assignments": True,
        "finalizer_accepts_complete_receipt_bound_union_only": True,
        "finalizer_input_hash_revalidated_before_publication": True,
        "finalizer_wall_seconds": 1740,
        "incomplete_or_partial_leaf_classification": "NONCLASSIFYING",
        "leaf_worker_wall_seconds": 900,
        "maximum_concurrent_workers": 2,
        "maximum_memory_gib_per_process_tree": 24,
        "no_automatic_retry": True,
        "numerical_library_threads_per_worker": 1,
        "pair_wave_count": 40,
        "process_tree_termination_proven_required": True,
        "receipt_binding": [
            "ATTEMPT",
            "AUTHORIZATION",
            "CANDIDATE_ARCHIVE_SHA256",
            "CANDIDATE_COMMIT",
            "CANDIDATE_TREE",
            "CONTRACT",
            "LEAF_CATALOG_SHA256",
            "LEAF_MANIFEST",
            "LEAF_SCIENTIFIC_HASHES",
            "PLAN_SHA256",
            "PRODUCER_PROGRAM_SHA256",
            "REQUEST_COMMAND_SHA256",
            "REQUEST_ID",
            "REQUEST_SHA256",
            "RESULT_SHA256",
            "TERMINATION_PROVEN",
            "WORKER_TERMINALS",
        ],
        "receipt_required_per_wave": True,
        "registered_wave_count": 41,
        "schedule": "40_CONTENT_ADDRESSED_PAIRS_THEN_1_SINGLETON_IN_FROZEN_ORDER",
        "singleton_wave_count": 1,
        "wave_wall_seconds": 1740,
    }
    assert authority["correction"]["predecessor_v5_execution"][
        "wave_wall_seconds"
    ] == 1800
    assert authority["execution"]["leaf_worker_wall_seconds"] < 30 * 60
    assert authority["execution"]["wave_wall_seconds"] < 30 * 60
    assert authority["execution"]["finalizer_wall_seconds"] < 30 * 60


def test_stage4a_prior_v3_authority_binding_is_exact(authority) -> None:
    prior = authority["correction"]["history"][2]
    raw = subprocess.run(
        ["git", "show", f"{prior['commit']}:{prior['path']}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout
    subject = subprocess.run(
        ["git", "show", "-s", "--format=%s", prior["commit"]],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    tree = subprocess.run(
        ["git", "rev-parse", f"{prior['commit']}^{{tree}}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert len(raw) == prior["bytes"]
    assert hashlib.sha256(raw).hexdigest().upper() == prior["sha256"]
    assert (subject, tree) == (prior["subject"], prior["tree"])


def test_stage4a_prior_v4_authority_binding_is_exact(authority) -> None:
    prior = authority["correction"]["history"][3]
    raw = subprocess.run(
        ["git", "show", f"{prior['commit']}:{prior['path']}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout
    subject = subprocess.run(
        ["git", "show", "-s", "--format=%s", prior["commit"]],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    tree = subprocess.run(
        ["git", "rev-parse", f"{prior['commit']}^{{tree}}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert len(raw) == prior["bytes"]
    assert hashlib.sha256(raw).hexdigest().upper() == prior["sha256"]
    assert (subject, tree) == (prior["subject"], prior["tree"])


def test_stage4a_prior_v5_authority_binding_and_history_are_exact(authority) -> None:
    prior = authority["correction"]["history"][4]
    raw = subprocess.run(
        ["git", "show", f"{prior['commit']}:{prior['path']}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout
    subject = subprocess.run(
        ["git", "show", "-s", "--format=%s", prior["commit"]],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    tree = subprocess.run(
        ["git", "rev-parse", f"{prior['commit']}^{{tree}}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    parent = subprocess.run(
        ["git", "rev-parse", f"{prior['commit']}^"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    predecessor = json.loads(
        raw.decode("utf-8"),
        object_pairs_hook=_reject_duplicates,
        parse_constant=_reject_constant,
    )
    assert raw == _canonical(predecessor)
    assert len(raw) == prior["bytes"]
    assert hashlib.sha256(raw).hexdigest().upper() == prior["sha256"]
    assert (subject, tree, parent) == (
        prior["subject"],
        prior["tree"],
        prior["parent"],
    )
    assert predecessor["schema"] == "anysolver.e4-pl-s3-v2-stage4a-authority-v5"
    assert predecessor["correction"]["history"] == authority["correction"][
        "history"
    ][:4]
    assert predecessor["correction"]["current_change"] == authority["correction"][
        "predecessor_v5_current_change"
    ]
    assert predecessor["execution"] == authority["correction"][
        "predecessor_v5_execution"
    ]
    for unchanged in (
        "advisory_policy",
        "candidate",
        "formal_phase",
        "formal_protocol",
        "frozen_inputs",
        "parent",
        "production_boundary",
        "review_correction_requirements",
        "scope_base",
        "terminals",
    ):
        assert predecessor[unchanged] == authority[unchanged]


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
