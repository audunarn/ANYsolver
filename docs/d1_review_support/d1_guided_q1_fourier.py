"""Independent scalar reference for one guided planar D1 pressure fixture.

The source transverse energy is ``scale * integral |grad(w)|**2`` on a
rectangle, with w=0 at the left edge and natural conditions elsewhere.
Only the declared rectangular Q1 source and horizontal clipped strip are
admitted. This is an offline reference, not production contact mechanics.
"""

from __future__ import annotations

import numpy as np


def _linear_trigonometric_integral(left, right, value_left, value_right,
                                   wave_number, kind):
    """Exact integral of a linear function times sin/cos on one interval."""
    slope = (value_right-value_left)/(right-left)
    intercept = value_left-slope*left
    if wave_number == 0.0:
        if kind != "cos":
            raise ValueError("zero sine mode is unavailable")
        return (intercept*(right-left)
                +0.5*slope*(right*right-left*left))
    k = wave_number
    if kind == "sin":
        constant = (np.cos(k*left)-np.cos(k*right))/k
        linear = ((-right*np.cos(k*right)+left*np.cos(k*left))/k
                  +(np.sin(k*right)-np.sin(k*left))/(k*k))
    elif kind == "cos":
        constant = (np.sin(k*right)-np.sin(k*left))/k
        linear = ((right*np.sin(k*right)-left*np.sin(k*left))/k
                  +(np.cos(k*right)-np.cos(k*left))/(k*k))
    else:
        raise ValueError("unknown Fourier factor")
    return intercept*constant+slope*linear


def _hat_fourier(knots, frequencies, kind, upper):
    result = np.zeros((len(frequencies), len(knots)))
    for element in range(len(knots)-1):
        left = float(knots[element])
        right = min(float(knots[element+1]), float(upper))
        if right <= left:
            continue
        full_right = float(knots[element+1])
        span = full_right-left
        values = ((1.0, 1.0-(right-left)/span),
                  (0.0, (right-left)/span))
        for local, (first, second) in enumerate(values):
            for mode, frequency in enumerate(frequencies):
                result[mode, element+local] += (
                    _linear_trigonometric_integral(
                        left, right, first, second, frequency, kind))
    return result


def _hat_mass(knots, upper):
    result = np.zeros((len(knots), len(knots)))
    for element in range(len(knots)-1):
        left = float(knots[element])
        right = min(float(knots[element+1]), float(upper))
        if right <= left:
            continue
        full_right = float(knots[element+1])
        span = full_right-left
        # Two-point Gauss integrates these quadratic products exactly.
        for root in (-1.0/np.sqrt(3.0), 1.0/np.sqrt(3.0)):
            point = (left+right+root*(right-left))/2.0
            shape = np.asarray(((full_right-point)/span,
                                (point-left)/span))
            ids = (element, element+1)
            result[np.ix_(ids, ids)] += (right-left)/2.0*np.outer(shape, shape)
    return result


def guided_q1_fourier_reference(x_knots, y_knots, active_indices, *,
                                contact_y_upper, shear_stiffness_n_per_m,
                                x_modes, y_modes):
    """Return finite spectral compliance and a rigorous L2 tail bound.

    Eigenfunctions are sin((m+1/2)pi*x/Lx) cos(n*pi*y/Ly).
    Completeness and Parseval give, for any Q1 pressure coefficient vector p,
    ``0 <= p.T (C_true-C_finite) p <= tail_coefficient * p.T G p``.
    """
    x = np.asarray(x_knots, dtype=float)
    y = np.asarray(y_knots, dtype=float)
    active = np.asarray(active_indices, dtype=int)
    if (x_modes <= 0 or y_modes <= 0 or shear_stiffness_n_per_m <= 0
            or not np.all(np.diff(x) > 0.0)
            or not np.all(np.diff(y) > 0.0)
            or not y[0] < contact_y_upper <= y[-1]):
        raise ValueError("invalid guided Fourier reference geometry or scale")
    nx = len(x)
    ny = len(y)
    if np.any(active < 0) or np.any(active >= nx*ny):
        raise ValueError("active pressure index is outside the Q1 grid")
    length_x = x[-1]-x[0]
    length_y = y[-1]-y[0]
    x_local = x-x[0]
    y_local = y-y[0]
    upper_local = contact_y_upper-y[0]
    x_wave = np.pi*(np.arange(x_modes)+0.5)/length_x
    y_wave = np.pi*np.arange(y_modes)/length_y
    x_integrals = _hat_fourier(x_local, x_wave, "sin", length_x)
    y_integrals = _hat_fourier(y_local, y_wave, "cos", upper_local)
    x_mass = _hat_mass(x_local, length_x)
    y_mass = _hat_mass(y_local, upper_local)
    gram = np.kron(y_mass, x_mass)[np.ix_(active, active)]
    ix = active % nx
    iy = active // nx
    coefficients = (x_integrals[:, None, ix]
                    *y_integrals[None, :, iy])
    eigenvalues = x_wave[:, None]**2+y_wave[None, :]**2
    mode_norm = (length_x/2.0)*np.where(
        np.arange(y_modes)[None, :] == 0, length_y, length_y/2.0,
    )
    weights = shear_stiffness_n_per_m*eigenvalues*mode_norm
    weighted = (coefficients/np.sqrt(weights)[:, :, None]).reshape(
        -1, len(active))
    finite = weighted.T @ weighted
    finite = 0.5*(finite+finite.T)
    first_omitted = min((np.pi*(x_modes+0.5)/length_x)**2,
                        (np.pi*0.5/length_x)**2
                        +(np.pi*y_modes/length_y)**2)
    tail_coefficient = 1.0/(shear_stiffness_n_per_m*first_omitted)
    return finite, gram, tail_coefficient
