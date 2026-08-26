"""Execute preregistered S3/Q4 burn-in commands and emit canonical manifests."""

from __future__ import annotations

import sys


if __name__ == "__main__" and not sys.flags.isolated:
    raise RuntimeError("process runner must be launched with Python isolated mode (-I)")

# The authority coordinator loads its validator from source and must never leave
# bytecode in the frozen worktree.  Child processes receive the matching
# PYTHONDONTWRITEBYTECODE setting from the hash-bound execution environment.
sys.dont_write_bytecode = True

import argparse
import datetime as dt
import os
from pathlib import Path
import re
import signal
import subprocess
import tempfile
import threading
import time
from typing import Any, Mapping


_RUNNER_PATH = Path(__file__).resolve(strict=True)
_FROZEN_ROOT = Path(r"C:\Github\ANYsolver\.perf2-worktrees\s3-e4-pl-final-freeze")
ROOT = _FROZEN_ROOT if __name__ == "__main__" else _RUNNER_PATH.parents[2]
_VALIDATOR_PATH = ROOT / "docs" / "reference_cases" / "e4_pl_s3_q4_burnin.py"
burnin: Any = None
PROCESS_RESULT_SCHEMA = "anysolver.e4-pl-s3-q4-process-result-v3"
LEDGER_SNAPSHOT_SCHEMA = "anysolver.e4-pl-s3-q4-resource-ledger-snapshot-v1"
PENDING_MANIFEST_SCHEMA = "anysolver.e4-pl-s3-q4-pending-process-manifest-v1"
MANAGER_RESERVATION_SCHEMA = "anysolver.e4-pl-s3-q4-manager-reservation-v1"
WORKER_COMPLETION_SCHEMA = "anysolver.e4-pl-s3-q4-worker-completion-v2"
_VALIDATOR_BYTES = 259157
_VALIDATOR_SHA256 = "3c6e978180c09a3c7f0453033dccf8470e8d221cb417aa8b13b8e86b93339612"
_RESOURCE_UNPROVEN_TREE = threading.Event()
_EARLY_RESOURCE_TIMEOUT_POLICY = {
    "taskkill": Path(r"C:\Windows\System32\taskkill.exe"),
    "taskkill_arguments": ["/PID", "{pid}", "/T", "/F"],
    "termination_grace_seconds": 10,
    "timeout_exit_code": 124,
    "wall_limit_seconds": 1200,
}
_ACTIVE_JOB_HANDLES: set[int] = set()
_ACTIVE_JOB_LOCK = threading.Lock()
_ACTIVE_SUSPENDED_WORKERS: dict[int, Any] = {}
_INVOCATION_JOB_HANDLE: int | None = None
_CYCLE_RESOURCE_EXECUTION_CAPABILITY = object()


def _load_source_module(path: Path, *, expected_bytes: int, expected_sha256: str) -> Any:
    import hashlib
    import types

    if path.is_symlink():
        raise RuntimeError("canonical evidence validator may not be a symlink")
    raw = path.read_bytes()
    if len(raw) != expected_bytes or hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise RuntimeError("canonical evidence validator source identity mismatch")
    module = types.ModuleType("_e4_pl_s3_q4_burnin_authority")
    module.__file__ = str(path)
    module.__package__ = ""
    exec(compile(raw, str(path), "exec", dont_inherit=True), module.__dict__)
    return module


def _bootstrap_authority() -> None:
    global ROOT, _VALIDATOR_PATH, burnin
    expected_runner = (
        _FROZEN_ROOT / "docs" / "reference_cases" / "e4_pl_s3_q4_process_runner.py"
    )
    if not sys.flags.isolated:
        raise RuntimeError("process coordinator is not running in Python isolated mode")
    if _RUNNER_PATH != expected_runner:
        raise RuntimeError("process runner is outside the literal frozen authority path")
    if expected_runner.resolve(strict=True) != expected_runner:
        raise RuntimeError("literal process runner authority path is noncanonical")
    ROOT = _FROZEN_ROOT
    _VALIDATOR_PATH = (
        ROOT / "docs" / "reference_cases" / "e4_pl_s3_q4_burnin.py"
    ).resolve(strict=True)
    module = _load_source_module(
        _VALIDATOR_PATH,
        expected_bytes=_VALIDATOR_BYTES,
        expected_sha256=_VALIDATOR_SHA256,
    )
    if (
        Path(module.__file__).resolve(strict=True) != _VALIDATOR_PATH
        or module.PROCESS_RESULT_SCHEMA != PROCESS_RESULT_SCHEMA
    ):
        raise RuntimeError("process runner loaded a noncanonical evidence validator")
    burnin = module


RESOURCE_ORDER = [
    (cycle, lane)
    for cycle in (1, 2)
    for lane in ("functional", "anyfem", "performance")
]
_RESOURCE_LANES = ("functional", "anyfem", "performance")
_CYCLE_LANE_CUMULATIVE_DEADLINES_SECONDS = {
    "functional": 900,
    "anyfem": 990,
    "performance": 1110,
}
_CYCLE_WALL_LIMIT_SECONDS = 1200


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def _manager_environment(contract: Mapping[str, Any]) -> dict[str, str]:
    python = burnin.execution_tool_path(contract, "python")
    git = burnin.execution_tool_path(contract, "git")
    burnin.execution_tool_path(contract, "powershell")
    if python != Path(sys.executable).resolve(strict=True):
        raise burnin.EvidenceError("process Python executable differs from frozen authority")
    environment = burnin.sanitized_execution_environment(contract)
    current_path = environment.get("PATH", "")
    environment["PATH"] = os.pathsep.join(
        (str(git.parent), str(python.parent), current_path)
    )
    environment["ANYSOLVER_FROZEN_GIT"] = str(git)
    if environment.get("PYTHONDONTWRITEBYTECODE") != "1":
        raise burnin.EvidenceError("authority execution must disable Python bytecode")
    return environment


def _manager_script_args(
    powershell: Path, script: Path, request_id: str
) -> list[str]:
    """Return the frozen Windows PowerShell transport for manager scripts."""

    return [
        str(powershell),
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(script),
        "-RequestId",
        request_id,
    ]


def _timeout_policy(contract: Mapping[str, Any]) -> dict[str, Any]:
    """Return the exact, hash-bound resource child-tree timeout policy."""

    policy = burnin._exact_keys(
        contract["execution"]["timeout_policy"],
        {
            "automatic_retry",
            "evidence_reserve_seconds",
            "scope",
            "termination_grace_seconds",
            "timeout_exit_code",
            "wall_limit_seconds",
            "windows_job",
            "windows_termination",
        },
        "$contract.execution.timeout_policy",
    )
    wall_limit = burnin._require_int(
        policy["wall_limit_seconds"],
        "$contract.execution.timeout_policy.wall_limit_seconds",
        minimum=1,
    )
    grace = burnin._require_int(
        policy["termination_grace_seconds"],
        "$contract.execution.timeout_policy.termination_grace_seconds",
        minimum=1,
    )
    timeout_exit_code = burnin._require_int(
        policy["timeout_exit_code"],
        "$contract.execution.timeout_policy.timeout_exit_code",
        minimum=1,
    )
    evidence_reserve = burnin._require_int(
        policy["evidence_reserve_seconds"],
        "$contract.execution.timeout_policy.evidence_reserve_seconds",
        minimum=1,
    )
    if (
        wall_limit != 1200
        or timeout_exit_code != 124
        or grace != 10
        or evidence_reserve != 20
        or policy["automatic_retry"] is not False
        or policy["scope"] != "COMPLETE_RESOURCE_INVOCATION_AND_CHILD_PROCESS_TREE"
    ):
        raise burnin.EvidenceError("resource child-tree timeout policy mismatch")
    if policy["windows_job"] != {
        "assignment": "CREATE_SUSPENDED_ASSIGN_RESUME",
        "limit": "JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE",
        "watchdog_termination_start_seconds": 1190,
    }:
        raise burnin.EvidenceError("resource Windows job-object policy mismatch")
    worker_timeout = wall_limit - (2 * grace) - evidence_reserve
    if worker_timeout != 1160:
        raise burnin.EvidenceError("resource worker deadline does not preserve termination/evidence time")
    windows = burnin._exact_keys(
        policy["windows_termination"],
        {"arguments", "bytes", "path", "sha256"},
        "$contract.execution.timeout_policy.windows_termination",
    )
    declared_taskkill = Path(
        burnin._require_string(
            windows["path"],
            "$contract.execution.timeout_policy.windows_termination.path",
        )
    )
    taskkill = burnin.timeout_termination_tool(contract)
    if (
        not taskkill.is_absolute()
        or taskkill != declared_taskkill
        or taskkill.resolve(strict=True) != taskkill
        or taskkill.is_symlink()
        or burnin.is_reparse_point(taskkill)
        or burnin.file_hash_record(taskkill)
        != {
            "bytes": windows["bytes"],
            "sha256": windows["sha256"],
        }
    ):
        raise burnin.EvidenceError("Windows child-tree terminator identity mismatch")
    arguments = windows["arguments"]
    if arguments != ["/PID", "{pid}", "/T", "/F"]:
        raise burnin.EvidenceError("Windows child-tree terminator arguments mismatch")
    return {
        "taskkill": taskkill,
        "taskkill_arguments": list(arguments),
        "evidence_reserve_seconds": evidence_reserve,
        "termination_grace_seconds": grace,
        "timeout_exit_code": timeout_exit_code,
        "wall_limit_seconds": wall_limit,
        "worker_timeout_seconds": worker_timeout,
    }


def _cycle_wall_policy(contract: Mapping[str, Any]) -> dict[str, Any]:
    """Return the exact authority for one complete three-lane cycle."""

    policy = burnin._exact_keys(
        contract["execution"]["cycle_wall_policy"],
        {
            "absolute_wall_limit_seconds",
            "clock",
            "cumulative_deadlines_seconds",
            "final_evidence_reserve_seconds",
            "scope",
        },
        "$contract.execution.cycle_wall_policy",
    )
    cumulative = burnin._exact_keys(
        policy["cumulative_deadlines_seconds"],
        set(_RESOURCE_LANES),
        "$contract.execution.cycle_wall_policy.cumulative_deadlines_seconds",
    )
    deadlines = {
        lane: burnin._require_int(
            cumulative[lane],
            (
                "$contract.execution.cycle_wall_policy."
                f"cumulative_deadlines_seconds.{lane}"
            ),
            minimum=1,
        )
        for lane in _RESOURCE_LANES
    }
    absolute_wall_limit = burnin._require_int(
        policy["absolute_wall_limit_seconds"],
        "$contract.execution.cycle_wall_policy.absolute_wall_limit_seconds",
        minimum=1,
    )
    final_reserve = burnin._require_int(
        policy["final_evidence_reserve_seconds"],
        "$contract.execution.cycle_wall_policy.final_evidence_reserve_seconds",
        minimum=1,
    )
    if (
        absolute_wall_limit != _CYCLE_WALL_LIMIT_SECONDS
        or deadlines != _CYCLE_LANE_CUMULATIVE_DEADLINES_SECONDS
        or final_reserve != 90
        or policy["clock"] != "time.monotonic"
        or policy["scope"] != "COMPLETE_CYCLE_AND_ALL_CHILD_PROCESS_TREES"
        or deadlines["performance"] + final_reserve != absolute_wall_limit
    ):
        raise burnin.EvidenceError("complete-cycle wall policy mismatch")
    return {
        "absolute_wall_limit_seconds": absolute_wall_limit,
        "clock": policy["clock"],
        "cumulative_deadlines_seconds": deadlines,
        "final_evidence_reserve_seconds": final_reserve,
        "scope": policy["scope"],
    }


def _request_execution_policy(contract: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the cycle-only authority for all six current request IDs."""

    policy = burnin._exact_keys(
        contract["execution"]["request_execution_policy"],
        {
            "current_request_execution_mode",
            "idempotent_publication_recovery",
            "scope",
            "standalone_resource_command",
        },
        "$contract.execution.request_execution_policy",
    )
    expected = {
        "current_request_execution_mode": "FORMAL_CYCLE_COORDINATOR_ONLY",
        "idempotent_publication_recovery": "FINALIZE_COMMAND_ONLY",
        "scope": "ALL_SIX_CURRENT_REQUEST_IDS",
        "standalone_resource_command": "FORBIDDEN_FOR_CURRENT_REQUEST_IDS",
    }
    if policy != expected:
        raise burnin.EvidenceError("current request execution policy mismatch")
    current_ids = [
        row.get("request_id")
        for cycle in ("cycle_1", "cycle_2")
        for row in contract["resource_requests"][cycle]
    ]
    if (
        len(current_ids) != 6
        or any(not isinstance(request_id, str) for request_id in current_ids)
        or len(set(current_ids)) != 6
    ):
        raise burnin.EvidenceError(
            "cycle-only execution policy does not bind six unique current requests"
        )
    return policy


def _remaining_budget(deadline: float) -> float:
    return max(0.001, deadline - time.monotonic())


def _validate_early_watchdog_policy(policy: Mapping[str, Any]) -> None:
    expected = _EARLY_RESOURCE_TIMEOUT_POLICY
    for key in (
        "taskkill",
        "taskkill_arguments",
        "termination_grace_seconds",
        "timeout_exit_code",
        "wall_limit_seconds",
    ):
        if policy[key] != expected[key]:
            raise burnin.EvidenceError("contract timeout policy differs from early watchdog")


def _create_kill_on_close_job() -> int | None:
    if os.name != "nt":
        return None
    import ctypes
    from ctypes import wintypes

    class BasicLimitInformation(ctypes.Structure):
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

    class IoCounters(ctypes.Structure):
        _fields_ = [
            ("ReadOperationCount", ctypes.c_ulonglong),
            ("WriteOperationCount", ctypes.c_ulonglong),
            ("OtherOperationCount", ctypes.c_ulonglong),
            ("ReadTransferCount", ctypes.c_ulonglong),
            ("WriteTransferCount", ctypes.c_ulonglong),
            ("OtherTransferCount", ctypes.c_ulonglong),
        ]

    class ExtendedLimitInformation(ctypes.Structure):
        _fields_ = [
            ("BasicLimitInformation", BasicLimitInformation),
            ("IoInfo", IoCounters),
            ("ProcessMemoryLimit", ctypes.c_size_t),
            ("JobMemoryLimit", ctypes.c_size_t),
            ("PeakProcessMemoryUsed", ctypes.c_size_t),
            ("PeakJobMemoryUsed", ctypes.c_size_t),
        ]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
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
    information = ExtendedLimitInformation()
    information.BasicLimitInformation.LimitFlags = 0x00002000
    if not kernel32.SetInformationJobObject(
        handle, 9, ctypes.byref(information), ctypes.sizeof(information)
    ):
        error = ctypes.get_last_error()
        kernel32.CloseHandle(handle)
        raise OSError(error, "SetInformationJobObject failed")
    return int(handle)


def _arm_invocation_job_boundary() -> int | None:
    """Place the coordinator in a kill-on-close job before it launches children."""

    global _INVOCATION_JOB_HANDLE
    if os.name != "nt":
        return None
    if _INVOCATION_JOB_HANDLE is not None:
        return _INVOCATION_JOB_HANDLE

    import ctypes
    from ctypes import wintypes

    handle = _create_kill_on_close_job()
    assert handle is not None
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.GetCurrentProcess.argtypes = []
    kernel32.GetCurrentProcess.restype = wintypes.HANDLE
    kernel32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    kernel32.AssignProcessToJobObject.restype = wintypes.BOOL
    if not kernel32.AssignProcessToJobObject(handle, kernel32.GetCurrentProcess()):
        error = ctypes.get_last_error()
        _close_job_handle(handle)
        raise OSError(error, "coordinator AssignProcessToJobObject failed")
    _INVOCATION_JOB_HANDLE = handle
    return handle


def _close_job_handle(handle: int | None) -> bool:
    if handle is None:
        return True
    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL
    closed = bool(kernel32.CloseHandle(handle))
    if closed:
        with _ACTIVE_JOB_LOCK:
            _ACTIVE_JOB_HANDLES.discard(handle)
    return closed


def _assign_worker_to_job_and_resume(worker: Any, job_handle: int) -> None:
    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    kernel32.AssignProcessToJobObject.restype = wintypes.BOOL
    process_handle = int(worker._handle)
    if not kernel32.AssignProcessToJobObject(job_handle, process_handle):
        raise OSError(ctypes.get_last_error(), "AssignProcessToJobObject failed")
    with _ACTIVE_JOB_LOCK:
        _ACTIVE_JOB_HANDLES.add(job_handle)
    ntdll = ctypes.WinDLL("ntdll")
    ntdll.NtResumeProcess.argtypes = [wintypes.HANDLE]
    ntdll.NtResumeProcess.restype = ctypes.c_long
    status = int(ntdll.NtResumeProcess(process_handle))
    if status != 0:
        raise OSError(status, "NtResumeProcess failed")


def _launch_bounded_worker(args: list[str], **options: Any) -> tuple[Any, int | None]:
    """Launch suspended, bind to a kill-on-close job, then permit execution."""

    if os.name != "nt":
        options["start_new_session"] = True
        return subprocess.Popen(args, **options), None

    job_handle = _create_kill_on_close_job()
    options["creationflags"] = int(options.get("creationflags", 0)) | 0x00000004
    try:
        worker = subprocess.Popen(args, **options)
        _assign_worker_to_job_and_resume(worker, job_handle)
        return worker, job_handle
    except BaseException:
        cleanup_proven = "worker" not in locals()
        if "worker" in locals():
            with _ACTIVE_JOB_LOCK:
                assigned = job_handle in _ACTIVE_JOB_HANDLES
            if assigned:
                cleanup_proven = _close_job_handle(job_handle)
            else:
                with _ACTIVE_JOB_LOCK:
                    _ACTIVE_SUSPENDED_WORKERS[worker.pid] = worker
                try:
                    worker.kill()
                    worker.wait(timeout=1.0)
                    cleanup_proven = True
                except BaseException:
                    cleanup_proven = False
                if cleanup_proven:
                    with _ACTIVE_JOB_LOCK:
                        _ACTIVE_SUSPENDED_WORKERS.pop(worker.pid, None)
                    cleanup_proven = _close_job_handle(job_handle)
        else:
            cleanup_proven = _close_job_handle(job_handle)
        if not cleanup_proven:
            _RESOURCE_UNPROVEN_TREE.set()
        raise


def _close_all_active_jobs() -> None:
    with _ACTIVE_JOB_LOCK:
        handles = tuple(_ACTIVE_JOB_HANDLES)
    for handle in handles:
        _close_job_handle(handle)
    with _ACTIVE_JOB_LOCK:
        suspended = tuple(_ACTIVE_SUSPENDED_WORKERS.values())
    for worker in suspended:
        try:
            worker.kill()
            worker.wait(timeout=0.5)
        except BaseException:
            pass


def _start_resource_invocation_watchdog(
    policy: Mapping[str, Any],
) -> tuple[float, threading.Event, threading.Thread]:
    """Arm the absolute 20-minute fail-safe for one resource invocation."""

    deadline = time.monotonic() + policy["wall_limit_seconds"]
    termination_start = deadline - policy["termination_grace_seconds"]
    stop = threading.Event()

    def watchdog() -> None:
        if stop.wait(max(0.0, termination_start - time.monotonic())):
            return
        try:
            _close_all_active_jobs()
        finally:
            # End the coordinator before the absolute wall deadline.  Any
            # unproven global resource lock remains held for manual recovery.
            os._exit(policy["timeout_exit_code"])

    thread = threading.Thread(
        target=watchdog,
        name="s3-q4-resource-wall-watchdog",
        daemon=True,
    )
    thread.start()
    return deadline, stop, thread


def _termination_proves_tree_absence(termination: Mapping[str, Any]) -> bool:
    return termination["disposition"] in {
        "INTERRUPTED_TREE_TERMINATED",
        "NORMAL_EXIT",
        "START_FAILED",
        "TIMEOUT_TREE_TERMINATED",
    }


def _hold_for_resource_watchdog(watchdog_thread: threading.Thread) -> None:
    """Never return while a launched resource tree remains unproven."""

    while True:
        try:
            watchdog_thread.join(timeout=1.0)
        except BaseException:
            continue
        time.sleep(0.01)


def _termination_metadata(
    *,
    disposition: str,
    policy: Mapping[str, Any],
    tree_kill_attempted: bool,
    tree_kill_exit_code: int | None,
    child_exit_observed: bool,
) -> dict[str, Any]:
    return {
        "child_exit_observed": child_exit_observed,
        "disposition": disposition,
        "tree_kill_attempted": tree_kill_attempted,
        "tree_kill_exit_code": tree_kill_exit_code,
        "wall_limit_seconds": policy["wall_limit_seconds"],
    }


def _validate_termination_metadata(
    value: Any, *, policy: Mapping[str, Any], location: str
) -> dict[str, Any]:
    termination = burnin._exact_keys(
        value,
        {
            "child_exit_observed",
            "disposition",
            "tree_kill_attempted",
            "tree_kill_exit_code",
            "wall_limit_seconds",
        },
        location,
    )
    dispositions = {
        "INTERRUPTED_TREE_TERMINATED",
        "INTERRUPTED_TREE_TERMINATION_FAILED",
        "NORMAL_EXIT",
        "START_FAILED",
        "TIMEOUT_TREE_TERMINATED",
        "TIMEOUT_TREE_TERMINATION_FAILED",
    }
    if termination["disposition"] not in dispositions:
        raise burnin.EvidenceError(f"{location}.disposition is invalid")
    if termination["wall_limit_seconds"] != policy["wall_limit_seconds"]:
        raise burnin.EvidenceError(f"{location}.wall_limit_seconds mismatch")
    for name in ("child_exit_observed", "tree_kill_attempted"):
        if not isinstance(termination[name], bool):
            raise burnin.EvidenceError(f"{location}.{name} must be boolean")
    exit_code = termination["tree_kill_exit_code"]
    if exit_code is not None and (
        not isinstance(exit_code, int) or isinstance(exit_code, bool)
    ):
        raise burnin.EvidenceError(f"{location}.tree_kill_exit_code is invalid")
    attempted = termination["tree_kill_attempted"]
    if attempted != (exit_code is not None):
        raise burnin.EvidenceError(f"{location} tree-kill fields disagree")
    if termination["disposition"] in {"NORMAL_EXIT", "START_FAILED"} and attempted:
        raise burnin.EvidenceError(f"{location} unexpectedly attempted tree termination")
    if termination["disposition"] == "NORMAL_EXIT" and not termination[
        "child_exit_observed"
    ]:
        raise burnin.EvidenceError(f"{location} normal exit was not observed")
    if termination["disposition"] == "START_FAILED" and termination[
        "child_exit_observed"
    ]:
        raise burnin.EvidenceError(f"{location} start failure observed a child exit")
    if termination["disposition"] not in {"NORMAL_EXIT", "START_FAILED"}:
        if not attempted or exit_code is None:
            raise burnin.EvidenceError(f"{location} tree termination was not attempted")
        if termination["disposition"].endswith("_TERMINATED") and (
            exit_code != 0 or not termination["child_exit_observed"]
        ):
            raise burnin.EvidenceError(f"{location} successful termination is inconsistent")
        if (
            termination["disposition"].endswith("_FAILED")
            and exit_code == 0
            and termination["child_exit_observed"]
        ):
            raise burnin.EvidenceError(f"{location} failed termination is inconsistent")
    return dict(termination)


def _execution_environment(
    contract: Mapping[str, Any], *, process_prefix: str
) -> dict[str, str]:
    environment = _manager_environment(contract)
    pycache, numba_cache = burnin.execution_cache_paths(contract, process_prefix)
    if pycache.exists() or numba_cache.exists():
        raise burnin.EvidenceError("one-shot external execution cache already exists")
    for name, root in (
        ("Python", pycache.parent),
        ("Numba", numba_cache.parent),
    ):
        if root.exists() and (
            not root.is_dir()
            or root.is_symlink()
            or burnin.is_reparse_point(root)
        ):
            raise burnin.EvidenceError(f"{name} cache root is not a canonical directory")
    environment["PYTHONPYCACHEPREFIX"] = str(pycache)
    environment["NUMBA_CACHE_DIR"] = str(numba_cache)
    return environment


def _verify_local_runner_inputs(contract: Mapping[str, Any]) -> None:
    if contract["execution"].get("coordinator_isolated_mode") is not True:
        raise burnin.EvidenceError("Python isolated mode is not frozen for the coordinator")
    if not sys.flags.isolated:
        raise burnin.EvidenceError("process coordinator is not running in Python isolated mode")
    _timeout_policy(contract)
    expected = {
        "burnin_runner": ROOT / "scripts" / "run_e4_pl_burnin_gate.py",
        "evidence_validator": _VALIDATOR_PATH,
        "performance_measurement": ROOT / "scripts" / "measure_e4_pl_q1m_baseline.py",
        "process_runner": _RUNNER_PATH,
    }
    for name, path in expected.items():
        if name == "burnin_runner":
            burnin.validate_eol_bound_input(
                path,
                contract["runner_inputs"][name],
                expected_relative_path=path.relative_to(ROOT).as_posix(),
                location=f"$contract.runner_inputs.{name}",
            )
            continue
        record = burnin._exact_keys(
            contract["runner_inputs"][name],
            {"bytes", "path", "sha256"},
            f"$contract.runner_inputs.{name}",
        )
        if record["path"] != path.relative_to(ROOT).as_posix():
            raise burnin.EvidenceError(f"{name} canonical path mismatch")
        if path.is_symlink() or burnin.file_hash_record(path) != {
            "bytes": record["bytes"],
            "sha256": record["sha256"],
        }:
            raise burnin.EvidenceError(f"{name} identity mismatch")


def _write_exclusive(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if (
        not path.parent.is_dir()
        or path.parent.is_symlink()
        or burnin.is_reparse_point(path.parent)
        or path.is_symlink()
        or burnin.is_reparse_point(path)
    ):
        raise burnin.EvidenceError(f"exclusive output path is noncanonical: {path}")
    try:
        with path.open("xb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    except FileExistsError as exc:
        raise burnin.EvidenceError(f"refusing to replace process artifact: {path}") from exc


def _reserve_output(path: Path) -> None:
    expected_parent = burnin.output_root(burnin.load_contract())
    if path.parent != expected_parent or path.name not in set(
        burnin.PROCESS_DIRECTORY_NAMES.values()
    ):
        raise burnin.EvidenceError(f"output directory is outside frozen authority: {path}")
    try:
        path.mkdir(parents=True, exist_ok=False)
    except FileExistsError as exc:
        raise burnin.EvidenceError(f"frozen one-shot output already exists: {path}") from exc
    if (
        path.resolve(strict=True) != path
        or path.is_symlink()
        or burnin.is_reparse_point(path)
        or burnin.is_reparse_point(path.parent)
    ):
        raise burnin.EvidenceError(f"output directory is not canonical: {path}")


def _pending_output_directory(contract: Mapping[str, Any], prefix: str) -> Path:
    final = burnin.process_output_directory(contract, prefix)
    return final.with_name(f".pending-{final.name}")


def _reserve_pending_output(contract: Mapping[str, Any], prefix: str) -> Path:
    final = burnin.process_output_directory(contract, prefix)
    pending = _pending_output_directory(contract, prefix)
    root = burnin.output_root(contract)
    if final.parent != root or pending.parent != root:
        raise burnin.EvidenceError("pending output is outside the frozen output root")
    if any(
        path.exists() or path.is_symlink() or burnin.is_reparse_point(path)
        for path in (final, pending)
    ):
        raise burnin.EvidenceError(f"frozen one-shot output already exists: {prefix}")
    root.mkdir(parents=True, exist_ok=True)
    try:
        pending.mkdir(exist_ok=False)
    except FileExistsError as exc:
        raise burnin.EvidenceError(f"pending output already exists: {prefix}") from exc
    if (
        pending.resolve(strict=True) != pending
        or pending.is_symlink()
        or burnin.is_reparse_point(pending)
        or burnin.is_reparse_point(root)
    ):
        raise burnin.EvidenceError("pending output directory is noncanonical")
    return pending


def _atomic_promote_directory(pending: Path, final: Path) -> None:
    if pending.parent != final.parent:
        raise burnin.EvidenceError("pending promotion crosses output volumes")
    if final.exists() or final.is_symlink() or burnin.is_reparse_point(final):
        raise burnin.EvidenceError(f"refusing to replace canonical output: {final}")
    if not pending.is_dir() or pending.is_symlink() or burnin.is_reparse_point(pending):
        raise burnin.EvidenceError(f"pending output is not canonical: {pending}")
    try:
        pending.rename(final)
    except FileExistsError as exc:
        raise burnin.EvidenceError(f"canonical output appeared during promotion: {final}") from exc
    if (
        final.resolve(strict=True) != final
        or final.is_symlink()
        or burnin.is_reparse_point(final)
    ):
        raise burnin.EvidenceError(f"promoted output is noncanonical: {final}")


def _authority_commit(candidate: Path, contract: Mapping[str, Any]) -> tuple[str, str]:
    candidate = candidate.resolve(strict=True)
    burnin.assert_clean_execution_repository(candidate, contract=contract)
    head = burnin._git(candidate, "rev-parse", "HEAD", contract=contract)
    tree = burnin._git(candidate, "rev-parse", "HEAD^{tree}", contract=contract)
    topology = burnin.validate_execution_authorization(candidate, contract=contract)
    if (topology["candidate_commit"], topology["candidate_tree"]) != (head, tree):
        raise burnin.EvidenceError(
            "validated execution authorization differs from candidate HEAD"
        )
    authority = contract["authority_commit"]
    authority_commit = topology["authority_commit"]
    metadata = burnin._git(
        candidate,
        "show",
        "-s",
        "--format=%P%n%s",
        authority_commit,
        contract=contract,
    ).splitlines()
    if metadata != [authority["exact_parent"], authority["subject"]]:
        raise burnin.EvidenceError("authority parent or subject mismatch")
    paths = burnin._git(
        candidate,
        "diff",
        "--name-only",
        authority["exact_parent"],
        authority_commit,
        contract=contract,
    ).splitlines()
    if paths != authority["exact_paths"]:
        raise burnin.EvidenceError("authority changed-path extent mismatch")
    execution = contract["execution_authorization_commit"]
    if execution["exact_parent_role"] != "DERIVED_AUTHORITY_COMMIT":
        raise burnin.EvidenceError("execution authorization parent role mismatch")
    if execution["approval_path"] not in execution["exact_paths"]:
        raise burnin.EvidenceError("execution authorization approval path is absent")
    if execution["review_paths"] != [
        path for path in execution["exact_paths"] if path != execution["approval_path"]
    ]:
        raise burnin.EvidenceError("execution authorization review extent mismatch")
    metadata = burnin._git(
        candidate, "show", "-s", "--format=%P%n%s", head, contract=contract
    ).splitlines()
    if metadata != [authority_commit, execution["subject"]]:
        raise burnin.EvidenceError("HEAD is not the registered execution authorization successor")
    paths = burnin._git(
        candidate,
        "diff",
        "--name-only",
        authority_commit,
        head,
        contract=contract,
    ).splitlines()
    if paths != execution["exact_paths"] or len(paths) != execution["path_count"]:
        raise burnin.EvidenceError("execution authorization changed-path extent mismatch")
    return head, tree


def _verify_repositories(
    contract: Mapping[str, Any],
) -> tuple[Path, dict[str, Path], str, str]:
    _verify_local_runner_inputs(contract)
    repositories = burnin.external_repository_paths(contract)
    candidate = repositories["ANYsolver"]
    siblings = {name: repositories[name] for name in contract["sibling_authority"]}
    if ROOT.resolve(strict=True) != candidate.resolve(strict=True):
        raise burnin.EvidenceError("process runner is not executing from the frozen candidate")
    for name, path in repositories.items():
        if path.resolve(strict=True) != path:
            raise burnin.EvidenceError(f"{name} path is not the exact frozen repository")
    # Complete, non-mutating cleanliness phase across the entire frozen graph.
    # No identity or topology probe may run until every repository passes.
    scope = contract["execution"]["clean_status_scope"]
    if (
        not isinstance(scope, list)
        or any(not isinstance(name, str) for name in scope)
        or len(scope) != len(set(scope))
        or set(scope) != set(repositories)
    ):
        raise burnin.EvidenceError("strict clean-status scope mismatch")
    burnin.validate_git_runtime(contract)
    for name in scope:
        burnin.strict_clean_status_record(repositories[name], contract=contract)
    head, tree = _authority_commit(candidate, contract)
    if set(siblings) != set(contract["sibling_authority"]):
        raise burnin.EvidenceError("sibling repository bindings are incomplete")
    for name, authority in contract["sibling_authority"].items():
        path = siblings[name].resolve(strict=True)
        burnin.assert_clean_execution_repository(path, contract=contract)
        if burnin._git(path, "rev-parse", "HEAD", contract=contract) != authority["commit"]:
            raise burnin.EvidenceError(f"{name} commit mismatch")
        if burnin._git(path, "rev-parse", "HEAD^{tree}", contract=contract) != authority["tree"]:
            raise burnin.EvidenceError(f"{name} tree mismatch")
    return candidate, siblings, head, tree


def _run(
    command: str,
    *,
    absolute_worker_deadline: float,
    contract: Mapping[str, Any],
    cwd: Path,
    process_prefix: str,
) -> tuple[
    subprocess.CompletedProcess[bytes], str, str, float, str, dict[str, Any]
]:
    policy = _timeout_policy(contract)
    started_at = _now()
    started = time.perf_counter()
    execution_state = "EXECUTED"
    powershell = burnin.execution_tool_path(contract, "powershell")
    args = [str(powershell), "-NoProfile", "-Command", command]
    returncode = 250
    termination = _termination_metadata(
        disposition="START_FAILED",
        policy=policy,
        tree_kill_attempted=False,
        tree_kill_exit_code=None,
        child_exit_observed=False,
    )
    with tempfile.TemporaryFile() as stdout_stream, tempfile.TemporaryFile() as stderr_stream:
        worker: subprocess.Popen[bytes] | None = None
        job_handle: int | None = None
        try:
            if absolute_worker_deadline <= time.monotonic():
                raise burnin.EvidenceError(
                    "local invocation exhausted its worker budget before launch"
                )
            popen_options: dict[str, Any] = {}
            if os.name == "nt":
                popen_options["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
            worker, job_handle = _launch_bounded_worker(
                args,
                cwd=cwd,
                env=_execution_environment(contract, process_prefix=process_prefix),
                stdout=stdout_stream,
                stderr=stderr_stream,
                **popen_options,
            )
        except (OSError, burnin.EvidenceError) as exc:
            execution_state = "NOT_STARTED"
            stderr_stream.write(
                f"process start failed: {exc}\n".encode("utf-8", errors="replace")
            )
        if worker is not None:
            child_exit_observed = False
            cleanup_reason = "INTERRUPTED"
            try:
                returncode = worker.wait(
                    timeout=_remaining_budget(absolute_worker_deadline)
                )
                child_exit_observed = True
                termination = _termination_metadata(
                    disposition="NORMAL_EXIT",
                    policy=policy,
                    tree_kill_attempted=False,
                    tree_kill_exit_code=None,
                    child_exit_observed=True,
                )
            except subprocess.TimeoutExpired:
                cleanup_reason = "TIMEOUT"
                returncode = policy["timeout_exit_code"]
            except KeyboardInterrupt:
                returncode = 130
            except Exception as exc:
                returncode = 250
                stderr_stream.write(
                    (
                        "preflight worker wait failed after launch; "
                        f"tree cleanup required: {exc}\n"
                    ).encode("utf-8", errors="replace")
                )
            finally:
                if not child_exit_observed:
                    try:
                        termination = _terminate_worker_tree(
                            worker,
                            policy=policy,
                            reason=cleanup_reason,
                            stderr_stream=stderr_stream,
                        )
                    except BaseException as exc:
                        stderr_stream.write(
                            f"preflight tree cleanup failed: {exc}\n".encode(
                                "utf-8", errors="replace"
                            )
                        )
                        termination = _termination_metadata(
                            disposition=f"{cleanup_reason}_TREE_TERMINATION_FAILED",
                            policy=policy,
                            tree_kill_attempted=True,
                            tree_kill_exit_code=255,
                            child_exit_observed=False,
                        )
                if not _termination_proves_tree_absence(termination):
                    _RESOURCE_UNPROVEN_TREE.set()
                elif not _close_job_handle(job_handle):
                    _RESOURCE_UNPROVEN_TREE.set()
                if termination["disposition"] == "NORMAL_EXIT":
                    returncode = (
                        worker.returncode
                        if worker.returncode is not None
                        else returncode
                    )
        stdout_stream.flush()
        stderr_stream.flush()
        stdout_stream.seek(0)
        stderr_stream.seek(0)
        completed = subprocess.CompletedProcess(
            args=args,
            returncode=returncode,
            stdout=stdout_stream.read(),
            stderr=stderr_stream.read(),
        )
    _validate_termination_metadata(
        termination, policy=policy, location="$local_process.termination"
    )
    elapsed = time.perf_counter() - started
    ended_at = _now()
    return completed, started_at, ended_at, elapsed, execution_state, termination


def _process_manifest(
    *,
    candidate_commit: str,
    candidate_tree: str,
    command: str,
    completed: subprocess.CompletedProcess[bytes],
    elapsed_seconds: float,
    ended_at: str,
    execution_state: str,
    request_id: str | None,
    request_sha256: str | None,
    resource_lock_released: bool | None,
    started_at: str,
    approval_snapshot: Mapping[str, Any] | None,
    termination: Mapping[str, Any],
) -> dict[str, Any]:
    producer_sha256 = burnin.file_hash_record(_RUNNER_PATH)["sha256"]
    return {
        "approval_snapshot": None if approval_snapshot is None else dict(approval_snapshot),
        "candidate_commit": candidate_commit,
        "candidate_tree": candidate_tree,
        "command_sha256": burnin.sha256_bytes(command.encode("utf-8")),
        "elapsed_seconds": elapsed_seconds,
        "ended_at": ended_at,
        "execution_state": execution_state,
        "exit_code": completed.returncode,
        "producer_sha256": producer_sha256,
        "request_id": request_id,
        "request_sha256": request_sha256,
        "resource_lock_released": resource_lock_released,
        "schema": PROCESS_RESULT_SCHEMA,
        "started_at": started_at,
        "stderr": {
            "bytes": len(completed.stderr),
            "sha256": burnin.sha256_bytes(completed.stderr),
        },
        "stdout": {
            "bytes": len(completed.stdout),
            "sha256": burnin.sha256_bytes(completed.stdout),
        },
        "termination": dict(termination),
    }


def _write_process(
    output_dir: Path,
    *,
    manifest: Mapping[str, Any],
    stderr: bytes,
    stdout: bytes,
) -> tuple[Path, Path, Path]:
    if (
        not output_dir.is_dir()
        or output_dir.is_symlink()
        or burnin.is_reparse_point(output_dir)
    ):
        raise burnin.EvidenceError(f"process output was not exclusively reserved: {output_dir}")
    stdout_path = output_dir / "stdout.txt"
    stderr_path = output_dir / "stderr.txt"
    result_path = output_dir / "result.json"
    _write_exclusive(stdout_path, stdout)
    _write_exclusive(stderr_path, stderr)
    _write_exclusive(result_path, burnin.canonical_json_bytes(dict(manifest)))
    return result_path, stdout_path, stderr_path


def _existing_process_directory(
    contract: Mapping[str, Any], prefix: str, *, required: bool
) -> Path | None:
    final = burnin.process_output_directory(contract, prefix)
    pending = _pending_output_directory(contract, prefix)
    present = [
        path
        for path in (final, pending)
        if path.exists() or path.is_symlink() or burnin.is_reparse_point(path)
    ]
    if len(present) > 1:
        raise burnin.EvidenceError(f"both pending and canonical output exist: {prefix}")
    if not present:
        if required:
            raise burnin.EvidenceError(f"required predecessor {prefix} is absent")
        return None
    directory = present[0]
    if (
        not directory.is_dir()
        or directory.is_symlink()
        or burnin.is_reparse_point(directory)
    ):
        raise burnin.EvidenceError(f"process output directory is noncanonical: {prefix}")
    return directory


def _load_process_manifest(
    contract: Mapping[str, Any], prefix: str, *, required: bool
) -> dict[str, Any] | None:
    directory = _existing_process_directory(contract, prefix, required=required)
    if directory is None:
        return None
    result_path = directory / "result.json"
    if not result_path.exists():
        if required:
            raise burnin.EvidenceError(f"required predecessor {prefix} is reserved but nonterminal")
        return None
    if result_path.is_symlink() or burnin.is_reparse_point(result_path):
        raise burnin.EvidenceError(f"process manifest is noncanonical: {prefix}")
    raw = result_path.read_bytes()
    manifest = burnin.strict_json_loads(raw)
    if raw != burnin.canonical_json_bytes(manifest):
        raise burnin.EvidenceError(f"process manifest is not canonical: {prefix}")
    is_resource = prefix.startswith("cycle_")
    request_row: dict[str, Any] | None = None
    if is_resource:
        match = re.fullmatch(r"cycle_(1|2)\.(functional|anyfem|performance)", prefix)
        if match is None:
            raise burnin.EvidenceError(f"invalid resource prefix: {prefix}")
        cycle, lane = int(match.group(1)), match.group(2)
        request_row = next(
            row
            for row in contract["resource_requests"][f"cycle_{cycle}"]
            if row["lane"] == lane
        )
        expected_command = request_row["command_sha256"]
        expected_request_id = request_row["request_id"]
    else:
        if prefix == "common.quick.1":
            command_row = contract["non_resource_commands"]["quick"]
        elif prefix == "common.package.1":
            command_row = contract["non_resource_commands"]["package"]
        else:
            partition = int(prefix.rsplit(".", 1)[1])
            command_row = contract["non_resource_commands"]["additive"][partition - 1]
        expected_command = command_row["command_sha256"]
        expected_request_id = None
    candidate = burnin.external_repository_paths(contract)["ANYsolver"]
    candidate_record = {
        "commit": burnin._git(candidate, "rev-parse", "HEAD", contract=contract),
        "tree": burnin._git(candidate, "rev-parse", "HEAD^{tree}", contract=contract),
    }
    status = (
        "PASS"
        if manifest.get("exit_code") == 0
        and manifest.get("execution_state") == "EXECUTED"
        and isinstance(manifest.get("termination"), dict)
        and manifest["termination"].get("disposition") == "NORMAL_EXIT"
        and manifest.get("resource_lock_released") == (True if is_resource else None)
        else "FAIL"
    )
    _validate_termination_metadata(
        manifest.get("termination"),
        policy=_timeout_policy(contract),
        location=f"$process.{prefix}.termination",
    )
    process = {
        key: manifest[key]
        for key in (
            "command_sha256",
            "approval_snapshot",
            "elapsed_seconds",
            "ended_at",
            "execution_state",
            "exit_code",
            "producer_sha256",
            "request_id",
            "resource_lock_released",
            "started_at",
            "stderr",
            "stdout",
            "termination",
        )
    }
    process.update(
        {
            "pending_manifest_sha256": (
                burnin.file_hash_record(directory / "pending-manifest.json")["sha256"]
                if is_resource and (directory / "pending-manifest.json").is_file()
                else None
            ),
            "result": burnin.file_hash_record(result_path),
            "status": status,
        }
    )
    burnin._validate_process(
        process,
        f"$process.{prefix}",
        expected_request_id=expected_request_id,
        expected_command_sha256=expected_command,
        expected_producer_sha256=burnin.contract_producer_sha256(contract),
    )
    for name in ("stdout", "stderr"):
        path = directory / f"{name}.txt"
        if (
            path.is_symlink()
            or burnin.is_reparse_point(path)
            or burnin.file_hash_record(path) != manifest[name]
        ):
            raise burnin.EvidenceError(f"process {name} identity mismatch: {prefix}")
    burnin._validate_process_result_artifact(
        result_path,
        candidate=candidate_record,
        process=process,
        request=request_row,
    )
    return manifest


def _manifest_passed(manifest: Mapping[str, Any]) -> bool:
    return (
        manifest.get("exit_code") == 0
        and manifest.get("execution_state") == "EXECUTED"
        and manifest.get("resource_lock_released") in {None, True}
        and isinstance(manifest.get("termination"), dict)
        and manifest["termination"].get("disposition") == "NORMAL_EXIT"
    )


def _require_passed(contract: Mapping[str, Any], prefix: str) -> dict[str, Any]:
    manifest = _load_process_manifest(contract, prefix, required=True)
    assert manifest is not None
    if not _manifest_passed(manifest):
        raise burnin.EvidenceError(f"required predecessor did not pass: {prefix}")
    return manifest


def _validate_package_artifacts(
    contract: Mapping[str, Any], *, candidate_commit: str, candidate_tree: str
) -> dict[str, Any]:
    """Revalidate the package result and preserved wheel at a use boundary."""

    directory = _existing_process_directory(
        contract, "common.package.1", required=True
    )
    assert directory is not None
    stdout_path = burnin.require_regular_file(directory / "stdout.txt", nonempty=True)
    root = burnin.output_root(contract)
    if not root.is_dir() or root.is_symlink() or burnin.is_reparse_point(root):
        raise burnin.EvidenceError("package output root is noncanonical")
    result_path = root / contract["package"]["result_filename"]
    wheel_path = root / contract["package"]["wheel_filename"]
    burnin.require_regular_file(result_path, nonempty=True)
    burnin.require_regular_file(wheel_path, nonempty=True)
    if result_path.name != contract["package"]["result_filename"]:
        raise burnin.EvidenceError("package result filename mismatch")
    if wheel_path.name != contract["package"]["wheel_filename"]:
        raise burnin.EvidenceError("preserved wheel filename mismatch")

    raw = burnin.require_package_process_result_identity(contract=contract)
    if stdout_path.read_bytes() != raw:
        raise burnin.EvidenceError("package-process stdout changed during validation")
    package = burnin.strict_json_loads(raw)
    if raw != burnin.canonical_json_bytes(package):
        raise burnin.EvidenceError("package result is not canonical JSON")
    package = burnin.validate_package_result(package, contract=contract)

    expected_sources = {
        "ANYsolver": {"commit": candidate_commit, "tree": candidate_tree},
        **{
            name: authority
            for name, authority in contract["sibling_authority"].items()
            if name != "ANYfem"
        },
    }
    for name, authority in expected_sources.items():
        source = package["sources"][name]
        if (
            source["commit"] != authority["commit"]
            or source["tree"] != authority["tree"]
        ):
            raise burnin.EvidenceError(f"package source authority mismatch: {name}")

    observed_wheel = {
        **burnin.file_hash_record(wheel_path),
        "filename": wheel_path.name,
    }
    if package["wheels"]["ANYsolver"] != observed_wheel:
        raise burnin.EvidenceError("preserved ANYsolver wheel identity mismatch")
    return package


def _require_package_artifacts(
    contract: Mapping[str, Any], *, candidate_commit: str, candidate_tree: str
) -> dict[str, Any]:
    """Bind the passed package process to its live result and wheel."""

    _require_passed(contract, "common.package.1")
    return _validate_package_artifacts(
        contract,
        candidate_commit=candidate_commit,
        candidate_tree=candidate_tree,
    )


def _assert_absent(contract: Mapping[str, Any], prefixes: list[str]) -> None:
    for prefix in prefixes:
        final = burnin.process_output_directory(contract, prefix)
        pending = _pending_output_directory(contract, prefix)
        if any(
            path.exists() or path.is_symlink() or burnin.is_reparse_point(path)
            for path in (final, pending)
        ):
            raise burnin.EvidenceError(f"frozen one-shot output already exists: {prefix}")


def _local_prefix(lane: str, partition: int | None) -> str:
    if lane == "additive":
        if partition not in {1, 2, 3}:
            raise burnin.EvidenceError("additive execution requires partition 1, 2, or 3")
        return f"common.additive.{partition}"
    if lane not in {"quick", "package"} or partition is not None:
        raise burnin.EvidenceError("invalid local lane/partition selection")
    return f"common.{lane}.1"


def _verify_local_order(
    contract: Mapping[str, Any], lane: str, partition: int | None
) -> str:
    prefix = _local_prefix(lane, partition)
    resource_prefixes = [f"cycle_{cycle}.{name}" for cycle, name in RESOURCE_ORDER]
    if lane == "quick":
        if burnin.output_root(contract).exists():
            raise burnin.EvidenceError("frozen output root already exists before quick")
    elif lane == "package":
        _require_passed(contract, "common.quick.1")
        _assert_absent(
            contract,
            [prefix, "common.additive.1", "common.additive.2", "common.additive.3", *resource_prefixes],
        )
        for filename in (
            contract["package"]["result_filename"],
            contract["package"]["wheel_filename"],
        ):
            if (burnin.output_root(contract) / filename).exists():
                raise burnin.EvidenceError("canonical package output already exists")
    else:
        _require_passed(contract, "common.quick.1")
        _require_passed(contract, "common.package.1")
        _assert_absent(contract, [prefix, *resource_prefixes])
        assert partition is not None
        if (burnin.output_root(contract) / f"pytest-additive-{partition}").exists():
            raise burnin.EvidenceError("additive pytest output already exists")
    if (burnin.output_root(contract) / contract["adjudication"]["external_result_filename"]).exists():
        raise burnin.EvidenceError("aggregate already exists; no further execution is allowed")
    return prefix


def _resource_position(
    contract: Mapping[str, Any], request_id: str
) -> tuple[int, str, int]:
    for index, (cycle, lane) in enumerate(RESOURCE_ORDER):
        row = next(
            candidate
            for candidate in contract["resource_requests"][f"cycle_{cycle}"]
            if candidate["lane"] == lane
        )
        if row["request_id"] == request_id:
            return cycle, lane, index
    raise burnin.EvidenceError(f"request is not preregistered: {request_id}")


def _verify_resource_order(
    contract: Mapping[str, Any], request_id: str
) -> tuple[str, int, str]:
    for prefix in (
        "common.quick.1",
        "common.package.1",
        "common.additive.1",
        "common.additive.2",
        "common.additive.3",
    ):
        _require_passed(contract, prefix)
    cycle, lane, index = _resource_position(contract, request_id)
    if cycle == 2:
        cycle_one_snapshot = _cycle_snapshot_path(contract, 1)
        if (
            not cycle_one_snapshot.is_file()
            or cycle_one_snapshot.is_symlink()
            or burnin.is_reparse_point(cycle_one_snapshot)
        ):
            raise burnin.EvidenceError(
                "cycle 2 requires the canonical cycle-1 terminal snapshot"
            )
        snapshot = _validate_ledger_snapshot(
            _load_canonical_json(cycle_one_snapshot), contract=contract
        )
        if snapshot.get("kind") != "CYCLE_TERMINAL" or snapshot.get("cycle") != 1:
            raise burnin.EvidenceError("cycle-1 terminal snapshot authority mismatch")
    ordered_prefixes = [f"cycle_{c}.{name}" for c, name in RESOURCE_ORDER]
    for prefix in ordered_prefixes[:index]:
        manifest = _require_passed(contract, prefix)
        _require_resource_terminal(contract, prefix, manifest)
    _assert_absent(contract, ordered_prefixes[index:])
    if (burnin.output_root(contract) / contract["adjudication"]["external_result_filename"]).exists():
        raise burnin.EvidenceError("aggregate already exists; no further execution is allowed")
    return lane, cycle, ordered_prefixes[index]


def _run_local_bounded(
    *,
    contract: Mapping[str, Any],
    invocation_deadline: float,
    lane: str,
    partition: int | None,
    timeout_policy: Mapping[str, Any],
) -> int:
    publication_deadline = (
        invocation_deadline - timeout_policy["termination_grace_seconds"]
    )
    worker_deadline = publication_deadline - (
        timeout_policy["termination_grace_seconds"]
        + timeout_policy["evidence_reserve_seconds"]
    )
    candidate, _siblings, candidate_commit, candidate_tree = _verify_repositories(contract)
    prefix = _verify_local_order(contract, lane, partition)
    output_dir = burnin.process_output_directory(contract, prefix)
    commands = contract["non_resource_commands"]
    if lane == "additive":
        assert partition is not None
        row = commands["additive"][partition - 1]
    else:
        row = commands[lane]
    command = row["command"]
    if burnin.sha256_bytes(command.encode("utf-8")) != row["command_sha256"]:
        raise burnin.EvidenceError("local command authority mismatch")
    _execution_environment(contract, process_prefix=prefix)
    _reserve_output(output_dir)
    completed, started_at, ended_at, elapsed, execution_state, termination = _run(
        command,
        absolute_worker_deadline=worker_deadline,
        contract=contract,
        cwd=candidate,
        process_prefix=prefix,
    )
    if _RESOURCE_UNPROVEN_TREE.is_set():
        raise burnin.EvidenceError(
            "local result publication requires proven child-tree closure"
        )
    try:
        _candidate, _siblings, post_commit, post_tree = _verify_repositories(contract)
        if (post_commit, post_tree) != (candidate_commit, candidate_tree):
            raise burnin.EvidenceError("candidate identity changed during execution")
    except burnin.EvidenceError as exc:
        completed = subprocess.CompletedProcess(
            args=completed.args,
            returncode=251,
            stdout=completed.stdout,
            stderr=completed.stderr + f"\npost-execution authority failure: {exc}\n".encode(),
        )
    manifest = _process_manifest(
        candidate_commit=candidate_commit,
        candidate_tree=candidate_tree,
        command=command,
        completed=completed,
        elapsed_seconds=elapsed,
        ended_at=ended_at,
        execution_state=execution_state,
        request_id=None,
        request_sha256=None,
        resource_lock_released=None,
        started_at=started_at,
        approval_snapshot=None,
        termination=termination,
    )
    _write_process(
        output_dir,
        manifest=manifest,
        stderr=completed.stderr,
        stdout=completed.stdout,
    )
    sys.stdout.buffer.write(burnin.canonical_json_bytes(manifest))
    sys.stdout.buffer.flush()
    return completed.returncode


def run_local(
    *,
    lane: str,
    partition: int | None,
) -> int:
    _RESOURCE_UNPROVEN_TREE.clear()
    invocation_deadline, watchdog_stop, watchdog_thread = (
        _start_resource_invocation_watchdog(_EARLY_RESOURCE_TIMEOUT_POLICY)
    )
    try:
        _bootstrap_authority()
        contract = burnin.load_contract()
        timeout_policy = _timeout_policy(contract)
        _validate_early_watchdog_policy(timeout_policy)
        return _run_local_bounded(
            contract=contract,
            invocation_deadline=invocation_deadline,
            lane=lane,
            partition=partition,
            timeout_policy=timeout_policy,
        )
    finally:
        if _RESOURCE_UNPROVEN_TREE.is_set():
            _hold_for_resource_watchdog(watchdog_thread)
        else:
            watchdog_stop.set()
            watchdog_thread.join(timeout=0.1)


def _request_row(contract: Mapping[str, Any], request_id: str) -> dict[str, Any]:
    matches = [
        row
        for cycle in ("cycle_1", "cycle_2")
        for row in contract["resource_requests"][cycle]
        if row["request_id"] == request_id
    ]
    if len(matches) != 1:
        raise burnin.EvidenceError(f"request is not uniquely preregistered: {request_id}")
    return matches[0]


def _reject_standalone_resource_execution(
    contract: Mapping[str, Any], request_id: str
) -> None:
    """Reject every current v15 worker request outside its complete cycle.

    ``finalize-resource`` is intentionally separate: it can validate and
    publish an existing durable worker-completion checkpoint, but it cannot
    launch or rerun the registered worker command.
    """

    _request_execution_policy(contract)
    row = _request_row(contract, request_id)
    cycle, lane, _index = _resource_position(contract, request_id)
    if row.get("lane") != lane:
        raise burnin.EvidenceError("standalone request lane authority mismatch")
    raise burnin.EvidenceError(
        "standalone resource worker execution is forbidden for current v15 "
        f"request {request_id} ({lane}, cycle {cycle}); use cycle --cycle {cycle}"
    )


def _manager_paths(contract: Mapping[str, Any]) -> dict[str, Path]:
    authority = burnin.resource_manager_authority(contract)
    root = Path(authority["root"])
    if (
        root.resolve(strict=True) != root
        or not root.is_dir()
        or root.is_symlink()
        or burnin.is_reparse_point(root)
    ):
        raise burnin.EvidenceError("resource-manager root identity mismatch")
    result = {
        "root": root,
        "ledger": root / authority["ledger"],
        "requests": root / authority["requests"],
        "active_lock": root / authority["active_lock"],
    }
    for key in ("acquire", "release"):
        record = authority[key]
        path = root / record["filename"]
        if path.is_symlink() or burnin.is_reparse_point(path) or burnin.file_hash_record(path) != {
            "bytes": record["bytes"],
            "sha256": record["sha256"],
        }:
            raise burnin.EvidenceError(f"resource-manager {key} identity mismatch")
        result[key] = path
    if (
        result["ledger"].is_symlink()
        or burnin.is_reparse_point(result["ledger"])
        or not result["ledger"].is_file()
        or result["requests"].is_symlink()
        or burnin.is_reparse_point(result["requests"])
        or not result["requests"].is_dir()
    ):
        raise burnin.EvidenceError("resource-manager ledger/request authority mismatch")
    if result["active_lock"].is_symlink() or burnin.is_reparse_point(result["active_lock"]):
        raise burnin.EvidenceError("resource-manager active lock is a reparse point")
    return result


def _request_payload(
    contract: Mapping[str, Any], request_id: str
) -> tuple[dict[str, Any], dict[str, Any], Path]:
    row = _request_row(contract, request_id)
    manager = _manager_paths(contract)
    request_path = manager["requests"] / f"{request_id}.json"
    if (
        request_path.name != f"{request_id}.json"
        or request_path.is_symlink()
        or burnin.is_reparse_point(request_path)
    ):
        raise burnin.EvidenceError("resource request path mismatch")
    if burnin.file_hash_record(request_path) != {
        "bytes": row["bytes"],
        "sha256": row["request_sha256"],
    }:
        raise burnin.EvidenceError("resource request identity mismatch")
    request = burnin.strict_json_load(request_path)
    if request.get("request_id") != request_id or request.get("status") != "PENDING":
        raise burnin.EvidenceError("resource request payload identity mismatch")
    command = request.get("command")
    if not isinstance(command, str) or burnin.sha256_bytes(command.encode("utf-8")) != row[
        "command_sha256"
    ]:
        raise burnin.EvidenceError("resource request command mismatch")
    return row, request, request_path


def _ledger_rows(ledger: str, request_id: str, status: str) -> list[str]:
    return re.findall(
        rf"^\|[^\n]*\|\s*{request_id}\s*\|\s*{status}\s*\|[^\n]*$",
        ledger,
        flags=re.MULTILINE,
    )


def _append_ledger_fields(
    ledger_path: Path, fields: list[str], *, timestamp: str | None = None
) -> list[str]:
    if len(fields) != 7 or any(
        not isinstance(field, str)
        or "|" in field
        or "\n" in field
        or "\r" in field
        for field in fields
    ):
        raise burnin.EvidenceError("resource ledger fields are malformed")
    timestamp = timestamp or _now()
    burnin._require_timestamp(timestamp, "$resource_ledger.timestamp")
    row = f"| {timestamp} | {' | '.join(fields)} |\n"
    with ledger_path.open("a", encoding="utf-8", newline="") as stream:
        stream.write(row)
        stream.flush()
        os.fsync(stream.fileno())
    entries = burnin._ledger_entries(
        ledger_path.read_text(encoding="utf-8"), fields[0], fields[1]
    )
    matching = [entry for entry in entries if entry == [timestamp, *fields]]
    if len(matching) != 1:
        raise burnin.EvidenceError("resource ledger append did not verify exactly")
    return matching[0]


def _ledger_row_object(entry: list[str]) -> dict[str, Any]:
    if len(entry) != 8:
        raise burnin.EvidenceError("resource ledger row width mismatch")
    return {"fields": entry[1:], "timestamp": entry[0]}


def _approval_snapshot_path(contract: Mapping[str, Any]) -> Path:
    name = contract["adjudication"]["approval_snapshot_filename"]
    if Path(name).name != name:
        raise burnin.EvidenceError("approval snapshot filename must be a basename")
    return burnin.output_root(contract) / name


def _cycle_snapshot_path(contract: Mapping[str, Any], cycle: int) -> Path:
    name = contract["adjudication"]["cycle_terminal_snapshot_filenames"][f"cycle_{cycle}"]
    if Path(name).name != name:
        raise burnin.EvidenceError("cycle snapshot filename must be a basename")
    return burnin.output_root(contract) / name


def _load_canonical_json(path: Path) -> dict[str, Any]:
    if path.is_symlink() or burnin.is_reparse_point(path) or not path.is_file():
        raise burnin.EvidenceError(f"canonical JSON artifact is unavailable: {path}")
    raw = path.read_bytes()
    value = burnin.strict_json_loads(raw)
    if not isinstance(value, dict) or raw != burnin.canonical_json_bytes(value):
        raise burnin.EvidenceError(f"artifact is not canonical JSON: {path}")
    return value


def _write_canonical_json_once(path: Path, value: Mapping[str, Any]) -> None:
    payload = burnin.canonical_json_bytes(dict(value))
    if path.exists() or path.is_symlink() or burnin.is_reparse_point(path):
        if _load_canonical_json(path) != dict(value):
            raise burnin.EvidenceError(f"canonical artifact already differs: {path}")
        return
    temporary = path.with_name(f".{path.name}.pending")
    if temporary.exists() or temporary.is_symlink() or burnin.is_reparse_point(temporary):
        if (
            temporary.is_symlink()
            or burnin.is_reparse_point(temporary)
            or temporary.read_bytes() != payload
        ):
            raise burnin.EvidenceError(f"incomplete canonical publication exists: {temporary}")
    else:
        _write_exclusive(temporary, payload)
    if path.exists() or path.is_symlink() or burnin.is_reparse_point(path):
        raise burnin.EvidenceError(f"canonical artifact appeared during publication: {path}")
    try:
        temporary.rename(path)
    except FileExistsError as exc:
        raise burnin.EvidenceError(f"canonical artifact appeared during publication: {path}") from exc


def _validate_ledger_snapshot(
    snapshot: Mapping[str, Any], *, contract: Mapping[str, Any]
) -> dict[str, Any]:
    return burnin.validate_ledger_snapshot(snapshot, contract=contract)


def _require_snapshot_rows_in_ledger(
    snapshot: Mapping[str, Any], ledger_path: Path
) -> None:
    ledger = ledger_path.read_text(encoding="utf-8")
    for row in snapshot["rows"]:
        entry = [row["timestamp"], *row["fields"]]
        matches = burnin._ledger_entries(ledger, row["fields"][0], row["fields"][1])
        if matches.count(entry) != 1:
            raise burnin.EvidenceError("ledger snapshot row is not uniquely present")


def _load_approval_snapshot(contract: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    path = _approval_snapshot_path(contract)
    snapshot = _validate_ledger_snapshot(_load_canonical_json(path), contract=contract)
    if snapshot.get("kind") != "APPROVAL":
        raise burnin.EvidenceError("resource approval snapshot kind mismatch")
    return snapshot, burnin.file_hash_record(path)


def _acquire_manager_reservation(
    manager: Mapping[str, Path],
    *,
    candidate: Mapping[str, str],
    request_order: list[str],
    purpose: str,
) -> dict[str, Any]:
    """Exclusively reserve the global resource-manager writer slot."""

    active_lock = manager["active_lock"]
    root = manager.get("root", active_lock.parent)
    _cleanup_prepared_manager_reservations(manager)
    staging = root / f".{active_lock.name}.prepared-{os.getpid()}-{time.time_ns()}"
    try:
        staging.mkdir(exist_ok=False)
    except FileExistsError as exc:
        raise burnin.EvidenceError("manager reservation staging collision") from exc
    owner = {
        "acquired_at": _now(),
        "candidate": dict(candidate),
        "process_id": os.getpid(),
        "purpose": purpose,
        "request_order": list(request_order),
        "schema": MANAGER_RESERVATION_SCHEMA,
    }
    owner_path = staging / "owner.json"
    try:
        if (
            staging.resolve(strict=True) != staging
            or staging.is_symlink()
            or burnin.is_reparse_point(staging)
        ):
            raise burnin.EvidenceError("approval reservation is noncanonical")
        _write_exclusive(owner_path, burnin.canonical_json_bytes(owner))
        try:
            staging.rename(active_lock)
        except OSError as exc:
            if active_lock.exists() or active_lock.is_symlink() or burnin.is_reparse_point(
                active_lock
            ):
                raise burnin.EvidenceError("global resource slot is occupied") from exc
            raise
    except Exception:
        if owner_path.is_file() and not owner_path.is_symlink() and not burnin.is_reparse_point(owner_path):
            owner_path.unlink()
        try:
            staging.rmdir()
        except OSError:
            pass
        raise
    return owner


def _cleanup_prepared_manager_reservations(manager: Mapping[str, Path]) -> None:
    """Remove only exact, dead staging reservations left before atomic publication."""

    active_lock = manager["active_lock"]
    root = manager.get("root", active_lock.parent)
    pattern = re.compile(
        rf"\.{re.escape(active_lock.name)}\.prepared-(\d+)-(\d+)\Z"
    )
    for staging in root.iterdir():
        match = pattern.fullmatch(staging.name)
        if match is None:
            continue
        if not staging.is_dir() or staging.is_symlink() or burnin.is_reparse_point(staging):
            raise burnin.EvidenceError("prepared manager reservation is malformed")
        process_id = int(match.group(1))
        if _process_is_alive(process_id):
            continue
        children = list(staging.iterdir())
        if not children:
            staging.rmdir()
            continue
        if {path.name for path in children} != {"owner.json"}:
            raise burnin.EvidenceError("prepared manager reservation is malformed")
        owner = _load_canonical_json(staging / "owner.json")
        if owner.get("process_id") != process_id:
            raise burnin.EvidenceError("prepared manager reservation owner mismatch")
        # Validate the complete schema before deleting the exact dead staging record.
        temporary_manager = dict(manager)
        temporary_manager["active_lock"] = staging
        _load_manager_reservation(temporary_manager)
        (staging / "owner.json").unlink()
        staging.rmdir()


def _release_manager_reservation(
    manager: Mapping[str, Path], owner: Mapping[str, Any]
) -> None:
    active_lock = manager["active_lock"]
    owner_path = active_lock / "owner.json"
    if (
        not active_lock.is_dir()
        or active_lock.is_symlink()
        or burnin.is_reparse_point(active_lock)
        or {path.name for path in active_lock.iterdir()} != {"owner.json"}
        or owner_path.is_symlink()
        or burnin.is_reparse_point(owner_path)
        or _load_canonical_json(owner_path) != dict(owner)
    ):
        raise burnin.EvidenceError("approval reservation ownership mismatch")
    owner_path.unlink()
    active_lock.rmdir()


def _load_manager_reservation(manager: Mapping[str, Path]) -> dict[str, Any]:
    owner = burnin._exact_keys(
        _load_canonical_json(manager["active_lock"] / "owner.json"),
        {
            "acquired_at",
            "candidate",
            "process_id",
            "purpose",
            "request_order",
            "schema",
        },
        "$manager_reservation",
    )
    if owner["schema"] != MANAGER_RESERVATION_SCHEMA:
        raise burnin.EvidenceError("active lock is not a manager reservation")
    burnin._require_timestamp(owner["acquired_at"], "$manager_reservation.acquired_at")
    if not isinstance(owner["process_id"], int) or isinstance(owner["process_id"], bool):
        raise burnin.EvidenceError("manager reservation process ID is invalid")
    candidate = burnin._exact_keys(
        owner["candidate"], {"commit", "tree"}, "$manager_reservation.candidate"
    )
    if not all(
        isinstance(candidate[key], str) and burnin.GIT_OBJECT_RE.fullmatch(candidate[key])
        for key in ("commit", "tree")
    ):
        raise burnin.EvidenceError("manager reservation candidate is invalid")
    if (
        not isinstance(owner["purpose"], str)
        or not owner["purpose"]
        or not isinstance(owner["request_order"], list)
        or not all(
            isinstance(value, str) and burnin.REQUEST_ID_RE.fullmatch(value)
            for value in owner["request_order"]
        )
    ):
        raise burnin.EvidenceError("manager reservation scope is invalid")
    return owner


def _recover_manager_reservation(
    manager: Mapping[str, Path],
    *,
    candidate: Mapping[str, str],
    purposes: set[str],
    request_orders: set[tuple[str, ...]],
) -> bool:
    """Explicitly recover an exact interrupted publication reservation."""

    try:
        owner = _load_manager_reservation(manager)
    except burnin.EvidenceError:
        return False
    if (
        owner["candidate"] != dict(candidate)
        or owner["purpose"] not in purposes
        or tuple(owner["request_order"]) not in request_orders
    ):
        return False
    if _process_is_alive(owner["process_id"]):
        return False
    _release_manager_reservation(manager, owner)
    return True


def _process_is_alive(process_id: int) -> bool:
    """Conservatively report whether a manager-reservation owner is still alive."""

    if process_id == os.getpid():
        return True
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        process_query_limited_information = 0x1000
        still_active = 259
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel32.OpenProcess.restype = wintypes.HANDLE
        kernel32.GetExitCodeProcess.argtypes = [wintypes.HANDLE, wintypes.LPDWORD]
        kernel32.GetExitCodeProcess.restype = wintypes.BOOL
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel32.CloseHandle.restype = wintypes.BOOL
        handle = kernel32.OpenProcess(
            process_query_limited_information, False, process_id
        )
        if not handle:
            # Access denied may describe a live protected process; only an
            # invalid PID is safe to classify as dead.
            return ctypes.get_last_error() != 87
        try:
            exit_code = wintypes.DWORD()
            if not kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
                return True
            return exit_code.value == still_active
        finally:
            kernel32.CloseHandle(handle)
    try:
        os.kill(process_id, 0)
    except ProcessLookupError:
        return False
    except (PermissionError, OSError):
        return True
    return True


def _execution_started_fields(
    request: Mapping[str, Any],
    *,
    candidate: Mapping[str, Any],
    cycle: int,
    lane: str,
    launch: Mapping[str, Any],
) -> list[str]:
    return burnin.execution_started_ledger_fields(
        request,
        {"candidate": dict(candidate), "cycle": cycle, "lane": lane},
        launch,
    )


def _append_execution_started(
    ledger_path: Path,
    request: Mapping[str, Any],
    *,
    candidate: Mapping[str, Any],
    cycle: int,
    lane: str,
    launch: Mapping[str, Any],
) -> list[str]:
    ledger = ledger_path.read_text(encoding="utf-8")
    request_id = request["request_id"]
    if any(
        burnin._ledger_entries(ledger, request_id, status)
        for status in (
            "EXECUTION_STARTED",
            "COMPLETED_PASS",
            "COMPLETED_FAIL",
            "CANCELLED_NOT_RUN",
        )
    ):
        raise burnin.EvidenceError("resource request was already consumed")
    return _append_ledger_fields(
        ledger_path,
        _execution_started_fields(
            request,
            candidate=candidate,
            cycle=cycle,
            lane=lane,
            launch=launch,
        ),
    )


def _pending_manifest(
    contract: Mapping[str, Any],
    *,
    prefix: str,
    candidate: Mapping[str, Any],
    request_row: Mapping[str, Any],
    approval_snapshot: Mapping[str, Any],
) -> dict[str, Any]:
    match = re.fullmatch(r"cycle_(1|2)\.(functional|anyfem|performance)", prefix)
    if match is None:
        raise burnin.EvidenceError("pending manifests are resource-only")
    cycle, lane = int(match.group(1)), match.group(2)
    directory = _pending_output_directory(contract, prefix)
    final = burnin.process_output_directory(contract, prefix)
    return {
        "approval_snapshot": dict(approval_snapshot),
        "candidate": dict(candidate),
        "cycle": cycle,
        "lane": lane,
        "launch": burnin.file_hash_record(directory / "launch.json"),
        "request": {
            "bytes": request_row["bytes"],
            "request_id": request_row["request_id"],
            "sha256": request_row["request_sha256"],
        },
        "result": burnin.file_hash_record(directory / "result.json"),
        "schema": PENDING_MANIFEST_SCHEMA,
        "stderr": burnin.file_hash_record(directory / "stderr.txt"),
        "stdout": burnin.file_hash_record(directory / "stdout.txt"),
        "target_directory": final.name,
    }


def _validate_pending_manifest(
    contract: Mapping[str, Any], prefix: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    directory = _pending_output_directory(contract, prefix)
    path = directory / "pending-manifest.json"
    manifest = _load_canonical_json(path)
    expected_names = {
        "launch.json",
        "pending-manifest.json",
        "result.json",
        "stderr.txt",
        "stdout.txt",
    }
    children = list(directory.iterdir())
    if (
        {child.name for child in children} != expected_names
        or any(child.is_symlink() or burnin.is_reparse_point(child) for child in children)
    ):
        raise burnin.EvidenceError(f"pending output extent mismatch: {prefix}")
    if manifest.get("schema") != PENDING_MANIFEST_SCHEMA:
        raise burnin.EvidenceError("pending process manifest schema mismatch")
    burnin.validate_pending_manifest(manifest, contract=contract)
    for key, filename in (
        ("launch", "launch.json"),
        ("result", "result.json"),
        ("stderr", "stderr.txt"),
        ("stdout", "stdout.txt"),
    ):
        if burnin.file_hash_record(directory / filename) != manifest.get(key):
            raise burnin.EvidenceError(f"pending process manifest {key} mismatch")
    return manifest, burnin.file_hash_record(path)


def _append_terminal_ledger(
    ledger_path: Path,
    *,
    manifest_path: Path,
    pending_manifest_path: Path,
    request: Mapping[str, Any],
) -> list[str]:
    manifest = burnin.strict_json_load(manifest_path)
    result = burnin.file_hash_record(manifest_path)
    launch_path = manifest_path.parent / "launch.json"
    launch = _load_canonical_json(launch_path)
    burnin.validate_resource_launch(launch, contract=burnin.load_contract())
    ledger = ledger_path.read_text(encoding="utf-8")
    started = burnin._ledger_entries(
        ledger, request["request_id"], "EXECUTION_STARTED"
    )
    expected_started = burnin.execution_started_ledger_fields(
        request, launch, burnin.file_hash_record(launch_path)
    )
    if len(started) != 1 or started[0][1:] != expected_started:
        raise burnin.EvidenceError(
            "resource terminal publication lacks its exact execution-start row"
        )
    process = dict(manifest)
    process["status"] = (
        "PASS"
        if process["exit_code"] == 0
        and process["execution_state"] == "EXECUTED"
        and process["resource_lock_released"] is True
        else "FAIL"
    )
    process["pending_manifest_sha256"] = burnin.file_hash_record(pending_manifest_path)[
        "sha256"
    ]
    fields = burnin.terminal_ledger_fields(request, process, result)
    terminal_statuses = ("COMPLETED_PASS", "COMPLETED_FAIL", "CANCELLED_NOT_RUN")
    existing = [
        entry
        for status in terminal_statuses
        for entry in burnin._ledger_entries(ledger, request["request_id"], status)
    ]
    if existing:
        if len(existing) != 1 or existing[0][1:] != fields:
            raise burnin.EvidenceError("resource terminal ledger row conflicts with pending evidence")
        return existing[0]
    return _append_ledger_fields(ledger_path, fields)


def _require_resource_terminal(
    contract: Mapping[str, Any],
    prefix: str,
    manifest: Mapping[str, Any],
    *,
    expected_status: str = "PASS",
) -> dt.datetime:
    request_id = manifest["request_id"]
    row, request, _path = _request_payload(contract, request_id)
    manager = _manager_paths(contract)
    ledger = manager["ledger"].read_text(encoding="utf-8")
    ledger_status = "COMPLETED_PASS" if expected_status == "PASS" else "COMPLETED_FAIL"
    entries = burnin._ledger_entries(ledger, request_id, ledger_status)
    process = dict(manifest)
    process["status"] = expected_status
    directory = _existing_process_directory(contract, prefix, required=True)
    assert directory is not None
    result_record = burnin.file_hash_record(directory / "result.json")
    pending_path = directory / "pending-manifest.json"
    if not pending_path.is_file() or pending_path.is_symlink():
        raise burnin.EvidenceError("resource predecessor lacks its pending manifest")
    process["pending_manifest_sha256"] = burnin.file_hash_record(pending_path)["sha256"]
    expected = burnin.terminal_ledger_fields(request, process, result_record)
    if len(entries) != 1 or entries[0][1:] != expected:
        raise burnin.EvidenceError(f"predecessor terminal ledger mismatch: {request_id}")
    ended = dt.datetime.fromisoformat(manifest["ended_at"].replace("Z", "+00:00"))
    terminal = dt.datetime.fromisoformat(entries[0][0].replace("Z", "+00:00"))
    if terminal < ended:
        raise burnin.EvidenceError(f"predecessor terminal precedes completion: {request_id}")
    if row["request_id"] != request_id:
        raise burnin.EvidenceError("predecessor request authority mismatch")
    return terminal


def approve_requests() -> None:
    _bootstrap_authority()
    contract = burnin.load_contract()
    burnin.validate_resource_approval_authority(contract)
    _candidate, _siblings, candidate_commit, candidate_tree = _verify_repositories(contract)
    for prefix in (
        "common.quick.1",
        "common.package.1",
        "common.additive.1",
        "common.additive.2",
        "common.additive.3",
    ):
        _require_passed(contract, prefix)
    _require_package_artifacts(
        contract,
        candidate_commit=candidate_commit,
        candidate_tree=candidate_tree,
    )
    _assert_absent(
        contract, [f"cycle_{cycle}.{lane}" for cycle, lane in RESOURCE_ORDER]
    )
    manager = _manager_paths(contract)
    candidate_record = {"commit": candidate_commit, "tree": candidate_tree}
    snapshot_path = _approval_snapshot_path(contract)
    request_order = [
        row["request_id"]
        for cycle in ("cycle_1", "cycle_2")
        for row in contract["resource_requests"][cycle]
    ]
    if snapshot_path.exists() or snapshot_path.is_symlink() or burnin.is_reparse_point(snapshot_path):
        snapshot = _validate_ledger_snapshot(
            _load_canonical_json(snapshot_path), contract=contract
        )
        if (
            snapshot.get("kind") != "APPROVAL"
            or snapshot.get("candidate") != candidate_record
            or snapshot.get("request_order") != request_order
        ):
            raise burnin.EvidenceError("existing approval snapshot differs from authority")
        _require_snapshot_rows_in_ledger(snapshot, manager["ledger"])
        if manager["active_lock"].exists():
            if not _recover_manager_reservation(
                manager,
                candidate=candidate_record,
                purposes={"PUBLISH_S3_Q4_BURN_IN_APPROVALS"},
                request_orders={tuple(request_order)},
            ):
                raise burnin.EvidenceError("global resource slot is occupied")
        return
    pending_snapshot = snapshot_path.with_name(f".{snapshot_path.name}.pending")
    if manager["active_lock"].exists():
        if not _recover_manager_reservation(
            manager,
            candidate=candidate_record,
            purposes={"PUBLISH_S3_Q4_BURN_IN_APPROVALS"},
            request_orders={tuple(request_order)},
        ):
            raise burnin.EvidenceError("global resource slot is occupied")
    owner = _acquire_manager_reservation(
        manager,
        candidate=candidate_record,
        request_order=request_order,
        purpose="PUBLISH_S3_Q4_BURN_IN_APPROVALS",
    )
    try:
        if (
            pending_snapshot.exists()
            or pending_snapshot.is_symlink()
            or burnin.is_reparse_point(pending_snapshot)
        ):
            recovered = _load_canonical_json(pending_snapshot)
            snapshot = _validate_ledger_snapshot(recovered, contract=contract)
            if (
                snapshot.get("kind") != "APPROVAL"
                or snapshot.get("candidate") != candidate_record
                or snapshot.get("request_order") != request_order
            ):
                raise burnin.EvidenceError("recovered approval snapshot differs from authority")
            _require_snapshot_rows_in_ledger(snapshot, manager["ledger"])
            _write_canonical_json_once(snapshot_path, snapshot)
            return
        approval_entries: list[list[str]] = []
        for cycle, lane in RESOURCE_ORDER:
            row = next(
                item
                for item in contract["resource_requests"][f"cycle_{cycle}"]
                if item["lane"] == lane
            )
            _authority, request, _path = _request_payload(contract, row["request_id"])
            fields = burnin.approval_ledger_fields(request, row, candidate_record)
            ledger = manager["ledger"].read_text(encoding="utf-8")
            if any(
                burnin._ledger_entries(ledger, row["request_id"], status)
                for status in (
                    "EXECUTION_STARTED",
                    "COMPLETED_PASS",
                    "COMPLETED_FAIL",
                    "CANCELLED_NOT_RUN",
                )
            ):
                raise burnin.EvidenceError(
                    f"request was consumed before approval: {row['request_id']}"
                )
            entries = burnin._ledger_entries(ledger, row["request_id"], "APPROVED")
            if not entries:
                entry = _append_ledger_fields(manager["ledger"], fields)
            elif len(entries) == 1 and entries[0][1:] == fields:
                entry = entries[0]
            else:
                raise burnin.EvidenceError(
                    f"request approval row conflicts: {row['request_id']}"
                )
            approval_entries.append(entry)
        ledger_raw = manager["ledger"].read_bytes()
        snapshot = {
            "candidate": candidate_record,
            "kind": "APPROVAL",
            "request_order": request_order,
            "rows": [_ledger_row_object(entry) for entry in approval_entries],
            "schema": LEDGER_SNAPSHOT_SCHEMA,
            "source_ledger": {
                "bytes": len(ledger_raw),
                "sha256": burnin.sha256_bytes(ledger_raw),
            },
        }
        _validate_ledger_snapshot(snapshot, contract=contract)
        _write_canonical_json_once(snapshot_path, snapshot)
    finally:
        _release_manager_reservation(manager, owner)


def _lock_owner(manager: Mapping[str, Path], request: Mapping[str, Any]) -> None:
    owner_path = manager["active_lock"] / "owner.json"
    if not owner_path.is_file() or owner_path.is_symlink():
        raise burnin.EvidenceError("resource lock owner record is missing")
    owner = burnin.strict_json_loads(owner_path.read_text(encoding="utf-8-sig"))
    burnin._exact_keys(
        owner,
        {"acquired_at", "command", "process_id", "repository", "request_id", "task"},
        "$resource_lock.owner",
    )
    for key in ("command", "repository", "request_id", "task"):
        if owner[key] != request[key]:
            raise burnin.EvidenceError(f"resource lock owner {key} mismatch")
    burnin._require_timestamp(owner["acquired_at"], "$resource_lock.owner.acquired_at")
    if not isinstance(owner["process_id"], int) or isinstance(owner["process_id"], bool):
        raise burnin.EvidenceError("resource lock owner process ID is invalid")


def _terminate_worker_tree(
    worker: subprocess.Popen[bytes],
    *,
    policy: Mapping[str, Any],
    reason: str,
    stderr_stream: Any,
) -> dict[str, Any]:
    """Terminate one launched worker tree and return auditable disposition metadata."""

    if reason not in {"INTERRUPTED", "TIMEOUT"}:
        raise burnin.EvidenceError("bounded worker termination reason is invalid")
    if worker.poll() is not None:
        stderr_stream.write(
            f"bounded worker {reason.lower()}; child exit was already observable\n".encode()
        )
        return _termination_metadata(
            disposition="NORMAL_EXIT",
            policy=policy,
            tree_kill_attempted=False,
            tree_kill_exit_code=None,
            child_exit_observed=True,
        )

    termination_deadline = time.monotonic() + policy["termination_grace_seconds"]

    def remaining_termination_time() -> float:
        return max(0.001, termination_deadline - time.monotonic())

    taskkill_exit_code: int | None = None
    taskkill_stdout = b""
    taskkill_stderr = b""
    try:
        if os.name == "nt":
            arguments = [
                argument.replace("{pid}", str(worker.pid))
                for argument in policy["taskkill_arguments"]
            ]
            try:
                terminated = subprocess.run(
                    [str(policy["taskkill"]), *arguments],
                    capture_output=True,
                    check=False,
                    timeout=remaining_termination_time(),
                )
                taskkill_exit_code = terminated.returncode
                taskkill_stdout = terminated.stdout
                taskkill_stderr = terminated.stderr
            except subprocess.TimeoutExpired as exc:
                taskkill_exit_code = 258
                taskkill_stdout = exc.stdout or b""
                taskkill_stderr = (exc.stderr or b"") + b"taskkill timed out\n"
        else:
            os.killpg(worker.pid, signal.SIGKILL)
            taskkill_exit_code = 0
    except OSError as exc:
        taskkill_exit_code = 255
        taskkill_stderr = f"tree termination could not start: {exc}\n".encode(
            "utf-8", errors="replace"
        )

    stderr_stream.write(
        (
            f"bounded worker {reason.lower()}; complete child-tree termination "
            f"attempt exit code {taskkill_exit_code}\n"
        ).encode()
    )
    if taskkill_stdout:
        stderr_stream.write(b"taskkill stdout:\n" + taskkill_stdout)
        if not taskkill_stdout.endswith(b"\n"):
            stderr_stream.write(b"\n")
    if taskkill_stderr:
        stderr_stream.write(b"taskkill stderr:\n" + taskkill_stderr)
        if not taskkill_stderr.endswith(b"\n"):
            stderr_stream.write(b"\n")

    child_exit_observed = worker.poll() is not None
    if not child_exit_observed:
        try:
            worker.wait(timeout=remaining_termination_time())
            child_exit_observed = True
        except (OSError, subprocess.TimeoutExpired):
            stderr_stream.write(
                b"child exit was not observed within the termination grace period\n"
            )
            try:
                worker.kill()
                worker.wait(timeout=remaining_termination_time())
                child_exit_observed = True
            except (OSError, subprocess.TimeoutExpired):
                stderr_stream.write(b"direct child fallback termination failed\n")
    terminated_tree = taskkill_exit_code == 0 and child_exit_observed
    return _termination_metadata(
        disposition=(
            f"{reason}_TREE_TERMINATED"
            if terminated_tree
            else f"{reason}_TREE_TERMINATION_FAILED"
        ),
        policy=policy,
        tree_kill_attempted=True,
        tree_kill_exit_code=taskkill_exit_code,
        child_exit_observed=child_exit_observed,
    )


def _run_bounded_control_command(
    args: list[str],
    *,
    absolute_deadline: float,
    environment: Mapping[str, str],
    policy: Mapping[str, Any],
) -> tuple[subprocess.CompletedProcess[bytes], dict[str, Any]]:
    """Run one resource-manager command inside the invocation kill boundary."""

    returncode = 255
    termination = _termination_metadata(
        disposition="START_FAILED",
        policy=policy,
        tree_kill_attempted=False,
        tree_kill_exit_code=None,
        child_exit_observed=False,
    )
    with tempfile.TemporaryFile() as stdout_stream, tempfile.TemporaryFile() as stderr_stream:
        worker: subprocess.Popen[bytes] | None = None
        job_handle: int | None = None
        try:
            if absolute_deadline <= time.monotonic():
                raise burnin.EvidenceError("resource-control deadline expired before launch")
            options: dict[str, Any] = {}
            if os.name == "nt":
                options["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
            worker, job_handle = _launch_bounded_worker(
                args,
                env=dict(environment),
                stdout=stdout_stream,
                stderr=stderr_stream,
                **options,
            )
        except (OSError, burnin.EvidenceError) as exc:
            stderr_stream.write(
                f"resource-control start failed: {exc}\n".encode(
                    "utf-8", errors="replace"
                )
            )
        if worker is not None:
            child_exit_observed = False
            try:
                returncode = int(worker.wait(timeout=_remaining_budget(absolute_deadline)))
                child_exit_observed = True
                termination = _termination_metadata(
                    disposition="NORMAL_EXIT",
                    policy=policy,
                    tree_kill_attempted=False,
                    tree_kill_exit_code=None,
                    child_exit_observed=True,
                )
            except subprocess.TimeoutExpired:
                returncode = policy["timeout_exit_code"]
            except BaseException as exc:
                stderr_stream.write(
                    f"resource-control wait failed: {exc}\n".encode(
                        "utf-8", errors="replace"
                    )
                )
            finally:
                if not child_exit_observed:
                    try:
                        termination = _terminate_worker_tree(
                            worker,
                            policy=policy,
                            reason="TIMEOUT",
                            stderr_stream=stderr_stream,
                        )
                    except BaseException as exc:
                        stderr_stream.write(
                            f"resource-control cleanup failed: {exc}\n".encode(
                                "utf-8", errors="replace"
                            )
                        )
                        termination = _termination_metadata(
                            disposition="TIMEOUT_TREE_TERMINATION_FAILED",
                            policy=policy,
                            tree_kill_attempted=True,
                            tree_kill_exit_code=255,
                            child_exit_observed=False,
                        )
                if not _termination_proves_tree_absence(termination):
                    _RESOURCE_UNPROVEN_TREE.set()
                elif not _close_job_handle(job_handle):
                    _RESOURCE_UNPROVEN_TREE.set()
        stdout_stream.flush()
        stderr_stream.flush()
        stdout_stream.seek(0)
        stderr_stream.seek(0)
        completed = subprocess.CompletedProcess(
            args=args,
            returncode=returncode,
            stdout=stdout_stream.read(),
            stderr=stderr_stream.read(),
        )
    return completed, termination


def _run_resource_command(
    command: str,
    *,
    absolute_worker_deadline: float,
    contract: Mapping[str, Any],
    cwd: Path,
    output_dir: Path,
    process_prefix: str,
) -> tuple[subprocess.CompletedProcess[bytes], str, dict[str, Any]]:
    policy = _timeout_policy(contract)
    powershell = burnin.execution_tool_path(contract, "powershell")
    args = [str(powershell), "-NoProfile", "-Command", command]
    stdout_path = output_dir / "stdout.txt"
    stderr_path = output_dir / "stderr.txt"
    execution_state = "EXECUTED"
    returncode = 250
    termination = _termination_metadata(
        disposition="START_FAILED",
        policy=policy,
        tree_kill_attempted=False,
        tree_kill_exit_code=None,
        child_exit_observed=False,
    )
    try:
        with stdout_path.open("xb") as stdout_stream, stderr_path.open("xb") as stderr_stream:
            worker: subprocess.Popen[bytes] | None = None
            job_handle: int | None = None
            try:
                if absolute_worker_deadline <= time.monotonic():
                    raise burnin.EvidenceError(
                        "resource invocation exhausted its worker budget before launch"
                    )
                popen_options: dict[str, Any] = {}
                if os.name == "nt":
                    popen_options["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
                worker, job_handle = _launch_bounded_worker(
                    args,
                    cwd=cwd,
                    env=_execution_environment(contract, process_prefix=process_prefix),
                    stdout=stdout_stream,
                    stderr=stderr_stream,
                    **popen_options,
                )
            except (OSError, burnin.EvidenceError) as exc:
                execution_state = "NOT_STARTED"
                stderr_stream.write(
                    f"process start failed: {exc}\n".encode("utf-8", errors="replace")
                )
            if worker is not None:
                child_exit_observed = False
                cleanup_reason = "INTERRUPTED"
                try:
                    returncode = worker.wait(
                        timeout=_remaining_budget(absolute_worker_deadline)
                    )
                    child_exit_observed = True
                    termination = _termination_metadata(
                        disposition="NORMAL_EXIT",
                        policy=policy,
                        tree_kill_attempted=False,
                        tree_kill_exit_code=None,
                        child_exit_observed=True,
                    )
                except subprocess.TimeoutExpired:
                    cleanup_reason = "TIMEOUT"
                    returncode = policy["timeout_exit_code"]
                except KeyboardInterrupt:
                    returncode = 130
                except Exception as exc:
                    returncode = 250
                    stderr_stream.write(
                        (
                            "resource worker wait failed after launch; "
                            f"tree cleanup required: {exc}\n"
                        ).encode("utf-8", errors="replace")
                    )
                finally:
                    if not child_exit_observed:
                        try:
                            termination = _terminate_worker_tree(
                                worker,
                                policy=policy,
                                reason=cleanup_reason,
                                stderr_stream=stderr_stream,
                            )
                        except BaseException as exc:
                            stderr_stream.write(
                                f"resource tree cleanup failed: {exc}\n".encode(
                                    "utf-8", errors="replace"
                                )
                            )
                            termination = _termination_metadata(
                                disposition=f"{cleanup_reason}_TREE_TERMINATION_FAILED",
                                policy=policy,
                                tree_kill_attempted=True,
                                tree_kill_exit_code=255,
                                child_exit_observed=False,
                            )
                    if not _termination_proves_tree_absence(termination):
                        _RESOURCE_UNPROVEN_TREE.set()
                    elif not _close_job_handle(job_handle):
                        _RESOURCE_UNPROVEN_TREE.set()
                    if termination["disposition"] == "NORMAL_EXIT":
                        returncode = (
                            worker.returncode
                            if worker.returncode is not None
                            else returncode
                        )
            stdout_stream.flush()
            stderr_stream.flush()
            os.fsync(stdout_stream.fileno())
            os.fsync(stderr_stream.fileno())
    except FileExistsError as exc:
        raise burnin.EvidenceError("resource log output was not exclusive") from exc
    _validate_termination_metadata(
        termination, policy=policy, location="$resource_process.termination"
    )
    return (
        subprocess.CompletedProcess(
            args=args,
            returncode=returncode,
            stdout=stdout_path.read_bytes(),
            stderr=stderr_path.read_bytes(),
        ),
        execution_state,
        termination,
    )


def _replace_resource_logs(
    output_dir: Path, completed: subprocess.CompletedProcess[bytes]
) -> None:
    for name, payload in (("stdout", completed.stdout), ("stderr", completed.stderr)):
        path = output_dir / f"{name}.txt"
        if path.is_symlink() or burnin.is_reparse_point(path):
            raise burnin.EvidenceError("resource log path is noncanonical")
        if path.is_file() and path.read_bytes() == payload:
            continue
        replacement = path.with_name(f".{path.name}.replacement")
        if replacement.exists() or replacement.is_symlink() or burnin.is_reparse_point(
            replacement
        ):
            raise burnin.EvidenceError("resource log replacement path already exists")
        with replacement.open("xb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(replacement, path)


def _discard_unconsumed_pending(output_dir: Path | None) -> None:
    """Remove only an unconsumed empty/launch-only reservation after failed acquire setup."""

    if output_dir is None or not output_dir.exists():
        return
    if (
        not output_dir.is_dir()
        or output_dir.is_symlink()
        or burnin.is_reparse_point(output_dir)
    ):
        raise burnin.EvidenceError("unconsumed pending output is noncanonical")
    children = list(output_dir.iterdir())
    if {path.name for path in children} - {"launch.json"} or any(
        path.is_symlink() or burnin.is_reparse_point(path) for path in children
    ):
        raise burnin.EvidenceError("unconsumed pending output has unexpected content")
    for path in children:
        path.unlink()
    output_dir.rmdir()


def _write_worker_completion(
    output_dir: Path,
    *,
    candidate_commit: str,
    candidate_tree: str,
    command: str,
    completed: subprocess.CompletedProcess[bytes],
    elapsed_seconds: float,
    ended_at: str,
    execution_state: str,
    request_id: str,
    request_sha256: str,
    started_at: str,
    approval_snapshot: Mapping[str, Any],
    termination: Mapping[str, Any],
) -> dict[str, Any]:
    """Durably checkpoint a completed worker before releasing its resource lock."""

    value = _process_manifest(
        candidate_commit=candidate_commit,
        candidate_tree=candidate_tree,
        command=command,
        completed=completed,
        elapsed_seconds=elapsed_seconds,
        ended_at=ended_at,
        execution_state=execution_state,
        request_id=request_id,
        request_sha256=request_sha256,
        resource_lock_released=None,
        started_at=started_at,
        approval_snapshot=approval_snapshot,
        termination=termination,
    )
    value.pop("resource_lock_released")
    value["schema"] = WORKER_COMPLETION_SCHEMA
    for name in ("stdout", "stderr"):
        if burnin.file_hash_record(output_dir / f"{name}.txt") != value[name]:
            raise burnin.EvidenceError(f"worker completion {name} identity mismatch")
    _write_exclusive(
        output_dir / "worker-completion.json", burnin.canonical_json_bytes(value)
    )
    return value


def _load_worker_completion(
    output_dir: Path,
    *,
    contract: Mapping[str, Any],
    candidate: Mapping[str, str],
    request_row: Mapping[str, Any],
    approval_snapshot: Mapping[str, Any],
) -> dict[str, Any]:
    path = output_dir / "worker-completion.json"
    value = burnin._exact_keys(
        _load_canonical_json(path),
        {
            "approval_snapshot",
            "candidate_commit",
            "candidate_tree",
            "command_sha256",
            "elapsed_seconds",
            "ended_at",
            "execution_state",
            "exit_code",
            "producer_sha256",
            "request_id",
            "request_sha256",
            "schema",
            "started_at",
            "stderr",
            "stdout",
            "termination",
        },
        "$worker_completion",
    )
    if (
        value["schema"] != WORKER_COMPLETION_SCHEMA
        or value["candidate_commit"] != candidate["commit"]
        or value["candidate_tree"] != candidate["tree"]
        or value["request_id"] != request_row["request_id"]
        or value["request_sha256"] != request_row["request_sha256"]
        or value["command_sha256"] != request_row["command_sha256"]
        or value["producer_sha256"] != burnin.contract_producer_sha256(contract)
        or value["approval_snapshot"] != approval_snapshot
    ):
        raise burnin.EvidenceError("worker completion authority mismatch")
    burnin._require_timestamp(value["started_at"], "$worker_completion.started_at")
    burnin._require_timestamp(value["ended_at"], "$worker_completion.ended_at")
    if (
        not isinstance(value["elapsed_seconds"], (int, float))
        or isinstance(value["elapsed_seconds"], bool)
        or value["elapsed_seconds"] < 0
        or value["execution_state"] not in {"EXECUTED", "NOT_STARTED"}
        or not isinstance(value["exit_code"], int)
        or isinstance(value["exit_code"], bool)
    ):
        raise burnin.EvidenceError("worker completion process state is invalid")
    _validate_termination_metadata(
        value["termination"],
        policy=_timeout_policy(contract),
        location="$worker_completion.termination",
    )
    for name in ("stdout", "stderr"):
        burnin._validate_hash_record(value[name], f"$worker_completion.{name}")
        path = output_dir / f"{name}.txt"
        if (
            path.is_symlink()
            or burnin.is_reparse_point(path)
            or burnin.file_hash_record(path) != value[name]
        ):
            raise burnin.EvidenceError(f"worker completion {name} mismatch")
    return value


def _publish_resource_result(
    contract: Mapping[str, Any],
    *,
    prefix: str,
    candidate: Mapping[str, str],
    request_row: Mapping[str, Any],
    request: Mapping[str, Any],
    approval_snapshot: Mapping[str, Any],
    lock_released: bool,
) -> dict[str, Any]:
    """Finish one staged resource result without executing its worker again."""

    _require_package_artifacts(
        contract,
        candidate_commit=candidate["commit"],
        candidate_tree=candidate["tree"],
    )

    output_dir = _pending_output_directory(contract, prefix)
    result_path = output_dir / "result.json"
    completion_path = output_dir / "worker-completion.json"
    if completion_path.exists() or completion_path.is_symlink() or burnin.is_reparse_point(
        completion_path
    ):
        completion = _load_worker_completion(
            output_dir,
            contract=contract,
            candidate=candidate,
            request_row=request_row,
            approval_snapshot=approval_snapshot,
        )
        result = dict(completion)
        result["resource_lock_released"] = lock_released
        result["schema"] = PROCESS_RESULT_SCHEMA
        if result_path.exists() or result_path.is_symlink() or burnin.is_reparse_point(
            result_path
        ):
            if _load_canonical_json(result_path) != result:
                raise burnin.EvidenceError("staged resource result differs from completion")
        else:
            _write_exclusive(result_path, burnin.canonical_json_bytes(result))
        completion_path.unlink()
    else:
        result = _load_canonical_json(result_path)
        process = {
            key: result[key]
            for key in (
                "approval_snapshot",
                "command_sha256",
                "elapsed_seconds",
                "ended_at",
                "execution_state",
                "exit_code",
                "producer_sha256",
                "request_id",
                "resource_lock_released",
                "started_at",
                "stderr",
                "stdout",
                "termination",
            )
        }
        if process["resource_lock_released"] is not lock_released:
            raise burnin.EvidenceError("staged resource lock disposition mismatch")
        burnin._validate_process_result_artifact(
            result_path, candidate=candidate, process=process, request=request_row
        )
    if result["termination"]["disposition"].endswith("_TERMINATION_FAILED"):
        raise burnin.EvidenceError(
            "resource result cannot publish without proven child-tree termination"
        )
    pending = _pending_manifest(
        contract,
        prefix=prefix,
        candidate=candidate,
        request_row=request_row,
        approval_snapshot=approval_snapshot,
    )
    pending_path = output_dir / "pending-manifest.json"
    if pending_path.exists() or pending_path.is_symlink() or burnin.is_reparse_point(pending_path):
        if _load_canonical_json(pending_path) != pending:
            raise burnin.EvidenceError("staged pending manifest differs from completion")
    else:
        _write_exclusive(pending_path, burnin.canonical_json_bytes(pending))
    _validate_pending_manifest(contract, prefix)
    validated = _load_process_manifest(contract, prefix, required=True)
    if validated != result:
        raise burnin.EvidenceError("resource process changed during publication")
    _append_terminal_ledger(
        _manager_paths(contract)["ledger"],
        manifest_path=result_path,
        pending_manifest_path=pending_path,
        request=request,
    )
    _atomic_promote_directory(
        output_dir, burnin.process_output_directory(contract, prefix)
    )
    return result


def _run_resource_bounded(
    *,
    request_id: str,
    contract: Mapping[str, Any],
    timeout_policy: Mapping[str, Any],
    invocation_deadline: float,
    emit_manifest: bool = True,
    cycle_execution_capability: object | None = None,
) -> int:
    _request_execution_policy(contract)
    if cycle_execution_capability is not _CYCLE_RESOURCE_EXECUTION_CAPABILITY:
        _reject_standalone_resource_execution(contract, request_id)
    publication_deadline = (
        invocation_deadline - timeout_policy["termination_grace_seconds"]
    )
    worker_deadline = publication_deadline - (
        timeout_policy["termination_grace_seconds"]
        + timeout_policy["evidence_reserve_seconds"]
    )
    candidate, _siblings, candidate_commit, candidate_tree = _verify_repositories(contract)
    lane, cycle, prefix = _verify_resource_order(contract, request_id)
    _require_package_artifacts(
        contract,
        candidate_commit=candidate_commit,
        candidate_tree=candidate_tree,
    )
    row, request, _request_path = _request_payload(contract, request_id)
    repositories = burnin.external_repository_paths(contract)
    execution_repository = repositories["ANYfem" if lane == "anyfem" else "ANYsolver"]
    if Path(request["repository"]) != execution_repository:
        raise burnin.EvidenceError("resource execution repository is not the frozen binding")
    manager = _manager_paths(contract)
    approval_snapshot_value, approval_snapshot = _load_approval_snapshot(contract)
    if approval_snapshot_value["candidate"] != {
        "commit": candidate_commit,
        "tree": candidate_tree,
    }:
        raise burnin.EvidenceError("approval snapshot candidate mismatch")
    ledger = manager["ledger"].read_text(encoding="utf-8")
    expected_approval = burnin.approval_ledger_fields(
        request, row, {"commit": candidate_commit, "tree": candidate_tree}
    )
    approvals = burnin._ledger_entries(ledger, request_id, "APPROVED")
    if len(approvals) != 1 or approvals[0][1:] != expected_approval:
        raise burnin.EvidenceError("resource request lacks its exact approval")
    if any(
        _ledger_rows(ledger, request_id, state)
        for state in (
            "EXECUTION_STARTED",
            "COMPLETED_PASS",
            "COMPLETED_FAIL",
            "CANCELLED_NOT_RUN",
        )
    ):
        raise burnin.EvidenceError("resource request already has a terminal ledger row")
    if manager["active_lock"].exists():
        raise burnin.EvidenceError("global resource slot is occupied")
    execution_environment = _execution_environment(contract, process_prefix=prefix)
    powershell = burnin.execution_tool_path(contract, "powershell")
    acquire_args = _manager_script_args(powershell, manager["acquire"], request_id)
    release_args = _manager_script_args(powershell, manager["release"], request_id)
    started_at = _now()
    started = time.perf_counter()
    command = request["command"]
    completed = subprocess.CompletedProcess(
        args=[str(powershell), "-NoProfile", "-Command", command],
        returncode=252,
        stdout=b"",
        stderr=b"resource command was not started\n",
    )
    execution_state = "NOT_STARTED"
    termination = _termination_metadata(
        disposition="START_FAILED",
        policy=timeout_policy,
        tree_kill_attempted=False,
        tree_kill_exit_code=None,
        child_exit_observed=False,
    )
    acquired_lock = False
    lock_released = False
    launch_written = False
    completion_written = False
    output_dir: Path | None = None
    pending_error: Exception | None = None
    completion_error: Exception | None = None
    try:
        if worker_deadline <= time.monotonic():
            raise burnin.EvidenceError(
                "resource invocation exhausted its acquisition budget"
            )
        acquired, _acquire_termination = _run_bounded_control_command(
            acquire_args,
            absolute_deadline=worker_deadline,
            environment=execution_environment,
            policy=timeout_policy,
        )
        if _RESOURCE_UNPROVEN_TREE.is_set():
            raise burnin.EvidenceError(
                "resource acquisition requires proven control-tree closure"
            )
        if acquired.returncode:
            raise burnin.EvidenceError(
                "resource acquisition failed: "
                + (acquired.stderr or acquired.stdout).decode("utf-8", errors="replace")
            )
        acquired_lock = True
        _lock_owner(manager, request)
        output_dir = _reserve_pending_output(contract, prefix)
        owner_path = manager["active_lock"] / "owner.json"
        launch = {
            "approval_snapshot": dict(approval_snapshot),
            "candidate": {"commit": candidate_commit, "tree": candidate_tree},
            "command_sha256": row["command_sha256"],
            "cycle": cycle,
            "lane": lane,
            "lock_owner": burnin.file_hash_record(owner_path),
            "request": {
                "bytes": row["bytes"],
                "request_id": request_id,
                "sha256": row["request_sha256"],
            },
            "schema": "anysolver.e4-pl-s3-q4-resource-launch-v1",
            "started_at": started_at,
            "target_directory": burnin.process_output_directory(contract, prefix).name,
        }
        burnin.validate_resource_launch(launch, contract=contract)
        _write_exclusive(output_dir / "launch.json", burnin.canonical_json_bytes(launch))
        launch_record = burnin.file_hash_record(output_dir / "launch.json")
        try:
            _append_execution_started(
                manager["ledger"],
                request,
                candidate={"commit": candidate_commit, "tree": candidate_tree},
                cycle=cycle,
                lane=lane,
                launch=launch_record,
            )
            launch_written = True
        except burnin.EvidenceError:
            expected_started = burnin.execution_started_ledger_fields(
                request, launch, launch_record
            )
            started_rows = burnin._ledger_entries(
                manager["ledger"].read_text(encoding="utf-8"),
                request_id,
                "EXECUTION_STARTED",
            )
            if len(started_rows) == 1 and started_rows[0][1:] == expected_started:
                launch_written = True
            raise
        completed, execution_state, termination = _run_resource_command(
            command,
            absolute_worker_deadline=worker_deadline,
            contract=contract,
            cwd=execution_repository,
            output_dir=output_dir,
            process_prefix=prefix,
        )
        if _RESOURCE_UNPROVEN_TREE.is_set():
            raise burnin.EvidenceError(
                "resource completion requires proven child-tree closure"
            )
        try:
            _candidate, _bound_siblings, post_commit, post_tree = _verify_repositories(contract)
            if (post_commit, post_tree) != (candidate_commit, candidate_tree):
                raise burnin.EvidenceError("candidate identity changed during resource execution")
        except burnin.EvidenceError as exc:
            completed = subprocess.CompletedProcess(
                args=completed.args,
                returncode=253,
                stdout=completed.stdout,
                stderr=completed.stderr
                + f"\npost-execution authority failure: {exc}\n".encode(),
            )
    except (burnin.EvidenceError, OSError, subprocess.TimeoutExpired) as exc:
        if not launch_written:
            pending_error = exc
        else:
            completed = subprocess.CompletedProcess(
                args=completed.args,
                returncode=254,
                stdout=completed.stdout,
                stderr=completed.stderr + f"\nresource authority failure: {exc}\n".encode(),
            )
    finally:
        try:
            if (
                launch_written
                and output_dir is not None
                and not _RESOURCE_UNPROVEN_TREE.is_set()
            ):
                ended_at = _now()
                elapsed = time.perf_counter() - started
                _replace_resource_logs(output_dir, completed)
                _write_worker_completion(
                    output_dir,
                    candidate_commit=candidate_commit,
                    candidate_tree=candidate_tree,
                    command=command,
                    completed=completed,
                    elapsed_seconds=elapsed,
                    ended_at=ended_at,
                    execution_state=execution_state,
                    request_id=request_id,
                    request_sha256=row["request_sha256"],
                    started_at=started_at,
                    approval_snapshot=approval_snapshot,
                    termination=termination,
                )
                completion_written = True
        except (burnin.EvidenceError, OSError) as exc:
            completion_error = exc
        finally:
            safe_to_release = (
                _termination_proves_tree_absence(termination)
                and not _RESOURCE_UNPROVEN_TREE.is_set()
            )
            if acquired_lock and safe_to_release:
                try:
                    released, _release_termination = _run_bounded_control_command(
                        release_args,
                        absolute_deadline=publication_deadline,
                        environment=execution_environment,
                        policy=timeout_policy,
                    )
                except OSError as exc:
                    released = subprocess.CompletedProcess(
                        args=release_args,
                        returncode=255,
                        stdout=b"",
                        stderr=f"resource lock release could not start: {exc}\n".encode(),
                    )
                lock_released = (
                    released.returncode == 0
                    and not manager["active_lock"].exists()
                    and not _RESOURCE_UNPROVEN_TREE.is_set()
                )
    if pending_error is not None:
        _discard_unconsumed_pending(output_dir)
        raise pending_error
    if not launch_written:
        raise burnin.EvidenceError("resource request was not durably launched")
    if completion_error is not None:
        raise burnin.EvidenceError(
            f"resource completion checkpoint failed after request consumption: {completion_error}"
        ) from completion_error
    if not completion_written or output_dir is None:
        raise burnin.EvidenceError("resource worker lacks its durable completion checkpoint")
    if not lock_released:
        if termination["disposition"].endswith("_TERMINATION_FAILED"):
            raise burnin.EvidenceError(
                "resource lock retained because complete child-tree termination was not proven"
            )
        raise burnin.EvidenceError(
            "resource lock release failed; use finalize-resource without rerunning the worker"
        )
    candidate_record = {"commit": candidate_commit, "tree": candidate_tree}
    owner = _acquire_manager_reservation(
        manager,
        candidate=candidate_record,
        request_order=[request_id],
        purpose="PUBLISH_S3_Q4_RESOURCE_RESULT",
    )
    try:
        manifest = _publish_resource_result(
            contract,
            prefix=prefix,
            candidate=candidate_record,
            request_row=row,
            request=request,
            approval_snapshot=approval_snapshot,
            lock_released=True,
        )
    finally:
        _release_manager_reservation(manager, owner)
    _publish_completed_cycles(contract)
    if emit_manifest:
        sys.stdout.buffer.write(burnin.canonical_json_bytes(manifest))
        sys.stdout.buffer.flush()
    return int(manifest["exit_code"])


def run_resource(*, request_id: str) -> int:
    """Reject standalone execution; use the ``cycle --cycle N`` command."""

    _RESOURCE_UNPROVEN_TREE.clear()
    invocation_deadline, watchdog_stop, watchdog_thread = (
        _start_resource_invocation_watchdog(_EARLY_RESOURCE_TIMEOUT_POLICY)
    )
    try:
        _bootstrap_authority()
        contract = burnin.load_contract()
        timeout_policy = _timeout_policy(contract)
        _validate_early_watchdog_policy(timeout_policy)
        _reject_standalone_resource_execution(contract, request_id)
        raise AssertionError("standalone resource rejection returned unexpectedly")
    finally:
        if _RESOURCE_UNPROVEN_TREE.is_set():
            _hold_for_resource_watchdog(watchdog_thread)
        else:
            watchdog_stop.set()
            watchdog_thread.join(timeout=0.1)


def _cycle_request_rows(contract: Mapping[str, Any], cycle: int) -> list[dict[str, Any]]:
    return list(contract["resource_requests"][f"cycle_{cycle}"])


def _validate_cycle_request_rows(
    contract: Mapping[str, Any], cycle: int
) -> list[dict[str, Any]]:
    """Validate all three requests before the cycle consumes its first one."""

    if type(cycle) is not int or cycle not in (1, 2):
        raise burnin.EvidenceError("resource cycle must be exactly 1 or 2")
    rows = _cycle_request_rows(contract, cycle)
    if (
        len(rows) != len(_RESOURCE_LANES)
        or tuple(row.get("lane") for row in rows) != _RESOURCE_LANES
    ):
        raise burnin.EvidenceError("resource cycle lane order mismatch")
    request_ids = [row.get("request_id") for row in rows]
    if (
        any(not isinstance(request_id, str) or not request_id for request_id in request_ids)
        or len(set(request_ids)) != len(request_ids)
    ):
        raise burnin.EvidenceError("resource cycle request IDs are not unique strings")

    # This proves the common preflight, the prior cycle (when applicable), and
    # the absence of all current/future canonical outputs before any request is
    # consumed by this command.
    _verify_resource_order(contract, request_ids[0])
    candidate, _siblings, candidate_commit, candidate_tree = _verify_repositories(contract)
    candidate_record = {"commit": candidate_commit, "tree": candidate_tree}
    approval_snapshot, _approval_record = _load_approval_snapshot(contract)
    if approval_snapshot["candidate"] != candidate_record:
        raise burnin.EvidenceError("cycle approval snapshot candidate mismatch")
    manager = _manager_paths(contract)
    if manager["active_lock"].exists():
        raise burnin.EvidenceError("global resource slot is occupied")
    ledger = manager["ledger"].read_text(encoding="utf-8")
    repositories = burnin.external_repository_paths(contract)

    validated: list[dict[str, Any]] = []
    for lane, row, request_id in zip(_RESOURCE_LANES, rows, request_ids, strict=True):
        positioned_cycle, positioned_lane, _index = _resource_position(
            contract, request_id
        )
        if positioned_cycle != cycle or positioned_lane != lane:
            raise burnin.EvidenceError("resource cycle request position mismatch")
        authority, request, _request_path = _request_payload(contract, request_id)
        if authority != row:
            raise burnin.EvidenceError("resource cycle authority row mismatch")
        expected_repository = repositories["ANYfem"] if lane == "anyfem" else candidate
        if Path(request["repository"]) != expected_repository:
            raise burnin.EvidenceError("resource cycle execution repository mismatch")
        expected_approval = burnin.approval_ledger_fields(
            request, authority, candidate_record
        )
        approvals = burnin._ledger_entries(ledger, request_id, "APPROVED")
        if len(approvals) != 1 or approvals[0][1:] != expected_approval:
            raise burnin.EvidenceError("resource cycle request lacks exact approval")
        if any(
            burnin._ledger_entries(ledger, request_id, status)
            for status in (
                "EXECUTION_STARTED",
                "COMPLETED_PASS",
                "COMPLETED_FAIL",
                "CANCELLED_NOT_RUN",
            )
        ):
            raise burnin.EvidenceError("resource cycle request was already consumed")
        validated.append(dict(row))
    return validated


def _emit_cycle_terminal_snapshot(contract: Mapping[str, Any], cycle: int) -> None:
    snapshot = _cycle_terminal_snapshot(contract, cycle)
    if snapshot is None:
        raise burnin.EvidenceError("complete resource cycle lacks its terminal snapshot")
    sys.stdout.buffer.write(burnin.canonical_json_bytes(snapshot))
    sys.stdout.buffer.flush()


def _run_cycle_bounded(
    *,
    cycle: int,
    contract: Mapping[str, Any],
    timeout_policy: Mapping[str, Any],
    invocation_deadline: float,
) -> int:
    """Run one three-request cycle against one absolute 20-minute clock."""

    _request_execution_policy(contract)
    cycle_policy = _cycle_wall_policy(contract)
    if (
        timeout_policy["wall_limit_seconds"]
        != cycle_policy["absolute_wall_limit_seconds"]
    ):
        raise burnin.EvidenceError("cycle watchdog and contract wall limits differ")
    invocation_started = (
        invocation_deadline - cycle_policy["absolute_wall_limit_seconds"]
    )
    cycle_deadline = invocation_started + cycle_policy["absolute_wall_limit_seconds"]
    if cycle_deadline != invocation_deadline:
        raise burnin.EvidenceError("cycle deadline is not derived from one absolute clock")

    rows = _validate_cycle_request_rows(contract, cycle)
    deadlines = cycle_policy["cumulative_deadlines_seconds"]
    for row in rows:
        lane = row["lane"]
        lane_deadline = invocation_started + deadlines[lane]
        if lane_deadline >= cycle_deadline:
            raise burnin.EvidenceError("resource lane consumes the final evidence reserve")
        status = _run_resource_bounded(
            request_id=row["request_id"],
            contract=contract,
            timeout_policy=timeout_policy,
            invocation_deadline=lane_deadline,
            emit_manifest=False,
            cycle_execution_capability=_CYCLE_RESOURCE_EXECUTION_CAPABILITY,
        )
        if status != 0:
            # The failed request is already terminal and its lock has been
            # released.  Record every later approved request as not run; never
            # launch or retry it.
            cancel_remaining()
            _emit_cycle_terminal_snapshot(contract, cycle)
            return status
        if time.monotonic() > lane_deadline:
            raise burnin.EvidenceError(
                f"{lane} completed after its cumulative cycle deadline"
            )

    # The performance lane must return by 1110 seconds.  Everything below is
    # evidence validation/publication and remains covered by the same watchdog.
    if time.monotonic() >= cycle_deadline:
        raise burnin.EvidenceError("complete cycle exhausted its evidence reserve")
    _publish_completed_cycles(contract)
    _emit_cycle_terminal_snapshot(contract, cycle)
    return 0


def _cycle_terminal_snapshot(
    contract: Mapping[str, Any], cycle: int
) -> dict[str, Any] | None:
    manager = _manager_paths(contract)
    ledger_raw = manager["ledger"].read_bytes()
    ledger = ledger_raw.decode("utf-8")
    candidate = burnin.external_repository_paths(contract)["ANYsolver"]
    candidate_record = {
        "commit": burnin._git(candidate, "rev-parse", "HEAD", contract=contract),
        "tree": burnin._git(candidate, "rev-parse", "HEAD^{tree}", contract=contract),
    }
    approval_snapshot, approval_record = _load_approval_snapshot(contract)
    if approval_snapshot["candidate"] != candidate_record:
        raise burnin.EvidenceError("approval snapshot candidate changed")
    rows: list[dict[str, Any]] = []
    request_order: list[str] = []
    for authority in _cycle_request_rows(contract, cycle):
        request_id = authority["request_id"]
        request_order.append(request_id)
        _row, request, _path = _request_payload(contract, request_id)
        approval_fields = burnin.approval_ledger_fields(
            request, authority, candidate_record
        )
        approvals = burnin._ledger_entries(ledger, request_id, "APPROVED")
        if len(approvals) != 1 or approvals[0][1:] != approval_fields:
            raise burnin.EvidenceError(f"cycle approval row mismatch: {request_id}")
        started = burnin._ledger_entries(ledger, request_id, "EXECUTION_STARTED")
        terminals = [
            entry
            for status in ("COMPLETED_PASS", "COMPLETED_FAIL", "CANCELLED_NOT_RUN")
            for entry in burnin._ledger_entries(ledger, request_id, status)
        ]
        if not terminals:
            return None
        if len(terminals) != 1 or len(started) > 1:
            raise burnin.EvidenceError(f"cycle terminal multiplicity mismatch: {request_id}")
        if terminals[0][2] == "CANCELLED_NOT_RUN":
            if started:
                raise burnin.EvidenceError("cancelled request has an execution-start row")
            expected_terminal = burnin.terminal_ledger_fields(
                request, {"request_id": request_id, "status": "NOT_RUN"}, None
            )
            if terminals[0][1:] != expected_terminal:
                raise burnin.EvidenceError("cancelled request terminal row mismatch")
        elif len(started) != 1:
            raise burnin.EvidenceError("executed request lacks one execution-start row")
        else:
            prefix = f"cycle_{cycle}.{authority['lane']}"
            directory = _existing_process_directory(contract, prefix, required=True)
            assert directory is not None
            launch_path = directory / "launch.json"
            launch = _load_canonical_json(launch_path)
            burnin.validate_resource_launch(launch, contract=contract)
            expected_started = burnin.execution_started_ledger_fields(
                request, launch, burnin.file_hash_record(launch_path)
            )
            if started[0][1:] != expected_started:
                raise burnin.EvidenceError("execution-start ledger row mismatch")
            manifest = _load_process_manifest(contract, prefix, required=True)
            assert manifest is not None
            expected_status = "PASS" if _manifest_passed(manifest) else "FAIL"
            expected_terminal_status = (
                "COMPLETED_PASS" if expected_status == "PASS" else "COMPLETED_FAIL"
            )
            if terminals[0][2] != expected_terminal_status:
                raise burnin.EvidenceError("resource terminal status differs from process result")
            _require_resource_terminal(
                contract, prefix, manifest, expected_status=expected_status
            )
        rows.append(
            {
                "approval": _ledger_row_object(approvals[0]),
                "execution_started": (
                    None if not started else _ledger_row_object(started[0])
                ),
                "terminal": _ledger_row_object(terminals[0]),
            }
        )
    predecessor_path = (
        _approval_snapshot_path(contract)
        if cycle == 1
        else _cycle_snapshot_path(contract, cycle - 1)
    )
    if cycle == 1:
        predecessor = approval_record
    else:
        if (
            not predecessor_path.is_file()
            or predecessor_path.is_symlink()
            or burnin.is_reparse_point(predecessor_path)
        ):
            return None
        predecessor = burnin.file_hash_record(predecessor_path)
    return {
        "candidate": candidate_record,
        "cycle": cycle,
        "kind": "CYCLE_TERMINAL",
        "predecessor": predecessor,
        "request_order": request_order,
        "rows": rows,
        "schema": LEDGER_SNAPSHOT_SCHEMA,
        "source_ledger": {
            "bytes": len(ledger_raw),
            "sha256": burnin.sha256_bytes(ledger_raw),
        },
    }


def _promote_cycle_outputs(contract: Mapping[str, Any], cycle: int) -> None:
    for authority in _cycle_request_rows(contract, cycle):
        prefix = f"cycle_{cycle}.{authority['lane']}"
        pending = _pending_output_directory(contract, prefix)
        final = burnin.process_output_directory(contract, prefix)
        if final.exists() or final.is_symlink() or burnin.is_reparse_point(final):
            if pending.exists() or pending.is_symlink() or burnin.is_reparse_point(pending):
                raise burnin.EvidenceError("both pending and canonical resource output exist")
            if (
                not final.is_dir()
                or final.is_symlink()
                or burnin.is_reparse_point(final)
            ):
                raise burnin.EvidenceError("canonical resource output is noncanonical")
            continue
        if pending.exists() or pending.is_symlink() or burnin.is_reparse_point(pending):
            _validate_pending_manifest(contract, prefix)
            _atomic_promote_directory(pending, final)


def _publish_completed_cycles(contract: Mapping[str, Any]) -> None:
    manager = _manager_paths(contract)
    approval, _approval_record = _load_approval_snapshot(contract)
    request_order = [
        row["request_id"]
        for cycle in ("cycle_1", "cycle_2")
        for row in contract["resource_requests"][cycle]
    ]
    if manager["active_lock"].exists() and not _recover_manager_reservation(
        manager,
        candidate=approval["candidate"],
        purposes={"PUBLISH_S3_Q4_CYCLE_SNAPSHOTS"},
        request_orders={tuple(request_order)},
    ):
        raise burnin.EvidenceError("cannot publish while the global slot is occupied")
    owner = _acquire_manager_reservation(
        manager,
        candidate=approval["candidate"],
        request_order=request_order,
        purpose="PUBLISH_S3_Q4_CYCLE_SNAPSHOTS",
    )
    try:
        for cycle in (1, 2):
            path = _cycle_snapshot_path(contract, cycle)
            snapshot = _cycle_terminal_snapshot(contract, cycle)
            if snapshot is None:
                return
            if path.exists() or path.is_symlink() or burnin.is_reparse_point(path):
                existing = _validate_ledger_snapshot(
                    _load_canonical_json(path), contract=contract
                )
                comparable = dict(snapshot)
                existing_comparable = dict(existing)
                comparable.pop("source_ledger", None)
                existing_comparable.pop("source_ledger", None)
                if existing_comparable != comparable:
                    raise burnin.EvidenceError(
                        "published cycle snapshot differs from terminal rows"
                    )
                snapshot = existing
            elif (
                path.with_name(f".{path.name}.pending").exists()
                or path.with_name(f".{path.name}.pending").is_symlink()
                or burnin.is_reparse_point(path.with_name(f".{path.name}.pending"))
            ):
                recovered = _load_canonical_json(path.with_name(f".{path.name}.pending"))
                recovered = _validate_ledger_snapshot(recovered, contract=contract)
                comparable = dict(snapshot)
                recovered_comparable = dict(recovered)
                comparable.pop("source_ledger", None)
                recovered_comparable.pop("source_ledger", None)
                if recovered_comparable != comparable:
                    raise burnin.EvidenceError(
                        "recovered cycle snapshot differs from terminal rows"
                    )
                snapshot = recovered
            _validate_ledger_snapshot(snapshot, contract=contract)
            _write_canonical_json_once(path, snapshot)
            _promote_cycle_outputs(contract, cycle)
    finally:
        _release_manager_reservation(manager, owner)


def finalize_resource(*, request_id: str, invocation_deadline: float) -> int:
    """Finish evidence publication for one consumed request without launching it."""

    _bootstrap_authority()
    contract = burnin.load_contract()
    _request_execution_policy(contract)
    timeout_policy = _timeout_policy(contract)
    _validate_early_watchdog_policy(timeout_policy)
    publication_deadline = (
        invocation_deadline - timeout_policy["termination_grace_seconds"]
    )
    _candidate, _siblings, candidate_commit, candidate_tree = _verify_repositories(contract)
    _require_package_artifacts(
        contract,
        candidate_commit=candidate_commit,
        candidate_tree=candidate_tree,
    )
    cycle, lane, _index = _resource_position(contract, request_id)
    prefix = f"cycle_{cycle}.{lane}"
    manager = _manager_paths(contract)
    candidate_record = {"commit": candidate_commit, "tree": candidate_tree}
    all_request_order = tuple(
        row["request_id"]
        for cycle_name in ("cycle_1", "cycle_2")
        for row in contract["resource_requests"][cycle_name]
    )
    directory = _existing_process_directory(contract, prefix, required=True)
    assert directory is not None
    approval_value, approval_record = _load_approval_snapshot(contract)
    row, request, _request_path = _request_payload(contract, request_id)
    if approval_value["candidate"] != candidate_record:
        raise burnin.EvidenceError("finalizer approval candidate mismatch")
    if directory == _pending_output_directory(contract, prefix):
        completion = _load_worker_completion(
            directory,
            contract=contract,
            candidate=candidate_record,
            request_row=row,
            approval_snapshot=approval_record,
        )
        if completion["termination"]["disposition"].endswith(
            "_TERMINATION_FAILED"
        ):
            raise burnin.EvidenceError(
                "finalizer cannot release a lock without proven child-tree termination"
            )
    if manager["active_lock"].exists():
        recovered = _recover_manager_reservation(
            manager,
            candidate=candidate_record,
            purposes={
                "PUBLISH_S3_Q4_RESOURCE_RESULT",
                "FINALIZE_S3_Q4_RESOURCE_RESULT",
                "PUBLISH_S3_Q4_CYCLE_SNAPSHOTS",
            },
            request_orders={(request_id,), all_request_order},
        )
        if not recovered:
            _lock_owner(manager, request)
            if directory != _pending_output_directory(contract, prefix):
                raise burnin.EvidenceError(
                    "live resource lock lacks its pending publication directory"
                )
            powershell = burnin.execution_tool_path(contract, "powershell")
            released, _release_termination = _run_bounded_control_command(
                _manager_script_args(
                    powershell, manager["release"], request_id
                ),
                absolute_deadline=publication_deadline,
                environment=_manager_environment(contract),
                policy=timeout_policy,
            )
            if _RESOURCE_UNPROVEN_TREE.is_set():
                raise burnin.EvidenceError(
                    "finalizer publication requires proven control-tree closure"
                )
            if released.returncode or manager["active_lock"].exists():
                raise burnin.EvidenceError(
                    "finalizer could not release the consumed request lock"
                )
    if _RESOURCE_UNPROVEN_TREE.is_set():
        raise burnin.EvidenceError(
            "finalizer publication requires proven child-tree closure"
        )
    owner = _acquire_manager_reservation(
        manager,
        candidate=candidate_record,
        request_order=[request_id],
        purpose="FINALIZE_S3_Q4_RESOURCE_RESULT",
    )
    try:
        if directory == burnin.process_output_directory(contract, prefix):
            manifest = _load_process_manifest(contract, prefix, required=True)
            assert manifest is not None
            _require_resource_terminal(
                contract,
                prefix,
                manifest,
                expected_status="PASS" if _manifest_passed(manifest) else "FAIL",
            )
        else:
            manifest = _publish_resource_result(
                contract,
                prefix=prefix,
                candidate=candidate_record,
                request_row=row,
                request=request,
                approval_snapshot=approval_record,
                lock_released=True,
            )
    finally:
        _release_manager_reservation(manager, owner)
    _publish_completed_cycles(contract)
    status = 0 if _manifest_passed(manifest) else int(manifest["exit_code"] or 1)
    return status


def cancel_remaining() -> None:
    _bootstrap_authority()
    contract = burnin.load_contract()
    _candidate, _siblings, candidate_commit, candidate_tree = _verify_repositories(contract)
    manager = _manager_paths(contract)
    request_order = [
        row["request_id"]
        for cycle in ("cycle_1", "cycle_2")
        for row in contract["resource_requests"][cycle]
    ]
    if manager["active_lock"].exists() and not _recover_manager_reservation(
        manager,
        candidate={"commit": candidate_commit, "tree": candidate_tree},
        purposes={"CANCEL_S3_Q4_REMAINING_REQUESTS"},
        request_orders={tuple(request_order)},
    ):
        raise burnin.EvidenceError("cannot cancel while the global slot is occupied")
    owner = _acquire_manager_reservation(
        manager,
        candidate={"commit": candidate_commit, "tree": candidate_tree},
        request_order=request_order,
        purpose="CANCEL_S3_Q4_REMAINING_REQUESTS",
    )
    try:
        failure_index: int | None = None
        failure_terminal: dt.datetime | None = None
        for index, (cycle, lane) in enumerate(RESOURCE_ORDER):
            prefix = f"cycle_{cycle}.{lane}"
            manifest = _load_process_manifest(contract, prefix, required=False)
            if manifest is None:
                break
            if not _manifest_passed(manifest):
                failure_index = index
                failure_terminal = _require_resource_terminal(
                    contract, prefix, manifest, expected_status="FAIL"
                )
                break
            _require_resource_terminal(contract, prefix, manifest)
        if failure_index is None:
            raise burnin.EvidenceError("no failed resource process authorizes cancellation")
        timestamp = _now()
        cancellation_time = dt.datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        assert failure_terminal is not None
        if cancellation_time < failure_terminal:
            raise burnin.EvidenceError("cancellation precedes failed-request terminal")
        for cycle, lane in RESOURCE_ORDER[failure_index + 1 :]:
            row = next(
                item
                for item in contract["resource_requests"][f"cycle_{cycle}"]
                if item["lane"] == lane
            )
            authority, request, _path = _request_payload(contract, row["request_id"])
            ledger = manager["ledger"].read_text(encoding="utf-8")
            approvals = burnin._ledger_entries(ledger, row["request_id"], "APPROVED")
            expected_approval = burnin.approval_ledger_fields(
                request,
                authority,
                {"commit": candidate_commit, "tree": candidate_tree},
            )
            if len(approvals) != 1 or approvals[0][1:] != expected_approval:
                raise burnin.EvidenceError("only approved later requests may be cancelled")
            if burnin._ledger_entries(ledger, row["request_id"], "EXECUTION_STARTED"):
                raise burnin.EvidenceError("a started request may not be cancelled")
            prefix = f"cycle_{cycle}.{lane}"
            if _existing_process_directory(contract, prefix, required=False) is not None:
                raise burnin.EvidenceError("a request with process output cannot be cancelled")
            process = {"request_id": row["request_id"], "status": "NOT_RUN"}
            fields = burnin.terminal_ledger_fields(request, process, None)
            terminals = [
                entry
                for state in ("COMPLETED_PASS", "COMPLETED_FAIL", "CANCELLED_NOT_RUN")
                for entry in burnin._ledger_entries(ledger, row["request_id"], state)
            ]
            if not terminals:
                _append_ledger_fields(manager["ledger"], fields, timestamp=timestamp)
            elif len(terminals) != 1 or terminals[0][1:] != fields:
                raise burnin.EvidenceError(
                    "later request already has a conflicting terminal row"
                )
    finally:
        _release_manager_reservation(manager, owner)
    _publish_completed_cycles(contract)


def _process_record(contract: Mapping[str, Any], prefix: str) -> dict[str, Any]:
    manifest = _load_process_manifest(contract, prefix, required=True)
    assert manifest is not None
    directory = _existing_process_directory(contract, prefix, required=True)
    assert directory is not None
    is_resource = prefix.startswith("cycle_")
    status = "PASS" if _manifest_passed(manifest) else "FAIL"
    return {
        "command_sha256": manifest["command_sha256"],
        "approval_snapshot": manifest["approval_snapshot"],
        "elapsed_seconds": manifest["elapsed_seconds"],
        "ended_at": manifest["ended_at"],
        "execution_state": manifest["execution_state"],
        "exit_code": manifest["exit_code"],
        "producer_sha256": manifest["producer_sha256"],
        "pending_manifest_sha256": (
            burnin.file_hash_record(directory / "pending-manifest.json")["sha256"]
            if is_resource
            else None
        ),
        "request_id": manifest["request_id"],
        "resource_lock_released": manifest["resource_lock_released"],
        "result": burnin.file_hash_record(directory / "result.json"),
        "started_at": manifest["started_at"],
        "status": status,
        "stderr": burnin.file_hash_record(directory / "stderr.txt"),
        "stdout": burnin.file_hash_record(directory / "stdout.txt"),
        "termination": manifest["termination"],
    }


def aggregate_result() -> dict[str, Any]:
    _bootstrap_authority()
    contract = burnin.load_contract()
    _candidate, _siblings, candidate_commit, candidate_tree = _verify_repositories(contract)
    not_run_local = {"request_id": None, "status": "NOT_RUN"}
    quick_processes = [_process_record(contract, "common.quick.1")]
    if quick_processes[0]["status"] == "PASS":
        package_processes = [_process_record(contract, "common.package.1")]
    else:
        package_processes = [dict(not_run_local)]
    if package_processes[0]["status"] == "PASS":
        additive_processes = [
            _process_record(contract, f"common.additive.{partition}")
            for partition in (1, 2, 3)
        ]
    else:
        additive_processes = [dict(not_run_local) for _partition in (1, 2, 3)]
    common_processes = {
        "quick": quick_processes,
        "package": package_processes,
        "additive": additive_processes,
    }
    common_statuses = {
        lane: (
            "PASS"
            if all(process["status"] == "PASS" for process in processes)
            else "NOT_RUN"
            if all(process["status"] == "NOT_RUN" for process in processes)
            else "FAIL"
        )
        for lane, processes in common_processes.items()
    }
    all_common_passed = all(
        status == "PASS" for status in common_statuses.values()
    )
    if all_common_passed:
        _publish_completed_cycles(contract)
    cycles: list[dict[str, Any]] = []
    encountered_failure = any(
        common_statuses[lane] != "PASS" for lane in ("quick", "package", "additive")
    )
    for cycle in (1, 2):
        lanes: dict[str, Any] = {}
        for lane in ("functional", "anyfem", "performance"):
            row = next(
                item
                for item in contract["resource_requests"][f"cycle_{cycle}"]
                if item["lane"] == lane
            )
            prefix = f"cycle_{cycle}.{lane}"
            if encountered_failure:
                lanes[lane] = {"request_id": row["request_id"], "status": "NOT_RUN"}
                continue
            manifest = _load_process_manifest(contract, prefix, required=True)
            assert manifest is not None
            process = _process_record(contract, prefix)
            lanes[lane] = process
            encountered_failure = process["status"] == "FAIL"
        statuses = [lanes[lane]["status"] for lane in ("functional", "anyfem", "performance")]
        cycle_status = (
            "PASS"
            if statuses == ["PASS", "PASS", "PASS"]
            else "NOT_RUN"
            if statuses == ["NOT_RUN", "NOT_RUN", "NOT_RUN"]
            else "FAIL"
        )
        cycles.append({"cycle": cycle, "lanes": lanes, "status": cycle_status})
    performance_passed = all(
        cycle["lanes"]["performance"]["status"] == "PASS" for cycle in cycles
    )
    performance_observations = (
        [
            {
                "cycle": cycle,
                "observation": burnin.extract_performance_observation(
                    burnin.process_output_directory(contract, f"cycle_{cycle}.performance")
                    / "stdout.txt",
                    contract=contract,
                ),
            }
            for cycle in (1, 2)
        ]
        if performance_passed
        else None
    )
    package_result = burnin.output_root(contract) / contract["package"]["result_filename"]
    wheel = burnin.output_root(contract) / contract["package"]["wheel_filename"]
    package_status = common_statuses["package"]
    if package_status == "PASS":
        _require_package_artifacts(
            contract,
            candidate_commit=candidate_commit,
            candidate_tree=candidate_tree,
        )

    package_artifacts = (
        None
        if package_status == "NOT_RUN"
        else {
            "result": burnin.optional_regular_file_record(package_result),
            "wheel": burnin.optional_regular_file_record(wheel, filename=True),
        }
    )
    all_resource_passed = all(cycle["status"] == "PASS" for cycle in cycles)
    success = all_common_passed and all_resource_passed and performance_passed
    ledger_snapshots: dict[str, dict[str, Any] | None]
    if all_common_passed:
        snapshot_paths = {
            "approval": _approval_snapshot_path(contract),
            "cycle_1": _cycle_snapshot_path(contract, 1),
            "cycle_2": _cycle_snapshot_path(contract, 2),
        }
        ledger_snapshots = {}
        for name, path in snapshot_paths.items():
            snapshot = _validate_ledger_snapshot(
                _load_canonical_json(path), contract=contract
            )
            if name == "approval" and snapshot["kind"] != "APPROVAL":
                raise burnin.EvidenceError("approval ledger snapshot mismatch")
            if name.startswith("cycle_") and snapshot.get("cycle") != int(name[-1]):
                raise burnin.EvidenceError("cycle ledger snapshot mismatch")
            ledger_snapshots[name] = burnin.file_hash_record(path)
    else:
        ledger_snapshots = {"approval": None, "cycle_1": None, "cycle_2": None}
    result = {
        "candidate": {"clean": True, "commit": candidate_commit, "tree": candidate_tree},
        "common_lanes": {
            lane: {
                "inventory": contract["lane_inventories"][lane],
                "processes": processes,
                "status": common_statuses[lane],
            }
            for lane, processes in common_processes.items()
        },
        "cycles": cycles,
        "hard_gates": {
            "batch_path_equality": "PASS" if performance_passed else "NOT_EVALUATED",
            "q4_numerical_parity": "PASS" if performance_passed else "NOT_EVALUATED",
            "qualified_s3_opt_in": (
                "PASS" if common_statuses["additive"] == "PASS" else "NOT_EVALUATED"
            ),
            "s3_default_legacy": (
                "PASS" if common_statuses["additive"] == "PASS" else "NOT_EVALUATED"
            ),
            "warm_cache_reuse": "PASS" if performance_passed else "NOT_EVALUATED",
        },
        "ledger_snapshots": ledger_snapshots,
        "package_artifacts": package_artifacts,
        "performance_observations": performance_observations,
        "production_boundary": contract["production_boundary"],
        "resource_requests": contract["resource_requests"],
        "schema": burnin.RESULT_SCHEMA,
        "siblings": contract["sibling_authority"],
        "terminal": contract["adjudication"][
            "result_success_terminal" if success else "result_blocked_terminal"
        ],
    }
    output = burnin.output_root(contract) / contract["adjudication"]["external_result_filename"]
    if output.exists() or output.is_symlink():
        existing = _load_canonical_json(output)
        if existing != result:
            raise burnin.EvidenceError("existing aggregate differs from reconstructed result")
        burnin.validate_external_bindings(existing, contract=contract, require_aggregate=True)
        return existing
    pending_output = output.with_name(f".{output.name}.pending")
    if pending_output.exists() or pending_output.is_symlink():
        recovered = _load_canonical_json(pending_output)
        if recovered != result:
            raise burnin.EvidenceError("pending aggregate differs from reconstructed result")
        burnin.validate_result(recovered, contract=contract)
        _write_canonical_json_once(output, recovered)
    else:
        burnin.validate_external_bindings(result, contract=contract, require_aggregate=False)
        _write_canonical_json_once(output, result)
    burnin.validate_external_bindings(result, contract=contract, require_aggregate=True)
    return result


def main(argv: list[str] | None = None) -> int:
    _RESOURCE_UNPROVEN_TREE.clear()
    active_test_lane = os.environ.get("ANYSOLVER_BURNIN_ACTIVE_TEST_LANE")
    if active_test_lane is not None:
        if active_test_lane != "quick":
            raise RuntimeError("active burn-in test lane marker is invalid")
        raise RuntimeError(
            "nested process coordinator execution from the active quick lane is forbidden"
        )
    _arm_invocation_job_boundary()
    invocation_deadline, watchdog_stop, watchdog_thread = (
        _start_resource_invocation_watchdog(_EARLY_RESOURCE_TIMEOUT_POLICY)
    )
    try:
        _bootstrap_authority()
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="mode", required=True)
        local = subparsers.add_parser("local", help="run a non-resource preflight")
        local.add_argument(
            "--lane", choices=("quick", "package", "additive"), required=True
        )
        local.add_argument("--partition", type=int)
        resource = subparsers.add_parser(
            "resource",
            help="reject standalone v15 worker execution; use cycle --cycle N",
            description=(
                "Standalone execution of current v15 resource requests is disabled. "
                "Use cycle --cycle N so all three workers share one 1200-second watchdog."
            ),
        )
        resource.add_argument("--request-id", required=True)
        cycle = subparsers.add_parser(
            "cycle",
            help="run all three registered requests under one 1200-second watchdog",
        )
        cycle.add_argument("--cycle", choices=(1, 2), required=True, type=int)
        finalize = subparsers.add_parser(
            "finalize-resource",
            help="recover publication from an existing worker completion; never rerun it",
        )
        finalize.add_argument("--request-id", required=True)
        subparsers.add_parser("approve")
        subparsers.add_parser("cancel-remaining")
        subparsers.add_parser("aggregate")
        args = parser.parse_args(argv)
        if args.mode in {"local", "resource", "cycle"}:
            contract = burnin.load_contract()
            timeout_policy = _timeout_policy(contract)
            _validate_early_watchdog_policy(timeout_policy)
            if args.mode == "local":
                return _run_local_bounded(
                    contract=contract,
                    invocation_deadline=invocation_deadline,
                    lane=args.lane,
                    partition=args.partition,
                    timeout_policy=timeout_policy,
                )
            if args.mode == "resource":
                _reject_standalone_resource_execution(contract, args.request_id)
                raise AssertionError(
                    "standalone resource rejection returned unexpectedly"
                )
            return _run_cycle_bounded(
                cycle=args.cycle,
                contract=contract,
                timeout_policy=timeout_policy,
                invocation_deadline=invocation_deadline,
            )
        if args.mode == "finalize-resource":
            return finalize_resource(
                request_id=args.request_id,
                invocation_deadline=invocation_deadline,
            )
        if args.mode == "approve":
            approve_requests()
            return 0
        if args.mode == "cancel-remaining":
            cancel_remaining()
            return 0
        result = aggregate_result()
        sys.stdout.buffer.write(burnin.canonical_json_bytes(result))
        sys.stdout.buffer.flush()
        return 0
    finally:
        if _RESOURCE_UNPROVEN_TREE.is_set():
            _hold_for_resource_watchdog(watchdog_thread)
        else:
            watchdog_stop.set()
            watchdog_thread.join(timeout=0.1)


if __name__ == "__main__":
    raise SystemExit(main())
