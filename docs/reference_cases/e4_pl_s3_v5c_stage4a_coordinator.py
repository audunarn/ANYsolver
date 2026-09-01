"""Coordinate two bounded deterministic V5C Stage 4A cycles."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import sys
import time
from typing import Any, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "docs" / "reference_cases"
if str(REFERENCE) not in sys.path:
    sys.path.insert(0, str(REFERENCE))

import e4_pl_s3_v5b_relaxed_screen_producer as bounded_source


CONTRACT = REFERENCE / "e4_pl_s3_v5c_stage4a_contract.json"
PRODUCER = REFERENCE / "e4_pl_s3_v5c_stage4a_producer.py"
CHECKER = REFERENCE / "e4_pl_s3_v5c_stage4a_checker.py"
FORMULATION_ID = "CANDIDATE_E4_PL_S3_V5B_MIN3_RELAXED_FLAT_LINEAR_SCREEN_V1"
SCHEMA = "anysolver.e4-pl-s3-v5c-stage4a-aggregate-v1"
DIAGONALS = ("slash", "backslash", "alternating")
BLOCKED = "BLOCKED_E4_PL_S3_V5C_STAGE4A_PROCESS_OR_EVIDENCE"
NO_GO = "NO_GO_E4_PL_S3_V5C_STAGE4A_MIXED_FLEXURAL_CONVERGENCE"
PASS = "PROVISIONAL_GO_E4_PL_S3_V5C_STAGE4B_PREPARATION"


class CoordinatorError(RuntimeError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("ascii")


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def _reject_constant(value: str) -> None:
    raise ValueError(f"nonfinite JSON constant {value}")


def _reject_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    made: dict[str, Any] = {}
    for key, value in pairs:
        if key in made:
            raise ValueError(f"duplicate JSON key {key}")
        made[key] = value
    return made


def load_canonical(path: Path) -> Mapping[str, Any]:
    raw = path.read_bytes()
    value = json.loads(raw, parse_constant=_reject_constant, object_pairs_hook=_reject_pairs)
    if not isinstance(value, dict) or raw != canonical_bytes(value):
        raise CoordinatorError(f"noncanonical JSON: {path}")
    return value


def exclusive_write(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(canonical_bytes(value))
        stream.flush()
        os.fsync(stream.fileno())


def validate_authority() -> Mapping[str, Any]:
    contract = load_canonical(CONTRACT)
    if contract.get("schema") != "anysolver.e4-pl-s3-v5c-stage4a-contract-v1":
        raise CoordinatorError("unexpected contract schema")
    for binding in contract.get("frozen_inputs", []):
        path = ROOT / str(binding["path"])
        raw = path.read_bytes()
        if len(raw) != binding["bytes"] or sha256_bytes(raw) != binding["sha256"]:
            raise CoordinatorError(f"frozen input mismatch: {path}")
    if contract.get("stage4a_execution_authorized") is not True or contract.get("activation_authorized") is not False:
        raise CoordinatorError("Stage 4A authority disposition mismatch")
    return contract


def _remaining(deadline: float, child_limit: int) -> int:
    remaining = int(deadline - time.monotonic())
    if remaining <= 0:
        raise CoordinatorError("complete Stage 4A wave exceeded its wall limit")
    return max(1, min(child_limit, remaining))


def _run(command: list[str], deadline: float, child_limit: int) -> None:
    bounded_source._run_child(command, _remaining(deadline, child_limit))


def _cycle(root: Path, cycle: int, deadline: float, child_limit: int) -> dict[str, Any]:
    cycle_root = root / f"cycle-{cycle}"
    cycle_root.mkdir()
    shards: dict[str, dict[str, Path]] = {}
    producer_commands: list[list[str]] = []
    for diagonal in DIAGONALS:
        shard_root = cycle_root / diagonal
        shard_root.mkdir()
        paths = {
            "proof": shard_root / "proof.json",
            "progress": shard_root / "producer-progress.jsonl",
            "checker_a": shard_root / "checker-a.json",
            "checker_b": shard_root / "checker-b.json",
        }
        shards[diagonal] = paths
        producer_commands.append([
            sys.executable,
            str(PRODUCER),
            "--emit-shard",
            "--diagonal",
            diagonal,
            "--output",
            str(paths["proof"]),
            "--progress",
            str(paths["progress"]),
        ])
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = [pool.submit(_run, command, deadline, child_limit) for command in producer_commands]
        for future in futures:
            future.result()
    for replica in ("checker_a", "checker_b"):
        commands = [
            [
                sys.executable,
                str(CHECKER),
                "--verify-shard",
                "--proof",
                str(shards[diagonal]["proof"]),
                "--output",
                str(shards[diagonal][replica]),
            ]
            for diagonal in DIAGONALS
        ]
        with ThreadPoolExecutor(max_workers=3) as pool:
            futures = [pool.submit(_run, command, deadline, child_limit) for command in commands]
            for future in futures:
                future.result()
    summaries = []
    sequence_results: list[Mapping[str, Any]] = []
    failures: list[str] = []
    for diagonal in DIAGONALS:
        paths = shards[diagonal]
        identical = paths["checker_a"].read_bytes() == paths["checker_b"].read_bytes()
        report = load_canonical(paths["checker_a"])
        if not identical or report.get("record_identity_passed") is not True:
            raise CoordinatorError(f"checker disagreement for {diagonal}")
        if report.get("independent_record_count") != 27 or report.get("sequence_count") != 8:
            raise CoordinatorError(f"checker coverage mismatch for {diagonal}")
        sequence_results.extend(report["sequence_results"])
        failures.extend(str(value) for value in report["formal_failures"])
        summaries.append({
            "checker_replicas_byte_identical": identical,
            "checker_sha256": sha256_file(paths["checker_a"]),
            "diagonal": diagonal,
            "formal_failure_count": int(report["formal_failure_count"]),
            "proof_bytes": paths["proof"].stat().st_size,
            "proof_sha256": sha256_file(paths["proof"]),
            "record_count": 27,
        })
    sequence_results.sort(key=lambda row: tuple(row["record_ids"]))
    failures.sort()
    return {
        "cycle": cycle,
        "formal_failure_count": len(failures),
        "formal_failures": failures,
        "record_count": 81,
        "sequence_count": 24,
        "sequence_results_sha256": sha256_bytes(canonical_bytes(sequence_results)),
        "shards": summaries,
    }


def _cycle_identity(cycle: Mapping[str, Any]) -> Mapping[str, Any]:
    return {key: cycle[key] for key in ("formal_failure_count", "formal_failures", "record_count", "sequence_count", "sequence_results_sha256", "shards")}


def run_bounded(output_root: Path, *, timeout_seconds: int = 600, wave_timeout_seconds: int = 1800) -> dict[str, Any]:
    validate_authority()
    if timeout_seconds not in range(1, 601) or wave_timeout_seconds not in range(1, 1801):
        raise CoordinatorError("requested limits exceed frozen bounds")
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=False)
    progress = root / "progress.jsonl"
    progress.touch(exist_ok=False)
    deadline = time.monotonic() + wave_timeout_seconds
    cycles: list[dict[str, Any]] = []
    terminal = BLOCKED
    try:
        for cycle in (1, 2):
            with progress.open("ab") as stream:
                stream.write(canonical_bytes({"cycle": cycle, "phase": "INITIALIZATION"}))
            made = _cycle(root, cycle, deadline, timeout_seconds)
            cycles.append(made)
            with progress.open("ab") as stream:
                stream.write(canonical_bytes({"cycle": cycle, "phase": "CYCLE_COMPLETE"}))
        if _cycle_identity(cycles[0]) != _cycle_identity(cycles[1]):
            terminal = BLOCKED
        elif cycles[0]["formal_failure_count"]:
            terminal = NO_GO
        else:
            terminal = PASS
    except BaseException as exc:
        cycles.append({"error_class": type(exc).__name__, "status": "FAILED_BOUNDED_CHILD"})
        terminal = BLOCKED
    aggregate = {
        "activation_authorized": False,
        "candidate_formulation_id": FORMULATION_ID,
        "contract_sha256": sha256_file(CONTRACT),
        "cycles": cycles,
        "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "schema": SCHEMA,
        "stage4b_preparation_authorized": terminal == PASS,
        "terminal": terminal,
    }
    exclusive_write(root / "aggregate.json", aggregate)
    return aggregate


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-bounded-stage4a", action="store_true", required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--timeout-seconds", type=int, default=600)
    parser.add_argument("--wave-timeout-seconds", type=int, default=1800)
    args = parser.parse_args(argv)
    run_bounded(args.output_root, timeout_seconds=args.timeout_seconds, wave_timeout_seconds=args.wave_timeout_seconds)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
