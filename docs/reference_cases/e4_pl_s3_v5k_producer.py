"""Produce one bounded V5K spectral, assembly, or performance proof."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
import time
from typing import Any, Mapping, Sequence

import numpy as np
from scipy import sparse


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "docs/reference_cases"
V5I = REFERENCE / "e4_pl_s3_v5i_stage4b.py"
V5I_INPUT = REFERENCE / "e4_pl_s3_v5i_stage4b_input.json"
SCHEMA = "anysolver.e4-pl-s3-v5k-worker-proof-v1"
PASS = "PASS_MEASURED_REGISTERED_SCOPE"
FAIL = "FAIL_MEASURED_CONTRADICTION"
WORKER_IDS = (
    "SPECTRAL_10",
    "SPECTRAL_25",
    "ASSEMBLY_10",
    "ASSEMBLY_25",
    "PERFORMANCE_0",
    "PERFORMANCE_10",
    "PERFORMANCE_25",
)


class V5KProducerError(RuntimeError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("ascii")


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def _load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise V5KProducerError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _lane() -> tuple[Any, Any]:
    v5i = _load_module("_v5k_frozen_v5i_lane", V5I)
    payload = json.loads(V5I_INPUT.read_text(encoding="ascii"))
    lane, _runner, authorities = v5i._lane_and_model(payload)
    return lane, authorities


def _canonical_modes(result: Any, count: int) -> tuple[np.ndarray, np.ndarray]:
    if result.solver_status != "ok" or len(result.modes) != count:
        raise V5KProducerError("buckling solver did not return the registered window")
    factors = np.asarray([mode.load_factor for mode in result.modes], dtype=np.float64)
    vectors = np.column_stack([mode.mode_shape for mode in result.modes]).astype(np.float64)
    if np.any(~np.isfinite(factors)) or np.any(factors <= 0.0) or np.any(~np.isfinite(vectors)):
        raise V5KProducerError("buckling window is invalid")
    for index in range(count):
        norm = float(np.linalg.norm(vectors[:, index]))
        if not math.isfinite(norm) or norm <= 0.0:
            raise V5KProducerError("buckling vector is null")
        vectors[:, index] /= norm
        pivot = int(np.argmax(np.abs(vectors[:, index])))
        if vectors[pivot, index] < 0.0:
            vectors[:, index] *= -1.0
    return factors, vectors


def spectral_clusters(reference: Sequence[float], candidate: Sequence[float], tolerance: float = 0.03) -> list[list[int]]:
    if len(reference) != len(candidate) or len(reference) == 0:
        raise V5KProducerError("spectral windows are incompatible")
    clusters: list[list[int]] = [[0]]
    for index in range(1, len(reference)):
        overlaps = []
        for values in (reference, candidate):
            left, right = float(values[index - 1]), float(values[index])
            overlaps.append(right * (1.0 - tolerance) <= left * (1.0 + tolerance))
        if all(overlaps):
            clusters[-1].append(index)
        else:
            clusters.append([index])
    return clusters


def _spectral(lane: Any, authorities: Any, fraction: int) -> dict[str, Any]:
    from anysolver.buckling import solve_eigenvalue_buckling

    count = 8
    reference = lane._build_case(authorities, 0, auxiliary=False)
    candidate = lane._build_case(authorities, fraction, auxiliary=False)
    if lane._apply_supported_boundary(reference.model) != lane._apply_supported_boundary(candidate.model):
        raise V5KProducerError("matched supports differ")
    spec = authorities.input["coverage"]["buckling"]
    arguments = {"num_modes": count, "dense_size_limit": 200, "reference_elastic_only": True, "search_factor": int(spec["search_factor"])}
    reference_result = solve_eigenvalue_buckling(reference.model, lane._reference_elastic_states(reference.model, spec), **arguments)
    candidate_result = solve_eigenvalue_buckling(candidate.model, lane._reference_elastic_states(candidate.model, spec), **arguments)
    reference_factors, reference_vectors = _canonical_modes(reference_result, count)
    candidate_factors, candidate_vectors = _canonical_modes(candidate_result, count)
    factor_errors = np.abs(candidate_factors[:5] - reference_factors[:5]) / reference_factors[:5]
    records = []
    for indices in spectral_clusters(reference_factors, candidate_factors):
        if indices[0] >= 5:
            continue
        left, _ = np.linalg.qr(reference_vectors[:, indices], mode="reduced")
        right, _ = np.linalg.qr(candidate_vectors[:, indices], mode="reduced")
        singular = np.linalg.svd(left.T @ right, compute_uv=False)
        records.append(
            {
                "indices_zero_based": indices,
                "minimum_subspace_mac_hex": float(np.min(np.square(singular))).hex(),
                "singular_values_hex": [float(value).hex() for value in singular],
            }
        )
    minimum = min(float.fromhex(row["minimum_subspace_mac_hex"]) for row in records)
    return {
        "clusters": records,
        "factor_gate_passed": bool(float(np.max(factor_errors)) <= 0.03),
        "factor_relative_errors_hex": [float(value).hex() for value in factor_errors],
        "fraction_percent": fraction,
        "mac_gate_passed": bool(minimum >= 0.95),
        "minimum_mac_hex": minimum.hex(),
        "reference_factors_hex": [float(value).hex() for value in reference_factors],
        "candidate_factors_hex": [float(value).hex() for value in candidate_factors],
    }


def _csr_hash(matrix: sparse.csr_matrix) -> str:
    return sha256(matrix.indptr.tobytes() + matrix.indices.tobytes() + matrix.data.tobytes())


def _scalar_assembly(model: Any) -> sparse.csr_matrix:
    rows, cols, data = [], [], []
    for _element_id, element in model.mesh.elements.items():
        dofs = np.asarray(element.get_dof_mapping(model.mesh), dtype=np.intp)
        material = model.get_material(element.material_name)
        matrix = np.asarray(element.compute_stiffness_matrix(model.mesh, material), dtype=np.float64)
        rows.append(np.repeat(dofs, dofs.size))
        cols.append(np.tile(dofs, dofs.size))
        data.append(matrix.ravel())
    return sparse.coo_matrix((np.concatenate(data), (np.concatenate(rows), np.concatenate(cols))), shape=(model.mesh.dof_manager.total_dofs,) * 2).tocsr()


def _assembly(lane: Any, authorities: Any, fraction: int) -> dict[str, Any]:
    from anysolver.matrix_assembly import assemble_stiffness_matrix

    built = lane._build_case(authorities, fraction, auxiliary=False)
    cold, _cold_info = assemble_stiffness_matrix(built.model)
    warm, warm_info = assemble_stiffness_matrix(built.model)
    # The scalar comparator runs after the production cold/warm pair so it
    # cannot populate Q4 derived caches during an active assembly lease.
    scalar = _scalar_assembly(built.model)
    hashes = [_csr_hash(value) for value in (scalar, cold, warm)]
    expected_s3 = sum(kind == "S3" for kind in built.element_kinds.values())
    route = warm_info["diagnostics"]
    return {
        "cold_warm_scalar_byte_identical": len(set(hashes)) == 1,
        "fraction_percent": fraction,
        "matrix_sha256": hashes[0],
        "scalar_shell_element_count": int(route["scalar_shell_element_count"]),
        "v2c_element_count": expected_s3,
        "vectorized_shell_element_count": int(route["vectorized_shell_element_count"]),
        "v2c_route_present": any(
            group.get("kernel") == "s3_v2c_exact_revision_bound_matrix_plan"
            and int(group.get("num_elements", -1)) == expected_s3
            for group in route["vectorized_shell_groups"]
        ),
    }


def produce(worker_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    if worker_id not in WORKER_IDS:
        raise V5KProducerError(f"unknown worker {worker_id}")
    lane, authorities = _lane()
    started = time.perf_counter()
    if worker_id.startswith("SPECTRAL_"):
        payload = _spectral(lane, authorities, int(worker_id.rsplit("_", 1)[1]))
        passed = payload["factor_gate_passed"] and payload["mac_gate_passed"]
        diagnostic: dict[str, Any] = {}
    elif worker_id.startswith("ASSEMBLY_"):
        payload = _assembly(lane, authorities, int(worker_id.rsplit("_", 1)[1]))
        passed = payload["cold_warm_scalar_byte_identical"] and payload["v2c_route_present"] and payload["scalar_shell_element_count"] == 0
        diagnostic = {}
    else:
        fraction = int(worker_id.rsplit("_", 1)[1])
        status, raw = lane._performance_worker(authorities, fraction)
        payload = {"fraction_percent": fraction, "measurement_complete": status.get("performance_measurement") == PASS}
        passed = payload["measurement_complete"]
        diagnostic = raw
    proof = {
        "activation_authorized": False,
        "candidate_formulation_id": "CANDIDATE_E4_PL_S3_V2C_FLAT_LINEAR_PARITY_V1",
        "gate_status": PASS if passed else FAIL,
        "payload": payload,
        "predecessor_terminal_preserved": "NO_GO_E4_PL_S3_V5I_MIXED_EIGEN",
        "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "schema": SCHEMA,
        "worker_id": worker_id,
    }
    proof["scientific_payload_sha256"] = sha256(canonical_bytes(proof))
    diagnostic = {"elapsed_seconds": float(time.perf_counter() - started), "raw": diagnostic, "worker_id": worker_id}
    return proof, diagnostic


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", choices=WORKER_IDS, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--diagnostic-output", type=Path, required=True)
    args = parser.parse_args(argv)
    proof, diagnostic = produce(args.worker)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("xb") as stream:
        stream.write(canonical_bytes(proof))
    with args.diagnostic_output.open("xb") as stream:
        stream.write(canonical_bytes(diagnostic))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
