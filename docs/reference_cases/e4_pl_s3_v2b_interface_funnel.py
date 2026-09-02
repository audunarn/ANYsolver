"""Bounded S3 V2B macrocell and mixed-interface diagnostic funnel.

This research-only program never changes the production selector.  It compares
the frozen V2A DKMT triangle with the qualified Q4 on small, deterministic
macrocells and executes only the preregistered N20/N40 development records.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Iterable, Mapping, Sequence

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
REFERENCE = ROOT / "docs" / "reference_cases"
CONTRACT_PATH = REFERENCE / "e4_pl_s3_v2b_interface_contract.json"
for entry in (str(SRC), str(REFERENCE)):
    if entry not in sys.path:
        sys.path.insert(0, entry)

FORMULATION_ID = "CANDIDATE_E4_PL_S3_V2A_FLAT_LINEAR_V1"
SUCCESSOR_ID = "CANDIDATE_E4_PL_S3_V2B_FLAT_LINEAR_V1"
SCHEMA = "anysolver.e4-pl-s3-v2b-interface-proof-v1"
AGGREGATE_SCHEMA = "anysolver.e4-pl-s3-v2b-interface-aggregate-v1"
THREAD_ENV = {
    "OMP_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
    "NUMEXPR_NUM_THREADS": "1",
}
MEMORY_LIMIT_BYTES = 24 * 1024**3
YOUNG = 210.0e9
POISSON = 0.3
THICKNESS = 0.08
NORMAL = np.asarray((0.0, 0.0, 1.0), dtype=np.float64)
DIAGONALS = ("slash", "backslash", "alternating")
PERMUTATIONS = tuple(itertools.permutations(range(3)))
DEVELOPMENT_IDS = (
    "N20:5PCT:dispersed:slash",
    "N40:5PCT:dispersed:slash",
    "N20:10PCT:dispersed:slash",
    "N40:10PCT:dispersed:slash",
)


class FunnelError(RuntimeError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("ascii")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def exclusive_write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = canonical_bytes(value)
    with path.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def array_payload(value: np.ndarray) -> dict[str, Any]:
    made = np.asarray(value, dtype=np.float64)
    values = [float(item).hex() for item in made.reshape(-1)]
    return {
        "sha256": sha256_bytes(canonical_bytes(values)),
        "shape": list(made.shape),
        "values_hex": values,
    }


def decode_array(value: Mapping[str, Any]) -> np.ndarray:
    shape = tuple(int(item) for item in value["shape"])
    made = np.asarray([float.fromhex(str(item)) for item in value["values_hex"]], dtype=np.float64).reshape(shape)
    if sha256_bytes(canonical_bytes(list(value["values_hex"]))) != value["sha256"]:
        raise FunnelError("array payload hash mismatch")
    return made


def relative_inf(actual: np.ndarray, expected: np.ndarray) -> float:
    return float(np.linalg.norm(actual - expected, ord=np.inf) / max(np.linalg.norm(expected, ord=np.inf), 1.0))


def _dense(value: Any) -> np.ndarray:
    if hasattr(value, "toarray"):
        value = value.toarray()
    return np.asarray(value, dtype=np.float64)


def _connectivity(diagonal: str, i: int = 0, j: int = 0) -> tuple[tuple[int, int, int], tuple[int, int, int]]:
    made = diagonal
    if made == "alternating":
        made = "backslash" if (i + j) % 2 == 0 else "slash"
    if made == "backslash":
        return ((1, 2, 3), (1, 3, 4))
    if made == "slash":
        return ((1, 2, 4), (2, 3, 4))
    raise FunnelError(f"unknown diagonal {diagonal!r}")


def _macro_model(kind: str, diagonal: str, *, permutation: Sequence[int] = (0, 1, 2), normal: np.ndarray = NORMAL):
    from anysolver.e4_pl_element import QualifiedE4PLShellElement
    from anysolver.e4_pl_s3_v2_element import StrictFlatLinearE4PLS3V2ShellElement
    from anysolver.fe_core import FEModel

    model = FEModel(f"v2b-{kind}-{diagonal}")
    model.add_material("steel", YOUNG, POISSON, density=7850.0)
    for node_id, xyz in enumerate(((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.0, 1.0, 0.0), (0.0, 1.0, 0.0)), 1):
        model.add_node(node_id, *xyz)
    if kind == "q4":
        model.add_element(1, QualifiedE4PLShellElement(1, (1, 2, 3, 4), "steel", thickness=THICKNESS, reference_normal=NORMAL, drilling_stabilization=0.001, hourglass_stabilization=0.001, pl_stabilization=1.0))
    elif kind == "s3":
        for element_id, nodes in enumerate(_connectivity(diagonal), 1):
            ordered = tuple(nodes[index] for index in permutation)
            model.add_element(element_id, StrictFlatLinearE4PLS3V2ShellElement(element_id, ordered, "steel", thickness=THICKNESS, reference_normal=normal))
    else:
        raise FunnelError(f"unknown macrocell kind {kind!r}")
    return model


def _assemble_local(matrix: np.ndarray, node_ids: Sequence[int], node_count: int) -> np.ndarray:
    result = np.zeros((6 * node_count, 6 * node_count), dtype=np.float64)
    for local_i, node_i in enumerate(node_ids):
        gi = 6 * (int(node_i) - 1)
        li = 6 * local_i
        for local_j, node_j in enumerate(node_ids):
            gj = 6 * (int(node_j) - 1)
            lj = 6 * local_j
            result[gi : gi + 6, gj : gj + 6] += matrix[li : li + 6, lj : lj + 6]
    return result


def macrocell_components(diagonal: str, *, permutation: Sequence[int] = (0, 1, 2), normal: np.ndarray = NORMAL) -> dict[str, np.ndarray]:
    from anysolver.matrix_assembly import assemble_stiffness_matrix

    q4_model = _macro_model("q4", diagonal)
    s3_model = _macro_model("s3", diagonal, permutation=permutation, normal=normal)
    q4_material = q4_model.materials["steel"]
    s3_material = s3_model.materials["steel"]
    q4_element = q4_model.mesh.elements[1]
    q4 = q4_element.compute_stiffness_components(q4_model.mesh, q4_material)
    result: dict[str, np.ndarray] = {
        "q4_physical": np.asarray(q4["physical"], dtype=np.float64),
        "q4_numerical": np.asarray(q4["numerical"], dtype=np.float64),
        "q4_total": _dense(assemble_stiffness_matrix(q4_model)[0]),
    }
    sums = {name: np.zeros((24, 24), dtype=np.float64) for name in ("membrane", "bending", "shear", "physical", "pl", "total")}
    for element in s3_model.mesh.elements.values():
        parts = element.compute_stiffness_components(s3_model.mesh, s3_material)
        for name in sums:
            sums[name] += _assemble_local(np.asarray(parts[name], dtype=np.float64), element.node_ids, 4)
    result.update({f"s3_{name}": value for name, value in sums.items()})
    return result


def _mode_vectors() -> dict[str, np.ndarray]:
    coordinates = np.asarray(((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)))
    result: dict[str, np.ndarray] = {}
    for axis, name in enumerate(("rigid_tx", "rigid_ty", "rigid_tz")):
        vector = np.zeros(24)
        vector[axis::6] = 1.0
        result[name] = vector
    for name, ux, uy in (
        ("constant_eps_x", lambda x, y: x, lambda x, y: 0.0),
        ("constant_eps_y", lambda x, y: 0.0, lambda x, y: y),
        ("constant_gamma_xy", lambda x, y: 0.5 * y, lambda x, y: 0.5 * x),
    ):
        vector = np.zeros(24)
        for node, (x, y) in enumerate(coordinates):
            vector[6 * node] = ux(x, y)
            vector[6 * node + 1] = uy(x, y)
        result[name] = vector
    for name, w, wx, wy in (
        ("constant_kappa_x", lambda x, y: 0.5 * x * x, lambda x, y: x, lambda x, y: 0.0),
        ("constant_kappa_y", lambda x, y: 0.5 * y * y, lambda x, y: 0.0, lambda x, y: y),
        ("constant_kappa_xy", lambda x, y: x * y, lambda x, y: y, lambda x, y: x),
        ("quadratic_transverse", lambda x, y: x * x + x * y + 0.5 * y * y, lambda x, y: 2.0 * x + y, lambda x, y: x + y),
    ):
        vector = np.zeros(24)
        for node, (x, y) in enumerate(coordinates):
            base = 6 * node
            vector[base + 2] = w(x, y)
            vector[base + 3] = wy(x, y)
            vector[base + 4] = -wx(x, y)
        result[name] = vector
    return result


def _grid_model(size: int, kind: str, diagonal: str):
    from anysolver.e4_pl_element import QualifiedE4PLShellElement
    from anysolver.e4_pl_s3_v2_element import StrictFlatLinearE4PLS3V2ShellElement
    from anysolver.fe_core import FEModel

    model = FEModel(f"v2b-grid-{size}-{kind}-{diagonal}")
    model.add_material("steel", YOUNG, POISSON, density=7850.0)
    node_id = lambda i, j: j * (size + 1) + i + 1
    for j in range(size + 1):
        for i in range(size + 1):
            model.add_node(node_id(i, j), i / size, j / size, 0.0)
    element_id = 0
    for j in range(size):
        for i in range(size):
            n00, n10, n11, n01 = node_id(i, j), node_id(i + 1, j), node_id(i + 1, j + 1), node_id(i, j + 1)
            if kind == "q4":
                element_id += 1
                model.add_element(element_id, QualifiedE4PLShellElement(element_id, (n00, n10, n11, n01), "steel", thickness=THICKNESS, reference_normal=NORMAL, drilling_stabilization=0.001, hourglass_stabilization=0.001, pl_stabilization=1.0))
            else:
                local = "backslash" if diagonal == "alternating" and (i + j) % 2 == 0 else "slash" if diagonal == "alternating" else diagonal
                pairs = ((n00, n10, n11), (n00, n11, n01)) if local == "backslash" else ((n00, n10, n01), (n10, n11, n01))
                for nodes in pairs:
                    element_id += 1
                    model.add_element(element_id, StrictFlatLinearE4PLS3V2ShellElement(element_id, nodes, "steel", thickness=THICKNESS, reference_normal=NORMAL))
    return model


def boundary_map(size: int, kind: str, diagonal: str) -> np.ndarray:
    from anysolver.matrix_assembly import assemble_stiffness_matrix

    model = _grid_model(size, kind, diagonal)
    stiffness = _dense(assemble_stiffness_matrix(model)[0])
    boundary_nodes = [j * (size + 1) + i for j in range(size + 1) for i in range(size + 1) if i in (0, size) or j in (0, size)]
    boundary = np.asarray([6 * node + dof for node in boundary_nodes for dof in range(6)], dtype=int)
    interior = np.asarray([index for index in range(stiffness.shape[0]) if index not in set(boundary)], dtype=int)
    if interior.size == 0:
        return stiffness[np.ix_(boundary, boundary)]
    kbb = stiffness[np.ix_(boundary, boundary)]
    kbi = stiffness[np.ix_(boundary, interior)]
    kii = stiffness[np.ix_(interior, interior)]
    condensed = kbb - kbi @ np.linalg.solve(kii, kbi.T)
    return 0.5 * (condensed + condensed.T)


def _development_records() -> list[dict[str, Any]]:
    from e4_pl_s3_v2_flat_funnel_producer import produce_case

    manifest = json.loads((REFERENCE / "e4_pl_s3_mixed_mesh_connectivity_manifest.json").read_text(encoding="utf-8"))
    records = manifest["records"] if isinstance(manifest, dict) else manifest
    selected = []
    for index, record in enumerate(records):
        record_id = f"N{record['level']}:{record['s3_area_fraction_percent']}PCT:{record['mask']}:{record['diagonal']}"
        if record_id in DEVELOPMENT_IDS:
            selected.append(produce_case({"manifest_index": index, "record": record, "record_id": record_id}))
    if tuple(item["record_id"] for item in selected) != DEVELOPMENT_IDS:
        by_id = {item["record_id"]: item for item in selected}
        selected = [by_id[item] for item in DEVELOPMENT_IDS]
    return selected


def produce_proof(*, include_development: bool = True) -> dict[str, Any]:
    comparisons: dict[str, Any] = {}
    matrices: dict[str, Any] = {}
    modes = _mode_vectors()
    d3_worst = 0.0
    reversal_worst = 0.0
    for diagonal in DIAGONALS:
        parts = macrocell_components(diagonal)
        matrices[diagonal] = {name: array_payload(value) for name, value in parts.items()}
        mode_rows = {}
        for name, vector in modes.items():
            q4_energy = float(vector @ parts["q4_total"] @ vector)
            s3_energy = float(vector @ parts["s3_total"] @ vector)
            mode_rows[name] = {"q4_energy_hex": q4_energy.hex(), "s3_energy_hex": s3_energy.hex()}
        for permutation in PERMUTATIONS:
            permuted = macrocell_components(diagonal, permutation=permutation)["s3_total"]
            d3_worst = max(d3_worst, relative_inf(permuted, parts["s3_total"]))
            reversed_matrix = macrocell_components(diagonal, permutation=permutation, normal=-NORMAL)["s3_total"]
            reversal_worst = max(reversal_worst, relative_inf(reversed_matrix, parts["s3_total"]))
        comparisons[diagonal] = {
            "component_relative_inf_hex": {
                "physical": relative_inf(parts["s3_physical"], parts["q4_physical"]).hex(),
                "numerical": relative_inf(parts["s3_pl"], parts["q4_numerical"]).hex(),
                "total": relative_inf(parts["s3_total"], parts["q4_total"]).hex(),
            },
            "mode_energies": mode_rows,
        }
    boundary = {}
    for diagonal in DIAGONALS:
        boundary[diagonal] = {}
        for size in (1, 2, 4):
            q4 = boundary_map(size, "q4", diagonal)
            s3 = boundary_map(size, "s3", diagonal)
            boundary[diagonal][str(size)] = {"q4": array_payload(q4), "relative_inf_hex": relative_inf(s3, q4).hex(), "s3": array_payload(s3)}
    development = _development_records() if include_development else []
    return {
        "boundary_maps": boundary,
        "comparisons": comparisons,
        "contract_sha256": sha256_file(CONTRACT_PATH),
        "development_records": development,
        "development_record_ids": list(DEVELOPMENT_IDS) if include_development else [],
        "diagnostics": {"d3_worst_relative_inf_hex": d3_worst.hex(), "director_reversal_worst_relative_inf_hex": reversal_worst.hex()},
        "formulation_id": FORMULATION_ID,
        "matrices": matrices,
        "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "schema": SCHEMA,
        "successor_id_reserved_not_implemented": SUCCESSOR_ID,
        "terminal": "DIAGNOSTIC_COMPLETE",
    }


def _run_child(command: list[str], timeout: int) -> None:
    from e4_pl_s3_v2_bounded_process import _ProcessJob

    environment = os.environ.copy()
    environment.update(THREAD_ENV)
    job = _ProcessJob(MEMORY_LIMIT_BYTES)
    process = None
    try:
        process = job.launch(command, cwd=ROOT, env=environment, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            return_code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            if not job.terminate(124):
                raise FunnelError("timed-out child process tree did not drain") from exc
            raise FunnelError(f"child exceeded {timeout} seconds") from exc
        _cpu, active, peak = job.accounting()
        if active != 0:
            if not job.terminate(125):
                raise FunnelError("completed child retained a live process tree")
            raise FunnelError("completed child retained descendants")
        if peak > MEMORY_LIMIT_BYTES:
            raise FunnelError("child exceeded the 24-GiB process-tree limit")
        if return_code != 0:
            raise FunnelError(f"child failed with exit code {return_code}")
    finally:
        job.close()


def _append_progress(path: Path, phase: str, sequence: int) -> None:
    record = canonical_bytes({"phase": phase, "sequence": sequence})
    with path.open("ab") as stream:
        stream.write(record)
        stream.flush()
        os.fsync(stream.fileno())


def adjudicate(*, checker_identical: bool, report: Mapping[str, Any], formulation_id: str) -> str:
    if not checker_identical or not report["authority_complete"]:
        return "BLOCKED_E4_PL_S3_V2B_PROCESS_OR_EVIDENCE"
    if not report["source_equation_agreement"]:
        return "NO_GO_E4_PL_S3_V2B_LOCAL_OPERATOR"
    mixed_failure = bool(report["macrocell_operator_mismatch_nonzero"] and (report["development_successive_response_failed"] or report["v2a_mixed_no_go_bound"]))
    if mixed_failure and formulation_id == FORMULATION_ID:
        return "UNCLASSIFIED_E4_PL_S3_V2B_FORMULATION_REPLACEMENT_REQUIRED"
    if mixed_failure:
        return "NO_GO_E4_PL_S3_V2B_MIXED_INTERFACE"
    return "PROVISIONAL_GO_E4_PL_S3_V2B_STAGE4A_RERUN"


def run_bounded(output_root: Path, *, timeout_seconds: int = 600) -> dict[str, Any]:
    output_root = Path(output_root)
    output_root.mkdir(parents=True, exist_ok=False)
    proof = output_root / "proof.json"
    checker_a = output_root / "checker-a.json"
    checker_b = output_root / "checker-b.json"
    script = Path(__file__).resolve()
    checker = REFERENCE / "e4_pl_s3_v2b_interface_checker.py"
    progress = output_root / "progress.jsonl"
    _append_progress(progress, "INITIALIZATION", 0)
    _run_child([sys.executable, str(script), "--emit-proof", "--output", str(proof)], timeout_seconds)
    _append_progress(progress, "PROOF_COMPLETE", 1)
    commands = [[sys.executable, str(checker), "--verify-proof", str(proof), "--output", str(path)] for path in (checker_a, checker_b)]
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(_run_child, command, timeout_seconds) for command in commands]
        for future in futures:
            future.result()
    _append_progress(progress, "CHECKERS_COMPLETE", 2)
    identical = checker_a.read_bytes() == checker_b.read_bytes()
    report = json.loads(checker_a.read_text(encoding="ascii"))
    proof_document = json.loads(proof.read_text(encoding="ascii"))
    terminal = adjudicate(checker_identical=identical, report=report, formulation_id=str(proof_document["formulation_id"]))
    aggregate = {
        "activation_authorized": False,
        "checker_replicas_byte_identical": identical,
        "checker_sha256": sha256_file(checker_a),
        "contract_sha256": sha256_file(CONTRACT_PATH),
        "full_stage4a_rerun_authorized": terminal == "PROVISIONAL_GO_E4_PL_S3_V2B_STAGE4A_RERUN",
        "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "proof_sha256": sha256_file(proof),
        "schema": AGGREGATE_SCHEMA,
        "terminal": terminal,
    }
    exclusive_write(output_root / "aggregate.json", aggregate)
    _append_progress(progress, "AGGREGATE_COMPLETE", 3)
    return aggregate


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--emit-proof", action="store_true")
    mode.add_argument("--run-bounded", action="store_true")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--timeout-seconds", type=int, default=600)
    parser.add_argument("--skip-development", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.emit_proof:
        if args.output is None:
            raise FunnelError("--output is required")
        exclusive_write(args.output, produce_proof(include_development=not args.skip_development))
    else:
        if args.output_root is None:
            raise FunnelError("--output-root is required")
        run_bounded(args.output_root, timeout_seconds=args.timeout_seconds)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
