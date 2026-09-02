"""Bounded producer for the research-only V4D Hermite-edge screen."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import itertools
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

import e4_pl_s3_v4a_screen_producer as q4_source
import e4_pl_s3_v4c_screen_producer as physical_first


CONTRACT = REFERENCE / "e4_pl_s3_v4d_screen_contract.json"
FORMULATION_ID = "CANDIDATE_E4_PL_S3_V4D_Q4_SUBCELL_HERMITE_EDGE_FLAT_LINEAR_V1"
PROOF_SCHEMA = "anysolver.e4-pl-s3-v4d-hermite-edge-screen-proof-v1"
AGGREGATE_SCHEMA = "anysolver.e4-pl-s3-v4d-hermite-edge-screen-aggregate-v1"
NORMAL = np.asarray((0.0, 0.0, 1.0), dtype=np.float64)
PERMUTATIONS = tuple(itertools.permutations(range(3)))
DIAGONALS = ("slash", "backslash", "alternating")
THREAD_ENV = {"OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1", "NUMEXPR_NUM_THREADS": "1"}
MEMORY_LIMIT_BYTES = 24 * 1024**3


class ScreenError(RuntimeError):
    pass


canonical_bytes = q4_source.canonical_bytes
sha256_file = q4_source.sha256_file
load_canonical = q4_source.load_canonical
exclusive_write = q4_source.exclusive_write
array_payload = q4_source.array_payload
relative_inf = q4_source.relative_inf


def validate_authority() -> dict[str, Any]:
    contract = load_canonical(CONTRACT)
    if contract.get("schema") != "anysolver.e4-pl-s3-v4d-hermite-edge-screen-contract-v1":
        raise ScreenError("unexpected V4D screen contract")
    for item in contract["frozen_inputs"]:
        path = ROOT / item["path"]
        if not path.is_file() or path.is_symlink() or path.stat().st_size != item["bytes"] or sha256_file(path) != item["sha256"]:
            raise ScreenError(f"frozen input mismatch: {path}")
    prereg = load_canonical(REFERENCE / "e4_pl_s3_v4d_preregistration_result.json")
    if prereg.get("terminal") != "PROVISIONAL_GO_E4_PL_S3_V4D_BOUNDED_HERMITE_EDGE_SCREEN" or prereg.get("next_gate_authorized") is not True:
        raise ScreenError("V4D preregistration does not authorize this screen")
    return contract


def _hermite_restriction(vertices: np.ndarray) -> np.ndarray:
    made = np.zeros((42, 20), dtype=np.float64)
    for node in range(3):
        for component in range(5):
            made[6 * node + component, 5 * node + component] = 1.0
    for edge, (left, right) in enumerate(((0, 1), (1, 2), (2, 0))):
        point = edge + 3
        dx = float(vertices[right, 0] - vertices[left, 0])
        dy = float(vertices[right, 1] - vertices[left, 1])
        for component in (0, 1, 3, 4):
            made[6 * point + component, 5 * left + component] = 0.5
            made[6 * point + component, 5 * right + component] = 0.5
        made[6 * point + 2, 5 * left + 2] = 0.5
        made[6 * point + 2, 5 * right + 2] = 0.5
        made[6 * point + 2, 5 * left + 3] = dy / 8.0
        made[6 * point + 2, 5 * left + 4] = -dx / 8.0
        made[6 * point + 2, 5 * right + 3] = -dy / 8.0
        made[6 * point + 2, 5 * right + 4] = dx / 8.0
    made[36:41, 15:20] = np.eye(5)
    return made


def v4d_components(coordinates: Sequence[Sequence[float]], *, normal: Sequence[float] = NORMAL) -> dict[str, Any]:
    vertices = np.asarray(coordinates, dtype=np.float64)
    if vertices.shape == (3, 2):
        vertices = np.column_stack((vertices, np.zeros(3)))
    if vertices.shape != (3, 3) or not np.all(np.isfinite(vertices)):
        raise ScreenError("V4D vertices must be finite 3x2 or 3x3 coordinates")
    normal_array = np.asarray(normal, dtype=np.float64)
    normal_array /= np.linalg.norm(normal_array)
    points = q4_source._subcell_points(vertices)
    assembled = np.zeros((42, 42), dtype=np.float64)
    for subcell in ((0, 3, 6, 5), (1, 4, 6, 3), (2, 5, 6, 4)):
        core = q4_source._qualified_q4_components(points[np.asarray(subcell)], normal_array)["physical"]
        assembled += q4_source._embed(core, subcell, 7)
    restriction = _hermite_restriction(vertices)
    restricted = restriction.T @ assembled @ restriction
    internal_block = restricted[15:, 15:]
    internal_map = -np.linalg.solve(internal_block, restricted[15:, :15])
    transform = np.vstack((np.eye(15), internal_map))
    physical_15 = transform.T @ restricted @ transform
    physical_15 = 0.5 * (physical_15 + physical_15.T)
    embedding = physical_first._external_embedding()
    physical = embedding @ physical_15 @ embedding.T
    constraint, gram, pl, drill_scale = physical_first._native_pl(vertices)
    total = physical + pl
    return {
        "component_sum_relative_inf": relative_inf(physical + pl, total),
        "drill_scale": drill_scale,
        "embedding": embedding,
        "internal_block": internal_block,
        "internal_map": internal_map,
        "physical": physical,
        "physical_15": physical_15,
        "pl": pl,
        "pl_constraint": constraint,
        "pl_gram": gram,
        "restriction": restriction,
        "total": 0.5 * (total + total.T),
    }


def local_proof() -> dict[str, Any]:
    vertices = np.asarray(((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.2, 0.9, 0.0)))
    made = v4d_components(vertices)
    internal_rank = physical_first._rank(made["internal_block"], 1.0e-12)
    physical_rank = physical_first._rank(made["physical"])
    pl_rank = physical_first._rank(made["pl"])
    total_rank = physical_first._rank(made["total"])
    rigid_residual = float(np.linalg.norm(made["total"] @ q4_source._rigid_modes(vertices), ord=np.inf) / max(np.linalg.norm(made["total"], ord=np.inf), 1.0))
    d3_worst = 0.0
    reversal_worst = 0.0
    for order in PERMUTATIONS:
        permutation = q4_source._block_permutation(order)
        permuted = v4d_components(vertices[np.asarray(order)])
        d3_worst = max(d3_worst, relative_inf(permutation.T @ permuted["total"] @ permutation, made["total"]))
        reversed_made = v4d_components(vertices[np.asarray(order)], normal=-NORMAL)
        reversal_worst = max(reversal_worst, relative_inf(permutation.T @ reversed_made["total"] @ permutation, made["total"]))
    diagnostics = {
        "component_sum_relative_inf_hex": float(made["component_sum_relative_inf"]).hex(),
        "d3_worst_relative_inf_hex": d3_worst.hex(),
        "director_reversal_worst_relative_inf_hex": reversal_worst.hex(),
        "internal_physical_block_rank": internal_rank,
        "physical_rank": physical_rank,
        "pl_rank": pl_rank,
        "rigid_residual_relative_inf_hex": rigid_residual.hex(),
        "symmetry_relative_inf_hex": relative_inf(made["total"], made["total"].T).hex(),
        "total_rank": total_rank,
    }
    diagnostics["gate_passed"] = bool(internal_rank == 5 and physical_rank == 9 and pl_rank == 3 and total_rank == 12 and d3_worst <= 3.0e-12 and reversal_worst <= 3.0e-12 and rigid_residual <= 3.0e-12 and float.fromhex(diagnostics["symmetry_relative_inf_hex"]) <= 3.0e-13)
    payloads = {name: array_payload(np.asarray(value)) for name, value in made.items() if isinstance(value, np.ndarray)}
    return {"diagnostics": diagnostics, "payloads": payloads}


def _grid_operators(size: int, diagonal: str) -> dict[str, np.ndarray]:
    node_count = (size + 1) ** 2
    coordinates = np.asarray(tuple((i / size, j / size, 0.0) for j in range(size + 1) for i in range(size + 1)))
    q4 = np.zeros((6 * node_count, 6 * node_count), dtype=np.float64)
    s3 = np.zeros_like(q4)
    for j in range(size):
        for i in range(size):
            nodes = (j * (size + 1) + i, j * (size + 1) + i + 1, (j + 1) * (size + 1) + i + 1, (j + 1) * (size + 1) + i)
            q4 += q4_source._embed(q4_source._qualified_q4_components(coordinates[np.asarray(nodes)], NORMAL)["total"], nodes, node_count)
            for triangle in physical_first._cell_triangles(i, j, size, diagonal):
                s3 += q4_source._embed(v4d_components(coordinates[np.asarray(triangle)])["total"], triangle, node_count)
    boundary_nodes = tuple(node for node in range(node_count) if node % (size + 1) in {0, size} or node // (size + 1) in {0, size})
    interior_nodes = tuple(node for node in range(node_count) if node not in boundary_nodes)
    boundary = np.concatenate([np.arange(6 * node, 6 * node + 6) for node in boundary_nodes])
    interior = np.concatenate([np.arange(6 * node, 6 * node + 6) for node in interior_nodes]) if interior_nodes else np.asarray([], dtype=np.intp)

    def condense(matrix: np.ndarray) -> np.ndarray:
        bb = matrix[np.ix_(boundary, boundary)]
        if not interior.size:
            return bb
        bi = matrix[np.ix_(boundary, interior)]
        reduced = bb - bi @ np.linalg.solve(matrix[np.ix_(interior, interior)], bi.T)
        return 0.5 * (reduced + reduced.T)

    return {"boundary_coordinates": coordinates[np.asarray(boundary_nodes)], "q4": condense(q4), "s3": condense(s3)}


def macrocell_proof() -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    matrices: dict[str, Any] = {}
    worst = 0.0
    for size in (1, 2, 4):
        for diagonal in DIAGONALS:
            made = _grid_operators(size, diagonal)
            key = f"{size}x{size}:{diagonal}"
            matrices[key] = {name: array_payload(value) for name, value in made.items() if name != "boundary_coordinates"}
            traces: dict[str, Any] = {}
            for name, vector in physical_first._trace_modes(made["boundary_coordinates"]).items():
                q4_action = made["q4"] @ vector
                s3_action = made["s3"] @ vector
                residual = float(np.linalg.norm(s3_action - q4_action, ord=np.inf) / max(np.linalg.norm(q4_action, ord=np.inf), 1.0))
                traces[name] = {"action_relative_inf_hex": residual.hex()}
                worst = max(worst, residual)
            records.append({"diagonal": diagonal, "full_operator_relative_inf_hex": relative_inf(made["s3"], made["q4"]).hex(), "size": size, "trace_modes": traces})
    return {"diagnostics": {"gate_passed": worst <= 3.0e-12, "record_count": len(records), "trace_worst_relative_inf_hex": worst.hex()}, "matrices": matrices, "records": records}


def produce_proof() -> dict[str, Any]:
    validate_authority()
    local = local_proof()
    base = {"candidate_formulation_id": FORMULATION_ID, "contract_sha256": sha256_file(CONTRACT), "local": local, "production_boundary": {"anymesh_untouched": True, "default_q4_formulation": "e4-pl", "default_s3_formulation": "legacy-s3", "q4_mechanics_unchanged": True}, "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED", "schema": PROOF_SCHEMA, "stage4a_rerun_authorized": False}
    if not local["diagnostics"]["gate_passed"]:
        return base | {"development_records": [], "later_stages": "NOT_EXECUTED_LOCAL_GATE_FAILED", "macrocell": {}}
    macrocell = macrocell_proof()
    if not macrocell["diagnostics"]["gate_passed"]:
        return base | {"development_records": [], "later_stages": "NOT_EXECUTED_MACROCELL_GATE_FAILED", "macrocell": macrocell}
    return base | {"development_records": [], "later_stages": "DEVELOPMENT_IMPLEMENTATION_REQUIRED_AFTER_MACROCELL_PASS", "macrocell": macrocell}


def adjudicate(*, identical: bool, report: Mapping[str, Any]) -> str:
    if not identical or not report.get("authority_complete"):
        return "BLOCKED_E4_PL_S3_V4D_PROCESS_OR_EVIDENCE"
    if not report.get("construction_identity_passed"):
        return "NO_GO_E4_PL_S3_V4D_CONSTRUCTION_IDENTITY"
    if not report.get("local_operator_passed"):
        return "NO_GO_E4_PL_S3_V4D_LOCAL_OPERATOR"
    if not report.get("mixed_interface_passed"):
        return "NO_GO_E4_PL_S3_V4D_MIXED_INTERFACE"
    return "PROVISIONAL_GO_E4_PL_S3_V4D_STAGE4A_RERUN"


def run_bounded(output_root: Path, *, timeout_seconds: int = 600, wave_timeout_seconds: int = 1800) -> dict[str, Any]:
    validate_authority()
    if timeout_seconds not in range(1, 601) or wave_timeout_seconds not in range(1, 1801):
        raise ScreenError("requested limits exceed the frozen process bounds")
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=False)
    progress = root / "progress.jsonl"
    progress.touch(exist_ok=False)
    deadline = time.monotonic() + wave_timeout_seconds
    checker = REFERENCE / "e4_pl_s3_v4d_screen_checker.py"
    cycles: list[dict[str, Any]] = []
    terminal = "BLOCKED_E4_PL_S3_V4D_PROCESS_OR_EVIDENCE"
    try:
        for cycle in (1, 2):
            cycle_root = root / f"cycle-{cycle}"
            cycle_root.mkdir()
            proof = cycle_root / "proof.json"
            checks = (cycle_root / "checker-a.json", cycle_root / "checker-b.json")
            with progress.open("ab") as stream:
                stream.write(canonical_bytes({"cycle": cycle, "phase": "INITIALIZATION", "sequence": 0}))
            remaining = int(max(1, min(timeout_seconds, deadline - time.monotonic())))
            physical_first._run_child([sys.executable, str(Path(__file__).resolve()), "--emit-proof", "--output", str(proof)], remaining)
            commands = [[sys.executable, str(checker), "--verify-proof", str(proof), "--output", str(path)] for path in checks]
            with ThreadPoolExecutor(max_workers=2) as pool:
                futures = [pool.submit(physical_first._run_child, command, int(max(1, min(timeout_seconds, deadline - time.monotonic())))) for command in commands]
                for future in futures:
                    future.result()
            identical = checks[0].read_bytes() == checks[1].read_bytes()
            report = load_canonical(checks[0])
            terminal = adjudicate(identical=identical, report=report)
            cycles.append({"checker_replicas_byte_identical": identical, "checker_sha256": sha256_file(checks[0]), "cycle": cycle, "proof_bytes": proof.stat().st_size, "proof_sha256": sha256_file(proof), "terminal": terminal})
            with progress.open("ab") as stream:
                stream.write(canonical_bytes({"cycle": cycle, "phase": "CYCLE_COMPLETE", "sequence": 1}))
        if cycles[0]["proof_sha256"] != cycles[1]["proof_sha256"] or cycles[0]["checker_sha256"] != cycles[1]["checker_sha256"]:
            terminal = "BLOCKED_E4_PL_S3_V4D_PROCESS_OR_EVIDENCE"
    except BaseException as exc:
        cycles.append({"error_class": type(exc).__name__, "status": "FAILED_BOUNDED_CHILD"})
        terminal = "BLOCKED_E4_PL_S3_V4D_PROCESS_OR_EVIDENCE"
    aggregate = {"activation_authorized": False, "candidate_formulation_id": FORMULATION_ID, "contract_sha256": sha256_file(CONTRACT), "cycles": cycles, "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED", "schema": AGGREGATE_SCHEMA, "stage4a_rerun_authorized": terminal == "PROVISIONAL_GO_E4_PL_S3_V4D_STAGE4A_RERUN", "terminal": terminal}
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
