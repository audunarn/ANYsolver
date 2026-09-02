"""Fail-closed publisher for the four V6O missing-leaf requests."""

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
GRAPH_PROGRAM = REFERENCE / "e4_pl_s3_v6o_stage4a_missing_leaf_graph.py"


class V6OPublisherError(RuntimeError):
    """Raised when V6O publication authority differs."""


def _load_base() -> ModuleType:
    if hashlib.sha256(BASE_PUBLISHER.read_bytes()).hexdigest().upper() != BASE_PUBLISHER_SHA256:
        raise V6OPublisherError("frozen V6I publisher differs")
    spec = importlib.util.spec_from_file_location("_s3_v6o_base_publisher", BASE_PUBLISHER)
    if spec is None or spec.loader is None:
        raise V6OPublisherError("cannot load frozen publisher")
    module = importlib.util.module_from_spec(spec)
    sys.modules["_s3_v6o_base_publisher"] = module
    spec.loader.exec_module(module)
    return module


_BASE = _load_base()
canonical_bytes = _BASE.canonical_bytes


def publish_authorized(
    graph_path: Path, authorization_path: Path, request_root: Path
) -> dict[str, Any]:
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
