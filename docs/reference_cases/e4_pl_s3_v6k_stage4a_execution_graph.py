"""V6K resource-admission correction for the frozen V6I Stage-4A graph.

The scientific plan and three-leaf wave grouping remain unchanged.  At most
two of the three registered workers run concurrently; the third is queued.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
from pathlib import Path
import stat
import sys
from types import ModuleType
from typing import Any, Mapping, Sequence


SCHEMA = "anysolver.e4-pl-s3-v6k-stage4a-execution-graph-v1"
AUTHORIZATION_SCHEMA = "anysolver.e4-pl-s3-v6k-stage4a-execution-authorization-v1"
REFERENCE = Path(__file__).resolve().parent
BASE_PROGRAM = REFERENCE / "e4_pl_s3_v6i_stage4a_execution_graph.py"
BASE_PROGRAM_SHA256 = "327AF03B25FCE587125B2B64A5C72D32AC6A58D1A3E4EA98C5D6E316991559C1"
REGISTERED_WORKERS_PER_WAVE = 3
MAXIMUM_CONCURRENT_WORKERS = 2


class V6KError(RuntimeError):
    """Raised when the concurrency-only successor graph differs."""


def _sha256(path: Path) -> str:
    information = path.resolve().lstat()
    if not stat.S_ISREG(information.st_mode) or path.is_symlink():
        raise V6KError(f"program is not regular: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _load_base() -> ModuleType:
    if _sha256(BASE_PROGRAM) != BASE_PROGRAM_SHA256:
        raise V6KError("frozen V6I graph program differs")
    spec = importlib.util.spec_from_file_location("_s3_v6k_base_graph", BASE_PROGRAM)
    if spec is None or spec.loader is None:
        raise V6KError("cannot load frozen V6I graph program")
    module = importlib.util.module_from_spec(spec)
    sys.modules["_s3_v6k_base_graph"] = module
    spec.loader.exec_module(module)
    return module


_BASE = _load_base()
_BASE_SCHEMA = _BASE.SCHEMA
_BASE_VALIDATE_GRAPH = _BASE.validate_graph


canonical_bytes = _BASE.canonical_bytes
strict_json = _BASE.strict_json
sha256 = _BASE.sha256
verify_archive = _BASE.verify_archive
CANDIDATE_ARCHIVE_BYTES = _BASE.CANDIDATE_ARCHIVE_BYTES
CANDIDATE_ARCHIVE_SHA256 = _BASE.CANDIDATE_ARCHIVE_SHA256
CANDIDATE_COMMIT = _BASE.CANDIDATE_COMMIT
CANDIDATE_TREE = _BASE.CANDIDATE_TREE
WAVE_COUNT = _BASE.WAVE_COUNT
LEAF_COUNT = _BASE.LEAF_COUNT
CHILD_WALL_SECONDS = _BASE.CHILD_WALL_SECONDS
WAVE_WALL_SECONDS = _BASE.WAVE_WALL_SECONDS
MEMORY_LIMIT_GIB = _BASE.MEMORY_LIMIT_GIB


def _program_sha256() -> str:
    return _sha256(Path(__file__))


def _as_base_graph(value: Mapping[str, Any]) -> dict[str, Any]:
    made = copy.deepcopy(dict(value))
    made["schema"] = _BASE_SCHEMA
    policy = made.get("runtime_policy")
    if not isinstance(policy, dict):
        raise V6KError("successor runtime policy is malformed")
    policy["maximum_concurrent_workers"] = REGISTERED_WORKERS_PER_WAVE
    return made


def validate_graph(value: Mapping[str, Any]) -> None:
    if (
        value.get("schema") != SCHEMA
        or value.get("leaf_count") != LEAF_COUNT
        or value.get("wave_count") != WAVE_COUNT
    ):
        raise V6KError("V6K graph schema or coverage differs")
    policy = value.get("runtime_policy")
    if not isinstance(policy, dict) or policy.get("maximum_concurrent_workers") != MAXIMUM_CONCURRENT_WORKERS:
        raise V6KError("V6K concurrency policy differs")
    previous_workers = _BASE.WORKERS_PER_WAVE
    previous_schema = _BASE.SCHEMA
    try:
        _BASE.WORKERS_PER_WAVE = REGISTERED_WORKERS_PER_WAVE
        _BASE.SCHEMA = _BASE_SCHEMA
        _BASE_VALIDATE_GRAPH(_as_base_graph(value))
    finally:
        _BASE.WORKERS_PER_WAVE = previous_workers
        _BASE.SCHEMA = previous_schema


def build_graph(candidate_archive: Path) -> dict[str, Any]:
    previous_hash = _BASE._program_sha256
    try:
        _BASE._program_sha256 = _program_sha256
        made = _BASE.build_graph(candidate_archive)
    finally:
        _BASE._program_sha256 = previous_hash
    made["schema"] = SCHEMA
    made["runtime_policy"]["maximum_concurrent_workers"] = MAXIMUM_CONCURRENT_WORKERS
    made["terminal"] = "VALIDATED_V6K_STAGE4A_GRAPH_NOT_EXECUTED"
    validate_graph(made)
    return made


def _prepare_execution_base() -> None:
    _BASE.__file__ = str(Path(__file__).resolve())
    _BASE._program_sha256 = _program_sha256
    _BASE.validate_graph = validate_graph
    _BASE.AUTHORIZATION_SCHEMA = AUTHORIZATION_SCHEMA
    _BASE.WORKERS_PER_WAVE = MAXIMUM_CONCURRENT_WORKERS


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
    _BASE._publish_exclusive(path, raw)


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
            raise V6KError("graph construction requires archive and output")
        _publish_exclusive(args.output.resolve(), canonical_bytes(build_graph(args.candidate_archive)))
        return 0
    if args.validate_graph:
        if args.graph is None:
            raise V6KError("graph validation requires --graph")
        value, _ = strict_json(args.graph)
        validate_graph(value)
        return 0
    required = (
        args.graph, args.candidate_archive, args.output_root,
        args.authorization, args.request, args.result,
    )
    if any(item is None for item in required) or args.wave_index is None:
        raise V6KError("registered wave execution arguments are incomplete")
    made = run_registered_wave(
        args.graph, args.wave_index, args.candidate_archive, args.output_root,
        args.authorization, args.request, args.result,
    )
    return 0 if made["terminal"] == "COMPLETED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
