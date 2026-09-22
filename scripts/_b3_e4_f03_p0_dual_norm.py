"""Reference-interval H^(-1/2) Gram for uniform, classical P0 line tests.

This is a norm construction only, not an F03 physical or stability result.
The Neumann cosine basis is orthonormal on x=s/L in [0, 1], and its spectral
weights are (1 + (pi*n)**2)**(-1/2). A density coefficient has units N/m;
the returned Gram has units m**2, so its quadratic form has units N**2.
"""

from __future__ import annotations

import numpy as np


def cell_cosine_moments(n_cells: int, first_mode: int, stop_mode: int) -> np.ndarray:
    """Exact integrals of normalized Neumann cosines over uniform P0 cells.

    Rows index cells, columns index modes in [first_mode, stop_mode).
    All integration is analytical; sinc avoids subtracting nearby sines.
    """
    if type(n_cells) is not int or not 1 <= n_cells <= 128:
        raise ValueError("n_cells must be a positive integer")
    if (type(first_mode) is not int or type(stop_mode) is not int
            or first_mode < 0 or stop_mode < first_mode or stop_mode > 65536):
        raise ValueError("invalid nonnegative mode interval")
    modes = np.arange(first_mode, stop_mode, dtype=np.float64)
    cells = np.arange(n_cells, dtype=np.float64) + 0.5
    moments = (np.sqrt(2.0) / n_cells
               * np.cos(np.pi * cells[:, None] * modes[None, :] / n_cells)
               * np.sinc(modes[None, :] / (2 * n_cells)))
    if first_mode == 0 and stop_mode > 0:
        moments[:, 0] = 1.0 / n_cells
    return moments


def p0_dual_gram(
    n_cells: int, length_m: float, last_mode: int, *, chunk_size: int = 2048
) -> tuple[np.ndarray, np.ndarray]:
    """Return floating Grams from analytic lower/upper Loewner formulas.

    Modes 0..last_mode are integrated exactly. At least n_cells modes are
    necessary for an SPD lower Gram. The upper bound uses Parseval's residual
    mass and the first omitted spectral weight; these are Loewner bounds, not
    elementwise bounds. Larger last_mode tightens the enclosure. No assertion
    of a mesh-uniform inf-sup or trace-continuity constant follows.
    """
    if type(n_cells) is not int or not 1 <= n_cells <= 128:
        raise ValueError("n_cells must be a positive integer")
    if (type(length_m) not in (int,float) or not np.isfinite(length_m)
            or length_m <= 0 or length_m > np.sqrt(np.finfo(float).max)
            or length_m < np.sqrt(np.nextafter(0.,1.))):
        raise ValueError("length_m must be finite and positive")
    if type(last_mode) is not int or not n_cells - 1 <= last_mode <= 65535:
        raise ValueError("last_mode must be at least n_cells - 1")
    if type(chunk_size) is not int or not 1 <= chunk_size <= 65536:
        raise ValueError("chunk_size must be a positive integer")

    weighted = np.zeros((n_cells, n_cells))
    projection = np.zeros_like(weighted)
    for start in range(0, last_mode + 1, chunk_size):
        stop = min(start + chunk_size, last_mode + 1)
        moments = cell_cosine_moments(n_cells, start, stop)
        modes = np.arange(start, stop, dtype=np.float64)
        weights = 1.0 / np.sqrt(1.0 + (np.pi * modes) ** 2)
        weighted += (moments * weights[None, :]) @ moments.T
        projection += moments @ moments.T
    mass = np.eye(n_cells) / n_cells
    residual = mass - projection
    # This is only roundoff cleanup of an analytically positive operator.
    residual = (residual + residual.T) / 2
    eig, vec = np.linalg.eigh(residual)
    if eig[0] < -1e-10 / n_cells:
        raise ArithmeticError("cosine projection exceeds P0 Parseval mass")
    residual = (vec * np.maximum(eig, 0.0)) @ vec.T
    first_omitted = 1.0 / np.sqrt(1.0 + (np.pi * (last_mode + 1)) ** 2)
    lower = length_m**2 * (weighted + weighted.T) / 2
    upper = lower + length_m**2 * first_omitted * residual
    upper = (upper + upper.T) / 2
    if not np.all(np.isfinite(lower)) or not np.all(np.isfinite(upper)):
        raise ValueError("P0 spectral Gram is not representable")
    return lower, upper


def dual_norm_squared(coefficients_n_per_m: np.ndarray, gram_m2: np.ndarray) -> float:
    """Quadratic force norm; apply separately to physical metre-gap channels."""
    coefficients = np.asarray(coefficients_n_per_m, dtype=float)
    if (coefficients.ndim != 1 or gram_m2.shape != (len(coefficients),) * 2
            or not np.all(np.isfinite(coefficients)) or
            not np.all(np.isfinite(gram_m2))):
        raise ValueError("coefficients and Gram dimensions disagree")
    if not np.array_equal(gram_m2, gram_m2.T) or np.linalg.eigvalsh(gram_m2)[0] <= 0:
        raise ValueError("positive symmetric dual Gram required")
    value = float(coefficients @ gram_m2 @ coefficients)
    if not np.isfinite(value):
        raise ValueError("dual norm is not representable")
    return value
