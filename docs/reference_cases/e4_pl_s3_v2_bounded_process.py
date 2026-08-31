"""Bounded, process-tree-safe execution for S3 V2 research waves.

This module is deliberately standard-library-only.  It is a process/evidence
guard, not part of the mechanics implementation.  A logical qualification
cycle is assembled from multiple invocations of :func:`run_wave`; no one
invocation may enqueue a second wave or exceed thirty minutes.
"""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import math
import os
import signal
import stat
import subprocess
import sys
import threading
import time
from ctypes import wintypes
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence


MANIFEST_SCHEMA = "anysolver.e4-pl-s3-v2-bounded-wave-manifest-v1"
RESULT_SCHEMA = "anysolver.e4-pl-s3-v2-bounded-wave-result-v1"
PROGRESS_SCHEMA = "anysolver.e4-pl-s3-v2-worker-progress-v1"
REQUIRED_PROGRESS_PHASES = (
    "INITIALIZATION",
    "AUTHORITY_COMPLETE",
    "CASE_OR_REFINEMENT_OR_STATION",
    "STAGING",
    "VALIDATION",
    "COMPLETION",
)
MAX_WORKERS = 3
MAX_CONCURRENT_WORKERS = 2
WAVE_WALL_SECONDS = 1_800
MAX_WORKER_WALL_SECONDS = 1_500
INACTIVITY_SECONDS = 300
TERMINATION_RESERVE_SECONDS = 60
EVIDENCE_RESERVE_SECONDS = 120
JOB_MEMORY_LIMIT_BYTES = 24 * (1 << 30)
OS_HEADROOM_BYTES = 16 * (1 << 30)
MAX_PROGRESS_BYTES = 8 * (1 << 20)
POLL_SECONDS = 0.5
THREAD_ENVIRONMENT = {
    "BLIS_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
    "NUMBA_NUM_THREADS": "1",
    "NUMEXPR_NUM_THREADS": "1",
    "OMP_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "TBB_NUM_THREADS": "1",
}

LANE_WALL_LIMITS = {
    "authority": 300,
    "static": 300,
    "aggregation": 300,
    "package": 600,
    "flat-proof": 900,
    "local-proof": 900,
    "mixed": 1_200,
    "curved": 1_200,
    "recovery": 1_200,
    "nonlinear": 1_500,
    "performance": 1_500,
    "qv10": 1_500,
}


class BoundedProcessError(RuntimeError):
    """Raised when a wave cannot produce valid process evidence."""


def _reject_constant(value: str) -> None:
    raise BoundedProcessError(f"non-finite JSON constant is forbidden: {value}")


def _reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise BoundedProcessError(f"duplicate JSON key is forbidden: {key}")
        result[key] = value
    return result


def strict_json_load(path: Path) -> Any:
    """Load UTF-8 JSON while rejecting duplicates and non-finite numbers."""

    try:
        payload = path.read_bytes()
    except (OSError, UnicodeError) as exc:
        raise BoundedProcessError(f"cannot read JSON {path}: {exc}") from exc
    return strict_json_bytes(payload, str(path))


def strict_json_bytes(payload: bytes, location: str) -> Any:
    """Decode strict UTF-8 JSON bytes without accepting duplicate/nonfinite data."""

    try:
        text = payload.decode("utf-8")
    except UnicodeError as exc:
        raise BoundedProcessError(f"cannot decode JSON {location}: {exc}") from exc
    try:
        return json.loads(
            text,
            object_pairs_hook=_reject_duplicate_pairs,
            parse_constant=_reject_constant,
        )
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        if isinstance(exc, BoundedProcessError):
            raise
        raise BoundedProcessError(f"invalid JSON {location}: {exc}") from exc


def canonical_json_bytes(value: Any) -> bytes:
    """Serialize deterministic canonical JSON after a finite-value walk."""

    def visit(item: Any, location: str) -> None:
        if item is None or isinstance(item, (bool, str, int)):
            return
        if isinstance(item, float):
            if not math.isfinite(item):
                raise BoundedProcessError(f"non-finite number at {location}")
            return
        if isinstance(item, list):
            for index, member in enumerate(item):
                visit(member, f"{location}[{index}]")
            return
        if isinstance(item, dict):
            for key, member in item.items():
                if not isinstance(key, str):
                    raise BoundedProcessError(f"non-string key at {location}")
                visit(member, f"{location}.{key}")
            return
        raise BoundedProcessError(
            f"unsupported canonical JSON type at {location}: {type(item).__name__}"
        )

    visit(value, "$")
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        + "\n"
    ).encode("ascii")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest().upper()


def _require_exact_keys(
    value: Any, keys: set[str], location: str
) -> Mapping[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        actual = sorted(value) if isinstance(value, dict) else type(value).__name__
        raise BoundedProcessError(
            f"{location} keys differ: expected={sorted(keys)} actual={actual}"
        )
    return value


def _require_plain_string(value: Any, location: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise BoundedProcessError(f"{location} must be a nonempty trimmed string")
    return value


def _require_sha256(value: Any, location: str) -> str:
    made = _require_plain_string(value, location)
    if len(made) != 64 or made != made.upper():
        raise BoundedProcessError(f"{location} must be an uppercase SHA-256")
    try:
        int(made, 16)
    except ValueError as exc:
        raise BoundedProcessError(f"{location} must be an uppercase SHA-256") from exc
    return made


def _require_absolute_path(value: Any, location: str) -> Path:
    made = Path(_require_plain_string(value, location))
    if not made.is_absolute():
        raise BoundedProcessError(f"{location} must be absolute")
    return made


@dataclass(frozen=True)
class InputBinding:
    path: Path
    sha256: str


@dataclass(frozen=True)
class WorkerSpec:
    assignment_id: str
    assignment_sha256: str
    command: tuple[str, ...]
    cwd: Path
    expected_record_count: int
    expected_selector: str
    input_hashes: tuple[InputBinding, ...]
    plan_path: Path
    plan_sha256: str
    progress_path: Path
    program_path: Path
    program_sha256: str
    scientific_path: Path
    scientific_schema: str
    stdout_path: Path
    stderr_path: Path
    wall_seconds: int


@dataclass
class _RunningWorker:
    spec: WorkerSpec
    process: subprocess.Popen[bytes]
    job: "_ProcessJob"
    stdout_stream: Any
    stderr_stream: Any
    started: float
    last_activity: float
    last_cpu_100ns: int = 0
    last_progress_sequence: int = -1
    status: str = "RUNNING"
    termination_proven: bool = False
    slot_released: bool = False


def validate_manifest(value: Any) -> tuple[str, str, Path, tuple[WorkerSpec, ...]]:
    manifest = _require_exact_keys(
        value,
        {"schema", "wave_id", "lane", "output_root", "workers"},
        "$",
    )
    if manifest["schema"] != MANIFEST_SCHEMA:
        raise BoundedProcessError("wave manifest schema mismatch")
    wave_id = _require_plain_string(manifest["wave_id"], "$.wave_id")
    lane = _require_plain_string(manifest["lane"], "$.lane")
    if lane not in LANE_WALL_LIMITS:
        raise BoundedProcessError(f"unsupported bounded lane: {lane}")
    root = _require_absolute_path(manifest["output_root"], "$.output_root").resolve()
    raw_workers = manifest["workers"]
    if not isinstance(raw_workers, list) or not 1 <= len(raw_workers) <= MAX_WORKERS:
        raise BoundedProcessError("wave must contain one to three workers")
    workers: list[WorkerSpec] = []
    seen: set[str] = set()
    seen_output_paths: set[Path] = set()
    for index, raw in enumerate(raw_workers):
        location = f"$.workers[{index}]"
        member = _require_exact_keys(
            raw,
            {
                "assignment_id",
                "assignment_sha256",
                "command",
                "cwd",
                "expected_record_count",
                "expected_selector",
                "input_hashes",
                "plan_path",
                "plan_sha256",
                "progress_path",
                "program_path",
                "program_sha256",
                "scientific_path",
                "scientific_schema",
                "stdout_path",
                "stderr_path",
                "wall_seconds",
            },
            location,
        )
        assignment_id = _require_plain_string(
            member["assignment_id"], f"{location}.assignment_id"
        )
        if assignment_id in seen:
            raise BoundedProcessError(f"duplicate assignment ID: {assignment_id}")
        seen.add(assignment_id)
        assignment_sha256 = _require_sha256(
            member["assignment_sha256"], f"{location}.assignment_sha256"
        )
        command = member["command"]
        if (
            not isinstance(command, list)
            or not command
            or any(not isinstance(part, str) or not part for part in command)
        ):
            raise BoundedProcessError(f"{location}.command is invalid")
        wall = member["wall_seconds"]
        if (
            isinstance(wall, bool)
            or not isinstance(wall, int)
            or wall <= 0
            or wall > LANE_WALL_LIMITS[lane]
            or wall > MAX_WORKER_WALL_SECONDS
        ):
            raise BoundedProcessError(f"{location}.wall_seconds exceeds lane policy")
        cwd = _require_absolute_path(member["cwd"], f"{location}.cwd").resolve()
        expected_record_count = member["expected_record_count"]
        if (
            isinstance(expected_record_count, bool)
            or not isinstance(expected_record_count, int)
            or expected_record_count <= 0
        ):
            raise BoundedProcessError(
                f"{location}.expected_record_count must be a positive integer"
            )
        expected_selector = _require_plain_string(
            member["expected_selector"], f"{location}.expected_selector"
        )
        program = _require_absolute_path(
            member["program_path"], f"{location}.program_path"
        ).resolve()
        program_sha256 = _require_sha256(
            member["program_sha256"], f"{location}.program_sha256"
        )
        if str(program) not in command:
            raise BoundedProcessError(f"{location}.program_path is absent from command")
        plan = _require_absolute_path(
            member["plan_path"], f"{location}.plan_path"
        ).resolve()
        plan_sha256 = _require_sha256(
            member["plan_sha256"], f"{location}.plan_sha256"
        )
        raw_input_hashes = member["input_hashes"]
        if not isinstance(raw_input_hashes, list) or not raw_input_hashes:
            raise BoundedProcessError(f"{location}.input_hashes must be a nonempty list")
        input_hashes: list[InputBinding] = []
        previous_input_path = ""
        for binding_index, raw_binding in enumerate(raw_input_hashes):
            binding_location = f"{location}.input_hashes[{binding_index}]"
            binding = _require_exact_keys(
                raw_binding, {"path", "sha256"}, binding_location
            )
            binding_path = _require_absolute_path(
                binding["path"], f"{binding_location}.path"
            ).resolve()
            binding_path_text = str(binding_path)
            if binding_path_text <= previous_input_path:
                raise BoundedProcessError(
                    f"{location}.input_hashes must be strictly path-sorted and unique"
                )
            previous_input_path = binding_path_text
            input_hashes.append(
                InputBinding(
                    path=binding_path,
                    sha256=_require_sha256(
                        binding["sha256"], f"{binding_location}.sha256"
                    ),
                )
            )
        progress = _require_absolute_path(
            member["progress_path"], f"{location}.progress_path"
        ).resolve()
        scientific = _require_absolute_path(
            member["scientific_path"], f"{location}.scientific_path"
        ).resolve()
        scientific_schema = _require_plain_string(
            member["scientific_schema"], f"{location}.scientific_schema"
        )
        stdout = _require_absolute_path(
            member["stdout_path"], f"{location}.stdout_path"
        ).resolve()
        stderr = _require_absolute_path(
            member["stderr_path"], f"{location}.stderr_path"
        ).resolve()
        try:
            for path in (progress, scientific, stdout, stderr):
                path.relative_to(root)
        except ValueError as exc:
            raise BoundedProcessError(
                f"{location} output path escapes output_root"
            ) from exc
        for path in (progress, scientific, stdout, stderr):
            if path in seen_output_paths:
                raise BoundedProcessError(f"duplicate worker output path: {path}")
            seen_output_paths.add(path)
        workers.append(
            WorkerSpec(
                assignment_id=assignment_id,
                assignment_sha256=assignment_sha256,
                command=tuple(command),
                cwd=cwd,
                expected_record_count=expected_record_count,
                expected_selector=expected_selector,
                input_hashes=tuple(input_hashes),
                plan_path=plan,
                plan_sha256=plan_sha256,
                progress_path=progress,
                program_path=program,
                program_sha256=program_sha256,
                scientific_path=scientific,
                scientific_schema=scientific_schema,
                stdout_path=stdout,
                stderr_path=stderr,
                wall_seconds=wall,
            )
        )
    return wave_id, lane, root, tuple(workers)


class _ProcessJob:
    """One complete process tree with queryable CPU/memory accounting."""

    def __init__(self, memory_limit_bytes: int) -> None:
        self._handle: int | None = None
        self._process: subprocess.Popen[bytes] | None = None
        self._memory_limit = memory_limit_bytes

    def launch(
        self,
        command: Sequence[str],
        *,
        cwd: Path,
        env: Mapping[str, str],
        stdout: Any,
        stderr: Any,
    ) -> subprocess.Popen[bytes]:
        if os.name == "nt":
            return self._launch_windows(command, cwd, env, stdout, stderr)
        process = subprocess.Popen(
            list(command),
            cwd=str(cwd),
            env=dict(env),
            stdout=stdout,
            stderr=stderr,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
        )
        self._process = process
        return process

    def _launch_windows(
        self,
        command: Sequence[str],
        cwd: Path,
        env: Mapping[str, str],
        stdout: Any,
        stderr: Any,
    ) -> subprocess.Popen[bytes]:
        handle = _create_windows_job(self._memory_limit)
        process: subprocess.Popen[bytes] | None = None
        try:
            process = subprocess.Popen(
                list(command),
                cwd=str(cwd),
                env=dict(env),
                stdout=stdout,
                stderr=stderr,
                stdin=subprocess.DEVNULL,
                creationflags=0x00000004,  # CREATE_SUSPENDED
            )
            _assign_windows_process(handle, int(process._handle))
            _resume_windows_process(int(process._handle))
        except BaseException:
            if process is not None:
                try:
                    process.kill()
                    process.wait(timeout=2)
                except BaseException:
                    pass
            _close_windows_handle(handle)
            raise
        self._handle = handle
        self._process = process
        return process

    def accounting(self) -> tuple[int, int, int]:
        """Return ``(cpu_100ns, active_processes, peak_tree_bytes)``."""

        if os.name == "nt":
            if self._handle is None:
                return 0, 0, 0
            return _query_windows_job(self._handle)
        process = self._process
        active = int(process is not None and process.poll() is None)
        return 0, active, 0

    def terminate(self, exit_code: int = 124) -> bool:
        if os.name == "nt":
            if self._handle is None:
                return True
            _terminate_windows_job(self._handle, exit_code)
            deadline = time.monotonic() + 15.0
            while time.monotonic() < deadline:
                _, active, _ = self.accounting()
                if active == 0:
                    return True
                time.sleep(0.05)
            return False
        process = self._process
        if process is None or process.poll() is not None:
            return True
        try:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=15)
            return True
        except (OSError, subprocess.TimeoutExpired):
            return False

    def close(self) -> None:
        if self._handle is not None:
            _close_windows_handle(self._handle)
            self._handle = None


class _BasicLimitInformation(ctypes.Structure):
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


class _IoCounters(ctypes.Structure):
    _fields_ = [
        ("ReadOperationCount", ctypes.c_ulonglong),
        ("WriteOperationCount", ctypes.c_ulonglong),
        ("OtherOperationCount", ctypes.c_ulonglong),
        ("ReadTransferCount", ctypes.c_ulonglong),
        ("WriteTransferCount", ctypes.c_ulonglong),
        ("OtherTransferCount", ctypes.c_ulonglong),
    ]


class _ExtendedLimitInformation(ctypes.Structure):
    _fields_ = [
        ("BasicLimitInformation", _BasicLimitInformation),
        ("IoInfo", _IoCounters),
        ("ProcessMemoryLimit", ctypes.c_size_t),
        ("JobMemoryLimit", ctypes.c_size_t),
        ("PeakProcessMemoryUsed", ctypes.c_size_t),
        ("PeakJobMemoryUsed", ctypes.c_size_t),
    ]


class _BasicAccountingInformation(ctypes.Structure):
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


def _kernel32() -> Any:
    return ctypes.WinDLL("kernel32", use_last_error=True)


def _create_windows_job(memory_limit_bytes: int) -> int:
    kernel32 = _kernel32()
    kernel32.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
    kernel32.CreateJobObjectW.restype = wintypes.HANDLE
    kernel32.SetInformationJobObject.argtypes = [
        wintypes.HANDLE,
        ctypes.c_int,
        ctypes.c_void_p,
        wintypes.DWORD,
    ]
    kernel32.SetInformationJobObject.restype = wintypes.BOOL
    handle = kernel32.CreateJobObjectW(None, None)
    if not handle:
        raise OSError(ctypes.get_last_error(), "CreateJobObjectW failed")
    information = _ExtendedLimitInformation()
    information.BasicLimitInformation.LimitFlags = 0x00002000 | 0x00000200
    information.JobMemoryLimit = memory_limit_bytes
    if not kernel32.SetInformationJobObject(
        handle, 9, ctypes.byref(information), ctypes.sizeof(information)
    ):
        error = ctypes.get_last_error()
        kernel32.CloseHandle(handle)
        raise OSError(error, "SetInformationJobObject failed")
    return int(handle)


def _assign_windows_process(job_handle: int, process_handle: int) -> None:
    kernel32 = _kernel32()
    kernel32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    kernel32.AssignProcessToJobObject.restype = wintypes.BOOL
    if not kernel32.AssignProcessToJobObject(job_handle, process_handle):
        raise OSError(ctypes.get_last_error(), "AssignProcessToJobObject failed")


def _resume_windows_process(process_handle: int) -> None:
    ntdll = ctypes.WinDLL("ntdll")
    ntdll.NtResumeProcess.argtypes = [wintypes.HANDLE]
    ntdll.NtResumeProcess.restype = ctypes.c_long
    status = int(ntdll.NtResumeProcess(process_handle))
    if status != 0:
        raise OSError(status, "NtResumeProcess failed")


def _query_windows_job(job_handle: int) -> tuple[int, int, int]:
    kernel32 = _kernel32()
    kernel32.QueryInformationJobObject.argtypes = [
        wintypes.HANDLE,
        ctypes.c_int,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
    ]
    kernel32.QueryInformationJobObject.restype = wintypes.BOOL
    accounting = _BasicAccountingInformation()
    if not kernel32.QueryInformationJobObject(
        job_handle, 1, ctypes.byref(accounting), ctypes.sizeof(accounting), None
    ):
        raise OSError(ctypes.get_last_error(), "job accounting query failed")
    limits = _ExtendedLimitInformation()
    if not kernel32.QueryInformationJobObject(
        job_handle, 9, ctypes.byref(limits), ctypes.sizeof(limits), None
    ):
        raise OSError(ctypes.get_last_error(), "job memory query failed")
    cpu = int(accounting.TotalUserTime + accounting.TotalKernelTime)
    return cpu, int(accounting.ActiveProcesses), int(limits.PeakJobMemoryUsed)


def _terminate_windows_job(job_handle: int, exit_code: int) -> None:
    kernel32 = _kernel32()
    kernel32.TerminateJobObject.argtypes = [wintypes.HANDLE, wintypes.UINT]
    kernel32.TerminateJobObject.restype = wintypes.BOOL
    if not kernel32.TerminateJobObject(job_handle, exit_code):
        raise OSError(ctypes.get_last_error(), "TerminateJobObject failed")


def _close_windows_handle(handle: int) -> None:
    kernel32 = _kernel32()
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL
    if not kernel32.CloseHandle(handle):
        raise OSError(ctypes.get_last_error(), "CloseHandle failed")


def available_physical_memory_bytes() -> int:
    if os.name != "nt":
        if hasattr(os, "sysconf"):
            return int(os.sysconf("SC_AVPHYS_PAGES") * os.sysconf("SC_PAGE_SIZE"))
        return 1 << 60

    class MemoryStatusEx(ctypes.Structure):
        _fields_ = [
            ("dwLength", wintypes.DWORD),
            ("dwMemoryLoad", wintypes.DWORD),
            ("ullTotalPhys", ctypes.c_ulonglong),
            ("ullAvailPhys", ctypes.c_ulonglong),
            ("ullTotalPageFile", ctypes.c_ulonglong),
            ("ullAvailPageFile", ctypes.c_ulonglong),
            ("ullTotalVirtual", ctypes.c_ulonglong),
            ("ullAvailVirtual", ctypes.c_ulonglong),
            ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
        ]

    status = MemoryStatusEx()
    status.dwLength = ctypes.sizeof(status)
    kernel32 = _kernel32()
    kernel32.GlobalMemoryStatusEx.argtypes = [ctypes.POINTER(MemoryStatusEx)]
    kernel32.GlobalMemoryStatusEx.restype = wintypes.BOOL
    if not kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
        raise OSError(ctypes.get_last_error(), "GlobalMemoryStatusEx failed")
    return int(min(status.ullAvailPhys, status.ullAvailPageFile))


@dataclass(frozen=True)
class _ProgressState:
    sequence: int
    phases: tuple[str, ...]


def _progress_state(path: Path, assignment_id: str) -> _ProgressState:
    if not path.exists():
        return _ProgressState(-1, ())
    size = path.stat().st_size
    if size > MAX_PROGRESS_BYTES:
        raise BoundedProcessError("progress log exceeded the registered byte cap")
    sequence = -1
    phases: list[str] = []
    required_rank = {phase: index for index, phase in enumerate(REQUIRED_PROGRESS_PHASES)}
    last_required_rank = -1
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        raise BoundedProcessError(f"progress log cannot be read: {exc}") from exc
    for index, line in enumerate(lines):
        try:
            record = json.loads(
                line,
                object_pairs_hook=_reject_duplicate_pairs,
                parse_constant=_reject_constant,
            )
        except (json.JSONDecodeError, ValueError, TypeError) as exc:
            raise BoundedProcessError(
                f"progress line {index + 1} is invalid: {exc}"
            ) from exc
        made = _require_exact_keys(
            record,
            {"schema", "assignment_id", "sequence", "phase", "completed", "total"},
            f"progress[{index}]",
        )
        if made["schema"] != PROGRESS_SCHEMA or made["assignment_id"] != assignment_id:
            raise BoundedProcessError("progress identity mismatch")
        made_sequence = made["sequence"]
        completed = made["completed"]
        total = made["total"]
        if (
            isinstance(made_sequence, bool)
            or not isinstance(made_sequence, int)
            or made_sequence != sequence + 1
            or isinstance(completed, bool)
            or not isinstance(completed, int)
            or isinstance(total, bool)
            or not isinstance(total, int)
            or completed < 0
            or total < 0
            or completed > total
        ):
            raise BoundedProcessError("progress sequence/count is invalid")
        phase = _require_plain_string(made["phase"], f"progress[{index}].phase")
        if phase in required_rank:
            rank = required_rank[phase]
            if rank < last_required_rank:
                raise BoundedProcessError("required progress phases are out of order")
            last_required_rank = rank
        phases.append(phase)
        sequence = made_sequence
    return _ProgressState(sequence, tuple(phases))


def _progress_sequence(path: Path, assignment_id: str) -> int:
    """Return the latest valid sequence; partial logs are valid while running."""

    return _progress_state(path, assignment_id).sequence


def _require_complete_progress(path: Path, assignment_id: str) -> _ProgressState:
    state = _progress_state(path, assignment_id)
    present = set(state.phases)
    missing = [phase for phase in REQUIRED_PROGRESS_PHASES if phase not in present]
    if missing:
        raise BoundedProcessError(
            f"required progress phases are missing: {','.join(missing)}"
        )
    return state


def _regular_file_bytes(path: Path, location: str) -> bytes:
    try:
        information = path.lstat()
    except FileNotFoundError as exc:
        raise BoundedProcessError(f"{location} is missing: {path}") from exc
    except OSError as exc:
        raise BoundedProcessError(f"cannot inspect {location} {path}: {exc}") from exc
    if not stat.S_ISREG(information.st_mode):
        raise BoundedProcessError(f"{location} is not a regular file: {path}")
    file_attributes = getattr(information, "st_file_attributes", 0)
    reparse_attribute = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    if file_attributes & reparse_attribute:
        raise BoundedProcessError(f"{location} must not be a reparse point: {path}")
    try:
        return path.read_bytes()
    except OSError as exc:
        raise BoundedProcessError(f"cannot read {location} {path}: {exc}") from exc


@dataclass(frozen=True)
class _ScientificMetadata:
    byte_count: int
    record_count: int
    record_ids_sha256: str
    scientific_payload_sha256: str
    sha256: str
    terminal: str


def _scientific_metadata(spec: WorkerSpec) -> _ScientificMetadata:
    raw = _regular_file_bytes(spec.scientific_path, "scientific output")
    value = strict_json_bytes(raw, str(spec.scientific_path))
    envelope = _require_exact_keys(
        value,
        {
            "schema",
            "assignment_sha256",
            "plan_sha256",
            "selector",
            "record_count",
            "record_ids",
            "record_ids_sha256",
            "scientific_payload",
            "scientific_payload_sha256",
            "terminal",
        },
        "$scientific",
    )
    if envelope["schema"] != spec.scientific_schema:
        raise BoundedProcessError("scientific output schema mismatch")
    if envelope["assignment_sha256"] != spec.assignment_sha256:
        raise BoundedProcessError("scientific assignment hash mismatch")
    if envelope["plan_sha256"] != spec.plan_sha256:
        raise BoundedProcessError("scientific plan hash mismatch")
    if envelope["selector"] != spec.expected_selector:
        raise BoundedProcessError("scientific selector mismatch")
    record_count = envelope["record_count"]
    if (
        isinstance(record_count, bool)
        or not isinstance(record_count, int)
        or record_count != spec.expected_record_count
    ):
        raise BoundedProcessError("scientific record count mismatch")
    record_ids = envelope["record_ids"]
    if (
        not isinstance(record_ids, list)
        or len(record_ids) != record_count
        or any(
            not isinstance(record_id, str)
            or not record_id
            or record_id != record_id.strip()
            for record_id in record_ids
        )
        or len(set(record_ids)) != len(record_ids)
    ):
        raise BoundedProcessError("scientific record IDs are incomplete or duplicated")
    record_ids_sha256 = _require_sha256(
        envelope["record_ids_sha256"], "$scientific.record_ids_sha256"
    )
    if record_ids_sha256 != sha256_bytes(canonical_json_bytes(record_ids)):
        raise BoundedProcessError("scientific record IDs hash mismatch")
    scientific_payload_sha256 = _require_sha256(
        envelope["scientific_payload_sha256"],
        "$scientific.scientific_payload_sha256",
    )
    if scientific_payload_sha256 != sha256_bytes(
        canonical_json_bytes(envelope["scientific_payload"])
    ):
        raise BoundedProcessError("scientific payload hash mismatch")
    if envelope["terminal"] != "ACCEPTED_FOR_AGGREGATION":
        raise BoundedProcessError("scientific terminal is not accepted for aggregation")
    if raw != canonical_json_bytes(value):
        raise BoundedProcessError("scientific output is not canonical JSON")
    return _ScientificMetadata(
        byte_count=len(raw),
        record_count=record_count,
        record_ids_sha256=record_ids_sha256,
        scientific_payload_sha256=scientific_payload_sha256,
        sha256=sha256_bytes(raw),
        terminal="ACCEPTED_FOR_AGGREGATION",
    )


def _verify_worker_bindings(spec: WorkerSpec) -> None:
    program_raw = _regular_file_bytes(spec.program_path, "registered program")
    if sha256_bytes(program_raw) != spec.program_sha256:
        raise BoundedProcessError("registered program hash mismatch")
    plan_raw = _regular_file_bytes(spec.plan_path, "registered plan")
    if sha256_bytes(plan_raw) != spec.plan_sha256:
        raise BoundedProcessError("registered plan hash mismatch")
    plan = strict_json_bytes(plan_raw, str(spec.plan_path))
    if plan_raw != canonical_json_bytes(plan):
        raise BoundedProcessError("registered plan is not canonical JSON")
    for binding in spec.input_hashes:
        raw = _regular_file_bytes(binding.path, "registered input")
        if sha256_bytes(raw) != binding.sha256:
            raise BoundedProcessError(f"registered input hash mismatch: {binding.path}")


def _path_lexists(path: Path) -> bool:
    try:
        path.lstat()
    except FileNotFoundError:
        return False
    except OSError as exc:
        raise BoundedProcessError(f"cannot inspect exclusive path {path}: {exc}") from exc
    return True


def _exclusive_stream(path: Path) -> Any:
    path.parent.mkdir(parents=True, exist_ok=True)
    return path.open("xb")


def _publish_exclusive(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.pending")
    with temporary.open("xb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    try:
        os.link(temporary, path)
    except BaseException:
        try:
            temporary.unlink()
        except OSError:
            pass
        raise
    temporary.unlink()


def _environment() -> dict[str, str]:
    made = dict(os.environ)
    made.update(THREAD_ENVIRONMENT)
    made["PYTHONHASHSEED"] = "0"
    return made


def _formal_platform_name() -> str:
    return os.name


def _require_formal_process_control() -> None:
    if _formal_platform_name() != "nt":
        raise BoundedProcessError(
            "formal bounded execution requires Windows Job Object tree containment"
        )


def _preflight_worker_specs(worker_specs: Sequence[WorkerSpec]) -> None:
    for spec in worker_specs:
        for path in (
            spec.progress_path,
            spec.scientific_path,
            spec.stdout_path,
            spec.stderr_path,
        ):
            if _path_lexists(path):
                raise BoundedProcessError(f"exclusive worker output exists: {path}")
        if not spec.cwd.is_dir():
            raise BoundedProcessError(f"worker cwd is not a directory: {spec.cwd}")
        _verify_worker_bindings(spec)


def _required_wave_memory_bytes(registered_worker_count: int) -> int:
    """Return the admission floor for the workers that can run concurrently."""

    if (
        isinstance(registered_worker_count, bool)
        or not isinstance(registered_worker_count, int)
        or registered_worker_count <= 0
        or registered_worker_count > MAX_WORKERS
    ):
        raise BoundedProcessError("registered worker count is outside wave policy")
    concurrent = min(registered_worker_count, MAX_CONCURRENT_WORKERS)
    return concurrent * JOB_MEMORY_LIMIT_BYTES + OS_HEADROOM_BYTES


def _terminate_and_release_slot(running: _RunningWorker) -> bool:
    """Release a worker slot only when whole-tree termination is proven."""

    try:
        proven = bool(running.job.terminate())
    except BaseException:
        proven = False
    running.termination_proven = proven
    running.slot_released = proven
    return proven


def _record_root_exit_if_tree_drained(
    running: _RunningWorker, active_processes: int
) -> bool:
    """Record root completion only after the Job reports no live descendants."""

    if active_processes != 0:
        return False
    running.status = "COMPLETED" if running.process.returncode == 0 else "FAILED"
    running.termination_proven = True
    running.slot_released = True
    return True


def _queued_launch_is_blocked(active: Sequence[_RunningWorker]) -> bool:
    """A failed termination proof forbids every later queued launch."""

    return any(
        running.status != "RUNNING" and not running.slot_released
        for running in active
    )


def run_wave(manifest_path: Path, result_path: Path) -> dict[str, Any]:
    """Execute exactly one registered bounded wave and publish its result."""

    manifest_bytes = manifest_path.read_bytes()
    manifest = strict_json_load(manifest_path)
    if manifest_bytes != canonical_json_bytes(manifest):
        raise BoundedProcessError("wave manifest is not canonical JSON")
    wave_id, lane, output_root, worker_specs = validate_manifest(manifest)
    if not result_path.is_absolute():
        raise BoundedProcessError("canonical wave result path must be absolute")
    result_path = result_path.resolve()
    try:
        result_path.relative_to(output_root)
    except ValueError as exc:
        raise BoundedProcessError("canonical wave result path escapes output_root") from exc
    registered_worker_outputs = {
        path
        for spec in worker_specs
        for path in (
            spec.progress_path,
            spec.scientific_path,
            spec.stdout_path,
            spec.stderr_path,
        )
    }
    if result_path in registered_worker_outputs:
        raise BoundedProcessError("canonical result aliases a registered worker output")
    if _path_lexists(result_path):
        raise BoundedProcessError("canonical wave result already exists")
    _require_formal_process_control()
    _preflight_worker_specs(worker_specs)
    required_memory = _required_wave_memory_bytes(len(worker_specs))
    available = available_physical_memory_bytes()
    if available < required_memory:
        made = {
            "schema": RESULT_SCHEMA,
            "wave_id": wave_id,
            "lane": lane,
            "manifest_sha256": sha256_bytes(manifest_bytes),
            "terminal": "RESOURCE_DEFERRED",
            "workers": [],
        }
        _publish_exclusive(result_path, canonical_json_bytes(made))
        return made

    wave_started = time.monotonic()
    worker_deadline_limit = (
        wave_started
        + WAVE_WALL_SECONDS
        - TERMINATION_RESERVE_SECONDS
        - EVIDENCE_RESERVE_SECONDS
    )
    active: list[_RunningWorker] = []
    stop_watchdog = threading.Event()

    def hard_watchdog() -> None:
        if stop_watchdog.wait(
            max(
                0.0,
                wave_started + WAVE_WALL_SECONDS - TERMINATION_RESERVE_SECONDS - time.monotonic(),
            )
        ):
            return
        for running in tuple(active):
            try:
                running.job.terminate()
            except BaseException:
                pass
        os._exit(124)

    watchdog = threading.Thread(
        target=hard_watchdog, name="s3-v2-wave-hard-wall", daemon=True
    )
    watchdog.start()

    try:
        _preflight_worker_specs(worker_specs)

        next_worker_index = 0

        def launch_available_workers() -> None:
            nonlocal next_worker_index
            if _queued_launch_is_blocked(active):
                return
            occupied_slots = sum(not item.slot_released for item in active)
            while (
                next_worker_index < len(worker_specs)
                and occupied_slots < MAX_CONCURRENT_WORKERS
            ):
                spec = worker_specs[next_worker_index]
                # Recheck a queued assignment immediately before launch.  Earlier
                # assignments have already created registered outputs, so this
                # check is deliberately scoped to the next assignment only.
                _preflight_worker_specs((spec,))
                stdout_stream = _exclusive_stream(spec.stdout_path)
                try:
                    stderr_stream = _exclusive_stream(spec.stderr_path)
                except BaseException:
                    stdout_stream.close()
                    raise
                job = _ProcessJob(JOB_MEMORY_LIMIT_BYTES)
                started = time.monotonic()
                try:
                    process = job.launch(
                        spec.command,
                        cwd=spec.cwd,
                        env=_environment(),
                        stdout=stdout_stream,
                        stderr=stderr_stream,
                    )
                except BaseException:
                    stdout_stream.close()
                    stderr_stream.close()
                    job.close()
                    raise
                active.append(
                    _RunningWorker(
                        spec=spec,
                        process=process,
                        job=job,
                        stdout_stream=stdout_stream,
                        stderr_stream=stderr_stream,
                        started=started,
                        last_activity=started,
                    )
                )
                next_worker_index += 1
                occupied_slots += 1

        launch_available_workers()
        while (
            (
                next_worker_index < len(worker_specs)
                and not _queued_launch_is_blocked(active)
            )
            or any(item.status == "RUNNING" for item in active)
        ):
            now = time.monotonic()
            for running in active:
                if running.status != "RUNNING":
                    continue
                try:
                    cpu, active_processes, _ = running.job.accounting()
                    sequence = _progress_sequence(
                        running.spec.progress_path, running.spec.assignment_id
                    )
                except BaseException:
                    running.status = "MALFORMED_PROGRESS_OR_ACCOUNTING"
                    _terminate_and_release_slot(running)
                    continue
                if cpu > running.last_cpu_100ns or sequence > running.last_progress_sequence:
                    running.last_activity = now
                    running.last_cpu_100ns = max(running.last_cpu_100ns, cpu)
                    running.last_progress_sequence = max(
                        running.last_progress_sequence, sequence
                    )
                if running.process.poll() is not None:
                    if _record_root_exit_if_tree_drained(running, active_processes):
                        continue
                deadline = min(
                    running.started + running.spec.wall_seconds,
                    worker_deadline_limit,
                )
                if now >= deadline:
                    running.status = "TIMEOUT"
                    _terminate_and_release_slot(running)
                elif now - running.last_activity >= INACTIVITY_SECONDS:
                    running.status = "INACTIVE"
                    _terminate_and_release_slot(running)
            launch_available_workers()
            time.sleep(POLL_SECONDS)

        records: list[dict[str, Any]] = []
        for running in active:
            try:
                cpu, active_processes, peak_memory = running.job.accounting()
            except BaseException:
                cpu, active_processes, peak_memory = 0, -1, 0
                running.termination_proven = False
            returncode = running.process.poll()
            scientific_byte_count: int | None = None
            scientific_record_count: int | None = None
            scientific_record_ids_sha256: str | None = None
            scientific_payload_sha256: str | None = None
            scientific_sha256: str | None = None
            scientific_terminal: str | None = None
            bindings_valid = True
            try:
                _verify_worker_bindings(running.spec)
            except BoundedProcessError:
                bindings_valid = False
                running.status = "FROZEN_INPUT_MISMATCH"
            if running.status == "COMPLETED" and bindings_valid:
                try:
                    progress = _require_complete_progress(
                        running.spec.progress_path, running.spec.assignment_id
                    )
                    running.last_progress_sequence = progress.sequence
                    metadata = _scientific_metadata(running.spec)
                    scientific_byte_count = metadata.byte_count
                    scientific_record_count = metadata.record_count
                    scientific_record_ids_sha256 = metadata.record_ids_sha256
                    scientific_payload_sha256 = metadata.scientific_payload_sha256
                    scientific_sha256 = metadata.sha256
                    scientific_terminal = metadata.terminal
                except BoundedProcessError:
                    running.status = "MALFORMED_PROGRESS_OR_SCIENTIFIC_EVIDENCE"
                    try:
                        raw_scientific = _regular_file_bytes(
                            running.spec.scientific_path, "scientific output"
                        )
                    except BoundedProcessError:
                        pass
                    else:
                        scientific_byte_count = len(raw_scientific)
                        scientific_sha256 = sha256_bytes(raw_scientific)
            records.append(
                {
                    "assignment_id": running.spec.assignment_id,
                    "assignment_sha256": running.spec.assignment_sha256,
                    "status": running.status,
                    "returncode": returncode,
                    "termination_proven": bool(
                        running.termination_proven and active_processes in {0, -1}
                    ),
                    "last_progress_sequence": running.last_progress_sequence,
                    "cpu_100ns": cpu,
                    "peak_tree_memory_bytes": peak_memory,
                    "plan_sha256": running.spec.plan_sha256,
                    "program_sha256": running.spec.program_sha256,
                    "input_hashes": [
                        {"path": str(binding.path), "sha256": binding.sha256}
                        for binding in running.spec.input_hashes
                    ],
                    "scientific_byte_count": scientific_byte_count,
                    "scientific_payload_sha256": scientific_payload_sha256,
                    "scientific_record_count": scientific_record_count,
                    "scientific_record_ids_sha256": scientific_record_ids_sha256,
                    "scientific_schema": running.spec.scientific_schema,
                    "scientific_sha256": scientific_sha256,
                    "scientific_terminal": scientific_terminal,
                    "stdout_sha256": sha256_bytes(running.spec.stdout_path.read_bytes()),
                    "stderr_sha256": sha256_bytes(running.spec.stderr_path.read_bytes()),
                }
            )
        terminal = (
            "COMPLETED"
            if all(
                record["status"] == "COMPLETED" and record["termination_proven"]
                for record in records
            )
            else "BLOCKED_E4_PL_S3_V2_PROCESS_OR_EVIDENCE"
        )
        made = {
            "schema": RESULT_SCHEMA,
            "wave_id": wave_id,
            "lane": lane,
            "manifest_sha256": sha256_bytes(manifest_bytes),
            "terminal": terminal,
            "workers": records,
        }
        _publish_exclusive(result_path, canonical_json_bytes(made))
        return made
    finally:
        for running in active:
            if not running.slot_released:
                _terminate_and_release_slot(running)
            running.stdout_stream.close()
            running.stderr_stream.close()
            running.job.close()
        stop_watchdog.set()
        watchdog.join(timeout=1.0)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--result", type=Path)
    parser.add_argument("--validate-only", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.validate_only:
        raw = args.manifest.read_bytes()
        value = strict_json_bytes(raw, str(args.manifest))
        if raw != canonical_json_bytes(value):
            raise BoundedProcessError("wave manifest is not canonical JSON")
        validate_manifest(value)
        return 0
    if args.result is None:
        raise SystemExit("--result is required unless --validate-only is used")
    made = run_wave(args.manifest, args.result)
    return 0 if made["terminal"] in {"COMPLETED", "RESOURCE_DEFERRED"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
