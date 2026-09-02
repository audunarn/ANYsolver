"""Bounded two-cycle coordinator for the S3 V5H local-parity gate."""

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
PRODUCER = REFERENCE / "e4_pl_s3_v5h_local_parity_producer.py"
CHECKER = REFERENCE / "e4_pl_s3_v5h_local_parity_checker.py"
CONTRACT = REFERENCE / "e4_pl_s3_v5h_local_parity_contract.json"
SCHEMA = "anysolver.e4-pl-s3-v5h-local-parity-aggregate-v1"
BLOCKED = "BLOCKED_E4_PL_S3_V5H_PROCESS_OR_EVIDENCE"
NO_GO = "NO_GO_E4_PL_S3_V5H_EXTENSION_PARITY"
PASS = "PROVISIONAL_GO_E4_PL_S3_V5H_STAGE4B_PROTOCOL_PREPARATION"
CHILD_TIMEOUT_SECONDS = 600
WAVE_TIMEOUT_SECONDS = 1800
MEMORY_LIMIT_GIB = 24
CYCLES = 2
CHECKER_REPLICAS = 2


class CoordinatorError(RuntimeError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
        + "\n"
    ).encode("ascii")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    made: dict[str, Any] = {}
    for key, value in items:
        if key in made:
            raise CoordinatorError(f"duplicate JSON key: {key}")
        made[key] = value
    return made


def load_canonical(path: Path) -> Any:
    raw = path.read_bytes()
    value = json.loads(
        raw,
        object_pairs_hook=_pairs,
        parse_constant=lambda token: (_ for _ in ()).throw(
            CoordinatorError(f"nonfinite JSON token: {token}")
        ),
    )
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
    if env.get("PYTHONPATH"):
        paths.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(dict.fromkeys(paths))
    for name in (
        "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "MKL_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
    ):
        env[name] = "1"
    return env


def _run(command: list[str], *, timeout: int, log: Path) -> None:
    job = process_guard._ProcessJob(MEMORY_LIMIT_GIB * 1024**3)
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("xb") as stream:
        try:
            process = job.launch(
                command,
                cwd=ROOT,
                env=_environment(),
                stdout=stream,
                stderr=subprocess.STDOUT,
            )
            try:
                return_code = process.wait(timeout=timeout)
            except subprocess.TimeoutExpired as exc:
                if not job.terminate():
                    raise CoordinatorError(
                        "timed-out child process tree did not terminate"
                    ) from exc
                raise CoordinatorError(
                    f"child exceeded {timeout} seconds: {command[1]}"
                ) from exc
            if return_code != 0:
                raise CoordinatorError(
                    f"child failed with status {return_code}: {command[1]}"
                )
        finally:
            job.close()


def _cycle(root: Path, cycle: int, deadline: float) -> dict[str, Any]:
    cycle_root = root / f"cycle-{cycle}"
    cycle_root.mkdir(parents=True, exist_ok=False)
    proof = cycle_root / "proof.json"
    progress = cycle_root / "progress.jsonl"
    remaining = min(CHILD_TIMEOUT_SECONDS, max(1, int(deadline - time.monotonic())))
    _run(
        [
            sys.executable,
            str(PRODUCER),
            "--emit-v5h-local-parity-proof",
            "--output",
            str(proof),
            "--progress",
            str(progress),
        ],
        timeout=remaining,
        log=cycle_root / "producer.log",
    )
    checker_paths = [cycle_root / f"checker-{replica}.json" for replica in (1, 2)]

    def verify(replica: int, path: Path) -> None:
        remaining_checker = min(
            CHILD_TIMEOUT_SECONDS,
            max(1, int(deadline - time.monotonic())),
        )
        _run(
            [
                sys.executable,
                str(CHECKER),
                "--verify-v5h-local-parity-proof",
                "--proof",
                str(proof),
                "--output",
                str(path),
            ],
            timeout=remaining_checker,
            log=cycle_root / f"checker-{replica}.log",
        )

    with ThreadPoolExecutor(max_workers=CHECKER_REPLICAS) as pool:
        futures = [
            pool.submit(verify, replica, path)
            for replica, path in zip((1, 2), checker_paths)
        ]
        for future in futures:
            future.result()
    if checker_paths[0].read_bytes() != checker_paths[1].read_bytes():
        raise CoordinatorError("checker replicas disagree")
    checked = load_canonical(checker_paths[0])
    return {
        "case_count": checked["case_count"],
        "checker_replicas_byte_identical": True,
        "checker_sha256": sha256_file(checker_paths[0]),
        "passed": checked["passed"],
        "proof_sha256": sha256_file(proof),
        "scientific_payload_sha256": checked["scientific_payload_sha256"],
        "worst": {
            name: checked[name]
            for name in (
                "buckling_worst_hex",
                "component_worst_hex",
                "geometric_worst_hex",
                "mass_worst_hex",
                "modal_worst_hex",
                "pressure_worst_hex",
                "work_worst_hex",
            )
        },
    }


def adjudicate(
    cycles: Sequence[Mapping[str, Any]],
    *,
    process_complete: bool = True,
) -> str:
    if not process_complete or len(cycles) != CYCLES:
        return BLOCKED
    if any(
        cycle.get("checker_replicas_byte_identical") is not True for cycle in cycles
    ):
        return BLOCKED
    if cycles[0].get("scientific_payload_sha256") != cycles[1].get(
        "scientific_payload_sha256"
    ):
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
        "candidate_formulation_id": (
            "CANDIDATE_E4_PL_S3_V2C_FLAT_LINEAR_PARITY_V1"
        ),
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
            "workers": 2,
        },
        "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "schema": SCHEMA,
        "stage4b_execution_authorized": False,
        "stage4b_protocol_preparation_authorized": terminal == PASS,
        "terminal": terminal,
    }
    exclusive_write(output_root / "aggregate.json", aggregate)
    return aggregate


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-v5h-local-parity", action="store_true", required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args(argv)
    made = run_bounded(args.output_root)
    return 0 if made["terminal"] == PASS else 2


if __name__ == "__main__":
    raise SystemExit(main())
