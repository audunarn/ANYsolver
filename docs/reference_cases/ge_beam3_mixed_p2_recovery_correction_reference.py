"""Independent rational audit of the GE-Beam3 P2 shear recovery correction."""

from __future__ import annotations

import argparse
import hashlib
import json
from fractions import Fraction
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CORRECTION = Path(__file__).with_name("ge_beam3_mixed_p2_recovery_correction.json")
CASES = Path(__file__).with_name("ge_beam3_mixed_p2_cases.json")


def _unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    made: dict[str, Any] = {}
    for key, value in pairs:
        if key in made:
            raise ValueError(f"duplicate key: {key}")
        made[key] = value
    return made


def _reject_constant(value: str) -> None:
    raise ValueError(f"nonfinite value: {value}")


def _load(path: Path) -> tuple[bytes, dict[str, Any]]:
    raw = path.read_bytes()
    value = json.loads(
        raw.decode("utf-8"),
        object_pairs_hook=_unique,
        parse_constant=_reject_constant,
    )
    if not isinstance(value, dict):
        raise ValueError(f"{path.name} must contain an object")
    canonical = (
        json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")
    if raw != canonical:
        raise ValueError(f"{path.name} is not canonical JSON")
    return raw, value


def _fraction(value: dict[str, Any]) -> Fraction:
    if set(value) != {"denominator", "numerator"}:
        raise ValueError("rational record keys mismatch")
    numerator = value["numerator"]
    denominator = value["denominator"]
    if type(numerator) is not int or type(denominator) is not int or denominator <= 0:
        raise ValueError("rational record is malformed")
    return Fraction(numerator, denominator)


def check() -> dict[str, Any]:
    cases_raw, cases = _load(CASES)
    correction_raw, correction = _load(CORRECTION)
    base = correction["base_preregistration"]["case_manifest"]
    if len(cases_raw) != base["bytes"]:
        raise ValueError("base case-manifest byte count mismatch")
    if hashlib.sha256(cases_raw).hexdigest().upper() != base["sha256"]:
        raise ValueError("base case-manifest hash mismatch")
    invalid = correction["incident"]["invalid_case_id"]
    old_rows = cases["cases"]["recovery_states"]
    if sum(row.get("case_id") == invalid for row in old_rows) != 1:
        raise ValueError("invalid incident fixture is not uniquely preserved")

    replacement = correction["replacement"]
    ell = _fraction(replacement["cell_length"])
    shear = _fraction(replacement["section"]["shear_stiffness_y"])
    bending = _fraction(replacement["section"]["bending_stiffness_z"])
    gamma = _fraction(replacement["expected"]["force_strain_gamma_y"])
    theta = _fraction(replacement["vertex_rotation"]["radians"])
    moment = _fraction(replacement["expected"]["bending_moment_z_abs"])
    curvature = _fraction(replacement["expected"]["moment_curvature_z_abs"])
    shear_resultant = _fraction(replacement["expected"]["shear_resultant_y"])

    derived_theta = -(ell * ell * shear * gamma) / (12 * bending)
    derived_moment = ell * shear * gamma / 2
    predicates = {
        "force_strain_is_manufactured_slope": gamma == Fraction(1, 5000),
        "left_moment_stationarity": -ell * moment / (6 * bending) - theta == 0,
        "local_rotation_stationarity": -ell * shear * gamma + 2 * moment == 0,
        "moment_curvature_relation": curvature == moment / bending,
        "right_moment_stationarity": ell * moment / (6 * bending) + theta == 0,
        "shear_constitutive_relation": shear_resultant == shear * gamma,
        "vertex_rotation_is_derived": theta == derived_theta,
        "endpoint_moment_is_derived": moment == derived_moment,
    }
    if not all(predicates.values()):
        raise ValueError("manufactured mixed recovery stationarity failed")
    content = {
        "case_id": replacement["case_id"],
        "correction_sha256": hashlib.sha256(correction_raw).hexdigest().upper(),
        "predicates": predicates,
        "schema": "anysolver.ge-beam3-mixed-p2-recovery-correction-check-v1",
        "status": "PASS",
    }
    digest = hashlib.sha256(
        (
            json.dumps(content, allow_nan=False, separators=(",", ":"), sort_keys=True)
            + "\n"
        ).encode("utf-8")
    ).hexdigest().upper()
    return {"content_sha256": digest, "status": "PASS"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-only", action="store_true", required=True)
    parser.parse_args()
    print(json.dumps(check(), allow_nan=False, separators=(",", ":"), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

