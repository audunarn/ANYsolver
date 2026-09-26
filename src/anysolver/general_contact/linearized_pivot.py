"""Disposable equilibrated pressure response for the refined shell patch.

This local linearization proposes an algorithmic iterate. The coupled path
must re-equilibrate it and apply its independent contact acceptance gates.
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
from scipy import sparse

from anysolver.linalg import MatrixClass, factorize

from .augmentation import ActiveSetPivot, propose_active_set_pivot


def refined_patch_pivot(manager, displacement, tangent, transform, control_rows,
                        *, difference_step: float, maximum_pressure: float,
                        pressure_tolerance: float,
                        check_cancel: Callable[[], None] | None = None,
                        ) -> ActiveSetPivot | None:
    """Form the constrained gap Schur map at one fixed-multiplier equilibrium."""

    source, target = manager._positions(displacement)
    pressure = manager.normal_multipliers
    state = manager.law.evaluate(source, target, pressure)
    active = np.flatnonzero(state.pressure > 0.0)
    if not 2 <= len(active) <= 4:
        return None
    geometry = manager.law.geometry
    base = geometry.evaluate(source, target)
    if np.any(base.reference_support[active] <= 0.0):
        return None
    coordinates = np.concatenate((source, target)).reshape(-1)
    count = len(coordinates)
    if 2*count + 1 > manager.settings.maximum_general_s3_energy_evaluations:
        raise ValueError("active-set pivot geometry evaluation budget exceeded")
    weighted = np.zeros((len(active), count))
    support = np.zeros_like(weighted)
    source_count = len(source)
    for coordinate in range(count):
        if check_cancel is not None:
            check_cancel()
        shifted = coordinates.copy()
        shifted[coordinate] += difference_step
        plus = geometry.evaluate(
            shifted[:3*source_count].reshape(-1, 3),
            shifted[3*source_count:].reshape(-1, 3),
        )
        shifted[coordinate] -= 2*difference_step
        minus = geometry.evaluate(
            shifted[:3*source_count].reshape(-1, 3),
            shifted[3*source_count:].reshape(-1, 3),
        )
        if (plus.overlap_signature != base.overlap_signature
                or minus.overlap_signature != base.overlap_signature
                or np.any(plus.reference_support[active] <= 0.0)
                or np.any(minus.reference_support[active] <= 0.0)):
            return None
        weighted[:, coordinate] = (
            plus.reference_weighted_gap[active]
            - minus.reference_weighted_gap[active]
        )/(2*difference_step)
        support[:, coordinate] = (
            plus.reference_support[active]
            - minus.reference_support[active]
        )/(2*difference_step)
    area = base.reference_support[active, None]
    gap_derivative = (weighted/area
                      - base.reference_weighted_gap[active, None]
                      * support/area**2)
    variations = manager.map @ transform
    force_derivative = -np.asarray(variations.T @ weighted.T)
    gap_reduced = np.asarray(variations.T @ gap_derivative.T).T
    reduced_tangent = (transform.T @ tangent @ transform).tocsr()
    rows = np.asarray(control_rows, dtype=float)
    matrix = sparse.bmat([
        [reduced_tangent, sparse.csr_matrix(-rows.T)],
        [sparse.csr_matrix(rows),
         sparse.csr_matrix((len(rows), len(rows)))],
    ], format="csr")
    right = np.vstack((-force_derivative,
                       np.zeros((len(rows), len(active)))))
    factor = factorize(matrix, MatrixClass.GENERAL,
                       signature="contact_path:active_set_pivot")
    response = np.column_stack([
        np.asarray(factor.solve(right[:, column])).reshape(-1)[:transform.shape[1]]
        for column in range(len(active))
    ])
    schur = gap_reduced @ response
    if not np.all(np.isfinite(schur)):
        return None
    return propose_active_set_pivot(
        pressure, state.normalized_gap, active, schur,
        maximum_pressure=maximum_pressure,
        gap_consistency=pressure_tolerance/manager.stiffness,
    )
