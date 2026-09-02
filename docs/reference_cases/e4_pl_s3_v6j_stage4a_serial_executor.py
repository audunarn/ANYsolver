"""Serial resource-manager executor for exact V6J Stage-4A wave requests."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
from types import ModuleType
from typing import Any, Mapping, Sequence


MANAGER = Path(r"C:\Github\.resource-manager")
REQUESTS = MANAGER / "requests"
LEDGER = MANAGER / "ledger.md"
ACTIVE_LOCK = MANAGER / "active-lock"
ACQUIRE = MANAGER / "acquire-test.ps1"
RELEASE = MANAGER / "release-test.ps1"
POWERSHELL = Path(r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe")
TASKKILL = Path(r"C:\Windows\System32\taskkill.exe")
OUTER_WALL_SECONDS = 1_830
TERMINAL_STATES = ("COMPLETED_PASS", "COMPLETED_FAIL", "CANCELLED_NOT_RUN")
REFERENCE = Path(__file__).resolve().parent
ROOT = REFERENCE.parents[1]
GRAPH_PROGRAM = REFERENCE / "e4_pl_s3_v6i_stage4a_execution_graph.py"
AUTHORITY_PROGRAM = REFERENCE / "e4_pl_s3_v6j_stage4a_authority.py"


class V6JExecutionError(RuntimeError):
    """Raised when a V6J request cannot be safely approved or executed."""


def _reject_constant(value: str) -> None:
    raise V6JExecutionError(f"nonfinite JSON constant is forbidden: {value}")


def _reject_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    made: dict[str, Any] = {}
    for key, value in pairs:
        if key in made:
            raise V6JExecutionError(f"duplicate JSON key is forbidden: {key}")
        made[key] = value
    return made


def canonical_bytes(value: Any) -> bytes:
    def visit(item: Any) -> None:
        if item is None or isinstance(item, (bool, int, str)):
            return
        if isinstance(item, float):
            if not math.isfinite(item):
                raise V6JExecutionError("nonfinite JSON number is forbidden")
            return
        if isinstance(item, list):
            for child in item:
                visit(child)
            return
        if isinstance(item, dict):
            for key, child in item.items():
                if not isinstance(key, str):
                    raise V6JExecutionError("JSON keys must be strings")
                visit(child)
            return
        raise V6JExecutionError(f"unsupported JSON type: {type(item).__name__}")

    visit(value)
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode(
        "utf-8"
    )


def strict_json(path: Path) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_reject_pairs,
            parse_constant=_reject_constant,
        )
    except (UnicodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
        if isinstance(exc, V6JExecutionError):
            raise
        raise V6JExecutionError(f"invalid JSON: {path}") from exc
    if not isinstance(value, dict) or raw != canonical_bytes(value):
        raise V6JExecutionError(f"noncanonical JSON: {path}")
    return value, raw


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def _load(path: Path, name: str) -> ModuleType:
    information = path.resolve().lstat()
    if not stat.S_ISREG(information.st_mode) or path.is_symlink():
        raise V6JExecutionError(f"program is not regular: {path}")
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise V6JExecutionError(f"cannot load program: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def validate_authorization(
    authorization_path: Path, graph_path: Path, archive: Path
) -> tuple[dict[str, Any], bytes, dict[str, Any], bytes]:
    authority_program = _load(AUTHORITY_PROGRAM, "_s3_v6j_authority")
    graph_program = _load(GRAPH_PROGRAM, "_s3_v6j_execution_graph")
    authorization, authorization_raw = strict_json(authorization_path.resolve())
    graph, graph_raw = strict_json(graph_path.resolve())
    graph_program.validate_graph(graph)
    graph_program.verify_archive(archive.resolve())
    if (
        authorization.get("schema") != authority_program.SCHEMA
        or authorization.get("activation_authorized") is not False
        or authorization.get("stage4a_execution_authorized") is not True
        or authorization.get("graph_sha256") != sha256(graph_raw)
    ):
        raise V6JExecutionError("V6J execution authorization differs")
    rows = authorization.get("requests")
    if not isinstance(rows, list) or len(rows) != graph_program.WAVE_COUNT:
        raise V6JExecutionError("V6J request coverage differs")
    seen: set[str] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping) or set(row) != {
            "request", "request_sha256", "wave_index"
        } or row["wave_index"] != index:
            raise V6JExecutionError("V6J request row differs")
        request = row["request"]
        raw = canonical_bytes(request)
        request_id = request.get("request_id") if isinstance(request, dict) else None
        if (
            not isinstance(request_id, str)
            or request_id != authority_program.request_id(index)
            or request_id in seen
            or row["request_sha256"] != sha256(raw)
        ):
            raise V6JExecutionError("V6J request identity differs")
        seen.add(request_id)
    return authorization, authorization_raw, graph, graph_raw


def _ledger_rows(ledger: str, request_id: str, state: str) -> list[str]:
    pattern = re.compile(rf"^\|[^\n]*\|\s*{re.escape(request_id)}\s*\|\s*{state}\s*\|", re.MULTILINE)
    return pattern.findall(ledger)


def _append_ledger(line: str) -> None:
    raw = (line.rstrip("\r\n") + "\n").encode("utf-8")
    with LEDGER.open("ab", buffering=0) as handle:
        handle.write(raw)
        os.fsync(handle.fileno())


def _request_file(row: Mapping[str, Any]) -> tuple[dict[str, Any], bytes, Path]:
    expected = row["request"]
    request_id = expected["request_id"]
    path = REQUESTS / f"{request_id}.json"
    request, raw = strict_json(path)
    if request != expected or sha256(raw) != row["request_sha256"]:
        raise V6JExecutionError(f"published request differs: {request_id}")
    return request, raw, path


def approve_all(authorization_path: Path, graph_path: Path, archive: Path) -> int:
    authorization, authorization_raw, _graph, graph_raw = validate_authorization(
        authorization_path, graph_path, archive
    )
    if ACTIVE_LOCK.exists():
        raise V6JExecutionError("resource slot is occupied")
    ledger = LEDGER.read_text(encoding="utf-8-sig")
    prepared: list[tuple[dict[str, Any], bytes]] = []
    for row in authorization["requests"]:
        request, raw, _path = _request_file(row)
        request_id = request["request_id"]
        if any(_ledger_rows(ledger, request_id, state) for state in ("APPROVED", "EXECUTION_STARTED", *TERMINAL_STATES)):
            raise V6JExecutionError(f"request already appears in ledger: {request_id}")
        prepared.append((request, raw))
    timestamp = _now()
    for request, raw in prepared:
        _append_ledger(
            f"| {timestamp} | {request['request_id']} | APPROVED | {request['task']} | "
            f"{request['repository']} | Immutable request bytes {len(raw)} SHA-256 {sha256(raw)}; "
            f"authorization SHA-256 {sha256(authorization_raw)}; graph SHA-256 {sha256(graph_raw)} | "
            "30 minutes | Standing approval; one three-worker bounded wave; 600-second child hard wall; "
            "1800-second wave hard wall; 24 GiB per process tree; no automatic retry. |"
        )
    return len(prepared)


def _validate_completed_wave(wave_index: int, wave_root: Path) -> dict[str, Any]:
    wrapper, wrapper_raw = strict_json(wave_root / "wave-wrapper-result.json")
    bounded, bounded_raw = strict_json(wave_root / "bounded-result.json")
    workers = bounded.get("workers")
    if (
        wrapper.get("terminal") != "COMPLETED"
        or wrapper.get("wave_index") != wave_index
        or wrapper.get("stage4a_execution_authorized") is not True
        or bounded.get("terminal") != "COMPLETED"
        or not isinstance(workers, list)
        or len(workers) != 3
        or any(
            worker.get("status") != "COMPLETED"
            or worker.get("termination_proven") is not True
            or worker.get("scientific_record_count") != 1
            or worker.get("scientific_terminal") != "ACCEPTED_FOR_AGGREGATION"
            for worker in workers
        )
    ):
        raise V6JExecutionError("bounded wave receipt is not an exact completion")
    return {
        "bounded_result_bytes": len(bounded_raw),
        "bounded_result_sha256": sha256(bounded_raw),
        "scientific_sha256": [worker["scientific_sha256"] for worker in workers],
        "wrapper_bytes": len(wrapper_raw),
        "wrapper_sha256": sha256(wrapper_raw),
    }


def run_wave(
    wave_index: int,
    authorization_path: Path,
    graph_path: Path,
    archive: Path,
    qualification_root: Path,
) -> int:
    authorization, authorization_raw, _graph, graph_raw = validate_authorization(
        authorization_path, graph_path, archive
    )
    if not 0 <= wave_index < len(authorization["requests"]):
        raise V6JExecutionError("wave index is outside authorization")
    row = authorization["requests"][wave_index]
    request, request_raw, request_path = _request_file(row)
    request_id = request["request_id"]
    graph_program = _load(GRAPH_PROGRAM, "_s3_v6j_run_graph")
    wave_root = qualification_root.resolve() / f"wave-{wave_index + 1:02d}"
    expected_command = graph_program.registered_command(
        graph_path=graph_path,
        wave_index=wave_index,
        candidate_archive=archive,
        output_root=wave_root,
        authorization_path=authorization_path,
        request_path=request_path,
        result_path=wave_root / "wave-wrapper-result.json",
    )
    if request["command"] != expected_command:
        raise V6JExecutionError("stored request command differs")
    ledger = LEDGER.read_text(encoding="utf-8-sig")
    if len(_ledger_rows(ledger, request_id, "APPROVED")) != 1:
        raise V6JExecutionError("request lacks one exact approval")
    if any(_ledger_rows(ledger, request_id, state) for state in ("EXECUTION_STARTED", *TERMINAL_STATES)):
        raise V6JExecutionError("request was already consumed")
    if ACTIVE_LOCK.exists():
        raise V6JExecutionError("resource slot is occupied")
    admin_root = qualification_root.resolve() / "administration" / f"wave-{wave_index + 1:02d}"
    admin_root.mkdir(parents=True, exist_ok=False)
    stdout_path = admin_root / "stdout.bin"
    stderr_path = admin_root / "stderr.bin"
    acquired = False
    returncode: int | None = None
    failure: str | None = None
    process: subprocess.Popen[bytes] | None = None
    subprocess.run(
        [str(POWERSHELL), "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ACQUIRE), "-RequestId", request_id],
        check=True,
        timeout=30,
        capture_output=True,
    )
    acquired = True
    _append_ledger(
        f"| {_now()} | {request_id} | EXECUTION_STARTED | {request['task']} | {request['repository']} | "
        f"exact command bytes {len(request['command'].encode('utf-8'))} SHA-256 {sha256(request['command'].encode('utf-8'))}; "
        f"authorization SHA-256 {sha256(authorization_raw)}; graph SHA-256 {sha256(graph_raw)} | "
        "30 minutes | One registered V6J wave; no automatic retry. |"
    )
    try:
        with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
            process = subprocess.Popen(
                [str(POWERSHELL), "-NoProfile", "-Command", request["command"]],
                cwd=ROOT,
                stdout=stdout,
                stderr=stderr,
            )
            try:
                returncode = process.wait(timeout=OUTER_WALL_SECONDS)
            except subprocess.TimeoutExpired:
                failure = "OUTER_WALL_TIMEOUT"
                subprocess.run(
                    [str(TASKKILL), "/PID", str(process.pid), "/T", "/F"],
                    check=False,
                    timeout=30,
                    capture_output=True,
                )
                returncode = process.wait(timeout=30)
    except BaseException as exc:
        failure = f"{type(exc).__name__}:{exc}"
    finally:
        if acquired:
            subprocess.run(
                [str(POWERSHELL), "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(RELEASE), "-RequestId", request_id],
                check=True,
                timeout=30,
                capture_output=True,
            )
    exact: dict[str, Any] | None = None
    if failure is None and returncode == 0:
        try:
            exact = _validate_completed_wave(wave_index, wave_root)
        except BaseException as exc:
            failure = f"{type(exc).__name__}:{exc}"
    if failure is None and returncode != 0:
        failure = f"COMMAND_EXIT_{returncode}"
    stdout_raw = stdout_path.read_bytes()
    stderr_raw = stderr_path.read_bytes()
    receipt = {
        "authorization_sha256": sha256(authorization_raw),
        "failure": failure,
        "graph_sha256": sha256(graph_raw),
        "request_id": request_id,
        "request_sha256": sha256(request_raw),
        "returncode": returncode,
        "schema": "anysolver.e4-pl-s3-v6j-stage4a-wave-receipt-v1",
        "stderr_bytes": len(stderr_raw),
        "stderr_sha256": sha256(stderr_raw),
        "stdout_bytes": len(stdout_raw),
        "stdout_sha256": sha256(stdout_raw),
        "terminal": "COMPLETED_PASS" if failure is None else "COMPLETED_FAIL",
        "validated_wave": exact,
        "wave_index": wave_index,
    }
    receipt_raw = canonical_bytes(receipt)
    receipt_path = admin_root / "receipt.json"
    with receipt_path.open("xb") as handle:
        handle.write(receipt_raw)
        handle.flush()
        os.fsync(handle.fileno())
    _append_ledger(
        f"| {_now()} | {request_id} | {receipt['terminal']} | {request['task']} | {request['repository']} | "
        f"receipt bytes {len(receipt_raw)} SHA-256 {sha256(receipt_raw)}; stdout bytes {len(stdout_raw)} SHA-256 {sha256(stdout_raw)}; "
        f"stderr bytes {len(stderr_raw)} SHA-256 {sha256(stderr_raw)} | exact | "
        f"{'EXIT_ZERO_AND_EXACT_COMPLETED_RECEIPT_VALIDATED' if failure is None else failure} |"
    )
    return 0 if failure is None else 2


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--validate-only", action="store_true")
    mode.add_argument("--approve", action="store_true")
    mode.add_argument("--run-wave", type=int)
    parser.add_argument("--authorization", type=Path, required=True)
    parser.add_argument("--graph", type=Path, required=True)
    parser.add_argument("--candidate-archive", type=Path, required=True)
    parser.add_argument("--qualification-root", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.validate_only:
        validate_authorization(args.authorization, args.graph, args.candidate_archive)
        return 0
    if args.approve:
        count = approve_all(args.authorization, args.graph, args.candidate_archive)
        print(f"APPROVED {count}")
        return 0
    assert args.run_wave is not None
    return run_wave(
        args.run_wave, args.authorization, args.graph, args.candidate_archive,
        args.qualification_root,
    )


if __name__ == "__main__":
    raise SystemExit(main())
