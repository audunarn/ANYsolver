"""Bounded V6S Stage 4B runner for the current V2D candidate."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import copy
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace
from typing import Any, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "docs/reference_cases"
CONTRACT = REFERENCE / "e4_pl_s3_v6s_stage4b_contract.json"
HISTORICAL_INPUT = REFERENCE / "e4_pl_s3_v5i_stage4b_input.json"
HISTORICAL_STAGE4B = REFERENCE / "e4_pl_s3_v5i_stage4b.py"
HISTORICAL_REPAIR = REFERENCE / "e4_pl_s3_v5k_producer.py"
CHECKER = REFERENCE / "e4_pl_s3_v6s_stage4b_checker.py"
PROCESS_GUARD = REFERENCE / "e4_pl_s3_v2_bounded_process.py"
WORKER_IDS = (
    "MODAL_10", "MODAL_25", "BUCKLING_10", "BUCKLING_25",
    "PERFORMANCE_0", "PERFORMANCE_10", "PERFORMANCE_25",
)
CANDIDATE = "CANDIDATE_E4_PL_S3_V2D_NATIVE_PARITY_V1"
PASS = "PASS_MEASURED_REGISTERED_SCOPE"
FAIL = "FAIL_MEASURED_CONTRADICTION"
BLOCKED = "BLOCKED_E4_PL_S3_V6S_STAGE4B_PROCESS_OR_EVIDENCE"
NO_GO_EIGEN = "NO_GO_E4_PL_S3_V6S_MIXED_EIGEN"
NO_GO_PERFORMANCE = "NO_GO_E4_PL_S3_V6S_MIXED_PERFORMANCE"
GO = "PROVISIONAL_GO_E4_PL_S3_V6S_STAGE4B_CLOSED_ONLY"
CHILD_TIMEOUT_SECONDS = 600
WAVE_TIMEOUT_SECONDS = 1800
MEMORY_LIMIT_GIB = 24
WORKER_CONCURRENCY = 3
CHECKER_CONCURRENCY = 4
CYCLES = 2
PROOF_SCHEMA = "anysolver.e4-pl-s3-v6s-stage4b-worker-proof-v1"


class V6SStage4BError(RuntimeError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("ascii")


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def _pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    made: dict[str, Any] = {}
    for key, value in items:
        if key in made:
            raise V6SStage4BError(f"duplicate JSON key: {key}")
        made[key] = value
    return made


def load(path: Path) -> tuple[bytes, dict[str, Any]]:
    raw = path.read_bytes()
    value = json.loads(
        raw,
        object_pairs_hook=_pairs,
        parse_constant=lambda token: (_ for _ in ()).throw(V6SStage4BError(f"nonfinite token: {token}")),
    )
    if not isinstance(value, dict) or raw != canonical_bytes(value):
        raise V6SStage4BError(f"noncanonical JSON: {path}")
    return raw, value


def _load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise V6SStage4BError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _git(*arguments: str) -> str:
    process = subprocess.run(["git", *arguments], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if process.returncode:
        raise V6SStage4BError(process.stderr.strip() or "git command failed")
    return process.stdout.strip()


def validate_contract(path: Path = CONTRACT) -> tuple[bytes, dict[str, Any]]:
    raw, value = load(path)
    if value.get("schema") != "anysolver.e4-pl-s3-v6s-stage4b-contract-v1":
        raise V6SStage4BError("unexpected V6S contract schema")
    if value.get("candidate_formulation_id") != CANDIDATE:
        raise V6SStage4BError("V6S candidate identity changed")
    expected_bounds = {
        "automatic_retry": False,
        "checker_concurrency": CHECKER_CONCURRENCY,
        "checker_replicas_per_worker": 2,
        "child_timeout_seconds": CHILD_TIMEOUT_SECONDS,
        "complete_wave_timeout_seconds": WAVE_TIMEOUT_SECONDS,
        "memory_limit_gib_per_process_tree": MEMORY_LIMIT_GIB,
        "numerical_library_threads_per_process": 1,
        "producer_concurrency": WORKER_CONCURRENCY,
        "required_cycle_count": CYCLES,
    }
    if value.get("execution") != expected_bounds or value.get("worker_ids") != list(WORKER_IDS):
        raise V6SStage4BError("V6S execution scope changed")
    for row in value.get("frozen_inputs", []):
        path_value = ROOT / row["path"]
        candidate = path_value.read_bytes()
        if len(candidate) != row["bytes"] or sha256(candidate) != row["sha256"]:
            raise V6SStage4BError(f"frozen input mismatch: {row['path']}")
    return raw, value


def validate_authorization(path: Path, contract_raw: bytes) -> dict[str, Any]:
    _raw, value = load(path)
    if value.get("schema") != "anysolver.e4-pl-s3-v6s-execution-authorization-v1":
        raise V6SStage4BError("unexpected V6S authorization schema")
    if value.get("contract_sha256") != sha256(contract_raw) or value.get("execution_authorized") is not True:
        raise V6SStage4BError("V6S authorization binding differs")
    if value.get("activation_authorized") is not False:
        raise V6SStage4BError("V6S authorization cannot activate S3")
    if _git("rev-parse", "HEAD^") != value.get("authority_commit"):
        raise V6SStage4BError("V6S execution must run from its authorization commit")
    if _git("show", "-s", "--format=%s", "HEAD") != value.get("expected_authorization_subject"):
        raise V6SStage4BError("V6S authorization subject differs")
    return value


def _lane() -> tuple[Any, Any]:
    historical = _load_module(f"_v6s_historical_{time.monotonic_ns()}", HISTORICAL_STAGE4B)
    payload = json.loads(HISTORICAL_INPUT.read_text(encoding="ascii"))
    lane, _runner, authorities = historical._lane_and_model(payload)
    original_build = lane._build_case
    cache: dict[tuple[int, bool], Any] = {}

    def build(authority: Any, fraction: int, *, auxiliary: bool) -> Any:
        key = (int(fraction), bool(auxiliary))
        if key not in cache:
            built = original_build(authority, fraction, auxiliary=auxiliary)
            from anysolver.elements import create_shell_element

            for element_id, kind in built.element_kinds.items():
                if kind != "S3":
                    continue
                old = built.model.mesh.elements[element_id]
                built.model.mesh.elements[element_id] = create_shell_element(
                    int(element_id), list(old.node_ids), str(old.material_name),
                    formulation="e4-pl-s3-v2d",
                    thickness=float(old.thickness),
                    reference_normal=list(old.reference_normal),
                    # V2C predates the explicit polarity field.  Its frozen
                    # builder always selected the positive physical director.
                    director_polarity=int(getattr(old, "director_polarity", 1)),
                )
            cache[key] = built
        return cache[key]

    def states(model: Any, spec: Mapping[str, Any]) -> dict[int, dict[str, Any]]:
        import numpy as np
        from anysolver.e4_pl_element import equation7_frame

        tensor = np.asarray(spec["physical_global_membrane_compression_tensor"], dtype=float)
        result: dict[int, dict[str, Any]] = {}
        for element_id, element in model.mesh.elements.items():
            if getattr(element, "formulation_id", None) == CANDIDATE:
                coordinates = np.asarray([model.mesh.nodes[node_id].coords() for node_id in element.node_ids], dtype=float)
                normal = np.asarray(element.reference_normal, dtype=float)
                signed = float(np.cross(coordinates[1] - coordinates[0], coordinates[2] - coordinates[0]) @ normal)
                if signed < 0.0:
                    coordinates = coordinates[[0, 2, 1]]
                first = coordinates[1] - coordinates[0]
                first /= float(np.linalg.norm(first))
                second = np.cross(normal, first)
                second /= float(np.linalg.norm(second))
                frame = np.column_stack((first, second, normal))
            else:
                frame = np.asarray(equation7_frame(element.get_node_coordinates(model.mesh))[0], dtype=float)
            local = frame[:, :2].T @ tensor @ frame[:, :2]
            membrane = [float(local[0, 0]), float(local[1, 1]), float(local[0, 1])]
            factor = 0.0 if getattr(element, "formulation_id", None) == CANDIDATE else float(element.thickness) ** 2 / 12.0
            result[int(element_id)] = {
                "bending_compression": [0.0, 0.0, 0.0],
                "membrane_compression": membrane,
                "stress_second_moment": [float(value * factor) for value in membrane],
            }
        return result

    lane._build_case = build
    lane._reference_elastic_states = states
    authorities = SimpleNamespace(input=authorities.input, contract=authorities.contract, input_raw=authorities.input_raw)
    return lane, authorities


def produce(worker_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    if worker_id not in WORKER_IDS:
        raise V6SStage4BError(f"unknown worker {worker_id}")
    lane, authorities = _lane()
    repaired = _load_module(f"_v6s_repair_{worker_id.lower()}_{time.monotonic_ns()}", HISTORICAL_REPAIR)
    started = time.perf_counter()
    if worker_id.startswith("MODAL_"):
        fraction = int(worker_id.rsplit("_", 1)[1])
        statuses, raw = lane._modal_worker(authorities, fraction)
        clustered = raw.get("clustered_mac", {})
        payload = {
            "fraction_percent": fraction,
            "frequency_error_max_hex": float(raw.get("maximum_frequency_relative_error", math.inf)).hex(),
            "frequency_gate_passed": statuses.get("modal_frequency") == PASS,
            "mac_gate_passed": statuses.get("modal_mac") == PASS,
            "minimum_clustered_mac_hex": float(clustered.get("minimum_clustered_mac", -math.inf)).hex(),
            "rigid_gate_passed": statuses.get("rigid_modes") == PASS,
        }
        passed = all(payload[key] is True for key in ("frequency_gate_passed", "mac_gate_passed", "rigid_gate_passed"))
        diagnostic = raw
    elif worker_id.startswith("BUCKLING_"):
        fraction = int(worker_id.rsplit("_", 1)[1])
        payload = repaired._spectral(lane, authorities, fraction)
        passed = payload["factor_gate_passed"] and payload["mac_gate_passed"]
        diagnostic = {}
    else:
        fraction = int(worker_id.rsplit("_", 1)[1])
        statuses, raw = lane._performance_worker(authorities, fraction)
        payload = {"fraction_percent": fraction, "measurement_complete": statuses.get("performance_measurement") == PASS}
        passed = payload["measurement_complete"]
        diagnostic = raw
    proof = {
        "activation_authorized": False,
        "candidate_formulation_id": CANDIDATE,
        "gate_status": PASS if passed else FAIL,
        "payload": payload,
        "predecessor_terminal": "PROVISIONAL_GO_E4_PL_S3_V6R_STAGE4B_PREPARATION",
        "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "schema": PROOF_SCHEMA,
        "worker_id": worker_id,
    }
    proof["scientific_payload_sha256"] = sha256(canonical_bytes(proof))
    return proof, {"elapsed_seconds": float(time.perf_counter() - started), "raw": diagnostic, "worker_id": worker_id}


def _environment() -> dict[str, str]:
    environment = dict(os.environ)
    paths = [str(ROOT / "src"), str(REFERENCE)]
    for parent in (ROOT, *ROOT.parents):
        # ANYmesh has concurrent work and is deliberately not added to this
        # scientific process path.  The frozen installed anymesher dependency
        # is import-only in this lane; topology is constructed by the bound
        # historical qualification runner.
        for repository in ("ANYfileIO", "ANYgeometry", "ANYmaterial"):
            candidate = parent / repository / "src"
            if candidate.is_dir():
                paths.append(str(candidate))
    if environment.get("PYTHONPATH"):
        paths.append(environment["PYTHONPATH"])
    environment["PYTHONPATH"] = os.pathsep.join(dict.fromkeys(paths))
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        environment[name] = "1"
    environment["PYTHONHASHSEED"] = "0"
    return environment


def _launch(label: str, command: Sequence[str], directory: Path, timeout: int) -> tuple[str, int, Path]:
    guard = _load_module(f"_v6s_guard_{label.lower().replace('-', '_')}_{time.monotonic_ns()}", PROCESS_GUARD)
    directory.mkdir(parents=True, exist_ok=False)
    job = guard._ProcessJob(MEMORY_LIMIT_GIB * 1024**3)
    with (directory / "stdout.log").open("xb") as stdout, (directory / "stderr.log").open("xb") as stderr:
        try:
            process = job.launch(list(command), cwd=ROOT, env=_environment(), stdout=stdout, stderr=stderr)
            try:
                code = process.wait(timeout=timeout)
                status = "COMPLETE" if code == 0 else "FAILED"
            except subprocess.TimeoutExpired:
                status, code = "TIMEOUT", -9
                if not job.terminate():
                    status = "TERMINATION_FAILED"
        finally:
            job.close()
    return status, int(code), directory


def _jobs(jobs: Sequence[tuple[str, list[str], Path]], maximum: int, deadline: float) -> dict[str, tuple[str, int, Path]]:
    results: dict[str, tuple[str, int, Path]] = {}
    with ThreadPoolExecutor(max_workers=maximum) as pool:
        futures = {}
        for label, command, directory in jobs:
            timeout = min(CHILD_TIMEOUT_SECONDS, max(1, int(deadline - time.monotonic())))
            futures[pool.submit(_launch, label, command, directory, timeout)] = label
        for future in as_completed(futures):
            results[futures[future]] = future.result()
    return results


def _cycle(root: Path, deadline: float) -> tuple[bytes, dict[str, Any]]:
    root.mkdir(parents=True, exist_ok=False)
    producer_jobs = []
    for worker_id in WORKER_IDS:
        directory = root / "workers" / worker_id.lower()
        command = [sys.executable, str(Path(__file__).resolve()), "--worker", worker_id, "--output", str(directory / "proof.json"), "--diagnostic-output", str(directory / "diagnostic.json")]
        producer_jobs.append((worker_id, command, directory))
    producers = _jobs(producer_jobs, WORKER_CONCURRENCY, deadline)
    if any(row[0] != "COMPLETE" for row in producers.values()):
        raise V6SStage4BError("V6S producer process failed")
    checker_jobs = []
    for worker_id in WORKER_IDS:
        proof = producers[worker_id][2] / "proof.json"
        for replica in (1, 2):
            label = f"{worker_id}-{replica}"
            directory = root / "checkers" / worker_id.lower() / str(replica)
            command = [sys.executable, str(CHECKER), "--verify-v6s-proof", "--proof", str(proof), "--output", str(directory / "check.json")]
            checker_jobs.append((label, command, directory))
    checkers = _jobs(checker_jobs, CHECKER_CONCURRENCY, deadline)
    if any(row[0] != "COMPLETE" for row in checkers.values()):
        raise V6SStage4BError("V6S checker process failed")
    proofs = {worker_id: load(producers[worker_id][2] / "proof.json")[1] for worker_id in WORKER_IDS}
    diagnostics = {worker_id: load(producers[worker_id][2] / "diagnostic.json")[1] for worker_id in WORKER_IDS}
    for worker_id in WORKER_IDS:
        first = (checkers[f"{worker_id}-1"][2] / "check.json").read_bytes()
        second = (checkers[f"{worker_id}-2"][2] / "check.json").read_bytes()
        if first != second:
            raise V6SStage4BError(f"V6S checker replicas disagree: {worker_id}")
    modal = all(proofs[worker_id]["gate_status"] == PASS for worker_id in WORKER_IDS[:2])
    buckling = all(proofs[worker_id]["gate_status"] == PASS for worker_id in WORKER_IDS[2:4])
    complete = all(proofs[worker_id]["gate_status"] == PASS for worker_id in WORKER_IDS[4:])
    performance = False
    if complete:
        by_fraction = {int(diagnostics[worker_id]["raw"]["fraction_percent"]): diagnostics[worker_id]["raw"] for worker_id in WORKER_IDS[4:]}
        reference = by_fraction[0]
        checks = []
        for fraction in (10, 25):
            candidate = by_fraction[fraction]
            ratios = (
                candidate["assembly"]["median_seconds"] / reference["assembly"]["median_seconds"],
                candidate["production_end_to_end_solve"]["median_seconds"] / reference["production_end_to_end_solve"]["median_seconds"],
                float(candidate["peak_rss_bytes"]) / float(reference["peak_rss_bytes"]),
            )
            checks.extend(math.isfinite(value) and value <= 1.10 for value in ratios)
        performance = all(checks)
    gates = {"buckling": PASS if buckling else FAIL, "mixed_performance": PASS if performance else FAIL, "modal": PASS if modal else FAIL}
    terminal = NO_GO_EIGEN if not modal or not buckling else NO_GO_PERFORMANCE if not performance else GO
    common = {
        "activation_authorized": False,
        "candidate_formulation_id": CANDIDATE,
        "coverage": {"buckling_factor_count": 5, "buckling_window_modes": 8, "checker_replicas_per_worker": 2, "modal_elastic_modes": 10, "performance_repetitions": 11, "worker_ids": list(WORKER_IDS)},
        "gate_status": gates,
        "next_gate": "V6T_PACKAGING_RESTART_BATCHING_AND_ACTIVATION_GAP_AUDIT" if terminal == GO else None,
        "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "schema": "anysolver.e4-pl-s3-v6s-stage4b-cycle-common-v1",
        "terminal": terminal,
    }
    raw = canonical_bytes(common)
    with (root / "common.json").open("xb") as stream:
        stream.write(raw)
    return raw, common


def run(authorization: Path, output: Path) -> dict[str, Any]:
    contract_raw, _contract = validate_contract()
    validate_authorization(authorization, contract_raw)
    if output.exists():
        raise V6SStage4BError("exclusive V6S output root exists")
    output.mkdir(parents=True)
    deadline = time.monotonic() + WAVE_TIMEOUT_SECONDS
    raws: list[bytes] = []
    cycles: list[dict[str, Any]] = []
    try:
        for cycle in (1, 2):
            raw, value = _cycle(output / f"cycle-{cycle}", deadline)
            raws.append(raw)
            cycles.append(value)
        identical = len(raws) == 2 and raws[0] == raws[1]
        terminal = cycles[0]["terminal"] if identical and cycles[0]["terminal"] == cycles[1]["terminal"] else BLOCKED
        error = None
    except Exception as exc:
        identical, terminal, error = False, BLOCKED, f"{type(exc).__name__}: {exc}"
        (output / "failure.txt").write_text(error + "\n", encoding="utf-8")
    result = {
        "activation_authorized": False,
        "authorization_sha256": sha256(authorization.read_bytes()),
        "candidate_formulation_id": CANDIDATE,
        "common_sha256": sha256(raws[0]) if raws else None,
        "cycles_byte_identical": identical,
        "error": error,
        "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "schema": "anysolver.e4-pl-s3-v6s-stage4b-aggregate-v1",
        "terminal": terminal,
    }
    with (output / "aggregate.json").open("xb") as stream:
        stream.write(canonical_bytes(result))
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--worker", choices=WORKER_IDS)
    mode.add_argument("--run-v6s", action="store_true")
    parser.add_argument("--authorization", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--diagnostic-output", type=Path)
    args = parser.parse_args(argv)
    if args.worker:
        if args.authorization is not None or args.diagnostic_output is None:
            raise V6SStage4BError("V6S worker arguments differ")
        validate_contract()
        proof, diagnostic = produce(args.worker)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("xb") as stream:
            stream.write(canonical_bytes(proof))
        with args.diagnostic_output.open("xb") as stream:
            stream.write(canonical_bytes(diagnostic))
        return 0
    if args.authorization is None or args.diagnostic_output is not None:
        raise V6SStage4BError("V6S coordinator arguments differ")
    result = run(args.authorization, args.output)
    print(canonical_bytes(result).decode("ascii"), end="")
    return 0 if result["terminal"] != BLOCKED else 2


if __name__ == "__main__":
    raise SystemExit(main())
