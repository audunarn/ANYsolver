"""Run the complete S3 activation-v3 qualification under activity controls.

The coordinator imports only the standard library, validates a reviewed final
candidate binding before mechanics imports, assigns every worker a canonical
hash-bound shard, and applies a complete-tree 24-GiB memory limit plus a
30-minute inactivity watchdog.  There is deliberately no elapsed runtime
ceiling; elapsed values are diagnostics and cannot classify a cycle.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from copy import deepcopy
from dataclasses import dataclass
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_CASES = ROOT / "docs" / "reference_cases"
BASE_PROGRAM = REFERENCE_CASES / "e4_pl_s3_default_activation_v2.py"
BASE_INPUT = REFERENCE_CASES / "e4_pl_s3_default_activation_v2_input.json"
SUCCESSOR = REFERENCE_CASES / "e4_pl_s3_qualification_optimization_v3.py"
CONTRACT = REFERENCE_CASES / "e4_pl_s3_qualification_optimization_v3_contract.json"
COLD_COORDINATOR = ROOT / "scripts" / "benchmark_e4_pl_s3_activation_cold_path.py"
BINDING_GENERATOR = ROOT / "scripts" / "prepare_e4_pl_s3_qualification_v3_input.py"
WORKER_SCHEMA = "anysolver.e4-pl-s3-default-activation-worker-v3"
SCIENTIFIC_SCHEMA = "anysolver.e4-pl-s3-default-activation-scientific-v3"
CYCLE_SET_SCHEMA = "anysolver.e4-pl-s3-default-activation-cycle-set-v3"
ASSIGNMENT_SCHEMA = "anysolver.e4-pl-s3-formal-shard-assignment-v3"
AUTHORIZATION_SCHEMA = "anysolver.e4-pl-s3-qualification-authorization-v3"
STRUCTURAL_WORKERS = (
    "STRUCTURAL_SLASH",
    "STRUCTURAL_BACKSLASH",
    "STRUCTURAL_ALTERNATING",
)
FOLLOWUP_WORKERS = ("EIGEN_PERFORMANCE", "SPECIAL_ECOSYSTEM")
BATCH_WORKERS = ("BATCH_0", "BATCH_1", "BATCH_2")
WORKERS = STRUCTURAL_WORKERS + FOLLOWUP_WORKERS + BATCH_WORKERS
WAVES = (STRUCTURAL_WORKERS, FOLLOWUP_WORKERS, BATCH_WORKERS)
TERMINALS = (
    "BLOCKED_E4_PL_S3_DEFAULT_ACTIVATION_EVIDENCE_OR_REVIEW",
    "NO_GO_E4_PL_S3_DEFAULT_ACTIVATION_QUALIFICATION",
    "PROVISIONAL_GO_E4_PL_S3_DEFAULT_ACTIVATION",
)
PRODUCTION_RESTRICTION = "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"
THREAD_ENVIRONMENT = {
    "OMP_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
    "NUMEXPR_NUM_THREADS": "1",
    "PYTHONHASHSEED": "0",
}
INACTIVITY_SECONDS = 1800
MEMORY_LIMIT_BYTES = 24 * (1 << 30)
MAX_RECORD_BYTES = 4 * (1 << 20)


class QualificationError(ValueError):
    """Successor authority, worker evidence, or coverage is malformed."""


def _reject_constant(value: str) -> None:
    raise QualificationError(f"nonfinite JSON value is forbidden: {value}")


def _pairs(values: Sequence[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in values:
        if key in result:
            raise QualificationError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def canonical_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        + b"\n"
    )


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def read_json(path: Path, *, canonical: bool = True) -> tuple[bytes, dict[str, Any]]:
    raw = path.read_bytes()
    if not raw or len(raw) > MAX_RECORD_BYTES:
        raise QualificationError(f"JSON record size is invalid: {path}")
    value = json.loads(
        raw,
        object_pairs_hook=_pairs,
        parse_constant=_reject_constant,
    )
    if not isinstance(value, dict):
        raise QualificationError(f"JSON record is not an object: {path}")
    if canonical and raw != canonical_bytes(value):
        raise QualificationError(f"JSON record is not canonical: {path}")
    return raw, value


def write_exclusive(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(canonical_bytes(value))


def _load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise QualificationError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@dataclass(frozen=True)
class SuccessorAuthority:
    base: Any
    successor: Any
    authority: Any
    binding_path: Path
    binding_raw: bytes
    binding: dict[str, Any]
    authorization_path: Path
    authorization_raw: bytes
    authorization: dict[str, Any]


def _live_file_binding(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    return {
        "bytes": len(raw),
        "path": path.resolve().relative_to(ROOT.resolve()).as_posix(),
        "sha256": sha256(raw),
    }


def _load_frozen_v2_scientific_authority(
    base: Any,
    binding_path: Path,
    binding_raw: bytes,
    binding: Mapping[str, Any],
    target: Path,
) -> Any:
    """Load v2 science without touching obsolete candidate worktrees."""

    input_raw, payload = base._read_json(
        BASE_INPUT, pretty=True, label="frozen v2 scientific input"
    )
    base._exact_keys(
        payload,
        ("candidates", "contract", "evidence", "execution", "programs", "schema"),
        "frozen v2 input",
    )
    if payload["schema"] != base.INPUT_SCHEMA:
        raise QualificationError("frozen v2 input schema differs")
    contract_row = payload["contract"]
    base._exact_keys(contract_row, ("bytes", "path", "sha256"), "v2 contract")
    contract_path = (ROOT / str(contract_row["path"])).resolve(strict=True)
    contract_raw, contract = base._read_json(
        contract_path, pretty=True, label="frozen v2 scientific contract"
    )
    if (
        len(contract_raw) != int(contract_row["bytes"])
        or sha256(contract_raw) != str(contract_row["sha256"])
        or contract.get("schema") != base.CONTRACT_SCHEMA
    ):
        raise QualificationError("frozen v2 contract binding differs")
    programs = payload["programs"]
    if not isinstance(programs, dict) or set(programs) != {
        "batch_benchmark",
        "runner",
        "test",
    }:
        raise QualificationError("frozen v2 program set differs")
    for name, row in programs.items():
        base._exact_keys(row, ("bytes", "path", "sha256"), f"v2 program {name}")
        program_path = (ROOT / str(row["path"])).resolve(strict=True)
        program_raw = program_path.read_bytes()
        if (
            len(program_raw) != int(row["bytes"])
            or sha256(program_raw) != str(row["sha256"])
        ):
            raise QualificationError(f"frozen v2 program differs: {name}")
    evidence = payload["evidence"]
    manifest_row = evidence.get("connectivity_manifest") if isinstance(evidence, dict) else None
    if not isinstance(manifest_row, dict) or set(manifest_row) != {
        "bytes",
        "path",
        "sha256",
    }:
        raise QualificationError("frozen connectivity authority differs")
    manifest_path = Path(str(manifest_row["path"]))
    if not manifest_path.is_absolute():
        manifest_path = ROOT / manifest_path
    manifest_path = manifest_path.resolve(strict=True)
    manifest_raw = manifest_path.read_bytes()
    if (
        len(manifest_raw) != int(manifest_row["bytes"])
        or sha256(manifest_raw) != str(manifest_row["sha256"])
    ):
        raise QualificationError("frozen connectivity manifest differs")
    manifest = base.strict_json(manifest_raw, label="frozen connectivity manifest")
    if not isinstance(manifest, dict) or len(manifest.get("records", ())) != 252:
        raise QualificationError("frozen connectivity manifest coverage differs")
    updated_input = deepcopy(payload)
    updated_input["candidates"] = deepcopy(binding["candidates"])
    updated_input["execution"] = {
        "automatic_retry": False,
        "inactivity_seconds": INACTIVITY_SECONDS,
        "memory_limit_gib_per_process": 24,
        "runtime_classification": False,
        "target": str(target),
        "total_runtime_limit_seconds": None,
        "workers_maximum": 3,
    }
    return base.Authority(
        input_path=binding_path.resolve(),
        input_raw=binding_raw,
        input=updated_input,
        contract_path=contract_path,
        contract_raw=contract_raw,
        contract=contract,
        manifest_path=manifest_path,
        manifest_raw=manifest_raw,
        manifest=manifest,
        target=target,
    )


def load_authority(binding_path: Path, authorization_path: Path) -> SuccessorAuthority:
    """Validate final successor authority before any mechanics import."""

    generator = _load_module("_s3_v3_binding_generator", BINDING_GENERATOR)
    binding_raw, binding = read_json(binding_path)
    if set(binding) != {
        "anysolver_policy",
        "candidate_graph",
        "candidate_preflight",
        "candidates",
        "execution_target",
        "files",
        "formal_execution_authorized",
        "production_restriction",
        "schema",
    }:
        raise QualificationError("candidate binding fields differ")
    if (
        binding["schema"] != generator.SCHEMA
        or binding["formal_execution_authorized"] is not False
        or binding["production_restriction"] != PRODUCTION_RESTRICTION
    ):
        raise QualificationError("candidate binding policy differs")
    expected_files = {
        "binding_generator": _live_file_binding(BINDING_GENERATOR),
        "contract": _live_file_binding(CONTRACT),
        "coordinator": _live_file_binding(COLD_COORDINATOR),
        "formal_runner": _live_file_binding(Path(__file__).resolve()),
        "formal_test": _live_file_binding(
            ROOT / "tests" / "test_e4_pl_s3_qualification_optimization_v3.py"
        ),
        "manifest": _live_file_binding(
            REFERENCE_CASES / "e4_pl_s3_mixed_mesh_connectivity_manifest.json"
        ),
        "optimization_evidence": _live_file_binding(
            REFERENCE_CASES / "e4_pl_s3_qualification_optimization_v3_evidence.json"
        ),
        "successor": _live_file_binding(SUCCESSOR),
        "test": _live_file_binding(
            ROOT / "tests" / "test_e4_pl_s3_activation_cold_path.py"
        ),
    }
    if binding["files"] != expected_files:
        raise QualificationError("candidate binding program graph differs")
    candidates = binding["candidates"]
    if not isinstance(candidates, dict) or set(candidates) != set(generator.CANDIDATES):
        raise QualificationError("candidate graph membership or order differs")
    for name in generator.CANDIDATES:
        if generator._verify_candidate(name, candidates[name]) != candidates[name]:
            raise QualificationError(f"{name} candidate identity differs")
    preflight = binding["candidate_preflight"]
    if not isinstance(preflight, dict) or set(preflight) != set(generator.CANDIDATES):
        raise QualificationError("candidate preflight membership differs")
    for name in generator.CANDIDATES:
        entry = preflight[name]
        if not isinstance(entry, dict) or set(entry) != {"record", "result"}:
            raise QualificationError(f"{name} candidate preflight fields differ")
        if generator._verify_preflight(name, candidates[name], entry["result"]) != entry:
            raise QualificationError(f"{name} candidate preflight differs")
    policy = binding["anysolver_policy"]
    if (
        not isinstance(policy, dict)
        or policy.get("q4_mechanics_git_blob")
        != "59ceb9534dfd22e05ea69296f92abeb0511f14cf"
    ):
        raise QualificationError("qualified Q4 mechanics identity differs")
    target = Path(str(binding["execution_target"])).resolve(strict=True)
    authorization_raw, authorization = read_json(authorization_path)
    if set(authorization) != {
        "candidate_binding",
        "formal_execution_authorized",
        "independent_review_sha256",
        "production_restriction",
        "schema",
        "user_approval_recorded",
    }:
        raise QualificationError("authorization fields differ")
    expected_binding = {
        "bytes": len(binding_raw),
        "path": str(binding_path.resolve()),
        "sha256": sha256(binding_raw),
    }
    reviews = authorization["independent_review_sha256"]
    if (
        authorization["schema"] != AUTHORIZATION_SCHEMA
        or authorization["candidate_binding"] != expected_binding
        or authorization["formal_execution_authorized"] is not True
        or authorization["user_approval_recorded"] is not True
        or authorization["production_restriction"] != PRODUCTION_RESTRICTION
        or not isinstance(reviews, list)
        or len(reviews) != 2
        or len(set(reviews)) != 2
        or any(
            type(value) is not str
            or len(value) != 64
            or any(character not in "0123456789ABCDEF" for character in value)
            for value in reviews
        )
    ):
        raise QualificationError("authorization is incomplete or malformed")
    base = _load_module("_s3_activation_v3_base", BASE_PROGRAM)
    authority = _load_frozen_v2_scientific_authority(
        base,
        binding_path,
        binding_raw,
        binding,
        target,
    )
    successor = _load_module("_s3_activation_v3_successor", SUCCESSOR)
    return SuccessorAuthority(
        base,
        successor,
        authority,
        binding_path,
        binding_raw,
        binding,
        authorization_path,
        authorization_raw,
        authorization,
    )


def _manifest_rows(authority: SuccessorAuthority, diagonal: str) -> list[dict[str, Any]]:
    rows = [
        dict(row)
        for row in authority.authority.manifest["records"]
        if row.get("diagonal") == diagonal
    ]
    if len(rows) != 84:
        raise QualificationError(f"{diagonal} assignment is not exactly 84 records")
    return rows


def _special_lanes(authority: SuccessorAuthority) -> tuple[list[dict[str, Any]], int]:
    _raw, contract = read_json(CONTRACT, canonical=False)
    formal = contract.get("formal_runner")
    overlay = formal.get("special_lane_overlay") if isinstance(formal, dict) else None
    if not isinstance(overlay, list) or len(overlay) != 3:
        raise QualificationError("v3 special-lane overlay differs")
    historical = deepcopy(
        authority.authority.contract["coverage"]["special_pytest_lanes"]
    )
    lanes = historical + deepcopy(overlay)
    names = [row.get("name") for row in lanes if isinstance(row, dict)]
    if len(names) != len(lanes) or len(set(names)) != len(lanes):
        raise QualificationError("special lane identities are duplicated")
    return lanes, len(overlay)


def build_assignment(authority: SuccessorAuthority, worker_id: str) -> dict[str, Any]:
    if worker_id not in WORKERS:
        raise QualificationError(f"unknown worker: {worker_id}")
    if worker_id in STRUCTURAL_WORKERS:
        diagonal = worker_id.removeprefix("STRUCTURAL_").lower()
        rows = _manifest_rows(authority, diagonal)
        payload: dict[str, Any] = {
            "diagonal": diagonal,
            "manifest_records": [
                {"record": row, "sha256": sha256(canonical_bytes(row))}
                for row in rows
            ],
            "record_count": 84,
        }
    elif worker_id == "EIGEN_PERFORMANCE":
        selected = []
        for fraction in (0, 10, 25):
            mask = "none" if fraction == 0 else "dispersed"
            matches = [
                dict(row)
                for row in authority.authority.manifest["records"]
                if row.get("level") == 20
                and row.get("s3_area_fraction_percent") == fraction
                and row.get("mask") == mask
                and row.get("diagonal") == "alternating"
            ]
            if len(matches) != 1:
                raise QualificationError("eigen topology assignment differs")
            selected.append(
                {
                    "record": matches[0],
                    "sha256": sha256(canonical_bytes(matches[0])),
                }
            )
        payload = {
            "buckling_cases": 2,
            "modal_cases": 2,
            "paired_performance_comparisons": 24,
            "topology_records": selected,
        }
    elif worker_id == "SPECIAL_ECOSYSTEM":
        lanes, overlay_count = _special_lanes(authority)
        payload = {
            "lane_count": len(lanes),
            "lanes": lanes,
            "registered_special_fixtures": 8,
            "v3_overlay_lane_count": overlay_count,
        }
    else:
        index = int(worker_id.removeprefix("BATCH_"))
        spec = authority.authority.contract["coverage"]["eigen_performance"][
            "batch"
        ]
        payload = {
            "eligible_element_count": int(spec["eligible_element_count"]),
            "repetition_indices": list(range(index, int(spec["repetitions"]), 3)),
            "shard_count": 3,
            "shard_index": index,
        }
    return {
        "authorization_sha256": sha256(authority.authorization_raw),
        "base_contract_sha256": sha256(authority.authority.contract_raw),
        "binding_sha256": sha256(authority.binding_raw),
        "formal_runner_sha256": sha256(Path(__file__).resolve().read_bytes()),
        "payload": payload,
        "schema": ASSIGNMENT_SCHEMA,
        "successor_sha256": sha256(SUCCESSOR.read_bytes()),
        "worker_id": worker_id,
    }


def read_assignment(
    authority: SuccessorAuthority, path: Path
) -> tuple[dict[str, Any], str]:
    raw, value = read_json(path)
    worker_id = value.get("worker_id")
    if type(worker_id) is not str or value != build_assignment(authority, worker_id):
        raise QualificationError("formal shard assignment differs")
    return value, sha256(raw)


def _checkpoint(path: Path, sequence: int, stage: str) -> None:
    with path.open("ab") as stream:
        stream.write(canonical_bytes({"sequence": sequence, "stage": stage}))
        stream.flush()
        os.fsync(stream.fileno())


def _await_tree_accounting_release(control: Any) -> None:
    release_name = os.environ.get(control.TREE_RELEASE_ENVIRONMENT)
    if not release_name:
        return
    release = Path(release_name)
    deadline = time.monotonic() + control.TREE_RELEASE_WAIT_SECONDS
    while not release.is_file():
        if time.monotonic() >= deadline:
            raise QualificationError("process-tree accounting was not released")
        time.sleep(0.01)
    if release.read_bytes() != control.TREE_RELEASE_BYTES:
        raise QualificationError("process-tree accounting release differs")


def run_worker(
    binding_path: Path,
    authorization_path: Path,
    assignment_path: Path,
    output: Path,
    progress: Path,
) -> None:
    control = _load_module("_s3_v3_worker_control", COLD_COORDINATOR)
    _await_tree_accounting_release(control)
    if {name: os.environ.get(name) for name in THREAD_ENVIRONMENT} != THREAD_ENVIRONMENT:
        raise QualificationError("worker thread environment differs")
    sequence = 0

    def checkpoint(stage: str) -> None:
        nonlocal sequence
        sequence += 1
        _checkpoint(progress, sequence, stage)

    checkpoint("worker-initialized")
    successor_authority = load_authority(binding_path, authorization_path)
    assignment, assignment_sha = read_assignment(successor_authority, assignment_path)
    worker_id = str(assignment["worker_id"])
    checkpoint("authority-and-assignment-verified")
    base = successor_authority.base
    successor = successor_authority.successor
    authority = successor_authority.authority
    bundle = successor.activate_assigned(base, authority)
    checkpoint("mechanics-activated")
    if worker_id in STRUCTURAL_WORKERS:
        original = base._structural_authority

        def structural_factory(value: Any, mechanics: Any, diagonal: str) -> Any:
            return successor.structural_authority(
                base,
                value,
                mechanics,
                diagonal,
                base_factory=original,
            )

        base._structural_authority = structural_factory
        # Coordinator authority has already validated and hash-bound all 252
        # rows; do not regenerate the full manifest independently per worker.
        bundle.manifest_generator.build_manifest = lambda: deepcopy(authority.manifest)
        gates, diagnostics, coverage = base._structural_worker(
            authority, bundle, worker_id
        )
    elif worker_id == "EIGEN_PERFORMANCE":
        gates, diagnostics, coverage = base._eigen_worker(authority, bundle)
    elif worker_id == "SPECIAL_ECOSYSTEM":
        base._run_pytest_lane = lambda value, name, cwd, nodes: (
            successor.run_pytest_lane_without_elapsed_ceiling(
                base, value, name, cwd, nodes
            )
        )
        lanes, overlay_count = _special_lanes(successor_authority)
        results: list[dict[str, Any]] = []
        for lane in lanes:
            root = Path(str(authority.input["candidates"][lane["repository"]]["root"])).resolve()
            nodes = [
                str(root / node.split("::", 1)[0])
                + ("::" + node.split("::", 1)[1] if "::" in node else "")
                for node in lane["nodes"]
            ]
            results.append(
                base._run_pytest_lane(authority, str(lane["name"]), root, nodes)
            )
        gates = {f"lane_{row['lane']}": bool(row["passed"]) for row in results}
        diagnostics = {
            row["lane"]: {key: value for key, value in row.items() if key != "lane"}
            for row in results
        }
        coverage = {
            "registered_special_fixtures": 8,
            "special_lanes": len(results),
            "v3_overlay_lanes": overlay_count,
        }
    else:
        gates, diagnostics, coverage = base._batch_shard_worker(
            authority,
            bundle,
            int(worker_id.removeprefix("BATCH_")),
        )
    checkpoint("scientific-work-complete")
    base._write_exclusive(output.with_name("diagnostic.json"), diagnostics, pretty=True)
    write_exclusive(
        output,
        {
            "assignment_sha256": assignment_sha,
            "coverage": coverage,
            "gates": gates,
            "production_restriction": PRODUCTION_RESTRICTION,
            "schema": WORKER_SCHEMA,
            "worker_id": worker_id,
        },
    )
    checkpoint("worker-output-complete")


@dataclass(frozen=True)
class ProcessRow:
    worker_id: str
    status: str
    returncode: int
    elapsed_ms: int
    peak_tree_memory_bytes: int
    assignment_sha256: str
    checkpoint_sha256: str
    last_checkpoint: str
    stdout_sha256: str
    stderr_sha256: str


def _environment(authority: SuccessorAuthority) -> dict[str, str]:
    environment = os.environ.copy()
    environment.update(THREAD_ENVIRONMENT)
    candidates = authority.binding["candidates"]
    pieces = [
        str(Path(authority.binding["execution_target"]).resolve()),
        str(Path(candidates["ANYstructure"]["root"]).resolve()),
        str(Path(candidates["ANYintelligent"]["root"]).resolve()),
    ]
    environment["PYTHONPATH"] = os.pathsep.join(pieces)
    environment["PYTHONNOUSERSITE"] = "1"
    environment["ANYSOLVER_S3_V3_CROSS_WHEEL"] = "1"
    environment["ANYSOLVER_S3_V3_TARGET"] = str(
        Path(authority.binding["execution_target"]).resolve()
    )
    return environment


def _checkpoint_identity(path: Path) -> tuple[str, str]:
    try:
        raw = path.read_bytes()
    except OSError:
        return "", ""
    last = ""
    for index, row in enumerate(raw.splitlines(keepends=True), start=1):
        value = json.loads(row, object_pairs_hook=_pairs, parse_constant=_reject_constant)
        if (
            not isinstance(value, dict)
            or value.get("sequence") != index
            or type(value.get("stage")) is not str
            or row != canonical_bytes(value)
        ):
            return sha256(raw), ""
        last = value["stage"]
    return sha256(raw) if raw else "", last


def _run_process(
    authority: SuccessorAuthority,
    worker_id: str,
    directory: Path,
    assignment_path: Path,
    assignment_sha: str,
) -> ProcessRow:
    control = _load_module(f"_s3_v3_control_{worker_id}", COLD_COORDINATOR)
    output = directory / "record.json"
    progress = directory / "progress.ndjson"
    stdout_path = directory / "stdout.log"
    stderr_path = directory / "stderr.log"
    release = directory / "tree-accounting.release"
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--worker",
        "--binding",
        str(authority.binding_path),
        "--authorization",
        str(authority.authorization_path),
        "--assignment",
        str(assignment_path),
        "--output",
        str(output),
        "--progress",
        str(progress),
    ]
    environment = _environment(authority)
    environment.pop(control.TREE_RELEASE_ENVIRONMENT, None)
    if os.name == "nt":
        environment[control.TREE_RELEASE_ENVIRONMENT] = str(release.resolve())
    started = time.monotonic_ns()
    status = "SPAWN_FAILED"
    returncode: int | None = None
    peak = -1
    process: Any | None = None
    controller: Any | None = None
    with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
        try:
            process = subprocess.Popen(
                command,
                cwd=directory,
                env=environment,
                stdin=subprocess.DEVNULL,
                stdout=stdout,
                stderr=stderr,
                creationflags=(
                    int(getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))
                    if os.name == "nt"
                    else 0
                ),
            )
        except (OSError, subprocess.SubprocessError):
            process = None
        if process is not None:
            try:
                controller = control._attach_tree_controller(process, MEMORY_LIMIT_BYTES)
            except (OSError, RuntimeError):
                status = "MEMORY_ACCOUNTING_UNAVAILABLE"
                control._terminate_tree(
                    process,
                    None,
                    deadline_ns=time.monotonic_ns()
                    + int(control.TERMINATION_BUDGET_SECONDS * 1.0e9),
                )
            else:
                try:
                    if os.name == "nt":
                        with release.open("xb") as stream:
                            stream.write(control.TREE_RELEASE_BYTES)
                    status = "RUNNING"
                    previous_activity: tuple[Any, ...] | None = None
                    last_activity = time.monotonic_ns()
                    while True:
                        try:
                            tree_peak, active, cpu = controller.sample_activity()
                        except (OSError, RuntimeError):
                            status = "MEMORY_ACCOUNTING_UNAVAILABLE"
                            break
                        peak = max(peak, int(tree_peak))
                        if tree_peak > MEMORY_LIMIT_BYTES:
                            status = "MEMORY_LIMIT"
                            break
                        returncode = process.poll()
                        if returncode is not None and active == 0:
                            break
                        now = time.monotonic_ns()
                        activity = (
                            cpu,
                            control._file_activity(progress),
                            control._file_activity(stdout_path),
                            control._file_activity(stderr_path),
                        )
                        if previous_activity is None or activity != previous_activity:
                            previous_activity = activity
                            last_activity = now
                        if now - last_activity >= INACTIVITY_SECONDS * 1_000_000_000:
                            status = "INACTIVITY_TIMEOUT"
                            break
                        time.sleep(0.05)
                    if status != "RUNNING":
                        control._terminate_tree(
                            process,
                            controller,
                            deadline_ns=time.monotonic_ns()
                            + int(control.TERMINATION_BUDGET_SECONDS * 1.0e9),
                        )
                    returncode = process.poll()
                    if status == "RUNNING":
                        if returncode == 0 and output.is_file():
                            try:
                                _read_worker(output, worker_id, assignment_sha)
                            except (OSError, QualificationError, TypeError, ValueError):
                                status = "MALFORMED_OUTPUT"
                            else:
                                status = "COMPLETE"
                        else:
                            status = "FAILED"
                except OSError:
                    status = "MEMORY_ACCOUNTING_UNAVAILABLE"
                    control._terminate_tree(
                        process,
                        controller,
                        deadline_ns=time.monotonic_ns()
                        + int(control.TERMINATION_BUDGET_SECONDS * 1.0e9),
                    )
            finally:
                if controller is not None:
                    try:
                        controller.close()
                    except (OSError, RuntimeError):
                        status = "MEMORY_ACCOUNTING_UNAVAILABLE"
    if status != "COMPLETE":
        output.unlink(missing_ok=True)
    checkpoint_sha, last_checkpoint = _checkpoint_identity(progress)
    ended = time.monotonic_ns()
    return ProcessRow(
        worker_id,
        status,
        -1 if returncode is None else int(returncode),
        int((ended - started) / 1_000_000),
        peak,
        assignment_sha,
        checkpoint_sha,
        last_checkpoint,
        sha256(stdout_path.read_bytes()),
        sha256(stderr_path.read_bytes()),
    )


def _read_worker(path: Path, worker_id: str, assignment_sha: str) -> dict[str, Any]:
    _raw, value = read_json(path)
    if set(value) != {
        "assignment_sha256",
        "coverage",
        "gates",
        "production_restriction",
        "schema",
        "worker_id",
    }:
        raise QualificationError(f"{worker_id} worker fields differ")
    if (
        value["schema"] != WORKER_SCHEMA
        or value["worker_id"] != worker_id
        or value["assignment_sha256"] != assignment_sha
        or value["production_restriction"] != PRODUCTION_RESTRICTION
        or not isinstance(value["coverage"], dict)
        or not isinstance(value["gates"], dict)
        or not value["gates"]
        or any(type(item) is not bool for item in value["gates"].values())
    ):
        raise QualificationError(f"{worker_id} worker identity differs")
    return value


def _coverage_complete(coverage: Mapping[str, int], authority: SuccessorAuthority) -> bool:
    special_lanes, overlay_count = _special_lanes(authority)
    return bool(
        all(
            coverage.get(f"{worker.lower()}::gated_topology_records") == 84
            and coverage.get(f"{worker.lower()}::global_convergence_records") == 84
            for worker in STRUCTURAL_WORKERS
        )
        and sum(
            coverage.get(f"{worker.lower()}::gated_topology_records", 0)
            for worker in STRUCTURAL_WORKERS
        )
        == 252
        and coverage.get("structural_slash::locking_records") == 18
        and coverage.get("eigen_performance::modal_cases") == 2
        and coverage.get("eigen_performance::buckling_cases") == 2
        and coverage.get("eigen_performance::paired_performance_comparisons") == 24
        and coverage.get("special_ecosystem::special_lanes")
        == len(special_lanes)
        and coverage.get("special_ecosystem::registered_special_fixtures") == 8
        and coverage.get("special_ecosystem::v3_overlay_lanes") == overlay_count
        and sum(
            coverage.get(f"{worker.lower()}::batch_repetitions", 0)
            for worker in BATCH_WORKERS
        )
        == 12
        and all(
            coverage.get(f"{worker.lower()}::batch_elements") == 4096
            for worker in BATCH_WORKERS
        )
    )


def run_cycle(authority: SuccessorAuthority, output_root: Path) -> tuple[bytes, dict[str, Any]]:
    output_root.mkdir(parents=True, exist_ok=False)
    assignments: dict[str, tuple[Path, str]] = {}
    for worker_id in WORKERS:
        directory = output_root / worker_id.lower()
        directory.mkdir()
        assignment = build_assignment(authority, worker_id)
        path = directory / "assignment.json"
        write_exclusive(path, assignment)
        assignments[worker_id] = (path, sha256(path.read_bytes()))
    rows: list[ProcessRow] = []
    for wave in WAVES:
        with ThreadPoolExecutor(max_workers=3, thread_name_prefix="s3-v3") as pool:
            futures = {
                pool.submit(
                    _run_process,
                    authority,
                    worker_id,
                    output_root / worker_id.lower(),
                    assignments[worker_id][0],
                    assignments[worker_id][1],
                ): worker_id
                for worker_id in wave
            }
            for future in as_completed(futures):
                worker_id = futures[future]
                try:
                    rows.append(future.result())
                except Exception:
                    rows.append(
                        ProcessRow(
                            worker_id,
                            "COORDINATOR_CHILD_ERROR",
                            -1,
                            0,
                            -1,
                            assignments[worker_id][1],
                            "",
                            "",
                            "",
                            "",
                        )
                    )
    rows.sort(key=lambda item: WORKERS.index(item.worker_id))
    blocked = len(rows) != len(WORKERS) or any(row.status != "COMPLETE" for row in rows)
    gates: dict[str, bool] = {}
    coverage: dict[str, int] = {}
    for row in rows:
        if row.status != "COMPLETE":
            continue
        try:
            worker = _read_worker(
                output_root / row.worker_id.lower() / "record.json",
                row.worker_id,
                row.assignment_sha256,
            )
            for name, passed in worker["gates"].items():
                key = f"{row.worker_id.lower()}::{name}"
                if key in gates:
                    raise QualificationError("duplicate worker gate")
                gates[key] = bool(passed)
            for name, count in worker["coverage"].items():
                coverage[f"{row.worker_id.lower()}::{name}"] = int(count)
        except (OSError, QualificationError, TypeError, ValueError):
            blocked = True
    if not blocked and not _coverage_complete(coverage, authority):
        blocked = True
    if not blocked:
        try:
            batch_gates, batch_diagnostic = authority.base._aggregate_batch_shards(
                authority.authority, output_root
            )
            gates.update(
                {f"batch_aggregate::{name}": bool(value) for name, value in batch_gates.items()}
            )
            authority.base._write_exclusive(
                output_root / "batch-aggregate-diagnostic.json",
                batch_diagnostic,
                pretty=True,
            )
        except (OSError, KeyError, TypeError, ValueError):
            blocked = True
    terminal = (
        TERMINALS[0]
        if blocked
        else TERMINALS[1]
        if not gates or not all(gates.values())
        else TERMINALS[2]
    )
    scientific = {
        "assignment_sha256": {
            worker_id: assignments[worker_id][1] for worker_id in WORKERS
        },
        "authorization_sha256": sha256(authority.authorization_raw),
        "candidate_binding_sha256": sha256(authority.binding_raw),
        "candidate_commits": {
            name: authority.binding["candidates"][name]["commit"]
            for name in sorted(authority.binding["candidates"])
        },
        "coverage": coverage,
        "gates": gates,
        "production_restriction": PRODUCTION_RESTRICTION,
        "schema": SCIENTIFIC_SCHEMA,
        "terminal": terminal,
    }
    raw = canonical_bytes(scientific)
    with (output_root / "scientific.json").open("xb") as stream:
        stream.write(raw)
    process_binding = {
        "inactivity_watchdog_seconds": INACTIVITY_SECONDS,
        "memory_limit_bytes_per_complete_tree": MEMORY_LIMIT_BYTES,
        "runtime_classification": False,
        "total_runtime_limit_seconds": None,
        "workers": [row.__dict__ for row in rows],
    }
    write_exclusive(output_root / "process-binding.json", process_binding)
    return raw, scientific


def run_cycles(
    authority: SuccessorAuthority, output_root: Path, cycles: int
) -> dict[str, Any]:
    if cycles not in (1, 2):
        raise QualificationError("cycles must be one or two")
    output_root.mkdir(parents=True, exist_ok=False)
    records = [run_cycle(authority, output_root / "cycle-1")]
    if cycles == 2 and records[0][1]["terminal"] == TERMINALS[2]:
        records.append(run_cycle(authority, output_root / "cycle-2"))
    identical = cycles == 1 or (
        len(records) == 2 and records[0][0] == records[1][0]
    )
    terminal = records[0][1]["terminal"] if len(records) == 1 else (
        TERMINALS[0] if not identical else records[1][1]["terminal"]
    )
    value = {
        "cycle_scientific_sha256": [sha256(raw) for raw, _value in records],
        "cycles_completed": len(records),
        "production_restriction": PRODUCTION_RESTRICTION,
        "runtime_classification": False,
        "schema": CYCLE_SET_SCHEMA,
        "scientific_byte_identical": identical,
        "terminal": terminal,
        "total_runtime_limit_seconds": None,
    }
    write_exclusive(output_root / "cycle-set.json", value)
    return value


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binding", type=Path, required=True)
    parser.add_argument("--authorization", type=Path, required=True)
    parser.add_argument("--authority-only", action="store_true")
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--assignment", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--progress", type=Path)
    parser.add_argument("--cycles", type=int, choices=(1, 2))
    parser.add_argument("--output-root", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.worker:
            if args.assignment is None or args.output is None or args.progress is None:
                raise QualificationError("worker paths are incomplete")
            run_worker(
                args.binding,
                args.authorization,
                args.assignment,
                args.output,
                args.progress,
            )
            return 0
        authority = load_authority(args.binding, args.authorization)
        if args.authority_only:
            print(sha256(authority.binding_raw))
            return 0
        if args.cycles is None or args.output_root is None:
            raise QualificationError("coordinator requires --cycles and --output-root")
        value = run_cycles(authority, args.output_root, args.cycles)
        print(value["terminal"])
        return 0 if value["terminal"] == TERMINALS[2] else 2
    except (OSError, QualificationError, subprocess.SubprocessError) as exc:
        print(f"qualification blocked: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
