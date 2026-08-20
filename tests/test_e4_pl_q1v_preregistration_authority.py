from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "docs" / "reference_cases"
BASE_COMMIT = "7d4ac30b4d50a1ee62edefbe5fb0198b47276360"
BASE_TREE = "50e212467ea5b9793e8741ff52800681ad3634ff"
BASE_PARENT = "d40506aee079d19ce7a1ec658a03dd499565bd0f"
BASE_SUBJECT = "docs: close E4 PL Q1U oracle-or-review block"
CANDIDATE = "candidate_e4_pl_q1v.wg2020_numbered_frame_surface_pl_planar_linear_iso_v1"
STUDY = "study_e4_pl_q1v.q1u_backend_repair_and_local_completion_v1"
PLAN_REVIEW_VERDICT = "ACCEPT_Q1V_PREREGISTRATION_NO_P0_P1"
HARD_FREEZE_EVENT = "FIRST_SUCCESSFULLY_WRITTEN_REOPENED_HASH_VERIFIED_COMPLETE_SCHEMA_VALID_EXCLUSIVELY_CREATED_CANONICAL_REGISTERED_CERTIFICATE"
PLAN14 = (
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
)
IMPLEMENTATION20 = (
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
)
CONTRACT3 = (
    "docs/reference_cases/e4_pl_q1v_execution_contract.json",
    "docs/reference_cases/e4_pl_q1v_contract_review.json",
    "tests/test_e4_pl_q1v_contract.py",
)
OUTCOME11 = (
    "docs/reference_cases/e4_pl_q1v_reference_raw.json",
    "docs/reference_cases/e4_pl_q1v_oracle_raw.json",
    "docs/reference_cases/e4_pl_q1v_agreement.json",
    "docs/reference_cases/e4_pl_q1v_output.json",
    "docs/reference_cases/e4_pl_q1v_status.json",
    "docs/reference_cases/e4_pl_q1v_execution_authority.json",
    "docs/reference_cases/e4_pl_q1v_scientific_test_result.json",
    "docs/E4_PL_Q1V_LOCAL_QUALIFICATION.md",
    "docs/reference_cases/e4_pl_q1v_scientific_review.json",
    "docs/E4_PL_Q1V_COMPLETION.md",
    "tests/test_e4_pl_q1v_closeout.py",
)
BLOCKED5 = (
    "docs/reference_cases/e4_pl_q1v_status.json",
    "docs/E4_PL_Q1V_LOCAL_QUALIFICATION.md",
    "docs/reference_cases/e4_pl_q1v_scientific_review.json",
    "docs/E4_PL_Q1V_COMPLETION.md",
    "tests/test_e4_pl_q1v_closeout.py",
)
TERMINALS = (
    (1, "BLOCKED", "BLOCKED_E4_PL_Q1V_BASELINE_MISMATCH", "Q1U_BASE_COMMIT_TREE_PARENT_SUBJECT_PATHS_OR_STATIC_CLOSEOUT_NODE_MISMATCH"),
    (2, "BLOCKED", "BLOCKED_E4_PL_Q1V_INHERITANCE_MISMATCH", "ANY_OF_117_DIRECT_INHERITANCE_ROWS_MISMATCHES"),
    (3, "BLOCKED", "BLOCKED_E4_PL_Q1V_PLAN_AUTHORITY", "PLAN14_EXTENT_PLAN_REVIEW_STAGE_BARRIER_OR_AUTHORITY_INVALID"),
    (4, "BLOCKED", "BLOCKED_E4_PL_Q1V_EXACT_BACKEND", "DIAGNOSTIC_UNRESOLVED_OR_EXACT_BACKEND_ENVIRONMENT_IDENTITY_INVALID"),
    (5, "NO_GO", "NO_GO_E4_PL_Q1V_FRAME_IDENTITY", "INDEPENDENT_EXACT_DIAGNOSIS_PROVES_FROZEN_EQUATION7_OR_FRAME_IDENTITY_CONTRADICTION"),
    (6, "BLOCKED", "BLOCKED_E4_PL_Q1V_IMPLEMENTATION_IDENTITY", "CORRECTION_BUDGET_IMPLEMENTATION20_COMMISSIONING_EQUIVALENCE_OR_IMPLEMENTATION_REVIEW_INVALID"),
    (7, "BLOCKED", "BLOCKED_E4_PL_Q1V_CONTRACT_OR_NONDETERMINISM", "CONTRACT3_REAUTHORIZATION_GUARDS_CANONICAL_TRANSPORT_OR_DETERMINISM_INVALID"),
    (8, "BLOCKED", "BLOCKED_E4_PL_Q1V_ORACLE_OR_REVIEW", "CROSS_IMPLEMENTATION_AGREEMENT_BACKEND_DEFECT_TERMINAL_APPLICATION_OR_SCIENTIFIC_REVIEW_INVALID"),
    (9, "NO_GO", "NO_GO_E4_PL_Q1V_LOCAL_ALGEBRA", "EXACT_LOCAL_ALGEBRA_CONTRADICTION"),
    (10, "NO_GO", "NO_GO_E4_PL_Q1V_PATCH_OR_COVARIANCE", "EXACT_FRAME_PATCH_WORK_RECOVERY_SUPPORT_REACTION_OR_COVARIANCE_CONTRADICTION"),
    (11, "UNCLASSIFIED", "UNCLASSIFIED_E4_PL_Q1V_LOCAL_PLANAR_IDENTITY", "REQUIRED_ORDERED_SIGN_UNRESOLVED_AT_1024_BITS_AFTER_ALL_HIGHER_GATES_PASS"),
    (12, "PROVISIONAL_GO", "PROVISIONAL_GO_E4_PL_Q1V_Q1B_PLAN", "ALL_AUTHORITY_DIAGNOSIS_COMMISSIONING_DETERMINISM_AGREEMENT_LOCAL_SCIENCE_AND_REVIEW_GATES_PASS"),
)


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    out: dict[str, object] = {}
    for key, value in pairs:
        if key in out:
            raise AssertionError(f"duplicate JSON key: {key}")
        out[key] = value
    return out


def _reject_constant(value: str) -> None:
    raise AssertionError(f"non-finite JSON constant: {value}")


def _load_json(path: Path) -> dict[str, object]:
    raw = path.read_bytes()
    assert raw.endswith(b"\n")
    assert b"\r" not in raw and not raw.startswith(b"\xef\xbb\xbf")
    value = json.loads(
        raw.decode("utf-8"),
        object_pairs_hook=_pairs,
        parse_constant=_reject_constant,
    )
    assert isinstance(value, dict)
    canonical = (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")
    assert raw == canonical, path
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _git(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return completed.stdout.strip()


def _reviewed_row(relative_path: str) -> dict[str, object]:
    path = ROOT / relative_path
    return {
        "bytes": len(path.read_bytes()),
        "path": relative_path,
        "sha256": _sha256(path),
    }


def test_q1v_baseline_and_117_row_inheritance_are_exact() -> None:
    baseline = _load_json(REF / "e4_pl_q1v_baseline.json")
    inheritance = _load_json(REF / "e4_pl_q1v_inheritance_manifest.json")

    assert baseline["schema"] == "anysolver.s4.e4-pl-q1v-baseline-v1"
    assert baseline["candidate_id"] == CANDIDATE
    assert baseline["study_id"] == STUDY
    assert baseline["attachment"] == {
        "bytes": 14497,
        "filename": "S4_E4_PL_Q1V_LOCAL_COMPLETION_PLAN.md",
        "role": "BACKGROUND_DESIGN_INPUT",
        "sha256": "74A9618F1C96D041C97816F2124AF2F1C0E23D21E297291E05CBC9ED76585EE7",
    }
    assert baseline["base"] == {
        "commit": BASE_COMMIT,
        "parent": BASE_PARENT,
        "path_count": 6,
        "paths": [
            "docs/E4_PL_Q1U_COMPLETION.md",
            "docs/E4_PL_Q1U_LOCAL_QUALIFICATION.md",
            "docs/reference_cases/e4_pl_q1u_execution_authority.json",
            "docs/reference_cases/e4_pl_q1u_scientific_review.json",
            "docs/reference_cases/e4_pl_q1u_status.json",
            "tests/test_e4_pl_q1u_closeout.py",
        ],
        "subject": BASE_SUBJECT,
        "tree": BASE_TREE,
    }
    assert _git("rev-parse", f"{BASE_COMMIT}^{{tree}}") == BASE_TREE
    assert _git("rev-parse", f"{BASE_COMMIT}^") == BASE_PARENT
    assert _git("show", "-s", "--format=%s", BASE_COMMIT) == BASE_SUBJECT
    assert _git("diff-tree", "--no-commit-id", "--name-only", "-r", BASE_COMMIT).splitlines() == baseline["base"]["paths"]

    assert inheritance["schema"] == "anysolver.s4.e4-pl-q1v-inheritance-manifest-v1"
    assert inheritance["candidate_id"] == CANDIDATE
    assert inheritance["study_id"] == STUDY
    assert inheritance["git_object_format"] == "sha1"
    assert inheritance["counts"] == {
        "q1u_blocked_closeout_inputs": 6,
        "q1u_contract3_inputs": 3,
        "q1u_implementation14_inputs": 14,
        "q1u_inherited_inputs": 82,
        "q1u_plan12_inputs": 12,
        "total_directly_bound_inputs": 117,
    }
    rows = inheritance["inputs"]
    assert isinstance(rows, list) and len(rows) == 117
    assert len({row["path"] for row in rows}) == 117
    assert all(set(row) == {"bytes", "classification", "git_blob", "path", "sha256", "source_commit", "source_tree"} for row in rows)
    assert set(inheritance["classifications"]) == {row["classification"] for row in rows}
    assert inheritance["input_groups"] == [
        {"count": 82, "end_index_inclusive": 81, "name": "Q1U_INHERITED82", "source": "docs/reference_cases/e4_pl_q1u_inheritance_manifest.json", "start_index": 0},
        {"count": 12, "end_index_inclusive": 93, "name": "Q1U_PLAN12", "source_commit": "2404ec3cec03fe9ddef131d9bfd39a24e4e7eabc", "start_index": 82},
        {"count": 14, "end_index_inclusive": 107, "name": "Q1U_IMPLEMENTATION14", "source_commit": "9add6b937d4e2bd5668717f9a9b8d6bd1dfe6cda", "start_index": 94},
        {"count": 3, "end_index_inclusive": 110, "name": "Q1U_CONTRACT3", "source_commit": "d40506aee079d19ce7a1ec658a03dd499565bd0f", "start_index": 108},
        {"count": 6, "end_index_inclusive": 116, "name": "Q1U_BLOCKED_CLOSEOUT6", "source_commit": BASE_COMMIT, "start_index": 111},
    ]
    q1u_inheritance = _load_json(REF / "e4_pl_q1u_inheritance_manifest.json")
    assert rows[:82] == q1u_inheritance["inputs"]
    q1u_extent = _load_json(REF / "e4_pl_q1u_allowed_extent.json")["path_sets"]
    assert {row["path"] for row in rows[82:94]} == set(q1u_extent["PLAN12"])
    assert {row["path"] for row in rows[94:108]} == set(q1u_extent["IMPLEMENTATION14"])
    assert {row["path"] for row in rows[108:111]} == set(q1u_extent["CONTRACT3"])
    assert [row["path"] for row in rows[111:]] == baseline["base"]["paths"]
    for row in rows:
        relative = row["path"]
        path = ROOT / relative
        assert path.is_file()
        assert len(path.read_bytes()) == row["bytes"]
        assert _sha256(path) == row["sha256"]
        assert _git("rev-parse", f"{row['source_commit']}^{{tree}}") == row["source_tree"]
        assert _git("rev-parse", f"{row['source_commit']}:{relative}") == row["git_blob"]
        assert _git("rev-parse", f"{BASE_COMMIT}:{relative}") == row["git_blob"]

    assert baseline["environment"] == {
        "record_path": "docs/reference_cases/e4_pl_q1t_environment.json",
        "sha256": "5461206324E7FC2A52B334CE736A512EE71313ED79181438047E3E20069A9746",
    }
    environment_path = ROOT / baseline["environment"]["record_path"]
    assert len(environment_path.read_bytes()) == 227603
    assert _sha256(environment_path) == baseline["environment"]["sha256"]


def test_q1v_stage_extents_correction_budget_and_reauthorization_are_exact() -> None:
    extent = _load_json(REF / "e4_pl_q1v_allowed_extent.json")
    authority = _load_json(REF / "e4_pl_q1v_authority_contract.json")

    assert extent["schema"] == "anysolver.s4.e4-pl-q1v-allowed-extent-v1"
    assert extent["stage_counts"] == {
        "BLOCKED5": 5,
        "CONTRACT3": 3,
        "IMPLEMENTATION20": 20,
        "OUTCOME11": 11,
        "PLAN14": 14,
    }
    assert extent["path_count"] == 48
    path_sets = extent["path_sets"]
    assert path_sets == {
        "BLOCKED5": list(BLOCKED5),
        "CONTRACT3": list(CONTRACT3),
        "IMPLEMENTATION20": list(IMPLEMENTATION20),
        "OUTCOME11": list(OUTCOME11),
        "PLAN14": list(PLAN14),
    }
    for name, count in extent["stage_counts"].items():
        assert len(path_sets[name]) == count
        assert len(set(path_sets[name])) == count
    stage_union = set(path_sets["PLAN14"]) | set(path_sets["IMPLEMENTATION20"]) | set(path_sets["CONTRACT3"]) | set(path_sets["OUTCOME11"])
    assert len(stage_union) == 48
    assert "docs/agent_plans/S4_E4_PL_Q1B_COMPLETION_PLAN.md" not in stage_union
    assert extent["q1b_boundary"] == {
        "path_created_by_q1v": False,
        "planning_run_requires": "SEPARATE_USER_REQUEST_AND_REVIEW",
        "q1b_execution_authorized": False,
    }

    routes = extent["blocked_routes"]
    assert routes == {
        "contract": {"exact_parent": "LATEST_ACCEPTED_IMPLEMENTATION_FREEZE", "path_count": 8, "path_expression": "CONTRACT3_UNION_BLOCKED5"},
        "implementation": {"exact_parent": "ACCEPTED_COMMIT1", "path_count": 25, "path_expression": "IMPLEMENTATION20_UNION_BLOCKED5"},
        "plan_or_inheritance": {"exact_parent": BASE_COMMIT, "path_count": 19, "path_expression": "PLAN14_UNION_BLOCKED5"},
        "post_authority_or_reauthorization": {"exact_parent": "LATEST_ACCEPTED_AUTHORIZATION", "path_count": 6, "path_expression": "EXECUTION_AUTHORITY_COPY_UNION_BLOCKED5"},
        "scientific": {"exact_parent": "LATEST_ACCEPTED_AUTHORIZATION", "path_count": 11, "path_expression": "OUTCOME11"},
    }
    revision = extent["revision_policy"]
    assert revision["corrections_max"] == 2
    assert revision["contract_correction_max"] == 1
    assert revision["plan_correction_max"] == 1
    assert revision["hard_freeze"] == HARD_FREEZE_EVENT
    assert revision["no_new_paths_during_revision"] is True
    assert set(revision["revision_paths_must_be_subset_of"]) < set(path_sets["IMPLEMENTATION20"])
    assert set(revision["revision_paths_must_be_subset_of"]).isdisjoint(revision["scientific_test_paths_immutable"])

    assert authority["schema"] == "anysolver.s4.e4-pl-q1v-authority-contract-v1"
    stages = authority["commit_stages"]
    assert [row["name"] for row in stages] == ["PLAN14", "IMPLEMENTATION20", "CONTRACT3", "OUTCOME11"]
    assert [row["path_count"] for row in stages] == [14, 20, 3, 11]
    assert [row["subject"] for row in stages] == [
        "docs: preregister E4 PL Q1V local completion",
        "docs: freeze E4 PL Q1V commissioned exact implementations",
        "docs: authorize E4 PL Q1V scientific execution",
        "docs: close E4 PL Q1V local qualification",
    ]
    assert authority["correction_authority"]["cycles_max"] == 2
    assert authority["correction_authority"]["new_paths_forbidden"] is True
    assert authority["hard_scientific_freeze"] == {
        "event": HARD_FREEZE_EVENT,
        "post_event_source_test_contract_tolerance_or_case_changes": False,
        "pre_certificate_reauthorization_required": True,
    }
    assert authority["pre_certificate_reauthorization"]["authorization_token"] == f"REAUTHORIZE_E4_PL_Q1V_{HARD_FREEZE_EVENT}"
    assert authority["execution_authority_record"]["timestamp_forbidden"] is True
    assert authority["blocked_routes"] == routes
    correction = authority["correction_authority"]
    assert correction["hard_freeze_event"] == HARD_FREEZE_EVENT
    assert correction["cycles_max"] == 2
    assert correction["mandatory_revision_paths"] == revision["mandatory_revision_paths"]
    assert correction["affected_mutable_program_or_test_paths"] == revision["affected_mutable_program_or_test_paths"]
    dag = correction["correction_dag"]
    assert dag["initial_authorization"] == {
        "authorization_alias": "A_0",
        "cycle": 0,
        "id": "C3",
        "parent": "ACCEPTED_COMMIT2",
        "path_count": 3,
        "paths": list(CONTRACT3),
        "subject": "docs: authorize E4 PL Q1V scientific execution",
    }
    assert dag["latest_accepted_authorization"] == {
        "cycle_0": "A_0_EQUALS_C3",
        "cycle_1": "A_1",
        "cycle_2": "A_2",
        "selector": "HIGHEST_MONOTONIC_ACCEPTED_CYCLE",
    }
    assert dag["monotonicity"] == {
        "cycle_numbers": [0, 1, 2],
        "cycles_max": 2,
        "gaps_reuse_or_decrease_forbidden": True,
        "strictly_increasing": True,
    }
    cycle_rows = dag["revision_cycles"]
    assert len(cycle_rows) == 2
    for number, row in enumerate(cycle_rows, start=1):
        assert row["revision"] == {
            "affected_subset_rule": "EXACT_SUBSET_OF_PREREGISTERED_MUTABLE_PROGRAM_OR_TEST_PATHS",
            "changed_paths_rule": "SORTED_UNIQUE_UNION_OF_MANDATORY_PATHS_AND_EXACT_AFFECTED_SUBSET",
            "cycle": number,
            "id": f"R_{number}",
            "incident_record": {
                "committed_separate_path": False,
                "digest_binding": "IMPLEMENTATION_MANIFEST_EXACT_SHA256",
                "location": "EXTERNAL",
            },
            "parent": "A_0" if number == 1 else "A_1",
            "subject": f"docs: revise E4 PL Q1V implementations before certificate cycle {number}",
        }
        assert row["authorization"] == {
            "cycle": number,
            "id": f"A_{number}",
            "parent": f"R_{number}",
            "path_count": 3,
            "paths": list(CONTRACT3),
            "subject": f"docs: reauthorize E4 PL Q1V scientific execution cycle {number}",
        }


def test_q1v_backend_incident_exact_contracts_and_certificate_boundary_are_exact() -> None:
    incident = _load_json(REF / "e4_pl_q1v_q1u_backend_incident.json")
    backend = _load_json(REF / "e4_pl_q1v_exact_backend_contract.json")
    commissioning = _load_json(REF / "e4_pl_q1v_commissioning_contract.json")
    equivalence = _load_json(REF / "e4_pl_q1v_mechanics_equivalence_contract.json")
    certificate = _load_json(REF / "e4_pl_q1v_certificate_schema.json")
    terminals = _load_json(REF / "e4_pl_q1v_terminal_table.json")
    inventory = _load_json(REF / "e4_pl_q1v_test_inventory.json")

    assert incident["schema"] == "anysolver.s4.e4-pl-q1v-q1u-backend-incident-v1"
    assert incident["current_classification"] == "REFERENCE_BACKEND_IMPLEMENTATION_DEFECT"
    witness = incident["exact_witness"]
    assert witness["geometry_id"] == "Q1_AFFINE_SKEW"
    assert witness["operation_id"] == "E"
    assert witness["den_times_inverse_exact"] is True
    assert witness["inverse_times_den_residual"] == "-459/2153779"
    assert witness["identity_valid"] is True
    assert witness["defect"] == "NONCOMMUTATIVE_NESTED_RADICAL_BASIS_REDUCTION"
    assert incident["mechanics_disposition"] == "NO_MECHANICS_CONTRADICTION_ESTABLISHED"

    assert backend["schema"] == "anysolver.s4.e4-pl-q1v-exact-backend-contract-v1"
    repair = backend["reference_repair"]
    assert repair["multiplication_rule"] == "(a+b*alpha)*(c+d*alpha)=(a*c+b*d*r)+(a*d+b*c)*alpha_WITH_alpha^2=r"
    assert repair["representation"] == "RECURSIVE_QUADRATIC_EXTENSION"
    assert "RECURSIVE_CONJUGATE_NORM_INVERSION" in repair["unchanged"]
    assert backend["e_numbering_field"]["formal_degree_maximum"] == 32
    assert len(backend["e_numbering_field"]["generator_schedule"]) == 5
    assert backend["equality"]["float_tolerance_interval_or_evalf"] is False

    assert commissioning["record_kind"] == "NONCLASSIFYING_IMPLEMENTATION_COMMISSIONING"
    assert commissioning["coverage"] == {
        "case_ids_exact_order": True,
        "centre_constructions": 56,
        "geometry_groups": 7,
        "numbered_cases": 56,
        "station_constructions": 224,
    }
    forbidden = set(commissioning["forbidden_content"])
    assert {"ENERGY", "STIFFNESS_SIGN", "RANK", "PATCH_PASS_FAIL", "SCIENTIFIC_CLASSIFICATION", "PROPOSED_TERMINAL"} <= forbidden
    assert commissioning["recursive_forbidden_content_scan"] is True
    serialized_keys = set(commissioning["result_schema"]["implementation_exact_keys"])
    assert not {"classification", "rank", "energy", "terminal"} & serialized_keys

    assert equivalence["correction_cycles"]["hard_limit"] == 2
    assert "UNCLASSIFIED_NODE" in equivalence["prohibitions"]
    assert set(equivalence["allowed_classifications"]) == {
        "IDENTICAL_SCIENTIFIC_BODY",
        "AUTHORIZED_BACKEND_DEFECT_CORRECTION",
        "AUTHORIZED_IDENTITY_RENAME",
        "AUTHORIZED_GUARD_OR_COMMISSIONING_DELTA",
    }
    assert certificate["common_payload"]["schema"] == "e4_pl_q1v_common_certificate_payload_v1"
    assert certificate["cross_implementation"]["mode"] == "BYTE_IDENTICAL_CANONICAL_CERTIFICATE_PAYLOAD"
    assert certificate["hard_freeze"]["pre_certificate_reauthorization_required"] is True
    assert certificate["hard_freeze"]["event"] == HARD_FREEZE_EVENT

    assert terminals["evaluation"] == "FIRST_MATCH_IN_ASCENDING_PRECEDENCE_WINS"
    rows = terminals["terminals"]
    assert [(row["precedence"], row["class"], row["id"], row["condition"]) for row in rows] == list(TERMINALS)
    assert rows[-1]["authorization"] == "AUTHORIZE_SEPARATELY_REQUESTED_AND_REVIEWED_Q1B_PLANNING_RUN_ONLY"
    assert rows[-1]["forbidden"] == ["EXECUTE_Q1B", "PRODUCTION_USE_OR_REGISTRATION"]
    assert terminals["global_effect"] == {
        "legacy_default": "ShellElement",
        "production": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "q1b_execution": "UNAUTHORIZED_FOR_EVERY_Q1V_TERMINAL",
        "q1b_plan_creation": "AUTHORIZED_ONLY_FOR_A_SEPARATELY_REQUESTED_AND_REVIEWED_PLANNING_RUN",
    }
    assert inventory["inventories_must_not_be_combined"] is True
    assert inventory["preregistration_inventory"]["count"] == 4
    assert inventory["implementation_inventory"]["count"] == 6
    assert inventory["scientific_inventory"]["count"] == 5


def test_q1v_production_boundary_and_later_stage_absences() -> None:
    extent = _load_json(REF / "e4_pl_q1v_allowed_extent.json")
    path_sets = extent["path_sets"]
    later = set(path_sets["IMPLEMENTATION20"]) | set(path_sets["CONTRACT3"]) | set(path_sets["OUTCOME11"])
    assert all(not (ROOT / relative).exists() for relative in later)
    assert not (ROOT / "docs/agent_plans/S4_E4_PL_Q1B_COMPLETION_PLAN.md").exists()
    assert not [path for parent in (ROOT / "docs", ROOT / "tests") for path in parent.rglob("*Q1B*")]

    assert subprocess.run(["git", "diff", "--quiet"], cwd=ROOT).returncode == 0
    assert subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=ROOT).returncode == 0
    changed = set(filter(None, _git("diff", "--name-only", f"{BASE_COMMIT}..HEAD").splitlines()))
    assert changed <= set(path_sets["PLAN14"])
    untracked = {
        line[3:].replace("\\", "/")
        for line in _git("status", "--porcelain=v1", "--untracked-files=all").splitlines()
        if line.startswith("?? ")
    }
    assert untracked <= set(path_sets["PLAN14"])
    forbidden = tuple(extent["forbidden_prefixes"])
    assert not [path for path in changed if path == ".gitattributes" or path.startswith(forbidden)]

    review_path = REF / "e4_pl_q1v_plan_review.json"
    assert review_path.is_file()
    review = _load_json(review_path)
    assert set(review) == {"findings", "reviewed_inputs", "reviewer_independence", "schema", "verdict"}
    assert review["schema"] == "anysolver.s4.e4-pl-q1v-plan-review-v1"
    assert review["findings"] == []
    assert review["verdict"] == PLAN_REVIEW_VERDICT
    assert review["reviewer_independence"] == {
        "mechanics_executed": False,
        "reviewer_role": "INDEPENDENT_PLAN_REVIEWER",
        "same_agent_as_packet_author": False,
    }
    expected_inputs = sorted(
        (_reviewed_row(path) for path in path_sets["PLAN14"] if path != review_path.relative_to(ROOT).as_posix()),
        key=lambda row: row["path"],
    )
    assert review["reviewed_inputs"] == expected_inputs
