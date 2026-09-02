"""Deterministic V6I Stage-4A graph and fail-closed bounded executor.

Graph construction is nonmechanical.  The execution entry point remains
unusable until a successor canonical authorization binds the graph and the
resource request.  Each authorized invocation can run exactly one wave.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tarfile
from types import ModuleType
from typing import Any, Mapping, Sequence


SCHEMA = "anysolver.e4-pl-s3-v6i-stage4a-execution-graph-v1"
AUTHORIZATION_SCHEMA = "anysolver.e4-pl-s3-v6j-stage4a-execution-authorization-v1"
RESULT_SCHEMA = "anysolver.e4-pl-s3-v6i-stage4a-wave-wrapper-result-v1"
REFERENCE = Path(__file__).resolve().parent
ROOT = REFERENCE.parents[1]
MANIFEST = REFERENCE / "e4_pl_s3_mixed_mesh_connectivity_manifest.json"
FUNNEL = REFERENCE / "e4_pl_s3_v2_flat_funnel.py"
PRODUCER = REFERENCE / "e4_pl_s3_v2_flat_funnel_producer.py"
ADAPTER = REFERENCE / "e4_pl_s3_v6h_stage4a_adapter.py"
BOUNDED = REFERENCE / "e4_pl_s3_v2_bounded_process.py"
V6H_AUTHORITY = REFERENCE / "e4_pl_s3_v6h_stage4a_preparation_authority.json"
V6H_REVIEW = REFERENCE / "e4_pl_s3_v6h_stage4a_preparation_review.json"
V6H_STATUS = REFERENCE / "e4_pl_s3_v6h_stage4a_preparation_status.json"

CANDIDATE_COMMIT = "c6e596c64321225e36aaff02b98ddb8fa81b6620"
CANDIDATE_TREE = "eeccd0a3088c2de0430755e02b27dd2343c7103f"
CANDIDATE_ARCHIVE_BYTES = 29_767_680
CANDIDATE_ARCHIVE_SHA256 = (
    "AC1EA6D71A273355439B25F915EE7BB383DC60769F22EEA8CC84095CDDAF426F"
)
FORMULATION_ID = "CANDIDATE_E4_PL_S3_V2D_NATIVE_PARITY_V1"
IMPLEMENTATION_ID = "E4_PL_S3_V2D_RECOVERY_CURRENT_EIGEN_GATE_V1"
RUNTIME_SELECTOR = "e4-pl-s3-v2d"
SCIENTIFIC_SELECTOR = "e4-pl-s3-v2"
LEAF_SCIENTIFIC_SCHEMA = (
    "anysolver.e4-pl-s3-v2-stage4a-leaf-scientific-v3"
)
DIAGONALS = ("slash", "backslash", "alternating")
LEAF_COUNT = 81
WAVE_COUNT = 27
WORKERS_PER_WAVE = 3
CHILD_WALL_SECONDS = 600
WAVE_WALL_SECONDS = 1800
MEMORY_LIMIT_GIB = 24
THREADS_PER_WORKER = 1

FROZEN_HASHES = {
    MANIFEST: "3EA7ABD0B332831D62B30B3CD52E0DB85EC951B125340FFAF40A891DC37BD589",
    FUNNEL: "8EDFF65DF7D67B771089B421A7CA9966E94ED4354162685CDC0CFC8A6603C146",
    PRODUCER: "A8FD7258303AA3D73968AAE775BCC0C4A31C88B6E7F2F1DF44F8A1D00180CB3F",
    ADAPTER: "2C70B6B952CB7100ED1ED7C3E9BAB867C634BD11497422DF2916D045948E54C5",
    BOUNDED: "C5B192C9C3F6EE2C68A42AB4A0CFBCDBE81581381B800C13AACCE0BB219A3383",
    V6H_AUTHORITY: "9C3322E9B457A12A84A3A07808A58EDB96B8D6864C735DA7BA11CF5F4ADD5B14",
    V6H_REVIEW: "D6FAAF96D1A313C2A63490A8C867E212EF4BBB070915D4E338D921027A69CB25",
    V6H_STATUS: "EE697C026E779A2DDA39CFA10EB1FEF0EF061A9168F0D71D80BE43CBFBC38FB4",
}


class V6IError(RuntimeError):
    """Raised when graph, archive, request, or execution authority differs."""


def _reject_constant(value: str) -> None:
    raise V6IError(f"nonfinite JSON constant is forbidden: {value}")


def _reject_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    made: dict[str, Any] = {}
    for key, value in pairs:
        if key in made:
            raise V6IError(f"duplicate JSON key is forbidden: {key}")
        made[key] = value
    return made


def canonical_bytes(value: Any) -> bytes:
    def visit(item: Any) -> None:
        if item is None or isinstance(item, (bool, int, str)):
            return
        if isinstance(item, float):
            if not math.isfinite(item):
                raise V6IError("nonfinite JSON number is forbidden")
            return
        if isinstance(item, list):
            for child in item:
                visit(child)
            return
        if isinstance(item, dict):
            for key, child in item.items():
                if not isinstance(key, str):
                    raise V6IError("JSON keys must be strings")
                visit(child)
            return
        raise V6IError(f"unsupported JSON type: {type(item).__name__}")

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
        if isinstance(exc, V6IError):
            raise
        raise V6IError(f"invalid JSON: {path}") from exc
    if not isinstance(value, dict) or raw != canonical_bytes(value):
        raise V6IError(f"noncanonical JSON: {path}")
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
        raise V6IError(f"{label} is not a regular non-reparse file")
    return path.read_bytes()


def _load(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise V6IError(f"cannot load frozen module: {path}")
    module = importlib.util.module_from_spec(spec)
    previous = sys.modules.get(name)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        if previous is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = previous
        raise
    return module


def _verify_frozen_inputs() -> None:
    for path, expected in FROZEN_HASHES.items():
        if sha256(_regular_bytes(path, path.name)) != expected:
            raise V6IError(f"frozen input differs: {path.name}")
    authority, _ = strict_json(V6H_AUTHORITY)
    status, _ = strict_json(V6H_STATUS)
    if (
        authority.get("terminal")
        != "PROVISIONAL_GO_E4_PL_S3_V6H_STAGE4A_PREPARATION"
        or authority.get("stage4a_preparation_authorized") is not True
        or authority.get("stage4a_execution_authorized") is not False
        or status.get("terminal")
        != "PROVISIONAL_GO_E4_PL_S3_V6H_STAGE4A_PREPARATION"
    ):
        raise V6IError("accepted V6H preparation authority differs")


def _safe_members(archive: Path) -> list[tarfile.TarInfo]:
    members: list[tarfile.TarInfo] = []
    seen: set[str] = set()
    with tarfile.open(archive, mode="r:") as bundle:
        for member in bundle.getmembers():
            name = member.name.rstrip("/")
            if not name:
                continue
            pure = Path(name.replace("/", os.sep))
            canonical = "/".join(pure.parts)
            folded = canonical.casefold()
            if (
                pure.is_absolute()
                or any(part in {"", ".", ".."} for part in pure.parts)
                or folded in seen
                or not (member.isdir() or member.isfile())
            ):
                raise V6IError("candidate archive has an unsafe or duplicate member")
            seen.add(folded)
            members.append(member)
    if not members:
        raise V6IError("candidate archive is empty")
    return members


def verify_archive(archive: Path) -> list[tarfile.TarInfo]:
    raw = _regular_bytes(archive, "candidate archive")
    if len(raw) != CANDIDATE_ARCHIVE_BYTES or sha256(raw) != CANDIDATE_ARCHIVE_SHA256:
        raise V6IError("candidate archive identity differs")
    return _safe_members(archive.resolve())


def _extract_archive_exclusive(archive: Path, destination: Path) -> None:
    verify_archive(archive)
    destination = destination.resolve()
    destination.mkdir(parents=True, exist_ok=False)
    try:
        with tarfile.open(archive.resolve(), mode="r:") as bundle:
            for member in bundle.getmembers():
                name = member.name.rstrip("/")
                if not name:
                    continue
                pure = Path(name.replace("/", os.sep))
                target = destination.joinpath(*pure.parts).resolve()
                try:
                    target.relative_to(destination)
                except ValueError as exc:
                    raise V6IError("candidate extraction escapes destination") from exc
                if member.isdir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                if not member.isfile():
                    raise V6IError("candidate archive member is not regular")
                target.parent.mkdir(parents=True, exist_ok=True)
                source = bundle.extractfile(member)
                if source is None:
                    raise V6IError("candidate archive member is unreadable")
                with target.open("xb") as handle:
                    shutil.copyfileobj(source, handle, length=1 << 20)
    except BaseException:
        # Partial external extraction is deliberately preserved for diagnosis.
        raise


def _program_sha256() -> str:
    return sha256(_regular_bytes(Path(__file__), "V6I graph/executor"))


def _record_key(leaf: Mapping[str, Any]) -> tuple[int, int, str]:
    parts = str(leaf["assignment"]["record_id"]).split(":")
    if len(parts) != 4 or not parts[0].startswith("N") or not parts[1].endswith("PCT"):
        raise V6IError("leaf record identity is malformed")
    return (int(parts[0][1:]), int(parts[1][:-3]), parts[2])


def build_graph(candidate_archive: Path) -> dict[str, Any]:
    _verify_frozen_inputs()
    verify_archive(candidate_archive)
    funnel = _load(FUNNEL, "e4_pl_s3_v2_flat_funnel")
    producer = _load(PRODUCER, "_s3_v6i_producer")
    manifest_value, manifest_raw = funnel.strict_json_load(MANIFEST)
    records = funnel.validate_manifest(manifest_value, manifest_raw)
    plan = funnel.build_phase_plan(records, "4A", scope="full")
    plan_raw = funnel.canonical_bytes(plan)
    plan_sha = funnel.sha256(plan_raw)
    program_sha = _program_sha256()
    catalog = producer.build_leaf_catalog(
        plan,
        plan_sha,
        candidate_commit=CANDIDATE_COMMIT,
        candidate_tree=CANDIDATE_TREE,
        candidate_archive_sha256=CANDIDATE_ARCHIVE_SHA256,
        producer_program_sha256=program_sha,
    )
    waves: list[dict[str, Any]] = []
    for wave_index in range(WAVE_COUNT):
        leaves = [catalog[wave_index + offset * WAVE_COUNT] for offset in range(3)]
        keys = {_record_key(leaf) for leaf in leaves}
        diagonals = tuple(str(leaf["assignment"]["diagonal"]) for leaf in leaves)
        if len(keys) != 1 or diagonals != DIAGONALS:
            raise V6IError("wave does not bind one matching record per diagonal")
        waves.append(
            {
                "sequence_key": list(next(iter(keys))),
                "wave_id": f"S3_V6I_STAGE4A_WAVE_{wave_index + 1:02d}",
                "wave_index": wave_index,
                "workers": [
                    {
                        "diagonal": diagonal,
                        "leaf_assignment_sha256": leaf["leaf_assignment_sha256"],
                        "leaf_id": leaf["leaf_id"],
                        "record_id": leaf["assignment"]["record_id"],
                    }
                    for diagonal, leaf in zip(DIAGONALS, leaves)
                ],
            }
        )
    made = {
        "activation_authorized": False,
        "candidate": {
            "archive_bytes": CANDIDATE_ARCHIVE_BYTES,
            "archive_sha256": CANDIDATE_ARCHIVE_SHA256,
            "commit": CANDIDATE_COMMIT,
            "formulation_id": FORMULATION_ID,
            "implementation_id": IMPLEMENTATION_ID,
            "runtime_selector": RUNTIME_SELECTOR,
            "scientific_selector_slot": SCIENTIFIC_SELECTOR,
            "tree": CANDIDATE_TREE,
        },
        "graph_program_sha256": program_sha,
        "leaf_catalog": catalog,
        "leaf_count": LEAF_COUNT,
        "plan": plan,
        "plan_sha256": plan_sha,
        "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "runtime_policy": {
            "automatic_retry": False,
            "child_wall_seconds": CHILD_WALL_SECONDS,
            "complete_wave_wall_seconds": WAVE_WALL_SECONDS,
            "maximum_concurrent_workers": WORKERS_PER_WAVE,
            "memory_limit_gib_per_process_tree": MEMORY_LIMIT_GIB,
            "numerical_library_threads_per_worker": THREADS_PER_WORKER,
        },
        "schema": SCHEMA,
        "stage4a_execution_authorized": False,
        "terminal": "VALIDATED_V6I_STAGE4A_GRAPH_NOT_EXECUTED",
        "v6h_authority_sha256": FROZEN_HASHES[V6H_AUTHORITY],
        "v6h_review_sha256": FROZEN_HASHES[V6H_REVIEW],
        "v6h_status_sha256": FROZEN_HASHES[V6H_STATUS],
        "wave_count": WAVE_COUNT,
        "waves": waves,
    }
    validate_graph(made)
    return made


def validate_graph(value: Mapping[str, Any]) -> None:
    expected = {
        "activation_authorized", "candidate", "graph_program_sha256", "leaf_catalog",
        "leaf_count", "plan", "plan_sha256", "production_restriction", "runtime_policy",
        "schema", "stage4a_execution_authorized", "terminal", "v6h_authority_sha256",
        "v6h_review_sha256", "v6h_status_sha256", "wave_count", "waves",
    }
    if set(value) != expected or value.get("schema") != SCHEMA:
        raise V6IError("V6I graph schema or keys differ")
    if (
        value["activation_authorized"] is not False
        or value["stage4a_execution_authorized"] is not False
        or value["leaf_count"] != LEAF_COUNT
        or value["wave_count"] != WAVE_COUNT
        or value["runtime_policy"]
        != {
            "automatic_retry": False,
            "child_wall_seconds": CHILD_WALL_SECONDS,
            "complete_wave_wall_seconds": WAVE_WALL_SECONDS,
            "maximum_concurrent_workers": WORKERS_PER_WAVE,
            "memory_limit_gib_per_process_tree": MEMORY_LIMIT_GIB,
            "numerical_library_threads_per_worker": THREADS_PER_WORKER,
        }
    ):
        raise V6IError("V6I graph policy differs")
    plan_raw = canonical_bytes(value["plan"])
    if sha256(plan_raw) != value["plan_sha256"]:
        raise V6IError("V6I plan hash differs")
    catalog = value["leaf_catalog"]
    waves = value["waves"]
    if not isinstance(catalog, list) or len(catalog) != LEAF_COUNT:
        raise V6IError("V6I leaf coverage differs")
    if not isinstance(waves, list) or len(waves) != WAVE_COUNT:
        raise V6IError("V6I wave coverage differs")
    expected_hashes = {str(leaf["leaf_assignment_sha256"]) for leaf in catalog}
    if len(expected_hashes) != LEAF_COUNT:
        raise V6IError("V6I leaf hashes are duplicated")
    observed: set[str] = set()
    for index, wave in enumerate(waves):
        if wave.get("wave_index") != index or wave.get("wave_id") != f"S3_V6I_STAGE4A_WAVE_{index + 1:02d}":
            raise V6IError("V6I wave order differs")
        workers = wave.get("workers")
        if not isinstance(workers, list) or len(workers) != WORKERS_PER_WAVE:
            raise V6IError("V6I worker count differs")
        if tuple(worker.get("diagonal") for worker in workers) != DIAGONALS:
            raise V6IError("V6I diagonal order differs")
        for worker in workers:
            observed.add(str(worker.get("leaf_assignment_sha256")))
    if observed != expected_hashes or len(observed) != LEAF_COUNT:
        raise V6IError("V6I wave-to-leaf coverage differs")


def _publish_exclusive(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())


def _ps_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def registered_command(
    *,
    graph_path: Path,
    wave_index: int,
    candidate_archive: Path,
    output_root: Path,
    authorization_path: Path,
    request_path: Path,
    result_path: Path,
    python_executable: Path | None = None,
) -> str:
    """Return the exact stored PowerShell command for one bounded wave."""

    executable = (python_executable or Path(sys.executable)).resolve()
    arguments = [
        str(executable), "-I", "-B", str(Path(__file__).resolve()),
        "--run-registered-wave", "--graph", str(graph_path.resolve()),
        "--wave-index", str(wave_index), "--candidate-archive",
        str(candidate_archive.resolve()), "--output-root", str(output_root.resolve()),
        "--authorization", str(authorization_path.resolve()), "--request",
        str(request_path.resolve()), "--result", str(result_path.resolve()),
    ]
    environment = [
        "$env:BLIS_NUM_THREADS='1'", "$env:MKL_NUM_THREADS='1'",
        "$env:NUMBA_NUM_THREADS='1'", "$env:NUMEXPR_NUM_THREADS='1'",
        "$env:OMP_NUM_THREADS='1'", "$env:OPENBLAS_NUM_THREADS='1'",
        "$env:TBB_NUM_THREADS='1'", "$env:PYTHONHASHSEED='0'",
        "$env:PYTHONNOUSERSITE='1'", "$env:PYTHONDONTWRITEBYTECODE='1'",
    ]
    return "; ".join(environment) + "; & " + " ".join(
        _ps_quote(part) for part in arguments
    )


def _configure_leaf_program(expected_sha256: str) -> ModuleType:
    if expected_sha256 != _program_sha256():
        raise V6IError("registered V6I executor hash differs")
    adapter = _load(ADAPTER, "_s3_v6i_adapter")
    base = adapter.configure()

    def require_v6i_program(expected: str) -> None:
        if expected != _program_sha256():
            raise V6IError("leaf executor program hash differs")

    base._require_current_producer_program = require_v6i_program
    return base


def run_flat_leaf(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--run-flat-leaf")
    parser.add_argument("--leaf-assignment-sha256")
    parser.add_argument("--selector")
    parser.add_argument("--candidate-source-root", type=Path)
    parser.add_argument("--candidate-archive", type=Path)
    parser.add_argument("--candidate-archive-sha256")
    parser.add_argument("--candidate-commit")
    parser.add_argument("--candidate-tree")
    parser.add_argument("--producer-program-sha256")
    parser.add_argument("--output")
    parser.add_argument("--progress")
    parsed = parser.parse_args(argv)
    if (
        parsed.candidate_archive_sha256 != CANDIDATE_ARCHIVE_SHA256
        or parsed.candidate_commit != CANDIDATE_COMMIT
        or parsed.candidate_tree != CANDIDATE_TREE
        or parsed.selector != SCIENTIFIC_SELECTOR
        or parsed.producer_program_sha256 != _program_sha256()
    ):
        raise V6IError("leaf command authority differs")
    _extract_archive_exclusive(parsed.candidate_archive, parsed.candidate_source_root)
    base = _configure_leaf_program(parsed.producer_program_sha256)
    return int(base.main(argv))


def _validate_authorization(
    path: Path, graph_raw: bytes, request_raw: bytes, wave_index: int
) -> dict[str, Any]:
    authorization, _ = strict_json(path)
    if set(authorization) != {
        "activation_authorized", "graph_sha256", "requests", "schema",
        "stage4a_execution_authorized",
    } or (
        authorization["schema"] != AUTHORIZATION_SCHEMA
        or authorization["activation_authorized"] is not False
        or authorization["stage4a_execution_authorized"] is not True
        or authorization["graph_sha256"] != sha256(graph_raw)
    ):
        raise V6IError("successor execution authorization differs")
    requests = authorization["requests"]
    if not isinstance(requests, list) or len(requests) != WAVE_COUNT:
        raise V6IError("successor request authority coverage differs")
    matches = [
        row
        for row in requests
        if isinstance(row, dict)
        and row.get("wave_index") == wave_index
        and row.get("request_sha256") == sha256(request_raw)
    ]
    if len(matches) != 1:
        raise V6IError("resource request is absent from successor authority")
    return authorization


def run_registered_wave(
    graph_path: Path,
    wave_index: int,
    candidate_archive: Path,
    output_root: Path,
    authorization_path: Path,
    request_path: Path,
    result_path: Path,
) -> dict[str, Any]:
    graph, graph_raw = strict_json(graph_path)
    validate_graph(graph)
    if graph["graph_program_sha256"] != _program_sha256():
        raise V6IError("frozen graph program differs")
    request, request_raw = strict_json(request_path)
    _validate_authorization(authorization_path, graph_raw, request_raw, wave_index)
    if set(request) != {
        "command", "estimate_minutes", "repository", "request_id", "requested_at",
        "status", "task",
    } or request.get("status") != "PENDING":
        raise V6IError("registered resource request differs")
    request_id = request["request_id"]
    expected_command = registered_command(
        graph_path=graph_path,
        wave_index=wave_index,
        candidate_archive=candidate_archive,
        output_root=output_root,
        authorization_path=authorization_path,
        request_path=request_path,
        result_path=result_path,
    )
    if (
        not isinstance(request_id, str)
        or len(request_id) != 32
        or any(character not in "0123456789abcdef" for character in request_id)
        or request_path.resolve().name != f"{request_id}.json"
        or request["command"] != expected_command
        or request["estimate_minutes"] != 30
        or Path(request["repository"]).resolve() != ROOT.resolve()
        or request["task"]
        != f"ANYsolver S3 V2D Stage 4A bounded wave {wave_index + 1:02d}"
        or not isinstance(request["requested_at"], str)
        or not request["requested_at"]
    ):
        raise V6IError("resource request command or identity differs")
    verify_archive(candidate_archive)
    output_root = output_root.resolve()
    output_root.mkdir(parents=True, exist_ok=False)
    plan_path = output_root / "stage4a-plan.json"
    _publish_exclusive(plan_path, canonical_bytes(graph["plan"]))
    wave = graph["waves"][wave_index]
    program = Path(__file__).resolve()
    program_sha = _program_sha256()
    workers: list[dict[str, Any]] = []
    catalog = {leaf["leaf_assignment_sha256"]: leaf for leaf in graph["leaf_catalog"]}
    for slot, worker in enumerate(wave["workers"]):
        leaf = catalog[worker["leaf_assignment_sha256"]]
        worker_root = output_root / f"worker-{slot + 1}"
        command = [
            sys.executable, str(program), "--run-flat-leaf", str(plan_path),
            "--leaf-assignment-sha256", worker["leaf_assignment_sha256"],
            "--selector", SCIENTIFIC_SELECTOR,
            "--candidate-source-root", str(worker_root / "candidate-source"),
            "--candidate-archive", str(candidate_archive.resolve()),
            "--candidate-archive-sha256", CANDIDATE_ARCHIVE_SHA256,
            "--candidate-commit", CANDIDATE_COMMIT,
            "--candidate-tree", CANDIDATE_TREE,
            "--producer-program-sha256", program_sha,
            "--output", str(worker_root / "scientific.json"),
            "--progress", str(worker_root / "progress.jsonl"),
        ]
        bindings = sorted(
            [
                {"path": str(candidate_archive.resolve()), "sha256": CANDIDATE_ARCHIVE_SHA256},
                {"path": str(plan_path), "sha256": graph["plan_sha256"]},
                {"path": str(program), "sha256": program_sha},
                {"path": str(ADAPTER), "sha256": FROZEN_HASHES[ADAPTER]},
                {"path": str(PRODUCER), "sha256": FROZEN_HASHES[PRODUCER]},
            ],
            key=lambda item: item["path"],
        )
        workers.append(
            {
                "assignment_id": leaf["leaf_id"],
                "assignment_sha256": worker["leaf_assignment_sha256"],
                "command": command,
                "cwd": str(ROOT),
                "expected_record_count": 1,
                "expected_selector": SCIENTIFIC_SELECTOR,
                "input_hashes": bindings,
                "plan_path": str(plan_path),
                "plan_sha256": graph["plan_sha256"],
                "progress_path": str(worker_root / "progress.jsonl"),
                "program_path": str(program),
                "program_sha256": program_sha,
                "scientific_path": str(worker_root / "scientific.json"),
                "scientific_schema": LEAF_SCIENTIFIC_SCHEMA,
                "stderr_path": str(worker_root / "stderr.bin"),
                "stdout_path": str(worker_root / "stdout.bin"),
                "wall_seconds": CHILD_WALL_SECONDS,
            }
        )
    bounded_manifest = {
        "lane": "flat-leaf",
        "output_root": str(output_root),
        "schema": "anysolver.e4-pl-s3-v2-bounded-wave-manifest-v1",
        "wave_id": wave["wave_id"],
        "workers": workers,
    }
    bounded_manifest_path = output_root / "bounded-manifest.json"
    _publish_exclusive(bounded_manifest_path, canonical_bytes(bounded_manifest))
    bounded = _load(BOUNDED, "_s3_v6i_bounded")
    bounded.MAX_CONCURRENT_WORKERS = WORKERS_PER_WAVE
    bounded.MAX_WORKER_WALL_SECONDS = CHILD_WALL_SECONDS
    bounded.WAVE_WALL_SECONDS = WAVE_WALL_SECONDS
    bounded.LANE_WALL_LIMITS["flat-leaf"] = CHILD_WALL_SECONDS
    bounded.JOB_MEMORY_LIMIT_BYTES = MEMORY_LIMIT_GIB * (1 << 30)
    bounded_result_path = output_root / "bounded-result.json"
    bounded_result = bounded.run_wave(bounded_manifest_path, bounded_result_path)
    wrapper = {
        "activation_authorized": False,
        "bounded_result_sha256": sha256(bounded_result_path.read_bytes()),
        "graph_sha256": sha256(graph_raw),
        "request_sha256": sha256(request_raw),
        "schema": RESULT_SCHEMA,
        "stage4a_execution_authorized": True,
        "terminal": bounded_result["terminal"],
        "wave_index": wave_index,
    }
    _publish_exclusive(result_path.resolve(), canonical_bytes(wrapper))
    return wrapper


def main(argv: Sequence[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments and arguments[0] == "--run-flat-leaf":
        return run_flat_leaf(arguments)
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--build-graph", action="store_true")
    mode.add_argument("--validate-graph", action="store_true")
    mode.add_argument("--run-registered-wave", action="store_true")
    parser.add_argument("--candidate-archive", type=Path)
    parser.add_argument("--graph", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--authorization", type=Path)
    parser.add_argument("--request", type=Path)
    parser.add_argument("--result", type=Path)
    parser.add_argument("--wave-index", type=int)
    args = parser.parse_args(arguments)
    if args.build_graph:
        if args.candidate_archive is None or args.output is None:
            raise V6IError("graph construction requires archive and output")
        _publish_exclusive(args.output.resolve(), canonical_bytes(build_graph(args.candidate_archive)))
        return 0
    if args.validate_graph:
        if args.graph is None:
            raise V6IError("graph validation requires --graph")
        value, _ = strict_json(args.graph)
        validate_graph(value)
        return 0
    required = (args.graph, args.candidate_archive, args.output_root, args.authorization, args.request, args.result)
    if any(item is None for item in required) or args.wave_index is None:
        raise V6IError("registered wave execution arguments are incomplete")
    made = run_registered_wave(
        args.graph, args.wave_index, args.candidate_archive, args.output_root,
        args.authorization, args.request, args.result,
    )
    return 0 if made["terminal"] == "COMPLETED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
