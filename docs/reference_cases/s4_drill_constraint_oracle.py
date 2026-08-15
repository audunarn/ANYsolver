"""Independent arbitrary-precision S4 drill-constraint certification oracle.

This module intentionally imports no :mod:`anysolver` code.  It reconstructs
the Q4 continuum, the literal 2025 Eq. 21 and Eqs. 24--25 fields, the /D mass
interpolation, the global Galerkin drill constraint, and the registered
rank/projector calculus from the content-addressed cases file.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import re
import stat
import sys
import sysconfig
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Sequence


if os.environ.get("MPMATH_NOGMPY") != "1":
    raise RuntimeError("MPMATH_NOGMPY=1 must be set before importing the oracle")

import mpmath as mp


SCHEMA = "s4-drill-constraint-certification-proof-v1"
PRECISION_SHARD_SCHEMA = "s4-drill-constraint-precision-shard-v1"
CASES_SCHEMA = "s4-drill-constraint-certification-cases-v1"
ENVIRONMENT_SCHEMA = "s4-drill-constraint-environment-v1"
FORMULATION_ID = "mitc4_plus_d_published_2025_linear_spin_constrained_research_v1"

GOVERNING_PLAN_SHA256 = "90b5c4903ee6a9c06056f7e1f3ab21dae0626c185a27627843a04bf289430e3a"
TOR_PLAN_SHA256 = "8e969863806461124510e7c31d99a3244fccf15dd67424517320ee819439aa90"
CASES_SHA256 = "b4d663382302e971752f0757f6e869549a54234f485235e06dbef74085860f38"
NULLSPACE_CASES_SHA256 = "223c0e1a1f03d30aa5efbb13e8ecd8f64e5f7f0865e6f11274577d15c6691abf"
NULLSPACE_PROOF_SHA256 = "713465f03be6221119c1ccb7539301be01324445de54fc466d398185b7b481cd"
PRIMARY_PDF_SHA256 = "89c10de1fb13056eb967111c2dbb28fe2d18179090814141455f4e8901d919ea"
SOURCE_SHA256 = {
    "protocol.py": "32bf05e0bd0b282c49c47392caf9400d2c8c136b9b6d1d398b3b54451eacb089",
    "q4_common.py": "de2dcdcd3bc04a90a4db2c074ec15d4e4b097123010f146a0c718506443c3d19",
    "mitc4_plus_d_reference.py": "aaf44046eee607541f2a84ea16cba948cb98130a568bbf8b5b03b243928e9536",
    "mitc4_plus_d_scalar.py": "9e3f1827f813546ff9c183c77e654f268c8a67f976b63ff010749efdeab3118b",
}
PRECISIONS = (80, 160, 320)
MULTIPLIERS = ("0.25", "1", "4")
DECIMAL_RE = re.compile(r"^-?(0|[1-9][0-9]*)(\.[0-9]+)?$")
DOF_INDEX = {"ux": 0, "uy": 1, "uz": 2, "rx": 3, "ry": 4, "rz": 5}
SHARD_DIRECTORY_NAME = ".s4_drill_constraint_shards"
SHARD_OUTPUT_NAMES = tuple(
    f"set{set_number}_{precision:03d}.json"
    for set_number in (1, 2)
    for precision in PRECISIONS
)
REPEAT_MERGE_NAME = "repeat_merged.json"


class ProofInputError(ValueError):
    """A content-addressed input violates the registered proof domain."""


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def cases_path() -> Path:
    return Path(__file__).with_name("s4_drill_constraint_cases.json")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_source_bytes(path: Path) -> bytes:
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raise ProofInputError(f"UTF-8 BOM is forbidden: {path}")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ProofInputError(f"source is not UTF-8: {path}") from exc
    text = text.replace("\r\n", "\n")
    if "\r" in text:
        raise ProofInputError(f"lone CR is forbidden: {path}")
    return text.encode("utf-8")


def _canonical_source_hash(path: Path) -> str:
    return _sha256_bytes(_canonical_source_bytes(path))


def canonical_json_bytes(value: Any) -> bytes:
    """Serialize the registered JSON domain with exactly one terminal LF."""

    def validate(item: Any) -> None:
        if item is None or isinstance(item, (bool, int, str)):
            if isinstance(item, str) and ("\r" in item or "\n" in item):
                raise ProofInputError("canonical JSON strings may not contain CR/LF")
            return
        if isinstance(item, float):
            raise ProofInputError("binary64 values are forbidden in canonical evidence")
        if isinstance(item, (list, tuple)):
            for child in item:
                validate(child)
            return
        if isinstance(item, Mapping):
            for key, child in item.items():
                if type(key) is not str:
                    raise ProofInputError("canonical JSON keys must be actual strings")
                validate(child)
            return
        raise ProofInputError(f"unsupported canonical JSON type: {type(item).__name__}")

    validate(value)
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def _path_key(path: Path) -> str:
    return os.path.normcase(str(path))


def _assert_no_reparse_components(path: Path) -> None:
    """Reject symlinks/reparse points in every existing absolute component."""

    absolute = Path(os.path.abspath(os.fspath(path)))
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current = current / part
        try:
            metadata = current.lstat()
        except FileNotFoundError:
            continue
        attributes = int(getattr(metadata, "st_file_attributes", 0))
        reparse_flag = int(getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))
        if stat.S_ISLNK(metadata.st_mode) or (reparse_flag and attributes & reparse_flag):
            raise ProofInputError(f"symlink/reparse path component is forbidden: {current}")


def _safe_resolved_path(path: str | os.PathLike[str]) -> Path:
    candidate = Path(path)
    _assert_no_reparse_components(candidate)
    resolved = candidate.resolve(strict=False)
    _assert_no_reparse_components(resolved)
    return resolved


def shard_directory() -> Path:
    return (_repo_root() / SHARD_DIRECTORY_NAME).resolve(strict=False)


def _allowed_shard_outputs() -> dict[str, Path]:
    directory = shard_directory()
    return {name: directory / name for name in SHARD_OUTPUT_NAMES}


def _stored_output_path() -> Path:
    return (
        _repo_root()
        / "docs"
        / "reference_cases"
        / "s4_drill_constraint_oracle_output.json"
    ).resolve(strict=False)


def _repeat_merge_path() -> Path:
    return (shard_directory() / REPEAT_MERGE_NAME).resolve(strict=False)


def _validate_output_path(
    supplied: str | os.PathLike[str], allowed: Sequence[Path]
) -> Path:
    resolved = _safe_resolved_path(supplied)
    allowed_by_key = {_path_key(path.resolve(strict=False)): path for path in allowed}
    key = _path_key(resolved)
    if key not in allowed_by_key:
        raise ProofInputError(f"output path is outside the exact allowlist: {resolved}")
    expected = allowed_by_key[key].resolve(strict=False)
    if not expected.parent.is_dir():
        raise ProofInputError(f"output parent directory is absent: {expected.parent}")
    if expected.exists():
        raise ProofInputError(f"output already exists: {expected}")
    temporary = expected.with_name(expected.name + ".tmp")
    if temporary.exists():
        raise ProofInputError(f"temporary output already exists: {temporary}")
    return expected


def _validate_shard_inputs(supplied: Sequence[str | os.PathLike[str]]) -> list[Path]:
    if len(supplied) != len(PRECISIONS):
        raise ProofInputError("exactly three shard inputs are required")
    allowed = _allowed_shard_outputs()
    allowed_by_key = {_path_key(path.resolve(strict=False)): path for path in allowed.values()}
    resolved: list[Path] = []
    keys: list[str] = []
    for item in supplied:
        path = _safe_resolved_path(item)
        key = _path_key(path)
        if key not in allowed_by_key:
            raise ProofInputError(f"shard input is outside the exact directory/allowlist: {path}")
        expected = allowed_by_key[key].resolve(strict=False)
        if not expected.is_file():
            raise ProofInputError(f"shard input is not a regular file: {expected}")
        resolved.append(expected)
        keys.append(key)
    if len(set(keys)) != len(keys):
        raise ProofInputError("case-fold duplicate shard inputs are forbidden")
    prefixes = {path.name.split("_", 1)[0] for path in resolved}
    if len(prefixes) != 1 or prefixes.pop() not in {"set1", "set2"}:
        raise ProofInputError("shard inputs must be one complete set1 or set2 triple")
    return resolved


def _write_canonical_output(target: Path, value: Any) -> tuple[int, str]:
    raw = canonical_json_bytes(value)
    temporary = target.with_name(target.name + ".tmp")
    descriptor = os.open(
        temporary,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0),
        0o600,
    )
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        # The registered cleanup gate requires partial evidence to remain.
        raise
    if target.exists():
        raise ProofInputError(f"output appeared before atomic replace: {target}")
    os.replace(temporary, target)
    return len(raw), _sha256_bytes(raw)


def _actual_decimal(value: Any, name: str) -> str:
    if type(value) is not str or DECIMAL_RE.fullmatch(value) is None:
        raise ProofInputError(f"{name} must be an actual canonical decimal string")
    return value


def _mp(value: Any, name: str = "scalar") -> mp.mpf:
    return mp.mpf(_actual_decimal(value, name))


def mpf_token(value: mp.mpf) -> list[Any]:
    number = mp.mpf(value)
    sign_value, mantissa, exponent, bitcount = number._mpf_
    if bitcount < 0:
        raise ProofInputError("non-finite mpf is forbidden")
    if mantissa == 0:
        return [0, "0", 0, 0]
    return [int(sign_value), str(int(mantissa)), int(exponent), int(bitcount)]


def matrix_tokens(value: mp.matrix) -> list[list[list[Any]]]:
    return [
        [mpf_token(value[row, column]) for column in range(value.cols)]
        for row in range(value.rows)
    ]


def matrix_digest(value: mp.matrix) -> str:
    return _sha256_bytes(canonical_json_bytes(matrix_tokens(value)))


def _is_reparse(path: Path) -> bool:
    attributes = getattr(path.stat(follow_symlinks=False), "st_file_attributes", 0)
    return bool(attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))


def _verified_distribution() -> tuple[dict[str, Any], Path]:
    distribution = importlib.metadata.distribution("mpmath")
    normalized = distribution.metadata["Name"].lower().replace("_", "-")
    if normalized != "mpmath" or distribution.version != "1.3.0":
        raise RuntimeError("the exact mpmath==1.3.0 distribution is required")
    root = Path(distribution.locate_file("")).resolve()
    records: list[list[Any]] = []
    pyc: list[str] = []
    seen: set[str] = set()
    files = distribution.files
    if files is None:
        raise RuntimeError("mpmath distribution exposes no RECORD file set")
    for package_path in files:
        name = package_path.as_posix()
        pure = PurePosixPath(name)
        if (
            not name
            or name in (".", "..")
            or "\\" in name
            or pure.is_absolute()
            or any(part in ("", ".", "..") for part in pure.parts)
        ):
            raise RuntimeError(f"noncanonical distribution path: {name!r}")
        folded = name.casefold()
        if folded in seen:
            raise RuntimeError(f"case-fold duplicate distribution path: {name!r}")
        seen.add(folded)
        target = Path(distribution.locate_file(package_path))
        resolved = target.resolve(strict=True)
        try:
            resolved.relative_to(root)
        except ValueError as exc:
            raise RuntimeError(f"distribution path escapes root: {name!r}") from exc
        if target.is_symlink() or _is_reparse(target) or not resolved.is_file():
            raise RuntimeError(f"distribution path is not a regular non-reparse file: {name!r}")
        if name.casefold().endswith(".pyc"):
            pyc.append(name)
        else:
            records.append([name, resolved.stat().st_size, _sha256_file(resolved)])
    records.sort(key=lambda item: item[0])
    pyc.sort()
    return {
        "name": normalized,
        "version": distribution.version,
        "root": str(root),
        "files": records,
        "excluded_pyc": pyc,
    }, root


def _binary_record(role: str, name: str, path: Path) -> dict[str, Any]:
    resolved = path.resolve(strict=True)
    if resolved.is_symlink() or _is_reparse(resolved) or not resolved.is_file():
        raise RuntimeError(f"binary artifact is not a regular non-reparse file: {resolved}")
    return {
        "role": role,
        "name": name,
        "size": resolved.stat().st_size,
        "sha256": _sha256_file(resolved),
    }


def environment_manifest() -> tuple[dict[str, Any] | None, str | None]:
    if not (
        sys.implementation.name == "cpython"
        and (3, 11) <= sys.version_info[:2] <= (3, 14)
        and sys.byteorder == "little"
    ):
        return None, "unsupported_runtime"
    if mp.libmp.BACKEND != "python":
        raise RuntimeError("mpmath.libmp.BACKEND must be python")
    for name, module in sorted(sys.modules.items()):
        if not name.startswith("mpmath"):
            continue
        filename = getattr(module, "__file__", None)
        if filename and Path(filename).suffix.casefold() in (".pyd", ".so", ".dll", ".dylib"):
            raise RuntimeError(f"native mpmath extension is forbidden: {name}")
    distribution, distribution_root = _verified_distribution()
    distribution_files = {record[0]: record for record in distribution["files"]}
    module_bindings: list[dict[str, Any]] = []
    for role, module_path in (
        ("mpmath", Path(mp.__file__)),
        ("mpmath.libmp", Path(mp.libmp.__file__)),
    ):
        resolved = module_path.resolve(strict=True)
        try:
            relative = resolved.relative_to(distribution_root).as_posix()
        except ValueError as exc:
            raise RuntimeError(f"{role} origin escapes the verified distribution root") from exc
        record = distribution_files.get(relative)
        if record is None:
            raise RuntimeError(f"{role} origin is absent from the verified distribution file set")
        if record[1] != resolved.stat().st_size or record[2] != _sha256_file(resolved):
            raise RuntimeError(f"{role} origin differs from the verified distribution record")
        module_bindings.append(
            {
                "role": role,
                "relative_name": relative,
                "size": record[1],
                "sha256": record[2],
            }
        )
    binaries = [_binary_record("interpreter", "sys.executable", Path(sys.executable))]
    if platform.system() == "Windows":
        dll_name = f"python{sys.version_info.major}{sys.version_info.minor}.dll"
        binaries.append(_binary_record("runtime", dll_name, Path(sys.base_prefix) / dll_name))
    else:
        library = sysconfig.get_config_var("LDLIBRARY")
        library_dir = sysconfig.get_config_var("LIBDIR")
        if library and library_dir:
            binaries.append(_binary_record("runtime", str(library), Path(library_dir) / library))
    binaries.sort(key=lambda item: (item["role"], item["name"]))
    targets: list[dict[str, Any]] = []
    old_dps = mp.mp.dps
    try:
        for decimal_digits in PRECISIONS:
            mp.mp.dps = decimal_digits
            target_epsilon = +mp.mp.eps
            targets.append(
                {
                    "dps": decimal_digits,
                    "prec": int(mp.mp.prec),
                    "eps": mpf_token(target_epsilon),
                }
            )
    finally:
        mp.mp.dps = old_dps
    manifest = {
        "schema": ENVIRONMENT_SCHEMA,
        "implementation": sys.implementation.name,
        "version": sys.version,
        "hexversion": int(sys.hexversion),
        "byteorder": sys.byteorder,
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
        },
        "binaries": binaries,
        "mpmath": {
            **distribution,
            "module_file": str(Path(mp.__file__).resolve(strict=True)),
            "backend": mp.libmp.BACKEND,
            "module_bindings": module_bindings,
        },
        "targets": targets,
    }
    return manifest, None


def load_cases(path: Path | None = None) -> dict[str, Any]:
    target = cases_path() if path is None else Path(path)
    raw = target.read_bytes()
    if _sha256_bytes(raw) != CASES_SHA256:
        raise ProofInputError("drill-constraint cases SHA-256 mismatch")
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProofInputError("cases file is not strict UTF-8 JSON") from exc
    if data.get("schema") != CASES_SCHEMA:
        raise ProofInputError("unexpected cases schema")
    if data.get("governing_plan_sha256") != GOVERNING_PLAN_SHA256:
        raise ProofInputError("cases governing-plan hash mismatch")
    if data.get("tor_plan_sha256") != TOR_PLAN_SHA256:
        raise ProofInputError("cases Tor-plan hash mismatch")
    if data.get("primary_pdf_sha256") != PRIMARY_PDF_SHA256:
        raise ProofInputError("cases paper hash mismatch")
    if data.get("accepted_source_sha256") != SOURCE_SHA256:
        raise ProofInputError("cases accepted-source hash map mismatch")
    root = _repo_root()
    source_dir = root / "src" / "anysolver" / "shell_formulations"
    for name, expected in SOURCE_SHA256.items():
        if _canonical_source_hash(source_dir / name) != expected:
            raise ProofInputError(f"accepted source hash mismatch: {name}")
    if _sha256_file(root / "docs" / "reference_cases" / "s4_nullspace_semantics_cases.json") != NULLSPACE_CASES_SHA256:
        raise ProofInputError("accepted nullspace cases hash mismatch")
    if _sha256_file(root / "docs" / "S4_NULLSPACE_SEMANTICS_PROOF.md") != NULLSPACE_PROOF_SHA256:
        raise ProofInputError("accepted nullspace proof hash mismatch")
    _validate_cases_grammar(data)
    return data


def _validate_triplet(value: Any, name: str) -> None:
    if not isinstance(value, list) or len(value) != 3:
        raise ProofInputError(f"{name} must be a three-string vector")
    for index, scalar in enumerate(value):
        _actual_decimal(scalar, f"{name}[{index}]")


def _validate_cases_grammar(data: Mapping[str, Any]) -> None:
    local_ids: list[str] = []
    for case in data.get("local_cases", []):
        identifier = case.get("id")
        if type(identifier) is not str or not identifier:
            raise ProofInputError("local case IDs must be nonempty strings")
        local_ids.append(identifier)
        if len(case.get("coordinates", [])) != 4 or len(case.get("director_seeds", [])) != 4:
            raise ProofInputError(f"local case must have four corners: {identifier}")
        for index, vector in enumerate(case["coordinates"]):
            _validate_triplet(vector, f"{identifier}.coordinates[{index}]")
        for index, vector in enumerate(case["director_seeds"]):
            _validate_triplet(vector, f"{identifier}.director_seeds[{index}]")
        thickness = case.get("thickness")
        if not isinstance(thickness, list) or len(thickness) != 4:
            raise ProofInputError(f"local thickness must contain four strings: {identifier}")
        for index, scalar in enumerate(thickness):
            _actual_decimal(scalar, f"{identifier}.thickness[{index}]")
    if len(local_ids) != len(set(local_ids)):
        raise ProofInputError("duplicate local case ID")
    topology_ids: list[str] = []
    for topology in data.get("topology_cases", []):
        identifier = topology.get("id")
        if type(identifier) is not str or not identifier:
            raise ProofInputError("topology IDs must be nonempty strings")
        topology_ids.append(identifier)
        nodes = topology.get("nodes")
        elements = topology.get("elements")
        if not isinstance(nodes, list) or not isinstance(elements, list):
            raise ProofInputError(f"topology must materialize nodes/elements: {identifier}")
        node_ids = [node.get("id") for node in nodes]
        element_ids = [element.get("id") for element in elements]
        if node_ids != sorted(node_ids) or len(node_ids) != len(set(node_ids)):
            raise ProofInputError(f"nodes are not unique ordinal records: {identifier}")
        if element_ids != sorted(element_ids) or len(element_ids) != len(set(element_ids)):
            raise ProofInputError(f"elements are not unique ordinal records: {identifier}")
        for node in nodes:
            if type(node.get("id")) is not str:
                raise ProofInputError(f"invalid node ID: {identifier}")
            _validate_triplet(node.get("x"), f"{identifier}.{node.get('id')}.x")
        node_set = set(node_ids)
        for element in elements:
            connectivity = element.get("nodes")
            if not isinstance(connectivity, list) or len(connectivity) != 4 or len(set(connectivity)) != 4:
                raise ProofInputError(f"invalid Q4 connectivity: {identifier}.{element.get('id')}")
            if any(type(node) is not str or node not in node_set for node in connectivity):
                raise ProofInputError(f"connectivity references an unknown node: {identifier}")
            if element.get("state", "active") not in ("active", "softened", "deleted"):
                raise ProofInputError(f"invalid element state: {identifier}")
            for key in ("alpha", "beta", "density"):
                _actual_decimal(element.get(key, "1"), f"{identifier}.{element.get('id')}.{key}")
            director_seed = element.get("director_seed")
            director_seeds = element.get("director_seeds")
            if (director_seed is None) == (director_seeds is None):
                raise ProofInputError(f"exactly one director form is required: {identifier}")
            if director_seed is not None:
                _validate_triplet(director_seed, f"{identifier}.{element.get('id')}.director_seed")
            else:
                if not isinstance(director_seeds, list) or len(director_seeds) != 4:
                    raise ProofInputError(f"director_seeds must have four rows: {identifier}")
                for index, vector in enumerate(director_seeds):
                    _validate_triplet(vector, f"{identifier}.{element.get('id')}.director_seeds[{index}]")
            thickness = element.get("thickness")
            if type(thickness) is str:
                _actual_decimal(thickness, f"{identifier}.{element.get('id')}.thickness")
            elif isinstance(thickness, list) and len(thickness) == 4:
                for index, scalar in enumerate(thickness):
                    _actual_decimal(scalar, f"{identifier}.{element.get('id')}.thickness[{index}]")
            else:
                raise ProofInputError(f"invalid thickness form: {identifier}")
        for constraint_set in topology.get("constraint_sets", []):
            if type(constraint_set.get("id")) is not str or type(constraint_set.get("kind")) is not str:
                raise ProofInputError(f"invalid constraint metadata: {identifier}")
            if type(constraint_set.get("expected_feasible")) is not bool:
                raise ProofInputError(f"constraint expected_feasible must be an actual bool: {identifier}")
            for row in constraint_set.get("rows", []):
                _actual_decimal(row.get("rhs"), f"{identifier}.constraint.rhs")
                for term in row.get("terms", []):
                    if not isinstance(term, list) or len(term) != 3:
                        raise ProofInputError(f"invalid constraint term: {identifier}")
                    node, dof, coefficient = term
                    if node not in node_set or dof not in DOF_INDEX:
                        raise ProofInputError(f"constraint references unknown node/DOF: {identifier}")
                    _actual_decimal(coefficient, f"{identifier}.constraint.coefficient")
    if len(topology_ids) != len(set(topology_ids)):
        raise ProofInputError("duplicate topology case ID")
    for point in data.get("sample_points", []):
        kind = point.get("kind")
        if kind == "center":
            if set(point) != {"kind"}:
                raise ProofInputError("center sample has extra fields")
        elif kind == "gauss":
            if set(point) != {"kind", "r_sign", "s_sign"} or point["r_sign"] not in ("-1", "1") or point["s_sign"] not in ("-1", "1"):
                raise ProofInputError("invalid Gauss sample")
        elif kind == "decimal":
            if set(point) != {"kind", "r", "s"}:
                raise ProofInputError("invalid decimal sample fields")
            _actual_decimal(point["r"], "sample.r")
            _actual_decimal(point["s"], "sample.s")
        else:
            raise ProofInputError(f"unregistered sample kind: {kind!r}")
    expected_warped_covariance = {
        "topology_id": "warped_varied_directors",
        "cyclic": {
            "local_corner_order": [1, 2, 3, 0],
            "natural_map_old_from_new": [["0", "-1"], ["1", "0"]],
            "director_sign": "1",
            "global_dof_pullback": "identity",
        },
        "anchored_reversal": {
            "local_corner_order": [0, 3, 2, 1],
            "natural_map_old_from_new": [["0", "1"], ["1", "0"]],
            "director_sign": "-1",
            "global_dof_pullback": "identity",
        },
    }
    if data.get("derived_variants", {}).get("warped_numbering_covariance") != expected_warped_covariance:
        raise ProofInputError("warped numbering covariance metadata differs from the closed grammar")
    topology_id_set = set(topology_ids)
    if expected_warped_covariance["topology_id"] not in topology_id_set:
        raise ProofInputError("warped covariance metadata references an unknown topology")


def _zeros(rows: int, columns: int) -> mp.matrix:
    return mp.matrix(rows, columns)


def _identity(dimension: int) -> mp.matrix:
    return mp.eye(dimension)


def _transpose(value: mp.matrix) -> mp.matrix:
    return value.T


def _symmetrize(value: mp.matrix) -> mp.matrix:
    return (value + value.T) / 2


def _vstack(values: Sequence[mp.matrix]) -> mp.matrix:
    if not values:
        return _zeros(0, 0)
    columns = values[0].cols
    if any(value.cols != columns for value in values):
        raise ProofInputError("vertical stack column mismatch")
    result = _zeros(sum(value.rows for value in values), columns)
    cursor = 0
    for value in values:
        for row in range(value.rows):
            for column in range(columns):
                result[cursor + row, column] = value[row, column]
        cursor += value.rows
    return result


def _hstack(values: Sequence[mp.matrix]) -> mp.matrix:
    if not values:
        return _zeros(0, 0)
    rows = values[0].rows
    if any(value.rows != rows for value in values):
        raise ProofInputError("horizontal stack row mismatch")
    result = _zeros(rows, sum(value.cols for value in values))
    cursor = 0
    for value in values:
        for row in range(rows):
            for column in range(value.cols):
                result[row, cursor + column] = value[row, column]
        cursor += value.cols
    return result


def _matrix_from_rows(rows: Sequence[Sequence[mp.mpf]], columns: int | None = None) -> mp.matrix:
    if not rows:
        return _zeros(0, 0 if columns is None else columns)
    width = len(rows[0])
    if any(len(row) != width for row in rows):
        raise ProofInputError("ragged matrix rows")
    return mp.matrix([[mp.mpf(value) for value in row] for row in rows])


def _matrix_column(value: mp.matrix, column: int) -> list[mp.mpf]:
    return [value[row, column] for row in range(value.rows)]


def _dot(left: Sequence[mp.mpf], right: Sequence[mp.mpf]) -> mp.mpf:
    if len(left) != len(right):
        raise ProofInputError("dot-product length mismatch")
    return mp.fsum(a * b for a, b in zip(left, right, strict=True))


def _cross(left: Sequence[mp.mpf], right: Sequence[mp.mpf]) -> list[mp.mpf]:
    if len(left) != 3 or len(right) != 3:
        raise ProofInputError("cross product requires three-vectors")
    return [
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    ]


def _norm(vector: Sequence[mp.mpf]) -> mp.mpf:
    return mp.sqrt(_dot(vector, vector))


def _normalize(vector: Sequence[mp.mpf], name: str) -> list[mp.mpf]:
    magnitude = _norm(vector)
    if not magnitude > 0:
        raise ProofInputError(f"singular vector: {name}")
    return [component / magnitude for component in vector]


def _scale_vector(factor: mp.mpf, vector: Sequence[mp.mpf]) -> list[mp.mpf]:
    return [factor * component for component in vector]


def _add_vectors(*vectors: Sequence[mp.mpf]) -> list[mp.mpf]:
    if not vectors:
        return []
    return [mp.fsum(vector[index] for vector in vectors) for index in range(len(vectors[0]))]


def _row(value: mp.matrix, row: int) -> list[mp.mpf]:
    return [value[row, column] for column in range(value.cols)]


def _set_block(target: mp.matrix, row: int, column: int, block: mp.matrix, factor: mp.mpf = mp.mpf(1)) -> None:
    for local_row in range(block.rows):
        for local_column in range(block.cols):
            target[row + local_row, column + local_column] += factor * block[local_row, local_column]


def _cross_matrix(vector: Sequence[mp.mpf]) -> mp.matrix:
    x_value, y_value, z_value = vector
    return mp.matrix(
        [
            [0, -z_value, y_value],
            [z_value, 0, -x_value],
            [-y_value, x_value, 0],
        ]
    )


def _frob(value: mp.matrix) -> mp.mpf:
    return mp.sqrt(mp.fsum(value[row, column] ** 2 for row in range(value.rows) for column in range(value.cols)))


def _exact_zero(value: mp.matrix) -> bool:
    return all(value[row, column] == 0 for row in range(value.rows) for column in range(value.cols))


def _equality_residual(left: mp.matrix, right: mp.matrix) -> mp.mpf:
    if left.rows != right.rows or left.cols != right.cols:
        return mp.inf
    numerator = _frob(left - right)
    denominator = max(_frob(left), _frob(right))
    if denominator == 0:
        return mp.mpf(0) if numerator == 0 else mp.inf
    return numerator / denominator


def q4_shape(r_value: mp.mpf, s_value: mp.mpf) -> tuple[list[mp.mpf], list[list[mp.mpf]]]:
    corners = ((-1, -1), (1, -1), (1, 1), (-1, 1))
    quarter = mp.mpf(1) / 4
    values: list[mp.mpf] = []
    derivatives: list[list[mp.mpf]] = []
    for corner_r, corner_s in corners:
        values.append(quarter * (1 + corner_r * r_value) * (1 + corner_s * s_value))
        derivatives.append(
            [
                quarter * corner_r * (1 + corner_s * s_value),
                quarter * corner_s * (1 + corner_r * r_value),
            ]
        )
    return values, derivatives


def q4_midside_shapes(r_value: mp.mpf, s_value: mp.mpf) -> list[mp.mpf]:
    half = mp.mpf(1) / 2
    return [
        half * (1 - r_value**2) * (1 - s_value),
        half * (1 - s_value**2) * (1 + r_value),
        half * (1 - r_value**2) * (1 + s_value),
        half * (1 - s_value**2) * (1 - r_value),
    ]


def q4_assumed_midside_derivatives(r_value: mp.mpf, s_value: mp.mpf) -> list[list[mp.mpf]]:
    return [
        [-r_value * (1 - s_value), mp.mpf(0)],
        [mp.mpf(0), -s_value * (1 + r_value)],
        [-r_value * (1 + s_value), mp.mpf(0)],
        [mp.mpf(0), -s_value * (1 - r_value)],
    ]


def _tensor_covariant_transform(mapping: mp.matrix) -> mp.matrix:
    a_value, b_value = mapping[0, 0], mapping[0, 1]
    c_value, d_value = mapping[1, 0], mapping[1, 1]
    return mp.matrix(
        [
            [a_value**2, b_value**2, 2 * a_value * b_value],
            [c_value**2, d_value**2, 2 * c_value * d_value],
            [a_value * c_value, b_value * d_value, a_value * d_value + b_value * c_value],
        ]
    )


@dataclass(slots=True)
class Reference:
    coordinates: mp.matrix
    directors: mp.matrix
    director_seed_strings: list[list[str]]
    thickness: list[mp.mpf]
    drill_direction: list[mp.mpf]
    center_covariant: mp.matrix
    center_dual: mp.matrix
    distortion_scalars: tuple[mp.mpf, mp.mpf, mp.mpf]
    mitc_coefficients: tuple[mp.mpf, mp.mpf, mp.mpf, mp.mpf, mp.mpf]
    qrs_coefficients: tuple[mp.mpf, ...]
    edge_coefficients: mp.matrix
    fingerprint: str


def _rows_to_matrix(rows: Sequence[Sequence[mp.mpf]]) -> mp.matrix:
    return mp.matrix([[mp.mpf(value) for value in row] for row in rows])


def _relative_coordinates(coordinates: mp.matrix) -> mp.matrix:
    centroid = [mp.fsum(coordinates[node, axis] for node in range(4)) / 4 for axis in range(3)]
    return mp.matrix(
        [[coordinates[node, axis] - centroid[axis] for axis in range(3)] for node in range(4)]
    )


def _geometry_bases(reference: Reference, r_value: mp.mpf, s_value: mp.mpf, zeta: mp.mpf) -> mp.matrix:
    values, derivatives = q4_shape(r_value, s_value)
    relative = _relative_coordinates(reference.coordinates)
    rows: list[list[mp.mpf]] = []
    for natural_axis in range(2):
        rows.append(
            [
                mp.fsum(
                    derivatives[node][natural_axis]
                    * (
                        relative[node, axis]
                        + zeta * reference.thickness[node] * reference.directors[node, axis] / 2
                    )
                    for node in range(4)
                )
                for axis in range(3)
            ]
        )
    rows.append(
        [
            mp.fsum(
                values[node] * reference.thickness[node] * reference.directors[node, axis] / 2
                for node in range(4)
            )
            for axis in range(3)
        ]
    )
    return _rows_to_matrix(rows)


def _positive_jacobian(reference: Reference, r_value: mp.mpf, s_value: mp.mpf, zeta: mp.mpf) -> mp.mpf:
    determinant = mp.det(_geometry_bases(reference, r_value, s_value, zeta).T)
    if not determinant > 0:
        raise ProofInputError(
            f"nonpositive continuum Jacobian at ({r_value!s},{s_value!s},{zeta!s})"
        )
    return determinant


def _director_fingerprint(
    element_id: str,
    connectivity: Sequence[str],
    seeds: Sequence[Sequence[str]],
    directors: mp.matrix,
) -> str:
    payload = {
        "cases_sha256": CASES_SHA256,
        "element_id": element_id,
        "connectivity": list(connectivity),
        "director_seed_strings": [list(seed) for seed in seeds],
        "normalized_director_mpf_tokens": [
            [mpf_token(directors[node, axis]) for axis in range(3)] for node in range(4)
        ],
    }
    return _sha256_bytes(canonical_json_bytes(payload))


def build_reference(
    coordinates_input: Sequence[Sequence[Any]],
    directors_input: Sequence[Sequence[Any]],
    thickness_input: Sequence[Any],
    *,
    element_id: str,
    connectivity: Sequence[str],
) -> Reference:
    if len(coordinates_input) != 4 or len(directors_input) != 4 or len(thickness_input) != 4:
        raise ProofInputError("Q4 reference requires four coordinates/directors/thicknesses")
    coordinate_rows = [[_mp(value, f"{element_id}.coordinate") for value in row] for row in coordinates_input]
    seed_strings = [
        [_actual_decimal(value, f"{element_id}.director_seed") for value in row]
        for row in directors_input
    ]
    director_rows = [_normalize([mp.mpf(value) for value in row], f"{element_id}.director") for row in seed_strings]
    thickness = [_mp(value, f"{element_id}.thickness") for value in thickness_input]
    if any(value <= 0 for value in thickness):
        raise ProofInputError("thickness must be positive")
    coordinates = _rows_to_matrix(coordinate_rows)
    directors = _rows_to_matrix(director_rows)
    relative = _relative_coordinates(coordinates)
    corner_r = (-1, 1, 1, -1)
    corner_s = (-1, -1, 1, 1)
    center_r = [mp.fsum(corner_r[node] * relative[node, axis] for node in range(4)) / 4 for axis in range(3)]
    center_s = [mp.fsum(corner_s[node] * relative[node, axis] for node in range(4)) / 4 for axis in range(3)]
    distortion = [
        mp.fsum(corner_r[node] * corner_s[node] * relative[node, axis] for node in range(4)) / 4
        for axis in range(3)
    ]
    drill_direction = _normalize(_cross(center_r, center_s), f"{element_id}.drill_direction")
    if any(_dot(_row(directors, node), drill_direction) <= 0 for node in range(4)):
        raise ProofInputError("director reverses or is orthogonal to fixed-center drill direction")
    gram = mp.matrix(
        [
            [_dot(center_r, center_r), _dot(center_r, center_s)],
            [_dot(center_s, center_r), _dot(center_s, center_s)],
        ]
    )
    if not mp.det(gram) > 0:
        raise ProofInputError("singular center-plane metric")
    inverse_gram = gram ** -1
    dual_r = _add_vectors(_scale_vector(inverse_gram[0, 0], center_r), _scale_vector(inverse_gram[0, 1], center_s))
    dual_s = _add_vectors(_scale_vector(inverse_gram[1, 0], center_r), _scale_vector(inverse_gram[1, 1], center_s))
    distortion_r = _dot(distortion, dual_r)
    distortion_s = _dot(distortion, dual_s)
    denominator = distortion_r**2 + distortion_s**2 - 1
    if not denominator < 0:
        raise ProofInputError("MITC4+ distortion denominator is outside the convex branch")
    coefficients = (
        distortion_r * (distortion_r - 1) / (2 * denominator),
        distortion_r * (distortion_r + 1) / (2 * denominator),
        distortion_s * (distortion_s - 1) / (2 * denominator),
        distortion_s * (distortion_s + 1) / (2 * denominator),
        2 * distortion_r * distortion_s / denominator,
    )
    provisional = Reference(
        coordinates=coordinates,
        directors=directors,
        director_seed_strings=seed_strings,
        thickness=thickness,
        drill_direction=drill_direction,
        center_covariant=_rows_to_matrix([center_r, center_s]),
        center_dual=_rows_to_matrix([dual_r, dual_s]),
        distortion_scalars=(distortion_r, distortion_s, denominator),
        mitc_coefficients=coefficients,
        qrs_coefficients=tuple(),
        edge_coefficients=_zeros(4, 2),
        fingerprint="",
    )
    gauss = 1 / mp.sqrt(3)
    reciprocal_a = _geometry_bases(provisional, 0, gauss, 0).T ** -1
    reciprocal_b = _geometry_bases(provisional, 0, -gauss, 0).T ** -1
    reciprocal_c = _geometry_bases(provisional, gauss, 0, 0).T ** -1
    reciprocal_d = _geometry_bases(provisional, -gauss, 0, 0).T ** -1
    a_r = _dot(center_r, _row(reciprocal_a, 0))
    a_s = _dot(center_r, _row(reciprocal_a, 1))
    b_r = _dot(center_r, _row(reciprocal_b, 0))
    b_s = _dot(center_r, _row(reciprocal_b, 1))
    c_r = _dot(center_s, _row(reciprocal_c, 0))
    c_s = _dot(center_s, _row(reciprocal_c, 1))
    d_r = _dot(center_s, _row(reciprocal_d, 0))
    d_s = _dot(center_s, _row(reciprocal_d, 1))
    provisional.qrs_coefficients = (
        (a_r**2 - b_r**2) / 2,
        (a_s**2 - b_s**2) / 2,
        (a_r**2 + b_r**2) / 2,
        (a_r * a_s + b_r * b_s) / 2,
        (a_r * a_s - b_r * b_s) / 2,
        (c_s**2 - d_s**2) / 2,
        (c_r**2 - d_r**2) / 2,
        (c_s**2 + d_s**2) / 2,
        (c_r * c_s + d_r * d_s) / 2,
        (c_r * c_s - d_r * d_s) / 2,
    )
    edge_midpoints = ((0, -1), (1, 0), (0, 1), (-1, 0))
    for edge, (r_edge, s_edge) in enumerate(edge_midpoints):
        node_i = edge
        node_j = (edge + 1) % 4
        x_mid = [(relative[node_i, axis] - relative[node_j, axis]) / 8 for axis in range(3)]
        bases = _geometry_bases(provisional, mp.mpf(r_edge), mp.mpf(s_edge), mp.mpf(0))
        provisional.edge_coefficients[edge, 0] = _dot(x_mid, _scale_vector(-1, _cross(_row(bases, 0), drill_direction)))
        provisional.edge_coefficients[edge, 1] = _dot(x_mid, _cross(_row(bases, 1), drill_direction))
    for r_point, s_point in ((-gauss, -gauss), (gauss, -gauss), (gauss, gauss), (-gauss, gauss), (0, -1), (1, 0), (0, 1), (-1, 0), (0, 0)):
        for zeta in (-1, 0, 1):
            _positive_jacobian(provisional, r_point, s_point, mp.mpf(zeta))
    provisional.fingerprint = _director_fingerprint(element_id, connectivity, seed_strings, directors)
    return provisional


def _continuum_parts(
    reference: Reference, r_value: mp.mpf, s_value: mp.mpf, zeta: mp.mpf
) -> tuple[mp.matrix, mp.matrix, mp.matrix, mp.matrix]:
    values, derivatives = q4_shape(r_value, s_value)
    displacement = _zeros(3, 24)
    derivative_r = _zeros(3, 24)
    derivative_s = _zeros(3, 24)
    derivative_zeta = _zeros(3, 24)
    identity = _identity(3)
    for node in range(4):
        translation = 6 * node
        rotation = translation + 3
        director_rotation = -_cross_matrix(_row(reference.directors, node))
        half_thickness = reference.thickness[node] / 2
        _set_block(displacement, 0, translation, identity, values[node])
        _set_block(derivative_r, 0, translation, identity, derivatives[node][0])
        _set_block(derivative_s, 0, translation, identity, derivatives[node][1])
        _set_block(displacement, 0, rotation, director_rotation, zeta * half_thickness * values[node])
        _set_block(derivative_r, 0, rotation, director_rotation, zeta * half_thickness * derivatives[node][0])
        _set_block(derivative_s, 0, rotation, director_rotation, zeta * half_thickness * derivatives[node][1])
        _set_block(derivative_zeta, 0, rotation, director_rotation, half_thickness * values[node])
    return displacement, derivative_r, derivative_s, derivative_zeta


def _raw_covariant(reference: Reference, r_value: mp.mpf, s_value: mp.mpf, zeta: mp.mpf) -> mp.matrix:
    _, derivative_r, derivative_s, derivative_zeta = _continuum_parts(reference, r_value, s_value, zeta)
    bases = _geometry_bases(reference, r_value, s_value, zeta)
    g_r, g_s, g_zeta = (_row(bases, index) for index in range(3))
    result = _zeros(5, 24)
    for column in range(24):
        h_r = _matrix_column(derivative_r, column)
        h_s = _matrix_column(derivative_s, column)
        h_zeta = _matrix_column(derivative_zeta, column)
        result[0, column] = _dot(g_r, h_r)
        result[1, column] = _dot(g_s, h_s)
        result[2, column] = (_dot(g_r, h_s) + _dot(g_s, h_r)) / 2
        result[3, column] = (_dot(g_r, h_zeta) + _dot(g_zeta, h_r)) / 2
        result[4, column] = (_dot(g_s, h_zeta) + _dot(g_zeta, h_s)) / 2
    return result


def _mid_membrane(reference: Reference, r_value: mp.mpf, s_value: mp.mpf) -> mp.matrix:
    raw = _raw_covariant(reference, r_value, s_value, mp.mpf(0))
    return mp.matrix([[raw[row, column] for column in range(24)] for row in range(3)])


def eq25_qrs_map(reference: Reference, r_value: mp.mpf, s_value: mp.mpf) -> mp.matrix:
    c_r, c_s, denominator = reference.distortion_scalars
    if not denominator < 0:
        raise ProofInputError("Eq. 25 requires negative distortion denominator")
    a_a, a_b, a_c, a_d, a_e = reference.mitc_coefficients
    n_1, n_2, n_3, n_4, n_5, m_1, m_2, m_3, m_4, m_5 = reference.qrs_coefficients
    center_jacobian = _positive_jacobian(reference, 0, 0, 0)
    point_jacobian = _positive_jacobian(reference, r_value, s_value, 0)
    lambda_ratio = center_jacobian / point_jacobian
    inverse_lambda = 1 / lambda_ratio
    root_three = mp.sqrt(3)
    q_map = mp.matrix(
        [
            [(1 + c_r * s_value) ** 2, (c_s * s_value) ** 2, 2 * c_s * s_value * (1 + c_r * s_value)],
            [(c_r * r_value) ** 2, (1 + c_s * r_value) ** 2, 2 * c_r * r_value * (1 + c_s * r_value)],
            [
                c_r * r_value * (1 + c_r * s_value),
                c_s * s_value * (1 + c_s * r_value),
                c_r * c_s * r_value * s_value + (1 + c_r * s_value) * (1 + c_s * r_value),
            ],
        ]
    )
    r_map = lambda_ratio * mp.matrix(
        [
            [inverse_lambda + root_three * n_1 * s_value, root_three * n_2 * s_value, 2 * root_three * n_5 * s_value, n_3 * s_value, n_4 * s_value, n_1 * s_value / root_three],
            [root_three * m_2 * r_value, inverse_lambda + root_three * m_1 * r_value, 2 * root_three * m_5 * r_value, m_4 * r_value, m_3 * r_value, m_1 * r_value / root_three],
            [0, 0, inverse_lambda, 0, 0, 0],
        ]
    )
    s_map = mp.matrix(
        [
            [mp.mpf("0.5") - a_a, mp.mpf("0.5") - a_b, -a_c, -a_d, -a_e],
            [-a_a, -a_b, mp.mpf("0.5") - a_c, mp.mpf("0.5") - a_d, -a_e],
            [0, 0, 0, 0, 1],
            [mp.mpf("0.5"), mp.mpf("-0.5"), 0, 0, 0],
            [0, 0, mp.mpf("0.5"), mp.mpf("-0.5"), 0],
            [a_a, a_b, a_c, a_d, a_e],
        ]
    )
    return q_map * r_map * s_map


def eq25_membrane(reference: Reference, r_value: mp.mpf, s_value: mp.mpf) -> mp.matrix:
    tying_a = _row(_mid_membrane(reference, 0, 1), 0)
    tying_b = _row(_mid_membrane(reference, 0, -1), 0)
    tying_c = _row(_mid_membrane(reference, 1, 0), 1)
    tying_d = _row(_mid_membrane(reference, -1, 0), 1)
    tying_e = _row(_mid_membrane(reference, 0, 0), 2)
    return eq25_qrs_map(reference, r_value, s_value) * _rows_to_matrix([tying_a, tying_b, tying_c, tying_d, tying_e])


def eq21_drill(reference: Reference, r_value: mp.mpf, s_value: mp.mpf) -> mp.matrix:
    derivatives = q4_assumed_midside_derivatives(r_value, s_value)
    scale = _positive_jacobian(reference, 0, 0, 0) / _positive_jacobian(reference, r_value, s_value, 0)
    fixed = _zeros(3, 24)
    for edge in range(4):
        node_i, node_j = edge, (edge + 1) % 4
        derivative_r, derivative_s = derivatives[edge]
        coefficient_r = reference.edge_coefficients[edge, 0]
        coefficient_s = reference.edge_coefficients[edge, 1]
        scalars = [
            scale * derivative_r * coefficient_r,
            -scale * derivative_s * coefficient_s,
            scale * (derivative_s * coefficient_r - derivative_r * coefficient_s) / 2,
        ]
        for tensor_component in range(3):
            for axis in range(3):
                value = scalars[tensor_component] * reference.drill_direction[axis]
                fixed[tensor_component, 6 * node_i + 3 + axis] -= value
                fixed[tensor_component, 6 * node_j + 3 + axis] += value
    c_r, c_s, _ = reference.distortion_scalars
    fixed_to_natural = mp.matrix(
        [[1 + s_value * c_r, s_value * c_s], [r_value * c_r, 1 + r_value * c_s]]
    )
    return _tensor_covariant_transform(fixed_to_natural) * fixed


def _assumed_shear(reference: Reference, r_value: mp.mpf, s_value: mp.mpf, zeta: mp.mpf) -> mp.matrix:
    tying_a = _row(_raw_covariant(reference, 0, 1, zeta), 3)
    tying_b = _row(_raw_covariant(reference, 0, -1, zeta), 3)
    tying_c = _row(_raw_covariant(reference, 1, 0, zeta), 4)
    tying_d = _row(_raw_covariant(reference, -1, 0, zeta), 4)
    result = _zeros(2, 24)
    for column in range(24):
        result[0, column] = ((1 + s_value) * tying_a[column] + (1 - s_value) * tying_b[column]) / 2
        result[1, column] = ((1 + r_value) * tying_c[column] + (1 - r_value) * tying_d[column]) / 2
    return result


def covariant_strain(reference: Reference, r_value: mp.mpf, s_value: mp.mpf, zeta: mp.mpf) -> mp.matrix:
    raw = _raw_covariant(reference, r_value, s_value, zeta)
    membrane = eq25_membrane(reference, r_value, s_value) + eq21_drill(reference, r_value, s_value) - _mid_membrane(reference, r_value, s_value)
    for row in range(3):
        for column in range(24):
            raw[row, column] += membrane[row, column]
    shear = _assumed_shear(reference, r_value, s_value, zeta)
    for row in range(2):
        for column in range(24):
            raw[3 + row, column] = shear[row, column]
    return raw


def _local_transform(reference: Reference, r_value: mp.mpf, s_value: mp.mpf, zeta: mp.mpf) -> tuple[mp.matrix, mp.mpf]:
    bases = _geometry_bases(reference, r_value, s_value, zeta)
    determinant = mp.det(bases.T)
    if not determinant > 0:
        raise ProofInputError("local transform requires positive Jacobian")
    reciprocal = bases.T ** -1
    local_3 = _normalize(_row(bases, 2), "local L3")
    local_1 = _normalize(_cross(_row(bases, 1), local_3), "local L1")
    local_2 = _cross(local_3, local_1)
    local = _rows_to_matrix([local_1, local_2, local_3])
    projection = local * reciprocal.T

    def tensor_row(i_value: int, j_value: int, factor: int) -> list[mp.mpf]:
        ai = _row(projection, i_value)
        aj = _row(projection, j_value)
        return [
            factor * ai[0] * aj[0],
            factor * ai[1] * aj[1],
            factor * (ai[0] * aj[1] + ai[1] * aj[0]),
            factor * (ai[0] * aj[2] + ai[2] * aj[0]),
            factor * (ai[1] * aj[2] + ai[2] * aj[1]),
        ]

    transform = _rows_to_matrix(
        [
            tensor_row(0, 0, 1),
            tensor_row(1, 1, 1),
            tensor_row(0, 1, 2),
            tensor_row(0, 2, 2),
            tensor_row(1, 2, 2),
        ]
    )
    return transform, determinant


def local_strain(reference: Reference, r_value: mp.mpf, s_value: mp.mpf, zeta: mp.mpf) -> tuple[mp.matrix, mp.mpf]:
    transform, determinant = _local_transform(reference, r_value, s_value, zeta)
    return transform * covariant_strain(reference, r_value, s_value, zeta), determinant


def displacement_operator(
    reference: Reference, r_value: mp.mpf, s_value: mp.mpf, zeta: mp.mpf, *, include_drill: bool
) -> mp.matrix:
    displacement, _, _, _ = _continuum_parts(reference, r_value, s_value, zeta)
    if not include_drill:
        return displacement
    midside = q4_midside_shapes(r_value, s_value)
    dual_r = _row(reference.center_dual, 0)
    dual_s = _row(reference.center_dual, 1)
    for edge in range(4):
        node_i, node_j = edge, (edge + 1) % 4
        coefficient_r = reference.edge_coefficients[edge, 0]
        coefficient_s = reference.edge_coefficients[edge, 1]
        physical_direction = _add_vectors(_scale_vector(coefficient_r, dual_r), _scale_vector(-coefficient_s, dual_s))
        block = _zeros(3, 3)
        for row_index in range(3):
            for column_index in range(3):
                block[row_index, column_index] = (
                    midside[edge] * physical_direction[row_index] * reference.drill_direction[column_index]
                )
        _set_block(displacement, 0, 6 * node_i + 3, block, -1)
        _set_block(displacement, 0, 6 * node_j + 3, block, 1)
    return displacement


def drill_trace_and_spin(reference: Reference, r_value: mp.mpf, s_value: mp.mpf) -> tuple[mp.matrix, mp.matrix]:
    values, _ = q4_shape(r_value, s_value)
    drill = _zeros(1, 24)
    for node in range(4):
        for axis in range(3):
            drill[0, 6 * node + 3 + axis] = values[node] * reference.drill_direction[axis]
    _, derivative_r, derivative_s, derivative_zeta = _continuum_parts(reference, r_value, s_value, mp.mpf(0))
    reciprocal = _geometry_bases(reference, r_value, s_value, mp.mpf(0)).T ** -1
    derivatives = (derivative_r, derivative_s, derivative_zeta)
    spin = _zeros(1, 24)
    for column in range(24):
        omega = [mp.mpf(0), mp.mpf(0), mp.mpf(0)]
        for natural_axis in range(3):
            omega = _add_vectors(
                omega,
                _scale_vector(
                    mp.mpf("0.5"),
                    _cross(_row(reciprocal, natural_axis), _matrix_column(derivatives[natural_axis], column)),
                ),
            )
        spin[0, column] = _dot(reference.drill_direction, omega)
    return drill, spin


def _scatter_rows(local: mp.matrix, connectivity: Sequence[int], node_count: int) -> mp.matrix:
    result = _zeros(local.rows, 6 * node_count)
    for local_node, global_node in enumerate(connectivity):
        for row_index in range(local.rows):
            for dof in range(6):
                result[row_index, 6 * global_node + dof] += local[row_index, 6 * local_node + dof]
    return result


def _round_matrix(value: mp.matrix) -> mp.matrix:
    return mp.matrix([[+value[row, column] for column in range(value.cols)] for row in range(value.rows)])


def _reconstruct_matrix(value: mp.matrix) -> mp.matrix:
    return mp.matrix(
        [[mp.mpf(value[row, column]._mpf_) for column in range(value.cols)] for row in range(value.rows)]
    )


def _spectral_rank(
    matrix: mp.matrix,
    *,
    decimal_digits: int,
    eps_p: mp.mpf,
    multiplier: mp.mpf,
    inherited_scale: mp.mpf | None = None,
) -> dict[str, Any]:
    rows, columns = matrix.rows, matrix.cols
    if columns == 0:
        return {
            "rank": 0,
            "kernel_dimension": 0,
            "sigma_max": mp.mpf(0),
            "tau": mp.mpf(0),
            "projector": _zeros(0, 0),
            "kernel_basis": _zeros(0, 0),
            "annihilation": mp.mpf(0),
        }
    if _exact_zero(matrix):
        if inherited_scale is not None and inherited_scale < 0:
            raise ProofInputError("inherited scale must be nonnegative")
        tau = (
            multiplier * 64 * max(rows, columns) * eps_p * inherited_scale
            if inherited_scale is not None
            else mp.mpf(0)
        )
        identity = _identity(columns)
        return {
            "rank": 0,
            "kernel_dimension": columns,
            "sigma_max": mp.mpf(0),
            "tau": tau,
            "projector": identity,
            "kernel_basis": identity,
            "annihilation": mp.mpf(0),
        }
    target_tuples = [
        [matrix[row, column]._mpf_ for column in range(columns)] for row in range(rows)
    ]
    eps_tuple = mp.mpf(eps_p)._mpf_
    with mp.workdps(2 * decimal_digits + 32):
        target = mp.matrix(
            [[mp.mpf(target_tuples[row][column]) for column in range(columns)] for row in range(rows)]
        )
        epsilon = mp.mpf(eps_tuple)
        gram = _symmetrize(target.T * target)
        eigenvalues, eigenvectors = mp.eigsy(gram)
        positive_max = max([mp.mpf(0)] + [eigenvalues[index] for index in range(columns)])
        sigma_max_actual = mp.sqrt(max(mp.mpf(0), positive_max))
        scale = sigma_max_actual if inherited_scale is None else mp.mpf(inherited_scale._mpf_)
        if scale == 0 and not _exact_zero(target):
            raise RuntimeError("a nonzero restriction cannot inherit exact zero scale")
        residual_tolerance = 4096 * max(1, rows, columns) * epsilon
        negative_limit = residual_tolerance * scale**2
        adjusted: list[mp.mpf] = []
        for index in range(columns):
            value = eigenvalues[index]
            if value < -negative_limit:
                raise RuntimeError("Gram matrix failed the registered PSD gate")
            adjusted.append(mp.mpf(0) if value < 0 else value)
        tau = multiplier * 64 * max(rows, columns) * epsilon * scale
        singular = [mp.sqrt(value) for value in adjusted]
        range_indices = [index for index, value in enumerate(singular) if value > tau]
        null_indices = [index for index in range(columns) if index not in range_indices]
        kernel = _zeros(columns, len(null_indices))
        for output_column, source_column in enumerate(null_indices):
            for row in range(columns):
                kernel[row, output_column] = eigenvectors[row, source_column]
        projector = _symmetrize(kernel * kernel.T)
        numerator = _frob(target * kernel)
        denominator = scale * _frob(kernel)
        annihilation = (
            mp.mpf(0) if numerator == 0 and denominator == 0 else numerator / denominator
        )
        if denominator == 0 and numerator != 0:
            annihilation = mp.inf
        if annihilation > residual_tolerance:
            raise RuntimeError("spectral null basis failed direct target-matrix annihilation")
        range_projector = _identity(columns) - projector
        gram_reconstruction = range_projector * gram * range_projector
        reconstruction_numerator = _frob(gram - gram_reconstruction)
        reconstruction_denominator = scale**2
        if reconstruction_denominator == 0:
            reconstruction = mp.mpf(0) if reconstruction_numerator == 0 else mp.inf
        else:
            reconstruction = reconstruction_numerator / reconstruction_denominator
        if reconstruction > residual_tolerance:
            raise RuntimeError("spectral range projector failed target Gram reconstruction")
    return {
        "rank": len(range_indices),
        "kernel_dimension": len(null_indices),
        "sigma_max": +sigma_max_actual,
        "tau": +tau,
        "projector": _round_matrix(projector),
        "kernel_basis": _round_matrix(kernel),
        "annihilation": +annihilation,
    }


def _canonical_basis(projector: mp.matrix, dimension: int, eps_p: mp.mpf) -> mp.matrix:
    if projector.rows != projector.cols or not 0 <= dimension <= projector.rows:
        raise ProofInputError("canonical basis requires a square projector and valid dimension")
    size = projector.rows
    if dimension == 0:
        return _zeros(size, 0)
    chosen: list[list[mp.mpf]] = []
    threshold = 256 * max(1, size) * eps_p
    for column in range(size):
        if len(chosen) == dimension:
            break
        residual = _matrix_column(projector, column)
        for _pass in range(2):
            for basis in chosen:
                coefficient = _dot(basis, residual)
                residual = _add_vectors(residual, _scale_vector(-coefficient, basis))
        magnitude = _norm(residual)
        if magnitude <= threshold:
            continue
        vector = [component / magnitude for component in residual]
        largest = max(abs(component) for component in vector)
        tie_band = 256 * max(1, size) * eps_p * largest
        sign_index = min(
            index for index, component in enumerate(vector) if largest - abs(component) <= tie_band
        )
        if vector[sign_index] < 0:
            vector = [-component for component in vector]
        chosen.append(vector)
    if len(chosen) != dimension:
        raise RuntimeError("projector-column canonicalization lost the registered dimension")
    basis = mp.matrix([[chosen[column][row] for column in range(dimension)] for row in range(size)])
    tolerance = 4096 * max(1, size, dimension) * eps_p
    if _equality_residual(basis.T * basis, _identity(dimension)) > tolerance:
        raise RuntimeError("canonical basis failed orthogonality")
    return basis


def _projector_gate(projector: mp.matrix, dimension: int, eps_p: mp.mpf) -> dict[str, mp.mpf]:
    tolerance = 4096 * max(1, projector.rows, projector.cols) * eps_p
    symmetry = _frob(projector - projector.T)
    idempotence = _frob(projector * projector - projector)
    trace = abs(mp.fsum(projector[index, index] for index in range(projector.rows)) - dimension)
    if max(symmetry, idempotence, trace) > tolerance:
        raise RuntimeError("projector invariant failed")
    return {"symmetry": symmetry, "idempotence": idempotence, "trace": trace}


def _range_projector(
    vectors: mp.matrix,
    *,
    decimal_digits: int,
    eps_p: mp.mpf,
    multiplier: mp.mpf,
    inherited_scale: mp.mpf | None = None,
) -> tuple[mp.matrix, int, dict[str, Any]]:
    if vectors.cols == 0 or _exact_zero(vectors):
        return _zeros(vectors.rows, vectors.rows), 0, {
            "rank": 0,
            "sigma_max": mp.mpf(0),
            "tau": mp.mpf(0),
        }
    decomposition = _spectral_rank(
        vectors.T,
        decimal_digits=decimal_digits,
        eps_p=eps_p,
        multiplier=multiplier,
        inherited_scale=inherited_scale,
    )
    projector = _symmetrize(_identity(vectors.rows) - decomposition["projector"])
    dimension = int(decomposition["rank"])
    _projector_gate(projector, dimension, eps_p)
    return projector, dimension, decomposition


def _operator_intersection(
    parent_projector: mp.matrix,
    parent_dimension: int,
    annihilator: mp.matrix,
    parent_scale: mp.mpf,
    *,
    decimal_digits: int,
    eps_p: mp.mpf,
    multiplier: mp.mpf,
) -> tuple[mp.matrix, int, dict[str, Any]]:
    parent_basis = _canonical_basis(parent_projector, parent_dimension, eps_p)
    restricted = _round_matrix(annihilator * parent_basis)
    decomposition = _spectral_rank(
        restricted,
        decimal_digits=decimal_digits,
        eps_p=eps_p,
        multiplier=multiplier,
        inherited_scale=parent_scale,
    )
    intersection_basis = parent_basis * decomposition["kernel_basis"]
    projector = _symmetrize(intersection_basis * intersection_basis.T)
    dimension = int(decomposition["kernel_dimension"])
    _projector_gate(projector, dimension, eps_p)
    return projector, dimension, decomposition


def _augmented_intersection(
    left_projector: mp.matrix,
    left_dimension: int,
    right_projector: mp.matrix,
    right_dimension: int,
    *,
    decimal_digits: int,
    eps_p: mp.mpf,
    multiplier: mp.mpf,
) -> tuple[mp.matrix, int]:
    left_basis = _canonical_basis(left_projector, left_dimension, eps_p)
    right_basis = _canonical_basis(right_projector, right_dimension, eps_p)
    augmented = _hstack([left_basis, -right_basis])
    decomposition = _spectral_rank(
        augmented,
        decimal_digits=decimal_digits,
        eps_p=eps_p,
        multiplier=multiplier,
    )
    dimension = int(decomposition["kernel_dimension"])
    if dimension == 0:
        return _zeros(left_projector.rows, left_projector.rows), 0
    coefficients = decomposition["kernel_basis"]
    mapped_left = left_basis * mp.matrix(
        [[coefficients[row, column] for column in range(dimension)] for row in range(left_dimension)]
    )
    mapped_right = right_basis * mp.matrix(
        [
            [coefficients[left_dimension + row, column] for column in range(dimension)]
            for row in range(right_dimension)
        ]
    )
    projector_left, rank_left, _ = _range_projector(
        mapped_left,
        decimal_digits=decimal_digits,
        eps_p=eps_p,
        multiplier=multiplier,
        inherited_scale=mp.mpf(1),
    )
    projector_right, rank_right, _ = _range_projector(
        mapped_right,
        decimal_digits=decimal_digits,
        eps_p=eps_p,
        multiplier=multiplier,
        inherited_scale=mp.mpf(1),
    )
    if rank_left != dimension or rank_right != dimension:
        raise RuntimeError("augmented intersection lost mapped dimension")
    tolerance = 4096 * max(1, left_projector.rows) * eps_p
    if _equality_residual(projector_left, projector_right) > tolerance:
        raise RuntimeError("symmetric augmented intersection projectors disagree")
    projector = _symmetrize((projector_left + projector_right) / 2)
    _projector_gate(projector, dimension, eps_p)
    return projector, dimension


def _projector_complement(
    parent: mp.matrix,
    child: mp.matrix,
    expected_dimension: int,
    eps_p: mp.mpf,
) -> mp.matrix:
    tolerance = 4096 * max(1, parent.rows) * eps_p
    if _frob((parent * child) - child) > tolerance:
        raise RuntimeError("projector complement child is not contained in parent")
    result = _symmetrize(parent - child)
    _projector_gate(result, expected_dimension, eps_p)
    return result


def _represented_sum(
    left: mp.matrix,
    left_dimension: int,
    right: mp.matrix,
    right_dimension: int,
    overlap_dimension: int,
    *,
    decimal_digits: int,
    eps_p: mp.mpf,
    multiplier: mp.mpf,
) -> tuple[mp.matrix, int]:
    vectors = _hstack(
        [_canonical_basis(left, left_dimension, eps_p), _canonical_basis(right, right_dimension, eps_p)]
    )
    projector, dimension, _ = _range_projector(
        vectors,
        decimal_digits=decimal_digits,
        eps_p=eps_p,
        multiplier=multiplier,
        inherited_scale=mp.mpf(1),
    )
    expected = left_dimension + right_dimension - overlap_dimension
    if dimension != expected:
        raise RuntimeError("represented-sum dimension mismatch")
    return projector, dimension


def _subspace_record(projector: mp.matrix, dimension: int, eps_p: mp.mpf) -> dict[str, Any]:
    basis = _canonical_basis(projector, dimension, eps_p)
    gates = _projector_gate(projector, dimension, eps_p)
    return {
        "dimension": dimension,
        "projector_sha256": matrix_digest(projector),
        "basis_sha256": matrix_digest(basis),
        "gates": {name: mpf_token(value) for name, value in gates.items()},
    }


def _element_inputs(
    topology: Mapping[str, Any], element: Mapping[str, Any]
) -> tuple[list[list[str]], list[list[str]], list[str]]:
    node_map = {node["id"]: node for node in topology["nodes"]}
    coordinates = [node_map[node_id]["x"] for node_id in element["nodes"]]
    if "director_seed" in element:
        directors = [list(element["director_seed"]) for _ in range(4)]
    else:
        directors = [list(value) for value in element["director_seeds"]]
    if type(element["thickness"]) is str:
        thickness = [element["thickness"]] * 4
    else:
        thickness = list(element["thickness"])
    return coordinates, directors, thickness


def _topology_length(coordinates: mp.matrix, retained_nodes: Sequence[int]) -> mp.mpf:
    if not retained_nodes:
        raise ProofInputError("topology has no node incident to a retained element")
    length = mp.mpf(0)
    for left in retained_nodes:
        for right in retained_nodes:
            difference = [coordinates[left, axis] - coordinates[right, axis] for axis in range(3)]
            length = max(length, _norm(difference))
    if not length > 0:
        raise ProofInputError("retained topology has zero extent")
    return length


def _mixed_unit_scale(node_count: int, length: mp.mpf) -> mp.matrix:
    result = _identity(6 * node_count)
    for node in range(node_count):
        for axis in range(3):
            result[6 * node + axis, 6 * node + axis] = length
    return result


def _retained_components(
    node_ids: Sequence[str], retained_elements: Sequence[Mapping[str, Any]]
) -> tuple[list[list[int]], list[int], list[tuple[int, int]]]:
    index = {node_id: position for position, node_id in enumerate(node_ids)}
    adjacency: dict[int, set[int]] = {position: set() for position in range(len(node_ids))}
    incident: set[int] = set()
    edges: set[tuple[int, int]] = set()
    for element in retained_elements:
        connectivity = [index[node_id] for node_id in element["nodes"]]
        incident.update(connectivity)
        for local in range(4):
            first, second = connectivity[local], connectivity[(local + 1) % 4]
            edge = (min(first, second), max(first, second))
            edges.add(edge)
            adjacency[first].add(second)
            adjacency[second].add(first)
    components: list[list[int]] = []
    remaining = set(incident)
    while remaining:
        seed = min(remaining)
        queue = [seed]
        component: list[int] = []
        remaining.remove(seed)
        while queue:
            current = queue.pop(0)
            component.append(current)
            for neighbor in sorted(adjacency[current]):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    queue.append(neighbor)
        components.append(sorted(component))
    orphans = sorted(set(range(len(node_ids))) - incident)
    return components, orphans, sorted(edges)


def _rigid_candidates(
    coordinates: mp.matrix,
    components: Sequence[Sequence[int]],
    length: mp.mpf,
) -> tuple[mp.matrix, list[str]]:
    node_count = coordinates.rows
    candidates: list[mp.matrix] = []
    labels: list[str] = []
    axes = ([mp.mpf(1), mp.mpf(0), mp.mpf(0)], [mp.mpf(0), mp.mpf(1), mp.mpf(0)], [mp.mpf(0), mp.mpf(0), mp.mpf(1)])
    for component_index, component in enumerate(components):
        centroid = [
            mp.fsum(coordinates[node, axis] for node in component) / len(component)
            for axis in range(3)
        ]
        for axis_index, axis in enumerate(axes):
            translation = _zeros(6 * node_count, 1)
            for node in component:
                for direction in range(3):
                    translation[6 * node + direction, 0] = axis[direction] / length
            candidates.append(translation)
            labels.append(f"component_{component_index}.translation_{axis_index}")
        for axis_index, axis in enumerate(axes):
            rotation = _zeros(6 * node_count, 1)
            for node in component:
                position = [coordinates[node, direction] - centroid[direction] for direction in range(3)]
                displacement = _cross(axis, position)
                for direction in range(3):
                    rotation[6 * node + direction, 0] = displacement[direction] / length
                    rotation[6 * node + 3 + direction, 0] = axis[direction]
            candidates.append(rotation)
            labels.append(f"component_{component_index}.rotation_{axis_index}")
    return _hstack(candidates) if candidates else _zeros(6 * node_count, 0), labels


def _bipartite_patterns(
    components: Sequence[Sequence[int]], edges: Sequence[tuple[int, int]], node_count: int
) -> tuple[bool, list[mp.matrix]]:
    adjacency: dict[int, set[int]] = {node: set() for node in range(node_count)}
    for first, second in edges:
        adjacency[first].add(second)
        adjacency[second].add(first)
    patterns: list[mp.matrix] = []
    for component in components:
        colors: dict[int, int] = {}
        seed = min(component)
        colors[seed] = 1
        queue = [seed]
        while queue:
            current = queue.pop(0)
            for neighbor in sorted(adjacency[current]):
                expected = -colors[current]
                if neighbor in colors and colors[neighbor] != expected:
                    return False, []
                if neighbor not in colors:
                    colors[neighbor] = expected
                    queue.append(neighbor)
        pattern = _zeros(node_count, 1)
        for node, color in colors.items():
            pattern[node, 0] = color
        patterns.append(pattern)
    return True, patterns


def assemble_topology(topology: Mapping[str, Any]) -> dict[str, Any]:
    node_ids = [node["id"] for node in topology["nodes"]]
    node_index = {node_id: index for index, node_id in enumerate(node_ids)}
    coordinates = _rows_to_matrix(
        [[_mp(value, f"{topology['id']}.{node['id']}.x") for value in node["x"]] for node in topology["nodes"]]
    )
    retained = [element for element in topology["elements"] if element.get("state", "active") != "deleted"]
    deleted = [element["id"] for element in topology["elements"] if element.get("state", "active") == "deleted"]
    components, orphans, edges = _retained_components(node_ids, retained)
    retained_nodes = sorted({node_index[node] for element in retained for node in element["nodes"]})
    length = _topology_length(coordinates, retained_nodes)
    scale = _mixed_unit_scale(len(node_ids), length)
    c_d_rows: list[mp.matrix] = []
    f_d_rows: list[mp.matrix] = []
    b_blocks: list[tuple[mp.mpf, mp.matrix]] = []
    h_blocks: list[tuple[mp.mpf, mp.matrix]] = []
    fingerprints: dict[str, str] = {}
    element_contributions: dict[str, str] = {}
    gauss = 1 / mp.sqrt(3)
    surface_points = ((-gauss, -gauss), (gauss, -gauss), (gauss, gauss), (-gauss, gauss))
    for element in retained:
        coordinates_input, directors_input, thickness_input = _element_inputs(topology, element)
        reference = build_reference(
            coordinates_input,
            directors_input,
            thickness_input,
            element_id=element["id"],
            connectivity=element["nodes"],
        )
        fingerprints[element["id"]] = reference.fingerprint
        connectivity = [node_index[node_id] for node_id in element["nodes"]]
        local_c_rows: list[mp.matrix] = []
        for r_value, s_value in surface_points:
            drill, spin = drill_trace_and_spin(reference, r_value, s_value)
            bases = _geometry_bases(reference, r_value, s_value, 0)
            measure = _norm(_cross(_row(bases, 0), _row(bases, 1)))
            if not measure > 0:
                raise ProofInputError("surface measure must be positive")
            factor = mp.sqrt(measure)
            drill_hat = _scatter_rows(drill, connectivity, len(node_ids)) * scale
            spin_hat = _scatter_rows(spin, connectivity, len(node_ids)) * scale
            c_d_rows.append(factor * drill_hat)
            f_d_rows.append(factor * spin_hat)
            local_c_rows.append(factor * drill_hat)
        element_contributions[element["id"]] = matrix_digest(_vstack(local_c_rows))
        alpha = _mp(element.get("alpha", "1"), f"{topology['id']}.{element['id']}.alpha")
        beta = _mp(element.get("beta", "1"), f"{topology['id']}.{element['id']}.beta")
        density = _mp(element.get("density", "1"), f"{topology['id']}.{element['id']}.density")
        if min(alpha, beta, density) <= 0:
            raise ProofInputError("retained activity and density must be positive")
        for r_value, s_value in surface_points:
            for zeta in (-gauss, gauss):
                local_b, volume_weight = local_strain(reference, r_value, s_value, zeta)
                local_h = displacement_operator(reference, r_value, s_value, zeta, include_drill=True)
                b_hat = _scatter_rows(local_b, connectivity, len(node_ids)) * scale
                h_hat = (_scatter_rows(local_h, connectivity, len(node_ids)) * scale) / length
                b_blocks.append((alpha * volume_weight, b_hat))
                h_blocks.append((density * beta * volume_weight, h_hat))
    if not c_d_rows:
        raise ProofInputError("no retained shell contributes to C_raw")
    c_sample = _vstack(c_d_rows)
    f_sample = _vstack(f_d_rows)
    c_raw = _symmetrize(c_sample.T * (c_sample - f_sample))
    # C_raw is not analytically symmetric in general.  Restore the literal
    # normal equation after using a distinct name for the later Gram matrices.
    c_raw = c_sample.T * (c_sample - f_sample)
    weight_b = mp.fsum(weight for weight, _ in b_blocks)
    weight_h = mp.fsum(weight for weight, _ in h_blocks)
    if not weight_b > 0 or not weight_h > 0:
        raise ProofInputError("weighted B/H normalization must be positive")
    b_weighted = _vstack([mp.sqrt(weight / weight_b) * block for weight, block in b_blocks])
    h_weighted = _vstack([mp.sqrt(weight / weight_h) * block for weight, block in h_blocks])
    rigid, rigid_labels = _rigid_candidates(coordinates, components, length)
    bipartite, alternating = _bipartite_patterns(components, edges, len(node_ids))
    return {
        "id": topology["id"],
        "node_ids": node_ids,
        "node_index": node_index,
        "coordinates": coordinates,
        "retained_elements": retained,
        "deleted_element_ids": deleted,
        "components": components,
        "orphans": orphans,
        "edges": edges,
        "bipartite": bipartite,
        "alternating_patterns": alternating,
        "ell": length,
        "S_q": scale,
        "B_w": b_weighted,
        "H_w": h_weighted,
        "K_w": _symmetrize(b_weighted.T * b_weighted),
        "M_w": _symmetrize(h_weighted.T * h_weighted),
        "C_sample": c_sample,
        "F_sample": f_sample,
        "C_raw": c_raw,
        "fingerprints": fingerprints,
        "element_contributions": element_contributions,
        "rigid_candidates": rigid,
        "rigid_labels": rigid_labels,
        "topology": topology,
    }


def free_partition(
    assembly: Mapping[str, Any], decimal_digits: int, eps_p: mp.mpf, multiplier: mp.mpf
) -> dict[str, Any]:
    b_operator = assembly["B_w"]
    h_operator = assembly["H_w"]
    rigid_candidates = assembly["rigid_candidates"]
    b_parent = _spectral_rank(
        b_operator,
        decimal_digits=decimal_digits,
        eps_p=eps_p,
        multiplier=mp.mpf(1),
    )
    h_parent = _spectral_rank(
        h_operator,
        decimal_digits=decimal_digits,
        eps_p=eps_p,
        multiplier=mp.mpf(1),
    )
    null = _spectral_rank(
        b_operator,
        decimal_digits=decimal_digits,
        eps_p=eps_p,
        multiplier=multiplier,
    )
    p_n = null["projector"]
    dim_n = int(null["kernel_dimension"])
    p_g, dim_g, _ = _operator_intersection(
        p_n,
        dim_n,
        h_operator,
        h_parent["sigma_max"],
        decimal_digits=decimal_digits,
        eps_p=eps_p,
        multiplier=multiplier,
    )
    dim_p = dim_n - dim_g
    p_p = _projector_complement(p_n, p_g, dim_p, eps_p)
    p_r, dim_r, _ = _range_projector(
        rigid_candidates,
        decimal_digits=decimal_digits,
        eps_p=eps_p,
        multiplier=multiplier,
    )
    p_rn, dim_rn = _augmented_intersection(
        p_r,
        dim_r,
        p_n,
        dim_n,
        decimal_digits=decimal_digits,
        eps_p=eps_p,
        multiplier=multiplier,
    )
    p_rg, dim_rg = _augmented_intersection(
        p_rn,
        dim_rn,
        p_g,
        dim_g,
        decimal_digits=decimal_digits,
        eps_p=eps_p,
        multiplier=multiplier,
    )
    q_rn = _canonical_basis(p_rn, dim_rn, eps_p)
    mapped = _round_matrix(p_p * q_rn)
    p_rq, dim_rq, _ = _range_projector(
        mapped,
        decimal_digits=decimal_digits,
        eps_p=eps_p,
        multiplier=multiplier,
        inherited_scale=mp.mpf(1),
    )
    if dim_rq != dim_rn - dim_rg:
        raise RuntimeError("free quotient-image dimension differs from R_N minus R_G")
    dim_z = dim_p - dim_rq
    if dim_z < 0:
        raise RuntimeError("negative quotient-mechanism dimension")
    p_z = _projector_complement(p_p, p_rq, dim_z, eps_p)
    if _frob((p_rq + p_z) - p_p) > 4096 * max(1, p_p.rows) * eps_p:
        raise RuntimeError("RQ plus Z does not reconstruct P")
    projectors = {
        "N": p_n,
        "G": p_g,
        "P": p_p,
        "R": p_r,
        "R_N": p_rn,
        "R_G": p_rg,
        "RQ": p_rq,
        "Z": p_z,
    }
    dimensions = {
        "rank_B": int(null["rank"]),
        "N": dim_n,
        "G": dim_g,
        "P": dim_p,
        "R": dim_r,
        "R_N": dim_rn,
        "R_G": dim_rg,
        "RQ": dim_rq,
        "Z": dim_z,
    }
    return {
        "dimensions": dimensions,
        "projectors": projectors,
        "subspaces": {name: _subspace_record(projector, dimensions[name], eps_p) for name, projector in projectors.items()},
        "B_parent_scale": b_parent["sigma_max"],
        "H_parent_scale": h_parent["sigma_max"],
    }


def constrained_partition(
    assembly: Mapping[str, Any],
    free: Mapping[str, Any],
    constraint_rows: mp.matrix,
    decimal_digits: int,
    eps_p: mp.mpf,
    multiplier: mp.mpf,
) -> dict[str, Any]:
    b_operator = assembly["B_w"]
    h_operator = assembly["H_w"]
    combined_null_operator = _vstack([b_operator, constraint_rows])
    null = _spectral_rank(
        combined_null_operator,
        decimal_digits=decimal_digits,
        eps_p=eps_p,
        multiplier=multiplier,
    )
    p_n = null["projector"]
    dim_n = int(null["kernel_dimension"])
    p_g, dim_g, _ = _operator_intersection(
        p_n,
        dim_n,
        h_operator,
        free["H_parent_scale"],
        decimal_digits=decimal_digits,
        eps_p=eps_p,
        multiplier=multiplier,
    )
    dim_p = dim_n - dim_g
    p_p = _projector_complement(p_n, p_g, dim_p, eps_p)
    p_sum, dim_sum = _represented_sum(
        free["projectors"]["R_N"],
        free["dimensions"]["R_N"],
        free["projectors"]["G"],
        free["dimensions"]["G"],
        free["dimensions"]["R_G"],
        decimal_digits=decimal_digits,
        eps_p=eps_p,
        multiplier=multiplier,
    )
    p_l, dim_l = _augmented_intersection(
        p_n,
        dim_n,
        p_sum,
        dim_sum,
        decimal_digits=decimal_digits,
        eps_p=eps_p,
        multiplier=multiplier,
    )
    p_lg, dim_lg = _augmented_intersection(
        p_l,
        dim_l,
        p_g,
        dim_g,
        decimal_digits=decimal_digits,
        eps_p=eps_p,
        multiplier=multiplier,
    )
    q_l = _canonical_basis(p_l, dim_l, eps_p)
    mapped = _round_matrix(p_p * q_l)
    p_rq, dim_rq, _ = _range_projector(
        mapped,
        decimal_digits=decimal_digits,
        eps_p=eps_p,
        multiplier=multiplier,
        inherited_scale=mp.mpf(1),
    )
    if dim_rq != dim_l - dim_lg:
        raise RuntimeError("constrained quotient-image dimension differs from L_C minus L_G_C")
    dim_z = dim_p - dim_rq
    if dim_z < 0:
        raise RuntimeError("negative constrained quotient-mechanism dimension")
    p_z = _projector_complement(p_p, p_rq, dim_z, eps_p)
    projectors = {
        "N_C": p_n,
        "G_C": p_g,
        "P_C": p_p,
        "L_C": p_l,
        "L_G_C": p_lg,
        "RQ_C": p_rq,
        "Z_C": p_z,
    }
    dimensions = {
        "rank_BC": int(null["rank"]),
        "N_C": dim_n,
        "G_C": dim_g,
        "P_C": dim_p,
        "L_C": dim_l,
        "L_G_C": dim_lg,
        "RQ_C": dim_rq,
        "Z_C": dim_z,
    }
    return {
        "dimensions": dimensions,
        "projectors": projectors,
        "subspaces": {name: _subspace_record(projector, dimensions[name], eps_p) for name, projector in projectors.items()},
    }


def _normalize_constraint_set(
    assembly: Mapping[str, Any], constraint_set: Mapping[str, Any], eps_p: mp.mpf
) -> dict[str, Any]:
    node_count = len(assembly["node_ids"])
    rows: list[tuple[tuple[Any, ...], list[mp.mpf], mp.mpf]] = []
    omitted = 0
    for row_input in constraint_set.get("rows", []):
        physical = [mp.mpf(0) for _ in range(6 * node_count)]
        for node_id, dof, coefficient in row_input["terms"]:
            column = 6 * assembly["node_index"][node_id] + DOF_INDEX[dof]
            physical[column] += _mp(coefficient, f"{constraint_set['id']}.coefficient")
        row_hat = [
            physical[column] * assembly["S_q"][column, column] for column in range(6 * node_count)
        ]
        rhs = _mp(row_input["rhs"], f"{constraint_set['id']}.rhs")
        magnitude = _norm(row_hat)
        if magnitude == 0:
            if rhs != 0:
                return {
                    "id": constraint_set["id"],
                    "kind": constraint_set["kind"],
                    "qualified": bool(constraint_set.get("qualified", True)),
                    "rows": _zeros(0, 6 * node_count),
                    "rhs": _zeros(0, 1),
                    "omitted_zero_rows": omitted,
                    "feasible": False,
                    "zero_row_nonzero_rhs": True,
                }
            omitted += 1
            continue
        normalized = [value / magnitude for value in row_hat]
        normalized_rhs = rhs / magnitude
        largest = max(abs(value) for value in normalized)
        tie_band = 256 * max(1, len(normalized)) * eps_p * largest
        pivot = min(index for index, value in enumerate(normalized) if largest - abs(value) <= tie_band)
        if normalized[pivot] < 0:
            normalized = [-value for value in normalized]
            normalized_rhs = -normalized_rhs
        key = tuple(tuple(mpf_token(value)) for value in normalized) + (tuple(mpf_token(normalized_rhs)),)
        rows.append((key, normalized, normalized_rhs))
    rows.sort(key=lambda item: item[0])
    matrix = _matrix_from_rows([row for _, row, _ in rows], columns=6 * node_count)
    rhs_matrix = _matrix_from_rows([[rhs] for _, _, rhs in rows], columns=1)
    return {
        "id": constraint_set["id"],
        "kind": constraint_set["kind"],
        "qualified": bool(constraint_set.get("qualified", True)),
        "rows": matrix,
        "rhs": rhs_matrix,
        "omitted_zero_rows": omitted,
        "zero_row_nonzero_rhs": False,
    }


def _constraint_feasibility(
    normalized: Mapping[str, Any],
    c_d: mp.matrix,
    decimal_digits: int,
    eps_p: mp.mpf,
) -> dict[str, Any]:
    if normalized.get("zero_row_nonzero_rhs"):
        return {"feasible": False, "ranks": {multiplier: [0, 1] for multiplier in MULTIPLIERS}}
    rows = _vstack([c_d, normalized["rows"]])
    rhs = _vstack([_zeros(c_d.rows, 1), normalized["rhs"]])
    augmented = _hstack([rows, rhs])
    ranks: dict[str, list[int]] = {}
    feasible = True
    for multiplier_string in MULTIPLIERS:
        multiplier = mp.mpf(multiplier_string)
        rank_rows = _spectral_rank(
            rows,
            decimal_digits=decimal_digits,
            eps_p=eps_p,
            multiplier=multiplier,
        )["rank"]
        rank_augmented = _spectral_rank(
            augmented,
            decimal_digits=decimal_digits,
            eps_p=eps_p,
            multiplier=multiplier,
        )["rank"]
        ranks[multiplier_string] = [int(rank_rows), int(rank_augmented)]
        feasible = feasible and rank_rows == rank_augmented
    return {"feasible": feasible, "ranks": ranks}


def _constraint_basis(
    assembly: Mapping[str, Any], decimal_digits: int, eps_p: mp.mpf, multiplier: mp.mpf
) -> tuple[mp.matrix, int, mp.matrix, dict[str, Any]]:
    projector, dimension, decomposition = _range_projector(
        assembly["C_raw"].T,
        decimal_digits=decimal_digits,
        eps_p=eps_p,
        multiplier=multiplier,
    )
    basis = _canonical_basis(projector, dimension, eps_p)
    c_d = basis.T
    tolerance = 4096 * max(1, assembly["C_raw"].rows) * eps_p
    rowspace_residual = _frob(assembly["C_raw"] * (_identity(projector.rows) - projector))
    raw_scale = decomposition["sigma_max"]
    normalized = mp.mpf(0) if rowspace_residual == 0 and raw_scale == 0 else rowspace_residual / raw_scale
    if raw_scale == 0 and rowspace_residual != 0:
        normalized = mp.inf
    if normalized > tolerance:
        raise RuntimeError("C_D projector does not reconstruct C_raw rowspace")
    return c_d, dimension, projector, {
        "rowspace_residual": mpf_token(normalized),
        "projector": _subspace_record(projector, dimension, eps_p),
    }


def _operator_zero_residual(operator: mp.matrix, vectors: mp.matrix, parent_scale: mp.mpf) -> mp.mpf:
    numerator = _frob(operator * vectors)
    denominator = parent_scale * _frob(vectors)
    if denominator == 0:
        return mp.mpf(0) if numerator == 0 else mp.inf
    return numerator / denominator


def _psd_record(matrix: mp.matrix, decimal_digits: int, eps_p: mp.mpf) -> dict[str, Any]:
    if matrix.rows != matrix.cols:
        raise ProofInputError("PSD gate requires a square matrix")
    dimension = matrix.rows
    symmetry = _frob(matrix - matrix.T)
    tuples = [[matrix[row, column]._mpf_ for column in range(dimension)] for row in range(dimension)]
    eps_tuple = mp.mpf(eps_p)._mpf_
    with mp.workdps(2 * decimal_digits + 32):
        target = mp.matrix(
            [[mp.mpf(tuples[row][column]) for column in range(dimension)] for row in range(dimension)]
        )
        eigenvalues, _ = mp.eigsy(_symmetrize(target)) if dimension else (_zeros(0, 1), _zeros(0, 0))
        values = [eigenvalues[index] for index in range(dimension)]
        scale = max([mp.mpf(0)] + [abs(value) for value in values])
        tolerance = 4096 * max(1, dimension) * mp.mpf(eps_tuple)
        if symmetry > tolerance * scale:
            raise RuntimeError("reduced operator failed symmetry")
        if values and min(values) < -tolerance * scale:
            raise RuntimeError(
                "reduced operator failed PSD: "
                f"minimum={mp.nstr(min(values), 20)}, "
                f"limit={mp.nstr(-tolerance * scale, 20)}"
            )
    return {
        "dimension": dimension,
        "symmetry": mpf_token(symmetry),
        "minimum_eigenvalue": mpf_token(min(values) if values else mp.mpf(0)),
        "maximum_abs_eigenvalue": mpf_token(scale),
        "sha256": matrix_digest(matrix),
    }


def _reduced_operator_record(
    assembly: Mapping[str, Any], combined_rows: mp.matrix, decimal_digits: int, eps_p: mp.mpf, multiplier: mp.mpf
) -> dict[str, Any]:
    decomposition = _spectral_rank(
        combined_rows,
        decimal_digits=decimal_digits,
        eps_p=eps_p,
        multiplier=multiplier,
    )
    t_basis = _canonical_basis(decomposition["projector"], int(decomposition["kernel_dimension"]), eps_p)
    k_reduced = _symmetrize(t_basis.T * assembly["K_w"] * t_basis)
    m_reduced = _symmetrize(t_basis.T * assembly["M_w"] * t_basis)
    k_record = _psd_record(k_reduced, decimal_digits, eps_p)
    m_record = _psd_record(m_reduced, decimal_digits, eps_p)
    if t_basis.cols:
        y_value = _zeros(t_basis.cols, 1)
        z_value = _zeros(t_basis.cols, 1)
        y_value[0, 0] = 1
        z_value[t_basis.cols - 1, 0] = 1
        left = (y_value.T * k_reduced * z_value)[0, 0]
        right = ((t_basis * y_value).T * assembly["K_w"] * (t_basis * z_value))[0, 0]
        congruence = abs(left - right)
    else:
        congruence = mp.mpf(0)
    tolerance = 4096 * max(1, combined_rows.cols) * eps_p
    congruence_scale = _frob(assembly["K_w"])
    if congruence_scale == 0 and congruence != 0:
        raise RuntimeError("exact-zero full stiffness produced nonzero reduced virtual work")
    if congruence_scale != 0 and congruence / congruence_scale > tolerance:
        raise RuntimeError("reduced/full virtual work congruence failed")
    return {
        "constraint_rank": int(decomposition["rank"]),
        "reduced_dimension": t_basis.cols,
        "T_sha256": matrix_digest(t_basis),
        "K": k_record,
        "M": m_record,
        "virtual_work_congruence": mpf_token(congruence),
    }


def _probe_vector(assembly: Mapping[str, Any], kind: str) -> mp.matrix | None:
    node_count = len(assembly["node_ids"])
    vector = _zeros(6 * node_count, 1)
    coordinates = assembly["coordinates"]
    length = assembly["ell"]
    if kind == "extension_x":
        for node in range(node_count):
            vector[6 * node, 0] = coordinates[node, 0] / length
    elif kind == "in_plane_shear_xy":
        for node in range(node_count):
            vector[6 * node, 0] = coordinates[node, 1] / (2 * length)
            vector[6 * node + 1, 0] = coordinates[node, 0] / (2 * length)
    elif kind == "bending_x":
        for node in range(node_count):
            vector[6 * node + 4, 0] = coordinates[node, 0]
    elif kind == "transverse_shear_xz":
        for node in range(node_count):
            vector[6 * node + 2, 0] = coordinates[node, 0] / length
    elif kind == "constant_drill":
        # Defined only for a flat component with a common global +z director.
        for node in {node for component in assembly["components"] for node in component}:
            vector[6 * node + 5, 0] = 1
    elif kind == "bipartite_alternating_drill":
        if not assembly["bipartite"]:
            return None
        for pattern in assembly["alternating_patterns"]:
            for node in range(node_count):
                vector[6 * node + 5, 0] += pattern[node, 0]
    else:
        raise ProofInputError(f"unknown probe kind: {kind}")
    return vector


def _probe_record(
    assembly: Mapping[str, Any],
    c_d: mp.matrix,
    decimal_digits: int,
    eps_p: mp.mpf,
    multiplier: mp.mpf,
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    tolerance = 4096 * max(1, c_d.rows, c_d.cols) * eps_p
    rigid = assembly["rigid_candidates"]
    rigid_residual = _operator_zero_residual(c_d, rigid, mp.mpf(1))
    if rigid_residual > tolerance:
        raise RuntimeError("analytic rigid motions are not in the drill-constraint kernel")
    result["rigid"] = {
        "count": rigid.cols,
        "labels": assembly["rigid_labels"],
        "constraint_residual": mpf_token(rigid_residual),
    }
    flat_common_z = True
    for element in assembly["retained_elements"]:
        coordinates_input, directors_input, _ = _element_inputs(assembly["topology"], element)
        if any(vector != ["0", "0", "1"] for vector in directors_input):
            flat_common_z = False
        if any(coordinate[2] != coordinates_input[0][2] for coordinate in coordinates_input):
            flat_common_z = False
    if flat_common_z:
        drill_coordinates = _zeros(c_d.cols, len(assembly["node_ids"]))
        for node in range(len(assembly["node_ids"])):
            drill_coordinates[6 * node + 5, node] = 1
        restriction = c_d * drill_coordinates
        restriction_rank = _spectral_rank(
            restriction,
            decimal_digits=decimal_digits,
            eps_p=eps_p,
            multiplier=multiplier,
            inherited_scale=mp.mpf(1),
        )["rank"]
        result["pure_drill_coordinate_restriction"] = {
            "rank": int(restriction_rank),
            "coordinate_count": len(assembly["node_ids"]),
            "sha256": matrix_digest(restriction),
        }
        if assembly["id"] == "one_square" and restriction_rank != 4:
            raise RuntimeError("one-square C_D does not remove the full four-coordinate pure-drill subspace")
        for identifier in ("constant_drill", "bipartite_alternating_drill"):
            vector = _probe_vector(assembly, identifier)
            if vector is not None:
                b_action = _frob(assembly["B_w"] * vector)
                h_action = _frob(assembly["H_w"] * vector)
                if assembly["id"] == "one_square":
                    if identifier == "constant_drill" and (b_action != 0 or h_action != 0):
                        raise RuntimeError("one-square constant drill is not the exact zero-mass gauge")
                    if identifier == "bipartite_alternating_drill" and (b_action != 0 or not h_action > 0):
                        raise RuntimeError("one-square alternating drill is not the positive-mass zero-stiffness Z mode")
                result[identifier] = {
                    "constraint_action": mpf_token(_frob(c_d * vector)),
                    "mass_action": mpf_token(h_action),
                    "stiffness_action": mpf_token(b_action),
                }
    if assembly["id"] == "one_square":
        for identifier in ("extension_x", "in_plane_shear_xy", "bending_x", "transverse_shear_xz"):
            vector = _probe_vector(assembly, identifier)
            if vector is not None:
                normalized_action = _operator_zero_residual(c_d, vector, mp.mpf(1))
                if normalized_action > tolerance:
                    raise RuntimeError(f"square patch violates the drill kinematic constraint: {identifier}")
                result[identifier] = {
                    "constraint_action": mpf_token(_frob(c_d * vector)),
                    "normalized_constraint_residual": mpf_token(normalized_action),
                    "B_action": mpf_token(_frob(assembly["B_w"] * vector)),
                }
    return result


def _sample_point(record: Mapping[str, Any]) -> tuple[mp.mpf, mp.mpf]:
    kind = record["kind"]
    if kind == "center":
        return mp.mpf(0), mp.mpf(0)
    if kind == "gauss":
        return mp.mpf(record["r_sign"]) / mp.sqrt(3), mp.mpf(record["s_sign"]) / mp.sqrt(3)
    if kind == "decimal":
        return _mp(record["r"], "sample.r"), _mp(record["s"], "sample.s")
    raise ProofInputError(f"unknown sample point kind: {kind}")


def _dof_permutation(order: Sequence[int]) -> mp.matrix:
    result = _zeros(24, 24)
    for new_node, old_node in enumerate(order):
        for dof in range(6):
            result[6 * new_node + dof, 6 * old_node + dof] = 1
    return result


def _spatial_dof_transform(rotation: mp.matrix, node_count: int) -> mp.matrix:
    result = _zeros(6 * node_count, 6 * node_count)
    for node in range(node_count):
        _set_block(result, 6 * node, 6 * node, rotation)
        _set_block(result, 6 * node + 3, 6 * node + 3, rotation)
    return result


def _transform_vectors(rows: Sequence[Sequence[str]], rotation: mp.matrix) -> list[list[str]]:
    # Transform at arbitrary precision, then preserve exact mpf tuples only in
    # memory.  The registered rotation is signed-permutation valued, so the
    # result remains in the base-decimal grammar.
    transformed: list[list[str]] = []
    for vector in rows:
        parsed = mp.matrix([_mp(value, "frame.vector") for value in vector])
        output = rotation * parsed
        transformed.append([str(int(output[index])) if output[index] == int(output[index]) else mp.nstr(output[index], mp.mp.dps) for index in range(3)])
    return transformed


def analyze_local_cases(cases: Mapping[str, Any], decimal_digits: int, eps_p: mp.mpf) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    tolerance = 4096 * 24 * eps_p
    proper_rotation = _rows_to_matrix(
        [[_mp(value, "proper_rotation") for value in row] for row in cases["derived_variants"]["proper_rotation"]]
    )
    if _equality_residual(proper_rotation.T * proper_rotation, _identity(3)) != 0 or mp.det(proper_rotation) != 1:
        raise ProofInputError("registered frame transform is not exactly proper orthogonal")
    dof_rotation = _spatial_dof_transform(proper_rotation, 4)
    for case in cases["local_cases"]:
        reference = build_reference(
            case["coordinates"],
            case["director_seeds"],
            case["thickness"],
            element_id=case["id"],
            connectivity=("0", "1", "2", "3"),
        )
        point_records: list[dict[str, Any]] = []
        maximum_numbering = mp.mpf(0)
        maximum_frame = mp.mpf(0)
        maximum_origin = mp.mpf(0)
        cyclic_order = (1, 2, 3, 0)
        reversal_order = (0, 3, 2, 1)
        cyclic = build_reference(
            [case["coordinates"][index] for index in cyclic_order],
            [case["director_seeds"][index] for index in cyclic_order],
            [case["thickness"][index] for index in cyclic_order],
            element_id=f"{case['id']}.cyclic",
            connectivity=("1", "2", "3", "0"),
        )
        reversal_seeds = [
            [str(-mp.mpf(value)) for value in case["director_seeds"][index]]
            for index in reversal_order
        ]
        reversal = build_reference(
            [case["coordinates"][index] for index in reversal_order],
            reversal_seeds,
            [case["thickness"][index] for index in reversal_order],
            element_id=f"{case['id']}.reversal",
            connectivity=("0", "3", "2", "1"),
        )
        p_cyclic = _dof_permutation(cyclic_order)
        p_reversal = _dof_permutation(reversal_order)
        t_cyclic = mp.matrix([[0, 1, 0], [1, 0, 0], [0, 0, -1]])
        t_reversal = mp.matrix([[0, 1, 0], [1, 0, 0], [0, 0, 1]])
        rotated_coordinates = _transform_vectors(case["coordinates"], proper_rotation)
        rotated_directors = _transform_vectors(case["director_seeds"], proper_rotation)
        rotated = build_reference(
            rotated_coordinates,
            rotated_directors,
            case["thickness"],
            element_id=f"{case['id']}.frame",
            connectivity=("0", "1", "2", "3"),
        )
        shift = cases["derived_variants"]["origin_shift"]
        shifted_coordinates = [
            [str(mp.mpf(vector[axis]) + mp.mpf(shift[axis])) for axis in range(3)]
            for vector in case["coordinates"]
        ]
        shifted = build_reference(
            shifted_coordinates,
            case["director_seeds"],
            case["thickness"],
            element_id=f"{case['id']}.origin",
            connectivity=("0", "1", "2", "3"),
        )
        for sample in cases["sample_points"]:
            r_value, s_value = _sample_point(sample)
            eq21 = eq21_drill(reference, r_value, s_value)
            eq25 = eq25_membrane(reference, r_value, s_value)
            cyclic_eq21 = _equality_residual(eq21_drill(cyclic, r_value, s_value) * p_cyclic, t_cyclic * eq21_drill(reference, -s_value, r_value))
            cyclic_eq25 = _equality_residual(eq25_membrane(cyclic, r_value, s_value) * p_cyclic, t_cyclic * eq25_membrane(reference, -s_value, r_value))
            reversal_eq21 = _equality_residual(eq21_drill(reversal, r_value, s_value) * p_reversal, t_reversal * eq21_drill(reference, s_value, r_value))
            reversal_eq25 = _equality_residual(eq25_membrane(reversal, r_value, s_value) * p_reversal, t_reversal * eq25_membrane(reference, s_value, r_value))
            frame_eq21 = _equality_residual(eq21_drill(rotated, r_value, s_value) * dof_rotation, eq21)
            frame_eq25 = _equality_residual(eq25_membrane(rotated, r_value, s_value) * dof_rotation, eq25)
            origin_eq21 = _equality_residual(eq21_drill(shifted, r_value, s_value), eq21)
            origin_eq25 = _equality_residual(eq25_membrane(shifted, r_value, s_value), eq25)
            maximum_numbering = max(maximum_numbering, cyclic_eq21, cyclic_eq25, reversal_eq21, reversal_eq25)
            maximum_frame = max(maximum_frame, frame_eq21, frame_eq25)
            maximum_origin = max(maximum_origin, origin_eq21, origin_eq25)
            point_records.append(
                {
                    "point": dict(sample),
                    "eq21_sha256": matrix_digest(eq21),
                    "eq25_sha256": matrix_digest(eq25),
                }
            )
        if max(maximum_numbering, maximum_frame, maximum_origin) > tolerance:
            raise RuntimeError(f"local covariance failed: {case['id']}")
        records.append(
            {
                "id": case["id"],
                "director_fingerprint": reference.fingerprint,
                "points": point_records,
                "maximum_numbering_residual": mpf_token(maximum_numbering),
                "maximum_frame_residual": mpf_token(maximum_frame),
                "maximum_origin_residual": mpf_token(maximum_origin),
            }
        )
    return {"cases": records, "count": len(records)}


def _constraint_set_record(
    assembly: Mapping[str, Any],
    free: Mapping[str, Any],
    c_d: mp.matrix,
    constraint_set: Mapping[str, Any],
    decimal_digits: int,
    eps_p: mp.mpf,
    multiplier: mp.mpf,
) -> dict[str, Any]:
    normalized = _normalize_constraint_set(assembly, constraint_set, eps_p)
    feasibility = _constraint_feasibility(normalized, c_d, decimal_digits, eps_p)
    result: dict[str, Any] = {
        "id": normalized["id"],
        "kind": normalized["kind"],
        "qualified": normalized["qualified"],
        "expected_feasible": bool(constraint_set["expected_feasible"]),
        "row_sha256": matrix_digest(normalized["rows"]),
        "rhs_sha256": matrix_digest(normalized["rhs"]),
        "omitted_zero_rows": normalized["omitted_zero_rows"],
        **feasibility,
    }
    expected_feasible = bool(constraint_set["expected_feasible"])
    if feasibility["feasible"] != expected_feasible:
        raise RuntimeError(
            f"combined affine feasibility differs from the frozen fixture status: {constraint_set['id']}"
        )
    if not feasibility["feasible"]:
        result["status"] = "infeasible_affine_rhs"
        return result
    combined = _vstack([c_d, normalized["rows"]])
    constrained = constrained_partition(
        assembly, free, combined, decimal_digits, eps_p, multiplier
    )
    result["status"] = "analyzed"
    result["dimensions"] = constrained["dimensions"]
    result["subspaces"] = constrained["subspaces"]
    result["reduced"] = _reduced_operator_record(assembly, combined, decimal_digits, eps_p, multiplier)
    if normalized["kind"] == "beam_shell" and normalized["rows"].rows:
        row = normalized["rows"]
        delta = _zeros(row.cols, 1)
        for column in range(row.cols):
            delta[column, 0] = mp.mpf(column + 1) / row.cols
        reaction = row.T
        work_left = (reaction.T * delta)[0, 0]
        work_right = (row * delta)[0, 0]
        result["virtual_work_identity"] = mpf_token(abs(work_left - work_right))
        raw_terms = constraint_set["rows"][0]["terms"]
        shell_sum = mp.fsum(_mp(term[2], "beam_shell.coefficient") for term in raw_terms[:2])
        beam_value = _mp(raw_terms[2][2], "beam_shell.coefficient")
        if shell_sum != 1 or beam_value != -1:
            raise RuntimeError("beam-shell work row violates frozen coefficient sums")
        common_drill = _zeros(row.cols, 1)
        for node in range(len(assembly["node_ids"])):
            common_drill[6 * node + 5, 0] = 1
        if (row * common_drill)[0, 0] != 0:
            raise RuntimeError("beam-shell row does work on common rigid drill trace")
    return result


def analyze_topology(
    topology: Mapping[str, Any], decimal_digits: int, eps_p: mp.mpf
) -> dict[str, Any]:
    assembly = assemble_topology(topology)
    sensitivities: dict[str, Any] = {}
    for multiplier_string in MULTIPLIERS:
        multiplier = mp.mpf(multiplier_string)
        c_d, c_rank, c_projector, c_record = _constraint_basis(
            assembly, decimal_digits, eps_p, multiplier
        )
        free = free_partition(assembly, decimal_digits, eps_p, multiplier)
        drill_constrained = constrained_partition(
            assembly, free, c_d, decimal_digits, eps_p, multiplier
        )
        physical_sets = [
            _constraint_set_record(
                assembly,
                free,
                c_d,
                constraint_set,
                decimal_digits,
                eps_p,
                multiplier,
            )
            for constraint_set in topology.get("constraint_sets", [])
        ]
        sensitivities[multiplier_string] = {
            "C_D_rank": c_rank,
            "C_D_sha256": matrix_digest(c_d),
            "C_D_rowspace": c_record,
            "free_dimensions": free["dimensions"],
            "free_subspaces": free["subspaces"],
            "drill_dimensions": drill_constrained["dimensions"],
            "drill_subspaces": drill_constrained["subspaces"],
            "reduced": _reduced_operator_record(assembly, c_d, decimal_digits, eps_p, multiplier),
            "physical_constraint_sets": physical_sets,
            "probes": _probe_record(
                assembly, c_d, decimal_digits, eps_p, multiplier
            ),
            "C_D_projector_sha256": matrix_digest(c_projector),
        }
    baseline = sensitivities["1"]
    return {
        "id": topology["id"],
        "node_ids": assembly["node_ids"],
        "retained_element_ids": [element["id"] for element in assembly["retained_elements"]],
        "deleted_element_ids": assembly["deleted_element_ids"],
        "components": [[assembly["node_ids"][node] for node in component] for component in assembly["components"]],
        "orphan_node_ids": [assembly["node_ids"][node] for node in assembly["orphans"]],
        "bipartite": assembly["bipartite"],
        "ell": mpf_token(assembly["ell"]),
        "director_fingerprints": assembly["fingerprints"],
        "element_contribution_sha256": assembly["element_contributions"],
        "C_raw_sha256": matrix_digest(assembly["C_raw"]),
        "nominal_drill_scalar_count": len(assembly["node_ids"]),
        "fan_declared_rigid": topology.get("joint") == "declared_rigid",
        "general_coupling_qualified": False if topology["id"] == "noncoplanar_rigid_fan" else None,
        "sensitivities": sensitivities,
        "baseline_C_D_rank": baseline["C_D_rank"],
        "baseline_free_dimensions": baseline["free_dimensions"],
        "baseline_drill_dimensions": baseline["drill_dimensions"],
    }


def _topology_variant(
    topology: Mapping[str, Any], *, scale_power: int = 0, rotation: Sequence[Sequence[str]] | None = None, shift: Sequence[str] | None = None
) -> dict[str, Any]:
    result = json.loads(json.dumps(topology))
    rotation_matrix = (
        _rows_to_matrix([[_mp(value, "variant.rotation") for value in row] for row in rotation])
        if rotation is not None
        else _identity(3)
    )
    scale_value = mp.mpf(2) ** scale_power
    shift_values = [mp.mpf(0), mp.mpf(0), mp.mpf(0)] if shift is None else [_mp(value, "variant.shift") for value in shift]
    for node in result["nodes"]:
        vector = mp.matrix([_mp(value, "variant.coordinate") * scale_value for value in node["x"]])
        transformed = rotation_matrix * vector
        node["x"] = [mp.nstr(transformed[index] + shift_values[index], mp.mp.dps) for index in range(3)]
    for element in result["elements"]:
        if "director_seed" in element:
            vector = rotation_matrix * mp.matrix([_mp(value, "variant.director") for value in element["director_seed"]])
            element["director_seed"] = [mp.nstr(vector[index], mp.mp.dps) for index in range(3)]
        else:
            transformed_seeds: list[list[str]] = []
            for seed in element["director_seeds"]:
                vector = rotation_matrix * mp.matrix([_mp(value, "variant.director") for value in seed])
                transformed_seeds.append([mp.nstr(vector[index], mp.mp.dps) for index in range(3)])
            element["director_seeds"] = transformed_seeds
    return result


def topology_covariance(cases: Mapping[str, Any], decimal_digits: int, eps_p: mp.mpf) -> dict[str, Any]:
    square = next(topology for topology in cases["topology_cases"] if topology["id"] == "one_square")
    base = assemble_topology(square)
    base_c, base_rank, base_projector, _ = _constraint_basis(base, decimal_digits, eps_p, mp.mpf(1))
    scale_results: dict[str, Any] = {}
    tolerance = 4096 * max(1, base_c.cols) * eps_p
    for exponent in cases["derived_variants"]["coordinate_scales_pow2"]:
        variant = assemble_topology(_topology_variant(square, scale_power=int(exponent)))
        _, rank, projector, _ = _constraint_basis(variant, decimal_digits, eps_p, mp.mpf(1))
        residual = _equality_residual(base_projector, projector)
        if rank != base_rank or residual > tolerance:
            raise RuntimeError("coordinate-scale covariance failed")
        scale_results[str(exponent)] = {"rank": rank, "projector_residual": mpf_token(residual)}
    rotation = cases["derived_variants"]["proper_rotation"]
    rotated = assemble_topology(_topology_variant(square, rotation=rotation))
    _, rotation_rank, rotation_projector, _ = _constraint_basis(rotated, decimal_digits, eps_p, mp.mpf(1))
    q_rotation = _spatial_dof_transform(
        _rows_to_matrix([[_mp(value, "rotation") for value in row] for row in rotation]), len(square["nodes"])
    )
    pulled_rotation = q_rotation.T * rotation_projector * q_rotation
    rotation_residual = _equality_residual(base_projector, pulled_rotation)
    shifted = assemble_topology(_topology_variant(square, shift=cases["derived_variants"]["origin_shift"]))
    _, shift_rank, shift_projector, _ = _constraint_basis(shifted, decimal_digits, eps_p, mp.mpf(1))
    shift_residual = _equality_residual(base_projector, shift_projector)
    if rotation_rank != base_rank or shift_rank != base_rank or max(rotation_residual, shift_residual) > tolerance:
        raise RuntimeError("frame/origin covariance failed")
    covariance_metadata = cases["derived_variants"]["warped_numbering_covariance"]
    warped = next(
        topology
        for topology in cases["topology_cases"]
        if topology["id"] == covariance_metadata["topology_id"]
    )
    if len(warped["elements"]) != 1:
        raise ProofInputError("warped covariance topology must materialize exactly one element")
    base_element = warped["elements"][0]
    warped_base = assemble_topology(warped)
    _, warped_rank, warped_projector, _ = _constraint_basis(
        warped_base, decimal_digits, eps_p, mp.mpf(1)
    )
    gauss_signs = {(-1, -1), (1, -1), (1, 1), (-1, 1)}
    variant_projectors: dict[str, tuple[int, mp.matrix]] = {}
    for variant_name in ("cyclic", "anchored_reversal"):
        metadata = covariance_metadata[variant_name]
        order = metadata["local_corner_order"]
        natural_map = _rows_to_matrix(
            [[_mp(value, f"{variant_name}.natural_map") for value in row] for row in metadata["natural_map_old_from_new"]]
        )
        mapped_signs = {
            (
                int((natural_map * mp.matrix([r_sign, s_sign]))[0]),
                int((natural_map * mp.matrix([r_sign, s_sign]))[1]),
            )
            for r_sign, s_sign in gauss_signs
        }
        if mapped_signs != gauss_signs:
            raise ProofInputError(f"{variant_name} natural map does not permute the 2x2 Gauss set")
        if metadata["global_dof_pullback"] != "identity":
            raise ProofInputError("only the registered identity global-DOF pullback is supported")
        sign = _mp(metadata["director_sign"], f"{variant_name}.director_sign")
        variant = json.loads(json.dumps(warped))
        element = variant["elements"][0]
        element["nodes"] = [base_element["nodes"][index] for index in order]
        element["director_seeds"] = [
            [str(sign * mp.mpf(value)) for value in base_element["director_seeds"][index]]
            for index in order
        ]
        element["thickness"] = [base_element["thickness"][index] for index in order]
        assembled_variant = assemble_topology(variant)
        _, variant_rank, variant_projector, _ = _constraint_basis(
            assembled_variant, decimal_digits, eps_p, mp.mpf(1)
        )
        variant_projectors[variant_name] = (variant_rank, variant_projector)
    warped_rotated = assemble_topology(_topology_variant(warped, rotation=rotation))
    _, warped_rotation_rank, warped_rotation_projector, _ = _constraint_basis(
        warped_rotated, decimal_digits, eps_p, mp.mpf(1)
    )
    warped_q_rotation = _spatial_dof_transform(
        _rows_to_matrix([[_mp(value, "rotation") for value in row] for row in rotation]), 4
    )
    warped_residuals = {
        "cyclic": _equality_residual(warped_projector, variant_projectors["cyclic"][1]),
        "anchored_reversal": _equality_residual(
            warped_projector, variant_projectors["anchored_reversal"][1]
        ),
        "frame": _equality_residual(
            warped_projector,
            warped_q_rotation.T * warped_rotation_projector * warped_q_rotation,
        ),
    }
    if (
        {
            warped_rank,
            variant_projectors["cyclic"][0],
            variant_projectors["anchored_reversal"][0],
            warped_rotation_rank,
        }
        != {warped_rank}
        or max(warped_residuals.values()) > tolerance
    ):
        raise RuntimeError("warped C_D numbering/frame covariance failed")
    return {
        "scales": scale_results,
        "frame": {"rank": rotation_rank, "projector_residual": mpf_token(rotation_residual)},
        "origin": {"rank": shift_rank, "projector_residual": mpf_token(shift_residual)},
        "warped_C_D": {
            "rank": warped_rank,
            "metadata_sha256": _sha256_bytes(canonical_json_bytes(covariance_metadata)),
            "residuals": {name: mpf_token(value) for name, value in warped_residuals.items()},
        },
    }


def activity_deletion_evidence(
    cases: Mapping[str, Any], decimal_digits: int, eps_p: mp.mpf
) -> dict[str, Any]:
    softened = next(topology for topology in cases["topology_cases"] if topology["id"] == "softened_invariance")
    neutral = json.loads(json.dumps(softened))
    for element in neutral["elements"]:
        if element.get("state") == "softened":
            element["state"] = "active"
        element["alpha"] = "1"
        element["beta"] = "1"
        element["density"] = "1"
    softened_assembly = assemble_topology(softened)
    neutral_assembly = assemble_topology(neutral)
    _, softened_rank, softened_projector, _ = _constraint_basis(
        softened_assembly, decimal_digits, eps_p, mp.mpf(1)
    )
    _, neutral_rank, neutral_projector, _ = _constraint_basis(
        neutral_assembly, decimal_digits, eps_p, mp.mpf(1)
    )
    activity_residual = _equality_residual(softened_projector, neutral_projector)
    tolerance = 4096 * max(1, softened_projector.rows) * eps_p
    if softened_rank != neutral_rank or activity_residual > tolerance:
        raise RuntimeError("positive activity changed the kinematic drill constraint")
    deletion = next(topology for topology in cases["topology_cases"] if topology["id"] == "deletion_split")
    restored = json.loads(json.dumps(deletion))
    for element in restored["elements"]:
        if element.get("state") == "deleted":
            element["state"] = "active"
    deletion_assembly = assemble_topology(deletion)
    restored_assembly = assemble_topology(restored)
    deletion_difference = _equality_residual(deletion_assembly["C_raw"], restored_assembly["C_raw"])
    if deletion_difference == 0:
        raise RuntimeError("hard deletion did not change C_raw")
    return {
        "positive_activity": {
            "rank": softened_rank,
            "projector_residual": mpf_token(activity_residual),
            "C_raw_equal": matrix_digest(softened_assembly["C_raw"]) == matrix_digest(neutral_assembly["C_raw"]),
        },
        "hard_deletion": {
            "C_raw_difference": mpf_token(deletion_difference),
            "deleted_contribution_absent": "e1" not in deletion_assembly["element_contributions"],
            "restored_contribution_present": "e1" in restored_assembly["element_contributions"],
        },
    }


def _scientific_summary(precision_records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    square_expected = {
        "rank_B": 16,
        "N": 8,
        "G": 1,
        "P": 7,
        "R": 6,
        "R_N": 6,
        "R_G": 0,
        "RQ": 6,
        "Z": 1,
    }
    dimensions_by_case: dict[str, list[tuple[int, str, tuple[tuple[str, int], ...], tuple[tuple[str, int], ...], int]]] = {}
    feasibility_by_fixture: dict[str, list[tuple[bool, tuple[tuple[str, tuple[int, int]], ...]]]] = {}
    physical_dimensions_by_fixture: dict[str, list[tuple[str, tuple[tuple[str, int], ...]]]] = {}
    blockers: list[str] = []
    for precision in precision_records:
        decimal_digits = precision["dps"]
        for topology in precision["topologies"]:
            identifier = topology["id"]
            for multiplier, sensitivity in topology["sensitivities"].items():
                free_tuple = tuple(sorted(sensitivity["free_dimensions"].items()))
                drill_tuple = tuple(sorted(sensitivity["drill_dimensions"].items()))
                dimensions_by_case.setdefault(identifier, []).append(
                    (decimal_digits, multiplier, free_tuple, drill_tuple, sensitivity["C_D_rank"])
                )
                if sensitivity["drill_dimensions"]["Z_C"] != 0:
                    blockers.append(
                        f"{identifier}: positive-mass quotient mechanism remains after C_D at dps={decimal_digits}, multiplier={multiplier}"
                    )
                for physical in sensitivity["physical_constraint_sets"]:
                    feasibility_key = f"{identifier}.{physical['id']}"
                    rank_profile = tuple(
                        sorted(
                            (name, tuple(values))
                            for name, values in physical["ranks"].items()
                        )
                    )
                    feasibility_by_fixture.setdefault(feasibility_key, []).append(
                        (bool(physical["feasible"]), rank_profile)
                    )
                    physical_dimensions_by_fixture.setdefault(feasibility_key, []).append(
                        (
                            physical["status"],
                            tuple(sorted(physical.get("dimensions", {}).items())),
                        )
                    )
                    expected_feasible = physical["expected_feasible"]
                    if physical["feasible"] != expected_feasible:
                        blockers.append(
                            f"{feasibility_key}: combined [C_D;C_phys] affine feasibility differs from fixture expectation"
                        )
                    if (
                        physical.get("qualified")
                        and physical.get("status") == "analyzed"
                        and physical["dimensions"]["Z_C"] != 0
                    ):
                        blockers.append(
                            f"{identifier}.{physical['id']}: qualified physical row leaves Z_C={physical['dimensions']['Z_C']}"
                        )
    stability: dict[str, bool] = {}
    for identifier, entries in dimensions_by_case.items():
        categories = {(entry[2], entry[3], entry[4]) for entry in entries}
        stability[identifier] = len(categories) == 1
        if len(categories) != 1:
            blockers.append(f"{identifier}: categorical dimensions are precision/sensitivity dependent")
    feasibility_stability: dict[str, bool] = {}
    for identifier, entries in feasibility_by_fixture.items():
        feasibility_stability[identifier] = len(set(entries)) == 1
        if len(set(entries)) != 1:
            blockers.append(f"{identifier}: combined affine rank/feasibility drifts across precision or sensitivity")
    physical_dimension_stability: dict[str, bool] = {}
    for identifier, entries in physical_dimensions_by_fixture.items():
        physical_dimension_stability[identifier] = len(set(entries)) == 1
        if len(set(entries)) != 1:
            blockers.append(f"{identifier}: physical constraint status/dimensions drift across precision or sensitivity")
    square_entries = dimensions_by_case.get("one_square", [])
    if not square_entries or dict(square_entries[0][2]) != square_expected:
        blockers.append("one_square: accepted unconstrained tuple was not reproduced")
    fan_records = [
        topology
        for precision in precision_records
        for topology in precision["topologies"]
        if topology["id"] == "noncoplanar_rigid_fan"
    ]
    fan = fan_records[0] if fan_records else None
    if fan is not None and fan["baseline_C_D_rank"] > fan["nominal_drill_scalar_count"] and not fan["fan_declared_rigid"]:
        blockers.append("noncoplanar fan adds rotational constraints without declared rigid-joint derivation")
    return {
        "square_expected": square_expected,
        "categorical_stability": stability,
        "affine_feasibility_stability": feasibility_stability,
        "physical_constraint_stability": physical_dimension_stability,
        "fan_general_coupling_qualified": False,
        "blockers": sorted(set(blockers)),
        "outcome": (
            "CERTIFIED_FOR_LATER_LINEAR_ADAPTER_PLANNING"
            if not blockers
            else "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"
        ),
    }


def case_ids(data: Mapping[str, Any] | None = None) -> list[str]:
    cases = load_cases() if data is None else data
    return [topology["id"] for topology in cases["topology_cases"]]


def _identities() -> dict[str, Any]:
    return {
        "governing_plan_sha256": GOVERNING_PLAN_SHA256,
        "tor_plan_sha256": TOR_PLAN_SHA256,
        "cases_sha256": CASES_SHA256,
        "oracle_sha256": _sha256_file(Path(__file__).resolve()),
        "accepted_source_sha256": SOURCE_SHA256,
        "accepted_nullspace_cases_sha256": NULLSPACE_CASES_SHA256,
        "accepted_nullspace_proof_sha256": NULLSPACE_PROOF_SHA256,
        "primary_pdf_sha256": PRIMARY_PDF_SHA256,
    }


def _exclusions() -> dict[str, bool]:
    return {
        "production_activation": False,
        "gauge_relabel": False,
        "penalty_or_stabilization": False,
        "local_rank18_claim": False,
        "general_shell_beam_coupling": False,
    }


def _evaluate_precision_record(
    cases: Mapping[str, Any], decimal_digits: int, *, quick: bool
) -> dict[str, Any]:
    selected_topologies = (
        [next(topology for topology in cases["topology_cases"] if topology["id"] == "one_square")]
        if quick
        else list(cases["topology_cases"])
    )
    old_dps = mp.mp.dps
    try:
        mp.mp.dps = decimal_digits
        eps_p = +mp.mp.eps
        record = {
            "dps": decimal_digits,
            "prec": int(mp.mp.prec),
            "eps": mpf_token(eps_p),
            "local": analyze_local_cases(cases, decimal_digits, eps_p),
            "topologies": [
                analyze_topology(topology, decimal_digits, eps_p)
                for topology in selected_topologies
            ],
            "covariance": topology_covariance(cases, decimal_digits, eps_p),
        }
        if not quick:
            record["activity_deletion"] = activity_deletion_evidence(cases, decimal_digits, eps_p)
        return record
    finally:
        mp.mp.dps = old_dps


def _unsupported_packet(schema: str, *, precision: int | None = None) -> dict[str, Any]:
    packet: dict[str, Any] = {
        "schema": schema,
        "status": "unsupported_runtime",
        "runtime": {
            "implementation": sys.implementation.name,
            "version": sys.version,
            "byteorder": sys.byteorder,
        },
    }
    if precision is not None:
        packet["precision"] = precision
    return packet


def run_proof(*, quick: bool = False) -> dict[str, Any]:
    cases = load_cases()
    manifest, unsupported = environment_manifest()
    if unsupported is not None:
        return _unsupported_packet(SCHEMA)
    assert manifest is not None
    environment_digest = _sha256_bytes(canonical_json_bytes(manifest))
    precisions = (80,) if quick else PRECISIONS
    precision_records = [
        _evaluate_precision_record(cases, decimal_digits, quick=quick)
        for decimal_digits in precisions
    ]
    summary = _scientific_summary(precision_records)
    return {
        "schema": SCHEMA,
        "status": "complete",
        "formulation_identity": FORMULATION_ID,
        "mode": "quick" if quick else "full",
        "identities": _identities(),
        "environment": manifest,
        "environment_sha256": environment_digest,
        "precision_records": precision_records,
        "scientific_summary": summary,
        "exclusions": _exclusions(),
    }


def run_precision_shard(decimal_digits: int) -> dict[str, Any]:
    if decimal_digits not in PRECISIONS:
        raise ProofInputError(f"unsupported precision shard: {decimal_digits}")
    cases = load_cases()
    manifest, unsupported = environment_manifest()
    if unsupported is not None:
        return _unsupported_packet(PRECISION_SHARD_SCHEMA, precision=decimal_digits)
    assert manifest is not None
    return {
        "schema": PRECISION_SHARD_SCHEMA,
        "status": "complete",
        "formulation_identity": FORMULATION_ID,
        "mode": "precision_shard",
        "precision": decimal_digits,
        "identities": _identities(),
        "environment": manifest,
        "environment_sha256": _sha256_bytes(canonical_json_bytes(manifest)),
        "precision_record": _evaluate_precision_record(
            cases, decimal_digits, quick=False
        ),
        "exclusions": _exclusions(),
    }


def _read_precision_shard(path: Path) -> tuple[dict[str, Any], str]:
    raw = path.read_bytes()
    try:
        packet = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProofInputError(f"invalid UTF-8/JSON shard: {path.name}") from exc
    if type(packet) is not dict:
        raise ProofInputError(f"shard root must be an object: {path.name}")
    if canonical_json_bytes(packet) != raw:
        raise ProofInputError(f"shard bytes are not their canonical reserialization: {path.name}")
    expected_keys = {
        "schema",
        "status",
        "formulation_identity",
        "mode",
        "precision",
        "identities",
        "environment",
        "environment_sha256",
        "precision_record",
        "exclusions",
    }
    if set(packet) != expected_keys:
        raise ProofInputError(f"unexpected shard object keys: {path.name}")
    if packet["schema"] != PRECISION_SHARD_SCHEMA or packet["status"] != "complete":
        raise ProofInputError(f"shard is not a complete registered packet: {path.name}")
    if packet["formulation_identity"] != FORMULATION_ID or packet["mode"] != "precision_shard":
        raise ProofInputError(f"shard formulation/mode mismatch: {path.name}")
    precision = packet["precision"]
    if type(precision) is not int or precision not in PRECISIONS:
        raise ProofInputError(f"invalid shard precision: {path.name}")
    if packet["precision_record"].get("dps") != precision:
        raise ProofInputError(f"shard precision-record mismatch: {path.name}")
    if packet["identities"] != _identities():
        raise ProofInputError(f"shard identity mismatch: {path.name}")
    if packet["exclusions"] != _exclusions():
        raise ProofInputError(f"shard exclusion mismatch: {path.name}")
    manifest_digest = _sha256_bytes(canonical_json_bytes(packet["environment"]))
    if manifest_digest != packet["environment_sha256"]:
        raise ProofInputError(f"shard environment digest mismatch: {path.name}")
    return packet, _sha256_bytes(raw)


def merge_precision_shards(paths: Sequence[Path]) -> dict[str, Any]:
    packets_and_hashes = [_read_precision_shard(path) for path in paths]
    packets = [item[0] for item in packets_and_hashes]
    raw_hashes = [item[1] for item in packets_and_hashes]
    precisions = [packet["precision"] for packet in packets]
    if set(precisions) != set(PRECISIONS) or len(set(precisions)) != len(PRECISIONS):
        raise ProofInputError("shards do not contain exactly one 80/160/320 precision record")
    first = packets[0]
    for packet in packets[1:]:
        for key in (
            "identities",
            "environment",
            "environment_sha256",
            "formulation_identity",
            "exclusions",
        ):
            if packet[key] != first[key]:
                raise ProofInputError(f"cross-shard {key} mismatch")
    current_manifest, unsupported = environment_manifest()
    if unsupported is not None or current_manifest is None:
        raise ProofInputError("merge runtime is outside the registered supported lane")
    current_digest = _sha256_bytes(canonical_json_bytes(current_manifest))
    if current_digest != first["environment_sha256"] or current_manifest != first["environment"]:
        raise ProofInputError("merge environment does not match the precision shards")
    by_precision = {
        packet["precision"]: (packet["precision_record"], raw_hash)
        for packet, raw_hash in zip(packets, raw_hashes, strict=True)
    }
    precision_records = [by_precision[precision][0] for precision in PRECISIONS]
    return {
        "schema": SCHEMA,
        "status": "complete",
        "formulation_identity": FORMULATION_ID,
        "mode": "full",
        "identities": first["identities"],
        "environment": first["environment"],
        "environment_sha256": first["environment_sha256"],
        "precision_records": precision_records,
        "scientific_summary": _scientific_summary(precision_records),
        "exclusions": first["exclusions"],
        "execution_shards": {
            str(precision): by_precision[precision][1] for precision in PRECISIONS
        },
    }


def proof_summary(result: Mapping[str, Any]) -> dict[str, Any]:
    if result.get("status") != "complete":
        return dict(result)
    precision_summary: list[dict[str, Any]] = []
    for precision in result["precision_records"]:
        topology_records: list[dict[str, Any]] = []
        for topology in precision["topologies"]:
            baseline = topology["sensitivities"]["1"]
            topology_records.append(
                {
                    "id": topology["id"],
                    "node_ids": topology["node_ids"],
                    "retained_element_ids": topology["retained_element_ids"],
                    "deleted_element_ids": topology["deleted_element_ids"],
                    "orphan_node_ids": topology["orphan_node_ids"],
                    "C_raw_sha256": topology["C_raw_sha256"],
                    "director_fingerprints": topology["director_fingerprints"],
                    "C_D_rank": topology["baseline_C_D_rank"],
                    "free": topology["baseline_free_dimensions"],
                    "drill": topology["baseline_drill_dimensions"],
                    "sensitivity_dimensions": {
                        multiplier: {
                            "C_D_rank": value["C_D_rank"],
                            "free": value["free_dimensions"],
                            "drill": value["drill_dimensions"],
                        }
                        for multiplier, value in topology["sensitivities"].items()
                    },
                    "physical_constraints": [
                        {
                            "id": physical["id"],
                            "kind": physical["kind"],
                            "qualified": physical["qualified"],
                            "expected_feasible": physical["expected_feasible"],
                            "feasible": physical["feasible"],
                            "ranks": physical["ranks"],
                            "status": physical["status"],
                            "dimensions": physical.get("dimensions"),
                            "row_sha256": physical["row_sha256"],
                            "rhs_sha256": physical["rhs_sha256"],
                        }
                        for physical in baseline["physical_constraint_sets"]
                    ],
                    "probes": baseline["probes"],
                    "fan_declared_rigid": topology["fan_declared_rigid"],
                    "general_coupling_qualified": topology["general_coupling_qualified"],
                }
            )
        precision_summary.append(
            {
                "dps": precision["dps"],
                "prec": precision["prec"],
                "eps": precision["eps"],
                "local": precision["local"],
                "topologies": topology_records,
                "covariance": precision["covariance"],
                "activity_deletion": precision.get("activity_deletion"),
            }
        )
    summary_packet = {
        "schema": result["schema"],
        "status": result["status"],
        "formulation_identity": result["formulation_identity"],
        "mode": result["mode"],
        "identities": result["identities"],
        "environment": result["environment"],
        "environment_sha256": result["environment_sha256"],
        "scientific_summary": result["scientific_summary"],
        "precision_summary": precision_summary,
        "exclusions": result["exclusions"],
        "topologies": [
            {
                "id": topology["id"],
                "C_D_rank": topology["baseline_C_D_rank"],
                "free": topology["baseline_free_dimensions"],
                "drill": topology["baseline_drill_dimensions"],
                "orphans": topology["orphan_node_ids"],
            }
            for topology in result["precision_records"][-1]["topologies"]
        ],
    }
    if "execution_shards" in result:
        summary_packet["execution_shards"] = result["execution_shards"]
    return summary_packet


def _failure_packet(
    exc: BaseException, *, schema: str = SCHEMA, precision: int | None = None
) -> dict[str, Any]:
    manifest: dict[str, Any] | None = None
    digest: str | None = None
    try:
        manifest, _ = environment_manifest()
        if manifest is not None:
            digest = _sha256_bytes(canonical_json_bytes(manifest))
    except BaseException:
        pass
    packet: dict[str, Any] = {
        "schema": schema,
        "status": "scientific_or_contract_failure",
        "outcome": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "failure": {"type": type(exc).__name__, "message": str(exc)},
        "identities": {
            "governing_plan_sha256": GOVERNING_PLAN_SHA256,
            "tor_plan_sha256": TOR_PLAN_SHA256,
            "cases_sha256": CASES_SHA256,
            "oracle_sha256": _sha256_file(Path(__file__).resolve()),
        },
        "environment": manifest,
        "environment_sha256": digest,
    }
    if precision is not None:
        packet["precision"] = precision
    return packet


def _write_receipt(
    target: Path,
    byte_count: int,
    digest: str,
    packet_status: str,
    *,
    precision: int | None = None,
) -> dict[str, Any]:
    receipt: dict[str, Any] = {
        "schema": "s4-drill-constraint-write-receipt-v1",
        "status": "written",
        "packet_status": packet_status,
        "output_path": str(target),
        "output_bytes": byte_count,
        "output_sha256": digest,
    }
    if precision is not None:
        receipt["precision"] = precision
    return receipt


def _main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quick", action="store_true", help="run the square/80-dps focused gate")
    parser.add_argument("--full", action="store_true", help="run the complete registered catalog")
    parser.add_argument("--summary", action="store_true", help="emit only the compact summary")
    parser.add_argument("--case-ids", action="store_true", help="emit registered topology IDs")
    parser.add_argument("--validate-cases", action="store_true", help="validate only the content-addressed cases")
    parser.add_argument("--precision", type=int, choices=PRECISIONS, help="emit one complete precision shard")
    parser.add_argument(
        "--merge-shards",
        nargs=3,
        metavar=("SHARD80", "SHARD160", "SHARD320"),
        help="canonically merge one complete precision-shard set",
    )
    parser.add_argument("--output", help="exclusive-create output path for shard/merge mode")
    arguments = parser.parse_args(argv)
    if arguments.quick and arguments.full:
        parser.error("--quick and --full are mutually exclusive")
    if arguments.case_ids and arguments.validate_cases:
        parser.error("--case-ids and --validate-cases are mutually exclusive")
    if (arguments.case_ids or arguments.validate_cases) and (
        arguments.quick
        or arguments.full
        or arguments.summary
        or arguments.precision is not None
        or arguments.merge_shards is not None
        or arguments.output is not None
    ):
        parser.error("validation modes may not be combined with scientific/output modes")
    if arguments.precision is not None:
        if not arguments.full or arguments.quick or arguments.summary or arguments.merge_shards is not None:
            parser.error("--precision requires only --full and --output")
        if arguments.output is None:
            parser.error("--precision requires --output")
    if arguments.merge_shards is not None:
        if arguments.quick or arguments.full or arguments.summary or arguments.precision is not None:
            parser.error("--merge-shards is a mutually exclusive non-scientific mode")
        if arguments.output is None:
            parser.error("--merge-shards requires --output")
    if arguments.output is not None and arguments.precision is None and arguments.merge_shards is None:
        parser.error("--output is valid only for precision-shard or merge mode")
    try:
        if arguments.case_ids:
            output: Any = {"case_ids": case_ids()}
        elif arguments.validate_cases:
            data = load_cases()
            output = {"schema": data["schema"], "cases_sha256": CASES_SHA256, "status": "valid"}
        elif arguments.precision is not None:
            allowed = _allowed_shard_outputs()
            target = _validate_output_path(
                arguments.output,
                (
                    allowed[f"set1_{arguments.precision:03d}.json"],
                    allowed[f"set2_{arguments.precision:03d}.json"],
                ),
            )
            try:
                packet = run_precision_shard(arguments.precision)
            except BaseException as exc:
                packet = _failure_packet(
                    exc,
                    schema=PRECISION_SHARD_SCHEMA,
                    precision=arguments.precision,
                )
                byte_count, digest = _write_canonical_output(target, packet)
                output = _write_receipt(
                    target,
                    byte_count,
                    digest,
                    packet["status"],
                    precision=arguments.precision,
                )
                sys.stdout.buffer.write(canonical_json_bytes(output))
                return 1
            byte_count, digest = _write_canonical_output(target, packet)
            output = _write_receipt(
                target,
                byte_count,
                digest,
                packet["status"],
                precision=arguments.precision,
            )
            sys.stdout.buffer.write(canonical_json_bytes(output))
            return 2 if packet.get("status") == "unsupported_runtime" else 0
        elif arguments.merge_shards is not None:
            inputs = _validate_shard_inputs(arguments.merge_shards)
            set_prefix = inputs[0].name.split("_", 1)[0]
            expected_target = _stored_output_path() if set_prefix == "set1" else _repeat_merge_path()
            target = _validate_output_path(arguments.output, (expected_target,))
            if _path_key(target) in {_path_key(path) for path in inputs}:
                raise ProofInputError("merge input/output alias is forbidden")
            packet = merge_precision_shards(inputs)
            byte_count, digest = _write_canonical_output(target, packet)
            output = _write_receipt(target, byte_count, digest, packet["status"])
            sys.stdout.buffer.write(canonical_json_bytes(output))
            return 0
        else:
            result = run_proof(quick=arguments.quick and not arguments.full)
            output = proof_summary(result) if arguments.summary else result
    except BaseException as exc:
        output = _failure_packet(exc)
        sys.stdout.buffer.write(canonical_json_bytes(output))
        return 1
    sys.stdout.buffer.write(canonical_json_bytes(output))
    return 2 if output.get("status") == "unsupported_runtime" else 0


if __name__ == "__main__":
    raise SystemExit(_main())
