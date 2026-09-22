"""Bounded dense oracle for the unselected F03 P0 spectral multiplier norm."""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
from scipy.integrate import quad

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from _b3_e4_f03_p0_dual_norm import (  # noqa: E402
    cell_cosine_moments, dual_norm_squared, p0_dual_gram,
)


def test_exact_cell_integrals_against_independent_quadrature() -> None:
    for cells in (1, 3, 8, 17):
        for mode in (0, 1, 2, 9, 28):
            exact = cell_cosine_moments(cells, mode, mode + 1)[:, 0]
            for cell in range(cells):
                basis = (lambda x: 1.0 if mode == 0 else
                         np.sqrt(2.0) * np.cos(np.pi * mode * x))
                oracle = quad(basis, cell / cells, (cell + 1) / cells,
                              epsabs=2e-14)[0]
                assert abs(exact[cell] - oracle) < 2e-13


def test_positive_definite_every_cell_count_through_128() -> None:
    for cells in range(1, 129):
        # Minimal n-dimensional cosine image is full-rank for every P0 grid.
        lower, upper = p0_dual_gram(cells, 2.3, cells - 1)
        assert np.linalg.eigvalsh(lower)[0] > 0.0
        assert np.linalg.eigvalsh(upper - lower)[0] > -2e-14
        assert np.allclose(lower, lower.T, rtol=0, atol=1e-15)


def test_reference_enclosure_and_nested_refinement() -> None:
    coarse, fine = 8, 16
    length = 0.7
    repeats = np.kron(np.eye(coarse), np.ones((2, 1)))
    for last_mode in (fine - 1, 255, 1023):
        cl, cu = p0_dual_gram(coarse, length, last_mode)
        fl, fu = p0_dual_gram(fine, length, last_mode, chunk_size=37)
        assert np.allclose(repeats.T @ fl @ repeats, cl, rtol=2e-13, atol=2e-15)
        assert np.allclose(repeats.T @ fu @ repeats, cu, rtol=2e-13, atol=2e-15)
    lower, upper = p0_dual_gram(coarse, length, 255)
    reference, _ = p0_dual_gram(coarse, length, 8191)
    assert np.linalg.eigvalsh(reference - lower)[0] > -2e-15
    assert np.linalg.eigvalsh(upper - reference)[0] > -2e-15
    coarse_width = np.linalg.norm(upper - lower, 2)
    tight_lower, tight_upper = p0_dual_gram(coarse, length, 1023)
    assert np.linalg.norm(tight_upper - tight_lower, 2) < coarse_width


def test_units_and_force_work_pairing() -> None:
    density = np.array([1.5, -2.0, 0.25, 3.0]) * 1e6  # N/m
    length_m = 0.7
    gm, _ = p0_dual_gram(4, length_m, 127)
    gmm, _ = p0_dual_gram(4, length_m * 1000, 127)
    assert np.isclose(dual_norm_squared(density, gm),
                      dual_norm_squared(density / 1000, gmm), rtol=3e-14)
    displacement_m = np.array([0.02, -0.01, 0.04, 0.03])
    work_j = length_m / 4 * density @ displacement_m
    work_in_mm_units = length_m * 1000 / 4 * (density / 1000) @ (
        displacement_m * 1000) / 1000
    assert np.isclose(work_j, work_in_mm_units)


def test_reject_underresolved_or_nonphysical_inputs() -> None:
    import pytest

    with pytest.raises(ValueError, match="last_mode"):
        p0_dual_gram(8, 1.0, 6)
    with pytest.raises(ValueError, match="length_m"):
        p0_dual_gram(2, 0.0, 2)
    with pytest.raises(ValueError, match="dimensions"):
        dual_norm_squared(np.ones(2), np.eye(3))
    with pytest.raises(ValueError, match="last_mode"):
        p0_dual_gram(2, 1.0, 65536)
    with pytest.raises(ValueError, match="length_m"):
        p0_dual_gram(2, 1e200, 2)
    with pytest.raises(ValueError, match="dimensions"):
        dual_norm_squared(np.array([1.0, np.nan]), np.eye(2))
    with pytest.raises(ValueError, match="positive symmetric"):
        dual_norm_squared(np.ones(2), np.diag([1., -1.]))
