from __future__ import annotations

import copy
import io
import importlib.util
from pathlib import Path
import subprocess
import sys
import tarfile
import threading
import time

import pytest


ROOT = Path(__file__).resolve().parents[1]
PROGRAM = (
    ROOT
    / "docs"
    / "reference_cases"
    / "e4_pl_s3_v2_stage4a_coordinator.py"
)


def _load():
    name = "_test_e4_pl_s3_v2_stage4a_coordinator"
    spec = importlib.util.spec_from_file_location(name, PROGRAM)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(name, None)
    return module


def _synthetic_predecessor_incident(module, tmp_path, monkeypatch):
    incident_root = (tmp_path / "cycle-1").resolve()
    incident_root.mkdir(parents=True)
    (incident_root / "candidate-source-tree").mkdir()
    resource_root = (tmp_path / "resource-manager").resolve()
    request_root = resource_root / "requests"
    request_root.mkdir(parents=True)
    repository = (tmp_path / "frozen-repository").resolve()
    repository.mkdir()
    request_id = "1" * 32
    candidate_commit, candidate_tree = "2" * 40, "3" * 40
    authorization_commit, authorization_tree = "4" * 40, "5" * 40
    authorization_parent = "6" * 40
    authorization_subject = "synthetic predecessor authorization"
    authorization_path = "docs/reference_cases/authorization.json"
    contract_path = "docs/reference_cases/contract.json"
    requested_at = "2026-08-31T09:06:41.6684913+02:00"
    task = "synthetic bounded Stage 4A"

    request = {
        "command": "",
        "estimate_minutes": 30,
        "repository": str(repository),
        "request_id": request_id,
        "requested_at": requested_at,
        "status": "PENDING",
        "task": task,
    }
    request["command"] = "x" * (1311 - len(module.canonical_bytes(request)))
    request_raw = module.canonical_bytes(request)
    assert len(request_raw) == 1311
    request_path = request_root / f"{request_id}.json"
    request_path.write_bytes(request_raw)

    approved_line = f"| t0 | {request_id} | APPROVED | synthetic |"
    started_line = f"| t1 | {request_id} | EXECUTION_STARTED | synthetic |"
    failed_line = f"| t2 | {request_id} | COMPLETED_FAIL | synthetic |"
    row_hashes = {
        status: module.sha256((line + "\n").encode())
        for status, line in (
            ("APPROVED", approved_line),
            ("EXECUTION_STARTED", started_line),
            ("COMPLETED_FAIL", failed_line),
        )
    }
    ledger_snapshot_raw = ("header\n" + approved_line + "\n").encode()
    live_ledger = resource_root / "ledger.md"
    live_ledger.write_text(
        "header\n" + "\n".join((approved_line, started_line, failed_line)) + "\n",
        encoding="utf-8",
    )

    archive_raw = b"synthetic exact archive"
    archive_name = "candidate-source.tar"
    archive_path = incident_root / archive_name
    archive_path.write_bytes(archive_raw)
    candidate_binding = {
        "artifact_path": str(archive_path),
        "artifact_sha256": module.sha256(archive_raw),
        "candidate_id": "CANDIDATE_E4_PL_S3_V2A_FLAT_LINEAR_V1",
        "commit": candidate_commit,
        "formulation_id": "E4_PL_QUALIFIED_S3_COMPANION_V2",
        "schema": "anysolver.e4-pl-s3-v2-flat-candidate-binding-v1",
        "selector": "e4-pl-s3-v2",
        "tree": candidate_tree,
    }
    phase_plan = {
        "advisory_review_triggers": {},
        "formal_thresholds": {},
        "manifest_sha256": "7" * 64,
        "phase": "4A",
        "prerequisites": [],
        "record_count": 81,
        "schema": "anysolver.e4-pl-s3-v2-flat-funnel-plan-v1",
        "scope": "full",
        "selector": "e4-pl-s3-v2",
        "shards": [
            {"assignment_id": assignment_id, "records": [{} for _ in range(27)]}
            for assignment_id in module.EXPECTED_SHARDS
        ],
    }
    phase_raw = module.canonical_bytes(phase_plan)
    wave_root = incident_root / "producer-wave"
    workers = []
    for assignment_id in module.EXPECTED_SHARDS:
        worker_root = wave_root / assignment_id
        workers.append(
            {
                "assignment_id": assignment_id,
                "plan_path": str(incident_root / "phase4a-plan.json"),
                "plan_sha256": module.sha256(phase_raw),
                "progress_path": str(worker_root / "progress.jsonl"),
                "scientific_path": str(worker_root / "scientific.json"),
                "stderr_path": str(worker_root / "stderr.log"),
                "stdout_path": str(worker_root / "stdout.log"),
            }
        )
    manifest = {
        "lane": "flat-proof",
        "output_root": str(wave_root),
        "schema": "anysolver.e4-pl-s3-v2-bounded-wave-manifest-v1",
        "wave_id": "S3_V2_FLAT_FUNNEL_4A_FULL",
        "workers": workers,
    }

    contract_sha = "8" * 64
    authorization = {
        "contract_path": contract_path,
        "contract_sha256": contract_sha,
        "execution_paths": {
            "aggregate_path": str(incident_root / "stage4a-aggregate.json"),
            "approval_snapshot_path": str(incident_root / "approval-snapshot.json"),
            "output_root": str(incident_root),
            "python_executable": sys.executable,
        },
        "formal_execution_authorized": True,
        "implementation_reviews": [],
        "ledger_approval": {},
        "resource_lock_required": True,
        "resource_request": {},
        "schema": module.AUTHORIZATION_SCHEMA,
        "user_approval": {
            "recorded": True,
            "source": f"synthetic approval for {request_id}",
        },
    }
    approval_snapshot = {
        "approved_row": {"line": approved_line, "sha256": row_hashes["APPROVED"]},
        "candidate": {"commit": candidate_commit, "tree": candidate_tree},
        "ledger": {},
        "request": {
            "byte_count": len(request_raw),
            "path": str(request_path),
            "request_id": request_id,
            "sha256": module.sha256(request_raw),
        },
        "schema": "anysolver.e4-pl-s3-v2-stage4a-approval-snapshot-v2",
    }
    transcript_raw = b"REGISTERED_COMMAND_EXIT=2\n"
    aggregate = {
        "advisory_review_required": False,
        "authorization_sha256": "0" * 64,
        "checker_replica_bindings": [],
        "classifying_record_count": 0,
        "contract_sha256": contract_sha,
        "formal_failures": ["FORMAL_PROCESS_FAILED"],
        "producer_wave_result_sha256": None,
        "production_restriction": module.PRODUCTION_RESTRICTION,
        "schema": module.AGGREGATE_SCHEMA,
        "sequence_results": [],
        "successor_expansion_authorized": False,
        "terminal": module.BLOCKED,
        "v1_diagnostic_record_count": 0,
    }
    coordinator_raw = (
        b'producer_result_path = (output_root / "producer-wave-result.json").resolve()'
    )
    bounded_raw = (
        b"result_path.relative_to(output_root)\n"
        b'raise BoundedProcessError("canonical wave result path escapes output_root")'
    )
    predecessor_contract = {
        "candidate": {"commit": candidate_commit, "tree": candidate_tree},
        "frozen_files": [
            {
                "git_blob_sha256": module.sha256(coordinator_raw),
                "path": "docs/reference_cases/e4_pl_s3_v2_stage4a_coordinator.py",
                "role": "coordinator",
            },
            {
                "git_blob_sha256": module.sha256(bounded_raw),
                "path": "docs/reference_cases/e4_pl_s3_v2_bounded_process.py",
                "role": "bounded",
            },
        ],
        "schema": "anysolver.e4-pl-s3-v2-stage4a-contract-v2",
    }
    contract_raw = module.canonical_bytes(predecessor_contract)
    contract_sha = module.sha256(contract_raw)
    authorization["contract_sha256"] = contract_sha
    aggregate["contract_sha256"] = contract_sha

    artifacts = {
        "candidate_archive": (archive_name, archive_raw),
        "candidate_binding": (
            "candidate-source-binding.json",
            module.canonical_bytes(candidate_binding),
        ),
        "ledger_snapshot": ("resource-ledger-pre-run.md", ledger_snapshot_raw),
        "manifest": ("producer-wave-manifest.json", module.canonical_bytes(manifest)),
        "phase_plan": ("phase4a-plan.json", phase_raw),
        "transcript": ("formal-transcript.txt", transcript_raw),
    }
    artifact_constants = {
        name: (filename, len(raw), module.sha256(raw))
        for name, (filename, raw) in artifacts.items()
    }
    approval_snapshot["ledger"] = {
        "byte_count": len(ledger_snapshot_raw),
        "path": str(live_ledger),
        "sha256": module.sha256(ledger_snapshot_raw),
        "snapshot_path": str(incident_root / "resource-ledger-pre-run.md"),
    }
    artifacts["approval_snapshot"] = (
        "approval-snapshot.json",
        module.canonical_bytes(approval_snapshot),
    )
    authorization["ledger_approval"] = {
        "approved_row_sha256": row_hashes["APPROVED"],
        "ledger_path": str(live_ledger),
        "snapshot_path": str(incident_root / "approval-snapshot.json"),
        "snapshot_sha256": module.sha256(artifacts["approval_snapshot"][1]),
    }
    authorization["resource_request"] = {
        "command_sha256": module.sha256(request["command"].encode()),
        "repository": str(repository),
        "request_id": request_id,
        "request_path": str(request_path),
        "request_sha256": module.sha256(request_raw),
        "task": task,
    }
    authorization_raw = module.canonical_bytes(authorization)
    aggregate["authorization_sha256"] = module.sha256(authorization_raw)
    artifacts["aggregate"] = (
        "stage4a-aggregate.json",
        module.canonical_bytes(aggregate),
    )
    artifact_constants = {
        name: (filename, len(raw), module.sha256(raw))
        for name, (filename, raw) in artifacts.items()
    }
    for filename, raw in artifacts.values():
        (incident_root / filename).write_bytes(raw)

    incident = {
        name: {
            "byte_count": count,
            "path": str(incident_root / filename),
            "sha256": digest,
        }
        for name, (filename, count, digest) in artifact_constants.items()
    }
    incident.update(
        {
            "authorization": {
                "byte_count": len(authorization_raw),
                "commit": authorization_commit,
                "parent": authorization_parent,
                "path": authorization_path,
                "sha256": module.sha256(authorization_raw),
                "subject": authorization_subject,
                "tree": authorization_tree,
            },
            "output_root": str(incident_root),
            "request": {
                "byte_count": len(request_raw),
                "path": str(request_path),
                "sha256": module.sha256(request_raw),
            },
            "root_cause": "PRODUCER_RESULT_PATH_OUTSIDE_REGISTERED_WAVE_ROOT",
            "scientific_execution": {
                "checker_processes_started": 0,
                "classifying_records": 0,
                "producer_processes_started": 0,
                "producer_result_present": False,
            },
            "terminal_ledger_rows": [
                {
                    "line": started_line,
                    "sha256": row_hashes["EXECUTION_STARTED"],
                    "status": "EXECUTION_STARTED",
                },
                {
                    "line": failed_line,
                    "sha256": row_hashes["COMPLETED_FAIL"],
                    "status": "COMPLETED_FAIL",
                },
            ],
        }
    )

    monkeypatch.setattr(module, "PREDECESSOR_INCIDENT_ROOT", incident_root)
    monkeypatch.setattr(module, "PREDECESSOR_REPOSITORY", str(repository))
    monkeypatch.setattr(module, "PREDECESSOR_REQUEST_ID", request_id)
    monkeypatch.setattr(module, "PREDECESSOR_REQUESTED_AT", requested_at)
    monkeypatch.setattr(module, "PREDECESSOR_TASK", task)
    monkeypatch.setattr(module, "PREDECESSOR_REQUEST_SHA256", module.sha256(request_raw))
    monkeypatch.setattr(
        module, "PREDECESSOR_COMMAND_SHA256", module.sha256(request["command"].encode())
    )
    monkeypatch.setattr(module, "PREDECESSOR_AUTHORIZATION_COMMIT", authorization_commit)
    monkeypatch.setattr(module, "PREDECESSOR_AUTHORIZATION_TREE", authorization_tree)
    monkeypatch.setattr(module, "PREDECESSOR_AUTHORIZATION_PARENT", authorization_parent)
    monkeypatch.setattr(module, "PREDECESSOR_AUTHORIZATION_SUBJECT", authorization_subject)
    monkeypatch.setattr(module, "PREDECESSOR_AUTHORIZATION_PATH", authorization_path)
    monkeypatch.setattr(module, "PREDECESSOR_AUTHORIZATION_SHA256", module.sha256(authorization_raw))
    monkeypatch.setattr(module, "PREDECESSOR_AUTHORIZATION_BYTE_COUNT", len(authorization_raw))
    monkeypatch.setattr(module, "PREDECESSOR_CONTRACT_PATH", contract_path)
    monkeypatch.setattr(module, "PREDECESSOR_CONTRACT_SHA256", contract_sha)
    monkeypatch.setattr(module, "PREDECESSOR_CONTRACT_BYTE_COUNT", len(contract_raw))
    monkeypatch.setattr(
        module,
        "PREDECESSOR_CONNECTIVITY_MANIFEST_SHA256",
        phase_plan["manifest_sha256"],
    )
    monkeypatch.setattr(module, "PREDECESSOR_CANDIDATE_COMMIT", candidate_commit)
    monkeypatch.setattr(module, "PREDECESSOR_CANDIDATE_TREE", candidate_tree)
    monkeypatch.setattr(module, "PREDECESSOR_COORDINATOR_SHA256", module.sha256(coordinator_raw))
    monkeypatch.setattr(module, "PREDECESSOR_BOUNDED_SHA256", module.sha256(bounded_raw))
    monkeypatch.setattr(module, "PREDECESSOR_LEDGER_ROW_SHA256", row_hashes)
    monkeypatch.setattr(module, "PREDECESSOR_ARTIFACTS", artifact_constants)
    monkeypatch.setattr(module, "RESOURCE_MANAGER_ROOT", resource_root)
    monkeypatch.setattr(module, "RESOURCE_LEDGER_PATH", live_ledger)
    monkeypatch.setattr(module, "_validate_git_object_authority", lambda: None)

    git_blobs = {
        f"{authorization_commit}:{authorization_path}": authorization_raw,
        f"{authorization_commit}:{contract_path}": contract_raw,
        f"{authorization_commit}:docs/reference_cases/e4_pl_s3_v2_stage4a_coordinator.py": coordinator_raw,
        f"{authorization_commit}:docs/reference_cases/e4_pl_s3_v2_bounded_process.py": bounded_raw,
    }

    def fake_git(*args, binary=False, **_kwargs):
        if args == ("rev-parse", authorization_commit):
            return authorization_commit
        if args == ("rev-parse", f"{authorization_commit}^{{tree}}"):
            return authorization_tree
        if args == ("show", "-s", "--format=%P", authorization_commit):
            return authorization_parent
        if args == ("show", "-s", "--format=%s", authorization_commit):
            return authorization_subject
        if args[0] == "show" and len(args) == 2 and args[1] in git_blobs:
            return git_blobs[args[1]] if binary else git_blobs[args[1]].decode()
        raise AssertionError(f"unexpected synthetic Git query: {args}")

    monkeypatch.setattr(module, "_git", fake_git)

    class SyntheticWorker:
        def __init__(self, assignment_id):
            self.assignment_id = assignment_id

    class SyntheticBounded:
        def validate_manifest(self, value):
            bounded_calls.append(copy.deepcopy(value))
            return (
                value["wave_id"],
                value["lane"],
                Path(value["output_root"]).resolve(),
                tuple(SyntheticWorker(item["assignment_id"]) for item in value["workers"]),
            )

    bounded_calls = []
    bounded = SyntheticBounded()
    real_load_module = module._load_module

    def fake_load_module(name, path):
        if path == module.BOUNDED_PATH:
            return bounded
        return real_load_module(name, path)

    monkeypatch.setattr(module, "_load_module", fake_load_module)

    def replace_artifact(name, value):
        raw = value if isinstance(value, bytes) else module.canonical_bytes(value)
        filename = artifacts[name][0]
        (incident_root / filename).write_bytes(raw)
        constants = dict(module.PREDECESSOR_ARTIFACTS)
        constants[name] = (filename, len(raw), module.sha256(raw))
        monkeypatch.setattr(module, "PREDECESSOR_ARTIFACTS", constants)
        incident[name] = {
            "byte_count": len(raw),
            "path": str(incident_root / filename),
            "sha256": module.sha256(raw),
        }

    def replace_request(value, *, rebind_command):
        value = copy.deepcopy(value)
        value["command"] = str(value["command"])
        raw = module.canonical_bytes(value)
        difference = 1311 - len(raw)
        assert difference >= 0
        value["command"] += "x" * difference
        raw = module.canonical_bytes(value)
        assert len(raw) == 1311
        request_path.write_bytes(raw)
        monkeypatch.setattr(module, "PREDECESSOR_REQUEST_SHA256", module.sha256(raw))
        if rebind_command:
            monkeypatch.setattr(
                module,
                "PREDECESSOR_COMMAND_SHA256",
                module.sha256(value["command"].encode()),
            )
        incident["request"] = {
            "byte_count": len(raw),
            "path": str(request_path),
            "sha256": module.sha256(raw),
        }

    return {
        "aggregate": aggregate,
        "approval_snapshot": approval_snapshot,
        "bounded_calls": bounded_calls,
        "candidate_binding": candidate_binding,
        "incident": incident,
        "live_ledger": live_ledger,
        "manifest": manifest,
        "phase_plan": phase_plan,
        "replace_artifact": replace_artifact,
        "replace_request": replace_request,
        "request": request,
        "request_path": request_path,
    }


def _synthetic_resource_deferred_incident(module, tmp_path, monkeypatch):
    incident_root = (tmp_path / "resource-deferred-cycle").resolve()
    candidate_tree_root = incident_root / "candidate-source-tree"
    candidate_directory = candidate_tree_root / "docs"
    candidate_directory.mkdir(parents=True)
    (candidate_directory / "one.txt").write_bytes(b"one\n")
    wave_root = incident_root / "producer-wave"
    wave_root.mkdir()

    resource_root = (tmp_path / "resource-manager").resolve()
    request_root = resource_root / "requests"
    attempt_root = resource_root / "attempts"
    request_root.mkdir(parents=True)
    attempt_root.mkdir()
    repository = (tmp_path / "frozen-repository").resolve()
    repository.mkdir()

    request_id = "a" * 32
    candidate_commit, candidate_tree = "b" * 40, "c" * 40
    contract_commit, contract_tree, contract_parent = "d" * 40, "e" * 40, "f" * 40
    authorization_commit = "1" * 40
    authorization_tree, authorization_parent = "2" * 40, "3" * 40
    contract_subject = "synthetic resource-deferred contract"
    authorization_subject = "synthetic resource-deferred authorization"
    requested_at = "2026-08-31T09:58:56.9567735+02:00"
    task = "synthetic bounded Stage 4A"
    connectivity_sha = "4" * 64
    coordinator_raw = b"synthetic corrected coordinator"
    bounded_raw = b"synthetic three-worker bounded runner"

    request = {
        "command": "registered resource command",
        "estimate_minutes": 30,
        "repository": str(repository),
        "request_id": request_id,
        "requested_at": requested_at,
        "status": "PENDING",
        "task": task,
    }
    request_raw = module.canonical_bytes(request)
    request_path = request_root / f"{request_id}.json"
    request_path.write_bytes(request_raw)

    approved_line = f"| t0 | {request_id} | APPROVED | synthetic |"
    started_line = f"| t1 | {request_id} | EXECUTION_STARTED | synthetic |"
    failed_line = f"| t2 | {request_id} | COMPLETED_FAIL | synthetic |"
    row_hashes = {
        status: module.sha256((line + "\n").encode())
        for status, line in (
            ("APPROVED", approved_line),
            ("EXECUTION_STARTED", started_line),
            ("COMPLETED_FAIL", failed_line),
        )
    }
    ledger_snapshot_raw = ("header\n" + approved_line + "\n").encode()
    live_ledger = resource_root / "ledger.md"
    live_ledger.write_text(
        "header\n" + "\n".join((approved_line, started_line, failed_line)) + "\n",
        encoding="utf-8",
    )

    archive_path = incident_root / "candidate-source.tar"
    candidate_payload = b"one\n"
    with tarfile.open(archive_path, "w") as bundle:
        directory = tarfile.TarInfo("docs/")
        directory.type = tarfile.DIRTYPE
        directory.mode = 0o755
        directory.mtime = 0
        bundle.addfile(directory)
        member = tarfile.TarInfo("docs/one.txt")
        member.mode = 0o644
        member.mtime = 0
        member.size = len(candidate_payload)
        bundle.addfile(member, io.BytesIO(candidate_payload))
    archive_raw = archive_path.read_bytes()
    candidate_binding = {
        "artifact_path": str(archive_path),
        "artifact_sha256": module.sha256(archive_raw),
        "candidate_id": "CANDIDATE_E4_PL_S3_V2A_FLAT_LINEAR_V1",
        "commit": candidate_commit,
        "formulation_id": "E4_PL_QUALIFIED_S3_COMPANION_V2",
        "schema": "anysolver.e4-pl-s3-v2-flat-candidate-binding-v1",
        "selector": "e4-pl-s3-v2",
        "tree": candidate_tree,
    }
    candidate_binding_raw = module.canonical_bytes(candidate_binding)

    plan = {
        "advisory_review_triggers": {},
        "formal_thresholds": {},
        "manifest_sha256": connectivity_sha,
        "phase": "4A",
        "prerequisites": [],
        "record_count": 81,
        "schema": "anysolver.e4-pl-s3-v2-flat-funnel-plan-v1",
        "scope": "full",
        "selector": "e4-pl-s3-v2",
        "shards": [
            {"assignment_id": assignment_id, "records": [{} for _ in range(27)]}
            for assignment_id in module.EXPECTED_SHARDS
        ],
    }
    plan_raw = module.canonical_bytes(plan)

    contract = {
        "candidate": {"commit": candidate_commit, "tree": candidate_tree},
        "execution": {
            "maximum_memory_gib_per_process_tree": 24,
            "maximum_workers": 3,
        },
        "frozen_files": [
            {
                "git_blob_sha256": module.sha256(bounded_raw),
                "path": "docs/reference_cases/e4_pl_s3_v2_bounded_process.py",
                "role": "bounded",
            },
            {
                "git_blob_sha256": module.sha256(coordinator_raw),
                "path": "docs/reference_cases/e4_pl_s3_v2_stage4a_coordinator.py",
                "role": "coordinator",
            },
        ],
        "schema": "anysolver.e4-pl-s3-v2-stage4a-contract-v3",
    }
    contract_raw = module.canonical_bytes(contract)
    contract_sha = module.sha256(contract_raw)

    attempt = {
        "contract_sha256": contract_sha,
        "request_id": request_id,
        "schema": "anysolver.resource-attempt-claim-v1",
    }
    attempt_raw = module.canonical_bytes(attempt)
    attempt_path = attempt_root / f"{request_id}.json"
    attempt_path.write_bytes(attempt_raw)

    approval_snapshot = {
        "approved_row": {"line": approved_line, "sha256": row_hashes["APPROVED"]},
        "candidate": {"commit": candidate_commit, "tree": candidate_tree},
        "ledger": {
            "byte_count": len(ledger_snapshot_raw),
            "path": str(live_ledger),
            "sha256": module.sha256(ledger_snapshot_raw),
            "snapshot_path": str(incident_root / "resource-ledger-pre-run.md"),
        },
        "request": {
            "byte_count": len(request_raw),
            "path": str(request_path),
            "request_id": request_id,
            "sha256": module.sha256(request_raw),
        },
        "schema": "anysolver.e4-pl-s3-v2-stage4a-approval-snapshot-v2",
    }
    approval_raw = module.canonical_bytes(approval_snapshot)
    authorization = {
        "contract_path": module.PREDECESSOR_CONTRACT_PATH,
        "contract_sha256": contract_sha,
        "execution_paths": {
            "aggregate_path": str(incident_root / "stage4a-aggregate.json"),
            "approval_snapshot_path": str(incident_root / "approval-snapshot.json"),
            "output_root": str(incident_root),
            "python_executable": sys.executable,
        },
        "formal_execution_authorized": True,
        "implementation_reviews": [
            {
                "path": "docs/reference_cases/e4_pl_s3_v2_stage4a_process_implementation_review.json",
                "role": "PROCESS_AND_AUTHORITY",
                "sha256": "7B7CF54AD998E31B11B2F4286C3BE638126817D28D7290F90B15BA1AAB0109E3",
                "verdict": "ACCEPT_STAGE4A_PROCESS_IMPLEMENTATION_NO_P0_P1",
            },
            {
                "path": "docs/reference_cases/e4_pl_s3_v2_stage4a_scientific_implementation_review.json",
                "role": "SCIENTIFIC_AND_MECHANICS",
                "sha256": "22EA28DAC7719F8748389204860AA4B90E936EE96AE564F414801D539D84A797",
                "verdict": "ACCEPT_STAGE4A_SCIENTIFIC_IMPLEMENTATION_NO_P0_P1",
            },
        ],
        "ledger_approval": {
            "approved_row_sha256": row_hashes["APPROVED"],
            "ledger_path": str(live_ledger),
            "snapshot_path": str(incident_root / "approval-snapshot.json"),
            "snapshot_sha256": module.sha256(approval_raw),
        },
        "resource_lock_required": True,
        "resource_request": {
            "command_sha256": module.sha256(request["command"].encode()),
            "repository": str(repository),
            "request_id": request_id,
            "request_path": str(request_path),
            "request_sha256": module.sha256(request_raw),
            "task": task,
        },
        "schema": module.AUTHORIZATION_SCHEMA,
        "user_approval": {
            "recorded": True,
            "source": f"synthetic approval for {request_id}",
        },
    }
    authorization_raw = module.canonical_bytes(authorization)

    workers = []
    for assignment_id in module.EXPECTED_SHARDS:
        assignment_root = wave_root / assignment_id
        workers.append(
            {
                "assignment_id": assignment_id,
                "input_hashes": [
                    {"path": str(module.AUTHORITY_PATH), "sha256": "5" * 64},
                    {
                        "path": str(
                            module.REFERENCE_CASES
                            / "e4_pl_s3_v2_stage4a_contract.json"
                        ),
                        "sha256": contract_sha,
                    },
                    {
                        "path": str(
                            module.REFERENCE_CASES
                            / "e4_pl_s3_v2_stage4a_execution_authorization.json"
                        ),
                        "sha256": module.sha256(authorization_raw),
                    },
                    {
                        "path": str(incident_root / "candidate-source-binding.json"),
                        "sha256": module.sha256(candidate_binding_raw),
                    },
                ],
                "plan_path": str(incident_root / "phase4a-plan.json"),
                "plan_sha256": module.sha256(plan_raw),
                "progress_path": str(assignment_root / "progress.jsonl"),
                "scientific_path": str(assignment_root / "scientific.json"),
                "stderr_path": str(assignment_root / "stderr.log"),
                "stdout_path": str(assignment_root / "stdout.log"),
            }
        )
    manifest = {
        "lane": "flat-proof",
        "output_root": str(wave_root),
        "schema": "anysolver.e4-pl-s3-v2-bounded-wave-manifest-v1",
        "wave_id": "S3_V2_FLAT_FUNNEL_4A_FULL",
        "workers": workers,
    }
    manifest_raw = module.canonical_bytes(manifest)
    producer_result = {
        "lane": "flat-proof",
        "manifest_sha256": module.sha256(manifest_raw),
        "schema": module.PRODUCER_RESULT_SCHEMA,
        "terminal": "RESOURCE_DEFERRED",
        "wave_id": "S3_V2_FLAT_FUNNEL_4A_FULL",
        "workers": [],
    }
    producer_raw = module.canonical_bytes(producer_result)
    producer_path = wave_root / "producer-wave-result.json"
    producer_path.write_bytes(producer_raw)
    aggregate = {
        "advisory_review_required": False,
        "authorization_sha256": module.sha256(authorization_raw),
        "checker_replica_bindings": [],
        "classifying_record_count": 0,
        "contract_sha256": contract_sha,
        "formal_failures": ["PRODUCER_WAVE_NOT_COMPLETED"],
        "producer_wave_result_sha256": module.sha256(producer_raw),
        "production_restriction": module.PRODUCTION_RESTRICTION,
        "schema": module.AGGREGATE_SCHEMA,
        "sequence_results": [],
        "successor_expansion_authorized": False,
        "terminal": module.BLOCKED,
        "v1_diagnostic_record_count": 0,
    }
    transcript_raw = b"REGISTERED_COMMAND_EXIT=2\n"
    artifacts = {
        "aggregate": ("stage4a-aggregate.json", module.canonical_bytes(aggregate)),
        "approval_snapshot": ("approval-snapshot.json", approval_raw),
        "candidate_archive": ("candidate-source.tar", archive_raw),
        "candidate_binding": (
            "candidate-source-binding.json",
            candidate_binding_raw,
        ),
        "ledger_snapshot": ("resource-ledger-pre-run.md", ledger_snapshot_raw),
        "manifest": ("producer-wave-manifest.json", manifest_raw),
        "phase_plan": ("phase4a-plan.json", plan_raw),
        "transcript": ("formal-transcript.txt", transcript_raw),
    }
    artifact_constants = {
        name: (filename, len(raw), module.sha256(raw))
        for name, (filename, raw) in artifacts.items()
    }
    for filename, raw in artifacts.values():
        (incident_root / filename).write_bytes(raw)

    incident = {
        name: {
            "byte_count": count,
            "path": str(incident_root / filename),
            "sha256": digest,
        }
        for name, (filename, count, digest) in artifact_constants.items()
    }
    incident.update(
        {
            "archive_ref": {
                "commit": authorization_commit,
                "ref": "refs/archive/synthetic-resource-deferred",
            },
            "attempt_claim": {
                "byte_count": len(attempt_raw),
                "path": str(attempt_path),
                "sha256": module.sha256(attempt_raw),
            },
            "authorization": {
                "byte_count": len(authorization_raw),
                "commit": authorization_commit,
                "parent": authorization_parent,
                "path": module.PREDECESSOR_AUTHORIZATION_PATH,
                "sha256": module.sha256(authorization_raw),
                "subject": authorization_subject,
                "tree": authorization_tree,
            },
            "candidate_tree": {
                "directory_count": 1,
                "file_count": 1,
                "path": str(candidate_tree_root),
            },
            "contract": {
                "byte_count": len(contract_raw),
                "commit": contract_commit,
                "parent": contract_parent,
                "path": module.PREDECESSOR_CONTRACT_PATH,
                "sha256": contract_sha,
                "subject": contract_subject,
                "tree": contract_tree,
            },
            "memory_admission": {
                "concurrent_workers_assumed": 3,
                "maximum_memory_gib_per_process_tree": 24,
                "observed_at_event_available_bytes": None,
                "observation_status": "NOT_RECORDED",
                "os_headroom_gib": 16,
                "registered_workers": 3,
                "required_bytes": 88 * (1 << 30),
            },
            "output_root": str(incident_root),
            "producer_result": {
                "byte_count": len(producer_raw),
                "path": str(producer_path),
                "sha256": module.sha256(producer_raw),
            },
            "request": {
                "byte_count": len(request_raw),
                "path": str(request_path),
                "sha256": module.sha256(request_raw),
            },
            "request_reuse_forbidden": True,
            "root_cause": "RESOURCE_ADMISSION_DEFERRED_BEFORE_WORKER_LAUNCH",
            "scientific_execution": {
                "checker_processes_started": 0,
                "classifying_records": 0,
                "producer_processes_started": 0,
                "producer_result_present": True,
            },
            "terminal_ledger_rows": [
                {
                    "line": started_line,
                    "sha256": row_hashes["EXECUTION_STARTED"],
                    "status": "EXECUTION_STARTED",
                },
                {
                    "line": failed_line,
                    "sha256": row_hashes["COMPLETED_FAIL"],
                    "status": "COMPLETED_FAIL",
                },
            ],
        }
    )

    patches = {
        "RESOURCE_DEFERRED_INCIDENT_ROOT": incident_root,
        "RESOURCE_DEFERRED_REPOSITORY": str(repository),
        "RESOURCE_DEFERRED_REQUEST_ID": request_id,
        "RESOURCE_DEFERRED_REQUESTED_AT": requested_at,
        "RESOURCE_DEFERRED_TASK": task,
        "RESOURCE_DEFERRED_REQUEST_BYTE_COUNT": len(request_raw),
        "RESOURCE_DEFERRED_REQUEST_SHA256": module.sha256(request_raw),
        "RESOURCE_DEFERRED_COMMAND_SHA256": module.sha256(request["command"].encode()),
        "RESOURCE_DEFERRED_ATTEMPT_BYTE_COUNT": len(attempt_raw),
        "RESOURCE_DEFERRED_ATTEMPT_SHA256": module.sha256(attempt_raw),
        "RESOURCE_DEFERRED_AUTHORIZATION_COMMIT": authorization_commit,
        "RESOURCE_DEFERRED_AUTHORIZATION_TREE": authorization_tree,
        "RESOURCE_DEFERRED_AUTHORIZATION_PARENT": authorization_parent,
        "RESOURCE_DEFERRED_AUTHORIZATION_SUBJECT": authorization_subject,
        "RESOURCE_DEFERRED_AUTHORIZATION_BYTE_COUNT": len(authorization_raw),
        "RESOURCE_DEFERRED_AUTHORIZATION_SHA256": module.sha256(authorization_raw),
        "RESOURCE_DEFERRED_CONTRACT_COMMIT": contract_commit,
        "RESOURCE_DEFERRED_CONTRACT_TREE": contract_tree,
        "RESOURCE_DEFERRED_CONTRACT_PARENT": contract_parent,
        "RESOURCE_DEFERRED_CONTRACT_SUBJECT": contract_subject,
        "RESOURCE_DEFERRED_CONTRACT_BYTE_COUNT": len(contract_raw),
        "RESOURCE_DEFERRED_CONTRACT_SHA256": contract_sha,
        "RESOURCE_DEFERRED_CANDIDATE_COMMIT": candidate_commit,
        "RESOURCE_DEFERRED_CANDIDATE_TREE": candidate_tree,
        "RESOURCE_DEFERRED_AUTHORITY_SHA256": "5" * 64,
        "RESOURCE_DEFERRED_COORDINATOR_SHA256": module.sha256(coordinator_raw),
        "RESOURCE_DEFERRED_BOUNDED_SHA256": module.sha256(bounded_raw),
        "RESOURCE_DEFERRED_CONNECTIVITY_MANIFEST_SHA256": connectivity_sha,
        "RESOURCE_DEFERRED_ARCHIVE_REF": "refs/archive/synthetic-resource-deferred",
        "RESOURCE_DEFERRED_ARCHIVE_COMMIT": authorization_commit,
        "RESOURCE_DEFERRED_CANDIDATE_FILE_COUNT": 1,
        "RESOURCE_DEFERRED_CANDIDATE_DIRECTORY_COUNT": 1,
        "RESOURCE_DEFERRED_OLD_ADMISSION_REQUIRED_BYTES": 88 * (1 << 30),
        "RESOURCE_DEFERRED_LEDGER_ROW_SHA256": row_hashes,
        "RESOURCE_DEFERRED_ARTIFACTS": artifact_constants,
        "RESOURCE_DEFERRED_PRODUCER_RESULT": (
            "producer-wave/producer-wave-result.json",
            len(producer_raw),
            module.sha256(producer_raw),
        ),
        "RESOURCE_MANAGER_ROOT": resource_root,
        "RESOURCE_LEDGER_PATH": live_ledger,
    }
    for name, made in patches.items():
        monkeypatch.setattr(module, name, made)
    monkeypatch.setattr(module, "_validate_git_object_authority", lambda: None)

    git_blobs = {
        f"{authorization_commit}:{module.PREDECESSOR_AUTHORIZATION_PATH}": authorization_raw,
        f"{authorization_commit}:{module.PREDECESSOR_CONTRACT_PATH}": contract_raw,
        f"{contract_commit}:{module.PREDECESSOR_CONTRACT_PATH}": contract_raw,
        f"{authorization_commit}:docs/reference_cases/e4_pl_s3_v2_stage4a_coordinator.py": coordinator_raw,
        f"{authorization_commit}:docs/reference_cases/e4_pl_s3_v2_bounded_process.py": bounded_raw,
    }
    identities = {
        authorization_commit: (
            authorization_tree,
            authorization_parent,
            authorization_subject,
        ),
        contract_commit: (contract_tree, contract_parent, contract_subject),
    }

    def fake_git(*args, binary=False, **_kwargs):
        if args == ("rev-parse", "refs/archive/synthetic-resource-deferred"):
            return authorization_commit
        for commit, (tree, parent, subject) in identities.items():
            if args == ("rev-parse", commit):
                return commit
            if args == ("rev-parse", f"{commit}^{{tree}}"):
                return tree
            if args == ("show", "-s", "--format=%P", commit):
                return parent
            if args == ("show", "-s", "--format=%s", commit):
                return subject
        if args[0] == "show" and len(args) == 2 and args[1] in git_blobs:
            return git_blobs[args[1]] if binary else git_blobs[args[1]].decode()
        raise AssertionError(f"unexpected synthetic Git query: {args}")

    monkeypatch.setattr(module, "_git", fake_git)

    class SyntheticWorker:
        def __init__(self, assignment_id):
            self.assignment_id = assignment_id

    class SyntheticBounded:
        def validate_manifest(self, value):
            return (
                value["wave_id"],
                value["lane"],
                Path(value["output_root"]).resolve(),
                tuple(SyntheticWorker(item["assignment_id"]) for item in value["workers"]),
            )

    bounded = SyntheticBounded()
    real_load_module = module._load_module

    def fake_load_module(name, path):
        if path == module.BOUNDED_PATH:
            return bounded
        return real_load_module(name, path)

    monkeypatch.setattr(module, "_load_module", fake_load_module)

    def replace_artifact(name, value):
        raw = value if isinstance(value, bytes) else module.canonical_bytes(value)
        filename = artifacts[name][0]
        (incident_root / filename).write_bytes(raw)
        constants = dict(module.RESOURCE_DEFERRED_ARTIFACTS)
        constants[name] = (filename, len(raw), module.sha256(raw))
        monkeypatch.setattr(module, "RESOURCE_DEFERRED_ARTIFACTS", constants)
        incident[name] = {
            "byte_count": len(raw),
            "path": str(incident_root / filename),
            "sha256": module.sha256(raw),
        }

    def replace_producer(value):
        raw = module.canonical_bytes(value)
        producer_path.write_bytes(raw)
        monkeypatch.setattr(
            module,
            "RESOURCE_DEFERRED_PRODUCER_RESULT",
            ("producer-wave/producer-wave-result.json", len(raw), module.sha256(raw)),
        )
        incident["producer_result"] = {
            "byte_count": len(raw),
            "path": str(producer_path),
            "sha256": module.sha256(raw),
        }

    return {
        "aggregate": aggregate,
        "candidate_tree_root": candidate_tree_root,
        "incident": incident,
        "live_ledger": live_ledger,
        "producer_result": producer_result,
        "replace_artifact": replace_artifact,
        "replace_producer": replace_producer,
    }


def _sequence(mask: str, fraction: int, *, advisory: bool = False, failure: str | None = None):
    failures = [] if failure is None else [failure]
    return {
        "advisory_triggered": advisory,
        "all_q4_response_slope": 2.1,
        "energy_norm_slope": 1.2,
        "energy_norm_slope_lower_95_percent": 1.0,
        "energy_norm_values": [0.4, 0.2, 0.1],
        "failed_subgates": failures,
        "finest_error_ratio_to_all_q4": 1.1,
        "fraction_percent": fraction,
        "mask": mask,
        "record_ids": [
            f"{mask}-{fraction}-N20",
            f"{mask}-{fraction}-N40",
            f"{mask}-{fraction}-N80",
        ],
        "response_error_slope": 2.0,
        "response_errors": [0.04, 0.01, 0.0025],
        "slope_deficit_from_all_q4": 0.1,
        "successive_refinement_passed": failure != "SUCCESSIVE_RESPONSE_ERROR",
    }


def _checker_value(
    module,
    assignment_id: str,
    *,
    advisory: bool = False,
    no_go: bool = False,
):
    diagonal = module.EXPECTED_SHARDS[assignment_id]
    sequences = [
        _sequence(
            mask,
            fraction,
            advisory=advisory and mask == "dispersed" and fraction == 1,
            failure=(
                "RESPONSE_SLOPE"
                if no_go and mask == "dispersed" and fraction == 1
                else None
            ),
        )
        for mask in module.MASK_ORDER
        for fraction in module.FRACTION_ORDER
    ]
    failures = ["dispersed:1:RESPONSE_SLOPE"] if no_go else []
    return {
        "advisory_review_required": bool(advisory and not no_go),
        "assignment_id": assignment_id,
        "assignment_sha256": "A" * 64,
        "classifying_record_count": 27,
        "diagonal": diagonal,
        "formal_failures": failures,
        "plan_sha256": "B" * 64,
        "production_restriction": module.PRODUCTION_RESTRICTION,
        "proof_sha256": module.sha256(b""),
        "schema": module.CHECKER_RESULT_SCHEMA,
        "sequence_results": sequences,
        "successor_expansion_authorized": bool(not advisory and not no_go),
        "terminal": module.NO_GO if no_go else module.PASS,
        "v1_diagnostic_record_count": 24,
    }


def _replica(
    module,
    tmp_path: Path,
    replica_index: int,
    values: dict[str, dict],
):
    made = []
    for assignment_id in module.EXPECTED_SHARDS:
        value = values[assignment_id]
        raw = module.canonical_bytes(value)
        output = (tmp_path / f"replica-{replica_index}" / f"{assignment_id}.json").resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(raw)
        proof = (tmp_path / "proofs" / f"{assignment_id}.json").resolve()
        proof.parent.mkdir(parents=True, exist_ok=True)
        if not proof.exists():
            proof.write_bytes(b"")
        made.append(
            {
                "assignment_id": assignment_id,
                "cpu_100ns": 10,
                "output_path": str(output),
                "output_sha256": module.sha256(raw),
                "peak_tree_memory_bytes": 1024,
                "proof_path": str(proof),
                "proof_sha256": module.sha256(proof.read_bytes()),
                "stderr_sha256": module.sha256(b""),
                "stdout_sha256": module.sha256(b""),
                "termination_proven": True,
                "value": value,
            }
        )
    return made


def _values(module, **overrides):
    made = {
        assignment_id: _checker_value(module, assignment_id)
        for assignment_id in module.EXPECTED_SHARDS
    }
    for assignment_id, options in overrides.items():
        made[assignment_id] = _checker_value(module, assignment_id, **options)
    return made


def _aggregate(module, tmp_path: Path, first_values, second_values=None):
    if second_values is None:
        second_values = copy.deepcopy(first_values)
    replicas = [
        _replica(module, tmp_path, 1, first_values),
        _replica(module, tmp_path, 2, second_values),
    ]
    producer_proofs = {
        assignment_id: {
            "assignment_sha256": "A" * 64,
            "plan_sha256": "B" * 64,
            "proof_path": str((tmp_path / "proofs" / f"{assignment_id}.json").resolve()),
            "proof_sha256": module.sha256(b""),
        }
        for assignment_id in module.EXPECTED_SHARDS
    }
    return module.aggregate_checker_results(
        replicas,
        producer_proofs=producer_proofs,
        producer_result_sha256="D" * 64,
        contract_sha256="E" * 64,
        authorization_sha256="F" * 64,
    )


def test_strict_json_rejects_duplicate_keys_and_nonfinite_constants():
    module = _load()
    with pytest.raises(module.CoordinatorError, match="duplicate JSON key"):
        module.strict_json_bytes(b'{"a":1,"a":2}', "duplicate")
    with pytest.raises(module.CoordinatorError, match="non-finite JSON constant"):
        module.strict_json_bytes(b'{"a":NaN}', "nonfinite")
    with pytest.raises(module.CoordinatorError, match="non-finite number"):
        module.canonical_bytes({"a": float("inf")})


def test_external_incident_binding_is_exact_and_supports_utf8_bom(tmp_path):
    module = _load()
    path = (tmp_path / "request.json").resolve()
    raw = b'\xef\xbb\xbf{"request_id":"' + b"1" * 32 + b'"}\r\n'
    path.write_bytes(raw)
    binding = {
        "byte_count": len(raw),
        "path": str(path),
        "sha256": module.sha256(raw),
    }
    assert module._validate_external_file_binding(binding, "incident") == (path, raw)
    value, observed = module._strict_external_json(path, "incident request")
    assert value == {"request_id": "1" * 32}
    assert observed == raw

    for field, replacement in (
        ("byte_count", len(raw) + 1),
        ("sha256", "0" * 64),
    ):
        changed = dict(binding)
        changed[field] = replacement
        with pytest.raises(module.CoordinatorError, match="identity differs"):
            module._validate_external_file_binding(changed, "incident")


@pytest.mark.parametrize("alias", [True, float(1)])
def test_external_incident_binding_rejects_boolean_and_float_byte_counts(
    tmp_path, alias
):
    module = _load()
    path = (tmp_path / "one-byte.bin").resolve()
    path.write_bytes(b"x")
    binding = {
        "byte_count": alias,
        "path": str(path),
        "sha256": module.sha256(b"x"),
    }
    with pytest.raises(module.CoordinatorError, match="nonnegative integer"):
        module._validate_external_file_binding(binding, "incident")


@pytest.mark.parametrize("digest", [None, 7, "a" * 64, "G" * 64, "A" * 63])
def test_external_incident_binding_rejects_noncanonical_digest(tmp_path, digest):
    module = _load()
    path = (tmp_path / "artifact.bin").resolve()
    path.write_bytes(b"exact")
    binding = {"byte_count": 5, "path": str(path), "sha256": digest}
    with pytest.raises(module.CoordinatorError, match="SHA-256"):
        module._validate_external_file_binding(binding, "incident")


def test_external_incident_binding_rejects_raw_reparse_alias_before_resolve(
    tmp_path, monkeypatch
):
    module = _load()
    target = (tmp_path / "target.bin").resolve()
    target.write_bytes(b"exact")

    class SyntheticRawReparsePath:
        def is_absolute(self):
            return True

        def lstat(self):
            class SyntheticStat:
                st_mode = target.stat().st_mode
                st_file_attributes = 0x400

            return SyntheticStat()

        def is_symlink(self):
            return False

        def resolve(self):
            return target

    monkeypatch.setattr(module, "Path", lambda _value: SyntheticRawReparsePath())
    binding = {
        "byte_count": 5,
        "path": str(tmp_path / "synthetic-reparse.bin"),
        "sha256": module.sha256(b"exact"),
    }
    with pytest.raises(module.CoordinatorError, match="reparse|identity"):
        module._validate_external_file_binding(binding, "incident")


def test_predecessor_incident_validates_complete_synthetic_graph(tmp_path, monkeypatch):
    module = _load()
    fixture = _synthetic_predecessor_incident(module, tmp_path, monkeypatch)
    monkeypatch.setattr(module, "ROOT", tmp_path / "unrelated-live-root")
    module._validate_predecessor_process_incident(fixture["incident"])
    assert fixture["bounded_calls"] == [fixture["manifest"]]


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("checker_processes_started", False),
        ("classifying_records", 0.0),
        ("producer_processes_started", False),
        ("producer_result_present", 0),
    ],
)
def test_predecessor_incident_rejects_scientific_type_aliases(
    tmp_path, monkeypatch, field, replacement
):
    module = _load()
    fixture = _synthetic_predecessor_incident(module, tmp_path, monkeypatch)
    fixture["incident"]["scientific_execution"][field] = replacement
    with pytest.raises(module.CoordinatorError, match="scientific|nonnegative integer"):
        module._validate_predecessor_process_incident(fixture["incident"])


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("authorization_sha256", "9" * 64),
        ("producer_wave_result_sha256", "9" * 64),
        ("advisory_review_required", 0),
        ("classifying_record_count", False),
        ("v1_diagnostic_record_count", 0.0),
    ],
)
def test_predecessor_incident_rejects_rebound_aggregate_disposition_mutations(
    tmp_path, monkeypatch, field, replacement
):
    module = _load()
    fixture = _synthetic_predecessor_incident(module, tmp_path, monkeypatch)
    changed = copy.deepcopy(fixture["aggregate"])
    changed[field] = replacement
    fixture["replace_artifact"]("aggregate", changed)
    with pytest.raises(module.CoordinatorError, match="aggregate"):
        module._validate_predecessor_process_incident(fixture["incident"])


def test_predecessor_incident_rejects_extra_aggregate_key(tmp_path, monkeypatch):
    module = _load()
    fixture = _synthetic_predecessor_incident(module, tmp_path, monkeypatch)
    changed = copy.deepcopy(fixture["aggregate"])
    changed["unexpected"] = False
    fixture["replace_artifact"]("aggregate", changed)
    with pytest.raises(module.CoordinatorError, match="keys differ"):
        module._validate_predecessor_process_incident(fixture["incident"])


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda request: request.__setitem__("estimate_minutes", False), "nonnegative integer"),
        (lambda request: request.__setitem__("estimate_minutes", 30.0), "nonnegative integer"),
        (lambda request: request.__setitem__("command", "tampered"), "request identity"),
        (lambda request: request.__setitem__("unexpected", True), "keys differ"),
    ],
)
def test_predecessor_incident_rejects_rebound_request_mutations(
    tmp_path, monkeypatch, mutation, message
):
    module = _load()
    fixture = _synthetic_predecessor_incident(module, tmp_path, monkeypatch)
    changed = copy.deepcopy(fixture["request"])
    changed["command"] = "registered"
    mutation(changed)
    fixture["replace_request"](
        changed,
        rebind_command=changed.get("command") != "tampered",
    )
    with pytest.raises(module.CoordinatorError, match=message):
        module._validate_predecessor_process_incident(fixture["incident"])


def test_predecessor_incident_rejects_arbitrary_authorization_commit(
    tmp_path, monkeypatch
):
    module = _load()
    fixture = _synthetic_predecessor_incident(module, tmp_path, monkeypatch)
    fixture["incident"]["authorization"]["commit"] = "f" * 40
    with pytest.raises(module.CoordinatorError, match="authorization binding"):
        module._validate_predecessor_process_incident(fixture["incident"])


@pytest.mark.parametrize("artifact", ["approval_snapshot", "candidate_binding"])
def test_predecessor_incident_rejects_rebound_cross_join_mutations(
    tmp_path, monkeypatch, artifact
):
    module = _load()
    fixture = _synthetic_predecessor_incident(module, tmp_path, monkeypatch)
    changed = copy.deepcopy(fixture[artifact])
    if artifact == "approval_snapshot":
        changed["candidate"]["commit"] = "f" * 40
    else:
        changed["artifact_sha256"] = "f" * 64
    fixture["replace_artifact"](artifact, changed)
    with pytest.raises(module.CoordinatorError, match="approval snapshot|archive join"):
        module._validate_predecessor_process_incident(fixture["incident"])


def test_predecessor_incident_rejects_rebound_phase_plan_manifest_hash(
    tmp_path, monkeypatch
):
    module = _load()
    fixture = _synthetic_predecessor_incident(module, tmp_path, monkeypatch)
    changed = copy.deepcopy(fixture["phase_plan"])
    changed["manifest_sha256"] = "f" * 64
    fixture["replace_artifact"]("phase_plan", changed)
    changed_manifest = copy.deepcopy(fixture["manifest"])
    for worker in changed_manifest["workers"]:
        worker["plan_sha256"] = fixture["incident"]["phase_plan"]["sha256"]
    fixture["replace_artifact"]("manifest", changed_manifest)
    with pytest.raises(module.CoordinatorError, match="phase-plan|manifest"):
        module._validate_predecessor_process_incident(fixture["incident"])


def test_predecessor_incident_rejects_manifest_coverage_and_ledger_reordering(
    tmp_path, monkeypatch
):
    module = _load()
    fixture = _synthetic_predecessor_incident(module, tmp_path, monkeypatch)
    changed = copy.deepcopy(fixture["manifest"])
    changed["workers"].pop()
    fixture["replace_artifact"]("manifest", changed)
    with pytest.raises(module.CoordinatorError, match="manifest"):
        module._validate_predecessor_process_incident(fixture["incident"])

    fixture = _synthetic_predecessor_incident(module, tmp_path / "other", monkeypatch)
    rows = fixture["live_ledger"].read_text(encoding="utf-8").splitlines()
    fixture["live_ledger"].write_text(
        "\n".join([rows[0], rows[1], rows[3], rows[2]]) + "\n", encoding="utf-8"
    )
    with pytest.raises(module.CoordinatorError, match="ledger history"):
        module._validate_predecessor_process_incident(fixture["incident"])


def test_resource_deferred_incident_validates_complete_synthetic_graph(
    tmp_path, monkeypatch
):
    module = _load()
    fixture = _synthetic_resource_deferred_incident(module, tmp_path, monkeypatch)
    module._validate_predecessor_resource_deferred_incident(fixture["incident"])


@pytest.mark.parametrize(
    ("path", "replacement", "message"),
    [
        (("memory_admission", "observed_at_event_available_bytes"), 1, "memory admission"),
        (("memory_admission", "required_bytes"), False, "nonnegative integer"),
        (("scientific_execution", "producer_processes_started"), True, "nonnegative integer"),
        (("scientific_execution", "classifying_records"), 0.0, "nonnegative integer"),
        (("scientific_execution", "producer_result_present"), False, "scientific"),
        (("request_reuse_forbidden",), False, "identity"),
    ],
)
def test_resource_deferred_incident_rejects_disposition_mutations(
    tmp_path, monkeypatch, path, replacement, message
):
    module = _load()
    fixture = _synthetic_resource_deferred_incident(module, tmp_path, monkeypatch)
    target = fixture["incident"]
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = replacement
    with pytest.raises(module.CoordinatorError, match=message):
        module._validate_predecessor_resource_deferred_incident(fixture["incident"])


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("terminal", "COMPLETED"),
        ("workers", [{"status": "COMPLETED"}]),
        ("manifest_sha256", "F" * 64),
    ],
)
def test_resource_deferred_incident_rejects_rebound_producer_result(
    tmp_path, monkeypatch, field, replacement
):
    module = _load()
    fixture = _synthetic_resource_deferred_incident(module, tmp_path, monkeypatch)
    changed = copy.deepcopy(fixture["producer_result"])
    changed[field] = replacement
    fixture["replace_producer"](changed)
    with pytest.raises(module.CoordinatorError, match="producer result"):
        module._validate_predecessor_resource_deferred_incident(fixture["incident"])


def test_resource_deferred_incident_rejects_aggregate_result_cross_join(
    tmp_path, monkeypatch
):
    module = _load()
    fixture = _synthetic_resource_deferred_incident(module, tmp_path, monkeypatch)
    changed = copy.deepcopy(fixture["aggregate"])
    changed["producer_wave_result_sha256"] = "F" * 64
    fixture["replace_artifact"]("aggregate", changed)
    with pytest.raises(module.CoordinatorError, match="aggregate"):
        module._validate_predecessor_resource_deferred_incident(fixture["incident"])


def test_resource_deferred_incident_rejects_tree_and_root_extent_mutations(
    tmp_path, monkeypatch
):
    module = _load()
    fixture = _synthetic_resource_deferred_incident(module, tmp_path, monkeypatch)
    (fixture["candidate_tree_root"] / "unexpected.txt").write_text(
        "unexpected\n", encoding="utf-8"
    )
    with pytest.raises(module.CoordinatorError, match="candidate-tree extent"):
        module._validate_predecessor_resource_deferred_incident(fixture["incident"])

    fixture = _synthetic_resource_deferred_incident(
        module, tmp_path / "other", monkeypatch
    )
    (module.RESOURCE_DEFERRED_INCIDENT_ROOT / "unregistered.bin").write_bytes(b"x")
    with pytest.raises(module.CoordinatorError, match="artifact extent"):
        module._validate_predecessor_resource_deferred_incident(fixture["incident"])


def test_resource_deferred_incident_rejects_same_count_candidate_tree_rename(
    tmp_path, monkeypatch
):
    module = _load()
    fixture = _synthetic_resource_deferred_incident(module, tmp_path, monkeypatch)
    candidate_directory = fixture["candidate_tree_root"] / "docs"
    (candidate_directory / "one.txt").rename(candidate_directory / "renamed.txt")
    with pytest.raises(module.CoordinatorError, match="extent differs from archive"):
        module._validate_predecessor_resource_deferred_incident(fixture["incident"])


def test_resource_deferred_incident_rejects_same_count_candidate_tree_content_mutation(
    tmp_path, monkeypatch
):
    module = _load()
    fixture = _synthetic_resource_deferred_incident(module, tmp_path, monkeypatch)
    (fixture["candidate_tree_root"] / "docs" / "one.txt").write_bytes(b"two\n")
    with pytest.raises(module.CoordinatorError, match="content differs from archive"):
        module._validate_predecessor_resource_deferred_incident(fixture["incident"])


def test_resource_deferred_incident_rejects_archive_ref_and_ledger_mutations(
    tmp_path, monkeypatch
):
    module = _load()
    fixture = _synthetic_resource_deferred_incident(module, tmp_path, monkeypatch)
    fixture["incident"]["archive_ref"]["commit"] = "0" * 40
    with pytest.raises(module.CoordinatorError, match="archive ref"):
        module._validate_predecessor_resource_deferred_incident(fixture["incident"])

    fixture = _synthetic_resource_deferred_incident(
        module, tmp_path / "other", monkeypatch
    )
    rows = fixture["live_ledger"].read_text(encoding="utf-8").splitlines()
    fixture["live_ledger"].write_text(
        "\n".join([rows[0], rows[1], rows[3], rows[2]]) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(module.CoordinatorError, match="ledger history"):
        module._validate_predecessor_resource_deferred_incident(fixture["incident"])


def test_stage4a_contract_v4_requires_both_predecessor_incidents():
    module = _load()
    assert module.CONTRACT_KEYS == {
        "adjudication",
        "authority",
        "candidate",
        "coverage",
        "dependencies",
        "execution",
        "frozen_files",
        "git_authority",
        "predecessor_process_incident",
        "predecessor_resource_deferred_incident",
        "production_boundary",
        "protocol",
        "schema",
        "stage",
    }


def test_aggregate_pass_has_exact_coverage_and_registered_order(tmp_path):
    module = _load()
    aggregate = _aggregate(module, tmp_path, _values(module))
    assert aggregate["terminal"] == module.PASS
    assert aggregate["successor_expansion_authorized"] is True
    assert aggregate["advisory_review_required"] is False
    assert aggregate["classifying_record_count"] == 81
    assert aggregate["v1_diagnostic_record_count"] == 72
    assert len(aggregate["sequence_results"]) == 24
    assert len(aggregate["checker_replica_bindings"]) == 3
    assert all(
        len(binding["checker_output_sha256"]) == 2
        for binding in aggregate["checker_replica_bindings"]
    )
    assert [
        (item["diagonal"], item["mask"], item["fraction_percent"])
        for item in aggregate["sequence_results"]
    ] == [
        (diagonal, mask, fraction)
        for diagonal in module.DIAGONAL_ORDER
        for mask in module.MASK_ORDER
        for fraction in module.FRACTION_ORDER
    ]


def test_aggregate_advisory_pass_requires_review_and_blocks_expansion(tmp_path):
    module = _load()
    assignment_id = "S3_V2_FLAT_4A_SLASH"
    aggregate = _aggregate(
        module,
        tmp_path,
        _values(module, **{assignment_id: {"advisory": True}}),
    )
    assert aggregate["terminal"] == module.PASS
    assert aggregate["advisory_review_required"] is True
    assert aggregate["successor_expansion_authorized"] is False
    assert aggregate["formal_failures"] == []


def test_aggregate_no_go_has_precedence_and_scopes_failure_to_diagonal(tmp_path):
    module = _load()
    assignment_id = "S3_V2_FLAT_4A_BACKSLASH"
    aggregate = _aggregate(
        module,
        tmp_path,
        _values(module, **{assignment_id: {"no_go": True}}),
    )
    assert aggregate["terminal"] == module.NO_GO
    assert aggregate["successor_expansion_authorized"] is False
    assert aggregate["advisory_review_required"] is False
    assert aggregate["formal_failures"] == [
        "backslash:dispersed:1:RESPONSE_SLOPE"
    ]


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (
            lambda value: value.__setitem__("classifying_record_count", 26),
            "identity or coverage",
        ),
        (
            lambda value: value["sequence_results"].pop(),
            "exactly eight sequences",
        ),
        (
            lambda value: value["sequence_results"].__setitem__(
                7, copy.deepcopy(value["sequence_results"][0])
            ),
            "duplicated",
        ),
    ],
)
def test_aggregate_rejects_incomplete_or_duplicate_coverage(tmp_path, mutation, message):
    module = _load()
    values = _values(module)
    mutation(values["S3_V2_FLAT_4A_SLASH"])
    with pytest.raises(module.CoordinatorError, match=message):
        _aggregate(module, tmp_path, values)


def test_aggregate_rejects_replica_byte_disagreement(tmp_path):
    module = _load()
    first = _values(module)
    second = copy.deepcopy(first)
    second["S3_V2_FLAT_4A_ALTERNATING"]["sequence_results"][0][
        "energy_norm_slope"
    ] = 1.21
    with pytest.raises(module.CoordinatorError, match="checker replicas disagree"):
        _aggregate(module, tmp_path, first, second)


def test_blocked_aggregate_uses_the_same_fixed_schema_as_scientific_aggregate(tmp_path):
    module = _load()
    passed = _aggregate(module, tmp_path, _values(module))
    blocked = module.blocked_aggregate(
        authorization_sha256="F" * 64,
        contract_sha256="E" * 64,
        producer_result_sha256=None,
        reason="FORMAL_PROCESS_FAILED",
    )
    assert set(blocked) == set(passed)
    assert blocked["terminal"] == module.BLOCKED
    assert blocked["formal_failures"] == ["FORMAL_PROCESS_FAILED"]
    assert blocked["sequence_results"] == []
    assert blocked["producer_wave_result_sha256"] is None
    assert blocked["successor_expansion_authorized"] is False


def test_coordinator_wall_guard_publishes_canonical_blocked_aggregate(tmp_path):
    module = _load()
    aggregate_path = (tmp_path / "stage4a-aggregate.json").resolve()
    guard = module._CoordinatorWallGuard(
        aggregate_path=aggregate_path,
        started=time.monotonic(),
        exit_function=lambda _code: None,
    )
    guard.bind_evidence(
        authorization_sha256="A" * 64,
        contract_sha256="B" * 64,
    )
    aggregate = guard.publish_fail_closed()
    assert aggregate["terminal"] == module.BLOCKED
    assert aggregate["formal_failures"] == ["COORDINATOR_WALL_EXCEEDED"]
    value, raw = module.strict_json_load(aggregate_path)
    assert value == aggregate
    assert raw == module.canonical_bytes(value)


def test_watchdog_never_publishes_while_a_process_tree_may_be_live(
    tmp_path, monkeypatch
):
    module = _load()
    observed_waits = []
    observed_exits = []

    class NeverStopped:
        @staticmethod
        def wait(seconds):
            observed_waits.append(seconds)
            return False

    monkeypatch.setattr(module.time, "monotonic", lambda: 100.0)
    aggregate_path = (tmp_path / "stage4a-aggregate.json").resolve()
    guard = module._CoordinatorWallGuard(
        aggregate_path=aggregate_path,
        started=100.0,
        exit_function=observed_exits.append,
    )
    guard.bind_evidence(
        authorization_sha256="A" * 64,
        contract_sha256="B" * 64,
    )
    guard.mark_process_phase_active()
    guard._stop = NeverStopped()
    guard._publisher_main()
    assert guard._expired.is_set()
    assert guard.publish_fail_closed() is None
    assert not aggregate_path.exists()
    guard._hard_exit_main()
    assert observed_waits == [
        float(
            module.COORDINATOR_WALL_SECONDS
            - module.COORDINATOR_FAIL_CLOSED_PUBLICATION_RESERVE_SECONDS
        ),
        float(module.COORDINATOR_WALL_SECONDS),
    ]
    assert observed_exits == [module.COORDINATOR_HARD_EXIT_CODE]


def test_expired_main_checkpoint_publishes_only_after_tree_terminal_proof(
    tmp_path
):
    module = _load()
    aggregate_path = (tmp_path / "stage4a-aggregate.json").resolve()
    guard = module._CoordinatorWallGuard(
        aggregate_path=aggregate_path,
        started=time.monotonic(),
        exit_function=lambda _code: None,
    )
    guard.bind_evidence(
        authorization_sha256="A" * 64,
        contract_sha256="B" * 64,
    )
    guard.mark_process_phase_active()
    guard._expired.set()
    with pytest.raises(module._CoordinatorWallExceeded):
        guard.checkpoint()
    assert not aggregate_path.exists()
    guard.mark_process_phase_terminal(proven=True)
    with pytest.raises(module._CoordinatorWallExceeded):
        guard.checkpoint()
    value, raw = module.strict_json_load(aggregate_path)
    assert raw == module.canonical_bytes(value)
    assert value["formal_failures"] == ["COORDINATOR_WALL_EXCEEDED"]


def test_coordinator_hard_wall_uses_absolute_deadline_and_exit_code(monkeypatch):
    module = _load()
    observed_waits = []
    observed_exits = []

    class NeverStopped:
        @staticmethod
        def wait(seconds):
            observed_waits.append(seconds)
            return False

    monkeypatch.setattr(module.time, "monotonic", lambda: 100.0)
    guard = module._CoordinatorWallGuard(
        aggregate_path=Path("aggregate.json"),
        started=100.0,
        exit_function=observed_exits.append,
    )
    guard._stop = NeverStopped()
    guard._hard_exit_main()
    assert observed_waits == [float(module.COORDINATOR_WALL_SECONDS)]
    assert observed_exits == [module.COORDINATOR_HARD_EXIT_CODE]


def test_normal_publication_fails_before_writing_in_reserved_window(
    tmp_path, monkeypatch
):
    module = _load()
    path = (tmp_path / "canonical.json").resolve()

    class ExpiredGuard:
        @staticmethod
        def require_canonical_publication_is_safe(_path):
            return None

        @staticmethod
        def checkpoint():
            raise module._CoordinatorWallExceeded("synthetic wall")

    monkeypatch.setattr(module, "_ACTIVE_COORDINATOR_GUARD", ExpiredGuard())
    with pytest.raises(module._CoordinatorWallExceeded, match="synthetic wall"):
        module._write_exclusive(path, b"{}\n")
    assert not path.exists()


def test_canonical_aggregate_is_rejected_when_tree_terminal_is_unproven(
    tmp_path, monkeypatch
):
    module = _load()
    aggregate_path = (tmp_path / "stage4a-aggregate.json").resolve()
    diagnostic_path = (tmp_path / "stage4a-process-incident.json").resolve()
    guard = module._CoordinatorWallGuard(
        aggregate_path=aggregate_path,
        started=time.monotonic(),
        exit_function=lambda _code: None,
    )
    guard.mark_process_phase_active()
    monkeypatch.setattr(module, "_ACTIVE_COORDINATOR_GUARD", guard)
    with pytest.raises(module.CoordinatorError, match="proven-empty"):
        module._write_exclusive(aggregate_path, b"{}\n")
    module._write_exclusive(diagnostic_path, b"{}\n")
    assert not aggregate_path.exists()
    assert diagnostic_path.read_bytes() == b"{}\n"


def test_run_stage4a_installs_wall_before_any_guarded_work(tmp_path, monkeypatch):
    module = _load()
    observed = []
    made = module.blocked_aggregate(
        authorization_sha256="A" * 64,
        contract_sha256="B" * 64,
        producer_result_sha256=None,
        reason="FORMAL_PROCESS_FAILED",
    )

    def fake_guarded(*args):
        guard = args[-1]
        observed.append(
            (
                module._ACTIVE_COORDINATOR_GUARD is guard,
                guard.hard_deadline - guard.work_deadline,
            )
        )
        return made

    monkeypatch.setattr(module, "_run_stage4a_guarded", fake_guarded)
    result = module.run_stage4a(
        tmp_path / "contract.json",
        tmp_path / "authorization.json",
        tmp_path,
        tmp_path / "aggregate.json",
    )
    assert result == made
    assert observed == [
        (True, float(module.COORDINATOR_FAIL_CLOSED_PUBLICATION_RESERVE_SECONDS))
    ]
    assert module._ACTIVE_COORDINATOR_GUARD is None


def test_registered_resource_command_isolated_and_supplies_only_bound_dependencies(tmp_path):
    module = _load()
    command = module.expected_resource_command(
        python_executable=Path(sys.executable),
        contract_path=ROOT / "contract.json",
        authorization_path=ROOT / "authorization.json",
        output_root=tmp_path,
        aggregate_path=tmp_path / "stage4a-aggregate.json",
    )
    assert "$env:PYTHONNOUSERSITE='1';" in command
    assert "$env:PYTHONDONTWRITEBYTECODE='1';" in command
    assert " -I -B " in command
    for _name, repository in module.DEPENDENCY_REPOSITORIES:
        assert str((repository / "src").resolve()) in command
    assert str(module.ROOT / "src") not in command
    assert command.count("--run-stage4a") == 1


def _checker_proofs(module, tmp_path):
    return {
        assignment_id: (tmp_path / assignment_id / "proof.json").resolve()
        for assignment_id in module.EXPECTED_SHARDS
    }


class _SyntheticCheckerResources:
    def __init__(self, available_values):
        self._available_values = iter(available_values)
        self.calls = 0

    def available_physical_memory_bytes(self):
        self.calls += 1
        return next(self._available_values)


def test_checker_policy_freezes_three_registered_but_only_two_concurrent_workers():
    module = _load()
    assert module.AUTHORITY_SCHEMA == "anysolver.e4-pl-s3-v2-stage4a-authority-v5"
    assert module.CONTRACT_SCHEMA == "anysolver.e4-pl-s3-v2-stage4a-contract-v5"
    assert module.MAXIMUM_REGISTERED_WORKERS == 3
    assert module.MAXIMUM_CONCURRENT_WORKERS == 2
    assert module._checker_replica_required_memory_bytes() == 64 * (1 << 30)
    assert module._execution_policy() == {
        "canonical_aggregate_requires_proven_empty_process_trees": True,
        "checker_tree_drain_required_before_queue_advance": True,
        "checker_phase_finalization_reserve_seconds": 60,
        "checker_phase_required_seconds": 960,
        "checker_phase_schedule": "REPLICA_PAIRS_BY_FROZEN_SHARD_ORDER",
        "checker_replica_wall_seconds": 300,
        "checker_replicas_per_shard": 2,
        "coordinator_wall_seconds": 1800,
        "coordinator_fail_closed_publication_reserve_seconds": 15,
        "coordinator_hard_exit_code": 124,
        "coordinator_work_deadline_action": "MARK_EXPIRED_ONLY",
        "git_subprocess_wall_seconds": 60,
        "hard_coordinator_wall_enforced": True,
        "inactivity_seconds": 300,
        "maximum_concurrent_workers": 2,
        "maximum_memory_gib_per_process_tree": 24,
        "maximum_workers": 3,
        "memory_admission_headroom_gib": 16,
        "memory_admission_required_bytes": 68_719_476_736,
        "no_automatic_retry": True,
        "numerical_library_threads_per_worker": 1,
        "producer_wall_seconds": 900,
        "registered_shards": 3,
        "schedule": "TWO_CONCURRENT_THEN_REMAINING_ONE_IN_FROZEN_ORDER",
        "timeout_aggregate_requires_proven_empty_process_trees": True,
        "unproven_tree_hard_deadline_action": (
            "EXIT_WITHOUT_CANONICAL_AGGREGATE"
        ),
        "wave_wall_seconds": 1800,
    }
    assert (
        "tests/test_e4_pl_s3_v2_bounded_process.py"
        in module.REQUIRED_FROZEN_PATHS
    )


def test_checker_phase_runs_replica_pairs_in_frozen_order_without_lost_coverage(
    tmp_path, monkeypatch
):
    module = _load()
    required = module._checker_replica_required_memory_bytes()
    resources = _SyntheticCheckerResources([required])
    lock = threading.Lock()
    active = 0
    maximum_active = 0
    events = []
    calls = {}

    def fake_checker(**kwargs):
        nonlocal active, maximum_active
        assignment_id = kwargs["assignment_id"]
        replica = int(kwargs["output"].parent.parent.name.rsplit("-", 1)[1])
        task_id = (replica, assignment_id)
        with lock:
            calls[task_id] = calls.get(task_id, 0) + 1
            active += 1
            maximum_active = max(maximum_active, active)
            events.append(("START", task_id))
        time.sleep(0.15)
        with lock:
            events.append(("END", task_id))
            active -= 1
        return {"assignment_id": assignment_id, "replica": replica}

    monkeypatch.setattr(module, "_run_checker_process", fake_checker)
    results = module._run_checker_phase(
        bounded=resources,
        proofs=_checker_proofs(module, tmp_path),
        plan=(tmp_path / "plan.json").resolve(),
        output_root=tmp_path.resolve(),
        deadline=time.monotonic() + module.CHECKER_PHASE_REQUIRED_SECONDS + 1,
    )

    frozen_order = list(module.EXPECTED_SHARDS)
    submission_order = [
        (replica, assignment_id)
        for assignment_id in frozen_order
        for replica in (1, 2)
    ]
    assert [result["assignment_id"] for result in results[0]] == frozen_order
    assert [result["assignment_id"] for result in results[1]] == frozen_order
    assert calls == {task_id: 1 for task_id in submission_order}
    assert resources.calls == 1
    assert maximum_active == 2
    assert [task_id for event, task_id in events[:2] if event == "START"] == (
        submission_order[:2]
    )
    for pair_index in range(1, 3):
        pair_start = events.index(("START", submission_order[pair_index * 2]))
        assert sum(event == "END" for event, _task_id in events[:pair_start]) >= 2


def test_checker_phase_resource_deferral_occurs_before_any_launch(
    tmp_path, monkeypatch
):
    module = _load()
    required = module._checker_replica_required_memory_bytes()
    resources = _SyntheticCheckerResources([required - 1])
    calls = []

    def fake_checker(**kwargs):
        calls.append((kwargs["assignment_id"], kwargs["output"]))
        return {"assignment_id": kwargs["assignment_id"]}

    monkeypatch.setattr(module, "_run_checker_process", fake_checker)
    with pytest.raises(module.CoordinatorError, match="resources are deferred"):
        module._run_checker_phase(
            bounded=resources,
            proofs=_checker_proofs(module, tmp_path),
            plan=(tmp_path / "plan.json").resolve(),
            output_root=tmp_path.resolve(),
            deadline=time.monotonic() + module.CHECKER_PHASE_REQUIRED_SECONDS + 1,
        )
    assert resources.calls == 1
    assert calls == []
    assert not list(tmp_path.glob("checker-replica-*"))


def test_checker_phase_time_deferral_occurs_before_any_launch(tmp_path, monkeypatch):
    module = _load()
    resources = _SyntheticCheckerResources(
        [module._checker_replica_required_memory_bytes()]
    )
    calls = []
    monkeypatch.setattr(
        module, "_run_checker_process", lambda **kwargs: calls.append(kwargs)
    )
    with pytest.raises(module.CoordinatorError, match="insufficient coordinator-wall"):
        module._run_checker_phase(
            bounded=resources,
            proofs=_checker_proofs(module, tmp_path),
            plan=(tmp_path / "plan.json").resolve(),
            output_root=tmp_path.resolve(),
            deadline=time.monotonic() + module.CHECKER_PHASE_REQUIRED_SECONDS - 1,
        )
    assert calls == []
    assert not list(tmp_path.glob("checker-replica-*"))


def test_checker_failure_is_not_retried_and_does_not_drop_queued_work(
    tmp_path, monkeypatch
):
    module = _load()
    resources = _SyntheticCheckerResources(
        [module._checker_replica_required_memory_bytes()]
    )
    frozen_order = list(module.EXPECTED_SHARDS)
    calls = {(replica, assignment_id): 0 for assignment_id in frozen_order for replica in (1, 2)}
    lock = threading.Lock()

    def fake_checker(**kwargs):
        assignment_id = kwargs["assignment_id"]
        replica = int(kwargs["output"].parent.parent.name.rsplit("-", 1)[1])
        task_id = (replica, assignment_id)
        with lock:
            calls[task_id] += 1
        if task_id == (1, frozen_order[0]):
            raise module.CoordinatorError("synthetic checker failure")
        time.sleep(0.05)
        return {"assignment_id": assignment_id, "replica": replica}

    monkeypatch.setattr(module, "_run_checker_process", fake_checker)
    with pytest.raises(module.CoordinatorError, match="all six registered tasks"):
        module._run_checker_phase(
            bounded=resources,
            proofs=_checker_proofs(module, tmp_path),
            plan=(tmp_path / "plan.json").resolve(),
            output_root=tmp_path.resolve(),
            deadline=time.monotonic() + module.CHECKER_PHASE_REQUIRED_SECONDS + 1,
        )
    assert all(count == 1 for count in calls.values())


def test_checker_tree_drain_failure_blocks_later_pairs_without_cancelling_peer(
    tmp_path, monkeypatch
):
    module = _load()
    resources = _SyntheticCheckerResources(
        [module._checker_replica_required_memory_bytes()]
    )
    guard = module._CoordinatorWallGuard(
        aggregate_path=(tmp_path / "stage4a-aggregate.json").resolve(),
        started=time.monotonic(),
        exit_function=lambda _code: None,
    )
    guard.bind_evidence(
        authorization_sha256="A" * 64,
        contract_sha256="B" * 64,
    )
    frozen_order = list(module.EXPECTED_SHARDS)
    calls = []
    completed = []
    lock = threading.Lock()

    def fake_checker(**kwargs):
        assignment_id = kwargs["assignment_id"]
        replica = int(kwargs["output"].parent.parent.name.rsplit("-", 1)[1])
        task_id = (replica, assignment_id)
        with lock:
            calls.append(task_id)
        if task_id == (1, frozen_order[0]):
            raise module._CheckerTreeNotDrained("synthetic uncontained tree")
        time.sleep(0.05)
        with lock:
            completed.append(task_id)
        return {"assignment_id": assignment_id, "replica": replica}

    monkeypatch.setattr(module, "_run_checker_process", fake_checker)
    with pytest.raises(module.CoordinatorError, match="queue blocked"):
        module._run_checker_phase(
            bounded=resources,
            proofs=_checker_proofs(module, tmp_path),
            plan=(tmp_path / "plan.json").resolve(),
            output_root=tmp_path.resolve(),
            deadline=time.monotonic() + module.CHECKER_PHASE_REQUIRED_SECONDS + 1,
            wall_guard=guard,
        )
    assert sorted(calls) == sorted(
        [(1, frozen_order[0]), (2, frozen_order[0])]
    )
    assert completed == [(2, frozen_order[0])]
    guard._expired.set()
    assert guard.publish_fail_closed() is None
    assert not guard.aggregate_path.exists()


def test_checker_root_exit_with_live_tree_requires_proven_termination(
    tmp_path, monkeypatch
):
    module = _load()

    class Process:
        returncode = 0

        @staticmethod
        def poll():
            return 0

    class Job:
        instance = None

        def __init__(self, _memory_limit):
            type(self).instance = self
            self.terminate_calls = 0
            self.closed = False

        @staticmethod
        def launch(*_args, **_kwargs):
            return Process()

        @staticmethod
        def accounting():
            return 1, 1, 1

        def terminate(self):
            self.terminate_calls += 1
            return False

        def close(self):
            self.closed = True

    class Bounded:
        _ProcessJob = Job

        @staticmethod
        def _environment():
            return {}

    monkeypatch.setattr(module, "_load_module", lambda *_args: Bounded)
    root = (tmp_path / "checker").resolve()
    with pytest.raises(module._CheckerTreeNotDrained, match="could not prove"):
        module._run_checker_process(
            assignment_id=next(iter(module.EXPECTED_SHARDS)),
            proof=(tmp_path / "proof.json").resolve(),
            plan=(tmp_path / "plan.json").resolve(),
            output=root / "checker.json",
            stdout_path=root / "stdout.log",
            stderr_path=root / "stderr.log",
            deadline=time.monotonic() + 10,
        )
    assert Job.instance.terminate_calls == 1
    assert Job.instance.closed is True


def test_producer_phase_requires_every_launched_tree_terminal_proof():
    module = _load()
    assert module._producer_process_trees_proven_terminal(
        {"terminal": "RESOURCE_DEFERRED", "workers": []}
    )
    assert module._producer_process_trees_proven_terminal(
        {
            "terminal": "COMPLETED",
            "workers": [
                {"termination_proven": True},
                {"termination_proven": True},
                {"termination_proven": True},
            ],
        }
    )
    assert not module._producer_process_trees_proven_terminal(
        {
            "terminal": "BLOCKED_E4_PL_S3_V2_PROCESS_OR_EVIDENCE",
            "workers": [
                {"termination_proven": True},
                {"termination_proven": False},
            ],
        }
    )


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("assignment_sha256", "7" * 64),
        ("plan_sha256", "8" * 64),
        ("proof_sha256", "9" * 64),
    ],
)
def test_checker_must_join_exact_producer_assignment_plan_and_proof(
    tmp_path, field, replacement
):
    module = _load()
    values = _values(module)
    values["S3_V2_FLAT_4A_SLASH"][field] = replacement
    with pytest.raises(module.CoordinatorError, match="not joined"):
        _aggregate(module, tmp_path, values)


def test_validate_producer_proofs_recomputes_each_scientific_hash(tmp_path):
    module = _load()
    workers = []
    completed = []
    for assignment_id in module.EXPECTED_SHARDS:
        proof = (tmp_path / assignment_id / "scientific.json").resolve()
        proof.parent.mkdir(parents=True)
        proof.write_bytes(assignment_id.encode("ascii"))
        workers.append(
            {
                "assignment_id": assignment_id,
                "assignment_sha256": "A" * 64,
                "plan_sha256": "B" * 64,
                "scientific_path": str(proof),
            }
        )
        completed.append(
            {
                "assignment_id": assignment_id,
                "assignment_sha256": "A" * 64,
                "cpu_100ns": 1,
                "input_hashes": [],
                "last_progress_sequence": 31,
                "peak_tree_memory_bytes": 1,
                "plan_sha256": "B" * 64,
                "program_sha256": "C" * 64,
                "returncode": 0,
                "scientific_byte_count": proof.stat().st_size,
                "scientific_payload_sha256": "D" * 64,
                "scientific_record_count": 27,
                "scientific_record_ids_sha256": "E" * 64,
                "scientific_schema": "proof-v1",
                "scientific_sha256": module.sha256(proof.read_bytes()),
                "scientific_terminal": "ACCEPTED_FOR_AGGREGATION",
                "status": "COMPLETED",
                "stderr_sha256": module.sha256(b""),
                "stdout_sha256": module.sha256(b""),
                "termination_proven": True,
            }
        )
    manifest = {"workers": workers}
    manifest_raw = module.canonical_bytes(manifest)
    result = {
        "lane": "flat-proof",
        "manifest_sha256": module.sha256(manifest_raw),
        "schema": module.PRODUCER_RESULT_SCHEMA,
        "terminal": "COMPLETED",
        "wave_id": "S3_V2_FLAT_FUNNEL_4A_FULL",
        "workers": completed,
    }
    result_raw = module.canonical_bytes(result)
    bindings = module.validate_producer_proofs(
        manifest, manifest_raw, result, result_raw
    )
    assert set(bindings) == set(module.EXPECTED_SHARDS)
    completed[0]["scientific_sha256"] = "F" * 64
    mutated_raw = module.canonical_bytes(result)
    with pytest.raises(module.CoordinatorError, match="proof binding differs"):
        module.validate_producer_proofs(manifest, manifest_raw, result, mutated_raw)


def test_approval_snapshot_recomputes_preserved_ledger_bytes(tmp_path, monkeypatch):
    module = _load()
    request_id = "1" * 32
    request_path = (tmp_path / f"{request_id}.json").resolve()
    request_raw = module.canonical_bytes({"request_id": request_id})
    request_path.write_bytes(request_raw)
    live_ledger = (tmp_path / "live-ledger.md").resolve()
    approved_line = f"| 2026-08-31 | {request_id} | APPROVED | exact |"
    ledger_raw = (approved_line + "\n").encode("utf-8")
    live_ledger.write_bytes(ledger_raw)
    monkeypatch.setattr(module, "RESOURCE_LEDGER_PATH", live_ledger)
    preserved = (tmp_path / "resource-ledger-pre-run.md").resolve()
    preserved.write_bytes(ledger_raw)
    contract = {"candidate": {"commit": "a" * 40, "tree": "b" * 40}}
    snapshot = {
        "approved_row": {
            "line": approved_line,
            "sha256": module.sha256((approved_line + "\n").encode("utf-8")),
        },
        "candidate": contract["candidate"],
        "ledger": {
            "byte_count": len(ledger_raw),
            "path": str(live_ledger),
            "sha256": module.sha256(ledger_raw),
            "snapshot_path": str(preserved),
        },
        "request": {
            "byte_count": len(request_raw),
            "path": str(request_path),
            "request_id": request_id,
            "sha256": module.sha256(request_raw),
        },
        "schema": "anysolver.e4-pl-s3-v2-stage4a-approval-snapshot-v2",
    }
    snapshot_path = (tmp_path / "approval-snapshot.json").resolve()
    snapshot_path.write_bytes(module.canonical_bytes(snapshot))
    value, raw = module._validate_approval_snapshot(
        snapshot_path,
        contract=contract,
        request_id=request_id,
        request_path=request_path,
        request_raw=request_raw,
    )
    assert value == snapshot
    assert raw == module.canonical_bytes(snapshot)
    preserved.write_bytes(ledger_raw + b"mutation\n")
    with pytest.raises(module.CoordinatorError, match="identity differs"):
        module._validate_approval_snapshot(
            snapshot_path,
            contract=contract,
            request_id=request_id,
            request_path=request_path,
            request_raw=request_raw,
        )


def test_atomic_publication_never_exposes_partial_canonical_path(tmp_path, monkeypatch):
    module = _load()
    output = tmp_path / "canonical.json"
    real_link = module.os.link

    def fail_link(_source, _target):
        raise OSError("synthetic promotion failure")

    monkeypatch.setattr(module.os, "link", fail_link)
    with pytest.raises(OSError, match="synthetic"):
        module._write_exclusive(output, b"complete\n")
    assert not output.exists()
    assert not list(tmp_path.glob(".canonical.json.pending-*"))
    monkeypatch.setattr(module.os, "link", real_link)
    module._write_exclusive(output, b"complete\n")
    assert output.read_bytes() == b"complete\n"
    with pytest.raises(module.CoordinatorError, match="overwrite"):
        module._write_exclusive(output, b"other\n")


def test_candidate_archive_extraction_rejects_escape_and_is_exclusive(
    tmp_path, monkeypatch
):
    module = _load()
    monkeypatch.setattr(
        module.tempfile,
        "mkdtemp",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("candidate extraction must inherit the output-root ACL")
        ),
    )
    safe_root = tmp_path / "safe"
    safe_root.mkdir()
    safe_archive = safe_root / "candidate.tar"
    with tarfile.open(safe_archive, "w") as bundle:
        directory = tarfile.TarInfo("src/anysolver/")
        directory.type = tarfile.DIRTYPE
        bundle.addfile(directory)
        payload = b"# exact candidate\n"
        member = tarfile.TarInfo("src/anysolver/__init__.py")
        member.size = len(payload)
        bundle.addfile(member, io.BytesIO(payload))
    extracted = module._extract_candidate_archive(safe_archive, safe_root)
    assert (extracted / "src" / "anysolver" / "__init__.py").read_bytes() == payload
    fresh_child = subprocess.run(
        [
            sys.executable,
            "-I",
            "-c",
            "from pathlib import Path; import sys; print(Path(sys.argv[1]).read_text())",
            str(extracted / "src" / "anysolver" / "__init__.py"),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert fresh_child.stdout.strip() == "# exact candidate"
    with pytest.raises(module.CoordinatorError, match="already exists"):
        module._extract_candidate_archive(safe_archive, safe_root)

    bad_root = tmp_path / "bad"
    bad_root.mkdir()
    bad_archive = bad_root / "candidate.tar"
    with tarfile.open(bad_archive, "w") as bundle:
        payload = b"escape"
        member = tarfile.TarInfo("../escape.txt")
        member.size = len(payload)
        bundle.addfile(member, io.BytesIO(payload))
    with pytest.raises(module.CoordinatorError, match="unsafe path"):
        module._extract_candidate_archive(bad_archive, bad_root)
    assert not (tmp_path / "escape.txt").exists()


def test_producer_result_is_contained_by_registered_wave_root(tmp_path):
    module = _load()
    wave_root = (tmp_path / "producer-wave").resolve()
    manifest = {
        "lane": "flat-proof",
        "output_root": str(wave_root),
        "schema": "anysolver.e4-pl-s3-v2-bounded-wave-manifest-v1",
        "wave_id": "S3_V2_FLAT_FUNNEL_4A_FULL",
        "workers": [],
    }
    manifest_path = (tmp_path / "producer-wave-manifest.json").resolve()
    manifest_path.write_bytes(module.canonical_bytes(manifest))
    result_path = module._producer_result_path(manifest_path)
    assert result_path == wave_root / "producer-wave-result.json"
    assert result_path.is_relative_to(wave_root)
    assert result_path != tmp_path / "producer-wave-result.json"


def test_process_incident_records_exact_failure_stage(tmp_path):
    module = _load()
    path = (tmp_path / "stage4a-process-incident.json").resolve()
    module._write_process_incident(
        path,
        authorization_sha256="A" * 64,
        contract_sha256="B" * 64,
        error=module.CoordinatorError("synthetic containment failure"),
        phase="PRODUCER_WAVE",
        producer_result_path=None,
    )
    value, raw = module.strict_json_load(path)
    assert raw == module.canonical_bytes(value)
    assert value == {
        "authorization_sha256": "A" * 64,
        "contract_sha256": "B" * 64,
        "errno": None,
        "exception_message": "synthetic containment failure",
        "exception_type": (
            f"{module.CoordinatorError.__module__}.CoordinatorError"
        ),
        "phase": "PRODUCER_WAVE",
        "producer_result_sha256": None,
        "schema": "anysolver.e4-pl-s3-v2-stage4a-process-incident-v1",
        "winerror": None,
    }


def test_formal_main_returns_nonzero_for_blocked_aggregate(tmp_path, monkeypatch):
    module = _load()
    blocked = module.blocked_aggregate(
        authorization_sha256="F" * 64,
        contract_sha256="E" * 64,
        producer_result_sha256=None,
        reason="FORMAL_PROCESS_FAILED",
    )
    monkeypatch.setattr(module, "run_stage4a", lambda *_args, **_kwargs: blocked)
    code = module.main(
        [
            "--run-stage4a",
            "--contract",
            str(tmp_path / "contract.json"),
            "--authorization",
            str(tmp_path / "authorization.json"),
            "--output-root",
            str(tmp_path),
            "--aggregate",
            str(tmp_path / "aggregate.json"),
        ]
    )
    assert code == 2


def test_git_launcher_and_engine_identity_is_complete():
    module = _load()
    runtime = module._discover_git_runtime()
    assert Path(runtime["launcher_path"]).is_file()
    assert Path(runtime["engine_path"]).is_file()
    assert Path(runtime["exec_path"]).is_dir()
    assert runtime["launcher_sha256"] == module.sha256(
        Path(runtime["launcher_path"]).read_bytes()
    )
    assert runtime["engine_sha256"] == module.sha256(
        Path(runtime["engine_path"]).read_bytes()
    )
    assert runtime["version"].startswith("git version ")


def test_every_git_subprocess_receives_a_finite_wall_timeout(monkeypatch):
    module = _load()
    observed = []

    def fake_run(command, **kwargs):
        observed.append((command, kwargs))
        return subprocess.CompletedProcess(command, 0, stdout=b"", stderr=b"")

    monkeypatch.setattr(module, "_git_command", lambda *_args, **_kwargs: ["git"])
    monkeypatch.setattr(module, "_git_environment", lambda: {})
    monkeypatch.setattr(module.subprocess, "run", fake_run)
    module._git_run("status")
    assert len(observed) == 1
    assert observed[0][1]["timeout"] == float(module.GIT_SUBPROCESS_WALL_SECONDS)


def test_git_timeout_is_capped_by_coordinator_reserved_deadline(monkeypatch):
    module = _load()
    now = time.monotonic()
    observed = []

    class ActiveGuard:
        work_deadline = now + 5.0

        @staticmethod
        def checkpoint():
            return None

    def fake_run(command, **kwargs):
        observed.append(kwargs["timeout"])
        return subprocess.CompletedProcess(command, 0, stdout=b"", stderr=b"")

    monkeypatch.setattr(module, "_ACTIVE_COORDINATOR_GUARD", ActiveGuard())
    monkeypatch.setattr(module, "_git_command", lambda *_args, **_kwargs: ["git"])
    monkeypatch.setattr(module, "_git_environment", lambda: {})
    monkeypatch.setattr(module.subprocess, "run", fake_run)
    module._git_run("status")
    assert len(observed) == 1
    assert 0 < observed[0] <= 5.0


def test_git_timeout_failure_is_fail_closed(monkeypatch):
    module = _load()

    def timeout(*_args, **_kwargs):
        raise subprocess.TimeoutExpired(["git"], 1)

    monkeypatch.setattr(module, "_git_command", lambda *_args, **_kwargs: ["git"])
    monkeypatch.setattr(module, "_git_environment", lambda: {})
    monkeypatch.setattr(module.subprocess, "run", timeout)
    with pytest.raises(module.CoordinatorError, match="exceeded its bound"):
        module._git_run("status")
