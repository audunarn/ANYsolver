from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import platform
from pathlib import Path
from pathlib import PurePosixPath
import stat
import subprocess
import sys
import sysconfig
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ORACLE = ROOT / "docs" / "reference_cases" / "s4_stage_m_mechanics_oracle.py"
CONTRACT = ROOT / "docs" / "reference_cases" / "s4_stage_m_mechanics_contract.json"
CASES = ROOT / "docs" / "reference_cases" / "s4_stage_m_mechanics_cases.json"
INTERVAL = ROOT / "docs" / "reference_cases" / "s4_stage_m_dyadic_interval.py"
TIMEOUT_ADDENDUM = (
    ROOT
    / "docs"
    / "agent_plans"
    / "s4_stage_m_320_timeout_execution_addendum.md"
)
FULL_EVIDENCE_DIR = ROOT / ".s4_stage_m_execution"
COMMITTED_OUTPUT = (
    ROOT / "docs" / "reference_cases" / "s4_stage_m_mechanics_output.json"
)

FULL_EXECUTION_ENVIRONMENT = "ANYSOLVER_RUN_S4_STAGE_M_FULL"
FULL_EXECUTION_VALUE = "PRECISION_SHARDS_THEN_CANONICAL_MERGE_V1"
SHARD_SCHEMA = "anysolver.s4.stage-m-mechanics-precision-shard-v1"
COMPLETE_SCHEMA = "anysolver.s4.stage-m-mechanics-completion-v1"

ORACLE_SHA256 = "1B123591388AE73E83E3BA7082E82D0A579BE856669D461AA500BF41FE772D48"
CONTRACT_SHA256 = "2FBB419F0C09D909F2B6A1D4FF77285EB078E8A6E7DB10286ECC47282D1F90DA"
CASES_SHA256 = "912E07377C174E1FE031EEBA98DD5E8406C9A294AF2B3032D9AB5B38F67C7B94"
INTERVAL_SHA256 = "05C086DB11548AA4B77A5B31A5171792E08C053F93682D5FBED2D16425C16CC3"
TIMEOUT_ADDENDUM_SHA256 = (
    "C5C3DD92CF0C7EA3625861592D4AD05B51CCC8C0FD6362CB8C6645A8E9DD8ADC"
)
SHARD_TIMEOUT_SECONDS_BY_PRECISION = {80: 7200, 160: 7200, 320: 14400}
# Rebound to the materialized canonical set-1 merge after local qualification.
OUTPUT_SHA256 = "3A26052DB79CE914FF8A1FCA7835F3B86C15F1D351754B45CA904753D8EFDA0D"


def _raw_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _raw_sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def _reject_constant(value: str) -> None:
    raise ValueError(f"nonfinite JSON constant is forbidden: {value}")


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        assert key not in result, f"duplicate JSON key: {key}"
        result[key] = value
    return result


def _parse_strict_json(raw: bytes, label: str) -> dict[str, Any]:
    assert not raw.startswith(b"\xef\xbb\xbf"), f"BOM is forbidden: {label}"
    assert b"\r" not in raw, f"CR transport is forbidden: {label}"
    assert raw.endswith(b"\n"), f"terminal LF is required: {label}"
    value = json.loads(
        raw.decode("utf-8"),
        object_pairs_hook=_reject_duplicate_keys,
        parse_constant=_reject_constant,
    )
    assert isinstance(value, dict), f"top-level JSON object required: {label}"
    return value


def _canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _parse_canonical_json(raw: bytes, label: str) -> dict[str, Any]:
    value = _parse_strict_json(raw, label)
    assert _canonical_json_bytes(value) == raw, f"noncanonical JSON: {label}"
    return value


def _strict_json(path: Path) -> object:
    raw = path.read_bytes()
    return _parse_strict_json(raw, str(path))


def _load_static_oracle():
    spec = importlib.util.spec_from_file_location("s4_stage_m_static_oracle", ORACLE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _worker_environment() -> dict[str, str]:
    environment = os.environ.copy()
    local_mpmath = ROOT / ".s4_stage_m_mpmath"
    environment["PYTHONPATH"] = str(local_mpmath) if local_mpmath.is_dir() else ""
    environment["PYTHONNOUSERSITE"] = "1"
    environment["MPMATH_NOGMPY"] = "1"
    return environment


def _run_worker(*arguments: str, timeout: int = 900) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ORACLE), *arguments],
        cwd=ROOT,
        env=_worker_environment(),
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def _run_worker_bytes(
    *arguments: str, timeout: int = 7200
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        [sys.executable, str(ORACLE), *arguments],
        cwd=ROOT,
        env=_worker_environment(),
        check=False,
        capture_output=True,
        text=False,
        timeout=timeout,
    )


def _write_exclusive(path: Path, content: bytes) -> None:
    with path.open("xb") as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())


def _lexists(path: Path) -> bool:
    return os.path.lexists(path)


def _is_reparse_point(path: Path) -> bool:
    attributes = getattr(path.lstat(), "st_file_attributes", 0)
    flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return bool(attributes & flag)


def _assert_safe_directory(path: Path) -> None:
    assert _lexists(path), f"required directory is absent: {path}"
    metadata = path.lstat()
    assert not stat.S_ISLNK(metadata.st_mode), f"directory is a link: {path}"
    assert not _is_reparse_point(path), f"directory is a reparse point: {path}"
    assert stat.S_ISDIR(metadata.st_mode), f"path is not a directory: {path}"


def _assert_safe_regular_file(path: Path) -> None:
    assert _lexists(path), f"required file is absent: {path}"
    metadata = path.lstat()
    assert not stat.S_ISLNK(metadata.st_mode), f"file is a link: {path}"
    assert not _is_reparse_point(path), f"file is a reparse point: {path}"
    assert stat.S_ISREG(metadata.st_mode), f"path is not a regular file: {path}"


def _execution_configuration() -> tuple[dict[str, Any], list[Path], list[Path], Path]:
    cases = _strict_json(CASES)
    assert isinstance(cases, dict)
    execution = cases["execution"]
    assert execution["mode"] == "precision_shards_then_canonical_merge"
    assert execution["precision_shards"] == [80, 160, 320]
    assert execution["repeat_sets"] == 2
    assert execution["shard_timeout_seconds"] == 7200
    assert execution["merge_timeout_seconds"] == 300
    assert execution["task_owned_directory"] == FULL_EVIDENCE_DIR.name
    assert execution["shard_filenames"] == [
        "set1_080.json",
        "set1_160.json",
        "set1_320.json",
        "set2_080.json",
        "set2_160.json",
        "set2_320.json",
    ]
    assert execution["merge_filenames"] == [
        "set1_merged.json",
        "set2_merged.json",
    ]
    assert execution["completion_manifest"] == "COMPLETE.json"
    assert execution["pending_suffix"] == ".pending"
    assert execution["full_execution_environment_variable"] == (
        FULL_EXECUTION_ENVIRONMENT
    )
    assert execution["full_execution_environment_value"] == FULL_EXECUTION_VALUE
    assert execution["shard_status"] == "partial"
    assert execution["shards_are_nonterminal"] is True
    assert execution["quick_summary_decimal_digits"] == 80
    assert execution["merge_precision_decimal_digits"] == 320
    assert execution["completed_shards_are_preserved"] is True
    assert execution["merge_recomputes_scientific_summary"] is True
    assert execution["monolithic_timeout"] == {
        "timeout_seconds": 7200,
        "packet_produced": False,
        "scientific_result": False,
        "evidence_directory_created": False,
    }
    assert Path(execution["task_owned_directory"]).name == execution[
        "task_owned_directory"
    ]
    shard_paths = [
        FULL_EVIDENCE_DIR / name for name in execution["shard_filenames"]
    ]
    merge_paths = [
        FULL_EVIDENCE_DIR / name for name in execution["merge_filenames"]
    ]
    completion = FULL_EVIDENCE_DIR / execution["completion_manifest"]
    return execution, shard_paths, merge_paths, completion


def _ensure_execution_directory() -> None:
    if not _lexists(FULL_EVIDENCE_DIR):
        FULL_EVIDENCE_DIR.mkdir()
    _assert_safe_directory(FULL_EVIDENCE_DIR)
    assert FULL_EVIDENCE_DIR.resolve(strict=True).parent == ROOT.resolve(strict=True)


def _inventory_prefix(
    execution: dict[str, Any], ordered_paths: list[Path]
) -> int:
    _assert_safe_directory(FULL_EVIDENCE_DIR)
    allowed_names = {path.name for path in ordered_paths}
    pending_names = {
        path.name + execution["pending_suffix"] for path in ordered_paths
    }
    seen_casefold: set[str] = set()
    actual_names: set[str] = set()
    for entry in FULL_EVIDENCE_DIR.iterdir():
        folded = entry.name.casefold()
        assert folded not in seen_casefold, "case-fold duplicate evidence name"
        seen_casefold.add(folded)
        assert entry.name not in pending_names, f"incomplete pending evidence: {entry}"
        assert entry.name in allowed_names, f"unexpected Stage-M evidence entry: {entry}"
        _assert_safe_regular_file(entry)
        actual_names.add(entry.name)
    prefix = 0
    missing_seen = False
    for path in ordered_paths:
        present = path.name in actual_names
        if present:
            assert not missing_seen, f"non-prefix Stage-M evidence gap before {path.name}"
            prefix += 1
        else:
            missing_seen = True
    return prefix


def _promote_canonical_exclusive(
    final_path: Path, raw: bytes, pending_suffix: str
) -> None:
    _assert_safe_directory(final_path.parent)
    pending = final_path.with_name(final_path.name + pending_suffix)
    assert not _lexists(final_path), f"refusing to overwrite evidence: {final_path}"
    assert not _lexists(pending), f"pending evidence already exists: {pending}"
    _write_exclusive(pending, raw)
    _assert_safe_regular_file(pending)
    assert pending.read_bytes() == raw
    assert not _lexists(final_path), f"evidence appeared before promotion: {final_path}"
    # The registered runner is Windows-only; os.rename is atomic there and refuses
    # to replace an existing destination.  A failure intentionally preserves pending.
    assert os.name == "nt", "no-overwrite rename semantics are frozen to Windows"
    os.rename(pending, final_path)
    _assert_safe_regular_file(final_path)
    assert not _lexists(pending)
    assert final_path.read_bytes() == raw


def _expected_identities(contract: dict[str, Any]) -> dict[str, Any]:
    authority = contract["authority"]
    inputs = contract["implementation_inputs"]
    assert inputs["cases"]["raw_sha256"] == _raw_sha256(CASES)
    assert inputs["oracle"]["raw_sha256"] == _raw_sha256(ORACLE)
    assert inputs["dyadic_interval"]["raw_sha256"] == _raw_sha256(INTERVAL)
    assert inputs["constrained_status"]["raw_sha256"] == authority[
        "candidate_a_status_sha256"
    ]
    assert inputs["energetic_derivation"]["raw_sha256"] == authority[
        "candidate_b_derivation_sha256"
    ]
    return {
        "candidate_id": contract["candidate_id"],
        "governing_sha256": authority["governing_program_sha256"],
        "plan_sha256": authority["stage_m_plan_sha256"],
        "source_manifest_sha256": authority["source_manifest_sha256"],
        "energetic_derivation_sha256": authority[
            "candidate_b_derivation_sha256"
        ],
        "constrained_status_sha256": authority["candidate_a_status_sha256"],
        "cases_sha256": inputs["cases"]["raw_sha256"],
        "interval_sha256": inputs["dyadic_interval"]["raw_sha256"],
        "oracle_sha256": inputs["oracle"]["raw_sha256"],
        "contract_sha256": _raw_sha256(CONTRACT),
        "contract_ledger_sha256": contract["ledger_sha256"],
    }


def _assert_sha256_token(value: Any, *, uppercase: bool = True) -> None:
    assert isinstance(value, str)
    assert len(value) == 64
    alphabet = "0123456789ABCDEF" if uppercase else "0123456789abcdef"
    assert all(character in alphabet for character in value)


def _assert_manifest_file_record(root: Path, record: Any) -> None:
    assert isinstance(record, list) and len(record) == 3
    relative, size, digest = record
    assert isinstance(relative, str) and relative
    pure = PurePosixPath(relative)
    assert not pure.is_absolute()
    assert "\\" not in relative
    assert all(part not in ("", ".", "..") for part in pure.parts)
    assert isinstance(size, int) and not isinstance(size, bool) and size >= 0
    _assert_sha256_token(digest, uppercase=False)
    target = root.joinpath(*pure.parts)
    _assert_safe_regular_file(target)
    assert target.resolve(strict=True).is_relative_to(root.resolve(strict=True))
    assert target.stat().st_size == size
    assert hashlib.sha256(target.read_bytes()).hexdigest() == digest


def _validate_environment(
    environment: Any, baseline: dict[str, Any] | None, *, require_current: bool
) -> dict[str, Any]:
    assert isinstance(environment, dict)
    assert set(environment) == {
        "frozen_base_manifest",
        "frozen_base_manifest_sha256",
        "python_implementation",
        "python_version",
        "mpmath_version",
        "mpmath_file",
    }
    manifest = environment["frozen_base_manifest"]
    assert isinstance(manifest, dict)
    assert set(manifest) == {
        "schema",
        "implementation",
        "version",
        "hexversion",
        "byteorder",
        "platform",
        "binaries",
        "mpmath",
        "targets",
    }
    assert manifest["schema"] == "s4-drill-constraint-environment-v1"
    _assert_sha256_token(environment["frozen_base_manifest_sha256"])
    assert (
        _raw_sha256_bytes(_canonical_json_bytes(manifest))
        == environment["frozen_base_manifest_sha256"]
    )
    if require_current:
        assert environment["python_implementation"] == sys.implementation.name
        assert environment["python_version"] == list(sys.version_info[:3])
        assert manifest["implementation"] == sys.implementation.name
        assert manifest["version"] == sys.version
        assert manifest["hexversion"] == sys.hexversion
        assert manifest["byteorder"] == sys.byteorder
        assert manifest["platform"] == {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
        }
    assert environment["mpmath_version"] == "1.3.0"
    local_mpmath_path = ROOT / ".s4_stage_m_mpmath"
    local_mpmath = (
        local_mpmath_path.resolve(strict=True) if require_current else None
    )
    expected_module = (
        (local_mpmath / "mpmath" / "__init__.py").resolve(strict=True)
        if local_mpmath is not None
        else None
    )
    if require_current:
        assert expected_module is not None
        assert environment["mpmath_file"] == str(expected_module)
    mpmath_manifest = manifest["mpmath"]
    assert isinstance(mpmath_manifest, dict)
    assert set(mpmath_manifest) == {
        "name",
        "version",
        "root",
        "files",
        "excluded_pyc",
        "module_file",
        "backend",
        "module_bindings",
    }
    assert mpmath_manifest["name"] == "mpmath"
    assert mpmath_manifest["version"] == "1.3.0"
    assert mpmath_manifest["backend"] == "python"
    if require_current:
        assert local_mpmath is not None and expected_module is not None
        assert Path(mpmath_manifest["root"]).resolve(strict=True) == local_mpmath
        assert mpmath_manifest["module_file"] == str(expected_module)
    distribution_root = Path(mpmath_manifest["root"])
    files = mpmath_manifest["files"]
    assert isinstance(files, list) and files
    names = [record[0] for record in files]
    assert names == sorted(names)
    assert len({name.casefold() for name in names}) == len(names)
    if require_current:
        _assert_safe_directory(distribution_root)
        for record in files:
            _assert_manifest_file_record(distribution_root, record)
    else:
        for record in files:
            assert isinstance(record, list) and len(record) == 3
            assert isinstance(record[0], str) and record[0]
            assert isinstance(record[1], int) and record[1] >= 0
            _assert_sha256_token(record[2], uppercase=False)
    excluded_pyc = mpmath_manifest["excluded_pyc"]
    assert isinstance(excluded_pyc, list)
    assert excluded_pyc == sorted(excluded_pyc)
    assert all(isinstance(name, str) and name.casefold().endswith(".pyc") for name in excluded_pyc)
    bindings = mpmath_manifest["module_bindings"]
    assert isinstance(bindings, list)
    assert [binding["role"] for binding in bindings] == ["mpmath", "mpmath.libmp"]
    file_by_name = {record[0]: record for record in files}
    for binding in bindings:
        assert set(binding) == {"role", "relative_name", "size", "sha256"}
        bound = file_by_name[binding["relative_name"]]
        assert [binding["relative_name"], binding["size"], binding["sha256"]] == bound
    binaries = manifest["binaries"]
    assert isinstance(binaries, list) and binaries
    expected_binary_paths: dict[str, Path] = {}
    if require_current:
        expected_binary_paths["interpreter"] = Path(sys.executable).resolve(strict=True)
        if platform.system() == "Windows":
            dll_name = f"python{sys.version_info.major}{sys.version_info.minor}.dll"
            expected_binary_paths["runtime"] = (
                Path(sys.base_prefix) / dll_name
            ).resolve(strict=True)
        else:
            library = sysconfig.get_config_var("LDLIBRARY")
            library_dir = sysconfig.get_config_var("LIBDIR")
            if library and library_dir:
                expected_binary_paths["runtime"] = (
                    Path(str(library_dir)) / str(library)
                ).resolve(strict=True)
        assert [item["role"] for item in binaries] == sorted(expected_binary_paths)
    for item in binaries:
        assert set(item) == {"role", "name", "size", "sha256"}
        assert item["role"] in {"interpreter", "runtime"}
        assert isinstance(item["name"], str) and item["name"]
        assert isinstance(item["size"], int) and item["size"] > 0
        _assert_sha256_token(item["sha256"], uppercase=False)
        if require_current:
            target = expected_binary_paths[item["role"]]
            _assert_safe_regular_file(target)
            assert item["size"] == target.stat().st_size
            assert item["sha256"] == hashlib.sha256(target.read_bytes()).hexdigest()
    targets = manifest["targets"]
    assert isinstance(targets, list)
    assert [target["dps"] for target in targets] == [80, 160, 320]
    assert all(set(target) == {"dps", "prec", "eps"} for target in targets)
    if baseline is not None:
        assert environment == baseline, "precision-shard environment drift"
    return environment


def _validate_precision_record(
    record: Any, decimal_digits: int, drill_cases: dict[str, Any]
) -> None:
    assert isinstance(record, dict)
    assert set(record) == {
        "decimal_digits",
        "mp_prec",
        "mp_eps",
        "classification_eps64",
        "exact_flat_certificate",
        "exact_flat_runtime_binding",
        "pointwise_derivation",
        "rules",
        "quadrature_categories_equal",
        "quick",
        "local_rules",
        "response",
        "covariance",
        "activity_deletion",
    }
    assert type(record["decimal_digits"]) is int
    assert record["decimal_digits"] == decimal_digits
    assert record["quick"] is False
    topology_ids = [item["id"] for item in drill_cases["topology_cases"]]
    local_ids = [
        f"candidate_b_local::{item['id']}" for item in drill_cases["local_cases"]
    ]
    for section_name, expected_ids in (
        ("rules", topology_ids),
        ("local_rules", local_ids),
    ):
        section = record[section_name]
        assert isinstance(section, dict)
        assert set(section) == {"primary", "sensitivity"}
        for rule in ("primary", "sensitivity"):
            values = section[rule]
            assert isinstance(values, list)
            assert [item["id"] for item in values] == expected_ids
            for item in values:
                assert set(item["sensitivities"]) == {"0.25", "1", "4"}
    for section_name in ("response", "covariance", "activity_deletion"):
        section = record[section_name]
        assert isinstance(section, dict)
        assert set(section) == {"primary", "sensitivity"}
    for rule in ("primary", "sensitivity"):
        assert set(record["response"][rule]) == {
            "patch",
            "thickness_locking",
            "curved_refinement",
        }


def _expected_exclusions() -> dict[str, bool]:
    return {
        "production_source_edit": False,
        "selector_or_activation": False,
        "penalty_or_stabilization": False,
        "invented_material_coefficient": False,
        "gauge_relabel": False,
        "rank18_claim": False,
        "candidate_a_equation_implementation": False,
    }


def _validate_shard_packet(
    raw: bytes,
    label: str,
    decimal_digits: int,
    identities: dict[str, Any],
    drill_cases: dict[str, Any],
    baseline_environment: dict[str, Any] | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    packet = _parse_canonical_json(raw, label)
    assert set(packet) == {
        "schema",
        "status",
        "mode",
        "identities",
        "environment",
        "decimal_digits",
        "precision_record",
        "execution",
        "exclusions",
    }
    assert packet["schema"] == SHARD_SCHEMA
    assert packet["status"] == "partial"
    assert packet["mode"] == "precision_shard"
    assert packet["identities"] == identities
    environment = _validate_environment(
        packet["environment"], baseline_environment, require_current=True
    )
    assert type(packet["decimal_digits"]) is int
    assert packet["decimal_digits"] == decimal_digits
    assert packet["execution"] == {
        "full_catalog": True,
        "quadrature_rules": ["primary", "sensitivity"],
        "sensitivity_multipliers": ["0.25", "1", "4"],
    }
    assert packet["exclusions"] == _expected_exclusions()
    _validate_precision_record(packet["precision_record"], decimal_digits, drill_cases)
    return packet, environment


def _validate_terminal_result(
    raw: bytes,
    label: str,
    identities: dict[str, Any],
    drill_cases: dict[str, Any],
    *,
    baseline_environment: dict[str, Any] | None,
    require_current_environment: bool,
    expected_shards: list[dict[str, Any]] | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    result = _parse_canonical_json(raw, label)
    assert set(result) == {
        "schema",
        "status",
        "mode",
        "identities",
        "environment",
        "summary_decimal_digits",
        "precision_records",
        "scientific_summary",
        "candidate_terminal",
        "overall_stage_m_status",
        "exclusions",
        "execution_shards",
    }
    module = _load_static_oracle()
    assert result["schema"] == module.SCHEMA
    assert result["status"] == "complete"
    assert result["mode"] == "full"
    assert result["identities"] == identities
    environment = _validate_environment(
        result["environment"],
        baseline_environment,
        require_current=require_current_environment,
    )
    assert result["summary_decimal_digits"] == 320
    records = result["precision_records"]
    assert isinstance(records, list) and len(records) == 3
    assert [record["decimal_digits"] for record in records] == [80, 160, 320]
    for record, precision in zip(records, (80, 160, 320), strict=True):
        _validate_precision_record(record, precision, drill_cases)
    if expected_shards is not None:
        assert result["execution_shards"] == expected_shards
    else:
        provenance = result["execution_shards"]
        assert isinstance(provenance, list) and len(provenance) == 3
        assert [row["decimal_digits"] for row in provenance] == [80, 160, 320]
        for row in provenance:
            assert set(row) == {"decimal_digits", "raw_sha256", "bytes"}
            _assert_sha256_token(row["raw_sha256"])
            assert isinstance(row["bytes"], int) and row["bytes"] > 0
    assert result["exclusions"] == _expected_exclusions()
    summary = result["scientific_summary"]
    gate_statuses = {record["status"] for record in summary["gates"].values()}
    expected_terminal = (
        "NO_GO_CANDIDATE_B"
        if "PROVEN_FAIL" in gate_statuses
        else "UNCLASSIFIED_CANDIDATE_B"
    )
    assert result["candidate_terminal"] == summary["candidate_terminal"]
    assert result["candidate_terminal"] == expected_terminal
    assert result["candidate_terminal"] != "GO_CANDIDATE_B"
    assert result["overall_stage_m_status"] == summary["overall_stage_m_status"]
    assert result["overall_stage_m_status"] == "BLOCKED_PRIMARY_SOURCE_UNAVAILABLE"
    ledger = summary["inherited_execution_ledger"]
    assert len(ledger) == 174
    assert len({row["coverage_key"] for row in ledger}) == 174
    assert {row["status"] for row in ledger} == {"BORDERLINE"}
    return result, environment


def _artifact_record(path: Path) -> dict[str, Any]:
    _assert_safe_regular_file(path)
    raw = path.read_bytes()
    return {
        "filename": path.name,
        "raw_sha256": _raw_sha256_bytes(raw),
        "bytes": len(raw),
    }


def _assert_files_byte_identical(left: Path, right: Path) -> None:
    _assert_safe_regular_file(left)
    _assert_safe_regular_file(right)
    assert left.stat().st_size == right.stat().st_size
    with left.open("rb") as left_stream, right.open("rb") as right_stream:
        while True:
            left_chunk = left_stream.read(1024 * 1024)
            right_chunk = right_stream.read(1024 * 1024)
            assert left_chunk == right_chunk
            if not left_chunk:
                break


def _expected_completion(
    identities: dict[str, Any],
    environment: dict[str, Any],
    artifact_records: list[dict[str, Any]],
    terminal_result: dict[str, Any],
) -> dict[str, Any]:
    assert len(artifact_records) == 8
    return {
        "schema": COMPLETE_SCHEMA,
        "status": "complete",
        "identities": identities,
        "environment": environment,
        "candidate_terminal": terminal_result["candidate_terminal"],
        "overall_stage_m_status": terminal_result["overall_stage_m_status"],
        "artifacts": artifact_records,
    }


def _run_precision_shard_execution() -> Path:
    assert _raw_sha256(ORACLE) == ORACLE_SHA256
    assert _raw_sha256(CONTRACT) == CONTRACT_SHA256
    assert _raw_sha256(CASES) == CASES_SHA256
    assert _raw_sha256(INTERVAL) == INTERVAL_SHA256
    assert _raw_sha256(TIMEOUT_ADDENDUM) == TIMEOUT_ADDENDUM_SHA256
    execution, shard_paths, merge_paths, completion_path = _execution_configuration()
    _ensure_execution_directory()
    ordered_paths = [*shard_paths, *merge_paths, completion_path]
    _inventory_prefix(execution, ordered_paths)

    contract = _strict_json(CONTRACT)
    drill_cases = _strict_json(
        ROOT / "docs" / "reference_cases" / "s4_drill_constraint_cases.json"
    )
    assert isinstance(contract, dict) and isinstance(drill_cases, dict)
    identities = _expected_identities(contract)
    environment: dict[str, Any] | None = None
    artifact_records: list[dict[str, Any]] = []

    shard_precisions = [80, 160, 320, 80, 160, 320]
    for path, decimal_digits in zip(shard_paths, shard_precisions, strict=True):
        if _lexists(path):
            _assert_safe_regular_file(path)
            raw = path.read_bytes()
        else:
            _inventory_prefix(execution, ordered_paths)
            worker = _run_worker_bytes(
                "--precision-shard",
                str(decimal_digits),
                "--contract-sha256",
                CONTRACT_SHA256,
                timeout=SHARD_TIMEOUT_SECONDS_BY_PRECISION[decimal_digits],
            )
            assert worker.returncode == 0, worker.stderr.decode(
                "utf-8", errors="replace"
            )
            assert worker.stderr == b"", "precision shard emitted stderr"
            raw = worker.stdout
            _validate_shard_packet(
                raw,
                f"worker::{path.name}",
                decimal_digits,
                identities,
                drill_cases,
                environment,
            )
            _promote_canonical_exclusive(path, raw, execution["pending_suffix"])
        _, environment = _validate_shard_packet(
            raw,
            str(path),
            decimal_digits,
            identities,
            drill_cases,
            environment,
        )
        artifact_records.append(_artifact_record(path))

    assert environment is not None
    for left, right in zip(shard_paths[:3], shard_paths[3:], strict=True):
        _assert_files_byte_identical(left, right)

    terminal_result: dict[str, Any] | None = None
    for set_index, merge_path in enumerate(merge_paths):
        set_shards = shard_paths[set_index * 3 : (set_index + 1) * 3]
        shard_records = artifact_records[set_index * 3 : (set_index + 1) * 3]
        expected_provenance = [
            {
                "decimal_digits": precision,
                "raw_sha256": record["raw_sha256"],
                "bytes": record["bytes"],
            }
            for precision, record in zip((80, 160, 320), shard_records, strict=True)
        ]
        if _lexists(merge_path):
            _assert_safe_regular_file(merge_path)
            raw = merge_path.read_bytes()
        else:
            _inventory_prefix(execution, ordered_paths)
            worker = _run_worker_bytes(
                "--merge-shards",
                *(str(path.resolve(strict=True)) for path in set_shards),
                "--shard-sha256",
                *(record["raw_sha256"] for record in shard_records),
                "--contract-sha256",
                CONTRACT_SHA256,
                timeout=execution["merge_timeout_seconds"],
            )
            assert worker.returncode == 0, worker.stderr.decode(
                "utf-8", errors="replace"
            )
            assert worker.stderr == b"", "precision merge emitted stderr"
            raw = worker.stdout
            _validate_terminal_result(
                raw,
                f"worker::{merge_path.name}",
                identities,
                drill_cases,
                baseline_environment=environment,
                require_current_environment=True,
                expected_shards=expected_provenance,
            )
            _promote_canonical_exclusive(
                merge_path, raw, execution["pending_suffix"]
            )
        terminal_result, merged_environment = _validate_terminal_result(
            raw,
            str(merge_path),
            identities,
            drill_cases,
            baseline_environment=environment,
            require_current_environment=True,
            expected_shards=expected_provenance,
        )
        assert merged_environment == environment
        artifact_records.append(_artifact_record(merge_path))

    assert terminal_result is not None
    _assert_files_byte_identical(merge_paths[0], merge_paths[1])
    expected_completion = _expected_completion(
        identities, environment, artifact_records, terminal_result
    )
    completion_raw = _canonical_json_bytes(expected_completion)
    if _lexists(completion_path):
        _assert_safe_regular_file(completion_path)
        assert completion_path.read_bytes() == completion_raw
        assert _parse_canonical_json(completion_raw, str(completion_path)) == expected_completion
    else:
        _inventory_prefix(execution, ordered_paths)
        _promote_canonical_exclusive(
            completion_path, completion_raw, execution["pending_suffix"]
        )
    assert _inventory_prefix(execution, ordered_paths) == len(ordered_paths)
    return merge_paths[0]


def _validate_committed_full_output() -> None:
    assert _lexists(COMMITTED_OUTPUT), (
        "canonical Stage-M output is absent; local precision-shard execution and "
        "content-addressed materialization are required before default qualification"
    )
    _assert_safe_regular_file(COMMITTED_OUTPUT)
    assert OUTPUT_SHA256 != "0" * 64, "committed output SHA-256 was not rebound"
    assert _raw_sha256(COMMITTED_OUTPUT) == OUTPUT_SHA256
    contract = _strict_json(CONTRACT)
    drill_cases = _strict_json(
        ROOT / "docs" / "reference_cases" / "s4_drill_constraint_cases.json"
    )
    assert isinstance(contract, dict) and isinstance(drill_cases, dict)
    _validate_terminal_result(
        COMMITTED_OUTPUT.read_bytes(),
        str(COMMITTED_OUTPUT),
        _expected_identities(contract),
        drill_cases,
        baseline_environment=None,
        require_current_environment=False,
        expected_shards=None,
    )


def test_stage_m_static_contract_is_content_addressed_before_science() -> None:
    assert _raw_sha256(ORACLE) == ORACLE_SHA256
    assert _raw_sha256(CONTRACT) == CONTRACT_SHA256
    assert _raw_sha256(CASES) == CASES_SHA256
    assert _raw_sha256(INTERVAL) == INTERVAL_SHA256
    assert _raw_sha256(TIMEOUT_ADDENDUM) == TIMEOUT_ADDENDUM_SHA256

    contract = _strict_json(CONTRACT)
    module = _load_static_oracle()
    cases = module.load_cases()
    verified, verified_sha = module.load_contract(cases, CONTRACT_SHA256)
    assert verified_sha == CONTRACT_SHA256
    assert verified == contract == module.extract_contract(cases)
    assert contract["implementation_inputs"]["oracle"]["raw_sha256"] == ORACLE_SHA256
    assert contract["counts"]["required_execution_coverage"] == 174
    assert len(contract["coverage_map"]) == 174
    assert {
        row["executor_kind"] for row in contract["coverage_map"]
    } == {"unresolved_exact_executor"}


def test_stage_m_contract_mismatch_fails_before_science_imports() -> None:
    worker = _run_worker("--quick", "--contract-sha256", "0" * 64)
    assert worker.returncode == 2, worker.stderr
    result = json.loads(worker.stdout)
    assert result["status"] == "blocked"
    assert result["terminal"] == "BLOCKED_CONTRACT_VIOLATION"


def test_stage_m_quick_candidate_b_record_is_truthfully_fail_closed() -> None:
    worker = _run_worker(
        "--quick", "--summary", "--contract-sha256", CONTRACT_SHA256
    )
    assert worker.returncode == 0, worker.stderr
    result = json.loads(worker.stdout)
    assert result["status"] == "complete"
    assert result["mode"] == "quick"
    assert result["identities"]["oracle_sha256"] == ORACLE_SHA256
    assert result["identities"]["contract_sha256"] == CONTRACT_SHA256
    gate_statuses = {
        record["status"]
        for record in result["scientific_summary"]["gates"].values()
    }
    expected_terminal = (
        "NO_GO_CANDIDATE_B"
        if "PROVEN_FAIL" in gate_statuses
        else "UNCLASSIFIED_CANDIDATE_B"
    )
    assert result["candidate_terminal"] == expected_terminal
    assert result["candidate_terminal"] != "GO_CANDIDATE_B"
    assert result["overall_stage_m_status"] == "BLOCKED_PRIMARY_SOURCE_UNAVAILABLE"
    ledger = result["scientific_summary"]["inherited_execution_ledger"]
    assert len(ledger) == 174
    assert len({row["coverage_key"] for row in ledger}) == 174
    assert {row["status"] for row in ledger} == {"BORDERLINE"}
    assert all(value is False for value in result["exclusions"].values())


def test_stage_m_full_candidate_b_record_is_deterministic_and_fail_closed() -> None:
    opt_in = os.environ.get(FULL_EXECUTION_ENVIRONMENT)
    assert opt_in in (None, FULL_EXECUTION_VALUE), (
        f"{FULL_EXECUTION_ENVIRONMENT} accepts only the frozen execution value"
    )
    if opt_in == FULL_EXECUTION_VALUE:
        merged = _run_precision_shard_execution()
        assert merged == FULL_EVIDENCE_DIR / "set1_merged.json"
    else:
        _validate_committed_full_output()
