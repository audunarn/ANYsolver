"""Generate the exact V6J authorization and 27 immutable request documents."""

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
from typing import Any, Sequence


SCHEMA = "anysolver.e4-pl-s3-v6j-stage4a-execution-authorization-v1"
REQUESTED_AT = "2026-09-02T04:26:10.2264996+02:00"
REQUEST_NONCE = "S3_V6J_STAGE4A_20260902_8538D3CD_CYCLE1"
GRAPH_SHA256 = "8538D3CDCA52E0204FF521DDB09D68896F468401BCC0D3F9B488E0FEFE4CBA45"
ARCHIVE_SHA256 = "AC1EA6D71A273355439B25F915EE7BB383DC60769F22EEA8CC84095CDDAF426F"
V6I_STATUS_SHA256 = "B754AE1873D0FB85A33DCA74718A817F6101E0DFC51F7462CDF7960DD13780D9"
REFERENCE = Path(__file__).resolve().parent
ROOT = REFERENCE.parents[1]
GRAPH_PROGRAM = REFERENCE / "e4_pl_s3_v6i_stage4a_execution_graph.py"
V6I_STATUS = REFERENCE / "e4_pl_s3_v6i_stage4a_execution_status.json"


class V6JAuthorityError(RuntimeError):
    """Raised when V6J request authority cannot be generated exactly."""


def _reject_constant(value: str) -> None:
    raise V6JAuthorityError(f"nonfinite JSON constant is forbidden: {value}")


def _reject_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    made: dict[str, Any] = {}
    for key, value in pairs:
        if key in made:
            raise V6JAuthorityError(f"duplicate JSON key is forbidden: {key}")
        made[key] = value
    return made


def canonical_bytes(value: Any) -> bytes:
    def visit(item: Any) -> None:
        if item is None or isinstance(item, (bool, int, str)):
            return
        if isinstance(item, float):
            if not math.isfinite(item):
                raise V6JAuthorityError("nonfinite JSON number is forbidden")
            return
        if isinstance(item, list):
            for child in item:
                visit(child)
            return
        if isinstance(item, dict):
            for key, child in item.items():
                if not isinstance(key, str):
                    raise V6JAuthorityError("JSON keys must be strings")
                visit(child)
            return
        raise V6JAuthorityError(f"unsupported JSON type: {type(item).__name__}")

    visit(value)
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode(
        "utf-8"
    )


def strict_json(path: Path) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_reject_pairs,
            parse_constant=_reject_constant,
        )
    except (UnicodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
        if isinstance(exc, V6JAuthorityError):
            raise
        raise V6JAuthorityError(f"invalid JSON: {path}") from exc
    if not isinstance(value, dict) or raw != canonical_bytes(value):
        raise V6JAuthorityError(f"noncanonical JSON: {path}")
    return value, raw


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def _regular_bytes(path: Path, label: str) -> bytes:
    path = path.resolve()
    information = path.lstat()
    if (
        not stat.S_ISREG(information.st_mode)
        or path.is_symlink()
        or getattr(information, "st_file_attributes", 0)
        & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    ):
        raise V6JAuthorityError(f"{label} is not regular non-reparse")
    return path.read_bytes()


def _load_graph() -> ModuleType:
    spec = importlib.util.spec_from_file_location("_s3_v6j_graph", GRAPH_PROGRAM)
    if spec is None or spec.loader is None:
        raise V6JAuthorityError("cannot load V6I graph program")
    module = importlib.util.module_from_spec(spec)
    sys.modules["_s3_v6j_graph"] = module
    spec.loader.exec_module(module)
    return module


def request_id(wave_index: int) -> str:
    raw = f"{REQUEST_NONCE}:{GRAPH_SHA256}:{wave_index}".encode("ascii")
    return hashlib.sha256(raw).hexdigest()[:32]


def generate(
    graph_path: Path,
    candidate_archive: Path,
    qualification_root: Path,
    authorization_path: Path,
    request_root: Path,
) -> dict[str, Any]:
    graph_program = _load_graph()
    graph, graph_raw = strict_json(graph_path.resolve())
    graph_program.validate_graph(graph)
    if (
        sha256(graph_raw) != GRAPH_SHA256
        or sha256(_regular_bytes(GRAPH_PROGRAM, "V6I graph program"))
        != graph["graph_program_sha256"]
    ):
        raise V6JAuthorityError("formal execution graph hash differs")
    graph_program.verify_archive(candidate_archive.resolve())
    if sha256(_regular_bytes(V6I_STATUS, "V6I status")) != V6I_STATUS_SHA256:
        raise V6JAuthorityError("V6I closeout status differs")
    if request_root.resolve() != Path(r"C:\Github\.resource-manager\requests"):
        raise V6JAuthorityError("resource request root differs")
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for wave_index in range(graph_program.WAVE_COUNT):
        made_id = request_id(wave_index)
        if made_id in seen:
            raise V6JAuthorityError("deterministic request ID collision")
        seen.add(made_id)
        request_path = request_root.resolve() / f"{made_id}.json"
        wave_root = qualification_root.resolve() / f"wave-{wave_index + 1:02d}"
        result_path = wave_root / "wave-wrapper-result.json"
        request = {
            "command": graph_program.registered_command(
                graph_path=graph_path,
                wave_index=wave_index,
                candidate_archive=candidate_archive,
                output_root=wave_root,
                authorization_path=authorization_path,
                request_path=request_path,
                result_path=result_path,
            ),
            "estimate_minutes": 30,
            "repository": str(ROOT.resolve()),
            "request_id": made_id,
            "requested_at": REQUESTED_AT,
            "status": "PENDING",
            "task": f"ANYsolver S3 V2D Stage 4A bounded wave {wave_index + 1:02d}",
        }
        raw_request = canonical_bytes(request)
        rows.append(
            {
                "request": request,
                "request_sha256": sha256(raw_request),
                "wave_index": wave_index,
            }
        )
    return {
        "activation_authorized": False,
        "graph_sha256": GRAPH_SHA256,
        "requests": rows,
        "schema": SCHEMA,
        "stage4a_execution_authorized": True,
    }


def _write_exclusive(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--graph", type=Path, required=True)
    parser.add_argument("--candidate-archive", type=Path, required=True)
    parser.add_argument("--qualification-root", type=Path, required=True)
    parser.add_argument("--authorization-path", type=Path, required=True)
    parser.add_argument("--request-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    made = generate(
        args.graph, args.candidate_archive, args.qualification_root,
        args.authorization_path, args.request_root,
    )
    _write_exclusive(args.output.resolve(), canonical_bytes(made))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
