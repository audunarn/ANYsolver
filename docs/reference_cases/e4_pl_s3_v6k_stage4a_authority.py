"""Generate fresh V6K requests after the preserved V6J resource deferral."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
from types import ModuleType
from typing import Any, Sequence


SCHEMA = "anysolver.e4-pl-s3-v6k-stage4a-execution-authorization-v1"
REQUESTED_AT = "2026-09-02T04:42:56.0063733+02:00"
REQUEST_NONCE = "S3_V6K_STAGE4A_20260902_2D91BBA2_CYCLE1"
GRAPH_SHA256 = "2D91BBA2D88B6D1D16A308EFF67AC73705B0E3C988521155C4E2B67BB68228B6"
REFERENCE = Path(__file__).resolve().parent
BASE_AUTHORITY = REFERENCE / "e4_pl_s3_v6j_stage4a_authority.py"
BASE_AUTHORITY_SHA256 = "80EC7DB6FDBA44B0584DE5F8FDFD416F2B9FFD80F0FD51FB6F71BB027674A2CA"
GRAPH_PROGRAM = REFERENCE / "e4_pl_s3_v6k_stage4a_execution_graph.py"
INCIDENT = REFERENCE / "e4_pl_s3_v6j_resource_deferred_incident.json"
INCIDENT_SHA256 = "A3BA33CF8F1C570F1171CF7299686FFC4F9035FDEA9A876E0FE25607AEA64706"


class V6KAuthorityError(RuntimeError):
    """Raised when the V6K successor authority differs."""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _load_base() -> ModuleType:
    if _sha256(BASE_AUTHORITY) != BASE_AUTHORITY_SHA256:
        raise V6KAuthorityError("frozen V6J authority generator differs")
    spec = importlib.util.spec_from_file_location("_s3_v6k_base_authority", BASE_AUTHORITY)
    if spec is None or spec.loader is None:
        raise V6KAuthorityError("cannot load V6J authority generator")
    module = importlib.util.module_from_spec(spec)
    sys.modules["_s3_v6k_base_authority"] = module
    spec.loader.exec_module(module)
    return module


_BASE = _load_base()
canonical_bytes = _BASE.canonical_bytes
strict_json = _BASE.strict_json
sha256 = _BASE.sha256


def _configure() -> None:
    if _sha256(INCIDENT) != INCIDENT_SHA256:
        raise V6KAuthorityError("preserved V6J resource incident differs")
    _BASE.SCHEMA = SCHEMA
    _BASE.REQUESTED_AT = REQUESTED_AT
    _BASE.REQUEST_NONCE = REQUEST_NONCE
    _BASE.GRAPH_SHA256 = GRAPH_SHA256
    _BASE.GRAPH_PROGRAM = GRAPH_PROGRAM


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
