"""Run and validate the frozen E4-PL Q1M burn-in gates.

The resource-heavy ``functional`` and ``performance`` lanes must be invoked
only after the repository resource manager has approved and acquired their
registered request.  This script deliberately does not mutate that manager.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import os
import re
import shutil
import stat
import statistics
import subprocess
import sys
import tempfile
import tomllib
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
TESTS = ROOT / "tests"
CONTRACT_PATH = ROOT / "docs" / "reference_cases" / "e4_pl_q1m_burnin_contract.json"

QUICK = {
    "test_e4_pl_burnin.py",
    "test_e4_pl_default_activation.py",
    "test_e4_pl_dormant_element.py",
    "test_e4_pl_functional_constructor_policy.py",
    "test_e4_pl_parity_matrix.py",
    "test_e4_pl_warped_qualification.py",
    "test_e4_pl_workflow_parity.py",
}

PERFORMANCE_TOKENS = (
    "_batch",
    "performance",
    "sol_ultra",
    "threading_policy",
    "vectorized",
)

PERFORMANCE_EXACT = {
    "test_analysis_session.py",
    "test_contact_work_buffer.py",
    "test_experimental_csr_assembly.py",
    "test_impact_reduced_assembly.py",
    "test_impact_tangent_reuse.py",
    "test_recovery_batches.py",
}

EXTENDED_PREFIXES = (
    "test_e3_",
    "test_e4_pl_q1",
    "test_s4_candidate_",
    "test_s4_e2_",
    "test_s4_eq21_",
    "test_s4_geometry_handoff",
    "test_s4_improved_",
    "test_s4_nullspace_",
    "test_s4_restricted_",
    "test_s4_stage_m_",
)

EXTENDED_EXACT = {
    "test_e4_baseline.py",
    "test_e4_closeout.py",
    "test_e4_core_identity.py",
    "test_e4_pl_identity.py",
    "test_e4_route.py",
    "test_e4_ws_feasibility.py",
    "test_s4_drill_constraint_derivation.py",
}

PACKAGE_CHECKS = (
    "BUILD_LOCAL_WHEELS_WITHOUT_ISOLATION",
    "INSTALL_FRESH_TARGET_WITHOUT_DEPENDENCY_RESOLUTION",
    "REJECT_SOURCE_TREE_IMPORTS",
    "VERIFY_QUALIFIED_Q4_DEFAULT",
    "VERIFY_NON_Q4_PRESERVATION",
    "VERIFY_DIAGNOSTICS_EXPORT",
    "VERIFY_EXPLICIT_LEGACY_WARNING",
)

GATE_LANES = ("quick", "package", "functional", "anyfem", "performance")
SIBLING_NAMES = ("ANYfem", "ANYmesh", "ANYgeometry", "ANYmaterial", "ANYfileIO")
LOCAL_DISTRIBUTIONS = (
    ("ANYgeometry", "ANYgeometry", "anygeometry"),
    ("ANYmaterial", "ANYmaterial", "anymaterial"),
    ("ANYmesh", "ANYmesher", "anymesher"),
    ("ANYfileIO", "ANYfileio", "anyfileio"),
    ("ANYsolver", "ANYsolver", "anysolver"),
)

SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
GIT_OBJECT_RE = re.compile(r"[0-9a-f]{40}\Z")
REQUEST_ID_RE = re.compile(r"[0-9a-f]{32}\Z")
UTC_RE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z\Z")
PROJECT_NAME_RE = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?\Z")
PROJECT_VERSION_RE = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9._+-]*[A-Za-z0-9])?\Z")
PERFORMANCE_OBSERVATION_SCHEMA = (
    "anysolver.s4.e4-pl-q1m-performance-observation-v1"
)
PERFORMANCE_BASELINE_MARKER = b"Q1M_PERFORMANCE_BASELINE_JSON="


class EvidenceError(ValueError):
    """Raised when a Q1M contract or gate record is not strict/canonical."""


def classify_test(path: Path) -> str:
    """Return the single burn-in lane for a test file."""

    name = path.name
    if name in QUICK:
        return "quick"
    if name in PERFORMANCE_EXACT or any(token in name for token in PERFORMANCE_TOKENS):
        return "performance"
    if name in EXTENDED_EXACT or name.startswith(EXTENDED_PREFIXES):
        return "extended"
    return "functional"


def inventory() -> dict[str, list[str]]:
    result = {lane: [] for lane in ("quick", "functional", "performance", "extended")}
    for path in sorted(TESTS.glob("test_*.py")):
        result[classify_test(path)].append(path.relative_to(ROOT).as_posix())
    return result


def gate_inventories() -> dict[str, list[str]]:
    """Return the exact evidence inventory for all five required gate lanes."""

    lanes = inventory()
    return {
        "quick": lanes["quick"],
        "package": list(PACKAGE_CHECKS),
        "functional": lanes["functional"],
        "anyfem": [
            "tests/test_e4_pl_default_routing.py",
            "tests/test_verification.py",
        ],
        "performance": lanes["performance"],
    }


def _reject_constant(value: str) -> None:
    raise EvidenceError(f"non-finite JSON number is forbidden: {value}")


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise EvidenceError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def strict_json_loads(raw: str | bytes) -> Any:
    """Decode JSON while rejecting duplicate keys and non-finite numbers."""

    if isinstance(raw, bytes):
        try:
            raw = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise EvidenceError("JSON must be UTF-8") from exc
    try:
        value = json.loads(
            raw,
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
        )
    except json.JSONDecodeError as exc:
        raise EvidenceError(f"invalid JSON: {exc.msg}") from exc
    _reject_nonfinite(value)
    return value


def strict_json_load(path: Path) -> Any:
    if not path.is_file() or path.is_symlink():
        raise EvidenceError(f"JSON input must be a regular non-symlink file: {path}")
    return strict_json_loads(path.read_bytes())


def _reject_nonfinite(value: Any, location: str = "$") -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise EvidenceError(f"non-finite value at {location}")
    if isinstance(value, dict):
        for key, child in value.items():
            _reject_nonfinite(child, f"{location}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_nonfinite(child, f"{location}[{index}]")


def canonical_json_bytes(value: Any) -> bytes:
    _reject_nonfinite(value)
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
        + "\n"
    ).encode("utf-8")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def file_hash_record(path: Path) -> dict[str, Any]:
    """Return the canonical byte count/hash for a regular external artifact."""

    if not path.is_file() or path.is_symlink():
        raise EvidenceError(f"artifact must be a regular non-symlink file: {path}")
    return {"bytes": path.stat().st_size, "sha256": _sha256_file(path)}


def wheel_hash_record(path: Path) -> dict[str, Any]:
    record = file_hash_record(path)
    if path.name != str(path.name) or not path.name.endswith(".whl"):
        raise EvidenceError("wheel artifact must have a .whl basename")
    return {"bytes": record["bytes"], "filename": path.name, "sha256": record["sha256"]}


def _exact_keys(value: Any, expected: set[str], location: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise EvidenceError(f"{location} must be an object")
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise EvidenceError(f"{location} keys mismatch; missing={missing}, extra={extra}")
    return value


def _require_bool(value: Any, location: str) -> bool:
    if type(value) is not bool:
        raise EvidenceError(f"{location} must be a boolean")
    return value


def _require_int(value: Any, location: str, *, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        raise EvidenceError(f"{location} must be an integer >= {minimum}")
    return value


def _require_match(value: Any, pattern: re.Pattern[str], location: str) -> str:
    if not isinstance(value, str) or pattern.fullmatch(value) is None:
        raise EvidenceError(f"{location} has invalid format")
    return value


def _require_timestamp(value: Any, location: str) -> dt.datetime:
    raw = _require_match(value, UTC_RE, location)
    try:
        parsed = dt.datetime.fromisoformat(raw[:-1] + "+00:00")
    except ValueError as exc:
        raise EvidenceError(f"{location} is not a valid UTC timestamp") from exc
    return parsed


def _validate_hash_record(value: Any, location: str, *, allow_empty: bool = True) -> None:
    value = _exact_keys(value, {"bytes", "sha256"}, location)
    minimum = 0 if allow_empty else 1
    _require_int(value["bytes"], f"{location}.bytes", minimum=minimum)
    _require_match(value["sha256"], SHA256_RE, f"{location}.sha256")
    if value["bytes"] == 0 and value["sha256"] != hashlib.sha256(b"").hexdigest():
        raise EvidenceError(f"{location} has the wrong SHA-256 for empty content")


def _validate_process_record(
    value: Any, location: str, *, allow_empty: bool = True
) -> None:
    value = _exact_keys(value, {"bytes", "returncode", "sha256"}, location)
    _require_int(value["returncode"], f"{location}.returncode")
    if value["returncode"] != 0:
        raise EvidenceError(f"{location}.returncode must be zero")
    _validate_hash_record(
        {"bytes": value["bytes"], "sha256": value["sha256"]},
        location,
        allow_empty=allow_empty,
    )


def validate_package_result(
    value: Any, *, contract: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    """Validate the canonical installed-wheel package result."""

    contract = dict(_load_contract() if contract is None else contract)
    value = _exact_keys(
        value,
        {
            "build_logs",
            "install_log",
            "schema",
            "smoke",
            "smoke_log",
            "sources",
            "status",
            "wheels",
        },
        "$package",
    )
    if value["schema"] != contract["package_result_schema"]:
        raise EvidenceError("package result schema mismatch")
    if value["status"] != "PASS":
        raise EvidenceError("package result status must be PASS")
    names = {name for name, _distribution, _package in LOCAL_DISTRIBUTIONS}
    logs = _exact_keys(value["build_logs"], names, "$package.build_logs")
    for name in names:
        _validate_process_record(logs[name], f"$package.build_logs.{name}", allow_empty=False)
    _validate_process_record(value["install_log"], "$package.install_log", allow_empty=False)
    _validate_hash_record(value["smoke_log"], "$package.smoke_log", allow_empty=False)

    sources = _exact_keys(value["sources"], names, "$package.sources")
    for name in names:
        location = f"$package.sources.{name}"
        source = _exact_keys(
            sources[name],
            {"archive", "archive_log", "commit", "content", "tree"},
            location,
        )
        _require_match(source["commit"], GIT_OBJECT_RE, f"{location}.commit")
        _require_match(source["tree"], GIT_OBJECT_RE, f"{location}.tree")
        _validate_hash_record(source["archive"], f"{location}.archive", allow_empty=False)
        _validate_process_record(source["archive_log"], f"{location}.archive_log")
        content = _exact_keys(source["content"], {"files", "sha256"}, f"{location}.content")
        _require_int(content["files"], f"{location}.content.files", minimum=1)
        _require_match(content["sha256"], SHA256_RE, f"{location}.content.sha256")

    wheels = _exact_keys(value["wheels"], names, "$package.wheels")
    for name in names:
        wheel = _exact_keys(
            wheels[name], {"bytes", "filename", "sha256"}, f"$package.wheels.{name}"
        )
        if (
            not isinstance(wheel["filename"], str)
            or Path(wheel["filename"]).name != wheel["filename"]
            or not wheel["filename"].endswith(".whl")
        ):
            raise EvidenceError(f"$package.wheels.{name}.filename is invalid")
        _require_int(wheel["bytes"], f"$package.wheels.{name}.bytes", minimum=1)
        _require_match(wheel["sha256"], SHA256_RE, f"$package.wheels.{name}.sha256")

    smoke = _exact_keys(
        value["smoke"],
        {"diagnostics_schema", "legacy_warning", "non_q4_types", "origins", "q4_type"},
        "$package.smoke",
    )
    if smoke["diagnostics_schema"] != contract["diagnostics_schema"]:
        raise EvidenceError("package diagnostics schema mismatch")
    if smoke["legacy_warning"] != contract["legacy_q4"]["warning"]:
        raise EvidenceError("package legacy warning mismatch")
    if smoke["q4_type"] != "QualifiedE4PLShellElement":
        raise EvidenceError("package Q4 type mismatch")
    if smoke["non_q4_types"] != [
        "ShellElement",
        "ShellElement",
        "ShellElement",
        "ShellElement",
    ]:
        raise EvidenceError("package non-Q4 type preservation mismatch")
    expected_packages = {package for _name, _distribution, package in LOCAL_DISTRIBUTIONS}
    origins = _exact_keys(smoke["origins"], expected_packages, "$package.smoke.origins")
    for package, origin in origins.items():
        if (
            not isinstance(origin, str)
            or PurePosixPath(origin).is_absolute()
            or ".." in PurePosixPath(origin).parts
            or PurePosixPath(origin).parts[0] != package
        ):
            raise EvidenceError(f"package origin is invalid for {package}")
    return value


def _validate_timing_summary(
    value: Any,
    location: str,
    *,
    repetitions: int,
) -> None:
    value = _exact_keys(
        value,
        {"mad_ns", "median_ns", "p95_ns", "samples_ns"},
        location,
    )
    samples = value["samples_ns"]
    if not isinstance(samples, list) or len(samples) != repetitions:
        raise EvidenceError(f"{location}.samples_ns must contain {repetitions} samples")
    for index, sample in enumerate(samples):
        _require_int(sample, f"{location}.samples_ns[{index}]")
    ordered = sorted(samples)
    median_ns = int(statistics.median(ordered))
    mad_ns = int(statistics.median(abs(sample - median_ns) for sample in ordered))
    p95_index = max(0, math.ceil(0.95 * len(ordered)) - 1)
    expected = {
        "mad_ns": mad_ns,
        "median_ns": median_ns,
        "p95_ns": int(ordered[p95_index]),
    }
    for key, expected_value in expected.items():
        if _require_int(value[key], f"{location}.{key}") != expected_value:
            raise EvidenceError(f"{location}.{key} does not match its timing samples")


def _validate_performance_evidence(
    hard_gates: Any,
    baseline: Any,
    *,
    contract: Mapping[str, Any],
    lanes: Mapping[str, Any] | None = None,
) -> bool:
    expected_gates = contract["hard_performance_gates"]
    hard_gates = _exact_keys(hard_gates, set(expected_gates), "$.hard_gates")
    all_pass = True
    inventories = gate_inventories()
    for name in sorted(expected_gates):
        location = f"$.hard_gates.{name}"
        gate = _exact_keys(
            hard_gates[name],
            {"evidence_nodes", "observed", "status"},
            location,
        )
        if gate["evidence_nodes"] != expected_gates[name]:
            raise EvidenceError(f"{location}.evidence_nodes does not match the contract")
        observed = _require_bool(gate["observed"], f"{location}.observed")
        expected_status = "PASS" if observed else "FAIL"
        if gate["status"] != expected_status:
            raise EvidenceError(f"{location}.status contradicts observed")
        all_pass = all_pass and observed
        for node in gate["evidence_nodes"]:
            if not isinstance(node, str) or "::" not in node:
                raise EvidenceError(f"{location}.evidence_nodes contains an invalid node")
            test_path = node.split("::", 1)[0]
            matching_lanes = [
                lane for lane, paths in inventories.items() if test_path in paths
            ]
            if len(matching_lanes) != 1:
                raise EvidenceError(f"{location} evidence node has no unique gate lane")
            if lanes is not None and lanes[matching_lanes[0]]["status"] != "PASS":
                raise EvidenceError(f"{location} cannot pass when its evidence lane failed")

    expected_baseline = contract["performance_baseline"]
    baseline = _exact_keys(
        baseline,
        {"measurements", "repetitions", "schema", "speed_claim", "warmups"},
        "$.performance_baseline",
    )
    for key in ("repetitions", "schema", "speed_claim", "warmups"):
        if baseline[key] != expected_baseline[key]:
            raise EvidenceError(f"$.performance_baseline.{key} does not match the contract")
    repetitions = _require_int(
        baseline["repetitions"], "$.performance_baseline.repetitions", minimum=1
    )
    _require_int(baseline["warmups"], "$.performance_baseline.warmups", minimum=1)
    measurements = _exact_keys(
        baseline["measurements"],
        set(expected_baseline["measurement_names"]),
        "$.performance_baseline.measurements",
    )
    for name in expected_baseline["measurement_names"]:
        _validate_timing_summary(
            measurements[name],
            f"$.performance_baseline.measurements.{name}",
            repetitions=repetitions,
        )
    return all_pass


def extract_performance_observation(path: Path) -> dict[str, Any]:
    """Extract the single strict Q1M observation from a performance log."""

    if not path.is_file() or path.is_symlink():
        raise EvidenceError(f"performance log must be a regular non-symlink file: {path}")
    payloads = [
        line[len(PERFORMANCE_BASELINE_MARKER) :]
        for line in path.read_bytes().splitlines()
        if line.startswith(PERFORMANCE_BASELINE_MARKER)
    ]
    if len(payloads) != 1:
        raise EvidenceError("performance log must contain exactly one Q1M baseline marker")
    observation = _exact_keys(
        strict_json_loads(payloads[0]),
        {"hard_gates", "performance_baseline", "schema"},
        "$performance_observation",
    )
    if observation["schema"] != PERFORMANCE_OBSERVATION_SCHEMA:
        raise EvidenceError("performance observation schema mismatch")
    return observation


def _load_contract() -> dict[str, Any]:
    contract = strict_json_load(CONTRACT_PATH)
    if not isinstance(contract, dict):
        raise EvidenceError("Q1M contract must be an object")
    return contract


def validate_gate_result(
    record: Any,
    *,
    contract: Mapping[str, Any] | None = None,
    repository_paths: Mapping[str, Path] | None = None,
    lane_log_paths: Mapping[str, Path] | None = None,
    package_result_path: Path | None = None,
    request_paths: Mapping[str, Path] | None = None,
    wheel_path: Path | None = None,
) -> dict[str, Any]:
    """Validate a prospective Q1M gate result without creating evidence.

    Passing ``repository_paths`` enables the final clean-tree and Git-object
    identity check. Its keys must name ANYsolver and all five siblings.
    """

    contract = dict(_load_contract() if contract is None else contract)
    required_top_keys = {
        "candidate",
        "clean_gate_index",
        "lanes",
        "legacy_removal_authorized",
        "production_boundary",
        "resource_requests",
        "rollback",
        "schema",
        "siblings",
    }
    optional_top_keys = {
        "hard_gates",
        "package_result",
        "performance_baseline",
        "wheel",
    }
    if not isinstance(record, dict):
        raise EvidenceError("$ must be an object")
    missing = required_top_keys - set(record)
    extra = set(record) - required_top_keys - optional_top_keys
    if missing or extra:
        raise EvidenceError(
            f"$ keys mismatch; missing={sorted(missing)}, extra={sorted(extra)}"
        )
    if record["schema"] != contract["gate_result_schema"]:
        raise EvidenceError("$.schema does not match the contract")

    candidate = _exact_keys(
        record["candidate"], {"clean", "commit", "repository", "tree"}, "$.candidate"
    )
    if candidate["repository"] != "ANYsolver":
        raise EvidenceError("$.candidate.repository must be ANYsolver")
    if not _require_bool(candidate["clean"], "$.candidate.clean"):
        raise EvidenceError("the candidate repository must be clean")
    _require_match(candidate["commit"], GIT_OBJECT_RE, "$.candidate.commit")
    _require_match(candidate["tree"], GIT_OBJECT_RE, "$.candidate.tree")

    siblings = _exact_keys(record["siblings"], set(SIBLING_NAMES), "$.siblings")
    for name in SIBLING_NAMES:
        identity = _exact_keys(
            siblings[name], {"clean", "commit", "tree"}, f"$.siblings.{name}"
        )
        if not _require_bool(identity["clean"], f"$.siblings.{name}.clean"):
            raise EvidenceError(f"sibling repository {name} must be clean")
        _require_match(identity["commit"], GIT_OBJECT_RE, f"$.siblings.{name}.commit")
        _require_match(identity["tree"], GIT_OBJECT_RE, f"$.siblings.{name}.tree")
    sibling_authority = contract.get("sibling_authority")
    if sibling_authority is None:
        # Immutable cycle-0/1/2 authorities predate the complete sibling
        # graph and bind the paired adapter commit directly.
        if siblings["ANYfem"]["commit"] != contract["anyfem_commit"]:
            raise EvidenceError("ANYfem commit does not match the contract")
    else:
        sibling_authority = _exact_keys(
            sibling_authority,
            set(SIBLING_NAMES),
            "$.contract.sibling_authority",
        )
        for name in SIBLING_NAMES:
            expected = _exact_keys(
                sibling_authority[name],
                {"commit", "tree"},
                f"$.contract.sibling_authority.{name}",
            )
            _require_match(
                expected["commit"],
                GIT_OBJECT_RE,
                f"$.contract.sibling_authority.{name}.commit",
            )
            _require_match(
                expected["tree"],
                GIT_OBJECT_RE,
                f"$.contract.sibling_authority.{name}.tree",
            )
            if siblings[name]["commit"] != expected["commit"]:
                raise EvidenceError(
                    f"sibling repository {name} commit does not match the contract"
                )
            if siblings[name]["tree"] != expected["tree"]:
                raise EvidenceError(
                    f"sibling repository {name} tree does not match the contract"
                )
        if contract.get("anyfem_commit") != sibling_authority["ANYfem"]["commit"]:
            raise EvidenceError("ANYfem authority aliases disagree")

    expected_requests = contract["resource_requests"]
    requests = record["resource_requests"]
    if not isinstance(requests, list) or len(requests) != len(expected_requests):
        raise EvidenceError("$.resource_requests must contain every contracted request")
    seen_ids: set[str] = set()
    seen_lanes: set[str] = set()
    for index, request in enumerate(requests):
        location = f"$.resource_requests[{index}]"
        request = _exact_keys(
            request, {"lane", "request_id", "request_sha256"}, location
        )
        lane = request["lane"]
        if lane not in expected_requests:
            raise EvidenceError(f"{location}.lane is not contracted")
        request_id = _require_match(
            request["request_id"], REQUEST_ID_RE, f"{location}.request_id"
        )
        _require_match(request["request_sha256"], SHA256_RE, f"{location}.request_sha256")
        if request_id in seen_ids or lane in seen_lanes:
            raise EvidenceError("resource request IDs and lanes must be unique")
        seen_ids.add(request_id)
        seen_lanes.add(lane)
        if request_id != expected_requests[lane]["request_id"]:
            raise EvidenceError(f"{location}.request_id does not match the contract")
        if request["request_sha256"] != expected_requests[lane]["request_sha256"]:
            raise EvidenceError(f"{location}.request_sha256 does not match the contract")
    if seen_lanes != set(expected_requests):
        raise EvidenceError("resource request lanes are incomplete")

    lanes = _exact_keys(record["lanes"], set(GATE_LANES), "$.lanes")
    expected_inventories = gate_inventories()
    all_pass = True
    statuses: list[str] = []
    for lane in GATE_LANES:
        location = f"$.lanes.{lane}"
        raw_result = lanes[lane]
        if not isinstance(raw_result, dict) or raw_result.get("status") not in {
            "PASS",
            "FAIL",
            "NOT_RUN",
        }:
            raise EvidenceError(f"{location}.status must be PASS, FAIL, or NOT_RUN")
        status = raw_result["status"]
        base_keys = {
            "command_sha256",
            "inventory",
            "resource_request_id",
            "status",
        }
        result = _exact_keys(
            raw_result,
            base_keys
            if status == "NOT_RUN"
            else base_keys | {"exit_code", "finished_at_utc", "log", "started_at_utc"},
            location,
        )
        statuses.append(status)
        if status == "NOT_RUN":
            all_pass = False
        else:
            exit_code = _require_int(result["exit_code"], f"{location}.exit_code")
            if (status == "PASS") != (exit_code == 0):
                raise EvidenceError(f"{location}.exit_code contradicts status")
            all_pass = all_pass and status == "PASS"
            started = _require_timestamp(result["started_at_utc"], f"{location}.started_at_utc")
            finished = _require_timestamp(result["finished_at_utc"], f"{location}.finished_at_utc")
            if finished < started:
                raise EvidenceError(f"{location} finishes before it starts")
            _validate_hash_record(result["log"], f"{location}.log", allow_empty=False)
        _require_match(
            result["command_sha256"], SHA256_RE, f"{location}.command_sha256"
        )
        expected_command_sha256 = (
            contract["non_resource_commands"][lane]["command_sha256"]
            if lane in contract["non_resource_commands"]
            else expected_requests[lane]["command_sha256"]
        )
        if result["command_sha256"] != expected_command_sha256:
            raise EvidenceError(f"$.lanes.{lane}.command_sha256 does not match authority")
        if result["inventory"] != expected_inventories[lane]:
            raise EvidenceError(f"{location}.inventory does not match discovery")
        expected_id = None if lane in {"quick", "package"} else expected_requests[lane]["request_id"]
        if result["resource_request_id"] != expected_id:
            raise EvidenceError(f"{location}.resource_request_id is invalid")

    failed_indices = [index for index, status in enumerate(statuses) if status == "FAIL"]
    if failed_indices:
        if len(failed_indices) != 1:
            raise EvidenceError("a fail-fast result must contain exactly one failed lane")
        failed_index = failed_indices[0]
        if statuses[:failed_index] != ["PASS"] * failed_index or statuses[failed_index + 1 :] != [
            "NOT_RUN"
        ] * (len(statuses) - failed_index - 1):
            raise EvidenceError("lane statuses violate fail-fast execution order")
    elif "NOT_RUN" in statuses:
        raise EvidenceError("NOT_RUN lanes require one preceding failed lane")

    if lanes["performance"]["status"] == "PASS":
        if not {"hard_gates", "performance_baseline"} <= set(record):
            raise EvidenceError("successful performance lane requires its exact evidence")
        hard_gates_pass = _validate_performance_evidence(
            record["hard_gates"],
            record["performance_baseline"],
            contract=contract,
            lanes=lanes,
        )
        all_pass = all_pass and hard_gates_pass
    elif {"hard_gates", "performance_baseline"} & set(record):
        raise EvidenceError("performance evidence is forbidden when the lane did not pass")

    wheel: dict[str, Any] | None = None
    if lanes["package"]["status"] == "PASS":
        if not {"package_result", "wheel"} <= set(record):
            raise EvidenceError("successful package lane requires result and wheel identities")
        wheel = _exact_keys(record["wheel"], {"bytes", "filename", "sha256"}, "$.wheel")
        if not isinstance(wheel["filename"], str) or not wheel["filename"].endswith(".whl"):
            raise EvidenceError("$.wheel.filename must be a wheel basename")
        if Path(wheel["filename"]).name != wheel["filename"]:
            raise EvidenceError("$.wheel.filename must not contain a path")
        _require_int(wheel["bytes"], "$.wheel.bytes", minimum=1)
        _require_match(wheel["sha256"], SHA256_RE, "$.wheel.sha256")
        _validate_hash_record(record["package_result"], "$.package_result", allow_empty=False)
    elif {"package_result", "wheel"} & set(record):
        raise EvidenceError("package artifacts are forbidden when the lane did not pass")

    rollback = _exact_keys(record["rollback"], {"state", "unresolved_incidents"}, "$.rollback")
    incidents = rollback["unresolved_incidents"]
    if not isinstance(incidents, list) or any(
        not isinstance(item, str) or not item for item in incidents
    ):
        raise EvidenceError("$.rollback.unresolved_incidents must be a string list")
    if len(incidents) != len(set(incidents)):
        raise EvidenceError("rollback incidents must be unique")
    expected_rollback_state = (
        "NO_UNRESOLVED_ROLLBACK_INCIDENT"
        if not incidents
        else "UNRESOLVED_LEGACY_Q4_ROLLBACK_INCIDENT"
    )
    if rollback["state"] != expected_rollback_state:
        raise EvidenceError("$.rollback.state contradicts unresolved incidents")
    if not all_pass and not incidents:
        raise EvidenceError("a failed required gate must record a rollback incident")

    expected_gate_index = 1 if all_pass and not incidents else 0
    if _require_int(record["clean_gate_index"], "$.clean_gate_index") != expected_gate_index:
        raise EvidenceError("$.clean_gate_index contradicts lane/rollback state")
    if _require_bool(record["legacy_removal_authorized"], "$.legacy_removal_authorized"):
        raise EvidenceError("Q1M gate 1 cannot authorize legacy removal")

    boundary = _exact_keys(
        record["production_boundary"],
        {"default", "legacy_q4_available_through", "mechanics_changed", "removal_not_before"},
        "$.production_boundary",
    )
    if boundary != contract["production_boundary"]:
        raise EvidenceError("$.production_boundary does not match the Q1M contract")
    if _require_bool(boundary["mechanics_changed"], "$.production_boundary.mechanics_changed"):
        raise EvidenceError("Q1M may not change qualified Q4 mechanics")

    if repository_paths is not None:
        _validate_repository_identities(record, repository_paths)
    if lane_log_paths is not None:
        executed_lanes = {
            lane for lane in GATE_LANES if lanes[lane]["status"] != "NOT_RUN"
        }
        if set(lane_log_paths) != executed_lanes:
            raise EvidenceError("lane_log_paths must name exactly the executed gate lanes")
        for lane in executed_lanes:
            if file_hash_record(Path(lane_log_paths[lane])) != lanes[lane]["log"]:
                raise EvidenceError(f"external log mismatch for lane {lane}")
        if lanes["performance"]["status"] == "PASS":
            observation = extract_performance_observation(
                Path(lane_log_paths["performance"])
            )
            if observation["hard_gates"] != record["hard_gates"]:
                raise EvidenceError("performance hard gates do not match their external log")
            if observation["performance_baseline"] != record["performance_baseline"]:
                raise EvidenceError("performance baseline does not match its external log")
    if request_paths is not None:
        if set(request_paths) != set(expected_requests):
            raise EvidenceError("request_paths must name every resource lane")
        for lane, expected in expected_requests.items():
            path = Path(request_paths[lane])
            if path.name != f"{expected['request_id']}.json":
                raise EvidenceError(f"request filename mismatch for lane {lane}")
            if file_hash_record(path)["sha256"] != expected["request_sha256"]:
                raise EvidenceError(f"immutable request hash mismatch for lane {lane}")
            request = strict_json_load(path)
            if not isinstance(request, dict) or request.get("request_id") != expected["request_id"]:
                raise EvidenceError(f"immutable request identity mismatch for lane {lane}")
            command = request.get("command")
            if not isinstance(command, str) or _sha256_bytes(command.encode("utf-8")) != expected[
                "command_sha256"
            ]:
                raise EvidenceError(f"immutable request command mismatch for lane {lane}")
    if lanes["package"]["status"] == "PASS" and package_result_path is not None:
        package_path = Path(package_result_path)
        package_value = strict_json_load(package_path)
        package_raw = package_path.read_bytes()
        package = validate_package_result(package_value, contract=contract)
        if package_raw != canonical_json_bytes(package):
            raise EvidenceError("package result is not canonical JSON")
        if file_hash_record(package_path) != record["package_result"]:
            raise EvidenceError("package result identity mismatch")
        expected_source_identities = {
            "ANYsolver": record["candidate"],
            "ANYmesh": record["siblings"]["ANYmesh"],
            "ANYgeometry": record["siblings"]["ANYgeometry"],
            "ANYmaterial": record["siblings"]["ANYmaterial"],
            "ANYfileIO": record["siblings"]["ANYfileIO"],
        }
        for name, identity in expected_source_identities.items():
            source = package["sources"][name]
            if source["commit"] != identity["commit"] or source["tree"] != identity["tree"]:
                raise EvidenceError(f"package source identity mismatch for {name}")
        if package["wheels"]["ANYsolver"] != record["wheel"]:
            raise EvidenceError("package result ANYsolver wheel mismatch")
    elif package_result_path is not None:
        raise EvidenceError("package result path is forbidden when package did not pass")
    if lanes["package"]["status"] == "PASS" and wheel_path is not None:
        if wheel_hash_record(Path(wheel_path)) != wheel:
            raise EvidenceError("installed ANYsolver wheel identity mismatch")
    elif wheel_path is not None:
        raise EvidenceError("wheel path is forbidden when package did not pass")
    return record


def _git(repository: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repository), *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if completed.returncode:
        raise EvidenceError(f"Git identity check failed for {repository}")
    return completed.stdout.strip()


def _validate_repository_identities(
    record: Mapping[str, Any], repository_paths: Mapping[str, Path]
) -> None:
    expected_names = {"ANYsolver", *SIBLING_NAMES}
    if set(repository_paths) != expected_names:
        raise EvidenceError("repository_paths must name the candidate and all siblings")
    identities = {"ANYsolver": record["candidate"], **record["siblings"]}
    for name in sorted(expected_names):
        repository = Path(repository_paths[name]).resolve()
        untracked_policy = "all" if name in {"ANYsolver", "ANYfem"} else "no"
        if _git(
            repository,
            "status",
            "--porcelain",
            f"--untracked-files={untracked_policy}",
        ):
            detail = "any changes" if untracked_policy == "all" else "tracked or index changes"
            raise EvidenceError(f"repository {name} has {detail}")
        if _git(repository, "rev-parse", "HEAD") != identities[name]["commit"]:
            raise EvidenceError(f"repository {name} commit mismatch")
        if _git(repository, "rev-parse", "HEAD^{tree}") != identities[name]["tree"]:
            raise EvidenceError(f"repository {name} tree mismatch")


def validate_final_gate_result(
    record: Any,
    *,
    repository_paths: Mapping[str, Path],
    lane_log_paths: Mapping[str, Path],
    package_result_path: Path | None,
    request_paths: Mapping[str, Path],
    wheel_path: Path | None,
    contract: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Authorize a gate result only after every external binding is checked."""

    package_passed = record.get("lanes", {}).get("package", {}).get("status") == "PASS"
    if package_passed and (package_result_path is None or wheel_path is None):
        raise EvidenceError("a passed package lane requires package-result and wheel paths")
    if not package_passed and (package_result_path is not None or wheel_path is not None):
        raise EvidenceError("an unpassed package lane forbids package-result and wheel paths")

    return validate_gate_result(
        record,
        contract=contract,
        repository_paths=repository_paths,
        lane_log_paths=lane_log_paths,
        package_result_path=package_result_path,
        request_paths=request_paths,
        wheel_path=wheel_path,
    )


def validate_adjudication_files(
    gate_result_path: Path,
    status_path: Path,
    review_path: Path,
    *,
    contract_path: Path = CONTRACT_PATH,
    repository_root: Path | None = ROOT,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Validate the frozen status and independent five-key review."""

    contract = strict_json_load(contract_path)
    gate_value = strict_json_load(gate_result_path)
    status_value = strict_json_load(status_path)
    review_value = strict_json_load(review_path)
    gate_raw = gate_result_path.read_bytes()
    status_raw = status_path.read_bytes()
    review_raw = review_path.read_bytes()
    gate = validate_gate_result(gate_value, contract=contract)
    status = _exact_keys(
        status_value,
        set(contract["adjudication"]["status_required_keys"]),
        "$status",
    )
    review = _exact_keys(
        review_value,
        set(contract["adjudication"]["review_required_keys"]),
        "$review",
    )
    for raw, value, label in (
        (gate_raw, gate, "gate result"),
        (status_raw, status, "status"),
        (review_raw, review, "review"),
    ):
        if raw != canonical_json_bytes(value):
            raise EvidenceError(f"{label} is not canonical JSON")
    if status["schema"] != contract["status_schema"]:
        raise EvidenceError("status schema mismatch")
    if status["gate_result_sha256"] != _sha256_bytes(gate_raw):
        raise EvidenceError("status gate-result hash mismatch")
    _require_match(status["gate_result_sha256"], SHA256_RE, "$status.gate_result_sha256")
    expected_success = gate["clean_gate_index"] == 1
    if repository_root is not None:
        root = repository_root.resolve()
        try:
            actual_paths = [
                path.resolve().relative_to(root).as_posix()
                for path in (gate_result_path, status_path, review_path)
            ]
        except ValueError as exc:
            raise EvidenceError("adjudication output is outside the repository") from exc
        route = "success_paths" if expected_success else "blocked_paths"
        if actual_paths != contract["adjudication"][route]:
            raise EvidenceError("adjudication output extent mismatch")
    expected_terminal = contract["adjudication"][
        "success_terminal" if expected_success else "blocked_terminal"
    ]
    if status["terminal"] != expected_terminal:
        raise EvidenceError("status terminal mismatch")
    if status["clean_gate_index"] != gate["clean_gate_index"]:
        raise EvidenceError("status clean-gate index mismatch")
    if status["legacy_removal_authorized"] is not False:
        raise EvidenceError("status cannot authorize legacy removal")

    if review["schema"] != contract["review_schema"]:
        raise EvidenceError("review schema mismatch")
    if review["findings"] != []:
        raise EvidenceError("accepted independent review must have no findings")
    if review["reviewer_independence"] != contract["adjudication"]["review_independence"]:
        raise EvidenceError("review independence mismatch")
    expected_verdict = contract["adjudication"][
        "accepted_success_verdict" if expected_success else "accepted_blocked_verdict"
    ]
    if review["verdict"] != expected_verdict:
        raise EvidenceError("review verdict mismatch")
    reviewed_inputs = _exact_keys(
        review["reviewed_inputs"],
        set(contract["adjudication"]["reviewed_input_hashes"]),
        "$review.reviewed_inputs",
    )
    expected_inputs = {
        "contract_sha256": _sha256_file(contract_path),
        "gate_result_sha256": _sha256_bytes(gate_raw),
        "status_sha256": _sha256_bytes(status_raw),
    }
    if reviewed_inputs != expected_inputs:
        raise EvidenceError("reviewed-input hashes mismatch")
    return gate, status, review


def canonical_gate_result_bytes(
    record: Any,
    *,
    contract: Mapping[str, Any] | None = None,
    repository_paths: Mapping[str, Path] | None = None,
    lane_log_paths: Mapping[str, Path] | None = None,
    package_result_path: Path | None = None,
    request_paths: Mapping[str, Path] | None = None,
    wheel_path: Path | None = None,
) -> bytes:
    validated = validate_gate_result(
        record,
        contract=contract,
        repository_paths=repository_paths,
        lane_log_paths=lane_log_paths,
        package_result_path=package_result_path,
        request_paths=request_paths,
        wheel_path=wheel_path,
    )
    return canonical_json_bytes(validated)


def write_gate_result_exclusive(
    path: Path,
    record: Any,
    *,
    contract: Mapping[str, Any] | None = None,
    repository_paths: Mapping[str, Path] | None = None,
    lane_log_paths: Mapping[str, Path] | None = None,
    package_result_path: Path | None = None,
    request_paths: Mapping[str, Path] | None = None,
    wheel_path: Path | None = None,
) -> None:
    if repository_paths is None or lane_log_paths is None or request_paths is None:
        raise EvidenceError("final gate-result creation requires repository/request/log bindings")
    package_passed = record.get("lanes", {}).get("package", {}).get("status") == "PASS"
    if package_passed and (package_result_path is None or wheel_path is None):
        raise EvidenceError("final passed-package result requires package and wheel bindings")
    if not package_passed and (package_result_path is not None or wheel_path is not None):
        raise EvidenceError("blocked pre-package result forbids package and wheel bindings")
    payload = canonical_gate_result_bytes(
        record,
        contract=contract,
        repository_paths=repository_paths,
        lane_log_paths=lane_log_paths,
        package_result_path=package_result_path,
        request_paths=request_paths,
        wheel_path=wheel_path,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as stream:
            stream.write(payload)
    except FileExistsError as exc:
        raise EvidenceError(f"refusing to replace existing evidence: {path}") from exc


def _github_root() -> Path:
    if len(ROOT.parents) < 3:
        raise RuntimeError("cannot locate the common GitHub repository directory")
    return ROOT.parents[2]


def _local_roots() -> dict[str, Path]:
    github = _github_root()
    roots = {
        "ANYgeometry": github / "ANYgeometry",
        "ANYmaterial": github / "ANYmaterial",
        "ANYmesh": github / "ANYmesh",
        "ANYfileIO": github / "ANYfileIO",
        "ANYsolver": ROOT,
    }
    for name in tuple(roots):
        override = os.environ.get(f"Q1M_{name.upper()}_ROOT")
        if override:
            roots[name] = Path(override).resolve()
    for name, path in roots.items():
        if not (path / "pyproject.toml").is_file():
            raise RuntimeError(f"required local source snapshot is unavailable: {name}")
    return roots


def _normalise_distribution_name(value: str) -> str:
    return re.sub(r"[-_.]+", "-", value).lower()


def _write_source_metadata_overlay(
    roots: Mapping[str, Path], destination: Path
) -> dict[str, str]:
    """Create deterministic distribution metadata for the exact source graph.

    Source worktrees intentionally contain no generated distribution metadata.
    Without this overlay, importlib.metadata can report an unrelated globally
    installed distribution even while Python imports the frozen source tree.
    Each record is derived solely from that source tree's tracked pyproject
    file and is deleted with the lane-local pytest temp directory.
    """

    expected_roots = {name for name, _distribution, _package in LOCAL_DISTRIBUTIONS}
    if set(roots) != expected_roots:
        raise EvidenceError("source metadata roots do not match the package graph")
    destination.mkdir()
    versions: dict[str, str] = {}
    for repository_name, distribution_name, _package_name in LOCAL_DISTRIBUTIONS:
        project_path = roots[repository_name] / "pyproject.toml"
        if not project_path.is_file() or project_path.is_symlink():
            raise EvidenceError(
                f"source project metadata is unavailable: {repository_name}"
            )
        try:
            document = tomllib.loads(project_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, tomllib.TOMLDecodeError) as exc:
            raise EvidenceError(
                f"source project metadata is invalid: {repository_name}"
            ) from exc
        project = document.get("project")
        if not isinstance(project, dict):
            raise EvidenceError(f"source project table is missing: {repository_name}")
        name = project.get("name")
        version = project.get("version")
        if (
            not isinstance(name, str)
            or not PROJECT_NAME_RE.fullmatch(name)
            or _normalise_distribution_name(name)
            != _normalise_distribution_name(distribution_name)
        ):
            raise EvidenceError(
                f"source distribution name mismatch: {repository_name}"
            )
        if not isinstance(version, str) or not PROJECT_VERSION_RE.fullmatch(version):
            raise EvidenceError(
                f"source distribution version is invalid: {repository_name}"
            )
        normalised = _normalise_distribution_name(distribution_name).replace("-", "_")
        record = destination / f"{normalised}-{version}.dist-info"
        record.mkdir()
        metadata = (
            "Metadata-Version: 2.1\n"
            f"Name: {distribution_name}\n"
            f"Version: {version}\n\n"
        ).encode("ascii")
        with (record / "METADATA").open("xb") as stream:
            stream.write(metadata)
        versions[distribution_name] = version
    return versions


def _pytest_environment(
    *, roots: Mapping[str, Path], metadata_overlay: Path
) -> dict[str, str]:
    """Provide the exact source set required by the frozen preflight command."""

    environment = os.environ.copy()
    environment["PYTHONPATH"] = os.pathsep.join(
        str(path)
        for path in (
            metadata_overlay,
            ROOT / "src",
            roots["ANYmesh"] / "src",
            roots["ANYgeometry"] / "src",
            roots["ANYmaterial"] / "src",
            roots["ANYfileIO"] / "src",
        )
    )
    environment["PYTHONNOUSERSITE"] = "1"
    return environment


def _run_pytest_lane(lane: str, selected: Sequence[str]) -> int:
    """Run one lane with an isolated workspace-local pytest temp root.

    The user-global pytest root can be owned by another Windows security
    context.  A fresh ignored directory under this worktree avoids that
    cross-context ACL dependency while leaving the registered outer command
    unchanged.  Cleanup is fail-closed and never follows a substituted link.
    """

    if lane not in {"quick", "functional", "performance", "extended"}:
        raise EvidenceError(f"pytest lane does not support basetemp isolation: {lane}")
    parent = ROOT / ".pytest_tmp_q1m_runtime"
    if parent.exists() and parent.is_symlink():
        raise EvidenceError("Q1M pytest temp parent must not be a symlink")
    parent.mkdir(exist_ok=True)
    if parent.resolve().parent != ROOT.resolve():
        raise EvidenceError("Q1M pytest temp parent escaped the repository")
    basetemp: Path | None = None
    metadata_workspace: Path | None = None
    try:
        basetemp = Path(tempfile.mkdtemp(prefix=f"{lane}-", dir=parent))
        if basetemp.resolve().parent != parent.resolve():
            raise EvidenceError("Q1M pytest basetemp escaped its parent")
        metadata_workspace = Path(
            tempfile.mkdtemp(prefix=f"{lane}-metadata-", dir=parent)
        )
        if metadata_workspace.resolve().parent != parent.resolve():
            raise EvidenceError("Q1M metadata workspace escaped its parent")
        roots = _local_roots()
        metadata_overlay = metadata_workspace / "source-distributions"
        _write_source_metadata_overlay(roots, metadata_overlay)
        environment = _pytest_environment(
            roots=roots,
            metadata_overlay=metadata_overlay,
        )
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "-q",
                f"--basetemp={basetemp}",
                *selected,
            ],
            cwd=ROOT,
            env=environment,
            check=False,
        )
        return int(completed.returncode)
    finally:
        for temporary_path in (basetemp, metadata_workspace):
            if temporary_path is None or not os.path.lexists(temporary_path):
                continue
            if temporary_path.is_symlink() or not temporary_path.is_dir():
                temporary_path.unlink()
                continue

            def make_writable_and_retry(function, path, _excinfo):
                os.chmod(path, stat.S_IREAD | stat.S_IWRITE)
                function(path)

            shutil.rmtree(temporary_path, onexc=make_writable_and_retry)
        try:
            parent.rmdir()
        except OSError:
            # Another explicitly launched non-resource lane may share only the
            # ignored parent; each randomized child remains isolated.
            pass


def _tracked_head_identity(repository: Path) -> dict[str, str]:
    """Return HEAD authority after rejecting tracked/index modifications.

    Untracked paths are intentionally ignored: sibling repositories may carry
    unrelated work, and the package source is obtained exclusively from HEAD.
    """

    if _git(repository, "status", "--porcelain", "--untracked-files=no"):
        raise RuntimeError(f"tracked or index changes exist in {repository}")
    return {
        "commit": _git(repository, "rev-parse", "HEAD"),
        "tree": _git(repository, "rev-parse", "HEAD^{tree}"),
    }


def _extract_git_archive(archive: Path, destination: Path) -> dict[str, Any]:
    """Safely extract a Git-created ZIP and hash its complete file graph."""

    destination.mkdir()
    seen: set[str] = set()
    with zipfile.ZipFile(archive, "r") as source:
        for member in source.infolist():
            name = member.filename
            relative = PurePosixPath(name)
            if (
                not name
                or "\\" in name
                or relative.is_absolute()
                or any(part in {"", ".", ".."} for part in relative.parts)
                or name in seen
            ):
                raise RuntimeError(f"unsafe or duplicate Git archive member: {name!r}")
            seen.add(name)
            mode = (member.external_attr >> 16) & 0xFFFF
            kind = stat.S_IFMT(mode)
            if kind == stat.S_IFLNK:
                raise RuntimeError(f"symlink Git archive member is forbidden: {name}")
            if kind not in {0, stat.S_IFREG, stat.S_IFDIR}:
                raise RuntimeError(f"unsupported Git archive member type: {name}")
            target = destination.joinpath(*relative.parts)
            if member.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            try:
                with source.open(member, "r") as input_stream, target.open("xb") as output_stream:
                    shutil.copyfileobj(input_stream, output_stream)
            except FileExistsError as exc:
                raise RuntimeError(f"duplicate Git archive target: {name}") from exc

    graph = []
    for path in sorted(item for item in destination.rglob("*") if item.is_file()):
        relative = path.relative_to(destination).as_posix()
        graph.append(
            {"bytes": path.stat().st_size, "path": relative, "sha256": _sha256_file(path)}
        )
    if not graph:
        raise RuntimeError("Git archive extracted no regular files")
    return {"files": len(graph), "sha256": _sha256_bytes(canonical_json_bytes(graph))}


def _archive_head_snapshot(
    repository: Path,
    archive: Path,
    destination: Path,
    *,
    environment: Mapping[str, str],
) -> dict[str, Any]:
    """Materialize only committed HEAD and bind both archive and file graph."""

    before = _tracked_head_identity(repository)
    archive.parent.mkdir(parents=True, exist_ok=True)
    archive_log = _run_captured(
        [
            "git",
            "-C",
            str(repository),
            "archive",
            "--format=zip",
            f"--output={archive}",
            "HEAD",
        ],
        cwd=archive.parent,
        env=environment,
    )
    if not archive.is_file() or archive.is_symlink():
        raise RuntimeError("git archive did not create a regular file")
    content = _extract_git_archive(archive, destination)
    after = _tracked_head_identity(repository)
    if after != before:
        raise RuntimeError(f"repository HEAD changed while archiving {repository}")
    return {
        "archive": file_hash_record(archive),
        "archive_log": archive_log,
        "commit": before["commit"],
        "content": content,
        "tree": before["tree"],
    }


def _run_captured(command: Sequence[str], *, cwd: Path, env: Mapping[str, str]) -> dict[str, Any]:
    completed = subprocess.run(
        list(command), cwd=cwd, env=dict(env), check=False, capture_output=True
    )
    combined = completed.stdout + completed.stderr
    result = {
        "bytes": len(combined),
        "returncode": int(completed.returncode),
        "sha256": _sha256_bytes(combined),
    }
    if completed.returncode:
        raise RuntimeError(
            f"package-lane subprocess failed ({completed.returncode}); "
            f"log_sha256={result['sha256']}"
        )
    return result


PACKAGE_SMOKE = r'''
import importlib
import json
import pathlib
import sys
import warnings

target = pathlib.Path(sys.argv[1]).resolve()
forbidden = [pathlib.Path(item).resolve() for item in json.loads(sys.argv[2])]

def under(path, root):
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True

origins = {}
for package in ("anysolver", "anygeometry", "anymaterial", "anymesher", "anyfileio"):
    module = importlib.import_module(package)
    origin = pathlib.Path(module.__file__).resolve()
    if not under(origin, target):
        raise AssertionError(f"{package} imported outside isolated target")
    origins[package] = origin.relative_to(target).as_posix()

for entry in sys.path:
    if not entry:
        continue
    resolved = pathlib.Path(entry).resolve()
    if any(under(resolved, root) for root in forbidden):
        raise AssertionError("source repository leaked onto sys.path")
if any(under(pathlib.Path.cwd().resolve(), root) for root in forbidden):
    raise AssertionError("smoke process cwd is inside a source repository")

from anysolver import (
    LegacyQ4DeprecationWarning,
    QualifiedE4PLShellElement,
    ShellElement,
    create_shell_element,
    shell_formulation_diagnostics,
)

default = create_shell_element(1, [1, 2, 3, 4], "steel")
non_q4 = [
    create_shell_element(2, [1, 2, 3], "steel"),
    create_shell_element(3, [1, 2, 3, 4, 5, 6], "steel"),
    create_shell_element(4, [1, 2, 3, 4, 5, 6, 7, 8], "steel"),
    create_shell_element(
        5, [1, 2, 3, 4, 5, 6, 7, 8], "steel", reduced_integration=True
    ),
]
if type(default) is not QualifiedE4PLShellElement:
    raise AssertionError("installed wheel did not select qualified Q4")
if any(type(item) is not ShellElement for item in non_q4):
    raise AssertionError("installed wheel changed a non-Q4 topology")
diagnostic = shell_formulation_diagnostics(node_count=4)
if diagnostic["schema"] != "anysolver.shell-formulation-diagnostics-v1":
    raise AssertionError("installed wheel did not export diagnostics")
with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter("always")
    rollback = create_shell_element(6, [1, 2, 3, 4], "steel", formulation="legacy")
if type(rollback) is not ShellElement:
    raise AssertionError("legacy selector did not preserve ShellElement")
if not any(item.category is LegacyQ4DeprecationWarning for item in caught):
    raise AssertionError("legacy selector did not emit LegacyQ4DeprecationWarning")

print(json.dumps({
    "diagnostics_schema": diagnostic["schema"],
    "legacy_warning": "LegacyQ4DeprecationWarning",
    "non_q4_types": [type(item).__name__ for item in non_q4],
    "origins": origins,
    "q4_type": type(default).__name__,
}, sort_keys=True, separators=(",", ":")))
'''


def run_package_lane(
    *, output: Path | None = None, wheel_output: Path | None = None
) -> dict[str, Any]:
    """Build verified committed-HEAD archives and smoke an isolated target."""

    for artifact in (output, wheel_output):
        if artifact is not None and artifact.exists():
            raise EvidenceError(f"refusing to replace existing package artifact: {artifact}")
    if output is not None and wheel_output is not None and output.resolve() == wheel_output.resolve():
        raise EvidenceError("package result and wheel outputs must be distinct")

    roots = _local_roots()
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    environment.pop("PYTHONHOME", None)
    environment["PYTHONNOUSERSITE"] = "1"

    with tempfile.TemporaryDirectory(prefix="anysolver-q1m-package-") as temporary:
        workspace = Path(temporary).resolve()
        if any(
            workspace == path.resolve() or workspace.is_relative_to(path.resolve())
            for path in roots.values()
        ):
            raise RuntimeError("package workspace must be external to every source repository")
        snapshots = workspace / "snapshots"
        archives = workspace / "archives"
        wheelhouse = workspace / "wheelhouse"
        target = workspace / "target"
        smoke_cwd = workspace / "smoke"
        snapshots.mkdir()
        archives.mkdir()
        wheelhouse.mkdir()
        target.mkdir()
        smoke_cwd.mkdir()

        build_logs: dict[str, dict[str, Any]] = {}
        source_records: dict[str, dict[str, Any]] = {}
        wheels: dict[str, Path] = {}
        for repository_name, distribution_name, _package_name in LOCAL_DISTRIBUTIONS:
            snapshot = snapshots / repository_name
            source_records[repository_name] = _archive_head_snapshot(
                roots[repository_name],
                archives / f"{repository_name}.zip",
                snapshot,
                environment=environment,
            )
            before = set(wheelhouse.glob("*.whl"))
            build_logs[repository_name] = _run_captured(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "wheel",
                    "--disable-pip-version-check",
                    "--no-deps",
                    "--no-build-isolation",
                    "--wheel-dir",
                    str(wheelhouse),
                    str(snapshot),
                ],
                cwd=workspace,
                env=environment,
            )
            created = set(wheelhouse.glob("*.whl")) - before
            if len(created) != 1:
                raise RuntimeError(f"expected one new wheel for {distribution_name}")
            wheel = created.pop()
            if not wheel.is_file() or wheel.is_symlink():
                raise RuntimeError(f"wheel for {distribution_name} is not a regular file")
            wheels[repository_name] = wheel

        install_log = _run_captured(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "--no-compile",
                "--no-deps",
                "--target",
                str(target),
                *[str(wheels[name]) for name, _, _ in LOCAL_DISTRIBUTIONS],
            ],
            cwd=workspace,
            env=environment,
        )

        # The system environment may contain editable-install ``.pth`` entries
        # for a different checkout.  Remove the entire common repository root,
        # not merely the five snapshots selected above.
        forbidden_roots = [str(_github_root().resolve())]
        smoke_command = [
            sys.executable,
            "-I",
            "-c",
            (
                "import json,pathlib,sys;"
                "roots=[pathlib.Path(p).resolve() for p in json.loads(sys.argv[2])];"
                "inside=lambda p:any(p==r or p.is_relative_to(r) for r in roots);"
                "sys.path[:]=[p for p in sys.path if p and not inside(pathlib.Path(p).resolve())];"
                "sys.path.insert(0,sys.argv[1]);exec(sys.argv[3])"
            ),
            str(target),
            json.dumps(forbidden_roots, separators=(",", ":")),
            PACKAGE_SMOKE,
        ]
        smoke_completed = subprocess.run(
            smoke_command,
            cwd=smoke_cwd,
            env=environment,
            check=False,
            capture_output=True,
        )
        smoke_log = smoke_completed.stdout + smoke_completed.stderr
        if smoke_completed.returncode:
            raise RuntimeError(
                f"installed-wheel smoke failed ({smoke_completed.returncode}); "
                f"log_sha256={_sha256_bytes(smoke_log)}; "
                f"tail={smoke_log[-4000:].decode('utf-8', errors='replace')}"
            )
        try:
            smoke = strict_json_loads(smoke_completed.stdout)
        except EvidenceError as exc:
            raise RuntimeError("installed-wheel smoke did not emit strict JSON") from exc

        wheel_records = {
            name: {
                "bytes": wheel.stat().st_size,
                "filename": wheel.name,
                "sha256": _sha256_file(wheel),
            }
            for name, wheel in sorted(wheels.items())
        }
        result = {
            "build_logs": build_logs,
            "install_log": install_log,
            "schema": _load_contract()["package_result_schema"],
            "smoke": smoke,
            "smoke_log": {
                "bytes": len(smoke_log),
                "sha256": _sha256_bytes(smoke_log),
            },
            "sources": source_records,
            "status": "PASS",
            "wheels": wheel_records,
        }
        validate_package_result(result)
        payload = canonical_json_bytes(result)
        if wheel_output is not None:
            if wheel_output.name != wheels["ANYsolver"].name:
                raise EvidenceError(
                    "preserved wheel path basename must match the built ANYsolver wheel"
                )
            wheel_output.parent.mkdir(parents=True, exist_ok=True)
            with wheels["ANYsolver"].open("rb") as source, wheel_output.open("xb") as target_stream:
                shutil.copyfileobj(source, target_stream)
        if output is not None:
            output.parent.mkdir(parents=True, exist_ok=True)
            with output.open("xb") as stream:
                stream.write(payload)
        sys.stdout.buffer.write(payload)
        sys.stdout.buffer.flush()
        return result


def _path_bindings(values: Sequence[str] | None, label: str) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for value in values or ():
        name, separator, raw_path = value.partition("=")
        if not separator or not name or not raw_path or name in result:
            raise EvidenceError(f"invalid or duplicate {label} binding: {value!r}")
        result[name] = Path(raw_path)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "lane",
        choices=(
            "quick",
            "package",
            "functional",
            "performance",
            "extended",
            "list",
            "validate-evidence",
        ),
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--evidence", type=Path)
    parser.add_argument("--final", action="store_true")
    parser.add_argument("--repository", action="append")
    parser.add_argument("--request", action="append")
    parser.add_argument("--log", action="append")
    parser.add_argument("--package-result", type=Path)
    parser.add_argument("--wheel", type=Path)
    parser.add_argument("--wheel-output", type=Path)
    args = parser.parse_args(argv)
    if args.lane == "list":
        print(json.dumps(gate_inventories(), sort_keys=True, separators=(",", ":")))
        return 0
    if args.lane == "package":
        if any(
            value
            for value in (
                args.evidence,
                args.final,
                args.repository,
                args.request,
                args.log,
                args.package_result,
                args.wheel,
            )
        ):
            parser.error("validation options are invalid for the package lane")
        output = args.output
        wheel_output = args.wheel_output
        if output is None and os.environ.get("Q1M_PACKAGE_RESULT_PATH"):
            output = Path(os.environ["Q1M_PACKAGE_RESULT_PATH"])
        if wheel_output is None and os.environ.get("Q1M_PACKAGE_WHEEL_PATH"):
            wheel_output = Path(os.environ["Q1M_PACKAGE_WHEEL_PATH"])
        run_package_lane(output=output, wheel_output=wheel_output)
        return 0
    if args.lane == "validate-evidence":
        if args.evidence is None:
            parser.error("validate-evidence requires --evidence")
        record = strict_json_load(args.evidence)
        if args.final:
            package_passed = record.get("lanes", {}).get("package", {}).get("status") == "PASS"
            if package_passed and (args.package_result is None or args.wheel is None):
                parser.error("passed-package validation requires --package-result and --wheel")
            if not package_passed and (args.package_result is not None or args.wheel is not None):
                parser.error("blocked pre-package validation forbids package/wheel paths")
            validate_final_gate_result(
                record,
                repository_paths=_path_bindings(args.repository, "repository"),
                lane_log_paths=_path_bindings(args.log, "log"),
                package_result_path=args.package_result,
                request_paths=_path_bindings(args.request, "request"),
                wheel_path=args.wheel,
            )
        else:
            if any(
                value
                for value in (
                    args.repository,
                    args.request,
                    args.log,
                    args.package_result,
                    args.wheel,
                    args.wheel_output,
                    args.output,
                )
            ):
                parser.error("external bindings require --final")
            validate_gate_result(record)
        return 0
    if any(
        value
        for value in (
            args.output,
            args.evidence,
            args.final,
            args.repository,
            args.request,
            args.log,
            args.package_result,
            args.wheel,
            args.wheel_output,
        )
    ):
        parser.error("evidence/package options are invalid for this lane")
    lanes = inventory()
    selected = lanes[args.lane]
    if not selected:
        raise SystemExit(f"burn-in lane {args.lane!r} is empty")
    returncode = _run_pytest_lane(args.lane, selected)
    if returncode:
        return returncode
    if args.lane == "performance":
        from measure_e4_pl_q1m_baseline import collect_performance_observation

        observation = collect_performance_observation()
        payload = canonical_json_bytes(observation).rstrip(b"\n")
        sys.stdout.buffer.write(PERFORMANCE_BASELINE_MARKER + payload + b"\n")
        sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
