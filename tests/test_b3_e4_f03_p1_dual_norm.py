"""Independent quadrature checks for the bounded P1 line-dual norm."""

import numpy as np
import pytest

from scripts._b3_e4_f03_p1_dual_norm import (
    hat_cosine_moments, p1_dual_gram)


@pytest.mark.parametrize("n_cells", (2, 4, 8))
def test_p1_hat_cosine_moments_match_independent_gauss(n_cells):
    modes = np.arange(13)
    observed = hat_cosine_moments(n_cells, 0, len(modes))
    expected = np.zeros_like(observed)
    points, weights = np.polynomial.legendre.leggauss(64)
    for cell in range(n_cells):
        x = (cell+.5+.5*points)/n_cells
        measure = weights/(2*n_cells)
        cosines = np.cos(np.pi*x[:, None]*modes[None, :])
        cosines[:, 1:] *= np.sqrt(2.)
        expected[cell] += (measure*(1.-points)/2)@cosines
        expected[cell+1] += (measure*(1.+points)/2)@cosines
    np.testing.assert_allclose(observed, expected, rtol=1e-10, atol=2e-14)


@pytest.mark.parametrize("n_cells", (2, 4, 8))
def test_p1_dual_gram_constant_and_tail_enclosure(n_cells):
    lower, upper = p1_dual_gram(n_cells, 1., 1023)
    ones = np.ones(n_cells+1)
    assert lower.shape == upper.shape == (n_cells+1, n_cells+1)
    assert np.linalg.eigvalsh(lower)[0] > 0.
    assert np.linalg.eigvalsh(upper-lower)[0] > -1e-14
    assert ones@lower@ones == pytest.approx(1., abs=2e-11)
    assert ones@upper@ones == pytest.approx(1., abs=2e-11)


def test_invalid_p1_norm_inventory_rejected():
    with pytest.raises(ValueError, match="positive length"):
        p1_dual_gram(2, 0., 16)
    with pytest.raises(ValueError, match="hat directions"):
        p1_dual_gram(8, 1., 7)
