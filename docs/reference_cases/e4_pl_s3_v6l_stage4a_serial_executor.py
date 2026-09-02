"""Serial executor for fresh V6L dependency-closed Stage 4A requests."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
from pathlib import Path
import sys
from types import ModuleType
from typing import Any, Sequence


REFERENCE = Path(__file__).resolve().parent
BASE_EXECUTOR = REFERENCE / "e4_pl_s3_v6k_stage4a_serial_executor.py"
BASE_EXECUTOR_SHA256 = "71EA77BD720F28D803A205223D2E85CF674524900C20082EB381E15012C0112F"
AUTHORITY_PROGRAM = REFERENCE / "e4_pl_s3_v6l_stage4a_authority.py"
GRAPH_PROGRAM = REFERENCE / "e4_pl_s3_v6l_stage4a_execution_graph.py"
INCIDENT = REFERENCE / "e4_pl_s3_v6k_dependency_closure_incident.json"
INCIDENT_SHA256 = "1E64B737CA9EB3484F8525570DA1DE71715161B498BABA5E90971B538D0361D4"


class V6LExecutionError(RuntimeError):
    """Raised when the V6L executor's frozen inputs differ."""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _load_base() -> ModuleType:
    if _sha256(BASE_EXECUTOR) != BASE_EXECUTOR_SHA256:
        raise V6LExecutionError("frozen V6K serial executor differs")
    spec = importlib.util.spec_from_file_location("_s3_v6l_base_executor", BASE_EXECUTOR)
    if spec is None or spec.loader is None:
        raise V6LExecutionError("cannot load V6K serial executor")
    module = importlib.util.module_from_spec(spec)
    sys.modules["_s3_v6l_base_executor"] = module
    spec.loader.exec_module(module)
    return module


_BASE = _load_base()
_BASE_CONFIGURE = _BASE._configure
_EXECUTOR = _BASE._BASE
_BASE_LOAD = _EXECUTOR._load
canonical_bytes = _BASE.canonical_bytes
strict_json = _BASE.strict_json
sha256 = _BASE.sha256


def _configure() -> None:
    if _sha256(INCIDENT) != INCIDENT_SHA256:
        raise V6LExecutionError("preserved V6K dependency incident differs")
    _BASE_CONFIGURE()
    executor = _BASE._BASE
    for module in (_BASE, executor):
        module.AUTHORITY_PROGRAM = AUTHORITY_PROGRAM
        module.GRAPH_PROGRAM = GRAPH_PROGRAM


_BASE._configure = _configure


def _load(path: Path, name: str) -> ModuleType:
    module = _BASE_LOAD(path, name)
    if path.resolve() == GRAPH_PROGRAM.resolve() and not hasattr(module, "verify_archive"):
        current: ModuleType | None = module
        while current is not None and not hasattr(current, "verify_archive"):
            candidate = getattr(current, "_BASE", None)
            current = candidate if isinstance(candidate, ModuleType) else None
        if current is None:
            raise V6LExecutionError("successor graph does not expose candidate archive validation")
        module.verify_archive = current.verify_archive
    return module


_EXECUTOR._load = _load


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
