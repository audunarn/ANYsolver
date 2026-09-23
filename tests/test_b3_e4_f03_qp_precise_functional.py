"""Preparatory full-functional rows on one-ulp Qp intervals."""

import numpy as np
import pytest

from scripts._b3_e4_f03_conforming_qp_trace import FinitePadQpTrace
from scripts._b3_e4_f03_qp_piecewise_functional import norm_squared
from scripts._b3_e4_f03_qp_precise_functional import (
    ENDPOINT_TOLERANCE, HELD_TOLERANCE, NODAL_TOLERANCE,
    PRECISION_TOLERANCE,
    from_qp_recovery_precise,
)


ETA = np.array((1.6e5, -2.2e5, 7.1e4))


@pytest.mark.parametrize("degree", (1, 2, 3))
def test_precise_conversion_replaces_only_three_unresolved_rows(degree):
    trace = FinitePadQpTrace(degree)
    q = np.random.default_rng(900+degree).normal(size=2*trace.n)*2e-4
    q[np.setdiff1d(np.arange(2*trace.n), trace.free_columns)] = 0.
    audit = from_qp_recovery_precise(trace, q, ETA)
    base, precise = audit.base.functional, audit.functional
    assert audit.repaired_indices == (5, 8, 10)
    assert audit.max_precision_defect <= PRECISION_TOLERANCE
    assert audit.max_held_defect/min((1e6, 1e6*.46)) <= HELD_TOLERANCE
    assert audit.max_nodal_defect <= NODAL_TOLERANCE
    assert audit.exact_interior_crossings == len(trace.station_breakpoints())-2
    assert audit.max_boundary_crossing_shift <= np.finfo(float).eps
    assert audit.max_endpoint_defect <= ENDPOINT_TOLERANCE
    np.testing.assert_array_equal(precise.breaks, base.breaks)
    np.testing.assert_array_equal(precise.cosine, base.cosine)
    np.testing.assert_array_equal(precise.atoms, base.atoms)
    for i in range(len(trace.station_intervals())):
        if i in audit.repaired_indices:
            assert np.any(precise.coefficients[i, 1:])
        else:
            np.testing.assert_array_equal(precise.coefficients[i],
                                          base.coefficients[i])
    norm = norm_squared(precise)
    assert norm.squared_total > 0.
    assert max(norm.density_order_discrepancy) < 1e-10
    assert max(norm.cross_order_discrepancy) < 1e-10


def test_custom_grid_needs_no_precision_replacement():
    trace = FinitePadQpTrace(1,
        x=(-.5, -.35, -.11, .08, .31, .67, .94, 1.23, 1.5),
        y=(-.5, -.31, -.09, .11, .31, .5))
    q = np.zeros(2*trace.n)
    audit = from_qp_recovery_precise(trace, q, ETA)
    assert audit.repaired_indices == ()
    np.testing.assert_array_equal(audit.functional.coefficients,
                                  audit.base.functional.coefficients)
