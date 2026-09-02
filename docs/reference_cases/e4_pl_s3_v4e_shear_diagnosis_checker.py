"""Independent checker for the V4E thickness-scaled shear diagnosis."""

from __future__ import annotations

import argparse
import hashlib
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
import e4_pl_s3_v4d_screen_checker as v4d_reference


CONTRACT = REFERENCE / "e4_pl_s3_v4e_shear_diagnosis_contract.json"
PROOF_SCHEMA = "anysolver.e4-pl-s3-v4e-shear-diagnosis-proof-v1"
CHECK_SCHEMA = "anysolver.e4-pl-s3-v4e-shear-diagnosis-check-v1"
THICKNESSES = (1.0, 0.1, 0.01, 0.001)
DIAGONALS = ("slash", "backslash")
NORMAL = np.asarray((0.0, 0.0, 1.0), dtype=np.float64)

canonical_bytes = independent_q4.canonical_bytes
sha256_file = independent_q4.sha256_file
load_document = independent_q4.load_document


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


def _macro_matrices(thickness: float, diagonal: str) -> dict[str, np.ndarray]:
    independent_q4.THICKNESS = float(thickness)
    v4d_reference.THICKNESS = float(thickness)
    coordinates = np.asarray(((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.0, 1.0, 0.0), (0.0, 1.0, 0.0)))
    q4_raw = independent_q4._q4(coordinates, NORMAL)
    q4 = {name: np.asarray(q4_raw[name], dtype=np.float64) for name in ("physical", "pl", "total")}
    s3 = {name: np.zeros((24, 24), dtype=np.float64) for name in q4}
    triangles = ((0, 1, 3), (1, 2, 3)) if diagonal == "slash" else ((0, 1, 2), (0, 2, 3))
    for triangle in triangles:
        made = v4d_reference.reconstruct(coordinates[np.asarray(triangle)], NORMAL)
        for name in s3:
            independent_q4._scatter(s3[name], np.asarray(made[name]), triangle)
    return {"coordinates": coordinates, **{f"q4_{name}": value for name, value in q4.items()}, **{f"s3_{name}": value for name, value in s3.items()}}


def _sample(thickness: float, diagonal: str) -> dict[str, Any]:
    made = _macro_matrices(thickness, diagonal)
    modes = physical_first._modes(made["coordinates"])
    vector = modes["linear_rotation"]
    q4_action = made["q4_total"] @ vector
    s3_action = made["s3_total"] @ vector
    q4_energy = float(vector @ q4_action)
    s3_energy = float(vector @ s3_action)
    residual = float(np.linalg.norm(s3_action - q4_action, ord=np.inf) / max(np.linalg.norm(q4_action, ord=np.inf), 1.0))
    physical_residual = float(np.linalg.norm(made["s3_physical"] @ vector - made["q4_physical"] @ vector, ord=np.inf) / max(np.linalg.norm(made["q4_physical"] @ vector, ord=np.inf), 1.0))
    pl_work = max(abs(float(vector @ made["q4_pl"] @ vector)), abs(float(vector @ made["s3_pl"] @ vector)))
    identity_worst = 0.0
    for name in ("constant_kappa_x", "constant_kappa_y", "constant_kappa_xy", "quadratic_transverse"):
        mode = modes[name]
        expected = made["q4_total"] @ mode
        identity_worst = max(identity_worst, float(np.linalg.norm(made["s3_total"] @ mode - expected, ord=np.inf) / max(np.linalg.norm(expected, ord=np.inf), 1.0)))
    return {
        "diagonal": diagonal,
        "energy_ratio_hex": float(s3_energy / q4_energy).hex(),
        "identity_trace_worst_relative_inf_hex": identity_worst.hex(),
        "linear_rotation_action_relative_inf_hex": residual.hex(),
        "physical_action_relative_inf_hex": physical_residual.hex(),
        "pl_work_abs_hex": pl_work.hex(),
        "q4_energy_hex": q4_energy.hex(),
        "s3_energy_hex": s3_energy.hex(),
        "thickness_hex": float(thickness).hex(),
    }


def _relative(actual: float, expected: float) -> float:
    return abs(actual - expected) / max(abs(expected), 1.0)


def verify(proof: Mapping[str, Any]) -> dict[str, Any]:
    if proof.get("schema") != PROOF_SCHEMA or proof.get("contract_sha256") != sha256_file(CONTRACT):
        raise ValueError("unexpected V4E proof identity")
    records = list(proof.get("records", []))
    if sha256_bytes(canonical_bytes(records)) != proof.get("records_sha256"):
        raise ValueError("record payload hash mismatch")
    expected = [_sample(thickness, diagonal) for thickness in THICKNESSES for diagonal in DIAGONALS]
    if len(records) != len(expected):
        raise ValueError("V4E record count mismatch")
    identity_worst = 0.0
    for actual, made in zip(records, expected):
        if actual["diagonal"] != made["diagonal"] or actual["thickness_hex"] != made["thickness_hex"]:
            raise ValueError("V4E record ordering mismatch")
        for key in ("energy_ratio_hex", "identity_trace_worst_relative_inf_hex", "linear_rotation_action_relative_inf_hex", "physical_action_relative_inf_hex", "pl_work_abs_hex", "q4_energy_hex", "s3_energy_hex"):
            identity_worst = max(identity_worst, _relative(float.fromhex(str(actual[key])), float.fromhex(str(made[key]))))
    by_key = {(str(row["diagonal"]), float.fromhex(str(row["thickness_hex"]))): row for row in expected}
    stable = True
    for diagonal in DIAGONALS:
        rows = (by_key[(diagonal, 0.01)], by_key[(diagonal, 0.001)])
        residuals = tuple(float.fromhex(str(row["linear_rotation_action_relative_inf_hex"])) for row in rows)
        ratios = tuple(float.fromhex(str(row["energy_ratio_hex"])) for row in rows)
        stable = stable and min(residuals) > 0.1 and abs(residuals[0] - residuals[1]) <= 0.01 and 0.0 < min(ratios) <= max(ratios) < 1.0 and abs(ratios[0] - ratios[1]) <= 0.01
    trace_identity = max(float.fromhex(str(row["identity_trace_worst_relative_inf_hex"])) for row in expected) <= 3.0e-9
    zero_pl = all(float.fromhex(str(row["pl_work_abs_hex"])) == 0.0 for row in expected)
    diagnostic_identity = identity_worst <= 3.0e-13 and trace_identity and zero_pl
    contract = load_document(CONTRACT)
    return {
        "authority_complete": contract.get("schema") == "anysolver.e4-pl-s3-v4e-shear-diagnosis-contract-v1",
        "diagnostic_identity_passed": bool(diagnostic_identity),
        "independent_record_count": len(expected),
        "independent_reconstruction_worst_relative_hex": identity_worst.hex(),
        "later_stages_absent": proof.get("later_stages") == "NOT_EXECUTED_DIAGNOSTIC_ONLY",
        "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "schema": CHECK_SCHEMA,
        "shear_replacement_required": bool(diagnostic_identity and stable),
        "thin_limit_stable": bool(stable),
        "zero_pl_work": bool(zero_pl),
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
