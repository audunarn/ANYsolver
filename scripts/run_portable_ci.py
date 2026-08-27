"""Run the current merge-test extent without reopening frozen burn-in evidence.

The S3/Q4 burn-in runner is retained as historical evidence and intentionally
binds the exact machine on which the accepted cycles ran.  Ordinary pull
requests need a different property: the current merge-test inventory must run
on every supported host, including tests added after the burn-in closeout.

This coordinator balances whole test modules over a small number of isolated
pytest processes.  It never retries a worker.  Ordinary CI has no elapsed-time
classification; a positive wall-clock limit remains available as an explicit
manual diagnostic option.
"""

from __future__ import annotations

import argparse
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from collections.abc import Mapping, Sequence
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_e4_pl_burnin_gate import inventory  # noqa: E402


MERGE_LANES = ("quick", "additive", "functional")
POST_CLOSEOUT_HISTORICAL_MODULES = (
    "tests/test_e4_pl_s3_mixed_mesh_qualification_runner.py",
    "tests/test_e4_pl_s3_q4_burnin_authority.py",
)
DEDICATED_LANE_NODES = (
    (
        "tests/test_fe_solver_infrastructure.py::"
        "test_pypardiso_backend_symmetric_mtypes_pattern_reuse_and_stale_handles"
    ),
    (
        "tests/test_local_patch_transition.py::"
        "test_local_patch_buckling_has_no_spurious_flat_facet_modes"
    ),
    (
        "tests/test_local_patch_transition.py::"
        "test_stiffened_cylinder_keeps_mesh_style_invariance_with_beams"
    ),
)
DEFAULT_WORKERS = 4
TIMEOUT_EXIT_CODE = 124


def _module_weight(module: str) -> int:
    """Return a stable, inexpensive proxy for collection/execution work."""

    path = ROOT / module
    if not path.is_file():
        raise RuntimeError(f"merge-test module is missing: {module}")
    return max(1, path.stat().st_size)


def partition_modules(
    modules: Sequence[str], workers: int
) -> tuple[tuple[str, ...], ...]:
    """Greedily balance complete modules with deterministic tie-breaking."""

    if isinstance(workers, bool) or workers < 1:
        raise ValueError("workers must be a positive integer")
    ordered = list(modules)
    if not ordered or len(ordered) != len(set(ordered)):
        raise ValueError("modules must be nonempty and unique")
    for module in ordered:
        if not isinstance(module, str) or not module:
            raise ValueError("module selectors must be nonempty strings")

    bucket_count = min(workers, len(ordered))
    buckets: list[list[str]] = [[] for _ in range(bucket_count)]
    weights = [0] * bucket_count
    weighted = sorted(
        ((_module_weight(module), module) for module in ordered),
        key=lambda item: (-item[0], item[1]),
    )
    for weight, module in weighted:
        index = min(range(bucket_count), key=lambda item: (weights[item], item))
        buckets[index].append(module)
        weights[index] += weight

    result = tuple(tuple(sorted(bucket)) for bucket in buckets)
    assigned = [module for bucket in result for module in bucket]
    if len(assigned) != len(set(assigned)) or set(assigned) != set(ordered):
        raise RuntimeError("portable CI partition is not disjoint and complete")
    return result


def merge_test_modules() -> tuple[str, ...]:
    """Return the current non-performance, non-historical merge-test extent."""

    lanes = inventory()
    registered = [module for lane in MERGE_LANES for module in lanes[lane]]
    if len(registered) != len(set(registered)):
        raise RuntimeError("merge-test lane inventories overlap")
    missing_historical = set(POST_CLOSEOUT_HISTORICAL_MODULES) - set(registered)
    if missing_historical:
        raise RuntimeError(
            f"post-closeout historical modules are absent: {sorted(missing_historical)}"
        )
    modules = [
        module
        for module in registered
        if module not in POST_CLOSEOUT_HISTORICAL_MODULES
    ]
    return tuple(modules)


def _worker_environment(root: Path) -> dict[str, str]:
    environment = dict(os.environ)
    for name in tuple(environment):
        if name.startswith("ANYSOLVER_CI_") or name.startswith(
            "ANYSOLVER_FUNCTIONAL_"
        ):
            environment.pop(name, None)
    environment.pop("ANYSOLVER_BURNIN_ACTIVE_TEST_LANE", None)
    environment.update(
        {
            "ANY3DVIEW_DISABLE_GPU": "1",
            "NUMBA_CACHE_DIR": str(root / "numba-cache"),
            "NUMBA_NUM_THREADS": "1",
            "OMP_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
            "NUMEXPR_NUM_THREADS": "1",
            "PYTHONHASHSEED": "0",
            "PYTHONNOUSERSITE": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONPYCACHEPREFIX": str(root / "python-cache"),
            "PYTEST_ADDOPTS": "-p no:cacheprovider",
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
        }
    )
    return environment


def _worker_command(modules: Sequence[str], root: Path) -> list[str]:
    owned_modules = set(modules)
    deselections = [
        node
        for node in DEDICATED_LANE_NODES
        if node.partition("::")[0] in owned_modules
    ]
    return [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "-p",
        "no:cacheprovider",
        "--durations=20",
        "--durations-min=0.0",
        f"--basetemp={root / 'basetemp'}",
        *(f"--deselect={node}" for node in deselections),
        *modules,
    ]


def _terminate_tree(worker: subprocess.Popen[bytes], grace_seconds: float = 10.0) -> None:
    if worker.poll() is not None:
        return
    if os.name == "nt":
        taskkill = shutil.which("taskkill.exe") or shutil.which("taskkill")
        if taskkill is not None:
            subprocess.run(
                [taskkill, "/PID", str(worker.pid), "/T", "/F"],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            worker.kill()
    else:
        try:
            os.killpg(worker.pid, signal.SIGTERM)
        except ProcessLookupError:
            return
        try:
            worker.wait(timeout=grace_seconds)
            return
        except subprocess.TimeoutExpired:
            try:
                os.killpg(worker.pid, signal.SIGKILL)
            except ProcessLookupError:
                return
    try:
        worker.wait(timeout=grace_seconds)
    except subprocess.TimeoutExpired:
        worker.kill()
        worker.wait()


def run(*, workers: int, timeout_seconds: int | None = None) -> int:
    if timeout_seconds is not None and (
        isinstance(timeout_seconds, bool) or timeout_seconds < 1
    ):
        raise ValueError("timeout_seconds must be None or a positive integer")
    modules = merge_test_modules()
    partitions = partition_modules(modules, workers)
    temp_parent = Path(os.environ.get("RUNNER_TEMP", tempfile.gettempdir())).resolve()
    temp_parent.mkdir(parents=True, exist_ok=True)
    run_root = Path(tempfile.mkdtemp(prefix="anysolver-portable-ci-", dir=temp_parent))
    launched: list[subprocess.Popen[bytes]] = []
    started = time.monotonic()
    options: dict[str, object]
    if os.name == "nt":
        options = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
    else:
        options = {"start_new_session": True}

    try:
        for index, modules_for_worker in enumerate(partitions, start=1):
            worker_root = run_root / f"P{index:02d}"
            worker_root.mkdir()
            command = _worker_command(modules_for_worker, worker_root)
            print(
                f"[portable-ci] starting P{index:02d}/{len(partitions):02d} "
                f"with {len(modules_for_worker)} modules",
                flush=True,
            )
            launched.append(
                subprocess.Popen(
                    command,
                    cwd=ROOT,
                    env=_worker_environment(worker_root),
                    **options,
                )
            )

        deadline = None if timeout_seconds is None else started + timeout_seconds
        while any(worker.poll() is None for worker in launched):
            if deadline is not None and time.monotonic() >= deadline:
                print(
                    f"[portable-ci] shared {timeout_seconds}-second limit reached",
                    file=sys.stderr,
                    flush=True,
                )
                for worker in launched:
                    _terminate_tree(worker)
                return TIMEOUT_EXIT_CODE
            time.sleep(0.1)
    except BaseException:
        for worker in launched:
            _terminate_tree(worker)
        raise

    returncodes = [int(worker.returncode) for worker in launched]
    for index, returncode in enumerate(returncodes, start=1):
        print(f"[portable-ci] P{index:02d} exit={returncode}", flush=True)
    return 0 if all(returncode == 0 for returncode in returncodes) else 1


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
    parser.add_argument("--timeout-seconds", type=int, default=None)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    return run(workers=args.workers, timeout_seconds=args.timeout_seconds)


if __name__ == "__main__":
    raise SystemExit(main())
