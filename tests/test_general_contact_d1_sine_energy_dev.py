"""Independent quadrature check for the development plate reference."""

import numpy as np

from scripts.general_contact_d1_sine_energy_dev import _hat_sine_integrals


def test_uniform_q1_hat_sine_integrals_match_direct_gauss_quadrature():
    roots, weights = np.polynomial.legendre.leggauss(24)
    for elements in (4, 8):
        h = 1.0/elements
        analytic = _hat_sine_integrals(elements, 20)
        for node in (1, elements//2, elements-1):
            for frequency in (1, 3, 7, 15):
                numeric = 0.0
                for left, right in ((node-1, node), (node, node+1)):
                    x = (left+0.5*(roots+1))*h
                    hat = ((x-left*h)/h if right == node else
                           (right*h-x)/h)
                    numeric += float(np.dot(
                        weights, hat*np.sin(np.pi*frequency*x),
                    ))*h/2.0
                np.testing.assert_allclose(
                    analytic[node-1, frequency-1], numeric,
                    rtol=0.0, atol=2.0e-14,
                )
