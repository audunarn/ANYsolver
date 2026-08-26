"""Authority and strict-schema tests for the corrected S3/Q4 burn-in."""

from __future__ import annotations

import ast
import copy
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import py_compile
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "docs" / "reference_cases"
CONTRACT_PATH = REFERENCE / "e4_pl_s3_q4_burnin_contract.json"
VALIDATOR_PATH = REFERENCE / "e4_pl_s3_q4_burnin.py"
CONTRACT_SHA256 = "99b803ef367830103d548bb8ae8c316ae27e916be0e424a44a1a28058c475611"
RESOURCE_MANAGER = Path(r"C:\Github\.resource-manager")
FINAL_FREEZE = Path(r"C:\Github\ANYsolver\.perf2-worktrees\s3-e4-pl-final-freeze")
ANYFEM_FREEZE = Path(
    r"C:\Github\ANYsolver\.perf2-worktrees\anyfem-e4-pl-default-routing"
)

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
        "command_sha256": command_sha256,
        "elapsed_seconds": 1.25,
        "ended_at": f"2026-08-26T12:00:{started_second + 1:02d}+02:00",
        "execution_state": "EXECUTED",
        "exit_code": 0 if status == "PASS" else 1,
        "producer_sha256": burnin.load_contract()["runner_inputs"]["process_runner"][
            "sha256"
        ],
        "request_id": request_id,
        "resource_lock_released": True if request_id is not None else None,
        "result": {"bytes": 1, "sha256": "b" * 64},
        "started_at": f"2026-08-26T12:00:{started_second:02d}+02:00",
        "status": status,
        "stderr": {"bytes": 0, "sha256": "c" * 64},
        "stdout": {"bytes": 1, "sha256": "d" * 64},
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
        "ledger": {"bytes": 1, "sha256": "9" * 64},
    }


def test_contract_is_canonical_and_binds_all_local_inputs() -> None:
    contract = _load_contract()
    assert contract["authority_commit"] == {
        "exact_parent": "eb1f1af313d59ac81e80d8567741faa326615296",
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
    for group in ("historical_inputs", "runner_inputs"):
        for record in contract[group].values():
            path = ROOT / record["path"]
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
    for name in ("git", "powershell", "python"):
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
    introduction = _git(
        "log",
        "--format=%H",
        "--diff-filter=A",
        "--",
        "docs/reference_cases/e4_pl_s3_q4_burnin_contract.json",
    ).stdout.splitlines()
    assert len(introduction) == 1
    authority_commit = introduction[0]
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


def test_external_request_ids_commands_and_hashes_are_preregistered() -> None:
    contract = _load_contract()
    rows = [
        row
        for cycle in ("cycle_1", "cycle_2")
        for row in contract["resource_requests"][cycle]
    ]
    assert len({row["request_id"] for row in rows}) == 6
    assert [row["lane"] for row in rows[:3]] == ["functional", "anyfem", "performance"]
    assert [row["command_sha256"] for row in rows[:3]] == [
        row["command_sha256"] for row in rows[3:]
    ]
    requests_root = RESOURCE_MANAGER / "requests"
    if not requests_root.is_dir():
        assert os.environ.get("GITHUB_ACTIONS") == "true"
        return
    for row in rows:
        path = requests_root / f"{row['request_id']}.json"
        assert _file_record(path) == {
            "bytes": row["bytes"],
            "sha256": row["request_sha256"],
        }
        request = burnin.strict_json_load(path)
        assert request["request_id"] == row["request_id"]
        assert request["status"] == "PENDING"
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
    tools_available = all(Path(guard[name]["path"]).is_file() for name in ("git", "powershell", "python"))
    if tools_available:
        environment = process_runner._execution_environment(
            contract, process_prefix="common.quick.1"
        )
        for name in (
            "GIT_CONFIG_COUNT",
            "GIT_DIR",
            "GIT_WORK_TREE",
            "PYTEST_PLUGINS",
            "PYTHONINSPECT",
            "PYTHONWARNINGS",
        ):
            assert name not in environment
        for name, value in guard["fixed"].items():
            assert environment[name] == value
        path_parts = environment["PATH"].split(os.pathsep)
        assert Path(path_parts[0]) == Path(guard["python"]["path"]).parent
        assert Path(path_parts[1]) == Path(guard["git"]["path"]).parent
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

        mutation = copy.deepcopy(contract)
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
            stream.write("sitecustomize.py\n")
        (namespace_repo / "sitecustomize.py").write_text(
            "raise RuntimeError('must never execute')\n", encoding="utf-8"
        )
        with pytest.raises(burnin.EvidenceError, match="untracked/ignored"):
            burnin.assert_clean_execution_repository(namespace_repo, contract=contract)
        (namespace_repo / "sitecustomize.py").unlink()
        with info_exclude.open("a", encoding="utf-8", newline="") as stream:
            stream.write("pytest.ini\n")
        (namespace_repo / "pytest.ini").write_text(
            "[pytest]\naddopts = --collect-only\n", encoding="utf-8"
        )
        with pytest.raises(burnin.EvidenceError, match="untracked/ignored"):
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
    cache_path.parent.mkdir()
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
