"""Neumann H^(-1/2) Gram for a local biorthogonal dual-P1 line space.

Each dual basis function is assembled from ``2*N_i-N_j`` on cells adjacent
to node i. It is generally discontinuous across cell boundaries. This is
a bounded F03 diagnostic norm, not a continuum inf-sup certificate.
"""

from __future__ import annotations

import numpy as np


def dual_linear_cosine_moments(n_cells: int, first_mode: int,
                               stop_mode: int) -> np.ndarray:
    """Analytic dual-basis moments against normalized Neumann cosines."""
    if type(n_cells) is not int or not 1 <= n_cells <= 128:
        raise ValueError("bounded positive dual cell count required")
    if (type(first_mode) is not int or type(stop_mode) is not int or
            first_mode < 0 or stop_mode < first_mode or stop_mode > 65536):
        raise ValueError("invalid dual cosine mode interval")
    modes = np.arange(first_mode, stop_mode, dtype=np.float64)
    out = np.zeros((n_cells+1, len(modes)))
    if not len(modes):
        return out
    h = 1./n_cells
    zero = modes == 0
    for cell in range(n_cells):
        left = np.zeros(len(modes))
        right = np.zeros(len(modes))
        left[zero] = h/2
        right[zero] = h/2
        active = ~zero
        if np.any(active):
            frequency = np.pi*modes[active]
            a, b = cell*h, (cell+1)*h
            cosine_difference = (np.cos(frequency*a)-
                                 np.cos(frequency*b))/(h*frequency**2)
            left[active] = np.sqrt(2.)*(
                -np.sin(frequency*a)/frequency+cosine_difference)
            right[active] = np.sqrt(2.)*(
                np.sin(frequency*b)/frequency-cosine_difference)
        out[cell] += 2*left-right
        out[cell+1] += 2*right-left
    return out


def dual_linear_gram(n_cells: int, length_m: float, last_mode: int,
                     *, chunk_size: int = 2048) -> tuple[np.ndarray, np.ndarray]:
    """Floating lower/upper spectral-tail Grams for dual-P1 coefficients."""
    if type(n_cells) is not int or not 1 <= n_cells <= 128:
        raise ValueError("bounded positive dual cell count required")
    if (type(length_m) not in (int, float) or not np.isfinite(length_m)
            or length_m <= 0.):
        raise ValueError("finite positive dual length required")
    if type(last_mode) is not int or not n_cells <= last_mode <= 65535:
        raise ValueError("dual modes must cover every basis direction")
    if type(chunk_size) is not int or not 1 <= chunk_size <= 65536:
        raise ValueError("bounded positive dual chunk size required")
    h = 1./n_cells
    mass = np.diag(np.r_[h, np.full(n_cells-1, 2*h), h])
    adjacent = np.arange(n_cells)
    mass[adjacent, adjacent+1] = -h/2
    mass[adjacent+1, adjacent] = -h/2
    weighted = np.zeros_like(mass)
    projection = np.zeros_like(mass)
    for start in range(0, last_mode+1, chunk_size):
        stop = min(start+chunk_size, last_mode+1)
        moments = dual_linear_cosine_moments(n_cells, start, stop)
        modes = np.arange(start, stop, dtype=np.float64)
        weights = 1./np.sqrt(1.+(np.pi*modes)**2)
        weighted += (moments*weights[None, :])@moments.T
        projection += moments@moments.T
    residual = (mass-projection+mass.T-projection.T)/2
    eigenvalues, vectors = np.linalg.eigh(residual)
    if eigenvalues[0] < -1e-10/n_cells:
        raise ArithmeticError("dual cosine projection exceeds Parseval mass")
    residual = (vectors*np.maximum(eigenvalues, 0.))@vectors.T
    first_omitted = 1./np.sqrt(1.+(np.pi*(last_mode+1))**2)
    lower = length_m**2*(weighted+weighted.T)/2
    upper = lower+length_m**2*first_omitted*residual
    upper = (upper+upper.T)/2
    if (not np.isfinite(lower).all() or not np.isfinite(upper).all() or
            np.linalg.eigvalsh(lower)[0] <= 0.):
        raise ArithmeticError("positive finite dual spectral Gram required")
    return lower, upper
