"""Emit the bounded S3 V5H V2C local-parity proof."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "docs/reference_cases/e4_pl_s3_v5h_local_parity_contract.json"
SCHEMA = "anysolver.e4-pl-s3-v5h-local-parity-proof-v1"
FORMULATION_ID = "CANDIDATE_E4_PL_S3_V2C_FLAT_LINEAR_PARITY_V1"
IMPLEMENTATION_ID = "E4_PL_S3_V2C_MIN3_RELAXED_UHM_CST_PL_PARITY_V1"
COMPONENTS = ("membrane", "bending", "shear", "physical", "pl", "total")
NORMAL = np.asarray((0.0, 0.0, 1.0), dtype=np.float64)
THICKNESS = 0.01
YOUNG = 210_000_000_000.0
POISSON = 0.3
DENSITY = 7850.0
PRESSURE = 1000.0
COMPRESSION = np.asarray((2.0, 2.0, 0.0), dtype=np.float64)
GEOMETRIES = {
    "BASE": np.asarray(((0.0, 0.0, 0.0), (2.0, 0.0, 0.0), (0.3, 1.1, 0.0))),
    "HOSTILE": np.asarray(((0.0, 0.0, 0.0), (1.7, 0.1, 0.0), (0.15, 0.55, 0.0))),
}


class LocalParityError(RuntimeError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
        + "\n"
    ).encode("ascii")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def _pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    made: dict[str, Any] = {}
    for key, value in items:
        if key in made:
            raise LocalParityError(f"duplicate JSON key: {key}")
        made[key] = value
    return made


def load_canonical(path: Path) -> Any:
    raw = path.read_bytes()
    value = json.loads(
        raw,
        object_pairs_hook=_pairs,
        parse_constant=lambda token: (_ for _ in ()).throw(
            LocalParityError(f"nonfinite JSON token: {token}")
        ),
    )
    if canonical_bytes(value) != raw:
        raise LocalParityError(f"noncanonical JSON: {path}")
    return value


def exclusive_write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(canonical_bytes(value))


def encode_array(value: Any) -> dict[str, Any]:
    array = np.asarray(value, dtype=np.float64)
    if not np.all(np.isfinite(array)):
        raise LocalParityError("proof array contains nonfinite values")
    return {
        "hex": [float(item).hex() for item in array.reshape(-1)],
        "shape": list(array.shape),
    }


def validate_authority() -> Mapping[str, Any]:
    contract = load_canonical(CONTRACT)
    if contract.get("schema") != "anysolver.e4-pl-s3-v5h-local-parity-contract-v1":
        raise LocalParityError("unexpected V5H contract schema")
    for binding in contract.get("frozen_inputs", []):
        path = ROOT / str(binding["path"])
        raw = path.read_bytes()
        if len(raw) != binding["bytes"] or sha256_bytes(raw) != binding["sha256"]:
            raise LocalParityError(f"frozen input mismatch: {path}")
    boundary = contract.get("production_boundary", {})
    if boundary != {
        "activation_authorized": False,
        "default_q4_formulation": "e4-pl",
        "default_s3_formulation": "legacy-s3",
        "q4_mechanics_unchanged": True,
        "stage4b_execution_authorized": False,
    }:
        raise LocalParityError("V5H production boundary mismatch")
    return contract


def _screen_eigenvalues(
    stiffness: np.ndarray,
    mass: np.ndarray,
    geometric: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    active = np.arange(6, 18, dtype=np.intp)
    dynamic = active[np.asarray([mass[index, index] > 0.0 for index in active])]
    algebraic = active[np.asarray([mass[index, index] == 0.0 for index in active])]
    kaa = stiffness[np.ix_(algebraic, algebraic)]
    kad = stiffness[np.ix_(algebraic, dynamic)]
    condensed = stiffness[np.ix_(dynamic, dynamic)] - kad.T @ np.linalg.solve(kaa, kad)
    condensed = 0.5 * (condensed + condensed.T)
    dynamic_mass = mass[np.ix_(dynamic, dynamic)].diagonal()
    modal = np.linalg.eigvalsh(
        condensed
        / np.sqrt(np.outer(dynamic_mass, dynamic_mass))
    )
    geometric_dynamic = geometric[np.ix_(dynamic, dynamic)]
    buckling = np.linalg.eigvals(np.linalg.solve(geometric_dynamic, condensed))
    buckling = np.sort(np.asarray(np.real_if_close(buckling), dtype=np.float64))
    if (
        len(dynamic) != 6
        or len(algebraic) != 6
        or np.linalg.matrix_rank(kaa) != 6
        or not np.all(np.isfinite(modal))
        or not np.all(np.isfinite(buckling))
        or np.any(modal <= 0.0)
        or np.any(buckling <= 0.0)
    ):
        raise LocalParityError("invalid constrained modal/buckling screen")
    return modal, buckling


def _case(
    geometry_id: str,
    coordinates: np.ndarray,
    order: tuple[int, int, int],
    normal: np.ndarray,
    case_id: str,
) -> dict[str, Any]:
    from anysolver.e4_pl_s3_v2b_element import StrictFlatLinearE4PLS3V2BShellElement
    from anysolver.e4_pl_s3_v2c_element import StrictFlatLinearE4PLS3V2CShellElement
    from anysolver.elements import create_shell_element, shell_element_from_dict
    from anysolver.fe_core import FEMesh, Material

    mesh = FEMesh()
    for node_id, coordinate in enumerate(coordinates, start=1):
        mesh.add_node(node_id, *coordinate)
    connectivity = tuple(index + 1 for index in order)
    candidate = create_shell_element(
        1,
        connectivity,
        "steel",
        formulation="e4-pl-s3-v2c",
        thickness=THICKNESS,
        reference_normal=normal,
    )
    if (
        type(candidate) is not StrictFlatLinearE4PLS3V2CShellElement
        or candidate.formulation_id != FORMULATION_ID
    ):
        raise LocalParityError("public selector did not create the V2C candidate")
    predecessor = StrictFlatLinearE4PLS3V2BShellElement(
        2,
        connectivity,
        "steel",
        thickness=THICKNESS,
        reference_normal=normal,
    )
    material = Material("steel", YOUNG, POISSON, density=DENSITY)
    components = candidate.compute_stiffness_components(mesh, material)
    previous = predecessor.compute_stiffness_components(mesh, material)
    static_identity = all(
        np.array_equal(components[name], previous[name]) for name in COMPONENTS
    ) and components["phi_squared"] == previous["phi_squared"]
    mass = candidate.compute_mass_matrix(mesh, material)
    geometric = candidate.compute_geometric_stiffness_matrix(
        mesh,
        material,
        {
            "bending_compression": [0.0, 0.0, 0.0],
            "membrane_compression": COMPRESSION.tolist(),
            "stress_second_moment": [0.0, 0.0, 0.0],
        },
    )
    displacement = np.asarray(
        tuple((index - 8.5) / 4096.0 for index in range(18)),
        dtype=np.float64,
    )
    recovered = candidate.compute_stresses(mesh, displacement, material)
    pressure = candidate.compute_dead_transverse_pressure_load(mesh, PRESSURE)
    modal, buckling = _screen_eigenvalues(components["total"], mass, geometric)
    serialized = candidate.to_dict()
    restored = shell_element_from_dict(serialized)
    serialization_roundtrip = (
        type(restored) is StrictFlatLinearE4PLS3V2CShellElement
        and restored.to_dict() == serialized
    )
    return {
        "buckling_eigenvalues": encode_array(buckling),
        "case_id": case_id,
        "components": {name: encode_array(components[name]) for name in COMPONENTS},
        "connectivity_order": list(order),
        "coordinates": encode_array(coordinates),
        "displacement": encode_array(displacement),
        "formulation_id": candidate.formulation_id,
        "geometric_stiffness": encode_array(geometric),
        "geometry_id": geometry_id,
        "implementation_id": IMPLEMENTATION_ID,
        "mass": encode_array(mass),
        "modal_eigenvalues": encode_array(modal),
        "normal": encode_array(normal),
        "phi_squared_hex": float(components["phi_squared"]).hex(),
        "pressure_load": encode_array(pressure),
        "resultants": {
            name: encode_array(recovered[name])
            for name in (
                "membrane_strain",
                "curvature",
                "transverse_shear_strain",
                "membrane_resultants",
                "bending_resultants",
                "transverse_shear_resultants",
                "physical_weights",
            )
        },
        "selector": "e4-pl-s3-v2c",
        "serialization_roundtrip": serialization_roundtrip,
        "serialized": serialized,
        "serialized_sha256": sha256_bytes(canonical_bytes(serialized)),
        "v2b_static_byte_identical": static_identity,
    }


def produce_proof(progress: Path | None = None) -> dict[str, Any]:
    validate_authority()
    if progress is not None:
        progress.parent.mkdir(parents=True, exist_ok=True)
        progress.touch(exist_ok=False)
    cases: list[dict[str, Any]] = []
    orders = tuple(itertools.permutations(range(3)))
    for geometry_id, coordinates in GEOMETRIES.items():
        for order in orders:
            case_id = f"{geometry_id}:D3:" + "".join(map(str, order))
            cases.append(_case(geometry_id, coordinates, order, NORMAL, case_id))
        cases.append(
            _case(
                geometry_id,
                coordinates,
                (0, 1, 2),
                -NORMAL,
                f"{geometry_id}:DIRECTOR_REVERSAL",
            )
        )
        if progress is not None:
            with progress.open("ab") as stream:
                stream.write(canonical_bytes({"geometry_complete": geometry_id}))
    payload = {
        "activation_authorized": False,
        "candidate_formulation_id": FORMULATION_ID,
        "case_count": len(cases),
        "cases": cases,
        "contract_sha256": sha256_file(CONTRACT),
        "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "schema": SCHEMA,
        "stage4b_execution_authorized": False,
    }
    payload["scientific_payload_sha256"] = sha256_bytes(canonical_bytes(payload))
    return payload


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--emit-v5h-local-parity-proof", action="store_true", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--progress", type=Path)
    args = parser.parse_args(argv)
    exclusive_write(args.output, produce_proof(args.progress))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
