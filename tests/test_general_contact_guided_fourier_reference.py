"""Independent continuum check for the bounded guided-plate oracle."""

import numpy as np

from docs.d1_review_support.d1_guided_q1_fourier import (
    guided_q1_fourier_reference,
)


def test_uniform_pressure_matches_exact_dirichlet_neumann_plate_solution():
    # -w''=1 on [0,1], w(0)=0, w'(1)=0 gives integral(w)=1/3.
    finite, gram, tail = guided_q1_fourier_reference(
        (0.0, 0.5, 1.0), (0.0, 1.0), np.arange(6),
        contact_y_upper=1.0, shear_stiffness_n_per_m=1.0,
        x_modes=64, y_modes=64,
    )
    pressure = np.ones(6)
    lower = float(pressure @ finite @ pressure)
    upper = lower+tail*float(pressure @ gram @ pressure)
    assert lower <= 1.0/3.0 <= upper
    assert upper-lower < 1.0e-4
    np.testing.assert_allclose(pressure @ gram @ pressure, 1.0,
                               rtol=0.0, atol=1.0e-14)


def test_clipped_strip_mass_integrates_its_physical_area():
    finite, gram, tail = guided_q1_fourier_reference(
        (0.0, 0.5, 1.0), (0.0, 0.4, 1.0), np.arange(9),
        contact_y_upper=0.9, shear_stiffness_n_per_m=2.0,
        x_modes=16, y_modes=16,
    )
    pressure = np.ones(9)
    np.testing.assert_allclose(pressure @ gram @ pressure, 0.9,
                               rtol=0.0, atol=1.0e-14)
    assert np.all(np.linalg.eigvalsh(finite) >= -1.0e-14)
    assert tail > 0.0
