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
        }
        if (
            self.reason not in allowed
            or (self.exit_code is not None and type(self.exit_code) is not int)
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
            or (self.failure is not None and type(self.failure) is not str)
        ):
            raise ValueError("invalid F03 process-tree supervision receipt")


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


def _terminate(processes: Sequence[object]) -> tuple[int, ...]:
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
    peak = 0
    tracked: dict[int, object] = {}
    terminated: set[int] = set()
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
                    terminated.update(_terminate(live_descendants))
                else:
                    reason = "completed"
                break
            sleep(float(limits.poll_seconds))
        if reason in {"rss_limit", "time_limit"}:
            terminated.update(_terminate(tuple(tracked.values())))
    except (OSError, psutil.Error, subprocess.SubprocessError) as exc:
        reason = "launch_failure" if process is None else "supervisor_failure"
        failure = f"{type(exc).__name__}: {exc}"
        if tracked:
            terminated.update(_terminate(tuple(tracked.values())))
    finally:
        if process is not None:
            try:
                if process.poll() is None:
                    if root is not None:
                        terminated.update(_terminate((root, *tracked.values())))
                    else:
                        process.kill()
                exit_code = int(process.wait(timeout=10.0))
            except (OSError, psutil.Error, subprocess.SubprocessError) as exc:
                reason = "supervisor_failure"
                failure = f"{type(exc).__name__}: {exc}"
    elapsed = max(0.0, float(monotonic() - begun))
    return SupervisionReceipt(
        reason,
        exit_code,
        elapsed,
        peak,
        tuple(sorted(tracked)),
        tuple(sorted(terminated)),
        failure,
    )
