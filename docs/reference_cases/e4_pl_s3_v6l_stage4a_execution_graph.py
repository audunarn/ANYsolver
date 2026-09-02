"""V6L isolated dependency-closure correction for the frozen V6K graph.

The scientific graph and two-worker concurrency policy remain unchanged.  A
commit-bound ANYfileIO source archive is added to each fresh candidate source
tree before the unchanged leaf producer imports ANYsolver.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import stat
import sys
import tarfile
from types import ModuleType
from typing import Any, Mapping, Sequence


SCHEMA = "anysolver.e4-pl-s3-v6l-stage4a-execution-graph-v1"
AUTHORIZATION_SCHEMA = "anysolver.e4-pl-s3-v6l-stage4a-execution-authorization-v1"
REFERENCE = Path(__file__).resolve().parent
BASE_PROGRAM = REFERENCE / "e4_pl_s3_v6k_stage4a_execution_graph.py"
BASE_PROGRAM_SHA256 = "E1F369E2035EE2A3D4F613195F307D78BB81AA473FA91FD71FC7BFD801C48026"
SUPPORT_ARCHIVE = Path(
    r"C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease"
    r"\s3-v2d-stage4a-v6l-dependency-closure\anyfileio-source.tar"
)
SUPPORT_ARCHIVE_BYTES = 389_120
SUPPORT_ARCHIVE_SHA256 = "ABDFD6F6B6E04185FD277E4EE80400FA05B702BD43BA50851C4F9E85A5970C90"
SUPPORT_COMMIT = "9b1e5adea77a20155bbc23866af8c9aad853ddfd"
SUPPORT_TREE = "70b406be2574adceab4a7b688c0e489e0937df5d"


class V6LError(RuntimeError):
    """Raised when dependency closure or predecessor authority differs."""


def _regular_bytes(path: Path, role: str) -> bytes:
    resolved = path.resolve()
    information = resolved.lstat()
    if not stat.S_ISREG(information.st_mode) or path.is_symlink():
        raise V6LError(f"{role} is not a regular non-link file")
    return resolved.read_bytes()


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def _load_base() -> ModuleType:
    if _sha256(_regular_bytes(BASE_PROGRAM, "frozen V6K program")) != BASE_PROGRAM_SHA256:
        raise V6LError("frozen V6K graph program differs")
    spec = importlib.util.spec_from_file_location("_s3_v6l_base_graph", BASE_PROGRAM)
    if spec is None or spec.loader is None:
        raise V6LError("cannot load frozen V6K graph program")
    module = importlib.util.module_from_spec(spec)
    sys.modules["_s3_v6l_base_graph"] = module
    spec.loader.exec_module(module)
    return module


_BASE = _load_base()
_EXECUTION_BASE = _BASE._BASE
_BASE_SCHEMA = _BASE.SCHEMA
_BASE_EXTRACT = _EXECUTION_BASE._extract_archive_exclusive
_BASE_PUBLISH = _EXECUTION_BASE._publish_exclusive

canonical_bytes = _BASE.canonical_bytes
strict_json = _BASE.strict_json
sha256 = _BASE.sha256
CANDIDATE_ARCHIVE_BYTES = _BASE.CANDIDATE_ARCHIVE_BYTES
CANDIDATE_ARCHIVE_SHA256 = _BASE.CANDIDATE_ARCHIVE_SHA256
CANDIDATE_COMMIT = _BASE.CANDIDATE_COMMIT
CANDIDATE_TREE = _BASE.CANDIDATE_TREE
WAVE_COUNT = _BASE.WAVE_COUNT
LEAF_COUNT = _BASE.LEAF_COUNT
CHILD_WALL_SECONDS = _BASE.CHILD_WALL_SECONDS
WAVE_WALL_SECONDS = _BASE.WAVE_WALL_SECONDS
MEMORY_LIMIT_GIB = _BASE.MEMORY_LIMIT_GIB
MAXIMUM_CONCURRENT_WORKERS = _BASE.MAXIMUM_CONCURRENT_WORKERS
REGISTERED_WORKERS_PER_WAVE = _BASE.REGISTERED_WORKERS_PER_WAVE


def _program_sha256() -> str:
    return _sha256(_regular_bytes(Path(__file__), "V6L graph/executor"))


def verify_support_archive() -> list[tarfile.TarInfo]:
    raw = _regular_bytes(SUPPORT_ARCHIVE, "ANYfileIO support archive")
    if len(raw) != SUPPORT_ARCHIVE_BYTES or _sha256(raw) != SUPPORT_ARCHIVE_SHA256:
        raise V6LError("ANYfileIO support archive identity differs")
    members: list[tarfile.TarInfo] = []
    seen: set[str] = set()
    required_file = False
    with tarfile.open(SUPPORT_ARCHIVE.resolve(), mode="r:") as bundle:
        for member in bundle.getmembers():
            name = member.name.rstrip("/")
            if not name:
                continue
            pure = Path(name.replace("/", os.sep))
            canonical = "/".join(pure.parts)
            folded = canonical.casefold()
            allowed = canonical == "src" or canonical.startswith("src/anyfileio")
            if (
                pure.is_absolute()
                or any(part in {"", ".", ".."} for part in pure.parts)
                or folded in seen
                or not allowed
                or not (member.isdir() or member.isfile())
            ):
                raise V6LError("ANYfileIO support archive has an unsafe member")
            seen.add(folded)
            members.append(member)
            required_file = required_file or canonical == "src/anyfileio/calculix/__init__.py"
    if not members or not required_file:
        raise V6LError("ANYfileIO support archive is incomplete")
    return members


def _extract_candidate_and_support(archive: Path, destination: Path) -> None:
    _BASE_EXTRACT(archive, destination)
    verify_support_archive()
    destination = destination.resolve()
    support_destination = destination.parent / "support-source"
    support_destination.mkdir(parents=False, exist_ok=False)
    with tarfile.open(SUPPORT_ARCHIVE.resolve(), mode="r:") as bundle:
        for member in bundle.getmembers():
            name = member.name.rstrip("/")
            if not name:
                continue
            pure = Path(name.replace("/", os.sep))
            target = support_destination.joinpath(*pure.parts).resolve()
            try:
                target.relative_to(support_destination)
            except ValueError as exc:
                raise V6LError("support extraction escapes candidate source") from exc
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            source = bundle.extractfile(member)
            if source is None:
                raise V6LError("support archive member is unreadable")
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as handle:
                shutil.copyfileobj(source, handle, length=1 << 20)
    support_source = support_destination / "src"
    if not support_source.is_dir() or support_source.is_symlink():
        raise V6LError("extracted ANYfileIO support source differs")
    sys.path.insert(0, str(support_source.resolve()))


def _publish_with_support_binding(path: Path, raw: bytes) -> None:
    if path.name == "bounded-manifest.json":
        value = json.loads(raw)
        binding = {
            "path": str(SUPPORT_ARCHIVE.resolve()),
            "sha256": SUPPORT_ARCHIVE_SHA256,
        }
        for worker in value["workers"]:
            worker["input_hashes"].append(binding.copy())
            worker["input_hashes"].sort(key=lambda item: item["path"])
        raw = canonical_bytes(value)
    _BASE_PUBLISH(path, raw)


def _as_base_graph(value: Mapping[str, Any]) -> dict[str, Any]:
    made = copy.deepcopy(dict(value))
    made["schema"] = _BASE_SCHEMA
    return made


def validate_graph(value: Mapping[str, Any]) -> None:
    if (
        value.get("schema") != SCHEMA
        or value.get("leaf_count") != LEAF_COUNT
        or value.get("wave_count") != WAVE_COUNT
    ):
        raise V6LError("V6L graph schema or coverage differs")
    policy = value.get("runtime_policy")
    if not isinstance(policy, dict) or policy.get("maximum_concurrent_workers") != MAXIMUM_CONCURRENT_WORKERS:
        raise V6LError("V6L concurrency policy differs")
    previous_schema = _BASE.SCHEMA
    try:
        _BASE.SCHEMA = _BASE_SCHEMA
        _BASE.validate_graph(_as_base_graph(value))
    finally:
        _BASE.SCHEMA = previous_schema


def build_graph(candidate_archive: Path) -> dict[str, Any]:
    verify_support_archive()
    previous_hash = _BASE._program_sha256
    try:
        _BASE._program_sha256 = _program_sha256
        made = _BASE.build_graph(candidate_archive)
    finally:
        _BASE._program_sha256 = previous_hash
    made["schema"] = SCHEMA
    made["terminal"] = "VALIDATED_V6L_STAGE4A_GRAPH_NOT_EXECUTED"
    validate_graph(made)
    return made


def _prepare_execution_base() -> None:
    verify_support_archive()
    _BASE.__file__ = str(Path(__file__).resolve())
    _BASE._program_sha256 = _program_sha256
    _BASE.validate_graph = validate_graph
    _BASE.AUTHORIZATION_SCHEMA = AUTHORIZATION_SCHEMA
    _EXECUTION_BASE._extract_archive_exclusive = _extract_candidate_and_support
    _EXECUTION_BASE._publish_exclusive = _publish_with_support_binding


def registered_command(**arguments: Any) -> str:
    _prepare_execution_base()
    return str(_BASE.registered_command(**arguments))


def run_flat_leaf(argv: Sequence[str]) -> int:
    _prepare_execution_base()
    return int(_BASE.run_flat_leaf(argv))


def run_registered_wave(
    graph_path: Path,
    wave_index: int,
    candidate_archive: Path,
    output_root: Path,
    authorization_path: Path,
    request_path: Path,
    result_path: Path,
) -> dict[str, Any]:
    _prepare_execution_base()
    return dict(
        _BASE.run_registered_wave(
            graph_path,
            wave_index,
            candidate_archive,
            output_root,
            authorization_path,
            request_path,
            result_path,
        )
    )


def _publish_exclusive(path: Path, raw: bytes) -> None:
    _BASE_PUBLISH(path, raw)


def main(argv: Sequence[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments and arguments[0] == "--run-flat-leaf":
        return run_flat_leaf(arguments)
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--build-graph", action="store_true")
    mode.add_argument("--validate-graph", action="store_true")
    mode.add_argument("--run-registered-wave", action="store_true")
    parser.add_argument("--candidate-archive", type=Path)
    parser.add_argument("--graph", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--authorization", type=Path)
    parser.add_argument("--request", type=Path)
    parser.add_argument("--result", type=Path)
    parser.add_argument("--wave-index", type=int)
    args = parser.parse_args(arguments)
    if args.build_graph:
        if args.candidate_archive is None or args.output is None:
            raise V6LError("graph construction requires archive and output")
        _publish_exclusive(args.output.resolve(), canonical_bytes(build_graph(args.candidate_archive)))
        return 0
    if args.validate_graph:
        if args.graph is None:
            raise V6LError("graph validation requires --graph")
        value, _ = strict_json(args.graph)
        validate_graph(value)
        return 0
    required = (
        args.graph,
        args.candidate_archive,
        args.output_root,
        args.authorization,
        args.request,
        args.result,
    )
    if any(item is None for item in required) or args.wave_index is None:
        raise V6LError("registered wave execution arguments are incomplete")
    made = run_registered_wave(
        args.graph,
        args.wave_index,
        args.candidate_archive,
        args.output_root,
        args.authorization,
        args.request,
        args.result,
    )
    return 0 if made["terminal"] == "COMPLETED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
