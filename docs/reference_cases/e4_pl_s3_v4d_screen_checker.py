"""Independent checker for the research-only V4D Hermite-edge screen."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "docs" / "reference_cases"
if str(REFERENCE) not in sys.path:
    sys.path.insert(0, str(REFERENCE))

import e4_pl_s3_v4a_screen_checker as independent_q4
import e4_pl_s3_v4c_screen_checker as physical_first
import e4_pl_s3_linear_reference as native_pl_reference


CONTRACT = REFERENCE / "e4_pl_s3_v4d_screen_contract.json"
FORMULATION_ID = "CANDIDATE_E4_PL_S3_V4D_Q4_SUBCELL_HERMITE_EDGE_FLAT_LINEAR_V1"
PROOF_SCHEMA = "anysolver.e4-pl-s3-v4d-hermite-edge-screen-proof-v1"
CHECK_SCHEMA = "anysolver.e4-pl-s3-v4d-hermite-edge-screen-check-v1"
YOUNG = 210_000_000_000.0
POISSON = 0.3
THICKNESS = 0.01
NORMAL = np.asarray((0.0, 0.0, 1.0))

canonical_bytes = independent_q4.canonical_bytes
sha256_file = independent_q4.sha256_file
load_document = independent_q4.load_document
_decode = independent_q4._decode
_relative_inf = independent_q4._relative_inf
_rank = independent_q4._rank


def reconstruct(vertices: np.ndarray, normal: np.ndarray) -> dict[str, np.ndarray]:
    points = np.empty((7, 3), dtype=np.float64)
    points[:3] = vertices
    points[3] = (vertices[0] + vertices[1]) / 2.0
    points[4] = (vertices[1] + vertices[2]) / 2.0
    points[5] = (vertices[2] + vertices[0]) / 2.0
    points[6] = np.mean(vertices, axis=0)
    assembled = np.zeros((42, 42), dtype=np.float64)
    for connectivity in ((0, 3, 6, 5), (1, 4, 6, 3), (2, 5, 6, 4)):
        independent_q4._scatter(assembled, independent_q4._q4(points[np.asarray(connectivity)], normal)["physical"], connectivity)
    restriction = np.zeros((42, 20), dtype=np.float64)
    for node in range(3):
        for component in range(5):
            restriction[6 * node + component, 5 * node + component] = 1.0
    for edge, endpoints in enumerate(((0, 1), (1, 2), (2, 0))):
        point = edge + 3
        dx = float(vertices[endpoints[1], 0] - vertices[endpoints[0], 0])
        dy = float(vertices[endpoints[1], 1] - vertices[endpoints[0], 1])
        for component in (0, 1, 3, 4):
            restriction[6 * point + component, 5 * endpoints[0] + component] = 0.5
            restriction[6 * point + component, 5 * endpoints[1] + component] = 0.5
        restriction[6 * point + 2, 5 * endpoints[0] + 2] = 0.5
        restriction[6 * point + 2, 5 * endpoints[1] + 2] = 0.5
        restriction[6 * point + 2, 5 * endpoints[0] + 3] = dy / 8.0
        restriction[6 * point + 2, 5 * endpoints[0] + 4] = -dx / 8.0
        restriction[6 * point + 2, 5 * endpoints[1] + 3] = -dy / 8.0
        restriction[6 * point + 2, 5 * endpoints[1] + 4] = dx / 8.0
    restriction[36:41, 15:20] = np.eye(5)
    restricted = restriction.T @ assembled @ restriction
    internal_block = restricted[15:, 15:]
    internal_map = -np.linalg.solve(internal_block, restricted[15:, :15])
    transform = np.vstack((np.eye(15), internal_map))
    physical_15 = transform.T @ restricted @ transform
    physical_15 = 0.5 * (physical_15 + physical_15.T)
    embedding = np.zeros((18, 15), dtype=np.float64)
    for node in range(3):
        for component in range(5):
            embedding[6 * node + component, 5 * node + component] = 1.0
    physical = embedding @ physical_15 @ embedding.T
    membrane = THICKNESS * YOUNG / (1.0 - POISSON**2) * np.asarray(((1.0, POISSON, 0.0), (POISSON, 1.0, 0.0), (0.0, 0.0, (1.0 - POISSON) / 2.0)))
    _local, inverse, determinant = native_pl_reference._geometry(vertices[:, :2])
    constraint, gram, pl = native_pl_reference._pl_blocks(inverse, determinant, native_pl_reference.invariant_drill_scale(membrane))
    return {"embedding": embedding, "internal_block": internal_block, "internal_map": internal_map, "physical": physical, "physical_15": physical_15, "pl": pl, "pl_constraint": constraint, "pl_gram": gram, "restriction": restriction, "total": 0.5 * (physical + pl + (physical + pl).T)}


def _triangles(i: int, j: int, size: int, diagonal: str) -> tuple[tuple[int, int, int], tuple[int, int, int]]:
    ll = j * (size + 1) + i
    lr, ul, ur = ll + 1, ll + size + 1, ll + size + 2
    selected = "slash" if diagonal == "alternating" and (i + j) % 2 == 0 else "backslash" if diagonal == "alternating" else diagonal
    return ((ll, lr, ul), (lr, ur, ul)) if selected == "slash" else ((ll, lr, ur), (ll, ur, ul))


def _grid(size: int, diagonal: str) -> dict[str, np.ndarray]:
    coordinates = np.asarray(tuple((i / size, j / size, 0.0) for j in range(size + 1) for i in range(size + 1)))
    count = len(coordinates)
    q4 = np.zeros((6 * count, 6 * count), dtype=np.float64)
    s3 = np.zeros_like(q4)
    for j in range(size):
        for i in range(size):
            nodes = (j * (size + 1) + i, j * (size + 1) + i + 1, (j + 1) * (size + 1) + i + 1, (j + 1) * (size + 1) + i)
            independent_q4._scatter(q4, independent_q4._q4(coordinates[np.asarray(nodes)], NORMAL)["total"], nodes)
            for triangle in _triangles(i, j, size, diagonal):
                independent_q4._scatter(s3, reconstruct(coordinates[np.asarray(triangle)], NORMAL)["total"], triangle)
    boundary_nodes = tuple(node for node in range(count) if node % (size + 1) in {0, size} or node // (size + 1) in {0, size})
    interior_nodes = tuple(node for node in range(count) if node not in boundary_nodes)
    boundary = np.concatenate([np.arange(6 * node, 6 * node + 6) for node in boundary_nodes])
    interior = np.concatenate([np.arange(6 * node, 6 * node + 6) for node in interior_nodes]) if interior_nodes else np.asarray([], dtype=np.intp)

    def dt_n(matrix: np.ndarray) -> np.ndarray:
        bb = matrix[np.ix_(boundary, boundary)]
        if not interior.size:
            return bb
        bi = matrix[np.ix_(boundary, interior)]
        value = bb - bi @ np.linalg.solve(matrix[np.ix_(interior, interior)], bi.T)
        return 0.5 * (value + value.T)

    return {"boundary_coordinates": coordinates[np.asarray(boundary_nodes)], "q4": dt_n(q4), "s3": dt_n(s3)}


def verify(proof: Mapping[str, Any]) -> dict[str, Any]:
    if proof.get("schema") != PROOF_SCHEMA or proof.get("candidate_formulation_id") != FORMULATION_ID:
        raise ValueError("unexpected V4D proof identity")
    contract = load_document(CONTRACT)
    if proof.get("contract_sha256") != sha256_file(CONTRACT):
        raise ValueError("proof contract hash mismatch")
    vertices = np.asarray(((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.2, 0.9, 0.0)))
    expected = reconstruct(vertices, NORMAL)
    payloads = proof["local"]["payloads"]
    local_worst = max(_relative_inf(_decode(payloads[name]), value) for name, value in expected.items())
    internal_rank = _rank(expected["internal_block"], 1.0e-12)
    physical_rank = _rank(expected["physical"], 1.0e-12)
    pl_rank = _rank(expected["pl"], 1.0e-12)
    total_rank = _rank(expected["total"], 1.0e-12)
    rigid = float(np.linalg.norm(expected["total"] @ independent_q4._rigid(vertices), ord=np.inf) / max(np.linalg.norm(expected["total"], ord=np.inf), 1.0))
    local_passed = bool(internal_rank == 5 and physical_rank == 9 and pl_rank == 3 and total_rank == 12 and local_worst <= 3.0e-13 and rigid <= 3.0e-12)
    macro = proof.get("macrocell", {})
    matrix_worst = 0.0
    trace_worst = 0.0
    count = 0
    for size in (1, 2, 4):
        for diagonal in ("slash", "backslash", "alternating"):
            made = _grid(size, diagonal)
            key = f"{size}x{size}:{diagonal}"
            for name in ("q4", "s3"):
                matrix_worst = max(matrix_worst, _relative_inf(_decode(macro["matrices"][key][name]), made[name]))
            for vector in physical_first._modes(made["boundary_coordinates"]).values():
                q4_action = made["q4"] @ vector
                trace_worst = max(trace_worst, float(np.linalg.norm(made["s3"] @ vector - q4_action, ord=np.inf) / max(np.linalg.norm(q4_action, ord=np.inf), 1.0)))
            count += 1
    macro_identity = matrix_worst <= 3.0e-13 and count == 9
    macro_passed = macro_identity and trace_worst <= 3.0e-12
    later_absent = proof.get("later_stages") == "NOT_EXECUTED_MACROCELL_GATE_FAILED" and proof.get("development_records") == []
    return {
        "authority_complete": contract.get("schema") == "anysolver.e4-pl-s3-v4d-hermite-edge-screen-contract-v1",
        "candidate_formulation_id": FORMULATION_ID,
        "construction_identity_passed": local_worst <= 3.0e-13 and macro_identity,
        "independent_internal_physical_block_rank": internal_rank,
        "independent_local_identity_worst_relative_inf_hex": local_worst.hex(),
        "independent_macrocell_identity_worst_relative_inf_hex": matrix_worst.hex(),
        "independent_macrocell_record_count": count,
        "independent_macrocell_trace_worst_relative_inf_hex": trace_worst.hex(),
        "independent_physical_rank": physical_rank,
        "independent_pl_rank": pl_rank,
        "independent_rigid_residual_relative_inf_hex": rigid.hex(),
        "independent_total_rank": total_rank,
        "later_stages_absent": bool(later_absent),
        "local_operator_passed": local_passed,
        "mixed_interface_passed": bool(macro_passed),
        "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "schema": CHECK_SCHEMA,
    }


def exclusive_write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(canonical_bytes(value))
        stream.flush()
        os.fsync(stream.fileno())


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-proof", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    exclusive_write(args.output, verify(load_document(args.verify_proof)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
