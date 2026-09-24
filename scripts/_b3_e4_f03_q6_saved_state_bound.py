"""Experimental physical component bound from an archived Q6 KKT certificate.

This reuses the saved candidate and matrix. It does not certify the physical
trace functionals or replace the complete F03 scientific adjudication.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

from scripts._b3_e4_f03_q6_interval_kernel import compiled_product_bounds
from scripts._b3_e4_f03_q6_system_archive import read_system
from scripts._b3_e4_f03_sparse_certificate import _norm2, _residual_abs, _up


def _json_bounded(path: Path, limit: int) -> tuple[dict, str]:
    payload = path.read_bytes()
    if not 0 < len(payload) <= limit:
        raise ValueError("saved Q6 JSON exceeds its byte bound")
    value = json.loads(payload)
    if type(value) is not dict:
        raise ValueError("saved Q6 JSON must be an object")
    return value, hashlib.sha256(payload).hexdigest()


def bound_components(matrix, rhs: np.ndarray, state: np.ndarray,
                     inverse_infinity_upper: float,
                     displacement_scale: np.ndarray,
                     multiplier_scale: np.ndarray) -> dict:
    """Bound exact saved-scale mappings using a certified inverse norm.

    The interval product and residual use the same experimental arithmetic
    kernel as the archived Q6 KKT certificate. The inverse bound is supplied
    by that certificate, not recomputed here. Separately rounded physical
    recovery arithmetic is outside this bound.
    """
    n = matrix.shape[0]
    if (matrix.shape != (n, n) or n <= 3 or rhs.shape != (n,) or
            state.shape != (n,) or displacement_scale.shape != (n-3,) or
            multiplier_scale.shape != (3,) or
            not all(np.isfinite(v).all() for v in
                    (rhs, state, displacement_scale, multiplier_scale)) or
            np.any(displacement_scale <= 0) or
            np.any(multiplier_scale <= 0) or
            not np.isfinite(inverse_infinity_upper) or
            inverse_infinity_upper <= 0):
        raise ValueError("invalid saved Q6 state-bound inputs")
    low, high = compiled_product_bounds(matrix.tocsr(), state[:, None])
    residual_abs = _residual_abs(low, high, rhs[:, None])
    residual_infinity = float(np.max(residual_abs))
    residual_two = float(_norm2(residual_abs)[1])
    scaled_error = float(_up(_up(residual_infinity)*inverse_infinity_upper))
    displacement_error = float(_up(scaled_error*float(np.max(displacement_scale))))
    root_force_error = float(_up(scaled_error*float(np.max(multiplier_scale[:2]))))
    root_moment_error = float(_up(scaled_error*float(multiplier_scale[2])))
    return {
        "residual_infinity_upper": residual_infinity,
        "residual_two_upper_recomputed": residual_two,
        "scaled_state_component_error_upper": scaled_error,
        "physical_displacement_component_error_upper": displacement_error,
        "physical_root_force_component_error_upper": root_force_error,
        "physical_root_moment_component_error_upper": root_moment_error,
    }


def evaluate_saved(certificate_dir: Path) -> dict:
    certificate_dir = Path(certificate_dir)
    measurement, _ = _json_bounded(certificate_dir/"measurement.json", 65536)
    candidate, candidate_hash = _json_bounded(
        certificate_dir/"candidate_state.json", 2*1024**2)
    if (measurement.get("candidate_state_sha256") != candidate_hash or
            measurement.get("case_id") != candidate.get("case_id") or
            measurement.get("certificate", {}).get("status") !=
            "CERTIFIED_WITHIN_LIMIT"):
        raise ValueError("saved candidate/certificate identity mismatch")
    matrix, rhs, displacement_scale, multiplier_scale, archive_bytes = read_system(
        certificate_dir/"scaled_system.npz",
        order=measurement["kkt_order"], nnz=measurement["kkt_nnz"],
        archive_sha256=measurement["scaled_system_archive_sha256"],
        kkt_rhs_sha256=measurement["scaled_kkt_rhs_sha256"])
    if archive_bytes != measurement["scaled_system_archive_bytes"]:
        raise ValueError("saved system archive size mismatch")
    state = np.asarray(candidate["scaled_kkt_state"], dtype=np.float64)
    bound = bound_components(
        matrix, rhs, state,
        float(measurement["certificate"]["inverse_infinity_upper"]),
        displacement_scale, multiplier_scale)
    if bound["residual_two_upper_recomputed"] > float(
            measurement["certificate"]["residual_two_upper"]):
        raise ValueError("saved residual enclosure exceeds original certificate")
    return {
        "status": "UNREGISTERED_SAVED_STATE_COMPONENT_DIAGNOSTIC",
        "case_id": measurement["case_id"],
        "candidate_state_sha256": candidate_hash,
        "scaled_system_archive_sha256": measurement["scaled_system_archive_sha256"],
        "scaled_kkt_rhs_sha256": measurement["scaled_kkt_rhs_sha256"],
        "inverse_infinity_upper_used": measurement["certificate"]["inverse_infinity_upper"],
        **bound,
        "scientific_registration": False,
    }
