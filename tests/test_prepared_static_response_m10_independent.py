"""Closed-form rational checks of the diagnostic enclosure building blocks."""
from fractions import Fraction

import numpy as np
import pytest

from prepared_static_response_m10_bounds import (
    ActionBound, SignedActionBound, dot, contains, shell_vm,
)


@pytest.mark.parametrize('bound_class', [ActionBound, SignedActionBound])
@pytest.mark.parametrize('matrix,rhs,solution', [
    ([[4., 1.], [2., 3.]], [1., 2.], [Fraction(1, 10), Fraction(3, 5)]),
    ([[0., 2.], [1., 3.]], [2., 4.], [Fraction(1), Fraction(1)]),
])
def test_component_error_contains_closed_form_exact_solution(bound_class, matrix, rhs, solution):
    candidate = np.array([float(x) for x in solution]) + np.array([1e-12, -2e-12])
    bound = bound_class(np.array(matrix))
    assert bound.accepted
    radii = bound.error(np.array(rhs), candidate)
    # Exact solutions are obtained from two scalar equations, not from the LU
    # candidate, factor-defect calculation, or another numerical solver.
    assert all(abs(Fraction(float(x)) - exact) <= radius
               for x, exact, radius in zip(candidate, solution, radii))


def test_dot_enclosure_covers_cancellation_and_gradual_underflow_examples():
    fixed = [(Fraction(1), Fraction(1))] * 3
    enclosure = dot([1e16, 1., -1e16], fixed)
    assert contains(enclosure, 0.)
    assert enclosure[0] <= 1 <= enclosure[1]
    subnormal = np.nextafter(0., 1.)
    enclosure = dot([subnormal], [(Fraction(1, 2), Fraction(1, 2))])
    assert contains(enclosure, 0.)
    assert enclosure[0] <= Fraction(float(subnormal)) / 2 <= enclosure[1]


def test_shell_vm_contains_closed_form_uniaxial_and_pure_shear_results():
    zero = (Fraction(0), Fraction(0))
    three = (Fraction(3), Fraction(3))
    assert contains(shell_vm([three, zero, zero, zero, zero, zero, zero, zero]), 3.)
    two = (Fraction(2), Fraction(2))
    low, high = shell_vm([zero, zero, two, zero, zero, zero, zero, zero])
    # The physical pure-shear result is sqrt(12); test the enclosure through
    # exact squaring, independently of either native or diagnostic sqrt.
    assert low >= 0 and low * low <= 12 <= high * high
