"""G0 F07 analytical check for a constrained, massless descriptor.

This is a small formulation oracle. It does not use or qualify B3/E4 mass
operators, the mixed owner, free-free modes, or buckling.
"""

import numpy as np
from scipy import linalg


def test_massless_retained_coordinate_and_multiplier_are_algebraic():
    # U = 12 us^2/2 + 20 (ub-r)^2/2 + 30 r^2/2.
    # The last row enforces us=ub; r and its multiplier have no inertia.
    stiffness = np.array(
        [[12., 0., 0., 1.],
         [0., 20., -20., -1.],
         [0., -20., 50., 0.],
         [1., -1., 0., 0.]],
    )
    mass = np.diag([2., 3., 0., 0.])
    homogeneous, vectors = linalg.eig(
        stiffness, mass, homogeneous_eigvals=True, check_finite=True,
    )
    alpha, beta = homogeneous
    finite = np.flatnonzero(np.abs(beta) > 1e-12 * np.max(np.abs(homogeneous)))
    assert finite.size == 1
    assert np.count_nonzero(beta == 0.) == 3
    assert np.array_equal(np.diag(mass), [2., 3., 0., 0.])

    value = alpha[finite[0]] / beta[finite[0]]
    # Static elimination gives r=(20/50) ub and us=ub, hence
    # K_eff=12+20*30/50=24 and M_eff=2+3=5.
    assert abs(value.imag) <= 1e-13
    np.testing.assert_allclose(value.real, 24. / 5., rtol=1e-12, atol=0.)
    vector = vectors[:, finite[0]]
    equation = stiffness @ vector - value * (mass @ vector)
    normalizer = (np.linalg.norm(stiffness, 2) +
                  abs(value) * np.linalg.norm(mass, 2)) * np.linalg.norm(vector)
    assert np.linalg.norm(equation) / normalizer <= 1e-12
    assert abs(vector[0] - vector[1]) / np.linalg.norm(vector[:3]) <= 1e-12
    assert abs(vector[2] - .4 * vector[1]) / np.linalg.norm(vector[:3]) <= 1e-12
