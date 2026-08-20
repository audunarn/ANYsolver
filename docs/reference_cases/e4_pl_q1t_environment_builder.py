#!/usr/bin/env python3
"""Build the frozen, external E4-PL-Q1T exact-research environment.

This plan-stage utility is deliberately mechanics-blind.  It accepts exactly the
two preregistered wheels, validates their archives and RECORD files, extracts
them into a new directory outside a Git worktree, and emits a canonical record.
It never installs a package and never imports ANYsolver shell code.
"""

from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import importlib.metadata
import io
import json
import os
from pathlib import Path, PurePosixPath
import stat
import sys
import zipfile


SCHEMA = "e4_pl_q1t_environment_record_v1"
STUDY_ID = "study_e4_pl_q1t.q1s_frozen_identity_exact_oracle_completion_v1"
CANDIDATE_ID = (
    "candidate_e4_pl_q1t.wg2020_numbered_frame_surface_pl_planar_linear_iso_v1"
)
EXPECTED_PYTHON = "3.13.9"
EXPECTED_PYTEST = "9.0.1"
WHEELS = {
    "mpmath-1.3.0-py3-none-any.whl": {
        "bytes": 536_198,
        "sha256": "a0b2b9fe80bbcd81a6647ff13108738cfb482d481d826cc0e02f5b35e5c88d2c",
        "distribution": "mpmath",
        "version": "1.3.0",
        "role": "sympy_import_dependency_only",
    },
    "sympy-1.14.0-py3-none-any.whl": {
        "bytes": 6_299_353,
        "sha256": "e091cc3e99d2141a0ba2847328f5479b05d94a6635cb96148ccb3f34671bd8f5",
        "distribution": "sympy",
        "version": "1.14.0",
        "role": "exact_oracle_backend",
    },
}


class BuildError(RuntimeError):
    """A frozen authority or archive-safety condition was not met."""


def _canonical_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True,
                   separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _regular_nonlink(path: Path, label: str) -> Path:
    try:
        info = path.lstat()
    except FileNotFoundError as exc:
        raise BuildError(f"missing {label}: {path.name}") from exc
    if path.is_symlink() or not stat.S_ISREG(info.st_mode):
        raise BuildError(f"{label} is not a regular non-symlink file: {path.name}")
    resolved = path.resolve(strict=True)
    if Path(os.path.abspath(path)) != resolved:
        raise BuildError(f"{label} traverses a symlink or alias: {path.name}")
    return resolved


def _safe_member_name(name: str) -> str:
    if not name or "\\" in name or "\x00" in name:
        raise BuildError("wheel contains an empty, NUL, or backslash member")
    pure = PurePosixPath(name)
    if pure.is_absolute() or any(part in ("", ".", "..") for part in pure.parts):
        raise BuildError(f"wheel contains an unsafe member: {name!r}")
    if pure.parts and ":" in pure.parts[0]:
        raise BuildError(f"wheel contains a drive-like member: {name!r}")
    return pure.as_posix()


def _member_kind(info: zipfile.ZipInfo) -> str:
    mode = (info.external_attr >> 16) & 0xFFFF
    file_type = stat.S_IFMT(mode)
    if file_type == stat.S_IFLNK:
        raise BuildError(f"wheel contains a symlink member: {info.filename!r}")
    if info.is_dir():
        return "directory"
    # Some valid wheels record only permission bits (for example 0664) and no
    # POSIX file-type bits.  Accept that conventional form, but reject every
    # explicitly non-regular type.
    if file_type not in (0, stat.S_IFREG):
        raise BuildError(f"wheel contains a non-regular member: {info.filename!r}")
    if info.flag_bits & 0x1:
        raise BuildError(f"wheel contains an encrypted member: {info.filename!r}")
    return "file"


def _validated_archive(path: Path) -> tuple[list[zipfile.ZipInfo], str]:
    try:
        archive = zipfile.ZipFile(path, "r")
    except zipfile.BadZipFile as exc:
        raise BuildError(f"invalid wheel archive: {path.name}") from exc
    with archive:
        infos = archive.infolist()
        seen: set[str] = set()
        record_names: list[str] = []
        for info in infos:
            name = _safe_member_name(info.filename)
            if name in seen:
                raise BuildError(f"duplicate wheel member: {name}")
            seen.add(name)
            if _member_kind(info) == "file" and name.endswith(".dist-info/RECORD"):
                record_names.append(name)
        if len(record_names) != 1:
            raise BuildError(f"wheel must contain one RECORD: {path.name}")
        bad = archive.testzip()
        if bad is not None:
            raise BuildError(f"wheel CRC failure: {bad}")
    return infos, record_names[0]


def _inside_git_worktree(path: Path) -> bool:
    return any((parent / ".git").exists() for parent in (path, *path.parents))


def _fresh_external_root(path: Path) -> Path:
    absolute = Path(os.path.abspath(path))
    if absolute.exists():
        raise BuildError("environment root must not already exist")
    existing = absolute.parent
    while not existing.exists():
        if existing == existing.parent:
            raise BuildError("environment root has no existing ancestor")
        existing = existing.parent
    if existing.is_symlink() or existing.resolve(strict=True) != existing:
        raise BuildError("environment root ancestor traverses a symlink or alias")
    candidate = existing.joinpath(*absolute.relative_to(existing).parts)
    if _inside_git_worktree(candidate):
        raise BuildError("environment root must be outside every Git worktree")
    candidate.mkdir(parents=True, exist_ok=False)
    return candidate.resolve(strict=True)


def _wheel_inputs(sympy_wheel: Path, mpmath_wheel: Path) -> dict[str, Path]:
    supplied = [sympy_wheel, mpmath_wheel]
    if len({path.name for path in supplied}) != 2:
        raise BuildError("exactly the two distinct frozen wheels are required")
    by_name: dict[str, Path] = {}
    for path in supplied:
        if path.name not in WHEELS:
            raise BuildError(f"unregistered wheel filename: {path.name}")
        resolved = _regular_nonlink(path, "wheel")
        expected = WHEELS[path.name]
        if resolved.stat().st_size != expected["bytes"]:
            raise BuildError(f"wheel byte-count mismatch: {path.name}")
        if _sha256_file(resolved) != expected["sha256"]:
            raise BuildError(f"wheel SHA-256 mismatch: {path.name}")
        by_name[path.name] = resolved
    if set(by_name) != set(WHEELS):
        raise BuildError("the supplied wheel set is not the frozen two-wheel set")
    return by_name


def _extract(wheels: dict[str, Path], root: Path) -> dict[str, str]:
    # Validate the complete two-wheel archive set before writing the first
    # member.  A rejected second wheel therefore cannot leave a plausibly
    # usable partial environment.
    validated = {
        wheel_name: _validated_archive(wheels[wheel_name])
        for wheel_name in sorted(wheels)
    }
    record_names: dict[str, str] = {
        wheel_name: validated[wheel_name][1]
        for wheel_name in sorted(wheels)
    }
    extracted: set[str] = set()
    for wheel_name in sorted(wheels):
        infos, _record_name = validated[wheel_name]
        with zipfile.ZipFile(wheels[wheel_name], "r") as archive:
            for info in infos:
                name = _safe_member_name(info.filename)
                target = root.joinpath(*PurePosixPath(name).parts)
                target_parent = target.parent
                target_parent.mkdir(parents=True, exist_ok=True)
                if not target_parent.resolve(strict=True).is_relative_to(root):
                    raise BuildError(f"member escapes environment root: {name}")
                kind = _member_kind(info)
                if kind == "directory":
                    target.mkdir(exist_ok=True)
                    continue
                if name in extracted or target.exists():
                    raise BuildError(f"wheel file collision: {name}")
                with archive.open(info, "r") as source, target.open("xb") as sink:
                    for chunk in iter(lambda: source.read(1024 * 1024), b""):
                        sink.write(chunk)
                if target.is_symlink() or not target.is_file():
                    raise BuildError(f"extraction did not create a regular file: {name}")
                extracted.add(name)
    return record_names


def _record_digest(value: str) -> bytes:
    algorithm, separator, encoded = value.partition("=")
    if algorithm != "sha256" or separator != "=" or not encoded:
        raise BuildError("RECORD permits only populated sha256 hashes")
    encoded += "=" * (-len(encoded) % 4)
    try:
        return base64.urlsafe_b64decode(encoded.encode("ascii"))
    except (ValueError, UnicodeEncodeError) as exc:
        raise BuildError("invalid RECORD sha256 encoding") from exc


def _validate_records(
    root: Path, wheels: dict[str, Path], record_names: dict[str, str]
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for wheel_name in sorted(wheels):
        record_name = record_names[wheel_name]
        with zipfile.ZipFile(wheels[wheel_name], "r") as archive:
            archive_files = {
                _safe_member_name(info.filename)
                for info in archive.infolist()
                if _member_kind(info) == "file"
            }
        record_path = root.joinpath(*PurePosixPath(record_name).parts)
        rows = list(csv.reader(io.StringIO(record_path.read_text(encoding="utf-8"))))
        observed: set[str] = set()
        for row in rows:
            if len(row) != 3:
                raise BuildError(f"malformed RECORD row in {wheel_name}")
            name = _safe_member_name(row[0])
            if name in observed:
                raise BuildError(f"duplicate RECORD row: {name}")
            observed.add(name)
            path = root.joinpath(*PurePosixPath(name).parts)
            if name == record_name:
                if row[1] or row[2]:
                    raise BuildError("RECORD self-row must have empty hash and size")
            else:
                if not row[1] or not row[2]:
                    raise BuildError(f"unhashed RECORD file: {name}")
                try:
                    expected_size = int(row[2])
                except ValueError as exc:
                    raise BuildError(f"invalid RECORD size: {name}") from exc
                data = path.read_bytes()
                if len(data) != expected_size:
                    raise BuildError(f"RECORD size mismatch: {name}")
                if hashlib.sha256(data).digest() != _record_digest(row[1]):
                    raise BuildError(f"RECORD hash mismatch: {name}")
        if observed != archive_files:
            missing = sorted(archive_files - observed)
            surplus = sorted(observed - archive_files)
            raise BuildError(f"RECORD/archive extent mismatch: {missing!r} {surplus!r}")
        counts[wheel_name] = len(observed)
    return counts


def _toy_sympy_probes(root: Path) -> dict[str, bool]:
    sys.path.insert(0, str(root))
    # The builder is a one-shot process.  Keep this set through lazy imports
    # triggered by the probes as well as the initial SymPy import so the exact
    # extracted-file graph cannot acquire runtime-created ``.pyc`` files.
    sys.dont_write_bytecode = True
    try:
        import sympy  # type: ignore[import-not-found]
        from sympy import Matrix, QQ, sqrt  # type: ignore[import-not-found]
    finally:
        if sys.path[0] == str(root):
            sys.path.pop(0)
    module_path = Path(sympy.__file__).resolve(strict=True)
    if not module_path.is_relative_to(root):
        raise BuildError("SymPy was not imported from the extracted environment")
    if sympy.__version__ != "1.14.0":
        raise BuildError("extracted SymPy version mismatch")
    mpmath_module = sys.modules.get("mpmath")
    if mpmath_module is None or not Path(mpmath_module.__file__).resolve(strict=True).is_relative_to(root):
        raise BuildError("mpmath dependency was not imported from the extracted environment")
    if getattr(mpmath_module, "__version__", None) != "1.3.0":
        raise BuildError("extracted mpmath version mismatch")

    nested = sqrt(1 + sqrt(2))
    field = QQ.algebraic_field(sqrt(2), nested, sqrt(3))
    a = field.from_sympy(nested)
    b = field.from_sympy(sqrt(2))
    one = field.one
    zero = field.zero
    exact_cancellation = (a - a) == zero and (b * b - field(2)) == zero
    exact_inverse = a * (one / a) == one
    nested_positive_root = a * a == one + b
    exact_rank = Matrix([[1, nested], [nested, 1 + sqrt(2)]]).rank() == 1
    serialized_a = str(field.to_sympy(a))
    deterministic_serialization = serialized_a == str(field.to_sympy(a))

    forbidden_prefixes = ("anysolver", "src", "shell_element")
    shell_imports_absent = not any(
        name == prefix or name.startswith(prefix + ".")
        for name in sys.modules
        for prefix in forbidden_prefixes
    )
    probes = {
        "deterministic_symbolic_serialization": deterministic_serialization,
        "exact_domain_cancellation": exact_cancellation,
        "exact_domain_inverse": exact_inverse,
        "exact_matrix_rank": exact_rank,
        "nested_positive_algebraic_radicand": nested_positive_root,
        "shell_mechanics_imports_absent": shell_imports_absent,
    }
    if not all(probes.values()):
        raise BuildError(f"toy SymPy capability probe failed: {probes!r}")
    return probes


def _file_graph(root: Path) -> list[dict[str, object]]:
    graph: list[dict[str, object]] = []
    for path in sorted((item for item in root.rglob("*") if item.is_file()),
                       key=lambda item: item.relative_to(root).as_posix()):
        if path.is_symlink():
            raise BuildError("extracted file graph contains a symlink")
        graph.append({
            "bytes": path.stat().st_size,
            "path": path.relative_to(root).as_posix(),
            "sha256": _sha256_file(path),
        })
    return graph


def build(sympy_wheel: Path, mpmath_wheel: Path, environment_root: Path) -> dict[str, object]:
    if sys.implementation.name != "cpython" or sys.version.split()[0] != EXPECTED_PYTHON:
        raise BuildError(f"requires CPython {EXPECTED_PYTHON}")
    try:
        pytest_version = importlib.metadata.version("pytest")
    except importlib.metadata.PackageNotFoundError as exc:
        raise BuildError("pytest is not installed in the caller runtime") from exc
    if pytest_version != EXPECTED_PYTEST:
        raise BuildError(f"requires pytest {EXPECTED_PYTEST}")

    wheels = _wheel_inputs(sympy_wheel, mpmath_wheel)
    root = _fresh_external_root(environment_root)
    record_names = _extract(wheels, root)
    record_counts = _validate_records(root, wheels, record_names)
    probes = _toy_sympy_probes(root)
    graph = _file_graph(root)
    expected_file_count = sum(record_counts.values())
    if len(graph) != expected_file_count:
        raise BuildError(
            "environment file extent changed after RECORD validation: "
            f"expected {expected_file_count}, observed {len(graph)}"
        )
    graph_bytes = _canonical_bytes(graph)
    wheel_rows = []
    for name in sorted(wheels):
        expected = WHEELS[name]
        wheel_rows.append({
            "bytes": expected["bytes"],
            "distribution": expected["distribution"],
            "filename": name,
            "record_file_count": record_counts[name],
            "role": expected["role"],
            "sha256": expected["sha256"],
            "version": expected["version"],
        })
    return {
        "absolute_paths_recorded": False,
        "candidate_id": CANDIDATE_ID,
        "environment_id": "e4_pl_q1t_external_exact_environment_v1",
        "extracted_file_count": len(graph),
        "extracted_file_hash_graph": graph,
        "extracted_file_hash_graph_sha256": _sha256_bytes(graph_bytes),
        "mpmath_categorical_evidence_permitted": False,
        "runtime": {
            "implementation": "CPython",
            "pytest": pytest_version,
            "python": EXPECTED_PYTHON,
        },
        "schema": SCHEMA,
        "study_id": STUDY_ID,
        "toy_sympy_capability_probes": probes,
        "wheels": wheel_rows,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sympy-wheel", type=Path, required=True)
    parser.add_argument("--mpmath-wheel", type=Path, required=True)
    parser.add_argument("--environment-root", type=Path, required=True)
    parser.add_argument("--record-out", type=Path, required=True)
    args = parser.parse_args(argv)
    record_out = Path(os.path.abspath(args.record_out))
    environment_root = Path(os.path.abspath(args.environment_root))
    if record_out == environment_root or record_out.is_relative_to(environment_root):
        raise BuildError("record output must be separate from the environment root")
    if record_out.exists() or record_out.is_symlink():
        raise BuildError("record output must not already exist")
    record_out.parent.mkdir(parents=True, exist_ok=True)
    record = build(args.sympy_wheel, args.mpmath_wheel, environment_root)
    payload = _canonical_bytes(record)
    with record_out.open("xb") as stream:
        stream.write(payload)
    print(json.dumps({
        "environment_record_sha256": _sha256_bytes(payload),
        "extracted_file_count": record["extracted_file_count"],
        "schema": SCHEMA,
    }, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BuildError as exc:
        print(f"Q1T environment build rejected: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
