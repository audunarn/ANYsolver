from __future__ import annotations

import math

import numpy as np
import pytest

from anysolver import e4_pl_s3_element as s3


def _jet() -> s3._SecondOrderJet:
    return s3._SecondOrderJet(
        1.25,
        np.asarray((0.0, -2.0, 3.5), dtype=float),
        np.asarray(
            (
                (0.0, 1.0, -2.0),
                (1.0, -3.0, 4.0),
                (-2.0, 4.0, 5.0),
            ),
            dtype=float,
        ),
    )


def _generic_add(
    left: s3._SecondOrderJet, right: s3._SecondOrderJet
) -> tuple[float, np.ndarray, np.ndarray]:
    return (
        left.value + right.value,
        left.gradient + right.gradient,
        left.hessian + right.hessian,
    )


def _generic_multiply(
    left: s3._SecondOrderJet, right: s3._SecondOrderJet
) -> tuple[float, np.ndarray, np.ndarray]:
    return (
        left.value * right.value,
        left.gradient * right.value + right.gradient * left.value,
        left.hessian * right.value
        + right.hessian * left.value
        + np.outer(left.gradient, right.gradient)
        + np.outer(right.gradient, left.gradient),
    )


def _assert_jet(
    actual: s3._SecondOrderJet,
    expected: tuple[float, np.ndarray, np.ndarray],
) -> None:
    assert actual.value == expected[0]
    np.testing.assert_array_equal(actual.gradient, expected[1])
    np.testing.assert_array_equal(actual.hessian, expected[2])


@pytest.mark.parametrize("scalar", [0.0, -0.0, 2.5, np.float64(-3.25)])
def test_scalar_arithmetic_matches_generic_jet_formulas(scalar: float) -> None:
    source = _jet()
    constant = s3._SecondOrderJet.constant(float(scalar), source.gradient.size)

    _assert_jet(source + scalar, _generic_add(source, constant))
    _assert_jet(scalar + source, _generic_add(source, constant))
    _assert_jet(source - scalar, _generic_add(source, -constant))
    _assert_jet(scalar - source, _generic_add(constant, -source))
    _assert_jet(source * scalar, _generic_multiply(source, constant))
    _assert_jet(scalar * source, _generic_multiply(source, constant))
    if float(scalar) != 0.0:
        inverse = 1.0 / float(scalar)
        inverse_jet = s3._SecondOrderJet.constant(
            inverse, source.gradient.size
        )
        _assert_jet(source / scalar, _generic_multiply(source, inverse_jet))


def test_scalar_results_own_derivative_arrays() -> None:
    source = _jet()
    results = (
        source + 2.0,
        source - 2.0,
        2.0 - source,
        source * 2.0,
        source / 2.0,
    )
    for result in results:
        assert not np.shares_memory(result.gradient, source.gradient)
        assert not np.shares_memory(result.hessian, source.hessian)

    original_gradient = source.gradient.copy()
    original_hessian = source.hessian.copy()
    results[0].gradient[0] = 99.0
    results[0].hessian[0, 0] = 99.0
    np.testing.assert_array_equal(source.gradient, original_gradient)
    np.testing.assert_array_equal(source.hessian, original_hessian)


def test_jet_by_jet_multiplication_keeps_generic_formula() -> None:
    left = _jet()
    right = s3._SecondOrderJet(
        -0.75,
        np.asarray((1.0, 0.25, -4.0), dtype=float),
        np.asarray(
            (
                (2.0, -1.0, 0.5),
                (-1.0, 3.0, 2.0),
                (0.5, 2.0, -2.0),
            ),
            dtype=float,
        ),
    )
    _assert_jet(left * right, _generic_multiply(left, right))


def test_scalar_fast_path_preserves_errors_and_nonfinite_propagation() -> None:
    source = _jet()
    with pytest.raises(TypeError, match="division by a variable"):
        source / s3._SecondOrderJet.constant(2.0, source.gradient.size)
    with pytest.raises(ZeroDivisionError, match="division by zero"):
        source / 0.0
    with pytest.raises((TypeError, ValueError)):
        source * object()

    nonfinite = s3._SecondOrderJet(
        math.inf,
        source.gradient.copy(),
        source.hessian.copy(),
    )
    constant = s3._SecondOrderJet.constant(2.0, source.gradient.size)
    with np.errstate(invalid="ignore"):
        actual = nonfinite * 2.0
        expected = _generic_multiply(nonfinite, constant)
    assert actual.value == expected[0]
    np.testing.assert_array_equal(
        np.isnan(actual.gradient), np.isnan(expected[1])
    )
    np.testing.assert_array_equal(
        np.isnan(actual.hessian), np.isnan(expected[2])
    )


@pytest.mark.parametrize(
    ("value", "gradient", "hessian", "scalar"),
    [
        (1.0, (math.inf, 1.0), ((2.0, 0.0), (0.0, 3.0)), 2.0),
        (1.0, (1.0, 2.0), ((math.inf, 0.0), (0.0, 3.0)), 2.0),
        (1.0, (1.0, 2.0), ((2.0, 0.0), (0.0, 3.0)), math.inf),
        (1.0, (1.0, 2.0), ((2.0, 0.0), (0.0, 3.0)), math.nan),
    ],
)
def test_scalar_multiplication_preserves_all_nonfinite_generic_paths(
    value: float,
    gradient: tuple[float, ...],
    hessian: tuple[tuple[float, ...], ...],
    scalar: float,
) -> None:
    source = s3._SecondOrderJet(
        value,
        np.asarray(gradient, dtype=float),
        np.asarray(hessian, dtype=float),
    )
    constant = s3._SecondOrderJet.constant(scalar, source.gradient.size)
    with np.errstate(invalid="ignore"):
        actual = source * scalar
        expected = _generic_multiply(source, constant)
    assert actual.value == expected[0] or (
        math.isnan(actual.value) and math.isnan(expected[0])
    )
    np.testing.assert_array_equal(actual.gradient, expected[1])
    np.testing.assert_array_equal(actual.hessian, expected[2])
