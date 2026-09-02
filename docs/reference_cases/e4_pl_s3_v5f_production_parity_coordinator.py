"""Bounded two-cycle coordinator for the S3 V5F production parity gate."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Mapping, Sequence

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

import e4_pl_s3_v2_bounded_process as process_guard


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "docs/reference_cases"
PRODUCER = REFERENCE / "e4_pl_s3_v5f_production_parity_producer.py"
CHECKER = REFERENCE / "e4_pl_s3_v5f_production_parity_checker.py"
CONTRACT = REFERENCE / "e4_pl_s3_v5f_production_parity_contract.json"
SCHEMA = "anysolver.e4-pl-s3-v5f-production-parity-aggregate-v1"
BLOCKED = "BLOCKED_E4_PL_S3_V5F_PRODUCTION_PARITY_PROCESS_OR_EVIDENCE"
NO_GO = "NO_GO_E4_PL_S3_V5F_PRODUCTION_PARITY"
PASS = "PROVISIONAL_GO_E4_PL_S3_V5F_STAGE4B_EXECUTION_PREPARATION"
CHILD_TIMEOUT_SECONDS = 600
WAVE_TIMEOUT_SECONDS = 1800
MEMORY_LIMIT_GIB = 24
WORKERS = 3
CHECKER_REPLICAS = 2
CYCLES = 2


class CoordinatorError(RuntimeError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("ascii")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def load_canonical(path: Path) -> Any:
    raw = path.read_bytes()
    value = json.loads(raw)
    if canonical_bytes(value) != raw:
        raise CoordinatorError(f"noncanonical JSON: {path}")
    return value


def exclusive_write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(canonical_bytes(value))


def _environment() -> dict[str, str]:
    env = dict(os.environ)
    paths = [str(ROOT / "src"), str(REFERENCE)]
    for parent in (ROOT, *ROOT.parents):
        for repository in ("ANYfileIO", "ANYgeometry", "ANYmaterial", "ANYmesh"):
            candidate = parent / repository / "src"
            if candidate.is_dir():
                paths.append(str(candidate))
    existing = env.get("PYTHONPATH")
    if existing:
        paths.append(existing)
    env["PYTHONPATH"] = os.pathsep.join(dict.fromkeys(paths))
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        env[name] = "1"
    return env


def _run(command: list[str], *, timeout: int) -> None:
    job = process_guard._ProcessJob(MEMORY_LIMIT_GIB * 1024**3)
    try:
        process = job.launch(
            command,
            cwd=ROOT,
            env=_environment(),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            return_code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            if not job.terminate():
                raise CoordinatorError("timed-out child process tree did not terminate") from exc
            raise CoordinatorError(f"child exceeded {timeout} seconds: {command[1]}") from exc
        if return_code != 0:
            raise CoordinatorError(f"child failed with status {return_code}: {command[1]}")
    finally:
        job.close()


def _cycle(root: Path, cycle: int, deadline: float) -> dict[str, Any]:
    cycle_root = root / f"cycle-{cycle}"
    cycle_root.mkdir(parents=True, exist_ok=False)
    proof = cycle_root / "proof.json"
    progress = cycle_root / "progress.jsonl"
    remaining = min(CHILD_TIMEOUT_SECONDS, max(1, int(deadline - time.monotonic())))
    _run([sys.executable, str(PRODUCER), "--emit-production-parity-proof", "--output", str(proof), "--progress", str(progress)], timeout=remaining)
    checker_paths = [cycle_root / f"checker-{replica}.json" for replica in (1, 2)]

    def verify(path: Path) -> None:
        remaining_checker = min(CHILD_TIMEOUT_SECONDS, max(1, int(deadline - time.monotonic())))
        _run([sys.executable, str(CHECKER), "--verify-production-parity-proof", "--proof", str(proof), "--output", str(path)], timeout=remaining_checker)

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(verify, path) for path in checker_paths]
        for future in futures:
            future.result()
    if checker_paths[0].read_bytes() != checker_paths[1].read_bytes():
        raise CoordinatorError("checker replicas disagree")
    checked = load_canonical(checker_paths[0])
    return {
        "case_count": checked["case_count"],
        "catalog_record_count": checked["catalog_record_count"],
        "checker_replicas_byte_identical": True,
        "checker_sha256": sha256_file(checker_paths[0]),
        "passed": checked["passed"],
        "proof_sha256": sha256_file(proof),
        "scientific_payload_sha256": checked["scientific_payload_sha256"],
    }


def adjudicate(cycles: Sequence[Mapping[str, Any]], *, process_complete: bool = True) -> str:
    if not process_complete or len(cycles) != CYCLES:
        return BLOCKED
    if any(cycle.get("checker_replicas_byte_identical") is not True for cycle in cycles):
        return BLOCKED
    if cycles[0].get("scientific_payload_sha256") != cycles[1].get("scientific_payload_sha256"):
        return BLOCKED
    if any(cycle.get("passed") is not True for cycle in cycles):
        return NO_GO
    return PASS


def run_bounded(output_root: Path) -> dict[str, Any]:
    if output_root.exists():
        raise CoordinatorError("exclusive output root already exists")
    output_root.mkdir(parents=True)
    deadline = time.monotonic() + WAVE_TIMEOUT_SECONDS
    cycles: list[dict[str, Any]] = []
    process_complete = True
    error: str | None = None
    try:
        for cycle in range(1, CYCLES + 1):
            cycles.append(_cycle(output_root, cycle, deadline))
    except (CoordinatorError, OSError, subprocess.SubprocessError, TimeoutError) as exc:
        process_complete = False
        error = f"{type(exc).__name__}:{exc}"
    terminal = adjudicate(cycles, process_complete=process_complete)
    aggregate = {
        "activation_authorized": False,
        "candidate_formulation_id": "CANDIDATE_E4_PL_S3_V2B_FLAT_LINEAR_V1",
        "contract_sha256": sha256_file(CONTRACT),
        "cycles": cycles,
        "error": error,
        "execution_bounds": {
            "checker_replicas": CHECKER_REPLICAS,
            "child_timeout_seconds": CHILD_TIMEOUT_SECONDS,
            "cycles": CYCLES,
            "memory_limit_gib_per_process_tree": MEMORY_LIMIT_GIB,
            "no_automatic_retry": True,
            "wave_timeout_seconds": WAVE_TIMEOUT_SECONDS,
            "workers": WORKERS,
        },
        "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "schema": SCHEMA,
        "stage4b_execution_authorized": False,
        "stage4b_preparation_authorized": terminal == PASS,
        "terminal": terminal,
    }
    exclusive_write(output_root / "aggregate.json", aggregate)
    return aggregate


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-production-parity", action="store_true", required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args(argv)
    made = run_bounded(args.output_root)
    return 0 if made["terminal"] == PASS else 2


if __name__ == "__main__":
    raise SystemExit(main())
