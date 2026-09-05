"""Installed-wheel and nonintrusion helpers for GE-Beam3 P3.

The coordinator builds one wheel from a clean frozen commit, installs it into
two independent virtual environments, and runs this same file in isolated
mode.  Only byte-identical, path-free correctness records are canonical;
commands, origins, and logs remain external diagnostics.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import stat
import subprocess
import sys
import tarfile
import time
from typing import Any, Iterable, Mapping, Sequence


SCHEMA = "anysolver.ge-beam3-mixed-p3-package-gate-v1"
CHECK_SCHEMA = "anysolver.ge-beam3-mixed-p3-installed-check-v1"
PERFORMANCE_SCHEMA = "anysolver.ge-beam3-mixed-p3-performance-summary-v1"
PERFORMANCE_RAW_SCHEMA = "anysolver.ge-beam3-mixed-p3-performance-raw-v1"
RUNNER_RELATIVE_PATH = Path(
    "docs/reference_cases/ge_beam3_mixed_p3_package_gate.py"
)
QUALIFIED_ID = "GE_BEAM3_DC_MIXED_K1_MACRO_V2"
SELECTOR = "ge-beam3"
BASE_COMMIT = "e31c9e292a2fc9f6b57472bb8c5b90919a535492"
CHILD_TIMEOUT_SECONDS = 600
WAVE_TIMEOUT_SECONDS = 1800
INACTIVITY_SECONDS = 300
MEMORY_LIMIT_GIB = 24
PROCESS_CONTAINMENT_ID = "WINDOWS_JOB_OBJECT_SUSPENDED_ASSIGN_V1"
MINIMUM_PAIRS = 11
MAXIMUM_MEDIAN_RATIO = 1.05
PERFORMANCE_INNER_REPETITIONS = 16
STATE_SCHEMA = "anysolver.ge-beam3-mixed.committed_state.v2"
STATE_VERSION = 2
STATE_LAYOUT_ID = "GE_BEAM3_MIXED_Q18_SHARED_SO3_OPERATOR_STATION4_V2"
INSTALLED_CHECK_KEYS = frozenset(
    {
        "beam_shell_joint_rejected",
        "candidate_state_rejected",
        "current_state_buckling_rejected",
        "element_roundtrip",
        "formulation_id",
        "global_nonlinear_restart",
        "installed_standard_assembly",
        "installed_standard_linear_solve",
        "installed_standard_modal",
        "interpolated_beam_shell_joint_rejected",
        "mass_positive",
        "module_origins_inside_environment",
        "native_recovery_four_stations",
        "reference_buckling_symmetric",
        "repository_absent",
        "restart_nonzero_continuation",
        "root_export_identity",
        "selector_exact",
        "standard_internal_force",
        "standard_reference_buckling",
        "standard_stiffness",
        "state_roundtrip",
        "unsupported_capability_inventory",
        "unsupported_guard_rejected",
    }
)
INSTALLED_ARRAY_HASH_KEYS = frozenset(
    {
        "buckling",
        "global_nonlinear_displacement",
        "internal_force",
        "linear_displacement",
        "mass",
        "nonzero_restart_state",
        "recovery_resultants",
        "stiffness",
    }
)
OPERATIONS = (
    "CONSTRUCTION",
    "STIFFNESS",
    "INTERNAL_FORCE",
    "ASSEMBLY",
    "SOLVE",
    "RECOVERY",
    "RESTART",
)
NEGATIVE_SELECTORS = (
    "ge_beam3",
    "beam3",
    "b3",
    "gebeam3",
    "ge-beam-3",
    "quadratic_beam",
    "beam",
)
_THREAD_VARIABLES = (
    "BLIS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMBA_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "TBB_NUM_THREADS",
)


class PackageGateError(RuntimeError):
    """The package gate is malformed, non-isolated, or failed."""


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def strict_canonical_json_loads(raw: bytes) -> Any:
    if type(raw) is not bytes or raw.startswith(b"\xef\xbb\xbf"):
        raise PackageGateError("canonical JSON must be BOM-free bytes")

    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise PackageGateError(f"duplicate JSON key {key!r}")
            result[key] = value
        return result

    def nonfinite(token: str) -> None:
        raise PackageGateError(f"nonfinite JSON token {token}")

    try:
        decoded = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=unique,
            parse_constant=nonfinite,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PackageGateError("invalid canonical JSON") from exc
    if canonical_json_bytes(decoded) != raw:
        raise PackageGateError("JSON is not canonical")
    return decoded


def _is_sha256(value: Any) -> bool:
    return (
        type(value) is str
        and len(value) == 64
        and value == value.upper()
        and all(character in "0123456789ABCDEF" for character in value)
    )


def _is_git_oid(value: Any) -> bool:
    return (
        type(value) is str
        and len(value) == 40
        and value == value.lower()
        and all(character in "0123456789abcdef" for character in value)
    )


def _validate_installed_correctness_record(value: Any) -> dict[str, Any]:
    """Validate the complete closed installed-wheel evidence schema."""

    required = {
        "array_hashes",
        "check_count",
        "checks",
        "element_record_sha256",
        "formulation_id",
        "loaded_anysolver_module_count",
        "schema",
        "selector",
        "state_layout_id",
        "state_record_sha256",
        "state_schema",
        "state_version",
    }
    if not isinstance(value, Mapping) or set(value) != required:
        raise PackageGateError("installed correctness record keys mismatch")
    if value["schema"] != CHECK_SCHEMA:
        raise PackageGateError("installed correctness record schema mismatch")
    if value["formulation_id"] != QUALIFIED_ID or value["selector"] != SELECTOR:
        raise PackageGateError("installed formulation or selector mismatch")
    if (
        value["state_schema"] != STATE_SCHEMA
        or value["state_version"] != STATE_VERSION
        or value["state_layout_id"] != STATE_LAYOUT_ID
    ):
        raise PackageGateError("installed state identity mismatch")
    checks = value["checks"]
    if not isinstance(checks, Mapping) or set(checks) != INSTALLED_CHECK_KEYS:
        raise PackageGateError("installed check inventory mismatch")
    if any(type(item) is not bool for item in checks.values()):
        raise PackageGateError("installed check values must be booleans")
    if not all(checks.values()):
        raise PackageGateError("installed correctness record contains a failed check")
    if type(value["check_count"]) is not int or value["check_count"] != len(checks):
        raise PackageGateError("installed check count mismatch")
    hashes = value["array_hashes"]
    if not isinstance(hashes, Mapping) or set(hashes) != INSTALLED_ARRAY_HASH_KEYS:
        raise PackageGateError("installed array-hash inventory mismatch")
    if any(not _is_sha256(item) for item in hashes.values()):
        raise PackageGateError("installed array hash is malformed")
    if not _is_sha256(value["element_record_sha256"]):
        raise PackageGateError("installed element-record hash is malformed")
    if not _is_sha256(value["state_record_sha256"]):
        raise PackageGateError("installed state-record hash is malformed")
    module_count = value["loaded_anysolver_module_count"]
    if type(module_count) is not int or module_count <= 0:
        raise PackageGateError("installed module count is malformed")
    return dict(value)


def _validate_package_aggregate(value: Any) -> dict[str, Any]:
    required = {
        "candidate_commit",
        "candidate_tree",
        "canonical_run_count",
        "correctness_record_sha256",
        "correctness_records_byte_identical",
        "formulation_id",
        "installed_runner_sha256",
        "package_gate_passed",
        "process_containment",
        "schema",
        "selector",
        "wheel",
    }
    if not isinstance(value, Mapping) or set(value) != required:
        raise PackageGateError("package aggregate keys mismatch")
    if value["schema"] != SCHEMA:
        raise PackageGateError("package aggregate schema mismatch")
    if value["formulation_id"] != QUALIFIED_ID or value["selector"] != SELECTOR:
        raise PackageGateError("package aggregate formulation or selector mismatch")
    if not _is_git_oid(value["candidate_commit"]) or not _is_git_oid(
        value["candidate_tree"]
    ):
        raise PackageGateError("package aggregate Git identity is malformed")
    if (
        value["canonical_run_count"] != 2
        or value["correctness_records_byte_identical"] is not True
        or value["package_gate_passed"] is not True
    ):
        raise PackageGateError("package aggregate does not record two accepted runs")
    if value["process_containment"] != PROCESS_CONTAINMENT_ID:
        raise PackageGateError("package aggregate process containment mismatch")
    if not _is_sha256(value["correctness_record_sha256"]) or not _is_sha256(
        value["installed_runner_sha256"]
    ):
        raise PackageGateError("package aggregate hash is malformed")
    wheel = value["wheel"]
    if not isinstance(wheel, Mapping) or set(wheel) != {
        "bytes",
        "filename",
        "sha256",
    }:
        raise PackageGateError("package aggregate wheel identity keys mismatch")
    if type(wheel["bytes"]) is not int or wheel["bytes"] <= 0:
        raise PackageGateError("package aggregate wheel size is malformed")
    if (
        type(wheel["filename"]) is not str
        or not wheel["filename"]
        or Path(wheel["filename"]).name != wheel["filename"]
        or not wheel["filename"].endswith(".whl")
        or not _is_sha256(wheel["sha256"])
    ):
        raise PackageGateError("package aggregate wheel identity is malformed")
    return dict(value)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def write_exclusive(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(canonical_json_bytes(value))


def assert_regular_wheel(path: Path) -> dict[str, Any]:
    identity = _regular_file_identity(path)
    if path.suffix != ".whl":
        raise PackageGateError("wheel must be a nonempty .whl file")
    return identity


def _regular_file_identity(path: Path) -> dict[str, Any]:
    absolute = path.resolve(strict=True)
    if absolute != path.absolute():
        raise PackageGateError("artifact path must be exact and contain no indirection")
    information = absolute.lstat()
    if not stat.S_ISREG(information.st_mode) or absolute.is_symlink():
        raise PackageGateError("artifact must be a regular non-symlink file")
    attributes = int(getattr(information, "st_file_attributes", 0))
    reparse = int(getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))
    if attributes & reparse:
        raise PackageGateError("artifact must not be a reparse point")
    if information.st_size <= 0:
        raise PackageGateError("artifact must be nonempty")
    return {
        "bytes": int(information.st_size),
        "filename": absolute.name,
        "sha256": sha256_file(absolute),
    }


def _require_file_identity(path: Path, expected: Mapping[str, Any]) -> None:
    if _regular_file_identity(path) != dict(expected):
        raise PackageGateError(f"frozen artifact identity changed: {path.name}")


def _copy_exclusive_verified(
    source: Path, destination: Path, expected: Mapping[str, Any]
) -> dict[str, Any]:
    _require_file_identity(source, expected)
    destination.parent.mkdir(parents=True, exist_ok=False)
    with source.open("rb") as input_stream, destination.open("xb") as output_stream:
        for block in iter(lambda: input_stream.read(1024 * 1024), b""):
            output_stream.write(block)
    _require_file_identity(source, expected)
    made = _regular_file_identity(destination)
    if made != dict(expected):
        raise PackageGateError("private artifact copy differs from frozen source")
    return made


def _inside(path: Path, root: Path) -> bool:
    try:
        path.resolve(strict=True).relative_to(root.resolve(strict=True))
    except (FileNotFoundError, ValueError):
        return False
    return True


def _bounded_environment() -> dict[str, str]:
    environment = dict(os.environ)
    for key in tuple(environment):
        if key.upper().startswith("GIT_") or key.upper().startswith("PYTHON"):
            environment.pop(key, None)
    for name in _THREAD_VARIABLES:
        environment[name] = "1"
    environment["PYTHONHASHSEED"] = "0"
    environment["PYTHONNOUSERSITE"] = "1"
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["GIT_ATTR_NOSYSTEM"] = "1"
    environment["GIT_CONFIG_GLOBAL"] = os.devnull
    environment["GIT_CONFIG_NOSYSTEM"] = "1"
    environment["GIT_NO_REPLACE_OBJECTS"] = "1"
    environment["GIT_OPTIONAL_LOCKS"] = "0"
    environment["GIT_TERMINAL_PROMPT"] = "0"
    environment.pop("PYTHONPATH", None)
    return environment


def _terminate_tree(process: subprocess.Popen[bytes]) -> None:
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


def _attach_windows_memory_job(process: subprocess.Popen[bytes]) -> Any:
    import ctypes
    from ctypes import wintypes

    class IoCounters(ctypes.Structure):
        _fields_ = [
            ("ReadOperationCount", ctypes.c_ulonglong),
            ("WriteOperationCount", ctypes.c_ulonglong),
            ("OtherOperationCount", ctypes.c_ulonglong),
            ("ReadTransferCount", ctypes.c_ulonglong),
            ("WriteTransferCount", ctypes.c_ulonglong),
            ("OtherTransferCount", ctypes.c_ulonglong),
        ]

    class BasicLimits(ctypes.Structure):
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

    class ExtendedLimits(ctypes.Structure):
        _fields_ = [
            ("BasicLimitInformation", BasicLimits),
            ("IoInfo", IoCounters),
            ("ProcessMemoryLimit", ctypes.c_size_t),
            ("JobMemoryLimit", ctypes.c_size_t),
            ("PeakProcessMemoryUsed", ctypes.c_size_t),
            ("PeakJobMemoryUsed", ctypes.c_size_t),
        ]

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateJobObjectW.argtypes = (ctypes.c_void_p, wintypes.LPCWSTR)
    kernel.CreateJobObjectW.restype = wintypes.HANDLE
    kernel.SetInformationJobObject.argtypes = (
        wintypes.HANDLE,
        ctypes.c_int,
        ctypes.c_void_p,
        wintypes.DWORD,
    )
    kernel.SetInformationJobObject.restype = wintypes.BOOL
    kernel.AssignProcessToJobObject.argtypes = (wintypes.HANDLE, wintypes.HANDLE)
    kernel.AssignProcessToJobObject.restype = wintypes.BOOL
    handle = kernel.CreateJobObjectW(None, None)
    if not handle:
        raise PackageGateError("unable to create bounded Windows job")
    information = ExtendedLimits()
    information.BasicLimitInformation.LimitFlags = 0x2000 | 0x0200
    information.JobMemoryLimit = MEMORY_LIMIT_GIB * 1024**3
    if not kernel.SetInformationJobObject(
        handle, 9, ctypes.byref(information), ctypes.sizeof(information)
    ):
        kernel.CloseHandle(handle)
        raise PackageGateError("unable to set 24-GiB Windows job limit")
    process_handle = wintypes.HANDLE(int(process._handle))
    if not kernel.AssignProcessToJobObject(handle, process_handle):
        kernel.CloseHandle(handle)
        raise PackageGateError("unable to bind child to 24-GiB Windows job")
    return handle


def _resume_windows_process(process: subprocess.Popen[bytes]) -> None:
    """Resume the sole primary thread after job assignment."""

    import ctypes
    from ctypes import wintypes

    class ThreadEntry32(ctypes.Structure):
        _fields_ = [
            ("dwSize", wintypes.DWORD),
            ("cntUsage", wintypes.DWORD),
            ("th32ThreadID", wintypes.DWORD),
            ("th32OwnerProcessID", wintypes.DWORD),
            ("tpBasePri", wintypes.LONG),
            ("tpDeltaPri", wintypes.LONG),
            ("dwFlags", wintypes.DWORD),
        ]

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateToolhelp32Snapshot.argtypes = (wintypes.DWORD, wintypes.DWORD)
    kernel.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    kernel.Thread32First.argtypes = (
        wintypes.HANDLE,
        ctypes.POINTER(ThreadEntry32),
    )
    kernel.Thread32First.restype = wintypes.BOOL
    kernel.Thread32Next.argtypes = (
        wintypes.HANDLE,
        ctypes.POINTER(ThreadEntry32),
    )
    kernel.Thread32Next.restype = wintypes.BOOL
    kernel.OpenThread.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    kernel.OpenThread.restype = wintypes.HANDLE
    kernel.ResumeThread.argtypes = (wintypes.HANDLE,)
    kernel.ResumeThread.restype = wintypes.DWORD
    snapshot = kernel.CreateToolhelp32Snapshot(0x00000004, 0)
    invalid_handle = ctypes.c_void_p(-1).value
    if not snapshot or int(snapshot) == invalid_handle:
        raise PackageGateError("unable to enumerate suspended Windows child")
    thread_handle = None
    try:
        entry = ThreadEntry32()
        entry.dwSize = ctypes.sizeof(entry)
        present = bool(kernel.Thread32First(snapshot, ctypes.byref(entry)))
        while present:
            if int(entry.th32OwnerProcessID) == process.pid:
                thread_handle = kernel.OpenThread(
                    0x0002, False, int(entry.th32ThreadID)
                )
                break
            present = bool(kernel.Thread32Next(snapshot, ctypes.byref(entry)))
        if not thread_handle:
            raise PackageGateError("suspended Windows child has no primary thread")
        if int(kernel.ResumeThread(thread_handle)) == 0xFFFFFFFF:
            raise PackageGateError("unable to resume bounded Windows child")
    finally:
        if thread_handle:
            kernel.CloseHandle(thread_handle)
        kernel.CloseHandle(snapshot)


def _close_windows_job(handle: Any) -> None:
    if handle is None:
        return
    import ctypes

    ctypes.windll.kernel32.CloseHandle(handle)


def _require_formal_process_containment() -> None:
    if os.name != "nt":
        raise PackageGateError(
            "formal P3 package/performance execution requires Windows Job Object "
            "containment with suspended assignment"
        )


def _process_cpu_marker(process: subprocess.Popen[bytes]) -> int | None:
    """Return a monotone parent-process CPU marker without optional packages."""

    if process.poll() is not None:
        return None
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.GetProcessTimes.argtypes = (
            wintypes.HANDLE,
            ctypes.POINTER(wintypes.FILETIME),
            ctypes.POINTER(wintypes.FILETIME),
            ctypes.POINTER(wintypes.FILETIME),
            ctypes.POINTER(wintypes.FILETIME),
        )
        kernel.GetProcessTimes.restype = wintypes.BOOL
        created = wintypes.FILETIME()
        exited = wintypes.FILETIME()
        kernel_time = wintypes.FILETIME()
        user_time = wintypes.FILETIME()
        if not kernel.GetProcessTimes(
            wintypes.HANDLE(int(process._handle)),
            ctypes.byref(created),
            ctypes.byref(exited),
            ctypes.byref(kernel_time),
            ctypes.byref(user_time),
        ):
            return None

        def ticks(value: wintypes.FILETIME) -> int:
            return (int(value.dwHighDateTime) << 32) | int(value.dwLowDateTime)

        return ticks(kernel_time) + ticks(user_time)
    stat_path = Path(f"/proc/{process.pid}/stat")
    try:
        remainder = stat_path.read_text(encoding="ascii").rsplit(")", 1)[1].split()
        return int(remainder[11]) + int(remainder[12])
    except (FileNotFoundError, IndexError, OSError, ValueError):
        return None


def _posix_process_group_rss_bytes(process_group: int) -> int:
    """Return aggregate resident memory for a Linux process group."""

    if os.name == "nt" or not Path("/proc").is_dir():
        return 0
    try:
        page_size = int(os.sysconf("SC_PAGE_SIZE"))
    except (AttributeError, OSError, ValueError):
        return 0
    resident_pages = 0
    for entry in Path("/proc").iterdir():
        if not entry.name.isdecimal():
            continue
        try:
            fields = (entry / "stat").read_text(encoding="ascii").rsplit(")", 1)[
                1
            ].split()
            if int(fields[2]) != process_group:
                continue
            statm = (entry / "statm").read_text(encoding="ascii").split()
            resident_pages += int(statm[1])
        except (FileNotFoundError, IndexError, OSError, ValueError):
            continue
    return resident_pages * page_size


def run_bounded(
    command: Sequence[str],
    *,
    cwd: Path,
    log_path: Path,
    timeout_seconds: int = CHILD_TIMEOUT_SECONDS,
    deadline_monotonic: float | None = None,
    inactivity_seconds: int = INACTIVITY_SECONDS,
) -> None:
    if type(inactivity_seconds) is not int or inactivity_seconds <= 0:
        raise PackageGateError("inactivity threshold must be a positive integer")
    if deadline_monotonic is not None:
        remaining = int(math.ceil(deadline_monotonic - time.monotonic()))
        if remaining <= 0:
            raise PackageGateError(
                f"complete wave exceeded {WAVE_TIMEOUT_SECONDS} seconds"
            )
        timeout_seconds = min(timeout_seconds, remaining)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    creationflags = (
        int(getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))
        | 0x00000004
        if os.name == "nt"
        else 0
    )
    preexec_fn = None
    if os.name != "nt":
        def impose_memory_limit() -> None:
            import resource

            limit = MEMORY_LIMIT_GIB * 1024**3
            resource.setrlimit(resource.RLIMIT_AS, (limit, limit))

        preexec_fn = impose_memory_limit
    with log_path.open("xb") as log:
        process = subprocess.Popen(
            list(command),
            cwd=str(cwd),
            env=_bounded_environment(),
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
            creationflags=creationflags,
            start_new_session=os.name != "nt",
            preexec_fn=preexec_fn,
        )
        memory_job = None
        try:
            if os.name == "nt":
                memory_job = _attach_windows_memory_job(process)
                _resume_windows_process(process)
            started = time.monotonic()
            last_activity = started
            last_size = -1
            last_cpu = _process_cpu_marker(process)
            while True:
                return_code = process.poll()
                if return_code is not None:
                    break
                now = time.monotonic()
                try:
                    current_size = log_path.stat().st_size
                except OSError:
                    current_size = last_size
                current_cpu = _process_cpu_marker(process)
                if current_size != last_size or (
                    current_cpu is not None
                    and last_cpu is not None
                    and current_cpu != last_cpu
                ):
                    last_activity = now
                last_size = current_size
                last_cpu = current_cpu
                if now - started >= timeout_seconds:
                    _terminate_tree(process)
                    process.wait()
                    raise PackageGateError(
                        f"child exceeded {timeout_seconds} seconds"
                    )
                if now - last_activity >= inactivity_seconds:
                    _terminate_tree(process)
                    process.wait()
                    raise PackageGateError(
                        f"child made no log or CPU progress for {inactivity_seconds} seconds"
                    )
                if (
                    os.name != "nt"
                    and _posix_process_group_rss_bytes(process.pid)
                    > MEMORY_LIMIT_GIB * 1024**3
                ):
                    _terminate_tree(process)
                    process.wait()
                    raise PackageGateError(
                        f"child process tree exceeded {MEMORY_LIMIT_GIB} GiB"
                    )
                time.sleep(0.1)
            if os.name != "nt":
                # The parent may exit successfully while leaving workers in its
                # process group.  Formal completion requires an empty tree.
                _terminate_tree(process)
        except BaseException:
            _terminate_tree(process)
            process.wait()
            raise
        finally:
            _close_windows_job(memory_job)
    if return_code != 0:
        # A failed parent may have already exited while descendants remain in
        # its process group.  Always terminate the group before classifying
        # the failure; the Windows job handle has already provided the same
        # kill-on-close guarantee there.
        _terminate_tree(process)
        raise PackageGateError(
            f"child exited {return_code}; see external log {log_path.name}"
        )


def balanced_orders(pair_count: int) -> tuple[tuple[str, str], ...]:
    if type(pair_count) is not int or pair_count < MINIMUM_PAIRS:
        raise PackageGateError(f"at least {MINIMUM_PAIRS} pairs are required")
    return tuple(
        ("base", "candidate") if index % 2 == 0 else ("candidate", "base")
        for index in range(pair_count)
    )


def _percentile95(values: Sequence[float]) -> float:
    ordered = sorted(values)
    position = 0.95 * (len(ordered) - 1)
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


def summarize_timings(values: Iterable[float]) -> dict[str, float]:
    samples = [float(value) for value in values]
    if len(samples) < MINIMUM_PAIRS or any(
        not math.isfinite(value) or value <= 0.0 for value in samples
    ):
        raise PackageGateError("timings require at least 11 finite positive samples")
    ordered = sorted(samples)
    middle = len(ordered) // 2
    median = (
        ordered[middle]
        if len(ordered) % 2
        else 0.5 * (ordered[middle - 1] + ordered[middle])
    )
    deviations = sorted(abs(value - median) for value in samples)
    mad = (
        deviations[middle]
        if len(deviations) % 2
        else 0.5 * (deviations[middle - 1] + deviations[middle])
    )
    return {"mad": mad, "median": median, "p95": _percentile95(samples)}


def adjudicate_performance(
    base: Mapping[str, Sequence[float]],
    candidate: Mapping[str, Sequence[float]],
) -> dict[str, Any]:
    if set(base) != set(OPERATIONS) or set(candidate) != set(OPERATIONS):
        raise PackageGateError("performance operation inventory mismatch")
    ratios: dict[str, str] = {}
    passed = True
    for operation in OPERATIONS:
        base_samples = list(base[operation])
        candidate_samples = list(candidate[operation])
        if len(base_samples) != len(candidate_samples):
            raise PackageGateError("paired performance sample count mismatch")
        summarize_timings(base_samples)
        summarize_timings(candidate_samples)
        paired_ratios = [
            float(candidate_value) / float(base_value)
            for base_value, candidate_value in zip(
                base_samples, candidate_samples, strict=True
            )
        ]
        ratio = summarize_timings(paired_ratios)["median"]
        ratios[operation] = format(ratio, ".12f")
        passed = passed and ratio <= MAXIMUM_MEDIAN_RATIO
    return {
        "all_operations_pass": bool(passed),
        "maximum_median_ratio": format(MAXIMUM_MEDIAN_RATIO, ".2f"),
        "operations": list(OPERATIONS),
        "ratios": ratios,
        "schema": PERFORMANCE_SCHEMA,
    }


def _peak_rss_bytes() -> int:
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        class ProcessMemoryCounters(ctypes.Structure):
            _fields_ = [
                ("cb", wintypes.DWORD),
                ("PageFaultCount", wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
            ]

        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        psapi = ctypes.WinDLL("psapi", use_last_error=True)
        kernel.GetCurrentProcess.argtypes = ()
        kernel.GetCurrentProcess.restype = wintypes.HANDLE
        psapi.GetProcessMemoryInfo.argtypes = (
            wintypes.HANDLE,
            ctypes.POINTER(ProcessMemoryCounters),
            wintypes.DWORD,
        )
        psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
        counters = ProcessMemoryCounters()
        counters.cb = ctypes.sizeof(counters)
        process = kernel.GetCurrentProcess()
        if not psapi.GetProcessMemoryInfo(
            process, ctypes.byref(counters), counters.cb
        ):
            raise PackageGateError("unable to read process peak RSS")
        return int(counters.PeakWorkingSetSize)
    import resource

    value = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return value if sys.platform == "darwin" else value * 1024


def _measure(operation: Any, repetitions: int = PERFORMANCE_INNER_REPETITIONS) -> dict[str, int]:
    operation()
    gc.collect()
    enabled = gc.isenabled()
    gc.disable()
    wall_start = time.perf_counter_ns()
    cpu_start = time.process_time_ns()
    try:
        for _ in range(repetitions):
            operation()
    finally:
        cpu_elapsed = time.process_time_ns() - cpu_start
        wall_elapsed = time.perf_counter_ns() - wall_start
        if enabled:
            gc.enable()
    return {
        "cpu_ns_per_call": max(1, int(round(cpu_elapsed / repetitions))),
        "wall_ns_per_call": max(1, int(round(wall_elapsed / repetitions))),
    }


def _legacy_fixture(family: str) -> tuple[Any, Any, Any, Any]:
    import numpy as np

    from anysolver.elements import BeamElement, QuadraticBeamElement
    from anysolver.fe_core import FEModel

    if family not in {"B2", "B3"}:
        raise PackageGateError("performance family must be B2 or B3")
    model = FEModel(f"p3-performance-{family.lower()}")
    material = model.add_material("mat", 210.0e9, 0.3, density=7850.0)
    if family == "B2":
        coordinates = ((1, 0.0), (2, 2.0))
        element_type = BeamElement
        node_ids = [1, 2]
    else:
        coordinates = ((1, 0.0), (2, 1.0), (3, 2.0))
        element_type = QuadraticBeamElement
        node_ids = [1, 2, 3]
    for node_id, x in coordinates:
        model.add_node(node_id, x, 0.0, 0.0)
    cross_section = {
        "Iy": 3.0e-5,
        "Iz": 2.0e-5,
        "J": 4.0e-5,
        "area": 0.02,
        "orientation": (0.0, 1.0, 0.0),
    }
    element = element_type(1, node_ids, "mat", cross_section=cross_section)
    model.add_element(1, element)
    displacement = np.linspace(-1.0e-5, 2.0e-5, 6 * len(node_ids))
    return model, element, material, (cross_section, displacement)


def _legacy_family_probe(family: str) -> dict[str, Any]:
    import numpy as np

    from anysolver.elements import BeamElement, QuadraticBeamElement
    from anysolver.matrix_assembly import assemble_stiffness_matrix

    model, element, material, inputs = _legacy_fixture(family)
    cross_section, displacement = inputs
    element_type = BeamElement if family == "B2" else QuadraticBeamElement
    node_ids = [1, 2] if family == "B2" else [1, 2, 3]
    local = element.compute_stiffness_matrix(model.mesh, material)
    free = np.arange(6, len(displacement))
    reduced = np.asarray(local[np.ix_(free, free)], dtype=float)
    rhs = np.linspace(0.01, 0.01 * len(free), len(free))

    operations = {
        "CONSTRUCTION": lambda: element_type(
            2, node_ids, "mat", cross_section=dict(cross_section)
        ),
        "STIFFNESS": lambda: element.compute_stiffness_matrix(
            model.mesh, material
        ),
        "INTERNAL_FORCE": lambda: element.compute_internal_forces(
            model.mesh, displacement, material
        ),
        "ASSEMBLY": lambda: assemble_stiffness_matrix(model),
        "SOLVE": lambda: np.linalg.solve(reduced, rhs),
        "RECOVERY": lambda: element.compute_stresses(
            model.mesh, displacement, material
        ),
        "RESTART": lambda: json.dumps(
            element.to_dict(), allow_nan=False, separators=(",", ":"), sort_keys=True
        ),
    }
    if set(operations) != set(OPERATIONS):
        raise PackageGateError("internal performance operation inventory mismatch")
    measurements = {name: _measure(operations[name]) for name in OPERATIONS}
    return {
        "family": family,
        "inner_repetitions": PERFORMANCE_INNER_REPETITIONS,
        "measurements": measurements,
    }


def installed_performance_probe(sample_index: int) -> dict[str, Any]:
    if type(sample_index) is not int or sample_index < -1:
        raise PackageGateError("sample index must be -1 for warmup or non-negative")
    return {
        "families": {
            family: _legacy_family_probe(family) for family in ("B2", "B3")
        },
        "peak_rss_bytes": _peak_rss_bytes(),
        "sample_index": sample_index,
        "schema": PERFORMANCE_RAW_SCHEMA,
    }


def _array_sha256(value: Any) -> str:
    import numpy as np

    array = np.ascontiguousarray(np.asarray(value, dtype="<f8"))
    return hashlib.sha256(array.tobytes(order="C")).hexdigest().upper()


def installed_correctness_record(forbidden_repository_root: Path) -> dict[str, Any]:
    """Exercise the exact P3 public surface from an installed environment."""

    import numpy as np

    import anysolver
    from anysolver._native_rotation_state import create_native_rotation_state_store
    from anysolver.assembly import solve_linear
    from anysolver.beam_sections import GeneralizedBeamSection
    from anysolver.boundary import BoundaryCondition, LoadCase
    from anysolver.element_capabilities import (
        ElementCapabilityError,
        require_model_element_capabilities,
    )
    from anysolver.elements import CoupledBeamShellElement, create_element
    from anysolver.fe_core import FEModel
    from anysolver.ge_beam3_element import (
        GeBeam3IntegrationError,
        GeometricallyExactBeam3D3NElement,
        deserialize_ge_beam3_element,
        serialize_ge_beam3_element,
    )
    from anysolver.ge_beam3_mixed_element import (
        GeometricallyExactBeam3D3NElement as CandidateElement,
    )
    from anysolver.ge_beam3_mixed_state import serialize_ge_beam3_mixed_state
    from anysolver.ge_beam3_state import (
        STATE_LAYOUT_ID,
        STATE_SCHEMA,
        STATE_VERSION,
        GeBeam3CommittedStateError,
        deserialize_ge_beam3_state,
        serialize_ge_beam3_state,
    )
    from anysolver.nonlinear_state import create_model_native_rotation_store
    from anysolver.matrix_assembly import assemble_stiffness_matrix
    from anysolver.modal import solve_free_vibration
    from anysolver.mesh_gen import InterpolatedBeamShellMPCElement
    from anysolver.nonlinear_static import solve_static_nonlinear

    stiffness = np.diag((1.2e7, 3.1e6, 2.9e6, 8.0e5, 6.0e5, 4.0e5))
    mass = np.diag((12.0, 12.0, 12.0, 0.2, 0.3, 0.4))
    section = GeneralizedBeamSection(stiffness, mass_matrix=mass, name="P3_GATE")
    model = FEModel("p3-installed-check")
    model.add_material("mat", 210.0e9, 0.3, density=7850.0)
    for node_id, x in ((1, 0.0), (2, 1.0), (3, 2.0)):
        model.add_node(node_id, x, 0.0, 0.0)
    kwargs = {
        "section": section,
        "reference_orientation": (0.0, 1.0, 0.0),
        "reference_axis_direction": (1.0, 0.0, 0.0),
    }
    element = create_element(SELECTOR, 1, [1, 2, 3], "mat", **kwargs)
    if type(element) is not GeometricallyExactBeam3D3NElement:
        raise PackageGateError("exact selector did not return exact qualified class")
    if anysolver.GeometricallyExactBeam3D3NElement is not type(element):
        raise PackageGateError("root class export is not identical")
    if anysolver.GE_BEAM3_QUALIFIED_FORMULATION_ID != QUALIFIED_ID:
        raise PackageGateError("root formulation ID export mismatch")
    if not {
        "GE_BEAM3_QUALIFIED_FORMULATION_ID",
        "GeometricallyExactBeam3D3NElement",
    } <= set(anysolver.__all__):
        raise PackageGateError("qualified root exports are absent from __all__")
    for selector in NEGATIVE_SELECTORS:
        try:
            other = create_element(selector, 2, [1, 2, 3], "mat", **kwargs)
        except (TypeError, ValueError):
            continue
        if type(other) is GeometricallyExactBeam3D3NElement:
            raise PackageGateError(f"forbidden selector {selector} selected GE-B3")

    matrix = element.compute_stiffness_matrix(model.mesh, None)
    private = element.compute_candidate_stiffness_matrix(model.mesh)
    if matrix.tobytes(order="C") != private.tobytes(order="C"):
        raise PackageGateError("standard stiffness differs from accepted P2 operator")
    displacement = np.linspace(-2.0e-4, 3.0e-4, 18)
    force = element.compute_internal_forces(model.mesh, displacement, None)
    if not np.array_equal(force, matrix @ displacement):
        raise PackageGateError("standard internal force is not K @ u")
    model.add_element(element.element_id, element)
    assembled, assembly_info = assemble_stiffness_matrix(model)
    assembly_matrix = np.asarray(assembled.toarray(), dtype=np.float64)
    assembly_route = bool(
        np.array_equal(assembly_matrix, matrix)
        and int(assembly_info["num_elements"]) == 1
    )
    modal = solve_free_vibration(model, num_modes=6)
    modal_route = bool(modal.solver_status == "ok" and len(modal.modes) == 6)

    model.add_boundary_condition(
        BoundaryCondition(
            "fixed-end",
            [1],
            {name: 0.0 for name in ("ux", "uy", "uz", "rx", "ry", "rz")},
        )
    )
    axial = LoadCase("installed-axial")
    axial.add_nodal_load(3, forces=np.asarray((100.0, 0.0, 0.0)))
    linear_displacement, linear_info = solve_linear(model, axial)
    linear_route = bool(
        linear_info["convergence_info"]["status"] == "converged"
        and linear_info["result_case"]["analysis_case"]["analysis_type"]
        == "linear_static"
        and np.linalg.norm(linear_displacement) > 0.0
    )

    element_raw = serialize_ge_beam3_element(element, mesh=model.mesh)
    restored_element = deserialize_ge_beam3_element(element_raw)
    if serialize_ge_beam3_element(restored_element) != element_raw:
        raise PackageGateError("element record is not byte-identical")
    state = element.init_model_bound_nonlinear_state(model.mesh, None, 1)
    state_raw = serialize_ge_beam3_state(state)
    restored_state = deserialize_ge_beam3_state(state_raw)
    element.validate_model_bound_nonlinear_state(model.mesh, None, restored_state, 1)
    if serialize_ge_beam3_state(restored_state) != state_raw:
        raise PackageGateError("qualified state record is not byte-identical")

    candidate = CandidateElement(1, [1, 2, 3], "mat", **kwargs)
    candidate_state = candidate.init_model_bound_nonlinear_state(model.mesh, None, 1)
    try:
        deserialize_ge_beam3_state(serialize_ge_beam3_mixed_state(candidate_state))
    except GeBeam3CommittedStateError:
        candidate_rejected = True
    else:
        candidate_rejected = False

    nodes = tuple(element.node_ids)
    reference = element.get_node_coordinates(model.mesh)
    identity = np.repeat(np.eye(3, dtype=np.float64)[None, :, :], 3, axis=0)

    def state_store(total: np.ndarray, operators: np.ndarray) -> Any:
        made = create_native_rotation_state_store(
            nodes,
            rotational_dofs={
                node: (6 * row + 3, 6 * row + 4, 6 * row + 5)
                for row, node in enumerate(nodes)
            },
            coordinate_rows={node: row for row, node in enumerate(nodes)},
            committed_full_displacement=total,
            committed_full_coordinates=reference + total.reshape(3, 6)[:, :3],
            committed_rotation_matrices=operators,
            coordinate_node_ids=nodes,
        )
        if made is None:
            raise PackageGateError("native rotation store was not constructed")
        return made

    def evaluate_state(
        store: Any,
        committed: Mapping[str, Any],
        total: np.ndarray,
        *,
        commit: bool,
    ) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
        coordinates = reference + total.reshape(3, 6)[:, :3]
        with store.candidate(total, coordinates) as transaction:
            view = transaction.element_view(
                element.element_id,
                nodes,
                element.native_reference_directors(model.mesh),
            )
            made_force, made_tangent, made_state = element.compute_nonlinear_response(
                model.mesh,
                model.get_material("mat"),
                total,
                committed,
                1,
                True,
                native_rotation_trial=view,
            )
            if made_tangent is None:
                raise PackageGateError("nonlinear continuation omitted its tangent")
            if commit:
                transaction.commit(total, coordinates)
        return np.asarray(made_force), np.asarray(made_tangent), made_state

    first = np.asarray(
        (
            0.0, 0.0, 0.0, 0.012, -0.009, 0.007,
            0.001, -0.002, 0.004, -0.006, 0.011, 0.005,
            0.003, 0.001, 0.006, 0.008, -0.004, 0.013,
        ),
        dtype=np.float64,
    )
    second = first + np.asarray(
        (
            0.0002, -0.0001, 0.0003, -0.004, 0.003, 0.002,
            0.0004, 0.0002, -0.0001, 0.003, -0.002, 0.004,
            -0.0001, 0.0003, 0.0002, 0.002, 0.004, -0.003,
        ),
        dtype=np.float64,
    )
    continuous_store = state_store(np.zeros(18, dtype=np.float64), identity)
    _unused_force, _unused_tangent, first_state = evaluate_state(
        continuous_store, state, first, commit=True
    )
    checkpoint = serialize_ge_beam3_state(first_state)
    restored_checkpoint = deserialize_ge_beam3_state(checkpoint)
    continuous_force, continuous_tangent, continuous_state = evaluate_state(
        continuous_store, first_state, second, commit=False
    )
    restarted_store = create_model_native_rotation_store(
        model,
        {element.element_id: restored_checkpoint},
        np.asarray(restored_checkpoint["committed_total_u"], dtype=np.float64),
    )
    if restarted_store is None:
        raise PackageGateError("qualified restart did not reconstruct a native store")
    restarted_force, restarted_tangent, restarted_state = evaluate_state(
        restarted_store, restored_checkpoint, second, commit=False
    )
    restart_continuation = bool(
        np.array_equal(restarted_force, continuous_force)
        and np.array_equal(restarted_tangent, continuous_tangent)
        and serialize_ge_beam3_state(restarted_state)
        == serialize_ge_beam3_state(continuous_state)
    )

    full_solution = solve_static_nonlinear(
        model,
        axial,
        num_steps=2,
        max_iterations=12,
        tolerance=1.0e-8,
        emit_restart_checkpoint=True,
    )
    partial_solution = solve_static_nonlinear(
        model,
        axial,
        max_load_factor=0.5,
        num_steps=1,
        max_iterations=12,
        tolerance=1.0e-8,
        emit_restart_checkpoint=True,
    )
    if partial_solution.restart_checkpoint is None:
        raise PackageGateError("installed nonlinear solve omitted its restart checkpoint")
    resumed_solution = solve_static_nonlinear(
        model,
        axial,
        max_load_factor=1.0,
        num_steps=2,
        max_iterations=12,
        tolerance=1.0e-8,
        restart_checkpoint=partial_solution.restart_checkpoint,
    )
    global_nonlinear_restart = bool(
        full_solution.status == resumed_solution.status == "completed"
        and np.array_equal(full_solution.displacements, resumed_solution.displacements)
        and serialize_ge_beam3_state(full_solution.element_states[1])
        == serialize_ge_beam3_state(resumed_solution.element_states[1])
    )
    rotations = np.repeat(np.eye(3)[None, :, :], 3, axis=0)
    recovery = element.recover_native_fields(
        model.mesh, np.zeros(18), rotation_matrices=rotations
    )
    mass_matrix = element.compute_mass_matrix(model.mesh, None)
    buckling = element.compute_reference_geometric_stiffness(
        model.mesh, axial_compression=1.0
    )
    standard_buckling = element.compute_geometric_stiffness_matrix(
        model.mesh, None, {"axial_compression": 1.0}
    )
    try:
        element.compute_geometric_stiffness_matrix(model.mesh, None, {})
    except GeBeam3IntegrationError:
        current_state_rejected = True
    else:
        current_state_rejected = False
    required_gaps = frozenset(
        {
            "beam_shell_connection",
            "conservative_follower_loads",
            "current_state_buckling",
            "current_state_modal",
            "curved_reference",
            "finite_rotation_transient_dynamics",
            "gyroscopic_terms",
            "history_bearing_sections",
            "linear_transient_dynamics",
            "nonconservative_follower_loads",
            "transient_algebraic_dynamics",
        }
    )
    try:
        require_model_element_capabilities(
            model,
            required_gaps,
            context="P3 installed unsupported-route guard",
        )
    except ElementCapabilityError:
        unsupported_guard_rejected = True
    else:
        unsupported_guard_rejected = False

    joint_model = FEModel("p3-installed-joint-negative")
    joint_model.add_material("mat", 210.0e9, 0.3, density=7850.0)
    for node_id, coordinates in (
        (1, (0.0, 0.0, 0.0)),
        (2, (1.0, 0.0, 0.0)),
        (3, (2.0, 0.0, 0.0)),
        (4, (2.0, 1.0, 0.0)),
    ):
        joint_model.add_node(node_id, *coordinates)
    joint_element = create_element(SELECTOR, 1, [1, 2, 3], "mat", **kwargs)
    joint_model.add_element(1, joint_element)
    joint_model.add_element(
        99,
        CoupledBeamShellElement(
            99,
            beam_node_id=3,
            shell_node_id=4,
            material_name="mat",
        ),
    )
    try:
        assemble_stiffness_matrix(joint_model)
    except GeBeam3IntegrationError:
        beam_shell_joint_rejected = True
    else:
        beam_shell_joint_rejected = False

    interpolated_model = FEModel("p3-installed-interpolated-joint-negative")
    interpolated_model.add_material("mat", 210.0e9, 0.3, density=7850.0)
    for node_id, coordinates in (
        (1, (0.0, 0.0, 0.0)),
        (2, (1.0, 0.0, 0.0)),
        (3, (2.0, 0.0, 0.0)),
        (4, (2.0, 1.0, 0.0)),
    ):
        interpolated_model.add_node(node_id, *coordinates)
    interpolated_element = create_element(SELECTOR, 1, [1, 2, 3], "mat", **kwargs)
    interpolated_model.add_element(1, interpolated_element)
    interpolated_model.add_element(
        100,
        InterpolatedBeamShellMPCElement(
            100,
            beam_node_id=3,
            shell_node_ids=[4],
            shape_weights=np.asarray((1.0,)),
            eccentricity=np.zeros(3),
            material_name="mat",
        ),
    )
    try:
        assemble_stiffness_matrix(interpolated_model)
    except GeBeam3IntegrationError:
        interpolated_joint_rejected = True
    else:
        interpolated_joint_rejected = False

    module_files = []
    for name, module in sorted(sys.modules.items()):
        if name == "anysolver" or name.startswith("anysolver."):
            raw_file = getattr(module, "__file__", None)
            if raw_file:
                module_files.append(Path(raw_file).resolve(strict=True))
    prefix = Path(sys.prefix).resolve(strict=True)
    origins_inside = bool(module_files) and all(_inside(path, prefix) for path in module_files)
    forbidden = forbidden_repository_root.resolve(strict=True)
    search_paths = [
        Path(item).resolve(strict=True)
        for item in sys.path
        if item and Path(item).exists()
    ]
    repository_absent = (
        not _inside(Path.cwd(), forbidden)
        and not _inside(Path(__file__), forbidden)
        and all(not _inside(path, forbidden) for path in search_paths)
        and all(not _inside(path, forbidden) for path in module_files)
    )
    checks = {
        "candidate_state_rejected": candidate_rejected,
        "beam_shell_joint_rejected": beam_shell_joint_rejected,
        "current_state_buckling_rejected": current_state_rejected,
        "global_nonlinear_restart": global_nonlinear_restart,
        "installed_standard_assembly": assembly_route,
        "installed_standard_linear_solve": linear_route,
        "installed_standard_modal": modal_route,
        "interpolated_beam_shell_joint_rejected": interpolated_joint_rejected,
        "element_roundtrip": serialize_ge_beam3_element(restored_element) == element_raw,
        "formulation_id": element.formulation_id == QUALIFIED_ID,
        "mass_positive": bool(np.linalg.eigvalsh(mass_matrix)[0] > 0.0),
        "module_origins_inside_environment": origins_inside,
        "native_recovery_four_stations": len(recovery["station_order"]) == 4,
        "reference_buckling_symmetric": bool(np.array_equal(buckling, buckling.T)),
        "repository_absent": repository_absent,
        "restart_nonzero_continuation": restart_continuation,
        "root_export_identity": anysolver.GeometricallyExactBeam3D3NElement is type(element),
        "selector_exact": type(element) is GeometricallyExactBeam3D3NElement,
        "state_roundtrip": serialize_ge_beam3_state(restored_state) == state_raw,
        "standard_internal_force": bool(np.array_equal(force, matrix @ displacement)),
        "standard_reference_buckling": bool(np.array_equal(standard_buckling, buckling)),
        "standard_stiffness": matrix.tobytes(order="C") == private.tobytes(order="C"),
        "unsupported_capability_inventory": required_gaps <= element.capability_gaps,
        "unsupported_guard_rejected": unsupported_guard_rejected,
    }
    if not all(checks.values()):
        failed = ", ".join(sorted(name for name, passed in checks.items() if not passed))
        raise PackageGateError(f"installed-wheel checks failed: {failed}")
    return {
        "array_hashes": {
            "buckling": _array_sha256(buckling),
            "global_nonlinear_displacement": _array_sha256(
                full_solution.displacements
            ),
            "internal_force": _array_sha256(force),
            "linear_displacement": _array_sha256(linear_displacement),
            "mass": _array_sha256(mass_matrix),
            "nonzero_restart_state": hashlib.sha256(
                serialize_ge_beam3_state(restarted_state)
            ).hexdigest().upper(),
            "recovery_resultants": _array_sha256(
                recovery["local_generalized_resultant"]
            ),
            "stiffness": _array_sha256(matrix),
        },
        "check_count": len(checks),
        "checks": checks,
        "element_record_sha256": hashlib.sha256(element_raw).hexdigest().upper(),
        "formulation_id": QUALIFIED_ID,
        "loaded_anysolver_module_count": len(module_files),
        "schema": CHECK_SCHEMA,
        "selector": SELECTOR,
        "state_layout_id": STATE_LAYOUT_ID,
        "state_record_sha256": hashlib.sha256(state_raw).hexdigest().upper(),
        "state_schema": STATE_SCHEMA,
        "state_version": STATE_VERSION,
    }


def _git_environment() -> dict[str, str]:
    environment = _bounded_environment()
    for key in tuple(environment):
        if key.upper().startswith("GIT_"):
            environment.pop(key, None)
    environment.update(
        {
            "GIT_ATTR_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_NO_REPLACE_OBJECTS": "1",
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_TERMINAL_PROMPT": "0",
        }
    )
    return environment


def _git_command(
    *arguments: str,
    safe_directory: Path | None = None,
) -> list[str]:
    command = [
        "git",
        "--no-replace-objects",
        "-c",
        "core.attributesFile=NUL" if os.name == "nt" else "core.attributesFile=/dev/null",
    ]
    if safe_directory is not None:
        command.extend(("-c", f"safe.directory={safe_directory.resolve(strict=True)}"))
    command.extend(arguments)
    return command


def _git(repository: Path, *arguments: str) -> str:
    result = subprocess.run(
        _git_command(*arguments, safe_directory=repository),
        cwd=str(repository),
        env=_git_environment(),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        raise PackageGateError(result.stderr.strip() or "git command failed")
    return result.stdout.strip()


def _git_bytes(repository: Path, *arguments: str) -> bytes:
    result = subprocess.run(
        _git_command(*arguments, safe_directory=repository),
        cwd=str(repository),
        env=_git_environment(),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=30,
    )
    if result.returncode != 0:
        raise PackageGateError(
            result.stderr.decode("utf-8", errors="replace").strip()
            or "git byte command failed"
        )
    return result.stdout


def run_package_gate(repository: Path, output_root: Path) -> dict[str, Any]:
    _require_formal_process_containment()
    deadline = time.monotonic() + WAVE_TIMEOUT_SECONDS
    repository = repository.resolve(strict=True)
    output_root.mkdir(parents=True, exist_ok=False)
    if _git(repository, "status", "--porcelain=v1", "--untracked-files=all"):
        raise PackageGateError("candidate repository must be clean")
    commit = _git(repository, "rev-parse", "HEAD")
    tree = _git(repository, "rev-parse", "HEAD^{tree}")
    diagnostics = output_root / "diagnostics"
    candidate_archive = output_root / "candidate-source.tar"
    run_bounded(
        [
            *_git_command(
                "archive",
                "--format=tar",
                f"--output={candidate_archive}",
                commit,
                safe_directory=repository,
            ),
        ],
        cwd=repository,
        log_path=diagnostics / "candidate-archive.log",
        deadline_monotonic=deadline,
    )
    candidate_source = output_root / "candidate-source"
    candidate_source.mkdir()
    with tarfile.open(candidate_archive, mode="r:") as archive:
        archive.extractall(candidate_source, filter="data")
    external_runner = output_root / "installed-check-runner.py"
    committed_runner = _git_bytes(
        repository,
        "cat-file",
        "blob",
        f"{commit}:{RUNNER_RELATIVE_PATH.as_posix()}",
    )
    materialized_runner = (candidate_source / RUNNER_RELATIVE_PATH).read_bytes()
    if materialized_runner != committed_runner:
        raise PackageGateError("materialized runner differs from the frozen Git blob")
    external_runner.write_bytes(materialized_runner)
    external_runner_identity = _regular_file_identity(external_runner)
    external_runner_hash = external_runner_identity["sha256"]
    wheel_directory = output_root / "wheel"
    wheel_directory.mkdir()
    run_bounded(
        [
            sys.executable,
            "-m",
            "pip",
            "wheel",
            "--no-deps",
            "--no-build-isolation",
            "--wheel-dir",
            str(wheel_directory),
            str(candidate_source),
        ],
        cwd=output_root,
        log_path=diagnostics / "build.log",
        deadline_monotonic=deadline,
    )
    wheels = sorted(wheel_directory.glob("*.whl"))
    if len(wheels) != 1:
        raise PackageGateError("build must create exactly one wheel")
    wheel_identity = assert_regular_wheel(wheels[0])

    check_hashes = []
    check_bytes = []
    for run_index in range(2):
        environment_root = output_root / f"environment-{run_index + 1}"
        run_bounded(
            [sys.executable, "-m", "venv", str(environment_root)],
            cwd=output_root,
            log_path=diagnostics / f"venv-{run_index + 1}.log",
            deadline_monotonic=deadline,
        )
        python = (
            environment_root / "Scripts" / "python.exe"
            if os.name == "nt"
            else environment_root / "bin" / "python"
        )
        _require_file_identity(wheels[0], wheel_identity)
        run_bounded(
            [
                str(python),
                "-s",
                "-P",
                "-B",
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                str(wheels[0]),
            ],
            cwd=output_root,
            log_path=diagnostics / f"install-{run_index + 1}.log",
            deadline_monotonic=deadline,
        )
        _require_file_identity(wheels[0], wheel_identity)
        result_path = output_root / f"installed-check-{run_index + 1}.json"
        _require_file_identity(external_runner, external_runner_identity)
        run_bounded(
            [
                str(python),
                "-s",
                "-P",
                "-B",
                str(external_runner),
                "--installed-check",
                "--forbidden-repository-root",
                str(repository),
                "--output",
                str(result_path),
            ],
            cwd=output_root,
            log_path=diagnostics / f"check-{run_index + 1}.log",
            deadline_monotonic=deadline,
        )
        _require_file_identity(external_runner, external_runner_identity)
        raw = result_path.read_bytes()
        _validate_installed_correctness_record(strict_canonical_json_loads(raw))
        check_bytes.append(raw)
        check_hashes.append(hashlib.sha256(raw).hexdigest().upper())
    if check_bytes[0] != check_bytes[1]:
        raise PackageGateError("two installed correctness records disagree")
    _require_file_identity(wheels[0], wheel_identity)
    _require_file_identity(external_runner, external_runner_identity)
    aggregate = {
        "candidate_commit": commit,
        "candidate_tree": tree,
        "canonical_run_count": 2,
        "correctness_record_sha256": check_hashes[0],
        "correctness_records_byte_identical": True,
        "formulation_id": QUALIFIED_ID,
        "installed_runner_sha256": external_runner_hash,
        "package_gate_passed": True,
        "process_containment": PROCESS_CONTAINMENT_ID,
        "schema": SCHEMA,
        "selector": SELECTOR,
        "wheel": wheel_identity,
    }
    write_exclusive(output_root / "package-aggregate.json", aggregate)
    return aggregate


def _venv_python(environment_root: Path) -> Path:
    return (
        environment_root / "Scripts" / "python.exe"
        if os.name == "nt"
        else environment_root / "bin" / "python"
    )


def _install_wheel_environment(
    wheel: Path,
    environment_root: Path,
    *,
    output_root: Path,
    diagnostics: Path,
    role: str,
    deadline_monotonic: float,
) -> Path:
    run_bounded(
        [sys.executable, "-m", "venv", str(environment_root)],
        cwd=output_root,
        log_path=diagnostics / f"{role}-venv.log",
        deadline_monotonic=deadline_monotonic,
    )
    python = _venv_python(environment_root)
    run_bounded(
        [
            str(python),
            "-I",
            "-B",
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            str(wheel),
        ],
        cwd=output_root,
        log_path=diagnostics / f"{role}-install.log",
        deadline_monotonic=deadline_monotonic,
    )
    return python


def _validate_raw_performance_record(
    value: Any, *, sample_index: int
) -> dict[str, Any]:
    if not isinstance(value, Mapping) or set(value) != {
        "families",
        "peak_rss_bytes",
        "sample_index",
        "schema",
    }:
        raise PackageGateError("raw performance record keys mismatch")
    if value["schema"] != PERFORMANCE_RAW_SCHEMA:
        raise PackageGateError("raw performance schema mismatch")
    if value["sample_index"] != sample_index:
        raise PackageGateError("raw performance sample index mismatch")
    if type(value["peak_rss_bytes"]) is not int or value["peak_rss_bytes"] <= 0:
        raise PackageGateError("raw performance peak RSS is malformed")
    families = value["families"]
    if not isinstance(families, Mapping) or set(families) != {"B2", "B3"}:
        raise PackageGateError("raw performance family inventory mismatch")
    for family, record in families.items():
        if not isinstance(record, Mapping) or set(record) != {
            "family",
            "inner_repetitions",
            "measurements",
        }:
            raise PackageGateError("raw performance family keys mismatch")
        if record["family"] != family:
            raise PackageGateError("raw performance family label mismatch")
        if record["inner_repetitions"] != PERFORMANCE_INNER_REPETITIONS:
            raise PackageGateError("raw performance repetition count mismatch")
        measurements = record["measurements"]
        if not isinstance(measurements, Mapping) or set(measurements) != set(
            OPERATIONS
        ):
            raise PackageGateError("raw performance operation inventory mismatch")
        for measurement in measurements.values():
            if not isinstance(measurement, Mapping) or set(measurement) != {
                "cpu_ns_per_call",
                "wall_ns_per_call",
            }:
                raise PackageGateError("raw performance measurement keys mismatch")
            if any(type(item) is not int or item <= 0 for item in measurement.values()):
                raise PackageGateError("raw performance measurement is malformed")
    return dict(value)


def run_performance_gate(
    repository: Path,
    candidate_wheel: Path,
    output_root: Path,
    *,
    package_aggregate: Path,
    pair_count: int = MINIMUM_PAIRS,
) -> dict[str, Any]:
    """Run the paired, order-balanced B2/B3 wheel comparison."""

    _require_formal_process_containment()
    repository = repository.resolve(strict=True)
    candidate_wheel = candidate_wheel.resolve(strict=True)
    package_aggregate = package_aggregate.resolve(strict=True)
    deadline = time.monotonic() + WAVE_TIMEOUT_SECONDS
    candidate_wheel_identity = assert_regular_wheel(candidate_wheel)
    package_information = package_aggregate.lstat()
    if (
        not stat.S_ISREG(package_information.st_mode)
        or package_aggregate.is_symlink()
        or int(getattr(package_information, "st_file_attributes", 0))
        & int(getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))
    ):
        raise PackageGateError("package aggregate must be a regular non-reparse file")
    package_file_identity = _regular_file_identity(package_aggregate)
    package_raw = package_aggregate.read_bytes()
    _require_file_identity(package_aggregate, package_file_identity)
    if hashlib.sha256(package_raw).hexdigest().upper() != package_file_identity["sha256"]:
        raise PackageGateError("package aggregate changed while it was read")
    package_record = _validate_package_aggregate(
        strict_canonical_json_loads(package_raw)
    )
    orders = balanced_orders(pair_count)
    output_root.mkdir(parents=True, exist_ok=False)
    if _git(repository, "status", "--porcelain=v1", "--untracked-files=all"):
        raise PackageGateError("candidate repository must be clean")
    candidate_commit = _git(repository, "rev-parse", "HEAD")
    candidate_tree = _git(repository, "rev-parse", "HEAD^{tree}")
    if (
        package_record["candidate_commit"] != candidate_commit
        or package_record["candidate_tree"] != candidate_tree
    ):
        raise PackageGateError("package aggregate does not bind current candidate")
    if package_record["wheel"] != candidate_wheel_identity:
        raise PackageGateError("candidate wheel differs from package-gate wheel")
    private_candidate_wheel = output_root / "candidate-wheel" / candidate_wheel.name
    private_candidate_identity = _copy_exclusive_verified(
        candidate_wheel,
        private_candidate_wheel,
        candidate_wheel_identity,
    )
    if _git(repository, "rev-parse", BASE_COMMIT) != BASE_COMMIT:
        raise PackageGateError("registered base commit is unavailable")

    diagnostics = output_root / "diagnostics"
    base_archive = output_root / "base-source.tar"
    run_bounded(
        _git_command(
            "archive",
            "--format=tar",
            f"--output={base_archive}",
            BASE_COMMIT,
            safe_directory=repository,
        ),
        cwd=repository,
        log_path=diagnostics / "base-archive.log",
        deadline_monotonic=deadline,
    )
    base_source = output_root / "base-source"
    base_source.mkdir()
    with tarfile.open(base_archive, mode="r:") as archive:
        archive.extractall(base_source, filter="data")
    base_wheel_directory = output_root / "base-wheel"
    base_wheel_directory.mkdir()
    run_bounded(
        [
            sys.executable,
            "-m",
            "pip",
            "wheel",
            "--no-deps",
            "--no-build-isolation",
            "--wheel-dir",
            str(base_wheel_directory),
            str(base_source),
        ],
        cwd=output_root,
        log_path=diagnostics / "base-build.log",
        deadline_monotonic=deadline,
    )
    base_wheels = sorted(base_wheel_directory.glob("*.whl"))
    if len(base_wheels) != 1:
        raise PackageGateError("base build must create exactly one wheel")
    base_wheel_identity = assert_regular_wheel(base_wheels[0])

    _require_file_identity(base_wheels[0], base_wheel_identity)
    base_python = _install_wheel_environment(
        base_wheels[0],
        output_root / "base-environment",
        output_root=output_root,
        diagnostics=diagnostics,
        role="base",
        deadline_monotonic=deadline,
    )
    _require_file_identity(base_wheels[0], base_wheel_identity)
    _require_file_identity(private_candidate_wheel, private_candidate_identity)
    candidate_python = _install_wheel_environment(
        private_candidate_wheel,
        output_root / "candidate-environment",
        output_root=output_root,
        diagnostics=diagnostics,
        role="candidate",
        deadline_monotonic=deadline,
    )
    _require_file_identity(private_candidate_wheel, private_candidate_identity)
    python_by_role = {"base": base_python, "candidate": candidate_python}
    external_runner = output_root / "performance-runner.py"
    external_runner.write_bytes(
        _git_bytes(
            repository,
            "cat-file",
            "blob",
            f"{candidate_commit}:{RUNNER_RELATIVE_PATH.as_posix()}",
        )
    )
    external_runner_identity = _regular_file_identity(external_runner)
    external_runner_hash = external_runner_identity["sha256"]
    if external_runner_hash != package_record["installed_runner_sha256"]:
        raise PackageGateError("performance runner differs from package-gate runner")

    raw_records: dict[str, list[dict[str, Any]]] = {"base": [], "candidate": []}
    raw_graph = []

    def execute(role: str, sample_index: int, label: str) -> None:
        result_path = output_root / "raw" / f"{label}-{role}.json"
        _require_file_identity(external_runner, external_runner_identity)
        run_bounded(
            [
                str(python_by_role[role]),
                "-s",
                "-P",
                "-B",
                str(external_runner),
                "--performance-probe",
                "--sample-index",
                str(sample_index),
                "--output",
                str(result_path),
            ],
            cwd=output_root,
            log_path=diagnostics / f"{label}-{role}.log",
            deadline_monotonic=deadline,
        )
        _require_file_identity(external_runner, external_runner_identity)
        raw = result_path.read_bytes()
        record = _validate_raw_performance_record(
            strict_canonical_json_loads(raw), sample_index=sample_index
        )
        if sample_index >= 0:
            raw_records[role].append(record)
            raw_graph.append(
                {
                    "bytes": len(raw),
                    "role": role,
                    "sample_index": sample_index,
                    "sha256": hashlib.sha256(raw).hexdigest().upper(),
                }
            )

    execute("base", -1, "warmup")
    execute("candidate", -1, "warmup")
    for sample_index, order in enumerate(orders):
        for role in order:
            execute(role, sample_index, f"pair-{sample_index + 1:02d}")

    diagnostic_summary: dict[str, Any] = {
        "families": {},
        "pair_count": pair_count,
        "schema": "anysolver.ge-beam3-mixed-p3-performance-diagnostics-v1",
    }
    for family in ("B2", "B3"):
        family_diagnostic: dict[str, Any] = {}
        for role in ("base", "candidate"):
            role_diagnostic: dict[str, Any] = {"operations": {}}
            peak_rss = [
                float(record["peak_rss_bytes"]) for record in raw_records[role]
            ]
            role_diagnostic["peak_rss_bytes"] = summarize_timings(peak_rss)
            for operation in OPERATIONS:
                measurements = [
                    record["families"][family]["measurements"][operation]
                    for record in raw_records[role]
                ]
                role_diagnostic["operations"][operation] = {
                    "cpu_ns_per_call": summarize_timings(
                        [float(item["cpu_ns_per_call"]) for item in measurements]
                    ),
                    "wall_ns_per_call": summarize_timings(
                        [float(item["wall_ns_per_call"]) for item in measurements]
                    ),
                }
            family_diagnostic[role] = role_diagnostic
        diagnostic_summary["families"][family] = family_diagnostic
    performance_diagnostics_path = diagnostics / "performance-statistics.json"
    write_exclusive(performance_diagnostics_path, diagnostic_summary)

    family_summaries: dict[str, Any] = {}
    all_pass = True
    for family in ("B2", "B3"):
        samples: dict[str, dict[str, list[float]]] = {
            role: {operation: [] for operation in OPERATIONS}
            for role in ("base", "candidate")
        }
        for role in ("base", "candidate"):
            if len(raw_records[role]) != pair_count:
                raise PackageGateError("raw performance pair count mismatch")
            for record in raw_records[role]:
                measurements = record["families"][family]["measurements"]
                for operation in OPERATIONS:
                    samples[role][operation].append(
                        float(measurements[operation]["wall_ns_per_call"])
                    )
        family_summary = adjudicate_performance(
            samples["base"], samples["candidate"]
        )
        family_summaries[family] = family_summary
        all_pass = all_pass and bool(family_summary["all_operations_pass"])

    order_hash = hashlib.sha256(
        canonical_json_bytes([list(order) for order in orders])
    ).hexdigest().upper()
    raw_graph_hash = hashlib.sha256(canonical_json_bytes(raw_graph)).hexdigest().upper()
    _require_file_identity(package_aggregate, package_file_identity)
    _require_file_identity(candidate_wheel, candidate_wheel_identity)
    _require_file_identity(private_candidate_wheel, private_candidate_identity)
    _require_file_identity(base_wheels[0], base_wheel_identity)
    _require_file_identity(external_runner, external_runner_identity)
    aggregate = {
        "all_existing_paths_pass": all_pass,
        "base_commit": BASE_COMMIT,
        "base_wheel": base_wheel_identity,
        "candidate_commit": candidate_commit,
        "candidate_tree": candidate_tree,
        "candidate_wheel": candidate_wheel_identity,
        "families": family_summaries,
        "ge_beam3_speed_gate": "NONE",
        "installed_runner_sha256": external_runner_hash,
        "order_sha256": order_hash,
        "package_aggregate_sha256": hashlib.sha256(package_raw).hexdigest().upper(),
        "pair_count": pair_count,
        "performance_diagnostics_sha256": sha256_file(
            performance_diagnostics_path
        ),
        "process_containment": PROCESS_CONTAINMENT_ID,
        "raw_record_count": len(raw_graph),
        "raw_record_graph_sha256": raw_graph_hash,
        "schema": PERFORMANCE_SCHEMA,
        "warmup_count_per_role": 1,
    }
    write_exclusive(output_root / "performance-aggregate.json", aggregate)
    return aggregate


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--installed-check", action="store_true")
    mode.add_argument("--performance-probe", action="store_true")
    mode.add_argument("--run-package-gate", action="store_true")
    mode.add_argument("--run-performance-gate", action="store_true")
    parser.add_argument("--repository", type=Path)
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--forbidden-repository-root", type=Path)
    parser.add_argument("--candidate-wheel", type=Path)
    parser.add_argument("--package-aggregate", type=Path)
    parser.add_argument("--sample-index", type=int)
    parser.add_argument("--pair-count", type=int, default=MINIMUM_PAIRS)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    if arguments.installed_check:
        if arguments.output is None or arguments.forbidden_repository_root is None:
            raise PackageGateError(
                "--output and --forbidden-repository-root are required for installed check"
            )
        write_exclusive(
            arguments.output,
            installed_correctness_record(arguments.forbidden_repository_root),
        )
        return 0
    if arguments.performance_probe:
        if arguments.output is None or arguments.sample_index is None:
            raise PackageGateError(
                "--output and --sample-index are required for performance probe"
            )
        write_exclusive(
            arguments.output,
            installed_performance_probe(arguments.sample_index),
        )
        return 0
    if arguments.repository is None or arguments.output_root is None:
        raise PackageGateError(
            "--repository and --output-root are required for coordinator mode"
        )
    if arguments.run_package_gate:
        run_package_gate(arguments.repository, arguments.output_root)
        return 0
    if arguments.candidate_wheel is None:
        raise PackageGateError("--candidate-wheel is required for performance gate")
    if arguments.package_aggregate is None:
        raise PackageGateError("--package-aggregate is required for performance gate")
    run_performance_gate(
        arguments.repository,
        arguments.candidate_wheel,
        arguments.output_root,
        package_aggregate=arguments.package_aggregate,
        pair_count=arguments.pair_count,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
