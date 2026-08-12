"""Deterministic proof oracle for literal MITC4+/D nullspace semantics.

This file is deliberately isolated from the normal :mod:`anysolver` package
initialization path.  It loads only the four content-addressed numerical
modules registered by ``S4_NULLSPACE_SEMANTICS_PROOF_PLAN.md`` and performs
proof/evidence calculations.  It does not choose, apply, or recommend a gauge,
constraint, stabilization, or rank policy.
"""

from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import importlib.machinery
import importlib.metadata
import importlib.util
import io
import json
import math
import os
from pathlib import Path, PurePosixPath
import platform
import re
import stat
import struct
import sys
import types
from typing import Any, Iterable, Mapping, Sequence


SCHEMA = "s4-nullspace-semantics-proof-v1"
CASES_SCHEMA = "s4-nullspace-semantics-cases-v1"
ENVIRONMENT_SCHEMA = "s4-nullspace-environment-v1"
SNAPSHOT_SCHEMA = "s4-nullspace-snapshot-v2"

PLAN_SHA256 = "855d76f0ca40549cbaead8360152f973b3162671295c53b16f58a5341cc382ca"
EDITOR_PLAN_SHA256 = "136cd18281f61d2705fd3c1145c95c63498be8b255c1d0f8118701d3e33ff3a6"
AUDITOR_PLAN_SHA256 = "6ab98ddb6f50139544610c2058d8ffb0c833749f25f126d404c8f18b76811530"

SOURCE_HASHES = {
    "protocol.py": "32bf05e0bd0b282c49c47392caf9400d2c8c136b9b6d1d398b3b54451eacb089",
    "q4_common.py": "de2dcdcd3bc04a90a4db2c074ec15d4e4b097123010f146a0c718506443c3d19",
    "mitc4_plus_d_reference.py": "aaf44046eee607541f2a84ea16cba948cb98130a568bbf8b5b03b243928e9536",
    "mitc4_plus_d_scalar.py": "9e3f1827f813546ff9c183c77e654f268c8a67f976b63ff010749efdeab3118b",
}
SOURCE_ORDER = tuple(SOURCE_HASHES)

EPS64 = 2.0**-52
SVD_FACTOR = 64.0
RESIDUAL_FACTOR = 4096.0
CANONICAL_TIE_FACTOR = 256.0
SENSITIVITY_MULTIPLIERS = (0.25, 1.0, 4.0)

_THREAD_CONTROLS = (
    "OPENBLAS_NUM_THREADS",
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "BLIS_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
)
_NUMERIC_PREFIXES = (
    "OPENBLAS_",
    "MKL_",
    "BLIS_",
    "VECLIB_",
    "ACCELERATE_",
    "OMP_",
    "GOTO_",
    "NUMEXPR_",
)
_RESULT_CHANGING_DENYLIST = {
    "openblas_coretype",
    "openblas_verbose",
    "openblas_default_num_threads",
    "mkl_cbwr",
    "mkl_debug_cpu_type",
    "mkl_enable_instructions",
    "mkl_verbose",
    "mkl_dynamic",
    "blis_arch_type",
    "blis_model_type",
    "goto_num_threads",
    "omp_dynamic",
    "omp_proc_bind",
    "omp_places",
    "omp_schedule",
}


class ProofInputError(ValueError):
    """Raised when a frozen proof input violates the registered boundary."""


def _configure_numeric_environment() -> dict[str, str]:
    """Freeze thread controls and capture all recognized numerical variables.

    This executes before NumPy is imported.  Environment keys are compared
    case-insensitively because the registered runtime is Windows.
    """

    folded: dict[str, tuple[str, str]] = {}
    for key, value in os.environ.items():
        if "\r" in key or "\n" in key or "\r" in value or "\n" in value:
            raise RuntimeError("environment names and values must not contain CR/LF")
        lowered = key.casefold()
        if lowered in folded:
            raise RuntimeError(f"duplicate case-folded environment name: {key!r}")
        folded[lowered] = (key, value)

    for denied in sorted(_RESULT_CHANGING_DENYLIST):
        if denied in folded:
            raise RuntimeError(f"unsupported result-changing environment variable: {folded[denied][0]}")

    for name in _THREAD_CONTROLS:
        existing = folded.get(name.casefold())
        if existing is not None and existing[0] != name:
            raise RuntimeError(f"controlled environment name must use exact uppercase spelling: {existing[0]}")
        if existing is not None and existing[1] != "1":
            raise RuntimeError(f"{existing[0]} must be absent or exactly '1'")
        if existing is None:
            os.environ[name] = "1"

    recognized: dict[str, str] = {}
    seen: set[str] = set()
    for key, value in os.environ.items():
        lowered = key.casefold()
        if any(lowered.startswith(prefix.casefold()) for prefix in _NUMERIC_PREFIXES):
            if lowered in seen:
                raise RuntimeError(f"duplicate case-folded numerical environment name: {key!r}")
            seen.add(lowered)
            recognized[key] = value
    return dict(sorted(recognized.items(), key=lambda item: item[0]))


_NUMERIC_ENVIRONMENT = _configure_numeric_environment()

if "numpy" in sys.modules or any(name.startswith("numpy.") for name in sys.modules):
    raise RuntimeError("NumPy was imported before S4 numerical environment controls were frozen")

import numpy as np  # noqa: E402  (must follow the environment preflight)
import threadpoolctl  # noqa: E402


FloatArray = np.ndarray
_ENVIRONMENT_CACHE: tuple[dict[str, Any] | None, str | None] | None = None
_LOADED_NUMERIC_MODULES: dict[str, types.ModuleType] | None = None


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _canonical_source_bytes(path: Path) -> bytes:
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raise ProofInputError(f"UTF-8 BOM is forbidden: {path}")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ProofInputError(f"source is not strict UTF-8: {path}") from exc
    if "\r" in text.replace("\r\n", ""):
        raise ProofInputError(f"lone CR is forbidden: {path}")
    return text.replace("\r\n", "\n").encode("utf-8")


def _canonical_source_hash(path: Path) -> str:
    return _sha256_bytes(_canonical_source_bytes(path))


def _float_token(value: float) -> str:
    value = float(value)
    if not math.isfinite(value):
        raise ProofInputError("canonical JSON forbids non-finite floats")
    if value == 0.0:
        return "0"
    token = format(value, ".17g").lower()
    if "e" not in token:
        return token
    mantissa, exponent = token.split("e")
    sign = ""
    if exponent.startswith(("+", "-")):
        if exponent[0] == "-":
            sign = "-"
        exponent = exponent[1:]
    exponent = exponent.lstrip("0") or "0"
    return f"{mantissa}e{sign}{exponent}"


def canonical_json_bytes(value: Any) -> bytes:
    """Serialize proof data with frozen key order and binary64 tokens."""

    def encode(item: Any) -> str:
        if item is None:
            return "null"
        if type(item) is bool:
            return "true" if item else "false"
        if type(item) is int:
            return str(item)
        if type(item) is float:
            return _float_token(item)
        if type(item) is str:
            if "\r" in item or "\n" in item:
                raise ProofInputError("canonical JSON strings must not contain CR/LF")
            return json.dumps(item, ensure_ascii=True)
        if isinstance(item, np.generic):
            return encode(item.item())
        if isinstance(item, np.ndarray):
            return encode(item.tolist())
        if type(item) in (list, tuple):
            return "[" + ",".join(encode(child) for child in item) + "]"
        if type(item) is dict:
            if any(type(key) is not str for key in item):
                raise ProofInputError("canonical JSON mapping keys must be actual strings")
            return "{" + ",".join(
                json.dumps(key, ensure_ascii=True) + ":" + encode(item[key])
                for key in sorted(item)
            ) + "}"
        raise ProofInputError(f"unsupported canonical JSON type: {type(item).__name__}")

    return (encode(value) + "\n").encode("utf-8")


def _strict_manifest_value(value: Any) -> Any:
    """Normalize an environment manifest value to the registered domain."""

    if value is None or type(value) in (bool, int):
        return value
    if type(value) is float:
        if not math.isfinite(value):
            raise RuntimeError("environment manifest contains a non-finite float")
        return 0.0 if value == 0.0 else value
    if type(value) is str:
        if "\r" in value or "\n" in value:
            raise RuntimeError("environment manifest strings must not contain CR/LF")
        return value
    if type(value) in (list, tuple):
        return [_strict_manifest_value(item) for item in value]
    if type(value) is dict:
        normalized: dict[str, Any] = {}
        for key in sorted(value):
            if type(key) is not str:
                raise RuntimeError("environment manifest keys must be actual strings")
            normalized[key] = _strict_manifest_value(value[key])
        return normalized
    raise RuntimeError(f"unsupported environment manifest type: {type(value).__name__}")


def _manifest_json_bytes(manifest: dict[str, Any]) -> bytes:
    normalized = _strict_manifest_value(manifest)
    return (json.dumps(normalized, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode("utf-8")


def _is_reparse(path: Path) -> bool:
    attributes = getattr(path.stat(follow_symlinks=False), "st_file_attributes", 0)
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return path.is_symlink() or bool(attributes & reparse_flag)


def _regular_non_reparse(path: Path) -> None:
    if not path.is_file() or _is_reparse(path):
        raise RuntimeError(f"expected a regular non-reparse file: {path}")


def _verified_distribution(literal: str, module_version: str) -> tuple[dict[str, Any], Path]:
    distribution = importlib.metadata.distribution(literal)
    metadata_name = distribution.metadata.get("Name", "")
    if metadata_name.casefold() != literal.casefold():
        raise RuntimeError(f"distribution name mismatch for {literal}: {metadata_name!r}")
    if distribution.version != module_version:
        raise RuntimeError(f"distribution/module version mismatch for {literal}")
    files = distribution.files
    if files is None:
        raise RuntimeError(f"distribution files unavailable for {literal}")
    records = [entry for entry in files if entry.name == "RECORD" and entry.parent.name.endswith(".dist-info")]
    if len(records) != 1:
        raise RuntimeError(f"expected exactly one RECORD for {literal}")

    distribution_base = Path(distribution.locate_file("")).resolve()
    if not distribution_base.is_dir() or _is_reparse(distribution_base):
        raise RuntimeError(f"distribution base is not a regular non-reparse directory: {literal}")
    record_entry = records[0]
    record_path = Path(distribution.locate_file(record_entry)).resolve()
    _regular_non_reparse(record_path)
    raw = record_path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raise RuntimeError(f"RECORD has a UTF-8 BOM: {literal}")
    try:
        decoded = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RuntimeError(f"RECORD is not strict UTF-8: {literal}") from exc

    verified_count = 0
    external_verified_count = 0
    unhashed_pyc_count = 0
    seen: set[str] = set()
    reader = csv.reader(io.StringIO(decoded, newline=""), strict=True)
    for row in reader:
        if len(row) != 3:
            raise RuntimeError(f"RECORD row must have exactly three fields: {literal}")
        name, encoded_hash, encoded_size = row
        if name in seen:
            raise RuntimeError(f"duplicate RECORD path: {name}")
        seen.add(name)
        if not name or "\\" in name or PurePosixPath(name).is_absolute() or re.match(r"^[A-Za-z]:", name):
            raise RuntimeError(f"invalid RECORD path: {name!r}")
        lexical_parts = name.split("/")
        if not lexical_parts or any(part in ("", ".") for part in lexical_parts):
            raise RuntimeError(f"non-canonical RECORD path: {name!r}")
        parts = PurePosixPath(name).parts
        parent_count = parts.count("..")
        external = parent_count > 0
        allowed_external = literal.casefold() == "numpy" and name in {
            "../../Scripts/f2py.exe",
            "../../Scripts/numpy-config.exe",
        }
        if external and not allowed_external:
            raise RuntimeError(f"forbidden external RECORD path: {name!r}")
        if allowed_external:
            target = (Path(sys.executable).resolve().parent / "Scripts" / PurePosixPath(name).name).resolve()
            located = Path(distribution.locate_file(name)).resolve()
            if located != target:
                raise RuntimeError(f"external RECORD path does not resolve to exact Scripts target: {name!r}")
            scripts_root = (Path(sys.executable).resolve().parent / "Scripts").resolve()
            try:
                target.relative_to(scripts_root)
            except ValueError as exc:
                raise RuntimeError(f"external RECORD path escapes exact Scripts root: {name!r}") from exc
        else:
            target = Path(distribution.locate_file(name)).resolve()
            try:
                target.relative_to(distribution_base)
            except ValueError as exc:
                raise RuntimeError(f"RECORD path escapes distribution: {name!r}") from exc

        if encoded_hash == "" and encoded_size == "":
            is_record = name == record_entry.as_posix()
            is_pyc = name.endswith(".pyc") and "__pycache__" in parts
            if not (is_record or is_pyc):
                raise RuntimeError(f"unexpected unhashed RECORD row: {name!r}")
            if is_pyc:
                unhashed_pyc_count += 1
            continue
        if not encoded_hash or not encoded_size or not encoded_size.isdecimal():
            raise RuntimeError(f"incomplete hashed RECORD row: {name!r}")
        algorithm, separator, expected_hash = encoded_hash.partition("=")
        if algorithm != "sha256" or separator != "=" or not expected_hash or "=" in expected_hash:
            raise RuntimeError(f"unsupported RECORD digest: {name!r}")
        _regular_non_reparse(target)
        data = target.read_bytes()
        actual_hash = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).decode("ascii").rstrip("=")
        if actual_hash != expected_hash or len(data) != int(encoded_size):
            raise RuntimeError(f"RECORD verification failed: {name!r}")
        verified_count += 1
        if external:
            external_verified_count += 1

    expected_external = 2 if literal.casefold() == "numpy" else 0
    if external_verified_count != expected_external:
        raise RuntimeError(f"unexpected external RECORD count for {literal}")
    return (
        {
            "name": metadata_name,
            "version": distribution.version,
            "record_name": record_entry.as_posix(),
            "record_sha256": _sha256_bytes(raw),
            "verified_count": verified_count,
            "external_verified_count": external_verified_count,
            "unhashed_pyc_count": unhashed_pyc_count,
        },
        distribution_base,
    )


def _validated_binary_path(path: Path, root: Path) -> Path:
    root_path = Path(root)
    if not root_path.is_dir() or _is_reparse(root_path):
        raise RuntimeError(f"numeric binary root must be a non-reparse directory: {root_path}")
    resolved_root = root_path.resolve()
    candidate = Path(path)
    if _is_reparse(candidate):
        raise RuntimeError(f"numeric binary must not be a symlink/reparse point: {candidate}")
    resolved = candidate.resolve()
    try:
        relative = resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise RuntimeError(f"numeric binary escapes declared root: {candidate}") from exc
    current = root_path
    for part in relative.parts[:-1]:
        current = current / part
        if _is_reparse(current):
            raise RuntimeError(f"numeric binary parent is a reparse point: {current}")
    _regular_non_reparse(resolved)
    return resolved


def _binary_artifact(role: str, name: str, path: Path, root: Path) -> dict[str, Any]:
    resolved = _validated_binary_path(path, root)
    return {
        "role": role,
        "name": name.replace("\\", "/"),
        "size": resolved.stat().st_size,
        "sha256": _sha256_file(resolved),
    }


def _numeric_binaries(numpy_base: Path) -> list[dict[str, str]]:
    executable_input = Path(sys.executable)
    executable = executable_input.resolve()
    python_dir = executable.parent
    numpy_dir = Path(np.__file__).resolve().parent
    try:
        numpy_dir.relative_to(numpy_base)
    except ValueError as exc:
        raise RuntimeError("NumPy package escapes its verified distribution") from exc
    artifacts = [_binary_artifact("python_executable", executable.name, executable_input, python_dir)]
    runtime_found = False
    for candidate in sorted(python_dir.iterdir(), key=lambda p: p.name.casefold()):
        lowered = candidate.name.casefold()
        if candidate.is_file() and (
            re.fullmatch(r"python\d+.*\.dll", lowered)
            or re.fullmatch(r"vcruntime.*\.dll", lowered)
            or re.fullmatch(r"msvcp.*\.dll", lowered)
        ):
            artifacts.append(_binary_artifact("python_runtime", candidate.name, candidate, python_dir))
            if re.fullmatch(fr"python{sys.version_info.major}{sys.version_info.minor}.*\.dll", lowered):
                runtime_found = True
    if not runtime_found:
        raise RuntimeError("matching Python runtime DLL was not found")

    numpy_binary_count = 0
    for candidate in sorted(numpy_dir.rglob("*"), key=lambda p: p.as_posix().casefold()):
        if candidate.is_file() and candidate.suffix.casefold() in (".pyd", ".dll"):
            relative = candidate.relative_to(numpy_dir).as_posix()
            artifacts.append(_binary_artifact("numpy", relative, candidate, numpy_dir))
            if candidate.suffix.casefold() == ".pyd":
                numpy_binary_count += 1
    if numpy_binary_count == 0:
        raise RuntimeError("NumPy distribution contains no extension module")

    libs_dir = numpy_dir.parent / "numpy.libs"
    if not libs_dir.is_dir() or _is_reparse(libs_dir):
        raise RuntimeError("NumPy sibling numpy.libs directory is unavailable")
    libs_count = 0
    for candidate in sorted(libs_dir.rglob("*"), key=lambda p: p.as_posix().casefold()):
        if candidate.is_file() and candidate.suffix.casefold() in (".pyd", ".dll"):
            relative = candidate.relative_to(libs_dir).as_posix()
            artifacts.append(_binary_artifact("numpy.libs", relative, candidate, libs_dir))
            libs_count += 1
    if libs_count == 0:
        raise RuntimeError("numpy.libs contains no numeric binary")
    artifacts.sort(key=lambda item: (item["role"], item["name"]))
    identities = [(item["role"].casefold(), item["name"].casefold()) for item in artifacts]
    if len(identities) != len(set(identities)):
        raise RuntimeError("duplicate numeric binary identity")
    return artifacts


_CONFIG_DENY_KEYS = {"path", "commands", "include directory", "lib directory", "pc file directory"}


def _filtered_numpy_config(value: Any) -> Any:
    if type(value) is dict:
        if any(type(key) is not str for key in value):
            raise RuntimeError("NumPy configuration mapping keys must be actual strings")
        return {
            key: _filtered_numpy_config(value[key])
            for key in sorted(value)
            if key.casefold() not in _CONFIG_DENY_KEYS
        }
    if type(value) in (list, tuple):
        return [_filtered_numpy_config(child) for child in value]
    if type(value) in (str, bool, int, float) or value is None:
        return _strict_manifest_value(value)
    raise RuntimeError(f"unsupported NumPy configuration value: {type(value).__name__}")


def environment_manifest() -> tuple[dict[str, Any] | None, str | None]:
    """Return the exact Windows-runtime manifest and digest, if supported."""

    global _ENVIRONMENT_CACHE
    if _ENVIRONMENT_CACHE is not None:
        return _ENVIRONMENT_CACHE
    supported = (
        platform.python_implementation() == "CPython"
        and platform.system() == "Windows"
        and sys.byteorder == "little"
    )
    if not supported:
        _ENVIRONMENT_CACHE = (None, None)
        return _ENVIRONMENT_CACHE

    numpy_record, numpy_base = _verified_distribution("numpy", np.__version__)
    threadpool_record, _ = _verified_distribution("threadpoolctl", threadpoolctl.__version__)
    # Force BLAS initialization before the runtime binding is inspected.
    np.linalg.svd(np.eye(2, dtype=np.float64), full_matrices=True)
    pools = [item for item in threadpoolctl.threadpool_info() if item.get("user_api") == "blas"]
    if len(pools) != 1:
        raise RuntimeError("exactly one BLAS runtime must be active")
    pool = pools[0]
    expected_pool_keys = {
        "user_api",
        "internal_api",
        "num_threads",
        "version",
        "threading_layer",
        "architecture",
        "prefix",
        "filepath",
    }
    if set(pool) != expected_pool_keys:
        raise RuntimeError(
            f"BLAS runtime source keys differ from the registered domain: {sorted(pool)!r}"
        )
    filepath = Path(str(pool.get("filepath", ""))).resolve()
    prefix = str(pool.get("prefix", ""))
    internal_api = str(pool.get("internal_api", ""))
    if internal_api.casefold() != "openblas" or int(pool.get("num_threads", 0)) != 1:
        raise RuntimeError("the registered runtime requires single-thread OpenBLAS")
    for key in ("version", "threading_layer", "architecture", "prefix"):
        if not isinstance(pool.get(key), str) or not pool[key]:
            raise RuntimeError(f"BLAS runtime field is unavailable: {key}")
    binaries = _numeric_binaries(numpy_base)
    matches = [item for item in binaries if Path(item["name"]).name.casefold() == filepath.name.casefold()]
    if len(matches) != 1:
        raise RuntimeError("BLAS runtime cannot be bound uniquely to a verified binary")
    blas_library = {
        "user_api": "blas",
        "internal_api": internal_api,
        "num_threads": int(pool["num_threads"]),
        "version": str(pool["version"]),
        "threading_layer": str(pool["threading_layer"]),
        "architecture": str(pool["architecture"]),
        "prefix": prefix,
        "binary": {
            "role": matches[0]["role"],
            "name": matches[0]["name"],
            "sha256": matches[0]["sha256"],
        },
    }

    cpu_module = importlib.import_module("numpy._core._multiarray_umath")
    cpu = {}
    for key, attribute in (
        ("features", "__cpu_features__"),
        ("baseline", "__cpu_baseline__"),
        ("dispatch", "__cpu_dispatch__"),
    ):
        if not hasattr(cpu_module, attribute):
            raise RuntimeError(f"NumPy CPU attribute unavailable: {attribute}")
        cpu[key] = _strict_manifest_value(getattr(cpu_module, attribute))

    config = np.__config__.show(mode="dicts")
    build = list(platform.python_build())
    required_strings = {
        "python_implementation": platform.python_implementation(),
        "python_version": platform.python_version(),
        "python_cache_tag": sys.implementation.cache_tag,
        "python_compiler": platform.python_compiler(),
        "os_system": platform.system(),
        "os_release": platform.release(),
        "os_version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
    }
    if any(type(value) is not str or not value for value in required_strings.values()):
        raise RuntimeError("registered environment string fields must be non-empty actual strings")
    if required_strings["os_system"] != "Windows" or sys.byteorder != "little":
        raise RuntimeError("snapshot manifest supports only little-endian Windows")
    if len(build) != 2 or any(type(value) is not str or not value for value in build):
        raise RuntimeError("python_build must be an exact two-string array")
    if str(np.dtype(np.float64)) != "float64" or np.dtype(np.float64).itemsize != 8 or not np.little_endian:
        raise RuntimeError("registered runtime requires little-endian binary64 NumPy")
    if {name: os.environ[name] for name in _THREAD_CONTROLS} != {
        name: "1" for name in _THREAD_CONTROLS
    }:
        raise RuntimeError("thread controls changed after the process-start assignment")
    manifest = {
        "schema": ENVIRONMENT_SCHEMA,
        "python_implementation": required_strings["python_implementation"],
        "python_version": required_strings["python_version"],
        "python_cache_tag": required_strings["python_cache_tag"],
        "python_compiler": required_strings["python_compiler"],
        "python_build": build,
        "numpy_version": np.__version__,
        "numpy_record": numpy_record,
        "os_system": required_strings["os_system"],
        "os_release": required_strings["os_release"],
        "os_version": required_strings["os_version"],
        "machine": required_strings["machine"],
        "processor": required_strings["processor"],
        "byteorder": sys.byteorder,
        "float_info": {
            "radix": sys.float_info.radix,
            "mant_dig": sys.float_info.mant_dig,
            "max_exp": sys.float_info.max_exp,
            "min_exp": sys.float_info.min_exp,
            "rounds": sys.float_info.rounds,
            "epsilon_hex": sys.float_info.epsilon.hex(),
        },
        "numpy_float64": {
            "dtype": str(np.dtype(np.float64)),
            "itemsize": np.dtype(np.float64).itemsize,
            "byteorder": "little" if np.little_endian else "big",
            "eps_hex": float(np.finfo(np.float64).eps).hex(),
        },
        "numpy_config": _filtered_numpy_config(config),
        "numpy_cpu": cpu,
        "numeric_binary_artifacts": binaries,
        "blas_runtime": {"library": blas_library, "distribution": threadpool_record},
        "thread_controls": {name: os.environ[name] for name in _THREAD_CONTROLS},
        "numeric_environment": _NUMERIC_ENVIRONMENT,
    }
    normalized = _strict_manifest_value(manifest)
    digest = _sha256_bytes(_manifest_json_bytes(normalized))
    _ENVIRONMENT_CACHE = (normalized, digest)
    return _ENVIRONMENT_CACHE


def snapshot_digest(array: FloatArray, kind: str, environment_digest: str) -> str:
    if kind not in ("projector", "basis"):
        raise ProofInputError("snapshot kind must be 'projector' or 'basis'")
    if not re.fullmatch(r"[0-9a-f]{64}", environment_digest):
        raise ProofInputError("environment digest must be canonical lowercase SHA-256")
    value = np.asarray(array, dtype=np.float64)
    if value.ndim != 2 or not np.all(np.isfinite(value)):
        raise ProofInputError("snapshot arrays must be finite matrices")
    value = np.array(value, dtype="<f8", order="C", copy=True)
    value[value == 0.0] = 0.0
    header = (
        f"{SNAPSHOT_SCHEMA}|env={environment_digest}|{kind}|"
        f"{value.shape[0]}x{value.shape[1]}|<f8|C|"
    ).encode("ascii")
    return _sha256_bytes(header + value.tobytes(order="C"))


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _numeric_source_dir() -> Path:
    return _repo_root() / "src" / "anysolver" / "shell_formulations"


def _rollback_modules(before: dict[str, object]) -> None:
    for key in list(sys.modules):
        if key not in before:
            del sys.modules[key]
    if list(sys.modules) != list(before) or any(sys.modules[key] is not value for key, value in before.items()):
        current = dict(sys.modules)
        sys.modules.clear()
        sys.modules.update(before)
        del current
    if list(sys.modules) != list(before) or any(sys.modules[key] is not value for key, value in before.items()):
        raise RuntimeError("failed to restore sys.modules transaction exactly")


def load_numeric_modules() -> dict[str, types.ModuleType]:
    """Load the four accepted numerical files without importing package roots."""

    global _LOADED_NUMERIC_MODULES
    if _LOADED_NUMERIC_MODULES is not None:
        for name, module in _LOADED_NUMERIC_MODULES.items():
            if sys.modules.get(name) is not module:
                raise RuntimeError("cached synthetic module identity changed")
        return dict(_LOADED_NUMERIC_MODULES)

    before = dict(sys.modules)
    forbidden = [name for name in before if name.casefold() == "anysolver" or name.casefold().startswith("anysolver.")]
    if forbidden:
        raise RuntimeError(f"synthetic loader refuses pre-existing ANYsolver modules: {forbidden!r}")
    source_dir = _numeric_source_dir().resolve()
    paths = {name: (source_dir / name).resolve() for name in SOURCE_ORDER}
    for name, path in paths.items():
        try:
            path.relative_to(source_dir)
        except ValueError as exc:
            raise RuntimeError(f"numeric source escapes registered directory: {name}") from exc
        _regular_non_reparse(path)
        actual = _canonical_source_hash(path)
        if actual != SOURCE_HASHES[name]:
            raise RuntimeError(f"numeric source hash mismatch for {name}: {actual}")

    package_names = ("anysolver", "anysolver.shell_formulations")
    accepted_names = set(package_names)
    accepted_names.update(f"anysolver.shell_formulations.{Path(name).stem}" for name in SOURCE_ORDER)
    loaded: dict[str, types.ModuleType] = {}
    try:
        root_package = types.ModuleType("anysolver")
        root_package.__path__ = [str(source_dir.parent)]
        root_package.__package__ = "anysolver"
        root_spec = importlib.machinery.ModuleSpec("anysolver", loader=None, is_package=True)
        root_spec.submodule_search_locations = list(root_package.__path__)
        root_package.__spec__ = root_spec
        sys.modules["anysolver"] = root_package
        loaded["anysolver"] = root_package

        shell_package = types.ModuleType("anysolver.shell_formulations")
        shell_package.__path__ = [str(source_dir)]
        shell_package.__package__ = "anysolver.shell_formulations"
        shell_spec = importlib.machinery.ModuleSpec(
            "anysolver.shell_formulations", loader=None, is_package=True
        )
        shell_spec.submodule_search_locations = list(shell_package.__path__)
        shell_package.__spec__ = shell_spec
        sys.modules["anysolver.shell_formulations"] = shell_package
        loaded["anysolver.shell_formulations"] = shell_package

        for filename in SOURCE_ORDER:
            full_name = f"anysolver.shell_formulations.{Path(filename).stem}"
            spec = importlib.util.spec_from_file_location(full_name, paths[filename])
            if spec is None or spec.loader is None:
                raise RuntimeError(f"unable to create module spec for {filename}")
            module = importlib.util.module_from_spec(spec)
            sys.modules[full_name] = module
            spec.loader.exec_module(module)
            module_path = Path(module.__file__).resolve()
            if module_path != paths[filename]:
                raise RuntimeError(f"loaded module path mismatch for {filename}")
            loaded[full_name] = module

        new_any = {
            name.casefold()
            for name in sys.modules
            if name not in before and name.split(".", 1)[0].casefold().startswith("any")
        }
        accepted_folded = {name.casefold() for name in accepted_names}
        if new_any != accepted_folded:
            raise RuntimeError(f"synthetic import escaped six-module allowlist: {sorted(new_any)!r}")
        if set(loaded) != accepted_names or any(sys.modules[name] is not loaded[name] for name in accepted_names):
            raise RuntimeError("synthetic loader did not bind the exact six accepted module objects")
    except BaseException:
        _rollback_modules(before)
        raise

    _LOADED_NUMERIC_MODULES = loaded
    return dict(loaded)


def _reference_module() -> types.ModuleType:
    return load_numeric_modules()["anysolver.shell_formulations.mitc4_plus_d_reference"]


def _scalar_module() -> types.ModuleType:
    return load_numeric_modules()["anysolver.shell_formulations.mitc4_plus_d_scalar"]


def residual_tolerance(*dimensions: int) -> float:
    values = [1]
    for dimension in dimensions:
        if type(dimension) is not int or dimension < 0:
            raise ProofInputError("residual dimensions must be non-negative integers")
        values.append(dimension)
    return RESIDUAL_FACTOR * max(values) * EPS64


def _matrix_norm_2(matrix: FloatArray) -> float:
    array = np.asarray(matrix, dtype=np.float64)
    if array.size == 0 or not np.any(array):
        return 0.0
    return float(np.linalg.norm(array, ord=2))


def zero_residual(operator: FloatArray, vectors: FloatArray) -> float:
    left = np.asarray(operator, dtype=np.float64)
    right = np.asarray(vectors, dtype=np.float64)
    numerator = float(np.linalg.norm(left @ right, ord="fro"))
    denominator = _matrix_norm_2(left) * float(np.linalg.norm(right, ord="fro"))
    if denominator == 0.0:
        return 0.0 if numerator == 0.0 else math.inf
    return numerator / denominator


def equality_residual(left: FloatArray, right: FloatArray) -> float:
    a = np.asarray(left, dtype=np.float64)
    b = np.asarray(right, dtype=np.float64)
    numerator = float(np.linalg.norm(a - b, ord="fro"))
    denominator = max(float(np.linalg.norm(a, ord="fro")), float(np.linalg.norm(b, ord="fro")))
    if denominator == 0.0:
        return 0.0 if numerator == 0.0 else math.inf
    return numerator / denominator


def _symmetrize(projector: FloatArray) -> FloatArray:
    value = np.asarray(projector, dtype=np.float64)
    return np.array(0.5 * (value + value.T), dtype=np.float64, order="C")


def rank_kernel(matrix: FloatArray, multiplier: float = 1.0) -> dict[str, Any]:
    """Frozen binary64 SVD rank decision and orthonormal kernel projector."""

    if multiplier not in SENSITIVITY_MULTIPLIERS:
        raise ProofInputError("unregistered SVD sensitivity multiplier")
    array = np.asarray(matrix, dtype=np.float64)
    if array.ndim != 2 or not np.all(np.isfinite(array)):
        raise ProofInputError("rank input must be a finite matrix")
    m, n = array.shape
    if n == 0:
        empty = np.empty((0, 0), dtype=np.float64)
        return {"rank": 0, "kernel_dimension": 0, "sigma_max": 0.0, "tau": 0.0,
                "singular_values": np.empty((0,), dtype=np.float64), "kernel_raw": empty,
                "range_raw": np.empty((m, 0), dtype=np.float64), "projector": empty}
    if m == 0 or not np.any(array):
        identity = np.eye(n, dtype=np.float64)
        return {"rank": 0, "kernel_dimension": n, "sigma_max": 0.0, "tau": 0.0,
                "singular_values": np.zeros((min(m, n),), dtype=np.float64),
                "kernel_raw": identity, "range_raw": np.empty((m, 0), dtype=np.float64),
                "projector": identity}
    u, singular, vh = np.linalg.svd(array, full_matrices=True)
    sigma_max = float(singular[0]) if singular.size else 0.0
    tau = multiplier * SVD_FACTOR * max(m, n) * EPS64 * sigma_max
    rank = int(np.count_nonzero(singular > tau))
    kernel = np.array(vh[rank:, :].T, dtype=np.float64, order="C")
    projector = _symmetrize(kernel @ kernel.T)
    return {"rank": rank, "kernel_dimension": n - rank, "sigma_max": sigma_max, "tau": tau,
            "singular_values": singular, "kernel_raw": kernel,
            "range_raw": np.array(u[:, :rank], dtype=np.float64, order="C"),
            "projector": projector}


def rank_kernel_inherited(
    matrix: FloatArray,
    parent_scale: float,
    multiplier: float = 1.0,
) -> dict[str, Any]:
    """Rank a derived restriction against its frozen multiplier-one parent scale."""

    if multiplier not in SENSITIVITY_MULTIPLIERS:
        raise ProofInputError("unregistered SVD sensitivity multiplier")
    if type(parent_scale) is not float or not math.isfinite(parent_scale) or parent_scale < 0.0:
        raise ProofInputError("inherited parent scale must be a finite nonnegative Python float")
    array = np.asarray(matrix, dtype=np.float64)
    if array.ndim != 2 or not np.all(np.isfinite(array)):
        raise ProofInputError("inherited-scale rank input must be a finite matrix")
    m, n = array.shape
    if parent_scale == 0.0 and np.any(array):
        raise RuntimeError("zero parent scale produced a nonzero derived restriction")
    tau = multiplier * SVD_FACTOR * max(m, n) * EPS64 * parent_scale
    if n == 0:
        empty = np.empty((0, 0), dtype=np.float64)
        return {
            "rank": 0,
            "kernel_dimension": 0,
            "sigma_max": 0.0,
            "parent_scale": parent_scale,
            "tau": tau,
            "singular_values": np.empty((0,), dtype=np.float64),
            "kernel_raw": empty,
            "range_raw": np.empty((m, 0), dtype=np.float64),
            "projector": empty,
        }
    if m == 0 or not np.any(array):
        identity = np.eye(n, dtype=np.float64)
        return {
            "rank": 0,
            "kernel_dimension": n,
            "sigma_max": 0.0,
            "parent_scale": parent_scale,
            "tau": tau,
            "singular_values": np.zeros((min(m, n),), dtype=np.float64),
            "kernel_raw": identity,
            "range_raw": np.empty((m, 0), dtype=np.float64),
            "projector": identity,
        }
    u, singular, vh = np.linalg.svd(array, full_matrices=True)
    sigma_max = float(singular[0]) if singular.size else 0.0
    rank = int(np.count_nonzero(singular > tau))
    kernel = np.array(vh[rank:, :].T, dtype=np.float64, order="C")
    projector = _symmetrize(kernel @ kernel.T)
    return {
        "rank": rank,
        "kernel_dimension": n - rank,
        "sigma_max": sigma_max,
        "parent_scale": parent_scale,
        "tau": tau,
        "singular_values": singular,
        "kernel_raw": kernel,
        "range_raw": np.array(u[:, :rank], dtype=np.float64, order="C"),
        "projector": projector,
    }


def canonical_basis(projector: FloatArray, dimension: int | None = None) -> FloatArray:
    """Canonicalize a subspace from its projector columns, never SVD vectors."""

    value = _symmetrize(np.asarray(projector, dtype=np.float64))
    if value.ndim != 2 or value.shape[0] != value.shape[1] or not np.all(np.isfinite(value)):
        raise ProofInputError("canonical basis requires a finite square projector")
    n = value.shape[0]
    if dimension is None:
        dimension = rank_kernel(value)["rank"]
    if type(dimension) is not int or not 0 <= dimension <= n:
        raise ProofInputError("invalid canonical subspace dimension")
    if dimension == 0:
        return np.empty((n, 0), dtype=np.float64)
    chosen: list[FloatArray] = []
    used: set[int] = set()
    for _ in range(dimension):
        candidates: list[tuple[float, int, FloatArray]] = []
        for column in range(n):
            if column in used:
                continue
            residual = np.array(value[:, column], dtype=np.float64, copy=True)
            for _pass in range(2):
                for basis_vector in chosen:
                    residual -= basis_vector * float(basis_vector @ residual)
            candidates.append((float(np.linalg.norm(residual)), column, residual))
        maximum = max(item[0] for item in candidates)
        tie = CANONICAL_TIE_FACTOR * EPS64 * max(1.0, maximum)
        eligible = [item for item in candidates if maximum - item[0] <= tie]
        norm, pivot, residual = min(eligible, key=lambda item: item[1])
        if norm <= residual_tolerance(max(1, n)):
            raise RuntimeError("canonical projector pivot is below the registered fail-closed threshold")
        vector = residual / norm
        absolute = np.abs(vector)
        largest = float(np.max(absolute))
        sign_tie = CANONICAL_TIE_FACTOR * EPS64 * max(1.0, largest)
        sign_index = min(int(index) for index in np.flatnonzero(largest - absolute <= sign_tie))
        if vector[sign_index] < 0.0:
            vector = -vector
        vector[vector == 0.0] = 0.0
        chosen.append(vector)
        used.add(pivot)
    result = np.column_stack(chosen)
    orthogonality = equality_residual(result.T @ result, np.eye(dimension, dtype=np.float64))
    if orthogonality > residual_tolerance(n, dimension, dimension):
        raise RuntimeError("canonical basis failed orthogonality gate")
    return np.array(result, dtype=np.float64, order="C")


def range_projector(vectors: FloatArray, multiplier: float = 1.0) -> tuple[FloatArray, int]:
    value = np.asarray(vectors, dtype=np.float64)
    if value.ndim != 2 or not np.all(np.isfinite(value)):
        raise ProofInputError("range vectors must be a finite matrix")
    n, k = value.shape
    if k == 0 or not np.any(value):
        return np.zeros((n, n), dtype=np.float64), 0
    decomposition = rank_kernel(value.T, multiplier)
    projector = _symmetrize(np.eye(n, dtype=np.float64) - decomposition["projector"])
    return projector, int(decomposition["rank"])


def range_projector_inherited(
    vectors: FloatArray,
    parent_scale: float,
    multiplier: float = 1.0,
) -> tuple[FloatArray, int, dict[str, Any]]:
    value = np.asarray(vectors, dtype=np.float64)
    if value.ndim != 2 or not np.all(np.isfinite(value)):
        raise ProofInputError("range vectors must be a finite matrix")
    decomposition = rank_kernel_inherited(value, parent_scale, multiplier)
    basis = decomposition["range_raw"]
    projector = _symmetrize(basis @ basis.T)
    return projector, int(decomposition["rank"]), decomposition


def operator_kernel_intersection(
    parent_projector: FloatArray,
    parent_dimension: int,
    annihilator: FloatArray,
    annihilator_parent_scale: float,
    multiplier: float = 1.0,
) -> tuple[FloatArray, int, dict[str, Any]]:
    """Intersect a represented subspace with an operator kernel."""

    parent = _symmetrize(parent_projector)
    parent_basis = canonical_basis(parent, parent_dimension)
    operator = np.asarray(annihilator, dtype=np.float64)
    if annihilator_parent_scale == 0.0 and np.any(operator):
        raise RuntimeError("zero inherited scale requires an exactly zero parent operator")
    restricted = operator @ parent_basis
    restricted_kernel = rank_kernel_inherited(
        restricted, float(annihilator_parent_scale), multiplier
    )
    intersection_basis = parent_basis @ restricted_kernel["kernel_raw"]
    projector = _symmetrize(intersection_basis @ intersection_basis.T)
    dimension = int(restricted_kernel["kernel_dimension"])
    return projector, dimension, restricted_kernel


def augmented_intersection(
    left_projector: FloatArray,
    left_dimension: int,
    right_projector: FloatArray,
    right_dimension: int,
    multiplier: float = 1.0,
) -> tuple[FloatArray, int, dict[str, Any]]:
    """Symmetric represented-subspace intersection through ``[Q_U,-Q_V]``."""

    left = _symmetrize(left_projector)
    right = _symmetrize(right_projector)
    if left.shape != right.shape or left.ndim != 2 or left.shape[0] != left.shape[1]:
        raise ProofInputError("augmented intersection requires equal square projectors")
    q_left = canonical_basis(left, left_dimension)
    q_right = canonical_basis(right, right_dimension)
    augmented = np.column_stack((q_left, -q_right))
    decomposition = rank_kernel(augmented, multiplier)
    dimension = int(decomposition["kernel_dimension"])
    n = left.shape[0]
    if dimension == 0:
        zero = np.zeros((n, n), dtype=np.float64)
        return zero, 0, {
            "augmented_rank": decomposition["rank"],
            "augmented_tau": decomposition["tau"],
            "mapped_projector_residual": 0.0,
        }
    coefficients = decomposition["kernel_raw"]
    mapped_left = q_left @ coefficients[:left_dimension, :]
    mapped_right = q_right @ coefficients[left_dimension:, :]
    # Mapped coefficient vectors inherit the unit scale of the two
    # projector-derived orthonormal bases; never rescale their near-zero image.
    p_left, rank_left, _ = range_projector_inherited(mapped_left, 1.0, multiplier)
    p_right, rank_right, _ = range_projector_inherited(mapped_right, 1.0, multiplier)
    if rank_left != dimension or rank_right != dimension:
        raise RuntimeError("augmented intersection mapped range lost its registered dimension")
    agreement = equality_residual(p_left, p_right)
    if agreement > residual_tolerance(n, n):
        raise RuntimeError("augmented intersection mapped projectors disagree")
    projector = _symmetrize(0.5 * (p_left + p_right))
    return projector, dimension, {
        "augmented_rank": decomposition["rank"],
        "augmented_tau": decomposition["tau"],
        "mapped_projector_residual": agreement,
    }


def represented_sum(
    left_projector: FloatArray,
    left_dimension: int,
    right_projector: FloatArray,
    right_dimension: int,
    overlap_dimension: int,
    multiplier: float = 1.0,
) -> tuple[FloatArray, int]:
    left_basis = canonical_basis(left_projector, left_dimension)
    right_basis = canonical_basis(right_projector, right_dimension)
    vectors = np.column_stack((left_basis, right_basis))
    if left_dimension + right_dimension == 0:
        projector = np.zeros_like(left_projector)
        dimension = 0
    else:
        # Concatenated projector-derived bases also have a preregistered O(1)
        # parent scale.  Anchoring it at one avoids relative-only collapse.
        projector, dimension, _ = range_projector_inherited(vectors, 1.0, multiplier)
    expected = left_dimension + right_dimension - overlap_dimension
    if dimension != expected:
        raise RuntimeError(f"represented sum dimension {dimension} differs from {expected}")
    return projector, dimension


def _projector_gate(projector: FloatArray, dimension: int) -> dict[str, float]:
    p = _symmetrize(projector)
    n = p.shape[0]
    values = {
        "symmetry": equality_residual(p, p.T),
        "idempotence": equality_residual(p @ p, p),
        "trace": abs(float(np.trace(p)) - dimension) / max(1, dimension),
    }
    tolerance = residual_tolerance(n, n)
    if any(value > tolerance for value in values.values()):
        raise RuntimeError(f"projector invariant failed: {values!r} > {tolerance}")
    return values


def _finite_array(value: Any, shape: tuple[int, ...], name: str) -> FloatArray:
    array = np.asarray(value, dtype=np.float64)
    if array.shape != shape or not np.all(np.isfinite(array)):
        raise ProofInputError(f"{name} must be finite with shape {shape}, got {array.shape}")
    return np.array(array, dtype=np.float64, order="C", copy=True)


def _positive_float(value: Any, name: str) -> float:
    if type(value) not in (int, float) or type(value) is bool:
        raise ProofInputError(f"{name} must be a real scalar")
    result = float(value)
    if not math.isfinite(result) or result <= 0.0:
        raise ProofInputError(f"{name} must be finite and positive")
    return result


def _activity_float(value: Any, name: str) -> float:
    result = _positive_float(value, name)
    if result > 1.0:
        raise ProofInputError(f"{name} must not exceed one")
    return result


def _diameter(coordinates: FloatArray, connectivities: Sequence[Sequence[int]]) -> float:
    maximum = 0.0
    for connectivity in connectivities:
        local = coordinates[np.asarray(connectivity, dtype=np.int64)]
        for left in range(4):
            for right in range(left + 1, 4):
                maximum = max(maximum, float(np.linalg.norm(local[left] - local[right])))
    if not math.isfinite(maximum) or maximum <= 0.0:
        raise ProofInputError("retained element diameter must be finite and positive")
    return maximum


def _scatter_matrix(local: FloatArray, connectivity: Sequence[int], node_count: int) -> FloatArray:
    local_array = np.asarray(local, dtype=np.float64)
    if local_array.ndim != 2 or local_array.shape[1] != 24:
        raise ProofInputError("local operator must have 24 columns")
    result = np.zeros((local_array.shape[0], 6 * node_count), dtype=np.float64)
    for local_node, global_node in enumerate(connectivity):
        result[:, 6 * global_node : 6 * global_node + 6] = local_array[
            :, 6 * local_node : 6 * local_node + 6
        ]
    return result


def _scatter_square(local: FloatArray, connectivity: Sequence[int], node_count: int) -> FloatArray:
    local_array = np.asarray(local, dtype=np.float64)
    if local_array.shape != (24, 24):
        raise ProofInputError("local square operator must have shape (24, 24)")
    result = np.zeros((6 * node_count, 6 * node_count), dtype=np.float64)
    for local_left, global_left in enumerate(connectivity):
        for local_right, global_right in enumerate(connectivity):
            result[
                6 * global_left : 6 * global_left + 6,
                6 * global_right : 6 * global_right + 6,
            ] += local_array[
                6 * local_left : 6 * local_left + 6,
                6 * local_right : 6 * local_right + 6,
            ]
    return result


def _validate_model(model: Mapping[str, Any]) -> dict[str, Any]:
    if type(model) is not dict:
        raise ProofInputError("model must be a JSON object")
    identifier = model.get("id")
    if type(identifier) is not str or not identifier or "\r" in identifier or "\n" in identifier:
        raise ProofInputError("model id must be a non-empty actual string")
    coordinates_raw = model.get("coordinates")
    directors_raw = model.get("directors")
    thickness_raw = model.get("thickness")
    if type(coordinates_raw) is not list or len(coordinates_raw) < 4:
        raise ProofInputError(f"{identifier}: coordinates must contain at least four nodes")
    node_count = len(coordinates_raw)
    coordinates = _finite_array(coordinates_raw, (node_count, 3), f"{identifier}.coordinates")
    directors = _finite_array(directors_raw, (node_count, 3), f"{identifier}.directors")
    director_norms = np.linalg.norm(directors, axis=1)
    if np.any(np.abs(director_norms - 1.0) > 64.0 * EPS64):
        raise ProofInputError(f"{identifier}: directors must be frozen unit vectors")
    thickness = _finite_array(thickness_raw, (node_count,), f"{identifier}.thickness")
    if np.any(thickness <= 0.0):
        raise ProofInputError(f"{identifier}: thickness must be positive")
    elements_raw = model.get("elements")
    if type(elements_raw) is not list or not elements_raw:
        raise ProofInputError(f"{identifier}: elements must be a non-empty list")

    elements: list[dict[str, Any]] = []
    retained_count = 0
    for index, element in enumerate(elements_raw):
        if type(element) is not dict:
            raise ProofInputError(f"{identifier}: element {index} must be an object")
        nodes = element.get("nodes")
        if type(nodes) is not list or len(nodes) != 4:
            raise ProofInputError(f"{identifier}: element {index} must have four nodes")
        validated_nodes: list[int] = []
        for node in nodes:
            if type(node) is not int or not 0 <= node < node_count:
                raise ProofInputError(f"{identifier}: invalid node index {node!r}")
            validated_nodes.append(node)
        if len(set(validated_nodes)) != 4:
            raise ProofInputError(f"{identifier}: element {index} repeats a node")
        state = element.get("state", "active")
        if state not in ("active", "softened", "deleted"):
            raise ProofInputError(f"{identifier}: invalid activity state {state!r}")
        if state == "deleted":
            alpha = None
            beta = None
        else:
            alpha = _activity_float(element.get("alpha", 1.0), f"{identifier}.alpha")
            beta = _activity_float(element.get("beta", 1.0), f"{identifier}.beta")
            retained_count += 1
        density = _positive_float(element.get("density", 1.0), f"{identifier}.density")
        elements.append(
            {
                "index": index,
                "nodes": tuple(validated_nodes),
                "state": state,
                "alpha": alpha,
                "beta": beta,
                "density": density,
            }
        )
    if retained_count == 0:
        raise ProofInputError(f"{identifier}: delete-all is invalid because positive totals are absent")
    constraints = model.get("constraint_sets", [])
    if type(constraints) is not list:
        raise ProofInputError(f"{identifier}: constraint_sets must be a list")
    return {
        "id": identifier,
        "kind": model.get("kind", "topology"),
        "coordinates": coordinates,
        "directors": directors,
        "thickness": thickness,
        "elements": elements,
        "constraint_sets": constraints,
        "expected": model.get("expected", {}),
        "notes": model.get("notes", []),
    }


def _retained_components(node_count: int, elements: Sequence[Mapping[str, Any]]) -> tuple[list[list[int]], list[int], list[tuple[int, int]]]:
    adjacency: list[set[int]] = [set() for _ in range(node_count)]
    incident = [False] * node_count
    edges: set[tuple[int, int]] = set()
    for element in elements:
        if element["state"] == "deleted":
            continue
        nodes = element["nodes"]
        for node in nodes:
            incident[node] = True
        for left, right in zip(nodes, nodes[1:] + nodes[:1]):
            edge = (min(left, right), max(left, right))
            edges.add(edge)
            adjacency[left].add(right)
            adjacency[right].add(left)
    components: list[list[int]] = []
    visited: set[int] = set()
    for seed in range(node_count):
        if not incident[seed] or seed in visited:
            continue
        stack = [seed]
        component: list[int] = []
        visited.add(seed)
        while stack:
            node = stack.pop()
            component.append(node)
            for neighbor in sorted(adjacency[node], reverse=True):
                if neighbor not in visited:
                    visited.add(neighbor)
                    stack.append(neighbor)
        components.append(sorted(component))
    components.sort(key=lambda values: values[0])
    orphans = [node for node, present in enumerate(incident) if not present]
    return components, orphans, sorted(edges)


def _bipartite_patterns(components: Sequence[Sequence[int]], edges: Sequence[tuple[int, int]]) -> tuple[bool, list[dict[int, float]]]:
    adjacency: dict[int, list[int]] = {}
    for left, right in edges:
        adjacency.setdefault(left, []).append(right)
        adjacency.setdefault(right, []).append(left)
    patterns: list[dict[int, float]] = []
    all_bipartite = True
    for component in components:
        colors: dict[int, float] = {}
        seed = min(component)
        colors[seed] = 1.0
        queue = [seed]
        valid = True
        while queue:
            node = queue.pop(0)
            for neighbor in sorted(adjacency.get(node, [])):
                expected = -colors[node]
                if neighbor in colors and colors[neighbor] != expected:
                    valid = False
                elif neighbor not in colors:
                    colors[neighbor] = expected
                    queue.append(neighbor)
        if valid:
            patterns.append(colors)
        else:
            all_bipartite = False
    return all_bipartite, patterns


def _rigid_candidates(
    coordinates: FloatArray,
    components: Sequence[Sequence[int]],
    scale_vector: FloatArray,
) -> FloatArray:
    node_count = coordinates.shape[0]
    columns: list[FloatArray] = []
    axes = np.eye(3, dtype=np.float64)
    for component in components:
        center = np.mean(coordinates[np.asarray(component, dtype=np.int64)], axis=0)
        for axis in axes:
            physical = np.zeros(6 * node_count, dtype=np.float64)
            for node in component:
                physical[6 * node : 6 * node + 3] = axis
            columns.append(physical / scale_vector)
        for axis in axes:
            physical = np.zeros(6 * node_count, dtype=np.float64)
            for node in component:
                physical[6 * node : 6 * node + 3] = np.cross(axis, coordinates[node] - center)
                physical[6 * node + 3 : 6 * node + 6] = axis
            columns.append(physical / scale_vector)
    if not columns:
        return np.empty((6 * node_count, 0), dtype=np.float64)
    return np.column_stack(columns)


def assemble_model(model_input: Mapping[str, Any]) -> dict[str, Any]:
    """Assemble registered element maps numerically, without solver assembly."""

    model = _validate_model(model_input)
    coordinates = model["coordinates"]
    directors = model["directors"]
    thickness = model["thickness"]
    elements = model["elements"]
    retained = [element for element in elements if element["state"] != "deleted"]
    node_count = coordinates.shape[0]
    ell = _diameter(coordinates, [element["nodes"] for element in retained])
    scale_vector = np.tile(np.array([ell, ell, ell, 1.0, 1.0, 1.0], dtype=np.float64), node_count)
    reference_module = _reference_module()
    scalar_module = _scalar_module()

    b_rows: list[tuple[float, FloatArray]] = []
    h_rows: list[tuple[float, FloatArray]] = []
    w_b = 0.0
    w_h = 0.0
    stiffness_physical = np.zeros((6 * node_count, 6 * node_count), dtype=np.float64)
    mass_physical = np.zeros_like(stiffness_physical)
    references: list[dict[str, Any]] = []
    for element in retained:
        connectivity = element["nodes"]
        reference = reference_module.build_reference_data(
            coordinates[np.asarray(connectivity, dtype=np.int64)],
            directors[np.asarray(connectivity, dtype=np.int64)],
            thickness[np.asarray(connectivity, dtype=np.int64)],
        )
        alpha = float(element["alpha"])
        beta = float(element["beta"])
        density = float(element["density"])
        references.append({"element": element, "reference": reference})
        for surface in range(4):
            for through in range(2):
                weight = float(reference.volume_weights[surface, through])
                if not math.isfinite(weight) or weight <= 0.0:
                    raise RuntimeError("reference quadrature weight must be positive")
                b_local = reference.volume_strain_operators[surface, through]
                h_local = reference.volume_displacement_operators[surface, through]
                b_rows.append((alpha * weight, _scatter_matrix(b_local, connectivity, node_count)))
                h_rows.append((density * beta * weight, _scatter_matrix(h_local, connectivity, node_count)))
                w_b += alpha * weight
                w_h += density * beta * weight
        local_stiffness = scalar_module.linear_stiffness(reference, np.eye(5, dtype=np.float64))
        local_mass = scalar_module.consistent_mass(reference, density)
        stiffness_physical += alpha * _scatter_square(local_stiffness, connectivity, node_count)
        mass_physical += beta * _scatter_square(local_mass, connectivity, node_count)
    if not math.isfinite(w_b) or w_b <= 0.0 or not math.isfinite(w_h) or w_h <= 0.0:
        raise RuntimeError("positive strain and mass quadrature totals are required")

    b_weighted = np.vstack(
        [math.sqrt(weight / w_b) * (row * scale_vector[np.newaxis, :]) for weight, row in b_rows]
    )
    h_weighted = np.vstack(
        [
            math.sqrt(weight / w_h)
            * (row * scale_vector[np.newaxis, :])
            / ell
            for weight, row in h_rows
        ]
    )
    scaled_stiffness = (
        scale_vector[:, None] * stiffness_physical * scale_vector[None, :] / w_b
    )
    scaled_mass = (
        scale_vector[:, None] * mass_physical * scale_vector[None, :] / (ell * ell * w_h)
    )
    stiffness_residual = equality_residual(scaled_stiffness, b_weighted.T @ b_weighted)
    mass_residual = equality_residual(scaled_mass, h_weighted.T @ h_weighted)
    gate_tolerance = residual_tolerance(b_weighted.shape[0], h_weighted.shape[0], 6 * node_count)
    if stiffness_residual > gate_tolerance or mass_residual > gate_tolerance:
        raise RuntimeError(
            f"operator/stiffness/mass corroboration failed: K={stiffness_residual}, M={mass_residual}"
        )

    components, orphans, edges = _retained_components(node_count, elements)
    rigid = _rigid_candidates(coordinates, components, scale_vector)
    drill_map = np.zeros((6 * node_count, node_count), dtype=np.float64)
    for node in range(node_count):
        drill_map[6 * node + 3 : 6 * node + 6, node] = directors[node]
    bipartite, patterns = _bipartite_patterns(components, edges)
    return {
        "model": model,
        "ell": ell,
        "scale_vector": scale_vector,
        "B_w": b_weighted,
        "H_w": h_weighted,
        "K_w": scaled_stiffness,
        "M_w": scaled_mass,
        "W_B": w_b,
        "W_H": w_h,
        "references": references,
        "components": components,
        "orphans": orphans,
        "edges": edges,
        "bipartite": bipartite,
        "bipartite_patterns": patterns,
        "rigid_candidates": rigid,
        "drill_map": drill_map,
        "corroboration": {"stiffness": stiffness_residual, "mass": mass_residual},
    }


def _subspace_record(projector: FloatArray, dimension: int, environment_digest: str | None) -> dict[str, Any]:
    canonical = canonical_basis(projector, dimension)
    gates = _projector_gate(projector, dimension)
    record: dict[str, Any] = {
        "dimension": dimension,
        "projector": projector,
        "basis": canonical,
        "gates": gates,
    }
    if environment_digest is not None:
        record["projector_snapshot_sha256"] = snapshot_digest(projector, "projector", environment_digest)
        record["basis_snapshot_sha256"] = snapshot_digest(canonical, "basis", environment_digest)
    return record


def _containment_residual(child: FloatArray, parent: FloatArray) -> float:
    return equality_residual(np.asarray(child) @ np.asarray(parent), child)


def _projector_complement(
    parent: FloatArray,
    child: FloatArray,
    expected_dimension: int,
    multiplier: float,
    label: str,
) -> FloatArray:
    """Return a registered projector complement without ranking roundoff alone."""

    raw = _symmetrize(np.asarray(parent) - np.asarray(child))
    if expected_dimension == 0:
        residual = equality_residual(parent, child)
        if residual > residual_tolerance(parent.shape[0], parent.shape[1]):
            raise RuntimeError(f"{label} expected zero but parent/child differ: {residual}")
        return np.zeros_like(raw)
    decision = rank_kernel_inherited(raw, 1.0, multiplier)
    if decision["rank"] != expected_dimension:
        raise RuntimeError(
            f"{label} inherited-scale rank {decision['rank']} differs from {expected_dimension}"
        )
    return raw


def _gate_partition(
    projectors: Mapping[str, FloatArray],
    dimensions: Mapping[str, int],
    b_operator: FloatArray,
    h_operator: FloatArray,
    b_zero_names: Sequence[str],
    h_zero_names: Sequence[str],
    containments: Mapping[str, tuple[str, str]],
    orthogonalities: Mapping[str, tuple[str, str]],
    physical_b_operator: FloatArray | None = None,
) -> tuple[dict[str, Any], dict[str, float]]:
    physical_b = b_operator if physical_b_operator is None else np.asarray(
        physical_b_operator, dtype=np.float64
    )
    stiffness_gram = physical_b.T @ physical_b
    mass_gram = h_operator.T @ h_operator
    gates: dict[str, Any] = {}
    for name, projector in projectors.items():
        basis = canonical_basis(projector, dimensions[name])
        gates[name] = {
            "projector": _projector_gate(projector, dimensions[name]),
            "B": zero_residual(b_operator, basis),
            "H": zero_residual(h_operator, basis),
            "K": zero_residual(stiffness_gram, basis),
            "M": zero_residual(mass_gram, basis),
        }
    tolerance = residual_tolerance(
        b_operator.shape[0], b_operator.shape[1], h_operator.shape[0], h_operator.shape[1]
    )
    for name in b_zero_names:
        if gates[name]["B"] > tolerance:
            raise RuntimeError(f"{name} fails its registered tangent annihilation gate")
        if gates[name]["K"] > tolerance:
            raise RuntimeError(f"{name} fails its registered stiffness-Gram annihilation gate")
    for name in h_zero_names:
        if gates[name]["H"] > tolerance:
            raise RuntimeError(f"{name} fails its registered mass annihilation gate")
        if gates[name]["M"] > tolerance:
            raise RuntimeError(f"{name} fails its registered mass-Gram annihilation gate")
    relations: dict[str, float] = {}
    for label, (child, parent) in containments.items():
        relations[label] = _containment_residual(projectors[child], projectors[parent])
    for label, (left, right) in orthogonalities.items():
        relations[label] = zero_residual(projectors[left], projectors[right])
    if any(value > tolerance for value in relations.values()):
        raise RuntimeError(f"partition containment/orthogonality failed: {relations!r}")
    return gates, relations


def _free_partition_at(
    b: FloatArray,
    h: FloatArray,
    rigid_candidates: FloatArray,
    multiplier: float,
) -> dict[str, Any]:
    null = rank_kernel(b, multiplier)
    p_n = null["projector"]
    dim_n = int(null["kernel_dimension"])
    h_parent_scale = float(rank_kernel(h, 1.0)["sigma_max"])
    p_g, dim_g, h_restriction = operator_kernel_intersection(
        p_n, dim_n, h, h_parent_scale, multiplier
    )
    dim_p = dim_n - dim_g
    p_p = _projector_complement(p_n, p_g, dim_p, multiplier, "P")

    p_r, dim_r = range_projector(rigid_candidates, multiplier)
    p_rn, dim_rn, rn_intersection = augmented_intersection(
        p_r, dim_r, p_n, dim_n, multiplier
    )
    p_rg, dim_rg, rg_intersection = augmented_intersection(
        p_rn, dim_rn, p_g, dim_g, multiplier
    )
    expected_rq = dim_rn - dim_rg
    q_rn = canonical_basis(p_rn, dim_rn)
    y_r = p_p @ q_rn
    if expected_rq == 0:
        p_rq = np.zeros_like(p_p)
        dim_rq = 0
        y_rank = rank_kernel_inherited(y_r, 1.0 if dim_p else 0.0, multiplier)
        if y_rank["rank"] != 0:
            raise RuntimeError("zero rigid quotient dimension produced a nonzero quotient image")
    else:
        p_rq, dim_rq, y_rank = range_projector_inherited(y_r, 1.0, multiplier)
    if dim_rq != expected_rq:
        raise RuntimeError(
            f"rigid quotient image rank {dim_rq} differs from dim(R_N)-dim(R_G)={expected_rq}"
        )
    dim_z = dim_p - dim_rq
    p_z = _projector_complement(p_p, p_rq, dim_z, multiplier, "Z")

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
        "N": dim_n,
        "G": dim_g,
        "P": dim_p,
        "R": dim_r,
        "R_N": dim_rn,
        "R_G": dim_rg,
        "RQ": dim_rq,
        "Z": dim_z,
    }
    gates, relations = _gate_partition(
        projectors,
        dimensions,
        b,
        h,
        tuple(projectors),
        ("G", "R_G"),
        {
            "G_in_N": ("G", "N"),
            "P_in_N": ("P", "N"),
            "R_N_in_R": ("R_N", "R"),
            "R_N_in_N": ("R_N", "N"),
            "R_G_in_R_N": ("R_G", "R_N"),
            "R_G_in_G": ("R_G", "G"),
            "RQ_in_P": ("RQ", "P"),
            "Z_in_P": ("Z", "P"),
        },
        {"G_orthogonal_P": ("G", "P"), "RQ_orthogonal_Z": ("RQ", "Z")},
        physical_b_operator=b,
    )
    quotient_identity = equality_residual(p_rq + p_z, p_p)
    if quotient_identity > residual_tolerance(p_p.shape[0], p_p.shape[1]):
        raise RuntimeError("RQ plus Z does not reconstruct the positive-mass quotient projector")
    relations["RQ_plus_Z_equals_P"] = quotient_identity
    return {
        "kind": "free",
        "rank": int(null["rank"]),
        "tau": float(null["tau"]),
        "sigma_max": float(null["sigma_max"]),
        "singular_values": null["singular_values"],
        "dimensions": dimensions,
        "projectors": projectors,
        "gates": gates,
        "containment": relations,
        "derived": {
            "H_parent_scale": h_parent_scale,
            "H_restriction_tau": h_restriction["tau"],
            "R_N_intersection": rn_intersection,
            "R_G_intersection": rg_intersection,
            "Y_R_parent_scale": y_rank["parent_scale"],
            "Y_R_tau": y_rank["tau"],
            "Y_R_rank": y_rank["rank"],
            "Y_R_expected_rank": expected_rq,
        },
    }


def _constrained_partition_at(
    b: FloatArray,
    h: FloatArray,
    rigid_candidates: FloatArray,
    constraints: FloatArray,
    multiplier: float,
) -> dict[str, Any]:
    free = _free_partition_at(b, h, rigid_candidates, multiplier)
    c = np.asarray(constraints, dtype=np.float64)
    operator = np.vstack((b, c))
    null = rank_kernel(operator, multiplier)
    p_n = null["projector"]
    dim_n = int(null["kernel_dimension"])
    h_parent_scale = float(rank_kernel(h, 1.0)["sigma_max"])
    p_g, dim_g, h_restriction = operator_kernel_intersection(
        p_n, dim_n, h, h_parent_scale, multiplier
    )
    dim_p = dim_n - dim_g
    p_p = _projector_complement(p_n, p_g, dim_p, multiplier, "P_C")

    p_srg, dim_srg = represented_sum(
        free["projectors"]["R_N"],
        free["dimensions"]["R_N"],
        free["projectors"]["G"],
        free["dimensions"]["G"],
        free["dimensions"]["R_G"],
        multiplier,
    )
    p_lc, dim_lc, lc_intersection = augmented_intersection(
        p_n, dim_n, p_srg, dim_srg, multiplier
    )
    p_lgc, dim_lgc, lgc_intersection = augmented_intersection(
        p_lc, dim_lc, p_g, dim_g, multiplier
    )
    expected_rq = dim_lc - dim_lgc
    q_lc = canonical_basis(p_lc, dim_lc)
    y_rc = p_p @ q_lc
    if expected_rq == 0:
        p_rq = np.zeros_like(p_p)
        dim_rq = 0
        y_rank = rank_kernel_inherited(y_rc, 1.0 if dim_p else 0.0, multiplier)
        if y_rank["rank"] != 0:
            raise RuntimeError("zero constrained rigid quotient dimension produced a nonzero image")
    else:
        p_rq, dim_rq, y_rank = range_projector_inherited(y_rc, 1.0, multiplier)
    if dim_rq != expected_rq:
        raise RuntimeError(
            f"constrained rigid quotient rank {dim_rq} differs from dim(L_C)-dim(L_G_C)={expected_rq}"
        )
    dim_z = dim_p - dim_rq
    p_z = _projector_complement(p_p, p_rq, dim_z, multiplier, "Z_C")

    projectors = {
        "N": p_n,
        "G": p_g,
        "P": p_p,
        "S_RG": p_srg,
        "L_C": p_lc,
        "L_G_C": p_lgc,
        "RQ": p_rq,
        "Z": p_z,
    }
    dimensions = {
        "N": dim_n,
        "G": dim_g,
        "P": dim_p,
        "S_RG": dim_srg,
        "L_C": dim_lc,
        "L_G_C": dim_lgc,
        "RQ": dim_rq,
        "Z": dim_z,
    }
    gates, relations = _gate_partition(
        projectors,
        dimensions,
        operator,
        h,
        ("N", "G", "P", "L_C", "L_G_C", "RQ", "Z"),
        ("G", "L_G_C"),
        {
            "G_in_N": ("G", "N"),
            "P_in_N": ("P", "N"),
            "L_C_in_N": ("L_C", "N"),
            "L_C_in_S_RG": ("L_C", "S_RG"),
            "L_G_C_in_L_C": ("L_G_C", "L_C"),
            "L_G_C_in_G": ("L_G_C", "G"),
            "RQ_in_P": ("RQ", "P"),
            "Z_in_P": ("Z", "P"),
        },
        {"G_orthogonal_P": ("G", "P"), "RQ_orthogonal_Z": ("RQ", "Z")},
        physical_b_operator=b,
    )
    # S_RG is free-tangent compatible but need not satisfy the constraints.
    srg_b_residual = zero_residual(
        b, canonical_basis(p_srg, dim_srg)
    )
    if srg_b_residual > residual_tolerance(b.shape[0], b.shape[1]):
        raise RuntimeError("R_N+G sum is not free-strain null")
    gates["S_RG"]["free_B"] = srg_b_residual
    quotient_identity = equality_residual(p_rq + p_z, p_p)
    if quotient_identity > residual_tolerance(p_p.shape[0], p_p.shape[1]):
        raise RuntimeError("constrained RQ plus Z does not reconstruct P_C")
    relations["RQ_plus_Z_equals_P"] = quotient_identity
    return {
        "kind": "constrained",
        "rank": int(null["rank"]),
        "tau": float(null["tau"]),
        "sigma_max": float(null["sigma_max"]),
        "singular_values": null["singular_values"],
        "dimensions": dimensions,
        "projectors": projectors,
        "gates": gates,
        "containment": relations,
        "derived": {
            "H_parent_scale": h_parent_scale,
            "H_restriction_tau": h_restriction["tau"],
            "L_C_intersection": lc_intersection,
            "L_G_C_intersection": lgc_intersection,
            "Y_R_C_parent_scale": y_rank["parent_scale"],
            "Y_R_C_tau": y_rank["tau"],
            "Y_R_C_rank": y_rank["rank"],
            "Y_R_C_expected_rank": expected_rq,
        },
    }


def _partition_at(
    b_weighted: FloatArray,
    h_weighted: FloatArray,
    rigid_candidates: FloatArray,
    multiplier: float,
    constraints: FloatArray | None = None,
) -> dict[str, Any]:
    b = np.asarray(b_weighted, dtype=np.float64)
    h = np.asarray(h_weighted, dtype=np.float64)
    if constraints is None:
        return _free_partition_at(b, h, rigid_candidates, multiplier)
    return _constrained_partition_at(
        b, h, rigid_candidates, np.asarray(constraints, dtype=np.float64), multiplier
    )


def partition_nullspace(
    b_weighted: FloatArray,
    h_weighted: FloatArray,
    rigid_candidates: FloatArray,
    constraints: FloatArray | None = None,
) -> dict[str, Any]:
    variants = {
        _float_token(multiplier): _partition_at(
            b_weighted, h_weighted, rigid_candidates, multiplier, constraints
        )
        for multiplier in SENSITIVITY_MULTIPLIERS
    }
    base = variants[_float_token(1.0)]
    base_dimensions = base["dimensions"]
    stable = all(item["dimensions"] == base_dimensions for item in variants.values())
    result = dict(base)
    result["sensitivity"] = {
        key: {
            "rank": value["rank"],
            "tau": value["tau"],
            "dimensions": value["dimensions"],
            "gates": value["gates"],
            "containment": value["containment"],
            "derived": value["derived"],
            "projectors": value["projectors"],
        }
        for key, value in variants.items()
    }
    result["sensitivity_stable"] = stable
    if not stable:
        result["categorical_claim_blocked"] = True
    return result


def _candidate_residuals(b: FloatArray, h: FloatArray, candidate: FloatArray) -> dict[str, Any]:
    vector = np.asarray(candidate, dtype=np.float64).reshape(-1, 1)
    if not np.any(vector):
        raise ProofInputError("candidate vector must be nonzero")
    b_residual = zero_residual(b, vector)
    h_residual = zero_residual(h, vector)
    tolerance = residual_tolerance(b.shape[0], b.shape[1], h.shape[0])
    strain_null = b_residual <= tolerance
    mass_null = h_residual <= tolerance
    if strain_null and mass_null:
        classification = "gauge_evidence"
    elif strain_null and not mass_null:
        classification = "positive_mass_strain_null"
    else:
        classification = "not_strain_null"
    return {
        "B_residual": b_residual,
        "H_residual": h_residual,
        "strain_null": strain_null,
        "mass_null": mass_null,
        "classification": classification,
    }


def drill_semantics(assembly: Mapping[str, Any]) -> dict[str, Any]:
    b_drill = assembly["B_w"] @ assembly["drill_map"]
    h_drill = assembly["H_w"] @ assembly["drill_map"]
    partition = partition_nullspace(
        b_drill,
        h_drill,
        np.empty((b_drill.shape[1], 0), dtype=np.float64),
    )
    node_count = b_drill.shape[1]
    constant: list[dict[str, Any]] = []
    for component_index, component in enumerate(assembly["components"]):
        candidate = np.zeros(node_count, dtype=np.float64)
        candidate[np.asarray(component, dtype=np.int64)] = 1.0
        constant.append(
            {
                "component": component_index,
                "nodes": list(component),
                **_candidate_residuals(b_drill, h_drill, candidate),
            }
        )
    checkerboard: list[dict[str, Any]] = []
    for component_index, pattern in enumerate(assembly["bipartite_patterns"]):
        candidate = np.zeros(node_count, dtype=np.float64)
        for node, value in pattern.items():
            candidate[node] = value
        metrics = _candidate_residuals(b_drill, h_drill, candidate)
        if metrics["classification"] == "gauge_evidence":
            raise RuntimeError("positive-mass checkerboard candidate was incorrectly classified as gauge")
        checkerboard.append(
            {
                "component": component_index,
                "pattern": [float(value) for value in candidate],
                **metrics,
            }
        )
    return {
        "partition": partition,
        "bipartite": assembly["bipartite"],
        "constant_candidates": constant,
        "checkerboard_candidates": checkerboard,
    }


def normalized_constraints(
    specification: Mapping[str, Any],
    scale_vector: FloatArray,
) -> dict[str, Any]:
    """Validate affine physical rows, then normalize C and d together."""

    if type(specification) is not dict:
        raise ProofInputError("constraint set must be an object")
    identifier = specification.get("id")
    if type(identifier) is not str or not identifier:
        raise ProofInputError("constraint set id must be a non-empty actual string")
    rows = specification.get("rows")
    if type(rows) is not list:
        raise ProofInputError(f"{identifier}: rows must be a list")
    ndof = int(np.asarray(scale_vector).size)
    c_physical_rows: list[FloatArray] = []
    rhs_values: list[float] = []
    omitted_zero_rows = 0
    for row_index, row in enumerate(rows):
        if type(row) is not dict:
            raise ProofInputError(f"{identifier}: row {row_index} must be an object")
        terms = row.get("terms")
        if type(terms) is not list:
            raise ProofInputError(f"{identifier}: row {row_index} terms must be a list")
        physical = np.zeros(ndof, dtype=np.float64)
        seen: set[int] = set()
        for term in terms:
            if type(term) is not list or len(term) != 2:
                raise ProofInputError(f"{identifier}: constraint term must be [index,value]")
            index, coefficient = term
            if type(index) is not int or not 0 <= index < ndof:
                raise ProofInputError(f"{identifier}: invalid original-universe DOF index {index!r}")
            if index in seen:
                raise ProofInputError(f"{identifier}: duplicate term index {index}")
            seen.add(index)
            if type(coefficient) not in (int, float) or type(coefficient) is bool:
                raise ProofInputError(f"{identifier}: coefficient must be a real scalar")
            coefficient_value = float(coefficient)
            if not math.isfinite(coefficient_value):
                raise ProofInputError(f"{identifier}: coefficient must be finite")
            physical[index] = coefficient_value
        rhs = row.get("rhs", 0.0)
        if type(rhs) not in (int, float) or type(rhs) is bool or not math.isfinite(float(rhs)):
            raise ProofInputError(f"{identifier}: RHS must be a finite scalar")
        rhs_value = float(rhs)
        dimensionless = physical * scale_vector
        norm = float(np.linalg.norm(dimensionless))
        if norm == 0.0:
            if rhs_value == 0.0:
                omitted_zero_rows += 1
                continue
            raise ProofInputError(f"{identifier}: zero row with nonzero RHS is infeasible")
        c_physical_rows.append(dimensionless / norm)
        rhs_values.append(rhs_value / norm)
    c_hat = (
        np.vstack(c_physical_rows)
        if c_physical_rows
        else np.empty((0, ndof), dtype=np.float64)
    )
    d_hat = np.asarray(rhs_values, dtype=np.float64)
    return {
        "id": identifier,
        "kind": specification.get("kind", "support_or_mpc"),
        "intended_work_conjugacy": specification.get("intended_work_conjugacy"),
        "C_hat": c_hat,
        "d_hat": d_hat,
        "omitted_zero_rows": omitted_zero_rows,
        "expected": specification.get("expected", {}),
    }


def affine_feasibility(c_hat: FloatArray, d_hat: FloatArray) -> dict[str, Any]:
    c = np.asarray(c_hat, dtype=np.float64)
    d = np.asarray(d_hat, dtype=np.float64)
    if c.ndim != 2 or d.shape != (c.shape[0],) or not np.all(np.isfinite(c)) or not np.all(np.isfinite(d)):
        raise ProofInputError("affine feasibility requires finite compatible C and d")
    variants: dict[str, Any] = {}
    for multiplier in SENSITIVITY_MULTIPLIERS:
        if c.shape[1] == 0 or c.shape[0] == 0 or not np.any(c):
            rank = 0
            solution = np.zeros(c.shape[1], dtype=np.float64)
            tau = 0.0
        else:
            u, singular, vh = np.linalg.svd(c, full_matrices=True)
            sigma_max = float(singular[0]) if singular.size else 0.0
            tau = multiplier * SVD_FACTOR * max(c.shape) * EPS64 * sigma_max
            rank = int(np.count_nonzero(singular > tau))
            solution = np.zeros(c.shape[1], dtype=np.float64)
            if rank:
                solution = vh[:rank, :].T @ ((u[:, :rank].T @ d) / singular[:rank])
        residual = float(np.linalg.norm(c @ solution - d)) / max(1.0, float(np.linalg.norm(d)))
        tolerance = residual_tolerance(c.shape[0], c.shape[1])
        variants[_float_token(multiplier)] = {
            "rank": rank,
            "tau": tau,
            "residual": residual,
            "feasible": residual <= tolerance,
        }
    base = variants[_float_token(1.0)]
    return {
        **base,
        "sensitivity": variants,
        "sensitivity_stable": all(
            item["rank"] == base["rank"] and item["feasible"] == base["feasible"]
            for item in variants.values()
        ),
    }


def _intersection_dimension(left: FloatArray, right: FloatArray) -> int:
    p_left = _symmetrize(left)
    p_right = _symmetrize(right)
    left_dimension = int(rank_kernel(p_left)["rank"])
    right_dimension = int(rank_kernel(p_right)["rank"])
    intersection, dimension, _ = augmented_intersection(
        p_left, left_dimension, p_right, right_dimension
    )
    _projector_gate(intersection, dimension)
    return dimension


def _orphan_record(
    node_count: int,
    orphan_nodes: Sequence[int],
    free_partition: Mapping[str, Any],
    constrained_partition: Mapping[str, Any] | None = None,
    c_hat: FloatArray | None = None,
) -> dict[str, Any]:
    ndof = 6 * node_count
    projector = np.zeros((ndof, ndof), dtype=np.float64)
    for node in orphan_nodes:
        start = 6 * node
        projector[start : start + 6, start : start + 6] = np.eye(6, dtype=np.float64)
    dimension = 6 * len(orphan_nodes)
    _projector_gate(projector, dimension)
    result: dict[str, Any] = {
        "nodes": list(orphan_nodes),
        "dimension": dimension,
        "projector": projector,
        "intersection_G": _intersection_dimension(projector, free_partition["projectors"]["G"]),
    }
    if constrained_partition is not None and c_hat is not None:
        result["intersection_G_C"] = _intersection_dimension(
            projector, constrained_partition["projectors"]["G"]
        )
        row_projector, row_dimension = range_projector(c_hat.T)
        result["constraint_rowspace_dimension"] = row_dimension
        result["intersection_constraint_rowspace"] = _intersection_dimension(projector, row_projector)
    return result


def _partition_record(
    partition: Mapping[str, Any],
    b_weighted: FloatArray,
    h_weighted: FloatArray,
    k_weighted: FloatArray,
    m_weighted: FloatArray,
    environment_digest: str | None,
) -> dict[str, Any]:
    records: dict[str, Any] = {}
    for name in partition["projectors"]:
        projector = partition["projectors"][name]
        dimension = int(partition["dimensions"][name])
        subspace = _subspace_record(projector, dimension, environment_digest)
        basis = subspace["basis"]
        subspace["residuals"] = {
            "B": zero_residual(b_weighted, basis),
            "H": zero_residual(h_weighted, basis),
            "K": zero_residual(k_weighted, basis),
            "M": zero_residual(m_weighted, basis),
        }
        records[name] = subspace
    return {
        "rank": partition["rank"],
        "tau": partition["tau"],
        "sigma_max": partition["sigma_max"],
        "singular_values": partition["singular_values"],
        "dimensions": partition["dimensions"],
        "sensitivity": partition["sensitivity"],
        "sensitivity_stable": partition["sensitivity_stable"],
        "subspaces": records,
        "containment": partition["containment"],
        "derived": partition["derived"],
    }


def analyze_model(model_input: Mapping[str, Any], environment_digest: str | None) -> dict[str, Any]:
    assembly = assemble_model(model_input)
    b = assembly["B_w"]
    h = assembly["H_w"]
    free = partition_nullspace(b, h, assembly["rigid_candidates"])
    free_record = _partition_record(
        free, b, h, assembly["K_w"], assembly["M_w"], environment_digest
    )
    drill = drill_semantics(assembly)
    drill_record = _partition_record(
        drill["partition"],
        b @ assembly["drill_map"],
        h @ assembly["drill_map"],
        (b @ assembly["drill_map"]).T @ (b @ assembly["drill_map"]),
        (h @ assembly["drill_map"]).T @ (h @ assembly["drill_map"]),
        environment_digest,
    )

    constrained: list[dict[str, Any]] = []
    for constraint_input in assembly["model"]["constraint_sets"]:
        constraint = normalized_constraints(constraint_input, assembly["scale_vector"])
        feasibility = affine_feasibility(constraint["C_hat"], constraint["d_hat"])
        for key, expected_value in constraint["expected"].items():
            if key == "rank" and feasibility["rank"] != expected_value:
                raise RuntimeError(
                    f"{constraint['id']}: expected constraint rank {expected_value}, "
                    f"got {feasibility['rank']}"
                )
            if key == "feasible" and feasibility["feasible"] is not expected_value:
                raise RuntimeError(
                    f"{constraint['id']}: expected feasibility {expected_value}, "
                    f"got {feasibility['feasible']}"
                )
            if key == "omitted_zero_rows" and constraint["omitted_zero_rows"] != expected_value:
                raise RuntimeError(
                    f"{constraint['id']}: expected {expected_value} omitted zero rows, "
                    f"got {constraint['omitted_zero_rows']}"
                )
        constrained_partition = partition_nullspace(
            b, h, assembly["rigid_candidates"], constraint["C_hat"]
        )
        record = _partition_record(
            constrained_partition,
            np.vstack((b, constraint["C_hat"])),
            h,
            assembly["K_w"],
            assembly["M_w"],
            environment_digest,
        )
        record.update(
            {
                "id": constraint["id"],
                "kind": constraint["kind"],
                "intended_work_conjugacy": constraint["intended_work_conjugacy"],
                "C_hat": constraint["C_hat"],
                "d_hat": constraint["d_hat"],
                "constraint_rank": feasibility["rank"],
                "feasibility": feasibility,
                "omitted_zero_rows": constraint["omitted_zero_rows"],
                "expected": constraint["expected"],
                "orphans": _orphan_record(
                    assembly["model"]["coordinates"].shape[0],
                    assembly["orphans"],
                    free,
                    constrained_partition,
                    constraint["C_hat"],
                ),
            }
        )
        constrained.append(record)

    expected = assembly["model"]["expected"]
    if type(expected) is not dict:
        raise ProofInputError("expected dimensions must be an object")
    for key, value in expected.items():
        if key == "rank" and free["rank"] != value:
            raise RuntimeError(f"{assembly['model']['id']}: expected rank {value}, got {free['rank']}")
        if key in free["dimensions"] and free["dimensions"][key] != value:
            raise RuntimeError(
                f"{assembly['model']['id']}: expected {key}={value}, got {free['dimensions'][key]}"
            )
    return {
        "id": assembly["model"]["id"],
        "kind": assembly["model"]["kind"],
        "node_count": assembly["model"]["coordinates"].shape[0],
        "retained_element_count": sum(
            element["state"] != "deleted" for element in assembly["model"]["elements"]
        ),
        "ell": assembly["ell"],
        "W_B": assembly["W_B"],
        "W_H": assembly["W_H"],
        "components": assembly["components"],
        "orphans": _orphan_record(
            assembly["model"]["coordinates"].shape[0], assembly["orphans"], free
        ),
        "edges": [list(edge) for edge in assembly["edges"]],
        "bipartite": assembly["bipartite"],
        "corroboration": assembly["corroboration"],
        "free": free_record,
        "drill": {
            "bipartite": drill["bipartite"],
            "constant_candidates": drill["constant_candidates"],
            "checkerboard_candidates": drill["checkerboard_candidates"],
            "partition": drill_record,
        },
        "constraints": constrained,
        "expected": expected,
        "notes": assembly["model"]["notes"],
    }


def _permuted_local_model(base: Mapping[str, Any], variant: Mapping[str, Any]) -> dict[str, Any]:
    if type(variant) is not dict or type(variant.get("id")) is not str:
        raise ProofInputError("local numbering variant must have an actual-string id")
    order = variant.get("order")
    if type(order) is not list or sorted(order) != [0, 1, 2, 3] or any(type(i) is not int for i in order):
        raise ProofInputError("local numbering order must be a permutation of [0,1,2,3]")
    sign = variant.get("director_sign", 1)
    if sign not in (-1, 1) or type(sign) is bool:
        raise ProofInputError("director_sign must be exactly -1 or 1")
    return {
        "id": f"{base['id']}::{variant['id']}",
        "kind": "local_numbering_variant",
        "coordinates": [base["coordinates"][index] for index in order],
        "directors": [
            [sign * float(value) for value in base["directors"][index]] for index in order
        ],
        "thickness": [base["thickness"][index] for index in order],
        "elements": [{"nodes": [0, 1, 2, 3], "state": "active"}],
        "expected": base.get("expected", {}),
        "notes": ["Derived only from the frozen base arrays and registered numbering permutation."],
    }


def _block_permutation(order: Sequence[int]) -> FloatArray:
    transform = np.zeros((24, 24), dtype=np.float64)
    for new_node, old_node in enumerate(order):
        transform[6 * new_node : 6 * new_node + 6, 6 * old_node : 6 * old_node + 6] = np.eye(6)
    return transform


def _numbering_comparison(
    base_result: Mapping[str, Any],
    variant_result: Mapping[str, Any],
    variant: Mapping[str, Any],
) -> dict[str, Any]:
    transform = _block_permutation(variant["order"])
    values: dict[str, float] = {}
    for name in ("N", "G", "P", "R", "R_N", "R_G", "RQ", "Z"):
        base_projector = base_result["free"]["subspaces"][name]["projector"]
        variant_projector = variant_result["free"]["subspaces"][name]["projector"]
        pulled_back = transform.T @ variant_projector @ transform
        values[name] = equality_residual(base_projector, pulled_back)
    tolerance = residual_tolerance(24, 24)
    return {
        "variant": variant["id"],
        "projector_residuals": values,
        "invariant": all(value <= tolerance for value in values.values()),
    }


def cases_path() -> Path:
    return Path(__file__).with_name("s4_nullspace_semantics_cases.json")


def load_cases(path: Path | None = None) -> dict[str, Any]:
    selected = cases_path() if path is None else Path(path)
    raw = selected.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raise ProofInputError("cases JSON must not contain a UTF-8 BOM")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ProofInputError("cases JSON must be strict UTF-8") from exc
    if "\r" in text:
        raise ProofInputError("cases JSON must use LF newlines only")
    data = json.loads(text, parse_constant=lambda value: (_ for _ in ()).throw(ProofInputError(value)))
    if type(data) is not dict or data.get("schema") != CASES_SCHEMA:
        raise ProofInputError("cases JSON schema mismatch")
    frozen = data.get("frozen_constants")
    required_frozen = {
        "eps64_hex": EPS64.hex(),
        "svd_factor": SVD_FACTOR,
        "residual_factor": RESIDUAL_FACTOR,
        "canonical_tie_factor": CANONICAL_TIE_FACTOR,
        "sensitivity_multipliers": list(SENSITIVITY_MULTIPLIERS),
    }
    if frozen != required_frozen:
        raise ProofInputError("cases JSON attempts to alter frozen numerical constants")
    algebraic = data.get("algebraic_cases")
    if type(algebraic) is not dict or set(algebraic) != {
        "quotient_counterexample",
        "inherited_scale_family",
    }:
        raise ProofInputError("cases JSON requires the two exact registered algebraic cases")
    hashes = data.get("source_hashes")
    if hashes != SOURCE_HASHES:
        raise ProofInputError("cases JSON source hashes differ from registered numerical sources")
    plan_hashes = data.get("plan_hashes")
    if plan_hashes != {
        "proof_plan": PLAN_SHA256,
        "vidar_editor_plan": EDITOR_PLAN_SHA256,
        "heimdall_auditor_plan": AUDITOR_PLAN_SHA256,
    }:
        raise ProofInputError("cases JSON plan hashes differ from registered plans")
    local = data.get("local_cases")
    topology = data.get("topology_cases")
    if type(local) is not list or type(topology) is not list:
        raise ProofInputError("cases JSON requires local_cases and topology_cases lists")
    identifiers: list[str] = []
    for case in [*local, *topology]:
        if type(case) is not dict or type(case.get("id")) is not str:
            raise ProofInputError("every case requires an actual-string id")
        identifiers.append(case["id"])
    if len(identifiers) != len(set(identifiers)):
        raise ProofInputError("case ids must be unique")
    data["cases_sha256"] = _sha256_bytes(raw)
    return data


def case_ids(data: Mapping[str, Any] | None = None) -> list[str]:
    cases = load_cases() if data is None else data
    result: list[str] = [
        cases["algebraic_cases"]["quotient_counterexample"]["id"],
        cases["algebraic_cases"]["inherited_scale_family"]["id"],
    ]
    for local in cases["local_cases"]:
        result.append(local["id"])
        for variant in local.get("numbering_variants", []):
            result.append(f"{local['id']}::{variant['id']}")
    result.extend(case["id"] for case in cases["topology_cases"])
    return result


def algebraic_regressions(cases: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Run the frozen quotient and inherited-scale counterexamples."""

    specifications = cases["algebraic_cases"]
    quotient = specifications["quotient_counterexample"]
    n_projector = _finite_array(quotient["N_projector"], (2, 2), "N_projector")
    g_basis = _finite_array(quotient["G_basis"], (2, 1), "G_basis")
    rn_basis = _finite_array(quotient["R_N_basis"], (2, 1), "R_N_basis")
    if equality_residual(rn_basis.T @ rn_basis, np.eye(1)) > residual_tolerance(2, 1):
        raise RuntimeError("frozen quotient counterexample R_N basis is not orthonormal")
    p_g = _symmetrize(g_basis @ g_basis.T)
    p_p = _symmetrize(n_projector - p_g)
    p_rn = _symmetrize(rn_basis @ rn_basis.T)
    quotient_variants: dict[str, Any] = {}
    for multiplier in SENSITIVITY_MULTIPLIERS:
        p_rn_p, dim_rn_p, _ = augmented_intersection(
            p_rn, 1, p_p, 1, multiplier
        )
        reverse, reverse_dimension, _ = augmented_intersection(
            p_p, 1, p_rn, 1, multiplier
        )
        commutativity = equality_residual(p_rn_p, reverse)
        if reverse_dimension != dim_rn_p or commutativity > residual_tolerance(2, 2):
            raise RuntimeError("augmented intersection is not commutative")
        _, dim_rg, _ = augmented_intersection(p_rn, 1, p_g, 1, multiplier)
        y_r = p_p @ canonical_basis(p_rn, 1)
        p_rq, dim_rq, y_rank = range_projector_inherited(y_r, 1.0, multiplier)
        p_z = _symmetrize(p_p - p_rq)
        dim_z = int(rank_kernel(p_z, multiplier)["rank"])
        observed = {
            "R_N_intersect_P": dim_rn_p,
            "R_N_intersect_G": dim_rg,
            "RQ": dim_rq,
            "Z": dim_z,
        }
        if observed != quotient["expected"]:
            raise RuntimeError(f"quotient counterexample differs from frozen result: {observed!r}")
        if dim_rq != 1 - dim_rg:
            raise RuntimeError("quotient counterexample rank-nullity identity failed")
        for projector, dimension in (
            (p_rn_p, dim_rn_p),
            (p_rq, dim_rq),
            (p_z, dim_z),
        ):
            _projector_gate(projector, dimension)
        quotient_variants[_float_token(multiplier)] = {
            "dimensions": observed,
            "intersection_commutativity": commutativity,
            "Y_R_tau": y_rank["tau"],
            "Y_R_parent_scale": y_rank["parent_scale"],
        }

    scale = specifications["inherited_scale_family"]
    q = _finite_array(scale["Q"], (2, 1), "inherited_scale.Q")
    parent_scale = _positive_float(scale["parent_scale"], "inherited_scale.parent_scale")
    deltas = [float.fromhex(value) for value in scale["deltas_hex"]]
    expected_ranks = scale["expected_ranks"]
    if expected_ranks != [0, 0, 1, 1]:
        raise ProofInputError("inherited-scale expected ranks are not the registered sequence")
    family_results: list[dict[str, Any]] = []
    for delta, delta_hex, expected in zip(deltas, scale["deltas_hex"], expected_ranks):
        operator = np.diag(np.array([1.0, delta], dtype=np.float64))
        restriction = operator @ q
        variants: dict[str, Any] = {}
        for multiplier in SENSITIVITY_MULTIPLIERS:
            decision = rank_kernel_inherited(restriction, parent_scale, multiplier)
            if decision["rank"] != expected:
                raise RuntimeError(
                    f"inherited-scale rank for {delta_hex} at {multiplier} is "
                    f"{decision['rank']}, expected {expected}"
                )
            variants[_float_token(multiplier)] = {
                "rank": decision["rank"],
                "tau": decision["tau"],
                "parent_scale": decision["parent_scale"],
            }
        relative_rank = rank_kernel(restriction)["rank"]
        family_results.append(
            {
                "delta_hex": delta_hex,
                "expected_rank": expected,
                "sensitivity": variants,
                "relative_only_rank": relative_rank,
            }
        )
    if family_results[1]["relative_only_rank"] != 1:
        raise RuntimeError("near-zero family no longer detects the relative-only threshold failure")
    return [
        {
            "id": quotient["id"],
            "classification": "exact_algebraic_counterexample",
            "sensitivity": quotient_variants,
        },
        {
            "id": scale["id"],
            "classification": "frozen_inherited_scale_regression",
            "results": family_results,
        },
    ]


def run_proof(selected_ids: set[str] | None = None) -> dict[str, Any]:
    cases = load_cases()
    manifest, environment_digest = environment_manifest()
    algebraic_ids = {
        item["id"] for item in cases["algebraic_cases"].values()
    }
    algebraic_results = (
        algebraic_regressions(cases)
        if selected_ids is None or selected_ids.intersection(algebraic_ids)
        else []
    )
    if selected_ids is not None:
        algebraic_results = [item for item in algebraic_results if item["id"] in selected_ids]
    local_results: list[dict[str, Any]] = []
    topology_results: list[dict[str, Any]] = []
    numbering: list[dict[str, Any]] = []
    for local in cases["local_cases"]:
        base_model = {
            "id": local["id"],
            "kind": "local",
            "coordinates": local["coordinates"],
            "directors": local["directors"],
            "thickness": local["thickness"],
            "elements": [{"nodes": [0, 1, 2, 3], "state": "active"}],
            "expected": local.get("expected", {}),
            "notes": local.get("notes", []),
        }
        base_result: dict[str, Any] | None = None
        if selected_ids is None or local["id"] in selected_ids or any(
            f"{local['id']}::{variant['id']}" in selected_ids
            for variant in local.get("numbering_variants", [])
        ):
            base_result = analyze_model(base_model, environment_digest)
            if selected_ids is None or local["id"] in selected_ids:
                local_results.append(base_result)
        for variant in local.get("numbering_variants", []):
            variant_id = f"{local['id']}::{variant['id']}"
            if selected_ids is not None and variant_id not in selected_ids:
                continue
            if base_result is None:
                base_result = analyze_model(base_model, environment_digest)
            variant_result = analyze_model(_permuted_local_model(local, variant), environment_digest)
            local_results.append(variant_result)
            numbering.append(_numbering_comparison(base_result, variant_result, variant))
    for topology in cases["topology_cases"]:
        if selected_ids is None or topology["id"] in selected_ids:
            topology_results.append(analyze_model(topology, environment_digest))

    unknown = set() if selected_ids is None else selected_ids.difference(case_ids(cases))
    if unknown:
        raise ProofInputError(f"unknown case ids: {sorted(unknown)!r}")
    return {
        "schema": SCHEMA,
        "classification": {
            "exact_theorem": [
                "G is the invariant intersection ker(B_w) intersect ker(H_w).",
                "Pi_P is the registered-metric quotient representative Pi_N-Pi_G.",
                "Pi_RQ is the image of R_N in the registered quotient representative P; Pi_Z=Pi_P-Pi_RQ.",
            ],
            "deterministic_evidence": [
                "All ranks and projectors use the frozen binary64 SVD/residual calculus.",
                "Snapshot hashes are comparable only when complete environment digests match.",
            ],
            "later_physical_authority": [
                "Whether a gauge is constrained or reduced.",
                "Whether any positive-mass mechanism receives a separately derived energetic formulation.",
            ],
            "unresolved": [
                "No rank-policy option is selected by this proof.",
                "Abstract coupling rows are not production coupling validation.",
            ],
        },
        "snapshot_digest_available": environment_digest is not None,
        "environment_manifest": manifest,
        "environment_manifest_sha256": environment_digest,
        "source_hashes": SOURCE_HASHES,
        "plan_hashes": cases["plan_hashes"],
        "cases_sha256": cases["cases_sha256"],
        "algebraic_cases": algebraic_results,
        "local_cases": local_results,
        "topology_cases": topology_results,
        "numbering_invariance": numbering,
    }


def proof_summary(result: Mapping[str, Any]) -> dict[str, Any]:
    def summarize_case(case: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "id": case["id"],
            "kind": case["kind"],
            "nodes": case["node_count"],
            "retained_elements": case["retained_element_count"],
            "components": case["components"],
            "orphan_nodes": case["orphans"]["nodes"],
            "bipartite": case["bipartite"],
            "rank": case["free"]["rank"],
            "dimensions": case["free"]["dimensions"],
            "sensitivity_stable": case["free"]["sensitivity_stable"],
            "drill_dimensions": case["drill"]["partition"]["dimensions"],
            "constant_drill": case["drill"]["constant_candidates"],
            "checkerboard": case["drill"]["checkerboard_candidates"],
            "constraints": [
                {
                    "id": constraint["id"],
                    "rank": constraint["rank"],
                    "dimensions": constraint["dimensions"],
                    "constraint_rank": constraint["constraint_rank"],
                    "feasible": constraint["feasibility"]["feasible"],
                    "sensitivity_stable": constraint["sensitivity_stable"],
                }
                for constraint in case["constraints"]
            ],
        }

    return {
        "schema": SCHEMA,
        "snapshot_digest_available": result["snapshot_digest_available"],
        "environment_manifest_sha256": result["environment_manifest_sha256"],
        "cases_sha256": result["cases_sha256"],
        "source_hashes": result["source_hashes"],
        "algebraic_cases": result["algebraic_cases"],
        "local_cases": [summarize_case(case) for case in result["local_cases"]],
        "topology_cases": [summarize_case(case) for case in result["topology_cases"]],
        "numbering_invariance": result["numbering_invariance"],
        "classification": result["classification"],
    }


def _main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true", help="list frozen case ids")
    parser.add_argument("--case", action="append", default=[], help="run one frozen case id")
    parser.add_argument("--full", action="store_true", help="emit full unquantized projector evidence")
    arguments = parser.parse_args(argv)
    if arguments.list:
        sys.stdout.buffer.write(canonical_json_bytes({"case_ids": case_ids()}))
        return 0
    result = run_proof(set(arguments.case) if arguments.case else None)
    output = result if arguments.full else proof_summary(result)
    sys.stdout.buffer.write(canonical_json_bytes(output))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
