"""Analytic-cosine H^(-1/2) Gram for uniform P1 line densities.

This scalar norm uses the same free-end Neumann spectral convention as the
existing P0 norm. The lower and upper matrices enclose only the omitted
cosine tail in exact arithmetic; floating evaluation is not an interval proof.
It is not a structural stability result by itself.
"""

from __future__ import annotations

import numpy as np


def hat_cosine_moments(n_cells: int, first_mode: int,
                       stop_mode: int) -> np.ndarray:
    """Exact integrals of uniform P1 hats against normalized cosines."""
    if type(n_cells) is not int or not 1 <= n_cells <= 128:
        raise ValueError("n_cells must be a positive integer")
    if (type(first_mode) is not int or type(stop_mode) is not int or
            first_mode < 0 or stop_mode < first_mode or stop_mode > 65536):
        raise ValueError("invalid nonnegative mode interval")
    modes = np.arange(first_mode, stop_mode, dtype=np.float64)
    out = np.zeros((n_cells+1, len(modes)))
    if not len(modes):
        return out
    zero = modes == 0
    if np.any(zero):
        h = 1./n_cells
        out[0, zero] = h/2
        out[-1, zero] = h/2
        out[1:-1, zero] = h
    active = ~zero
    if np.any(active):
        frequency = np.pi*modes[active]
        h = 1./n_cells
        for cell in range(n_cells):
            a, b = cell*h, (cell+1)*h
            cosine_difference = (np.cos(frequency*a)-
                                 np.cos(frequency*b))/(h*frequency**2)
            out[cell, active] += np.sqrt(2.)*(
                -np.sin(frequency*a)/frequency+cosine_difference)
            out[cell+1, active] += np.sqrt(2.)*(
                np.sin(frequency*b)/frequency-cosine_difference)
    return out


def p1_dual_gram(n_cells: int, length_m: float, last_mode: int,
                 *, chunk_size: int = 2048) -> tuple[np.ndarray, np.ndarray]:
    """Floating lower/upper H^(-1/2) Grams for physical P1 coefficients."""
    if type(n_cells) is not int or not 1 <= n_cells <= 128:
        raise ValueError("n_cells must be a positive integer")
    if (type(length_m) not in (int, float) or
            not np.isfinite(length_m) or length_m <= 0.):
        raise ValueError("finite positive length required")
    if type(last_mode) is not int or not n_cells <= last_mode <= 65535:
        raise ValueError("last_mode must include all P1 hat directions")
    if type(chunk_size) is not int or not 1 <= chunk_size <= 65536:
        raise ValueError("chunk_size must be a positive integer")
    h = 1./n_cells
    mass = np.diag(np.r_[h/3, np.full(n_cells-1, 2*h/3), h/3])
    adjacent = np.arange(n_cells)
    mass[adjacent, adjacent+1] = h/6
    mass[adjacent+1, adjacent] = h/6
    weighted = np.zeros_like(mass)
    projection = np.zeros_like(mass)
    for start in range(0, last_mode+1, chunk_size):
        stop = min(start+chunk_size, last_mode+1)
        moments = hat_cosine_moments(n_cells, start, stop)
        modes = np.arange(start, stop, dtype=np.float64)
        weights = 1./np.sqrt(1.+(np.pi*modes)**2)
        weighted += (moments*weights[None, :])@moments.T
        projection += moments@moments.T
    residual = (mass-projection+mass.T-projection.T)/2
    eigenvalues, vectors = np.linalg.eigh(residual)
    if eigenvalues[0] < -1e-10/n_cells:
        raise ArithmeticError("cosine projection exceeds P1 Parseval mass")
    residual = (vectors*np.maximum(eigenvalues, 0.))@vectors.T
    first_omitted = 1./np.sqrt(1.+(np.pi*(last_mode+1))**2)
    lower = length_m**2*(weighted+weighted.T)/2
    upper = lower+length_m**2*first_omitted*residual
    upper = (upper+upper.T)/2
    if not np.isfinite(lower).all() or not np.isfinite(upper).all():
        raise ValueError("P1 spectral Gram is not representable")
    return lower, upper
