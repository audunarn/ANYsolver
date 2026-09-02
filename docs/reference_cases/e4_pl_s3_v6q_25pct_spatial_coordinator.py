"""Coordinate two bounded V6Q 25% spatial-response cycles."""

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
from types import ModuleType
from typing import Any, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "docs" / "reference_cases"
CONTRACT = REFERENCE / "e4_pl_s3_v6q_25pct_spatial_contract.json"
PRODUCER = REFERENCE / "e4_pl_s3_v6q_25pct_spatial_producer.py"
CHECKER = REFERENCE / "e4_pl_s3_v6q_25pct_spatial_checker.py"
AUTHORIZATION = REFERENCE / "e4_pl_s3_v6q_25pct_spatial_execution_authorization.json"
BOUNDED = REFERENCE / "e4_pl_s3_v2_bounded_process.py"
SCHEMA = "anysolver.e4-pl-s3-v6q-25pct-spatial-aggregate-v1"
FORMULATION_ID = "CANDIDATE_E4_PL_S3_V2D_NATIVE_PARITY_V1"
DIAGONALS = ("slash", "backslash", "alternating")
BLOCKED = "BLOCKED_E4_PL_S3_V6Q_PROCESS_OR_EVIDENCE"
NO_GO = "NO_GO_E4_PL_S3_V6Q_25PCT_SPATIAL_CONVERGENCE"
PASS = "PROVISIONAL_GO_E4_PL_S3_V6Q_STAGE4A_PROTOCOL_CLOSED"
THREAD_ENV = {
    "BLIS_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
    "NUMBA_NUM_THREADS": "1",
    "NUMEXPR_NUM_THREADS": "1",
    "OMP_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "TBB_NUM_THREADS": "1",
}
MEMORY_LIMIT_BYTES = 24 * (1 << 30)


class V6QCoordinatorError(RuntimeError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("ascii")


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def _reject_constant(value: str) -> None:
    raise V6QCoordinatorError(f"nonfinite JSON constant: {value}")


def _reject_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    made: dict[str, Any] = {}
    for key, value in pairs:
        if key in made:
            raise V6QCoordinatorError(f"duplicate JSON key: {key}")
        made[key] = value
    return made


def strict_json(path: Path) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    value = json.loads(raw, parse_constant=_reject_constant, object_pairs_hook=_reject_pairs)
    if not isinstance(value, dict) or raw != canonical_bytes(value):
        raise V6QCoordinatorError(f"noncanonical JSON: {path}")
    return value, raw


def _exclusive(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(canonical_bytes(value))
        stream.flush()
        os.fsync(stream.fileno())


def _load_bounded() -> ModuleType:
    spec = importlib.util.spec_from_file_location("_s3_v6q_bounded_process", BOUNDED)
    if spec is None or spec.loader is None:
        raise V6QCoordinatorError("cannot load bounded process guard")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_authority(*, require_execution: bool) -> tuple[dict[str, Any], bytes]:
    contract, contract_raw = strict_json(CONTRACT)
    if (
        contract.get("schema") != "anysolver.e4-pl-s3-v6q-25pct-spatial-contract-v1"
        or contract.get("activation_authorized") is not False
    ):
        raise V6QCoordinatorError("V6Q contract identity differs")
    for item in contract.get("frozen_inputs", []):
        path = Path(str(item["path"]))
        if not path.is_absolute():
            path = ROOT / path
        raw = path.read_bytes()
        if len(raw) != item["bytes"] or sha256(raw) != item["sha256"]:
            raise V6QCoordinatorError(f"frozen input differs: {path}")
    for name, path in (("producer", PRODUCER), ("checker", CHECKER), ("coordinator", Path(__file__).resolve())):
        raw = path.read_bytes()
        expected = contract["programs"][name]
        if len(raw) != expected["bytes"] or sha256(raw) != expected["sha256"]:
            raise V6QCoordinatorError(f"V6Q {name} differs")
    if require_execution:
        authorization, auth_raw = strict_json(AUTHORIZATION)
        if (
            set(authorization)
            != {"activation_authorized", "authority_commit", "contract_sha256", "execution_authorized", "review_sha256", "schema", "user_approval"}
            or authorization["schema"] != "anysolver.e4-pl-s3-v6q-25pct-spatial-execution-authorization-v1"
            or authorization["activation_authorized"] is not False
            or authorization["execution_authorized"] is not True
            or authorization["contract_sha256"] != sha256(contract_raw)
            or authorization["review_sha256"] != sha256((REFERENCE / "e4_pl_s3_v6q_25pct_spatial_review.json").read_bytes())
            or authorization["user_approval"] != "STANDING_S3_QUALIFICATION_APPROVAL"
        ):
            raise V6QCoordinatorError("V6Q execution authorization differs")
        contract["execution_authorization_sha256"] = sha256(auth_raw)
    return contract, contract_raw


def _remaining(deadline: float, child_limit: int) -> int:
    value = int(deadline - time.monotonic())
    if value <= 0:
        raise V6QCoordinatorError("V6Q cycle exceeded 1,800 seconds")
    return min(child_limit, value)


def _run_child(command: list[str], deadline: float, child_limit: int, stdout: Path, stderr: Path) -> None:
    bounded = _load_bounded()
    environment = os.environ.copy()
    environment.update(THREAD_ENV)
    job = bounded._ProcessJob(MEMORY_LIMIT_BYTES)
    stdout.parent.mkdir(parents=True, exist_ok=True)
    with stdout.open("xb") as out_stream, stderr.open("xb") as err_stream:
        try:
            process = job.launch(command, cwd=ROOT, env=environment, stdout=out_stream, stderr=err_stream)
            try:
                return_code = process.wait(timeout=_remaining(deadline, child_limit))
            except subprocess.TimeoutExpired as exc:
                if not job.terminate(124):
                    raise V6QCoordinatorError("timed-out process tree did not drain") from exc
                raise V6QCoordinatorError("bounded child timed out") from exc
            _cpu, active, peak = job.accounting()
            if active or peak > MEMORY_LIMIT_BYTES:
                job.terminate(125)
                raise V6QCoordinatorError("bounded child retained descendants or exceeded memory")
            if return_code:
                raise V6QCoordinatorError(f"bounded child failed with exit code {return_code}")
        finally:
            job.close()


def _cycle(root: Path, cycle: int, contract: Mapping[str, Any], child_limit: int) -> dict[str, Any]:
    cycle_root = root / f"cycle-{cycle}"
    cycle_root.mkdir()
    deadline = time.monotonic() + int(contract["execution"]["cycle_wall_seconds"])
    shards: dict[str, dict[str, Path]] = {}
    commands: list[tuple[list[str], Path, Path]] = []
    candidate_archive = Path(contract["candidate"]["archive_path"])
    support_archive = Path(contract["support"]["archive_path"])
    for diagonal in DIAGONALS:
        shard = cycle_root / diagonal
        shard.mkdir()
        paths = {
            "proof": shard / "proof.json",
            "progress": shard / "producer-progress.jsonl",
            "checker_a": shard / "checker-a.json",
            "checker_b": shard / "checker-b.json",
            "producer_stdout": shard / "producer-stdout.bin",
            "producer_stderr": shard / "producer-stderr.bin",
        }
        shards[diagonal] = paths
        commands.append(([
            sys.executable,
            str(PRODUCER),
            "--emit-spatial-shard",
            "--diagonal", diagonal,
            "--source-root", str(shard / "sources"),
            "--candidate-archive", str(candidate_archive),
            "--support-archive", str(support_archive),
            "--progress", str(paths["progress"]),
            "--output", str(paths["proof"]),
        ], paths["producer_stdout"], paths["producer_stderr"]))
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(_run_child, command, deadline, child_limit, stdout, stderr) for command, stdout, stderr in commands]
        for future in futures:
            future.result()
    summaries: list[dict[str, Any]] = []
    failures: list[str] = []
    sequences: list[Mapping[str, Any]] = []
    center_diagnostics: list[str] = []
    for diagonal in DIAGONALS:
        paths = shards[diagonal]
        checker_commands = []
        for suffix, output in (("a", paths["checker_a"]), ("b", paths["checker_b"])):
            checker_commands.append(([
                sys.executable, str(CHECKER), "--verify-spatial-shard",
                "--proof", str(paths["proof"]), "--output", str(output),
            ], output.with_name(f"checker-{suffix}-stdout.bin"), output.with_name(f"checker-{suffix}-stderr.bin")))
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(_run_child, command, deadline, child_limit, stdout, stderr) for command, stdout, stderr in checker_commands]
            for future in futures:
                future.result()
        identical = paths["checker_a"].read_bytes() == paths["checker_b"].read_bytes()
        report, report_raw = strict_json(paths["checker_a"])
        proof_raw = paths["proof"].read_bytes()
        if (
            not identical
            or report.get("record_identity_passed") is not True
            or report.get("independent_candidate_record_count") != 6
            or report.get("independent_baseline_record_count") != 3
            or report.get("sequence_count") != 2
        ):
            raise V6QCoordinatorError(f"checker disagreement or coverage mismatch: {diagonal}")
        failures.extend(str(item) for item in report["formal_failures"])
        sequences.extend(report["sequence_results"])
        center_diagnostics.extend(report["center_diagnostic_failures"])
        summaries.append({
            "checker_replicas_byte_identical": identical,
            "checker_sha256": sha256(report_raw),
            "diagonal": diagonal,
            "formal_failure_count": int(report["formal_failure_count"]),
            "proof_bytes": len(proof_raw),
            "proof_sha256": sha256(proof_raw),
            "record_count": 6,
        })
    failures.sort()
    sequences.sort(key=lambda item: tuple(item["record_ids"]))
    return {
        "center_diagnostic_failure_sequences": sorted(center_diagnostics),
        "cycle": cycle,
        "formal_failure_count": len(failures),
        "formal_failures": failures,
        "record_count": 18,
        "response_metric": "NODAL_UZ_RELATIVE_L2",
        "sequence_count": 6,
        "sequence_results_sha256": sha256(canonical_bytes(sequences)),
        "shards": summaries,
    }


def _cycle_identity(cycle: Mapping[str, Any]) -> dict[str, Any]:
    return {key: cycle[key] for key in cycle if key != "cycle"}


def adjudicate(cycles: Sequence[Mapping[str, Any]], *, process_complete: bool = True) -> str:
    if not process_complete or len(cycles) != 2 or _cycle_identity(cycles[0]) != _cycle_identity(cycles[1]):
        return BLOCKED
    return NO_GO if cycles[0]["formal_failure_count"] else PASS


def run_bounded(output_root: Path, *, timeout_seconds: int = 600) -> dict[str, Any]:
    contract, contract_raw = validate_authority(require_execution=True)
    if timeout_seconds not in range(1, 601):
        raise V6QCoordinatorError("child wall limit exceeds 600 seconds")
    output_root.mkdir(parents=True, exist_ok=False)
    progress = output_root / "progress.jsonl"
    progress.touch(exist_ok=False)
    cycles: list[dict[str, Any]] = []
    process_complete = True
    try:
        for cycle in (1, 2):
            with progress.open("ab") as stream:
                stream.write(canonical_bytes({"cycle": cycle, "phase": "INITIALIZATION"}))
            cycles.append(_cycle(output_root, cycle, contract, timeout_seconds))
            with progress.open("ab") as stream:
                stream.write(canonical_bytes({"cycle": cycle, "phase": "CYCLE_COMPLETE"}))
    except BaseException as exc:
        process_complete = False
        cycles.append({"error_class": type(exc).__name__, "status": "FAILED_BOUNDED_CHILD"})
    terminal = adjudicate(cycles, process_complete=process_complete)
    result = {
        "activation_authorized": False,
        "candidate_formulation_id": FORMULATION_ID,
        "center_metric_classifying": False,
        "contract_sha256": sha256(contract_raw),
        "cycles": cycles,
        "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "response_metric": "NODAL_UZ_RELATIVE_L2",
        "schema": SCHEMA,
        "stage4a_protocol_closed": terminal == PASS,
        "stage4b_execution_authorized": False,
        "stage4b_preparation_authorized": terminal == PASS,
        "terminal": terminal,
        "v6p_reclassified": False,
    }
    _exclusive(output_root / "aggregate.json", result)
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--validate-authority", action="store_true")
    mode.add_argument("--run-bounded-spatial-correction", action="store_true")
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--timeout-seconds", type=int, default=600)
    args = parser.parse_args(argv)
    if args.validate_authority:
        validate_authority(require_execution=False)
        return 0
    if args.output_root is None:
        raise V6QCoordinatorError("--output-root is required")
    result = run_bounded(args.output_root, timeout_seconds=args.timeout_seconds)
    return 0 if result["terminal"] in {NO_GO, PASS} else 2


if __name__ == "__main__":
    raise SystemExit(main())
