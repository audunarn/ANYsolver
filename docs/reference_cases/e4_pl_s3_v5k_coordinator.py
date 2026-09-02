"""Run two bounded V5K repair-gate cycles and adjudicate canonical evidence."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "docs/reference_cases"
PRODUCER = REFERENCE / "e4_pl_s3_v5k_producer.py"
CHECKER = REFERENCE / "e4_pl_s3_v5k_checker.py"
PROCESS_GUARD = REFERENCE / "e4_pl_s3_v2_bounded_process.py"
WORKER_IDS = (
    "SPECTRAL_10", "SPECTRAL_25", "ASSEMBLY_10", "ASSEMBLY_25",
    "PERFORMANCE_0", "PERFORMANCE_10", "PERFORMANCE_25",
)
PASS = "PASS_MEASURED_REGISTERED_SCOPE"
BLOCKED = "BLOCKED_E4_PL_S3_V5K_PROCESS_OR_EVIDENCE"
NO_GO_SPECTRAL = "NO_GO_E4_PL_S3_V5K_SPECTRAL_RULE"
NO_GO_IDENTITY = "NO_GO_E4_PL_S3_V5K_FAST_ASSEMBLY_IDENTITY"
NO_GO_PERFORMANCE = "NO_GO_E4_PL_S3_V5K_MIXED_PERFORMANCE"
GO = "PROVISIONAL_GO_E4_PL_S3_V5K_STAGE4B_RERUN"
CHILD_TIMEOUT_SECONDS = 600
WAVE_TIMEOUT_SECONDS = 1800
MEMORY_LIMIT_GIB = 24
WORKER_CONCURRENCY = 3
CHECKER_CONCURRENCY = 4
CYCLES = 2


class V5KCoordinatorError(RuntimeError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("ascii")


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def _pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    made: dict[str, Any] = {}
    for key, value in items:
        if key in made:
            raise V5KCoordinatorError(f"duplicate JSON key: {key}")
        made[key] = value
    return made


def load(path: Path) -> tuple[bytes, dict[str, Any]]:
    raw = path.read_bytes()
    value = json.loads(raw, object_pairs_hook=_pairs, parse_constant=lambda token: (_ for _ in ()).throw(V5KCoordinatorError(f"nonfinite token: {token}")))
    if not isinstance(value, dict) or raw != canonical_bytes(value):
        raise V5KCoordinatorError(f"noncanonical JSON: {path}")
    return raw, value


def _git(*arguments: str) -> str:
    process = subprocess.run(["git", *arguments], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if process.returncode:
        raise V5KCoordinatorError(process.stderr.strip() or "git command failed")
    return process.stdout.strip()


def validate_authorization(path: Path) -> dict[str, Any]:
    _raw, value = load(path)
    if value.get("schema") != "anysolver.e4-pl-s3-v5k-execution-authorization-v1":
        raise V5KCoordinatorError("unexpected execution authorization schema")
    if _git("rev-parse", "HEAD^") != value.get("implementation_commit") or _git("show", "-s", "--format=%s", "HEAD") != value.get("expected_authorization_subject"):
        raise V5KCoordinatorError("execution authorization topology changed")
    for row in value.get("frozen_inputs", []):
        raw = (ROOT / row["path"]).read_bytes()
        if len(raw) != row["bytes"] or sha256(raw) != row["sha256"]:
            raise V5KCoordinatorError(f"frozen input mismatch: {row['path']}")
    return value


def _load_guard() -> Any:
    spec = importlib.util.spec_from_file_location("_v5k_process_guard", PROCESS_GUARD)
    if spec is None or spec.loader is None:
        raise V5KCoordinatorError("cannot load bounded process guard")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _environment() -> dict[str, str]:
    environment = dict(os.environ)
    paths = [str(ROOT / "src"), str(REFERENCE)]
    for parent in (ROOT, *ROOT.parents):
        for repository in ("ANYfileIO", "ANYgeometry", "ANYmaterial", "ANYmesh"):
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
    guard = _load_guard()
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


def _cycle(root: Path, deadline: float) -> tuple[bytes, dict[str, Any]]:
    root.mkdir(parents=True, exist_ok=False)
    producer_results: dict[str, tuple[str, int, Path]] = {}
    with ThreadPoolExecutor(max_workers=WORKER_CONCURRENCY) as pool:
        futures = {}
        for worker_id in WORKER_IDS:
            directory = root / "workers" / worker_id.lower()
            command = [sys.executable, str(PRODUCER), "--worker", worker_id, "--output", str(directory / "proof.json"), "--diagnostic-output", str(directory / "diagnostic.json")]
            timeout = min(CHILD_TIMEOUT_SECONDS, max(1, int(deadline - time.monotonic())))
            futures[pool.submit(_launch, worker_id, command, directory, timeout)] = worker_id
        for future in as_completed(futures):
            producer_results[futures[future]] = future.result()
    if any(result[0] != "COMPLETE" for result in producer_results.values()):
        raise V5KCoordinatorError("producer process failure")

    checker_jobs = []
    for worker_id in WORKER_IDS:
        proof = producer_results[worker_id][2] / "proof.json"
        for replica in (1, 2):
            directory = root / "checkers" / worker_id.lower() / str(replica)
            command = [sys.executable, str(CHECKER), "--verify-proof", "--proof", str(proof), "--output", str(directory / "check.json")]
            checker_jobs.append((worker_id, replica, directory, command))
    checker_results: dict[tuple[str, int], tuple[str, int, Path]] = {}
    with ThreadPoolExecutor(max_workers=CHECKER_CONCURRENCY) as pool:
        futures = {}
        for worker_id, replica, directory, command in checker_jobs:
            timeout = min(CHILD_TIMEOUT_SECONDS, max(1, int(deadline - time.monotonic())))
            futures[pool.submit(_launch, f"{worker_id}-{replica}", command, directory, timeout)] = (worker_id, replica)
        for future in as_completed(futures):
            checker_results[futures[future]] = future.result()
    if any(result[0] != "COMPLETE" for result in checker_results.values()):
        raise V5KCoordinatorError("checker process failure")

    proofs = {worker_id: load(producer_results[worker_id][2] / "proof.json")[1] for worker_id in WORKER_IDS}
    diagnostics = {worker_id: load(producer_results[worker_id][2] / "diagnostic.json")[1] for worker_id in WORKER_IDS}
    for worker_id in WORKER_IDS:
        first = (checker_results[(worker_id, 1)][2] / "check.json").read_bytes()
        second = (checker_results[(worker_id, 2)][2] / "check.json").read_bytes()
        if first != second:
            raise V5KCoordinatorError(f"checker replicas disagree: {worker_id}")

    spectral = all(proofs[worker_id]["gate_status"] == PASS for worker_id in WORKER_IDS[:2])
    assembly = all(proofs[worker_id]["gate_status"] == PASS for worker_id in WORKER_IDS[2:4])
    performance_complete = all(proofs[worker_id]["gate_status"] == PASS for worker_id in WORKER_IDS[4:])
    performance = False
    if performance_complete:
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
    gates = {"fast_assembly_identity": PASS if assembly else "FAIL_MEASURED_CONTRADICTION", "mixed_performance": PASS if performance else "FAIL_MEASURED_CONTRADICTION", "spectral_rule": PASS if spectral else "FAIL_MEASURED_CONTRADICTION"}
    terminal = NO_GO_SPECTRAL if not spectral else NO_GO_IDENTITY if not assembly else NO_GO_PERFORMANCE if not performance else GO
    common = {
        "activation_authorized": False,
        "candidate_formulation_id": "CANDIDATE_E4_PL_S3_V2C_FLAT_LINEAR_PARITY_V1",
        "coverage": {"checker_replicas_per_worker": 2, "cycles": 2, "fractions_percent": [0, 10, 25], "performance_repetitions": 11, "spectral_window_modes": 8, "worker_ids": list(WORKER_IDS)},
        "gate_status": gates,
        "next_gate": "V5I_STAGE4B_SUCCESSOR_RERUN" if terminal == GO else None,
        "predecessor_terminal_preserved": "NO_GO_E4_PL_S3_V5I_MIXED_EIGEN",
        "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "schema": "anysolver.e4-pl-s3-v5k-cycle-common-v1",
        "terminal": terminal,
    }
    raw = canonical_bytes(common)
    with (root / "common.json").open("xb") as stream:
        stream.write(raw)
    return raw, common


def run(authorization: Path, output: Path) -> dict[str, Any]:
    auth = validate_authorization(authorization)
    if output.exists():
        raise V5KCoordinatorError("exclusive output root already exists")
    output.mkdir(parents=True)
    deadline = time.monotonic() + WAVE_TIMEOUT_SECONDS
    raws, cycles = [], []
    try:
        for cycle in (1, 2):
            raw, value = _cycle(output / f"cycle-{cycle}", deadline)
            raws.append(raw)
            cycles.append(value)
        identical = raws[0] == raws[1]
        terminal = cycles[0]["terminal"] if identical and cycles[0]["terminal"] == cycles[1]["terminal"] else BLOCKED
    except Exception as error:
        identical = False
        terminal = BLOCKED
        cycles = []
        (output / "failure.txt").write_text(f"{type(error).__name__}: {error}\n", encoding="utf-8")
    aggregate = {
        "activation_authorized": False,
        "authorization_sha256": sha256(authorization.read_bytes()),
        "cycles_byte_identical": identical,
        "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "schema": "anysolver.e4-pl-s3-v5k-aggregate-v1",
        "terminal": terminal,
    }
    with (output / "aggregate.json").open("xb") as stream:
        stream.write(canonical_bytes(aggregate))
    return aggregate


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-v5k", action="store_true", required=True)
    parser.add_argument("--authorization", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    result = run(args.authorization, args.output)
    print(canonical_bytes(result).decode("ascii"), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
