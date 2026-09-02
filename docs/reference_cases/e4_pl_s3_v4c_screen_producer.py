"""Bounded producer for the research-only V4C physical-first screen."""

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
import e4_pl_s3_v4b_screen_producer as bounded_source


CONTRACT = REFERENCE / "e4_pl_s3_v4c_screen_contract.json"
FORMULATION_ID = "CANDIDATE_E4_PL_S3_V4C_Q4_SUBCELL_PHYSICAL_FIRST_FLAT_LINEAR_V1"
PROOF_SCHEMA = "anysolver.e4-pl-s3-v4c-physical-first-screen-proof-v1"
AGGREGATE_SCHEMA = "anysolver.e4-pl-s3-v4c-physical-first-screen-aggregate-v1"
YOUNG = 210_000_000_000.0
POISSON = 0.3
THICKNESS = 0.01
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
    if contract.get("schema") != "anysolver.e4-pl-s3-v4c-physical-first-screen-contract-v1":
        raise ScreenError("unexpected V4C screen contract")
    for item in contract["frozen_inputs"]:
        path = ROOT / item["path"]
        if not path.is_file() or path.is_symlink() or path.stat().st_size != item["bytes"] or sha256_file(path) != item["sha256"]:
            raise ScreenError(f"frozen input mismatch: {path}")
    prereg = load_canonical(REFERENCE / "e4_pl_s3_v4c_preregistration_result.json")
    if prereg.get("terminal") != "PROVISIONAL_GO_E4_PL_S3_V4C_BOUNDED_PHYSICAL_FIRST_SCREEN" or prereg.get("next_gate_authorized") is not True:
        raise ScreenError("V4C preregistration does not authorize this screen")
    return contract


def _physical_restriction() -> np.ndarray:
    made = np.zeros((42, 20), dtype=np.float64)
    for node in range(3):
        for component in range(5):
            made[6 * node + component, 5 * node + component] = 1.0
    for edge, (left, right) in enumerate(((0, 1), (1, 2), (2, 0))):
        point = edge + 3
        for component in range(5):
            made[6 * point + component, 5 * left + component] = 0.5
            made[6 * point + component, 5 * right + component] = 0.5
    for component in range(5):
        made[36 + component, 15 + component] = 1.0
    return made


def _external_embedding() -> np.ndarray:
    made = np.zeros((18, 15), dtype=np.float64)
    for node in range(3):
        for component in range(5):
            made[6 * node + component, 5 * node + component] = 1.0
    return made


def _native_pl(vertices: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    local = np.asarray(vertices[:, :2], dtype=np.float64)
    jacobian = np.asarray(
        ((local[1, 0] - local[0, 0], local[1, 1] - local[0, 1]), (local[2, 0] - local[0, 0], local[2, 1] - local[0, 1])),
        dtype=np.float64,
    )
    determinant = float(np.linalg.det(jacobian))
    inverse = np.linalg.inv(jacobian)
    derivative_r = np.asarray((-1.0, 1.0, 0.0))
    derivative_s = np.asarray((-1.0, 0.0, 1.0))
    derivative_x = inverse[0, 0] * derivative_r + inverse[0, 1] * derivative_s
    derivative_y = inverse[1, 0] * derivative_r + inverse[1, 1] * derivative_s
    constraint = np.zeros((3, 18), dtype=np.float64)
    for row in range(3):
        constraint[row, 0::6] = 0.5 * derivative_y
        constraint[row, 1::6] = -0.5 * derivative_x
        constraint[row, 6 * row + 5] = 1.0
    gram = (abs(determinant) / 24.0) * np.asarray(((2.0, 1.0, 1.0), (1.0, 2.0, 1.0), (1.0, 1.0, 2.0)))
    drill_scale = THICKNESS * YOUNG / (2.0 * (1.0 + POISSON))
    pl = drill_scale * constraint.T @ gram @ constraint
    return constraint, gram, 0.5 * (pl + pl.T), drill_scale


def v4c_components(coordinates: Sequence[Sequence[float]], *, normal: Sequence[float] = NORMAL) -> dict[str, Any]:
    vertices = np.asarray(coordinates, dtype=np.float64)
    if vertices.shape == (3, 2):
        vertices = np.column_stack((vertices, np.zeros(3)))
    if vertices.shape != (3, 3) or not np.all(np.isfinite(vertices)):
        raise ScreenError("V4C vertices must be finite 3x2 or 3x3 coordinates")
    normal_array = np.asarray(normal, dtype=np.float64)
    normal_array /= np.linalg.norm(normal_array)
    points = q4_source._subcell_points(vertices)
    assembled = np.zeros((42, 42), dtype=np.float64)
    for subcell in ((0, 3, 6, 5), (1, 4, 6, 3), (2, 5, 6, 4)):
        core = q4_source._qualified_q4_components(points[np.asarray(subcell)], normal_array)["physical"]
        assembled += q4_source._embed(core, subcell, 7)
    restriction = _physical_restriction()
    restricted = restriction.T @ assembled @ restriction
    internal_block = restricted[15:, 15:]
    internal_map = -np.linalg.solve(internal_block, restricted[15:, :15])
    condensation = np.vstack((np.eye(15), internal_map))
    physical_15 = condensation.T @ restricted @ condensation
    physical_15 = 0.5 * (physical_15 + physical_15.T)
    embedding = _external_embedding()
    physical = embedding @ physical_15 @ embedding.T
    constraint, gram, pl, drill_scale = _native_pl(vertices)
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


def _rank(matrix: np.ndarray, relative: float = 1.0e-10) -> int:
    singular = np.linalg.svd(matrix, compute_uv=False)
    return int(np.count_nonzero(singular > max(float(singular[0]), 1.0) * relative))


def local_proof() -> dict[str, Any]:
    vertices = np.asarray(((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.2, 0.9, 0.0)))
    made = v4c_components(vertices)
    internal_rank = _rank(made["internal_block"], 1.0e-12)
    physical_rank = _rank(made["physical"])
    pl_rank = _rank(made["pl"])
    total_rank = _rank(made["total"])
    rigid_residual = float(np.linalg.norm(made["total"] @ q4_source._rigid_modes(vertices), ord=np.inf) / max(np.linalg.norm(made["total"], ord=np.inf), 1.0))
    d3_worst = 0.0
    reversal_worst = 0.0
    for order in PERMUTATIONS:
        permutation = q4_source._block_permutation(order)
        permuted = v4c_components(vertices[np.asarray(order)])
        d3_worst = max(d3_worst, relative_inf(permutation.T @ permuted["total"] @ permutation, made["total"]))
        reversed_made = v4c_components(vertices[np.asarray(order)], normal=-NORMAL)
        reversal_worst = max(reversal_worst, relative_inf(permutation.T @ reversed_made["total"] @ permutation, made["total"]))
    first = np.arange(1.0, 19.0)
    second = np.arange(18.0, 0.0, -1.0)
    left_work = float(first @ made["total"] @ second)
    right_work = float(second @ made["total"] @ first)
    work_error = abs(left_work - right_work) / max(abs(left_work), abs(right_work), 1.0)
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
        "work_conjugacy_relative_hex": work_error.hex(),
    }
    diagnostics["gate_passed"] = bool(
        internal_rank == 5
        and physical_rank == 9
        and pl_rank == 3
        and total_rank == 12
        and float.fromhex(diagnostics["component_sum_relative_inf_hex"]) <= 3.0e-13
        and d3_worst <= 3.0e-12
        and reversal_worst <= 3.0e-12
        and rigid_residual <= 3.0e-12
        and float.fromhex(diagnostics["symmetry_relative_inf_hex"]) <= 3.0e-13
        and work_error <= 3.0e-13
    )
    payloads = {name: array_payload(np.asarray(value)) for name, value in made.items() if isinstance(value, np.ndarray)}
    return {"diagnostics": diagnostics, "payloads": payloads}


def _cell_triangles(i: int, j: int, n: int, diagonal: str) -> tuple[tuple[int, int, int], tuple[int, int, int]]:
    lower_left = j * (n + 1) + i
    lower_right = lower_left + 1
    upper_left = lower_left + n + 1
    upper_right = upper_left + 1
    selected = diagonal
    if diagonal == "alternating":
        selected = "slash" if (i + j) % 2 == 0 else "backslash"
    if selected == "slash":
        return ((lower_left, lower_right, upper_left), (lower_right, upper_right, upper_left))
    return ((lower_left, lower_right, upper_right), (lower_left, upper_right, upper_left))


def _grid_operators(size: int, diagonal: str) -> dict[str, np.ndarray]:
    node_count = (size + 1) ** 2
    coordinates = np.asarray(tuple((i / size, j / size, 0.0) for j in range(size + 1) for i in range(size + 1)))
    q4 = np.zeros((6 * node_count, 6 * node_count), dtype=np.float64)
    s3 = np.zeros_like(q4)
    for j in range(size):
        for i in range(size):
            nodes = (j * (size + 1) + i, j * (size + 1) + i + 1, (j + 1) * (size + 1) + i + 1, (j + 1) * (size + 1) + i)
            local_q4 = q4_source._qualified_q4_components(coordinates[np.asarray(nodes)], NORMAL)["total"]
            q4 += q4_source._embed(local_q4, nodes, node_count)
            for triangle in _cell_triangles(i, j, size, diagonal):
                s3 += q4_source._embed(v4c_components(coordinates[np.asarray(triangle)])["total"], triangle, node_count)
    boundary_nodes = tuple(node for node in range(node_count) if (node % (size + 1) in {0, size} or node // (size + 1) in {0, size}))
    interior_nodes = tuple(node for node in range(node_count) if node not in boundary_nodes)
    boundary = np.concatenate([np.arange(6 * node, 6 * node + 6) for node in boundary_nodes])
    interior = np.concatenate([np.arange(6 * node, 6 * node + 6) for node in interior_nodes]) if interior_nodes else np.asarray([], dtype=np.intp)

    def condense(matrix: np.ndarray) -> np.ndarray:
        bb = matrix[np.ix_(boundary, boundary)]
        if not interior.size:
            return bb
        bi = matrix[np.ix_(boundary, interior)]
        ii = matrix[np.ix_(interior, interior)]
        return 0.5 * ((bb - bi @ np.linalg.solve(ii, bi.T)) + (bb - bi @ np.linalg.solve(ii, bi.T)).T)

    return {"q4": condense(q4), "s3": condense(s3), "boundary_coordinates": coordinates[np.asarray(boundary_nodes)]}


def _trace_modes(coordinates: np.ndarray) -> dict[str, np.ndarray]:
    definitions = {
        "rigid_tx": lambda x, y: (1, 0, 0, 0, 0, 0),
        "rigid_ty": lambda x, y: (0, 1, 0, 0, 0, 0),
        "rigid_tz": lambda x, y: (0, 0, 1, 0, 0, 0),
        "rigid_rx": lambda x, y: (0, 0, y, 1, 0, 0),
        "rigid_ry": lambda x, y: (0, 0, -x, 0, 1, 0),
        "rigid_rz": lambda x, y: (-y, x, 0, 0, 0, 1),
        "constant_eps_x": lambda x, y: (x, 0, 0, 0, 0, 0),
        "constant_eps_y": lambda x, y: (0, y, 0, 0, 0, 0),
        "constant_gamma": lambda x, y: (y / 2, x / 2, 0, 0, 0, 0),
        "constant_kappa_x": lambda x, y: (0, 0, x * x / 2, 0, -x, 0),
        "constant_kappa_y": lambda x, y: (0, 0, y * y / 2, y, 0, 0),
        "constant_kappa_xy": lambda x, y: (0, 0, x * y, x, -y, 0),
        "linear_rotation": lambda x, y: (0, 0, 0, x, y, 0),
        "quadratic_transverse": lambda x, y: (0, 0, x * x + x * y + y * y, x + 2 * y, -(2 * x + y), 0),
    }
    return {name: np.asarray([item for x, y, _z in coordinates for item in function(x, y)], dtype=np.float64) for name, function in definitions.items()}


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
            for name, vector in _trace_modes(made["boundary_coordinates"]).items():
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
        return "BLOCKED_E4_PL_S3_V4C_PROCESS_OR_EVIDENCE"
    if not report.get("construction_identity_passed"):
        return "NO_GO_E4_PL_S3_V4C_CONSTRUCTION_IDENTITY"
    if not report.get("local_operator_passed"):
        return "NO_GO_E4_PL_S3_V4C_LOCAL_OPERATOR"
    if not report.get("mixed_interface_passed"):
        return "NO_GO_E4_PL_S3_V4C_MIXED_INTERFACE"
    return "PROVISIONAL_GO_E4_PL_S3_V4C_STAGE4A_RERUN"


def _run_child(command: list[str], timeout_seconds: int) -> None:
    bounded_source._run_child(command, timeout_seconds)


def run_bounded(output_root: Path, *, timeout_seconds: int = 600, wave_timeout_seconds: int = 1800) -> dict[str, Any]:
    validate_authority()
    if timeout_seconds not in range(1, 601) or wave_timeout_seconds not in range(1, 1801):
        raise ScreenError("requested limits exceed the frozen process bounds")
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=False)
    progress = root / "progress.jsonl"
    progress.touch(exist_ok=False)
    deadline = time.monotonic() + wave_timeout_seconds
    checker = REFERENCE / "e4_pl_s3_v4c_screen_checker.py"
    cycles: list[dict[str, Any]] = []
    terminal = "BLOCKED_E4_PL_S3_V4C_PROCESS_OR_EVIDENCE"
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
            terminal = "BLOCKED_E4_PL_S3_V4C_PROCESS_OR_EVIDENCE"
    except BaseException as exc:
        cycles.append({"error_class": type(exc).__name__, "status": "FAILED_BOUNDED_CHILD"})
        terminal = "BLOCKED_E4_PL_S3_V4C_PROCESS_OR_EVIDENCE"
    aggregate = {"activation_authorized": False, "candidate_formulation_id": FORMULATION_ID, "contract_sha256": sha256_file(CONTRACT), "cycles": cycles, "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED", "schema": AGGREGATE_SCHEMA, "stage4a_rerun_authorized": terminal == "PROVISIONAL_GO_E4_PL_S3_V4C_STAGE4A_RERUN", "terminal": terminal}
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
