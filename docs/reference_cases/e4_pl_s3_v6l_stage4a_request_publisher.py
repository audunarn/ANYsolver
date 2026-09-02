"""Fail-closed publisher for fresh V6L dependency-closed requests."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
from pathlib import Path
import sys
from types import ModuleType
from typing import Any, Sequence


REFERENCE = Path(__file__).resolve().parent
BASE_PUBLISHER = REFERENCE / "e4_pl_s3_v6i_stage4a_request_publisher.py"
BASE_PUBLISHER_SHA256 = "704859B630161A2630111218B3D7A6B7BFF989F828F0454C860C2986A215F90A"
GRAPH_PROGRAM = REFERENCE / "e4_pl_s3_v6l_stage4a_execution_graph.py"
INCIDENT = REFERENCE / "e4_pl_s3_v6k_dependency_closure_incident.json"
INCIDENT_SHA256 = "1E64B737CA9EB3484F8525570DA1DE71715161B498BABA5E90971B538D0361D4"


class V6LPublisherError(RuntimeError):
    """Raised when V6L publication authority differs."""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _load_base() -> ModuleType:
    if _sha256(BASE_PUBLISHER) != BASE_PUBLISHER_SHA256:
        raise V6LPublisherError("frozen V6I publisher differs")
    spec = importlib.util.spec_from_file_location("_s3_v6l_base_publisher", BASE_PUBLISHER)
    if spec is None or spec.loader is None:
        raise V6LPublisherError("cannot load frozen V6I publisher")
    module = importlib.util.module_from_spec(spec)
    sys.modules["_s3_v6l_base_publisher"] = module
    spec.loader.exec_module(module)
    return module


_BASE = _load_base()
_BASE_LOAD_GRAPH = _BASE._load_graph_program
canonical_bytes = _BASE.canonical_bytes


def _load_graph_program() -> ModuleType:
    module = _BASE_LOAD_GRAPH()
    current: ModuleType | None = module
    while current is not None and not hasattr(current, "ROOT"):
        candidate = getattr(current, "_BASE", None)
        current = candidate if isinstance(candidate, ModuleType) else None
    if current is None:
        raise V6LPublisherError("successor graph does not expose its repository root")
    module.ROOT = current.ROOT
    return module


_BASE._load_graph_program = _load_graph_program


def publish_authorized(
    graph_path: Path, authorization_path: Path, request_root: Path
) -> dict[str, Any]:
    if _sha256(INCIDENT) != INCIDENT_SHA256:
        raise V6LPublisherError("preserved V6K dependency incident differs")
    _BASE.GRAPH_PROGRAM = GRAPH_PROGRAM
    return dict(_BASE.publish_authorized(graph_path, authorization_path, request_root))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--graph", type=Path, required=True)
    parser.add_argument("--authorization", type=Path, required=True)
    parser.add_argument("--request-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    made = publish_authorized(args.graph, args.authorization, args.request_root)
    _BASE._write_exclusive(args.output.resolve(), canonical_bytes(made))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
