"""Run the current merge-test extent without reopening frozen burn-in evidence.

The S3/Q4 burn-in runner is retained as historical evidence and intentionally
binds the exact machine on which the accepted cycles ran.  Ordinary pull
requests need a different property: the current merge-test inventory must run
on every supported host, including tests added after the burn-in closeout.

This coordinator balances whole test modules over a small number of isolated
pytest processes.  It never retries a worker, and it terminates every launched
process tree when the shared wall-clock limit expires.
"""

from __future__ import annotations

import argparse
import os
import re
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
    "tests/test_e4_pl_s3_q4_burnin_authority.py",
)
# Versioned S3 files record authority, experiments, incidents, and formal
# evidence accumulated while the successor was developed.  Most of those
# modules deliberately bind a particular checkout representation, full Git
# history, or external machine-local evidence.  They remain valuable in their
# registered environment but are not portable merge tests.  Keep the small
# current runtime-facing V2D suite explicit so a newly added study cannot
# silently enter ordinary CI merely by matching the broad additive prefix.
PORTABLE_CURRENT_S3_SUCCESSOR_MODULES = (
    "tests/test_e4_pl_s3_v2d_linear_native_parity.py",
    "tests/test_e4_pl_s3_v2d_native_state_corotational.py",
    "tests/test_e4_pl_s3_v6c_offset_load_restart.py",
    "tests/test_e4_pl_s3_v6e_final_parity.py",
    "tests/test_e4_pl_s3_v6g_recovery_current_eigen.py",
    "tests/test_e4_pl_s3_v6t_global_cache.py",
)
_VERSIONED_S3_STUDY_RE = re.compile(
    r"tests/test_e4_pl_s3_(?:qv\d+|v\d)[^/]*\.py\Z"
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
# These nodes replay frozen authority or selector state. Shallow pull-request
# checkouts may not carry the bound object, and superseded aliases must retain
# their historical meaning on the frozen source revision.
PORTABLE_HISTORY_ONLY_NODES = (
    # This module replays the immutable V1 opt-in mixed-mesh campaign. Its
    # canonical input intentionally binds the original ``e4-pl-s3`` alias to
    # QualifiedE4PLS3ShellElement, so it cannot be replayed after that public
    # alias is activated for V2D. Keep it available as a focused historical
    # test on its frozen source revision, but do not mix it into current CI.
    "tests/test_e4_pl_s3_mixed_mesh_qualification_runner.py",
    (
        "tests/test_e4_pl_s3_v2d_linear_native_parity.py::"
        "test_v2d_stateless_identity_roundtrip_and_remaining_successor_gaps"
    ),
    (
        "tests/test_e4_pl_s3_v6e_final_parity.py::"
        "test_v6e_contract_and_production_boundary_are_exact"
    ),
    (
        "tests/test_e4_pl_s3_v6g_recovery_current_eigen.py::"
        "test_v6g_contract_is_canonical_and_defaults_remain_frozen"
    ),
    (
        "tests/test_e4_pl_s3_v6g_recovery_current_eigen.py::"
        "test_v6g_closes_the_frozen_v6f_readiness_inventory"
    ),
)
# This invokes an external two-cycle N20/N40 diagnostic with its own 240-second
# subprocess bound.  It is explicitly nonclassifying and already preserved by
# the qualification record; ordinary CI retains every deterministic manifest,
# geometry, and guard test in the module without rerunning that diagnostic.
PORTABLE_NONQUALIFYING_NODES = (
    (
        "tests/test_e4_pl_s3_mixed_mesh_qualification_runner.py::"
        "test_real_n20_n40_smoke_is_byte_identical_and_never_claims_a_gate"
    ),
)
# File size is a useful default partition proxy, but these integration modules
# are computationally dense relative to their source size.  Frozen observed
# costs keep the four existing workers balanced on slower hosted runners; they
# do not change any test, timeout, or scientific result.
PORTABLE_MODULE_WEIGHT_OVERRIDES = {
    "tests/test_beam_shell_verification.py": 250_000,
    "tests/test_corotational.py": 100_000,
    "tests/test_e4_pl_q4_state_lifecycle.py": 160_000,
    "tests/test_e4_pl_s3_generalized_nonlinear.py": 100_000,
    "tests/test_e4_pl_s3_mixed_mesh_qualification_runner.py": 80_000,
    "tests/test_e4_pl_s3_restart_history.py": 220_000,
    "tests/test_e4_pl_s3_state_lifecycle.py": 220_000,
    "tests/test_fe_solver_nonlinear_static.py": 150_000,
    "tests/test_hht_alpha.py": 100_000,
    "tests/test_mixed_shell_quadrature_grouping.py": 120_000,
}
# Runtime panel tests repeatedly construct and solve independent application
# models.  Keep them in a fresh interpreter so report/restart tests cannot
# leak process-local solver bootstrap state into these production routes.
PORTABLE_ISOLATED_MODULES = (
    "tests/test_geometry_panel.py",
)
DEFAULT_WORKERS = 4
DEFAULT_TIMEOUT_SECONDS = 1_200
TIMEOUT_EXIT_CODE = 124


def _module_weight(module: str) -> int:
    """Return a stable, inexpensive proxy for collection/execution work."""

    path = ROOT / module
    if not path.is_file():
        raise RuntimeError(f"merge-test module is missing: {module}")
    # Git stores text with LF endings, while Windows worktrees may expose CRLF.
    # Normalize the proxy so the same commit receives the same shard assignment
    # on every supported host.
    normalized_size = len(path.read_bytes().replace(b"\r\n", b"\n"))
    return PORTABLE_MODULE_WEIGHT_OVERRIDES.get(
        module, max(1, normalized_size)
    )


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


def execution_partitions(
    modules: Sequence[str], workers: int
) -> tuple[tuple[str, ...], ...]:
    """Partition ordinary modules and isolate process-state-sensitive modules."""

    if isinstance(workers, bool) or workers < 1:
        raise ValueError("workers must be a positive integer")
    ordered = tuple(modules)
    if not ordered or len(ordered) != len(set(ordered)):
        raise ValueError("modules must be nonempty and unique")
    if any(not isinstance(module, str) or not module for module in ordered):
        raise ValueError("module selectors must be nonempty strings")
    isolated_set = set(PORTABLE_ISOLATED_MODULES)
    isolated = tuple(sorted(module for module in ordered if module in isolated_set))
    shared = tuple(module for module in ordered if module not in isolated_set)
    ordinary = partition_modules(shared, workers) if shared else ()
    return (*ordinary, *((module,) for module in isolated))


def matrix_modules(
    modules: Sequence[str],
    shard_index: int | None,
    shard_count: int | None,
) -> tuple[str, ...]:
    """Select one matrix shard while repeating the current S3 critical suite."""

    if shard_index is None and shard_count is None:
        return tuple(modules)
    if shard_index is None or shard_count is None:
        raise ValueError("matrix shard index and count must be provided together")
    if (
        isinstance(shard_index, bool)
        or isinstance(shard_count, bool)
        or shard_count < 1
        or shard_index < 0
        or shard_index >= shard_count
    ):
        raise ValueError("matrix shard index/count are invalid")
    ordered = tuple(modules)
    if len(ordered) != len(set(ordered)):
        raise ValueError("matrix input modules must be unique")
    critical = tuple(
        module
        for module in ordered
        if module in PORTABLE_CURRENT_S3_SUCCESSOR_MODULES
    )
    if set(critical) != set(PORTABLE_CURRENT_S3_SUCCESSOR_MODULES):
        raise RuntimeError("matrix input omits current S3 successor coverage")
    general = tuple(module for module in ordered if module not in set(critical))
    if shard_count > len(general):
        raise ValueError("matrix shard count exceeds general module count")
    shards = partition_modules(general, shard_count)
    return tuple(sorted((*shards[shard_index], *critical)))


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
    missing_current = set(PORTABLE_CURRENT_S3_SUCCESSOR_MODULES) - set(registered)
    if missing_current:
        raise RuntimeError(
            f"current S3 successor modules are absent: {sorted(missing_current)}"
        )
    modules = [
        module
        for module in registered
        if not _is_portable_historical_module(module)
    ]
    return tuple(modules)


def _is_portable_historical_module(module: str) -> bool:
    """Return whether *module* needs frozen history or external evidence."""

    if module in POST_CLOSEOUT_HISTORICAL_MODULES:
        return True
    if module in PORTABLE_CURRENT_S3_SUCCESSOR_MODULES:
        return False
    return _VERSIONED_S3_STUDY_RE.fullmatch(module) is not None


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
        for node in (
            *DEDICATED_LANE_NODES,
            *PORTABLE_HISTORY_ONLY_NODES,
            *PORTABLE_NONQUALIFYING_NODES,
        )
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


def run(
    *,
    workers: int,
    timeout_seconds: int,
    matrix_shard_index: int | None = None,
    matrix_shard_count: int | None = None,
) -> int:
    if isinstance(timeout_seconds, bool) or timeout_seconds < 1:
        raise ValueError("timeout_seconds must be a positive integer")
    modules = matrix_modules(
        merge_test_modules(), matrix_shard_index, matrix_shard_count
    )
    if matrix_shard_index is not None:
        print(
            "[portable-ci] matrix shard "
            f"{matrix_shard_index + 1}/{matrix_shard_count} "
            f"selected {len(modules)} modules",
            flush=True,
        )
    partitions = execution_partitions(modules, workers)
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

        deadline = started + timeout_seconds
        while any(worker.poll() is None for worker in launched):
            if time.monotonic() >= deadline:
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
    parser.add_argument(
        "--timeout-seconds", type=int, default=DEFAULT_TIMEOUT_SECONDS
    )
    parser.add_argument("--matrix-shard-index", type=int)
    parser.add_argument("--matrix-shard-count", type=int)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    return run(
        workers=args.workers,
        timeout_seconds=args.timeout_seconds,
        matrix_shard_index=args.matrix_shard_index,
        matrix_shard_count=args.matrix_shard_count,
    )


if __name__ == "__main__":
    raise SystemExit(main())
