"""Analytic and independent small-grid checks of the preparatory Qp norm."""

import numpy as np
import pytest
from numpy.polynomial.legendre import leggauss, legval

from scripts import _b3_e4_f03_qp_piecewise_functional as gf


def functional(breaks, coefficients, cosine=(0., 0., 0.), atoms=None):
    if atoms is None:
        atoms = np.zeros((2, 3))
    return gf.PiecewiseFunctional(breaks, coefficients, cosine, atoms)


def test_constant_density_linear_density_and_one_ulp_measure():
    tiny = np.nextafter(.5, 1.)
    breaks = [0., .5, tiny, 1.]
    c = np.zeros((3, 2, 3))
    c[:, 0, 0] = 2.
    c[:, 0, 2] = .46*4.
    f = functional(breaks, c)
    np.testing.assert_array_equal(f.breaks, breaks)
    np.testing.assert_allclose(gf.norm_squared(f).squared_channels,
                               [4., 0., 16.], rtol=2e-14, atol=1e-14)
    # For rho(s)=s, (-d²/ds²+1)^-1 rho has Neumann solution
    # u=s+tanh(1/2)cosh(s)-sinh(s).
    c[:] = 0.
    for i, (left, right) in enumerate(zip(breaks[:-1], breaks[1:])):
        c[i, 0, 0] = (left+right)/2.
        c[i, 1, 0] = (right-left)/2.
    linear = functional(breaks, c)
    exact = (1./3. + np.tanh(.5)*(np.sinh(1.)-np.cosh(1.)+1.)
             -np.cosh(1.)+np.sinh(1.))
    assert gf.norm_squared(linear).squared_total == pytest.approx(exact, rel=2e-13)


def test_signed_endpoint_atoms_density_cross_and_moment_scaling():
    coeff = np.array([[[1., 0., .46]]])
    atoms = np.array([[2., 0., -.46*3.], [-3., 0., .46*4.]])
    result = gf.norm_squared(functional([0., 1.], coeff, atoms=atoms))
    coth = np.cosh(1.)/np.sinh(1.)
    csch = 1./np.sinh(1.)
    def expected(root, tip):
        return 1+2*(root+tip)+coth*(root*root+tip*tip)+2*csch*root*tip
    np.testing.assert_allclose(result.squared_channels,
                               [expected(2., -3.), 0., expected(-3., 4.)],
                               rtol=2e-14, atol=1e-14)
    np.testing.assert_allclose(result.density_atoms, [-2., 0., 2.],
                               rtol=2e-14, atol=1e-14)


def _direct_kernel_quadrature(f, order=88):
    """Small independent full rectangle rule with a local triangle split."""
    roots, weights = leggauss(order)
    nodes = (roots+1.)/2.
    weights = weights/2.
    scale = np.array((1., 1., 1./gf.ELL))
    def density(interval, fraction):
        l, r = f.breaks[interval:interval+2]
        s = l+(r-l)*fraction
        poly = np.moveaxis(legval(2*fraction-1,
                        f.coefficients[interval], tensor=True), 0, -1)
        return (poly+np.cos(2*np.pi*s)[..., None]*f.cosine)*scale
    answer = np.zeros(3)
    for i, (left, right) in enumerate(zip(f.breaks[:-1], f.breaks[1:])):
        width = right-left
        s = left+width*nodes
        ds = density(i, nodes)
        for j in range(i+1, len(f.breaks)-1):
            low, high = f.breaks[j:j+2]
            t = low+(high-low)*nodes
            dt = density(j, nodes)
            kernel = np.cosh(s[:, None])*np.cosh(1-t[None, :])/np.sinh(1.)
            answer += 2*width*(high-low)*np.einsum(
                "ij,ic,jc->c", weights[:, None]*weights[None, :]*kernel, ds, dt)
        # Exact triangle map t=left+(s-left)*v, plus its transpose.
        fraction_t = nodes[:, None]*nodes[None, :]
        t = left+width*fraction_t
        dt = density(i, fraction_t)
        kernel = np.cosh(t)*np.cosh(1-s[:, None])/np.sinh(1.)
        answer += 2*width**2*np.einsum(
            "ij,ic,ijc->c", weights[:, None]*weights[None, :]*
            nodes[:, None]*kernel, ds, dt)
        atoms = f.atoms*scale
        answer += 2*width*np.einsum("i,ic,ic->c", weights, ds,
            (atoms[0]*np.cosh(1-s)[:, None]+atoms[1]*np.cosh(s)[:, None])/
            np.sinh(1.))
    atoms = f.atoms*scale
    gram = np.array(((np.cosh(1.), 1.), (1., np.cosh(1.))))/np.sinh(1.)
    answer += np.einsum("ic,ij,jc->c", atoms, gram, atoms)
    return answer


@pytest.mark.parametrize("degree", (1, 2, 3))
def test_random_qp_piecewise_norm_against_full_rectangle_rule(degree):
    rng = np.random.default_rng(50300+degree)
    c = rng.normal(size=(3, degree+1, 3))
    cosine = rng.normal(size=3)*.3
    atoms = rng.normal(size=(2, 3))*.4
    f = functional([0., .2, .71, 1.], c, cosine, atoms)
    result = gf.norm_squared(f)
    np.testing.assert_allclose(result.squared_channels,
                               _direct_kernel_quadrature(f), rtol=2e-12,
                               atol=2e-12)
    assert np.max(result.density_order_discrepancy) <= gf.CHECK_TOLERANCE
    assert np.max(result.cross_order_discrepancy) <= gf.CHECK_TOLERANCE


def test_coefficient_subtraction_merges_partitions_and_cancels_cosine():
    base = functional([0., .5, 1.],
        [[[2., -1., .46], [.3, .2, -.1]],
         [[-2., 1., -.46], [.4, -.2, .1]]],
        [0., .25e6, 0.], [[3., 4., 5.], [-2., 1., -1.]])
    refined = base.refine([0., .25, .5, .75, 1.])
    first, second, difference = gf.comparison(base, refined)
    assert first.squared_total == pytest.approx(second.squared_total, rel=3e-14)
    assert difference.squared_total < 1e-24
    np.testing.assert_array_equal(base.difference(refined).cosine, np.zeros(3))
    assert gf.comparison(base, base)[2].squared_total == 0.
    altered = functional(refined.breaks, refined.coefficients,
                         [0., .25e6+2., 0.], refined.atoms)
    assert base.difference(altered).cosine[1] == -2.
    assert gf.comparison(base, altered)[2].squared_total > 0.


def test_bounded_shape_and_nonfinite_or_quadrature_failures(monkeypatch):
    with pytest.raises(ValueError, match="bounded"):
        functional(np.linspace(0., 1., 130), np.zeros((129, 1, 3)))
    with pytest.raises(ValueError, match="breakpoints"):
        functional([0., .5, .5, 1.], np.zeros((3, 1, 3)))
    f = functional([0., 1.], np.ones((1, 1, 3)))
    terms = gf._terms
    monkeypatch.setattr(gf, "_terms", lambda item, order:
        (np.array([1e9 if order == 48 else 2e9, 0., 0.]),
         np.zeros(3), np.zeros(3)))
    with pytest.raises(gf.GreenQuadratureDisagreement):
        gf.norm_squared(f)
    monkeypatch.setattr(gf, "_terms", lambda item, order:
        (np.array([-1., 0., 0.]), np.zeros(3), np.zeros(3)))
    with pytest.raises(gf.NegativeGreenResponse):
        gf.norm_squared(f)
    monkeypatch.setattr(gf, "_terms", lambda item, order:
        (np.array([np.nan, 0., 0.]), np.zeros(3), np.zeros(3)))
    with pytest.raises(gf.NonfiniteGreenResponse):
        gf.norm_squared(f)
    monkeypatch.setattr(gf, "_terms", terms)
