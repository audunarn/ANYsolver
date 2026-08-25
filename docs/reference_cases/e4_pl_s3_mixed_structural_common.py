"""Frozen authority and canonical-record helpers for mixed S3/Q4 structure tests.

This module deliberately contains no mechanics.  Producers may import it and
the frozen smoke-model builder, while the coordinator imports only this module
and the generic bounded-process runner.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import sys
from typing import Any, Iterable, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[2]
REFERENCE_CASES = ROOT / "docs" / "reference_cases"
DEFAULT_INPUT = REFERENCE_CASES / "e4_pl_s3_mixed_structural_input.json"

PROGRAM_PATHS = {
    "common": "docs/reference_cases/e4_pl_s3_mixed_structural_common.py",
    "coordinator": "docs/reference_cases/e4_pl_s3_mixed_structural_coordinator.py",
    "producer": "docs/reference_cases/e4_pl_s3_mixed_structural_producer.py",
    "qualification_test": "tests/test_e4_pl_s3_mixed_structural_qualification.py",
}
ALLOWED_EXECUTION_EXTENT = (
    "docs/reference_cases/e4_pl_s3_mixed_structural_common.py",
    "docs/reference_cases/e4_pl_s3_mixed_structural_coordinator.py",
    "docs/reference_cases/e4_pl_s3_mixed_structural_input.json",
    "docs/reference_cases/e4_pl_s3_mixed_structural_input_schema.json",
    "docs/reference_cases/e4_pl_s3_mixed_structural_producer.py",
    "tests/test_e4_pl_s3_mixed_structural_qualification.py",
)

INPUT_SCHEMA = "anysolver.e4-pl-s3-mixed-structural-input-v1"
SHARD_SCHEMA = "anysolver.e4-pl-s3-mixed-structural-shard-v1"
AGGREGATE_SCHEMA = "anysolver.e4-pl-s3-mixed-structural-aggregate-v1"
SHARD_IDS = (
    "PATCH_EQUILIBRIUM_COVARIANCE",
    "CONVERGENCE_INTERFACE_PARTICIPATION",
    "LOCKING_AND_SPECIAL_FIXTURES",
)
GATE_IDS = (
    "patch_and_equilibrium",
    "symmetry_and_covariance",
    "convergence",
    "locking",
    "interface_resultants",
    "pl_participation",
    "special_fixtures",
)
TERMINALS = (
    "BLOCKED_E4_PL_S3_MIXED_STRUCTURAL_PROCESS_OR_EVIDENCE",
    "NO_GO_E4_PL_S3_MIXED_STRUCTURAL_CONTRADICTION",
    "UNCLASSIFIED_E4_PL_S3_MIXED_STRUCTURAL_PARTIAL_COVERAGE",
    "STRUCTURAL_GATES_CLOSED_E4_PL_S3_MIXED_ONLY",
)
PRODUCTION_RESTRICTION = (
    "QUALIFIED_S3_REMAINS_OPT_IN_AND_QUALIFIED_Q4_REMAINS_UNCHANGED"
)

COMPLETE = "PASS_COMPLETE_SCOPE"
PARTIAL = "PASS_REPRESENTATIVE_SCOPE_ONLY"
UNEXECUTED = "UNEXECUTED"
FAIL = "FAIL_CONTRADICTION"
BLOCKED = "BLOCKED"
GATE_STATUSES = frozenset((COMPLETE, PARTIAL, UNEXECUTED, FAIL, BLOCKED))


class StructuralEvidenceError(ValueError):
    """A frozen input or canonical structural record is malformed."""


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
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise StructuralEvidenceError(f"{label} contains duplicate key {key!r}")
            result[key] = value
        return result

    def reject_constant(value: str) -> object:
        raise StructuralEvidenceError(f"{label} contains nonfinite value {value!r}")

    try:
        return json.loads(
            raw,
            object_pairs_hook=reject_duplicates,
            parse_constant=reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise StructuralEvidenceError(f"{label} is not strict UTF-8 JSON: {exc}") from exc


def read_canonical(path: Path, *, pretty: bool, label: str) -> tuple[bytes, dict[str, Any]]:
    raw = Path(path).read_bytes()
    value = strict_json(raw, label=label)
    if not isinstance(value, dict):
        raise StructuralEvidenceError(f"{label} must be an object")
    expected = pretty_canonical_bytes(value) if pretty else canonical_bytes(value)
    if raw != expected:
        style = "pretty" if pretty else "compact"
        raise StructuralEvidenceError(f"{label} is not canonical {style} JSON")
    return raw, value


def _exact_keys(value: Mapping[str, Any], expected: Iterable[str], label: str) -> None:
    actual = set(value)
    wanted = set(expected)
    if actual != wanted:
        raise StructuralEvidenceError(
            f"{label} keys differ: missing={sorted(wanted-actual)}, extra={sorted(actual-wanted)}"
        )


def _object(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise StructuralEvidenceError(f"{label} must be an object")
    return value


def _array(value: object, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise StructuralEvidenceError(f"{label} must be an array")
    return value


def _positive_integer(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise StructuralEvidenceError(f"{label} must be a positive integer")
    return int(value)


def _digest(value: object, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789ABCDEF" for character in value)
    ):
        raise StructuralEvidenceError(f"{label} must be an uppercase SHA-256")
    return value


def _finite_tree(value: object, label: str = "value") -> None:
    if value is None or isinstance(value, (bool, str, int)):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise StructuralEvidenceError(f"{label} contains a nonfinite float")
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise StructuralEvidenceError(f"{label} contains a non-string key")
            _finite_tree(item, f"{label}.{key}")
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _finite_tree(item, f"{label}[{index}]")
        return
    raise StructuralEvidenceError(f"{label} contains unsupported {type(value).__name__}")


def _load_source(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise StructuralEvidenceError(f"cannot import frozen helper {path.name}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@dataclass(frozen=True)
class Authorities:
    input_path: Path
    input_raw: bytes
    input: dict[str, Any]
    execution_commit: str
    execution_tree: str
    execution_subject: str
    contract_path: Path
    contract_raw: bytes
    contract: dict[str, Any]
    manifest_path: Path
    manifest_raw: bytes
    manifest: dict[str, Any]
    smoke_input_path: Path
    smoke_input_raw: bytes
    program_paths: dict[str, Path]
    program_raw: dict[str, bytes]
    smoke_runner: Any
    manifest_generator: Any


def _bound_file(
    root: Path,
    row_value: object,
    label: str,
    *,
    allowed_prefixes: Sequence[str] = ("docs/reference_cases/",),
) -> tuple[Path, bytes]:
    row = _object(row_value, label)
    _exact_keys(row, ("bytes", "path", "sha256"), label)
    relative = row["path"]
    if not isinstance(relative, str) or not any(
        relative.startswith(prefix) for prefix in allowed_prefixes
    ):
        raise StructuralEvidenceError(f"{label}.path is outside research evidence")
    path = (root / relative).resolve(strict=True)
    if not path.is_relative_to(root.resolve()):
        raise StructuralEvidenceError(f"{label}.path escapes the repository")
    raw = path.read_bytes()
    if len(raw) != _positive_integer(row["bytes"], f"{label}.bytes"):
        raise StructuralEvidenceError(f"{label} byte count mismatch")
    if sha256(raw) != _digest(row["sha256"], f"{label}.sha256"):
        raise StructuralEvidenceError(f"{label} hash mismatch")
    return path, raw


def _validate_execution_extent(rows: Sequence[tuple[str, str]]) -> None:
    """Require the clean successor to contain exactly the six research files."""

    normalized: list[str] = []
    for status, path in rows:
        if status != "A" or not isinstance(path, str) or not path:
            raise StructuralEvidenceError("execution extent contains a non-addition")
        normalized.append(path.replace("\\", "/"))
    if len(normalized) != len(set(normalized)):
        raise StructuralEvidenceError("execution extent contains duplicate paths")
    if tuple(sorted(normalized)) != tuple(sorted(ALLOWED_EXECUTION_EXTENT)):
        raise StructuralEvidenceError("execution extent differs from the six-file research boundary")


def load_authorities(input_path: Path = DEFAULT_INPUT) -> Authorities:
    input_raw, payload = read_canonical(Path(input_path), pretty=True, label="structural input")
    _exact_keys(payload, ("authority", "candidate", "coverage", "execution", "schema"), "input")
    if payload["schema"] != INPUT_SCHEMA:
        raise StructuralEvidenceError(f"input schema must be {INPUT_SCHEMA}")

    candidate = _object(payload["candidate"], "candidate")
    expected_candidate = {
        "commit": "4e5b5976d4286ffd0cda5b8424d154132f3f8da0",
        "parent": "7d85ecef35daa6ebe11f11536a7ede4d288e0aa3",
        "qualified_q4_formulation_id": "E4_PL_QUALIFIED_Q4_HYBRID_V2",
        "qualified_s3_formulation_id": "E4_PL_QUALIFIED_S3_COMPANION_V1",
        "subject": "perf: amortize immutable S3 matrix validation",
        "tree": "96f60dcdd61a78111091ce4f93d7170cf7d0878a",
    }
    if candidate != expected_candidate:
        raise StructuralEvidenceError("frozen candidate identity changed")
    try:
        execution_commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        ).stdout.strip()
        execution_tree = subprocess.run(
            ["git", "show", "-s", "--format=%T", "HEAD"],
            cwd=ROOT,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        ).stdout.strip()
        execution_subject = subprocess.run(
            ["git", "show", "-s", "--format=%s", "HEAD"],
            cwd=ROOT,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        ).stdout.strip()
        candidate_tree = subprocess.run(
            ["git", "show", "-s", "--format=%T", candidate["commit"]],
            cwd=ROOT,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        ).stdout.strip()
        candidate_parent = subprocess.run(
            ["git", "show", "-s", "--format=%P", candidate["commit"]],
            cwd=ROOT,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        ).stdout.strip()
        candidate_subject = subprocess.run(
            ["git", "show", "-s", "--format=%s", candidate["commit"]],
            cwd=ROOT,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        ).stdout.strip()
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", candidate["commit"], execution_commit],
            cwd=ROOT,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        tracked_status = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=no"],
            cwd=ROOT,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        ).stdout
        extent_output = subprocess.run(
            [
                "git",
                "diff",
                "--name-status",
                "--no-renames",
                f"{candidate['commit']}..{execution_commit}",
            ],
            cwd=ROOT,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError) as exc:
        raise StructuralEvidenceError("frozen candidate commit is unavailable") from exc
    if (
        candidate_tree != candidate["tree"]
        or candidate_parent != candidate["parent"]
        or candidate_subject != candidate["subject"]
    ):
        raise StructuralEvidenceError("frozen candidate Git identity mismatch")
    if tracked_status:
        raise StructuralEvidenceError("frozen candidate tracked worktree is dirty")
    extent_rows: list[tuple[str, str]] = []
    for line in extent_output.splitlines():
        pieces = line.split("\t")
        if len(pieces) != 2:
            raise StructuralEvidenceError("execution extent contains malformed Git output")
        extent_rows.append((pieces[0], pieces[1]))
    _validate_execution_extent(extent_rows)

    authority = _object(payload["authority"], "authority")
    _exact_keys(
        authority,
        (
            "connectivity_manifest",
            "input_schema",
            "model_authority",
            "programs",
            "q4_mechanics",
            "qualification_contract",
        ),
        "authority",
    )
    programs = _object(authority["programs"], "authority.programs")
    _exact_keys(programs, PROGRAM_PATHS, "authority.programs")
    program_paths: dict[str, Path] = {}
    program_raw: dict[str, bytes] = {}
    # These hashes are checked before either frozen mechanics helper is loaded.
    for name, relative in PROGRAM_PATHS.items():
        allowed_prefixes = ("tests/",) if name == "qualification_test" else (
            "docs/reference_cases/",
        )
        path, raw = _bound_file(
            ROOT,
            programs[name],
            f"{name} program",
            allowed_prefixes=allowed_prefixes,
        )
        if path != (ROOT / relative).resolve():
            raise StructuralEvidenceError(f"{name} program authority path changed")
        program_paths[name] = path
        program_raw[name] = raw
    schema_path, schema_raw = _bound_file(ROOT, authority["input_schema"], "input schema")
    manifest_path, manifest_raw = _bound_file(ROOT, authority["connectivity_manifest"], "manifest")
    contract_path, contract_raw = _bound_file(ROOT, authority["qualification_contract"], "contract")
    smoke_input_path, smoke_input_raw = _bound_file(ROOT, authority["model_authority"], "model authority")
    q4_path, q4_raw = _bound_file(
        ROOT,
        authority["q4_mechanics"],
        "Q4 mechanics",
        allowed_prefixes=("src/anysolver/",),
    )
    if q4_path != (ROOT / "src" / "anysolver" / "e4_pl_element.py").resolve():
        raise StructuralEvidenceError("Q4 mechanics authority path changed")
    schema_value = strict_json(schema_raw, label="structural input schema")
    if (
        schema_path != (REFERENCE_CASES / "e4_pl_s3_mixed_structural_input_schema.json").resolve()
        or not isinstance(schema_value, dict)
        or schema_raw != pretty_canonical_bytes(schema_value)
        or schema_value.get("$id") != INPUT_SCHEMA
    ):
        raise StructuralEvidenceError("structural input schema authority mismatch")

    manifest_value = strict_json(manifest_raw, label="connectivity manifest")
    contract_value = strict_json(contract_raw, label="qualification contract")
    if not isinstance(manifest_value, dict) or manifest_raw != canonical_bytes(manifest_value):
        raise StructuralEvidenceError("connectivity manifest is not canonical compact JSON")
    if not isinstance(contract_value, dict) or contract_raw != pretty_canonical_bytes(contract_value):
        raise StructuralEvidenceError("qualification contract is not canonical pretty JSON")
    if manifest_value.get("schema") != "anysolver.e4-pl-s3-mixed-mesh-connectivity-manifest-v1":
        raise StructuralEvidenceError("connectivity manifest schema mismatch")
    if contract_value.get("schema") != "anysolver.e4-pl-s3-mixed-mesh-qualification-contract-v1":
        raise StructuralEvidenceError("qualification contract schema mismatch")
    if len(_array(manifest_value.get("records"), "manifest.records")) != 252:
        raise StructuralEvidenceError("gated manifest must contain exactly 252 records")
    if contract_value.get("connectivity_authority", {}).get("sha256") != sha256(manifest_raw):
        raise StructuralEvidenceError("contract does not bind the selected connectivity manifest")

    execution = _object(payload["execution"], "execution")
    _exact_keys(
        execution,
        (
            "automatic_retry",
            "allowed_changed_paths",
            "canonical_cycles",
            "memory_limit_gib_per_process",
            "numerical_threads_per_process",
            "shards",
            "timeout_seconds_per_process",
            "workers",
        ),
        "execution",
    )
    expected_execution = {
        "automatic_retry": False,
        "allowed_changed_paths": list(ALLOWED_EXECUTION_EXTENT),
        "canonical_cycles": 2,
        "memory_limit_gib_per_process": 24,
        "numerical_threads_per_process": 1,
        "shards": list(SHARD_IDS),
        "timeout_seconds_per_process": 600,
        "workers": 3,
    }
    if execution != expected_execution:
        raise StructuralEvidenceError("structural execution controls changed")

    coverage = _object(payload["coverage"], "coverage")
    _exact_keys(
        coverage,
        (
            "convergence_reference",
            "convergence_sequences",
            "locking_fixture",
            "patch_basis_cases",
            "required_diagonals",
            "required_fractions_percent",
            "required_levels",
            "required_masks",
            "special_fixtures",
        ),
        "coverage",
    )
    reference = _object(coverage["convergence_reference"], "coverage.convergence_reference")
    if reference != {
        "interface_series_max_odd_index": 31,
        "length": 1.0,
        "pressure": 1000.0,
        "series_max_odd_index": 99,
        "shear_correction": "5/6",
        "theory": "INDEPENDENT_NAVIER_REISSNER_MINDLIN_UNIFORM_PRESSURE_V1",
        "thickness": 0.01,
        "width": 1.0,
    }:
        raise StructuralEvidenceError("convergence reference identity changed")
    campaign = contract_value["campaign"]
    if coverage["required_levels"] != campaign["levels"]:
        raise StructuralEvidenceError("coverage levels differ from the qualification contract")
    if coverage["required_fractions_percent"] != campaign["gated_s3_area_fractions_percent"]:
        raise StructuralEvidenceError("coverage fractions differ from the qualification contract")
    if coverage["required_masks"] != campaign["mask_policies"]:
        raise StructuralEvidenceError("coverage masks differ from the qualification contract")
    if coverage["required_diagonals"] != campaign["diagonal_policies"]:
        raise StructuralEvidenceError("coverage diagonals differ from the qualification contract")
    if coverage["special_fixtures"] != campaign["special_fixtures"]:
        raise StructuralEvidenceError("special fixtures differ from the qualification contract")
    expected_sequences = [
        {"diagonal": "alternating", "fraction_percent": 0, "mask": "none"},
        {"diagonal": "slash", "fraction_percent": 1, "mask": "dispersed"},
        {"diagonal": "backslash", "fraction_percent": 5, "mask": "chain"},
        {"diagonal": "alternating", "fraction_percent": 10, "mask": "boundary_band"},
        {"diagonal": "alternating", "fraction_percent": 25, "mask": "hole_band"},
    ]
    if coverage["convergence_sequences"] != expected_sequences:
        raise StructuralEvidenceError("declared representative convergence sequences changed")
    expected_patch_basis = [
        {"diagonal": "slash", "fraction_percent": 0, "level": 20, "mask": "none"},
        {
            "diagonal": "slash",
            "fraction_percent": 25,
            "level": 20,
            "mask": "compact_cluster",
        },
        {
            "diagonal": "backslash",
            "fraction_percent": 25,
            "level": 20,
            "mask": "compact_cluster",
        },
        {
            "diagonal": "alternating",
            "fraction_percent": 25,
            "level": 20,
            "mask": "compact_cluster",
        },
    ]
    if coverage["patch_basis_cases"] != expected_patch_basis:
        raise StructuralEvidenceError("patch translation/covariance basis changed")
    if coverage["locking_fixture"] != {
        "diagonal": "alternating",
        "fractions_percent": [0, 10, 25],
        "length": 1.0,
        "longitudinal_divisions": 160,
        "mask": "DETERMINISTIC_STRIP_DISPERSED_V1",
        "tip_force": 1.0,
        "transverse_divisions": 16,
        "width": 0.1,
    }:
        raise StructuralEvidenceError("locking fixture changed")

    smoke_runner = _load_source(
        "_mixed_smoke_authority_for_structural",
        REFERENCE_CASES / "e4_pl_s3_mixed_mesh_qualification_runner.py",
    )
    smoke_authorities = smoke_runner.load_authorities(smoke_input_path)
    if smoke_authorities.input_raw != smoke_input_raw:
        raise StructuralEvidenceError("smoke model authority changed during validation")
    manifest_generator = _load_source(
        "_mixed_manifest_authority_for_structural",
        REFERENCE_CASES / "e4_pl_s3_mixed_mesh_manifest.py",
    )
    _finite_tree(payload, "input")
    return Authorities(
        input_path=Path(input_path).resolve(),
        input_raw=input_raw,
        input=payload,
        execution_commit=execution_commit,
        execution_tree=execution_tree,
        execution_subject=execution_subject,
        contract_path=contract_path,
        contract_raw=contract_raw,
        contract=contract_value,
        manifest_path=manifest_path,
        manifest_raw=manifest_raw,
        manifest=manifest_value,
        smoke_input_path=smoke_input_path,
        smoke_input_raw=smoke_input_raw,
        program_paths=program_paths,
        program_raw=program_raw,
        smoke_runner=smoke_runner,
        manifest_generator=manifest_generator,
    )


def verify_execution_identity(authorities: Authorities) -> None:
    """Fail if the clean execution HEAD/tree changes after authorization."""

    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        ).stdout.strip()
        tree = subprocess.run(
            ["git", "show", "-s", "--format=%T", "HEAD"],
            cwd=ROOT,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        ).stdout.strip()
        status = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=no"],
            cwd=ROOT,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError) as exc:
        raise StructuralEvidenceError("cannot revalidate execution Git identity") from exc
    if commit != authorities.execution_commit or tree != authorities.execution_tree or status:
        raise StructuralEvidenceError("clean execution HEAD/tree changed during the bounded run")


def record_id(record: Mapping[str, Any]) -> str:
    return (
        f"N{int(record['level'])}:{int(record['s3_area_fraction_percent'])}PCT:"
        f"{record['mask']}:{record['diagonal']}"
    )


def case_spec(record: Mapping[str, Any], *, prefix: str = "FORMAL") -> dict[str, Any]:
    return {
        "case_id": f"{prefix}_{record_id(record).replace(':', '_').upper()}",
        "topology": {
            "connectivity_sha256": record["connectivity_sha256"],
            "diagonal": record["diagonal"],
            "level": int(record["level"]),
            "mask": record["mask"],
            "split_base_cell_count": int(record["split_base_cell_count"]),
        },
    }


def find_record(
    authorities: Authorities,
    *,
    level: int,
    fraction: int,
    mask: str,
    diagonal: str,
) -> dict[str, Any]:
    rows = [
        row
        for row in authorities.manifest["records"]
        if int(row["level"]) == int(level)
        and int(row["s3_area_fraction_percent"]) == int(fraction)
        and str(row["diagonal"]) == str(diagonal)
        and str(row["mask"]) == ("none" if int(fraction) == 0 else str(mask))
    ]
    if len(rows) != 1:
        raise StructuralEvidenceError(
            f"expected one manifest row for {(level, fraction, mask, diagonal)}, found {len(rows)}"
        )
    return dict(rows[0])


def write_exclusive(path: Path, value: object) -> None:
    _finite_tree(value)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(canonical_bytes(value))


def _boolean(value: object, label: str) -> bool:
    if not isinstance(value, bool):
        raise StructuralEvidenceError(f"{label} must be a boolean")
    return value


def _integer(value: object, label: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise StructuralEvidenceError(f"{label} must be an integer >= {minimum}")
    return int(value)


def _number(value: object, label: str, *, minimum: float | None = None) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise StructuralEvidenceError(f"{label} must be a finite number")
    made = float(value)
    if not math.isfinite(made) or (minimum is not None and made < minimum):
        raise StructuralEvidenceError(f"{label} is outside its finite domain")
    return made


def _optional_number(value: object, label: str, *, minimum: float | None = None) -> float | None:
    return None if value is None else _number(value, label, minimum=minimum)


def _string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise StructuralEvidenceError(f"{label} must be a nonempty string")
    return value


def _string_array(value: object, label: str) -> list[str]:
    rows = _array(value, label)
    made = [_string(item, f"{label}[{index}]") for index, item in enumerate(rows)]
    if len(set(made)) != len(made):
        raise StructuralEvidenceError(f"{label} contains duplicates")
    return made


def _manifest_record_map(authorities: Authorities) -> dict[str, dict[str, Any]]:
    return {record_id(row): dict(row) for row in authorities.manifest["records"]}


def _expected_patch_payload(
    payload: object,
    authorities: Authorities,
    *,
    quick: bool,
) -> tuple[dict[str, str], list[str]]:
    made = _object(payload, "patch payload")
    _exact_keys(
        made,
        (
            "basis",
            "basis_complete",
            "contradictions",
            "contradictions_classifying",
            "manifest_audit",
            "scope",
        ),
        "patch payload",
    )
    specifications = list(authorities.input["coverage"]["patch_basis_cases"])
    expected_specs = specifications[:2] if quick else specifications
    basis = _array(made["basis"], "patch payload.basis")
    if len(basis) != len(expected_specs):
        raise StructuralEvidenceError("patch basis count differs from the execution tier")
    records = _manifest_record_map(authorities)
    patch_contradictions: list[str] = []
    covariance_contradictions: list[str] = []
    patch_limit = float(
        authorities.contract["acceptance_gates"]["patch_and_equilibrium"][
            "patch_residual_maximum"
        ]
    )
    equilibrium = authorities.contract["acceptance_gates"]["patch_and_equilibrium"]
    covariance_limit = float(
        authorities.contract["acceptance_gates"]["symmetry_and_covariance_residual_maximum"]
    )
    for index, (item, spec) in enumerate(zip(basis, expected_specs)):
        row = _object(item, f"patch payload.basis[{index}]")
        _exact_keys(
            row,
            (
                "connectivity_sha256",
                "covariance_residual",
                "force_loaded_in_plane",
                "patch_residuals",
                "pl_participation",
                "q4_residual_hourglass_participation",
                "record_id",
                "symmetry_residual",
                "transverse_shear_classification",
            ),
            f"patch payload.basis[{index}]",
        )
        expected_record = find_record(
            authorities,
            level=int(spec["level"]),
            fraction=int(spec["fraction_percent"]),
            mask=str(spec["mask"]),
            diagonal=str(spec["diagonal"]),
        )
        rid = _string(row["record_id"], f"patch basis {index} record_id")
        if rid != record_id(expected_record) or rid not in records:
            raise StructuralEvidenceError("patch basis record order or identity changed")
        if _digest(row["connectivity_sha256"], f"patch basis {index} connectivity") != str(
            expected_record["connectivity_sha256"]
        ):
            raise StructuralEvidenceError("patch basis connectivity hash mismatch")
        force = _object(row["force_loaded_in_plane"], f"patch basis {index} force")
        force_keys = (
            "action_reaction_residual",
            "edge_work_residual",
            "force_residual",
            "moment_residual",
            "patch_residual",
        )
        _exact_keys(force, force_keys, f"patch basis {index} force")
        force_values = {
            name: _number(force[name], f"patch basis {index} force.{name}", minimum=0.0)
            for name in force_keys
        }
        if force_values["patch_residual"] > patch_limit:
            patch_contradictions.append(f"{rid}:PATCH")
        for name in force_keys[:-1]:
            if force_values[name] > float(equilibrium[f"{name}_maximum"]):
                patch_contradictions.append(f"{rid}:{name.upper()}")
        residuals = _object(row["patch_residuals"], f"patch basis {index} residuals")
        _exact_keys(residuals, ("bending", "membrane", "shear"), f"patch basis {index} residuals")
        residual_values = {
            name: _number(
                residuals[name],
                f"patch basis {index} residuals.{name}",
                minimum=0.0,
            )
            for name in ("bending", "membrane", "shear")
        }
        for name in ("bending", "membrane"):
            if residual_values[name] > patch_limit:
                patch_contradictions.append(f"{rid}:{name.upper()}_PATCH")
        pl = _object(row["pl_participation"], f"patch basis {index} PL")
        _exact_keys(pl, ("Q4_PL", "S3_PL"), f"patch basis {index} PL")
        for name in ("Q4_PL", "S3_PL"):
            _number(pl[name], f"patch basis {index} PL.{name}")
        _number(
            row["q4_residual_hourglass_participation"],
            f"patch basis {index} Q4 residual/hourglass",
        )
        symmetry = _number(row["symmetry_residual"], f"patch basis {index} symmetry", minimum=0.0)
        covariance = _number(
            row["covariance_residual"], f"patch basis {index} covariance", minimum=0.0
        )
        if symmetry > covariance_limit:
            covariance_contradictions.append(f"{rid}:SYMMETRY")
        if covariance > covariance_limit:
            covariance_contradictions.append(f"{rid}:COVARIANCE")
        if row["transverse_shear_classification"] != (
            "NONCLASSIFYING_NOT_THE_PUBLISHED_FORCE_LOADED_PATCH"
        ):
            raise StructuralEvidenceError("transverse-shear diagnostic was overstated")
    expected_complete = len(basis) == len(specifications) and not quick
    if _boolean(made["basis_complete"], "patch payload.basis_complete") != expected_complete:
        raise StructuralEvidenceError("patch basis completeness was not recomputed")
    audit = _object(made["manifest_audit"], "patch payload.manifest_audit")
    _exact_keys(
        audit,
        (
            "coverage_exact",
            "gated_record_count",
            "manifest_regeneration_byte_identical",
            "observed",
            "research_control_record_count",
        ),
        "patch payload.manifest_audit",
    )
    if (
        _boolean(audit["coverage_exact"], "manifest coverage") is not True
        or _boolean(audit["manifest_regeneration_byte_identical"], "manifest regeneration")
        is not True
        or _integer(audit["gated_record_count"], "manifest gated count") != 252
        or _integer(audit["research_control_record_count"], "manifest control count") != 12
    ):
        raise StructuralEvidenceError("manifest audit does not prove the frozen inventory")
    observed = _object(audit["observed"], "manifest observed")
    _exact_keys(observed, ("diagonals", "fractions_percent", "levels", "masks"), "manifest observed")
    if observed != {
        "diagonals": sorted(authorities.input["coverage"]["required_diagonals"]),
        "fractions_percent": sorted(authorities.input["coverage"]["required_fractions_percent"]),
        "levels": sorted(authorities.input["coverage"]["required_levels"]),
        "masks": sorted(authorities.input["coverage"]["required_masks"]),
    }:
        raise StructuralEvidenceError("manifest audit inventory mismatch")
    scope = _object(made["scope"], "patch payload.scope")
    expected_scope = {
        "all_registered_topology_hashes": "EXECUTED",
        "bending_patch": "EXECUTED",
        "d3_numberings": "UNEXECUTED_ALL_SIX_REQUIRED",
        "force_loaded_in_plane_patch": "EXECUTED",
        "membrane_patch": "EXECUTED",
        "physical_director_reversal": "UNEXECUTED_REQUIRED",
        "translation_equivalence": (
            "REGULAR_CELL_BASIS_DIAGNOSTIC_NOT_A_SUBSTITUTE_FOR_D3_OR_REVERSAL"
        ),
        "transverse_force_loaded_shear_patch": (
            "UNEXECUTED_NO_HASH_BOUND_LOAD_AND_RESTRAINT_PROTOCOL"
        ),
    }
    if scope != expected_scope:
        raise StructuralEvidenceError("patch/covariance scope was overstated")
    expected_contradictions = sorted(set(patch_contradictions + covariance_contradictions))
    if _string_array(made["contradictions"], "patch contradictions") != expected_contradictions:
        raise StructuralEvidenceError("patch contradictions were not recomputed")
    formal = not quick
    if _boolean(made["contradictions_classifying"], "patch classifying flag") != bool(
        formal and expected_contradictions
    ):
        raise StructuralEvidenceError("patch contradiction classification mismatch")
    if quick:
        return {
            "patch_and_equilibrium": PARTIAL,
            "symmetry_and_covariance": PARTIAL,
        }, expected_contradictions
    return {
        "patch_and_equilibrium": FAIL if patch_contradictions else PARTIAL,
        # This remains partial until every D3 numbering and physical director
        # reversal is constructed and executed, irrespective of this basis.
        "symmetry_and_covariance": FAIL if covariance_contradictions else PARTIAL,
    }, expected_contradictions


def _expected_convergence_payload(
    payload: object,
    authorities: Authorities,
    *,
    quick: bool,
) -> tuple[dict[str, str], list[str]]:
    made = _object(payload, "convergence payload")
    _exact_keys(
        made,
        (
            "complete_registered_sequence_count",
            "contradictions",
            "contradictions_classifying",
            "energy_scope",
            "executed_levels",
            "executed_sequence_count",
            "interface_rows",
            "rows",
            "selected_sequence_count",
            "scope_complete",
            "unresolved_interface_ratio_count",
        ),
        "convergence payload",
    )
    declared = list(authorities.input["coverage"]["convergence_sequences"])
    levels = list(authorities.input["coverage"]["required_levels"])
    executed_sequences = declared[:2] if quick else declared
    executed_levels = levels[:2] if quick else levels
    if made["executed_levels"] != executed_levels:
        raise StructuralEvidenceError("convergence executed levels changed")
    complete_count = 3 + 4 * 5 * 3
    if _integer(made["complete_registered_sequence_count"], "complete sequence count") != complete_count:
        raise StructuralEvidenceError("complete sequence inventory changed")
    if _integer(made["selected_sequence_count"], "selected sequence count") != len(declared):
        raise StructuralEvidenceError("selected sequence count was not recomputed")
    if _integer(made["executed_sequence_count"], "executed sequence count") != len(
        executed_sequences
    ):
        raise StructuralEvidenceError("executed sequence count was not recomputed")
    rows = _array(made["rows"], "convergence payload.rows")
    if len(rows) != len(executed_sequences):
        raise StructuralEvidenceError("convergence row count mismatch")
    manifest_records = _manifest_record_map(authorities)
    convergence_contradictions: list[str] = []
    pl_contradictions: list[str] = []
    convergence_gate = authorities.contract["acceptance_gates"]["convergence"]
    pl_limit = float(
        authorities.contract["acceptance_gates"]["pl_participation"]["finest_fraction_maximum"]
    )
    record_ids: set[str] = set()
    for sequence_index, (item, expected_sequence) in enumerate(zip(rows, executed_sequences)):
        sequence = _object(item, f"convergence row {sequence_index}")
        _exact_keys(
            sequence,
            ("energy_defect_proxy_slope", "records", "response_error_slope", "sequence"),
            f"convergence row {sequence_index}",
        )
        if sequence["sequence"] != expected_sequence:
            raise StructuralEvidenceError("convergence sequence order changed")
        records = _array(sequence["records"], f"convergence row {sequence_index}.records")
        if len(records) != len(executed_levels):
            raise StructuralEvidenceError("convergence level coverage mismatch")
        response_values: list[float] = []
        energy_values: list[float] = []
        pl_values: dict[str, list[float]] = {"Q4_PL": [], "S3_PL": []}
        for level_index, (record_value, level) in enumerate(zip(records, executed_levels)):
            record = _object(record_value, f"convergence record {sequence_index}:{level_index}")
            _exact_keys(
                record,
                (
                    "center_displacement",
                    "center_displacement_relative_error",
                    "connectivity_sha256",
                    "energy_defect_proxy",
                    "finite_element_strain_energy",
                    "level",
                    "mindlin_center_displacement",
                    "mindlin_strain_energy",
                    "pl_participation",
                    "q4_residual_hourglass_participation",
                    "record_id",
                    "solver_status",
                ),
                f"convergence record {sequence_index}:{level_index}",
            )
            if _integer(record["level"], "convergence record level") != int(level):
                raise StructuralEvidenceError("convergence record level changed")
            expected_record = find_record(
                authorities,
                level=int(level),
                fraction=int(expected_sequence["fraction_percent"]),
                mask=str(expected_sequence["mask"]),
                diagonal=str(expected_sequence["diagonal"]),
            )
            rid = _string(record["record_id"], "convergence record ID")
            if rid != record_id(expected_record) or rid in record_ids or rid not in manifest_records:
                raise StructuralEvidenceError("convergence record identity/order mismatch")
            record_ids.add(rid)
            if _digest(record["connectivity_sha256"], "convergence connectivity") != str(
                expected_record["connectivity_sha256"]
            ):
                raise StructuralEvidenceError("convergence connectivity hash mismatch")
            if record["solver_status"] != "converged":
                raise StructuralEvidenceError("convergence record is not a converged solve")
            response_values.append(
                _number(
                    record["center_displacement_relative_error"],
                    "center displacement relative error",
                    minimum=0.0,
                )
            )
            energy_values.append(
                _number(record["energy_defect_proxy"], "energy defect proxy", minimum=0.0)
            )
            for name in (
                "center_displacement",
                "finite_element_strain_energy",
                "mindlin_center_displacement",
                "mindlin_strain_energy",
            ):
                _number(record[name], f"convergence record {name}", minimum=0.0)
            pl = _object(record["pl_participation"], "convergence PL participation")
            _exact_keys(pl, ("Q4_PL", "S3_PL"), "convergence PL participation")
            for name in ("Q4_PL", "S3_PL"):
                pl_values[name].append(_number(pl[name], f"convergence PL {name}"))
            _number(
                record["q4_residual_hourglass_participation"],
                "Q4 residual/hourglass participation",
            )
        for first, second, record in zip(response_values, response_values[1:], records[1:]):
            if second > float(convergence_gate["successive_error_factor_maximum"]) * first + 1.0e-13:
                convergence_contradictions.append(
                    f"{record['record_id']}:SUCCESSIVE_RESPONSE_ERROR"
                )
        for name, values in pl_values.items():
            if values and values[-1] > pl_limit:
                pl_contradictions.append(f"{records[-1]['record_id']}:{name}:FINEST_PARTICIPATION")
            if any(second > first + 1.0e-14 for first, second in zip(values, values[1:])):
                pl_contradictions.append(f"{records[-1]['record_id']}:{name}:NOT_NONINCREASING")
        expected_response_slope = slope(response_values, executed_levels)
        expected_energy_slope = slope(energy_values, executed_levels)
        if sequence["response_error_slope"] != expected_response_slope:
            raise StructuralEvidenceError("response-error slope was not recomputed")
        if sequence["energy_defect_proxy_slope"] != expected_energy_slope:
            raise StructuralEvidenceError("energy-defect slope was not recomputed")
    interface_gate = authorities.contract["acceptance_gates"]["interface_resultants"]
    interface_rows = _array(made["interface_rows"], "convergence interface rows")
    expected_interface_count = max(0, len(executed_sequences) - 1) * len(executed_levels)
    if len(interface_rows) != expected_interface_count:
        raise StructuralEvidenceError("interface row coverage mismatch")
    interface_contradictions: list[str] = []
    unresolved = 0
    for index, item in enumerate(interface_rows):
        row = _object(item, f"interface row {index}")
        _exact_keys(
            row,
            (
                "all_q4_l2_error",
                "all_q4_p99_error",
                "band_cell_count",
                "l2_ratio_to_all_q4",
                "mixed_l2_error",
                "mixed_p99_error",
                "p99_ratio_to_all_q4",
                "record_id",
            ),
            f"interface row {index}",
        )
        rid = _string(row["record_id"], f"interface row {index} ID")
        if rid not in record_ids or ":0PCT:" in rid:
            raise StructuralEvidenceError("interface row does not bind a mixed solved record")
        _integer(row["band_cell_count"], f"interface row {index} count", minimum=1)
        for name in (
            "all_q4_l2_error",
            "all_q4_p99_error",
            "mixed_l2_error",
            "mixed_p99_error",
        ):
            _number(row[name], f"interface row {index}.{name}", minimum=0.0)
        l2 = _optional_number(row["l2_ratio_to_all_q4"], f"interface row {index}.l2", minimum=0.0)
        p99 = _optional_number(
            row["p99_ratio_to_all_q4"], f"interface row {index}.p99", minimum=0.0
        )
        unresolved += int(l2 is None or p99 is None)
        fraction = int(rid.split(":")[1].removesuffix("PCT"))
        l2_limit = float(
            interface_gate[
                "l2_ratio_at_25_percent" if fraction == 25 else "l2_ratio_through_10_percent"
            ]
        )
        p99_limit = float(
            interface_gate[
                "p99_ratio_at_25_percent" if fraction == 25 else "p99_ratio_through_10_percent"
            ]
        )
        if l2 is not None and l2 > l2_limit:
            interface_contradictions.append(f"{rid}:INTERFACE_L2")
        if p99 is not None and p99 > p99_limit:
            interface_contradictions.append(f"{rid}:INTERFACE_P99")
    if _integer(made["unresolved_interface_ratio_count"], "unresolved interface count") != unresolved:
        raise StructuralEvidenceError("unresolved interface count was not recomputed")
    complete_scope = len(declared) == complete_count and executed_levels == levels
    if _boolean(made["scope_complete"], "convergence scope_complete") != complete_scope:
        raise StructuralEvidenceError("convergence scope completeness was not recomputed")
    if made["energy_scope"] != "MINDLIN_TOTAL_ENERGY_DEFECT_PROXY_NOT_A_PROVEN_ENERGY_NORM_ERROR":
        raise StructuralEvidenceError("energy proxy was overstated as an energy norm")
    expected_contradictions = sorted(
        set(convergence_contradictions + interface_contradictions + pl_contradictions)
    )
    if _string_array(made["contradictions"], "convergence contradictions") != expected_contradictions:
        raise StructuralEvidenceError("convergence contradictions were not recomputed")
    formal = not quick
    if _boolean(made["contradictions_classifying"], "convergence classifying flag") != bool(
        formal and expected_contradictions
    ):
        raise StructuralEvidenceError("convergence contradiction classification mismatch")
    if quick:
        return {
            "convergence": PARTIAL,
            "interface_resultants": PARTIAL,
            "pl_participation": PARTIAL,
        }, expected_contradictions
    return {
        "convergence": FAIL if convergence_contradictions else PARTIAL,
        "interface_resultants": FAIL if interface_contradictions else PARTIAL,
        "pl_participation": FAIL if pl_contradictions else PARTIAL,
    }, expected_contradictions


def _expected_locking_payload(
    payload: object,
    authorities: Authorities,
    *,
    quick: bool,
) -> tuple[dict[str, str], list[str]]:
    made = _object(payload, "locking payload")
    _exact_keys(
        made,
        (
            "analytical_reference",
            "contradictions",
            "contradictions_classifying",
            "fixture_mask",
            "locking_strip_protocol_complete",
            "rows",
            "scope",
            "special_fixtures",
        ),
        "locking payload",
    )
    if made["analytical_reference"] != (
        "EULER_BERNOULLI_CANTILEVER_TIP_FORCE_P_L3_OVER_3_E_I"
    ):
        raise StructuralEvidenceError("locking reference identity changed")
    fixture = authorities.input["coverage"]["locking_fixture"]
    fractions = list(fixture["fractions_percent"])
    thicknesses = list(
        authorities.contract["acceptance_gates"]["locking"]["thickness_over_length"]
    )
    expected_fractions = fractions[:2] if quick else fractions
    expected_thicknesses = thicknesses[:2] if quick else thicknesses
    expected_nx = 20 if quick else int(fixture["longitudinal_divisions"])
    expected_ny = 2 if quick else int(fixture["transverse_divisions"])
    rows = _array(made["rows"], "locking payload.rows")
    if len(rows) != len(expected_fractions):
        raise StructuralEvidenceError("locking fraction coverage mismatch")
    contradictions: list[str] = []
    error_limit = float(
        authorities.contract["acceptance_gates"]["locking"]["finest_response_error_maximum"]
    )
    spread_limit = float(
        authorities.contract["acceptance_gates"]["locking"][
            "thin_range_response_spread_maximum"
        ]
    )
    for group_index, (item, fraction) in enumerate(zip(rows, expected_fractions)):
        group = _object(item, f"locking group {group_index}")
        _exact_keys(
            group,
            ("fraction_percent", "rows", "thin_range_response_spread"),
            f"locking group {group_index}",
        )
        if _integer(group["fraction_percent"], "locking fraction") != int(fraction):
            raise StructuralEvidenceError("locking fraction order changed")
        case_rows = _array(group["rows"], f"locking group {group_index}.rows")
        if len(case_rows) != len(expected_thicknesses):
            raise StructuralEvidenceError("locking thickness coverage mismatch")
        thin: list[float] = []
        for row_index, (item_row, token) in enumerate(zip(case_rows, expected_thicknesses)):
            row = _object(item_row, f"locking row {group_index}:{row_index}")
            _exact_keys(
                row,
                (
                    "fraction_percent",
                    "nx",
                    "ny",
                    "reference_displacement",
                    "relative_error",
                    "response_ratio",
                    "solver_status",
                    "thickness_ratio",
                    "tip_displacement",
                ),
                f"locking row {group_index}:{row_index}",
            )
            if (
                _integer(row["fraction_percent"], "locking row fraction") != int(fraction)
                or _integer(row["nx"], "locking nx", minimum=1) != expected_nx
                or _integer(row["ny"], "locking ny", minimum=1) != expected_ny
                or _number(row["thickness_ratio"], "locking thickness", minimum=0.0)
                != float(token)
                or row["solver_status"] != "converged"
            ):
                raise StructuralEvidenceError("locking case identity changed")
            reference = _number(
                row["reference_displacement"], "locking reference displacement", minimum=0.0
            )
            tip = _number(row["tip_displacement"], "locking tip displacement")
            ratio = _number(row["response_ratio"], "locking response ratio", minimum=0.0)
            relative_error = _number(row["relative_error"], "locking relative error", minimum=0.0)
            if ratio != abs(tip) / reference or relative_error != abs(abs(tip) - reference) / reference:
                raise StructuralEvidenceError("locking response predicates were not recomputed")
            if relative_error > error_limit:
                contradictions.append(f"LOCKING:{int(fraction)}PCT:{float(token):.0e}")
            if float(token) <= 1.0e-4:
                thin.append(ratio)
        expected_spread = (
            (max(thin) - min(thin)) / max(sum(thin) / len(thin), sys.float_info.min)
            if len(thin) >= 2
            else None
        )
        if group["thin_range_response_spread"] != expected_spread:
            raise StructuralEvidenceError("locking spread was not recomputed")
        if expected_spread is not None and expected_spread > spread_limit:
            contradictions.append(f"LOCKING_SPREAD:{int(fraction)}PCT")
    expected_complete = not quick and expected_fractions == fractions and expected_thicknesses == thicknesses
    if _boolean(
        made["locking_strip_protocol_complete"], "locking strip protocol complete"
    ) != expected_complete:
        raise StructuralEvidenceError("locking strip completeness was not recomputed")
    if made["fixture_mask"] != fixture["mask"]:
        raise StructuralEvidenceError("locking fixture mask changed")
    if made["scope"] != (
        "INDEPENDENT_LOCKING_STRIP_REPRESENTATIVE_NOT_THE_COMPLETE_REGISTERED_SQUARE_MASK_CAMPAIGN"
    ):
        raise StructuralEvidenceError("locking scope was overstated")
    fixtures = _object(made["special_fixtures"], "locking special fixtures")
    expected_fixtures = {
        name: "UNEXECUTED_NO_DEDICATED_FIXTURE_CONSTRUCTED"
        for name in authorities.input["coverage"]["special_fixtures"]
    }
    if fixtures != expected_fixtures:
        raise StructuralEvidenceError("special fixture execution was overstated")
    expected_contradictions = sorted(set(contradictions))
    if _string_array(made["contradictions"], "locking contradictions") != expected_contradictions:
        raise StructuralEvidenceError("locking contradictions were not recomputed")
    formal = not quick
    if _boolean(made["contradictions_classifying"], "locking classifying flag") != bool(
        formal and expected_contradictions
    ):
        raise StructuralEvidenceError("locking contradiction classification mismatch")
    if quick:
        return {"locking": PARTIAL, "special_fixtures": PARTIAL}, expected_contradictions
    return {
        "locking": FAIL if expected_contradictions else PARTIAL,
        "special_fixtures": PARTIAL,
    }, expected_contradictions


def validate_shard(
    value: object,
    expected_shard: str | None = None,
    *,
    authorities: Authorities,
) -> dict[str, Any]:
    made = _object(value, "shard")
    _exact_keys(
        made,
        (
            "authority_sha256",
            "coverage",
            "diagnostic_payload",
            "diagnostic_payload_sha256",
            "execution_commit",
            "execution_tier",
            "execution_tree",
            "gate_status",
            "production_restriction",
            "schema",
            "shard_id",
            "terminal_status",
        ),
        "shard",
    )
    if made["schema"] != SHARD_SCHEMA or made["shard_id"] not in SHARD_IDS:
        raise StructuralEvidenceError("shard identity mismatch")
    if expected_shard is not None and made["shard_id"] != expected_shard:
        raise StructuralEvidenceError("unexpected shard ID")
    if made["production_restriction"] != PRODUCTION_RESTRICTION:
        raise StructuralEvidenceError("production restriction changed")
    if made["execution_tier"] not in {"FORMAL_BOUNDED", "QUICK_NONCLASSIFYING"}:
        raise StructuralEvidenceError("shard execution tier is invalid")
    expected_gates = {
        SHARD_IDS[0]: {"patch_and_equilibrium", "symmetry_and_covariance"},
        SHARD_IDS[1]: {"convergence", "interface_resultants", "pl_participation"},
        SHARD_IDS[2]: {"locking", "special_fixtures"},
    }[made["shard_id"]]
    gate_status = _object(made["gate_status"], "shard.gate_status")
    if set(gate_status) != expected_gates or any(status not in GATE_STATUSES for status in gate_status.values()):
        raise StructuralEvidenceError("shard gate status is invalid")
    coverage = _object(made["coverage"], "shard.coverage")
    _exact_keys(
        coverage,
        ("executed_gate_count", "gate_count", "representative_only_gate_count"),
        "shard.coverage",
    )
    if made["authority_sha256"] != sha256(authorities.input_raw):
        raise StructuralEvidenceError("shard authority hash mismatch")
    if (
        made["execution_commit"] != authorities.execution_commit
        or made["execution_tree"] != authorities.execution_tree
    ):
        raise StructuralEvidenceError("shard clean execution HEAD/tree mismatch")
    diagnostic = _object(made["diagnostic_payload"], "shard.diagnostic_payload")
    if sha256(canonical_bytes(diagnostic)) != _digest(
        made["diagnostic_payload_sha256"], "diagnostic payload hash"
    ):
        raise StructuralEvidenceError("diagnostic payload hash mismatch")
    quick = made["execution_tier"] == "QUICK_NONCLASSIFYING"
    if made["shard_id"] == SHARD_IDS[0]:
        expected_status, _ = _expected_patch_payload(diagnostic, authorities, quick=quick)
    elif made["shard_id"] == SHARD_IDS[1]:
        expected_status, _ = _expected_convergence_payload(diagnostic, authorities, quick=quick)
    else:
        expected_status, _ = _expected_locking_payload(diagnostic, authorities, quick=quick)
    if gate_status != expected_status:
        raise StructuralEvidenceError("shard gate predicates were not recomputed")
    expected_coverage = {
        "executed_gate_count": sum(
            status not in {BLOCKED, UNEXECUTED} for status in expected_status.values()
        ),
        "gate_count": len(expected_status),
        "representative_only_gate_count": sum(
            status == PARTIAL for status in expected_status.values()
        ),
    }
    if coverage != expected_coverage:
        raise StructuralEvidenceError("shard coverage counts were not recomputed")
    expected_terminal = (
        "BLOCKED"
        if any(status == BLOCKED for status in expected_status.values())
        else "CONTRADICTION"
        if any(status == FAIL for status in expected_status.values())
        else "COMPLETE_PROCESS_STATE"
    )
    if made["terminal_status"] != expected_terminal:
        raise StructuralEvidenceError("shard terminal was not recomputed")
    if quick and (
        any(status != PARTIAL for status in expected_status.values())
        or made["terminal_status"] != "COMPLETE_PROCESS_STATE"
    ):
        raise StructuralEvidenceError("quick execution attempted to classify")
    _finite_tree(made)
    return made


def choose_terminal(statuses: Sequence[str], *, blocked: bool) -> str:
    if blocked or any(status == BLOCKED for status in statuses):
        return TERMINALS[0]
    if any(status == FAIL for status in statuses):
        return TERMINALS[1]
    if any(status in {PARTIAL, UNEXECUTED} for status in statuses):
        return TERMINALS[2]
    if statuses and all(status == COMPLETE for status in statuses):
        return TERMINALS[3]
    return TERMINALS[0]


def slope(values: Sequence[float], levels: Sequence[int]) -> float | None:
    """Least-squares log-log convergence slope, or ``None`` for zero data."""

    if len(values) != len(levels) or len(values) < 3:
        return None
    if any(value <= 0.0 or not math.isfinite(value) for value in values):
        return None
    x = [-math.log(float(level)) for level in levels]
    y = [math.log(float(value)) for value in values]
    mean_x = sum(x) / len(x)
    mean_y = sum(y) / len(y)
    denominator = sum((item - mean_x) ** 2 for item in x)
    if denominator == 0.0:
        return None
    return sum((a - mean_x) * (b - mean_y) for a, b in zip(x, y)) / denominator


def percentile_nearest_rank(values: Sequence[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(float(value) for value in values)
    index = max(0, min(len(ordered) - 1, math.ceil(float(fraction) * len(ordered)) - 1))
    return ordered[index]
