"""Bounded coordinator for the formal S3 V2A Stage-4A funnel.

The coordinator validates the frozen Git candidate before numerical imports,
creates an exact source archive and three-shard producer manifest, runs the
existing Windows Job-Object wave, then runs two independent checker replicas
per shard.  It publishes one canonical aggregate only after every launched
process has reached a proven terminal state.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
from typing import Any, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[2]
REFERENCE_CASES = ROOT / "docs" / "reference_cases"
AUTHORITY_PATH = REFERENCE_CASES / "e4_pl_s3_v2_stage4a_authority.json"
MANIFEST_PATH = REFERENCE_CASES / "e4_pl_s3_mixed_mesh_connectivity_manifest.json"
SCAFFOLD_CONTRACT_PATH = REFERENCE_CASES / "e4_pl_s3_v2_flat_funnel_contract.json"
SOURCE_CONTRACT_PATH = REFERENCE_CASES / "e4_pl_s3_v2_source_equation_contract.json"
PRODUCER_PATH = REFERENCE_CASES / "e4_pl_s3_v2_flat_funnel_producer.py"
CHECKER_PATH = REFERENCE_CASES / "e4_pl_s3_v2_flat_funnel_checker.py"
FUNNEL_PATH = REFERENCE_CASES / "e4_pl_s3_v2_flat_funnel.py"
BOUNDED_PATH = REFERENCE_CASES / "e4_pl_s3_v2_bounded_process.py"

CONTRACT_SCHEMA = "anysolver.e4-pl-s3-v2-stage4a-contract-v2"
AUTHORIZATION_SCHEMA = "anysolver.e4-pl-s3-v2-stage4a-execution-authorization-v2"
AUTHORITY_SCHEMA = "anysolver.e4-pl-s3-v2-stage4a-authority-v3"
REVIEW_SCHEMA = "anysolver.e4-pl-s3-v2-stage4a-implementation-review-v1"
AGGREGATE_SCHEMA = "anysolver.e4-pl-s3-v2-stage4a-aggregate-v2"
CHECKER_RESULT_SCHEMA = "anysolver.e4-pl-s3-v2-phase4a-checker-result-v1"
PRODUCER_RESULT_SCHEMA = "anysolver.e4-pl-s3-v2-bounded-wave-result-v1"
BLOCKED = "BLOCKED_E4_PL_S3_V2_PROCESS_OR_EVIDENCE"
NO_GO = "NO_GO_E4_PL_S3_V2A_MIXED_FLEXURAL_CONVERGENCE"
PASS = "PASS_E4_PL_S3_V2A_FLAT_FUNNEL_PHASE_4A"
PRODUCTION_RESTRICTION = "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"
CHECKER_WALL_SECONDS = 300
WAVE_WALL_SECONDS = 1800
MEMORY_LIMIT_BYTES = 24 * (1 << 30)
EXPECTED_SHARDS = {
    "S3_V2_FLAT_4A_SLASH": "slash",
    "S3_V2_FLAT_4A_BACKSLASH": "backslash",
    "S3_V2_FLAT_4A_ALTERNATING": "alternating",
}
DIAGONAL_ORDER = ("slash", "backslash", "alternating")
MASK_ORDER = ("dispersed", "chain")
FRACTION_ORDER = (1, 5, 10, 25)
RESOURCE_MANAGER_ROOT = Path(r"C:\Github\.resource-manager")
RESOURCE_LEDGER_PATH = RESOURCE_MANAGER_ROOT / "ledger.md"
RESOURCE_LOCK_OWNER_PATH = RESOURCE_MANAGER_ROOT / "active-lock" / "owner.json"
PROCESS_REVIEW_PATH = (
    REFERENCE_CASES / "e4_pl_s3_v2_stage4a_process_implementation_review.json"
)
SCIENTIFIC_REVIEW_PATH = (
    REFERENCE_CASES / "e4_pl_s3_v2_stage4a_scientific_implementation_review.json"
)
EXPECTED_REVIEW_VERDICTS = {
    "PROCESS_AND_AUTHORITY": "ACCEPT_STAGE4A_PROCESS_IMPLEMENTATION_NO_P0_P1",
    "SCIENTIFIC_AND_MECHANICS": "ACCEPT_STAGE4A_SCIENTIFIC_IMPLEMENTATION_NO_P0_P1",
}
REQUIRED_FROZEN_PATHS = {
    "docs/reference_cases/e4_pl_s3_mixed_mesh_connectivity_manifest.json",
    "docs/reference_cases/e4_pl_s3_v2_bounded_process.py",
    "docs/reference_cases/e4_pl_s3_v2_candidate_binding.json",
    "docs/reference_cases/e4_pl_s3_v2_flat_funnel.py",
    "docs/reference_cases/e4_pl_s3_v2_flat_funnel_checker.py",
    "docs/reference_cases/e4_pl_s3_v2_flat_funnel_contract.json",
    "docs/reference_cases/e4_pl_s3_v2_flat_funnel_producer.py",
    "docs/reference_cases/e4_pl_s3_v2_source_equation_contract.json",
    "docs/reference_cases/e4_pl_s3_v2_stage4a_authority.json",
    "docs/reference_cases/e4_pl_s3_v2_stage4a_coordinator.py",
    "src/anysolver/e4_pl_element.py",
    "src/anysolver/e4_pl_s3_element.py",
    "src/anysolver/e4_pl_s3_v2_element.py",
    "tests/test_e4_pl_s3_v2_candidate_binding.py",
    "tests/test_e4_pl_s3_v2_flat_candidate_review.py",
    "tests/test_e4_pl_s3_v2_flat_funnel_checker.py",
    "tests/test_e4_pl_s3_v2_flat_funnel_producer.py",
    "tests/test_e4_pl_s3_v2_mixed_scope.py",
    "tests/test_e4_pl_s3_v2_stage4a_authority.py",
    "tests/test_e4_pl_s3_v2_stage4a_coordinator.py",
}
DEPENDENCY_REPOSITORIES = (
    ("ANYmaterial", Path(r"C:\Github\ANYmaterial")),
    ("ANYgeometry", Path(r"C:\Github\ANYgeometry")),
    (
        "ANYmesh",
        Path(
            r"C:\Github\ANYsolver\.perf2-worktrees\s3-v2-stage4a-anymesh-dependency"
        ),
    ),
    ("ANYfileIO", Path(r"C:\Github\ANYfileIO")),
)


class CoordinatorError(RuntimeError):
    """Raised when formal process or evidence authority is incomplete."""


def _load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise CoordinatorError(f"cannot load registered program: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(name, None)
    return module


def _reject_constant(value: str) -> None:
    raise CoordinatorError(f"non-finite JSON constant is forbidden: {value}")


def _reject_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    made: dict[str, Any] = {}
    for key, value in pairs:
        if key in made:
            raise CoordinatorError(f"duplicate JSON key is forbidden: {key}")
        made[key] = value
    return made


def strict_json_bytes(raw: bytes, label: str) -> Any:
    try:
        return json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_reject_pairs,
            parse_constant=_reject_constant,
        )
    except (UnicodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
        if isinstance(exc, CoordinatorError):
            raise
        raise CoordinatorError(f"{label} is invalid strict JSON: {exc}") from exc


def strict_json_load(path: Path) -> tuple[Any, bytes]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise CoordinatorError(f"cannot read {path}: {exc}") from exc
    return strict_json_bytes(raw, str(path)), raw


def canonical_bytes(value: Any) -> bytes:
    def visit(item: Any, location: str) -> None:
        if item is None or isinstance(item, (bool, int, str)):
            return
        if isinstance(item, float):
            if not math.isfinite(item):
                raise CoordinatorError(f"non-finite number at {location}")
            return
        if isinstance(item, list):
            for index, member in enumerate(item):
                visit(member, f"{location}[{index}]")
            return
        if isinstance(item, dict):
            for key, member in item.items():
                if not isinstance(key, str):
                    raise CoordinatorError(f"non-string key at {location}")
                visit(member, f"{location}.{key}")
            return
        raise CoordinatorError(f"unsupported canonical value at {location}")

    visit(value, "$")
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        + "\n"
    ).encode("ascii")


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def _exact(value: Any, keys: set[str], location: str) -> Mapping[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        actual = sorted(value) if isinstance(value, dict) else type(value).__name__
        raise CoordinatorError(
            f"{location} keys differ: expected={sorted(keys)} actual={actual}"
        )
    return value


def _digest(value: Any, location: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789ABCDEF" for character in value)
    ):
        raise CoordinatorError(f"{location} must be an uppercase SHA-256")
    return value


def _lower_object(value: Any, location: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 40
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise CoordinatorError(f"{location} must be a lowercase SHA-1 Git object")
    return value


def _repo_relative_path(value: Any, location: str, *, regular_file: bool = True) -> Path:
    if not isinstance(value, str) or not value or "\\" in value:
        raise CoordinatorError(f"{location} must be a repository-relative POSIX path")
    pure = PurePosixPath(value)
    if pure.is_absolute() or any(part in {"", ".", ".."} for part in pure.parts):
        raise CoordinatorError(f"{location} escapes the repository")
    lexical = ROOT.joinpath(*pure.parts)
    resolved = lexical.resolve()
    try:
        resolved.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise CoordinatorError(f"{location} resolves outside the repository") from exc
    if regular_file and (not resolved.is_file() or resolved.is_symlink()):
        raise CoordinatorError(f"{location} is not a regular non-link file")
    return resolved


def _strict_external_json(path: Path, location: str) -> tuple[Any, bytes]:
    try:
        raw = path.read_bytes()
        text = raw.decode("utf-8-sig")
        value = json.loads(
            text,
            object_pairs_hook=_reject_pairs,
            parse_constant=_reject_constant,
        )
    except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
        if isinstance(exc, CoordinatorError):
            raise
        raise CoordinatorError(f"{location} is invalid strict JSON: {exc}") from exc
    return value, raw


def _nonnegative_integer(value: Any, location: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise CoordinatorError(f"{location} must be a nonnegative integer")
    return value


def _validate_sequence_results(
    value: Any,
    *,
    assignment_id: str,
) -> list[Mapping[str, Any]]:
    if not isinstance(value, list) or len(value) != 8:
        raise CoordinatorError(
            f"checker shard must contain exactly eight sequences: {assignment_id}"
        )
    expected_coordinates = {
        (mask, fraction) for mask in MASK_ORDER for fraction in FRACTION_ORDER
    }
    made_coordinates: set[tuple[str, int]] = set()
    checked: list[Mapping[str, Any]] = []
    keys = {
        "advisory_triggered",
        "all_q4_response_slope",
        "energy_norm_slope",
        "energy_norm_slope_lower_95_percent",
        "energy_norm_values",
        "failed_subgates",
        "finest_error_ratio_to_all_q4",
        "fraction_percent",
        "mask",
        "record_ids",
        "response_error_slope",
        "response_errors",
        "slope_deficit_from_all_q4",
        "successive_refinement_passed",
    }
    for index, raw_sequence in enumerate(value):
        sequence = _exact(
            raw_sequence,
            keys,
            f"$.checker[{assignment_id}].sequence_results[{index}]",
        )
        mask = sequence["mask"]
        fraction = sequence["fraction_percent"]
        if (
            mask not in MASK_ORDER
            or isinstance(fraction, bool)
            or not isinstance(fraction, int)
        ):
            raise CoordinatorError("checker sequence coordinate is invalid")
        coordinate = (str(mask), fraction)
        if coordinate in made_coordinates:
            raise CoordinatorError("checker sequence coordinate is duplicated")
        made_coordinates.add(coordinate)
        if (
            not isinstance(sequence["advisory_triggered"], bool)
            or not isinstance(sequence["successive_refinement_passed"], bool)
            or not isinstance(sequence["failed_subgates"], list)
            or any(
                not isinstance(failure, str)
                for failure in sequence["failed_subgates"]
            )
            or not isinstance(sequence["record_ids"], list)
            or len(sequence["record_ids"]) != 3
            or any(not isinstance(record_id, str) for record_id in sequence["record_ids"])
        ):
            raise CoordinatorError("checker sequence evidence is malformed")
        checked.append(sequence)
    if made_coordinates != expected_coordinates:
        raise CoordinatorError("checker sequence coverage differs")
    return checked


def _validate_checker_result(
    wrapper: Mapping[str, Any],
    *,
    expected_assignment_id: str,
    expected_proof: Mapping[str, Any],
) -> tuple[Mapping[str, Any], bytes]:
    wrapper = _exact(
        wrapper,
        {
            "assignment_id",
            "cpu_100ns",
            "output_path",
            "output_sha256",
            "peak_tree_memory_bytes",
            "proof_path",
            "proof_sha256",
            "stderr_sha256",
            "stdout_sha256",
            "termination_proven",
            "value",
        },
        "$.checker_wrapper",
    )
    if (
        wrapper["assignment_id"] != expected_assignment_id
        or wrapper["termination_proven"] is not True
    ):
        raise CoordinatorError("checker wrapper identity or termination differs")
    _nonnegative_integer(wrapper["cpu_100ns"], "$.checker_wrapper.cpu_100ns")
    _nonnegative_integer(
        wrapper["peak_tree_memory_bytes"],
        "$.checker_wrapper.peak_tree_memory_bytes",
    )
    for key in ("output_sha256", "stderr_sha256", "stdout_sha256"):
        _digest(wrapper[key], f"$.checker_wrapper.{key}")
    proof_path = Path(str(wrapper["proof_path"])).resolve()
    if (
        not proof_path.is_file()
        or proof_path.is_symlink()
        or proof_path != Path(str(expected_proof["proof_path"])).resolve()
        or wrapper["proof_sha256"] != expected_proof["proof_sha256"]
        or sha256(proof_path.read_bytes()) != expected_proof["proof_sha256"]
    ):
        raise CoordinatorError("checker wrapper proof binding differs")
    output_path = Path(str(wrapper["output_path"]))
    if not output_path.is_absolute() or not output_path.is_file():
        raise CoordinatorError("checker output path is not an absolute regular file")
    output_value, output_raw = strict_json_load(output_path)
    if output_raw != canonical_bytes(output_value):
        raise CoordinatorError("checker output is not canonical JSON")
    if sha256(output_raw) != wrapper["output_sha256"]:
        raise CoordinatorError("checker output wrapper hash differs")
    if output_value != wrapper["value"]:
        raise CoordinatorError("checker wrapper value differs from its output")
    result = _exact(
        output_value,
        {
            "advisory_review_required",
            "assignment_id",
            "assignment_sha256",
            "classifying_record_count",
            "diagonal",
            "formal_failures",
            "plan_sha256",
            "production_restriction",
            "proof_sha256",
            "schema",
            "sequence_results",
            "successor_expansion_authorized",
            "terminal",
            "v1_diagnostic_record_count",
        },
        f"$.checker[{expected_assignment_id}]",
    )
    classifying_count = _nonnegative_integer(
        result["classifying_record_count"],
        f"$.checker[{expected_assignment_id}].classifying_record_count",
    )
    v1_count = _nonnegative_integer(
        result["v1_diagnostic_record_count"],
        f"$.checker[{expected_assignment_id}].v1_diagnostic_record_count",
    )
    if (
        result["schema"] != CHECKER_RESULT_SCHEMA
        or result["assignment_id"] != expected_assignment_id
        or result["diagonal"] != EXPECTED_SHARDS[expected_assignment_id]
        or classifying_count != 27
        or v1_count != 24
        or result["production_restriction"] != PRODUCTION_RESTRICTION
    ):
        raise CoordinatorError("checker result identity or coverage differs")
    for key in ("assignment_sha256", "plan_sha256", "proof_sha256"):
        _digest(result[key], f"$.checker[{expected_assignment_id}].{key}")
    if (
        result["assignment_sha256"] != expected_proof["assignment_sha256"]
        or result["plan_sha256"] != expected_proof["plan_sha256"]
        or result["proof_sha256"] != expected_proof["proof_sha256"]
    ):
        raise CoordinatorError("checker result is not joined to its producer proof")
    failures = result["formal_failures"]
    if (
        not isinstance(failures, list)
        or any(not isinstance(failure, str) for failure in failures)
        or failures != sorted(set(failures))
    ):
        raise CoordinatorError("checker formal failures are not canonical")
    terminal = result["terminal"]
    if terminal not in (PASS, NO_GO) or (terminal == NO_GO) != bool(failures):
        raise CoordinatorError("checker terminal and formal failures disagree")
    if not isinstance(result["advisory_review_required"], bool):
        raise CoordinatorError("checker advisory disposition is not Boolean")
    expected_expansion = terminal == PASS and not result["advisory_review_required"]
    if result["successor_expansion_authorized"] is not expected_expansion:
        raise CoordinatorError("checker successor disposition differs")
    sequences = _validate_sequence_results(
        result["sequence_results"], assignment_id=expected_assignment_id
    )
    sequence_failures = sorted(
        f"{sequence['mask']}:{sequence['fraction_percent']}:{failure}"
        for sequence in sequences
        for failure in sequence["failed_subgates"]
    )
    if sequence_failures != failures:
        raise CoordinatorError("checker sequence and shard failures disagree")
    advisory = any(bool(sequence["advisory_triggered"]) for sequence in sequences)
    if result["advisory_review_required"] is not bool(advisory and not failures):
        raise CoordinatorError("checker sequence and shard advisory differs")
    return result, output_raw


def _git_environment() -> dict[str, str]:
    environment = dict(os.environ)
    for key in tuple(environment):
        if key in {
            "GIT_ALTERNATE_OBJECT_DIRECTORIES",
            "GIT_ATTR_SOURCE",
            "GIT_CEILING_DIRECTORIES",
            "GIT_COMMON_DIR",
            "GIT_CONFIG",
            "GIT_CONFIG_COUNT",
            "GIT_CONFIG_SYSTEM",
            "GIT_DIR",
            "GIT_DISCOVERY_ACROSS_FILESYSTEM",
            "GIT_EXTERNAL_DIFF",
            "GIT_INDEX_FILE",
            "GIT_OBJECT_DIRECTORY",
            "GIT_NAMESPACE",
            "GIT_SHALLOW_FILE",
            "GIT_WORK_TREE",
        } or key.startswith(("GIT_CONFIG_KEY_", "GIT_CONFIG_VALUE_")):
            environment.pop(key, None)
    environment.update(
        {
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_ATTR_NOSYSTEM": "1",
            "GIT_NO_REPLACE_OBJECTS": "1",
            "GIT_OPTIONAL_LOCKS": "0",
        }
    )
    return environment


def _git_runtime_paths() -> tuple[Path, Path]:
    launcher_text = shutil.which("git")
    if launcher_text is None:
        raise CoordinatorError("registered Git launcher cannot be resolved")
    launcher = Path(launcher_text).resolve()
    if os.name == "nt":
        engine = (launcher.parent.parent / "mingw64" / "bin" / "git.exe").resolve()
    else:
        engine = launcher
    for label, path in (("launcher", launcher), ("engine", engine)):
        if not path.is_file() or path.is_symlink():
            raise CoordinatorError(f"Git {label} is not a regular non-link file")
    return launcher, engine


def _discover_git_runtime() -> dict[str, Any]:
    launcher, engine = _git_runtime_paths()
    completed_version = subprocess.run(
        [str(engine), "--version"],
        cwd=ROOT,
        env=_git_environment(),
        check=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    completed_exec = subprocess.run(
        [str(engine), "--exec-path"],
        cwd=ROOT,
        env=_git_environment(),
        check=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    exec_path = Path(completed_exec.stdout.decode("utf-8").strip()).resolve()
    if not exec_path.is_dir() or exec_path.is_symlink():
        raise CoordinatorError("Git exec path is not a regular directory")
    return {
        "engine_byte_count": engine.stat().st_size,
        "engine_path": str(engine),
        "engine_sha256": sha256(engine.read_bytes()),
        "exec_path": str(exec_path),
        "launcher_byte_count": launcher.stat().st_size,
        "launcher_path": str(launcher),
        "launcher_sha256": sha256(launcher.read_bytes()),
        "version": completed_version.stdout.decode("utf-8").strip(),
    }


def _git_command(*arguments: str, repository: Path = ROOT) -> list[str]:
    _launcher, engine = _git_runtime_paths()
    return [
        str(engine),
        "-c",
        f"safe.directory={repository.resolve()}",
        "-c",
        "core.autocrlf=true",
        "-c",
        "core.attributesfile=NUL",
        "-c",
        "extensions.objectformat=sha1",
        *arguments,
    ]


def _git_run(
    *arguments: str,
    check: bool = True,
    stdout: Any = subprocess.PIPE,
    repository: Path = ROOT,
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        _git_command(*arguments, repository=repository),
        cwd=repository,
        env=_git_environment(),
        check=check,
        stdin=subprocess.DEVNULL,
        stdout=stdout,
        stderr=subprocess.PIPE,
    )


def _git(
    *arguments: str,
    binary: bool = False,
    repository: Path = ROOT,
) -> bytes | str:
    completed = _git_run(*arguments, repository=repository)
    return completed.stdout if binary else completed.stdout.decode("utf-8").strip()


def _validate_git_object_authority(repository: Path = ROOT) -> None:
    included = _git_run(
        "config",
        "--local",
        "--no-includes",
        "--get-regexp",
        r"^include(If)?\.",
        check=False,
        repository=repository,
    )
    if included.returncode not in {0, 1} or included.stdout.strip():
        raise CoordinatorError("repository-local Git config includes are forbidden")
    attributes_setting = _git_run(
        "config",
        "--local",
        "--no-includes",
        "--get-all",
        "core.attributesfile",
        check=False,
        repository=repository,
    )
    if attributes_setting.returncode not in {0, 1} or attributes_setting.stdout.strip():
        raise CoordinatorError("repository-local external attributes are forbidden")
    if _git(
        "for-each-ref",
        "--format=%(refname)",
        "refs/replace",
        repository=repository,
    ):
        raise CoordinatorError("Git replacement objects are forbidden")
    common = Path(
        str(_git("rev-parse", "--git-common-dir", repository=repository))
    )
    if not common.is_absolute():
        common = (repository / common).resolve()
    git_dir = Path(str(_git("rev-parse", "--git-dir", repository=repository)))
    if not git_dir.is_absolute():
        git_dir = (repository / git_dir).resolve()
    forbidden = {
        common / "info" / "attributes": "Git common attributes",
        common / "info" / "grafts": "Git graft authority",
        common / "objects" / "info" / "alternates": "Git object alternates",
        common / "objects" / "info" / "http-alternates": "Git HTTP alternates",
        git_dir / "info" / "attributes": "Git worktree attributes",
    }
    for path, label in forbidden.items():
        if os.path.lexists(path):
            raise CoordinatorError(f"{label} is forbidden")


def _git_blob_sha256(commit: str, path: str) -> str:
    return sha256(_git("show", f"{commit}:{path}", binary=True))


def validate_contract(path: Path) -> tuple[Mapping[str, Any], bytes]:
    value, raw = strict_json_load(path)
    if raw != canonical_bytes(value):
        raise CoordinatorError("Stage 4A contract is not canonical JSON")
    contract = _exact(
        value,
        {
            "adjudication",
            "authority",
            "candidate",
            "coverage",
            "dependencies",
            "execution",
            "frozen_files",
            "git_authority",
            "production_boundary",
            "protocol",
            "schema",
            "stage",
        },
        "$contract",
    )
    if contract["schema"] != CONTRACT_SCHEMA or contract["stage"] != "STAGE_4A":
        raise CoordinatorError("Stage 4A contract identity differs")
    git_authority = _exact(
        contract["git_authority"],
        {
            "engine_byte_count",
            "engine_path",
            "engine_sha256",
            "exec_path",
            "launcher_byte_count",
            "launcher_path",
            "launcher_sha256",
            "version",
        },
        "$.contract.git_authority",
    )
    discovered_git = _discover_git_runtime()
    if git_authority != discovered_git:
        raise CoordinatorError("registered Git launcher or engine identity differs")
    _validate_git_object_authority()
    authority_value, authority_raw = strict_json_load(AUTHORITY_PATH)
    if authority_raw != canonical_bytes(authority_value):
        raise CoordinatorError("Stage 4A authority is not canonical JSON")
    if authority_value.get("schema") != AUTHORITY_SCHEMA:
        raise CoordinatorError("Stage 4A authority schema differs")
    authority = _exact(
        contract["authority"],
        {"commit", "path", "schema", "sha256", "tree"},
        "$.contract.authority",
    )
    authority_commit = _lower_object(authority["commit"], "$.contract.authority.commit")
    authority_tree = _lower_object(authority["tree"], "$.contract.authority.tree")
    authority_path = _repo_relative_path(authority["path"], "$.contract.authority.path")
    if (
        authority_path != AUTHORITY_PATH.resolve()
        or authority["schema"] != AUTHORITY_SCHEMA
        or authority["sha256"] != sha256(authority_raw)
        or _git("rev-parse", authority_commit) != authority_commit
        or _git("rev-parse", f"{authority_commit}^{{tree}}") != authority_tree
        or _git_blob_sha256(authority_commit, str(authority["path"])) != sha256(authority_raw)
    ):
        raise CoordinatorError("Stage 4A authority binding differs")
    candidate = _exact(
        contract["candidate"],
        {"changed_paths", "commit", "scope_base_commit", "subject", "tree"},
        "$.contract.candidate",
    )
    commit = _lower_object(candidate["commit"], "$.contract.candidate.commit")
    tree = _lower_object(candidate["tree"], "$.contract.candidate.tree")
    scope_base = _lower_object(
        candidate["scope_base_commit"], "$.contract.candidate.scope_base_commit"
    )
    if (
        _git("rev-parse", commit) != commit
        or _git("rev-parse", f"{commit}^{{tree}}") != tree
        or _git("show", "-s", "--format=%s", commit) != candidate["subject"]
        or scope_base != authority_value["scope_base"]["commit"]
    ):
        raise CoordinatorError("frozen candidate Git identity differs")
    if _git_run("merge-base", "--is-ancestor", commit, "HEAD", check=False).returncode:
        raise CoordinatorError("frozen candidate is not an ancestor of execution HEAD")
    if _git("status", "--porcelain=v1", "--untracked-files=all"):
        raise CoordinatorError("formal Stage 4A input worktree is dirty")
    changed_paths = candidate["changed_paths"]
    if (
        not isinstance(changed_paths, list)
        or any(not isinstance(item, str) for item in changed_paths)
        or changed_paths != sorted(set(changed_paths))
    ):
        raise CoordinatorError("candidate changed-path set is not canonical")
    registered_extent = sorted(
        authority_value["allowed_extent"]["authority_commit_paths"]
        + authority_value["allowed_extent"]["implementation_paths"]
    )
    actual_changed = sorted(
        filter(
            None,
            str(
                _git(
                    "diff",
                    "--no-ext-diff",
                    "--name-only",
                    scope_base,
                    commit,
                    "--",
                )
            ).splitlines(),
        )
    )
    if changed_paths != registered_extent or changed_paths != actual_changed:
        raise CoordinatorError("candidate changed-path extent differs")
    dependencies = contract["dependencies"]
    if not isinstance(dependencies, list) or len(dependencies) != len(
        DEPENDENCY_REPOSITORIES
    ):
        raise CoordinatorError("Stage 4A dependency graph differs")
    for index, ((expected_name, expected_root), raw_dependency) in enumerate(
        zip(DEPENDENCY_REPOSITORIES, dependencies)
    ):
        dependency = _exact(
            raw_dependency,
            {"commit", "name", "path", "source_path", "tree"},
            f"$.contract.dependencies[{index}]",
        )
        repository = Path(str(dependency["path"])).resolve()
        source = Path(str(dependency["source_path"])).resolve()
        dependency_commit = _lower_object(
            dependency["commit"], f"$.contract.dependencies[{index}].commit"
        )
        dependency_tree = _lower_object(
            dependency["tree"], f"$.contract.dependencies[{index}].tree"
        )
        if (
            dependency["name"] != expected_name
            or repository != expected_root.resolve()
            or source != (expected_root / "src").resolve()
            or not source.is_dir()
        ):
            raise CoordinatorError("Stage 4A dependency path or order differs")
        _validate_git_object_authority(repository)
        if (
            _git("rev-parse", "HEAD", repository=repository) != dependency_commit
            or _git(
                "rev-parse",
                f"{dependency_commit}^{{tree}}",
                repository=repository,
            )
            != dependency_tree
            or _git(
                "status",
                "--porcelain=v1",
                "--untracked-files=all",
                repository=repository,
            )
        ):
            raise CoordinatorError(f"Stage 4A dependency is dirty or differs: {expected_name}")
    files = contract["frozen_files"]
    if not isinstance(files, list) or not files:
        raise CoordinatorError("Stage 4A frozen-file graph is empty")
    seen: set[str] = set()
    roles: set[str] = set()
    for index, raw_binding in enumerate(files):
        binding = _exact(
            raw_binding,
            {"git_blob_sha256", "path", "role"},
            f"$.contract.frozen_files[{index}]",
        )
        made_path = str(binding["path"])
        _repo_relative_path(made_path, f"$.contract.frozen_files[{index}].path")
        role = binding["role"]
        if (
            made_path in seen
            or not isinstance(role, str)
            or not role
            or role in roles
        ):
            raise CoordinatorError("Stage 4A frozen-file path is absent or duplicated")
        seen.add(made_path)
        roles.add(role)
        if _git_blob_sha256(commit, made_path) != _digest(
            binding["git_blob_sha256"], f"$.contract.frozen_files[{index}].git_blob_sha256"
        ):
            raise CoordinatorError(f"frozen Git blob differs: {made_path}")
        if _git_run(
            "diff", "--no-ext-diff", "--quiet", commit, "--", made_path, check=False
        ).returncode:
            raise CoordinatorError(f"working file differs from frozen candidate: {made_path}")
    if seen != REQUIRED_FROZEN_PATHS or [item["path"] for item in files] != sorted(seen):
        raise CoordinatorError("Stage 4A frozen-file graph coverage or order differs")
    if contract["coverage"] != {
        "classifying_records": 81,
        "records_per_diagonal_shard": 27,
        "v1_diagnostic_records": 72,
    }:
        raise CoordinatorError("Stage 4A coverage contract differs")
    if contract["execution"] != {
        "checker_replica_wall_seconds": 300,
        "checker_replicas_per_shard": 2,
        "inactivity_seconds": 300,
        "maximum_memory_gib_per_process_tree": 24,
        "maximum_workers": 3,
        "no_automatic_retry": True,
        "numerical_library_threads_per_worker": 1,
        "producer_wall_seconds": 900,
        "wave_wall_seconds": 1800,
    }:
        raise CoordinatorError("Stage 4A bounded execution contract differs")
    if contract["production_boundary"] != {
        "default_s3_formulation": "legacy-s3",
        "default_s3_unchanged": True,
        "q4_default": "e4-pl",
        "q4_mechanics_unchanged": True,
        "v1_fallback_forbidden": True,
    }:
        raise CoordinatorError("Stage 4A production boundary differs")
    if contract["protocol"] != authority_value["formal_protocol"]:
        raise CoordinatorError("Stage 4A scientific protocol differs from authority")
    if contract["adjudication"] != {
        "advisory_policy": authority_value["advisory_policy"],
        "production_restriction": PRODUCTION_RESTRICTION,
        "terminal_precedence": [BLOCKED, NO_GO, PASS],
    }:
        raise CoordinatorError("Stage 4A adjudication contract differs")
    return contract, raw


def _review_inputs(contract: Mapping[str, Any], contract_raw: bytes) -> dict[str, str]:
    return {
        "candidate_commit": str(contract["candidate"]["commit"]),
        "candidate_tree": str(contract["candidate"]["tree"]),
        "changed_paths_sha256": sha256(canonical_bytes(contract["candidate"]["changed_paths"])),
        "contract_sha256": sha256(contract_raw),
        "dependency_graph_sha256": sha256(canonical_bytes(contract["dependencies"])),
        "frozen_file_graph_sha256": sha256(canonical_bytes(contract["frozen_files"])),
    }


def _validate_review(
    path: Path,
    *,
    role: str,
    expected_inputs: Mapping[str, str],
) -> tuple[Mapping[str, Any], bytes]:
    value, raw = strict_json_load(path)
    if raw != canonical_bytes(value):
        raise CoordinatorError("implementation review is not canonical JSON")
    review = _exact(
        value,
        {"findings", "reviewed_inputs", "reviewer_independence", "schema", "verdict"},
        "$.review",
    )
    findings = _exact(review["findings"], {"P0", "P1"}, "$.review.findings")
    independence = _exact(
        review["reviewer_independence"],
        {
            "authored_candidate",
            "independent_of_other_reviewer",
            "reviewer_id",
            "reviewer_role",
        },
        "$.review.reviewer_independence",
    )
    if (
        review["schema"] != REVIEW_SCHEMA
        or review["verdict"] != EXPECTED_REVIEW_VERDICTS[role]
        or findings != {"P0": [], "P1": []}
        or review["reviewed_inputs"] != expected_inputs
        or independence["authored_candidate"] is not False
        or independence["independent_of_other_reviewer"] is not True
        or independence["reviewer_role"] != role
        or not isinstance(independence["reviewer_id"], str)
        or not independence["reviewer_id"]
    ):
        raise CoordinatorError("implementation review does not accept the exact freeze")
    return review, raw


def _powershell_quote(value: str | Path) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def expected_resource_command(
    *,
    python_executable: Path,
    contract_path: Path,
    authorization_path: Path,
    output_root: Path,
    aggregate_path: Path,
) -> str:
    dependency_path = ";".join(
        str((repository / "src").resolve())
        for _name, repository in DEPENDENCY_REPOSITORIES
    )
    parts = [
        f"$env:PYTHONPATH={_powershell_quote(dependency_path)};",
        "$env:PYTHONNOUSERSITE='1';",
        "$env:PYTHONDONTWRITEBYTECODE='1';",
        "&",
        _powershell_quote(python_executable.resolve()),
        "-I",
        "-B",
        _powershell_quote(Path(__file__).resolve()),
        _powershell_quote("--run-stage4a"),
        _powershell_quote("--contract"),
        _powershell_quote(contract_path.resolve()),
        _powershell_quote("--authorization"),
        _powershell_quote(authorization_path.resolve()),
        _powershell_quote("--output-root"),
        _powershell_quote(output_root.resolve()),
        _powershell_quote("--aggregate"),
        _powershell_quote(aggregate_path.resolve()),
    ]
    return " ".join(parts)


def _validate_approval_snapshot(
    path: Path,
    *,
    contract: Mapping[str, Any],
    request_id: str,
    request_path: Path,
    request_raw: bytes,
) -> tuple[Mapping[str, Any], bytes]:
    value, raw = strict_json_load(path)
    if raw != canonical_bytes(value):
        raise CoordinatorError("resource approval snapshot is not canonical JSON")
    snapshot = _exact(
        value,
        {"approved_row", "candidate", "ledger", "request", "schema"},
        "$.approval_snapshot",
    )
    approved = _exact(
        snapshot["approved_row"], {"line", "sha256"}, "$.approval_snapshot.approved_row"
    )
    ledger = _exact(
        snapshot["ledger"],
        {"byte_count", "path", "sha256", "snapshot_path"},
        "$.approval_snapshot.ledger",
    )
    request = _exact(
        snapshot["request"],
        {"byte_count", "path", "request_id", "sha256"},
        "$.approval_snapshot.request",
    )
    line = approved["line"]
    ledger_snapshot_path = Path(str(ledger["snapshot_path"])).resolve()
    ledger_byte_count = _nonnegative_integer(
        ledger["byte_count"], "$.approval_snapshot.ledger.byte_count"
    )
    if (
        not ledger_snapshot_path.is_file()
        or ledger_snapshot_path.is_symlink()
        or ledger_snapshot_path.parent != path.parent.resolve()
        or ledger_snapshot_path.name != "resource-ledger-pre-run.md"
    ):
        raise CoordinatorError("preserved pre-run ledger snapshot path differs")
    ledger_raw = ledger_snapshot_path.read_bytes()
    if (
        snapshot["schema"] != "anysolver.e4-pl-s3-v2-stage4a-approval-snapshot-v2"
        or snapshot["candidate"]
        != {"commit": contract["candidate"]["commit"], "tree": contract["candidate"]["tree"]}
        or not isinstance(line, str)
        or "\n" in line
        or f"| {request_id} | APPROVED |" not in line
        or approved["sha256"] != sha256((line.rstrip() + "\n").encode("utf-8"))
        or ledger["path"] != str(RESOURCE_LEDGER_PATH)
        or ledger_byte_count != len(ledger_raw)
        or ledger_byte_count <= 0
        or ledger["sha256"] != sha256(ledger_raw)
        or request
        != {
            "byte_count": len(request_raw),
            "path": str(request_path),
            "request_id": request_id,
            "sha256": sha256(request_raw),
        }
    ):
        raise CoordinatorError("resource approval snapshot identity differs")
    try:
        preserved_lines = ledger_raw.decode("utf-8-sig").splitlines()
    except UnicodeError as exc:
        raise CoordinatorError("preserved pre-run ledger is not UTF-8") from exc
    if preserved_lines.count(line) != 1:
        raise CoordinatorError("preserved pre-run ledger approval row differs")
    return snapshot, raw


def validate_authorization(
    path: Path,
    *,
    contract_path: Path,
    contract_raw: bytes,
) -> tuple[Mapping[str, Any], bytes]:
    value, raw = strict_json_load(path)
    if raw != canonical_bytes(value):
        raise CoordinatorError("execution authorization is not canonical JSON")
    authorization = _exact(
        value,
        {
            "contract_path",
            "contract_sha256",
            "execution_paths",
            "formal_execution_authorized",
            "implementation_reviews",
            "ledger_approval",
            "resource_request",
            "resource_lock_required",
            "schema",
            "user_approval",
        },
        "$authorization",
    )
    contract = strict_json_bytes(contract_raw, str(contract_path))
    registered_contract_path = _repo_relative_path(
        authorization["contract_path"], "$.authorization.contract_path"
    )
    if (
        authorization["schema"] != AUTHORIZATION_SCHEMA
        or authorization["formal_execution_authorized"] is not True
        or authorization["resource_lock_required"] is not True
        or registered_contract_path != contract_path.resolve()
        or authorization["contract_sha256"] != sha256(contract_raw)
    ):
        raise CoordinatorError("execution authorization identity differs")
    user_approval = _exact(
        authorization["user_approval"], {"recorded", "source"}, "$.authorization.user_approval"
    )
    if (
        user_approval["recorded"] is not True
        or not isinstance(user_approval["source"], str)
        or not user_approval["source"]
    ):
        raise CoordinatorError("explicit user approval is not recorded")
    reviews = authorization["implementation_reviews"]
    if not isinstance(reviews, list) or len(reviews) != 2:
        raise CoordinatorError("two implementation reviews are required")
    expected_paths = {
        "PROCESS_AND_AUTHORITY": PROCESS_REVIEW_PATH.resolve(),
        "SCIENTIFIC_AND_MECHANICS": SCIENTIFIC_REVIEW_PATH.resolve(),
    }
    reviewer_ids: set[str] = set()
    observed_roles: list[str] = []
    expected_inputs = _review_inputs(contract, contract_raw)
    for index, review in enumerate(reviews):
        binding = _exact(
            review, {"path", "role", "sha256", "verdict"}, f"$.reviews[{index}]"
        )
        role = str(binding["role"])
        if role not in EXPECTED_REVIEW_VERDICTS or role in observed_roles:
            raise CoordinatorError("implementation review role is missing or duplicated")
        review_path = _repo_relative_path(binding["path"], f"$.reviews[{index}].path")
        if review_path != expected_paths[role]:
            raise CoordinatorError("implementation review path differs")
        review_value, review_raw = _validate_review(
            review_path, role=role, expected_inputs=expected_inputs
        )
        if (
            binding["sha256"] != sha256(review_raw)
            or binding["verdict"] != EXPECTED_REVIEW_VERDICTS[role]
        ):
            raise CoordinatorError("implementation review binding differs")
        reviewer_ids.add(review_value["reviewer_independence"]["reviewer_id"])
        observed_roles.append(role)
    if observed_roles != list(EXPECTED_REVIEW_VERDICTS) or len(reviewer_ids) != 2:
        raise CoordinatorError("implementation reviews are not distinct and ordered")
    request = _exact(
        authorization["resource_request"],
        {
            "command_sha256",
            "request_id",
            "request_path",
            "request_sha256",
            "repository",
            "task",
        },
        "$.authorization.resource_request",
    )
    request_path = Path(str(request["request_path"]))
    request_id = request["request_id"]
    if (
        not isinstance(request_id, str)
        or len(request_id) != 32
        or any(character not in "0123456789abcdef" for character in request_id)
        or request_path.resolve()
        != (RESOURCE_MANAGER_ROOT / "requests" / f"{request_id}.json").resolve()
        or not request_path.is_file()
        or request_path.is_symlink()
    ):
        raise CoordinatorError("resource request path is not an absolute file")
    request_value, request_raw = _strict_external_json(request_path, "resource request")
    request_value = _exact(
        request_value,
        {
            "command",
            "estimate_minutes",
            "repository",
            "request_id",
            "requested_at",
            "status",
            "task",
        },
        "$.resource_request_file",
    )
    execution_paths = _exact(
        authorization["execution_paths"],
        {"aggregate_path", "approval_snapshot_path", "output_root", "python_executable"},
        "$.authorization.execution_paths",
    )
    python_executable = Path(str(execution_paths["python_executable"])).resolve()
    output_root = Path(str(execution_paths["output_root"])).resolve()
    aggregate_path = Path(str(execution_paths["aggregate_path"])).resolve()
    approval_snapshot_path = Path(str(execution_paths["approval_snapshot_path"])).resolve()
    expected_command = expected_resource_command(
        python_executable=python_executable,
        contract_path=contract_path,
        authorization_path=path,
        output_root=output_root,
        aggregate_path=aggregate_path,
    )
    expected_task = "ANYsolver S3 V2A Stage 4A bounded mixed-flexural gate"
    if (
        not python_executable.is_file()
        or aggregate_path.parent != output_root
        or approval_snapshot_path.parent != output_root
        or request_value["request_id"] != request_id
        or request_value["status"] != "PENDING"
        or request_value["task"] != expected_task
        or request_value["repository"] != str(ROOT)
        or request_value["estimate_minutes"] != 30
        or request_value["command"] != expected_command
        or request["task"] != expected_task
        or request["repository"] != str(ROOT)
        or request["command_sha256"] != sha256(expected_command.encode("utf-8"))
        or request["request_sha256"] != sha256(request_raw)
    ):
        raise CoordinatorError("resource request content differs")
    approval = _exact(
        authorization["ledger_approval"],
        {"approved_row_sha256", "ledger_path", "snapshot_path", "snapshot_sha256"},
        "$.authorization.ledger_approval",
    )
    if approval["ledger_path"] != str(RESOURCE_LEDGER_PATH):
        raise CoordinatorError("resource ledger path differs")
    snapshot, snapshot_raw = _validate_approval_snapshot(
        approval_snapshot_path,
        contract=contract,
        request_id=request_id,
        request_path=request_path,
        request_raw=request_raw,
    )
    if (
        Path(str(approval["snapshot_path"])).resolve() != approval_snapshot_path
        or approval["snapshot_sha256"] != sha256(snapshot_raw)
        or approval["approved_row_sha256"] != snapshot["approved_row"]["sha256"]
    ):
        raise CoordinatorError("resource ledger approval binding differs")
    try:
        ledger_lines = RESOURCE_LEDGER_PATH.read_text(encoding="utf-8-sig").splitlines()
    except (OSError, UnicodeError) as exc:
        raise CoordinatorError(f"cannot inspect resource ledger: {exc}") from exc
    if ledger_lines.count(snapshot["approved_row"]["line"]) != 1:
        raise CoordinatorError("registered APPROVED row is absent or duplicated")
    return authorization, raw


def validate_resource_execution_state(
    authorization: Mapping[str, Any], *, claim_attempt: bool = True
) -> None:
    request = authorization["resource_request"]
    request_id = str(request["request_id"])
    request_path = Path(str(request["request_path"]))
    request_value, _request_raw = _strict_external_json(request_path, "resource request")
    try:
        ledger_lines = RESOURCE_LEDGER_PATH.read_text(encoding="utf-8-sig").splitlines()
    except (OSError, UnicodeError) as exc:
        raise CoordinatorError(f"cannot inspect live resource ledger: {exc}") from exc
    matching = [line for line in ledger_lines if f"| {request_id} |" in line]
    statuses = [
        fields[3].strip()
        for line in matching
        if len(fields := line.split("|")) > 3
    ]
    if statuses.count("APPROVED") != 1:
        raise CoordinatorError("resource request lacks one APPROVED ledger row")
    if statuses.count("EXECUTION_STARTED") != 1:
        raise CoordinatorError("resource request lacks one EXECUTION_STARTED row")
    if len(statuses) != 2 or set(statuses) != {"APPROVED", "EXECUTION_STARTED"}:
        raise CoordinatorError("resource request was already consumed")
    if not RESOURCE_LOCK_OWNER_PATH.is_file():
        raise CoordinatorError("global resource lock is not held")
    owner, _owner_raw = _strict_external_json(RESOURCE_LOCK_OWNER_PATH, "resource lock owner")
    owner = _exact(
        owner,
        {"acquired_at", "command", "process_id", "repository", "request_id", "task"},
        "$.resource_lock_owner",
    )
    if (
        owner["request_id"] != request_id
        or owner["command"] != request_value["command"]
        or owner["repository"] != request_value["repository"]
        or owner["task"] != request_value["task"]
        or _nonnegative_integer(owner["process_id"], "$.resource_lock_owner.process_id") <= 0
    ):
        raise CoordinatorError("global resource lock owner differs")
    attempt_path = RESOURCE_MANAGER_ROOT / "attempts" / f"{request_id}.json"
    attempt = {
        "contract_sha256": authorization["contract_sha256"],
        "request_id": request_id,
        "schema": "anysolver.resource-attempt-claim-v1",
    }
    if claim_attempt:
        _write_exclusive(attempt_path, canonical_bytes(attempt))
    else:
        value, raw = strict_json_load(attempt_path)
        if raw != canonical_bytes(value) or value != attempt:
            raise CoordinatorError("resource attempt claim differs at finalization")


def _write_exclusive(path: Path, raw: bytes) -> None:
    """Stage, fsync, and atomically publish without exposing partial bytes."""

    path.parent.mkdir(parents=True, exist_ok=True)
    if os.path.lexists(path):
        raise CoordinatorError(f"refusing to overwrite canonical output: {path}")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.pending-",
        dir=path.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError as exc:
            raise CoordinatorError(
                f"refusing to overwrite canonical output: {path}"
            ) from exc
    finally:
        try:
            temporary.unlink()
        except OSError:
            pass


def _publish_candidate_archive(path: Path, commit: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if os.path.lexists(path):
        raise CoordinatorError("candidate source archive output already exists")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.pending-",
        dir=path.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            _git_run("archive", "--format=tar", commit, stdout=stream)
            stream.flush()
            os.fsync(stream.fileno())
        if temporary.stat().st_size <= 0:
            raise CoordinatorError("candidate source archive is empty")
        try:
            os.link(temporary, path)
        except FileExistsError as exc:
            raise CoordinatorError("candidate source archive output already exists") from exc
    finally:
        try:
            temporary.unlink()
        except OSError:
            pass


def _extract_candidate_archive(archive_path: Path, output_root: Path) -> Path:
    """Safely extract the exact Git archive into one fresh external tree."""

    candidate_root = (output_root / "candidate-source-tree").resolve()
    if os.path.lexists(candidate_root):
        raise CoordinatorError("candidate source tree output already exists")
    staging = Path(
        tempfile.mkdtemp(prefix=".candidate-source-tree.pending-", dir=output_root)
    ).resolve()
    seen: set[str] = set()
    try:
        with tarfile.open(archive_path, mode="r:") as bundle:
            for member in bundle.getmembers():
                raw_name = member.name.rstrip("/")
                if not raw_name:
                    continue
                pure = PurePosixPath(raw_name)
                if pure.is_absolute() or any(
                    part in {"", ".", ".."} for part in pure.parts
                ):
                    raise CoordinatorError("candidate archive contains an unsafe path")
                folded = pure.as_posix().casefold()
                if folded in seen:
                    raise CoordinatorError("candidate archive path is duplicated")
                seen.add(folded)
                target = staging.joinpath(*pure.parts).resolve()
                try:
                    target.relative_to(staging)
                except ValueError as exc:
                    raise CoordinatorError(
                        "candidate archive path escapes its extraction root"
                    ) from exc
                if member.isdir():
                    target.mkdir(parents=True, exist_ok=False)
                    continue
                if not member.isfile():
                    raise CoordinatorError(
                        "candidate archive contains a link or special entry"
                    )
                target.parent.mkdir(parents=True, exist_ok=True)
                source = bundle.extractfile(member)
                if source is None:
                    raise CoordinatorError("candidate archive member cannot be read")
                with target.open("xb") as destination:
                    shutil.copyfileobj(source, destination)
                    destination.flush()
                    os.fsync(destination.fileno())
        if not (staging / "src" / "anysolver" / "__init__.py").is_file():
            raise CoordinatorError("candidate archive lacks the ANYsolver source tree")
        os.rename(staging, candidate_root)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return candidate_root


def prepare_wave(
    contract_path: Path,
    output_root: Path,
    *,
    authorization_path: Path | None = None,
) -> dict[str, Path]:
    contract, contract_raw = validate_contract(contract_path)
    if authorization_path is not None:
        validate_authorization(
            authorization_path,
            contract_path=contract_path,
            contract_raw=contract_raw,
        )
    funnel = _load_module("_s3_v2_stage4a_funnel", FUNNEL_PATH)
    manifest_value, manifest_raw = funnel.strict_json_load(MANIFEST_PATH)
    records = funnel.validate_manifest(manifest_value, manifest_raw)
    plan = funnel.build_phase_plan(records, "4A")
    plan_path = (output_root / "phase4a-plan.json").resolve()
    _write_exclusive(plan_path, funnel.canonical_bytes(plan))
    candidate = contract["candidate"]
    archive_path = (output_root / "candidate-source.tar").resolve()
    _publish_candidate_archive(archive_path, str(candidate["commit"]))
    archive_sha256 = sha256(archive_path.read_bytes())
    candidate_source_root = _extract_candidate_archive(archive_path, output_root)
    binding = {
        "artifact_path": str(archive_path),
        "artifact_sha256": archive_sha256,
        "candidate_id": "CANDIDATE_E4_PL_S3_V2A_FLAT_LINEAR_V1",
        "commit": candidate["commit"],
        "formulation_id": "E4_PL_QUALIFIED_S3_COMPANION_V2",
        "schema": "anysolver.e4-pl-s3-v2-flat-candidate-binding-v1",
        "selector": "e4-pl-s3-v2",
        "tree": candidate["tree"],
    }
    binding_path = (output_root / "candidate-source-binding.json").resolve()
    _write_exclusive(binding_path, canonical_bytes(binding))
    wave_manifest = funnel.build_bounded_wave_manifest(
        plan,
        plan_path=plan_path,
        producer_program=PRODUCER_PATH,
        python_executable=Path(sys.executable).resolve(),
        cwd=ROOT,
        output_root=(output_root / "producer-wave").resolve(),
        input_paths={
            "candidate_artifact": binding_path,
            "connectivity_manifest": MANIFEST_PATH,
            "flat_funnel_contract": SCAFFOLD_CONTRACT_PATH,
            "source_equation_contract": SOURCE_CONTRACT_PATH,
        },
    )
    extra_inputs = [contract_path.resolve(), AUTHORITY_PATH.resolve()]
    if authorization_path is not None:
        extra_inputs.append(authorization_path.resolve())
    for worker in wave_manifest["workers"]:
        worker["input_hashes"] = list(worker["input_hashes"])
        worker["command"].extend(
            [
                "--candidate-source-root",
                str(candidate_source_root),
                "--candidate-archive",
                str(archive_path),
                "--candidate-archive-sha256",
                archive_sha256,
            ]
        )
    for worker in wave_manifest["workers"]:
        for path in extra_inputs:
            worker["input_hashes"].append(
                {"path": str(path), "sha256": sha256(path.read_bytes())}
            )
        worker["input_hashes"].sort(key=lambda item: item["path"])
    wave_manifest_path = (output_root / "producer-wave-manifest.json").resolve()
    _write_exclusive(wave_manifest_path, canonical_bytes(wave_manifest))
    return {
        "archive": archive_path,
        "binding": binding_path,
        "candidate_source_root": candidate_source_root,
        "plan": plan_path,
        "producer_manifest": wave_manifest_path,
    }


def _run_checker_process(
    *,
    assignment_id: str,
    proof: Path,
    plan: Path,
    output: Path,
    stdout_path: Path,
    stderr_path: Path,
    deadline: float,
) -> dict[str, Any]:
    bounded = _load_module(
        f"_s3_v2_checker_bounded_{assignment_id}_{output.parent.name}",
        BOUNDED_PATH,
    )
    for path in (output, stdout_path, stderr_path):
        if path.exists():
            raise CoordinatorError(f"checker output is not exclusive: {path}")
        path.parent.mkdir(parents=True, exist_ok=True)
    stdout = stdout_path.open("xb")
    stderr = stderr_path.open("xb")
    job = bounded._ProcessJob(MEMORY_LIMIT_BYTES)
    command = [
        str(Path(sys.executable).resolve()),
        str(CHECKER_PATH.resolve()),
        "--verify-proof",
        "--proof",
        str(proof.resolve()),
        "--plan",
        str(plan.resolve()),
        "--output",
        str(output.resolve()),
    ]
    started = time.monotonic()
    last_cpu = 0
    last_activity = started
    termination_proven = False
    peak = 0
    process: Any = None
    try:
        process = job.launch(
            command,
            cwd=ROOT,
            env=bounded._environment(),
            stdout=stdout,
            stderr=stderr,
        )
        while process.poll() is None:
            now = time.monotonic()
            cpu, _active, peak = job.accounting()
            if cpu > last_cpu:
                last_cpu = cpu
                last_activity = now
            if now >= min(deadline, started + CHECKER_WALL_SECONDS) or now - last_activity >= 300:
                termination_proven = job.terminate()
                raise CoordinatorError(f"checker process exceeded its bound: {assignment_id}")
            time.sleep(0.05)
        cpu, active, peak = job.accounting()
        last_cpu = max(last_cpu, cpu)
        termination_proven = active in (0, -1)
        if process.returncode != 0 or not termination_proven:
            raise CoordinatorError(f"checker process failed: {assignment_id}")
    except BaseException:
        if process is not None and process.poll() is None:
            termination_proven = job.terminate()
        raise
    finally:
        stdout.close()
        stderr.close()
        job.close()
    value, raw = strict_json_load(output)
    if raw != canonical_bytes(value) or value.get("schema") != CHECKER_RESULT_SCHEMA:
        raise CoordinatorError("checker output is malformed or noncanonical")
    return {
        "assignment_id": assignment_id,
        "cpu_100ns": last_cpu,
        "output_path": str(output.resolve()),
        "output_sha256": sha256(raw),
        "peak_tree_memory_bytes": peak,
        "proof_path": str(proof.resolve()),
        "proof_sha256": sha256(proof.read_bytes()),
        "stderr_sha256": sha256(stderr_path.read_bytes()),
        "stdout_sha256": sha256(stdout_path.read_bytes()),
        "termination_proven": termination_proven,
        "value": value,
    }


def validate_producer_proofs(
    manifest: Mapping[str, Any],
    manifest_raw: bytes,
    producer_result: Mapping[str, Any],
    producer_result_raw: bytes,
) -> dict[str, dict[str, Any]]:
    """Join each completed worker result to its exact proof and assignment."""

    if producer_result_raw != canonical_bytes(producer_result):
        raise CoordinatorError("producer wave result is not canonical JSON")
    result = _exact(
        producer_result,
        {"lane", "manifest_sha256", "schema", "terminal", "wave_id", "workers"},
        "$.producer_result",
    )
    if (
        result["schema"] != PRODUCER_RESULT_SCHEMA
        or result["terminal"] != "COMPLETED"
        or result["manifest_sha256"] != sha256(manifest_raw)
        or not isinstance(result["workers"], list)
        or len(result["workers"]) != 3
    ):
        raise CoordinatorError("producer wave result identity differs")
    manifest_workers = manifest.get("workers")
    if not isinstance(manifest_workers, list) or len(manifest_workers) != 3:
        raise CoordinatorError("producer wave manifest coverage differs")
    by_manifest = {
        str(worker.get("assignment_id")): worker for worker in manifest_workers
    }
    by_result = {
        str(worker.get("assignment_id")): worker for worker in result["workers"]
        if isinstance(worker, dict)
    }
    if (
        set(by_manifest) != set(EXPECTED_SHARDS)
        or set(by_result) != set(EXPECTED_SHARDS)
        or len(by_manifest) != 3
        or len(by_result) != 3
    ):
        raise CoordinatorError("producer assignment coverage differs")
    worker_keys = {
        "assignment_id",
        "assignment_sha256",
        "cpu_100ns",
        "input_hashes",
        "last_progress_sequence",
        "peak_tree_memory_bytes",
        "plan_sha256",
        "program_sha256",
        "returncode",
        "scientific_byte_count",
        "scientific_payload_sha256",
        "scientific_record_count",
        "scientific_record_ids_sha256",
        "scientific_schema",
        "scientific_sha256",
        "scientific_terminal",
        "status",
        "stderr_sha256",
        "stdout_sha256",
        "termination_proven",
    }
    made: dict[str, dict[str, Any]] = {}
    for assignment_id in EXPECTED_SHARDS:
        registered = by_manifest[assignment_id]
        completed = _exact(
            by_result[assignment_id],
            worker_keys,
            f"$.producer_result.workers[{assignment_id}]",
        )
        proof_path = Path(str(registered.get("scientific_path"))).resolve()
        proof_sha256 = _digest(
            completed["scientific_sha256"],
            f"$.producer_result.workers[{assignment_id}].scientific_sha256",
        )
        if (
            completed["status"] != "COMPLETED"
            or completed["returncode"] != 0
            or completed["termination_proven"] is not True
            or completed["assignment_sha256"] != registered.get("assignment_sha256")
            or completed["plan_sha256"] != registered.get("plan_sha256")
            or not proof_path.is_file()
            or proof_path.is_symlink()
            or sha256(proof_path.read_bytes()) != proof_sha256
        ):
            raise CoordinatorError("producer proof binding differs")
        made[assignment_id] = {
            "assignment_sha256": completed["assignment_sha256"],
            "plan_sha256": completed["plan_sha256"],
            "proof_path": str(proof_path),
            "proof_sha256": proof_sha256,
        }
    return made


def aggregate_checker_results(
    replica_results: Sequence[Sequence[Mapping[str, Any]]],
    *,
    producer_proofs: Mapping[str, Mapping[str, Any]],
    producer_result_sha256: str,
    contract_sha256: str,
    authorization_sha256: str,
) -> dict[str, Any]:
    _digest(producer_result_sha256, "$.producer_result_sha256")
    _digest(contract_sha256, "$.contract_sha256")
    _digest(authorization_sha256, "$.authorization_sha256")
    if set(producer_proofs) != set(EXPECTED_SHARDS):
        raise CoordinatorError("producer proof binding coverage differs")
    for assignment_id, proof in producer_proofs.items():
        _exact(
            proof,
            {"assignment_sha256", "plan_sha256", "proof_path", "proof_sha256"},
            f"$.producer_proofs[{assignment_id}]",
        )
        _digest(proof["assignment_sha256"], "$.producer_proof.assignment_sha256")
        _digest(proof["plan_sha256"], "$.producer_proof.plan_sha256")
        _digest(proof["proof_sha256"], "$.producer_proof.proof_sha256")
    if len(replica_results) != 2 or any(len(replica) != 3 for replica in replica_results):
        raise CoordinatorError("exactly two complete three-shard checker replicas are required")
    by_replica = [
        {str(item["assignment_id"]): item for item in replica}
        for replica in replica_results
    ]
    expected_assignments = set(EXPECTED_SHARDS)
    if (
        set(by_replica[0]) != expected_assignments
        or set(by_replica[1]) != expected_assignments
        or any(
            len(replica) != len(mapping)
            for replica, mapping in zip(replica_results, by_replica)
        )
    ):
        raise CoordinatorError("checker replica assignment coverage differs")
    accepted: list[Mapping[str, Any]] = []
    for assignment_id in EXPECTED_SHARDS:
        first = by_replica[0][assignment_id]
        second = by_replica[1][assignment_id]
        first_value, first_raw = _validate_checker_result(
            first,
            expected_assignment_id=assignment_id,
            expected_proof=producer_proofs[assignment_id],
        )
        _second_value, second_raw = _validate_checker_result(
            second,
            expected_assignment_id=assignment_id,
            expected_proof=producer_proofs[assignment_id],
        )
        if first_raw != second_raw:
            raise CoordinatorError(f"checker replicas disagree: {assignment_id}")
        accepted.append(first_value)
    terminals = {str(value["terminal"]) for value in accepted}
    if not terminals <= {PASS, NO_GO}:
        raise CoordinatorError("checker result contains an unregistered terminal")
    terminal = NO_GO if NO_GO in terminals else PASS
    failures = sorted(
        f"{value['diagonal']}:{failure}"
        for value in accepted
        for failure in value["formal_failures"]
    )
    if (terminal == NO_GO) != bool(failures):
        raise CoordinatorError("checker terminal and formal failures disagree")
    advisory = any(bool(value["advisory_review_required"]) for value in accepted)
    sequences = []
    by_diagonal = {str(value["diagonal"]): value for value in accepted}
    for diagonal in DIAGONAL_ORDER:
        value = by_diagonal[diagonal]
        by_coordinate = {
            (str(sequence["mask"]), int(sequence["fraction_percent"])): sequence
            for sequence in value["sequence_results"]
        }
        for mask in MASK_ORDER:
            for fraction in FRACTION_ORDER:
                sequences.append(
                    {
                        "diagonal": diagonal,
                        **by_coordinate[(mask, fraction)],
                    }
                )
    if len(sequences) != 24:
        raise CoordinatorError("aggregate sequence coverage is not exactly 24")
    classifying_count = sum(int(value["classifying_record_count"]) for value in accepted)
    v1_count = sum(int(value["v1_diagnostic_record_count"]) for value in accepted)
    if classifying_count != 81 or v1_count != 72:
        raise CoordinatorError("aggregate checker record coverage differs")
    checker_bindings = []
    for assignment_id in EXPECTED_SHARDS:
        first = by_replica[0][assignment_id]
        second = by_replica[1][assignment_id]
        proof = producer_proofs[assignment_id]
        checker_bindings.append(
            {
                "assignment_id": assignment_id,
                "assignment_sha256": proof["assignment_sha256"],
                "checker_output_sha256": [
                    first["output_sha256"],
                    second["output_sha256"],
                ],
                "checker_stderr_sha256": [
                    first["stderr_sha256"],
                    second["stderr_sha256"],
                ],
                "checker_stdout_sha256": [
                    first["stdout_sha256"],
                    second["stdout_sha256"],
                ],
                "plan_sha256": proof["plan_sha256"],
                "proof_sha256": proof["proof_sha256"],
            }
        )
    return {
        "advisory_review_required": bool(advisory and terminal == PASS),
        "authorization_sha256": authorization_sha256,
        "classifying_record_count": classifying_count,
        "checker_replica_bindings": checker_bindings,
        "contract_sha256": contract_sha256,
        "formal_failures": failures,
        "production_restriction": PRODUCTION_RESTRICTION,
        "producer_wave_result_sha256": producer_result_sha256,
        "schema": AGGREGATE_SCHEMA,
        "sequence_results": sequences,
        "successor_expansion_authorized": bool(
            terminal == PASS and not advisory
        ),
        "terminal": terminal,
        "v1_diagnostic_record_count": v1_count,
    }


def blocked_aggregate(
    *,
    authorization_sha256: str,
    contract_sha256: str,
    producer_result_sha256: str | None,
    reason: str,
) -> dict[str, Any]:
    _digest(authorization_sha256, "$.authorization_sha256")
    _digest(contract_sha256, "$.contract_sha256")
    if producer_result_sha256 is not None:
        _digest(producer_result_sha256, "$.producer_result_sha256")
    if reason not in {
        "CHECKER_WAVE_FAILED",
        "FORMAL_PROCESS_FAILED",
        "PRODUCER_WAVE_NOT_COMPLETED",
    }:
        raise CoordinatorError("unregistered blocked reason")
    return {
        "advisory_review_required": False,
        "authorization_sha256": authorization_sha256,
        "classifying_record_count": 0,
        "checker_replica_bindings": [],
        "contract_sha256": contract_sha256,
        "formal_failures": [reason],
        "production_restriction": PRODUCTION_RESTRICTION,
        "producer_wave_result_sha256": producer_result_sha256,
        "schema": AGGREGATE_SCHEMA,
        "sequence_results": [],
        "successor_expansion_authorized": False,
        "terminal": BLOCKED,
        "v1_diagnostic_record_count": 0,
    }


def run_stage4a(
    contract_path: Path,
    authorization_path: Path,
    output_root: Path,
    aggregate_path: Path,
) -> dict[str, Any]:
    started = time.monotonic()
    if not sys.flags.isolated or not sys.dont_write_bytecode:
        raise CoordinatorError("formal Stage 4A requires the registered -I -B launcher")
    _contract, contract_raw = validate_contract(contract_path)
    authorization, authorization_raw = validate_authorization(
        authorization_path,
        contract_path=contract_path,
        contract_raw=contract_raw,
    )
    execution_paths = authorization["execution_paths"]
    if (
        Path(str(execution_paths["output_root"])).resolve() != output_root.resolve()
        or Path(str(execution_paths["aggregate_path"])).resolve() != aggregate_path.resolve()
        or Path(str(execution_paths["python_executable"])).resolve()
        != Path(sys.executable).resolve()
    ):
        raise CoordinatorError("live Stage 4A invocation differs from the resource request")
    validate_resource_execution_state(authorization)
    authorization_digest = sha256(authorization_raw)
    contract_digest = sha256(contract_raw)
    producer_result_path = (output_root / "producer-wave-result.json").resolve()
    try:
        paths = prepare_wave(
            contract_path,
            output_root,
            authorization_path=authorization_path,
        )
        bounded = _load_module("_s3_v2_stage4a_bounded", BOUNDED_PATH)
        producer_result = bounded.run_wave(paths["producer_manifest"], producer_result_path)
    except Exception:
        producer_digest = (
            sha256(producer_result_path.read_bytes())
            if producer_result_path.is_file()
            else None
        )
        blocked = blocked_aggregate(
            authorization_sha256=authorization_digest,
            contract_sha256=contract_digest,
            producer_result_sha256=producer_digest,
            reason="FORMAL_PROCESS_FAILED",
        )
        _write_exclusive(aggregate_path, canonical_bytes(blocked))
        return blocked
    if producer_result.get("terminal") != "COMPLETED":
        blocked = blocked_aggregate(
            authorization_sha256=authorization_digest,
            contract_sha256=contract_digest,
            producer_result_sha256=sha256(producer_result_path.read_bytes()),
            reason="PRODUCER_WAVE_NOT_COMPLETED",
        )
        _write_exclusive(aggregate_path, canonical_bytes(blocked))
        return blocked
    deadline = started + WAVE_WALL_SECONDS
    replicas: list[list[dict[str, Any]]] = []
    try:
        manifest, raw_manifest = strict_json_load(paths["producer_manifest"])
        stored_producer_result, producer_result_raw = strict_json_load(
            producer_result_path
        )
        if stored_producer_result != producer_result:
            raise CoordinatorError("producer result changed after bounded execution")
        producer_proofs = validate_producer_proofs(
            manifest,
            raw_manifest,
            stored_producer_result,
            producer_result_raw,
        )
        proofs = {
            assignment_id: Path(str(binding["proof_path"]))
            for assignment_id, binding in producer_proofs.items()
        }
        if set(proofs) != set(EXPECTED_SHARDS):
            raise CoordinatorError("producer manifest does not expose three exact proofs")
        for replica_index in (1, 2):
            tasks = []
            with ThreadPoolExecutor(max_workers=3) as pool:
                for assignment_id, proof in sorted(proofs.items()):
                    root = output_root / f"checker-replica-{replica_index}" / assignment_id
                    tasks.append(
                        pool.submit(
                            _run_checker_process,
                            assignment_id=assignment_id,
                            proof=proof,
                            plan=paths["plan"],
                            output=root / "checker.json",
                            stdout_path=root / "stdout.log",
                            stderr_path=root / "stderr.log",
                            deadline=deadline,
                        )
                    )
                replicas.append([task.result() for task in tasks])
        _final_contract, final_contract_raw = validate_contract(contract_path)
        final_authorization, final_authorization_raw = validate_authorization(
            authorization_path,
            contract_path=contract_path,
            contract_raw=final_contract_raw,
        )
        if final_contract_raw != contract_raw or final_authorization_raw != authorization_raw:
            raise CoordinatorError("formal authority changed during execution")
        validate_resource_execution_state(final_authorization, claim_attempt=False)
        aggregate = aggregate_checker_results(
            replicas,
            producer_proofs=producer_proofs,
            producer_result_sha256=sha256(producer_result_path.read_bytes()),
            contract_sha256=contract_digest,
            authorization_sha256=authorization_digest,
        )
    except Exception:
        aggregate = blocked_aggregate(
            authorization_sha256=authorization_digest,
            contract_sha256=contract_digest,
            producer_result_sha256=sha256(producer_result_path.read_bytes()),
            reason="CHECKER_WAVE_FAILED",
        )
    _write_exclusive(aggregate_path, canonical_bytes(aggregate))
    return aggregate


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prepare-only", action="store_true")
    mode.add_argument("--run-stage4a", action="store_true")
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--authorization", type=Path)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--aggregate", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    contract = args.contract.resolve()
    output_root = args.output_root.resolve()
    if args.prepare_only:
        if args.authorization is not None or args.aggregate is not None:
            raise CoordinatorError("prepare-only does not accept execution outputs")
        prepare_wave(contract, output_root)
        return 0
    if args.authorization is None or args.aggregate is None:
        raise CoordinatorError("formal execution requires authorization and aggregate")
    aggregate = run_stage4a(
        contract,
        args.authorization.resolve(),
        output_root,
        args.aggregate.resolve(),
    )
    return 0 if aggregate["terminal"] in {PASS, NO_GO} else 2


if __name__ == "__main__":
    raise SystemExit(main())
