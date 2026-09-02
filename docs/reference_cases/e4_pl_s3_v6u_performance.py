"""Bounded V6U performance-only Stage 4B successor."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Sequence


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "docs/reference_cases"
CONTRACT = REFERENCE / "e4_pl_s3_v6u_performance_contract.json"
V6S = REFERENCE / "e4_pl_s3_v6s_stage4b.py"
CHECKER = REFERENCE / "e4_pl_s3_v6u_performance_checker.py"
WORKER_IDS = ("PERFORMANCE_0", "PERFORMANCE_10", "PERFORMANCE_25")
CANDIDATE = "CANDIDATE_E4_PL_S3_V2D_NATIVE_PARITY_V1"
PASS = "PASS_MEASURED_REGISTERED_SCOPE"
FAIL = "FAIL_MEASURED_CONTRADICTION"
BLOCKED = "BLOCKED_E4_PL_S3_V6U_PERFORMANCE_PROCESS_OR_EVIDENCE"
NO_GO = "NO_GO_E4_PL_S3_V6U_MIXED_PERFORMANCE"
GO = "PROVISIONAL_GO_E4_PL_S3_V6U_STAGE4B_CLOSED_ONLY"
CHILD_TIMEOUT_SECONDS = 600
WAVE_TIMEOUT_SECONDS = 1800
MEMORY_LIMIT_GIB = 24
PRODUCER_CONCURRENCY = 3
CHECKER_CONCURRENCY = 4
CYCLES = 2


class V6UError(RuntimeError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("ascii")


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def _pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    made: dict[str, Any] = {}
    for key, value in items:
        if key in made:
            raise V6UError(f"duplicate key: {key}")
        made[key] = value
    return made


def load(path: Path) -> tuple[bytes, dict[str, Any]]:
    raw = path.read_bytes()
    value = json.loads(
        raw,
        object_pairs_hook=_pairs,
        parse_constant=lambda token: (_ for _ in ()).throw(V6UError(f"nonfinite token: {token}")),
    )
    if not isinstance(value, dict) or raw != canonical_bytes(value):
        raise V6UError(f"noncanonical JSON: {path}")
    return raw, value


def _module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise V6UError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _git(*arguments: str) -> str:
    process = subprocess.run(["git", *arguments], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if process.returncode:
        raise V6UError(process.stderr.strip() or "git command failed")
    return process.stdout.strip()


def validate_contract() -> tuple[bytes, dict[str, Any]]:
    raw, value = load(CONTRACT)
    if value.get("schema") != "anysolver.e4-pl-s3-v6u-performance-contract-v1":
        raise V6UError("V6U contract schema differs")
    expected = {
        "automatic_retry": False,
        "checker_concurrency": CHECKER_CONCURRENCY,
        "checker_replicas_per_worker": 2,
        "child_timeout_seconds": CHILD_TIMEOUT_SECONDS,
        "complete_wave_timeout_seconds": WAVE_TIMEOUT_SECONDS,
        "memory_limit_gib_per_process_tree": MEMORY_LIMIT_GIB,
        "numerical_library_threads_per_process": 1,
        "producer_concurrency": PRODUCER_CONCURRENCY,
        "required_cycle_count": CYCLES,
    }
    if value.get("execution") != expected or value.get("worker_ids") != list(WORKER_IDS):
        raise V6UError("V6U execution scope differs")
    for row in value.get("frozen_inputs", []):
        candidate = (ROOT / row["path"]).read_bytes()
        if len(candidate) != row["bytes"] or sha256(candidate) != row["sha256"]:
            raise V6UError(f"frozen input differs: {row['path']}")
    return raw, value


def validate_authorization(path: Path, contract_raw: bytes) -> None:
    _raw, value = load(path)
    if value.get("schema") != "anysolver.e4-pl-s3-v6u-execution-authorization-v1":
        raise V6UError("V6U authorization schema differs")
    if value.get("contract_sha256") != sha256(contract_raw) or value.get("execution_authorized") is not True:
        raise V6UError("V6U authorization binding differs")
    if value.get("activation_authorized") is not False:
        raise V6UError("V6U cannot activate S3")
    if _git("rev-parse", "HEAD^") != value.get("authority_commit"):
        raise V6UError("V6U authorization topology differs")
    if _git("show", "-s", "--format=%s", "HEAD") != value.get("expected_authorization_subject"):
        raise V6UError("V6U authorization subject differs")


def produce(worker_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    if worker_id not in WORKER_IDS:
        raise V6UError("unknown V6U worker")
    base = _module(f"_v6u_base_{worker_id.lower()}_{time.monotonic_ns()}", V6S)
    lane, authorities = base._lane()
    fraction = int(worker_id.rsplit("_", 1)[1])
    started = time.perf_counter()
    statuses, diagnostic = lane._performance_worker(authorities, fraction)
    complete = statuses.get("performance_measurement") == PASS
    proof = {
        "activation_authorized": False,
        "candidate_formulation_id": CANDIDATE,
        "gate_status": PASS if complete else FAIL,
        "payload": {"fraction_percent": fraction, "measurement_complete": complete},
        "predecessor_terminal": "PROVISIONAL_GO_E4_PL_S3_V6T_PERFORMANCE_SUCCESSOR",
        "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "schema": "anysolver.e4-pl-s3-v6u-performance-proof-v1",
        "worker_id": worker_id,
    }
    proof["scientific_payload_sha256"] = sha256(canonical_bytes(proof))
    return proof, {"elapsed_seconds": time.perf_counter() - started, "raw": diagnostic, "worker_id": worker_id}


def _launch_jobs(base: Any, jobs: list[tuple[str, list[str], Path]], maximum: int, deadline: float) -> dict[str, tuple[str, int, Path]]:
    results: dict[str, tuple[str, int, Path]] = {}
    with ThreadPoolExecutor(max_workers=maximum) as pool:
        futures = {}
        for label, command, directory in jobs:
            timeout = min(CHILD_TIMEOUT_SECONDS, max(1, int(deadline - time.monotonic())))
            futures[pool.submit(base._launch, label, command, directory, timeout)] = label
        for future in as_completed(futures):
            results[futures[future]] = future.result()
    return results


def _cycle(root: Path, deadline: float) -> tuple[bytes, dict[str, Any]]:
    root.mkdir(parents=True, exist_ok=False)
    base = _module(f"_v6u_process_{time.monotonic_ns()}", V6S)
    jobs = []
    for worker_id in WORKER_IDS:
        directory = root / "workers" / worker_id.lower()
        command = [sys.executable, str(Path(__file__).resolve()), "--worker", worker_id, "--output", str(directory / "proof.json"), "--diagnostic-output", str(directory / "diagnostic.json")]
        jobs.append((worker_id, command, directory))
    producers = _launch_jobs(base, jobs, PRODUCER_CONCURRENCY, deadline)
    if any(row[0] != "COMPLETE" for row in producers.values()):
        raise V6UError("V6U producer process failed")
    checks = []
    for worker_id in WORKER_IDS:
        for replica in (1, 2):
            label = f"{worker_id}-{replica}"
            directory = root / "checkers" / worker_id.lower() / str(replica)
            command = [sys.executable, str(CHECKER), "--verify-v6u-proof", "--proof", str(producers[worker_id][2] / "proof.json"), "--output", str(directory / "check.json")]
            checks.append((label, command, directory))
    checkers = _launch_jobs(base, checks, CHECKER_CONCURRENCY, deadline)
    if any(row[0] != "COMPLETE" for row in checkers.values()):
        raise V6UError("V6U checker process failed")
    proofs = {worker_id: load(producers[worker_id][2] / "proof.json")[1] for worker_id in WORKER_IDS}
    diagnostics = {worker_id: load(producers[worker_id][2] / "diagnostic.json")[1] for worker_id in WORKER_IDS}
    for worker_id in WORKER_IDS:
        if (checkers[f"{worker_id}-1"][2] / "check.json").read_bytes() != (checkers[f"{worker_id}-2"][2] / "check.json").read_bytes():
            raise V6UError(f"V6U checker replicas disagree: {worker_id}")
    complete = all(proof["gate_status"] == PASS for proof in proofs.values())
    route_status = {"assembly": FAIL, "rss": FAIL, "solve": FAIL}
    if complete:
        by_fraction = {int(diagnostics[worker_id]["raw"]["fraction_percent"]): diagnostics[worker_id]["raw"] for worker_id in WORKER_IDS}
        reference = by_fraction[0]
        values = {name: [] for name in route_status}
        for fraction in (10, 25):
            candidate = by_fraction[fraction]
            values["assembly"].append(candidate["assembly"]["median_seconds"] / reference["assembly"]["median_seconds"])
            values["solve"].append(candidate["production_end_to_end_solve"]["median_seconds"] / reference["production_end_to_end_solve"]["median_seconds"])
            values["rss"].append(float(candidate["peak_rss_bytes"]) / float(reference["peak_rss_bytes"]))
        route_status = {name: PASS if all(math.isfinite(value) and value <= 1.10 for value in rows) else FAIL for name, rows in values.items()}
    passed = complete and all(value == PASS for value in route_status.values())
    common = {
        "activation_authorized": False,
        "candidate_formulation_id": CANDIDATE,
        "coverage": {"checker_replicas_per_worker": 2, "performance_repetitions": 11, "worker_ids": list(WORKER_IDS)},
        "gate_status": route_status,
        "next_gate": "V6V_PACKAGING_RESTART_BATCHING_AND_ACTIVATION_GAP_AUDIT" if passed else None,
        "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "schema": "anysolver.e4-pl-s3-v6u-performance-common-v1",
        "stage4b_composition": {"v6s_buckling": PASS, "v6s_modal": PASS},
        "terminal": GO if passed else NO_GO,
    }
    raw = canonical_bytes(common)
    with (root / "common.json").open("xb") as stream:
        stream.write(raw)
    return raw, common


def run(authorization: Path, output: Path) -> dict[str, Any]:
    contract_raw, _contract = validate_contract()
    validate_authorization(authorization, contract_raw)
    if output.exists():
        raise V6UError("exclusive V6U output exists")
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
    aggregate = {
        "activation_authorized": False,
        "authorization_sha256": sha256(authorization.read_bytes()),
        "candidate_formulation_id": CANDIDATE,
        "common_sha256": sha256(raws[0]) if raws else None,
        "cycles_byte_identical": identical,
        "error": error,
        "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "schema": "anysolver.e4-pl-s3-v6u-performance-aggregate-v1",
        "terminal": terminal,
    }
    with (output / "aggregate.json").open("xb") as stream:
        stream.write(canonical_bytes(aggregate))
    return aggregate


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--worker", choices=WORKER_IDS)
    mode.add_argument("--run-v6u", action="store_true")
    parser.add_argument("--authorization", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--diagnostic-output", type=Path)
    args = parser.parse_args(argv)
    if args.worker:
        if args.authorization is not None or args.diagnostic_output is None:
            raise V6UError("V6U worker arguments differ")
        validate_contract()
        proof, diagnostic = produce(args.worker)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("xb") as stream:
            stream.write(canonical_bytes(proof))
        with args.diagnostic_output.open("xb") as stream:
            stream.write(canonical_bytes(diagnostic))
        return 0
    if args.authorization is None or args.diagnostic_output is not None:
        raise V6UError("V6U coordinator arguments differ")
    result = run(args.authorization, args.output)
    print(canonical_bytes(result).decode("ascii"), end="")
    return 0 if result["terminal"] != BLOCKED else 2


if __name__ == "__main__":
    raise SystemExit(main())
