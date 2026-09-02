"""Bounded V5L full Stage 4B successor runner."""

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
from typing import Any, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "docs/reference_cases"
V5K_PRODUCER = REFERENCE / "e4_pl_s3_v5k_producer.py"
V5K_COORDINATOR = REFERENCE / "e4_pl_s3_v5k_coordinator.py"
CHECKER = REFERENCE / "e4_pl_s3_v5l_checker.py"
WORKER_IDS = (
    "MODAL_10", "MODAL_25", "BUCKLING_10", "BUCKLING_25",
    "PERFORMANCE_0", "PERFORMANCE_10", "PERFORMANCE_25",
)
PASS = "PASS_MEASURED_REGISTERED_SCOPE"
FAIL = "FAIL_MEASURED_CONTRADICTION"
BLOCKED = "BLOCKED_E4_PL_S3_V5L_STAGE4B_PROCESS_OR_EVIDENCE"
NO_GO_EIGEN = "NO_GO_E4_PL_S3_V5L_MIXED_EIGEN"
NO_GO_PERFORMANCE = "NO_GO_E4_PL_S3_V5L_MIXED_PERFORMANCE"
GO = "PROVISIONAL_GO_E4_PL_S3_V5L_STAGE4B_CLOSED_ONLY"
CHILD_TIMEOUT_SECONDS = 600
WAVE_TIMEOUT_SECONDS = 1800
WORKER_CONCURRENCY = 3
CHECKER_CONCURRENCY = 4
CYCLES = 2
SCHEMA = "anysolver.e4-pl-s3-v5l-worker-proof-v1"


class V5LStage4BError(RuntimeError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("ascii")


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def _pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    made: dict[str, Any] = {}
    for key, value in items:
        if key in made:
            raise V5LStage4BError(f"duplicate JSON key: {key}")
        made[key] = value
    return made


def load(path: Path) -> tuple[bytes, dict[str, Any]]:
    raw = path.read_bytes()
    value = json.loads(raw, object_pairs_hook=_pairs, parse_constant=lambda token: (_ for _ in ()).throw(V5LStage4BError(f"nonfinite token: {token}")))
    if not isinstance(value, dict) or raw != canonical_bytes(value):
        raise V5LStage4BError(f"noncanonical JSON: {path}")
    return raw, value


def _load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise V5LStage4BError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def produce(worker_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    if worker_id not in WORKER_IDS:
        raise V5LStage4BError(f"unknown worker {worker_id}")
    v5k = _load_module(f"_v5l_v5k_{worker_id.lower()}", V5K_PRODUCER)
    lane, authorities = v5k._lane()
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
        payload = v5k._spectral(lane, authorities, fraction)
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
        "candidate_formulation_id": "CANDIDATE_E4_PL_S3_V2C_FLAT_LINEAR_PARITY_V1",
        "gate_status": PASS if passed else FAIL,
        "payload": payload,
        "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "schema": SCHEMA,
        "v5k_terminal":"PROVISIONAL_GO_E4_PL_S3_V5K_STAGE4B_RERUN",
        "worker_id": worker_id,
    }
    proof["scientific_payload_sha256"] = sha256(canonical_bytes(proof))
    return proof, {"elapsed_seconds": float(time.perf_counter() - started), "raw": diagnostic, "worker_id": worker_id}


def _git(*arguments: str) -> str:
    process = subprocess.run(["git", *arguments], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if process.returncode:
        raise V5LStage4BError(process.stderr.strip() or "git command failed")
    return process.stdout.strip()


def validate_authorization(path: Path) -> dict[str, Any]:
    _raw, value = load(path)
    if value.get("schema") != "anysolver.e4-pl-s3-v5l-execution-authorization-v1":
        raise V5LStage4BError("unexpected V5L authorization schema")
    if _git("rev-parse", "HEAD^") != value.get("implementation_commit") or _git("show", "-s", "--format=%s", "HEAD") != value.get("expected_authorization_subject"):
        raise V5LStage4BError("V5L authorization topology changed")
    for row in value.get("frozen_inputs", []):
        raw = (ROOT / row["path"]).read_bytes()
        if len(raw) != row["bytes"] or sha256(raw) != row["sha256"]:
            raise V5LStage4BError(f"frozen input mismatch: {row['path']}")
    return value


def _launch_jobs(jobs: Sequence[tuple[str, list[str], Path]], maximum: int, deadline: float) -> dict[str, tuple[str, int, Path]]:
    process = _load_module(f"_v5l_process_{time.monotonic_ns()}", V5K_COORDINATOR)
    results: dict[str, tuple[str, int, Path]] = {}
    with ThreadPoolExecutor(max_workers=maximum) as pool:
        futures = {}
        for label, command, directory in jobs:
            timeout = min(CHILD_TIMEOUT_SECONDS, max(1, int(deadline - time.monotonic())))
            futures[pool.submit(process._launch, label, command, directory, timeout)] = label
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
    producers = _launch_jobs(producer_jobs, WORKER_CONCURRENCY, deadline)
    if any(row[0] != "COMPLETE" for row in producers.values()):
        raise V5LStage4BError("V5L producer process failed")
    checker_jobs = []
    for worker_id in WORKER_IDS:
        proof = producers[worker_id][2] / "proof.json"
        for replica in (1, 2):
            label = f"{worker_id}-{replica}"
            directory = root / "checkers" / worker_id.lower() / str(replica)
            command = [sys.executable, str(CHECKER), "--verify-v5l-proof", "--proof", str(proof), "--output", str(directory / "check.json")]
            checker_jobs.append((label, command, directory))
    checkers = _launch_jobs(checker_jobs, CHECKER_CONCURRENCY, deadline)
    if any(row[0] != "COMPLETE" for row in checkers.values()):
        raise V5LStage4BError("V5L checker process failed")
    proofs = {worker_id: load(producers[worker_id][2] / "proof.json")[1] for worker_id in WORKER_IDS}
    diagnostics = {worker_id: load(producers[worker_id][2] / "diagnostic.json")[1] for worker_id in WORKER_IDS}
    for worker_id in WORKER_IDS:
        if (checkers[f"{worker_id}-1"][2] / "check.json").read_bytes() != (checkers[f"{worker_id}-2"][2] / "check.json").read_bytes():
            raise V5LStage4BError(f"V5L checker replicas disagree: {worker_id}")
    modal = all(proofs[worker_id]["gate_status"] == PASS for worker_id in WORKER_IDS[:2])
    buckling = all(proofs[worker_id]["gate_status"] == PASS for worker_id in WORKER_IDS[2:4])
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
    gates = {"buckling": PASS if buckling else FAIL, "mixed_performance": PASS if performance else FAIL, "modal": PASS if modal else FAIL}
    terminal = NO_GO_EIGEN if not modal or not buckling else NO_GO_PERFORMANCE if not performance else GO
    common = {
        "activation_authorized": False,
        "candidate_formulation_id": "CANDIDATE_E4_PL_S3_V2C_FLAT_LINEAR_PARITY_V1",
        "coverage": {"buckling_factor_count":5,"buckling_window_modes":8,"checker_replicas_per_worker":2,"modal_elastic_modes":10,"performance_repetitions":11,"worker_ids":list(WORKER_IDS)},
        "gate_status": gates,
        "next_gate": "V5M_BATCH_RESTART_AND_PACKAGE_PARITY" if terminal == GO else None,
        "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "schema": "anysolver.e4-pl-s3-v5l-cycle-common-v1",
        "terminal": terminal,
    }
    raw = canonical_bytes(common)
    with (root / "common.json").open("xb") as stream:
        stream.write(raw)
    return raw, common


def run(authorization: Path, output: Path) -> dict[str, Any]:
    validate_authorization(authorization)
    if output.exists():
        raise V5LStage4BError("exclusive V5L output root exists")
    output.mkdir(parents=True)
    deadline = time.monotonic() + WAVE_TIMEOUT_SECONDS
    try:
        rows = [_cycle(output / f"cycle-{cycle}", deadline) for cycle in (1, 2)]
        identical = rows[0][0] == rows[1][0]
        terminal = rows[0][1]["terminal"] if identical and rows[0][1]["terminal"] == rows[1][1]["terminal"] else BLOCKED
    except Exception as error:
        identical, terminal = False, BLOCKED
        (output / "failure.txt").write_text(f"{type(error).__name__}: {error}\n", encoding="utf-8")
    result = {"activation_authorized":False,"authorization_sha256":sha256(authorization.read_bytes()),"cycles_byte_identical":identical,"production_restriction":"NO_GO_PRODUCTION_RESTRICTION_UNCHANGED","schema":"anysolver.e4-pl-s3-v5l-aggregate-v1","terminal":terminal}
    with (output / "aggregate.json").open("xb") as stream:
        stream.write(canonical_bytes(result))
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--worker", choices=WORKER_IDS)
    mode.add_argument("--run-v5l", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--diagnostic-output", type=Path)
    parser.add_argument("--authorization", type=Path)
    args = parser.parse_args(argv)
    if args.worker:
        if args.diagnostic_output is None:
            raise V5LStage4BError("worker diagnostic output is required")
        proof, diagnostic = produce(args.worker)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("xb") as stream:
            stream.write(canonical_bytes(proof))
        with args.diagnostic_output.open("xb") as stream:
            stream.write(canonical_bytes(diagnostic))
    else:
        if args.authorization is None:
            raise V5LStage4BError("execution authorization is required")
        print(canonical_bytes(run(args.authorization, args.output)).decode("ascii"), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
