"""V6M preparation-safe validator correction for the frozen V6L graph."""

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


SCHEMA = "anysolver.e4-pl-s3-v6m-stage4a-execution-graph-v1"
AUTHORIZATION_SCHEMA = "anysolver.e4-pl-s3-v6m-stage4a-execution-authorization-v1"
REFERENCE = Path(__file__).resolve().parent
BASE_PROGRAM = REFERENCE / "e4_pl_s3_v6l_stage4a_execution_graph.py"
BASE_PROGRAM_SHA256 = "16C8D6DB452AC5BC963DA9A6B9E93445248129C2EC12FA69692448683E197EE1"


class V6MError(RuntimeError):
    """Raised when the preparation-safe successor differs."""


def _sha256(path: Path) -> str:
    information = path.resolve().lstat()
    if not stat.S_ISREG(information.st_mode) or path.is_symlink():
        raise V6MError(f"program is not regular: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _load_base() -> ModuleType:
    if _sha256(BASE_PROGRAM) != BASE_PROGRAM_SHA256:
        raise V6MError("frozen V6L graph program differs")
    spec = importlib.util.spec_from_file_location("_s3_v6m_base_graph", BASE_PROGRAM)
    if spec is None or spec.loader is None:
        raise V6MError("cannot load frozen V6L graph program")
    module = importlib.util.module_from_spec(spec)
    sys.modules["_s3_v6m_base_graph"] = module
    spec.loader.exec_module(module)
    return module


_BASE = _load_base()
_V6K = _BASE._BASE
_V6I = _V6K._BASE
_PREPARATION_SAFE_VALIDATE = _V6K.validate_graph
_VALIDATOR_SCHEMA = _V6K.SCHEMA

canonical_bytes = _BASE.canonical_bytes
strict_json = _BASE.strict_json
sha256 = _BASE.sha256
verify_archive = _V6K.verify_archive
verify_support_archive = _BASE.verify_support_archive
ROOT = _V6I.ROOT
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
    return _sha256(Path(__file__))


def _as_validator_graph(value: Mapping[str, Any]) -> dict[str, Any]:
    made = copy.deepcopy(dict(value))
    made["schema"] = _VALIDATOR_SCHEMA
    return made


def validate_graph(value: Mapping[str, Any]) -> None:
    if (
        value.get("schema") != SCHEMA
        or value.get("leaf_count") != LEAF_COUNT
        or value.get("wave_count") != WAVE_COUNT
    ):
        raise V6MError("V6M graph schema or coverage differs")
    policy = value.get("runtime_policy")
    if not isinstance(policy, dict) or policy.get("maximum_concurrent_workers") != MAXIMUM_CONCURRENT_WORKERS:
        raise V6MError("V6M concurrency policy differs")
    _PREPARATION_SAFE_VALIDATE(_as_validator_graph(value))


def build_graph(candidate_archive: Path) -> dict[str, Any]:
    verify_support_archive()
    previous_hash = _V6K._program_sha256
    try:
        _V6K._program_sha256 = _program_sha256
        made = _V6K.build_graph(candidate_archive)
    finally:
        _V6K._program_sha256 = previous_hash
    made["schema"] = SCHEMA
    made["terminal"] = "VALIDATED_V6M_STAGE4A_GRAPH_NOT_EXECUTED"
    validate_graph(made)
    return made


def _prepare_execution_base() -> None:
    _BASE.__file__ = str(Path(__file__).resolve())
    _BASE._program_sha256 = _program_sha256
    _BASE.validate_graph = validate_graph
    _BASE.AUTHORIZATION_SCHEMA = AUTHORIZATION_SCHEMA
    _BASE._prepare_execution_base()


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
    _BASE._BASE_PUBLISH(path, raw)


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
            raise V6MError("graph construction requires archive and output")
        _publish_exclusive(args.output.resolve(), canonical_bytes(build_graph(args.candidate_archive)))
        return 0
    if args.validate_graph:
        if args.graph is None:
            raise V6MError("graph validation requires --graph")
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
        raise V6MError("registered wave execution arguments are incomplete")
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
