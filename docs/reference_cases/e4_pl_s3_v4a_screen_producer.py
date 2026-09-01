"""Bounded producer for the research-only V4A Q4-subcell S3 screen."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import itertools
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Mapping, Sequence

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "docs" / "reference_cases"
CONTRACT = REFERENCE / "e4_pl_s3_v4a_screen_contract.json"
ECOSYSTEM_ROOT = next(
    (parent for parent in ROOT.parents if (parent / "ANYfileIO" / "src").is_dir()),
    ROOT.parent,
)
for _path in (
    ROOT / "src",
    ECOSYSTEM_ROOT / "ANYfileIO" / "src",
    ECOSYSTEM_ROOT / "ANYmaterial" / "src",
    ECOSYSTEM_ROOT / "ANYgeometry" / "src",
    ECOSYSTEM_ROOT / "ANYmesh" / "src",
    REFERENCE,
):
    if _path.is_dir() and str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

FORMULATION_ID = "CANDIDATE_E4_PL_S3_V4A_Q4_SUBCELL_CONDENSED_FLAT_LINEAR_V1"
PROOF_SCHEMA = "anysolver.e4-pl-s3-v4a-subcell-screen-proof-v1"
CHECK_SCHEMA = "anysolver.e4-pl-s3-v4a-subcell-screen-check-v1"
AGGREGATE_SCHEMA = "anysolver.e4-pl-s3-v4a-subcell-screen-aggregate-v1"
YOUNG = 210_000_000_000.0
POISSON = 0.3
THICKNESS = 0.01
NORMAL = np.asarray((0.0, 0.0, 1.0), dtype=np.float64)
DIAGONALS = ("slash", "backslash", "alternating")
PERMUTATIONS = tuple(itertools.permutations(range(3)))
THREAD_ENV = {"OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1", "NUMEXPR_NUM_THREADS": "1"}
MEMORY_LIMIT_BYTES = 24 * 1024**3


class ScreenError(RuntimeError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("ascii")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


def sha256_file(path: Path) -> str:
    return sha256_bytes(Path(path).read_bytes())


def _unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    made: dict[str, Any] = {}
    for key, value in pairs:
        if key in made:
            raise ScreenError(f"duplicate key {key!r}")
        made[key] = value
    return made


def load_canonical(path: Path) -> dict[str, Any]:
    raw = Path(path).read_bytes()
    value = json.loads(raw, object_pairs_hook=_unique, parse_constant=lambda token: (_ for _ in ()).throw(ScreenError(token)))
    if raw != canonical_bytes(value):
        raise ScreenError(f"{path.name} is not canonical JSON")
    return value


def exclusive_write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(canonical_bytes(value))
        stream.flush()
        os.fsync(stream.fileno())


def array_payload(value: np.ndarray) -> dict[str, Any]:
    made = np.asarray(value, dtype=np.float64)
    values = [float(item).hex() for item in made.reshape(-1)]
    return {"shape": list(made.shape), "sha256": sha256_bytes(canonical_bytes(values)), "values_hex": values}


def relative_inf(actual: np.ndarray, expected: np.ndarray) -> float:
    return float(np.linalg.norm(actual - expected, ord=np.inf) / max(np.linalg.norm(expected, ord=np.inf), 1.0))


def validate_authority() -> dict[str, Any]:
    contract = load_canonical(CONTRACT)
    if contract.get("schema") != "anysolver.e4-pl-s3-v4a-subcell-screen-contract-v1":
        raise ScreenError("unexpected V4A screen contract")
    for item in contract["frozen_inputs"]:
        path = ROOT / item["path"]
        if not path.is_file() or path.is_symlink() or path.stat().st_size != item["bytes"] or sha256_file(path) != item["sha256"]:
            raise ScreenError(f"frozen input mismatch: {path}")
    prereg = load_canonical(REFERENCE / "e4_pl_s3_v4a_preregistration_result.json")
    if prereg.get("terminal") != "PROVISIONAL_GO_E4_PL_S3_V4A_BOUNDED_SUBCELL_SCREEN" or prereg.get("next_gate_authorized") is not True:
        raise ScreenError("V4A preregistration does not authorize this screen")
    return contract


def _qualified_q4_components(coordinates: np.ndarray, normal: np.ndarray) -> dict[str, np.ndarray]:
    from anysolver.e4_pl_element import QualifiedE4PLShellElement
    from anysolver.fe_core import FEModel

    model = FEModel("v4a-qualified-q4-subcell")
    model.add_material("steel", YOUNG, POISSON, density=7850.0)
    for node, point in enumerate(coordinates, 1):
        model.add_node(node, float(point[0]), float(point[1]), float(point[2]))
    element = QualifiedE4PLShellElement(
        1,
        (1, 2, 3, 4),
        "steel",
        thickness=THICKNESS,
        reference_normal=normal,
        drilling_stabilization=0.001,
        hourglass_stabilization=0.001,
        pl_stabilization=1.0,
    )
    model.add_element(1, element)
    raw = element.compute_stiffness_components(model.mesh, model.materials["steel"])
    return {name: np.asarray(raw[name], dtype=np.float64) for name in ("physical", "pl", "hourglass", "total")}


def _embed(matrix: np.ndarray, nodes: Sequence[int], node_count: int) -> np.ndarray:
    result = np.zeros((6 * node_count, 6 * node_count), dtype=np.float64)
    for local_i, node_i in enumerate(nodes):
        for local_j, node_j in enumerate(nodes):
            result[6 * node_i : 6 * node_i + 6, 6 * node_j : 6 * node_j + 6] += matrix[6 * local_i : 6 * local_i + 6, 6 * local_j : 6 * local_j + 6]
    return result


def _subcell_points(vertices: np.ndarray) -> np.ndarray:
    midpoints = np.asarray(((vertices[0] + vertices[1]) / 2.0, (vertices[1] + vertices[2]) / 2.0, (vertices[2] + vertices[0]) / 2.0))
    centre = np.mean(vertices, axis=0, keepdims=True)
    return np.vstack((vertices, midpoints, centre))


def _affine_restriction() -> np.ndarray:
    scalar = np.asarray(((1.0, 0.0, 0.0, 0.0), (0.0, 1.0, 0.0, 0.0), (0.0, 0.0, 1.0, 0.0), (0.5, 0.5, 0.0, 0.0), (0.0, 0.5, 0.5, 0.0), (0.5, 0.0, 0.5, 0.0), (0.0, 0.0, 0.0, 1.0)))
    made = np.zeros((42, 24), dtype=np.float64)
    for point in range(7):
        for variable in range(4):
            made[6 * point : 6 * point + 6, 6 * variable : 6 * variable + 6] = scalar[point, variable] * np.eye(6)
    return made


def v4a_components(coordinates: Sequence[Sequence[float]], *, normal: Sequence[float] = NORMAL) -> dict[str, Any]:
    vertices = np.asarray(coordinates, dtype=np.float64)
    if vertices.shape == (3, 2):
        vertices = np.column_stack((vertices, np.zeros(3)))
    if vertices.shape != (3, 3) or not np.all(np.isfinite(vertices)):
        raise ScreenError("V4A vertices must be finite 3x2 or 3x3 coordinates")
    normal_array = np.asarray(normal, dtype=np.float64)
    normal_array /= np.linalg.norm(normal_array)
    points = _subcell_points(vertices)
    subcells = ((0, 3, 6, 5), (1, 4, 6, 3), (2, 5, 6, 4))
    assembled = {name: np.zeros((42, 42), dtype=np.float64) for name in ("physical", "pl", "hourglass", "total")}
    for subcell in subcells:
        local = _qualified_q4_components(points[np.asarray(subcell)], normal_array)
        for name in assembled:
            assembled[name] += _embed(local[name], subcell, 7)
    restriction = _affine_restriction()
    restricted = {name: restriction.T @ value @ restriction for name, value in assembled.items()}
    total = restricted["total"]
    centre_block = total[18:, 18:]
    centre_coupling = total[18:, :18]
    centre_map = -np.linalg.solve(centre_block, centre_coupling)
    condensation = np.vstack((np.eye(18), centre_map))
    condensed = {name: 0.5 * (condensation.T @ value @ condensation + (condensation.T @ value @ condensation).T) for name, value in restricted.items()}
    return {
        **condensed,
        "centre_block": centre_block,
        "centre_map": centre_map,
        "component_sum_relative_inf": relative_inf(condensed["physical"] + condensed["pl"] + condensed["hourglass"], condensed["total"]),
        "points": points,
        "restriction": restriction,
    }


def _rigid_modes(vertices: np.ndarray) -> np.ndarray:
    modes = np.zeros((18, 6), dtype=np.float64)
    for node, (x, y, _z) in enumerate(vertices):
        base = 6 * node
        modes[base, 0] = modes[base + 1, 1] = modes[base + 2, 2] = 1.0
        modes[base + 2, 3], modes[base + 3, 3] = y, 1.0
        modes[base + 2, 4], modes[base + 4, 4] = -x, 1.0
        modes[base, 5], modes[base + 1, 5], modes[base + 5, 5] = -y, x, 1.0
    return modes


def _block_permutation(order: Sequence[int]) -> np.ndarray:
    made = np.zeros((18, 18), dtype=np.float64)
    for new, old in enumerate(order):
        made[6 * new : 6 * new + 6, 6 * old : 6 * old + 6] = np.eye(6)
    return made


def local_proof() -> dict[str, Any]:
    vertices = np.asarray(((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.2, 0.9, 0.0)))
    made = v4a_components(vertices)
    physical_singular = np.linalg.svd(made["physical"], compute_uv=False)
    total_singular = np.linalg.svd(made["total"], compute_uv=False)
    centre_singular = np.linalg.svd(made["centre_block"], compute_uv=False)
    physical_rank = int(np.count_nonzero(physical_singular > max(physical_singular[0], 1.0) * 1.0e-10))
    total_rank = int(np.count_nonzero(total_singular > max(total_singular[0], 1.0) * 1.0e-10))
    centre_rank = int(np.count_nonzero(centre_singular > max(centre_singular[0], 1.0) * 1.0e-12))
    rigid_residual = float(np.linalg.norm(made["total"] @ _rigid_modes(vertices), ord=np.inf) / max(np.linalg.norm(made["total"], ord=np.inf), 1.0))
    d3_worst = 0.0
    reversal_worst = 0.0
    for order in PERMUTATIONS:
        permutation = _block_permutation(order)
        permuted = v4a_components(vertices[np.asarray(order)])
        restored = permutation.T @ permuted["total"] @ permutation
        d3_worst = max(d3_worst, relative_inf(restored, made["total"]))
        reversed_made = v4a_components(vertices[np.asarray(order)], normal=-NORMAL)
        reversed_restored = permutation.T @ reversed_made["total"] @ permutation
        reversal_worst = max(reversal_worst, relative_inf(reversed_restored, made["total"]))
    diagnostics = {
        "centre_block_rank": centre_rank,
        "centre_block_minimum_singular_hex": float(centre_singular[-1]).hex(),
        "component_sum_relative_inf_hex": float(made["component_sum_relative_inf"]).hex(),
        "d3_worst_relative_inf_hex": d3_worst.hex(),
        "director_reversal_worst_relative_inf_hex": reversal_worst.hex(),
        "physical_rank": physical_rank,
        "rigid_residual_relative_inf_hex": rigid_residual.hex(),
        "symmetry_relative_inf_hex": relative_inf(made["total"], made["total"].T).hex(),
        "total_rank": total_rank,
    }
    diagnostics["gate_passed"] = bool(
        centre_rank == 6
        and physical_rank == 9
        and total_rank == 12
        and float.fromhex(diagnostics["component_sum_relative_inf_hex"]) <= 3.0e-13
        and d3_worst <= 3.0e-12
        and reversal_worst <= 3.0e-12
        and rigid_residual <= 3.0e-12
        and float.fromhex(diagnostics["symmetry_relative_inf_hex"]) <= 3.0e-13
    )
    payloads = {name: array_payload(np.asarray(value)) for name, value in made.items() if isinstance(value, np.ndarray) and name != "points"}
    return {"diagnostics": diagnostics, "payloads": payloads}


def _connectivity(diagonal: str) -> tuple[tuple[int, int, int], tuple[int, int, int]]:
    if diagonal in {"backslash", "alternating"}:
        return ((1, 2, 3), (1, 3, 4))
    if diagonal == "slash":
        return ((1, 2, 4), (2, 3, 4))
    raise ScreenError(f"unknown diagonal {diagonal!r}")


def _q4_macrocell() -> np.ndarray:
    coordinates = np.asarray(((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.0, 1.0, 0.0), (0.0, 1.0, 0.0)))
    return _qualified_q4_components(coordinates, NORMAL)["total"]


def macrocell_pair(diagonal: str) -> dict[str, np.ndarray]:
    xy = {1: (0.0, 0.0, 0.0), 2: (1.0, 0.0, 0.0), 3: (1.0, 1.0, 0.0), 4: (0.0, 1.0, 0.0)}
    s3 = np.zeros((24, 24), dtype=np.float64)
    for nodes in _connectivity(diagonal):
        local = v4a_components([xy[node] for node in nodes])["total"]
        s3 += _embed(local, tuple(node - 1 for node in nodes), 4)
    return {"q4": _q4_macrocell(), "s3": s3}


def _macro_modes() -> dict[str, np.ndarray]:
    xy = ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0))
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
        "constant_kappa_x": lambda x, y: (0, 0, x * x / 2, 0, x, 0),
        "constant_kappa_y": lambda x, y: (0, 0, y * y / 2, -y, 0, 0),
        "constant_shear_x": lambda x, y: (0, 0, x, 0, 0, 0),
        "constant_shear_y": lambda x, y: (0, 0, y, 0, 0, 0),
        "affine_trace": lambda x, y: (x + y / 4, y - x / 5, 2 * x / 5 - 3 * y / 10, x / 10, -3 * y / 20, (x - y) / 2),
    }
    return {name: np.asarray([item for point in xy for item in definition(*point)], dtype=np.float64) for name, definition in definitions.items()}


def macrocell_proof() -> dict[str, Any]:
    modes = _macro_modes()
    comparisons: dict[str, Any] = {}
    matrices: dict[str, Any] = {}
    trace_worst = 0.0
    for diagonal in DIAGONALS:
        pair = macrocell_pair(diagonal)
        matrices[diagonal] = {name: array_payload(value) for name, value in pair.items()}
        rows: dict[str, Any] = {}
        for name, vector in modes.items():
            q4_action = pair["q4"] @ vector
            s3_action = pair["s3"] @ vector
            residual = float(np.linalg.norm(s3_action - q4_action, ord=np.inf) / max(np.linalg.norm(q4_action, ord=np.inf), 1.0))
            rows[name] = {"action_relative_inf_hex": residual.hex()}
            trace_worst = max(trace_worst, residual)
        comparisons[diagonal] = {"full_operator_relative_inf_hex": relative_inf(pair["s3"], pair["q4"]).hex(), "trace_modes": rows}
    # The preregistered exact trace action is the classifying macrocell gate.
    gate_passed = trace_worst <= 3.0e-12
    return {"comparisons": comparisons, "diagnostics": {"gate_passed": gate_passed, "trace_worst_relative_inf_hex": trace_worst.hex()}, "matrices": matrices}


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
    # Development remains after the classifying local/macrocell gates.  This
    # implementation screen records authorization rather than entering Stage 4A.
    return base | {"development_records": [], "later_stages": "DEVELOPMENT_NOT_EXECUTED_IN_LOCAL_MACROCELL_SCREEN", "macrocell": macrocell}


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


def adjudicate(*, identical: bool, report: Mapping[str, Any]) -> str:
    if not identical or not report.get("authority_complete"):
        return "BLOCKED_E4_PL_S3_V4A_PROCESS_OR_EVIDENCE"
    if not report.get("construction_identity_passed"):
        return "NO_GO_E4_PL_S3_V4A_CONSTRUCTION_IDENTITY"
    if not report.get("local_operator_passed"):
        return "NO_GO_E4_PL_S3_V4A_LOCAL_OPERATOR"
    if not report.get("mixed_interface_passed"):
        return "NO_GO_E4_PL_S3_V4A_MIXED_INTERFACE"
    return "PROVISIONAL_GO_E4_PL_S3_V4A_STAGE4A_RERUN"


def run_bounded(output_root: Path, *, timeout_seconds: int = 600, wave_timeout_seconds: int = 1800) -> dict[str, Any]:
    validate_authority()
    if timeout_seconds not in range(1, 601) or wave_timeout_seconds not in range(1, 1801):
        raise ScreenError("requested limits exceed the frozen process bounds")
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=False)
    progress = root / "progress.jsonl"
    progress.touch(exist_ok=False)
    deadline = time.monotonic() + wave_timeout_seconds
    script = Path(__file__).resolve()
    checker = REFERENCE / "e4_pl_s3_v4a_screen_checker.py"
    cycles: list[dict[str, Any]] = []
    terminal = "BLOCKED_E4_PL_S3_V4A_PROCESS_OR_EVIDENCE"
    try:
        for cycle in (1, 2):
            cycle_root = root / f"cycle-{cycle}"
            cycle_root.mkdir()
            proof = cycle_root / "proof.json"
            checks = (cycle_root / "checker-a.json", cycle_root / "checker-b.json")
            with progress.open("ab") as stream:
                stream.write(canonical_bytes({"cycle": cycle, "phase": "INITIALIZATION", "sequence": 0}))
            remaining = int(max(1, min(timeout_seconds, deadline - time.monotonic())))
            _run_child([sys.executable, str(script), "--emit-proof", "--output", str(proof)], remaining)
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
            terminal = "BLOCKED_E4_PL_S3_V4A_PROCESS_OR_EVIDENCE"
    except BaseException as exc:
        cycles.append({"error_class": type(exc).__name__, "status": "FAILED_BOUNDED_CHILD"})
        terminal = "BLOCKED_E4_PL_S3_V4A_PROCESS_OR_EVIDENCE"
    aggregate = {"activation_authorized": False, "candidate_formulation_id": FORMULATION_ID, "contract_sha256": sha256_file(CONTRACT), "cycles": cycles, "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED", "schema": AGGREGATE_SCHEMA, "stage4a_rerun_authorized": terminal == "PROVISIONAL_GO_E4_PL_S3_V4A_STAGE4A_RERUN", "terminal": terminal}
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
