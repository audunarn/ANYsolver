"""Content identity for the bounded diagnostic Qp operator handoff."""

from __future__ import annotations

import hashlib
import json

import numpy as np
from scipy import sparse

from scripts._b3_e4_f03_conforming_qp_energy import QpOperators
from scripts._b3_e4_f03_sparse_factor_candidate import _digest_owned


def _numbers(value, dtype):
    array = np.asarray(value)
    required_kinds = ("i", "u") if dtype == "<i8" else ("i", "u", "f")
    if array.dtype.kind not in required_kinds or not np.isfinite(array).all():
        raise ValueError("nonfinite or nonnumerical shared Qp operator field")
    result = np.asarray(array, dtype=dtype, order="C")
    return {"shape": list(result.shape), "source_dtype": array.dtype.str,
            "sha256": hashlib.sha256(
        result.tobytes(order="C")).hexdigest()}


def fingerprint(operators: QpOperators, expected_trace) -> str:
    if type(operators) is not QpOperators:
        raise ValueError("owned Qp operators required")
    trace = operators.trace
    names = ("p", "x", "y", "offsets", "a", "j")
    if any(getattr(trace, name) != getattr(expected_trace, name) for name in names):
        raise ValueError("shared Qp trace parameters differ")
    if (trace.nodes_x != expected_trace.nodes_x or
            trace.nodes_y != expected_trace.nodes_y or
            trace.station_breakpoints() != expected_trace.station_breakpoints() or
            trace.nx != expected_trace.nx or trace.ny != expected_trace.ny or
            trace.n != expected_trace.n or trace.area != expected_trace.area):
        raise ValueError("shared Qp derived trace differs")
    if (len(trace._basis) != len(expected_trace._basis) or
            any(not np.array_equal(actual.c, expected.c)
                for actual_pair, expected_pair in
                zip(trace._basis, expected_trace._basis)
                for actual, expected in zip(actual_pair, expected_pair)) or
            not np.array_equal(trace._roots, expected_trace._roots) or
            not np.array_equal(trace._weights, expected_trace._weights)):
        raise ValueError("shared Qp basis or quadrature differs")
    if (not np.array_equal(trace.free_columns, expected_trace.free_columns) or
            not np.array_equal(operators.free_columns, trace.free_columns)):
        raise ValueError("shared Qp free-column map differs")
    if (type(operators.shell_stiffness) is not sparse.csr_matrix or
            type(operators.beam_stiffness) is not sparse.csr_matrix or
            operators.shell_stiffness.shape != (operators.dof_count,)*2 or
            operators.beam_stiffness.shape != (operators.dof_count,)*2 or
            not operators.shell_stiffness.has_canonical_format or
            not operators.beam_stiffness.has_canonical_format or
            not np.isfinite(operators.shell_stiffness.data).all() or
            not np.isfinite(operators.beam_stiffness.data).all()):
        raise ValueError("invalid shared Qp sparse operators")
    geometry = {
        "p": trace.p,
        "x": [float(v).hex() for v in trace.x],
        "y": [float(v).hex() for v in trace.y],
        "offsets": [[float(v).hex() for v in pair] for pair in trace.offsets],
        "a": trace.a.hex(), "j": trace.j.hex(),
        "nx": trace.nx, "ny": trace.ny, "n": trace.n,
        "area": trace.area.hex(),
        "nodes_x": [float(v).hex() for v in trace.nodes_x],
        "nodes_y": [float(v).hex() for v in trace.nodes_y],
        "events": [float(v).hex() for v in trace.station_breakpoints()],
        "basis": [[_numbers(poly.c, "<f8") for poly in pair]
                  for pair in trace._basis],
        "roots": _numbers(trace._roots, "<f8"),
        "weights": _numbers(trace._weights, "<f8"),
    }
    fields = {
        "geometry": geometry,
        "trace_free_columns": _numbers(trace.free_columns, "<i8"),
        "operator_free_columns": _numbers(operators.free_columns, "<i8"),
        "shell": (_digest_owned(operators.shell_stiffness),
                  operators.shell_stiffness.data.dtype.str,
                  operators.shell_stiffness.indices.dtype.str,
                  operators.shell_stiffness.indptr.dtype.str),
        "beam": (_digest_owned(operators.beam_stiffness),
                 operators.beam_stiffness.data.dtype.str,
                 operators.beam_stiffness.indices.dtype.str,
                 operators.beam_stiffness.indptr.dtype.str),
        "load": _numbers(operators.load, "<f8"),
        "root_constraint": _numbers(operators.root_constraint, "<f8"),
        "tip_pose": _numbers(operators.tip_pose, "<f8"),
        "load_discrepancy_scaled": float(operators.load_discrepancy_scaled).hex(),
        "beam_discrepancy_relative": float(operators.beam_discrepancy_relative).hex(),
        "station_intervals": int(operators.station_intervals),
    }
    if (not np.isfinite(operators.load_discrepancy_scaled) or
            not np.isfinite(operators.beam_discrepancy_relative)):
        raise ValueError("nonfinite shared Qp operator diagnostic")
    payload = json.dumps(fields, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(b"F03_QP_OPERATOR_HANDOFF_V1\0"+payload).hexdigest()
