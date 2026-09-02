"""Generate fresh V6L requests for the dependency-closed Stage 4A graph."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import os
from pathlib import Path
import sys
from types import ModuleType
from typing import Any, Sequence


SCHEMA = "anysolver.e4-pl-s3-v6l-stage4a-execution-authorization-v1"
REQUESTED_AT = "2026-09-02T05:20:00.0000000+02:00"
REQUEST_NONCE = "S3_V6L_STAGE4A_20260902_1DFC5272_CYCLE1"
GRAPH_SHA256 = "1DFC5272DD92BB0A2A91FB63641B9446D168A487D9E60B4FC8298C2773047F79"
REFERENCE = Path(__file__).resolve().parent
BASE_AUTHORITY = REFERENCE / "e4_pl_s3_v6k_stage4a_authority.py"
BASE_AUTHORITY_SHA256 = "E44157433A8AA5FC6F9BF98A5542556876CB7BDD17C78FE292707AA58B991DD2"
GRAPH_PROGRAM = REFERENCE / "e4_pl_s3_v6l_stage4a_execution_graph.py"
INCIDENT = REFERENCE / "e4_pl_s3_v6k_dependency_closure_incident.json"
INCIDENT_SHA256 = "1E64B737CA9EB3484F8525570DA1DE71715161B498BABA5E90971B538D0361D4"


class V6LAuthorityError(RuntimeError):
    """Raised when the V6L successor authority differs."""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _load_base() -> ModuleType:
    if _sha256(BASE_AUTHORITY) != BASE_AUTHORITY_SHA256:
        raise V6LAuthorityError("frozen V6K authority generator differs")
    spec = importlib.util.spec_from_file_location("_s3_v6l_base_authority", BASE_AUTHORITY)
    if spec is None or spec.loader is None:
        raise V6LAuthorityError("cannot load V6K authority generator")
    module = importlib.util.module_from_spec(spec)
    sys.modules["_s3_v6l_base_authority"] = module
    spec.loader.exec_module(module)
    return module


_BASE = _load_base()
_BASE_CONFIGURE = _BASE._configure
_GENERATOR = _BASE._BASE
_BASE_LOAD_GRAPH = _GENERATOR._load_graph
canonical_bytes = _BASE.canonical_bytes
strict_json = _BASE.strict_json
sha256 = _BASE.sha256


def _configure() -> None:
    if _sha256(INCIDENT) != INCIDENT_SHA256:
        raise V6LAuthorityError("preserved V6K dependency incident differs")
    _BASE_CONFIGURE()
    generator = _BASE._BASE
    for module in (_BASE, generator):
        module.SCHEMA = SCHEMA
        module.REQUESTED_AT = REQUESTED_AT
        module.REQUEST_NONCE = REQUEST_NONCE
        module.GRAPH_SHA256 = GRAPH_SHA256
        module.GRAPH_PROGRAM = GRAPH_PROGRAM


_BASE._configure = _configure


def _load_graph() -> ModuleType:
    module = _BASE_LOAD_GRAPH()
    current: ModuleType | None = module
    while current is not None and not hasattr(current, "verify_archive"):
        candidate = getattr(current, "_BASE", None)
        current = candidate if isinstance(candidate, ModuleType) else None
    if current is None:
        raise V6LAuthorityError("successor graph does not expose candidate archive validation")
    module.verify_archive = current.verify_archive
    return module


_GENERATOR._load_graph = _load_graph


def request_id(wave_index: int) -> str:
    _configure()
    return str(_BASE.request_id(wave_index))


def generate(
    graph_path: Path,
    candidate_archive: Path,
    qualification_root: Path,
    authorization_path: Path,
    request_root: Path,
) -> dict[str, Any]:
    _configure()
    return dict(
        _BASE.generate(
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
