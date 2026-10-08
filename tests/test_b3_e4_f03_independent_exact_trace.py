"""Check the exact-trace diagnostic's polynomial and rank assumptions."""

import numpy as np
from numpy.polynomial.legendre import leggauss

from scripts.b3_e4_f03_independent_exact_trace import (
    exact_trace_image, one_tolerance, trace_rows)
from scripts.b3_e4_f03_independent_transverse_reference import _line_edges


def test_four_point_trace_is_cubic_on_every_declared_segment():
    nx, ny, nb = 2, 2, 4
    edges = _line_edges(0, 1, nx, nb, "spline")
    points, _ = leggauss(4)
    vandermonde = np.column_stack([points**power for power in range(4)])
    rng = np.random.default_rng(1902)
    q = rng.standard_normal(trace_rows(nx, ny, nb, .5).shape[1])
    for left, right in zip(edges[:-1], edges[1:]):
        center, half = (left+right)/2, (right-left)/2
        values = np.vstack([trace_rows(nx, ny, nb, center+half*point)@q
                            for point in points])
        midpoint_from_cubic = np.linalg.solve(vandermonde, values)[0]
        np.testing.assert_allclose(midpoint_from_cubic,
                                   trace_rows(nx, ny, nb, center)@q,
                                   rtol=1e-11, atol=1e-12)
    image, _ = exact_trace_image(nx, ny, nb)
    assert image.shape[0] == 12*(len(edges)-1)


def test_exact_bond_response_is_rank_tolerance_stable_and_gap_free():
    loose = one_tolerance(1e-9, 2, 2, 4)
    tight = one_tolerance(1e-11, 2, 2, 4)
    assert loose["trace_rank"] == tight["trace_rank"]
    assert loose["null_dimension"] > 0
    for kind in ("torsion", "transverse_force_z"):
        for response in ("tip_z_m", "tip_rx_rad"):
            np.testing.assert_allclose(loose["responses"][kind][response],
                                       tight["responses"][kind][response],
                                       rtol=1e-10, atol=1e-15)
        assert loose["responses"][kind][
            "sampled_gap_max_m_at_1m_characteristic_length"] < 1e-12
