"""Bounded mixed-Q4/S3 eigenvalue and performance qualification lane.

The committed input selects three registered N=20 topologies: the matched
all-Q4 reference and dispersed 10%/25% S3 meshes.  Every worker constructs
real production elements through the public factory and uses production
assembly, modal, buckling, linear-solve, recovery-batch and stiffness-batch
paths.  Raw timings and process measurements are external diagnostics; the
cycle-common record contains only deterministic authority, coverage and gate
dispositions so two independently executed cycles can be compared byte for
byte.  Assembly and solve gates use adjacent, position-balanced Q4/candidate
pairs in one process; fresh topology-specific workers measure peak RSS only.

This lane does not activate S3, change either element formulation, or turn a
representative N=20 measurement into unexecuted full-campaign coverage.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import contextlib
import ctypes
from ctypes import wintypes
from dataclasses import dataclass
import hashlib
import importlib.util
import io
import json
import math
import os
from pathlib import Path
import signal
import statistics
import subprocess
import sys
import time
from typing import Any, Callable, Iterable, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[2]
REFERENCE_CASES = ROOT / "docs" / "reference_cases"
DEFAULT_INPUT = REFERENCE_CASES / "e4_pl_s3_mixed_eigen_performance_input.json"

INPUT_SCHEMA = "anysolver.e4-pl-s3-mixed-eigen-performance-input-v1"
WORKER_SCHEMA = "anysolver.e4-pl-s3-mixed-eigen-performance-worker-v1"
COMMON_SCHEMA = "anysolver.e4-pl-s3-mixed-eigen-performance-common-v1"
DIAGNOSTIC_SCHEMA = "anysolver.e4-pl-s3-mixed-eigen-performance-diagnostic-v1"
TWO_CYCLE_SCHEMA = "anysolver.e4-pl-s3-mixed-eigen-performance-two-cycle-v1"

PRODUCTION_RESTRICTION = (
    "QUALIFIED_S3_REMAINS_OPT_IN_AND_QUALIFIED_Q4_REMAINS_UNCHANGED"
)
PASS = "PASS_MEASURED_REGISTERED_SCOPE"
FAIL = "FAIL_MEASURED_CONTRADICTION"
BLOCKED = "BLOCKED_PROCESS_OR_MALFORMED_MECHANICS"
UNEXECUTED = "UNEXECUTED_NO_HASH_BOUND_BASELINE"

HOT_PATH_PRIMARY_METRIC = "s3_stiffness_batch_median_seconds"
HOT_PATH_DIAGNOSTIC_METRICS = (
    "mixed_10_assembly_ratio_to_all_q4",
    "mixed_25_assembly_ratio_to_all_q4",
    "s3_stiffness_batch_ratio_to_q4",
    "s3_stiffness_batch_ratio_to_scalar_fallback",
    "s3_recovery_batch_ratio_to_scalar_fallback",
)

PAIRED_REPETITIONS = 12
PAIRED_SCHEDULE = "BALANCED_ADJACENT_AB_BA_12_V1"
PAIRED_COMPARISON = "MEDIAN_OF_ADJACENT_CANDIDATE_TO_Q4_RATIOS"
PERFORMANCE_ROUTES = ("assembly", "production_end_to_end_solve")
PERFORMANCE_FRACTIONS = (0, 10, 25)
MIXED_FRACTIONS = (10, 25)

LEGACY_PERFORMANCE_WORKER_IDS = (
    "PERFORMANCE_ALL_Q4",
    "PERFORMANCE_MIXED_10",
    "PERFORMANCE_MIXED_25",
)

WORKER_IDS = (
    "MODAL_MIXED_10",
    "MODAL_MIXED_25",
    "BUCKLING_MIXED_10",
    "BUCKLING_MIXED_25",
    "PERFORMANCE_PAIRED",
    "RSS_ALL_Q4",
    "RSS_MIXED_10",
    "RSS_MIXED_25",
    "BATCH_4096",
)
PARALLEL_WORKERS = WORKER_IDS[:4]
SERIAL_PERFORMANCE_WORKERS = WORKER_IDS[4:5]
SERIAL_RSS_WORKERS = WORKER_IDS[5:8]
SERIAL_BATCH_WORKERS = WORKER_IDS[8:]

THREAD_ENVIRONMENT = {
    "OMP_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
    "NUMEXPR_NUM_THREADS": "1",
}

TERMINALS = (
    "BLOCKED_E4_PL_S3_MIXED_EIGEN_PERFORMANCE_PROCESS_OR_EVIDENCE",
    "NO_GO_E4_PL_S3_MIXED_EIGEN_OR_PERFORMANCE",
    "UNCLASSIFIED_E4_PL_S3_MIXED_EIGEN_PERFORMANCE_PARTIAL_COVERAGE",
    "EIGEN_PERFORMANCE_GATES_CLOSED_E4_PL_S3_MIXED_ONLY",
)


class EigenPerformanceError(ValueError):
    """A frozen input, worker record or aggregate is invalid."""


def canonical_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
        + b"\n"
    )


def pretty_canonical_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            indent=2,
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
        + b"\n"
    )


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def strict_json(raw: bytes, *, label: str) -> object:
    def reject_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
        made: dict[str, object] = {}
        for key, value in pairs:
            if key in made:
                raise EigenPerformanceError(
                    f"{label} contains duplicate key {key!r}"
                )
            made[key] = value
        return made

    def reject_constant(value: str) -> object:
        raise EigenPerformanceError(
            f"{label} contains nonfinite constant {value!r}"
        )

    try:
        return json.loads(
            raw,
            object_pairs_hook=reject_duplicates,
            parse_constant=reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise EigenPerformanceError(
            f"{label} is not strict UTF-8 JSON: {error}"
        ) from error


def _finite_tree(value: object, label: str = "value") -> None:
    if value is None or isinstance(value, (bool, str, int)):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise EigenPerformanceError(f"{label} contains a nonfinite float")
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise EigenPerformanceError(f"{label} has a non-string key")
            _finite_tree(item, f"{label}.{key}")
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _finite_tree(item, f"{label}[{index}]")
        return
    raise EigenPerformanceError(
        f"{label} contains unsupported {type(value).__name__}"
    )


def _exact_keys(value: Mapping[str, Any], expected: Iterable[str], label: str) -> None:
    actual = set(value)
    wanted = set(expected)
    if actual != wanted:
        raise EigenPerformanceError(
            f"{label} keys differ: missing={sorted(wanted-actual)}, "
            f"extra={sorted(actual-wanted)}"
        )


def _object(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise EigenPerformanceError(f"{label} must be an object")
    return value


def _array(value: object, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise EigenPerformanceError(f"{label} must be an array")
    return value


def _positive_integer(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise EigenPerformanceError(f"{label} must be a positive integer")
    return int(value)


def _digest(value: object, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789ABCDEF" for character in value)
    ):
        raise EigenPerformanceError(f"{label} must be an uppercase SHA-256")
    return value


def _fraction(value: str, label: str) -> float:
    if not isinstance(value, str):
        raise EigenPerformanceError(f"{label} must be a decimal string")
    try:
        made = float(value)
    except ValueError as error:
        raise EigenPerformanceError(f"{label} is not a decimal string") from error
    if not math.isfinite(made) or made < 0.0:
        raise EigenPerformanceError(f"{label} must be finite and nonnegative")
    return made


def read_canonical(path: Path, *, pretty: bool, label: str) -> tuple[bytes, dict[str, Any]]:
    raw = Path(path).read_bytes()
    value = strict_json(raw, label=label)
    if not isinstance(value, dict):
        raise EigenPerformanceError(f"{label} must be an object")
    expected = pretty_canonical_bytes(value) if pretty else canonical_bytes(value)
    if raw != expected:
        style = "pretty" if pretty else "compact"
        raise EigenPerformanceError(f"{label} is not canonical {style} JSON")
    return raw, value


def write_exclusive(path: Path, value: object) -> None:
    _finite_tree(value)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(canonical_bytes(value))


@dataclass(frozen=True)
class Authorities:
    input_path: Path
    input_raw: bytes
    input: dict[str, Any]
    manifest: dict[str, Any]
    manifest_raw: bytes
    contract: dict[str, Any]
    contract_raw: bytes
    model_path: Path
    batch_path: Path
    hot_path_baseline_cycles: tuple[dict[str, dict[str, Any]], ...]


def _bound_file(
    row_value: object,
    label: str,
    *,
    allowed_prefixes: Sequence[str],
) -> tuple[Path, bytes]:
    row = _object(row_value, label)
    _exact_keys(row, ("bytes", "path", "sha256"), label)
    relative = row["path"]
    if not isinstance(relative, str) or not any(
        relative.startswith(prefix) for prefix in allowed_prefixes
    ):
        raise EigenPerformanceError(f"{label}.path is outside its allowed extent")
    path = (ROOT / relative).resolve(strict=True)
    if not path.is_relative_to(ROOT.resolve()):
        raise EigenPerformanceError(f"{label}.path escapes the repository")
    raw = path.read_bytes()
    if len(raw) != _positive_integer(row["bytes"], f"{label}.bytes"):
        raise EigenPerformanceError(f"{label} byte count mismatch")
    if sha256(raw) != _digest(row["sha256"], f"{label}.sha256"):
        raise EigenPerformanceError(f"{label} hash mismatch")
    return path, raw


def _git(*arguments: str) -> str:
    process = subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if process.returncode != 0:
        raise EigenPerformanceError(
            f"git {' '.join(arguments)} failed: {process.stderr.strip()}"
        )
    return process.stdout.strip()


def _validate_candidate(value: object) -> None:
    candidate = _object(value, "authority.candidate")
    _exact_keys(
        candidate,
        (
            "allowed_successor_paths",
            "changed_paths",
            "commit",
            "parent",
            "subject",
            "tree",
        ),
        "authority.candidate",
    )
    commit = str(candidate["commit"])
    parent = str(candidate["parent"])
    tree = str(candidate["tree"])
    if len(commit) != 40 or len(parent) != 40 or len(tree) != 40:
        raise EigenPerformanceError(
            "candidate commit/parent/tree must be full object IDs"
        )
    if _git("show", "-s", "--format=%H", commit) != commit:
        raise EigenPerformanceError("candidate commit identity mismatch")
    if _git("show", "-s", "--format=%P", commit) != parent:
        raise EigenPerformanceError("candidate parent identity mismatch")
    if _git("show", "-s", "--format=%T", commit) != tree:
        raise EigenPerformanceError("candidate tree identity mismatch")
    if _git("show", "-s", "--format=%s", commit) != candidate["subject"]:
        raise EigenPerformanceError("candidate subject identity mismatch")
    changed_paths = _array(candidate["changed_paths"], "candidate.changed_paths")
    if (
        any(not isinstance(path, str) or not path for path in changed_paths)
        or changed_paths != sorted(set(changed_paths))
    ):
        raise EigenPerformanceError(
            "candidate changed paths must be unique sorted nonempty strings"
        )
    actual_paths = sorted(
        path
        for path in _git("diff", "--name-only", parent, commit, "--").splitlines()
        if path
    )
    if actual_paths != changed_paths:
        raise EigenPerformanceError("candidate changed extent mismatch")
    allowed_successor_paths = _array(
        candidate["allowed_successor_paths"], "candidate.allowed_successor_paths"
    )
    if (
        any(
            not isinstance(path, str) or not path
            for path in allowed_successor_paths
        )
        or allowed_successor_paths != sorted(set(allowed_successor_paths))
    ):
        raise EigenPerformanceError(
            "candidate successor paths must be unique sorted nonempty strings"
        )
    process = subprocess.run(
        ["git", "merge-base", "--is-ancestor", commit, "HEAD"],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        check=False,
    )
    if process.returncode != 0:
        raise EigenPerformanceError("current HEAD does not descend from the candidate")
    committed_successor_paths = sorted(
        path
        for path in _git("diff", "--name-only", commit, "HEAD", "--").splitlines()
        if path
    )
    untracked_successor_paths: list[str] = []
    for row in _git("status", "--porcelain=v1", "--untracked-files=all").splitlines():
        if not row.startswith("?? "):
            raise EigenPerformanceError(
                "current evidence worktree has a tracked modification"
            )
        untracked_successor_paths.append(row[3:])
    if set(committed_successor_paths) & set(untracked_successor_paths):
        raise EigenPerformanceError("evidence path is both committed and untracked")
    observed_successor_paths = sorted(
        {*committed_successor_paths, *untracked_successor_paths}
    )
    if observed_successor_paths != allowed_successor_paths:
        raise EigenPerformanceError(
            "candidate-to-current evidence extent mismatch"
        )


def _bound_external_file(
    root: Path,
    row_value: object,
    label: str,
) -> tuple[bytes, dict[str, Any]]:
    row = _object(row_value, label)
    _exact_keys(row, ("bytes", "path", "sha256"), label)
    relative = row["path"]
    if (
        not isinstance(relative, str)
        or not relative
        or Path(relative).is_absolute()
    ):
        raise EigenPerformanceError(f"{label}.path must be relative")
    path = (root / relative).resolve(strict=True)
    if not path.is_relative_to(root):
        raise EigenPerformanceError(f"{label}.path escapes the frozen root")
    raw = path.read_bytes()
    if len(raw) != _positive_integer(row["bytes"], f"{label}.bytes"):
        raise EigenPerformanceError(f"{label} byte count mismatch")
    if sha256(raw) != _digest(row["sha256"], f"{label}.sha256"):
        raise EigenPerformanceError(f"{label} hash mismatch")
    value = strict_json(raw, label=label)
    if not isinstance(value, dict) or raw != canonical_bytes(value):
        raise EigenPerformanceError(f"{label} is not canonical compact JSON")
    return raw, value


def _load_hot_path_baseline(value: object) -> tuple[dict[str, dict[str, Any]], ...]:
    authority = _object(value, "authority.prior_hot_path_baseline")
    _exact_keys(
        authority,
        ("authority_sha256", "files", "root"),
        "authority.prior_hot_path_baseline",
    )
    authority_sha = _digest(
        authority["authority_sha256"], "prior baseline authority_sha256"
    )
    root_value = authority["root"]
    if not isinstance(root_value, str):
        raise EigenPerformanceError("prior baseline root must be a string")
    root = Path(root_value).resolve(strict=True)
    expected_root = Path(
        r"C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease\s3-eigen-performance-20260825-2b169855"
    ).resolve(strict=True)
    if root != expected_root:
        raise EigenPerformanceError("prior baseline root identity changed")
    files = _object(authority["files"], "prior baseline files")
    expected_file_ids = {
        "two_cycle_common",
        "cycle_1_common",
        "cycle_1_batch",
        "cycle_1_performance_all_q4",
        "cycle_1_performance_mixed_10",
        "cycle_1_performance_mixed_25",
        "cycle_2_common",
        "cycle_2_batch",
        "cycle_2_performance_all_q4",
        "cycle_2_performance_mixed_10",
        "cycle_2_performance_mixed_25",
    }
    _exact_keys(files, expected_file_ids, "prior baseline files")
    bound = {
        file_id: _bound_external_file(
            root, files[file_id], f"prior baseline {file_id}"
        )
        for file_id in sorted(expected_file_ids)
    }
    two_raw, two_cycle = bound["two_cycle_common"]
    del two_raw
    _exact_keys(
        two_cycle,
        (
            "authority_sha256",
            "common_aggregate_sha256",
            "cycles_byte_identical",
            "production_restriction",
            "schema",
            "terminal",
        ),
        "prior two-cycle common",
    )
    if (
        two_cycle["schema"] != TWO_CYCLE_SCHEMA
        or two_cycle["authority_sha256"] != authority_sha
        or two_cycle["cycles_byte_identical"] is not True
        or two_cycle["production_restriction"] != PRODUCTION_RESTRICTION
    ):
        raise EigenPerformanceError("prior two-cycle authority is invalid")
    common_raws = (bound["cycle_1_common"][0], bound["cycle_2_common"][0])
    if (
        common_raws[0] != common_raws[1]
        or sha256(common_raws[0]) != two_cycle["common_aggregate_sha256"]
    ):
        raise EigenPerformanceError("prior cycle-common agreement is invalid")

    cycles: list[dict[str, dict[str, Any]]] = []
    for cycle in (1, 2):
        common = bound[f"cycle_{cycle}_common"][1]
        if (
            common.get("schema") != COMMON_SCHEMA
            or common.get("authority_sha256") != authority_sha
            or common.get("production_restriction") != PRODUCTION_RESTRICTION
            or common.get("coverage", {}).get("registered_scope_only") is not True
        ):
            raise EigenPerformanceError(
                f"prior cycle {cycle} common authority is invalid"
            )
        records: dict[str, dict[str, Any]] = {}
        for suffix, worker_id in (
            ("batch", "BATCH_4096"),
            ("performance_all_q4", "PERFORMANCE_ALL_Q4"),
            ("performance_mixed_10", "PERFORMANCE_MIXED_10"),
            ("performance_mixed_25", "PERFORMANCE_MIXED_25"),
        ):
            record = validate_worker(
                bound[f"cycle_{cycle}_{suffix}"][1],
                worker_id,
                allowed_ids=(*LEGACY_PERFORMANCE_WORKER_IDS, "BATCH_4096"),
            )
            if record["authority_sha256"] != authority_sha:
                raise EigenPerformanceError(
                    f"prior cycle {cycle} {worker_id} authority mismatch"
                )
            records[worker_id] = record
        if any(
            records[worker_id]["common"]["gate_status"].get(
                "performance_measurement"
            )
            != PASS
            for worker_id in LEGACY_PERFORMANCE_WORKER_IDS
        ):
            raise EigenPerformanceError(
                f"prior cycle {cycle} performance measurement was not accepted"
            )
        batch_status = records["BATCH_4096"]["common"]["gate_status"]
        if any(
            batch_status.get(key) != PASS
            for key in (
                "batch_equality",
                "batch_scalar_fallback",
                "batch_throughput",
                "warm_s3_vs_q4",
            )
        ):
            raise EigenPerformanceError(
                f"prior cycle {cycle} batch measurement was not accepted"
            )
        cycles.append(records)
    return tuple(cycles)


def _topology_rows(payload: Mapping[str, Any]) -> dict[int, dict[str, Any]]:
    coverage = _object(payload["coverage"], "coverage")
    matched = _object(coverage["matched_topologies"], "coverage.matched_topologies")
    _exact_keys(
        matched,
        ("all_q4", "mixed_10_percent", "mixed_25_percent"),
        "coverage.matched_topologies",
    )
    result: dict[int, dict[str, Any]] = {}
    for name, expected_fraction in (
        ("all_q4", 0),
        ("mixed_10_percent", 10),
        ("mixed_25_percent", 25),
    ):
        row = _object(matched[name], f"coverage.matched_topologies.{name}")
        _exact_keys(
            row,
            (
                "connectivity_sha256",
                "diagonal",
                "level",
                "mask",
                "s3_area_fraction_percent",
                "split_base_cell_count",
            ),
            f"coverage.matched_topologies.{name}",
        )
        if (
            row["s3_area_fraction_percent"] != expected_fraction
            or row["level"] != 20
            or row["diagonal"] != "alternating"
            or row["mask"] != ("none" if expected_fraction == 0 else "dispersed")
        ):
            raise EigenPerformanceError(f"{name} topology identity changed")
        _digest(row["connectivity_sha256"], f"{name}.connectivity_sha256")
        result[expected_fraction] = dict(row)
    return result


def load_authorities(input_path: Path = DEFAULT_INPUT) -> Authorities:
    input_raw, payload = read_canonical(
        Path(input_path), pretty=True, label="eigen/performance input"
    )
    _exact_keys(payload, ("authority", "coverage", "execution", "schema"), "input")
    if payload["schema"] != INPUT_SCHEMA:
        raise EigenPerformanceError(f"input schema must be {INPUT_SCHEMA}")
    authority = _object(payload["authority"], "authority")
    _exact_keys(
        authority,
        (
            "batch_benchmark",
            "candidate",
            "connectivity_manifest",
            "model_authority",
            "prior_hot_path_baseline",
            "production_boundary",
            "qualification_contract",
            "runner",
        ),
        "authority",
    )
    _validate_candidate(authority["candidate"])
    manifest_path, manifest_raw = _bound_file(
        authority["connectivity_manifest"],
        "connectivity manifest",
        allowed_prefixes=("docs/reference_cases/",),
    )
    contract_path, contract_raw = _bound_file(
        authority["qualification_contract"],
        "qualification contract",
        allowed_prefixes=("docs/reference_cases/",),
    )
    model_path, _model_raw = _bound_file(
        authority["model_authority"],
        "model authority",
        allowed_prefixes=("docs/reference_cases/",),
    )
    production_boundary = _object(
        authority["production_boundary"], "authority.production_boundary"
    )
    _exact_keys(
        production_boundary,
        ("default_selector", "production_readiness", "public_exports", "q4_mechanics"),
        "authority.production_boundary",
    )
    boundary_paths: dict[str, Path] = {}
    boundary_raws: dict[str, bytes] = {}
    for boundary_id in sorted(production_boundary):
        boundary_paths[boundary_id], boundary_raws[boundary_id] = _bound_file(
            production_boundary[boundary_id],
            f"production boundary {boundary_id}",
            allowed_prefixes=("src/anysolver/",),
        )
    batch_path, _batch_raw = _bound_file(
        authority["batch_benchmark"],
        "batch benchmark",
        allowed_prefixes=("scripts/",),
    )
    runner_path, _runner_raw = _bound_file(
        authority["runner"],
        "eigen/performance runner",
        allowed_prefixes=("docs/reference_cases/",),
    )
    if runner_path != Path(__file__).resolve():
        raise EigenPerformanceError("runner authority path changed")
    expected_boundary_paths = {
        "default_selector": (ROOT / "src" / "anysolver" / "elements.py").resolve(),
        "production_readiness": (
            ROOT / "src" / "anysolver" / "production_readiness.py"
        ).resolve(),
        "public_exports": (ROOT / "src" / "anysolver" / "__init__.py").resolve(),
        "q4_mechanics": (ROOT / "src" / "anysolver" / "e4_pl_element.py").resolve(),
    }
    if boundary_paths != expected_boundary_paths:
        raise EigenPerformanceError("production boundary path identity changed")
    manifest_value = strict_json(manifest_raw, label="connectivity manifest")
    contract_value = strict_json(contract_raw, label="qualification contract")
    if not isinstance(manifest_value, dict) or manifest_raw != canonical_bytes(manifest_value):
        raise EigenPerformanceError("connectivity manifest is not canonical compact JSON")
    if not isinstance(contract_value, dict) or contract_raw != pretty_canonical_bytes(contract_value):
        raise EigenPerformanceError("qualification contract is not canonical pretty JSON")
    if manifest_value.get("schema") != (
        "anysolver.e4-pl-s3-mixed-mesh-connectivity-manifest-v1"
    ):
        raise EigenPerformanceError("connectivity manifest schema mismatch")
    if contract_value.get("schema") != (
        "anysolver.e4-pl-s3-mixed-mesh-qualification-contract-v1"
    ):
        raise EigenPerformanceError("qualification contract schema mismatch")
    if contract_value["connectivity_authority"]["sha256"] != sha256(manifest_raw):
        raise EigenPerformanceError("contract does not bind the manifest")
    if contract_value["candidate"]["qualified_q4_mechanics_sha256"] != sha256(
        boundary_raws["q4_mechanics"]
    ):
        raise EigenPerformanceError("contract does not bind the Q4 mechanics")

    hot_path_baseline_cycles = _load_hot_path_baseline(
        authority["prior_hot_path_baseline"]
    )

    rows = _topology_rows(payload)
    for fraction, expected in rows.items():
        found = [
            row
            for row in manifest_value["records"]
            if row["level"] == expected["level"]
            and row["mask"] == expected["mask"]
            and row["diagonal"] == expected["diagonal"]
            and row["split_base_cell_count"] == expected["split_base_cell_count"]
            and row["s3_area_fraction_percent"] == fraction
        ]
        if len(found) != 1 or found[0]["connectivity_sha256"] != expected["connectivity_sha256"]:
            raise EigenPerformanceError(f"registered topology {fraction}% mismatch")

    execution = _object(payload["execution"], "execution")
    expected_execution = {
        "automatic_retry": False,
        "canonical_cycles": 2,
        "memory_limit_gib_per_process": 24,
        "numerical_library_threads_per_process": 1,
        "performance_workers_are_serial": True,
        "timeout_seconds_per_process": 600,
        "worker_concurrency": 3,
        "worker_ids": list(WORKER_IDS),
    }
    if execution != expected_execution:
        raise EigenPerformanceError("bounded execution policy changed")

    gates = contract_value["acceptance_gates"]
    modal = payload["coverage"]["modal"]
    buckling = payload["coverage"]["buckling"]
    performance = _object(
        payload["coverage"]["performance"], "coverage.performance"
    )
    _exact_keys(
        performance,
        (
            "comparison",
            "mixed_fractions_percent",
            "repetitions",
            "rss_isolated_workers",
            "schedule",
            "warmups_per_route",
        ),
        "coverage.performance",
    )
    batch = payload["coverage"]["batch"]
    hot_path_policy = _object(
        payload["coverage"]["candidate_hot_path_baseline"],
        "coverage.candidate_hot_path_baseline",
    )
    _exact_keys(
        hot_path_policy,
        (
            "maximum_regression",
            "normalized_diagnostic_metrics",
            "primary_metric",
            "reference_selection",
            "secondary_guard",
        ),
        "coverage.candidate_hot_path_baseline",
    )
    if (
        hot_path_policy["primary_metric"] != HOT_PATH_PRIMARY_METRIC
        or hot_path_policy["normalized_diagnostic_metrics"]
        != list(HOT_PATH_DIAGNOSTIC_METRICS)
        or hot_path_policy["reference_selection"]
        != "MAXIMUM_RAW_S3_STIFFNESS_MEDIAN_ACROSS_TWO_HASH_BOUND_FORMAL_CYCLES"
        or hot_path_policy["secondary_guard"]
        != "WARM_S3_NO_SLOWER_THAN_Q4_EXISTING_BATCH_GATE"
        or _fraction(
            hot_path_policy["maximum_regression"],
            "candidate hot-path maximum regression",
        )
        != 0.05
    ):
        raise EigenPerformanceError("candidate hot-path gate policy changed")
    if (
        modal["required_rigid_mode_count"] != gates["modal"]["exact_rigid_mode_count"]
        or modal["elastic_frequency_count"] != gates["modal"]["elastic_frequency_count"]
        or buckling["first_factor_count"] != gates["buckling"]["first_factor_count"]
        or performance["mixed_fractions_percent"] != list(MIXED_FRACTIONS)
        or performance["repetitions"] != PAIRED_REPETITIONS
        or performance["repetitions"]
        < gates["performance"]["repetitions_minimum"]
        or performance["warmups_per_route"]
        != gates["performance"]["warmup_count"]
        or performance["comparison"] != PAIRED_COMPARISON
        or performance["schedule"] != PAIRED_SCHEDULE
        or performance["rss_isolated_workers"] is not True
        or batch["eligible_element_count"] != gates["batch"]["eligible_element_count"]
        or batch["repetitions"] != gates["performance"]["repetitions_minimum"]
    ):
        raise EigenPerformanceError("coverage counts differ from the contract")
    _finite_tree(payload, "input")
    return Authorities(
        input_path=Path(input_path).resolve(),
        input_raw=input_raw,
        input=payload,
        manifest=manifest_value,
        manifest_raw=manifest_raw,
        contract=contract_value,
        contract_raw=contract_raw,
        model_path=model_path,
        batch_path=batch_path,
        hot_path_baseline_cycles=hot_path_baseline_cycles,
    )


def _load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise EigenPerformanceError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _smoke_authorities(authorities: Authorities) -> tuple[Any, Any]:
    runner = _load_module(
        "_s3_eigen_performance_model_authority",
        REFERENCE_CASES / "e4_pl_s3_mixed_mesh_qualification_runner.py",
    )
    smoke = runner.load_authorities(authorities.model_path)
    if smoke.manifest_raw != authorities.manifest_raw:
        raise EigenPerformanceError("model authority selected a different manifest")
    if smoke.contract_raw != authorities.contract_raw:
        raise EigenPerformanceError("model authority selected a different contract")
    return runner, smoke


def _build_case(authorities: Authorities, fraction: int, *, auxiliary: bool) -> Any:
    runner, smoke = _smoke_authorities(authorities)
    row = _topology_rows(authorities.input)[int(fraction)]
    spec = {
        "case_id": f"EIGEN_PERFORMANCE_N20_{int(fraction)}PCT_DISPERSED_ALTERNATING",
        "topology": {
            key: row[key]
            for key in (
                "connectivity_sha256",
                "diagonal",
                "level",
                "mask",
                "split_base_cell_count",
            )
        },
    }
    built = runner.build_case_model(
        smoke,
        spec,
        include_auxiliary_inputs=bool(auxiliary),
    )
    from anysolver.elements import DEFAULT_S3_FORMULATION

    expected_default = smoke.input_payload["factories"]["default_s3_expected"]
    if DEFAULT_S3_FORMULATION != expected_default or expected_default != "legacy-s3":
        raise EigenPerformanceError("qualified S3 was implicitly activated")
    return built


def _apply_supported_boundary(model: Any) -> list[int]:
    from anysolver.boundary import BoundaryCondition

    edge_nodes: list[int] = []
    for node_id, node in sorted(model.mesh.nodes.items()):
        x, y, _z = node.coords()
        if min(abs(x), abs(x - 1.0), abs(y), abs(y - 1.0)) <= 1.0e-12:
            edge_nodes.append(int(node_id))
    model.add_boundary_condition(
        BoundaryCondition(
            "all-boundary-translational-simple-support",
            edge_nodes,
            {"ux": 0.0, "uy": 0.0, "uz": 0.0},
        )
    )
    return edge_nodes


def _summary(samples: Sequence[float]) -> dict[str, Any]:
    chronological = [float(value) for value in samples]
    if not chronological or any(
        not math.isfinite(value) or value <= 0.0 for value in chronological
    ):
        raise EigenPerformanceError("timing samples must be finite and positive")
    values = sorted(chronological)
    median = float(statistics.median(chronological))
    position = 0.95 * (len(chronological) - 1)
    lower = int(math.floor(position))
    upper = int(math.ceil(position))
    p95 = values[lower] + (position - lower) * (values[upper] - values[lower])
    return {
        "mad_seconds": float(
            statistics.median(abs(value - median) for value in chronological)
        ),
        "median_seconds": median,
        "p95_seconds": float(p95),
        "samples_seconds": chronological,
    }


def _ratio_summary(samples: Sequence[float]) -> dict[str, Any]:
    chronological = [float(value) for value in samples]
    if not chronological or any(
        not math.isfinite(value) or value <= 0.0 for value in chronological
    ):
        raise EigenPerformanceError("paired ratios must be finite and positive")
    values = sorted(chronological)
    median = float(statistics.median(chronological))
    position = 0.95 * (len(chronological) - 1)
    lower = int(math.floor(position))
    upper = int(math.ceil(position))
    p95 = values[lower] + (position - lower) * (values[upper] - values[lower])
    return {
        "mad": float(
            statistics.median(abs(value - median) for value in chronological)
        ),
        "median": median,
        "p95": float(p95),
        "samples": chronological,
    }


def _paired_schedule(repetitions: int) -> list[dict[str, Any]]:
    """Return the frozen adjacent, position-balanced timing schedule."""
    if repetitions != PAIRED_REPETITIONS:
        raise EigenPerformanceError(
            f"paired timing requires exactly {PAIRED_REPETITIONS} repetitions"
        )
    patterns = (
        ((10, "REFERENCE_FIRST"), (25, "REFERENCE_FIRST")),
        ((25, "CANDIDATE_FIRST"), (10, "CANDIDATE_FIRST")),
        ((25, "REFERENCE_FIRST"), (10, "REFERENCE_FIRST")),
        ((10, "CANDIDATE_FIRST"), (25, "CANDIDATE_FIRST")),
    )
    rows: list[dict[str, Any]] = []
    for repetition in range(repetitions):
        phase = repetition % len(patterns)
        routes = (
            PERFORMANCE_ROUTES
            if phase in (0, 1)
            else tuple(reversed(PERFORMANCE_ROUTES))
        )
        for route in routes:
            for fraction, orientation in patterns[phase]:
                order = (
                    [0, fraction]
                    if orientation == "REFERENCE_FIRST"
                    else [fraction, 0]
                )
                rows.append(
                    {
                        "fraction_percent": fraction,
                        "order": order,
                        "repetition": repetition,
                        "route": route,
                    }
                )
    return rows


def _peak_rss_bytes() -> int | None:
    if os.name == "nt":
        class Counters(ctypes.Structure):
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

        handle = ctypes.windll.kernel32.OpenProcess(0x0410, False, os.getpid())
        if not handle:
            return None
        try:
            counters = Counters()
            counters.cb = ctypes.sizeof(counters)
            if not ctypes.windll.psapi.GetProcessMemoryInfo(
                handle, ctypes.byref(counters), counters.cb
            ):
                return None
            return int(counters.PeakWorkingSetSize)
        finally:
            ctypes.windll.kernel32.CloseHandle(handle)
    try:
        import resource

        peak = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        return peak if sys.platform == "darwin" else peak * 1024
    except (ImportError, ValueError):
        return None


def _free_rigid_certificate(model: Any, root_count: int) -> dict[str, Any]:
    import numpy as np
    from scipy import sparse
    from scipy.sparse import linalg as sparse_linalg

    from anysolver.assembly import (
        build_constraint_transformation,
        build_reduced_rigid_body_modes,
    )
    from anysolver.matrix_assembly import assemble_stiffness_matrix

    stiffness, _info = assemble_stiffness_matrix(model)
    zero = np.zeros(stiffness.shape[0], dtype=float)
    reduced, _load, transform, _known, independent, _constraint = (
        build_constraint_transformation(stiffness, zero, model)
    )
    rigid, rigid_info = build_reduced_rigid_body_modes(
        model,
        independent,
        int(stiffness.shape[0]),
        transformation=transform,
    )
    diagonal = np.asarray(reduced.diagonal(), dtype=float)
    if np.any(~np.isfinite(diagonal)) or np.any(diagonal <= 0.0):
        raise EigenPerformanceError("free stiffness has a nonpositive diagonal")
    scale = 1.0 / np.sqrt(diagonal)
    scaling = sparse.diags(scale, format="csr")
    dimensionless = (scaling @ reduced @ scaling).tocsr()
    dimensionless = (0.5 * (dimensionless + dimensionless.T)).tocsr()
    values = sparse_linalg.eigsh(
        dimensionless.tocsc(),
        k=int(root_count),
        sigma=-1.0e-7,
        which="LM",
        return_eigenvectors=False,
        tol=1.0e-10,
        maxiter=5000,
    )
    values = np.sort(np.asarray(values, dtype=float))
    threshold = 1.0e-10
    numerical_nullity = int(np.count_nonzero(np.abs(values) <= threshold))
    rigid_rank = int(np.linalg.matrix_rank(np.asarray(rigid, dtype=float)))
    action = np.asarray(reduced @ rigid, dtype=float)
    action_residual = float(
        np.linalg.norm(action, ord="fro")
        / max(float(sparse_linalg.norm(reduced)), np.finfo(float).tiny)
    )
    passed = bool(
        rigid.shape[1] == 6
        and rigid_rank == 6
        and numerical_nullity == 6
        and values.size >= 7
        and values[6] > 100.0 * threshold
        and action_residual <= 1.0e-12
    )
    return {
        "analytic_basis_columns": int(rigid.shape[1]),
        "analytic_basis_rank": rigid_rank,
        "analytic_null_action_residual": action_residual,
        "dimensionless_smallest_roots": [float(value) for value in values],
        "dimensionless_zero_threshold": threshold,
        "first_flexible_root": float(values[6]),
        "numerical_nullity": numerical_nullity,
        "nullspace_info": rigid_info,
        "passed": passed,
        "support_state": "NO_BOUNDARY_CONDITIONS_APPLIED",
    }


def _clusters(values: Sequence[float], tolerance: float) -> list[list[int]]:
    made = [float(value) for value in values]
    result: list[list[int]] = []
    for index, value in enumerate(made):
        if not result:
            result.append([index])
            continue
        reference = made[result[-1][0]]
        spread = abs(value - reference) / max(abs(reference), 1.0)
        if spread <= tolerance:
            result[-1].append(index)
        else:
            result.append([index])
    return result


def _inverse_sqrt(matrix: Any) -> Any:
    import numpy as np

    made = np.asarray(matrix, dtype=float)
    made = 0.5 * (made + made.T)
    values, vectors = np.linalg.eigh(made)
    threshold = max(float(np.max(np.abs(values))), 1.0) * 1.0e-12
    if np.any(values <= threshold):
        raise EigenPerformanceError("MAC Gram matrix is not positive definite")
    return (vectors * (1.0 / np.sqrt(values))) @ vectors.T


def _clustered_mac(
    reference_vectors: Any,
    candidate_vectors: Any,
    metric: Any,
    reference_values: Sequence[float],
    tolerance: float,
) -> dict[str, Any]:
    import numpy as np
    from scipy import sparse

    reference = np.asarray(reference_vectors, dtype=float)
    candidate = np.asarray(candidate_vectors, dtype=float)
    if reference.shape != candidate.shape or reference.ndim != 2:
        raise EigenPerformanceError("MAC vector arrays are incompatible")
    metric_matrix = metric if sparse.issparse(metric) else np.asarray(metric, dtype=float)
    records: list[dict[str, Any]] = []
    for indices in _clusters(reference_values, tolerance):
        left = reference[:, indices]
        right = candidate[:, indices]
        metric_left = metric_matrix @ left
        metric_right = metric_matrix @ right
        left_gram = np.asarray(left.T @ metric_left, dtype=float)
        right_gram = np.asarray(right.T @ metric_right, dtype=float)
        cross = np.asarray(left.T @ metric_right, dtype=float)
        correlation = _inverse_sqrt(left_gram) @ cross @ _inverse_sqrt(right_gram)
        singular = np.linalg.svd(correlation, compute_uv=False)
        score = float(np.min(np.square(np.clip(singular, 0.0, 1.0))))
        records.append(
            {
                "indices": [int(index) for index in indices],
                "minimum_subspace_mac": score,
                "singular_values": [float(value) for value in singular],
            }
        )
    return {
        "clusters": records,
        "minimum_clustered_mac": min(
            (record["minimum_subspace_mac"] for record in records),
            default=0.0,
        ),
        "relative_cluster_tolerance": float(tolerance),
    }


def _modal_worker(authorities: Authorities, fraction: int) -> tuple[dict[str, str], dict[str, Any]]:
    import numpy as np

    from anysolver.matrix_assembly import assemble_mass_matrix
    from anysolver.modal import solve_free_vibration

    modal_spec = authorities.input["coverage"]["modal"]
    rigid_reference = _free_rigid_certificate(
        _build_case(authorities, 0, auxiliary=False).model,
        int(modal_spec["free_scaled_spectrum_root_count"]),
    )
    rigid_candidate = _free_rigid_certificate(
        _build_case(authorities, fraction, auxiliary=False).model,
        int(modal_spec["free_scaled_spectrum_root_count"]),
    )
    rigid_status = (
        PASS
        if rigid_reference["passed"] and rigid_candidate["passed"]
        else FAIL
    )

    reference = _build_case(authorities, 0, auxiliary=False)
    candidate = _build_case(authorities, fraction, auxiliary=False)
    reference_edges = _apply_supported_boundary(reference.model)
    candidate_edges = _apply_supported_boundary(candidate.model)
    if reference_edges != candidate_edges:
        raise EigenPerformanceError("matched modal support node IDs differ")
    mode_count = int(modal_spec["elastic_frequency_count"])
    shift = float(modal_spec["shift"])
    started = time.perf_counter()
    reference_result = solve_free_vibration(
        reference.model,
        num_modes=mode_count,
        dense_size_limit=200,
        shift=shift,
    )
    reference_seconds = float(time.perf_counter() - started)
    started = time.perf_counter()
    candidate_result = solve_free_vibration(
        candidate.model,
        num_modes=mode_count,
        dense_size_limit=200,
        shift=shift,
    )
    candidate_seconds = float(time.perf_counter() - started)
    diagnostics: dict[str, Any] = {
        "call_path": (
            "anysolver.modal.solve_free_vibration -> "
            "anysolver.algebraic_dynamics.build_declared_algebraic_basis -> "
            "anysolver.algebraic_dynamics.solve_descriptor_spectrum"
        ),
        "candidate_elapsed_seconds": candidate_seconds,
        "candidate_solver_diagnostics": candidate_result.diagnostics,
        "fraction_percent": int(fraction),
        "reference_elapsed_seconds": reference_seconds,
        "reference_solver_diagnostics": reference_result.diagnostics,
        "rigid_candidate": rigid_candidate,
        "rigid_reference": rigid_reference,
        "support_dofs": ["ux", "uy", "uz"],
        "support_node_count": len(reference_edges),
        "topology_candidate": _topology_rows(authorities.input)[fraction],
        "topology_reference": _topology_rows(authorities.input)[0],
    }
    if (
        reference_result.solver_status != "ok"
        or candidate_result.solver_status != "ok"
        or len(reference_result.modes) != mode_count
        or len(candidate_result.modes) != mode_count
    ):
        diagnostics.update(
            {
                "candidate_mode_count": len(candidate_result.modes),
                "candidate_status": candidate_result.solver_status,
                "reference_mode_count": len(reference_result.modes),
                "reference_status": reference_result.solver_status,
            }
        )
        return {
            "modal_frequency": BLOCKED,
            "modal_mac": BLOCKED,
            "rigid_modes": rigid_status,
        }, diagnostics

    reference_frequencies = np.asarray(reference_result.frequencies_hz, dtype=float)
    candidate_frequencies = np.asarray(candidate_result.frequencies_hz, dtype=float)
    errors = np.abs(candidate_frequencies - reference_frequencies) / np.maximum(
        np.abs(reference_frequencies), np.finfo(float).tiny
    )
    mass, _mass_info = assemble_mass_matrix(reference.model)
    reference_vectors = np.column_stack(
        [mode.mode_shape for mode in reference_result.modes]
    )
    candidate_vectors = np.column_stack(
        [mode.mode_shape for mode in candidate_result.modes]
    )
    mac = _clustered_mac(
        reference_vectors,
        candidate_vectors,
        mass,
        reference_frequencies,
        _fraction(modal_spec["cluster_relative_tolerance"], "modal cluster tolerance"),
    )
    gates = authorities.contract["acceptance_gates"]["modal"]
    frequency_limit = _fraction(gates["maximum_frequency_error"], "modal error gate")
    mac_limit = _fraction(gates["clustered_mac_minimum"], "modal MAC gate")
    diagnostics.update(
        {
            "candidate_frequencies_hz": [float(value) for value in candidate_frequencies],
            "clustered_mac": mac,
            "frequency_relative_errors": [float(value) for value in errors],
            "maximum_frequency_relative_error": float(np.max(errors)),
            "reference_frequencies_hz": [float(value) for value in reference_frequencies],
        }
    )
    return {
        "modal_frequency": PASS if float(np.max(errors)) <= frequency_limit else FAIL,
        "modal_mac": PASS if mac["minimum_clustered_mac"] >= mac_limit else FAIL,
        "rigid_modes": rigid_status,
    }, diagnostics


def _reference_elastic_states(
    model: Any,
    buckling_spec: Mapping[str, Any],
) -> dict[int, dict[str, Any]]:
    import numpy as np

    from anysolver.e4_pl_s3_element import (
        FORMULATION_ID as QUALIFIED_S3_FORMULATION_ID,
        REFERENCE_ELASTIC_BUBBLE_LINEARIZATION_ID,
    )

    global_tensor = np.asarray(
        buckling_spec["physical_global_membrane_compression_tensor"],
        dtype=float,
    )
    if (
        global_tensor.shape != (3, 3)
        or np.any(~np.isfinite(global_tensor))
        or not np.array_equal(global_tensor, global_tensor.T)
    ):
        raise EigenPerformanceError(
            "buckling physical global compression tensor must be finite symmetric 3x3"
        )
    states: dict[int, dict[str, Any]] = {}
    for element_id, element in model.mesh.elements.items():
        material = model.get_material(element.material_name)
        components = element.compute_stiffness_components(model.mesh, material)
        frame = np.asarray(components["frame"], dtype=float)
        if frame.shape != (3, 3) or np.any(~np.isfinite(frame)):
            raise EigenPerformanceError("buckling element frame is not finite 3x3")
        in_plane = frame[:, :2]
        local_tensor = in_plane.T @ global_tensor @ in_plane
        local_resultant = [
            float(local_tensor[0, 0]),
            float(local_tensor[1, 1]),
            float(local_tensor[0, 1]),
        ]
        thickness = float(element.thickness)
        if not math.isfinite(thickness) or thickness <= 0.0:
            raise EigenPerformanceError("buckling element thickness is invalid")
        state: dict[str, Any] = {
            "bending_compression": [0.0, 0.0, 0.0],
            "membrane_compression": local_resultant,
            "stress_second_moment": [
                float(value * thickness * thickness / 12.0)
                for value in local_resultant
            ],
        }
        if getattr(element, "formulation_id", None) == QUALIFIED_S3_FORMULATION_ID:
            state["bubble_linearization_policy"] = (
                REFERENCE_ELASTIC_BUBBLE_LINEARIZATION_ID
            )
        states[int(element_id)] = state
    return states


def _rejected_nonpositive_count(result: Any) -> int:
    count = 0
    for row in result.diagnostics.get("rejected_roots", ()):
        if row.get("reason") == "nonpositive_modal_terms":
            count += 1
        elif row.get("reason") == "invalid_load_factor" and float(
            row.get("load_factor", 1.0)
        ) <= 0.0:
            count += 1
    return count


def _buckling_worker(authorities: Authorities, fraction: int) -> tuple[dict[str, str], dict[str, Any]]:
    import numpy as np
    from scipy import sparse

    from anysolver.buckling import solve_eigenvalue_buckling

    spec = authorities.input["coverage"]["buckling"]
    reference = _build_case(authorities, 0, auxiliary=False)
    candidate = _build_case(authorities, fraction, auxiliary=False)
    reference_edges = _apply_supported_boundary(reference.model)
    candidate_edges = _apply_supported_boundary(candidate.model)
    if reference_edges != candidate_edges:
        raise EigenPerformanceError("matched buckling support node IDs differ")
    count = int(spec["first_factor_count"])
    common_arguments = {
        "num_modes": count,
        "dense_size_limit": 200,
        "reference_elastic_only": True,
        "search_factor": int(spec["search_factor"]),
    }
    started = time.perf_counter()
    reference_result = solve_eigenvalue_buckling(
        reference.model,
        _reference_elastic_states(reference.model, spec),
        **common_arguments,
    )
    reference_seconds = float(time.perf_counter() - started)
    started = time.perf_counter()
    candidate_result = solve_eigenvalue_buckling(
        candidate.model,
        _reference_elastic_states(candidate.model, spec),
        **common_arguments,
    )
    candidate_seconds = float(time.perf_counter() - started)
    diagnostics: dict[str, Any] = {
        "boundary_construction": (
            "all boundary nodes constrain ux, uy, uz; rotations remain free"
        ),
        "call_path": "anysolver.buckling.solve_eigenvalue_buckling",
        "candidate_elapsed_seconds": candidate_seconds,
        "candidate_solver_diagnostics": candidate_result.diagnostics,
        "fraction_percent": int(fraction),
        "mode_pairing": (
            "ascending positive load factor; repeated reference factors form "
            "clustered Euclidean subspaces"
        ),
        "prestress": {
            "bending_compression": [0.0, 0.0, 0.0],
            "physical_global_membrane_compression_tensor": spec[
                "physical_global_membrane_compression_tensor"
            ],
            "reference_elastic_only": True,
            "stress_second_moment_policy": (
                "H_LOCAL_EQUALS_N_LOCAL_TIMES_THICKNESS_SQUARED_OVER_12"
            ),
        },
        "reference_elapsed_seconds": reference_seconds,
        "reference_solver_diagnostics": reference_result.diagnostics,
        "support_node_count": len(reference_edges),
        "topology_candidate": _topology_rows(authorities.input)[fraction],
        "topology_reference": _topology_rows(authorities.input)[0],
    }
    if (
        reference_result.solver_status != "ok"
        or candidate_result.solver_status != "ok"
        or len(reference_result.modes) != count
        or len(candidate_result.modes) != count
    ):
        return {
            "buckling_factors": BLOCKED,
            "buckling_mac": BLOCKED,
            "buckling_positive": BLOCKED,
        }, diagnostics
    reference_factors = np.asarray(
        [mode.load_factor for mode in reference_result.modes], dtype=float
    )
    candidate_factors = np.asarray(
        [mode.load_factor for mode in candidate_result.modes], dtype=float
    )
    errors = np.abs(candidate_factors - reference_factors) / np.maximum(
        np.abs(reference_factors), np.finfo(float).tiny
    )
    reference_vectors = np.column_stack(
        [mode.mode_shape for mode in reference_result.modes]
    )
    candidate_vectors = np.column_stack(
        [mode.mode_shape for mode in candidate_result.modes]
    )
    mac = _clustered_mac(
        reference_vectors,
        candidate_vectors,
        sparse.eye(reference_vectors.shape[0], format="csr", dtype=float),
        reference_factors,
        _fraction(
            spec["cluster_relative_tolerance"], "buckling cluster tolerance"
        ),
    )
    reference_nonpositive = _rejected_nonpositive_count(reference_result)
    candidate_nonpositive = _rejected_nonpositive_count(candidate_result)
    all_positive = bool(
        np.all(np.isfinite(candidate_factors))
        and np.all(candidate_factors > 0.0)
        and candidate_nonpositive <= reference_nonpositive
    )
    gates = authorities.contract["acceptance_gates"]["buckling"]
    factor_limit = _fraction(gates["maximum_factor_error"], "buckling error gate")
    mac_limit = _fraction(gates["clustered_mac_minimum"], "buckling MAC gate")
    diagnostics.update(
        {
            "candidate_factors": [float(value) for value in candidate_factors],
            "candidate_nonpositive_searched_roots": candidate_nonpositive,
            "clustered_mac": mac,
            "factor_relative_errors": [float(value) for value in errors],
            "maximum_factor_relative_error": float(np.max(errors)),
            "reference_factors": [float(value) for value in reference_factors],
            "reference_nonpositive_searched_roots": reference_nonpositive,
        }
    )
    return {
        "buckling_factors": PASS if float(np.max(errors)) <= factor_limit else FAIL,
        "buckling_mac": PASS if mac["minimum_clustered_mac"] >= mac_limit else FAIL,
        "buckling_positive": PASS if all_positive else FAIL,
    }, diagnostics


def _execute_performance_route(built: Any, route: str) -> None:
    from anysolver.assembly import solve_linear
    from anysolver.matrix_assembly import assemble_stiffness_matrix

    if route == "assembly":
        assemble_stiffness_matrix(built.model)
        return
    if route != "production_end_to_end_solve":
        raise EigenPerformanceError(f"unknown performance route {route!r}")
    if built.load_case is None:
        raise EigenPerformanceError("performance model has no production load case")
    displacement, info = solve_linear(
        built.model,
        built.load_case,
        constraint_mode="transformation",
    )
    if (info.get("convergence_info") or {}).get("status") != "converged":
        raise EigenPerformanceError("performance solve did not converge")
    if not all(math.isfinite(float(value)) for value in displacement):
        raise EigenPerformanceError("performance solve returned nonfinite displacement")


def _timed_performance_route(built: Any, route: str) -> tuple[int, int]:
    wall_started = time.perf_counter_ns()
    cpu_started = time.process_time_ns()
    _execute_performance_route(built, route)
    cpu_elapsed = time.process_time_ns() - cpu_started
    wall_elapsed = time.perf_counter_ns() - wall_started
    if wall_elapsed <= 0 or cpu_elapsed < 0:
        raise EigenPerformanceError("performance timer returned an invalid duration")
    return int(wall_elapsed), int(cpu_elapsed)


def _paired_comparison(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    candidate_ns = [int(record["candidate_wall_ns"]) for record in records]
    reference_ns = [int(record["reference_wall_ns"]) for record in records]
    ratios = [
        float(candidate) / float(reference)
        for candidate, reference in zip(candidate_ns, reference_ns, strict=True)
    ]
    return {
        "candidate": _summary([value * 1.0e-9 for value in candidate_ns]),
        "paired_ratio": _ratio_summary(ratios),
        "pairs": [dict(record) for record in records],
        "reference": _summary([value * 1.0e-9 for value in reference_ns]),
    }


def _collect_paired_measurements(
    built_by_fraction: Mapping[int, Any],
    *,
    repetitions: int,
    warmups_per_route: int,
) -> dict[str, dict[str, dict[str, Any]]]:
    if set(built_by_fraction) != set(PERFORMANCE_FRACTIONS):
        raise EigenPerformanceError("paired timing topology coverage differs")
    if warmups_per_route != 1:
        raise EigenPerformanceError("paired timing requires one warmup per topology/route")
    for fraction in PERFORMANCE_FRACTIONS:
        for route in PERFORMANCE_ROUTES:
            for _ in range(warmups_per_route):
                _execute_performance_route(built_by_fraction[fraction], route)

    collected: dict[str, dict[int, list[dict[str, Any]]]] = {
        route: {fraction: [] for fraction in MIXED_FRACTIONS}
        for route in PERFORMANCE_ROUTES
    }
    for row in _paired_schedule(repetitions):
        route = str(row["route"])
        fraction = int(row["fraction_percent"])
        order = [int(value) for value in row["order"]]
        measured: dict[int, tuple[int, int]] = {}
        for topology_fraction in order:
            measured[topology_fraction] = _timed_performance_route(
                built_by_fraction[topology_fraction], route
            )
        reference_wall, reference_cpu = measured[0]
        candidate_wall, candidate_cpu = measured[fraction]
        collected[route][fraction].append(
            {
                "candidate_cpu_ns": candidate_cpu,
                "candidate_wall_ns": candidate_wall,
                "order": order,
                "reference_cpu_ns": reference_cpu,
                "reference_wall_ns": reference_wall,
                "repetition": int(row["repetition"]),
            }
        )
    return {
        route: {
            str(fraction): _paired_comparison(collected[route][fraction])
            for fraction in MIXED_FRACTIONS
        }
        for route in PERFORMANCE_ROUTES
    }


def _topology_diagnostics(authorities: Authorities, built: Any, fraction: int) -> dict[str, Any]:
    return {
        "element_counts": {
            "Q4": sum(kind == "Q4" for kind in built.element_kinds.values()),
            "S3": sum(kind == "S3" for kind in built.element_kinds.values()),
        },
        "fraction_percent": int(fraction),
        "node_count": int(built.model.mesh.num_nodes),
        "topology": _topology_rows(authorities.input)[fraction],
    }


def _paired_performance_worker(
    authorities: Authorities,
) -> tuple[dict[str, str], dict[str, Any]]:
    spec = authorities.input["coverage"]["performance"]
    repeats = int(spec["repetitions"])
    warmups = int(spec["warmups_per_route"])
    built_by_fraction = {
        fraction: _build_case(authorities, fraction, auxiliary=True)
        for fraction in PERFORMANCE_FRACTIONS
    }
    comparisons = _collect_paired_measurements(
        built_by_fraction,
        repetitions=repeats,
        warmups_per_route=warmups,
    )
    diagnostics = {
        "comparisons": comparisons,
        "protocol": {
            "comparison": PAIRED_COMPARISON,
            "repetitions": repeats,
            "schedule": PAIRED_SCHEDULE,
            "warmups_per_topology_route": warmups,
        },
        "topologies": {
            str(fraction): _topology_diagnostics(
                authorities, built_by_fraction[fraction], fraction
            )
            for fraction in PERFORMANCE_FRACTIONS
        },
    }
    return {"performance_measurement": PASS}, diagnostics


def _rss_worker(
    authorities: Authorities, fraction: int
) -> tuple[dict[str, str], dict[str, Any]]:
    spec = authorities.input["coverage"]["performance"]
    repeats = int(spec["repetitions"])
    warmups = int(spec["warmups_per_route"])
    built = _build_case(authorities, fraction, auxiliary=True)
    for route in PERFORMANCE_ROUTES:
        for _ in range(warmups):
            _execute_performance_route(built, route)
    for repetition in range(repeats):
        routes = (
            PERFORMANCE_ROUTES
            if repetition % 2 == 0
            else tuple(reversed(PERFORMANCE_ROUTES))
        )
        for route in routes:
            _execute_performance_route(built, route)
    peak = _peak_rss_bytes()
    diagnostics = {
        **_topology_diagnostics(authorities, built, fraction),
        "operations_per_route": repeats + warmups,
        "peak_rss_bytes": peak,
        "repetitions": repeats,
        "warmups_per_route": warmups,
    }
    return {
        "rss_measurement": PASS if isinstance(peak, int) and peak > 0 else BLOCKED
    }, diagnostics


def _batch_worker(authorities: Authorities) -> tuple[dict[str, str], dict[str, Any]]:
    benchmark = _load_module(
        "_s3_formal_batch_benchmark",
        authorities.batch_path,
    )
    spec = authorities.input["coverage"]["batch"]
    arguments = [
        str(authorities.batch_path),
        "--elements",
        str(spec["eligible_element_count"]),
        "--repeats",
        str(spec["repetitions"]),
        "--include-q4-comparator",
    ]
    stream = io.StringIO()
    previous = list(sys.argv)
    try:
        sys.argv = arguments
        with contextlib.redirect_stdout(stream):
            returncode = benchmark.main()
    finally:
        sys.argv = previous
    if returncode != 0:
        raise EigenPerformanceError(f"batch benchmark returned {returncode}")
    payload = strict_json(stream.getvalue().encode("utf-8"), label="batch output")
    if not isinstance(payload, dict):
        raise EigenPerformanceError("batch benchmark output must be an object")
    gates = authorities.contract["acceptance_gates"]
    equality_limit = _fraction(gates["batch"]["scalar_equality_relative"], "batch equality")
    throughput_limit = _fraction(gates["batch"]["minimum_throughput_ratio"], "batch throughput")
    q4_ratio_limit = _fraction(
        gates["performance"]["warm_s3_tangent_ratio_to_qualified_q4_maximum"],
        "warm S3/Q4 ratio",
    )
    equality_pass = bool(
        payload["stiffness"]["equality"]["maximum_scaled_error"] <= equality_limit
        and payload["recovery"]["equality"]["maximum_scaled_error"] <= equality_limit
    )
    throughput_pass = bool(
        payload["stiffness"]["median_speedup"] >= throughput_limit
        and payload["recovery"]["median_speedup"] >= throughput_limit
    )
    fallback_pass = bool(
        payload["stiffness"]["scalar_fallback_element_count"]
        == spec["eligible_element_count"]
        and payload["recovery"]["scalar_fallback_element_count"]
        == spec["eligible_element_count"]
        and payload["recovery"]["scalar_batch_count"] == 0
    )
    q4_ratio = payload["qualified_q4_comparator"][
        "s3_over_q4_per_element_ratio"
    ]
    return {
        "batch_equality": PASS if equality_pass else FAIL,
        "batch_scalar_fallback": PASS if fallback_pass else FAIL,
        "batch_throughput": PASS if throughput_pass else FAIL,
        "warm_s3_vs_q4": PASS if q4_ratio <= q4_ratio_limit else FAIL,
    }, {"benchmark": payload, "peak_rss_bytes": _peak_rss_bytes()}


def run_worker(authorities: Authorities, worker_id: str) -> dict[str, Any]:
    if worker_id not in WORKER_IDS:
        raise EigenPerformanceError(f"unknown worker {worker_id!r}")
    started = time.perf_counter()
    try:
        if worker_id.startswith("MODAL_MIXED_"):
            statuses, diagnostics = _modal_worker(
                authorities, int(worker_id.rsplit("_", 1)[1])
            )
        elif worker_id.startswith("BUCKLING_MIXED_"):
            statuses, diagnostics = _buckling_worker(
                authorities, int(worker_id.rsplit("_", 1)[1])
            )
        elif worker_id == "PERFORMANCE_PAIRED":
            statuses, diagnostics = _paired_performance_worker(authorities)
        elif worker_id.startswith("RSS_"):
            fraction = 0 if worker_id.endswith("ALL_Q4") else int(
                worker_id.rsplit("_", 1)[1]
            )
            statuses, diagnostics = _rss_worker(authorities, fraction)
        else:
            statuses, diagnostics = _batch_worker(authorities)
    except Exception as error:  # Worker records a terminal mechanics failure.
        statuses = {"worker_execution": BLOCKED}
        diagnostics = {
            "error": str(error),
            "error_type": type(error).__name__,
        }
    diagnostics = {
        **diagnostics,
        "worker_elapsed_seconds": float(time.perf_counter() - started),
    }
    common = {
        "gate_status": statuses,
        "production_restriction": PRODUCTION_RESTRICTION,
        "worker_id": worker_id,
    }
    value = {
        "authority_sha256": sha256(authorities.input_raw),
        "common": common,
        "diagnostic_payload": diagnostics,
        "diagnostic_payload_sha256": sha256(canonical_bytes(diagnostics)),
        "schema": WORKER_SCHEMA,
        "worker_id": worker_id,
    }
    _finite_tree(value, "worker")
    return value


def validate_worker(
    value: object,
    expected_id: str | None = None,
    *,
    allowed_ids: Sequence[str] = WORKER_IDS,
) -> dict[str, Any]:
    made = _object(value, "worker")
    _exact_keys(
        made,
        (
            "authority_sha256",
            "common",
            "diagnostic_payload",
            "diagnostic_payload_sha256",
            "schema",
            "worker_id",
        ),
        "worker",
    )
    if made["schema"] != WORKER_SCHEMA or made["worker_id"] not in allowed_ids:
        raise EigenPerformanceError("worker identity mismatch")
    if expected_id is not None and made["worker_id"] != expected_id:
        raise EigenPerformanceError("unexpected worker ID")
    common = _object(made["common"], "worker.common")
    _exact_keys(
        common,
        ("gate_status", "production_restriction", "worker_id"),
        "worker.common",
    )
    if common["worker_id"] != made["worker_id"]:
        raise EigenPerformanceError("worker/common ID mismatch")
    if common["production_restriction"] != PRODUCTION_RESTRICTION:
        raise EigenPerformanceError("worker changed the production restriction")
    statuses = _object(common["gate_status"], "worker.common.gate_status")
    if not statuses or any(status not in {PASS, FAIL, BLOCKED} for status in statuses.values()):
        raise EigenPerformanceError("worker has an invalid gate status")
    diagnostics = _object(made["diagnostic_payload"], "worker diagnostics")
    if sha256(canonical_bytes(diagnostics)) != _digest(
        made["diagnostic_payload_sha256"], "worker diagnostic hash"
    ):
        raise EigenPerformanceError("worker diagnostic hash mismatch")
    _finite_tree(made, "worker")
    return made


@dataclass(frozen=True)
class ProcessResult:
    worker_id: str
    status: str
    returncode: int
    elapsed_seconds: float
    peak_rss_bytes: int | None
    directory: Path


def _rss_bytes(pid: int) -> int | None:
    if os.name == "nt":
        class Counters(ctypes.Structure):
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

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        psapi = ctypes.WinDLL("psapi", use_last_error=True)
        handle = kernel32.OpenProcess(0x0410, False, int(pid))
        if not handle:
            return None
        try:
            counters = Counters()
            counters.cb = ctypes.sizeof(counters)
            if not psapi.GetProcessMemoryInfo(
                handle, ctypes.byref(counters), counters.cb
            ):
                return None
            return int(counters.WorkingSetSize)
        finally:
            kernel32.CloseHandle(handle)
    try:
        raw = Path(f"/proc/{int(pid)}/status").read_text(encoding="ascii")
        line = next(item for item in raw.splitlines() if item.startswith("VmRSS:"))
        return int(line.split()[1]) * 1024
    except (OSError, StopIteration, ValueError, IndexError):
        return None


def _terminate_tree(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=30,
        )
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()


def run_bounded_process(
    worker_id: str,
    command: Sequence[str],
    *,
    directory: Path,
    environment: Mapping[str, str],
    timeout_seconds: int,
    memory_limit_bytes: int,
    rss_reader: Callable[[int], int | None] = _rss_bytes,
) -> ProcessResult:
    if directory.exists():
        raise EigenPerformanceError(f"worker directory already exists: {directory}")
    directory.mkdir(parents=True, exist_ok=False)
    stdout_path = directory / "stdout.log"
    stderr_path = directory / "stderr.log"
    record_path = directory / "record.json"
    started = time.monotonic()
    peak: int | None = None
    status = "RUNNING"
    flags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
    with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
        process = subprocess.Popen(
            list(command),
            cwd=ROOT,
            env=dict(environment),
            stdin=subprocess.DEVNULL,
            stdout=stdout,
            stderr=stderr,
            creationflags=flags,
            start_new_session=os.name != "nt",
        )
        while process.poll() is None:
            elapsed = time.monotonic() - started
            current = rss_reader(process.pid)
            if current is not None:
                peak = current if peak is None else max(peak, current)
            if elapsed > timeout_seconds:
                status = "TIMEOUT"
                _terminate_tree(process)
                break
            if current is not None and current > memory_limit_bytes:
                status = "MEMORY_LIMIT"
                _terminate_tree(process)
                break
            time.sleep(0.05)
        returncode = process.poll()
    if returncode is None:
        returncode = -9
    if status == "RUNNING":
        status = "COMPLETE" if returncode == 0 else "FAILED"
    if status != "COMPLETE":
        record_path.unlink(missing_ok=True)
    return ProcessResult(
        worker_id=worker_id,
        status=status,
        returncode=int(returncode),
        elapsed_seconds=float(time.monotonic() - started),
        peak_rss_bytes=peak,
        directory=directory,
    )


def _worker_command(authorities: Authorities, worker_id: str, output: Path) -> list[str]:
    return [
        sys.executable,
        str(Path(__file__).resolve()),
        "--worker",
        worker_id,
        "--input",
        str(authorities.input_path),
        "--output",
        str(output),
    ]


def _one_thread_environment() -> dict[str, str]:
    environment = dict(os.environ)
    environment.update(THREAD_ENVIRONMENT)
    source = str((ROOT / "src").resolve())
    current = environment.get("PYTHONPATH", "")
    environment["PYTHONPATH"] = source if not current else source + os.pathsep + current
    environment["PYTHONHASHSEED"] = "0"
    return environment


def _run_worker_set(
    authorities: Authorities,
    worker_ids: Sequence[str],
    *,
    cycle_root: Path,
    parallel: bool,
) -> list[ProcessResult]:
    execution = authorities.input["execution"]
    timeout = int(execution["timeout_seconds_per_process"])
    memory = int(execution["memory_limit_gib_per_process"]) * (1 << 30)
    environment = _one_thread_environment()

    def launch(worker_id: str) -> ProcessResult:
        directory = cycle_root / "workers" / worker_id.lower()
        return run_bounded_process(
            worker_id,
            _worker_command(authorities, worker_id, directory / "record.json"),
            directory=directory,
            environment=environment,
            timeout_seconds=timeout,
            memory_limit_bytes=memory,
        )

    if not parallel:
        return [launch(worker_id) for worker_id in worker_ids]
    maximum = min(int(execution["worker_concurrency"]), len(worker_ids))
    results: list[ProcessResult] = []
    with ThreadPoolExecutor(max_workers=maximum) as executor:
        futures = {
            executor.submit(launch, worker_id): worker_id
            for worker_id in worker_ids
        }
        for future in as_completed(futures):
            results.append(future.result())
    return sorted(results, key=lambda row: WORKER_IDS.index(row.worker_id))


def _process_diagnostic(result: ProcessResult) -> dict[str, Any]:
    return {
        "elapsed_seconds": result.elapsed_seconds,
        "peak_rss_bytes": result.peak_rss_bytes,
        "returncode": result.returncode,
        "status": result.status,
        "stderr_path": str((result.directory / "stderr.log").resolve()),
        "stdout_path": str((result.directory / "stdout.log").resolve()),
        "worker_id": result.worker_id,
    }


def _ratio_gate(value: float, maximum: float) -> str:
    if not math.isfinite(value) or value < 0.0:
        return BLOCKED
    return PASS if value <= maximum else FAIL


def _validated_paired_metrics(
    record: Mapping[str, Any],
    *,
    repetitions: int,
    warmups_per_route: int,
) -> dict[str, dict[int, float]]:
    diagnostics = _object(record.get("diagnostic_payload"), "paired diagnostics")
    protocol = _object(diagnostics.get("protocol"), "paired protocol")
    expected_protocol = {
        "comparison": PAIRED_COMPARISON,
        "repetitions": repetitions,
        "schedule": PAIRED_SCHEDULE,
        "warmups_per_topology_route": warmups_per_route,
    }
    if protocol != expected_protocol:
        raise EigenPerformanceError("paired timing protocol identity differs")
    comparisons = _object(diagnostics.get("comparisons"), "paired comparisons")
    _exact_keys(comparisons, PERFORMANCE_ROUTES, "paired comparisons")
    result: dict[str, dict[int, float]] = {}
    schedule = _paired_schedule(repetitions)
    for route in PERFORMANCE_ROUTES:
        route_value = _object(comparisons[route], f"paired comparisons.{route}")
        _exact_keys(
            route_value,
            (str(fraction) for fraction in MIXED_FRACTIONS),
            f"paired comparisons.{route}",
        )
        result[route] = {}
        for fraction in MIXED_FRACTIONS:
            label = f"paired comparisons.{route}.{fraction}"
            comparison = _object(route_value[str(fraction)], label)
            _exact_keys(
                comparison,
                ("candidate", "paired_ratio", "pairs", "reference"),
                label,
            )
            records = _array(comparison["pairs"], f"{label}.pairs")
            expected_rows = [
                row
                for row in schedule
                if row["route"] == route
                and row["fraction_percent"] == fraction
            ]
            if len(records) != repetitions or len(expected_rows) != repetitions:
                raise EigenPerformanceError(f"{label} repetition coverage differs")
            for index, (record_value, expected) in enumerate(
                zip(records, expected_rows, strict=True)
            ):
                pair = _object(record_value, f"{label}.pairs[{index}]")
                _exact_keys(
                    pair,
                    (
                        "candidate_cpu_ns",
                        "candidate_wall_ns",
                        "order",
                        "reference_cpu_ns",
                        "reference_wall_ns",
                        "repetition",
                    ),
                    f"{label}.pairs[{index}]",
                )
                if (
                    pair["order"] != expected["order"]
                    or pair["repetition"] != expected["repetition"]
                ):
                    raise EigenPerformanceError(f"{label} schedule differs")
                _positive_integer(
                    pair["candidate_wall_ns"], f"{label}.candidate_wall_ns"
                )
                _positive_integer(
                    pair["reference_wall_ns"], f"{label}.reference_wall_ns"
                )
                for cpu_key in ("candidate_cpu_ns", "reference_cpu_ns"):
                    cpu_value = pair[cpu_key]
                    if (
                        isinstance(cpu_value, bool)
                        or not isinstance(cpu_value, int)
                        or cpu_value < 0
                    ):
                        raise EigenPerformanceError(
                            f"{label}.{cpu_key} must be a nonnegative integer"
                        )
            recomputed = _paired_comparison(records)
            if comparison != recomputed:
                raise EigenPerformanceError(f"{label} summary does not recompute")
            result[route][fraction] = _positive_metric(
                recomputed["paired_ratio"]["median"],
                f"{label} median paired ratio",
            )
    return result


def _positive_metric(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise EigenPerformanceError(f"{label} must be numeric")
    made = float(value)
    if not math.isfinite(made) or made <= 0.0:
        raise EigenPerformanceError(f"{label} must be finite and positive")
    return made


def _hot_path_metrics(records: Mapping[str, dict[str, Any]]) -> dict[str, float]:
    paired_record = records.get("PERFORMANCE_PAIRED")
    if paired_record is not None:
        paired_diagnostics = _object(
            paired_record.get("diagnostic_payload"), "hot-path paired diagnostics"
        )
        protocol = _object(
            paired_diagnostics.get("protocol"), "hot-path paired protocol"
        )
        paired_metrics = _validated_paired_metrics(
            paired_record,
            repetitions=_positive_integer(
                protocol.get("repetitions"), "hot-path paired repetitions"
            ),
            warmups_per_route=_positive_integer(
                protocol.get("warmups_per_topology_route"),
                "hot-path paired warmups",
            ),
        )
        assembly_ratios = paired_metrics["assembly"]
    else:
        performance: dict[int, dict[str, Any]] = {}
        for worker_id in LEGACY_PERFORMANCE_WORKER_IDS:
            record = _object(records.get(worker_id), f"hot-path {worker_id}")
            diagnostics = _object(
                record.get("diagnostic_payload"),
                f"hot-path {worker_id} diagnostics",
            )
            fraction = diagnostics.get("fraction_percent")
            if fraction not in PERFORMANCE_FRACTIONS or fraction in performance:
                raise EigenPerformanceError(
                    "hot-path performance fractions are invalid"
                )
            performance[int(fraction)] = diagnostics
        if set(performance) != set(PERFORMANCE_FRACTIONS):
            raise EigenPerformanceError("hot-path performance coverage is incomplete")
        reference_assembly = _positive_metric(
            _object(performance[0].get("assembly"), "all-Q4 assembly").get(
                "median_seconds"
            ),
            "all-Q4 assembly median",
        )
        assembly_ratios = {
            fraction: _positive_metric(
                _object(
                    performance[fraction].get("assembly"),
                    f"mixed {fraction} assembly",
                ).get("median_seconds"),
                f"mixed {fraction} assembly median",
            )
            / reference_assembly
            for fraction in MIXED_FRACTIONS
        }
    batch_record = _object(records.get("BATCH_4096"), "hot-path BATCH_4096")
    benchmark = _object(
        _object(
            batch_record.get("diagnostic_payload"), "hot-path batch diagnostics"
        ).get("benchmark"),
        "hot-path benchmark",
    )
    stiffness = _object(benchmark.get("stiffness"), "hot-path stiffness")
    recovery = _object(benchmark.get("recovery"), "hot-path recovery")
    comparator = _object(
        benchmark.get("qualified_q4_comparator"), "hot-path Q4 comparator"
    )
    result = {
        HOT_PATH_PRIMARY_METRIC: _positive_metric(
            _object(stiffness.get("batch"), "stiffness batch").get(
                "median_seconds"
            ),
            "stiffness batch median",
        )
    }
    for fraction in MIXED_FRACTIONS:
        result[f"mixed_{fraction}_assembly_ratio_to_all_q4"] = assembly_ratios[
            fraction
        ]
    result["s3_stiffness_batch_ratio_to_q4"] = (
        result[HOT_PATH_PRIMARY_METRIC]
        / _positive_metric(
            _object(comparator.get("batch"), "Q4 comparator batch").get(
                "median_seconds"
            ),
            "Q4 comparator median",
        )
    )
    result["s3_stiffness_batch_ratio_to_scalar_fallback"] = (
        result[HOT_PATH_PRIMARY_METRIC]
        / _positive_metric(
            _object(stiffness.get("scalar"), "stiffness scalar").get(
                "median_seconds"
            ),
            "stiffness scalar median",
        )
    )
    result["s3_recovery_batch_ratio_to_scalar_fallback"] = (
        _positive_metric(
            _object(recovery.get("batch"), "recovery batch").get(
                "median_seconds"
            ),
            "recovery batch median",
        )
        / _positive_metric(
            _object(recovery.get("scalar"), "recovery scalar").get(
                "median_seconds"
            ),
            "recovery scalar median",
        )
    )
    expected_order = (
        HOT_PATH_PRIMARY_METRIC,
        *HOT_PATH_DIAGNOSTIC_METRICS,
    )
    if tuple(result) != expected_order:
        raise EigenPerformanceError("hot-path metric ordering changed")
    return result


def _candidate_hot_path_gate(
    authorities: Authorities,
    records: Mapping[str, dict[str, Any]],
) -> tuple[str, dict[str, Any]]:
    required_ids = (
        ("PERFORMANCE_PAIRED", "BATCH_4096")
        if "PERFORMANCE_PAIRED" in records
        else (*LEGACY_PERFORMANCE_WORKER_IDS, "BATCH_4096")
    )
    relevant_statuses: list[str] = []
    for worker_id in required_ids:
        record = records.get(worker_id)
        if record is None:
            return BLOCKED, {"error": f"missing {worker_id}"}
        relevant_statuses.extend(record["common"]["gate_status"].values())
    if BLOCKED in relevant_statuses:
        return BLOCKED, {"error": "a required worker was blocked"}
    if FAIL in relevant_statuses:
        return FAIL, {"error": "a required worker reported a contradiction"}
    try:
        candidate = _hot_path_metrics(records)
        baseline_cycles = [
            _hot_path_metrics(cycle)
            for cycle in authorities.hot_path_baseline_cycles
        ]
    except (KeyError, TypeError, EigenPerformanceError) as error:
        return BLOCKED, {
            "error": str(error),
            "error_type": type(error).__name__,
        }
    maximum_regression = _fraction(
        authorities.input["coverage"]["candidate_hot_path_baseline"]
        ["maximum_regression"],
        "candidate hot-path maximum regression",
    )
    baseline_values = [
        cycle[HOT_PATH_PRIMARY_METRIC] for cycle in baseline_cycles
    ]
    reference = max(baseline_values)
    limit = reference * (1.0 + maximum_regression)
    status = _ratio_gate(candidate[HOT_PATH_PRIMARY_METRIC], limit)
    normalized_diagnostics = {
        metric: {
            "baseline_cycle_values": [cycle[metric] for cycle in baseline_cycles],
            "candidate_value": candidate[metric],
        }
        for metric in HOT_PATH_DIAGNOSTIC_METRICS
    }
    return status, {
        "maximum_regression": maximum_regression,
        "normalized_diagnostics": normalized_diagnostics,
        "primary_metric": {
            "baseline_cycle_values": baseline_values,
            "baseline_envelope": reference,
            "candidate_value": candidate[HOT_PATH_PRIMARY_METRIC],
            "gate_limit": limit,
            "gate_status": status,
            "metric": HOT_PATH_PRIMARY_METRIC,
        },
        "reference_selection": authorities.input["coverage"]
        ["candidate_hot_path_baseline"]["reference_selection"],
        "secondary_guard": authorities.input["coverage"]
        ["candidate_hot_path_baseline"]["secondary_guard"],
    }


def _aggregate(
    authorities: Authorities,
    cycle: int,
    process_results: Sequence[ProcessResult],
) -> tuple[dict[str, Any], dict[str, Any]]:
    if tuple(result.worker_id for result in process_results) != WORKER_IDS:
        raise EigenPerformanceError("aggregate worker order or coverage differs")
    records: dict[str, dict[str, Any]] = {}
    blocked_processes: list[str] = []
    for result in process_results:
        if result.status != "COMPLETE":
            blocked_processes.append(result.worker_id)
            continue
        path = result.directory / "record.json"
        try:
            raw, value = read_canonical(path, pretty=False, label=result.worker_id)
            del raw
            record = validate_worker(value, result.worker_id)
        except (OSError, EigenPerformanceError) as error:
            blocked_processes.append(result.worker_id)
            records[result.worker_id] = {
                "schema": WORKER_SCHEMA,
                "worker_id": result.worker_id,
                "common": {
                    "gate_status": {"record_validation": BLOCKED},
                    "production_restriction": PRODUCTION_RESTRICTION,
                    "worker_id": result.worker_id,
                },
                "diagnostic_payload": {
                    "error": str(error),
                    "error_type": type(error).__name__,
                },
            }
            continue
        if record["authority_sha256"] != sha256(authorities.input_raw):
            blocked_processes.append(result.worker_id)
        records[result.worker_id] = record

    gate_status: dict[str, str] = {}
    modal_statuses: list[str] = []
    for worker_id in WORKER_IDS[:2]:
        record = records.get(worker_id)
        if record is None:
            modal_statuses.append(BLOCKED)
        else:
            modal_statuses.extend(record["common"]["gate_status"].values())
    gate_status["modal"] = (
        BLOCKED
        if BLOCKED in modal_statuses
        else FAIL
        if FAIL in modal_statuses
        else PASS
    )

    buckling_statuses: list[str] = []
    for worker_id in WORKER_IDS[2:4]:
        record = records.get(worker_id)
        if record is None:
            buckling_statuses.append(BLOCKED)
        else:
            buckling_statuses.extend(record["common"]["gate_status"].values())
    gate_status["buckling"] = (
        BLOCKED
        if BLOCKED in buckling_statuses
        else FAIL
        if FAIL in buckling_statuses
        else PASS
    )

    paired_record = records.get("PERFORMANCE_PAIRED")
    rss_records = [records.get(worker_id) for worker_id in SERIAL_RSS_WORKERS]
    performance_complete = bool(
        paired_record is not None
        and paired_record["common"]["gate_status"].get("performance_measurement")
        == PASS
        and all(record is not None for record in rss_records)
        and all(
            record["common"]["gate_status"].get("rss_measurement") == PASS
            for record in rss_records
            if record is not None
        )
    )
    performance_metrics: dict[str, Any] = {}
    if performance_complete:
        try:
            spec = authorities.input["coverage"]["performance"]
            paired_metrics = _validated_paired_metrics(
                paired_record,
                repetitions=int(spec["repetitions"]),
                warmups_per_route=int(spec["warmups_per_route"]),
            )
            rss_by_fraction = {
                int(record["diagnostic_payload"]["fraction_percent"]): record[
                    "diagnostic_payload"
                ]
                for record in rss_records
                if record is not None
            }
            if set(rss_by_fraction) != set(PERFORMANCE_FRACTIONS):
                raise EigenPerformanceError("isolated RSS coverage differs")
            reference_rss = _positive_metric(
                rss_by_fraction[0].get("peak_rss_bytes"), "all-Q4 peak RSS"
            )
            maximum = _fraction(
                authorities.contract["acceptance_gates"]["performance"]
                ["mixed_assembly_solve_rss_regression_maximum"],
                "mixed performance maximum",
            )
            status_values: list[str] = []
            for fraction in MIXED_FRACTIONS:
                assembly_ratio = paired_metrics["assembly"][fraction]
                solve_ratio = paired_metrics["production_end_to_end_solve"][
                    fraction
                ]
                rss_ratio = _positive_metric(
                    rss_by_fraction[fraction].get("peak_rss_bytes"),
                    f"mixed {fraction} peak RSS",
                ) / reference_rss
                statuses = {
                    "assembly": _ratio_gate(assembly_ratio, 1.0 + maximum),
                    "rss": _ratio_gate(rss_ratio, 1.0 + maximum),
                    "solve": _ratio_gate(solve_ratio, 1.0 + maximum),
                }
                status_values.extend(statuses.values())
                performance_metrics[str(fraction)] = {
                    "assembly_paired_median_ratio_to_all_q4": assembly_ratio,
                    "gate_status": statuses,
                    "rss_ratio_to_all_q4": rss_ratio,
                    "solve_paired_median_ratio_to_all_q4": solve_ratio,
                }
            gate_status["mixed_performance"] = (
                BLOCKED
                if BLOCKED in status_values
                else FAIL
                if FAIL in status_values
                else PASS
            )
        except (KeyError, TypeError, EigenPerformanceError) as error:
            gate_status["mixed_performance"] = BLOCKED
            performance_metrics["error"] = {
                "message": str(error),
                "type": type(error).__name__,
            }
    else:
        gate_status["mixed_performance"] = BLOCKED

    batch_record = records.get("BATCH_4096")
    if batch_record is None:
        gate_status["batch"] = BLOCKED
        gate_status["warm_s3_vs_q4"] = BLOCKED
    else:
        batch_status = batch_record["common"]["gate_status"]
        core = [
            batch_status.get("batch_equality", BLOCKED),
            batch_status.get("batch_scalar_fallback", BLOCKED),
            batch_status.get("batch_throughput", BLOCKED),
        ]
        gate_status["batch"] = (
            BLOCKED if BLOCKED in core else FAIL if FAIL in core else PASS
        )
        gate_status["warm_s3_vs_q4"] = batch_status.get(
            "warm_s3_vs_q4", BLOCKED
        )

    (
        gate_status["candidate_hot_path_regression"],
        hot_path_comparison,
    ) = _candidate_hot_path_gate(authorities, records)
    if blocked_processes or BLOCKED in gate_status.values():
        terminal = TERMINALS[0]
    elif FAIL in gate_status.values():
        terminal = TERMINALS[1]
    elif UNEXECUTED in gate_status.values():
        terminal = TERMINALS[2]
    else:
        terminal = TERMINALS[3]

    common = {
        "authority_sha256": sha256(authorities.input_raw),
        "coverage": {
            "batch_element_count": 4096,
            "fractions_percent": [0, 10, 25],
            "level": 20,
            "modal_elastic_mode_count": 10,
            "buckling_factor_count": 5,
            "performance_repetitions": PAIRED_REPETITIONS,
            "registered_scope_only": True,
            "worker_ids": list(WORKER_IDS),
        },
        "gate_status": gate_status,
        "production_restriction": PRODUCTION_RESTRICTION,
        "schema": COMMON_SCHEMA,
        "terminal": terminal,
    }
    diagnostics = {
        "blocked_processes": blocked_processes,
        "common_sha256": sha256(canonical_bytes(common)),
        "cycle": int(cycle),
        "candidate_hot_path_comparison": hot_path_comparison,
        "performance_comparison": performance_metrics,
        "processes": [_process_diagnostic(result) for result in process_results],
        "schema": DIAGNOSTIC_SCHEMA,
        "workers": {
            worker_id: records.get(worker_id, {}).get("diagnostic_payload")
            for worker_id in WORKER_IDS
        },
    }
    _finite_tree(common, "common aggregate")
    _finite_tree(diagnostics, "diagnostic aggregate")
    return common, diagnostics


def run_cycle(
    authorities: Authorities,
    output_root: Path,
    *,
    cycle: int,
) -> tuple[bytes, dict[str, Any], dict[str, Any]]:
    if cycle not in (1, 2):
        raise EigenPerformanceError("cycle must be 1 or 2")
    output_root = Path(output_root)
    if output_root.exists():
        raise EigenPerformanceError("cycle output root must be fresh")
    output_root.mkdir(parents=True, exist_ok=False)
    parallel = _run_worker_set(
        authorities,
        PARALLEL_WORKERS,
        cycle_root=output_root,
        parallel=True,
    )
    performance = _run_worker_set(
        authorities,
        SERIAL_PERFORMANCE_WORKERS,
        cycle_root=output_root,
        parallel=False,
    )
    rss = _run_worker_set(
        authorities,
        SERIAL_RSS_WORKERS,
        cycle_root=output_root,
        parallel=False,
    )
    batch = _run_worker_set(
        authorities,
        SERIAL_BATCH_WORKERS,
        cycle_root=output_root,
        parallel=False,
    )
    by_id = {
        row.worker_id: row
        for row in (*parallel, *performance, *rss, *batch)
    }
    ordered = [by_id[worker_id] for worker_id in WORKER_IDS]
    common, diagnostics = _aggregate(authorities, cycle, ordered)
    common_path = output_root / "common.json"
    diagnostic_path = output_root / "diagnostic.json"
    write_exclusive(common_path, common)
    write_exclusive(diagnostic_path, diagnostics)
    return common_path.read_bytes(), common, diagnostics


def run_two_cycles(authorities: Authorities, output_root: Path) -> dict[str, Any]:
    output_root = Path(output_root)
    if output_root.exists():
        raise EigenPerformanceError("two-cycle output root must be fresh")
    output_root.mkdir(parents=True, exist_ok=False)
    first_raw, first, _first_diagnostics = run_cycle(
        authorities,
        output_root / "cycle-1",
        cycle=1,
    )
    second_raw, second, _second_diagnostics = run_cycle(
        authorities,
        output_root / "cycle-2",
        cycle=2,
    )
    agreement = bool(first_raw == second_raw)
    value = {
        "authority_sha256": sha256(authorities.input_raw),
        "common_aggregate_sha256": sha256(first_raw),
        "cycles_byte_identical": agreement,
        "production_restriction": PRODUCTION_RESTRICTION,
        "schema": TWO_CYCLE_SCHEMA,
        "terminal": (
            first["terminal"]
            if agreement and first == second
            else TERMINALS[0]
        ),
    }
    write_exclusive(output_root / "two-cycle-common.json", value)
    return value


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--worker", choices=WORKER_IDS)
    parser.add_argument("--run-cycle", type=int, choices=(1, 2))
    parser.add_argument("--run-two-cycles", action="store_true")
    arguments = parser.parse_args(argv)
    selected = sum(
        (
            arguments.worker is not None,
            arguments.run_cycle is not None,
            bool(arguments.run_two_cycles),
        )
    )
    if selected != 1:
        parser.error("select exactly one of --worker, --run-cycle, --run-two-cycles")
    authorities = load_authorities(arguments.input)
    if arguments.worker is not None:
        if arguments.output is None or arguments.output_root is not None:
            parser.error("--worker requires --output only")
        write_exclusive(arguments.output, run_worker(authorities, arguments.worker))
        return 0
    if arguments.output_root is None or arguments.output is not None:
        parser.error("cycle execution requires --output-root only")
    if arguments.run_cycle is not None:
        run_cycle(authorities, arguments.output_root, cycle=arguments.run_cycle)
        return 0
    run_two_cycles(authorities, arguments.output_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
