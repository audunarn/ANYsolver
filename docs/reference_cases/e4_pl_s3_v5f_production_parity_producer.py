"""Emit deterministic production-candidate parity proofs for S3 V5F."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "docs/reference_cases/e4_pl_s3_v5f_production_parity_contract.json"
SCHEMA = "anysolver.e4-pl-s3-v5f-production-parity-proof-v1"
FORMULATION_ID = "CANDIDATE_E4_PL_S3_V2B_FLAT_LINEAR_V1"
DIAGONALS = ("slash", "backslash", "alternating")
LEVELS = (20, 40, 80)
MASKS = ("dispersed", "chain")
FRACTIONS = (1, 5, 10, 25)
COMPONENTS = ("membrane", "bending", "shear", "physical", "pl", "total")
NORMAL = np.asarray((0.0, 0.0, 1.0), dtype=np.float64)


class ProductionParityError(RuntimeError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("ascii")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def load_canonical(path: Path) -> Any:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        made: dict[str, Any] = {}
        for key, value in items:
            if key in made:
                raise ProductionParityError(f"duplicate JSON key: {key}")
            made[key] = value
        return made

    raw = path.read_bytes()
    value = json.loads(raw, object_pairs_hook=pairs, parse_constant=lambda token: (_ for _ in ()).throw(ProductionParityError(f"nonfinite JSON token: {token}")))
    if canonical_bytes(value) != raw:
        raise ProductionParityError(f"noncanonical JSON: {path}")
    return value


def exclusive_write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(canonical_bytes(value))


def encode_array(value: Any) -> dict[str, Any]:
    array = np.asarray(value, dtype=np.float64)
    if not np.all(np.isfinite(array)):
        raise ProductionParityError("proof array contains nonfinite values")
    return {"hex": [float(item).hex() for item in array.reshape(-1)], "shape": list(array.shape)}


def validate_authority() -> Mapping[str, Any]:
    contract = load_canonical(CONTRACT)
    if contract.get("schema") != "anysolver.e4-pl-s3-v5f-production-parity-contract-v1":
        raise ProductionParityError("unexpected V5F contract schema")
    for binding in contract.get("frozen_inputs", []):
        path = ROOT / str(binding["path"])
        raw = path.read_bytes()
        if len(raw) != binding["bytes"] or sha256_bytes(raw) != binding["sha256"]:
            raise ProductionParityError(f"frozen input mismatch: {path}")
    boundary = contract.get("production_boundary", {})
    if boundary.get("default_q4_formulation") != "e4-pl" or boundary.get("default_s3_formulation") != "legacy-s3" or boundary.get("activation_authorized") is not False:
        raise ProductionParityError("production boundary mismatch")
    return contract


def _catalog() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for diagonal in DIAGONALS:
        for level in LEVELS:
            rows.append({"diagonal": diagonal, "fraction_percent": 0, "level": level, "mask": "dispersed"})
            for mask in MASKS:
                for fraction in FRACTIONS:
                    rows.append({"diagonal": diagonal, "fraction_percent": fraction, "level": level, "mask": mask})
    return rows


def _triangles(level: int, diagonal: str) -> tuple[np.ndarray, np.ndarray]:
    h = 1.0 / float(level)
    ll = np.asarray((0.0, 0.0, 0.0))
    lr = np.asarray((h, 0.0, 0.0))
    ul = np.asarray((0.0, h, 0.0))
    ur = np.asarray((h, h, 0.0))
    selected = "backslash" if diagonal == "alternating" else diagonal
    if selected == "slash":
        return np.asarray((ll, lr, ul)), np.asarray((lr, ur, ul))
    return np.asarray((ll, lr, ur)), np.asarray((ll, ur, ul))


def _production_case(coordinates: np.ndarray, order: tuple[int, int, int], normal: np.ndarray, case_id: str) -> dict[str, Any]:
    from anysolver.elements import create_shell_element
    from anysolver.fe_core import FEMesh, Material

    mesh = FEMesh()
    for node_id, coordinate in enumerate(coordinates, start=1):
        mesh.add_node(node_id, *coordinate)
    connectivity = tuple(index + 1 for index in order)
    element = create_shell_element(
        1,
        connectivity,
        "steel",
        formulation="e4-pl-s3-v2b",
        thickness=0.01,
        reference_normal=normal,
    )
    if type(element).__name__ != "StrictFlatLinearE4PLS3V2BShellElement" or element.formulation_id != FORMULATION_ID:
        raise ProductionParityError("public selector did not create the frozen V2B candidate")
    material = Material("steel", 210_000_000_000.0, 0.3, density=7850.0)
    components = element.compute_stiffness_components(mesh, material)
    displacement = np.asarray(tuple((index - 8.5) / 4096.0 for index in range(18)), dtype=np.float64)
    force = element.compute_internal_forces(mesh, displacement, material)
    recovered = element.compute_variational_resultants(mesh, displacement, material)
    pressure = element.compute_dead_transverse_pressure_load(mesh, 1000.0)
    return {
        "case_id": case_id,
        "components": {name: encode_array(components[name]) for name in COMPONENTS},
        "connectivity_order": list(order),
        "coordinates": encode_array(coordinates),
        "displacement": encode_array(displacement),
        "formulation_id": element.formulation_id,
        "internal_force": encode_array(force),
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
        "selector": "e4-pl-s3-v2b",
    }


def produce_proof(progress: Path | None = None) -> dict[str, Any]:
    contract = validate_authority()
    if progress is not None:
        progress.parent.mkdir(parents=True, exist_ok=True)
        progress.touch(exist_ok=False)
    base = np.asarray(((0.0, 0.0, 0.0), (2.0, 0.0, 0.0), (0.3, 1.1, 0.0)), dtype=np.float64)
    cases: list[dict[str, Any]] = []
    for order in ((0, 1, 2), (0, 2, 1), (1, 0, 2), (1, 2, 0), (2, 0, 1), (2, 1, 0)):
        cases.append(_production_case(base, order, NORMAL, "D3:" + "".join(map(str, order))))
    cases.append(_production_case(base, (0, 1, 2), -NORMAL, "DIRECTOR_REVERSAL"))
    catalog = _catalog()
    catalog_cases: list[dict[str, Any]] = []
    for row_index, row in enumerate(catalog):
        for triangle_index, coordinates in enumerate(_triangles(row["level"], row["diagonal"])):
            case_id = f"CATALOG:{row_index:02d}:T{triangle_index}"
            cases.append(_production_case(coordinates, (0, 1, 2), NORMAL, case_id))
            catalog_cases.append({"case_id": case_id, **row, "triangle_index": triangle_index})
        if progress is not None:
            with progress.open("ab") as stream:
                stream.write(canonical_bytes({"catalog_record": row_index + 1}))
    payload = {
        "activation_authorized": False,
        "candidate_formulation_id": FORMULATION_ID,
        "cases": cases,
        "catalog": catalog,
        "catalog_cases": catalog_cases,
        "catalog_record_count": len(catalog),
        "contract_sha256": sha256_file(CONTRACT),
        "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "schema": SCHEMA,
        "stage4b_execution_authorized": False,
    }
    payload["scientific_payload_sha256"] = sha256_bytes(canonical_bytes(payload))
    return payload


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--emit-production-parity-proof", action="store_true", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--progress", type=Path)
    args = parser.parse_args(argv)
    exclusive_write(args.output, produce_proof(args.progress))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
