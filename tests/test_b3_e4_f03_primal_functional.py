"""Analytical checks of a reference functional, without structural solves."""
import importlib.util
from pathlib import Path
import sys

import numpy as np
from numpy.polynomial import Polynomial, Legendre
import pytest

_path = Path(__file__).resolve().parents[1]/'scripts/_b3_e4_f03_primal_functional.py'
_spec = importlib.util.spec_from_file_location('_f03_primal_functional_test', _path)
module = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = module
_spec.loader.exec_module(module)
Functional = module.Functional


def test_constant_density_and_physical_moment_scaling():
    force = np.array([2., -3., .46*4.])
    f = Functional(force[None], np.zeros(3), np.zeros((2, 3)))
    np.testing.assert_allclose(module.green_inner(f, f), [4., 9., 16.], rtol=2e-14)
    assert module.norm_squared(f) == pytest.approx(29., rel=2e-14)


def test_signed_atoms_match_exact_free_endpoint_green_matrix():
    atoms = np.array([[2., 0., -.46], [-3., 0., .92]])
    f = Functional(np.zeros((1, 3)), np.zeros(3), atoms)
    gram = np.array([[np.cosh(1.), 1.], [1., np.cosh(1.)]])/np.sinh(1.)
    expected = np.array([np.array([2., -3.])@gram@np.array([2., -3.]),
                         0., np.array([-1., 2.])@gram@np.array([-1., 2.])])
    np.testing.assert_allclose(module.green_inner(f, f), expected, rtol=2e-15)


def test_manufactured_polynomial_riesz_solution_including_boundary_atoms():
    # y(s) arbitrary polynomial, rho=y-y'', atoms=(-y'(0),y'(1)).
    y = Polynomial([1., 2., -.75, .3, -.2, .04])
    rho = y-y.deriv(2)
    x_polynomial = rho(Polynomial([.5, .5])).convert(kind=Legendre)
    coeff = np.zeros((len(x_polynomial.coef), 3)); coeff[:, 0] = x_polynomial.coef
    f = Functional(coeff, np.zeros(3), [[-y.deriv()(0), 0, 0], [y.deriv()(1), 0, 0]])
    primitive = (y*y+y.deriv()*y.deriv()).integ()
    expected = primitive(1)-primitive(0)
    assert module.norm_squared(f) == pytest.approx(expected, rel=2e-13)


def test_cosine_riesz_solution_and_split_triangle_quadrature():
    amplitude = 2.5
    f = Functional(np.zeros((1, 3)), [0, amplitude, 0], np.zeros((2, 3)))
    expected = amplitude**2/(2*(1+4*np.pi**2))
    assert module.norm_squared(f, order=48) == pytest.approx(expected, rel=3e-13)
    assert module.norm_squared(f, order=64) == pytest.approx(expected, rel=3e-13)


def test_physical_bands_include_lever_arm_and_atoms_once():
    f = Functional([[2., 3., 5.]], np.zeros(3), [[7., 11., 13.], [17., 19., 23.]])
    np.testing.assert_allclose(module.band_wrench(f, 0, 1), [26., 33., 61.5], atol=2e-14)
    quarters = sum((module.band_wrench(f, i/4, (i+1)/4) for i in range(4)))
    np.testing.assert_allclose(quarters, module.band_wrench(f, 0, 1), atol=2e-14)
    np.testing.assert_allclose(module.band_wrench(f, .25, .5), [.5, .75, 1.53125], atol=2e-14)


def test_owned_arrays_and_difference_do_not_alias():
    coeff = np.ones((2, 3)); cosine = np.zeros(3); atoms = np.zeros((2, 3))
    f = Functional(coeff, cosine, atoms)
    coeff[:] = 99; cosine[:] = 99; atoms[:] = 99
    np.testing.assert_array_equal(f.coefficients, 1.)
    difference = f.difference(Functional(np.ones((1, 3)), np.zeros(3), np.zeros((2, 3))))
    assert not np.shares_memory(difference.coefficients, f.coefficients)
    np.testing.assert_array_equal(difference.coefficients, [[0, 0, 0], [1, 1, 1]])
    with pytest.raises(ValueError):
        f.coefficients[0, 0] = 2


@pytest.mark.parametrize('bad', [np.zeros((26, 3)), np.zeros((2, 2)), [[np.nan, 0, 0]]])
def test_reject_bad_density(bad):
    with pytest.raises(ValueError):
        Functional(bad, np.zeros(3), np.zeros((2, 3)))


def test_bounds_and_negative_norm_are_explicit(monkeypatch):
    f = Functional(np.zeros((1, 3)), np.zeros(3), np.zeros((2, 3)))
    with pytest.raises(ValueError):
        f.density(-.01)
    with pytest.raises(ValueError):
        module.norm_squared(f, order=100)
    with pytest.raises(ValueError):
        module.band_wrench(f, 0, 1.1)
    monkeypatch.setattr(module, 'green_inner', lambda *a, **kw: np.array([-1e-20, 0, 0]))
    with pytest.raises(ValueError, match='no clipping'):
        module.norm_squared(f)


def test_degree24_projection_and_independent_band_antiderivatives():
    rng = np.random.default_rng(73821)
    f = Functional(rng.normal(size=(25, 3))*1000, [0, 250000, 0],
                   [[120, -240, 72], [230, 150, -47]])
    x, _ = np.polynomial.legendre.leggauss(25)
    projected = module.from_gauss_density(24, f.density((x+1)/2), f.cosine, f.atoms)
    np.testing.assert_allclose(projected.coefficients, f.coefficients, atol=2e-9, rtol=3e-11)
    for left, right in ((0, 1), (0, 1/32), (1/32, 1/16), (15/16, 31/32), (31/32, 1)):
        exact = module.band_wrench_analytic(f, left, right)
        np.testing.assert_allclose(module.band_wrench(f, left, right, order=48), exact, atol=2e-9)
        np.testing.assert_allclose(module.band_wrench(f, left, right, order=64), exact, atol=2e-9)


def test_zero_polynomial_moment_and_final_overflow_rejected(monkeypatch):
    zero = Functional(np.zeros((25, 3)), np.zeros(3), np.zeros((2, 3)))
    np.testing.assert_array_equal(module.band_wrench_analytic(zero, 0, 1), np.zeros(3))
    monkeypatch.setattr(module, 'green_inner', lambda *a, **kw: np.full(3, 1e308))
    with np.errstate(over='ignore'), pytest.raises(ValueError, match='nonfinite total'):
        module.norm_squared(zero)
    large = Functional([[0, 1e308, 1e308]], [0, 0, 0], [[0, 1e308, 1e308], [0, 1e308, 1e308]])
    for method in (module.band_wrench, module.band_wrench_analytic):
        with np.errstate(over='ignore', invalid='ignore'), pytest.raises(ValueError, match='nonfinite'):
            method(large, 0, 1)
