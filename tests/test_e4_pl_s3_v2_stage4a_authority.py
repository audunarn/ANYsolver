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
    assert authority["schema"] == "anysolver.e4-pl-s3-v2-stage4a-authority-v8"
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
    assert phase["v1_diagnostic_record_count"] == 0
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
    assert correction["predecessor_v6_current_change"] == {
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
    assert correction["current_change"] == {
        "cases_changed": False,
        "classification": (
            "V2_ONLY_FORMAL_RUNTIME_PROCESS_AND_EVIDENCE_PROTOCOL_CORRECTION"
        ),
        "classifying_scientific_protocol_changed": False,
        "defaults_changed": False,
        "mechanics_changed": False,
        "process_or_evidence_protocol_changed": True,
        "protocol_changed": False,
        "tolerances_changed": False,
        "v1_mechanics_changed": False,
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
    assert correction["history"][5] == {
        "bytes": 12266,
        "commit": "0de98307c02a5b98cb924941fee9c21f94b60d66",
        "parent": "d085c097c434db396024d06c3f113b540189b75e",
        "path": "docs/reference_cases/e4_pl_s3_v2_stage4a_authority.json",
        "reason": "COMBINED_ROLE_N80_LEAVES_EXCEEDED_900_SECOND_WORKER_WALL",
        "sha256": (
            "69B75020D165EFBA3642D4575F624D99A1556B2352739E396C34754D0BC3987E"
        ),
        "subject": "fix: partition Stage 4A bounded evidence",
        "tree": "55d836332cecca7f9a38d8f5b3484adab5138fcc",
    }
    assert correction["history"][6] == {
        "bytes": 17991,
        "commit": "0470804a56b00cd15fc1aca92a5bee9151783716",
        "parent": "0de98307c02a5b98cb924941fee9c21f94b60d66",
        "path": "docs/reference_cases/e4_pl_s3_v2_stage4a_authority.json",
        "reason": (
            "NONCLASSIFYING_V1_DIAGNOSTIC_EXCEEDED_1500_SECOND_WORKER_WALL_"
            "AFTER_V2_COMPLETED"
        ),
        "sha256": (
            "0B4E8ADCE4BAE49DB1F8429296C9CC246B7FB56870A3087CC6EEB08EC498B4EB"
        ),
        "subject": "fix: split Stage 4A formulation roles",
        "tree": "9833c99edb92c88d6442ac960354030bf080191c",
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
        "docs/reference_cases/e4_pl_s3_v2_stage4a_leaf_wave_authorization.json",
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


def test_stage4a_correction4_nonclassifying_calibration_is_exact(authority) -> None:
    calibration = authority["correction"]["correction4_calibration"]
    assert calibration["disposition"] == "ROLE_SPLIT_REQUIRED_BEFORE_FORMAL_EXECUTION"
    assert calibration["earlier_requests"] == [
        {
            "disposition": "MALFORMED_COMMAND_NEVER_APPROVED_OR_EXECUTED",
            "request": {
                "byte_count": 1187,
                "request_id": "d6fe49a58b3444a092ae64a734a7a31a",
                "request_reuse_forbidden": True,
                "sha256": (
                    "3B75A3FDC7A1DF40E9B6FA7EA124F52E8BF3CF253321245B63FE74712DB7D8B3"
                ),
            },
            "terminal": "CANCELLED_UNAPPROVED",
        },
        {
            "disposition": "INVALID_PILOT_GIT_ENVIRONMENT_BEFORE_OUTPUT",
            "lock_released": True,
            "output_root_present": False,
            "request": {
                "byte_count": 1264,
                "command_sha256": (
                    "F01956582A71F19A9BCB0A73367BBF3675BF552251C4406C4F3FD63542BB657F"
                ),
                "request_id": "36380f3acd8c43e48a17eb0ac3eaf4ea",
                "request_reuse_forbidden": True,
                "sha256": (
                    "64D68EEEAA1C95877E2A1BBC528CE66C6F2575E06D40E5D5745FA1FC5290D26D"
                ),
            },
            "terminal": "COMPLETED_FAIL",
            "transcript": {
                "byte_count": 954,
                "sha256": (
                    "D3233B391C0D020C9E642F7CD07E3C84F03DBAE228A26A342336544098E68A80"
                ),
            },
        },
    ]
    assert calibration["n20_success"] == {
        "bounded_result": {
            "byte_count": 3120,
            "sha256": (
                "4F595234B5E8C27D388B5BF36DBE7616DD2F58037A8CE76EC1741CF2CC1AB4C2"
            ),
        },
        "peak_tree_memory_bytes": 332_537_856,
        "request": {
            "byte_count": 1277,
            "command_sha256": (
                "028FBA2C16E80C46A691C73E866F82CAB1D05475AA6DC14E66D0ADB27BC851CA"
            ),
            "request_id": "f5a6be8595484898ba566af5d91aa483",
            "request_reuse_forbidden": True,
            "sha256": (
                "57793FB7E6D2F352F8795288A6A18B32398F3CB3235B554A852834776C20A66C"
            ),
        },
        "scientific_classification": "NONCLASSIFYING_RUNTIME_CALIBRATION_ONLY",
        "summary": {
            "byte_count": 3716,
            "sha256": (
                "D19C6160A424518A909851D97ED42250FB5C949A52AA7ABDCABE6401930E5DF0"
            ),
        },
        "terminal": "COMPLETED_PASS",
        "termination_proven": True,
        "transcript": {
            "byte_count": 3717,
            "sha256": (
                "CF18AB52FE057FF712A642003D5E530C12F27E111A2700852ED36D352DFC850B"
            ),
        },
        "wall_seconds": "29.683154",
    }
    assert calibration["n80_timeout"] == {
        "bounded_result": {
            "byte_count": 5539,
            "sha256": (
                "5ECD12B629D320E076A2DA9252A6DCA9EA4D37FA40EECA1E271365D5FBAF02CE"
            ),
        },
        "last_progress_sequence": [1, 1],
        "peak_tree_memory_bytes": [1_937_715_200, 1_935_978_496],
        "request": {
            "byte_count": 1254,
            "command_sha256": (
                "2B7D302AD348F3FC3BFC8A31A8DE1FB3C33F05EF165F2B6455CE36D140BBFAF1"
            ),
            "request_id": "dc08835483b747d3afd3397fb35ef46d",
            "request_reuse_forbidden": True,
            "sha256": (
                "C2F2C206486E1CF043B67D8340F674E3C5650FA1DB9956EE6164F13EC53315E2"
            ),
        },
        "scientific_classification": "NONCLASSIFYING_RUNTIME_CALIBRATION_ONLY",
        "scientific_proof_count": 0,
        "summary": {
            "byte_count": 6301,
            "sha256": (
                "1A9D1BE927D71B38E3CE3F510CB9A1158B4930F18ACFA0188A2364ADFC23B781"
            ),
        },
        "terminal": "COMPLETED_FAIL",
        "termination_proven": [True, True],
        "transcript": {
            "byte_count": 6302,
            "sha256": (
                "1F01661205F5FD3A9EED0CB71ECCB57FD591EBAD94B7D4C2124665E87F3B51AB"
            ),
        },
        "wall_seconds": "900.872125",
        "worker_terminal_counts": {"TIMEOUT": 2},
    }
    assert calibration["canceled_never_run"] == [
        {
            "byte_count": 1266,
            "command_sha256": (
                "A0DC4A08E8F60DD351CDC09A3768125886C1F9A92C1ED78A3EE6242DEE1038BB"
            ),
            "request_id": "92297500432c46c9ad46523232817d9d",
            "request_reuse_forbidden": True,
            "sha256": (
                "0C370444B534C58D2C818A53FB3306522C95A8E3F0F206834D6FCDEE59062F57"
            ),
            "terminal": "CANCELLED_NOT_RUN",
        },
        {
            "byte_count": 1272,
            "command_sha256": (
                "89ACD2D229474CFA3A68F9CEC93C40BAAD442642499DEC2DC1B11B91BC35901A"
            ),
            "request_id": "96bf7d1d6d514e14b9b0a6da3307ec0e",
            "request_reuse_forbidden": True,
            "sha256": (
                "00A0DC143E30FCC11077935E463DA224D236A1E339C073339E7A91D3B5E23D2A"
            ),
            "terminal": "CANCELLED_NOT_RUN",
        },
    ]


def test_stage4a_correction5_nonclassifying_calibration_is_exact(authority) -> None:
    calibration = authority["correction"]["correction5_calibration"]
    assert calibration["disposition"] == (
        "HISTORICAL_V1_COMPARATOR_EXCLUDED_FROM_FORMAL_RUNTIME_NO_FALLBACK"
    )
    assert calibration["n20_role_equivalence"] == {
        "bounded_result": {
            "byte_count": 5962,
            "sha256": (
                "92BFCFECFF0DA5D728FFA71AD35D7EE84C9643052E74064F087891FEDE3CCB90"
            ),
        },
        "equivalence": {
            "byte_count": 2502,
            "disposition": "NONCLASSIFYING_RUNTIME_EQUIVALENCE_ONLY",
            "sha256": (
                "83352E5121E4B925321B3B6AA8575EB24BF6BF496545B174F77FC04DAED9B1F1"
            ),
            "terminal": "PASS_EXACT_INNER_RECORD_EQUIVALENCE",
        },
        "pilot_runner": {
            "byte_count": 10495,
            "sha256": (
                "441DC8E39871A2836513B7A7CF10A3FB4AA33B7A983DCA3217180B372C254539"
            ),
        },
        "proofs": {
            "v1_diagnostic": {
                "byte_count": 3652,
                "inner_record": {
                    "byte_count": 1570,
                    "correction4_sha256": (
                        "4DF1908BBD3C7BCE71FB050975A0D514AF88802CD2B1729E16021B5AD3CC4DA6"
                    ),
                    "sha256": (
                        "4DF1908BBD3C7BCE71FB050975A0D514AF88802CD2B1729E16021B5AD3CC4DA6"
                    ),
                },
                "sha256": (
                    "A2201E843CD389CCD0A7906DD9AB7DCD92DB303CA18A725EBCD1604F3B3C2A45"
                ),
                "status": "COMPLETED",
            },
            "v2_classifying": {
                "byte_count": 3615,
                "inner_record": {
                    "byte_count": 1528,
                    "correction4_sha256": (
                        "682353D9B6849CF05AE3C61BB6F545D753C5C82B07128115FB3A959123A65FD5"
                    ),
                    "sha256": (
                        "682353D9B6849CF05AE3C61BB6F545D753C5C82B07128115FB3A959123A65FD5"
                    ),
                },
                "sha256": (
                    "D1C6D1B44B10249A9DB423E0BA5ED64942FAD68EBA1C531400A065237240D5F9"
                ),
                "status": "COMPLETED",
            },
        },
        "request": {
            "byte_count": 1292,
            "command_sha256": (
                "4ACF18BA8E9A3E946641264D818BC96F536D2A937BBCB1F340F084E08DF9506C"
            ),
            "request_id": "91d5550d3b18459d80d1c6ce157de056",
            "request_reuse_forbidden": True,
            "sha256": (
                "A16711471E99C1B524D9C2E213BFC0E47BA6736F40C67985EC2A0C58E2739267"
            ),
        },
        "scientific_classification": "NONCLASSIFYING_RUNTIME_CALIBRATION_ONLY",
        "summary": {
            "byte_count": 2730,
            "sha256": (
                "9FADA46C663CF2A7D753DE36B7AC080DC16B618092152277ACFD8B109628AB83"
            ),
        },
        "terminal": "COMPLETED_PASS",
        "termination_proven": [True, True],
        "transcript": {
            "byte_count": 2731,
            "sha256": (
                "05CD6295399281AD032659856809781FB5397023767C8444395D6EE22645AB8A"
            ),
        },
        "wall_seconds": "26.272784",
    }
    assert calibration["n80_v1_timeout"] == {
        "bounded_result": {
            "byte_count": 5803,
            "sha256": (
                "274933EEE33FF8B50E5C88835C7A24506E6255913F2B892792EFB8A0C1C80826"
            ),
            "terminal": "BLOCKED_E4_PL_S3_V2_PROCESS_OR_EVIDENCE",
        },
        "manifest": {
            "byte_count": 10736,
            "sha256": (
                "2111BB7F2740D218F272FBC89AE942AA1616202223F14D7B7FC977EF1287A8A0"
            ),
        },
        "pilot_runner": {
            "byte_count": 10495,
            "sha256": (
                "441DC8E39871A2836513B7A7CF10A3FB4AA33B7A983DCA3217180B372C254539"
            ),
        },
        "record_id": "N80:25PCT:dispersed:slash",
        "request": {
            "byte_count": 1291,
            "command_sha256": (
                "61895014712DBCD31CDD69C21444B0857E4E3311A69E7FE4BB08817D3723C196"
            ),
            "request_id": "f016d9a4d0a9429bb09517a29998046a",
            "request_reuse_forbidden": True,
            "sha256": (
                "618E9051C9E1830A81551C2D5E9A11305E7888B3A8B9791238A3C014128ECE69"
            ),
        },
        "scientific_classification": "NONCLASSIFYING_RUNTIME_CALIBRATION_ONLY",
        "summary": {
            "byte_count": 2709,
            "sha256": (
                "509C1CF2D135A024D50BC2BB92FCA2A42030ED9C426B76DC4BBB9453746E2D1F"
            ),
        },
        "terminal": "COMPLETED_FAIL",
        "transcript": {
            "byte_count": 2710,
            "sha256": (
                "2966E53C7FC0963BC39813B2571E578CFC2E2F7F88EF2097ECE91AC5BAE26205"
            ),
        },
        "wall_seconds": "1500.962516",
        "workers": {
            "v1_diagnostic": {
                "cpu_100ns": 14_869_687_500,
                "last_progress_sequence": 1,
                "peak_tree_memory_bytes": 964_890_624,
                "returncode": 124,
                "scientific_proof_count": 0,
                "status": "TIMEOUT",
                "termination_proven": True,
            },
            "v2_classifying": {
                "cpu_100ns": 597_500_000,
                "last_progress_sequence": 5,
                "peak_tree_memory_bytes": 1_954_713_600,
                "proof": {
                    "byte_count": 3625,
                    "sha256": (
                        "9A765D7B44D55736A75017660D7BA9C790A6B451A1FC8BAEF84F7C7F8E89EBC9"
                    ),
                },
                "returncode": 0,
                "status": "COMPLETED",
                "termination_proven": True,
            },
        },
    }


def test_stage4a_correction6_v2_only_leaf_bounds(authority) -> None:
    assert authority["execution"] == {
        "all_launched_process_terminals_bound": True,
        "candidate_authority_bound_in_every_leaf": True,
        "canonical_aggregate_requires_complete_leaf_union": True,
        "canonical_aggregate_requires_proven_empty_process_trees": True,
        "checker_replica_wall_seconds": 300,
        "checker_tree_drain_required_before_queue_advance": True,
        "classifying_record_count": 81,
        "common_leaf_wave_authorization_required": True,
        "complete_receipt_coverage_required": True,
        "computation_leaf_count": 81,
        "consumed_request_reuse_forbidden": True,
        "content_addressed_assignments": True,
        "diagnostic_record_count": 0,
        "finalizer_accepts_complete_receipt_bound_union_only": True,
        "finalizer_input_hash_revalidated_before_publication": True,
        "finalizer_wall_seconds": 1740,
        "incomplete_or_partial_leaf_classification": "NONCLASSIFYING",
        "leaf_roles": ["V2_CLASSIFYING"],
        "leaf_worker_wall_seconds": 1500,
        "live_v1_diagnostic_execution_authorized": False,
        "maximum_concurrent_workers": 2,
        "maximum_memory_gib_per_process_tree": 24,
        "no_automatic_retry": True,
        "numerical_library_threads_per_worker": 1,
        "pair_wave_count": 40,
        "pairing_policy": "CONSECUTIVE_V2_CLASSIFYING_LEAVES_IN_FROZEN_ORDER",
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
        "required_receipt_count": 41,
        "role_split_required": False,
        "schedule": (
            "40_CONSECUTIVE_TWO_V2_WORKER_PAIRS_THEN_1_V2_SINGLETON_IN_FROZEN_ORDER"
        ),
        "singleton_wave_count": 1,
        "v1_comparator_disposition": (
            "HISTORICAL_V1_COMPARATOR_EXCLUDED_FROM_FORMAL_RUNTIME_NO_FALLBACK"
        ),
        "v1_diagnostic_leaf_count": 0,
        "v1_diagnostic_never_classifies_or_falls_back": True,
        "v2_classifying_leaf_count": 81,
        "wave_wall_seconds": 1740,
    }
    assert authority["correction"]["predecessor_v5_execution"][
        "wave_wall_seconds"
    ] == 1800
    assert authority["execution"]["leaf_worker_wall_seconds"] < 30 * 60
    assert authority["execution"]["wave_wall_seconds"] < 30 * 60
    assert authority["execution"]["finalizer_wall_seconds"] < 30 * 60
    assert authority["execution"]["computation_leaf_count"] == (
        authority["execution"]["v2_classifying_leaf_count"]
        + authority["execution"]["v1_diagnostic_leaf_count"]
    )
    assert authority["execution"]["registered_wave_count"] == (
        authority["execution"]["pair_wave_count"]
        + authority["execution"]["singleton_wave_count"]
    )


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
        "formal_protocol",
        "frozen_inputs",
        "parent",
        "production_boundary",
        "review_correction_requirements",
        "scope_base",
        "terminals",
    ):
        assert predecessor[unchanged] == authority[unchanged]
    current_candidate = dict(authority["candidate"])
    assert current_candidate.pop("v1_formal_runtime_disposition") == (
        "HISTORICAL_V1_COMPARATOR_EXCLUDED_FROM_FORMAL_RUNTIME_NO_FALLBACK"
    )
    assert predecessor["candidate"] == current_candidate
    assert predecessor["formal_phase"] == authority["correction"][
        "predecessor_v7_formal_phase"
    ]


def test_stage4a_prior_v6_authority_binding_and_history_are_exact(authority) -> None:
    prior = authority["correction"]["history"][5]
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
    assert predecessor["schema"] == "anysolver.e4-pl-s3-v2-stage4a-authority-v6"
    assert predecessor["correction"]["history"] == authority["correction"][
        "history"
    ][:5]
    assert predecessor["correction"]["current_change"] == authority["correction"][
        "predecessor_v6_current_change"
    ]
    assert predecessor["execution"] == authority["correction"][
        "predecessor_v6_execution"
    ]
    for unchanged in (
        "advisory_policy",
        "component_cache_policy",
        "formal_protocol",
        "frozen_inputs",
        "parent",
        "production_boundary",
        "review_correction_requirements",
        "scope_base",
        "terminals",
    ):
        assert predecessor[unchanged] == authority[unchanged]
    current_candidate = dict(authority["candidate"])
    current_candidate.pop("v1_formal_runtime_disposition")
    assert predecessor["candidate"] == current_candidate
    assert predecessor["formal_phase"] == authority["correction"][
        "predecessor_v7_formal_phase"
    ]
    predecessor_paths = set(predecessor["allowed_extent"]["freeze_authorization_paths"])
    current_paths = set(authority["allowed_extent"]["freeze_authorization_paths"])
    assert current_paths - predecessor_paths == {
        "docs/reference_cases/e4_pl_s3_v2_stage4a_leaf_wave_authorization.json"
    }


def test_stage4a_prior_v7_authority_binding_and_history_are_exact(authority) -> None:
    prior = authority["correction"]["history"][6]
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
    assert predecessor["schema"] == "anysolver.e4-pl-s3-v2-stage4a-authority-v7"
    assert predecessor["correction"]["history"] == authority["correction"][
        "history"
    ][:6]
    assert predecessor["correction"]["current_change"] == authority["correction"][
        "predecessor_v7_current_change"
    ]
    assert predecessor["execution"] == authority["correction"][
        "predecessor_v7_execution"
    ]
    assert predecessor["formal_phase"] == authority["correction"][
        "predecessor_v7_formal_phase"
    ]
    current_candidate = dict(authority["candidate"])
    current_candidate.pop("v1_formal_runtime_disposition")
    assert predecessor["candidate"] == current_candidate
    predecessor_paths = set(predecessor["allowed_extent"]["freeze_authorization_paths"])
    current_paths = set(authority["allowed_extent"]["freeze_authorization_paths"])
    assert current_paths - predecessor_paths == {
        "docs/reference_cases/e4_pl_s3_v2_stage4a_leaf_wave_authorization.json"
    }
    for unchanged in (
        "advisory_policy",
        "component_cache_policy",
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
