"""Bounded two-cycle coordinator for the V5I-R1 diagnosis."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "docs/reference_cases"
PRODUCER = REFERENCE / "e4_pl_s3_v5i_r1_diagnosis_producer.py"
CHECKER = REFERENCE / "e4_pl_s3_v5i_r1_diagnosis_checker.py"
CONTRACT = REFERENCE / "e4_pl_s3_v5i_r1_diagnosis_contract.json"
PROCESS_GUARD = REFERENCE / "e4_pl_s3_v2_bounded_process.py"
SCHEMA = "anysolver.e4-pl-s3-v5i-r1-diagnosis-aggregate-v1"
BLOCKED = "BLOCKED_E4_PL_S3_V5I_R1_PROCESS_OR_EVIDENCE"
GENUINE = "NO_GO_E4_PL_S3_V5I_R1_GENUINE_BUCKLING_SHAPE"
INCOMPLETE = "UNCLASSIFIED_E4_PL_S3_V5I_R1_DIAGNOSIS_INCOMPLETE"
PASS = "DIAGNOSED_E4_PL_S3_V5I_R1_PAIR_SUBSPACE_AND_ASSEMBLY_ROUTE_GAP"
CHILD_TIMEOUT_SECONDS = 600
WAVE_TIMEOUT_SECONDS = 1800
MEMORY_LIMIT_GIB = 24
CYCLES = 2
CHECKER_REPLICAS = 2


class DiagnosisCoordinatorError(RuntimeError):
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
            raise DiagnosisCoordinatorError(f"duplicate JSON key: {key}")
        made[key] = value
    return made


def load_canonical(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    value = json.loads(
        raw,
        object_pairs_hook=_pairs,
        parse_constant=lambda token: (_ for _ in ()).throw(
            DiagnosisCoordinatorError(f"nonfinite JSON token: {token}")
        ),
    )
    if not isinstance(value, dict) or raw != canonical_bytes(value):
        raise DiagnosisCoordinatorError(f"noncanonical JSON: {path}")
    return value


def exclusive_write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(canonical_bytes(value))


def _load_guard() -> Any:
    spec = importlib.util.spec_from_file_location("_v5i_r1_process_guard", PROCESS_GUARD)
    if spec is None or spec.loader is None:
        raise DiagnosisCoordinatorError("cannot load process guard")
    module = importlib.util.module_from_spec(spec)
    sys.modules["_v5i_r1_process_guard"] = module
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


def _run(command: Sequence[str], *, log: Path, timeout: int) -> None:
    guard = _load_guard()
    job = guard._ProcessJob(MEMORY_LIMIT_GIB * 1024**3)
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("xb") as stream:
        try:
            process = job.launch(
                list(command), cwd=ROOT, env=_environment(),
                stdout=stream, stderr=subprocess.STDOUT,
            )
            try:
                return_code = process.wait(timeout=timeout)
            except subprocess.TimeoutExpired as exc:
                if not job.terminate():
                    raise DiagnosisCoordinatorError("timed-out process tree did not terminate") from exc
                raise DiagnosisCoordinatorError("diagnosis child timed out") from exc
            if return_code != 0:
                raise DiagnosisCoordinatorError(f"diagnosis child returned {return_code}")
        finally:
            job.close()


def _cycle(root: Path, cycle: int, deadline: float) -> dict[str, Any]:
    cycle_root = root / f"cycle-{cycle}"
    cycle_root.mkdir(parents=True, exist_ok=False)
    proof = cycle_root / "proof.json"
    remaining = min(CHILD_TIMEOUT_SECONDS, max(1, int(deadline - time.monotonic())))
    _run(
        [sys.executable, str(PRODUCER), "--emit-v5i-r1-diagnosis", "--output", str(proof)],
        log=cycle_root / "producer.log", timeout=remaining,
    )
    checks = [cycle_root / f"checker-{replica}.json" for replica in (1, 2)]

    def check(replica: int, output: Path) -> None:
        remaining_checker = min(CHILD_TIMEOUT_SECONDS, max(1, int(deadline - time.monotonic())))
        _run(
            [sys.executable, str(CHECKER), "--verify-v5i-r1-diagnosis", "--proof", str(proof), "--output", str(output)],
            log=cycle_root / f"checker-{replica}.log", timeout=remaining_checker,
        )

    with ThreadPoolExecutor(max_workers=CHECKER_REPLICAS) as pool:
        futures = [pool.submit(check, replica, output) for replica, output in zip((1, 2), checks)]
        for future in futures:
            future.result()
    if checks[0].read_bytes() != checks[1].read_bytes():
        raise DiagnosisCoordinatorError("checker replicas disagree")
    checked = load_canonical(checks[0])
    return {
        "checker_replicas_byte_identical": True,
        "checker_sha256": sha256_file(checks[0]),
        "cycle": cycle,
        "passed": checked["passed"],
        "proof_sha256": sha256_file(proof),
        "scientific_payload_sha256": checked["scientific_payload_sha256"],
        "terminal": checked["terminal"],
    }


def adjudicate(cycles: Sequence[Mapping[str, Any]], *, process_complete: bool = True) -> str:
    if not process_complete or len(cycles) != CYCLES:
        return BLOCKED
    if any(cycle.get("checker_replicas_byte_identical") is not True for cycle in cycles):
        return BLOCKED
    if cycles[0].get("scientific_payload_sha256") != cycles[1].get("scientific_payload_sha256"):
        return BLOCKED
    terminals = [cycle.get("terminal") for cycle in cycles]
    if GENUINE in terminals:
        return GENUINE
    if INCOMPLETE in terminals:
        return INCOMPLETE
    return PASS if terminals == [PASS, PASS] else BLOCKED


def run_bounded(output_root: Path) -> dict[str, Any]:
    if output_root.exists():
        raise DiagnosisCoordinatorError("exclusive output root already exists")
    output_root.mkdir(parents=True)
    deadline = time.monotonic() + WAVE_TIMEOUT_SECONDS
    cycles: list[dict[str, Any]] = []
    error: str | None = None
    try:
        for cycle in (1, 2):
            cycles.append(_cycle(output_root, cycle, deadline))
    except (DiagnosisCoordinatorError, OSError, subprocess.SubprocessError, TimeoutError) as exc:
        error = f"{type(exc).__name__}:{exc}"
    terminal = adjudicate(cycles, process_complete=error is None)
    aggregate = {
        "activation_authorized": False,
        "candidate_formulation_id": "CANDIDATE_E4_PL_S3_V2C_FLAT_LINEAR_PARITY_V1",
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
        },
        "next_gate": "V5K_INVARIANT_SUBSPACE_AUTHORITY_AND_V2C_FAST_ASSEMBLY" if terminal == PASS else None,
        "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "schema": SCHEMA,
        "terminal": terminal,
    }
    exclusive_write(output_root / "aggregate.json", aggregate)
    return aggregate


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-v5i-r1-diagnosis", action="store_true", required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args(argv)
    result = run_bounded(args.output_root)
    return 0 if result["terminal"] == PASS else 2


if __name__ == "__main__":
    raise SystemExit(main())
