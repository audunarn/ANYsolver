"""Endpoint-choice diagnostics for default Qp one-ulp rows, not an enclosure."""

from math import sqrt

import numpy as np
import pytest

from scripts._b3_e4_f03_conforming_qp_energy import assemble, solve
from scripts._b3_e4_f03_conforming_qp_trace import FinitePadQpTrace
from scripts._b3_e4_f03_qp_fallback_bracket import pair_bracket, single_bracket
from scripts._b3_e4_f03_qp_functional_conversion import from_qp_recovery


ETA = np.array((1.6e5, -2.2e5, 7.1e4))


def random_audit(degree):
    trace = FinitePadQpTrace(degree)
    rng = np.random.default_rng(900+degree)
    q = rng.normal(size=2*trace.n)*2e-4
    q[np.setdiff1d(np.arange(2*trace.n), trace.free_columns)] = 0.
    return from_qp_recovery(trace, q, ETA)


@pytest.mark.parametrize("degree", (1, 2, 3))
def test_endpoint_choices_change_only_counted_fallback_rows(degree):
    audit = random_audit(degree)
    left, right = audit.functional, audit.right_limit_functional
    assert audit.fallback_indices == (5, 8, 10)
    assert audit.fallback_intervals == len(audit.fallback_indices)
    np.testing.assert_array_equal(left.breaks, right.breaks)
    np.testing.assert_array_equal(left.cosine, right.cosine)
    np.testing.assert_array_equal(left.atoms, right.atoms)
    changed = np.flatnonzero(np.any(left.coefficients != right.coefficients,
                                   axis=(1, 2)))
    np.testing.assert_array_equal(changed, audit.fallback_indices)
    for i in audit.fallback_indices:
        assert not np.any(left.coefficients[i, 1:])
        assert not np.any(right.coefficients[i, 1:])
    bracket = single_bracket(audit)
    assert bracket.endpoint_choice_distance_n > 0.
    assert bracket.physical_floor_n == pytest.approx(.01*max(
        1000., sqrt(bracket.left.squared_total),
        sqrt(bracket.right.squared_total)))
    assert bracket.signed_norm_change_n == pytest.approx(
        sqrt(bracket.right.squared_total)-sqrt(bracket.left.squared_total))
    assert bracket.absolute_norm_change_n == abs(bracket.signed_norm_change_n)
    assert bracket.distance_fraction_of_floor == pytest.approx(
        bracket.endpoint_choice_distance_n/bracket.physical_floor_n)
    for result in (bracket.left, bracket.right,
                   bracket.endpoint_choice_distance):
        assert np.max(result.density_order_discrepancy) <= 1e-10
        assert np.max(result.cross_order_discrepancy) <= 1e-10


def test_cross_degree_difference_reports_all_four_choices():
    first, second = random_audit(1), random_audit(2)
    pair = pair_bracket(first, second)
    distances = np.array([sqrt(item.squared_total) for item in (
        pair.left_left, pair.right_right, pair.left_right, pair.right_left)])
    assert pair.signed_same_choice_change_n == pytest.approx(
        distances[1]-distances[0])
    assert pair.absolute_distance_range_n == pytest.approx(
        np.ptp(distances))
    assert pair.range_fraction_of_floor == pytest.approx(
        pair.absolute_distance_range_n/pair.physical_floor_n)
    assert pair.physical_floor_n >= 10.


def test_representative_solved_q1_state_bracket():
    trace = FinitePadQpTrace(1)
    operators = assemble(trace)
    free_q, eta, _ = solve(operators)
    q = np.zeros(2*trace.n)
    q[operators.free_columns] = free_q
    audit = from_qp_recovery(trace, q, eta)
    bracket = single_bracket(audit)
    assert audit.fallback_intervals == 3
    assert bracket.left.squared_total > 0.
    assert bracket.right.squared_total > 0.
    assert bracket.endpoint_choice_distance_n >= 0.
    assert np.isfinite(bracket.distance_fraction_of_floor)
