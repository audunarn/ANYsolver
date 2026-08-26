"""Authority and strict-schema tests for the corrected S3/Q4 burn-in."""

from __future__ import annotations

import ast
import copy
import datetime as dt
import hashlib
import importlib.util
import io
import json
import os
import re
from pathlib import Path
import py_compile
import subprocess
import sys
import threading
import time

import pytest


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "docs" / "reference_cases"
CONTRACT_PATH = REFERENCE / "e4_pl_s3_q4_burnin_contract.json"
VALIDATOR_PATH = REFERENCE / "e4_pl_s3_q4_burnin.py"
CONTRACT_SHA256 = "d33b307ba3b475d5e6f70f20323cbb1a99fdde0ee3438dac490ee36c0ab98527"
ATTEMPT_5_CONTRACT_SHA256 = (
    "519b24c97f7a3953457922aa08514efd59e5aacfc26843c1765988e79cc1842c"
)
RESOURCE_MANAGER = Path(r"C:\Github\.resource-manager")
FINAL_FREEZE = Path(r"C:\Github\ANYsolver\.perf2-worktrees\s3-e4-pl-final-freeze")
ANYFEM_FREEZE = Path(
    r"C:\Github\ANYsolver\.perf2-worktrees\anyfem-e4-pl-default-routing"
)
CORRECTION_OUTPUT_ROOT = Path(
    r"C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease\s3-q4-final-freeze-correction-10"
)
FAILED_ATTEMPT_1_REQUEST_IDS = [
    "228852e559ba4adca2cfd8cffd2a98c0",
    "0adced21fef64846b26a7aef9285c10c",
    "7ae6f9be76d941909513f06adb250d2c",
    "c3873e15cbb748c3839b5e383db72920",
    "66ffe2ec6cee49cba3e804305e6f3808",
    "1f2ce7ef17e94135b6be2f62d1980e5d",
]
FAILED_ATTEMPT_2_REQUEST_IDS = [
    "03a5bbc54f8543b4af149539d1c02e06",
    "9b256cbbb8f6433fb5b0783f102de532",
    "62b1ec5324f64da0bab514a477eb692f",
    "6a5649d0185744ba8bc4f5da98de0609",
    "4e8803b0cc574e6889eec206b7617aca",
    "10996f7e57524fffa1e52cebd8cc5317",
]
FAILED_ATTEMPT_3_REQUEST_IDS = [
    "e0d90dd10caf456db0315c7ea8e4365e",
    "7058ea94c6514add9095fb8d8bd9a667",
    "83ff76c26e2746a6b00789d79bc509af",
    "51ac0a751d3548899f5ec4af30ea32cd",
    "5000f2041b3742dfb706b94f18592ca5",
    "363a81c40ad64c218aafde4c9e36fd48",
]
FAILED_ATTEMPT_4_REQUEST_IDS = [
    "5c8dd384914c4f7cac6a628a658ce3c9",
    "74475e0ae7444fc4b4a48e25f4400ba5",
    "de953b708c9b4ff5bf96963d74e5cc3a",
    "150ebb3da109449eb16e4a21714c8ba3",
    "3b5c383d85664da99d60d4f8d65456ba",
    "9451d872c7554a8aa764d8496952a9f5",
]
FAILED_ATTEMPT_5_REQUEST_IDS = [
    "fa0a053dbd144a15b65e6f63d1abd81c",
    "bac1d19b20574f69a74e2313973e7f33",
    "2b34ad0ce56d49579405e8431f4a47d1",
    "1353d866827648b88e718f2134a26fc5",
    "020582eaea1e4633a29abc853a2647dc",
    "15205bbf29a54b2abb4289a5fcb02379",
]
FAILED_ATTEMPT_6_REQUEST_IDS = [
    "31973767658f492ea0b7f376d59399df",
    "ec8740b65b9e45c5a803a718372b91c4",
    "d07ea2cee1224e26bc8c1aa0c5215e64",
    "0193fe79ba67489aa63af05cf6e23780",
    "eb4ac0c0d9cf46a7be4be22a59faffa5",
    "fdf28a8c7eda4d6faf6cb359561042a4",
]
FAILED_ATTEMPT_7_REQUEST_IDS = [
    "43fd3902318c41bab21aa0ea851bbbb3",
    "f8586b30ae12448498bfe104b3776f01",
    "06a261a4e43549acb33449d6ef455644",
    "435ffa6e24b84371ba9be0f41128c22e",
    "535cb95402874b5b8dfe32a912db20e4",
    "a024744a6f674ebba9a7d6028434e1d8",
]
FAILED_ATTEMPT_8_REQUEST_IDS = [
    "c2f3383ea7ab4702bb9107c010afa826",
    "0a1f61046a4e4a8a8857f191b60b87f6",
    "dc3c9442dfd547dda5cd86854a541253",
    "8142bd76fe494f34886f5b0f8124efd0",
    "570f8fba9c9544a9989ae71400688794",
    "1dc0401d62b04e959d6cb9424db17a54",
]
FAILED_ATTEMPT_9_REQUEST_IDS = [
    "99c2fcc3c6e84c7c99408023e5dc33a4",
    "5c7e14b9ec54493eab0c07b65b9ea060",
    "66beb32c09804696894ad948f6af1a03",
    "34d8eebb21814cd68968940bbe8eb54c",
    "227de96509e445f1acdbb70f531dee73",
    "701c043879b0481180926b890ae1571d",
]
FAILED_ATTEMPT_10_REQUEST_IDS = [
    "7a0b6b26646d42f8b6a51787e47dc205",
    "4585253af140476fae32c9953926519b",
    "3bf2afed4d324947ad17a390a607bf00",
    "1e1de0b84cb2408aae25426aa95e87fa",
    "98ff7f767fbd4c2da1d9f96d2d572a8d",
    "ce9f73f7f5194cbcb138c157e47f7964",
]
CURRENT_REQUEST_IDS = [
    "332d8d4192e247859d73810dd4ef5bcb",
    "41092897ba884ef39e015cefc451de39",
    "48f2afd41cf946fb9671871e61402f3d",
    "a8d35183b8b84d89b9d95103cf7c60d8",
    "f3f14c97691d494bae9e9834b112252b",
    "8238ffbc8b0f457f808ce3cef0e20eca",
]
CURRENT_REQUEST_FILE_RECORDS = [
    {
        "bytes": 1358,
        "sha256": "c3ea8c0aeec8c0b4427261b677887b7e21bde568ce336ce83b1385287c8353be",
    },
    {
        "bytes": 1010,
        "sha256": "0051837077c684e3a0041233aa653c445ad1647762508609f657d42040e7e936",
    },
    {
        "bytes": 1272,
        "sha256": "2ebca9c468834135e5c50e1d96d9b445ebbe623c471c818c93da6da3c5ba6d3f",
    },
    {
        "bytes": 1358,
        "sha256": "ac5caaa14feba568afbe4badbdbebfcb14dc2f12f275a728ae5085ebb702c3b0",
    },
    {
        "bytes": 1010,
        "sha256": "8ac8114f3e1247c3a3adef9362614f3e318a418819c29129dcd28b111a04de23",
    },
    {
        "bytes": 1272,
        "sha256": "e66407de83d31556aa3b8972afeb50c01c534375e358a54d4241106b77a87276",
    },
]

sys.path.insert(0, str(REFERENCE))
import e4_pl_s3_q4_burnin as burnin
import e4_pl_s3_q4_process_runner as process_runner

process_runner.burnin = burnin


INITIAL_PATHS = [
    "docs/reference_cases/e4_pl_s3_formulation_contract.json",
    "docs/reference_cases/e4_pl_s3_mixed_mesh_qualification_contract.json",
    "docs/reference_cases/e4_pl_s3_mixed_mesh_smoke_input.json",
    "scripts/run_e4_pl_burnin_gate.py",
    "src/anysolver/__init__.py",
    "src/anysolver/_qualified_authority_epoch.py",
    "src/anysolver/algebraic_dynamics.py",
    "src/anysolver/arc_length.py",
    "src/anysolver/assembly.py",
    "src/anysolver/boundary.py",
    "src/anysolver/buckling.py",
    "src/anysolver/current_state_tangent.py",
    "src/anysolver/dynamics.py",
    "src/anysolver/e4_pl_element.py",
    "src/anysolver/e4_pl_s3_element.py",
    "src/anysolver/e4_pl_s3_state.py",
    "src/anysolver/elements.py",
    "src/anysolver/fe_core.py",
    "src/anysolver/matrix_assembly.py",
    "src/anysolver/modal.py",
    "src/anysolver/nonlinear_performance.py",
    "src/anysolver/nonlinear_restart.py",
    "src/anysolver/nonlinear_state.py",
    "src/anysolver/nonlinear_static.py",
    "src/anysolver/recovery.py",
    "src/anysolver/recovery_batches.py",
    "src/anysolver/s3_reference_batch.py",
    "src/anysolver/shell_sections.py",
    "tests/test_e4_pl_burnin.py",
    "tests/test_e4_pl_component_snapshot_integrity.py",
    "tests/test_e4_pl_current_state_input_ownership.py",
    "tests/test_e4_pl_dormant_element.py",
    "tests/test_e4_pl_functional_constructor_policy.py",
    "tests/test_e4_pl_guarded_observations.py",
    "tests/test_e4_pl_mixed_current_state_route.py",
    "tests/test_e4_pl_orchestrator_operation_lease.py",
    "tests/test_e4_pl_planar_physical_recovery.py",
    "tests/test_e4_pl_q4_current_tangent.py",
    "tests/test_e4_pl_q4_state_lifecycle.py",
    "tests/test_e4_pl_s3_assembly_fast_total.py",
    "tests/test_e4_pl_s3_current_tangent_buckling.py",
    "tests/test_e4_pl_s3_fast_total.py",
    "tests/test_e4_pl_s3_formulation_contract.py",
    "tests/test_e4_pl_s3_generalized_nonlinear.py",
    "tests/test_e4_pl_s3_geometric_stiffness.py",
    "tests/test_e4_pl_s3_guard_persistence.py",
    "tests/test_e4_pl_s3_mixed_mesh_manifest.py",
    "tests/test_e4_pl_s3_mixed_mesh_qualification_runner.py",
    "tests/test_e4_pl_s3_modal_provenance.py",
    "tests/test_e4_pl_s3_model_bound_nonlinear_hook.py",
    "tests/test_e4_pl_s3_opt_in.py",
    "tests/test_e4_pl_s3_prestressed_modal_buckling.py",
    "tests/test_e4_pl_s3_reference_batch.py",
    "tests/test_e4_pl_s3_state_lifecycle.py",
    "tests/test_e4_pl_transient_authority.py",
    "tests/test_e4_pl_warped_qualification.py",
    "tests/test_e4_pl_workflow_parity.py",
    "tests/test_fe_solver_fracture.py",
    "tests/test_generalized_shell_sections.py",
    "tests/test_generalized_state_recovery.py",
    "tests/test_mixed_shell_quadrature_grouping.py",
    "tests/test_namespace_neutral_deepcopy.py",
    "tests/test_native_rotation_state.py",
    "tests/test_nonlinear_performance.py",
    "tests/test_nonlinear_restart_checkpoint.py",
    "tests/test_qualified_assembly_exception_precedence.py",
    "tests/test_qualified_mutation_epoch.py",
    "tests/test_qualified_q4_assembly_authority.py",
    "tests/test_solver_control_contracts.py",
]
REJECTED_PATHS = [
    "docs/reference_cases/e4_pl_s3_q4_cycle1_rejected_resource_result.json",
    "docs/reference_cases/e4_pl_s3_q4_cycle1_rejected_resource_review.json",
    "docs/reference_cases/e4_pl_s3_q4_cycle1_rejected_resource_status.json",
]
CORRECTION_PATHS = [
    "src/anysolver/current_state_tangent.py",
    "src/anysolver/recovery.py",
    "src/anysolver/s4_validity.py",
    "tests/test_e4_pl_guarded_observations.py",
    "tests/test_material_history_recovery.py",
    "tests/test_nonlinear_static_state_lifecycle.py",
    "tests/test_production_validation.py",
]


def _git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=check,
    )


def _canonical_list_hash(values: list[str]) -> str:
    raw = (json.dumps(values, sort_keys=True, separators=(",", ":")) + "\n").encode()
    return hashlib.sha256(raw).hexdigest()


def _file_record(path: Path) -> dict[str, object]:
    raw = path.read_bytes()
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def _load_contract() -> dict[str, object]:
    raw = CONTRACT_PATH.read_bytes()
    contract = burnin.strict_json_loads(raw)
    assert raw == burnin.canonical_json_bytes(contract)
    assert hashlib.sha256(raw).hexdigest() == CONTRACT_SHA256
    return contract


def _is_github_shallow_boundary() -> bool:
    if os.environ.get("GITHUB_ACTIONS") != "true":
        return False
    shallow_text = _git("rev-parse", "--git-path", "shallow").stdout.strip()
    shallow = Path(shallow_text)
    if not shallow.is_absolute():
        shallow = (ROOT / shallow).resolve()
    head = _git("rev-parse", "HEAD").stdout.strip()
    return shallow.is_file() and head in shallow.read_text(encoding="ascii").splitlines()


def _process(
    status: str = "PASS",
    *,
    command_sha256: str = "a" * 64,
    request_id: str | None = None,
    started_second: int = 0,
) -> dict[str, object]:
    if status == "NOT_RUN":
        return {"request_id": request_id, "status": status}
    return {
        "approval_snapshot": (
            {"bytes": 1, "sha256": "8" * 64} if request_id is not None else None
        ),
        "command_sha256": command_sha256,
        "elapsed_seconds": 1.25,
        "ended_at": f"2026-08-26T12:00:{started_second + 1:02d}+02:00",
        "execution_state": "EXECUTED",
        "exit_code": 0 if status == "PASS" else 1,
        "producer_sha256": burnin.load_contract()["runner_inputs"]["process_runner"][
            "sha256"
        ],
        "pending_manifest_sha256": "7" * 64 if request_id is not None else None,
        "request_id": request_id,
        "resource_lock_released": True if request_id is not None else None,
        "result": {"bytes": 1, "sha256": "b" * 64},
        "started_at": f"2026-08-26T12:00:{started_second:02d}+02:00",
        "status": status,
        "stderr": {"bytes": 0, "sha256": "c" * 64},
        "stdout": {"bytes": 1, "sha256": "d" * 64},
        "termination": {
            "child_exit_observed": True,
            "disposition": "NORMAL_EXIT",
            "tree_kill_attempted": False,
            "tree_kill_exit_code": None,
            "wall_limit_seconds": 1200,
        },
    }


def _performance_observation(contract: dict[str, object]) -> dict[str, object]:
    authority = contract["hard_gate_authority"]["performance"]
    samples = list(range(100, 111))
    summary = {
        "mad_ns": 3,
        "median_ns": 105,
        "p95_ns": 110,
        "samples_ns": samples,
    }
    return {
        "hard_gates": {
            name: {"evidence_nodes": nodes, "observed": True, "status": "PASS"}
            for name, nodes in authority["evidence_nodes"].items()
        },
        "performance_baseline": {
            "measurements": {
                name: dict(summary) for name in authority["measurement_names"]
            },
            "repetitions": authority["repetitions"],
            "schema": authority["baseline_schema"],
            "speed_claim": authority["speed_claim"],
            "warmups": authority["warmups"],
        },
        "schema": authority["observation_schema"],
    }


def _valid_result(contract: dict[str, object]) -> dict[str, object]:
    requests = contract["resource_requests"]
    cycles = []
    for cycle_number in (1, 2):
        request_rows = {
            row["lane"]: row for row in requests[f"cycle_{cycle_number}"]
        }
        lanes = {}
        for lane_index, lane in enumerate(("functional", "anyfem", "performance")):
            process = _process(
                command_sha256=request_rows[lane]["command_sha256"],
                request_id=request_rows[lane]["request_id"],
                started_second=8 + (cycle_number - 1) * 6 + lane_index * 2,
            )
            lanes[lane] = process
        cycles.append({"cycle": cycle_number, "lanes": lanes, "status": "PASS"})
    return {
        "candidate": {"clean": True, "commit": "1" * 40, "tree": "2" * 40},
        "common_lanes": {
            "additive": {
                "inventory": contract["lane_inventories"]["additive"],
                "processes": [
                    _process(
                        command_sha256=row["command_sha256"],
                        started_second=4,
                    )
                    for row in contract["non_resource_commands"]["additive"]
                ],
                "status": "PASS",
            },
            "package": {
                "inventory": contract["lane_inventories"]["package"],
                "processes": [
                    _process(
                        command_sha256=contract["non_resource_commands"]["package"][
                            "command_sha256"
                        ],
                        started_second=2,
                    )
                ],
                "status": "PASS",
            },
            "quick": {
                "inventory": contract["lane_inventories"]["quick"],
                "processes": [
                    _process(
                        command_sha256=contract["non_resource_commands"]["quick"][
                            "command_sha256"
                        ],
                        started_second=0,
                    )
                ],
                "status": "PASS",
            },
        },
        "cycles": cycles,
        "hard_gates": {
            "batch_path_equality": "PASS",
            "q4_numerical_parity": "PASS",
            "qualified_s3_opt_in": "PASS",
            "s3_default_legacy": "PASS",
            "warm_cache_reuse": "PASS",
        },
        "package_artifacts": {
            "result": {"bytes": 1, "sha256": "e" * 64},
            "wheel": {
                "bytes": 1,
                "filename": "anysolver-0.3.1-py3-none-any.whl",
                "sha256": "f" * 64,
            },
        },
        "performance_observations": [
            {"cycle": cycle, "observation": _performance_observation(contract)}
            for cycle in (1, 2)
        ],
        "production_boundary": contract["production_boundary"],
        "resource_requests": requests,
        "schema": burnin.RESULT_SCHEMA,
        "siblings": contract["sibling_authority"],
        "terminal": contract["adjudication"]["result_success_terminal"],
        "ledger_snapshots": {
            "approval": {"bytes": 1, "sha256": "8" * 64},
            "cycle_1": {"bytes": 1, "sha256": "9" * 64},
            "cycle_2": {"bytes": 1, "sha256": "a" * 64},
        },
    }


def test_contract_is_canonical_and_binds_all_local_inputs() -> None:
    contract = _load_contract()
    assert contract["study_id"] == (
        "study_e4_pl_s3_q4.corrected_opt_in_release_burnin_v11"
    )
    assert contract["authority_commit"] == {
        "exact_parent": "1e84bcacc539e90941bf718af443b8e34f283c63",
        "exact_paths": [
            "docs/reference_cases/e4_pl_s3_q4_burnin.py",
            "docs/reference_cases/e4_pl_s3_q4_burnin_contract.json",
            "docs/reference_cases/e4_pl_s3_q4_process_runner.py",
            "scripts/run_e4_pl_burnin_gate.py",
            "tests/test_e4_pl_s3_q4_burnin_authority.py",
        ],
        "path_count": 5,
        "subject": "docs: authorize corrected S3 Q4 burn-in cycles",
    }
    assert contract["background_inputs"]["attachment"] == {
        "bytes": 14355,
        "role": "BACKGROUND_ONLY_NOT_EXECUTION_AUTHORITY",
        "sha256": "c76832af87afa4a8828ba6dbad0c582b79d69934233081f0bb640fb2d250240a",
    }
    assert contract["background_inputs"]["paused_checkpoint"]["commit"] == (
        "bfdadccfb35b7f62689acb77bb071192ad831c61"
    )
    assert contract["background_inputs"]["failed_preflight_attempt"] == {
        "attempt": 1,
        "authority_commit": {
            "commit": "37f805d4679a489dcf102562a56fcdf9434d3acf",
            "subject": "docs: authorize corrected S3 Q4 burn-in cycles",
            "tree": "959065f408db44c28906c594c643012f2cce06b7",
        },
        "blocked_closeout": {
            "commit": "8a5308b1ae23818bc9a0d30d1c42699270ff6332",
            "subject": "docs: record blocked corrected S3 Q4 burn-in",
            "tree": "11b5b51d0e21405474fad3ef0dba496702e61941",
        },
        "execution_authorization_commit": {
            "commit": "ddc28e7895a374816e6178b1492c40cab1c41ff4",
            "subject": "docs: reauthorize corrected S3 Q4 burn-in execution",
            "tree": "b56e4e38542d7f186d9c7817990a0d460e1fc38f",
        },
        "external_result": {
            "bytes": 8173,
            "path": (
                r"C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease"
                r"\s3-q4-final-freeze\gate-result.json"
            ),
            "sha256": "7e94272a4cd2232ed5143dafa6a7e3d8e50b6eef043c38bdc2e66d82a7efc4ea",
            "terminal": "BLOCKED_E4_PL_S3_Q4_BURN_IN_GATE",
        },
        "failure": {
            "cause": "AUTHORITY_TEST_REUSED_LIVE_ONE_SHOT_CACHE",
            "failed": 1,
            "lane": "additive",
            "passed": 269,
            "partition": 3,
            "resource_requests_approved": False,
            "resource_requests_consumed": False,
            "test": (
                "tests/test_e4_pl_s3_q4_burnin_authority.py::"
                "test_process_runner_sanitizes_pytest_controls_and_reserves_exact_outputs"
            ),
        },
        "preserved_branch": "codex/s3-e4-pl-final-burnin-blocked-attempt-1",
        "preserved_repository_evidence": {
            "result": {
                "bytes": 8173,
                "path": "docs/reference_cases/e4_pl_s3_q4_blocked_burnin_result.json",
                "sha256": "7e94272a4cd2232ed5143dafa6a7e3d8e50b6eef043c38bdc2e66d82a7efc4ea",
            },
            "review": {
                "bytes": 536,
                "path": "docs/reference_cases/e4_pl_s3_q4_blocked_burnin_review.json",
                "sha256": "91809450d2fc7fbd9b196a85edf62877b7d93e146a848400ea73ff871f5dce81",
            },
            "status": {
                "bytes": 293,
                "path": "docs/reference_cases/e4_pl_s3_q4_blocked_burnin_status.json",
                "sha256": "5121af7c17fa5643dc0110b4132a3c16f02b813a2f81eeff72feba311521a3ff",
            },
        },
        "resource_request_disposition": "NOT_APPROVED_NOT_CONSUMED_SUPERSEDED",
        "resource_request_ids": FAILED_ATTEMPT_1_REQUEST_IDS,
        "role": "PRESERVED_BLOCKED_PREDECESSOR_ONLY",
    }
    assert contract["background_inputs"]["failed_resource_acquisition_attempt"] == {
        "attempt": 2,
        "authority_commit": {
            "commit": "ebd851755e0386e040b40ecf8d99432df6a8bc22",
            "subject": "docs: authorize corrected S3 Q4 burn-in cycles",
            "tree": "14a6b52c6866655c34866a3fdec442cd1baaf45e",
        },
        "blocked_closeout": {
            "commit": "dbf4598933d2675a13c7a8ba0932340140ed6ee6",
            "subject": "docs: record blocked corrected S3 Q4 burn-in",
            "tree": "9f556ca6208745be369626575babb01329cf9aa2",
        },
        "contract_sha256": "372e9327c215530c135aabe592f40b277ee76e57c8f5fa397b0ca1dfadcc56ba",
        "execution_authorization_commit": {
            "commit": "8fb46791963291c9aa1adc085b9b3485453362e2",
            "subject": "docs: reauthorize corrected S3 Q4 burn-in execution",
            "tree": "e938fd0fef029bc52712a443366f47334bdeef80",
        },
        "external_authority": {
            "approval_snapshot": {
                "bytes": 4466,
                "sha256": "d137e88fa512dc9e8100b990a1e1aa6c36d73e3caee1e93b6b7bdd2a1ebe0b19",
            },
            "cycle_1_terminal_snapshot": {
                "bytes": 3762,
                "sha256": "2e9c08849bb4283147c630943828ed3899696305e11d48c50a5a421cac67286e",
            },
            "cycle_2_terminal_snapshot": {
                "bytes": 3762,
                "sha256": "45990370f2742c59836e82c44f67db1cbea4a0fa541a0db33269d401c78ac593",
            },
            "output_root": (
                r"C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease"
                r"\s3-q4-final-freeze-correction-1"
            ),
        },
        "failure": {
            "cause": "POWERSHELL_SCRIPT_EXECUTION_DISABLED",
            "execution_started": False,
            "global_lock_survived": False,
            "lane": "functional",
            "phase": "RESOURCE_ACQUISITION",
            "request_id": FAILED_ATTEMPT_2_REQUEST_IDS[0],
            "resource_command_started": False,
        },
        "preserved_branch": "codex/s3-e4-pl-final-burnin-blocked-attempt-2",
        "preserved_repository_evidence": {
            "result": {
                "bytes": 3357,
                "path": "docs/reference_cases/e4_pl_s3_q4_blocked_burnin_result.json",
                "sha256": "facbfc376c4a9b5986377f47007290db4f826bf11bcd95e555b2cedd1807832c",
            },
            "review": {
                "bytes": 536,
                "path": "docs/reference_cases/e4_pl_s3_q4_blocked_burnin_review.json",
                "sha256": "9b624a32245d31a0d436648c82dcd3064b0c0e4f2fa5626ca09ac14aa54b7cb4",
            },
            "status": {
                "bytes": 293,
                "path": "docs/reference_cases/e4_pl_s3_q4_blocked_burnin_status.json",
                "sha256": "3c869356023b3b0a0687d756fb1b2f7e7ef664135b1e077b5e13a761ecc6e195",
            },
        },
        "request_disposition": "CANCELLED_NOT_RUN_SUPERSEDED",
        "request_ids": FAILED_ATTEMPT_2_REQUEST_IDS,
        "role": "PRESERVED_BLOCKED_PREDECESSOR_ONLY",
        "terminal": "BLOCKED_E4_PL_S3_Q4_BURN_IN_GATE",
    }
    assert contract["background_inputs"]["failed_common_preflight_attempt"] == {
        "attempt": 3,
        "authority_commit": {
            "commit": "2e734c526b9c99ea67f98c693a75d440a27214ee",
            "subject": "docs: authorize corrected S3 Q4 burn-in cycles",
            "tree": "2c124cde660a87bc30417638f9da96ca1e3b62fa",
        },
        "blocked_closeout": {
            "commit": "52bb927de160680dc29b4c42a8211d1d0bfeef97",
            "subject": "docs: record blocked corrected S3 Q4 burn-in",
            "tree": "7d93947f466035fb94ec415c56421bc8a5c4e81c",
        },
        "contract_sha256": "27b329d5cae84231e76cc1de8e3eefdef4b232b8a0789ca33ff7c985387a723c",
        "execution_authorization_commit": {
            "commit": "03c376db3b0867c65e76edf492a352dc45e190bc",
            "subject": "docs: reauthorize corrected S3 Q4 burn-in execution",
            "tree": "f13629a2a7b2340951a22e626a7d96ca0127d7a1",
        },
        "external_authority": {
            "output_root": (
                r"C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease"
                r"\s3-q4-final-freeze-correction-2"
            ),
            "present": False,
        },
        "failure": {
            "cause": "IGNORED_BYTECODE_CONTAMINATED_FROZEN_INPUT",
            "clean_input_guard_rejected": True,
            "input_contamination": {
                "bytes": 121473,
                "path": (
                    "docs/reference_cases/__pycache__/"
                    "e4_pl_s3_q4_burnin.cpython-313.pyc"
                ),
                "sha256": "52cbd9f41d2b274f8eaaee42123463c7fd0a5f2f02bbac144508c4c8e118bd5d",
            },
            "lane": "quick",
            "phase": "COMMON_PREFLIGHT_AUTHORITY_CHECK",
            "quick_command_started": False,
            "resource_commands_started": False,
        },
        "preserved_branch": "codex/s3-e4-pl-final-burnin-blocked-attempt-3",
        "preserved_repository_evidence": {
            "result": {
                "bytes": 1962,
                "path": "docs/reference_cases/e4_pl_s3_q4_blocked_burnin_result.json",
                "sha256": "6fab27284bc5668fdcbb05269d65341a76872fbbd3f7ca0dfb0d8d0da6af352f",
            },
            "review": {
                "bytes": 536,
                "path": "docs/reference_cases/e4_pl_s3_q4_blocked_burnin_review.json",
                "sha256": "9af6a87aa02857c218b83b1537b75944ae77887c295e59e6c6af7e13de665676",
            },
            "status": {
                "bytes": 293,
                "path": "docs/reference_cases/e4_pl_s3_q4_blocked_burnin_status.json",
                "sha256": "9498f8fbb3e7f2e569c2c1c8dbb676bbbf789b28ca03eeb51b7709b72143bcbd",
            },
        },
        "request_disposition": "NOT_APPROVED_NOT_CONSUMED_SUPERSEDED",
        "request_ids": FAILED_ATTEMPT_3_REQUEST_IDS,
        "role": "PRESERVED_BLOCKED_PREDECESSOR_ONLY",
        "terminal": "BLOCKED_E4_PL_S3_Q4_BURN_IN_GATE",
    }
    interrupted = contract["background_inputs"][
        "failed_resource_interruption_attempt"
    ]
    assert interrupted["attempt"] == 4
    assert interrupted["authority_commit"] == {
        "commit": "d7bdc8cafe714a4f8d9fd082ec05e7ed64b15a1c",
        "subject": "docs: authorize corrected S3 Q4 burn-in cycles",
        "tree": "36890750f735d36ee887a5f1d35e6dfa0becce8c",
    }
    assert interrupted["execution_authorization_commit"]["commit"] == (
        "4642b7487dc9f9db8e709f3b2e133c781a69fbc9"
    )
    assert interrupted["blocked_closeout"] == {
        "commit": "7bf87c397f11bcfb27a242bb74369cf0df3437a5",
        "subject": "docs: record blocked corrected S3 Q4 burn-in",
        "tree": "0c84054d9a060fb37aef2d6f8ddd51db46630140",
    }
    assert interrupted["request_ids"] == FAILED_ATTEMPT_4_REQUEST_IDS
    assert interrupted["failure"] == {
        "cause": "MONOLITHIC_FUNCTIONAL_GATE_EXCEEDED_USER_WALL_LIMIT",
        "completion_observed": False,
        "end_time_observed": False,
        "exit_code_observed": False,
        "lane": "functional",
        "phase": "CYCLE_1_RESOURCE_EXECUTION",
        "protocol_terminal_observed": False,
        "request_id": FAILED_ATTEMPT_4_REQUEST_IDS[0],
        "resource_command_started": True,
        "wall_limit_seconds": 1200,
        "worker_tree_confirmed_absent": True,
    }
    assert interrupted["request_disposition"] == (
        "INTERRUPTED_INCOMPLETE_FIRST_REQUEST_REMAINING_CANCELLED_NOT_RUN_SUPERSEDED"
    )
    assert interrupted["external_authority"]["interruption_checkpoint"] == {
        "bytes": 1952,
        "sha256": "c929d708c4a2dbccdf2d83184a5fb14f3c4dc364a14b231614adedb95f139fb6",
    }
    assert interrupted["preserved_repository_evidence"]["result"] == {
        "bytes": 4730,
        "path": "docs/reference_cases/e4_pl_s3_q4_blocked_burnin_result.json",
        "sha256": "8b332ad570906d98d9f705f4671b0f25ee7a4b24f1c46549eacca34176c5f7b4",
    }
    contaminated = contract["background_inputs"][
        "failed_review_contamination_attempt"
    ]
    assert contaminated["attempt"] == 5
    assert contaminated["authority_commit"] == {
        "commit": "ca0b3a5d95d336262542f317f0e207dde837197a",
        "subject": "docs: authorize corrected S3 Q4 burn-in cycles",
        "tree": "c0216f08d7613de7a22c25e1ae88fa79f3aee896",
    }
    assert contaminated["execution_authorization_commit"] == {
        "commit": "c51e5c249f4d754ee285c489b165fba78cd34c01",
        "subject": "docs: reauthorize corrected S3 Q4 burn-in execution",
        "tree": "14f6d1cd696d35ee329f4a4cdc79b39058f31e2f",
    }
    assert contaminated["blocked_closeout"] == {
        "commit": "6fa5f1e86c8b4fb91d00dce095cd4ba4a6c81e28",
        "subject": "docs: record blocked corrected S3 Q4 burn-in",
        "tree": "bfd679e4410105d5d5ab29c2e3df6dc647d826e5",
    }
    assert contaminated["contract_sha256"] == ATTEMPT_5_CONTRACT_SHA256
    assert contaminated["request_ids"] == FAILED_ATTEMPT_5_REQUEST_IDS
    assert contaminated["failure"]["cause"] == (
        "IGNORED_BYTECODE_CONTAMINATED_FROZEN_INPUT"
    )
    assert contaminated["failure"]["input_contamination"]["count"] == 5
    assert contaminated["request_disposition"] == (
        "NOT_APPROVED_NOT_CONSUMED_SUPERSEDED"
    )
    assert contaminated["preserved_repository_evidence"] == {
        "result": {
            "bytes": 2796,
            "path": "docs/reference_cases/e4_pl_s3_q4_blocked_burnin_result.json",
            "sha256": "b7b42e283e3a8ce58bd8527e567dd70e5e7829e39d33256db59d031795291090",
        },
        "review": {
            "bytes": 536,
            "path": "docs/reference_cases/e4_pl_s3_q4_blocked_burnin_review.json",
            "sha256": "5ce4294c9d8f5ce9efc53685ae57a6881b96107a593bf698c7b890281ada6ed6",
        },
        "status": {
            "bytes": 293,
            "path": "docs/reference_cases/e4_pl_s3_q4_blocked_burnin_status.json",
            "sha256": "2b28f2d0029cb5c0339d41e2978ee38e4628958c973dcd621c72b61d83e10962",
        },
    }
    git_probe = contract["background_inputs"]["failed_git_probe_review_attempt"]
    assert git_probe["attempt"] == 6
    assert git_probe["authority_commit"] == {
        "commit": "a52994945721295686d9c1776a2bdb5a9a1c7ec3",
        "subject": "docs: authorize corrected S3 Q4 burn-in cycles",
        "tree": "87d18d978d94035bc49c11a4610d2bcbc964157c",
    }
    assert git_probe["contract"] == {
        "bytes": 274979,
        "sha256": "9f7e5a2bf25ba2ed94efd1c6fbf7caec98bda48124a43466a83447846040f7f0",
    }
    assert git_probe["failure"] == {
        "cause": "SANITIZED_GATE_GIT_POLICY_OMITTED_SAFE_DIRECTORY_AND_AUTOCRLF",
        "formal_execution_started": False,
        "resource_requests_approved": False,
        "resource_requests_consumed": False,
    }
    assert git_probe["ledger_occurrences"] == 0
    assert git_probe["preserved_ref"] == (
        "codex/s3-e4-pl-final-burnin-rejected-v6-a529949"
    )
    assert git_probe["request_disposition"] == (
        "NOT_APPROVED_NOT_CONSUMED_SUPERSEDED"
    )
    assert git_probe["request_ids"] == FAILED_ATTEMPT_6_REQUEST_IDS
    assert git_probe["review_test_results"] == [
        {
            "failed": 0,
            "passed": 35,
            "reviewer_id": "codex-v6-independent-authority-review-1-a5299494",
        },
        {
            "failed": 0,
            "passed": 35,
            "reviewer_id": "codex-v6-independent-authority-review-2-a529949",
        },
    ]
    assert [review["verdict"] for review in git_probe["reviews"]] == [
        "REJECT_E4_PL_S3_Q4_BURN_IN_AUTHORITY_P1",
        "REJECT_E4_PL_S3_Q4_BURN_IN_AUTHORITY_P1",
    ]
    assert [
        review["reviewer_independence"]["reviewer_id"]
        for review in git_probe["reviews"]
    ] == [
        "codex-v6-independent-authority-review-1-a5299494",
        "codex-v6-independent-authority-review-2-a529949",
    ]
    assert all(
        review["findings"][0]["priority"] == "P1"
        for review in git_probe["reviews"]
    )
    assert git_probe["role"] == "PRESERVED_REJECTED_AUTHORITY_ONLY"
    assert git_probe["terminal"] == (
        "BLOCKED_E4_PL_S3_Q4_BURN_IN_AUTHORITY_REVIEW"
    )
    ci_partition = contract["background_inputs"][
        "failed_ci_partition_review_attempt"
    ]
    assert ci_partition["attempt"] == 7
    assert ci_partition["authority_commit"] == {
        "commit": "f9fa288a0b19b63f3d51d1e5e0eaab64790b14d8",
        "subject": "docs: authorize corrected S3 Q4 burn-in cycles",
        "tree": "3942ae13d497ce3353d900b4d46502167d8b68c0",
    }
    assert ci_partition["contract"] == {
        "bytes": 279259,
        "sha256": "c779a03ee08db6f9f8696a804cab31fa7da0d73bc6841e1fe483bd9c741de79c",
    }
    assert ci_partition["failure"] == {
        "cause": "BOUNDED_CI_P01_NONFUNCTIONAL_PARTITION_EMPTY",
        "formal_execution_started": False,
        "resource_requests_approved": False,
        "resource_requests_consumed": False,
    }
    assert ci_partition["ledger_occurrences"] == 0
    assert ci_partition["preserved_ref"] == (
        "codex/s3-e4-pl-final-burnin-rejected-v7-f9fa288"
    )
    assert ci_partition["request_disposition"] == (
        "NOT_APPROVED_NOT_CONSUMED_SUPERSEDED"
    )
    assert ci_partition["request_ids"] == FAILED_ATTEMPT_7_REQUEST_IDS
    assert ci_partition["review_test_results"] == [
        {
            "failed": 0,
            "passed": 35,
            "reviewer_id": "codex-v7-independent-authority-review-1-f9fa288",
        },
        {
            "failed": 0,
            "passed": 35,
            "reviewer_id": "codex-v7-independent-authority-review-2-f9fa288",
        },
    ]
    assert [review["verdict"] for review in ci_partition["reviews"]] == [
        "ACCEPT_E4_PL_S3_Q4_BURN_IN_AUTHORITY_NO_P0_P1",
        "REJECT_E4_PL_S3_Q4_BURN_IN_AUTHORITY_P1",
    ]
    assert ci_partition["reviews"][0]["findings"] == []
    assert ci_partition["reviews"][1]["findings"] == [
        {
            "evidence": (
                "The independently collected current extent is 1,036 functional plus "
                "871 nonfunctional nodes, totaling 1,907. However, "
                "nonfunctional_buckets[0] is empty, so P01 contains only its one "
                "functional node, while CI_SHARD_NODE_AUTHORITIES requires P01 to "
                "contain 93 nodes. _run_bounded_ci therefore deterministically raises "
                "before launching any CI worker."
            ),
            "location": "scripts/run_e4_pl_burnin_gate.py:3630",
            "priority": "P1",
            "summary": (
                "The bounded CI shard assignment cannot satisfy its frozen P01 authority."
            ),
        }
    ]
    assert ci_partition["role"] == "PRESERVED_REJECTED_AUTHORITY_ONLY"
    assert ci_partition["terminal"] == (
        "BLOCKED_E4_PL_S3_Q4_BURN_IN_AUTHORITY_REVIEW"
    )
    sibling_hygiene = contract["background_inputs"][
        "failed_sibling_hygiene_preflight_attempt"
    ]
    assert sibling_hygiene["attempt"] == 8
    assert sibling_hygiene["authority_commit"] == {
        "commit": "880a75a672c9dd32b774aab819a08475af7ba05c",
        "subject": "docs: authorize corrected S3 Q4 burn-in cycles",
        "tree": "e2964ddfa4e1c5291c0f95ba8edc0df0f8fbf231",
    }
    assert sibling_hygiene["execution_authorization_commit"] == {
        "commit": "da12d8264338ff80cfe54540aaa233565dcaaae0",
        "subject": "docs: reauthorize corrected S3 Q4 burn-in execution",
        "tree": "bece1cb5eeb0d49b46d50edff5faf10ed567c146",
    }
    assert sibling_hygiene["blocked_closeout"] == {
        "commit": "0a893a39ffefeebbeab0dfe31f7ac84cd2c91b25",
        "subject": "docs: record blocked corrected S3 Q4 burn-in",
        "tree": "2b8b3d7ddb5991b056f03483d979d75d0445ec4b",
    }
    assert sibling_hygiene["contract"] == {
        "bytes": 282481,
        "sha256": "2301bcdeffc85f4e6c9c6242591eca9c81af1bcdebbd9da231cf329c908347e2",
    }
    assert sibling_hygiene["failure"] == {
        "cause": "IGNORED_BYTECODE_CONTAMINATED_FROZEN_SIBLING_INPUT",
        "clean_input_guard_rejected": True,
        "coordinator_exit_code": 1,
        "input_contamination": {
            "complete_file_hashes_available": False,
            "reported_paths": [
                "src/anyfileio/__pycache__/__init__.cpython-313.pyc",
                "src/anyfileio/__pycache__/_semantic_dependencies.cpython-313.pyc",
                "src/anyfileio/__pycache__/cad.cpython-313.pyc",
            ],
            "repository": (
                r"C:\Github\ANYsolver\.perf2-worktrees\s3-q4-anyfileio-9b1e5ad"
            ),
        },
        "lane": "quick",
        "phase": "COMMON_PREFLIGHT_AUTHORITY_CHECK",
        "post_abort_hygiene": {
            "all_six_frozen_repositories_clean_including_ignored": True,
            "generated_bytecode_removed_only": True,
        },
        "quick_command_started": False,
        "resource_commands_started": False,
    }
    assert sibling_hygiene["external_authority"] == {
        "gate_result": {
            "bytes": 4382,
            "path": (
                r"C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease"
                r"\s3-q4-final-freeze-correction-7\gate-result.json"
            ),
            "sha256": "a752ede1659f9abe57fe1bfc5a41d28134f36627d0a274695dea8fd91dae5c3f",
        },
        "output_root": (
            r"C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease"
            r"\s3-q4-final-freeze-correction-7"
        ),
    }
    assert sibling_hygiene["preserved_branch"] == (
        "codex/s3-e4-pl-final-burnin-blocked-attempt-8"
    )
    assert sibling_hygiene["preserved_repository_evidence"] == {
        "result": {
            "bytes": 4382,
            "path": "docs/reference_cases/e4_pl_s3_q4_blocked_burnin_result.json",
            "sha256": "a752ede1659f9abe57fe1bfc5a41d28134f36627d0a274695dea8fd91dae5c3f",
        },
        "review": {
            "bytes": 536,
            "path": "docs/reference_cases/e4_pl_s3_q4_blocked_burnin_review.json",
            "sha256": "838a25cb80357c5d995fa40a48735cc2e0eff37d8886bcbb3031f427e94d3746",
        },
        "status": {
            "bytes": 293,
            "path": "docs/reference_cases/e4_pl_s3_q4_blocked_burnin_status.json",
            "sha256": "949bed07b708815a839f6f51e91b329ffb5292217186bc24329158c3d2076414",
        },
    }
    assert sibling_hygiene["request_disposition"] == (
        "NOT_APPROVED_NOT_CONSUMED_SUPERSEDED"
    )
    assert sibling_hygiene["request_ids"] == FAILED_ATTEMPT_8_REQUEST_IDS
    assert sibling_hygiene["role"] == "PRESERVED_BLOCKED_PREDECESSOR_ONLY"
    assert sibling_hygiene["terminal"] == "BLOCKED_E4_PL_S3_Q4_BURN_IN_GATE"
    recursive_ci = contract["background_inputs"][
        "failed_recursive_ci_quick_preflight_attempt"
    ]
    assert recursive_ci["attempt"] == 9
    assert recursive_ci["authority_commit"] == {
        "commit": "9109a820dd45d35839c50f27d75593fd9caadadb",
        "subject": "docs: authorize corrected S3 Q4 burn-in cycles",
        "tree": "34c299b47dda6215e0d0022efda7b005946c22c7",
    }
    assert recursive_ci["execution_authorization_commit"] == {
        "commit": "06182d7bcfae40a0b0fad827f3b494b53eec0f0a",
        "subject": "docs: reauthorize corrected S3 Q4 burn-in execution",
        "tree": "3eed0a4a527364177e6f7a6df108980e26a7903c",
    }
    assert recursive_ci["correction_commit"] == {
        "commit": "02a3b101aa5d1d7877eef7b15b6349210e0441cc",
        "subject": "test: make S3 Q4 CI extent check process-free",
        "tree": "df3af43a29321a49a119e1bcc1386d1ef92d7bb7",
    }
    assert recursive_ci["contract"] == {
        "bytes": 285245,
        "sha256": "9cdea010543f4b6cd712310f713c199626018f1b135f492fca121d07ec31d6f4",
    }
    assert recursive_ci["external_authority"] == {
        "output_root": (
            r"C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease"
            r"\s3-q4-final-freeze-correction-8"
        ),
        "partial_tree": {
            "captured_at": "2026-08-26T19:13:19.8920987+02:00",
            "file_count": 185,
            "file_graph_bytes": 40223,
            "file_graph_sha256": (
                "b4e823d8c705834aa36000f265eec03700976cdd6a1c3ad1b77a3ff980fa51f1"
            ),
            "quick_output_file_count": 0,
            "quick_output_reserved": True,
            "started_at": "2026-08-26T18:58:15.9476579+02:00",
            "total_bytes": 14418287,
        },
    }
    assert recursive_ci["failure"] == {
        "canonical_process_manifest_created": False,
        "cause": "OUTDATED_QUICK_TEST_PATCH_LAUNCHED_RECURSIVE_COMPLETE_CI_WAVE",
        "formal_cycle_started": False,
        "phase": "COMMON_QUICK_PREFLIGHT",
        "quick_command_started": True,
        "resource_requests_approved": False,
        "resource_requests_consumed": False,
        "termination": "USER_DIRECTED_EFFICIENCY_ABORT_AFTER_ROOT_CAUSE_CONFIRMED",
        "worker_tree_confirmed_absent": True,
    }
    assert recursive_ci["request_disposition"] == (
        "NOT_APPROVED_NOT_CONSUMED_SUPERSEDED"
    )
    assert recursive_ci["request_ids"] == FAILED_ATTEMPT_9_REQUEST_IDS
    assert recursive_ci["role"] == "PRESERVED_BLOCKED_PREDECESSOR_ONLY"
    assert recursive_ci["terminal"] == "BLOCKED_E4_PL_S3_Q4_BURN_IN_GATE"
    functional_cleanliness = contract["background_inputs"][
        "failed_v10_functional_cleanliness_attempt"
    ]
    assert set(functional_cleanliness) == {
        "attempt",
        "authority_commit",
        "blocked_closeout",
        "contract",
        "execution_authorization_commit",
        "external_authority",
        "failure",
        "preserved_branch",
        "preserved_repository_evidence",
        "request_disposition",
        "request_ids",
        "role",
        "terminal",
    }
    assert functional_cleanliness["attempt"] == 10
    assert functional_cleanliness["authority_commit"] == {
        "commit": "f2feeead59bc79471652bf562c3862533e213518",
        "subject": "docs: authorize corrected S3 Q4 burn-in cycles",
        "tree": "fcdfd4db6d5016430dd0ddbf3dc7f85c955d38e7",
    }
    assert functional_cleanliness["execution_authorization_commit"] == {
        "commit": "5244822799feb8a73de636b076099e03a1d68e0b",
        "subject": "docs: reauthorize corrected S3 Q4 burn-in execution",
        "tree": "1079fa8d8703db821b3ab322a489e4b9c55dcf73",
    }
    assert functional_cleanliness["blocked_closeout"] == {
        "commit": "1e84bcacc539e90941bf718af443b8e34f283c63",
        "subject": "docs: record blocked corrected S3 Q4 burn-in",
        "tree": "5c2c9c3256267882b432fc9173de24c131022cb2",
    }
    assert functional_cleanliness["failure"] == {
        "cause": "IGNORED_EMPTY_SCRATCH_DIRECTORIES_ESCAPED_PREAPPROVAL_CLEAN_GUARD",
        "clean_cycles_recorded": 0,
        "failed_request": {
            "execution_state": "EXECUTED_ONCE",
            "request_id": FAILED_ATTEMPT_10_REQUEST_IDS[0],
            "status": "COMPLETED_FAIL",
        },
        "other_requests": {
            "acquired": False,
            "request_ids": FAILED_ATTEMPT_10_REQUEST_IDS[1:],
            "status": "CANCELLED_NOT_RUN",
        },
        "phase": "CYCLE_1_FUNCTIONAL_SOURCE_STATUS_BEFORE_SHARD_LAUNCH",
        "recovered_cleanliness": {
            "entries": [
                ".pytest_tmp_beam_validity/",
                ".pytest_tmp_capacity_workflow/",
                ".pytest_tmp_element_qualification/",
                ".pytest_tmp_fe_verification/",
                ".pytest_tmp_fe_verification_family/",
                ".pytest_tmp_mass_modal/",
                ".pytest_tmp_plasticity_qualification/",
                ".pytest_tmp_s4_validity/",
                "reports/external_references/",
            ],
            "entries_verified_empty": True,
            "entries_verified_non_reparse": True,
            "post_status": {
                "bytes": 0,
                "sha256": hashlib.sha256(b"").hexdigest(),
            },
            "removal": "EXACT_EMPTY_LEAVES_NONRECURSIVE",
        },
        "shards_started": 0,
        "source_status": {
            "bytes": 301,
            "sha256": "827045256df721e866640ffd7abde585f437a5a4f36b1575b57c15d7f3c1b124",
        },
    }
    assert functional_cleanliness["request_ids"] == FAILED_ATTEMPT_10_REQUEST_IDS
    assert functional_cleanliness["preserved_branch"] == (
        "codex/s3-e4-pl-final-burnin-blocked-attempt-10"
    )
    assert functional_cleanliness["request_disposition"] == (
        "ONE_COMPLETED_FAIL_FIVE_CANCELLED_NOT_RUN_SUPERSEDED"
    )
    assert functional_cleanliness["role"] == "PRESERVED_BLOCKED_PREDECESSOR_ONLY"
    assert functional_cleanliness["terminal"] == "BLOCKED_E4_PL_S3_Q4_BURN_IN_GATE"
    assert Path(contract["non_resource_commands"]["output_root"]) == CORRECTION_OUTPUT_ROOT
    environment_guard = contract["execution"]["environment_guard"]
    assert Path(environment_guard["python_cache_root"]) == (
        CORRECTION_OUTPUT_ROOT / "python-cache"
    )
    assert Path(environment_guard["numba_cache_root"]) == (
        CORRECTION_OUTPUT_ROOT / "numba-cache"
    )
    old_output_root = r"C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease\s3-q4-final-freeze"
    commands = [
        contract["non_resource_commands"]["package"]["command"],
        *(row["command"] for row in contract["non_resource_commands"]["additive"]),
    ]
    assert all(str(CORRECTION_OUTPUT_ROOT) in command for command in commands)
    assert all(old_output_root + "\\" not in command for command in commands)
    attempt2_output_root = contract["background_inputs"][
        "failed_resource_acquisition_attempt"
    ]["external_authority"]["output_root"]
    assert all(attempt2_output_root + "\\" not in command for command in commands)
    attempt3_output_root = contract["background_inputs"][
        "failed_common_preflight_attempt"
    ]["external_authority"]["output_root"]
    assert all(attempt3_output_root + "\\" not in command for command in commands)
    attempt4_output_root = contract["background_inputs"][
        "failed_resource_interruption_attempt"
    ]["external_authority"]["output_root"]
    assert all(attempt4_output_root + "\\" not in command for command in commands)
    attempt10_output_root = functional_cleanliness["external_authority"]["output_root"]
    assert all(attempt10_output_root + "\\" not in command for command in commands)
    for incident_name in (
        "failed_preflight_attempt",
        "failed_resource_acquisition_attempt",
        "failed_common_preflight_attempt",
        "failed_resource_interruption_attempt",
        "failed_review_contamination_attempt",
        "failed_sibling_hygiene_preflight_attempt",
        "failed_v10_functional_cleanliness_attempt",
    ):
        incident = contract["background_inputs"][incident_name]
        blocked_commit = incident["blocked_closeout"]["commit"]
        if _git("cat-file", "-e", f"{blocked_commit}^{{commit}}", check=False).returncode:
            assert _is_github_shallow_boundary()
            continue
        for record in incident["preserved_repository_evidence"].values():
            completed = subprocess.run(
                ["git", "show", f"{blocked_commit}:{record['path']}"],
                cwd=ROOT,
                capture_output=True,
                check=True,
            )
            assert {
                "bytes": len(completed.stdout),
                "sha256": hashlib.sha256(completed.stdout).hexdigest(),
            } == {"bytes": record["bytes"], "sha256": record["sha256"]}
    successor = contract["execution_authorization_commit"]
    assert successor["exact_parent_role"] == "DERIVED_AUTHORITY_COMMIT"
    assert successor["subject"] == "docs: reauthorize corrected S3 Q4 burn-in execution"
    assert successor["exact_paths"] == [*successor["review_paths"], successor["approval_path"]]
    assert successor["review_hygiene"] == {
        "candidate_worktree_mode": "DETACHED_CLEAN_REVIEW_WORKTREE",
        "post_review_status": "EXACTLY_MATCHES_PRE_REVIEW",
        "pre_review_status": "CLEAN_INCLUDING_IGNORED",
        "pytest_basetemp": "FRESH_EXTERNAL_DIRECTORY",
        "python_cache_prefix": "FRESH_EXTERNAL_DIRECTORY",
        "python_invocation": ["python", "-B", "-m", "pytest"],
        "reviewers_must_not_modify_candidate": True,
        "schema": "anysolver.e4-pl-s3-q4-review-hygiene-v2",
    }
    for record in contract["historical_inputs"].values():
        path = ROOT / record["path"]
        assert _file_record(path) == {
            "bytes": record["bytes"],
            "sha256": record["sha256"],
        }
    for name, record in contract["runner_inputs"].items():
        path = ROOT / record["path"]
        if name == "burnin_runner":
            assert burnin.validate_eol_bound_input(
                path,
                record,
                expected_relative_path="scripts/run_e4_pl_burnin_gate.py",
                location="$contract.runner_inputs.burnin_runner",
            ) == record
        else:
            assert _file_record(path) == {
                "bytes": record["bytes"],
                "sha256": record["sha256"],
            }
    manager = contract["external_authority"]["resource_manager"]
    assert Path(manager["root"]) == RESOURCE_MANAGER
    if RESOURCE_MANAGER.is_dir():
        for name in ("acquire", "release"):
            record = manager[name]
            assert _file_record(RESOURCE_MANAGER / record["filename"]) == {
                "bytes": record["bytes"],
                "sha256": record["sha256"],
            }
    else:
        assert os.environ.get("GITHUB_ACTIONS") == "true"
    environment_guard = contract["execution"]["environment_guard"]
    for name in ("git", "git_engine", "powershell", "python"):
        authority = environment_guard[name]
        executable = Path(authority["path"])
        if executable.is_file():
            assert _file_record(executable) == {
                "bytes": authority["bytes"],
                "sha256": authority["sha256"],
            }
            if name == "python":
                assert executable.resolve() == Path(sys.executable).resolve()
        else:
            assert os.environ.get("GITHUB_ACTIONS") == "true"
    source = VALIDATOR_PATH.read_text(encoding="utf-8")
    imported_roots = {
        node.names[0].name.split(".")[0]
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Import)
    } | {
        (node.module or "").split(".")[0]
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.ImportFrom)
    }
    assert imported_roots <= {
        "__future__",
        "argparse",
        "datetime",
        "hashlib",
        "json",
        "math",
        "os",
        "pathlib",
        "re",
        "stat",
        "statistics",
        "subprocess",
        "typing",
    }


def test_candidate_chain_and_authority_extent_are_exact() -> None:
    contract = _load_contract()
    chain_rows = (
        (contract["candidate_chain"]["initial_freeze"], INITIAL_PATHS),
        (contract["candidate_chain"]["rejected_resource_evidence"], REJECTED_PATHS),
        (contract["candidate_chain"]["correction"], CORRECTION_PATHS),
    )
    if any(
        _git("cat-file", "-e", f"{row['commit']}^{{commit}}", check=False).returncode
        for row, _paths in chain_rows
    ):
        assert _is_github_shallow_boundary()
        return
    for row, expected_paths in chain_rows:
        metadata = _git(
            "show", "-s", "--format=%H%n%T%n%P%n%s", row["commit"]
        ).stdout.splitlines()
        assert metadata == [
            row["commit"],
            row["tree"],
            row["exact_parent"],
            row["subject"],
        ]
        actual_paths = _git(
            "diff", "--name-only", row["exact_parent"], row["commit"]
        ).stdout.splitlines()
        assert actual_paths == expected_paths
        assert len(actual_paths) == row["path_count"]
        assert _canonical_list_hash(actual_paths) == row["path_inventory_sha256"]
    authority = contract["authority_commit"]
    authority_commits = _git(
        "log",
        "-1",
        "--format=%H",
        "--",
        "docs/reference_cases/e4_pl_s3_q4_burnin_contract.json",
    ).stdout.splitlines()
    assert len(authority_commits) == 1
    authority_commit = authority_commits[0]
    authority_metadata = _git(
        "show", "-s", "--format=%P%n%s", authority_commit
    ).stdout.splitlines()
    assert authority_metadata == [authority["exact_parent"], authority["subject"]]
    authority_paths = _git(
        "diff", "--name-only", authority["exact_parent"], authority_commit
    ).stdout.splitlines()
    assert authority_paths == authority["exact_paths"]
    assert len(authority_paths) == authority["path_count"]


def test_lane_inventory_hashes_are_current_and_extended_is_excluded() -> None:
    contract = _load_contract()
    spec = importlib.util.spec_from_file_location(
        "s3_q4_burnin_runner_inventory",
        ROOT / "scripts" / "run_e4_pl_burnin_gate.py",
    )
    assert spec is not None and spec.loader is not None
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    inventory = runner.inventory()
    gate_inventory = runner.gate_inventories()
    for lane in ("quick", "functional", "performance", "extended", "additive"):
        expected = contract["lane_inventories"][lane]
        assert len(inventory[lane]) == expected["count"]
        assert _canonical_list_hash(inventory[lane]) == expected["sha256"]
    for lane in ("package", "anyfem"):
        expected = contract["lane_inventories"][lane]
        assert len(gate_inventory[lane]) == expected["count"]
        assert _canonical_list_hash(gate_inventory[lane]) == expected["sha256"]
    assert contract["lane_inventories"]["extended"]["execution"] == (
        "EXCLUDED_OPTIONAL_HISTORICAL_DIAGNOSTICS"
    )
    for protected in (
        "tests/test_e4_pl_s3_mixed_eigen_performance.py",
        "tests/test_e4_pl_s3_mixed_structural_qualification.py",
    ):
        assert protected in inventory["extended"]
        assert protected not in inventory["additive"]
    for nodes in contract["hard_gate_authority"]["s3"].values():
        for node in nodes:
            assert node.split("::", 1)[0] in inventory["additive"]
    for nodes in contract["hard_gate_authority"]["performance"][
        "evidence_nodes"
    ].values():
        for node in nodes:
            assert node.split("::", 1)[0] in inventory["quick"]
    command_table = burnin._non_resource_command_table(contract)
    assert command_table["additive"] == [
        row["command_sha256"] for row in contract["non_resource_commands"]["additive"]
    ]
    assert all(
        "mixed_structural_qualification" not in row["command"]
        and "mixed_eigen_performance" not in row["command"]
        for row in contract["non_resource_commands"]["additive"]
    )


def test_functional_wave_is_exact_parallel_and_hard_bounded() -> None:
    contract = _load_contract()
    wave = contract["functional_wave"]
    assert wave["schema"] == "anysolver.e4-pl-s3-q4-functional-wave-v2"
    assert wave["source"] == {
        "archive_filename": "functional-wave-source.tar",
        "commit_role": "EXECUTION_AUTHORIZATION_COMMIT",
        "file_graph_filename": "functional-wave-source-file-graph.json",
        "file_graph_schema": (
            "anysolver.e4-pl-s3-q4-functional-wave-file-graph-v1"
        ),
        "tree_role": "EXECUTION_AUTHORIZATION_TREE",
    }
    execution = wave["execution"]
    assert execution["max_workers"] == 4
    assert execution["numerical_library_threads"] == 1
    assert execution["automatic_retry"] is False
    assert execution["internal_deadline_seconds"] == 830
    assert execution["environment"] == {
        "NUMBA_NUM_THREADS": "1",
        "scope": "FUNCTIONAL_SHARDS_ONLY",
    }
    assert execution["selector_safety"] == {
        "extra_nodes": "REJECT",
        "full_module_selector": (
            "ONLY_WHEN_ALL_COLLECTED_MODULE_NODES_ARE_SHARD_OWNED"
        ),
        "missing_nodes": "REJECT",
        "split_module_selector": "EXACT_NODE_IDS_ONLY",
    }
    assert execution["raw_observability"] == {
        "canonical_timings": False,
        "lifecycle_progress": True,
        "pytest_durations": True,
    }
    assert (
        execution["unproven_tree_action"]
        == "WAIT_FOR_OUTER_RESOURCE_TREE_TERMINATION"
    )
    assert execution["source_mode"] == "GIT_ARCHIVE_HEAD"
    assert execution["source_status_must_match"] is True
    assert execution["artifact_routing"] == {
        "aggregate_filename": "functional-wave-aggregate.json",
        "archive_filename": "functional-wave-source.tar",
        "directory_name": "functional-wave",
        "raw_diagnostics_filename": "functional-wave-raw-diagnostics.json",
        "shard_directory_prefix": "shard-",
        "source_directory_name": "source",
    }

    manifest = wave["manifest"]
    assert manifest["module_count"] == 85
    assert manifest["node_count"] == 1036
    assert manifest["collection_artifact"] == {
        "bytes": 116046,
        "sha256": "244132e6294f3dc37f5bf865bd800c7402d9ff6b3300af670ca954ad24bb5c15",
    }
    spec = importlib.util.spec_from_file_location(
        "s3_q4_wave_inventory", ROOT / "scripts" / "run_e4_pl_burnin_gate.py"
    )
    assert spec is not None and spec.loader is not None
    gate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate)
    modules = gate.inventory()["functional"]
    assert manifest["modules"] == modules
    assert manifest["modules_sha256"] == _canonical_list_hash(modules)
    full_nodes = manifest["full_node_ids"]
    assert len(full_nodes) == len(set(full_nodes)) == manifest["node_count"]
    assert manifest["full_node_ids_sha256"] == _canonical_list_hash(full_nodes)
    assert all(node.split("::", 1)[0] in modules for node in full_nodes)
    shards = manifest["shards"]
    assert [shard["shard_id"] for shard in shards] == [
        "P01",
        "P02",
        "P03",
        "P04",
    ]
    assert [shard["node_count"] for shard in shards] == [1, 362, 361, 312]
    assert [shard["node_ids_sha256"] for shard in shards] == [
        "9a2ff93c333465e9815679ef6e9f971cbee782f2b833934c765447867a5a5704",
        "c6d005d0e69b2be5bbe1b197c71f22af598081ec2a1fc9e31cf217f7b5ef37ce",
        "c7dad7210a3bebcdd7a497db946b574e05c5d2a1694fa9426ee7b62da271b8b3",
        "38cb6d54b4c0e163308cdbcde38eff5a8372cc5a3c3702b1c0edbdf173b2118a",
    ]
    assigned = [node for shard in shards for node in shard["node_ids"]]
    assert len(assigned) == len(set(assigned)) == len(full_nodes)
    assert set(assigned) == set(full_nodes)
    for shard in shards:
        assert shard["node_count"] == len(shard["node_ids"])
        assert shard["node_ids_sha256"] == _canonical_list_hash(shard["node_ids"])
    assert shards[0]["node_ids"] == [
        "tests/test_fe_solver_nonlinear_static.py::"
        "test_pure_bending_reaches_plastic_moment"
    ]

    timeout = contract["execution"]["timeout_policy"]
    assert timeout == {
        "automatic_retry": False,
        "evidence_reserve_seconds": 20,
        "scope": "COMPLETE_RESOURCE_INVOCATION_AND_CHILD_PROCESS_TREE",
        "termination_grace_seconds": 10,
        "timeout_exit_code": 124,
        "wall_limit_seconds": 1200,
        "windows_job": {
            "assignment": "CREATE_SUSPENDED_ASSIGN_RESUME",
            "limit": "JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE",
            "watchdog_termination_start_seconds": 1190,
        },
        "windows_termination": {
            "arguments": ["/PID", "{pid}", "/T", "/F"],
            "bytes": 118784,
            "path": r"C:\Windows\System32\taskkill.exe",
            "sha256": (
                "1249717315fc8f4d2df17d5db9da0444795fdb9fb83dfb1f763c3f39282244f7"
            ),
        },
    }
    taskkill = Path(timeout["windows_termination"]["path"])
    if taskkill.is_file():
        assert _file_record(taskkill) == {
            "bytes": timeout["windows_termination"]["bytes"],
            "sha256": timeout["windows_termination"]["sha256"],
        }
    assert contract["execution"]["cycle_wall_policy"] == {
        "absolute_wall_limit_seconds": 1200,
        "clock": "time.monotonic",
        "cumulative_deadlines_seconds": {
            "anyfem": 990,
            "functional": 900,
            "performance": 1110,
        },
        "final_evidence_reserve_seconds": 90,
        "scope": "COMPLETE_CYCLE_AND_ALL_CHILD_PROCESS_TREES",
    }
    assert contract["execution"]["clean_status_args"] == [
        "status",
        "--porcelain=v1",
        "-z",
        "--untracked-files=all",
        "--ignored=matching",
    ]
    assert contract["execution"]["clean_status_empty"] == {
        "bytes": 0,
        "sha256": hashlib.sha256(b"").hexdigest(),
    }
    assert contract["execution"]["clean_status_phases"] == [
        "BEFORE_LOCAL_PREFLIGHT_OUTPUT_RESERVATION",
        "BEFORE_APPROVAL_LEDGER_MUTATION",
        "BEFORE_RESOURCE_ACQUIRE_OR_EXECUTION_STARTED",
        "POST_WORKER",
        "FINAL_RESULT_VALIDATION",
    ]
    assert contract["execution"]["clean_status_scope"] == [
        "ANYsolver",
        "ANYfem",
        "ANYfileIO",
        "ANYgeometry",
        "ANYmaterial",
        "ANYmesh",
    ]
    assert contract["execution"]["gate_git_invocation_policy"] == {
        "environment": "VALIDATOR_EQUIVALENT_SANITIZED_GIT_ENVIRONMENT",
        "launcher": "FROZEN_EXECUTION_GIT",
        "prefix_after_launcher": [
            "--no-replace-objects",
            "-c",
            "safe.directory={repository}",
            "-c",
            "core.autocrlf=true",
            "-c",
            "core.attributesFile=NUL",
            "-c",
            "core.fsmonitor=false",
            "-c",
            "core.quotepath=false",
            "-c",
            "core.untrackedCache=false",
            "-c",
            "status.showUntrackedFiles=all",
            "-C",
            "{repository}",
        ],
        "scope": "ALL_GATE_GIT_SUBPROCESSES",
    }
    assert contract["ci_policy"] == {
        "coordinator_wall_limit_seconds": 1200,
        "extent": "COMPLETE_FROZEN_INVENTORIES",
        "required_lanes": ["quick", "functional", "additive"],
        "smoke_or_representative_only_forbidden": True,
    }


def test_timeout_and_functional_manifest_mutations_are_rejected() -> None:
    contract = _load_contract()
    bounded_policy = process_runner._timeout_policy(contract)
    assert bounded_policy["wall_limit_seconds"] == 1200
    assert bounded_policy["worker_timeout_seconds"] == 1160
    assert contract["functional_wave"]["execution"]["internal_deadline_seconds"] == 830
    assert (
        contract["execution"]["cycle_wall_policy"]["cumulative_deadlines_seconds"][
            "functional"
        ]
        == 900
    )
    assert (
        bounded_policy["worker_timeout_seconds"]
        + bounded_policy["termination_grace_seconds"]
        + bounded_policy["termination_grace_seconds"]
        + bounded_policy["evidence_reserve_seconds"]
        == bounded_policy["wall_limit_seconds"]
    )
    for key, bad in (
        ("wall_limit_seconds", 1201),
        ("timeout_exit_code", 0),
        ("termination_grace_seconds", 0),
        ("evidence_reserve_seconds", 0),
        ("scope", "TOP_LEVEL_PROCESS_ONLY"),
        ("automatic_retry", True),
    ):
        mutated = copy.deepcopy(contract)
        mutated["execution"]["timeout_policy"][key] = bad
        with pytest.raises(burnin.EvidenceError):
            process_runner._timeout_policy(mutated)

    mutated = copy.deepcopy(contract)
    mutated["functional_wave"]["manifest"]["shards"][0]["node_ids"].append(
        mutated["functional_wave"]["manifest"]["shards"][1]["node_ids"][0]
    )
    with pytest.raises(burnin.EvidenceError):
        burnin.validate_functional_wave_contract(mutated)

    mutated = copy.deepcopy(contract)
    mutated["functional_wave"]["execution"]["max_workers"] = 3
    with pytest.raises(burnin.EvidenceError):
        burnin.validate_functional_wave_contract(mutated)

    for deadline in (829, 831):
        mutated = copy.deepcopy(contract)
        mutated["functional_wave"]["execution"]["internal_deadline_seconds"] = deadline
        with pytest.raises(burnin.EvidenceError):
            burnin.validate_functional_wave_contract(mutated)
    mutated = copy.deepcopy(contract)
    mutated["functional_wave"]["execution"]["unproven_tree_action"] = "RETURN"
    with pytest.raises(burnin.EvidenceError):
        burnin.validate_functional_wave_contract(mutated)

    source = (
        REFERENCE / "e4_pl_s3_q4_process_runner.py"
    ).read_text(encoding="utf-8")
    assert "timeout=_remaining_budget(absolute_worker_deadline)" in source
    assert source.count("timeout=_remaining_budget(absolute_worker_deadline)") == 2
    assert "_start_resource_invocation_watchdog(_EARLY_RESOURCE_TIMEOUT_POLICY)" in source
    assert "absolute_deadline=worker_deadline" in source
    assert "absolute_deadline=publication_deadline" in source
    assert "termination_deadline = time.monotonic()" in source
    assert "timeout=remaining_termination_time()" in source
    assert '"/T"' in source and '"/F"' in source


def test_complete_cycle_uses_one_absolute_clock_and_stops_after_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    contract = _load_contract()
    timeout_policy = process_runner._timeout_policy(contract)
    assert process_runner._cycle_wall_policy(contract) == {
        "absolute_wall_limit_seconds": 1200,
        "clock": "time.monotonic",
        "cumulative_deadlines_seconds": {
            "anyfem": 990,
            "functional": 900,
            "performance": 1110,
        },
        "final_evidence_reserve_seconds": 90,
        "scope": "COMPLETE_CYCLE_AND_ALL_CHILD_PROCESS_TREES",
    }
    rows = contract["resource_requests"]["cycle_1"]
    monkeypatch.setattr(
        process_runner,
        "_validate_cycle_request_rows",
        lambda _contract, _cycle: rows,
    )
    monkeypatch.setattr(process_runner.time, "monotonic", lambda: 1000.0)
    assert process_runner._request_execution_policy(contract) == {
        "current_request_execution_mode": "FORMAL_CYCLE_COORDINATOR_ONLY",
        "idempotent_publication_recovery": "FINALIZE_COMMAND_ONLY",
        "scope": "ALL_SIX_CURRENT_REQUEST_IDS",
        "standalone_resource_command": "FORBIDDEN_FOR_CURRENT_REQUEST_IDS",
    }
    calls: list[tuple[str, float, bool, bool]] = []

    def pass_lane(**kwargs: object) -> int:
        calls.append(
            (
                str(kwargs["request_id"]),
                float(kwargs["invocation_deadline"]),
                bool(kwargs["emit_manifest"]),
                kwargs["cycle_execution_capability"]
                is process_runner._CYCLE_RESOURCE_EXECUTION_CAPABILITY,
            )
        )
        return 0

    published: list[int] = []
    emitted: list[int] = []
    monkeypatch.setattr(process_runner, "_run_resource_bounded", pass_lane)
    monkeypatch.setattr(
        process_runner,
        "_publish_completed_cycles",
        lambda _contract: published.append(1),
    )
    monkeypatch.setattr(
        process_runner,
        "_emit_cycle_terminal_snapshot",
        lambda _contract, cycle: emitted.append(cycle),
    )
    assert (
        process_runner._run_cycle_bounded(
            cycle=1,
            contract=contract,
            timeout_policy=timeout_policy,
            invocation_deadline=2200.0,
        )
        == 0
    )
    assert calls == [
        (rows[0]["request_id"], 1900.0, False, True),
        (rows[1]["request_id"], 1990.0, False, True),
        (rows[2]["request_id"], 2110.0, False, True),
    ]
    assert published == [1]
    assert emitted == [1]

    calls.clear()
    published.clear()
    emitted.clear()
    cancelled: list[bool] = []

    def fail_second(**kwargs: object) -> int:
        calls.append(
            (
                str(kwargs["request_id"]),
                float(kwargs["invocation_deadline"]),
                bool(kwargs["emit_manifest"]),
                kwargs["cycle_execution_capability"]
                is process_runner._CYCLE_RESOURCE_EXECUTION_CAPABILITY,
            )
        )
        return 1 if len(calls) == 2 else 0

    monkeypatch.setattr(process_runner, "_run_resource_bounded", fail_second)
    monkeypatch.setattr(
        process_runner, "cancel_remaining", lambda: cancelled.append(True)
    )
    assert (
        process_runner._run_cycle_bounded(
            cycle=1,
            contract=contract,
            timeout_policy=timeout_policy,
            invocation_deadline=2200.0,
        )
        == 1
    )
    assert [request_id for request_id, _deadline, _emit, _capability in calls] == [
        rows[0]["request_id"],
        rows[1]["request_id"],
    ]
    assert cancelled == [True]
    assert published == []
    assert emitted == [1]

    for path, bad in (
        (("absolute_wall_limit_seconds",), 1201),
        (("clock",), "time.time"),
        (("final_evidence_reserve_seconds",), 89),
        (("scope",), "PER_LANE"),
        (("cumulative_deadlines_seconds", "functional"), 901),
        (("cumulative_deadlines_seconds", "anyfem"), 991),
        (("cumulative_deadlines_seconds", "performance"), 1111),
    ):
        hostile = copy.deepcopy(contract)
        target = hostile["execution"]["cycle_wall_policy"]
        if len(path) == 1:
            target[path[0]] = bad
        else:
            target[path[0]][path[1]] = bad
        with pytest.raises(burnin.EvidenceError):
            process_runner._cycle_wall_policy(hostile)

    for key, bad in (
        ("current_request_execution_mode", "STANDALONE_OR_CYCLE"),
        ("idempotent_publication_recovery", "RERUN_ALLOWED"),
        ("scope", "CYCLE_1_ONLY"),
        ("standalone_resource_command", "PERMITTED"),
    ):
        hostile = copy.deepcopy(contract)
        hostile["execution"]["request_execution_policy"][key] = bad
        with pytest.raises(burnin.EvidenceError):
            process_runner._request_execution_policy(hostile)


def test_current_requests_reject_standalone_execution_before_side_effects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    contract = _load_contract()
    timeout_policy = process_runner._timeout_policy(contract)

    def forbidden(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("standalone execution reached a protected side effect")

    for name in (
        "_verify_repositories",
        "_verify_resource_order",
        "_require_package_artifacts",
        "_request_payload",
        "_load_approval_snapshot",
        "_run_resource_command",
    ):
        monkeypatch.setattr(process_runner, name, forbidden)

    current_ids = [
        row["request_id"]
        for cycle in ("cycle_1", "cycle_2")
        for row in contract["resource_requests"][cycle]
    ]
    assert len(current_ids) == len(set(current_ids)) == 6
    for request_id in current_ids:
        for capability in (None, object()):
            with pytest.raises(
                burnin.EvidenceError,
                match="standalone resource worker execution is forbidden",
            ):
                process_runner._run_resource_bounded(
                    request_id=request_id,
                    contract=contract,
                    timeout_policy=timeout_policy,
                    invocation_deadline=time.monotonic() + 1200.0,
                    cycle_execution_capability=capability,
                )


def test_functional_wave_deadline_prevents_late_launch_and_binds_partial_extent(
    tmp_path: Path,
) -> None:
    contract = _load_contract()
    spec = importlib.util.spec_from_file_location(
        "s3_q4_wave_deadline_probe", ROOT / "scripts" / "run_e4_pl_burnin_gate.py"
    )
    assert spec is not None and spec.loader is not None
    gate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate)

    shard_root = tmp_path / "shard-P01"
    sandbox = shard_root / "cwd"
    logs = shard_root / "logs"
    sandbox.mkdir(parents=True)
    logs.mkdir()
    (shard_root / "temp").mkdir()
    shard = contract["functional_wave"]["manifest"]["shards"][0]
    canonical, raw = gate._run_functional_shard(
        {
            "full_node_ids": contract["functional_wave"]["manifest"]["full_node_ids"],
            "sandbox": sandbox,
            "shard": shard,
            "shard_root": shard_root,
        },
        absolute_deadline=time.monotonic() - 1.0,
        deadline_seconds=830,
        timeout_policy=contract["execution"]["timeout_policy"],
    )
    assert canonical == {
        "exit_code": 124,
        "node_count": shard["node_count"],
        "node_ids_sha256": shard["node_ids_sha256"],
        "result": None,
        "shard_id": "P01",
        "status": "TIMED_OUT_NOT_STARTED",
    }
    assert raw["attempts"] == 0
    assert raw["disposition"] == "DEADLINE_EXPIRED_NOT_STARTED"
    assert raw["termination"] is None
    assert raw["timed_out"] is True

    extra = tmp_path / "source.bin"
    extra.write_bytes(b"partial\n")
    extent = gate._functional_artifact_extent(tmp_path, exclude=set())
    assert extent["files"] == len(extent["records"])
    assert [row["path"] for row in extent["records"]] == sorted(
        row["path"] for row in extent["records"]
    )
    assert extent["sha256"] == hashlib.sha256(
        gate.canonical_json_bytes(extent["records"])
    ).hexdigest()

    source = (ROOT / "scripts" / "run_e4_pl_burnin_gate.py").read_text(
        encoding="utf-8"
    )
    assert "absolute_deadline = wave_started + deadline" in source
    assert "max_workers=int(wave[\"execution\"][\"max_workers\"])" in source


def test_functional_selectors_preserve_split_module_ownership() -> None:
    contract = _load_contract()
    spec = importlib.util.spec_from_file_location(
        "s3_q4_selector_probe", ROOT / "scripts" / "run_e4_pl_burnin_gate.py"
    )
    assert spec is not None and spec.loader is not None
    gate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate)
    manifest = contract["functional_wave"]["manifest"]
    full_nodes = manifest["full_node_ids"]
    shards = {row["shard_id"]: row for row in manifest["shards"]}
    pure_bending = (
        "tests/test_fe_solver_nonlinear_static.py::"
        "test_pure_bending_reaches_plastic_moment"
    )

    selectors, summary = gate._functional_shard_selectors(
        shards["P01"]["node_ids"], full_nodes
    )
    assert selectors == [pure_bending]
    assert summary["exact_node_count"] == 1
    assert summary["full_module_count"] == 0

    selectors, summary = gate._functional_shard_selectors(
        shards["P04"]["node_ids"], full_nodes
    )
    nonlinear_selectors = [
        selector
        for selector in selectors
        if selector.startswith("tests/test_fe_solver_nonlinear_static.py")
    ]
    assert len(nonlinear_selectors) == 9
    assert all("::" in selector for selector in nonlinear_selectors)
    assert pure_bending not in nonlinear_selectors
    assert summary["exact_node_count"] == 9

    source = (ROOT / "scripts" / "run_e4_pl_burnin_gate.py").read_text(
        encoding="utf-8"
    )
    assert '"NUMBA_NUM_THREADS": "1"' in source
    assert '"--durations=0"' in source
    assert '"PREPARATION_FAILED"' in source
    assert '"START_FAILED"' in source


def test_functional_shard_results_are_independently_recomputed_and_mutation_safe(
    tmp_path: Path,
) -> None:
    contract = _load_contract()
    authority = contract["functional_wave"]["manifest"]["shards"][1]
    result_path = tmp_path / "shard-result.json"
    valid = {
        "collection_matches": True,
        "exit_code": 0,
        "nodes": [
            {"node_id": node_id, "outcome": "PASSED"}
            for node_id in authority["node_ids"]
        ],
        "schema": burnin.FUNCTIONAL_SHARD_SCHEMA,
        "shard_id": authority["shard_id"],
    }
    result_path.write_bytes(burnin.canonical_json_bytes(valid))
    parsed, passed = burnin._validate_functional_shard_result(
        result_path, authority=authority, location="$probe"
    )
    assert parsed == valid
    assert passed is True

    for mutate in (
        lambda value: value.__setitem__("schema", "wrong-schema"),
        lambda value: value.__setitem__("shard_id", "F10"),
        lambda value: value.__setitem__("collection_matches", 1),
        lambda value: value.__setitem__("exit_code", True),
        lambda value: value.__setitem__("extra", None),
        lambda value: value.pop("schema"),
        lambda value: value["nodes"][0].__setitem__("node_id", "tests/unknown.py::test_x"),
        lambda value: value["nodes"][0].__setitem__("outcome", "SUCCESS"),
        lambda value: value["nodes"][0].__setitem__("extra", None),
        lambda value: value["nodes"][0].pop("outcome"),
        lambda value: value["nodes"].pop(),
        lambda value: value["nodes"].append(copy.deepcopy(value["nodes"][-1])),
        lambda value: value["nodes"].__setitem__(1, copy.deepcopy(value["nodes"][0])),
        lambda value: value["nodes"].__setitem__(
            slice(0, 2), [value["nodes"][1], value["nodes"][0]]
        ),
    ):
        hostile = copy.deepcopy(valid)
        mutate(hostile)
        result_path.write_bytes(burnin.canonical_json_bytes(hostile))
        with pytest.raises(burnin.EvidenceError):
            burnin._validate_functional_shard_result(
                result_path, authority=authority, location="$probe"
            )

    for semantic_failure in (
        {"collection_matches": False},
        {"exit_code": 1},
        {"outcome": "FAILED"},
        {"outcome": "ERROR"},
        {"outcome": "NOT_RUN"},
        {"outcome": "XPASS"},
    ):
        failure = copy.deepcopy(valid)
        for key, value in semantic_failure.items():
            if key == "outcome":
                failure["nodes"][0][key] = value
            else:
                failure[key] = value
        result_path.write_bytes(burnin.canonical_json_bytes(failure))
        _parsed, passed = burnin._validate_functional_shard_result(
            result_path, authority=authority, location="$probe"
        )
        assert passed is False

    hostile_raw_values = (
        json.dumps(valid, indent=2).encode("utf-8"),
        burnin.canonical_json_bytes(valid).replace(
            b'{"collection_matches":true,',
            b'{"collection_matches":true,"collection_matches":true,',
            1,
        ),
        burnin.canonical_json_bytes(valid).replace(b'"exit_code":0', b'"exit_code":NaN', 1),
    )
    for hostile_raw in hostile_raw_values:
        result_path.write_bytes(hostile_raw)
        with pytest.raises((burnin.EvidenceError, ValueError)):
            burnin._validate_functional_shard_result(
                result_path, authority=authority, location="$probe"
            )


def test_functional_plugin_rejects_unregistered_collected_nodes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec = importlib.util.spec_from_file_location(
        "s3_q4_wave_collection_probe", ROOT / "scripts" / "run_e4_pl_burnin_gate.py"
    )
    assert spec is not None and spec.loader is not None
    gate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate)

    class Item:
        def __init__(self, nodeid: str) -> None:
            self.nodeid = nodeid

    class Hook:
        def __init__(self) -> None:
            self.deselected: list[Item] = []

        def pytest_deselected(self, *, items: list[Item]) -> None:
            self.deselected.extend(items)

    class Config:
        def __init__(self) -> None:
            self.hook = Hook()

    expected = ["tests/test_registered.py::test_registered"]
    state = {
        "collection_matches": False,
        "expected": expected,
        "expected_set": set(expected),
        "durations": {},
        "outcomes": {},
        "progress_stream": io.BytesIO(),
        "result_path": Path("unused.json"),
        "shard_id": "P01",
    }
    monkeypatch.setattr(gate, "_functional_plugin_state", lambda: state)
    items = [Item(expected[0]), Item("tests/test_unregistered.py::test_extra")]
    config = Config()
    gate.pytest_collection_modifyitems(None, config, items)
    assert state["collection_matches"] is False
    assert [item.nodeid for item in items] == expected
    assert [item.nodeid for item in config.hook.deselected] == [
        "tests/test_unregistered.py::test_extra"
    ]


def test_bounded_ci_uses_exact_node_guards_and_complete_inventory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec = importlib.util.spec_from_file_location(
        "s3_q4_ci_guard_probe", ROOT / "scripts" / "run_e4_pl_burnin_gate.py"
    )
    assert spec is not None and spec.loader is not None
    gate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate)

    assert gate.CI_NONFUNCTIONAL_NODE_AUTHORITY == {
        "node_count": 871,
        "node_ids_sha256": (
            "7b5ea229272fcde6bae810c6ce0ae52a4d1cfe2c35efa65c681b24f278a015ff"
        ),
    }
    assert {
        shard_id: authority["node_count"]
        for shard_id, authority in gate.CI_SHARD_NODE_AUTHORITIES.items()
    } == {"P01": 93, "P02": 622, "P03": 589, "P04": 603}
    assert sum(
        authority["node_count"]
        for authority in gate.CI_SHARD_NODE_AUTHORITIES.values()
    ) == 1907
    synthetic_lanes = {
        "quick": ["quick_a", "quick_b"],
        "additive": ["add_0", "add_1", "add_2", "add_3", "add_4"],
    }
    assert gate._ci_nonfunctional_module_buckets(synthetic_lanes) == [
        ["quick_a", "quick_b"],
        ["add_0", "add_3"],
        ["add_1", "add_4"],
        ["add_2"],
    ]

    class Item:
        def __init__(self, nodeid: str) -> None:
            self.nodeid = nodeid

    class Hook:
        def pytest_deselected(self, *, items: list[Item]) -> None:
            del items

    class Config:
        hook = Hook()

    class Session:
        exitstatus = 0

    expected = ["tests/test_registered.py::test_registered"]
    state = {
        "collection_matches": False,
        "expected": expected,
        "expected_set": set(expected),
        "mode": "ci-guard",
        "shard_id": "P01",
    }
    monkeypatch.setattr(gate, "_functional_plugin_state", lambda: state)
    exact_items = [Item(expected[0])]
    gate.pytest_collection_modifyitems(None, Config(), exact_items)
    exact_session = Session()
    gate.pytest_sessionfinish(exact_session, 0)
    assert state["collection_matches"] is True
    assert exact_session.exitstatus == 0

    hostile_items = [Item(expected[0]), Item("tests/test_extra.py::test_extra")]
    gate.pytest_collection_modifyitems(None, Config(), hostile_items)
    hostile_session = Session()
    gate.pytest_sessionfinish(hostile_session, 0)
    assert state["collection_matches"] is False
    assert hostile_session.exitstatus == 3

    source = (ROOT / "scripts" / "run_e4_pl_burnin_gate.py").read_text(
        encoding="utf-8"
    )
    assert "sys.dont_write_bytecode = True" in source
    ci_start = source.index("def _run_bounded_ci(")
    ci_end = source.index("\ndef _tracked_head_identity(", ci_start)
    ci_source = source[ci_start:ci_end]
    assert "_collect_ci_nonfunctional_nodes(" in ci_source
    assert "_ci_nonfunctional_module_buckets(lanes)" in ci_source
    assert "CI_SHARD_NODE_AUTHORITIES[shard_id]" in ci_source
    assert "_CI_EXPECTED_ENV" in ci_source and "_CI_SHARD_ENV" in ci_source
    assert '"scripts.run_e4_pl_burnin_gate"' in ci_source
    assert "if not _terminate_ci_workers(" in ci_source
    assert "_await_outer_resource_tree_termination()" in ci_source
    assert '_ACTIVE_TEST_LANE_ENV = "ANYSOLVER_BURNIN_ACTIVE_TEST_LANE"' in source
    assert 'environment[_ACTIVE_TEST_LANE_ENV] = "quick"' in source

    forbidden_calls: list[str] = []
    dangerous_lanes = {"ci", "functional-wave", "package", "performance"}
    for module_name in gate.inventory()["quick"]:
        module_path = ROOT / module_name
        tree = ast.parse(module_path.read_text(encoding="utf-8"), filename=module_name)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if isinstance(node.func, ast.Attribute):
                callable_name = node.func.attr
            elif isinstance(node.func, ast.Name):
                callable_name = node.func.id
            else:
                callable_name = ""
            literals = {
                child.value
                for child in ast.walk(node)
                if isinstance(child, ast.Constant) and isinstance(child.value, str)
            }
            if callable_name in {
                "_run_bounded_ci",
                "run_functional_wave",
                "_run_gate_cli_watchdog",
            }:
                forbidden_calls.append(f"{module_name}:{node.lineno}:{callable_name}")
            if callable_name == "main" and literals & dangerous_lanes:
                forbidden_calls.append(f"{module_name}:{node.lineno}:main")
            if callable_name in {"run", "Popen"} and any(
                "run_e4_pl_burnin_gate.py" in literal
                or "e4_pl_s3_q4_process_runner.py" in literal
                for literal in literals
            ):
                forbidden_calls.append(f"{module_name}:{node.lineno}:subprocess")
    assert forbidden_calls == []

    nested_dispatch: list[str] = []
    monkeypatch.setenv(gate._ACTIVE_TEST_LANE_ENV, "quick")
    monkeypatch.setattr(
        gate,
        "_run_gate_cli_watchdog",
        lambda *_args, **_kwargs: nested_dispatch.append("gate") or 0,
    )
    with pytest.raises(gate.EvidenceError, match="nested burn-in execution"):
        gate.main(["ci"])
    monkeypatch.setattr(
        process_runner,
        "_arm_invocation_job_boundary",
        lambda: nested_dispatch.append("process-runner"),
    )
    with pytest.raises(RuntimeError, match="nested process coordinator"):
        process_runner.main(["aggregate"])
    assert nested_dispatch == []


def test_gate_watchdog_authenticates_child_and_owns_timeout_tree(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec = importlib.util.spec_from_file_location(
        "s3_q4_gate_watchdog_probe", ROOT / "scripts" / "run_e4_pl_burnin_gate.py"
    )
    assert spec is not None and spec.loader is not None
    gate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate)
    monkeypatch.delenv(gate._GATE_WATCHDOG_ENV, raising=False)
    monkeypatch.setattr(gate, "FUNCTIONAL_COMMAND_WALL_LIMIT_SECONDS", 2)
    monkeypatch.setattr(gate, "FUNCTIONAL_COMMAND_TERMINATION_RESERVE_SECONDS", 1)

    class TimedOutWorker:
        pid = 4242

        def __init__(self) -> None:
            self.waits = 0

        def wait(self, timeout: float) -> int:
            assert timeout > 0
            self.waits += 1
            if self.waits == 1:
                raise subprocess.TimeoutExpired(["gate-child"], timeout)
            return 124

    worker = TimedOutWorker()
    launched: list[tuple[list[str], dict[str, str]]] = []
    closed: list[int | None] = []

    def launch(
        command: list[str], *, cwd: Path, env: dict[str, str]
    ) -> tuple[TimedOutWorker, int]:
        assert cwd == ROOT
        launched.append((command, env))
        return worker, 77

    monkeypatch.setattr(gate, "_launch_gate_watchdog_child", launch)
    monkeypatch.setattr(
        gate,
        "_close_gate_job",
        lambda handle: closed.append(handle) is None,
    )
    assert (
        gate._run_gate_cli_watchdog(
            "functional-wave",
            cycle=1,
            command_started=time.monotonic(),
        )
        == 124
    )
    assert worker.waits == 2
    assert closed == [77]
    command, environment = launched[0]
    token_index = command.index("--_watchdog-token") + 1
    parent_index = command.index("--_watchdog-parent") + 1
    token = command[token_index]
    parent = command[parent_index]
    assert re.fullmatch(r"[0-9a-f]{64}", token)
    assert parent == str(os.getpid())
    assert environment[gate._GATE_WATCHDOG_ENV] == (
        f"functional-wave:{parent}:{token}"
    )

    monkeypatch.setenv(gate._GATE_WATCHDOG_ENV, "forged")
    with pytest.raises(gate.EvidenceError, match="preexisting gate watchdog context"):
        gate._run_gate_cli_watchdog(
            "functional-wave",
            cycle=1,
            command_started=time.monotonic(),
        )


def test_inner_tree_termination_failure_is_held_for_outer_tree_kill(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    contract = _load_contract()
    spec = importlib.util.spec_from_file_location(
        "s3_q4_wave_tree_failure_probe", ROOT / "scripts" / "run_e4_pl_burnin_gate.py"
    )
    assert spec is not None and spec.loader is not None
    gate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate)
    shard = contract["functional_wave"]["manifest"]["shards"][0]
    shard_root = tmp_path / "shard-P01"
    sandbox = shard_root / "cwd"
    (shard_root / "logs").mkdir(parents=True)
    sandbox.mkdir()

    class UncertainWorker:
        pid = 4242

        def wait(self, timeout: float) -> int:
            raise OSError(f"simulated wait failure after launch ({timeout})")

    monkeypatch.setattr(gate, "_functional_shard_environment", lambda **_kwargs: {})
    monkeypatch.setattr(gate.subprocess, "Popen", lambda *_args, **_kwargs: UncertainWorker())
    monkeypatch.setattr(
        gate,
        "_terminate_functional_process_tree",
        lambda *_args, **_kwargs: {
            "bytes": 0,
            "returncode": 259,
            "sha256": hashlib.sha256(b"").hexdigest(),
        },
    )
    canonical, raw = gate._run_functional_shard(
        {
            "full_node_ids": contract["functional_wave"]["manifest"]["full_node_ids"],
            "sandbox": sandbox,
            "shard": shard,
            "shard_root": shard_root,
        },
        absolute_deadline=time.monotonic() + 60.0,
        deadline_seconds=830,
        timeout_policy=contract["execution"]["timeout_policy"],
    )
    assert canonical["status"] == "TIMEOUT_TREE_TERMINATION_FAILED"
    assert raw["termination"]["returncode"] == 259
    assert "simulated wait failure" in raw["process_error"]
    assert gate._functional_wave_has_unproven_tree([canonical]) is True
    assert gate._FUNCTIONAL_UNPROVEN_TREE.is_set()

    held: list[bool] = []

    def fail_after_unproven_tree(*_args: object, **_kwargs: object) -> int:
        gate._FUNCTIONAL_UNPROVEN_TREE.set()
        raise OSError("simulated aggregate publication failure")

    monkeypatch.setattr(gate, "_run_functional_wave_unprotected", fail_after_unproven_tree)
    monkeypatch.setattr(gate, "_record_functional_wave_failure", lambda *_args: 1)
    monkeypatch.setattr(
        gate, "_await_outer_resource_tree_termination", lambda: held.append(True)
    )
    assert gate.run_functional_wave(1, contract_path=CONTRACT_PATH) == 1
    assert held == [True]

    source = (ROOT / "scripts" / "run_e4_pl_burnin_gate.py").read_text(
        encoding="utf-8"
    )
    run_start = source.index("def run_functional_wave(")
    run_source = source[run_start : source.index("\ndef _run_pytest_lane", run_start)]
    assert "finally:" in run_source
    assert "if _FUNCTIONAL_UNPROVEN_TREE.is_set():" in run_source
    assert "_await_outer_resource_tree_termination()" in run_source


def test_outer_wait_failure_is_tree_terminated_or_retains_resource_lock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    contract = _load_contract()
    policy = process_runner._timeout_policy(contract)
    output_dir = tmp_path / "resource-output"
    output_dir.mkdir()

    class UncertainOuterWorker:
        pid = 4343
        returncode = None

        def wait(self, timeout: float) -> int:
            raise OSError(f"simulated outer wait failure ({timeout})")

    monkeypatch.setattr(process_runner, "_timeout_policy", lambda _contract: policy)
    monkeypatch.setattr(
        process_runner.burnin,
        "execution_tool_path",
        lambda _contract, _name: Path("powershell.exe"),
    )
    monkeypatch.setattr(process_runner, "_execution_environment", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(
        process_runner,
        "_launch_bounded_worker",
        lambda *_args, **_kwargs: (UncertainOuterWorker(), None),
    )
    monkeypatch.setattr(
        process_runner,
        "_terminate_worker_tree",
        lambda *_args, **_kwargs: process_runner._termination_metadata(
            disposition="INTERRUPTED_TREE_TERMINATION_FAILED",
            policy=policy,
            tree_kill_attempted=True,
            tree_kill_exit_code=259,
            child_exit_observed=False,
        ),
    )
    completed, execution_state, termination = process_runner._run_resource_command(
        "Write-Output never-runs",
        absolute_worker_deadline=time.monotonic() + 60.0,
        contract=contract,
        cwd=tmp_path,
        output_dir=output_dir,
        process_prefix="cycle_1.functional",
    )
    assert execution_state == "EXECUTED"
    assert completed.returncode == 250
    assert termination["disposition"] == "INTERRUPTED_TREE_TERMINATION_FAILED"
    assert termination["tree_kill_attempted"] is True
    assert termination["tree_kill_exit_code"] == 259
    assert not termination["disposition"].endswith("_TERMINATED")
    assert process_runner._RESOURCE_UNPROVEN_TREE.is_set()
    process_runner._RESOURCE_UNPROVEN_TREE.clear()


def test_normal_exit_closes_job_before_local_or_resource_result_returns(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    contract = _load_contract()
    events: list[str] = []

    class NormalWorker:
        pid = 4444
        returncode = 0

        def wait(self, timeout: float) -> int:
            assert timeout > 0.0
            events.append("wait")
            return 0

    monkeypatch.setattr(
        process_runner.burnin,
        "execution_tool_path",
        lambda _contract, _name: Path("powershell.exe"),
    )
    monkeypatch.setattr(process_runner, "_execution_environment", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(
        process_runner,
        "_launch_bounded_worker",
        lambda *_args, **_kwargs: (NormalWorker(), 9191),
    )

    def close_job(handle: int | None) -> bool:
        assert handle == 9191
        events.append("close")
        return True

    monkeypatch.setattr(process_runner, "_close_job_handle", close_job)
    process_runner._RESOURCE_UNPROVEN_TREE.clear()

    local, *_local_metadata = process_runner._run(
        "Write-Output local",
        absolute_worker_deadline=time.monotonic() + 60.0,
        contract=contract,
        cwd=tmp_path,
        process_prefix="common.quick.1",
    )
    assert local.returncode == 0
    assert events == ["wait", "close"]

    events.clear()
    output_dir = tmp_path / "resource-normal-exit"
    output_dir.mkdir()
    resource, execution_state, termination = process_runner._run_resource_command(
        "Write-Output resource",
        absolute_worker_deadline=time.monotonic() + 60.0,
        contract=contract,
        cwd=tmp_path,
        output_dir=output_dir,
        process_prefix="cycle_1.functional",
    )
    assert resource.returncode == 0
    assert execution_state == "EXECUTED"
    assert termination["disposition"] == "NORMAL_EXIT"
    assert events == ["wait", "close"]
    assert not process_runner._RESOURCE_UNPROVEN_TREE.is_set()


def test_failed_job_close_prevents_local_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    contract = _load_contract()
    policy = process_runner._timeout_policy(contract)
    published: list[bool] = []
    candidate = tmp_path / "candidate"
    candidate.mkdir()
    monkeypatch.setattr(
        process_runner,
        "_verify_repositories",
        lambda _contract: (candidate, {}, "a" * 40, "b" * 40),
    )
    monkeypatch.setattr(
        process_runner,
        "_verify_local_order",
        lambda _contract, _lane, _partition: "common.quick.1",
    )
    monkeypatch.setattr(process_runner, "_execution_environment", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(process_runner, "_reserve_output", lambda _path: None)
    monkeypatch.setattr(
        process_runner.burnin,
        "process_output_directory",
        lambda _contract, _prefix: tmp_path / "local-output",
    )

    def unproven_run(*_args: object, **_kwargs: object) -> tuple[object, ...]:
        process_runner._RESOURCE_UNPROVEN_TREE.set()
        completed = subprocess.CompletedProcess(
            args=["worker"], returncode=0, stdout=b"", stderr=b""
        )
        return (
            completed,
            "2026-08-26T00:00:00Z",
            "2026-08-26T00:00:01Z",
            1.0,
            "EXECUTED",
            process_runner._termination_metadata(
                disposition="NORMAL_EXIT",
                policy=policy,
                tree_kill_attempted=False,
                tree_kill_exit_code=None,
                child_exit_observed=True,
            ),
        )

    monkeypatch.setattr(process_runner, "_run", unproven_run)
    monkeypatch.setattr(
        process_runner,
        "_write_process",
        lambda *_args, **_kwargs: published.append(True),
    )
    process_runner._RESOURCE_UNPROVEN_TREE.clear()
    with pytest.raises(
        process_runner.burnin.EvidenceError,
        match="publication requires proven child-tree closure",
    ):
        process_runner._run_local_bounded(
            contract=contract,
            invocation_deadline=time.monotonic() + 1200.0,
            lane="quick",
            partition=None,
            timeout_policy=policy,
        )
    assert published == []
    process_runner._RESOURCE_UNPROVEN_TREE.clear()


def test_failed_acquisition_job_close_prevents_request_consumption(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    contract = _load_contract()
    policy = process_runner._timeout_policy(contract)
    request_id = contract["resource_requests"]["cycle_1"][0]["request_id"]
    candidate = tmp_path / "candidate"
    candidate.mkdir()
    ledger = tmp_path / "ledger.md"
    ledger.write_text("approved\n", encoding="utf-8")
    manager = {
        "acquire": tmp_path / "acquire.ps1",
        "active_lock": tmp_path / "active-lock",
        "ledger": ledger,
        "release": tmp_path / "release.ps1",
    }
    row = {
        "bytes": 1,
        "command_sha256": "c" * 64,
        "lane": "functional",
        "request_id": request_id,
        "request_sha256": "d" * 64,
    }
    request = {"command": "worker", "repository": str(candidate)}
    consumed: list[bool] = []
    monkeypatch.setattr(
        process_runner,
        "_verify_repositories",
        lambda _contract: (candidate, {}, "a" * 40, "b" * 40),
    )
    monkeypatch.setattr(
        process_runner,
        "_verify_resource_order",
        lambda _contract, _request_id: ("functional", 1, "cycle_1.functional"),
    )
    monkeypatch.setattr(process_runner, "_require_package_artifacts", lambda *_a, **_k: None)
    monkeypatch.setattr(
        process_runner,
        "_request_payload",
        lambda _contract, _request_id: (row, request, tmp_path / "request.json"),
    )
    monkeypatch.setattr(
        process_runner.burnin,
        "external_repository_paths",
        lambda _contract: {"ANYsolver": candidate},
    )
    monkeypatch.setattr(process_runner, "_manager_paths", lambda _contract: manager)
    monkeypatch.setattr(
        process_runner,
        "_load_approval_snapshot",
        lambda _contract: (
            {"candidate": {"commit": "a" * 40, "tree": "b" * 40}},
            {"bytes": 1, "sha256": "e" * 64},
        ),
    )
    monkeypatch.setattr(
        process_runner.burnin,
        "approval_ledger_fields",
        lambda *_args, **_kwargs: ("expected",),
    )
    monkeypatch.setattr(
        process_runner.burnin,
        "_ledger_entries",
        lambda _text, _request_id, state: (
            [("2026-08-26T00:00:00Z", "expected")] if state == "APPROVED" else []
        ),
    )
    monkeypatch.setattr(process_runner, "_ledger_rows", lambda *_args: [])
    monkeypatch.setattr(process_runner, "_execution_environment", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(
        process_runner.burnin,
        "execution_tool_path",
        lambda _contract, _name: Path("powershell.exe"),
    )

    def unproven_acquire(*_args: object, **_kwargs: object) -> tuple[object, object]:
        process_runner._RESOURCE_UNPROVEN_TREE.set()
        completed = subprocess.CompletedProcess(
            args=["acquire"], returncode=0, stdout=b"", stderr=b""
        )
        termination = process_runner._termination_metadata(
            disposition="NORMAL_EXIT",
            policy=policy,
            tree_kill_attempted=False,
            tree_kill_exit_code=None,
            child_exit_observed=True,
        )
        return completed, termination

    monkeypatch.setattr(process_runner, "_run_bounded_control_command", unproven_acquire)
    monkeypatch.setattr(
        process_runner,
        "_reserve_pending_output",
        lambda *_args, **_kwargs: consumed.append(True),
    )
    process_runner._RESOURCE_UNPROVEN_TREE.clear()
    with pytest.raises(
        process_runner.burnin.EvidenceError,
        match="acquisition requires proven control-tree closure",
    ):
        process_runner._run_resource_bounded(
            request_id=request_id,
            contract=contract,
            timeout_policy=policy,
            invocation_deadline=time.monotonic() + 1200.0,
            cycle_execution_capability=(
                process_runner._CYCLE_RESOURCE_EXECUTION_CAPABILITY
            ),
        )
    assert consumed == []
    process_runner._RESOURCE_UNPROVEN_TREE.clear()


def test_failed_finalizer_job_close_prevents_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    contract = _load_contract()
    policy = process_runner._timeout_policy(contract)
    request_id = contract["resource_requests"]["cycle_1"][0]["request_id"]
    candidate = tmp_path / "candidate"
    candidate.mkdir()
    active_lock = tmp_path / "active-lock"
    active_lock.mkdir()
    pending = tmp_path / "pending"
    pending.mkdir()
    manager = {
        "active_lock": active_lock,
        "release": tmp_path / "release.ps1",
    }
    candidate_record = {"commit": "a" * 40, "tree": "b" * 40}
    row = {"request_id": request_id}
    request = {"command": "worker", "repository": str(candidate)}
    published: list[bool] = []
    monkeypatch.setattr(process_runner, "_bootstrap_authority", lambda: None)
    monkeypatch.setattr(process_runner.burnin, "load_contract", lambda: contract)
    monkeypatch.setattr(
        process_runner,
        "_verify_repositories",
        lambda _contract: (candidate, {}, "a" * 40, "b" * 40),
    )
    monkeypatch.setattr(process_runner, "_require_package_artifacts", lambda *_a, **_k: None)
    monkeypatch.setattr(
        process_runner,
        "_resource_position",
        lambda _contract, _request_id: (1, "functional", 0),
    )
    monkeypatch.setattr(process_runner, "_manager_paths", lambda _contract: manager)
    monkeypatch.setattr(process_runner, "_existing_process_directory", lambda *_a, **_k: pending)
    monkeypatch.setattr(process_runner, "_pending_output_directory", lambda *_a, **_k: pending)
    monkeypatch.setattr(
        process_runner,
        "_load_approval_snapshot",
        lambda _contract: (
            {"candidate": candidate_record},
            {"bytes": 1, "sha256": "e" * 64},
        ),
    )
    monkeypatch.setattr(
        process_runner,
        "_request_payload",
        lambda _contract, _request_id: (row, request, tmp_path / "request.json"),
    )
    monkeypatch.setattr(
        process_runner,
        "_load_worker_completion",
        lambda *_a, **_k: {
            "termination": process_runner._termination_metadata(
                disposition="NORMAL_EXIT",
                policy=policy,
                tree_kill_attempted=False,
                tree_kill_exit_code=None,
                child_exit_observed=True,
            )
        },
    )
    monkeypatch.setattr(process_runner, "_recover_manager_reservation", lambda *_a, **_k: False)
    monkeypatch.setattr(process_runner, "_lock_owner", lambda *_a, **_k: None)
    monkeypatch.setattr(
        process_runner.burnin,
        "execution_tool_path",
        lambda _contract, _name: Path("powershell.exe"),
    )
    monkeypatch.setattr(process_runner, "_manager_environment", lambda _contract: {})

    def unproven_release(*_args: object, **_kwargs: object) -> tuple[object, object]:
        process_runner._RESOURCE_UNPROVEN_TREE.set()
        completed = subprocess.CompletedProcess(
            args=["release"], returncode=0, stdout=b"", stderr=b""
        )
        termination = process_runner._termination_metadata(
            disposition="NORMAL_EXIT",
            policy=policy,
            tree_kill_attempted=False,
            tree_kill_exit_code=None,
            child_exit_observed=True,
        )
        return completed, termination

    monkeypatch.setattr(process_runner, "_run_bounded_control_command", unproven_release)
    monkeypatch.setattr(
        process_runner,
        "_publish_resource_result",
        lambda *_args, **_kwargs: published.append(True),
    )
    process_runner._RESOURCE_UNPROVEN_TREE.clear()
    with pytest.raises(
        process_runner.burnin.EvidenceError,
        match="publication requires proven control-tree closure",
    ):
        process_runner.finalize_resource(
            request_id=request_id,
            invocation_deadline=time.monotonic() + 1200.0,
        )
    assert published == []
    process_runner._RESOURCE_UNPROVEN_TREE.clear()


def test_resource_watchdog_uses_one_absolute_invocation_deadline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    contract = _load_contract()
    policy = process_runner._timeout_policy(contract)
    started: list[bool] = []

    class FakeThread:
        def __init__(self, **kwargs: object) -> None:
            assert kwargs["daemon"] is True
            assert kwargs["name"] == "s3-q4-resource-wall-watchdog"

        def start(self) -> None:
            started.append(True)

    monkeypatch.setattr(process_runner.time, "monotonic", lambda: 100.0)
    monkeypatch.setattr(process_runner.threading, "Thread", FakeThread)
    deadline, stop, _thread = process_runner._start_resource_invocation_watchdog(policy)
    assert deadline == 1300.0
    assert started == [True]
    assert not stop.is_set()
    stop.set()


def test_cli_dispatch_does_not_bootstrap_before_bounded_wrapper(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[str] = []
    stop = threading.Event()

    class FakeThread:
        def join(self, timeout: float) -> None:
            assert timeout == 0.1
            events.append("join")

    monkeypatch.setattr(
        process_runner,
        "_arm_invocation_job_boundary",
        lambda: events.append("job"),
    )

    def start_watchdog(_policy: object) -> tuple[float, threading.Event, FakeThread]:
        events.append("watchdog")
        return 1300.0, stop, FakeThread()

    monkeypatch.setattr(
        process_runner,
        "_start_resource_invocation_watchdog",
        start_watchdog,
    )

    def fail_bootstrap() -> None:
        events.append("bootstrap")
        raise RuntimeError("simulated authority rejection")

    monkeypatch.setattr(
        process_runner,
        "_bootstrap_authority",
        fail_bootstrap,
    )
    with pytest.raises(RuntimeError, match="authority rejection"):
        process_runner.main(["local", "--lane", "quick"])
    assert stop.is_set()
    assert events == ["job", "watchdog", "bootstrap", "join"]


def test_job_assignment_failure_latches_unproven_suspended_child(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class UnkillableSuspendedWorker:
        pid = 4545

        def kill(self) -> None:
            raise OSError("simulated suspended-worker kill failure")

        def wait(self, timeout: float) -> int:
            raise subprocess.TimeoutExpired(cmd="suspended", timeout=timeout)

    worker = UnkillableSuspendedWorker()
    process_runner._RESOURCE_UNPROVEN_TREE.clear()
    monkeypatch.setattr(process_runner, "_create_kill_on_close_job", lambda: 123)
    monkeypatch.setattr(
        process_runner.subprocess, "Popen", lambda *_args, **_kwargs: worker
    )
    monkeypatch.setattr(
        process_runner,
        "_assign_worker_to_job_and_resume",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            OSError("simulated job assignment failure")
        ),
    )
    with pytest.raises(OSError, match="assignment failure"):
        process_runner._launch_bounded_worker(["worker.exe"])
    assert process_runner._RESOURCE_UNPROVEN_TREE.is_set()
    assert process_runner._ACTIVE_SUSPENDED_WORKERS[worker.pid] is worker
    with process_runner._ACTIVE_JOB_LOCK:
        process_runner._ACTIVE_SUSPENDED_WORKERS.clear()
    process_runner._RESOURCE_UNPROVEN_TREE.clear()


@pytest.mark.skipif(os.name != "nt", reason="Windows Job Object integration probe")
def test_windows_job_object_closure_terminates_the_complete_descendant_tree(
    tmp_path: Path,
) -> None:
    import ctypes
    from ctypes import wintypes

    started = time.monotonic()
    grandchild_pid_path = tmp_path / "grandchild.pid"
    child_code = (
        "import pathlib,subprocess,sys,time;"
        "child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)']);"
        f"pathlib.Path({str(grandchild_pid_path)!r}).write_text(str(child.pid),encoding='utf-8');"
        "time.sleep(60)"
    )
    worker, job_handle = process_runner._launch_bounded_worker(
        [sys.executable, "-c", child_code],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    grandchild_handle = None
    try:
        assert job_handle is not None
        marker_deadline = time.monotonic() + 5.0
        while not grandchild_pid_path.is_file() and time.monotonic() < marker_deadline:
            time.sleep(0.02)
        grandchild_pid = int(grandchild_pid_path.read_text(encoding="utf-8"))
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel32.OpenProcess.restype = wintypes.HANDLE
        kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        kernel32.WaitForSingleObject.restype = wintypes.DWORD
        kernel32.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
        kernel32.TerminateProcess.restype = wintypes.BOOL
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel32.CloseHandle.restype = wintypes.BOOL
        grandchild_handle = kernel32.OpenProcess(0x00100001, False, grandchild_pid)
        assert grandchild_handle
        assert process_runner._close_job_handle(job_handle) is True
        job_handle = None
        worker.wait(timeout=5.0)
        assert kernel32.WaitForSingleObject(grandchild_handle, 5000) == 0
    finally:
        if worker.poll() is None:
            worker.kill()
            worker.wait(timeout=5.0)
        if job_handle is not None:
            process_runner._close_job_handle(job_handle)
        if grandchild_handle:
            if kernel32.WaitForSingleObject(grandchild_handle, 0) != 0:
                kernel32.TerminateProcess(grandchild_handle, 1)
                kernel32.WaitForSingleObject(grandchild_handle, 5000)
            kernel32.CloseHandle(grandchild_handle)
    assert time.monotonic() - started < 11.0


@pytest.mark.skipif(os.name != "nt", reason="Windows invocation Job Object probe")
def test_invocation_job_contains_pre_worker_descendants(tmp_path: Path) -> None:
    import ctypes
    from ctypes import wintypes

    started = time.monotonic()
    grandchild_pid_path = tmp_path / "pre-worker-grandchild.pid"
    coordinator_code = (
        "import pathlib,subprocess,sys,time;"
        f"sys.path.insert(0,{str(REFERENCE)!r});"
        "sys.dont_write_bytecode=True;"
        "import e4_pl_s3_q4_process_runner as runner;"
        "runner._arm_invocation_job_boundary();"
        "runner._start_resource_invocation_watchdog({"
        "'wall_limit_seconds':1.0,'termination_grace_seconds':0.5,"
        "'timeout_exit_code':124});"
        "child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)']);"
        f"pathlib.Path({str(grandchild_pid_path)!r}).write_text(str(child.pid),encoding='utf-8');"
        "time.sleep(60)"
    )
    coordinator = subprocess.Popen(
        [sys.executable, "-I", "-c", coordinator_code],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    grandchild_handle = None
    try:
        marker_deadline = time.monotonic() + 5.0
        while not grandchild_pid_path.is_file() and time.monotonic() < marker_deadline:
            time.sleep(0.02)
        grandchild_pid = int(grandchild_pid_path.read_text(encoding="utf-8"))
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel32.OpenProcess.restype = wintypes.HANDLE
        kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        kernel32.WaitForSingleObject.restype = wintypes.DWORD
        kernel32.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
        kernel32.TerminateProcess.restype = wintypes.BOOL
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel32.CloseHandle.restype = wintypes.BOOL
        grandchild_handle = kernel32.OpenProcess(0x00100001, False, grandchild_pid)
        assert grandchild_handle
        assert coordinator.wait(timeout=5.0) == 124
        assert kernel32.WaitForSingleObject(grandchild_handle, 5000) == 0
    finally:
        if coordinator.poll() is None:
            coordinator.kill()
            coordinator.wait(timeout=5.0)
        if grandchild_handle:
            if kernel32.WaitForSingleObject(grandchild_handle, 0) != 0:
                kernel32.TerminateProcess(grandchild_handle, 1)
                kernel32.WaitForSingleObject(grandchild_handle, 5000)
            kernel32.CloseHandle(grandchild_handle)
    assert time.monotonic() - started < 11.0


def test_external_request_ids_commands_and_hashes_are_preregistered() -> None:
    contract = _load_contract()
    rows = [
        row
        for cycle in ("cycle_1", "cycle_2")
        for row in contract["resource_requests"][cycle]
    ]
    assert len({row["request_id"] for row in rows}) == 6
    live_ids = [row["request_id"] for row in rows]
    assert live_ids == CURRENT_REQUEST_IDS
    assert [
        {"bytes": row["bytes"], "sha256": row["request_sha256"]} for row in rows
    ] == CURRENT_REQUEST_FILE_RECORDS
    assert set(live_ids).isdisjoint(
        {
            *FAILED_ATTEMPT_1_REQUEST_IDS,
            *FAILED_ATTEMPT_2_REQUEST_IDS,
            *FAILED_ATTEMPT_3_REQUEST_IDS,
            *FAILED_ATTEMPT_4_REQUEST_IDS,
            *FAILED_ATTEMPT_5_REQUEST_IDS,
            *FAILED_ATTEMPT_6_REQUEST_IDS,
            *FAILED_ATTEMPT_7_REQUEST_IDS,
            *FAILED_ATTEMPT_8_REQUEST_IDS,
            *FAILED_ATTEMPT_9_REQUEST_IDS,
            *FAILED_ATTEMPT_10_REQUEST_IDS,
        }
    )
    approval = burnin.validate_resource_approval_authority(contract)
    assert approval["request_ids"] == live_ids
    assert [row["lane"] for row in rows[:3]] == ["functional", "anyfem", "performance"]
    assert rows[0]["command_sha256"] != rows[3]["command_sha256"]
    assert rows[1]["command_sha256"] == rows[4]["command_sha256"]
    assert rows[2]["command_sha256"] == rows[5]["command_sha256"]
    requests_root = RESOURCE_MANAGER / "requests"
    if not requests_root.is_dir():
        assert os.environ.get("GITHUB_ACTIONS") == "true"
        return
    ledger = RESOURCE_MANAGER / "ledger.md"
    assert ledger.is_file()
    ledger_text = ledger.read_text(encoding="utf-8")
    assert all(request_id not in ledger_text for request_id in FAILED_ATTEMPT_1_REQUEST_IDS)
    assert all(request_id not in ledger_text for request_id in FAILED_ATTEMPT_3_REQUEST_IDS)
    assert all(request_id not in ledger_text for request_id in FAILED_ATTEMPT_5_REQUEST_IDS)
    assert all(request_id not in ledger_text for request_id in FAILED_ATTEMPT_6_REQUEST_IDS)
    assert all(request_id not in ledger_text for request_id in FAILED_ATTEMPT_7_REQUEST_IDS)
    assert all(request_id not in ledger_text for request_id in FAILED_ATTEMPT_8_REQUEST_IDS)
    assert all(request_id not in ledger_text for request_id in FAILED_ATTEMPT_9_REQUEST_IDS)
    assert all(request_id not in ledger_text for request_id in live_ids)
    assert [
        state
        for state in ("APPROVED", "EXECUTION_STARTED", "COMPLETED_FAIL")
        if burnin._ledger_entries(
            ledger_text, FAILED_ATTEMPT_10_REQUEST_IDS[0], state
        )
    ] == ["APPROVED", "EXECUTION_STARTED", "COMPLETED_FAIL"]
    for request_id in FAILED_ATTEMPT_10_REQUEST_IDS[1:]:
        assert len(burnin._ledger_entries(ledger_text, request_id, "APPROVED")) == 1
        assert len(
            burnin._ledger_entries(ledger_text, request_id, "CANCELLED_NOT_RUN")
        ) == 1
        assert not burnin._ledger_entries(ledger_text, request_id, "EXECUTION_STARTED")
    assert len(
        burnin._ledger_entries(
            ledger_text, FAILED_ATTEMPT_4_REQUEST_IDS[0], "INTERRUPTED_INCOMPLETE"
        )
    ) == 1
    assert len(
        burnin._ledger_entries(
            ledger_text, FAILED_ATTEMPT_4_REQUEST_IDS[0], "EXECUTION_STARTED"
        )
    ) == 1
    assert not burnin._ledger_entries(
        ledger_text, FAILED_ATTEMPT_4_REQUEST_IDS[0], "COMPLETED_FAIL"
    )
    for request_id in FAILED_ATTEMPT_4_REQUEST_IDS[1:]:
        assert len(
            burnin._ledger_entries(ledger_text, request_id, "CANCELLED_NOT_RUN")
        ) == 1
        assert not burnin._ledger_entries(ledger_text, request_id, "EXECUTION_STARTED")
    for request_id in FAILED_ATTEMPT_2_REQUEST_IDS:
        assert len(burnin._ledger_entries(ledger_text, request_id, "APPROVED")) == 1
        assert len(
            burnin._ledger_entries(ledger_text, request_id, "CANCELLED_NOT_RUN")
        ) == 1
        assert not burnin._ledger_entries(ledger_text, request_id, "EXECUTION_STARTED")
        assert not burnin._ledger_entries(ledger_text, request_id, "COMPLETED_PASS")
        assert not burnin._ledger_entries(ledger_text, request_id, "COMPLETED_FAIL")
    for row in rows:
        path = requests_root / f"{row['request_id']}.json"
        assert _file_record(path) == {
            "bytes": row["bytes"],
            "sha256": row["request_sha256"],
        }
        request = burnin.strict_json_load(path)
        assert request["request_id"] == row["request_id"]
        assert request["status"] == "PENDING"
        assert request["estimate_minutes"] <= 20
        assert hashlib.sha256(request["command"].encode()).hexdigest() == row["command_sha256"]
        if row["lane"] == "anyfem":
            assert Path(request["repository"]) == ANYFEM_FREEZE
        else:
            assert Path(request["repository"]) == FINAL_FREEZE
        assert str(FINAL_FREEZE) in request["command"]
        assert "q1m-anymesh-frozen" in request["command"]
        assert "q1m-anygeometry-frozen" in request["command"]
        assert "s3-q4-anymaterial-74100a9" in request["command"]
        assert "s3-q4-anyfileio-9b1e5ad" in request["command"]
        assert "s3-q4-anymesh-2d8478c" not in request["command"]
        if row["lane"] == "functional":
            assert "run_e4_pl_burnin_gate.py functional-wave --cycle" in request["command"]
        assert "s3-q4-anygeometry-069f22f" not in request["command"]


def test_success_and_blocked_result_schemas_are_strict_and_fail_fast() -> None:
    contract = _load_contract()
    success = _valid_result(contract)
    assert burnin.validate_result(success, contract=contract) == success
    assert burnin.strict_json_loads(burnin.canonical_json_bytes(success)) == success

    blocked = copy.deepcopy(success)
    blocked["common_lanes"]["quick"]["processes"] = [
        _process(
            "FAIL",
            command_sha256=contract["non_resource_commands"]["quick"][
                "command_sha256"
            ],
            started_second=0,
        )
    ]
    blocked["common_lanes"]["quick"]["status"] = "FAIL"
    for lane, count in (("package", 1), ("additive", 3)):
        blocked["common_lanes"][lane]["processes"] = [
            _process("NOT_RUN") for _index in range(count)
        ]
        blocked["common_lanes"][lane]["status"] = "NOT_RUN"
    for cycle in blocked["cycles"]:
        for lane in ("functional", "anyfem", "performance"):
            cycle_number = cycle["cycle"]
            request = next(
                row
                for row in contract["resource_requests"][f"cycle_{cycle_number}"]
                if row["lane"] == lane
            )
            cycle["lanes"][lane] = _process(
                "NOT_RUN", request_id=request["request_id"]
            )
        cycle["status"] = "NOT_RUN"
    blocked["hard_gates"] = {
        key: "NOT_EVALUATED" for key in blocked["hard_gates"]
    }
    blocked["package_artifacts"] = None
    blocked["performance_observations"] = None
    blocked["ledger_snapshots"] = {
        "approval": None,
        "cycle_1": None,
        "cycle_2": None,
    }
    blocked["terminal"] = contract["adjudication"]["result_blocked_terminal"]
    assert burnin.validate_result(blocked, contract=contract) == blocked

    package_failure = copy.deepcopy(blocked)
    package_failure["common_lanes"]["quick"] = copy.deepcopy(
        success["common_lanes"]["quick"]
    )
    package_failure["common_lanes"]["package"]["processes"] = [
        _process(
            "FAIL",
            command_sha256=contract["non_resource_commands"]["package"][
                "command_sha256"
            ],
            started_second=2,
        )
    ]
    package_failure["common_lanes"]["package"]["status"] = "FAIL"
    package_failure["package_artifacts"] = {
        "result": None,
        "wheel": {
            "bytes": 1,
            "filename": "anysolver-0.3.1-py3-none-any.whl",
            "sha256": "f" * 64,
        },
    }
    assert burnin.validate_result(package_failure, contract=contract) == package_failure
    malformed_partial = copy.deepcopy(package_failure)
    malformed_partial["package_artifacts"].pop("result")
    with pytest.raises(burnin.EvidenceError, match="keys mismatch"):
        burnin.validate_result(malformed_partial, contract=contract)
    malformed_partial = copy.deepcopy(package_failure)
    malformed_partial["package_artifacts"]["wheel"]["sha256"] = "0"
    with pytest.raises(burnin.EvidenceError, match="SHA-256"):
        burnin.validate_result(malformed_partial, contract=contract)

    premature = copy.deepcopy(blocked)
    premature["terminal"] = contract["adjudication"]["result_success_terminal"]
    with pytest.raises(burnin.EvidenceError, match="terminal"):
        burnin.validate_result(premature, contract=contract)
    non_fail_fast = copy.deepcopy(blocked)
    non_fail_fast["common_lanes"]["package"]["processes"] = [
        _process(
            command_sha256=contract["non_resource_commands"]["package"][
                "command_sha256"
            ],
            started_second=2,
        )
    ]
    non_fail_fast["common_lanes"]["package"]["status"] = "PASS"
    with pytest.raises(burnin.EvidenceError, match="later lane"):
        burnin.validate_result(non_fail_fast, contract=contract)

    cycle_two_failure = copy.deepcopy(success)
    failed = cycle_two_failure["cycles"][1]["lanes"]["functional"]
    failed["status"] = "FAIL"
    failed["exit_code"] = 1
    for lane in ("anyfem", "performance"):
        row = next(
            item
            for item in contract["resource_requests"]["cycle_2"]
            if item["lane"] == lane
        )
        cycle_two_failure["cycles"][1]["lanes"][lane] = _process(
            "NOT_RUN", request_id=row["request_id"]
        )
    cycle_two_failure["cycles"][1]["status"] = "FAIL"
    cycle_two_failure["hard_gates"] = {
        "batch_path_equality": "NOT_EVALUATED",
        "q4_numerical_parity": "NOT_EVALUATED",
        "qualified_s3_opt_in": "PASS",
        "s3_default_legacy": "PASS",
        "warm_cache_reuse": "NOT_EVALUATED",
    }
    cycle_two_failure["performance_observations"] = None
    cycle_two_failure["terminal"] = contract["adjudication"][
        "result_blocked_terminal"
    ]
    assert burnin.validate_result(cycle_two_failure, contract=contract) == cycle_two_failure
    assert contract["adjudication"]["clean_cycle_counter_policy"] == (
        "RESET_TO_ZERO_ON_ANY_FAILURE"
    )


def test_duplicate_nonfinite_hash_and_request_reuse_mutations_are_rejected() -> None:
    with pytest.raises(burnin.EvidenceError, match="duplicate JSON key"):
        burnin.strict_json_loads('{"a":1,"a":2}')
    with pytest.raises(burnin.EvidenceError, match="non-finite"):
        burnin.strict_json_loads('{"a":NaN}')

    contract = _load_contract()
    mutation = copy.deepcopy(contract)
    mutation["resource_requests"]["cycle_2"][0]["request_id"] = (
        mutation["resource_requests"]["cycle_1"][0]["request_id"]
    )
    with pytest.raises(burnin.EvidenceError, match="unique"):
        burnin.validate_result(_valid_result(mutation), contract=mutation)

    result = _valid_result(contract)
    result["cycles"][0]["lanes"]["functional"]["command_sha256"] = "0" * 64
    with pytest.raises(burnin.EvidenceError, match="command_sha256 mismatch"):
        burnin.validate_result(result, contract=contract)

    result = _valid_result(contract)
    result["common_lanes"]["quick"]["processes"][0]["producer_sha256"] = "0" * 64
    with pytest.raises(burnin.EvidenceError, match="producer_sha256 mismatch"):
        burnin.validate_result(result, contract=contract)

    result = _valid_result(contract)
    result["common_lanes"]["package"]["processes"][0]["started_at"] = (
        "2026-08-26T11:59:59+02:00"
    )
    with pytest.raises(burnin.EvidenceError, match="chronology"):
        burnin.validate_result(result, contract=contract)

    result = _valid_result(contract)
    timing = result["performance_observations"][0]["observation"][
        "performance_baseline"
    ]["measurements"]["qualified_q4_cached_tangent"]
    timing["median_ns"] += 1
    with pytest.raises(burnin.EvidenceError, match="timing statistics"):
        burnin.validate_result(result, contract=contract)

    previous_terminal = dt.datetime.fromisoformat("2026-08-26T12:00:05+02:00")
    successor_start = dt.datetime.fromisoformat("2026-08-26T12:00:04+02:00")
    with pytest.raises(burnin.EvidenceError, match="predecessor terminal"):
        burnin._require_successor_after_terminal(
            successor_start, previous_terminal, "0" * 32
        )


def test_filtered_ledger_snapshot_and_pending_schemas_are_strict() -> None:
    contract = _load_contract()
    candidate = {"commit": "1" * 40, "tree": "2" * 40}
    requests = [
        row
        for cycle in ("cycle_1", "cycle_2")
        for row in contract["resource_requests"][cycle]
    ]
    approval_rows = [
        {
            "fields": [
                row["request_id"],
                "APPROVED",
                f"task-{index}",
                "C:\\repository",
                "scope",
                "10 minutes",
                "approved",
            ],
            "timestamp": f"2026-08-26T12:00:0{index}+02:00",
        }
        for index, row in enumerate(requests)
    ]
    approval = {
        "candidate": candidate,
        "kind": "APPROVAL",
        "request_order": [row["request_id"] for row in requests],
        "rows": approval_rows,
        "schema": burnin.LEDGER_SNAPSHOT_SCHEMA,
        "source_ledger": {"bytes": 1, "sha256": "a" * 64},
    }
    assert burnin.validate_ledger_snapshot(approval, contract=contract) == approval
    duplicate = copy.deepcopy(approval)
    duplicate["request_order"][1] = duplicate["request_order"][0]
    with pytest.raises(burnin.EvidenceError, match="ordering"):
        burnin.validate_ledger_snapshot(duplicate, contract=contract)

    cycle_rows = []
    for index, row in enumerate(requests[:3]):
        cycle_rows.append(
            {
                "approval": approval_rows[index],
                "execution_started": {
                    "fields": [
                        row["request_id"],
                        "EXECUTION_STARTED",
                        f"task-{index}",
                        "C:\\repository",
                        "Exact immutable request launch committed",
                        "10 minutes",
                        "launch",
                    ],
                    "timestamp": f"2026-08-26T12:01:0{index}+02:00",
                },
                "terminal": {
                    "fields": [
                        row["request_id"],
                        "COMPLETED_PASS",
                        f"task-{index}",
                        "C:\\repository",
                        "executed",
                        "10 minutes",
                        "pending manifest SHA-256 " + "b" * 64,
                    ],
                    "timestamp": f"2026-08-26T12:02:0{index}+02:00",
                },
            }
        )
    cycle = {
        "candidate": candidate,
        "cycle": 1,
        "kind": "CYCLE_TERMINAL",
        "predecessor": {"bytes": 1, "sha256": "c" * 64},
        "request_order": [row["request_id"] for row in requests[:3]],
        "rows": cycle_rows,
        "schema": burnin.LEDGER_SNAPSHOT_SCHEMA,
        "source_ledger": {"bytes": 2, "sha256": "d" * 64},
    }
    assert burnin.validate_ledger_snapshot(cycle, contract=contract) == cycle
    malformed = copy.deepcopy(cycle)
    malformed["rows"][0]["terminal"]["fields"][6] = "missing binding"
    with pytest.raises(burnin.EvidenceError, match="pending manifest"):
        burnin.validate_ledger_snapshot(malformed, contract=contract)

    request = requests[0]
    pending = {
        "approval_snapshot": {"bytes": 1, "sha256": "1" * 64},
        "candidate": candidate,
        "cycle": 1,
        "lane": "functional",
        "launch": {"bytes": 1, "sha256": "2" * 64},
        "request": {
            "bytes": request["bytes"],
            "request_id": request["request_id"],
            "sha256": request["request_sha256"],
        },
        "result": {"bytes": 1, "sha256": "3" * 64},
        "schema": burnin.PENDING_MANIFEST_SCHEMA,
        "stderr": {"bytes": 0, "sha256": "4" * 64},
        "stdout": {"bytes": 1, "sha256": "5" * 64},
        "target_directory": "cycle-1-functional",
    }
    assert burnin.validate_pending_manifest(pending, contract=contract) == pending
    pending["target_directory"] = "wrong"
    with pytest.raises(burnin.EvidenceError, match="target"):
        burnin.validate_pending_manifest(pending, contract=contract)


def test_manager_reservation_and_unconsumed_output_are_atomic(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manager = {"active_lock": tmp_path / "active-lock"}
    candidate = {"commit": "1" * 40, "tree": "2" * 40}
    request_order = ["3" * 32]
    ownerless = tmp_path / ".active-lock.prepared-2147483647-1"
    ownerless.mkdir()
    owner = process_runner._acquire_manager_reservation(
        manager,
        candidate=candidate,
        request_order=request_order,
        purpose="TEST_RESERVATION",
    )
    assert not ownerless.exists()
    assert (manager["active_lock"] / "owner.json").is_file()
    assert not process_runner._recover_manager_reservation(
        manager,
        candidate=candidate,
        purposes={"TEST_RESERVATION"},
        request_orders={tuple(request_order)},
    )
    assert manager["active_lock"].is_dir()
    with pytest.raises(burnin.EvidenceError, match="occupied"):
        process_runner._acquire_manager_reservation(
            manager,
            candidate=candidate,
            request_order=request_order,
            purpose="CONTENDING_RESERVATION",
        )
    process_runner._release_manager_reservation(manager, owner)
    assert not manager["active_lock"].exists()

    stale = process_runner._acquire_manager_reservation(
        manager,
        candidate=candidate,
        request_order=request_order,
        purpose="TEST_STALE_RESERVATION",
    )
    stale["process_id"] = 2**31 - 1
    (manager["active_lock"] / "owner.json").write_bytes(
        burnin.canonical_json_bytes(stale)
    )
    assert process_runner._recover_manager_reservation(
        manager,
        candidate=candidate,
        purposes={"TEST_STALE_RESERVATION"},
        request_orders={tuple(request_order)},
    )
    assert not manager["active_lock"].exists()

    pending = tmp_path / ".pending-resource"
    pending.mkdir()
    (pending / "launch.json").write_bytes(b"{}\n")
    process_runner._discard_unconsumed_pending(pending)
    assert not pending.exists()

    reparse = tmp_path / "reparse.json"
    reparse.write_bytes(b"{}\n")
    original = burnin.is_reparse_point
    monkeypatch.setattr(
        burnin,
        "is_reparse_point",
        lambda path: Path(path) == reparse or original(Path(path)),
    )
    with pytest.raises(burnin.EvidenceError, match="canonical JSON"):
        process_runner._load_canonical_json(reparse)


def test_worker_checkpoint_can_publish_without_reexecuting(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    contract = copy.deepcopy(_load_contract())
    output_root = tmp_path / "burnin"
    contract["non_resource_commands"]["output_root"] = str(output_root)
    row = contract["resource_requests"]["cycle_1"][0]
    prefix = "cycle_1.functional"
    candidate = {"commit": "1" * 40, "tree": "2" * 40}
    approval_record = {"bytes": 1, "sha256": "3" * 64}
    request = {
        "estimate_minutes": 10,
        "repository": r"C:\frozen-repository",
        "request_id": row["request_id"],
        "task": "bounded functional gate",
    }
    output_dir = process_runner._reserve_pending_output(contract, prefix)
    launch = {
        "approval_snapshot": approval_record,
        "candidate": candidate,
        "command_sha256": row["command_sha256"],
        "cycle": 1,
        "lane": "functional",
        "lock_owner": {"bytes": 1, "sha256": "4" * 64},
        "request": {
            "bytes": row["bytes"],
            "request_id": row["request_id"],
            "sha256": row["request_sha256"],
        },
        "schema": "anysolver.e4-pl-s3-q4-resource-launch-v1",
        "started_at": "2026-08-26T10:00:00Z",
        "target_directory": "cycle-1-functional",
    }
    burnin.validate_resource_launch(launch, contract=contract)
    launch_path = output_dir / "launch.json"
    launch_path.write_bytes(burnin.canonical_json_bytes(launch))
    (output_dir / "stdout.txt").write_bytes(b"worker output\n")
    (output_dir / "stderr.txt").write_bytes(b"")
    completed = subprocess.CompletedProcess(
        args=["frozen-command"], returncode=0, stdout=b"worker output\n", stderr=b""
    )
    process_runner._write_worker_completion(
        output_dir,
        candidate_commit=candidate["commit"],
        candidate_tree=candidate["tree"],
        command="ignored",
        completed=completed,
        elapsed_seconds=1.0,
        ended_at="2026-08-26T10:00:01Z",
        execution_state="EXECUTED",
        request_id=row["request_id"],
        request_sha256=row["request_sha256"],
        started_at="2026-08-26T10:00:00Z",
        approval_snapshot=approval_record,
        termination={
            "child_exit_observed": True,
            "disposition": "NORMAL_EXIT",
            "tree_kill_attempted": False,
            "tree_kill_exit_code": None,
            "wall_limit_seconds": 1200,
        },
    )
    completion_path = output_dir / "worker-completion.json"
    completion = burnin.strict_json_load(completion_path)
    completion["command_sha256"] = row["command_sha256"]
    completion_path.write_bytes(burnin.canonical_json_bytes(completion))

    ledger = tmp_path / "ledger.md"
    ledger.write_text("# isolated ledger\n", encoding="utf-8", newline="")
    started_fields = burnin.execution_started_ledger_fields(
        request, launch, burnin.file_hash_record(launch_path)
    )
    process_runner._append_ledger_fields(
        ledger, started_fields, timestamp="2026-08-26T10:00:00Z"
    )
    manager = {"ledger": ledger}
    monkeypatch.setattr(process_runner, "_manager_paths", lambda _contract: manager)
    monkeypatch.setattr(
        burnin,
        "_git",
        lambda _repository, *args, **_kwargs: (
            candidate["tree"] if args[-1] == "HEAD^{tree}" else candidate["commit"]
        ),
    )
    monkeypatch.setattr(
        process_runner,
        "_run_resource_command",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("worker must not be rerun during publication recovery")
        ),
    )
    monkeypatch.setattr(
        process_runner,
        "_require_package_artifacts",
        lambda *args, **kwargs: {},
    )
    manifest = process_runner._publish_resource_result(
        contract,
        prefix=prefix,
        candidate=candidate,
        request_row=row,
        request=request,
        approval_snapshot=approval_record,
        lock_released=True,
    )
    final = burnin.process_output_directory(contract, prefix)
    assert manifest["exit_code"] == 0
    assert final.is_dir() and not output_dir.exists()
    assert {path.name for path in final.iterdir()} == {
        "launch.json",
        "pending-manifest.json",
        "result.json",
        "stderr.txt",
        "stdout.txt",
    }
    assert len(burnin._ledger_entries(ledger.read_text(encoding="utf-8"), row["request_id"], "COMPLETED_PASS")) == 1


def test_resource_state_machine_order_and_finalizer_prefixes_are_frozen() -> None:
    contract = _load_contract()
    powershell = Path(contract["execution"]["environment_guard"]["powershell"]["path"])
    script = RESOURCE_MANAGER / "acquire-test.ps1"
    request_id = "0" * 32
    assert process_runner._manager_script_args(powershell, script, request_id) == [
        str(powershell),
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(script),
        "-RequestId",
        request_id,
    ]
    for cycle in (1, 2):
        for row in contract["resource_requests"][f"cycle_{cycle}"]:
            observed_cycle, lane, _index = process_runner._resource_position(
                contract, row["request_id"]
            )
            assert f"cycle_{observed_cycle}.{lane}" == f"cycle_{cycle}.{row['lane']}"
    source = (REFERENCE / "e4_pl_s3_q4_process_runner.py").read_text(encoding="utf-8")
    assert source.count('"-File"') == 1
    assert source.count("_manager_script_args(") == 4
    assert "acquired, _acquire_termination = _run_bounded_control_command(" in source
    assert "released, _release_termination = _run_bounded_control_command(" in source
    verify_start = source.index("def _verify_repositories")
    verify_end = source.index("\ndef _run(", verify_start)
    verify_source = source[verify_start:verify_end]
    scope_check = verify_source.index(
        'list(repositories) != contract["execution"]["clean_status_scope"]'
    )
    complete_clean_probe = verify_source.index("burnin.strict_clean_status_record")
    candidate_authority = verify_source.index("_authority_commit(candidate, contract)")
    assert scope_check < complete_clean_probe < candidate_authority

    local_start = source.index("def _run_local_bounded")
    local_clean = source.index("_verify_repositories(contract)", local_start)
    local_reserve = source.index("_reserve_output(output_dir)", local_start)
    local_worker = source.index("completed, started_at", local_start)
    assert local_clean < local_reserve < local_worker

    run_start = source.index("def _run_resource_bounded")
    resource_clean = source.index("_verify_repositories(contract)", run_start)
    acquire = source.index("acquired, _acquire_termination", run_start)
    reserve = source.index("_reserve_pending_output", acquire)
    execution_started = source.index("_append_execution_started", run_start)
    assert resource_clean < acquire < reserve < execution_started
    assert "_write_worker_completion(" in source[run_start:]
    publish_start = source.index("def _publish_resource_result")
    assert source.index("_append_terminal_ledger", publish_start) < source.index(
        "_atomic_promote_directory", publish_start
    )
    validator_source = VALIDATOR_PATH.read_text(encoding="utf-8")
    assert 'launch["candidate"] != pending["candidate"]' in validator_source
    assert 'ledger_process["candidate_commit"]' in validator_source
    approve_start = source.index("def approve_requests")
    approval_clean = source.index("_verify_repositories(contract)", approve_start)
    approval_mutation = source.index("_acquire_manager_reservation", approve_start)
    assert approval_clean < approval_mutation
    assert source.index("_recover_manager_reservation", approve_start) < source.index(
        "_acquire_manager_reservation", approve_start
    )
    finalize_start = source.index("def finalize_resource")
    completion_check = source.index("_load_worker_completion", finalize_start)
    resource_release = source.index(
        'powershell, manager["release"], request_id', finalize_start
    )
    assert completion_check < resource_release
    assert source.index("_require_package_artifacts", finalize_start) < resource_release
    assert source.index("_require_package_artifacts", publish_start) < source.index(
        "_append_terminal_ledger", publish_start
    )
    gate_source = (ROOT / "scripts" / "run_e4_pl_burnin_gate.py").read_text(
        encoding="utf-8"
    )
    final_identity_start = gate_source.index("def _validate_repository_identities")
    final_identity_end = gate_source.index(
        "\ndef validate_final_gate_result", final_identity_start
    )
    final_identity_source = gate_source[final_identity_start:final_identity_end]
    assert 'empty_status = contract["execution"]["clean_status_empty"]' in (
        final_identity_source
    )
    assert 'repository_order = contract["execution"]["clean_status_scope"]' in (
        final_identity_source
    )
    assert "_functional_source_status(repository) != empty_status" in final_identity_source
    assert '"--ignored=matching"' not in final_identity_source


def test_process_runner_sanitizes_pytest_controls_and_reserves_exact_outputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    contract = _load_contract()
    guard = contract["execution"]["environment_guard"]
    cache_pairs = {
        prefix: burnin.execution_cache_paths(contract, prefix)
        for prefix in burnin.PROCESS_DIRECTORY_NAMES
    }
    assert len({path for pair in cache_pairs.values() for path in pair}) == 2 * len(
        cache_pairs
    )
    monkeypatch.setenv("PYTEST_ADDOPTS", "--collect-only")
    monkeypatch.setenv("PYTEST_PLUGINS", "hostile_plugin")
    monkeypatch.setenv("GIT_DIR", str(tmp_path / "hostile-git-dir"))
    monkeypatch.setenv("GIT_WORK_TREE", str(tmp_path / "hostile-work-tree"))
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setenv("PYTHONWARNINGS", "error")
    monkeypatch.setenv("PYTHONINSPECT", "1")
    monkeypatch.setenv("ANYSOLVER_BURNIN_ACTIVE_TEST_LANE", "quick")
    tools_available = all(
        Path(guard[name]["path"]).is_file()
        for name in ("git", "git_engine", "powershell", "python")
    )
    if tools_available:
        assert burnin.validate_git_runtime(contract) == guard["git_runtime"]
        gate_spec = importlib.util.spec_from_file_location(
            "s3_q4_git_policy_probe",
            ROOT / "scripts" / "run_e4_pl_burnin_gate.py",
        )
        assert gate_spec is not None and gate_spec.loader is not None
        gate = importlib.util.module_from_spec(gate_spec)
        gate_spec.loader.exec_module(gate)
        crlf_repository = tmp_path / "crlf-repository"
        crlf_repository.mkdir()
        git = str(Path(guard["git"]["path"]))
        monkeypatch.setenv("ANYSOLVER_FROZEN_GIT", git)
        git_environment = gate._sanitized_git_environment()
        initialized = subprocess.run(
            [git, "init", str(crlf_repository)],
            check=False,
            capture_output=True,
            env=git_environment,
        )
        assert initialized.returncode == 0
        probe = crlf_repository / "probe.txt"
        probe.write_bytes(b"registered\n")
        prefix = gate._git_command_prefix(crlf_repository)
        assert prefix == [
            git,
            "--no-replace-objects",
            "-c",
            f"safe.directory={crlf_repository}",
            "-c",
            "core.autocrlf=true",
            "-c",
            "core.attributesFile=NUL",
            "-c",
            "core.fsmonitor=false",
            "-c",
            "core.quotepath=false",
            "-c",
            "core.untrackedCache=false",
            "-c",
            "status.showUntrackedFiles=all",
            "-C",
            str(crlf_repository),
        ]
        for command in (
            [*prefix, "add", "probe.txt"],
            [
                *prefix,
                "-c",
                "user.name=Q1M Review",
                "-c",
                "user.email=q1m-review@example.invalid",
                "commit",
                "-m",
                "fixture",
            ],
            [*prefix, "config", "core.autocrlf", "false"],
        ):
            completed = subprocess.run(
                command,
                check=False,
                capture_output=True,
                env=git_environment,
            )
            assert completed.returncode == 0
        probe.unlink()
        checkout = subprocess.run(
            [*prefix, "checkout", "--", "probe.txt"],
            check=False,
            capture_output=True,
            env=git_environment,
        )
        assert checkout.returncode == 0
        assert probe.read_bytes() == b"registered\r\n"
        assert gate._git(
            crlf_repository,
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
        ) == ""
        clean_probe = subprocess.run(
            [*prefix, *contract["execution"]["clean_status_args"]],
            check=False,
            capture_output=True,
            env=git_environment,
        )
        assert clean_probe.returncode == 0
        clean_status = {
            "bytes": 0,
            "sha256": hashlib.sha256(b"").hexdigest(),
        }
        assert clean_probe.stdout == b""
        assert clean_status == contract["execution"]["clean_status_empty"]
        assert gate._functional_source_status(crlf_repository) == clean_status
        assert burnin.strict_clean_status_record(
            crlf_repository, contract=contract
        ) == clean_status
        manager = process_runner._manager_paths(contract)
        absent_request_id = "0" * 32
        assert not (manager["requests"] / f"{absent_request_id}.json").exists()
        lock_existed = manager["active_lock"].exists()
        manager_probe = subprocess.run(
            process_runner._manager_script_args(
                Path(guard["powershell"]["path"]),
                manager["acquire"],
                absent_request_id,
            ),
            capture_output=True,
            check=False,
            env=process_runner._manager_environment(contract),
        )
        manager_error = (manager_probe.stderr + manager_probe.stdout).decode(
            "utf-8", errors="replace"
        )
        assert manager_probe.returncode != 0
        assert "Unknown performance-test request" in manager_error
        assert "running scripts is disabled" not in manager_error
        assert manager["active_lock"].exists() is lock_existed
        runtime_contract = copy.deepcopy(contract)
        runtime_guard = runtime_contract["execution"]["environment_guard"]
        runtime_guard["python_cache_root"] = str(tmp_path / "python-cache")
        runtime_guard["numba_cache_root"] = str(tmp_path / "numba-cache")
        environment = process_runner._execution_environment(
            runtime_contract, process_prefix="common.quick.1"
        )
        for name in (
            "GIT_CONFIG_COUNT",
            "GIT_DIR",
            "GIT_WORK_TREE",
            "PYTEST_PLUGINS",
            "PYTHONINSPECT",
            "PYTHONWARNINGS",
            "ANYSOLVER_BURNIN_ACTIVE_TEST_LANE",
        ):
            assert name not in environment
        for name, value in guard["fixed"].items():
            assert environment[name] == value
        assert environment["GIT_ATTR_NOSYSTEM"] == "1"
        path_parts = environment["PATH"].split(os.pathsep)
        assert Path(path_parts[0]) == Path(guard["git"]["path"]).parent
        assert Path(path_parts[1]) == Path(guard["python"]["path"]).parent
        assert Path(environment["ANYSOLVER_FROZEN_GIT"]) == Path(guard["git"]["path"])
        assert environment["NUMBA_CACHE_DIR"].endswith("numba-cache\\quick")
        assert environment["PYTHONPYCACHEPREFIX"].endswith("python-cache\\quick")
        assert not Path(environment["PYTHONPYCACHEPREFIX"]).exists()

        hostile_python = tmp_path / "hostile-python"
        hostile_python.mkdir()
        startup_marker = tmp_path / "hostile-sitecustomize-executed.txt"
        (hostile_python / "sitecustomize.py").write_text(
            "from pathlib import Path\n"
            f"Path({str(startup_marker)!r}).write_text('executed', encoding='utf-8')\n",
            encoding="utf-8",
        )
        monkeypatch.setenv("PYTHONPATH", str(hostile_python))
        probe_contract = copy.deepcopy(contract)
        probe_guard = probe_contract["execution"]["environment_guard"]
        probe_guard["python_cache_root"] = str(tmp_path / "python-cache")
        probe_guard["numba_cache_root"] = str(tmp_path / "numba-cache")
        probe_environment = process_runner._execution_environment(
            probe_contract, process_prefix="common.package.1"
        )
        probe = subprocess.run(
            [str(Path(guard["python"]["path"])), "-c", "print('isolated child')"],
            capture_output=True,
            check=False,
            env=probe_environment,
            cwd=tmp_path,
        )
        assert probe.returncode == 0
        assert not startup_marker.exists()

        mutation = copy.deepcopy(runtime_contract)
        mutation["execution"]["environment_guard"]["python"]["sha256"] = "0" * 64
        with pytest.raises(process_runner.burnin.EvidenceError, match="python executable identity"):
            process_runner._execution_environment(
                mutation, process_prefix="common.quick.1"
            )

        cold = copy.deepcopy(mutation)
        cold["non_resource_commands"]["output_root"] = str(tmp_path / "cold-setup")
        monkeypatch.setattr(process_runner, "_bootstrap_authority", lambda: None)
        monkeypatch.setattr(process_runner.burnin, "load_contract", lambda: cold)
        monkeypatch.setattr(
            process_runner,
            "_verify_repositories",
            lambda _contract: (ROOT, {}, "a" * 40, "b" * 40),
        )
        monkeypatch.setattr(
            process_runner,
            "_verify_local_order",
            lambda _contract, _lane, _partition: "common.quick.1",
        )
        with pytest.raises(process_runner.burnin.EvidenceError, match="python executable identity"):
            process_runner.run_local(lane="quick", partition=None)
        assert not (tmp_path / "cold-setup" / "quick").exists()

        namespace_repo = tmp_path / "namespace-repo"
        namespace_repo.mkdir()
        git = str(Path(guard["git"]["path"]))
        git_environment = burnin.sanitized_execution_environment(contract)
        for command in (
            [git, "init", str(namespace_repo)],
            [
                git,
                "-C",
                str(namespace_repo),
                "-c",
                "user.name=Authority Test",
                "-c",
                "user.email=authority@example.invalid",
                "commit",
                "--allow-empty",
                "-m",
                "initial",
            ],
        ):
            subprocess.run(
                command,
                capture_output=True,
                check=True,
                env=git_environment,
            )
        info_exclude = namespace_repo / ".git" / "info" / "exclude"
        with info_exclude.open("a", encoding="utf-8", newline="") as stream:
            stream.write("ignored-empty/\n")
        ignored_empty = namespace_repo / "ignored-empty"
        ignored_empty.mkdir()
        ignored_probe = subprocess.run(
            [
                *gate._git_command_prefix(namespace_repo),
                *contract["execution"]["clean_status_args"],
            ],
            check=False,
            capture_output=True,
            env=git_environment,
        )
        assert ignored_probe.returncode == 0
        ignored_status = {
            "bytes": len(ignored_probe.stdout),
            "sha256": hashlib.sha256(ignored_probe.stdout).hexdigest(),
        }
        assert ignored_status["bytes"] > 0
        assert gate._functional_source_status(namespace_repo) == ignored_status
        diagnostic_contract = copy.deepcopy(contract)
        diagnostic_contract["execution"]["clean_status_empty"] = ignored_status
        assert burnin.strict_clean_status_record(
            namespace_repo, contract=diagnostic_contract
        ) == ignored_status
        with pytest.raises(burnin.EvidenceError, match="not completely clean"):
            burnin.assert_clean_execution_repository(namespace_repo, contract=contract)
        identity = {
            "commit": gate._git(namespace_repo, "rev-parse", "HEAD"),
            "tree": gate._git(namespace_repo, "rev-parse", "HEAD^{tree}"),
        }
        repository_record = {
            "candidate": identity,
            "siblings": {
                name: identity for name in contract["execution"]["clean_status_scope"][1:]
            },
        }
        repository_paths = {
            name: namespace_repo for name in contract["execution"]["clean_status_scope"]
        }
        with pytest.raises(gate.EvidenceError, match="not completely clean"):
            gate._validate_repository_identities(
                repository_record, repository_paths, contract
            )
        ignored_empty.rmdir()
        observed_repositories: list[Path] = []
        original_source_status = gate._functional_source_status

        def _record_source_status(repository: Path) -> dict[str, object]:
            observed_repositories.append(repository)
            return original_source_status(repository)

        monkeypatch.setattr(gate, "_functional_source_status", _record_source_status)
        gate._validate_repository_identities(
            repository_record, repository_paths, contract
        )
        assert observed_repositories == [namespace_repo] * len(
            contract["execution"]["clean_status_scope"]
        )
        with info_exclude.open("a", encoding="utf-8", newline="") as stream:
            stream.write("sitecustomize.py\n")
        (namespace_repo / "sitecustomize.py").write_text(
            "raise RuntimeError('must never execute')\n", encoding="utf-8"
        )
        with pytest.raises(burnin.EvidenceError, match="not completely clean"):
            burnin.assert_clean_execution_repository(namespace_repo, contract=contract)
        (namespace_repo / "sitecustomize.py").unlink()
        (namespace_repo / "fixture.json").write_text("{}\n", encoding="utf-8")
        with pytest.raises(burnin.EvidenceError, match="not completely clean"):
            burnin.assert_clean_execution_repository(namespace_repo, contract=contract)
        (namespace_repo / "fixture.json").unlink()
        with info_exclude.open("a", encoding="utf-8", newline="") as stream:
            stream.write("pytest.ini\n")
        (namespace_repo / "pytest.ini").write_text(
            "[pytest]\naddopts = --collect-only\n", encoding="utf-8"
        )
        with pytest.raises(burnin.EvidenceError, match="not completely clean"):
            burnin.assert_clean_execution_repository(namespace_repo, contract=contract)
    else:
        assert os.environ.get("GITHUB_ACTIONS") == "true"
        assert guard["removed_prefixes"] == [
            "GIT_CONFIG_",
            "NUMBA_",
            "PYTEST_",
            "PYTHON",
        ]

    isolated = copy.deepcopy(contract)
    isolated["non_resource_commands"]["output_root"] = str(tmp_path / "burnin")
    monkeypatch.setattr(process_runner.burnin, "load_contract", lambda: isolated)
    output = burnin.process_output_directory(isolated, "common.quick.1")
    process_runner._reserve_output(output)
    assert output.is_dir()
    with pytest.raises(process_runner.burnin.EvidenceError, match="one-shot"):
        process_runner._reserve_output(output)
    with pytest.raises(process_runner.burnin.EvidenceError, match="outside frozen authority"):
        process_runner._reserve_output(tmp_path / "wrong" / "quick")

    source = (REFERENCE / "e4_pl_s3_q4_process_runner.py").read_text(encoding="utf-8")
    for forbidden in ("--output-dir", "--manager", "--candidate", "--sibling"):
        assert forbidden not in source

    fake_root = tmp_path / "ignored" / "fake-root"
    copied_dir = fake_root / "docs" / "reference_cases"
    copied_dir.mkdir(parents=True)
    fake_gitdir = tmp_path / "ignored" / "fake-gitdir"
    fake_gitdir.mkdir()
    (fake_root / ".git").write_text(f"gitdir: {fake_gitdir}\n", encoding="utf-8")
    (fake_gitdir / "gitdir").write_text(str(fake_root / ".git") + "\n", encoding="utf-8")
    copied_runner = copied_dir / "e4_pl_s3_q4_process_runner.py"
    copied_runner.write_bytes((REFERENCE / copied_runner.name).read_bytes())
    marker = tmp_path / "hostile-import-executed.txt"
    (copied_dir / "e4_pl_s3_q4_burnin.py").write_text(
        "from pathlib import Path\n"
        f"Path({str(marker)!r}).write_text('executed', encoding='utf-8')\n",
        encoding="utf-8",
    )
    copied = subprocess.run(
        [sys.executable, "-I", str(copied_runner), "--help"],
        capture_output=True,
        check=False,
    )
    assert copied.returncode != 0
    assert not marker.exists()
    imported = subprocess.run(
        [
            sys.executable,
            "-I",
            "-c",
            (
                "import importlib.util;"
                f"p={str(copied_runner)!r};"
                "s=importlib.util.spec_from_file_location('ignored_runner',p);"
                "m=importlib.util.module_from_spec(s);"
                "s.loader.exec_module(m);"
                "m.main(['aggregate'])"
            ),
        ],
        capture_output=True,
        check=False,
    )
    assert imported.returncode != 0
    assert not marker.exists()

    benign = tmp_path / "validator.py"
    benign.write_bytes(b"VALUE = 'source'\n")
    malicious = tmp_path / "malicious_validator.py"
    pyc_marker = tmp_path / "unchecked-pyc-executed.txt"
    malicious.write_text(
        "from pathlib import Path\n"
        f"Path({str(pyc_marker)!r}).write_text('executed', encoding='utf-8')\n"
        "VALUE = 'bytecode'\n",
        encoding="utf-8",
    )
    cache_path = Path(importlib.util.cache_from_source(str(benign)))
    cache_path.parent.mkdir(parents=True)
    py_compile.compile(
        str(malicious),
        cfile=str(cache_path),
        dfile=str(benign),
        invalidation_mode=py_compile.PycInvalidationMode.UNCHECKED_HASH,
    )
    source_module = process_runner._load_source_module(
        benign,
        expected_bytes=len(benign.read_bytes()),
        expected_sha256=hashlib.sha256(benign.read_bytes()).hexdigest(),
    )
    assert source_module.VALUE == "source"
    assert not pyc_marker.exists()


def _valid_package_result(contract: dict[str, object]) -> dict[str, object]:
    distributions = contract["package"]["local_distributions"]
    process = {"bytes": 1, "returncode": 0, "sha256": "1" * 64}
    sources = {
        name: {
            "archive": {"bytes": 1, "sha256": "2" * 64},
            "archive_log": {"bytes": 0, "returncode": 0, "sha256": "3" * 64},
            "commit": "4" * 40,
            "content": {"files": 1, "sha256": "5" * 64},
            "tree": "6" * 40,
        }
        for name in distributions
    }
    wheels = {
        name: {
            "bytes": 1,
            "filename": f"{name.lower()}-0.0.0-py3-none-any.whl",
            "sha256": "7" * 64,
        }
        for name in distributions
    }
    return {
        "build_logs": {name: dict(process) for name in distributions},
        "install_log": dict(process),
        "schema": contract["package"]["package_result_schema"],
        "smoke": {
            **contract["package"]["smoke"],
            "origins": {
                package: f"{package}/__init__.py" for package in distributions.values()
            },
        },
        "smoke_log": {"bytes": 1, "sha256": "8" * 64},
        "sources": sources,
        "status": "PASS",
        "wheels": wheels,
    }


def test_package_artifacts_are_revalidated_before_approval_and_consumption(
    tmp_path: Path,
) -> None:
    contract = copy.deepcopy(_load_contract())
    root = tmp_path / "burnin"
    contract["non_resource_commands"]["output_root"] = str(root)
    package_directory = burnin.process_output_directory(contract, "common.package.1")
    package_directory.mkdir(parents=True)
    result_path = root / contract["package"]["result_filename"]
    wheel_path = root / contract["package"]["wheel_filename"]
    wheel_bytes = b"frozen wheel bytes"
    wheel_path.write_bytes(wheel_bytes)

    candidate = {"commit": "a" * 40, "tree": "b" * 40}
    package = _valid_package_result(contract)
    expected_sources = {
        "ANYsolver": candidate,
        **{
            name: authority
            for name, authority in contract["sibling_authority"].items()
            if name != "ANYfem"
        },
    }
    for name, authority in expected_sources.items():
        package["sources"][name]["commit"] = authority["commit"]
        package["sources"][name]["tree"] = authority["tree"]
    package["wheels"]["ANYsolver"] = {
        "bytes": len(wheel_bytes),
        "filename": wheel_path.name,
        "sha256": hashlib.sha256(wheel_bytes).hexdigest(),
    }
    raw = burnin.canonical_json_bytes(package)
    result_path.write_bytes(raw)
    (package_directory / "stdout.txt").write_bytes(raw)

    assert process_runner._validate_package_artifacts(
        contract,
        candidate_commit=candidate["commit"],
        candidate_tree=candidate["tree"],
    ) == package
    assert burnin.require_package_process_result_identity(contract=contract) == raw

    post_resource_substitution = copy.deepcopy(package)
    post_resource_substitution["smoke"]["q4_type"] = "SubstitutedShellElement"
    result_path.write_bytes(burnin.canonical_json_bytes(post_resource_substitution))
    with pytest.raises(burnin.EvidenceError, match="package-process stdout"):
        burnin.require_package_process_result_identity(contract=contract)
    result_path.write_bytes(raw)

    wheel_path.write_bytes(b"mutated wheel")
    with pytest.raises(burnin.EvidenceError, match="wheel identity"):
        process_runner._validate_package_artifacts(
            contract,
            candidate_commit=candidate["commit"],
            candidate_tree=candidate["tree"],
        )
    wheel_path.write_bytes(wheel_bytes)

    mutation = copy.deepcopy(package)
    mutation["sources"]["ANYmesh"]["commit"] = "c" * 40
    mutated_raw = burnin.canonical_json_bytes(mutation)
    result_path.write_bytes(mutated_raw)
    (package_directory / "stdout.txt").write_bytes(mutated_raw)
    with pytest.raises(burnin.EvidenceError, match="source authority"):
        process_runner._validate_package_artifacts(
            contract,
            candidate_commit=candidate["commit"],
            candidate_tree=candidate["tree"],
        )

    result_path.write_bytes(raw)
    (package_directory / "stdout.txt").write_bytes(b"mutated process stdout")
    with pytest.raises(burnin.EvidenceError, match="process stdout"):
        process_runner._validate_package_artifacts(
            contract,
            candidate_commit=candidate["commit"],
            candidate_tree=candidate["tree"],
        )
    (package_directory / "stdout.txt").write_bytes(raw)

    result_path.unlink()
    with pytest.raises(burnin.EvidenceError, match="regular non-reparse"):
        process_runner._validate_package_artifacts(
            contract,
            candidate_commit=candidate["commit"],
            candidate_tree=candidate["tree"],
        )


def test_package_result_and_final_adjudication_are_strict(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    contract = _load_contract()
    package = _valid_package_result(contract)
    assert burnin.validate_package_result(package, contract=contract) == package
    mutation = copy.deepcopy(package)
    mutation["smoke"]["q4_type"] = "ShellElement"
    with pytest.raises(burnin.EvidenceError, match="q4_type"):
        burnin.validate_package_result(mutation, contract=contract)

    result = _valid_result(contract)
    result_path = tmp_path / "result.json"
    status_path = tmp_path / "status.json"
    review_path = tmp_path / "review.json"
    result_path.write_bytes(burnin.canonical_json_bytes(result))
    result_sha = hashlib.sha256(result_path.read_bytes()).hexdigest()
    status = {
        "clean_cycles_recorded": 2,
        "gate_result_sha256": result_sha,
        "legacy_q4_removal_authorized": False,
        "qualified_s3_default_activation_authorized": False,
        "schema": contract["adjudication"]["status_schema"],
        "terminal": contract["adjudication"]["success_terminal"],
    }
    status_path.write_bytes(burnin.canonical_json_bytes(status))
    review = {
        "findings": [],
        "reviewed_inputs": {
            "contract_sha256": hashlib.sha256(CONTRACT_PATH.read_bytes()).hexdigest(),
            "gate_result_sha256": result_sha,
            "status_sha256": hashlib.sha256(status_path.read_bytes()).hexdigest(),
        },
        "reviewer_independence": contract["adjudication"]["review_independence"],
        "schema": contract["adjudication"]["review_schema"],
        "verdict": contract["adjudication"]["accepted_success_verdict"],
    }
    review_path.write_bytes(burnin.canonical_json_bytes(review))
    monkeypatch.setattr(burnin, "validate_external_bindings", lambda *args, **kwargs: None)
    assert burnin.validate_adjudication_files(
        result_path,
        status_path,
        review_path,
        contract=contract,
        repository_root=None,
    ) == (result, status, review)
    mutation = copy.deepcopy(review)
    mutation["findings"] = [{"priority": "P1"}]
    review_path.write_bytes(burnin.canonical_json_bytes(mutation))
    with pytest.raises(burnin.EvidenceError, match="no findings"):
        burnin.validate_adjudication_files(
            result_path,
            status_path,
            review_path,
            contract=contract,
            repository_root=None,
        )


def test_production_boundary_keeps_q4_and_s3_rollbacks_available() -> None:
    contract = _load_contract()
    assert contract["production_boundary"] == {
        "legacy_q4_available": True,
        "legacy_q4_removal_authorized": False,
        "q4_default": "QUALIFIED_E4_PL_Q4",
        "q4_formulation_mechanics_changed": False,
        "s3_default": "LEGACY_S3",
        "s3_qualified_aliases": ["e4-pl-s3", "qualified-s3"],
        "s3_qualified_opt_in": True,
    }
    assert contract["execution"]["resource_lanes_serial"] is True
    assert contract["execution"]["automatic_retry"] is False
    assert contract["adjudication"]["default_s3_activation_authorized"] is False
    assert contract["adjudication"]["result_success_terminal"].startswith(
        "PENDING_REVIEW_"
    )
    assert contract["adjudication"]["success_terminal"] == (
        "PROVISIONAL_GO_E4_PL_S3_COMPANION_OPT_IN_RELEASE"
    )
