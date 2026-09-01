"""Independent checker for the research-only V4A Q4-subcell screen."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
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
):
    if _path.is_dir() and str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

FORMULATION_ID = "CANDIDATE_E4_PL_S3_V4A_Q4_SUBCELL_CONDENSED_FLAT_LINEAR_V1"
PROOF_SCHEMA = "anysolver.e4-pl-s3-v4a-subcell-screen-proof-v1"
CHECK_SCHEMA = "anysolver.e4-pl-s3-v4a-subcell-screen-check-v1"
YOUNG = 210_000_000_000.0
POISSON = 0.3
THICKNESS = 0.01


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("ascii")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


def sha256_file(path: Path) -> str:
    return sha256_bytes(Path(path).read_bytes())


def _unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate key {key!r}")
        value[key] = item
    return value


def load_document(path: Path) -> dict[str, Any]:
    raw = Path(path).read_bytes()
    value = json.loads(
        raw,
        object_pairs_hook=_unique,
        parse_constant=lambda token: (_ for _ in ()).throw(ValueError(token)),
    )
    if raw != canonical_bytes(value):
        raise ValueError("document is not canonical JSON")
    return value


def _decode(payload: Mapping[str, Any]) -> np.ndarray:
    values = list(payload["values_hex"])
    if sha256_bytes(canonical_bytes(values)) != payload["sha256"]:
        raise ValueError("array payload hash mismatch")
    shape = tuple(int(item) for item in payload["shape"])
    return np.asarray([float.fromhex(str(item)) for item in values], dtype=np.float64).reshape(shape)


def _relative_inf(actual: np.ndarray, expected: np.ndarray) -> float:
    return float(np.linalg.norm(actual - expected, ord=np.inf) / max(np.linalg.norm(expected, ord=np.inf), 1.0))


def _rank(matrix: np.ndarray, relative: float) -> int:
    singular = np.linalg.svd(matrix, compute_uv=False)
    return int(np.count_nonzero(singular > max(float(singular[0]), 1.0) * relative))


def _q4(coordinates: np.ndarray, normal: np.ndarray) -> dict[str, np.ndarray]:
    from anysolver.e4_pl_element import QualifiedE4PLShellElement
    from anysolver.fe_core import FEModel

    model = FEModel("v4a-independent-q4-reconstruction")
    model.add_material("steel", YOUNG, POISSON, density=7850.0)
    for identifier, xyz in enumerate(coordinates, 1):
        model.add_node(identifier, *(float(item) for item in xyz))
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
    return {key: np.asarray(raw[key], dtype=np.float64) for key in ("physical", "pl", "hourglass", "total")}


def _scatter(assembled: np.ndarray, local: np.ndarray, connectivity: Sequence[int]) -> None:
    indices = np.concatenate([np.arange(6 * node, 6 * node + 6) for node in connectivity])
    assembled[np.ix_(indices, indices)] += local


def reconstruct(vertices: np.ndarray, normal: np.ndarray) -> dict[str, np.ndarray]:
    points = np.empty((7, 3), dtype=np.float64)
    points[:3] = vertices
    points[3] = 0.5 * (vertices[0] + vertices[1])
    points[4] = 0.5 * (vertices[1] + vertices[2])
    points[5] = 0.5 * (vertices[2] + vertices[0])
    points[6] = (vertices[0] + vertices[1] + vertices[2]) / 3.0
    assembled = {name: np.zeros((42, 42), dtype=np.float64) for name in ("physical", "pl", "hourglass", "total")}
    for connectivity in ((0, 3, 6, 5), (1, 4, 6, 3), (2, 5, 6, 4)):
        local = _q4(points[np.asarray(connectivity)], normal)
        for name, matrix in assembled.items():
            _scatter(matrix, local[name], connectivity)
    scalar = np.asarray(
        (
            (1.0, 0.0, 0.0, 0.0),
            (0.0, 1.0, 0.0, 0.0),
            (0.0, 0.0, 1.0, 0.0),
            (0.5, 0.5, 0.0, 0.0),
            (0.0, 0.5, 0.5, 0.0),
            (0.5, 0.0, 0.5, 0.0),
            (0.0, 0.0, 0.0, 1.0),
        ),
        dtype=np.float64,
    )
    restriction = np.kron(scalar, np.eye(6))
    restricted = {name: restriction.T @ matrix @ restriction for name, matrix in assembled.items()}
    centre_block = restricted["total"][18:, 18:]
    centre_map = -np.linalg.solve(centre_block, restricted["total"][18:, :18])
    transform = np.vstack((np.eye(18), centre_map))
    condensed: dict[str, np.ndarray] = {}
    for name, matrix in restricted.items():
        value = transform.T @ matrix @ transform
        condensed[name] = 0.5 * (value + value.T)
    return condensed | {"centre_block": centre_block, "centre_map": centre_map, "restriction": restriction}


def _rigid(vertices: np.ndarray) -> np.ndarray:
    result = np.zeros((18, 6), dtype=np.float64)
    for node, xyz in enumerate(vertices):
        base = 6 * node
        result[base : base + 3, :3] = np.eye(3)
        for mode in range(3):
            omega = np.eye(3)[mode]
            result[base : base + 3, mode + 3] = np.cross(omega, xyz)
            result[base + 3 : base + 6, mode + 3] = omega
    return result


def verify(proof: Mapping[str, Any]) -> dict[str, Any]:
    if proof.get("schema") != PROOF_SCHEMA or proof.get("candidate_formulation_id") != FORMULATION_ID:
        raise ValueError("unexpected V4A proof identity")
    contract = load_document(CONTRACT)
    if proof.get("contract_sha256") != sha256_file(CONTRACT):
        raise ValueError("proof contract hash mismatch")
    if proof.get("production_boundary") != {
        "anymesh_untouched": True,
        "default_q4_formulation": "e4-pl",
        "default_s3_formulation": "legacy-s3",
        "q4_mechanics_unchanged": True,
    }:
        raise ValueError("production boundary mismatch")
    if proof.get("stage4a_rerun_authorized") is not False:
        raise ValueError("proof improperly authorizes Stage 4A")
    vertices = np.asarray(((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.2, 0.9, 0.0)))
    expected = reconstruct(vertices, np.asarray((0.0, 0.0, 1.0)))
    payloads = proof["local"]["payloads"]
    worst = 0.0
    for name, value in expected.items():
        supplied = _decode(payloads[name])
        worst = max(worst, _relative_inf(supplied, value))
    physical_rank = _rank(expected["physical"], 1.0e-10)
    total_rank = _rank(expected["total"], 1.0e-10)
    centre_rank = _rank(expected["centre_block"], 1.0e-12)
    rigid_residual = float(
        np.linalg.norm(expected["total"] @ _rigid(vertices), ord=np.inf)
        / max(np.linalg.norm(expected["total"], ord=np.inf), 1.0)
    )
    component_sum = _relative_inf(
        expected["physical"] + expected["pl"] + expected["hourglass"],
        expected["total"],
    )
    symmetry = _relative_inf(expected["total"], expected["total"].T)
    construction = bool(centre_rank == 6 and worst <= 3.0e-13 and component_sum <= 3.0e-13)
    local_passed = bool(
        construction
        and physical_rank == 9
        and total_rank == 12
        and rigid_residual <= 3.0e-12
        and symmetry <= 3.0e-13
    )
    later_stages_absent = bool(
        proof.get("later_stages") == "NOT_EXECUTED_LOCAL_GATE_FAILED"
        and proof.get("macrocell") == {}
        and proof.get("development_records") == []
    )
    return {
        "authority_complete": contract.get("schema") == "anysolver.e4-pl-s3-v4a-subcell-screen-contract-v1",
        "candidate_formulation_id": FORMULATION_ID,
        "construction_identity_passed": construction,
        "independent_centre_block_rank": centre_rank,
        "independent_component_sum_relative_inf_hex": component_sum.hex(),
        "independent_local_identity_worst_relative_inf_hex": worst.hex(),
        "independent_physical_rank": physical_rank,
        "independent_rigid_residual_relative_inf_hex": rigid_residual.hex(),
        "independent_symmetry_relative_inf_hex": symmetry.hex(),
        "independent_total_rank": total_rank,
        "later_stages_absent": later_stages_absent,
        "local_operator_passed": local_passed,
        "mixed_interface_passed": False,
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
