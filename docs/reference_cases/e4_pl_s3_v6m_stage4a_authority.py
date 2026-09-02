"""Generate fresh V6M requests for the preparation-safe Stage 4A graph."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import os
from pathlib import Path
import sys
from types import ModuleType
from typing import Any, Sequence


SCHEMA = "anysolver.e4-pl-s3-v6m-stage4a-execution-authorization-v1"
REQUESTED_AT = "2026-09-02T05:40:00.0000000+02:00"
REQUEST_NONCE = "S3_V6M_STAGE4A_20260902_604CDECA_CYCLE1"
GRAPH_SHA256 = "604CDECA29FF0387B1BB9D18D8539C79277B8FB3CE593F870C8C5EFB19D8219E"
REFERENCE = Path(__file__).resolve().parent
BASE_AUTHORITY = REFERENCE / "e4_pl_s3_v6l_stage4a_authority.py"
BASE_AUTHORITY_SHA256 = "232F506A6852318292AB090E8510A10F12A03ABE6AE0D5E217A0375D5F9186E7"
GRAPH_PROGRAM = REFERENCE / "e4_pl_s3_v6m_stage4a_execution_graph.py"
INCIDENT = REFERENCE / "e4_pl_s3_v6l_validator_recursion_incident.json"
INCIDENT_SHA256 = "EA64C50EF1BD764DE4306B189AE8D26320094E5D4F72B5CF9A591658C48FE641"


class V6MAuthorityError(RuntimeError):
    """Raised when the V6M successor authority differs."""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _load_base() -> ModuleType:
    if _sha256(BASE_AUTHORITY) != BASE_AUTHORITY_SHA256:
        raise V6MAuthorityError("frozen V6L authority generator differs")
    spec = importlib.util.spec_from_file_location("_s3_v6m_base_authority", BASE_AUTHORITY)
    if spec is None or spec.loader is None:
        raise V6MAuthorityError("cannot load V6L authority generator")
    module = importlib.util.module_from_spec(spec)
    sys.modules["_s3_v6m_base_authority"] = module
    spec.loader.exec_module(module)
    return module


_BASE = _load_base()
_BASE_CONFIGURE = _BASE._configure
_GENERATOR = _BASE._GENERATOR
canonical_bytes = _GENERATOR.canonical_bytes
strict_json = _GENERATOR.strict_json
sha256 = _GENERATOR.sha256


def _configure() -> None:
    if _sha256(INCIDENT) != INCIDENT_SHA256:
        raise V6MAuthorityError("preserved V6L validator incident differs")
    _BASE_CONFIGURE()
    for module in (_BASE, _BASE._BASE, _GENERATOR):
        module.SCHEMA = SCHEMA
        module.REQUESTED_AT = REQUESTED_AT
        module.REQUEST_NONCE = REQUEST_NONCE
        module.GRAPH_SHA256 = GRAPH_SHA256
        module.GRAPH_PROGRAM = GRAPH_PROGRAM


def request_id(wave_index: int) -> str:
    _configure()
    return str(_GENERATOR.request_id(wave_index))


def generate(
    graph_path: Path,
    candidate_archive: Path,
    qualification_root: Path,
    authorization_path: Path,
    request_root: Path,
) -> dict[str, Any]:
    _configure()
    return dict(
        _GENERATOR.generate(
            graph_path,
            candidate_archive,
            qualification_root,
            authorization_path,
            request_root,
        )
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--graph", type=Path, required=True)
    parser.add_argument("--candidate-archive", type=Path, required=True)
    parser.add_argument("--qualification-root", type=Path, required=True)
    parser.add_argument("--authorization-path", type=Path, required=True)
    parser.add_argument("--request-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    raw = canonical_bytes(
        generate(
            args.graph,
            args.candidate_archive,
            args.qualification_root,
            args.authorization_path,
            args.request_root,
        )
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("xb") as handle:
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
