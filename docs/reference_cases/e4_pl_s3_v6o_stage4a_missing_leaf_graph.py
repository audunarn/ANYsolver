"""V6O graph/executor for only the 12 Stage-4A leaves absent after V6M.

The full frozen Phase-4A plan remains the source of every leaf assignment.
V6O rebuilds that catalog against the mechanics-equivalent optimized archive,
then selects exactly predecessor waves 24--27.  The 69 completed V6M records
are never launched again.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
from pathlib import Path
import stat
import sys
from types import ModuleType
from typing import Any, Mapping, Sequence


SCHEMA = "anysolver.e4-pl-s3-v6o-stage4a-missing-leaf-graph-v1"
AUTHORIZATION_SCHEMA = "anysolver.e4-pl-s3-v6o-stage4a-missing-leaf-authorization-v1"
REFERENCE = Path(__file__).resolve().parent
BASE_PROGRAM = REFERENCE / "e4_pl_s3_v6m_stage4a_execution_graph.py"
BASE_PROGRAM_SHA256 = "1716245399502F66CC93D1EAE3839AF5A4FF9150FEC3F2287B28348C181C0771"
V6N_RESULT = REFERENCE / "e4_pl_s3_v6n_lease_optimization_result.json"
V6N_RESULT_SHA256 = "ACC2B116E1A08B0AF2F0F3F2C3242A82FE8B54A3057F18DEE85A8900AD34ACE5"

CANDIDATE_ARCHIVE_BYTES = 30_320_640
CANDIDATE_ARCHIVE_SHA256 = "DBEFBF12554832962C375F0CD827BE5310E0507145A5B6C84CFD68EB9BC2ABA1"
CANDIDATE_COMMIT = "c1e2ad91fdcc604fe3b568e6838d95769cee7bcd"
CANDIDATE_TREE = "ec61f802b63fff10a49fe25e04a1b5040cd03164"
SOURCE_WAVE_INDICES = (23, 24, 25, 26)
WAVE_COUNT = 4
LEAF_COUNT = 12
MISSING_RECORD_IDS = (
    "N80:10PCT:dispersed:slash",
    "N80:10PCT:dispersed:backslash",
    "N80:10PCT:dispersed:alternating",
    "N80:10PCT:chain:slash",
    "N80:10PCT:chain:backslash",
    "N80:10PCT:chain:alternating",
    "N80:25PCT:dispersed:slash",
    "N80:25PCT:dispersed:backslash",
    "N80:25PCT:dispersed:alternating",
    "N80:25PCT:chain:slash",
    "N80:25PCT:chain:backslash",
    "N80:25PCT:chain:alternating",
)


class V6OError(RuntimeError):
    """Raised when the missing-leaf successor differs."""


def _regular_sha256(path: Path) -> str:
    information = path.resolve().lstat()
    if not stat.S_ISREG(information.st_mode) or path.is_symlink():
        raise V6OError(f"frozen input is not a regular file: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _load_base() -> ModuleType:
    if _regular_sha256(BASE_PROGRAM) != BASE_PROGRAM_SHA256:
        raise V6OError("frozen V6M graph/executor differs")
    spec = importlib.util.spec_from_file_location("_s3_v6o_base_graph", BASE_PROGRAM)
    if spec is None or spec.loader is None:
        raise V6OError("cannot load frozen V6M graph/executor")
    module = importlib.util.module_from_spec(spec)
    sys.modules["_s3_v6o_base_graph"] = module
    spec.loader.exec_module(module)
    return module


_BASE = _load_base()
_V6L = _BASE._BASE
_V6K = _BASE._V6K
_V6I = _BASE._V6I
canonical_bytes = _BASE.canonical_bytes
strict_json = _BASE.strict_json
sha256 = _BASE.sha256
CHILD_WALL_SECONDS = _BASE.CHILD_WALL_SECONDS
WAVE_WALL_SECONDS = _BASE.WAVE_WALL_SECONDS
MEMORY_LIMIT_GIB = _BASE.MEMORY_LIMIT_GIB
MAXIMUM_CONCURRENT_WORKERS = _BASE.MAXIMUM_CONCURRENT_WORKERS
REGISTERED_WORKERS_PER_WAVE = _BASE.REGISTERED_WORKERS_PER_WAVE
DIAGONALS = ("slash", "backslash", "alternating")
ROOT = _V6I.ROOT


def _program_sha256() -> str:
    return _regular_sha256(Path(__file__))


def _configure_candidate() -> None:
    if _regular_sha256(V6N_RESULT) != V6N_RESULT_SHA256:
        raise V6OError("accepted V6N optimization result differs")
    for module in (_BASE, _V6L, _V6K, _V6I):
        module.CANDIDATE_ARCHIVE_BYTES = CANDIDATE_ARCHIVE_BYTES
        module.CANDIDATE_ARCHIVE_SHA256 = CANDIDATE_ARCHIVE_SHA256
        module.CANDIDATE_COMMIT = CANDIDATE_COMMIT
        module.CANDIDATE_TREE = CANDIDATE_TREE


def verify_archive(path: Path) -> None:
    """Expose exact optimized-archive verification to authority tooling."""

    _configure_candidate()
    _V6I.verify_archive(path.resolve())


def _configure_execution() -> None:
    _configure_candidate()
    _BASE.__file__ = str(Path(__file__).resolve())
    _BASE._program_sha256 = _program_sha256
    _BASE.validate_graph = validate_graph
    _BASE.AUTHORIZATION_SCHEMA = AUTHORIZATION_SCHEMA
    _BASE._prepare_execution_base()
    # The deepest frozen executor validates authorization cardinality itself.
    # V6O deliberately owns four fresh requests, not the predecessor's 27.
    _V6I.WAVE_COUNT = WAVE_COUNT


def build_graph(candidate_archive: Path) -> dict[str, Any]:
    """Rebuild the full frozen catalog, then retain only missing leaves."""

    _configure_candidate()
    previous_program = _BASE._program_sha256
    try:
        _BASE._program_sha256 = _program_sha256
        full = _BASE.build_graph(candidate_archive)
    finally:
        _BASE._program_sha256 = previous_program
    selected_source_waves = [full["waves"][index] for index in SOURCE_WAVE_INDICES]
    selected_hashes = {
        worker["leaf_assignment_sha256"]
        for wave in selected_source_waves
        for worker in wave["workers"]
    }
    selected_catalog = [
        leaf
        for leaf in full["leaf_catalog"]
        if leaf["leaf_assignment_sha256"] in selected_hashes
    ]
    waves: list[dict[str, Any]] = []
    for index, (source_index, source_wave) in enumerate(
        zip(SOURCE_WAVE_INDICES, selected_source_waves)
    ):
        made_wave = copy.deepcopy(source_wave)
        made_wave["source_wave_index"] = source_index
        made_wave["wave_id"] = f"S3_V6O_STAGE4A_MISSING_WAVE_{index + 1:02d}"
        made_wave["wave_index"] = index
        waves.append(made_wave)
    made = copy.deepcopy(full)
    made.update(
        {
            "leaf_catalog": selected_catalog,
            "leaf_count": LEAF_COUNT,
            "predecessor": {
                "completed_record_count": 69,
                "missing_record_count": LEAF_COUNT,
                "terminal": "BLOCKED_E4_PL_S3_V6M_PROCESS_OR_EVIDENCE",
            },
            "repair_authority": {
                "optimized_candidate_archive_sha256": CANDIDATE_ARCHIVE_SHA256,
                "v6n_result_sha256": V6N_RESULT_SHA256,
            },
            "schema": SCHEMA,
            "source_wave_indices": list(SOURCE_WAVE_INDICES),
            "terminal": "VALIDATED_V6O_MISSING_LEAF_GRAPH_NOT_EXECUTED",
            "wave_count": WAVE_COUNT,
            "waves": waves,
        }
    )
    validate_graph(made)
    return made


def validate_graph(value: Mapping[str, Any]) -> None:
    expected_keys = {
        "activation_authorized",
        "candidate",
        "graph_program_sha256",
        "leaf_catalog",
        "leaf_count",
        "plan",
        "plan_sha256",
        "predecessor",
        "production_restriction",
        "repair_authority",
        "runtime_policy",
        "schema",
        "source_wave_indices",
        "stage4a_execution_authorized",
        "terminal",
        "v6h_authority_sha256",
        "v6h_review_sha256",
        "v6h_status_sha256",
        "wave_count",
        "waves",
    }
    candidate = value.get("candidate")
    policy = value.get("runtime_policy")
    if (
        set(value) != expected_keys
        or value.get("schema") != SCHEMA
        or value.get("activation_authorized") is not False
        or value.get("stage4a_execution_authorized") is not False
        or value.get("leaf_count") != LEAF_COUNT
        or value.get("wave_count") != WAVE_COUNT
        or value.get("source_wave_indices") != list(SOURCE_WAVE_INDICES)
        or value.get("graph_program_sha256") != _program_sha256()
        or not isinstance(candidate, dict)
        or candidate.get("archive_bytes") != CANDIDATE_ARCHIVE_BYTES
        or candidate.get("archive_sha256") != CANDIDATE_ARCHIVE_SHA256
        or candidate.get("commit") != CANDIDATE_COMMIT
        or candidate.get("tree") != CANDIDATE_TREE
        or not isinstance(policy, dict)
        or policy.get("child_wall_seconds") != CHILD_WALL_SECONDS
        or policy.get("complete_wave_wall_seconds") != WAVE_WALL_SECONDS
        or policy.get("maximum_concurrent_workers") != MAXIMUM_CONCURRENT_WORKERS
        or policy.get("memory_limit_gib_per_process_tree") != MEMORY_LIMIT_GIB
        or policy.get("automatic_retry") is not False
        or value.get("predecessor")
        != {
            "completed_record_count": 69,
            "missing_record_count": LEAF_COUNT,
            "terminal": "BLOCKED_E4_PL_S3_V6M_PROCESS_OR_EVIDENCE",
        }
        or value.get("repair_authority")
        != {
            "optimized_candidate_archive_sha256": CANDIDATE_ARCHIVE_SHA256,
            "v6n_result_sha256": V6N_RESULT_SHA256,
        }
    ):
        raise V6OError("V6O graph identity or policy differs")
    if sha256(canonical_bytes(value["plan"])) != value.get("plan_sha256"):
        raise V6OError("V6O plan hash differs")
    catalog = value.get("leaf_catalog")
    waves = value.get("waves")
    if not isinstance(catalog, list) or len(catalog) != LEAF_COUNT:
        raise V6OError("V6O leaf catalog coverage differs")
    if not isinstance(waves, list) or len(waves) != WAVE_COUNT:
        raise V6OError("V6O wave coverage differs")
    catalog_by_hash: dict[str, Mapping[str, Any]] = {}
    for leaf in catalog:
        if not isinstance(leaf, Mapping) or not isinstance(leaf.get("assignment"), Mapping):
            raise V6OError("V6O leaf is malformed")
        digest = str(leaf.get("leaf_assignment_sha256"))
        assignment = leaf["assignment"]
        if (
            sha256(canonical_bytes(assignment)) != digest
            or leaf.get("leaf_id") != f"S3_V2_FLAT_4A_LEAF_{digest}"
            or assignment.get("candidate_archive_sha256") != CANDIDATE_ARCHIVE_SHA256
            or assignment.get("candidate_commit") != CANDIDATE_COMMIT
            or assignment.get("candidate_tree") != CANDIDATE_TREE
            or assignment.get("producer_program_sha256") != _program_sha256()
            or digest in catalog_by_hash
        ):
            raise V6OError("V6O leaf authority differs")
        catalog_by_hash[digest] = leaf
    observed_ids: list[str] = []
    observed_hashes: set[str] = set()
    for index, wave in enumerate(waves):
        if (
            not isinstance(wave, Mapping)
            or wave.get("wave_index") != index
            or wave.get("source_wave_index") != SOURCE_WAVE_INDICES[index]
            or wave.get("wave_id") != f"S3_V6O_STAGE4A_MISSING_WAVE_{index + 1:02d}"
        ):
            raise V6OError("V6O wave identity differs")
        workers = wave.get("workers")
        if (
            not isinstance(workers, list)
            or len(workers) != REGISTERED_WORKERS_PER_WAVE
            or tuple(worker.get("diagonal") for worker in workers) != DIAGONALS
        ):
            raise V6OError("V6O worker grouping differs")
        for worker in workers:
            digest = str(worker.get("leaf_assignment_sha256"))
            leaf = catalog_by_hash.get(digest)
            if (
                leaf is None
                or worker.get("leaf_id") != leaf.get("leaf_id")
                or worker.get("record_id") != leaf["assignment"].get("record_id")
                or digest in observed_hashes
            ):
                raise V6OError("V6O wave-to-leaf binding differs")
            observed_hashes.add(digest)
            observed_ids.append(str(worker["record_id"]))
    if tuple(observed_ids) != MISSING_RECORD_IDS or observed_hashes != set(catalog_by_hash):
        raise V6OError("V6O missing-record coverage differs")


def registered_command(**arguments: Any) -> str:
    _configure_execution()
    return str(_BASE.registered_command(**arguments))


def run_flat_leaf(argv: Sequence[str]) -> int:
    _configure_execution()
    return int(_BASE.run_flat_leaf(argv))


def run_registered_wave(
    graph_path: Path,
    wave_index: int,
    candidate_archive: Path,
    output_root: Path,
    authorization_path: Path,
    request_path: Path,
    result_path: Path,
) -> dict[str, Any]:
    _configure_execution()
    return dict(
        _BASE.run_registered_wave(
            graph_path,
            wave_index,
            candidate_archive,
            output_root,
            authorization_path,
            request_path,
            result_path,
        )
    )


def _publish_exclusive(path: Path, raw: bytes) -> None:
    _V6L._BASE_PUBLISH(path, raw)


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
            raise V6OError("graph construction requires archive and output")
        _publish_exclusive(
            args.output.resolve(),
            canonical_bytes(build_graph(args.candidate_archive.resolve())),
        )
        return 0
    if args.validate_graph:
        if args.graph is None:
            raise V6OError("graph validation requires --graph")
        graph, _ = strict_json(args.graph.resolve())
        validate_graph(graph)
        return 0
    required = (
        args.graph,
        args.candidate_archive,
        args.output_root,
        args.authorization,
        args.request,
        args.result,
    )
    if any(item is None for item in required) or args.wave_index is None:
        raise V6OError("registered execution arguments are incomplete")
    made = run_registered_wave(
        args.graph.resolve(),
        args.wave_index,
        args.candidate_archive.resolve(),
        args.output_root.resolve(),
        args.authorization.resolve(),
        args.request.resolve(),
        args.result.resolve(),
    )
    return 0 if made["terminal"] == "COMPLETED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
