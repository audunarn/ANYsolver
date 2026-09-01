"""Bounded producer for the research-only V4B midpoint-drill-release screen."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import itertools
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Mapping, Sequence

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "docs" / "reference_cases"
if str(REFERENCE) not in sys.path:
    sys.path.insert(0, str(REFERENCE))

import e4_pl_s3_v4a_screen_producer as predecessor


CONTRACT = REFERENCE / "e4_pl_s3_v4b_screen_contract.json"
FORMULATION_ID = "CANDIDATE_E4_PL_S3_V4B_Q4_SUBCELL_DRILL_RELEASE_FLAT_LINEAR_V1"
PROOF_SCHEMA = "anysolver.e4-pl-s3-v4b-drill-release-screen-proof-v1"
AGGREGATE_SCHEMA = "anysolver.e4-pl-s3-v4b-drill-release-screen-aggregate-v1"
NORMAL = np.asarray((0.0, 0.0, 1.0), dtype=np.float64)
PERMUTATIONS = tuple(itertools.permutations(range(3)))
THREAD_ENV = {"OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1", "NUMEXPR_NUM_THREADS": "1"}
MEMORY_LIMIT_BYTES = 24 * 1024**3


class ScreenError(RuntimeError):
    pass


canonical_bytes = predecessor.canonical_bytes
sha256_bytes = predecessor.sha256_bytes
sha256_file = predecessor.sha256_file
load_canonical = predecessor.load_canonical
exclusive_write = predecessor.exclusive_write
array_payload = predecessor.array_payload
relative_inf = predecessor.relative_inf


def validate_authority() -> dict[str, Any]:
    contract = load_canonical(CONTRACT)
    if contract.get("schema") != "anysolver.e4-pl-s3-v4b-drill-release-screen-contract-v1":
        raise ScreenError("unexpected V4B screen contract")
    for item in contract["frozen_inputs"]:
        path = ROOT / item["path"]
        if not path.is_file() or path.is_symlink() or path.stat().st_size != item["bytes"] or sha256_file(path) != item["sha256"]:
            raise ScreenError(f"frozen input mismatch: {path}")
    prereg = load_canonical(REFERENCE / "e4_pl_s3_v4b_preregistration_result.json")
    if prereg.get("terminal") != "PROVISIONAL_GO_E4_PL_S3_V4B_BOUNDED_DRILL_RELEASE_SCREEN" or prereg.get("next_gate_authorized") is not True:
        raise ScreenError("V4B preregistration does not authorize this screen")
    return contract


def _drill_release_restriction() -> np.ndarray:
    made = np.zeros((42, 27), dtype=np.float64)
    for node in range(3):
        made[6 * node : 6 * node + 6, 6 * node : 6 * node + 6] = np.eye(6)
    for edge, (left, right) in enumerate(((0, 1), (1, 2), (2, 0))):
        point = edge + 3
        for component in range(5):
            made[6 * point + component, 6 * left + component] = 0.5
            made[6 * point + component, 6 * right + component] = 0.5
        made[6 * point + 5, 18 + edge] = 1.0
    made[36:42, 21:27] = np.eye(6)
    return made


def v4b_components(coordinates: Sequence[Sequence[float]], *, normal: Sequence[float] = NORMAL) -> dict[str, Any]:
    vertices = np.asarray(coordinates, dtype=np.float64)
    if vertices.shape == (3, 2):
        vertices = np.column_stack((vertices, np.zeros(3)))
    if vertices.shape != (3, 3) or not np.all(np.isfinite(vertices)):
        raise ScreenError("V4B vertices must be finite 3x2 or 3x3 coordinates")
    normal_array = np.asarray(normal, dtype=np.float64)
    normal_array /= np.linalg.norm(normal_array)
    points = predecessor._subcell_points(vertices)
    assembled = {name: np.zeros((42, 42), dtype=np.float64) for name in ("physical", "pl", "hourglass", "total")}
    for subcell in ((0, 3, 6, 5), (1, 4, 6, 3), (2, 5, 6, 4)):
        local = predecessor._qualified_q4_components(points[np.asarray(subcell)], normal_array)
        for name in assembled:
            assembled[name] += predecessor._embed(local[name], subcell, 7)
    restriction = _drill_release_restriction()
    restricted = {name: restriction.T @ value @ restriction for name, value in assembled.items()}
    total = restricted["total"]
    internal_block = total[18:, 18:]
    internal_map = -np.linalg.solve(internal_block, total[18:, :18])
    condensation = np.vstack((np.eye(18), internal_map))
    condensed: dict[str, np.ndarray] = {}
    for name, value in restricted.items():
        transformed = condensation.T @ value @ condensation
        condensed[name] = 0.5 * (transformed + transformed.T)
    return condensed | {
        "component_sum_relative_inf": relative_inf(condensed["physical"] + condensed["pl"] + condensed["hourglass"], condensed["total"]),
        "internal_block": internal_block,
        "internal_map": internal_map,
        "restriction": restriction,
    }


def _rank(matrix: np.ndarray, relative: float) -> int:
    singular = np.linalg.svd(matrix, compute_uv=False)
    return int(np.count_nonzero(singular > max(float(singular[0]), 1.0) * relative))


def local_proof() -> dict[str, Any]:
    vertices = np.asarray(((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.2, 0.9, 0.0)))
    made = v4b_components(vertices)
    internal_rank = _rank(made["internal_block"], 1.0e-12)
    physical_rank = _rank(made["physical"], 1.0e-10)
    total_rank = _rank(made["total"], 1.0e-10)
    rigid_residual = float(np.linalg.norm(made["total"] @ predecessor._rigid_modes(vertices), ord=np.inf) / max(np.linalg.norm(made["total"], ord=np.inf), 1.0))
    d3_worst = 0.0
    reversal_worst = 0.0
    for order in PERMUTATIONS:
        permutation = predecessor._block_permutation(order)
        permuted = v4b_components(vertices[np.asarray(order)])
        d3_worst = max(d3_worst, relative_inf(permutation.T @ permuted["total"] @ permutation, made["total"]))
        reversed_made = v4b_components(vertices[np.asarray(order)], normal=-NORMAL)
        reversal_worst = max(reversal_worst, relative_inf(permutation.T @ reversed_made["total"] @ permutation, made["total"]))
    diagnostics = {
        "component_sum_relative_inf_hex": float(made["component_sum_relative_inf"]).hex(),
        "d3_worst_relative_inf_hex": d3_worst.hex(),
        "director_reversal_worst_relative_inf_hex": reversal_worst.hex(),
        "internal_total_block_rank": internal_rank,
        "physical_rank": physical_rank,
        "rigid_residual_relative_inf_hex": rigid_residual.hex(),
        "symmetry_relative_inf_hex": relative_inf(made["total"], made["total"].T).hex(),
        "total_rank": total_rank,
    }
    diagnostics["gate_passed"] = bool(
        internal_rank == 9
        and physical_rank == 9
        and total_rank == 12
        and float.fromhex(diagnostics["component_sum_relative_inf_hex"]) <= 3.0e-13
        and d3_worst <= 3.0e-12
        and reversal_worst <= 3.0e-12
        and rigid_residual <= 3.0e-12
        and float.fromhex(diagnostics["symmetry_relative_inf_hex"]) <= 3.0e-13
    )
    payloads = {name: array_payload(np.asarray(value)) for name, value in made.items() if isinstance(value, np.ndarray)}
    return {"diagnostics": diagnostics, "payloads": payloads}


def macrocell_pair(diagonal: str) -> dict[str, np.ndarray]:
    xy = {1: (0.0, 0.0, 0.0), 2: (1.0, 0.0, 0.0), 3: (1.0, 1.0, 0.0), 4: (0.0, 1.0, 0.0)}
    s3 = np.zeros((24, 24), dtype=np.float64)
    for nodes in predecessor._connectivity(diagonal):
        local = v4b_components([xy[node] for node in nodes])["total"]
        s3 += predecessor._embed(local, tuple(node - 1 for node in nodes), 4)
    return {"q4": predecessor._q4_macrocell(), "s3": s3}


def macrocell_proof() -> dict[str, Any]:
    comparisons: dict[str, Any] = {}
    matrices: dict[str, Any] = {}
    trace_worst = 0.0
    for diagonal in predecessor.DIAGONALS:
        pair = macrocell_pair(diagonal)
        matrices[diagonal] = {name: array_payload(value) for name, value in pair.items()}
        rows: dict[str, Any] = {}
        for name, vector in predecessor._macro_modes().items():
            residual = float(np.linalg.norm(pair["s3"] @ vector - pair["q4"] @ vector, ord=np.inf) / max(np.linalg.norm(pair["q4"] @ vector, ord=np.inf), 1.0))
            rows[name] = {"action_relative_inf_hex": residual.hex()}
            trace_worst = max(trace_worst, residual)
        comparisons[diagonal] = {"full_operator_relative_inf_hex": relative_inf(pair["s3"], pair["q4"]).hex(), "trace_modes": rows}
    return {"comparisons": comparisons, "diagnostics": {"gate_passed": trace_worst <= 3.0e-12, "trace_worst_relative_inf_hex": trace_worst.hex()}, "matrices": matrices}


def produce_proof() -> dict[str, Any]:
    validate_authority()
    local = local_proof()
    base = {
        "candidate_formulation_id": FORMULATION_ID,
        "contract_sha256": sha256_file(CONTRACT),
        "local": local,
        "production_boundary": {"anymesh_untouched": True, "default_q4_formulation": "e4-pl", "default_s3_formulation": "legacy-s3", "q4_mechanics_unchanged": True},
        "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "schema": PROOF_SCHEMA,
        "stage4a_rerun_authorized": False,
    }
    if not local["diagnostics"]["gate_passed"]:
        return base | {"development_records": [], "later_stages": "NOT_EXECUTED_LOCAL_GATE_FAILED", "macrocell": {}}
    macrocell = macrocell_proof()
    if not macrocell["diagnostics"]["gate_passed"]:
        return base | {"development_records": [], "later_stages": "NOT_EXECUTED_MACROCELL_GATE_FAILED", "macrocell": macrocell}
    return base | {"development_records": [], "later_stages": "DEVELOPMENT_IMPLEMENTATION_REQUIRED_AFTER_MACROCELL_PASS", "macrocell": macrocell}


def adjudicate(*, identical: bool, report: Mapping[str, Any]) -> str:
    if not identical or not report.get("authority_complete"):
        return "BLOCKED_E4_PL_S3_V4B_PROCESS_OR_EVIDENCE"
    if not report.get("construction_identity_passed"):
        return "NO_GO_E4_PL_S3_V4B_CONSTRUCTION_IDENTITY"
    if not report.get("local_operator_passed"):
        return "NO_GO_E4_PL_S3_V4B_LOCAL_OPERATOR"
    if not report.get("mixed_interface_passed"):
        return "NO_GO_E4_PL_S3_V4B_MIXED_INTERFACE"
    return "PROVISIONAL_GO_E4_PL_S3_V4B_STAGE4A_RERUN"


def _run_child(command: list[str], timeout_seconds: int) -> None:
    from e4_pl_s3_v2_bounded_process import _ProcessJob

    environment = os.environ.copy()
    environment.update(THREAD_ENV)
    job = _ProcessJob(MEMORY_LIMIT_BYTES)
    try:
        process = job.launch(command, cwd=ROOT, env=environment, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            return_code = process.wait(timeout=timeout_seconds)
        except subprocess.TimeoutExpired as exc:
            if not job.terminate(124):
                raise ScreenError("timed-out process tree did not drain") from exc
            raise ScreenError("bounded child timed out") from exc
        _cpu, active, peak = job.accounting()
        if active or peak > MEMORY_LIMIT_BYTES:
            job.terminate(125)
            raise ScreenError("bounded child retained descendants or exceeded memory")
        if return_code:
            raise ScreenError(f"bounded child failed with exit code {return_code}")
    finally:
        job.close()


def run_bounded(output_root: Path, *, timeout_seconds: int = 600, wave_timeout_seconds: int = 1800) -> dict[str, Any]:
    validate_authority()
    if timeout_seconds not in range(1, 601) or wave_timeout_seconds not in range(1, 1801):
        raise ScreenError("requested limits exceed the frozen process bounds")
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=False)
    progress = root / "progress.jsonl"
    progress.touch(exist_ok=False)
    deadline = time.monotonic() + wave_timeout_seconds
    checker = REFERENCE / "e4_pl_s3_v4b_screen_checker.py"
    cycles: list[dict[str, Any]] = []
    terminal = "BLOCKED_E4_PL_S3_V4B_PROCESS_OR_EVIDENCE"
    try:
        for cycle in (1, 2):
            cycle_root = root / f"cycle-{cycle}"
            cycle_root.mkdir()
            proof = cycle_root / "proof.json"
            checks = (cycle_root / "checker-a.json", cycle_root / "checker-b.json")
            with progress.open("ab") as stream:
                stream.write(canonical_bytes({"cycle": cycle, "phase": "INITIALIZATION", "sequence": 0}))
            remaining = int(max(1, min(timeout_seconds, deadline - time.monotonic())))
            _run_child([sys.executable, str(Path(__file__).resolve()), "--emit-proof", "--output", str(proof)], remaining)
            commands = [[sys.executable, str(checker), "--verify-proof", str(proof), "--output", str(path)] for path in checks]
            with ThreadPoolExecutor(max_workers=2) as pool:
                futures = [pool.submit(_run_child, command, int(max(1, min(timeout_seconds, deadline - time.monotonic())))) for command in commands]
                for future in futures:
                    future.result()
            identical = checks[0].read_bytes() == checks[1].read_bytes()
            report = load_canonical(checks[0])
            terminal = adjudicate(identical=identical, report=report)
            cycles.append({"checker_replicas_byte_identical": identical, "checker_sha256": sha256_file(checks[0]), "cycle": cycle, "proof_bytes": proof.stat().st_size, "proof_sha256": sha256_file(proof), "terminal": terminal})
            with progress.open("ab") as stream:
                stream.write(canonical_bytes({"cycle": cycle, "phase": "CYCLE_COMPLETE", "sequence": 1}))
        if cycles[0]["proof_sha256"] != cycles[1]["proof_sha256"] or cycles[0]["checker_sha256"] != cycles[1]["checker_sha256"]:
            terminal = "BLOCKED_E4_PL_S3_V4B_PROCESS_OR_EVIDENCE"
    except BaseException as exc:
        cycles.append({"error_class": type(exc).__name__, "status": "FAILED_BOUNDED_CHILD"})
        terminal = "BLOCKED_E4_PL_S3_V4B_PROCESS_OR_EVIDENCE"
    aggregate = {"activation_authorized": False, "candidate_formulation_id": FORMULATION_ID, "contract_sha256": sha256_file(CONTRACT), "cycles": cycles, "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED", "schema": AGGREGATE_SCHEMA, "stage4a_rerun_authorized": terminal == "PROVISIONAL_GO_E4_PL_S3_V4B_STAGE4A_RERUN", "terminal": terminal}
    exclusive_write(root / "aggregate.json", aggregate)
    return aggregate


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--emit-proof", action="store_true")
    mode.add_argument("--run-bounded", action="store_true")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--timeout-seconds", type=int, default=600)
    parser.add_argument("--wave-timeout-seconds", type=int, default=1800)
    args = parser.parse_args(argv)
    if args.emit_proof:
        if args.output is None:
            raise ScreenError("--output is required")
        exclusive_write(args.output, produce_proof())
    else:
        if args.output_root is None:
            raise ScreenError("--output-root is required")
        run_bounded(args.output_root, timeout_seconds=args.timeout_seconds, wave_timeout_seconds=args.wave_timeout_seconds)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
