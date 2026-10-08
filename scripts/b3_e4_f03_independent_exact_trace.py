"""Exact trace-image limit of the bounded independent spline line model.

Four interior samples are unisolvent for each cubic trace segment. This is
the pointwise bond in the *fixed finite spline trial spaces*, not a
continuum solution or a native E4/B3 qualification reference.
"""

import json

import numpy as np
from numpy.polynomial.legendre import leggauss
from scipy import linalg

from scripts.b3_e4_f03_independent_transverse_reference import (
    _line_edges, assemble, beam_basis, shell_trace)


def trace_rows(nx: int, ny: int, nb: int, station: float) -> np.ndarray:
    shell = shell_trace(nx, ny, station, "local", basis="spline")
    value, _ = beam_basis(nb, station, basis="spline")
    beam = np.zeros((3, 3*len(value)))
    for channel in range(3):
        beam[channel, channel*len(value):(channel+1)*len(value)] = value
    return np.column_stack((-shell, beam))


def exact_trace_image(nx: int, ny: int, nb: int):
    edges = _line_edges(0, 1, nx, nb, "spline")
    points, _ = leggauss(4)
    rows = []
    for left, right in zip(edges[:-1], edges[1:]):
        for point in points:
            station = (left+right)/2+(right-left)*point/2
            rows.append(trace_rows(nx, ny, nb, float(station)))
    return np.vstack(rows), edges


def one_tolerance(tolerance: float, nx: int, ny: int, nb: int):
    # Only the independently assembled primal stiffness is used here. The
    # temporary two-cell mortar returned by assemble is discarded; using a
    # finer temporary mortar can fail its unrelated row-rank guard.
    ks, kb, _, _, _, _ = assemble(
        nx, ny, nb, 2, origin="local", multiplier="p0", basis="spline")
    ns, nbeam = len(ks), len(kb)
    n = nbeam//3
    k = linalg.block_diag(ks, kb)
    trace, edges = exact_trace_image(nx, ny, nb)
    _, singular, right = linalg.svd(trace, full_matrices=True,
                                    check_finite=True)
    rank = int(np.count_nonzero(singular > tolerance*singular[0]))
    null = right[rank:].T
    if null.shape[1] == 0:
        raise ValueError("exact fixed-trial line has no admissible motion")
    projected = null.T@k@null
    min_stiffness = float(linalg.eigvalsh(projected, check_finite=True)[0])
    if min_stiffness <= 0.:
        raise ValueError("projected stiffness is not positive")
    tip, _ = beam_basis(nb, 1., basis="spline")
    responses = {}
    for name, channel, magnitude in (("transverse_force_z", 0, 1000.),
                                     ("torsion", 1, 100.)):
        load = np.zeros(ns+nbeam)
        load[ns+channel*n:ns+(channel+1)*n] = magnitude*tip
        q = null@linalg.solve(projected, null.T@load, assume_a="pos")
        samples = [float(s) for left, right in zip(edges[:-1], edges[1:])
                   for s in np.linspace(left, right, 7)[1:-1]]
        gap = max(float(np.linalg.norm(trace_rows(nx, ny, nb, s)@q))
                  for s in samples)
        responses[name] = {
            "tip_z_m": float(tip@q[ns:ns+n]),
            "tip_rx_rad": float(tip@q[ns+n:ns+2*n]),
            "sampled_gap_max_m_at_1m_characteristic_length": gap,
            "work_error_j": float(q@k@q-load@q),
        }
    return {
        "purpose": "UNREGISTERED_FIXED_SPLINE_EXACT_TRACE_IMAGE",
        "not_continuum_or_native_qualification": True,
        "nx": nx, "ny": ny, "nb": nb,
        "trace_polynomial_degree_per_segment": 3,
        "trace_segments": len(edges)-1,
        "trace_rows": trace.shape[0],
        "primal_count": trace.shape[1],
        "relative_rank_tolerance": tolerance,
        "trace_rank": rank,
        "null_dimension": null.shape[1],
        "smallest_retained_singular_over_largest": float(
            singular[rank-1]/singular[0]),
        "largest_discarded_singular_over_largest": float(
            singular[rank]/singular[0]) if rank < len(singular) else 0.,
        "projected_min_stiffness": min_stiffness,
        "responses": responses,
    }


def main():
    for nx, ny, nb in ((2, 2, 4), (4, 4, 8), (8, 8, 16)):
        for tolerance in (1e-9, 1e-11):
            print(json.dumps(one_tolerance(tolerance, nx, ny, nb),
                             sort_keys=True))


if __name__ == "__main__":
    main()
