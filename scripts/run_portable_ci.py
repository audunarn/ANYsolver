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
import hashlib
import importlib.metadata
import json
import os
import platform
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

def inventory():
    """Keep the historical inventory API without importing it in focused runs."""
    from scripts.run_e4_pl_burnin_gate import inventory as historical_inventory
    return historical_inventory()


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
    # Original P3 metadata/commit authority remains frozen at 0.4.2. Runtime
    # routing/state tests in this module still run; release metadata is tested
    # independently by test_release_043.py.
    "tests/test_ge_beam3_mixed_p3_optin.py::test_frozen_mechanics_defaults_and_package_metadata_are_unchanged",
    # The 0.4.3 publication manifest binds the exact released runtime tree.
    # Later additive runtime modules cannot be reconstructed from the current
    # checkout, so replay this bridge only with the preserved 0.4.3 artifact.
    "tests/test_release_043.py::test_publication_manifest_checks_all_accepted_runtime_files",
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
    # Python 3.11 can materialize Protocol.__annotations__ during runtime
    # structural checks. Keep those standard-library cache mutations away from
    # exact qualified-authority tests in the shared interpreter.
    "tests/test_generalized_section_api_workflows.py",
    "tests/test_generalized_shell_sections.py",
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

    _ge_beam3_inventory()
    intents = _current_development_inventory()
    lanes = inventory()
    registered = [module for lane in MERGE_LANES for module in lanes[lane]]
    if not set(intents["portable"]) <= set(registered):
        raise RuntimeError("portable development test intent is incompatible with existing lanes")
    nonportable = set(intents["performance"] + intents["extended"])
    registered = [module for module in registered if module not in nonportable]
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

    if module.startswith("tests/test_ge_beam3_"):
        return module in _ge_beam3_inventory()["extended"]
    if module in POST_CLOSEOUT_HISTORICAL_MODULES:
        return True
    if module in PORTABLE_CURRENT_S3_SUCCESSOR_MODULES:
        return False
    return _VERSIONED_S3_STUDY_RE.fullmatch(module) is not None


def _ge_beam3_inventory() -> dict[str, list[str]]:
    """Classify every GE test explicitly; never silently skip new modules."""
    record = json.loads((ROOT / "scripts/ge_beam3_release_test_inventory.json").read_text())
    if record["schema"] != "anysolver.release-ge-test-inventory.v1":
        raise RuntimeError("invalid GE test inventory schema")
    portable, extended = record["portable"], record["extended"]
    registered = portable + extended
    actual = {path.relative_to(ROOT).as_posix()
              for path in (ROOT / "tests").glob("test_ge_beam3_*.py")}
    if len(registered) != len(set(registered)) or set(registered) != actual:
        raise RuntimeError("GE test inventory is incomplete or overlapping")
    return record


def _current_development_inventory() -> dict[str, object]:
    """Current test intent only; frozen lane inventories remain authoritative."""
    record = json.loads((ROOT / "scripts/development_test_inventory.json").read_text(encoding="utf-8"))
    if set(record) != {"schema", "portable", "performance", "extended"} or record["schema"] != "anysolver.development-test-intent.v1":
        raise RuntimeError("invalid current development test inventory schema")
    registered = []
    for category in ("portable", "performance", "extended"):
        entries = record[category]
        if not isinstance(entries, list) or any(not isinstance(name, str) for name in entries):
            raise RuntimeError("invalid current development test intent entries")
        registered.extend(entries)
    actual = {path.relative_to(ROOT).as_posix() for pattern in (
        "test_stiffened_shell_*.py", "test_general_contact_*.py", "test_performance_contact_chain_*.py"
    ) for path in (ROOT / "tests").glob(pattern)}
    if len(registered) != len(set(registered)) or set(registered) != actual:
        raise RuntimeError("current development test inventory is incomplete or overlapping")
    return record


def _worker_environment(root: Path) -> dict[str, str]:
    environment = dict(os.environ)
    for name in tuple(environment):
        if name.startswith("ANYSOLVER_CI_") or name.startswith(
            "ANYSOLVER_FUNCTIONAL_"
        ) or name.startswith("ANYSOLVER_DEVELOPMENT_"):
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


def _development_targets(targets: Sequence[str]) -> tuple[str, ...]:
    if not targets:
        raise ValueError("explicit nonempty development selection required")
    normalized = []
    for target in targets:
        if not isinstance(target, str) or not target or target.startswith("-"):
            raise ValueError("test file or node ID required")
        filename, separator, node = target.partition("::")
        if "us3-modal-canary" in {part.casefold() for part in Path(filename).parts}:
            raise ValueError("protected source subtree is not a development target")
        path = (ROOT / filename).resolve(strict=True)
        if not path.is_relative_to(ROOT / "tests") or path.suffix != ".py" or not path.is_file():
            raise ValueError("development targets must be test files inside this repository")
        if separator and not node:
            raise ValueError("empty node ID")
        normalized.append(path.relative_to(ROOT).as_posix()+(separator+node if separator else ""))
    if len(set(normalized)) != len(normalized):
        raise ValueError("duplicate development selectors")
    return tuple(normalized)


def _profile_targets(name: str) -> tuple[str, ...]:
    profiles = json.loads((ROOT / "scripts/development_test_profiles.json").read_text(encoding="utf-8"))
    if not isinstance(profiles, dict):
        raise ValueError("development profiles must be an object of explicit string arrays")
    if name not in profiles or not isinstance(profiles[name], list):
        raise ValueError(f"unknown development profile: {name}")
    return _development_targets(profiles[name])


def _development_cache(environment: dict[str, str], parent: Path, deadline: float | None = None) -> dict[str, object]:
    """Opt-in compilation cache; hash watched source even with restored times.

    Normal cold runs do no cache hashing. External editable dependencies are
    unbound: the runtime guard rejects their use in any cache-enabled run.
    """
    identity = str(ROOT.resolve())
    base = parent / "anysolver-development-cache" / hashlib.sha256(identity.encode()).hexdigest()[:20]
    base.mkdir(parents=True, exist_ok=True)
    current = {}
    for directory in ("src", "scripts", "tests"):
        source_directory = ROOT / directory
        if source_directory.is_symlink():
            raise RuntimeError("source directory symlinks require cold development")
        for folder, directories, filenames in os.walk(source_directory, topdown=True, followlinks=False):
            # Prune before descent: even enumerating protected code is outside
            # this runner's development authority.
            directories[:] = sorted(name for name in directories if name.casefold() not in
                                    {"__pycache__", "us3-modal-canary"})
            if any((Path(folder) / name).is_symlink() for name in directories):
                raise RuntimeError("source directory symlinks require cold development")
            for filename in sorted(filenames):
                if deadline is not None and time.monotonic() >= deadline:
                    raise TimeoutError("shared deadline reached during cache preparation")
                if not filename.endswith(".py"):
                    continue
                path = Path(folder) / filename
                relative = path.relative_to(ROOT).as_posix()
                if relative.casefold() == "scripts/b3_e4_f03_c1_fy_supported_reference.py":
                    continue
                if path.is_symlink():
                    raise RuntimeError("source symlinks require cold development")
                stat = path.stat()
                fingerprint = [stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns, stat.st_ino]
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                after = path.stat()
                if fingerprint != [after.st_size, after.st_mtime_ns, after.st_ctime_ns, after.st_ino]:
                    raise RuntimeError(f"source changed while preparing compilation cache: {relative}")
                current[relative] = {"stat": fingerprint, "sha256": digest}
    dependencies = []
    dependency_bytes = 0
    unbound_dependencies = []
    native_eligible = {"numpy", "scipy", "numba", "llvmlite", "threadpoolctl", "anymaterial",
                       "anygeometry", "anymesher", "anyfileio", "pypardiso", "mkl", "mkl-service",
                       "intel-openmp", "intel-cmplr-lib-rt", "intel-cmplr-lib-ur", "tbb", "umf"}
    for distribution in importlib.metadata.distributions():
        name = distribution.metadata["Name"]
        normalized_name = name.lower().replace("_", "-")
        own_source = normalized_name == "anysolver"
        unbound = False
        recorded_files = distribution.files if not own_source else None
        explicit_top_levels = distribution.read_text("top_level.txt")
        if explicit_top_levels:
            top_levels = explicit_top_levels.split()
        else:
            top_levels = sorted({entry.parts[0] if len(entry.parts) > 1 else entry.name.partition(".")[0]
                                 for entry in (recorded_files or []) if entry.parts and
                                 (entry.parts[0] if len(entry.parts) > 1 else entry.name.partition(".")[0]).isidentifier()})
            if not top_levels:
                top_levels = [name.lower().replace("-", "_")]
        location = Path(distribution.locate_file("")).resolve()
        module_roots = {str(location / top.replace(".", "/")) for top in top_levels}
        module_roots.update(str(location / (top+".py")) for top in top_levels)
        module_roots.update(str(distribution.locate_file(entry)) for entry in (recorded_files or [])
                            if len(entry.parts) == 1 and entry.name.partition(".")[0] in top_levels)
        unbound_record = {"name": name, "root": str(location), "top_levels": top_levels,
                          "module_roots": sorted(module_roots)}
        direct = distribution.read_text("direct_url.json")
        if direct and json.loads(direct).get("dir_info", {}).get("editable"):
            # The selected checkout itself is fully watched above; other
            # editable installs have unbound code and cannot share this cache.
            from urllib.parse import unquote, urlparse
            editable = Path(unquote(urlparse(json.loads(direct)["url"]).path).lstrip("/")
                            if os.name == "nt" else unquote(urlparse(json.loads(direct)["url"]).path)).resolve()
            if not own_source and editable != ROOT.resolve():
                unbound_record.update(root=str(editable), module_roots=[str(editable)], reason="editable source")
                unbound = True
        content = {}
        if not own_source and not unbound:
            if not recorded_files or not distribution.read_text("RECORD"):
                unbound_record["reason"] = "missing installed file inventory"
                unbound = True
            elif normalized_name not in native_eligible and any(
                re.search(r"\.(?:pyd|dll|dylib|so(?:\.\d+)*)$", str(entry), re.IGNORECASE)
                for entry in recorded_files
            ):
                unbound_record["reason"] = "native package outside solver/compiler eligibility"
                unbound = True
        if unbound:
            unbound_dependencies.append(unbound_record)
        if not own_source and not unbound:
            for entry in sorted(recorded_files, key=str):
                if "us3-modal-canary" in {part.casefold() for part in Path(entry).parts} or Path(entry).name.casefold() == "b3_e4_f03_c1_fy_supported_reference.py":
                    raise RuntimeError(f"protected dependency source cannot be inspected: {name}")
                if Path(entry).suffix == ".pyc":
                    continue
                installed = Path(distribution.locate_file(entry))
                if installed.is_symlink():
                    raise RuntimeError(f"dependency symlinks require cold development: {name}")
                # Bind current bytes, rather than trusting version or RECORD
                # hashes after an in-place local package repair.
                before = installed.stat()
                digest = hashlib.sha256()
                with installed.open("rb") as stream:
                    while chunk := stream.read(1024 * 1024):
                        if deadline is not None and time.monotonic() >= deadline:
                            raise TimeoutError("shared deadline reached during cache preparation")
                        digest.update(chunk)
                        dependency_bytes += len(chunk)
                after = installed.stat()
                if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (after.st_size, after.st_mtime_ns, after.st_ctime_ns):
                    raise RuntimeError(f"dependency changed while preparing compilation cache: {name}")
                content[str(entry)] = digest.hexdigest()
        dependencies.append({"name": name, "version": distribution.version,
                              "location": str(location),
                              "installed_record_sha256": hashlib.sha256(
                                  (distribution.read_text("RECORD") or "").encode()).hexdigest(),
                              "current_content": content,
                              "unbound": unbound})
    dependencies.sort(key=lambda entry: json.dumps(entry, sort_keys=True))
    unbound_dependencies.sort(key=lambda entry: json.dumps(entry, sort_keys=True))
    binding = {"schema": 1, "checkout": identity, "python": sys.version,
               "executable": str(Path(sys.executable).resolve()), "optimization": sys.flags.optimize,
               "dependencies": dependencies, "platform": platform.platform(),
               "machine": platform.machine(), "processor": platform.processor(), "host": platform.node(),
               "runtime": {name: value for name, value in sorted(environment.items())
                           if name.startswith(("NUMBA_", "ANYSOLVER_")) and name not in
                           ("NUMBA_CACHE_DIR", "ANYSOLVER_DEVELOPMENT_RECORD", "ANYSOLVER_DEVELOPMENT_SOURCE",
                            "ANYSOLVER_EXPECT_DEVELOPMENT_CACHE_HIT")
                           or name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
                                       "NUMEXPR_NUM_THREADS", "PYTHONHASHSEED", "PYTHONOPTIMIZE")},
               "sources": {name: entry["sha256"] for name, entry in current.items()},
               "native_eligible_dependencies": sorted(native_eligible),
               "unbound_dependencies": unbound_dependencies}
    key = hashlib.sha256(json.dumps(binding, sort_keys=True).encode()).hexdigest()
    directory = base / key
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "binding.json").write_text(json.dumps(binding, indent=2)+"\n", encoding="utf-8")
    # Keep bytecode cold in the isolated per-invocation prefix. Repository
    # helpers outside watched source cannot safely share a bytecode cache.
    environment.update(NUMBA_CACHE_DIR=str(directory / "numba"), PYTHONDONTWRITEBYTECODE="1")
    return {"enabled": True, "key": key, "path": str(directory),
            "watched_root": identity,
            "dependency_bytes_hashed": dependency_bytes,
            "unbound_dependencies": unbound_dependencies,
            "scope": "Numba compilation only; watched source and eligible installed dependency content hashes; unbound imports forbidden; bytecode reuse disabled"}


def run(
    *,
    workers: int,
    timeout_seconds: int,
    matrix_shard_index: int | None = None,
    matrix_shard_count: int | None = None,
    development_targets: Sequence[str] | None = None,
    jit: str | None = None,
    memory_limit_mib: int | None = None,
    development_cache: bool = False,
    development_profile: str | None = None,
) -> int:
    if isinstance(timeout_seconds, bool) or timeout_seconds < 1:
        raise ValueError("timeout_seconds must be a positive integer")
    if isinstance(workers, bool) or workers < 1:
        raise ValueError("workers must be a positive integer")
    if development_profile is not None:
        if development_targets is not None:
            raise ValueError("choose explicit development targets or a profile")
        development_targets = _profile_targets(development_profile)
    development = development_targets is not None
    if development:
        if matrix_shard_index is not None or matrix_shard_count is not None:
            raise ValueError("focused development cannot select a CI matrix shard")
        modules = _development_targets(development_targets)
        if memory_limit_mib is not None and (isinstance(memory_limit_mib, bool) or memory_limit_mib < 1):
            raise ValueError("memory_limit_mib must be positive")
    else:
        if jit is not None or memory_limit_mib is not None or development_cache:
            raise ValueError("JIT/memory options belong to explicit focused development")
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
    partitions = (tuple(modules),) if development else execution_partitions(modules, workers)
    temp_parent = Path(os.environ.get("RUNNER_TEMP", tempfile.gettempdir())).resolve()
    temp_parent.mkdir(parents=True, exist_ok=True)
    run_root = Path(tempfile.mkdtemp(prefix="anysolver-portable-ci-", dir=temp_parent))
    launched: list[subprocess.Popen[bytes]] = []
    monitor = None
    peak_bytes = 0
    if memory_limit_mib is not None:
        import psutil
        monitor = psutil
    started = time.monotonic()
    options: dict[str, object]
    if os.name == "nt":
        options = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
    else:
        options = {"start_new_session": True}

    try:
        deadline = started + timeout_seconds
        next_partition = 0
        ceiling = 1 if development else workers
        while next_partition < len(partitions) or any(worker.poll() is None for worker in launched):
            while next_partition < len(partitions) and sum(w.poll() is None for w in launched) < ceiling:
                if time.monotonic() >= deadline:
                    break
                index = next_partition + 1
                modules_for_worker = partitions[next_partition]
                next_partition += 1
                worker_root = run_root / f"P{index:02d}"
                worker_preparation_started = time.monotonic()
                worker_root.mkdir()
                environment = _worker_environment(worker_root)
                command = _worker_command(modules_for_worker, worker_root)
                if development:
                    # Explicit targets are never silently filtered by CI/history rules.
                    command = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                               "-p", "scripts.development_test_runtime", "--durations=10",
                               f"--basetemp={worker_root / 'basetemp'}", *modules_for_worker]
                    environment.update(NUMBA_DISABLE_JIT="0" if jit == "on" else "1",
                        ANYSOLVER_DEVELOPMENT_RECORD=str(worker_root / "runtime.json"),
                        ANYSOLVER_DEVELOPMENT_SOURCE=str(ROOT / "src" / "anysolver"))
                    cache = {"enabled": False, "reason": "cold default"}
                    if development_cache:
                        cache_started = time.monotonic()
                        try:
                            cache = _development_cache(environment, temp_parent, deadline)
                        except (OSError, ValueError, RuntimeError) as exc:
                            cache = {"enabled": False, "reason": str(exc)}
                        cache["preparation_seconds"] = time.monotonic() - cache_started
                        summary = {name: cache[name] for name in ("enabled", "key", "preparation_seconds", "reason") if name in cache}
                        summary["unbound_dependency_count"] = len(cache.get("unbound_dependencies", []))
                        print(f"[development] compilation cache={json.dumps(summary, sort_keys=True)}", flush=True)
                    environment["ANYSOLVER_DEVELOPMENT_CACHE"] = json.dumps(cache, sort_keys=True)
                    (worker_root / "selection.json").write_text(json.dumps({
                        "scope": "focused source development, not qualification",
                        "targets": list(modules_for_worker), "command": command,
                        "source_root": str(ROOT), "timeout_seconds": timeout_seconds,
                        "selected_file_sha256": {target.partition("::")[0]: hashlib.sha256(
                            (ROOT / target.partition("::")[0]).read_bytes()).hexdigest()
                            for target in modules_for_worker},
                        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                        "source_identity_scope": "working-tree paths and selected files; not an installed artifact binding",
                        "memory_limit_mib": memory_limit_mib,
                        "profile": development_profile, "compilation_cache": cache,
                        "worker_preparation_seconds": time.monotonic() - worker_preparation_started,
                        "jit": jit or "off"}, indent=2)+"\n", encoding="utf-8")
                    print(f"[development] exact targets={len(modules_for_worker)}; record={worker_root}", flush=True)
                if time.monotonic() >= deadline:
                    next_partition -= 1
                    break
                print(
                    f"[portable-ci] starting P{index:02d}/{len(partitions):02d} "
                    f"with {len(modules_for_worker)} modules",
                    flush=True,
                )
                launched.append(
                    subprocess.Popen(
                        command,
                        cwd=ROOT,
                        env=environment,
                        **options,
                    )
                )

            if monitor is not None and launched:
                try:
                    parent = monitor.Process(launched[0].pid)
                    peak_bytes = max(peak_bytes, sum(p.memory_info().rss for p in
                        [parent, *parent.children(recursive=True)] if p.is_running()))
                except monitor.NoSuchProcess:
                    pass
                except monitor.AccessDenied as exc:
                    raise RuntimeError("cannot monitor the requested process-tree memory limit") from exc
                if peak_bytes > memory_limit_mib * 1024**2:
                    print("[development] process-tree memory limit reached", file=sys.stderr, flush=True)
                    for worker in launched:
                        _terminate_tree(worker)
                    (worker_root / "resource.json").write_text(json.dumps({
                        "peak_sampled_bytes": peak_bytes, "limit_mib": memory_limit_mib,
                        "status": "memory_limit"})+"\n", encoding="utf-8")
                    return TIMEOUT_EXIT_CODE
            if time.monotonic() >= deadline:
                print(
                    f"[portable-ci] shared {timeout_seconds}-second limit reached",
                    file=sys.stderr,
                    flush=True,
                )
                for worker in launched:
                    _terminate_tree(worker)
                if development:
                    worker_root = run_root / "P01"
                    worker_root.mkdir(exist_ok=True)
                    (worker_root / "resource.json").write_text(json.dumps({
                        "peak_sampled_bytes": peak_bytes if monitor is not None else None,
                        "limit_mib": memory_limit_mib, "elapsed_seconds": time.monotonic()-started,
                        "status": "timeout", "child_exit_codes": [w.returncode for w in launched]})+"\n",
                        encoding="utf-8")
                return TIMEOUT_EXIT_CODE
            time.sleep(0.1)
    except BaseException:
        for worker in launched:
            _terminate_tree(worker)
        raise

    returncodes = [int(worker.returncode) for worker in launched]
    if development:
        (worker_root / "resource.json").write_text(json.dumps({
            "peak_sampled_bytes": peak_bytes if monitor is not None else None,
            "limit_mib": memory_limit_mib, "elapsed_seconds": time.monotonic()-started,
            "status": "terminal", "child_exit_codes": returncodes})+"\n", encoding="utf-8")
        if returncodes == [0] and not (worker_root / "runtime.json").is_file():
            print("[development] missing runtime/coverage record", file=sys.stderr)
            return 1
    for index, returncode in enumerate(returncodes, start=1):
        print(f"[portable-ci] P{index:02d} exit={returncode}", flush=True)
    return 0 if all(returncode == 0 for returncode in returncodes) else 1


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
    parser.add_argument(
        "--timeout-seconds", type=int,
    )
    parser.add_argument("--matrix-shard-index", type=int)
    parser.add_argument("--matrix-shard-count", type=int)
    parser.add_argument("--development", nargs="+", metavar="TEST",
                        help="Run exactly these test files/node IDs in one source process; no qualification")
    parser.add_argument("--jit", choices=("off", "on"),
                        help="Focused development JIT mode (default off); use on for affected compiled paths")
    parser.add_argument("--memory-limit-mib", type=int,
                        help="Focused child process-tree RSS ceiling; requires psutil when selected")
    parser.add_argument("--development-profile", help="Explicit named source-development selection")
    parser.add_argument("--development-cache", action="store_true",
                        help="Opt-in Numba compilation reuse; bytecode stays cold; imported unbound dependencies reject the run")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    return run(
        workers=args.workers,
        timeout_seconds=args.timeout_seconds if args.timeout_seconds is not None else (
            600 if args.development is not None or args.development_profile is not None else DEFAULT_TIMEOUT_SECONDS),
        matrix_shard_index=args.matrix_shard_index,
        matrix_shard_count=args.matrix_shard_count,
        development_targets=args.development,
        jit=args.jit,
        memory_limit_mib=args.memory_limit_mib,
        development_profile=args.development_profile,
        development_cache=args.development_cache,
    )


if __name__ == "__main__":
    raise SystemExit(main())
