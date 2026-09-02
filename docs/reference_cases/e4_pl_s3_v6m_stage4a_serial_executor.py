"""Serial executor for fresh V6M preparation-safe Stage 4A requests."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
from pathlib import Path
import sys
from types import ModuleType
from typing import Any, Sequence


REFERENCE = Path(__file__).resolve().parent
BASE_EXECUTOR = REFERENCE / "e4_pl_s3_v6l_stage4a_serial_executor.py"
BASE_EXECUTOR_SHA256 = "AB1786501F08F7CF1413E317926BE88AD423A7B7254DD64DF62AE9A62BBCCA59"
AUTHORITY_PROGRAM = REFERENCE / "e4_pl_s3_v6m_stage4a_authority.py"
GRAPH_PROGRAM = REFERENCE / "e4_pl_s3_v6m_stage4a_execution_graph.py"
INCIDENT = REFERENCE / "e4_pl_s3_v6l_validator_recursion_incident.json"
INCIDENT_SHA256 = "EA64C50EF1BD764DE4306B189AE8D26320094E5D4F72B5CF9A591658C48FE641"


class V6MExecutionError(RuntimeError):
    """Raised when the V6M executor's frozen inputs differ."""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _load_base() -> ModuleType:
    if _sha256(BASE_EXECUTOR) != BASE_EXECUTOR_SHA256:
        raise V6MExecutionError("frozen V6L serial executor differs")
    spec = importlib.util.spec_from_file_location("_s3_v6m_base_executor", BASE_EXECUTOR)
    if spec is None or spec.loader is None:
        raise V6MExecutionError("cannot load V6L serial executor")
    module = importlib.util.module_from_spec(spec)
    sys.modules["_s3_v6m_base_executor"] = module
    spec.loader.exec_module(module)
    return module


_BASE = _load_base()
_BASE_CONFIGURE = _BASE._configure
_EXECUTOR = _BASE._EXECUTOR
canonical_bytes = _EXECUTOR.canonical_bytes
strict_json = _EXECUTOR.strict_json
sha256 = _EXECUTOR.sha256


def _configure() -> None:
    if _sha256(INCIDENT) != INCIDENT_SHA256:
        raise V6MExecutionError("preserved V6L validator incident differs")
    _BASE_CONFIGURE()
    for module in (_BASE, _BASE._BASE, _EXECUTOR):
        module.AUTHORITY_PROGRAM = AUTHORITY_PROGRAM
        module.GRAPH_PROGRAM = GRAPH_PROGRAM


def validate_authorization(
    authorization_path: Path, graph_path: Path, archive: Path
) -> tuple[dict[str, Any], bytes, dict[str, Any], bytes]:
    _configure()
    return _EXECUTOR.validate_authorization(authorization_path, graph_path, archive)


def approve_all(authorization_path: Path, graph_path: Path, archive: Path) -> int:
    _configure()
    return int(_EXECUTOR.approve_all(authorization_path, graph_path, archive))


def run_wave(
    wave_index: int,
    authorization_path: Path,
    graph_path: Path,
    archive: Path,
    qualification_root: Path,
) -> int:
    _configure()
    return int(
        _EXECUTOR.run_wave(
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
