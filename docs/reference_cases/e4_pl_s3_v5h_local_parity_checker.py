"""Independent V5H checker; it never imports production or producer mechanics."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "docs/reference_cases"
if str(REFERENCE) not in sys.path:
    sys.path.insert(0, str(REFERENCE))

import e4_pl_s3_v5b_relaxed_screen_checker as independent


CONTRACT = REFERENCE / "e4_pl_s3_v5h_local_parity_contract.json"
PROOF_SCHEMA = "anysolver.e4-pl-s3-v5h-local-parity-proof-v1"
CHECK_SCHEMA = "anysolver.e4-pl-s3-v5h-local-parity-check-v1"
FORMULATION_ID = "CANDIDATE_E4_PL_S3_V2C_FLAT_LINEAR_PARITY_V1"
IMPLEMENTATION_ID = "E4_PL_S3_V2C_MIN3_RELAXED_UHM_CST_PL_PARITY_V1"
FORMULATION_SCHEMA = "anysolver.e4-pl-s3-v2c-flat-linear-parity-element-v1"
COMPONENTS = ("membrane", "bending", "shear", "physical", "pl", "total")
THICKNESS = 0.01
DENSITY = 7850.0
PRESSURE = 1000.0
COMPRESSION = np.asarray((2.0, 2.0, 0.0), dtype=np.float64)
RELATIVE_LIMIT = 3.0e-12


class LocalParityCheckError(RuntimeError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
        + "\n"
    ).encode("ascii")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


def _pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    made: dict[str, Any] = {}
    for key, value in items:
        if key in made:
            raise LocalParityCheckError(f"duplicate JSON key: {key}")
        made[key] = value
    return made


def load_canonical(path: Path) -> Any:
    raw = path.read_bytes()
    value = json.loads(
        raw,
        object_pairs_hook=_pairs,
        parse_constant=lambda token: (_ for _ in ()).throw(
            LocalParityCheckError(f"nonfinite JSON token: {token}")
        ),
    )
    if canonical_bytes(value) != raw:
        raise LocalParityCheckError(f"noncanonical JSON: {path}")
    return value


def decode_array(value: Mapping[str, Any]) -> np.ndarray:
    if not isinstance(value, Mapping) or set(value) != {"hex", "shape"}:
        raise LocalParityCheckError("malformed encoded array")
    shape = tuple(value["shape"])
    entries = value["hex"]
    if not isinstance(entries, list) or not all(isinstance(item, str) for item in entries):
        raise LocalParityCheckError("malformed encoded array entries")
    made = np.asarray([float.fromhex(item) for item in entries], dtype=np.float64)
    if not np.all(np.isfinite(made)) or int(np.prod(shape, dtype=np.int64)) != made.size:
        raise LocalParityCheckError("invalid encoded array")
    return made.reshape(shape)


def _relative(left: Any, right: Any) -> float:
    left_array = np.asarray(left, dtype=np.float64)
    right_array = np.asarray(right, dtype=np.float64)
    return float(
        np.linalg.norm(left_array - right_array, ord=np.inf)
        / max(float(np.linalg.norm(right_array, ord=np.inf)), 1.0)
    )


def _mass(vertices: np.ndarray) -> np.ndarray:
    area, _nx, _ny = independent.v5a_check._metric(vertices)
    nodal = DENSITY * THICKNESS * area / 3.0
    made = np.zeros((18, 18), dtype=np.float64)
    for node in range(3):
        for axis in range(3):
            made[6 * node + axis, 6 * node + axis] = nodal
    return made


def _geometric(vertices: np.ndarray) -> np.ndarray:
    area, nx, ny = independent.v5a_check._metric(vertices)
    gradients = np.column_stack((nx, ny))
    stress = np.asarray(
        ((COMPRESSION[0], COMPRESSION[2]), (COMPRESSION[2], COMPRESSION[1])),
        dtype=np.float64,
    )
    scalar = area * gradients @ stress @ gradients.T
    made = np.zeros((18, 18), dtype=np.float64)
    for first in range(3):
        for second in range(3):
            for axis in range(3):
                made[6 * first + axis, 6 * second + axis] = scalar[first, second]
    return 0.5 * (made + made.T)


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
        condensed / np.sqrt(np.outer(dynamic_mass, dynamic_mass))
    )
    buckling = np.linalg.eigvals(
        np.linalg.solve(geometric[np.ix_(dynamic, dynamic)], condensed)
    )
    return modal, np.sort(np.asarray(np.real_if_close(buckling), dtype=np.float64))


def _serialized(case: Mapping[str, Any]) -> bool:
    value = case.get("serialized")
    if not isinstance(value, Mapping):
        return False
    expected = {
        "formulation_id": FORMULATION_ID,
        "formulation_schema": FORMULATION_SCHEMA,
        "geometric_stiffness_policy_id": (
            "CST_MEMBRANE_STRESS_STIFFNESS_TRANSLATIONAL_3D_V1"
        ),
        "implementation_id": IMPLEMENTATION_ID,
        "mass_policy_id": "MYSTRAN_TRIA3_LUMPED_TRANSLATIONAL_MASS_V1",
        "quadrature_authority_id": "S3_V2C_MIN3_HAMMER3_DEGREE2_EXACT_V1",
        "recovery_policy_id": "SHELL_VARIATIONAL_RESULTANTS_V1",
        "relaxation_authority_sha256": (
            "0AE9DAA05B63A43D456423BCDC676E7421AB3583F152EE5DB3D0E36FE60A17A0"
        ),
        "selector": "e4-pl-s3-v2c",
        "serialization_policy_id": (
            "V2C_FORMULATION_SCHEMA_AND_STATELESS_FINGERPRINT_V1"
        ),
        "type": "StrictFlatLinearE4PLS3V2CShellElement",
    }
    if any(value.get(key) != expected_value for key, expected_value in expected.items()):
        return False
    if set(value) != {
        "element_id",
        "formulation_id",
        "formulation_schema",
        "geometric_stiffness_policy_id",
        "implementation_id",
        "mass_policy_id",
        "material_name",
        "node_ids",
        "quadrature_authority_id",
        "recovery_policy_id",
        "reference_normal",
        "relaxation_authority_sha256",
        "selector",
        "serialization_policy_id",
        "thickness",
        "type",
    }:
        return False
    return case.get("serialized_sha256") == sha256_bytes(canonical_bytes(value))


def verify_proof(proof: Mapping[str, Any]) -> dict[str, Any]:
    if (
        proof.get("schema") != PROOF_SCHEMA
        or proof.get("candidate_formulation_id") != FORMULATION_ID
        or proof.get("activation_authorized") is not False
        or proof.get("stage4b_execution_authorized") is not False
    ):
        raise LocalParityCheckError("V5H proof identity or authority mismatch")
    payload = dict(proof)
    claimed_payload_hash = payload.pop("scientific_payload_sha256", None)
    if claimed_payload_hash != sha256_bytes(canonical_bytes(payload)):
        raise LocalParityCheckError("V5H scientific payload hash mismatch")
    cases = proof.get("cases")
    if not isinstance(cases, list) or len(cases) != 14 or proof.get("case_count") != 14:
        raise LocalParityCheckError("V5H case coverage mismatch")
    expected_ids = []
    for geometry_id in ("BASE", "HOSTILE"):
        expected_ids.extend(
            f"{geometry_id}:D3:" + "".join(map(str, order))
            for order in itertools.permutations(range(3))
        )
        expected_ids.append(f"{geometry_id}:DIRECTOR_REVERSAL")
    if [case.get("case_id") for case in cases] != expected_ids:
        raise LocalParityCheckError("V5H case ordering mismatch")

    component_worst = 0.0
    mass_worst = 0.0
    geometric_worst = 0.0
    pressure_worst = 0.0
    work_worst = 0.0
    modal_worst = 0.0
    buckling_worst = 0.0
    failures: list[str] = []
    for case in cases:
        if (
            case.get("formulation_id") != FORMULATION_ID
            or case.get("implementation_id") != IMPLEMENTATION_ID
            or case.get("selector") != "e4-pl-s3-v2c"
        ):
            raise LocalParityCheckError("V5H production identity mismatch")
        coordinates = decode_array(case["coordinates"])
        order = tuple(case["connectivity_order"])
        if sorted(order) != [0, 1, 2]:
            raise LocalParityCheckError("invalid D3 order")
        vertices = coordinates[np.asarray(order)]
        expected = independent.reconstruct(vertices, thickness=THICKNESS)
        matrices = {
            name: decode_array(case["components"][name]) for name in COMPONENTS
        }
        for name in COMPONENTS:
            component_worst = max(
                component_worst,
                _relative(matrices[name], expected[name]),
            )
        actual_mass = decode_array(case["mass"])
        expected_mass = _mass(vertices)
        mass_worst = max(mass_worst, _relative(actual_mass, expected_mass))
        actual_geometric = decode_array(case["geometric_stiffness"])
        expected_geometric = _geometric(vertices)
        geometric_worst = max(
            geometric_worst,
            _relative(actual_geometric, expected_geometric),
        )
        expected_pressure = np.asarray(expected["pressure_load"])
        if str(case["case_id"]).endswith("DIRECTOR_REVERSAL"):
            expected_pressure = -expected_pressure
        pressure_worst = max(
            pressure_worst,
            _relative(decode_array(case["pressure_load"]), expected_pressure),
        )
        displacement = decode_array(case["displacement"])
        resultants = {
            name: decode_array(value) for name, value in case["resultants"].items()
        }
        weights = resultants["physical_weights"][:, None]
        for component, strain_name, resultant_name in (
            ("membrane", "membrane_strain", "membrane_resultants"),
            ("bending", "curvature", "bending_resultants"),
            ("shear", "transverse_shear_strain", "transverse_shear_resultants"),
        ):
            recovered_work = float(
                np.sum(weights * resultants[strain_name] * resultants[resultant_name])
            )
            matrix_work = float(displacement @ matrices[component] @ displacement)
            work_worst = max(
                work_worst,
                abs(recovered_work - matrix_work) / max(abs(matrix_work), 1.0),
            )
        expected_modal, expected_buckling = _screen_eigenvalues(
            expected["total"],
            expected_mass,
            expected_geometric,
        )
        modal_worst = max(
            modal_worst,
            _relative(decode_array(case["modal_eigenvalues"]), expected_modal),
        )
        buckling_worst = max(
            buckling_worst,
            _relative(
                decode_array(case["buckling_eigenvalues"]),
                expected_buckling,
            ),
        )
        ranks = {
            "mass": int(np.linalg.matrix_rank(actual_mass)),
            "geometric": int(np.linalg.matrix_rank(actual_geometric)),
            "physical": int(np.linalg.matrix_rank(matrices["physical"], tol=max(float(np.linalg.norm(matrices["physical"], ord=2)), 1.0) * 1.0e-10)),
            "pl": int(np.linalg.matrix_rank(matrices["pl"], tol=max(float(np.linalg.norm(matrices["pl"], ord=2)), 1.0) * 1.0e-10)),
            "total": int(np.linalg.matrix_rank(matrices["total"], tol=max(float(np.linalg.norm(matrices["total"], ord=2)), 1.0) * 1.0e-10)),
        }
        if (
            ranks != {"mass": 9, "geometric": 6, "physical": 9, "pl": 3, "total": 12}
            or case.get("v2b_static_byte_identical") is not True
            or case.get("serialization_roundtrip") is not True
            or not _serialized(case)
            or float.fromhex(case["phi_squared_hex"]) <= 0.0
        ):
            failures.append(str(case["case_id"]))
    worst = max(
        component_worst,
        mass_worst,
        geometric_worst,
        pressure_worst,
        work_worst,
        modal_worst,
        buckling_worst,
    )
    return {
        "activation_authorized": False,
        "buckling_worst_hex": buckling_worst.hex(),
        "candidate_formulation_id": FORMULATION_ID,
        "case_count": len(cases),
        "component_worst_hex": component_worst.hex(),
        "failure_case_ids": failures,
        "geometric_worst_hex": geometric_worst.hex(),
        "mass_worst_hex": mass_worst.hex(),
        "modal_worst_hex": modal_worst.hex(),
        "passed": not failures and worst <= RELATIVE_LIMIT,
        "pressure_worst_hex": pressure_worst.hex(),
        "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "schema": CHECK_SCHEMA,
        "scientific_payload_sha256": claimed_payload_hash,
        "stage4b_execution_authorized": False,
        "work_worst_hex": work_worst.hex(),
    }


def exclusive_write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(canonical_bytes(value))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-v5h-local-parity-proof", action="store_true", required=True)
    parser.add_argument("--proof", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    exclusive_write(args.output, verify_proof(load_canonical(args.proof)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
