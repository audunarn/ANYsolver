from __future__ import annotations

import copy
import io
import importlib.util
from pathlib import Path
import sys
import tarfile

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
        "exception_message": "synthetic containment failure",
        "exception_type": "CoordinatorError",
        "phase": "PRODUCER_WAVE",
        "producer_result_sha256": None,
        "schema": "anysolver.e4-pl-s3-v2-stage4a-process-incident-v1",
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
