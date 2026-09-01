"""Bounded V2C Stage 4B modal, buckling, and mixed-performance gate.

The reviewed numerical procedures are reused from the historical Stage 4B
lane, but model construction and elastic prestress are replaced by the
source-authorized V2C policies.  Raw timings remain external diagnostics.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import copy
from dataclasses import dataclass, replace
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace
from typing import Any, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "docs/reference_cases"
INPUT = REFERENCE / "e4_pl_s3_v5i_stage4b_input.json"
HISTORICAL_LANE = REFERENCE / "e4_pl_s3_mixed_eigen_performance.py"
MODEL_RUNNER = REFERENCE / "e4_pl_s3_mixed_mesh_qualification_runner.py"
SMOKE_INPUT = REFERENCE / "e4_pl_s3_mixed_mesh_smoke_input.json"
PROCESS_GUARD = REFERENCE / "e4_pl_s3_v2_bounded_process.py"
AUTHORIZATION_SCHEMA = "anysolver.e4-pl-s3-v5i-stage4b-execution-authorization-v1"
WORKER_SCHEMA = "anysolver.e4-pl-s3-v5i-stage4b-worker-v1"
COMMON_SCHEMA = "anysolver.e4-pl-s3-v5i-stage4b-common-v1"
AGGREGATE_SCHEMA = "anysolver.e4-pl-s3-v5i-stage4b-aggregate-v1"
FORMULATION_ID = "CANDIDATE_E4_PL_S3_V2C_FLAT_LINEAR_PARITY_V1"
PRODUCTION_RESTRICTION = "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"
PASS = "PASS_MEASURED_REGISTERED_SCOPE"
FAIL = "FAIL_MEASURED_CONTRADICTION"
BLOCKED_STATUS = "BLOCKED_PROCESS_OR_MALFORMED_MECHANICS"
BLOCKED = "BLOCKED_E4_PL_S3_V5I_STAGE4B_PROCESS_OR_EVIDENCE"
NO_GO_EIGEN = "NO_GO_E4_PL_S3_V5I_MIXED_EIGEN"
NO_GO_PERFORMANCE = "NO_GO_E4_PL_S3_V5I_MIXED_PERFORMANCE"
PASS_TERMINAL = "PROVISIONAL_GO_E4_PL_S3_V5I_STAGE4B_CLOSED_ONLY"
CHILD_TIMEOUT_SECONDS = 600
WAVE_TIMEOUT_SECONDS = 1800
MEMORY_LIMIT_GIB = 24
WORKER_CONCURRENCY = 3
CYCLES = 2
WORKER_IDS = (
    "MODAL_MIXED_10",
    "MODAL_MIXED_25",
    "BUCKLING_MIXED_10",
    "BUCKLING_MIXED_25",
    "PERFORMANCE_ALL_Q4",
    "PERFORMANCE_MIXED_10",
    "PERFORMANCE_MIXED_25",
)


class Stage4BError(RuntimeError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
        + "\n"
    ).encode("ascii")


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def _pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    made: dict[str, Any] = {}
    for key, value in items:
        if key in made:
            raise Stage4BError(f"duplicate JSON key: {key}")
        made[key] = value
    return made


def load_canonical(path: Path) -> tuple[bytes, dict[str, Any]]:
    raw = path.read_bytes()
    value = json.loads(
        raw,
        object_pairs_hook=_pairs,
        parse_constant=lambda token: (_ for _ in ()).throw(
            Stage4BError(f"nonfinite JSON token: {token}")
        ),
    )
    if not isinstance(value, dict) or raw != canonical_bytes(value):
        raise Stage4BError(f"noncanonical JSON: {path}")
    return raw, value


def exclusive_write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(canonical_bytes(value))


def _load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise Stage4BError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _git(*arguments: str) -> str:
    process = subprocess.run(
        ["git", *arguments], cwd=ROOT, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if process.returncode:
        raise Stage4BError(process.stderr.strip() or "git command failed")
    return process.stdout.strip()


def _validate_bindings(payload: Mapping[str, Any]) -> None:
    bindings = payload.get("frozen_inputs")
    if not isinstance(bindings, list) or not bindings:
        raise Stage4BError("frozen_inputs must be a nonempty array")
    paths: list[str] = []
    for row in bindings:
        if not isinstance(row, dict) or set(row) != {"bytes", "path", "sha256"}:
            raise Stage4BError("malformed frozen input binding")
        relative = row["path"]
        if not isinstance(relative, str) or Path(relative).is_absolute():
            raise Stage4BError("frozen input path must be repository-relative")
        path = (ROOT / relative).resolve(strict=True)
        if not path.is_relative_to(ROOT.resolve()):
            raise Stage4BError("frozen input escapes repository")
        raw = path.read_bytes()
        if len(raw) != row["bytes"] or sha256_bytes(raw) != row["sha256"]:
            raise Stage4BError(f"frozen input mismatch: {relative}")
        paths.append(relative)
    if len(paths) != len(set(paths)):
        raise Stage4BError("frozen input bindings must be unique")


def load_input(path: Path = INPUT) -> tuple[bytes, dict[str, Any]]:
    raw, payload = load_canonical(path)
    if payload.get("schema") != "anysolver.e4-pl-s3-v5i-stage4b-input-v1":
        raise Stage4BError("unexpected V5I input schema")
    _validate_bindings(payload)
    if payload.get("candidate_formulation_id") != FORMULATION_ID:
        raise Stage4BError("candidate formulation identity changed")
    execution = payload.get("execution", {})
    if execution != {
        "automatic_retry": False,
        "canonical_cycles": CYCLES,
        "child_timeout_seconds": CHILD_TIMEOUT_SECONDS,
        "complete_wave_timeout_seconds": WAVE_TIMEOUT_SECONDS,
        "memory_limit_gib_per_process_tree": MEMORY_LIMIT_GIB,
        "numerical_library_threads_per_process": 1,
        "worker_concurrency": WORKER_CONCURRENCY,
    }:
        raise Stage4BError("execution bounds changed")
    if payload.get("worker_ids") != list(WORKER_IDS):
        raise Stage4BError("worker coverage changed")
    boundary = payload.get("production_boundary", {})
    if boundary != {
        "activation_authorized": False,
        "default_q4_formulation": "e4-pl",
        "default_s3_formulation": "legacy-s3",
        "q4_mechanics_unchanged": True,
    }:
        raise Stage4BError("production boundary changed")
    return raw, payload


def validate_authorization(path: Path, input_raw: bytes, payload: Mapping[str, Any]) -> dict[str, Any]:
    _raw, authorization = load_canonical(path)
    if authorization.get("schema") != AUTHORIZATION_SCHEMA:
        raise Stage4BError("unexpected execution authorization schema")
    if authorization.get("input_sha256") != sha256_bytes(input_raw):
        raise Stage4BError("execution authorization binds another input")
    if authorization.get("execution_authorized") is not True:
        raise Stage4BError("Stage 4B execution is not authorized")
    if authorization.get("activation_authorized") is not False:
        raise Stage4BError("execution authorization must not activate S3")
    authority = authorization.get("authority", {})
    commit = authority.get("commit")
    if not isinstance(commit, str) or len(commit) != 40:
        raise Stage4BError("invalid authority commit")
    if _git("show", "-s", "--format=%H", commit) != commit:
        raise Stage4BError("authority commit is unavailable")
    expected = payload["authority_commit"]
    if (
        _git("show", "-s", "--format=%P", commit) != expected["expected_parent"]
        or _git("show", "-s", "--format=%s", commit) != expected["expected_subject"]
    ):
        raise Stage4BError("authority commit identity mismatch")
    changed = sorted(
        item for item in _git("diff-tree", "--no-commit-id", "--name-only", "-r", commit).splitlines() if item
    )
    if changed != expected["exact_paths"]:
        raise Stage4BError("authority commit extent mismatch")
    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", commit, "HEAD"], cwd=ROOT,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
    ).returncode:
        raise Stage4BError("current HEAD does not descend from authority")
    review_path = ROOT / authorization.get("protocol_review_path", "")
    if not review_path.is_file() or sha256_file(review_path) != authorization.get("protocol_review_sha256"):
        raise Stage4BError("protocol review binding mismatch")
    review = load_canonical(review_path)[1]
    if review.get("verdict") != "ACCEPT_S3_V5I_STAGE4B_PROTOCOL_NO_P0_P1":
        raise Stage4BError("protocol review is not accepted")
    return authorization


def _lane_and_model(payload: Mapping[str, Any]) -> tuple[Any, Any, Any]:
    lane = _load_module("_v5i_historical_lane", HISTORICAL_LANE)
    runner = _load_module("_v5i_model_runner", MODEL_RUNNER)
    smoke = runner.load_authorities(SMOKE_INPUT)
    model_payload = copy.deepcopy(smoke.input_payload)
    model_payload["factories"]["s3"] = {
        "class_module": "anysolver.e4_pl_s3_v2c_element",
        "class_name": "StrictFlatLinearE4PLS3V2CShellElement",
        "formulation_id": FORMULATION_ID,
        "selector": "e4-pl-s3-v2c",
    }
    smoke = replace(smoke, input_payload=model_payload)
    authorities = SimpleNamespace(
        input={"coverage": payload["lane"]},
        contract=smoke.contract,
        input_raw=canonical_bytes(payload),
    )
    cache: dict[tuple[int, bool], Any] = {}

    def build(_authorities: Any, fraction: int, *, auxiliary: bool) -> Any:
        key = (int(fraction), bool(auxiliary))
        if key not in cache:
            row = lane._topology_rows(authorities.input)[int(fraction)]
            spec = {
                "case_id": f"V5I_N20_{int(fraction)}PCT_DISPERSED_ALTERNATING",
                "topology": {
                    name: row[name]
                    for name in (
                        "connectivity_sha256", "diagonal", "level", "mask",
                        "split_base_cell_count",
                    )
                },
            }
            built = runner.build_case_model(
                smoke, spec, include_auxiliary_inputs=bool(auxiliary)
            )
            # The historical builder predates physical-normal authority on Q4.
            # Reconstruct the same Q4 instances with the frozen owner normal;
            # all mechanics and numerical options remain byte-for-byte selected
            # from the same model input.
            from anysolver.elements import create_shell_element

            section = model_payload["model"]["section"]
            material_name = str(model_payload["model"]["material"]["name"])
            normal = model_payload["model"]["coordinates"]["owner_normal"]
            for element_id, kind in built.element_kinds.items():
                if kind != "Q4":
                    continue
                old = built.model.mesh.elements[element_id]
                built.model.mesh.elements[element_id] = create_shell_element(
                    int(element_id), list(old.node_ids), material_name,
                    formulation="e4-pl",
                    thickness=float(section["thickness"]),
                    drilling_stabilization=float(section["q4_drilling_stabilization"]),
                    hourglass_stabilization=float(section["q4_hourglass_stabilization"]),
                    pl_stabilization=float(section["q4_pl_stabilization"]),
                    planar_tolerance=float(section["q4_planar_tolerance"]),
                    warped_formulation=str(section["q4_warped_formulation"]),
                    reference_normal=normal,
                    director_polarity=1,
                )
            cache[key] = built
        return cache[key]

    def states(model: Any, spec: Mapping[str, Any]) -> dict[int, dict[str, Any]]:
        import numpy as np
        from anysolver.e4_pl_element import equation7_frame

        tensor = np.asarray(spec["physical_global_membrane_compression_tensor"], dtype=float)
        result: dict[int, dict[str, Any]] = {}
        for element_id, element in model.mesh.elements.items():
            if getattr(element, "formulation_id", None) == FORMULATION_ID:
                coordinates = np.asarray(
                    [model.mesh.nodes[node_id].coords() for node_id in element.node_ids],
                    dtype=float,
                )
                normal = np.asarray(element.reference_normal, dtype=float)
                signed = float(np.cross(coordinates[1] - coordinates[0], coordinates[2] - coordinates[0]) @ normal)
                if signed < 0.0:
                    coordinates = coordinates[[0, 2, 1]]
                first = coordinates[1] - coordinates[0]
                first /= float(np.linalg.norm(first))
                second = np.cross(normal, first)
                second /= float(np.linalg.norm(second))
                frame = np.column_stack((first, second, normal))
            else:
                frame = np.asarray(
                    equation7_frame(element.get_node_coordinates(model.mesh))[0],
                    dtype=float,
                )
            local = frame[:, :2].T @ tensor @ frame[:, :2]
            membrane = [float(local[0, 0]), float(local[1, 1]), float(local[0, 1])]
            if getattr(element, "formulation_id", None) == FORMULATION_ID:
                second = [0.0, 0.0, 0.0]
            else:
                factor = float(element.thickness) ** 2 / 12.0
                second = [float(value * factor) for value in membrane]
            result[int(element_id)] = {
                "bending_compression": [0.0, 0.0, 0.0],
                "membrane_compression": membrane,
                "stress_second_moment": second,
            }
        return result

    lane._build_case = build
    lane._reference_elastic_states = states
    return lane, runner, authorities


def run_worker(input_raw: bytes, payload: Mapping[str, Any], worker_id: str) -> dict[str, Any]:
    lane, _runner, authorities = _lane_and_model(payload)
    started = time.perf_counter()
    if worker_id == "MODAL_MIXED_10":
        status, diagnostics = lane._modal_worker(authorities, 10)
    elif worker_id == "MODAL_MIXED_25":
        status, diagnostics = lane._modal_worker(authorities, 25)
    elif worker_id == "BUCKLING_MIXED_10":
        status, diagnostics = lane._buckling_worker(authorities, 10)
    elif worker_id == "BUCKLING_MIXED_25":
        status, diagnostics = lane._buckling_worker(authorities, 25)
    elif worker_id.startswith("PERFORMANCE_"):
        fraction = {"PERFORMANCE_ALL_Q4": 0, "PERFORMANCE_MIXED_10": 10, "PERFORMANCE_MIXED_25": 25}[worker_id]
        status, diagnostics = lane._performance_worker(authorities, fraction)
    else:
        raise Stage4BError(f"unknown worker {worker_id}")
    diagnostics["elapsed_seconds_total"] = float(time.perf_counter() - started)
    return {
        "authority_sha256": sha256_bytes(input_raw),
        "common": {
            "candidate_formulation_id": FORMULATION_ID,
            "gate_status": status,
            "production_restriction": PRODUCTION_RESTRICTION,
            "worker_id": worker_id,
        },
        "diagnostics": diagnostics,
        "schema": WORKER_SCHEMA,
        "worker_id": worker_id,
    }


@dataclass(frozen=True)
class ProcessResult:
    worker_id: str
    status: str
    returncode: int
    directory: Path


def _environment() -> dict[str, str]:
    env = dict(os.environ)
    paths = [str(ROOT / "src"), str(REFERENCE)]
    for parent in (ROOT, *ROOT.parents):
        for repository in ("ANYfileIO", "ANYgeometry", "ANYmaterial", "ANYmesh"):
            candidate = parent / repository / "src"
            if candidate.is_dir():
                paths.append(str(candidate))
    if env.get("PYTHONPATH"):
        paths.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(dict.fromkeys(paths))
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        env[name] = "1"
    env["PYTHONHASHSEED"] = "0"
    return env


def _launch_worker(worker_id: str, cycle_root: Path, input_path: Path, authorization: Path, timeout: int) -> ProcessResult:
    guard = _load_module(f"_v5i_guard_{worker_id}", PROCESS_GUARD)
    directory = cycle_root / "workers" / worker_id.lower()
    directory.mkdir(parents=True, exist_ok=False)
    record = directory / "record.json"
    job = guard._ProcessJob(MEMORY_LIMIT_GIB * 1024**3)
    command = [
        sys.executable, str(Path(__file__).resolve()), "--worker", worker_id,
        "--input", str(input_path), "--authorization", str(authorization),
        "--output", str(record),
    ]
    with (directory / "stdout.log").open("xb") as stdout, (directory / "stderr.log").open("xb") as stderr:
        try:
            process = job.launch(command, cwd=ROOT, env=_environment(), stdout=stdout, stderr=stderr)
            try:
                code = process.wait(timeout=timeout)
                status = "COMPLETE" if code == 0 else "FAILED"
            except subprocess.TimeoutExpired:
                status, code = "TIMEOUT", -9
                if not job.terminate():
                    status = "TERMINATION_FAILED"
        finally:
            job.close()
    if status != "COMPLETE":
        record.unlink(missing_ok=True)
    return ProcessResult(worker_id, status, int(code), directory)


def _combined_status(values: Sequence[str]) -> str:
    if BLOCKED_STATUS in values:
        return BLOCKED_STATUS
    if FAIL in values:
        return FAIL
    return PASS


def _cycle(input_raw: bytes, payload: Mapping[str, Any], input_path: Path, authorization: Path, root: Path, deadline: float) -> tuple[bytes, dict[str, Any]]:
    root.mkdir(parents=True, exist_ok=False)
    results: list[ProcessResult] = []
    first = WORKER_IDS[:4]
    with ThreadPoolExecutor(max_workers=WORKER_CONCURRENCY) as pool:
        futures = {
            pool.submit(
                _launch_worker, worker_id, root, input_path, authorization,
                min(CHILD_TIMEOUT_SECONDS, max(1, int(deadline - time.monotonic()))),
            ): worker_id for worker_id in first
        }
        for future in as_completed(futures):
            results.append(future.result())
    for worker_id in WORKER_IDS[4:]:
        results.append(
            _launch_worker(
                worker_id, root, input_path, authorization,
                min(CHILD_TIMEOUT_SECONDS, max(1, int(deadline - time.monotonic()))),
            )
        )
    by_id = {result.worker_id: result for result in results}
    records: dict[str, dict[str, Any]] = {}
    blocked: list[str] = []
    for worker_id in WORKER_IDS:
        result = by_id[worker_id]
        if result.status != "COMPLETE":
            blocked.append(worker_id)
            continue
        try:
            record = load_canonical(result.directory / "record.json")[1]
            if (
                record.get("schema") != WORKER_SCHEMA
                or record.get("worker_id") != worker_id
                or record.get("authority_sha256") != sha256_bytes(input_raw)
            ):
                raise Stage4BError("worker authority mismatch")
            records[worker_id] = record
        except (OSError, Stage4BError, json.JSONDecodeError):
            blocked.append(worker_id)
    modal_values = [
        status for worker_id in WORKER_IDS[:2]
        for status in records.get(worker_id, {"common": {"gate_status": {"missing": BLOCKED_STATUS}}})["common"]["gate_status"].values()
    ]
    buckling_values = [
        status for worker_id in WORKER_IDS[2:4]
        for status in records.get(worker_id, {"common": {"gate_status": {"missing": BLOCKED_STATUS}}})["common"]["gate_status"].values()
    ]
    performance_status = BLOCKED_STATUS
    performance_diagnostic: dict[str, Any] = {}
    performance_records = [records.get(worker_id) for worker_id in WORKER_IDS[4:]]
    if all(record is not None for record in performance_records):
        measured = [record for record in performance_records if record is not None]
        if all(record["common"]["gate_status"].get("performance_measurement") == PASS for record in measured):
            by_fraction = {int(record["diagnostics"]["fraction_percent"]): record["diagnostics"] for record in measured}
            reference = by_fraction[0]
            limit = 1.0 + float(payload["lane"]["performance_regression_maximum"])
            values: list[str] = []
            for fraction in (10, 25):
                candidate = by_fraction[fraction]
                assembly = candidate["assembly"]["median_seconds"] / reference["assembly"]["median_seconds"]
                solve = candidate["production_end_to_end_solve"]["median_seconds"] / reference["production_end_to_end_solve"]["median_seconds"]
                rr, cr = reference.get("peak_rss_bytes"), candidate.get("peak_rss_bytes")
                rss = float(cr) / float(rr) if isinstance(rr, int) and rr > 0 and isinstance(cr, int) else None
                statuses = {
                    "assembly": PASS if math.isfinite(assembly) and assembly <= limit else FAIL,
                    "solve": PASS if math.isfinite(solve) and solve <= limit else FAIL,
                    "rss": BLOCKED_STATUS if rss is None else PASS if math.isfinite(rss) and rss <= limit else FAIL,
                }
                values.extend(statuses.values())
                performance_diagnostic[str(fraction)] = {"assembly_ratio": assembly, "solve_ratio": solve, "rss_ratio": rss, "gate_status": statuses}
            performance_status = _combined_status(values)
    gates = {
        "buckling": _combined_status(buckling_values),
        "modal": _combined_status(modal_values),
        "mixed_performance": performance_status,
    }
    if blocked or BLOCKED_STATUS in gates.values():
        terminal = BLOCKED
    elif FAIL in (gates["modal"], gates["buckling"]):
        terminal = NO_GO_EIGEN
    elif gates["mixed_performance"] == FAIL:
        terminal = NO_GO_PERFORMANCE
    else:
        terminal = PASS_TERMINAL
    common = {
        "activation_authorized": False,
        "authority_sha256": sha256_bytes(input_raw),
        "candidate_formulation_id": FORMULATION_ID,
        "coverage": {"buckling_factors": 5, "fractions_percent": [0, 10, 25], "modal_elastic_modes": 10, "performance_repetitions": 11, "worker_ids": list(WORKER_IDS)},
        "gate_status": gates,
        "next_gate": "V5J_V2C_BATCH_RESTART_AND_PACKAGE_PARITY" if terminal == PASS_TERMINAL else None,
        "production_restriction": PRODUCTION_RESTRICTION,
        "schema": COMMON_SCHEMA,
        "terminal": terminal,
    }
    diagnostic = {
        "blocked_workers": blocked,
        "performance": performance_diagnostic,
        "processes": [{"returncode": result.returncode, "status": result.status, "worker_id": result.worker_id} for result in sorted(results, key=lambda item: WORKER_IDS.index(item.worker_id))],
        "workers": {worker_id: records.get(worker_id, {}).get("diagnostics") for worker_id in WORKER_IDS},
    }
    exclusive_write(root / "common.json", common)
    exclusive_write(root / "diagnostic.json", diagnostic)
    return canonical_bytes(common), common


def adjudicate(cycles: Sequence[Mapping[str, Any]], *, byte_identical: bool, process_complete: bool = True) -> str:
    if not process_complete or len(cycles) != CYCLES or not byte_identical:
        return BLOCKED
    terminals = [cycle.get("terminal") for cycle in cycles]
    if BLOCKED in terminals:
        return BLOCKED
    if NO_GO_EIGEN in terminals:
        return NO_GO_EIGEN
    if NO_GO_PERFORMANCE in terminals:
        return NO_GO_PERFORMANCE
    return PASS_TERMINAL if terminals == [PASS_TERMINAL, PASS_TERMINAL] else BLOCKED


def run_two_cycles(input_path: Path, authorization: Path, output_root: Path) -> dict[str, Any]:
    input_raw, payload = load_input(input_path)
    validate_authorization(authorization, input_raw, payload)
    if output_root.exists():
        raise Stage4BError("exclusive output root already exists")
    output_root.mkdir(parents=True)
    deadline = time.monotonic() + WAVE_TIMEOUT_SECONDS
    raws: list[bytes] = []
    cycles: list[dict[str, Any]] = []
    error: str | None = None
    try:
        for cycle in (1, 2):
            raw, common = _cycle(input_raw, payload, input_path, authorization, output_root / f"cycle-{cycle}", deadline)
            raws.append(raw)
            cycles.append(common)
    except (Stage4BError, OSError, subprocess.SubprocessError, TimeoutError) as exc:
        error = f"{type(exc).__name__}:{exc}"
    identical = len(raws) == 2 and raws[0] == raws[1]
    terminal = adjudicate(cycles, byte_identical=identical, process_complete=error is None)
    aggregate = {
        "activation_authorized": False,
        "authority_sha256": sha256_bytes(input_raw),
        "candidate_formulation_id": FORMULATION_ID,
        "common_sha256": sha256_bytes(raws[0]) if raws else None,
        "cycles_byte_identical": identical,
        "error": error,
        "execution_bounds": payload["execution"],
        "next_gate": "V5J_V2C_BATCH_RESTART_AND_PACKAGE_PARITY" if terminal == PASS_TERMINAL else None,
        "production_restriction": PRODUCTION_RESTRICTION,
        "schema": AGGREGATE_SCHEMA,
        "terminal": terminal,
    }
    exclusive_write(output_root / "aggregate.json", aggregate)
    return aggregate


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=INPUT)
    parser.add_argument("--authorization", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--worker", choices=WORKER_IDS)
    parser.add_argument("--run-v5i-stage4b", action="store_true")
    args = parser.parse_args(argv)
    input_raw, payload = load_input(args.input)
    validate_authorization(args.authorization, input_raw, payload)
    if args.worker:
        if args.output is None or args.output_root is not None or args.run_v5i_stage4b:
            parser.error("--worker requires only --output")
        exclusive_write(args.output, run_worker(input_raw, payload, args.worker))
        return 0
    if not args.run_v5i_stage4b or args.output_root is None or args.output is not None:
        parser.error("--run-v5i-stage4b requires only --output-root")
    result = run_two_cycles(args.input, args.authorization, args.output_root)
    return 0 if result["terminal"] == PASS_TERMINAL else 2


if __name__ == "__main__":
    raise SystemExit(main())
