"""Bounded process-tree supervision for the F03 local scientific runner.

The supervisor is mechanics-blind.  It starts one already-registered child,
accounts for the resident memory of the observed process tree, and returns a
typed receipt.  It does not register, retry, assemble, factor, solve, or decide
scientific acceptance.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import os
from pathlib import Path
import subprocess
import time
from typing import Callable, IO, Mapping, Sequence

import psutil


THREADS = (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
)


@dataclass(frozen=True, slots=True)
class SupervisorLimits:
    seconds: float
    rss_bytes: int
    poll_seconds: float = 0.1

    def __post_init__(self):
        if (
            isinstance(self.seconds, bool)
            or not isinstance(self.seconds, (int, float))
            or not math.isfinite(float(self.seconds))
            or self.seconds <= 0
            or type(self.rss_bytes) is not int
            or self.rss_bytes <= 0
            or isinstance(self.poll_seconds, bool)
            or not isinstance(self.poll_seconds, (int, float))
            or not math.isfinite(float(self.poll_seconds))
            or not 0 < self.poll_seconds <= 1
        ):
            raise ValueError("positive finite process-tree limits required")


SCIENTIFIC_LIMITS = SupervisorLimits(1_800.0, 6 * 1024**3, 0.1)


@dataclass(frozen=True, slots=True)
class SupervisionReceipt:
    reason: str
    exit_code: int | None
    root_pid: int | None
    elapsed_seconds: float
    sampled_peak_tree_rss_bytes: int
    observed_pids: tuple[int, ...]
    terminated_pids: tuple[int, ...]
    failure: str | None

    def __post_init__(self):
        allowed = {
            "completed",
            "time_limit",
            "rss_limit",
            "launch_failure",
            "supervisor_failure",
            "orphaned_descendants",
            "cancelled",
        }
        if (
            self.reason not in allowed
            or (self.exit_code is not None and type(self.exit_code) is not int)
            or (self.root_pid is not None and (type(self.root_pid) is not int or self.root_pid <= 0))
            or (self.root_pid is None and self.reason not in {"launch_failure", "cancelled"})
            or (self.reason == "launch_failure" and self.root_pid is not None)
            or (self.root_pid is None and self.exit_code is not None)
            or not isinstance(self.elapsed_seconds, (int, float))
            or not math.isfinite(float(self.elapsed_seconds))
            or self.elapsed_seconds < 0
            or type(self.sampled_peak_tree_rss_bytes) is not int
            or self.sampled_peak_tree_rss_bytes < 0
            or type(self.observed_pids) is not tuple
            or type(self.terminated_pids) is not tuple
            or any(type(pid) is not int or pid <= 0 for pid in self.observed_pids + self.terminated_pids)
            or tuple(sorted(set(self.observed_pids))) != self.observed_pids
            or tuple(sorted(set(self.terminated_pids))) != self.terminated_pids
            or (self.root_pid is None and (
                self.sampled_peak_tree_rss_bytes != 0
                or self.observed_pids or self.terminated_pids
            ))
            or (self.failure is not None and type(self.failure) is not str)
        ):
            raise ValueError("invalid F03 process-tree supervision receipt")


class SupervisionCancelled(KeyboardInterrupt):
    """Cooperative cancellation with the retained process-tree receipt."""

    def __init__(self, receipt: SupervisionReceipt):
        if type(receipt) is not SupervisionReceipt or receipt.reason != "cancelled":
            raise ValueError("cancelled F03 supervision receipt required")
        self.receipt = receipt
        super().__init__("F03 process-tree supervision cancelled")


def frozen_thread_environment(source: Mapping[str, str] | None = None) -> dict[str, str]:
    if source is None:
        source = os.environ
    if not isinstance(source, Mapping) or any(
        type(key) is not str or type(value) is not str for key, value in source.items()
    ):
        raise ValueError("string process environment required")
    result = dict(source)
    result.update({name: "1" for name in THREADS})
    return result


def _tree_sample(root, tracked: dict[int, object]) -> int:
    # Retain every process once observed.  A worker can outlive an intermediate
    # parent and disappear from a later root.children() result while remaining
    # part of the owned tree that must be accounted and terminated.
    root_pid = int(root.pid)
    if root_pid <= 0:
        raise ValueError("invalid supervised root process identity")
    tracked.setdefault(root_pid, root)
    try:
        discovered = root.children(recursive=True)
    except psutil.NoSuchProcess:
        discovered = ()
    # Populate cleanup ownership before any memory query can fail or be
    # cancelled.  Existing Process objects retain their original PID identity.
    for process in discovered:
        pid = int(process.pid)
        if pid <= 0:
            raise ValueError("invalid supervised descendant process identity")
        tracked.setdefault(pid, process)
    total = 0
    for process in tuple(tracked.values()):
        try:
            if not _running(process):
                continue
            total += int(process.memory_info().rss)
        except psutil.NoSuchProcess:
            continue
    return total


def _running(process) -> bool:
    try:
        return bool(process.is_running()) and process.status() != psutil.STATUS_ZOMBIE
    except (psutil.NoSuchProcess, psutil.ZombieProcess):
        return False


def _terminate(
    processes: Sequence[object], *, record: set[int] | None = None,
) -> tuple[int, ...]:
    terminated: set[int] = set()
    unique = {int(process.pid): process for process in processes if int(process.pid) > 0}
    # Callers provide root before recursively discovered descendants.  Reverse
    # insertion order so descendants are killed before their owner.
    for pid in reversed(tuple(unique)):
        process = unique[pid]
        if not _running(process):
            continue
        try:
            process.kill()
            terminated.add(pid)
            if record is not None:
                record.add(pid)
        except psutil.NoSuchProcess:
            continue
    if unique:
        try:
            psutil.wait_procs(tuple(unique.values()), timeout=5.0)
        except (psutil.Error, OSError):
            pass
    return tuple(sorted(terminated))


def supervise(
    command: Sequence[str],
    *,
    cwd: Path,
    environment: Mapping[str, str],
    stdout: IO[str],
    stderr: IO[str],
    limits: SupervisorLimits = SCIENTIFIC_LIMITS,
    popen: Callable[..., object] = subprocess.Popen,
    process_factory: Callable[[int], object] = psutil.Process,
    monotonic: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
) -> SupervisionReceipt:
    """Run one command once and account for its observed process tree."""
    if (
        type(command) not in (tuple, list)
        or not command
        or any(type(item) is not str or not item for item in command)
        or not isinstance(cwd, Path)
        or not cwd.is_dir()
        or not isinstance(environment, Mapping)
        or any(type(key) is not str or type(value) is not str for key, value in environment.items())
        or not hasattr(stdout, "write")
        or not hasattr(stderr, "write")
        or type(limits) is not SupervisorLimits
    ):
        raise ValueError("validated process-tree supervision inputs required")
    begun = monotonic()
    process = None
    root = None
    reason = "supervisor_failure"
    failure = None
    exit_code = None
    root_pid = None
    peak = 0
    tracked: dict[int, object] = {}
    terminated: set[int] = set()
    interruption: KeyboardInterrupt | None = None
    try:
        flags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
        process = popen(
            tuple(command),
            cwd=cwd,
            env=dict(environment),
            stdout=stdout,
            stderr=stderr,
            creationflags=flags,
        )
        root_pid = int(process.pid)
        if root_pid <= 0:
            raise ValueError("invalid launched process identity")
        root = process_factory(process.pid)
        while True:
            peak = max(peak, _tree_sample(root, tracked))
            elapsed = monotonic() - begun
            code = process.poll()
            if peak > limits.rss_bytes:
                reason = "rss_limit"
                break
            if elapsed > limits.seconds:
                reason = "time_limit"
                break
            if code is not None:
                exit_code = int(code)
                live_descendants = tuple(
                    item for pid, item in tracked.items() if pid != int(process.pid) and _running(item)
                )
                if live_descendants:
                    reason = "orphaned_descendants"
                    _terminate(live_descendants, record=terminated)
                else:
                    reason = "completed"
                break
            sleep(float(limits.poll_seconds))
        if reason in {"rss_limit", "time_limit"}:
            _terminate(tuple(tracked.values()), record=terminated)
    except (OSError, psutil.Error, subprocess.SubprocessError) as exc:
        reason = "launch_failure" if process is None else "supervisor_failure"
        failure = f"{type(exc).__name__}: {exc}"
    except KeyboardInterrupt as exc:
        interruption = exc
        reason = "cancelled"
        failure = "KeyboardInterrupt"
    finally:
        if process is not None:
            def cleanup_error(exc: Exception) -> None:
                nonlocal reason, failure
                if interruption is None:
                    reason = "supervisor_failure"
                detail = f"{type(exc).__name__}: {exc}"
                failure = f"{failure}; cleanup {detail}" if failure else detail

            def close_owned_process() -> None:
                nonlocal root, exit_code

                def owned_state() -> bool | None:
                    try:
                        return process.poll() is None
                    except (OSError, subprocess.SubprocessError) as exc:
                        cleanup_error(exc)
                        return None  # ownership unknown; use only the Popen handle

                # Reacquire solely for descendant discovery while the exact
                # Popen handle still owns a live root. Never kill a newly
                # acquired PID through psutil; root termination uses Popen.
                if root is None and root_pid is not None and owned_state() is True:
                    try:
                        candidate = process_factory(root_pid)
                        if int(candidate.pid) != root_pid:
                            raise ValueError("reacquired F03 process PID disagrees")
                        if owned_state() is True:
                            root = candidate
                            tracked.setdefault(root_pid, root)
                    except (OSError, psutil.Error) as exc:
                        cleanup_error(exc)
                if reason != "completed" and root is not None and owned_state() is True:
                    try:
                        discovered = tuple(root.children(recursive=True))
                        if owned_state() is True:
                            for child in discovered:
                                tracked.setdefault(int(child.pid), child)
                    except (OSError, psutil.Error) as exc:
                        cleanup_error(exc)
                if reason != "completed":
                    try:
                        _terminate(tuple(
                            item for pid, item in tracked.items() if pid != root_pid
                        ), record=terminated)
                    except (OSError, psutil.Error) as exc:
                        cleanup_error(exc)
                if owned_state() is not False:
                    try:
                        process.kill()
                        if root_pid is not None:
                            terminated.add(root_pid)
                    except (OSError, subprocess.SubprocessError) as exc:
                        cleanup_error(exc)
                try:
                    exit_code = int(process.wait(timeout=10.0))
                except (OSError, subprocess.SubprocessError) as exc:
                    cleanup_error(exc)

            # A second Ctrl-C during cleanup must not erase the first
            # cancellation or abandon an already discovered process tree.
            for attempt in range(2):
                try:
                    close_owned_process()
                    break
                except KeyboardInterrupt as exc:
                    if interruption is None:
                        interruption = exc
                        reason = "cancelled"
                        failure = "KeyboardInterrupt"
                    else:
                        failure = f"{failure}; cleanup KeyboardInterrupt"
                except (OSError, psutil.Error, subprocess.SubprocessError) as exc:
                    cleanup_error(exc)
                    break
    elapsed = max(0.0, float(monotonic() - begun))
    receipt = SupervisionReceipt(
        reason,
        exit_code,
        root_pid,
        elapsed,
        peak,
        tuple(sorted(tracked)),
        tuple(sorted(terminated)),
        failure,
    )
    if interruption is not None:
        raise SupervisionCancelled(receipt) from interruption
    return receipt
