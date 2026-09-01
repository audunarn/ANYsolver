"""Produce the bounded V5I-R1 buckling-subspace and assembly-route diagnosis."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "docs/reference_cases"
CONTRACT = REFERENCE / "e4_pl_s3_v5i_r1_diagnosis_contract.json"
V5I = REFERENCE / "e4_pl_s3_v5i_stage4b.py"
V5I_INPUT = REFERENCE / "e4_pl_s3_v5i_stage4b_input.json"
V5I_AUTHORIZATION = REFERENCE / "e4_pl_s3_v5i_stage4b_execution_authorization.json"
SCHEMA = "anysolver.e4-pl-s3-v5i-r1-diagnosis-proof-v1"
FORMULATION_ID = "CANDIDATE_E4_PL_S3_V2C_FLAT_LINEAR_PARITY_V1"


class DiagnosisProducerError(RuntimeError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
        + "\n"
    ).encode("ascii")


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def _pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    made: dict[str, Any] = {}
    for key, value in items:
        if key in made:
            raise DiagnosisProducerError(f"duplicate JSON key: {key}")
        made[key] = value
    return made


def load_canonical(path: Path) -> tuple[bytes, dict[str, Any]]:
    raw = path.read_bytes()
    value = json.loads(
        raw,
        object_pairs_hook=_pairs,
        parse_constant=lambda token: (_ for _ in ()).throw(
            DiagnosisProducerError(f"nonfinite JSON token: {token}")
        ),
    )
    if not isinstance(value, dict) or raw != canonical_bytes(value):
        raise DiagnosisProducerError(f"noncanonical JSON: {path}")
    return raw, value


def _load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise DiagnosisProducerError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _validate_contract() -> dict[str, Any]:
    _raw, contract = load_canonical(CONTRACT)
    if contract.get("schema") != "anysolver.e4-pl-s3-v5i-r1-diagnosis-contract-v1":
        raise DiagnosisProducerError("unexpected diagnosis contract schema")
    for row in contract.get("frozen_inputs", []):
        path = (ROOT / row["path"]).resolve(strict=True)
        raw = path.read_bytes()
        if len(raw) != row["bytes"] or sha256_bytes(raw) != row["sha256"]:
            raise DiagnosisProducerError(f"frozen input mismatch: {row['path']}")
    return contract


def _canonical_modes(result: Any, count: int) -> tuple[np.ndarray, np.ndarray]:
    if result.solver_status != "ok" or len(result.modes) != count:
        raise DiagnosisProducerError("buckling solver did not return the requested window")
    factors = np.asarray([mode.load_factor for mode in result.modes], dtype=float)
    vectors = np.column_stack([mode.mode_shape for mode in result.modes]).astype(float)
    if np.any(~np.isfinite(factors)) or np.any(factors <= 0.0) or np.any(~np.isfinite(vectors)):
        raise DiagnosisProducerError("buckling window contains invalid values")
    for column in range(vectors.shape[1]):
        norm = float(np.linalg.norm(vectors[:, column]))
        if not math.isfinite(norm) or norm <= 0.0:
            raise DiagnosisProducerError("buckling mode has zero norm")
        vectors[:, column] /= norm
        pivot = int(np.argmax(np.abs(vectors[:, column])))
        if vectors[pivot, column] < 0.0:
            vectors[:, column] *= -1.0
    return factors, vectors


def _hex_array(values: np.ndarray) -> list[Any]:
    if values.ndim == 1:
        return [float(value).hex() for value in values]
    return [_hex_array(row) for row in values]


def _buckling_diagnosis(v5i: Any, payload: Mapping[str, Any]) -> dict[str, Any]:
    from anysolver.buckling import solve_eigenvalue_buckling

    lane, _runner, authorities = v5i._lane_and_model(payload)
    spec = dict(authorities.input["coverage"]["buckling"])
    count = 8
    reference = lane._build_case(authorities, 0, auxiliary=False)
    candidate = lane._build_case(authorities, 25, auxiliary=False)
    reference_edges = lane._apply_supported_boundary(reference.model)
    candidate_edges = lane._apply_supported_boundary(candidate.model)
    if reference_edges != candidate_edges:
        raise DiagnosisProducerError("matched support node IDs differ")
    arguments = {
        "num_modes": count,
        "dense_size_limit": 200,
        "reference_elastic_only": True,
        "search_factor": int(spec["search_factor"]),
    }
    reference_result = solve_eigenvalue_buckling(
        reference.model, lane._reference_elastic_states(reference.model, spec), **arguments
    )
    candidate_result = solve_eigenvalue_buckling(
        candidate.model, lane._reference_elastic_states(candidate.model, spec), **arguments
    )
    reference_factors, reference_vectors = _canonical_modes(reference_result, count)
    candidate_factors, candidate_vectors = _canonical_modes(candidate_result, count)
    factor_errors = np.abs(candidate_factors - reference_factors) / reference_factors
    diagonal_dots = np.sum(reference_vectors * candidate_vectors, axis=0)
    diagonal_mac = np.square(diagonal_dots)
    pair = np.asarray((4, 5), dtype=np.intp)
    q_reference, _ = np.linalg.qr(reference_vectors[:, pair], mode="reduced")
    q_candidate, _ = np.linalg.qr(candidate_vectors[:, pair], mode="reduced")
    cross = q_reference.T @ q_candidate
    singular = np.linalg.svd(cross, compute_uv=False)
    pair_mac = float(np.min(np.square(singular)))
    return {
        "candidate_factors_hex": _hex_array(candidate_factors),
        "diagonal_inner_products_hex": _hex_array(diagonal_dots),
        "diagonal_mac_hex": _hex_array(diagonal_mac),
        "factor_relative_errors_hex": _hex_array(factor_errors),
        "first_five_factor_error_max_hex": float(np.max(factor_errors[:5])).hex(),
        "mode_count": count,
        "pair_candidate_relative_gap_hex": float(
            (candidate_factors[5] - candidate_factors[4]) / candidate_factors[4]
        ).hex(),
        "pair_indices_zero_based": [4, 5],
        "pair_orthonormal_cross_hex": _hex_array(cross),
        "pair_reference_relative_gap_hex": float(
            (reference_factors[5] - reference_factors[4]) / reference_factors[4]
        ).hex(),
        "pair_singular_values_hex": _hex_array(singular),
        "pair_subspace_mac_hex": pair_mac.hex(),
        "reference_factors_hex": _hex_array(reference_factors),
        "support_node_count": len(reference_edges),
    }


def _csr_byte_identical(first: Any, second: Any) -> bool:
    return bool(
        first.shape == second.shape
        and np.array_equal(first.indptr, second.indptr)
        and np.array_equal(first.indices, second.indices)
        and np.array_equal(first.data, second.data)
    )


def _assembly_diagnosis(v5i: Any, payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    from anysolver.matrix_assembly import assemble_stiffness_matrix

    lane, _runner, authorities = v5i._lane_and_model(payload)
    records: list[dict[str, Any]] = []
    for fraction in (0, 10, 25):
        built = lane._build_case(authorities, fraction, auxiliary=False)
        first, _first_info = assemble_stiffness_matrix(built.model)
        second, second_info = assemble_stiffness_matrix(built.model)
        diagnostics = second_info["diagnostics"]
        q4_count = sum(kind == "Q4" for kind in built.element_kinds.values())
        s3_count = sum(kind == "S3" for kind in built.element_kinds.values())
        records.append(
            {
                "fraction_percent": fraction,
                "matrix_byte_identical_cold_warm": _csr_byte_identical(first, second),
                "q4_element_count": q4_count,
                "s3_element_count": s3_count,
                "scalar_shell_element_count": int(diagnostics["scalar_shell_element_count"]),
                "vectorized_shell_element_count": int(diagnostics["vectorized_shell_element_count"]),
                "vectorized_shell_groups": [
                    {
                        key: group[key]
                        for key in ("kernel", "num_elements", "shell_order")
                    }
                    for group in diagnostics["vectorized_shell_groups"]
                ],
            }
        )
    return records


def produce_proof() -> dict[str, Any]:
    contract = _validate_contract()
    v5i = _load_module("_v5i_r1_frozen_stage4b", V5I)
    input_raw, payload = v5i.load_input(V5I_INPUT)
    v5i.validate_authorization(V5I_AUTHORIZATION, input_raw, payload)
    proof = {
        "activation_authorized": False,
        "assembly": _assembly_diagnosis(v5i, payload),
        "buckling": _buckling_diagnosis(v5i, payload),
        "candidate_formulation_id": FORMULATION_ID,
        "contract_sha256": sha256_bytes(CONTRACT.read_bytes()),
        "predecessor_terminal": contract["predecessor"]["terminal"],
        "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "schema": SCHEMA,
    }
    proof["scientific_payload_sha256"] = sha256_bytes(canonical_bytes(proof))
    return proof


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--emit-v5i-r1-diagnosis", action="store_true", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("xb") as stream:
        stream.write(canonical_bytes(produce_proof()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
