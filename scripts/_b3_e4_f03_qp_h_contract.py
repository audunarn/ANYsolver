"""Solve-free shape checks for a prospective F03 classical Q6 h gate.

This is not a scientific adjudicator. Formal acceptance also needs independent
mechanical replay, numerical certification, and a supervised resource receipt.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

import numpy as np

from scripts._b3_e4_f03_conforming_qp_trace import FinitePadQpTrace
from scripts._b3_e4_f03_qp_piecewise_functional import PiecewiseFunctional
from scripts.b3_e4_f03_qp_nested_x_pilot import BANDS, refined_x, refined_x2


SCHEMA = "f03_q6_h_v1"
CASES = ("X0", "X1", "X2")
CASE_STATUS = {
    "X0": "UNREGISTERED_NESTED_X0_PILOT",
    "X1": "UNREGISTERED_NESTED_X_PILOT",
    "X2": "UNREGISTERED_NESTED_X2_PILOT",
}
CASE_COUNTS = {"X0": (10, 11, 3286, 3410),
               "X1": (13, 17, 4402, 4526),
               "X2": (17, 25, 5890, 6014)}
_X0_HEX = (
    "-0x1.0000000000000p-1", "-0x1.0000000000000p-2",
    "-0x1.3333333333334p-3", "0x1.3333333333334p-3",
    "0x1.0000000000000p-2", "0x1.8000000000000p-1",
    "0x1.b333333333334p-1", "0x1.2666666666666p+0",
    "0x1.4000000000000p+0", "0x1.8000000000000p+0",
)
_X1_HEX = _X0_HEX[:3] + ("0x0.0p+0",) + _X0_HEX[3:5] + (
    "0x1.0000000000000p-1",) + _X0_HEX[5:7] + (
    "0x1.0000000000000p+0",) + _X0_HEX[7:]
_X2_HEX = (
    "-0x1.0000000000000p-1", "-0x1.8000000000000p-2",
    "-0x1.0000000000000p-2", "-0x1.3333333333334p-3",
    "0x0.0p+0", "0x1.3333333333334p-3",
    "0x1.0000000000000p-2", "0x1.8000000000000p-2",
    "0x1.0000000000000p-1", "0x1.4000000000000p-1",
    "0x1.8000000000000p-1", "0x1.b333333333334p-1",
    "0x1.0000000000000p+0", "0x1.2666666666666p+0",
    "0x1.4000000000000p+0", "0x1.6000000000000p+0",
    "0x1.8000000000000p+0",
)
CASE_X_HEX = {"X0": _X0_HEX, "X1": _X1_HEX, "X2": _X2_HEX}
CASE_Y_HEX = (
    "-0x1.0000000000000p-1", "-0x1.1eb851eb851ecp-2",
    "-0x1.70a3d70a3d70ap-3", "0x1.70a3d70a3d70ap-3",
    "0x1.1eb851eb851ecp-2", "0x1.0000000000000p-1",
)
CASE_NUMERICAL = (
    "beam_discrepancy_relative", "load_discrepancy_scaled",
    "root_compatibility_scaled", "equilibrium_scaled",
    "work_identity_scaled", "max_precision_defect", "max_nodal_defect",
    "max_held_defect", "max_boundary_crossing_shift",
    "max_endpoint_defect",
)
SPATIAL_NUMERICAL_LIMITS = {
    "area_line_nodal_gap_scaled": 2e-10,
    "free_equilibrium_scaled": 2e-9,
    "area_line_wrench_gap_scaled": 2e-9,
    "area_order_discrepancy": 2e-10,
    "lifting_invariance_scaled": 2e-9,
    "global_shell_balance_scaled": 2e-9,
    "beam_root_reaction_defect_scaled": 2e-9,
    "maximum_spatial_work_defect_scaled": 2e-9,
}
# These byte counts are mathematical minima for a full float64 inverse-column
# stream, not execution budgets. A future protocol must set its own limits.
def minimum_inverse_bytes(case_id: str) -> int:
    if case_id not in CASES:
        raise ValueError("unknown fixed-Q6 case")
    order = CASE_COUNTS[case_id][2] + 3
    return 8 * order * order


def trace_for_case(case_id: str) -> FinitePadQpTrace:
    if case_id not in CASES:
        raise ValueError("unknown fixed-Q6 case")
    x = None if case_id == "X0" else (
        refined_x() if case_id == "X1" else refined_x2())
    trace = FinitePadQpTrace(6, x=x)
    expected = CASE_COUNTS[case_id]
    if (len(trace.x), len(trace.station_intervals()),
            len(trace.free_columns), 2*trace.n) != expected:
        raise ArithmeticError("frozen Q6 topology changed")
    if (tuple(value.hex() for value in trace.x) != CASE_X_HEX[case_id] or
            tuple(value.hex() for value in trace.y) != CASE_Y_HEX):
        raise ArithmeticError("frozen Q6 coordinates changed")
    return trace


def _finite(value, shape, label):
    # Check structural size before NumPy converts caller-controlled data.
    if shape == ():
        if isinstance(value, (list, tuple, dict)):
            raise ValueError(f"invalid {label} shape")
    elif len(shape) == 1:
        if not isinstance(value, (list, tuple, np.ndarray)) or len(value) != shape[0]:
            raise ValueError(f"invalid {label} shape")
    elif len(shape) == 2:
        if (not isinstance(value, (list, tuple, np.ndarray)) or len(value) != shape[0] or
                any(not isinstance(row, (list, tuple, np.ndarray)) or len(row) != shape[1]
                    for row in value)):
            raise ValueError(f"invalid {label} shape")
    result = np.asarray(value, dtype=np.float64)
    if result.shape != shape or not np.isfinite(result).all():
        raise ValueError(f"invalid {label}")
    return result


@dataclass(frozen=True)
class CaseEvidence:
    case_id: str
    free_state: np.ndarray
    root_multiplier: np.ndarray
    functional: PiecewiseFunctional


def validate_case_payload(case_id: str, record: dict) -> CaseEvidence:
    """Validate bounded payload shape; do not infer a scientific pass."""
    if type(record) is not dict or case_id not in CASES:
        raise ValueError("invalid Q6 case record")
    trace = trace_for_case(case_id)
    if (record.get("status") != CASE_STATUS[case_id] or
            record.get("grid") != case_id.lower() or
            record.get("degree") != 6 or
            record.get("x") != list(trace.x) or
            record.get("y") != list(trace.y) or
            record.get("x_hex") != [x.hex() for x in trace.x] or
            record.get("y_hex") != [y.hex() for y in trace.y] or
            record.get("dof_count") != len(trace.free_columns) or
            record.get("physical_coordinates") != 2*trace.n or
            record.get("station_intervals") != [list(pair) for pair in
                                                 trace.station_intervals()]):
        raise ValueError("Q6 case topology or identity mismatch")
    q = _finite(record.get("free_state"), (len(trace.free_columns),),
                "free state")
    eta = _finite(record.get("root_multiplier"), (3,), "root multiplier")
    if hashlib.sha256(q.tobytes()).hexdigest() != record.get("free_state_sha256"):
        raise ValueError("Q6 free-state hash mismatch")
    signed = record.get("signed")
    if type(signed) is not dict:
        raise ValueError("missing signed Q6 observables")
    vector_keys = ("tip_pose", "eta", "root_section", "tip_section",
                   "root_atom", "tip_atom", "line_wrench")
    for key in vector_keys:
        _finite(signed.get(key), (3,), key)
    for key in ("shell_energy_j", "beam_energy_j", "total_energy_j",
                "external_work_j"):
        _finite(signed.get(key), (), key)
    _finite(signed.get("bands"), (len(BANDS), 3), "physical bands")
    if not np.array_equal(eta, np.asarray(signed["eta"], dtype=np.float64)):
        raise ValueError("Q6 signed root multiplier differs from saved state")
    functional_record = record.get("functional")
    if type(functional_record) is not dict:
        raise ValueError("missing Q6 functional")
    interval_count = len(trace.station_intervals())
    coefficients = functional_record.get("coefficients")
    if (not isinstance(coefficients, list) or len(coefficients) != interval_count or
            any(not isinstance(row, list) or len(row) != 9 or
                any(not isinstance(channel, list) or len(channel) != 3
                    for channel in row) for row in coefficients)):
        raise ValueError("outside bounded Q6 functional shape")
    _finite(functional_record.get("breaks"), (interval_count+1,), "breaks")
    _finite(functional_record.get("cosine"), (3,), "cosine")
    _finite(functional_record.get("atoms"), (2, 3), "atoms")
    functional = PiecewiseFunctional(
        functional_record.get("breaks"),
        coefficients,
        functional_record.get("cosine"),
        functional_record.get("atoms"),
    )
    if not np.array_equal(functional.breaks,
                          np.asarray(trace.station_breakpoints())):
        raise ValueError("Q6 functional station partition differs")
    _finite(record.get("functional_norm_n"), (), "functional norm")
    _finite(record.get("functional_squared_channels"), (3,),
            "functional channels")
    numerical = record.get("numerical")
    if type(numerical) is not dict:
        raise ValueError("missing Q6 numerical observations")
    for name in CASE_NUMERICAL:
        _finite(numerical.get(name), (), name)
    _finite(numerical.get("root_singular_values"), (3,),
            "root singular values")
    _finite(numerical.get("root_pose_derivative_singular_values"), (6,),
            "root pose/derivative singular values")
    _finite(numerical.get("scaled_shell_min_eigenvalue"), (),
            "scaled shell minimum eigenvalue")
    _finite(numerical.get("density_order_discrepancy"), (3,),
            "density order discrepancy")
    _finite(numerical.get("cross_order_discrepancy"), (3,),
            "cross order discrepancy")
    if (numerical.get("exact_interior_crossings") !=
            len(trace.station_breakpoints())-2):
        raise ValueError("Q6 exact crossing inventory differs")
    if (type(numerical.get("shell_nnz")) is not int or
            numerical["shell_nnz"] <= 0 or
            type(numerical.get("beam_nnz")) is not int or
            numerical["beam_nnz"] <= 0 or
            numerical.get("fallback_indices") != [i for i, (left, right) in
                enumerate(trace.station_intervals()) if
                np.nextafter(left, np.inf) >= right]):
        raise ValueError("Q6 sparse or sub-ulp inventory differs")
    owned_q, owned_eta = q.copy(), eta.copy()
    owned_q.setflags(write=False)
    owned_eta.setflags(write=False)
    return CaseEvidence(case_id, owned_q, owned_eta, functional)


def validate_spatial_payload(case_id: str, case_sha256: str,
                             record: dict) -> dict[str, float]:
    """Check bounded spatial shape and observed limits, not physical truth."""
    if (case_id not in CASES or type(record) is not dict or
            record.get("status") != "UNREGISTERED_Q6_SPATIAL_AUDIT" or
            record.get("grid") != case_id.lower() or
            record.get("input_sha256") != case_sha256):
        raise ValueError("Q6 spatial input identity mismatch")
    numerical = record.get("numerical")
    if type(numerical) is not dict or set(numerical) != set(SPATIAL_NUMERICAL_LIMITS):
        raise ValueError("incomplete Q6 spatial numerical inventory")
    result = {}
    for name, limit in SPATIAL_NUMERICAL_LIMITS.items():
        value = float(_finite(numerical[name], (), name))
        if value < 0 or value > limit:
            raise ArithmeticError(f"Q6 spatial check failed: {name}")
        result[name] = value
    if (type(record.get("sampled_peak_rss_bytes")) is not int or
            record["sampled_peak_rss_bytes"] <= 0):
        raise ValueError("missing Q6 spatial peak memory")
    _finite(record.get("support_wrenches"), (6,), "support wrenches")
    for name in ("area_wrench", "line_wrench", "beam_root_reaction"):
        _finite(record.get(name), (3,), name)
    works = record.get("spatial_work")
    fields = {"cell", "support", "free", "interior", "total", "reaction"}
    if (not isinstance(works, list) or len(works) != 2 or
            any(not isinstance(group, list) or len(group) != 6 for group in works)):
        raise ValueError("incomplete Q6 spatial work inventory")
    for group in works:
        for work in group:
            if type(work) is not dict or set(work) != fields:
                raise ValueError("incomplete Q6 spatial work inventory")
            for field in fields:
                _finite(work[field], (), field)
    return result
