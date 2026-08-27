"""Run a bounded, nonclassifying S3-activation cold-path timing smoke.

The coordinator imports only the Python standard library.  Numerical and
mechanics imports occur solely in bounded child processes after the one-thread
environment has been checked.  This program never emits qualification
evidence and never authorizes a formal activation cycle.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import ctypes
from ctypes import wintypes
from dataclasses import dataclass
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


ROOT = Path(__file__).resolve().parents[1]
PROGRAM = ROOT / "docs" / "reference_cases" / "e4_pl_s3_default_activation_v2.py"
INPUT = ROOT / "docs" / "reference_cases" / "e4_pl_s3_default_activation_v2_input.json"
CONTRACT = ROOT / "docs" / "reference_cases" / "e4_pl_s3_default_activation_v2_contract.json"
MANIFEST = ROOT / "docs" / "reference_cases" / "e4_pl_s3_mixed_mesh_connectivity_manifest.json"
SCHEMA = "anysolver.e4-pl-s3-activation-cold-path-smoke-v1"
CHILD_SCHEMA = "anysolver.e4-pl-s3-activation-cold-path-child-v1"
NONCLASSIFYING_TERMINAL = "NONCLASSIFYING_E4_PL_S3_COLD_PATH_TIMING_ONLY"
BLOCKED_TERMINAL = "BLOCKED_NONCLASSIFYING_E4_PL_S3_COLD_PATH_SMOKE"
PRODUCTION_RESTRICTION = "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"
THREAD_ENVIRONMENT = {
    "OMP_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
    "NUMEXPR_NUM_THREADS": "1",
    "PYTHONHASHSEED": "0",
}
ALLOWED_LEVELS = (20, 40, 80, 160)
FRACTIONS = (0, 10, 25)
FULL_FORECAST_LEVELS = frozenset(ALLOWED_LEVELS)
TREE_RELEASE_ENVIRONMENT = "ANYSOLVER_S3_COLD_TREE_RELEASE"
TREE_RELEASE_BYTES = b"ANYSOLVER_S3_COLD_TREE_ACCOUNTED_V1\n"
TREE_RELEASE_WAIT_SECONDS = 5.0
TASKKILL_TIMEOUT_SECONDS = 0.5
PROCESS_WAIT_SECONDS = 0.25
MAX_CHILD_RECORD_BYTES = 1 << 20

JOB_OBJECT_LIMIT_JOB_MEMORY = 0x00000200
JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
JOB_OBJECT_BASIC_AND_IO_ACCOUNTING_INFORMATION = 8
JOB_OBJECT_EXTENDED_LIMIT_INFORMATION = 9


class SmokeError(ValueError):
    """A nonclassifying smoke input or child record is malformed."""


def _reject_constant(value: str) -> None:
    raise SmokeError(f"nonfinite JSON value is forbidden: {value}")


def _pairs(values: Sequence[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in values:
        if key in result:
            raise SmokeError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(
        path.read_bytes(),
        object_pairs_hook=_pairs,
        parse_constant=_reject_constant,
    )
    if not isinstance(value, dict):
        raise SmokeError(f"{path} must contain one JSON object")
    return value


def canonical_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        + b"\n"
    )


def write_exclusive(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(canonical_bytes(value))


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def forecast_seconds(rows: Sequence[Mapping[str, Any]]) -> float | None:
    """Return the conservative 21-sequence structural-shard forecast."""

    completed: dict[tuple[int, int], float] = {}
    for row in rows:
        if row.get("status") != "COMPLETE":
            continue
        level = int(row["level"])
        fraction = int(row["fraction_percent"])
        elapsed = int(row["elapsed_ms"]) / 1000.0
        completed[(level, fraction)] = elapsed
    required = {(level, fraction) for level in ALLOWED_LEVELS for fraction in FRACTIONS}
    if set(completed) != required:
        return None
    sequence_seconds = sum(
        completed[(level, 0)]
        + 20.0 * max(completed[(level, 10)], completed[(level, 25)])
        for level in ALLOWED_LEVELS
    )
    return float(60.0 + 1.25 * sequence_seconds)


def partial_forecast_lower_bound_seconds(
    rows: Sequence[Mapping[str, Any]],
) -> float:
    """Return a lower bound from every level with all three timings.

    The omitted registered levels can only add nonnegative work.  This lets a
    bounded N20/N40 screen reject an infeasible forecast without launching the
    more expensive N80/N160 records.  It never completes or authorizes the
    full forecast.
    """

    completed: dict[tuple[int, int], float] = {}
    for row in rows:
        if row.get("status") != "COMPLETE":
            continue
        level = int(row["level"])
        fraction = int(row["fraction_percent"])
        if level not in ALLOWED_LEVELS or fraction not in FRACTIONS:
            continue
        completed[(level, fraction)] = int(row["elapsed_ms"]) / 1000.0
    sequence_seconds = 0.0
    for level in ALLOWED_LEVELS:
        if all((level, fraction) in completed for fraction in FRACTIONS):
            sequence_seconds += completed[(level, 0)] + 20.0 * max(
                completed[(level, 10)], completed[(level, 25)]
            )
    return float(60.0 + 1.25 * sequence_seconds)


def _load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise SmokeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _child(level: int, fraction: int, output: Path) -> None:
    release_name = os.environ.get(TREE_RELEASE_ENVIRONMENT)
    if release_name:
        release = Path(release_name)
        release_deadline = time.monotonic() + TREE_RELEASE_WAIT_SECONDS
        while not release.is_file():
            if time.monotonic() >= release_deadline:
                raise SmokeError("child process-tree accounting was not released")
            time.sleep(0.01)
        if release.read_bytes() != TREE_RELEASE_BYTES:
            raise SmokeError("child process-tree accounting release is malformed")
    if {name: os.environ.get(name) for name in THREAD_ENVIRONMENT} != THREAD_ENVIRONMENT:
        raise SmokeError("child numerical-thread environment is not exactly one")
    source = (ROOT / "src").resolve()
    if str(source) not in sys.path:
        sys.path.insert(0, str(source))
    runner = _load_module("_s3_activation_cold_path_runner", PROGRAM)
    input_value = read_json(INPUT)
    contract_value = read_json(CONTRACT)
    manifest_value = read_json(MANIFEST)
    authority = runner.Authority(
        INPUT,
        INPUT.read_bytes(),
        input_value,
        CONTRACT,
        CONTRACT.read_bytes(),
        contract_value,
        MANIFEST,
        runner.canonical_bytes(manifest_value),
        manifest_value,
        source,
    )
    bundle = runner._activate(authority)
    synthetic = runner._structural_authority(authority, bundle, "alternating")
    record = bundle.structural_common.find_record(
        synthetic,
        level=level,
        fraction=fraction,
        mask="none" if fraction == 0 else "dispersed",
        diagonal="alternating",
    )
    started = time.perf_counter_ns()
    value, _errors = runner._plate_case_v2(
        bundle,
        synthetic,
        record,
        recover_interface=True,
    )
    elapsed_microseconds = (time.perf_counter_ns() - started) // 1000
    write_exclusive(
        output,
        {
            "classification_authority": False,
            "elapsed_microseconds": int(elapsed_microseconds),
            "energy_norm_error": float(value["energy_norm_error"]),
            "fraction_percent": fraction,
            "level": level,
            "record_id": str(value["record_id"]),
            "schema": CHILD_SCHEMA,
        },
    )


def _expected_record_id(*, level: int, fraction: int) -> str:
    mask = "none" if fraction == 0 else "dispersed"
    return f"N{level}:{fraction}PCT:{mask}:alternating"


def _read_child(
    path: Path,
    *,
    level: int,
    fraction: int,
) -> tuple[dict[str, Any], str, int]:
    try:
        byte_count = path.stat().st_size
    except OSError as exc:
        raise SmokeError("child output cannot be inspected") from exc
    if byte_count <= 0:
        raise SmokeError("child output is empty")
    if byte_count > MAX_CHILD_RECORD_BYTES:
        raise SmokeError("child output exceeds the canonical record bound")
    raw = path.read_bytes()
    value = read_json(path)
    if raw != canonical_bytes(value):
        raise SmokeError("child output is not canonical JSON")
    expected_keys = {
        "classification_authority",
        "elapsed_microseconds",
        "energy_norm_error",
        "fraction_percent",
        "level",
        "record_id",
        "schema",
    }
    if set(value) != expected_keys:
        raise SmokeError("child output schema fields changed")
    elapsed = value["elapsed_microseconds"]
    energy = value["energy_norm_error"]
    if (
        value["schema"] != CHILD_SCHEMA
        or value["classification_authority"] is not False
        or type(value["level"]) is not int
        or value["level"] != level
        or type(value["fraction_percent"]) is not int
        or value["fraction_percent"] != fraction
        or type(value["record_id"]) is not str
        or value["record_id"] != _expected_record_id(
            level=level,
            fraction=fraction,
        )
        or type(elapsed) is not int
        or elapsed < 0
        or not isinstance(energy, (int, float))
        or isinstance(energy, bool)
        or not math.isfinite(float(energy))
        or float(energy) < 0.0
    ):
        raise SmokeError("child output identity or value is invalid")
    return value, sha256(raw), len(raw)


def _rejected_record_identity(path: Path) -> tuple[int, str]:
    """Bind a small rejected record without reading an unbounded child file."""

    try:
        byte_count = int(path.stat().st_size)
    except OSError:
        return 0, ""
    if byte_count <= 0 or byte_count > MAX_CHILD_RECORD_BYTES:
        return max(0, byte_count), ""
    try:
        raw = path.read_bytes()
    except OSError:
        return byte_count, ""
    return len(raw), sha256(raw) if raw else ""


@dataclass(frozen=True)
class ProcessResult:
    level: int
    fraction: int
    status: str
    returncode: int
    elapsed_ms: int
    peak_tree_memory_bytes: int
    started_ns: int
    ended_ns: int
    directory: str
    child_elapsed_microseconds: int = -1
    record_byte_count: int = 0
    record_sha256: str = ""


class _TreeAccountingError(RuntimeError):
    """The coordinator cannot prove or enforce a complete-tree bound."""


class _IoCounters(ctypes.Structure):
    _fields_ = [
        ("ReadOperationCount", ctypes.c_ulonglong),
        ("WriteOperationCount", ctypes.c_ulonglong),
        ("OtherOperationCount", ctypes.c_ulonglong),
        ("ReadTransferCount", ctypes.c_ulonglong),
        ("WriteTransferCount", ctypes.c_ulonglong),
        ("OtherTransferCount", ctypes.c_ulonglong),
    ]


class _JobBasicAccounting(ctypes.Structure):
    _fields_ = [
        ("TotalUserTime", ctypes.c_longlong),
        ("TotalKernelTime", ctypes.c_longlong),
        ("ThisPeriodTotalUserTime", ctypes.c_longlong),
        ("ThisPeriodTotalKernelTime", ctypes.c_longlong),
        ("TotalPageFaultCount", wintypes.DWORD),
        ("TotalProcesses", wintypes.DWORD),
        ("ActiveProcesses", wintypes.DWORD),
        ("TotalTerminatedProcesses", wintypes.DWORD),
    ]


class _JobBasicAndIoAccounting(ctypes.Structure):
    _fields_ = [
        ("BasicInfo", _JobBasicAccounting),
        ("IoInfo", _IoCounters),
    ]


class _JobBasicLimit(ctypes.Structure):
    _fields_ = [
        ("PerProcessUserTimeLimit", ctypes.c_longlong),
        ("PerJobUserTimeLimit", ctypes.c_longlong),
        ("LimitFlags", wintypes.DWORD),
        ("MinimumWorkingSetSize", ctypes.c_size_t),
        ("MaximumWorkingSetSize", ctypes.c_size_t),
        ("ActiveProcessLimit", wintypes.DWORD),
        ("Affinity", ctypes.c_size_t),
        ("PriorityClass", wintypes.DWORD),
        ("SchedulingClass", wintypes.DWORD),
    ]


class _JobExtendedLimit(ctypes.Structure):
    _fields_ = [
        ("BasicLimitInformation", _JobBasicLimit),
        ("IoInfo", _IoCounters),
        ("ProcessMemoryLimit", ctypes.c_size_t),
        ("JobMemoryLimit", ctypes.c_size_t),
        ("PeakProcessMemoryUsed", ctypes.c_size_t),
        ("PeakJobMemoryUsed", ctypes.c_size_t),
    ]


def _windows_kernel32() -> Any:
    """Return kernel32 with pointer-width-safe Job Object signatures."""

    if os.name != "nt":
        raise _TreeAccountingError(
            "complete process-tree memory accounting is unavailable"
        )
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateJobObjectW.argtypes = (ctypes.c_void_p, wintypes.LPCWSTR)
    kernel32.CreateJobObjectW.restype = wintypes.HANDLE
    kernel32.SetInformationJobObject.argtypes = (
        wintypes.HANDLE,
        ctypes.c_int,
        ctypes.c_void_p,
        wintypes.DWORD,
    )
    kernel32.SetInformationJobObject.restype = wintypes.BOOL
    kernel32.AssignProcessToJobObject.argtypes = (
        wintypes.HANDLE,
        wintypes.HANDLE,
    )
    kernel32.AssignProcessToJobObject.restype = wintypes.BOOL
    kernel32.QueryInformationJobObject.argtypes = (
        wintypes.HANDLE,
        ctypes.c_int,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
    )
    kernel32.QueryInformationJobObject.restype = wintypes.BOOL
    kernel32.TerminateJobObject.argtypes = (wintypes.HANDLE, wintypes.UINT)
    kernel32.TerminateJobObject.restype = wintypes.BOOL
    kernel32.TerminateProcess.argtypes = (wintypes.HANDLE, wintypes.UINT)
    kernel32.TerminateProcess.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
    kernel32.CloseHandle.restype = wintypes.BOOL
    return kernel32


class _WindowsJobTree:
    """Kill-on-close Windows Job Object covering the complete child tree."""

    def __init__(
        self,
        process: subprocess.Popen[bytes],
        memory_limit_bytes: int,
    ) -> None:
        kernel32 = _windows_kernel32()
        handle = kernel32.CreateJobObjectW(None, None)
        if not handle:
            raise _TreeAccountingError("CreateJobObjectW failed")
        self._kernel32 = kernel32
        self._handle = handle
        self._closed = False
        try:
            limits = _JobExtendedLimit()
            limits.BasicLimitInformation.LimitFlags = (
                JOB_OBJECT_LIMIT_JOB_MEMORY
                | JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            )
            limits.JobMemoryLimit = int(memory_limit_bytes)
            if not kernel32.SetInformationJobObject(
                handle,
                JOB_OBJECT_EXTENDED_LIMIT_INFORMATION,
                ctypes.byref(limits),
                ctypes.sizeof(limits),
            ):
                raise _TreeAccountingError(
                    "SetInformationJobObject failed for the tree memory limit"
                )
            raw_process_handle = getattr(process, "_handle", None)
            if raw_process_handle is None:
                raise _TreeAccountingError("child process handle is unavailable")
            process_handle = wintypes.HANDLE(int(raw_process_handle))
            if not kernel32.AssignProcessToJobObject(handle, process_handle):
                raise _TreeAccountingError("AssignProcessToJobObject failed")
            # Both queries are mandatory.  A system on which either query is
            # unavailable is not allowed to claim the registered tree cap.
            self.sample()
        except BaseException:
            self.close()
            raise

    def sample(self) -> tuple[int, int]:
        accounting = _JobBasicAndIoAccounting()
        returned = wintypes.DWORD()
        if not self._kernel32.QueryInformationJobObject(
            self._handle,
            JOB_OBJECT_BASIC_AND_IO_ACCOUNTING_INFORMATION,
            ctypes.byref(accounting),
            ctypes.sizeof(accounting),
            ctypes.byref(returned),
        ):
            raise _TreeAccountingError("job active-process query failed")
        limits = _JobExtendedLimit()
        if not self._kernel32.QueryInformationJobObject(
            self._handle,
            JOB_OBJECT_EXTENDED_LIMIT_INFORMATION,
            ctypes.byref(limits),
            ctypes.sizeof(limits),
            ctypes.byref(returned),
        ):
            raise _TreeAccountingError("job memory query failed")
        return (
            int(limits.PeakJobMemoryUsed),
            int(accounting.BasicInfo.ActiveProcesses),
        )

    def terminate(self) -> bool:
        return bool(self._kernel32.TerminateJobObject(self._handle, 1))

    def close(self) -> None:
        if not self._closed:
            self._closed = True
            if not self._kernel32.CloseHandle(self._handle):
                raise _TreeAccountingError("CloseHandle failed for the child job")


def _attach_tree_controller(
    process: subprocess.Popen[bytes], memory_limit_bytes: int
) -> _WindowsJobTree:
    if os.name != "nt":
        raise _TreeAccountingError(
            "complete process-tree memory accounting is unavailable"
        )
    return _WindowsJobTree(process, memory_limit_bytes)


def _terminate_root_now(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    if os.name == "nt" and getattr(process, "_handle", None) is not None:
        kernel32 = _windows_kernel32()
        kernel32.TerminateProcess(
            wintypes.HANDLE(int(getattr(process, "_handle"))), 1
        )
        return
    process.kill()


def _terminate_tree(
    process: subprocess.Popen[bytes],
    controller: Any | None,
    *,
    deadline_ns: int,
) -> None:
    """Request tree termination without an unbounded subprocess or wait."""

    if process.poll() is not None:
        return
    terminated = False
    if controller is not None:
        try:
            terminated = bool(controller.terminate())
        except (OSError, RuntimeError):
            terminated = False
    remaining = max(0.0, (deadline_ns - time.monotonic_ns()) / 1.0e9)
    if not terminated and os.name == "nt" and remaining > 0.0:
        try:
            subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=min(TASKKILL_TIMEOUT_SECONDS, remaining),
            )
        except (OSError, subprocess.SubprocessError, ValueError):
            pass
    if process.poll() is None:
        try:
            _terminate_root_now(process)
        except (OSError, RuntimeError):
            pass
    remaining = max(0.0, (deadline_ns - time.monotonic_ns()) / 1.0e9)
    if remaining > 0.0:
        try:
            process.wait(timeout=min(PROCESS_WAIT_SECONDS, remaining))
        except (OSError, subprocess.SubprocessError):
            pass


def _child_environment(input_value: Mapping[str, Any]) -> dict[str, str]:
    environment = os.environ.copy()
    environment.update(THREAD_ENVIRONMENT)
    candidates = input_value["candidates"]
    pieces = [
        str((ROOT / "src").resolve()),
        str(Path(input_value["execution"]["target"]).resolve()),
        str(Path(candidates["ANYstructure"]["root"]).resolve()),
        str(Path(candidates["ANYintelligent"]["root"]).resolve()),
    ]
    existing = environment.get("PYTHONPATH")
    if existing:
        pieces.append(existing)
    environment["PYTHONPATH"] = os.pathsep.join(pieces)
    environment["PYTHONNOUSERSITE"] = "1"
    return environment


def _run_child(
    *,
    level: int,
    fraction: int,
    root: Path,
    environment: dict[str, str],
    timeout_seconds: float,
    deadline_ns: int,
    memory_limit_bytes: int,
) -> ProcessResult:
    directory = root / f"n{level}-{fraction}pct"
    directory.mkdir()
    started_ns = time.monotonic_ns()
    remaining_seconds = (deadline_ns - started_ns) / 1.0e9
    if remaining_seconds <= 0.0:
        return ProcessResult(
            level,
            fraction,
            "NOT_LAUNCHED_GLOBAL_LIMIT",
            -1,
            0,
            -1,
            started_ns,
            started_ns,
            directory.name,
        )
    hard_deadline_ns = min(
        int(deadline_ns),
        started_ns + int(float(timeout_seconds) * 1_000_000_000),
    )
    output = directory / "record.json"
    release = directory / "tree-accounting.release"
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--child",
        "--level",
        str(level),
        "--fraction",
        str(fraction),
        "--output",
        str(output),
    ]
    peak = -1
    child_elapsed_microseconds = -1
    record_byte_count = 0
    record_sha256 = ""
    status = "SPAWN_FAILED"
    returncode: int | None = None
    controller: Any | None = None
    process: subprocess.Popen[bytes] | None = None
    child_environment = dict(environment)
    child_environment.pop(TREE_RELEASE_ENVIRONMENT, None)
    if os.name == "nt":
        child_environment[TREE_RELEASE_ENVIRONMENT] = str(release.resolve())
    with (directory / "stdout.log").open("xb") as stdout, (
        directory / "stderr.log"
    ).open("xb") as stderr:
        creationflags = (
            int(getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))
            if os.name == "nt"
            else 0
        )
        try:
            process = subprocess.Popen(
                command,
                cwd=directory,
                env=child_environment,
                stdin=subprocess.DEVNULL,
                stdout=stdout,
                stderr=stderr,
                creationflags=creationflags,
            )
        except (OSError, subprocess.SubprocessError):
            process = None
            status = "SPAWN_FAILED"
        if process is not None:
            try:
                controller = _attach_tree_controller(
                    process, memory_limit_bytes
                )
            except (OSError, _TreeAccountingError):
                status = "MEMORY_ACCOUNTING_UNAVAILABLE"
                _terminate_tree(
                    process,
                    None,
                    deadline_ns=hard_deadline_ns,
                )
            else:
                try:
                    if os.name == "nt":
                        with release.open("xb") as stream:
                            stream.write(TREE_RELEASE_BYTES)
                except OSError:
                    status = "MEMORY_ACCOUNTING_UNAVAILABLE"
                    _terminate_tree(
                        process,
                        controller,
                        deadline_ns=hard_deadline_ns,
                    )
                else:
                    status = "RUNNING"
                    while True:
                        try:
                            tree_peak, active_processes = controller.sample()
                        except (OSError, _TreeAccountingError):
                            status = "MEMORY_ACCOUNTING_UNAVAILABLE"
                            _terminate_tree(
                                process,
                                controller,
                                deadline_ns=hard_deadline_ns,
                            )
                            break
                        peak = max(peak, int(tree_peak))
                        if tree_peak >= memory_limit_bytes:
                            status = "MEMORY_LIMIT"
                            _terminate_tree(
                                process,
                                controller,
                                deadline_ns=hard_deadline_ns,
                            )
                            break
                        returncode = process.poll()
                        if returncode is not None and active_processes == 0:
                            break
                        now_ns = time.monotonic_ns()
                        if now_ns >= hard_deadline_ns:
                            status = (
                                "GLOBAL_LIMIT"
                                if now_ns >= deadline_ns
                                else "TIMEOUT"
                            )
                            _terminate_tree(
                                process,
                                controller,
                                deadline_ns=hard_deadline_ns,
                            )
                            break
                        remaining = (hard_deadline_ns - now_ns) / 1.0e9
                        time.sleep(min(0.05, max(0.0, remaining)))
                    returncode = process.poll()
                    if status == "RUNNING":
                        if returncode == 0 and output.is_file():
                            try:
                                child, record_sha256, record_byte_count = _read_child(
                                    output,
                                    level=level,
                                    fraction=fraction,
                                )
                            except (OSError, SmokeError, TypeError, ValueError):
                                status = "MALFORMED_OUTPUT"
                                (
                                    record_byte_count,
                                    record_sha256,
                                ) = _rejected_record_identity(output)
                            else:
                                child_elapsed_microseconds = int(
                                    child["elapsed_microseconds"]
                                )
                                status = "COMPLETE"
                        else:
                            status = "FAILED"
            finally:
                if controller is not None:
                    try:
                        controller.close()
                    except (OSError, RuntimeError):
                        if status == "COMPLETE":
                            status = "MEMORY_ACCOUNTING_UNAVAILABLE"
        if process is not None and returncode is None:
            returncode = process.poll()
    ended_ns = time.monotonic_ns()
    if status != "COMPLETE":
        output.unlink(missing_ok=True)
    return ProcessResult(
        level=level,
        fraction=fraction,
        status=status,
        returncode=-1 if returncode is None else int(returncode),
        elapsed_ms=int((ended_ns - started_ns) / 1_000_000),
        peak_tree_memory_bytes=peak,
        started_ns=started_ns,
        ended_ns=ended_ns,
        directory=directory.name,
        child_elapsed_microseconds=child_elapsed_microseconds,
        record_byte_count=record_byte_count,
        record_sha256=record_sha256,
    )


def run_smoke(
    *,
    levels: Sequence[int],
    output_root: Path,
    workers: int,
    timeout_seconds: int,
    global_limit_seconds: int,
    memory_limit_gib: int,
) -> dict[str, Any]:
    if not 1 <= workers <= 3:
        raise SmokeError("workers must be between one and three")
    if not 1 <= timeout_seconds <= 600:
        raise SmokeError("per-child timeout must be between 1 and 600 seconds")
    if not 1 <= global_limit_seconds <= 1200:
        raise SmokeError("global limit must be between 1 and 1200 seconds")
    if not 1 <= memory_limit_gib <= 24:
        raise SmokeError("memory limit must be between 1 and 24 GiB")
    ordered_levels = tuple(int(value) for value in levels)
    if (
        not ordered_levels
        or len(set(ordered_levels)) != len(ordered_levels)
        or any(value not in ALLOWED_LEVELS for value in ordered_levels)
        or tuple(sorted(ordered_levels)) != ordered_levels
    ):
        raise SmokeError("levels must be an ordered subset of 20,40,80,160")
    output_root = output_root.resolve()
    if output_root.is_relative_to(ROOT.resolve()):
        raise SmokeError("smoke output must be outside the repository")
    output_root.mkdir(parents=True, exist_ok=False)
    environment = _child_environment(read_json(INPUT))
    started_ns = time.monotonic_ns()
    deadline_ns = started_ns + global_limit_seconds * 1_000_000_000
    results: list[ProcessResult] = []
    overlap: dict[str, bool] = {}
    launched: set[tuple[int, int]] = set()
    for level in ordered_levels:
        remaining = (deadline_ns - time.monotonic_ns()) / 1.0e9
        if remaining <= 0.0:
            break
        wave: list[ProcessResult] = []
        with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="s3-cold-smoke") as pool:
            futures = {
                pool.submit(
                    _run_child,
                    level=level,
                    fraction=fraction,
                    root=output_root,
                    environment=environment,
                    timeout_seconds=float(timeout_seconds),
                    deadline_ns=deadline_ns,
                    memory_limit_bytes=memory_limit_gib * (1 << 30),
                ): fraction
                for fraction in FRACTIONS
            }
            for future in as_completed(futures):
                result = future.result()
                wave.append(result)
                launched.add((level, result.fraction))
        results.extend(wave)
        overlap[f"N{level}"] = len(wave) < 2 or max(
            item.started_ns for item in wave
        ) < min(item.ended_ns for item in wave)
    for level in ordered_levels:
        for fraction in FRACTIONS:
            if (level, fraction) not in launched:
                now = time.monotonic_ns()
                results.append(
                    ProcessResult(
                        level,
                        fraction,
                        "NOT_LAUNCHED_GLOBAL_LIMIT",
                        -1,
                        0,
                        -1,
                        now,
                        now,
                        "",
                    )
                )
    results.sort(key=lambda item: (item.level, item.fraction))
    rows: list[dict[str, Any]] = []
    for item in results:
        rows.append(
            {
                "child_elapsed_microseconds": item.child_elapsed_microseconds,
                "directory": item.directory,
                "elapsed_ms": item.elapsed_ms,
                "fraction_percent": item.fraction,
                "level": item.level,
                # Windows Job Objects expose aggregate job memory, not an
                # aggregate working-set/RSS value.  Preserve the legacy field
                # without mislabelling the enforced measurement.
                "peak_rss_bytes": -1,
                "peak_tree_memory_bytes": item.peak_tree_memory_bytes,
                "record_byte_count": item.record_byte_count,
                "record_sha256": item.record_sha256,
                "returncode": item.returncode,
                "status": item.status,
            }
        )
    forecast = forecast_seconds(rows)
    partial_forecast = partial_forecast_lower_bound_seconds(rows)
    complete = all(row["status"] == "COMPLETE" for row in rows)
    value = {
        "automatic_retry": False,
        "classification_authority": False,
        "coordinator_sha256": sha256(Path(__file__).resolve().read_bytes()),
        "elapsed_ms": int((time.monotonic_ns() - started_ns) / 1_000_000),
        "formal_execution_authorized": False,
        "forecast_acceptance_seconds": 480,
        "forecast_complete": forecast is not None,
        "forecast_seconds": forecast,
        "global_limit_seconds": global_limit_seconds,
        "contract_sha256": sha256(CONTRACT.read_bytes()),
        "input_sha256": sha256(INPUT.read_bytes()),
        "levels": list(ordered_levels),
        "manifest_sha256": sha256(MANIFEST.read_bytes()),
        "memory_accounting_metric": "WINDOWS_JOB_PEAK_MEMORY_USED",
        "memory_limit_gib_per_child": memory_limit_gib,
        "memory_limit_scope": "COMPLETE_CHILD_PROCESS_TREE",
        "partial_forecast_exceeds_acceptance": partial_forecast > 480.0,
        "partial_forecast_lower_bound_seconds": partial_forecast,
        "per_child_timeout_seconds": timeout_seconds,
        "processes": rows,
        "program_sha256": sha256(PROGRAM.read_bytes()),
        "production_restriction": PRODUCTION_RESTRICTION,
        "schema": SCHEMA,
        "terminal": NONCLASSIFYING_TERMINAL if complete else BLOCKED_TERMINAL,
        "worker_overlap": overlap,
        "workers": workers,
    }
    write_exclusive(output_root / "summary.json", value)
    return value


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--child", action="store_true")
    parser.add_argument("--level", type=int)
    parser.add_argument("--fraction", type=int)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--levels", nargs="+", type=int, default=[20, 40])
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--timeout-seconds", type=int, default=120)
    parser.add_argument("--global-limit-seconds", type=int, default=600)
    parser.add_argument("--memory-limit-gib", type=int, default=24)
    args = parser.parse_args(argv)
    try:
        if args.child:
            if (
                args.level not in ALLOWED_LEVELS
                or args.fraction not in FRACTIONS
                or args.output is None
            ):
                raise SmokeError("child requires a registered level, fraction, and output")
            _child(int(args.level), int(args.fraction), args.output)
            return 0
        if args.output_root is None:
            raise SmokeError("coordinator requires --output-root")
        value = run_smoke(
            levels=args.levels,
            output_root=args.output_root,
            workers=args.workers,
            timeout_seconds=args.timeout_seconds,
            global_limit_seconds=args.global_limit_seconds,
            memory_limit_gib=args.memory_limit_gib,
        )
        print(json.dumps(value, allow_nan=False, sort_keys=True))
        return 0 if value["terminal"] == NONCLASSIFYING_TERMINAL else 2
    except (OSError, SmokeError, subprocess.SubprocessError) as exc:
        print(f"cold-path smoke blocked: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
