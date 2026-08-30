from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
PROGRAM = ROOT / "docs/reference_cases/e4_pl_s3_v2_bounded_process.py"
CONTRACT = ROOT / "docs/reference_cases/e4_pl_s3_v2_bounded_execution_contract.json"


def _load():
    spec = importlib.util.spec_from_file_location("s3_v2_bounded_process", PROGRAM)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(spec.name, None)
    return module


def _manifest(tmp_path: Path, *, lane: str = "flat-proof", wall: int = 900):
    program_path = (tmp_path / "worker.py").resolve()
    plan_path = (tmp_path / "plan.json").resolve()
    input_path = (tmp_path / "input.bin").resolve()
    return {
        "schema": "anysolver.e4-pl-s3-v2-bounded-wave-manifest-v1",
        "wave_id": "wave-1",
        "lane": lane,
        "output_root": str(tmp_path),
        "workers": [
            {
                "assignment_id": "shard-1",
                "assignment_sha256": "A" * 64,
                "command": [sys.executable, str(program_path)],
                "cwd": str(tmp_path),
                "expected_record_count": 1,
                "expected_selector": "e4-pl-s3-v2",
                "input_hashes": [{"path": str(input_path), "sha256": "B" * 64}],
                "plan_path": str(plan_path),
                "plan_sha256": "C" * 64,
                "progress_path": str(tmp_path / "shard-1" / "progress.ndjson"),
                "program_path": str(program_path),
                "program_sha256": "D" * 64,
                "scientific_path": str(tmp_path / "shard-1" / "scientific.json"),
                "scientific_schema": "test.s3-v2-scientific-v1",
                "stdout_path": str(tmp_path / "shard-1" / "stdout.bin"),
                "stderr_path": str(tmp_path / "shard-1" / "stderr.bin"),
                "wall_seconds": wall,
            }
        ],
    }


def test_frozen_bounds_are_finite_and_below_thirty_minutes():
    module = _load()
    assert module.WAVE_WALL_SECONDS == 1800
    assert module.MAX_WORKER_WALL_SECONDS == 1500
    assert module.INACTIVITY_SECONDS == 300
    assert module.JOB_MEMORY_LIMIT_BYTES == 24 * (1 << 30)
    assert max(module.LANE_WALL_LIMITS.values()) == 1500
    assert None not in module.LANE_WALL_LIMITS.values()


def test_every_registered_contract_hard_wall_has_an_exact_runner_lane():
    module = _load()
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    walls = contract["command_hard_walls_seconds"]
    expected = {
        "authority": walls["authority_and_static"],
        "static": walls["authority_and_static"],
        "aggregation": walls["final_aggregation"],
        "package": walls["package_isolation"],
        "flat-proof": walls["flat_exact_or_local_proof"],
        "local-proof": walls["flat_exact_or_local_proof"],
        "mixed": walls["mixed_curved_or_recovery"],
        "curved": walls["mixed_curved_or_recovery"],
        "recovery": walls["mixed_curved_or_recovery"],
        "nonlinear": walls["nonlinear_performance_or_qv10"],
        "performance": walls["nonlinear_performance_or_qv10"],
        "qv10": walls["nonlinear_performance_or_qv10"],
    }
    assert module.LANE_WALL_LIMITS == expected


def test_manifest_enforces_lane_limit_and_output_containment(tmp_path):
    module = _load()
    made = _manifest(tmp_path)
    _, lane, root, workers = module.validate_manifest(made)
    assert lane == "flat-proof"
    assert root == tmp_path
    assert workers[0].wall_seconds == 900
    assert workers[0].scientific_path == tmp_path / "shard-1" / "scientific.json"
    assert workers[0].scientific_schema == "test.s3-v2-scientific-v1"
    assert workers[0].expected_record_count == 1
    assert workers[0].expected_selector == "e4-pl-s3-v2"
    assert workers[0].assignment_sha256 == "A" * 64
    assert workers[0].program_path == tmp_path / "worker.py"
    assert workers[0].plan_path == tmp_path / "plan.json"
    assert workers[0].input_hashes[0].path == tmp_path / "input.bin"

    made["workers"][0]["wall_seconds"] = 901
    with pytest.raises(module.BoundedProcessError, match="exceeds lane policy"):
        module.validate_manifest(made)

    made = _manifest(tmp_path)
    made["workers"][0]["stdout_path"] = str(tmp_path.parent / "escape.bin")
    with pytest.raises(module.BoundedProcessError, match="escapes output_root"):
        module.validate_manifest(made)


def test_manifest_rejects_duplicate_assignments_and_more_than_three(tmp_path):
    module = _load()
    made = _manifest(tmp_path)
    made["workers"] = made["workers"] * 2
    with pytest.raises(module.BoundedProcessError, match="duplicate assignment"):
        module.validate_manifest(made)
    made = _manifest(tmp_path)
    made["workers"] = [dict(made["workers"][0], assignment_id=str(i)) for i in range(4)]
    with pytest.raises(module.BoundedProcessError, match="one to three"):
        module.validate_manifest(made)


def test_run_wave_rejects_noncanonical_manifest_and_result_escape(tmp_path):
    module = _load()
    made = _manifest(tmp_path)
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(made, indent=2) + "\n", encoding="utf-8")
    with pytest.raises(module.BoundedProcessError, match="manifest is not canonical"):
        module.run_wave(manifest_path, tmp_path / "result.json")

    manifest_path.write_bytes(module.canonical_json_bytes(made))
    with pytest.raises(module.BoundedProcessError, match="escapes output_root"):
        module.run_wave(manifest_path, tmp_path.parent / "escaped-result.json")


def test_formal_run_wave_fails_closed_without_windows_job_objects(tmp_path, monkeypatch):
    module = _load()
    made = _manifest(tmp_path)
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_bytes(module.canonical_json_bytes(made))
    monkeypatch.setattr(module, "_formal_platform_name", lambda: "posix")
    with pytest.raises(module.BoundedProcessError, match="Windows Job Object"):
        module.run_wave(manifest_path, tmp_path / "result.json")


def test_run_wave_rejects_preexisting_scientific_output(tmp_path, monkeypatch):
    module = _load()
    made = _manifest(tmp_path, lane="authority", wall=5)
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_bytes(module.canonical_json_bytes(made))
    scientific = Path(made["workers"][0]["scientific_path"])
    scientific.parent.mkdir(parents=True)
    scientific.write_bytes(b"preexisting")
    monkeypatch.setattr(module, "_formal_platform_name", lambda: "nt")
    monkeypatch.setattr(module, "available_physical_memory_bytes", lambda: 1 << 50)
    with pytest.raises(module.BoundedProcessError, match="exclusive worker output exists"):
        module.run_wave(manifest_path, tmp_path / "result.json")


def test_strict_json_rejects_duplicate_and_nonfinite(tmp_path):
    module = _load()
    duplicate = tmp_path / "duplicate.json"
    duplicate.write_text('{"a":1,"a":2}', encoding="utf-8")
    with pytest.raises(module.BoundedProcessError, match="duplicate"):
        module.strict_json_load(duplicate)
    nonfinite = tmp_path / "nonfinite.json"
    nonfinite.write_text('{"a":NaN}', encoding="utf-8")
    with pytest.raises(module.BoundedProcessError, match="non-finite"):
        module.strict_json_load(nonfinite)


def test_registered_program_plan_and_input_hashes_are_verified(tmp_path):
    module = _load()
    program = tmp_path / "worker.py"
    program.write_bytes(b"pass\n")
    plan = tmp_path / "plan.json"
    plan.write_bytes(module.canonical_json_bytes({"schema": "test.plan-v1"}))
    registered_input = tmp_path / "input.bin"
    registered_input.write_bytes(b"input\n")
    made = _manifest(tmp_path)
    worker = made["workers"][0]
    worker["program_sha256"] = module.sha256_bytes(program.read_bytes())
    worker["plan_sha256"] = module.sha256_bytes(plan.read_bytes())
    worker["input_hashes"][0]["sha256"] = module.sha256_bytes(
        registered_input.read_bytes()
    )
    spec = module.validate_manifest(made)[3][0]
    module._verify_worker_bindings(spec)

    registered_input.write_bytes(b"mutated\n")
    with pytest.raises(module.BoundedProcessError, match="input hash mismatch"):
        module._verify_worker_bindings(spec)

    registered_input.write_bytes(b"input\n")
    program.write_bytes(b"raise SystemExit\n")
    with pytest.raises(module.BoundedProcessError, match="program hash mismatch"):
        module._verify_worker_bindings(spec)

    program.write_bytes(b"pass\n")
    plan.write_bytes(b'{"schema": "test.plan-v1"}\n')
    worker["plan_sha256"] = module.sha256_bytes(plan.read_bytes())
    noncanonical_spec = module.validate_manifest(made)[3][0]
    with pytest.raises(module.BoundedProcessError, match="plan is not canonical"):
        module._verify_worker_bindings(noncanonical_spec)


def test_progress_requires_monotone_schema_and_identity(tmp_path):
    module = _load()
    path = tmp_path / "progress.ndjson"
    rows = [
        {
            "schema": module.PROGRESS_SCHEMA,
            "assignment_id": "s",
            "sequence": i,
            "phase": "CASE",
            "completed": i,
            "total": 2,
        }
        for i in range(2)
    ]
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    assert module._progress_sequence(path, "s") == 1
    rows[1]["sequence"] = 3
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    with pytest.raises(module.BoundedProcessError, match="sequence"):
        module._progress_sequence(path, "s")


def test_complete_progress_requires_all_registered_phases_in_order(tmp_path):
    module = _load()
    path = tmp_path / "progress.ndjson"
    phases = list(module.REQUIRED_PROGRESS_PHASES)
    rows = [
        {
            "schema": module.PROGRESS_SCHEMA,
            "assignment_id": "s",
            "sequence": index,
            "phase": phase,
            "completed": index,
            "total": len(phases),
        }
        for index, phase in enumerate(phases)
    ]
    path.write_text(
        "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8"
    )
    assert module._require_complete_progress(path, "s").sequence == len(phases) - 1

    rows.insert(
        2,
        {
            "schema": module.PROGRESS_SCHEMA,
            "assignment_id": "s",
            "sequence": 2,
            "phase": "EXTRA_DIAGNOSTIC",
            "completed": 1,
            "total": len(phases),
        },
    )
    for index, row in enumerate(rows):
        row["sequence"] = index
    path.write_text(
        "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8"
    )
    assert module._require_complete_progress(path, "s").sequence == len(rows) - 1

    rows[-2]["phase"] = "AUTHORITY_COMPLETE"
    path.write_text(
        "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8"
    )
    with pytest.raises(module.BoundedProcessError, match="out of order"):
        module._progress_sequence(path, "s")


def test_worker_environment_forces_one_thread(monkeypatch):
    module = _load()
    monkeypatch.setenv("OMP_NUM_THREADS", "99")
    made = module._environment()
    assert made["PYTHONHASHSEED"] == "0"
    assert all(made[name] == "1" for name in module.THREAD_ENVIRONMENT)


def test_canonical_output_is_stable_and_exclusive(tmp_path):
    module = _load()
    payload = module.canonical_json_bytes({"b": 1, "a": [True, None]})
    assert payload == b'{"a":[true,null],"b":1}\n'
    target = tmp_path / "result.json"
    module._publish_exclusive(target, payload)
    assert target.read_bytes() == payload
    with pytest.raises(FileExistsError):
        module._publish_exclusive(target, payload)


def _scientific_envelope(module, spec):
    record_ids = ["record-1"]
    scientific_payload = {"records": [{"exact": True}]}
    return {
        "schema": spec.scientific_schema,
        "assignment_sha256": spec.assignment_sha256,
        "plan_sha256": spec.plan_sha256,
        "selector": spec.expected_selector,
        "record_count": 1,
        "record_ids": record_ids,
        "record_ids_sha256": module.sha256_bytes(
            module.canonical_json_bytes(record_ids)
        ),
        "scientific_payload": scientific_payload,
        "scientific_payload_sha256": module.sha256_bytes(
            module.canonical_json_bytes(scientific_payload)
        ),
        "terminal": "ACCEPTED_FOR_AGGREGATION",
    }


def test_scientific_envelope_binds_identity_coverage_payload_and_terminal(tmp_path):
    module = _load()
    spec = module.validate_manifest(_manifest(tmp_path))[3][0]
    spec.scientific_path.parent.mkdir(parents=True)
    envelope = _scientific_envelope(module, spec)
    spec.scientific_path.write_bytes(module.canonical_json_bytes(envelope))
    metadata = module._scientific_metadata(spec)
    assert metadata.record_count == 1
    assert metadata.terminal == "ACCEPTED_FOR_AGGREGATION"

    mutations = [
        ("assignment_sha256", "F" * 64, "assignment hash"),
        ("plan_sha256", "F" * 64, "plan hash"),
        ("selector", "legacy-s3", "selector"),
        ("record_count", 2, "record count"),
        ("record_ids", ["record-1", "record-1"], "record IDs"),
        ("record_ids_sha256", "F" * 64, "record IDs hash"),
        ("scientific_payload", {"records": []}, "payload hash"),
        ("scientific_payload_sha256", "F" * 64, "payload hash"),
        ("terminal", "NO_GO", "terminal"),
    ]
    for field, value, message in mutations:
        mutated = dict(envelope)
        mutated[field] = value
        spec.scientific_path.write_bytes(module.canonical_json_bytes(mutated))
        with pytest.raises(module.BoundedProcessError, match=message):
            module._scientific_metadata(spec)

    spec.scientific_path.write_bytes(
        module.canonical_json_bytes({"schema": spec.scientific_schema})
    )
    with pytest.raises(module.BoundedProcessError, match="keys differ"):
        module._scientific_metadata(spec)


def _worker_program() -> str:
    return (
        "import hashlib,json,pathlib,sys;"
        "progress=pathlib.Path(sys.argv[1]);science=pathlib.Path(sys.argv[2]);mode=sys.argv[3];"
        "assignment_sha256=sys.argv[4];plan_sha256=sys.argv[5];selector=sys.argv[6];"
        "progress.parent.mkdir(parents=True,exist_ok=True);"
        "phases=['INITIALIZATION','AUTHORITY_COMPLETE','CASE_OR_REFINEMENT_OR_STATION',"
        "'STAGING','VALIDATION','COMPLETION'];"
        "phases=phases[:-1] if mode=='missing-phase' else phases;"
        "rows=[{'schema':'anysolver.e4-pl-s3-v2-worker-progress-v1',"
        "'assignment_id':'shard-1','sequence':i,'phase':phase,"
        "'completed':i+1,'total':len(phases)} for i,phase in enumerate(phases)];"
        "progress.write_text(''.join(json.dumps(row,sort_keys=True,separators=(',',':'))+'\\n' "
        "for row in rows),encoding='utf-8');"
        "canonical=lambda value:(json.dumps(value,sort_keys=True,separators=(',',':'))+'\\n').encode('ascii');"
        "record_ids=['record-1'];scientific_payload={'records':[{'exact':True}]};"
        "payload={'schema':('wrong.schema' if mode=='wrong-schema' else "
        "'test.s3-v2-scientific-v1'),'assignment_sha256':assignment_sha256,"
        "'plan_sha256':plan_sha256,'selector':selector,'record_count':1,"
        "'record_ids':record_ids,'record_ids_sha256':hashlib.sha256(canonical(record_ids)).hexdigest().upper(),"
        "'scientific_payload':scientific_payload,"
        "'scientific_payload_sha256':hashlib.sha256(canonical(scientific_payload)).hexdigest().upper(),"
        "'terminal':'ACCEPTED_FOR_AGGREGATION'};"
        "raw=canonical(payload);"
        "raw=(json.dumps(payload,indent=2)+'\\n').encode('ascii') if mode=='noncanonical' else raw;"
        "science.write_bytes(raw) if mode!='missing-science' else None"
    )


def _run_worker_wave(module, tmp_path: Path, monkeypatch, mode: str):
    module = _load()
    progress = tmp_path / "shard-1" / "progress.ndjson"
    scientific = tmp_path / "shard-1" / "scientific.json"
    program = tmp_path / "worker.py"
    program.write_text(_worker_program(), encoding="utf-8")
    plan = tmp_path / "plan.json"
    plan.write_bytes(module.canonical_json_bytes({"schema": "test.plan-v1"}))
    registered_input = tmp_path / "input.bin"
    registered_input.write_bytes(b"frozen input\n")
    made = _manifest(tmp_path, lane="authority", wall=5)
    made["workers"][0]["command"] = [
        sys.executable,
        str(program.resolve()),
        str(progress),
        str(scientific),
        mode,
    ]
    made["workers"][0]["program_sha256"] = module.sha256_bytes(program.read_bytes())
    made["workers"][0]["plan_sha256"] = module.sha256_bytes(plan.read_bytes())
    made["workers"][0]["input_hashes"][0]["sha256"] = module.sha256_bytes(
        registered_input.read_bytes()
    )
    assignment_sha256 = made["workers"][0]["assignment_sha256"]
    plan_sha256 = made["workers"][0]["plan_sha256"]
    selector = made["workers"][0]["expected_selector"]
    made["workers"][0]["command"].extend(
        [assignment_sha256, plan_sha256, selector]
    )
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_bytes(module.canonical_json_bytes(made))
    result_path = tmp_path / "result.json"
    monkeypatch.setattr(module, "_formal_platform_name", lambda: "nt")
    monkeypatch.setattr(module, "available_physical_memory_bytes", lambda: 1 << 50)
    result = module.run_wave(manifest_path, result_path)
    assert module.strict_json_load(result_path) == result
    return result, scientific


def test_run_wave_assigns_process_tree_and_publishes_result(tmp_path, monkeypatch):
    module = _load()
    result, scientific = _run_worker_wave(module, tmp_path, monkeypatch, "valid")
    assert result["terminal"] == "COMPLETED", (
        result["workers"][0]["status"],
        result["workers"][0]["termination_proven"],
        result["workers"][0]["scientific_byte_count"],
        result["workers"][0]["scientific_sha256"],
    )
    assert result["workers"][0]["status"] == "COMPLETED"
    assert result["workers"][0]["termination_proven"] is True
    assert result["workers"][0]["last_progress_sequence"] == 5
    assert result["workers"][0]["assignment_sha256"] == "A" * 64
    assert result["workers"][0]["plan_sha256"] == module.sha256_bytes(
        (tmp_path / "plan.json").read_bytes()
    )
    assert result["workers"][0]["program_sha256"] == module.sha256_bytes(
        (tmp_path / "worker.py").read_bytes()
    )
    assert result["workers"][0]["input_hashes"] == [
        {
            "path": str((tmp_path / "input.bin").resolve()),
            "sha256": module.sha256_bytes((tmp_path / "input.bin").read_bytes()),
        }
    ]
    assert result["workers"][0]["scientific_byte_count"] == scientific.stat().st_size
    assert result["workers"][0]["scientific_record_count"] == 1
    assert result["workers"][0]["scientific_terminal"] == "ACCEPTED_FOR_AGGREGATION"
    assert result["workers"][0]["scientific_record_ids_sha256"] is not None
    assert result["workers"][0]["scientific_payload_sha256"] is not None
    assert result["workers"][0]["scientific_sha256"] == module.sha256_bytes(
        scientific.read_bytes()
    )


@pytest.mark.parametrize(
    ("mode", "exists"),
    [
        ("missing-science", False),
        ("wrong-schema", True),
        ("noncanonical", True),
        ("missing-phase", True),
    ],
)
def test_exit_zero_with_invalid_evidence_blocks(tmp_path, monkeypatch, mode, exists):
    module = _load()
    result, scientific = _run_worker_wave(module, tmp_path, monkeypatch, mode)
    worker = result["workers"][0]
    assert result["terminal"] == "BLOCKED_E4_PL_S3_V2_PROCESS_OR_EVIDENCE"
    assert worker["status"] == "MALFORMED_PROGRESS_OR_SCIENTIFIC_EVIDENCE"
    assert scientific.exists() is exists
    if exists:
        assert worker["scientific_byte_count"] == scientific.stat().st_size
        assert worker["scientific_sha256"] == module.sha256_bytes(
            scientific.read_bytes()
        )
    else:
        assert worker["scientific_byte_count"] is None
        assert worker["scientific_sha256"] is None
