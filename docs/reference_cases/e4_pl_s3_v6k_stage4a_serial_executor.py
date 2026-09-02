"""Serial V6K executor using fresh requests and two concurrent workers."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
from pathlib import Path
import sys
from types import ModuleType
from typing import Any, Sequence


REFERENCE = Path(__file__).resolve().parent
BASE_EXECUTOR = REFERENCE / "e4_pl_s3_v6j_stage4a_serial_executor.py"
BASE_EXECUTOR_SHA256 = "CDA84877351629981368DF7232CD101A8FA7AAC64A4D97E58784432353ADDA12"
AUTHORITY_PROGRAM = REFERENCE / "e4_pl_s3_v6k_stage4a_authority.py"
GRAPH_PROGRAM = REFERENCE / "e4_pl_s3_v6k_stage4a_execution_graph.py"
INCIDENT = REFERENCE / "e4_pl_s3_v6j_resource_deferred_incident.json"
INCIDENT_SHA256 = "A3BA33CF8F1C570F1171CF7299686FFC4F9035FDEA9A876E0FE25607AEA64706"


class V6KExecutionError(RuntimeError):
    """Raised when the V6K executor's frozen inputs differ."""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _load_base() -> ModuleType:
    if _sha256(BASE_EXECUTOR) != BASE_EXECUTOR_SHA256:
        raise V6KExecutionError("frozen V6J serial executor differs")
    spec = importlib.util.spec_from_file_location("_s3_v6k_base_executor", BASE_EXECUTOR)
    if spec is None or spec.loader is None:
        raise V6KExecutionError("cannot load V6J serial executor")
    module = importlib.util.module_from_spec(spec)
    sys.modules["_s3_v6k_base_executor"] = module
    spec.loader.exec_module(module)
    return module


_BASE = _load_base()
canonical_bytes = _BASE.canonical_bytes
strict_json = _BASE.strict_json
sha256 = _BASE.sha256


def _configure() -> None:
    if _sha256(INCIDENT) != INCIDENT_SHA256:
        raise V6KExecutionError("preserved V6J resource incident differs")
    _BASE.AUTHORITY_PROGRAM = AUTHORITY_PROGRAM
    _BASE.GRAPH_PROGRAM = GRAPH_PROGRAM


def validate_authorization(
    authorization_path: Path, graph_path: Path, archive: Path
) -> tuple[dict[str, Any], bytes, dict[str, Any], bytes]:
    _configure()
    return _BASE.validate_authorization(authorization_path, graph_path, archive)


def approve_all(authorization_path: Path, graph_path: Path, archive: Path) -> int:
    _configure()
    return int(_BASE.approve_all(authorization_path, graph_path, archive))


def run_wave(
    wave_index: int,
    authorization_path: Path,
    graph_path: Path,
    archive: Path,
    qualification_root: Path,
) -> int:
    _configure()
    return int(
        _BASE.run_wave(
            wave_index,
            authorization_path,
            graph_path,
            archive,
            qualification_root,
        )
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--validate-only", action="store_true")
    mode.add_argument("--approve", action="store_true")
    mode.add_argument("--run-wave", type=int)
    parser.add_argument("--authorization", type=Path, required=True)
    parser.add_argument("--graph", type=Path, required=True)
    parser.add_argument("--candidate-archive", type=Path, required=True)
    parser.add_argument("--qualification-root", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.validate_only:
        validate_authorization(args.authorization, args.graph, args.candidate_archive)
        return 0
    if args.approve:
        count = approve_all(args.authorization, args.graph, args.candidate_archive)
        print(f"APPROVED {count}")
        return 0
    assert args.run_wave is not None
    return run_wave(
        args.run_wave,
        args.authorization,
        args.graph,
        args.candidate_archive,
        args.qualification_root,
    )


if __name__ == "__main__":
    raise SystemExit(main())
