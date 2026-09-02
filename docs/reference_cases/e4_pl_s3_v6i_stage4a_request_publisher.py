"""Fail-closed V6I publisher for successor-authorized Stage-4A requests.

Preview mode is non-authoritative.  Publication requires a canonical V6J
authorization containing all 27 exact request documents; this V6I gate does
not create such an authorization and therefore cannot publish or execute.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import stat
import sys
from types import ModuleType
from typing import Any, Mapping, Sequence


PREVIEW_SCHEMA = "anysolver.e4-pl-s3-v6i-stage4a-request-preview-v1"
PUBLICATION_SCHEMA = "anysolver.e4-pl-s3-v6i-stage4a-request-publication-v1"
GRAPH_PROGRAM = Path(__file__).with_name(
    "e4_pl_s3_v6i_stage4a_execution_graph.py"
).resolve()


class V6IPublisherError(RuntimeError):
    """Raised when request publication lacks exact successor authority."""


def _reject_constant(value: str) -> None:
    raise V6IPublisherError(f"nonfinite JSON constant is forbidden: {value}")


def _reject_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    made: dict[str, Any] = {}
    for key, value in pairs:
        if key in made:
            raise V6IPublisherError(f"duplicate JSON key is forbidden: {key}")
        made[key] = value
    return made


def canonical_bytes(value: Any) -> bytes:
    def visit(item: Any) -> None:
        if item is None or isinstance(item, (bool, int, str)):
            return
        if isinstance(item, float):
            if not math.isfinite(item):
                raise V6IPublisherError("nonfinite JSON number is forbidden")
            return
        if isinstance(item, list):
            for child in item:
                visit(child)
            return
        if isinstance(item, dict):
            for key, child in item.items():
                if not isinstance(key, str):
                    raise V6IPublisherError("JSON keys must be strings")
                visit(child)
            return
        raise V6IPublisherError(f"unsupported JSON type: {type(item).__name__}")

    visit(value)
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode(
        "utf-8"
    )


def _strict(path: Path) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_reject_pairs,
            parse_constant=_reject_constant,
        )
    except (UnicodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
        if isinstance(exc, V6IPublisherError):
            raise
        raise V6IPublisherError(f"invalid JSON: {path}") from exc
    if not isinstance(value, dict) or raw != canonical_bytes(value):
        raise V6IPublisherError(f"noncanonical JSON: {path}")
    return value, raw


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def _load_graph_program() -> ModuleType:
    information = GRAPH_PROGRAM.lstat()
    if (
        not stat.S_ISREG(information.st_mode)
        or GRAPH_PROGRAM.is_symlink()
        or getattr(information, "st_file_attributes", 0)
        & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    ):
        raise V6IPublisherError("V6I graph program is not regular non-reparse")
    spec = importlib.util.spec_from_file_location("_s3_v6i_graph", GRAPH_PROGRAM)
    if spec is None or spec.loader is None:
        raise V6IPublisherError("cannot load V6I graph program")
    module = importlib.util.module_from_spec(spec)
    previous = sys.modules.get("_s3_v6i_graph")
    sys.modules["_s3_v6i_graph"] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        if previous is None:
            sys.modules.pop("_s3_v6i_graph", None)
        else:
            sys.modules["_s3_v6i_graph"] = previous
        raise
    return module


def _validated_graph(path: Path) -> tuple[ModuleType, dict[str, Any], bytes]:
    graph_program = _load_graph_program()
    graph, raw = _strict(path.resolve())
    graph_program.validate_graph(graph)
    if graph["graph_program_sha256"] != _sha256(GRAPH_PROGRAM.read_bytes()):
        raise V6IPublisherError("graph program binding differs")
    return graph_program, graph, raw


def build_preview(
    graph_path: Path,
    candidate_archive: Path,
    qualification_root: Path,
    authorization_path: Path,
    request_root: Path,
) -> dict[str, Any]:
    program, graph, graph_raw = _validated_graph(graph_path)
    program.verify_archive(candidate_archive)
    templates: list[dict[str, Any]] = []
    for wave_index in range(program.WAVE_COUNT):
        request_id = f"REQUEST_ID_{wave_index + 1:02d}"
        request_path = request_root.resolve() / f"{request_id}.json"
        wave_root = qualification_root.resolve() / f"wave-{wave_index + 1:02d}"
        result_path = wave_root / "wave-wrapper-result.json"
        templates.append(
            {
                "command": program.registered_command(
                    graph_path=graph_path,
                    wave_index=wave_index,
                    candidate_archive=candidate_archive,
                    output_root=wave_root,
                    authorization_path=authorization_path,
                    request_path=request_path,
                    result_path=result_path,
                ),
                "estimate_minutes": 30,
                "repository": str(program.ROOT.resolve()),
                "request_path": str(request_path),
                "requested_at": "FROZEN_BY_SUCCESSOR_AUTHORITY",
                "status": "PENDING",
                "task": f"ANYsolver S3 V2D Stage 4A bounded wave {wave_index + 1:02d}",
                "wave_index": wave_index,
            }
        )
    return {
        "activation_authorized": False,
        "graph_sha256": _sha256(graph_raw),
        "publication_authorized": False,
        "request_count": len(templates),
        "requests": templates,
        "schema": PREVIEW_SCHEMA,
        "stage4a_execution_authorized": False,
        "terminal": "VALIDATED_REQUEST_PREVIEW_NOT_PUBLISHED",
    }


def publish_authorized(
    graph_path: Path,
    authorization_path: Path,
    request_root: Path,
) -> dict[str, Any]:
    _program, graph, graph_raw = _validated_graph(graph_path)
    authorization, authorization_raw = _strict(authorization_path.resolve())
    if set(authorization) != {
        "activation_authorized", "graph_sha256", "requests", "schema",
        "stage4a_execution_authorized",
    } or (
        authorization["schema"] != _program.AUTHORIZATION_SCHEMA
        or authorization["activation_authorized"] is not False
        or authorization["stage4a_execution_authorized"] is not True
        or authorization["graph_sha256"] != _sha256(graph_raw)
    ):
        raise V6IPublisherError("successor publication authority differs")
    rows = authorization["requests"]
    if not isinstance(rows, list) or len(rows) != _program.WAVE_COUNT:
        raise V6IPublisherError("successor request coverage differs")
    request_root = request_root.resolve()
    if not request_root.is_dir() or request_root.is_symlink():
        raise V6IPublisherError("registered request root is unavailable")
    published: list[dict[str, Any]] = []
    seen: set[str] = set()
    for expected_index, row in enumerate(rows):
        if not isinstance(row, Mapping) or set(row) != {
            "request", "request_sha256", "wave_index"
        } or row["wave_index"] != expected_index:
            raise V6IPublisherError("successor request row differs")
        request = row["request"]
        if not isinstance(request, dict) or set(request) != {
            "command", "estimate_minutes", "repository", "request_id", "requested_at",
            "status", "task",
        }:
            raise V6IPublisherError("successor request document is malformed")
        raw = canonical_bytes(request)
        request_id = request.get("request_id")
        if (
            _sha256(raw) != row["request_sha256"]
            or not isinstance(request_id, str)
            or len(request_id) != 32
            or any(character not in "0123456789abcdef" for character in request_id)
            or request_id in seen
            or request.get("status") != "PENDING"
            or request.get("estimate_minutes") != 30
            or request.get("repository") != str(_program.ROOT.resolve())
            or request.get("task")
            != f"ANYsolver S3 V2D Stage 4A bounded wave {expected_index + 1:02d}"
            or not isinstance(request.get("requested_at"), str)
            or not request["requested_at"]
            or not isinstance(request.get("command"), str)
            or "--run-registered-wave" not in request["command"]
            or str(graph_path.resolve()) not in request["command"]
            or str(authorization_path.resolve()) not in request["command"]
        ):
            raise V6IPublisherError("successor request identity differs")
        seen.add(request_id)
        path = request_root / f"{request_id}.json"
        try:
            with path.open("xb") as handle:
                handle.write(raw)
                handle.flush()
                os.fsync(handle.fileno())
        except BaseException:
            # Already-published rows are immutable; no rollback or overwrite.
            raise
        published.append(
            {
                "request_id": request_id,
                "request_path": str(path),
                "request_sha256": row["request_sha256"],
                "wave_index": expected_index,
            }
        )
    return {
        "activation_authorized": False,
        "authorization_sha256": _sha256(authorization_raw),
        "graph_sha256": _sha256(graph_raw),
        "published": published,
        "request_count": len(published),
        "schema": PUBLICATION_SCHEMA,
        "stage4a_execution_authorized": True,
        "terminal": "PUBLISHED_V6I_REQUESTS_NOT_EXECUTED",
    }


def _write_exclusive(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(raw)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preview", action="store_true")
    mode.add_argument("--publish", action="store_true")
    parser.add_argument("--graph", type=Path, required=True)
    parser.add_argument("--candidate-archive", type=Path)
    parser.add_argument("--qualification-root", type=Path)
    parser.add_argument("--authorization", type=Path, required=True)
    parser.add_argument("--request-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.preview:
        if args.candidate_archive is None or args.qualification_root is None:
            raise V6IPublisherError("preview requires archive and qualification root")
        made = build_preview(
            args.graph, args.candidate_archive, args.qualification_root,
            args.authorization, args.request_root,
        )
    else:
        made = publish_authorized(args.graph, args.authorization, args.request_root)
    _write_exclusive(args.output.resolve(), canonical_bytes(made))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
