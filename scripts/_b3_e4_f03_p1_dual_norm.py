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


def nonuniform_hat_cosine_moments(knots_m, first_mode: int,
                                 stop_mode: int) -> np.ndarray:
    """Exact P1-hat/cosine moments on declared physical reference knots.

    The Neumann cosines use xi=(x-x0)/(xN-x0), as in the uniform convention.
    This is a scalar multiplier-space construction, not a structural norm.
    """
    knots = np.asarray(knots_m, dtype=float)
    if (knots.ndim != 1 or not 2 <= len(knots) <= 129 or
            not np.isfinite(knots).all() or
            np.any(np.diff(knots) <= 0.) or
            not np.isfinite(knots[-1]-knots[0]) or knots[-1] <= knots[0]):
        raise ValueError("strictly increasing finite P1 reference knots required")
    if (type(first_mode) is not int or type(stop_mode) is not int or
            first_mode < 0 or stop_mode < first_mode or stop_mode > 65536):
        raise ValueError("invalid nonnegative mode interval")
    xi = (knots-knots[0])/(knots[-1]-knots[0])
    widths = np.diff(xi)
    if np.any(widths <= 0.):
        raise ValueError("representable distinct normalized P1 knots required")
    modes = np.arange(first_mode, stop_mode, dtype=np.float64)
    out = np.zeros((len(knots), len(modes)))
    if not len(modes):
        return out
    zero = modes == 0
    active = ~zero
    for cell, h in enumerate(widths):
        a, b = xi[cell], xi[cell+1]
        if np.any(zero):
            out[cell, zero] += h/2
            out[cell+1, zero] += h/2
        if np.any(active):
            frequency = np.pi*modes[active]
            difference = (np.cos(frequency*a)-np.cos(frequency*b))/(
                h*frequency**2)
            out[cell, active] += np.sqrt(2.)*(
                -np.sin(frequency*a)/frequency+difference)
            out[cell+1, active] += np.sqrt(2.)*(
                np.sin(frequency*b)/frequency-difference)
    return out


def p1_nonuniform_dual_gram(knots_m, last_mode: int, *,
                            chunk_size: int = 2048) -> tuple[np.ndarray, np.ndarray]:
    """Floating scalar H^(-1/2) Gram bounds for nonuniform physical P1 hats.

    The length scaling matches p1_dual_gram for identical uniform knots.
    Positive tail enclosure follows Parseval in exact arithmetic; binary64
    evaluation and its clipped roundoff are not interval certification.
    """
    knots = np.asarray(knots_m, dtype=float)
    if (knots.ndim != 1 or not 2 <= len(knots) <= 129 or
            not np.isfinite(knots).all() or
            np.any(np.diff(knots) <= 0.) or
            not np.isfinite(knots[-1]-knots[0]) or knots[-1] <= knots[0]):
        raise ValueError("strictly increasing finite P1 reference knots required")
    if type(last_mode) is not int or not len(knots)-1 <= last_mode <= 65535:
        raise ValueError("last_mode must include all P1 hat directions")
    if type(chunk_size) is not int or not 1 <= chunk_size <= 65536:
        raise ValueError("chunk_size must be a positive integer")
    length = float(knots[-1]-knots[0])
    widths = np.diff((knots-knots[0])/length)
    if np.any(widths <= 0.):
        raise ValueError("representable distinct normalized P1 knots required")
    mass = np.zeros((len(knots), len(knots)))
    for cell, h in enumerate(widths):
        mass[cell, cell] += h/3
        mass[cell+1, cell+1] += h/3
        mass[cell, cell+1] += h/6
        mass[cell+1, cell] += h/6
    weighted = np.zeros_like(mass)
    projection = np.zeros_like(mass)
    for start in range(0, last_mode+1, chunk_size):
        stop = min(start+chunk_size, last_mode+1)
        moments = nonuniform_hat_cosine_moments(knots, start, stop)
        modes = np.arange(start, stop, dtype=np.float64)
        weights = 1./np.sqrt(1.+(np.pi*modes)**2)
        weighted += (moments*weights[None, :])@moments.T
        projection += moments@moments.T
    residual = (mass-projection+mass.T-projection.T)/2
    eigenvalues, vectors = np.linalg.eigh(residual)
    if eigenvalues[0] < -1e-10/(len(knots)-1):
        raise ArithmeticError("cosine projection exceeds nonuniform P1 mass")
    residual = (vectors*np.maximum(eigenvalues, 0.))@vectors.T
    first_omitted = 1./np.sqrt(1.+(np.pi*(last_mode+1))**2)
    lower = length**2*(weighted+weighted.T)/2
    upper = lower+length**2*first_omitted*residual
    upper = (upper+upper.T)/2
    if not np.isfinite(lower).all() or not np.isfinite(upper).all():
        raise ValueError("nonuniform P1 spectral Gram is not representable")
    return lower, upper
